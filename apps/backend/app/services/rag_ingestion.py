"""Glue layer between LMS Material uploads and the RAG pipeline.

The Teacher uploads Material rows via the existing course / lesson endpoints.
For document types we know how to index (PDF and DOCX) we forward the file to
``llm.rag.service.RAGService`` so the content is chunked, embedded and stored
in the vector store. When the Material row is removed, the corresponding RAG
document and its chunks are removed as well.

This module is intentionally fail-soft: any ingestion error is logged and the
LMS request still succeeds. The vector store is *not* the source of truth for
the Material itself.
"""

from __future__ import annotations

import hashlib
import logging
import uuid as uuid_lib
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.models.material import Material, MaterialType
from app.models.rag import RAGDocument
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


# MIME types we currently support indexing.
INDEXABLE_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
# File extensions used as a fallback when the upload has no MIME type recorded.
INDEXABLE_EXTENSIONS = {".pdf", ".docx"}


def _resolve_storage_path(file_url: str) -> Optional[Path]:
    # Chuyển URL /storage thành đường dẫn thật trên đĩa.
    """Resolve the on-disk path for a `/storage/...` URL produced by FileHandler."""
    if not file_url:
        return None
    if file_url.startswith("http://") or file_url.startswith("https://"):
        # External link \u2014 nothing to ingest.
        return None
    relative = file_url.replace("/storage/", "", 1)
    storage_root = Path(settings.STORAGE_PATH)
    candidate = storage_root / relative
    return candidate if candidate.exists() else None


def is_indexable(material: Material) -> bool:
    # Kiểm tra material có thể đưa vào pipeline RAG hay không.
    """Return True if the Material should be sent to the RAG pipeline."""
    if not material.file_url:
        return False  # external link / no file
    if material.type and material.type != MaterialType.DOCUMENT:
        return False
    if material.mime_type and material.mime_type in INDEXABLE_MIME_TYPES:
        return True
    suffix = Path(material.file_url).suffix.lower()
    return suffix in INDEXABLE_EXTENSIONS


def _hash_file(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for block in iter(lambda: fh.read(1 << 16), b""):
                h.update(block)
        return h.hexdigest()
    except OSError as exc:
        logger.warning("[RAGIngestion] Could not hash %s: %s", path, exc)
        return None


def _doc_id_for_material(material: Material) -> str:
    return f"material_{material.id}"


def index_material(db: Session, material: Material) -> Optional[RAGDocument]:
    # Đưa tài liệu vào RAG và đồng bộ metadata vào bảng rag_documents.
    """Ingest ``material`` into the RAG pipeline if its type is supported.

    Returns the ``RAGDocument`` ORM row that mirrors the indexed document, or
    ``None`` when the material was skipped or the ingestion failed.
    The DB row is committed in this function.
    """
    if not is_indexable(material):
        logger.debug("[RAGIngestion] Skipping non-indexable material id=%s", material.id)
        return None

    storage_path = _resolve_storage_path(material.file_url or "")
    if not storage_path:
        logger.warning(
            "[RAGIngestion] Storage path missing for material id=%s url=%s",
            material.id, material.file_url,
        )
        return None

    # Lazy import so importing this module does not pull in google-genai etc.
    from llm.rag.service import get_rag_service

    rag_service = get_rag_service(use_postgres=True, verbose=False)

    file_hash = _hash_file(storage_path)
    doc_id = _doc_id_for_material(material)

    # If we already have a row for this material, reuse the doc_id and de-dup
    # via the file hash.
    existing = db.query(RAGDocument).filter(RAGDocument.material_id == material.id).first()
    if existing and existing.file_hash and existing.file_hash == file_hash:
        logger.info(
            "[RAGIngestion] Material %s already indexed with same hash \u2014 skipping",
            material.id,
        )
        return existing

    result = rag_service.ingest_document(
        file_path=storage_path,
        document_id=doc_id,
        course_id=str(material.course_id) if material.course_id else None,
        lesson_id=str(material.lesson_id) if material.lesson_id else None,
        material_id=str(material.id),
        file_hash=file_hash,
        title=material.title,
    )

    if result.get("status") != "success":
        logger.error(
            "[RAGIngestion] Failed to ingest material id=%s: %s",
            material.id, result.get("error") or result.get("message"),
        )
        return None

    # PostgresVectorStore writes to the same rag_documents table. If this is a
    # first-time ingest, re-load that row instead of inserting a duplicate ORM
    # row with the same doc_id/material_id.
    rag_doc = (
        existing
        or db.query(RAGDocument).filter(RAGDocument.material_id == material.id).first()
        or db.query(RAGDocument).filter(RAGDocument.doc_id == doc_id).first()
        or RAGDocument(doc_id=doc_id, material_id=material.id)
    )
    rag_doc.doc_id = doc_id
    rag_doc.material_id = material.id
    rag_doc.course_id = material.course_id
    rag_doc.lesson_id = material.lesson_id
    rag_doc.title = material.title
    rag_doc.description = material.description
    rag_doc.source_path = material.file_url
    rag_doc.source_type = result.get("source_type") or storage_path.suffix.lower().lstrip(".")
    rag_doc.file_hash = file_hash
    rag_doc.chunks_count = int(result.get("chunks", 0))
    rag_doc.total_tokens = int(result.get("total_tokens", 0))
    rag_doc.is_active = 1
    rag_doc.metadata_json = {
        "pages": result.get("pages"),
        "mime_type": material.mime_type,
        "uploaded_by": str(getattr(material, "uploaded_by", "") or "") or None,
    }

    if existing is None:
        db.add(rag_doc)
    db.commit()
    db.refresh(rag_doc)

    logger.info(
        "[RAGIngestion] Indexed material id=%s as doc_id=%s chunks=%s",
        material.id, doc_id, rag_doc.chunks_count,
    )
    return rag_doc


def remove_material_index(db: Session, material_id: uuid_lib.UUID) -> int:
    # Xóa dữ liệu RAG theo material (cả vector store và ORM row).
    """Remove the RAG document and chunks linked to a Material row."""
    material_id_str = str(material_id)

    # Delete from the vector store (and any cascaded chunks).
    deleted = 0
    try:
        from llm.rag.service import get_rag_service

        rag_service = get_rag_service(use_postgres=True, verbose=False)
        result = rag_service.delete_by_material(material_id_str)
        deleted = int(result.get("deleted", 0)) if result.get("status") == "success" else 0
    except Exception as exc:
        logger.warning("[RAGIngestion] Vector store delete failed for material %s: %s", material_id_str, exc)

    # Remove the ORM row (chunks cascade via FK).
    rag_doc = db.query(RAGDocument).filter(RAGDocument.material_id == material_id).first()
    if rag_doc:
        db.delete(rag_doc)
        db.commit()
        logger.info("[RAGIngestion] Removed RAGDocument material_id=%s doc_id=%s", material_id_str, rag_doc.doc_id)

    return max(deleted, 1 if rag_doc else 0)


def _remove_index_by_scope(db: Session, scope: str, value: uuid_lib.UUID) -> int:
    # Xóa RAG theo phạm vi (lesson/course) và trả về số lượng đã xóa.
    """Remove RAG documents/chunks for a lesson or course scope."""
    value_str = str(value)
    deleted = 0

    try:
        from llm.rag.service import get_rag_service

        rag_service = get_rag_service(use_postgres=True, verbose=False)
        if scope == "lesson":
            result = rag_service.delete_by_lesson(value_str)
        elif scope == "course":
            result = rag_service.delete_by_course(value_str)
        else:  # pragma: no cover - internal misuse guard
            raise ValueError(f"Unsupported RAG cleanup scope: {scope}")
        deleted = int(result.get("deleted", 0)) if result.get("status") == "success" else 0
    except Exception as exc:
        logger.warning("[RAGIngestion] Vector store delete failed for %s %s: %s", scope, value_str, exc)

    query = db.query(RAGDocument)
    if scope == "lesson":
        query = query.filter(RAGDocument.lesson_id == value)
    else:
        query = query.filter(RAGDocument.course_id == value)

    rag_docs = query.all()
    for rag_doc in rag_docs:
        db.delete(rag_doc)
    if rag_docs:
        db.commit()
        logger.info("[RAGIngestion] Removed %s RAGDocument row(s) for %s_id=%s", len(rag_docs), scope, value_str)

    return max(deleted, len(rag_docs))


def remove_lesson_index(db: Session, lesson_id: uuid_lib.UUID) -> int:
    # Xóa toàn bộ RAG của một buổi học.
    """Remove all RAG documents and chunks linked to a Lesson."""
    return _remove_index_by_scope(db, "lesson", lesson_id)


def remove_course_index(db: Session, course_id: uuid_lib.UUID) -> int:
    # Xóa toàn bộ RAG của một khóa học.
    """Remove all RAG documents and chunks linked to a Course."""
    return _remove_index_by_scope(db, "course", course_id)
