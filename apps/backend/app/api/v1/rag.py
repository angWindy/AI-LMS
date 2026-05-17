"""RAG API routes for LMS."""

import logging
import time
import uuid
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.rag import RAGDocument, RAGChunk, RAGSearchSession, RAGSearchResult
from app.schemas.rag import (
    RAGSearchRequest,
    RAGSearchResponse,
    RAGChunkResponse,
    RAGDocumentResponse,
    RAGIngestionResponse,
    RAGStatsResponse,
)
from llm.rag.service import get_rag_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/upload", response_model=RAGIngestionResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    course_id: Optional[uuid.UUID] = None,
    lesson_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RAGIngestionResponse:
    """Upload a document directly to the RAG store (admin / instructor side-channel).

    For Teacher uploads via the regular Material endpoints, ingestion happens
    automatically; this endpoint is for ad-hoc / testing usage.
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        doc_title = title or Path(file.filename or "Untitled").stem
        doc_id = f"upload_{uuid.uuid4().hex[:16]}"

        rag_service = get_rag_service(use_postgres=True, verbose=False)
        result = rag_service.ingest_document(
            file_path=tmp_path,
            document_id=doc_id,
            course_id=str(course_id) if course_id else None,
            lesson_id=str(lesson_id) if lesson_id else None,
            uploaded_by=str(current_user.id),
            title=doc_title,
        )

        if result["status"] != "success":
            logger.error("[RAG API] Ingestion failed: %s", result.get("error"))
            raise HTTPException(status_code=400, detail=result.get("error", "Ingestion failed"))

        rag_doc = db.query(RAGDocument).filter(RAGDocument.doc_id == result["document_id"]).first()
        if rag_doc is None:
            rag_doc = RAGDocument(doc_id=result["document_id"])
            db.add(rag_doc)
        rag_doc.title = doc_title
        rag_doc.source_path = file.filename
        rag_doc.source_type = result.get("source_type", suffix.lstrip("."))
        rag_doc.course_id = course_id
        rag_doc.lesson_id = lesson_id
        rag_doc.uploaded_by = current_user.id
        rag_doc.chunks_count = result["chunks"]
        rag_doc.total_tokens = result["total_tokens"]
        rag_doc.metadata_json = {"original_filename": file.filename}
        db.commit()

        return RAGIngestionResponse(
            status="success",
            document_id=result["document_id"],
            title=doc_title,
            pages=result["pages"],
            chunks=result["chunks"],
            total_tokens=result["total_tokens"],
            message=result["message"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG API] Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/search", response_model=RAGSearchResponse)
async def search(
    request: RAGSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RAGSearchResponse:
    """Search the indexed RAG content (optionally scoped to a course/lesson)."""
    try:
        start_time = time.time()

        rag_service = get_rag_service(use_postgres=True, verbose=False)
        result = rag_service.search(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
            course_id=str(request.course_id) if request.course_id else None,
            lesson_id=str(request.lesson_id) if request.lesson_id else None,
        )

        execution_time = time.time() - start_time

        if result["status"] != "success":
            logger.warning("[RAG API] Search failed: %s", result.get("error"))
            raise HTTPException(status_code=400, detail=result.get("error", "Search failed"))

        # Persist search session + ranked results for analytics.
        search_session = RAGSearchSession(
            user_id=current_user.id,
            course_id=request.course_id,
            lesson_id=request.lesson_id,
            query=request.query,
            results_count=len(result["results"]),
            search_duration_ms=int(execution_time * 1000),
        )
        db.add(search_session)
        db.flush()

        for rank, res in enumerate(result["results"], 1):
            db.add(RAGSearchResult(
                session_id=search_session.id,
                chunk_id=res.get("chunk_id", ""),
                relevance_score=res.get("relevance", 0.0),
                rank=rank,
            ))
        db.commit()

        logger.info(
            "[RAG API] Search completed: %s results in %.2fs (course=%s lesson=%s)",
            len(result["results"]), execution_time,
            request.course_id, request.lesson_id,
        )

        return RAGSearchResponse(
            status="success",
            query=request.query,
            results_count=len(result["results"]),
            results=[
                RAGChunkResponse(
                    chunk_id=res["chunk_id"],
                    content=res["content"][:500],
                    page_number=res.get("page_number"),
                    chunk_type="reference",
                    tokens_count=0,
                    relevance=res["relevance"],
                )
                for res in result["results"]
            ],
            execution_time_ms=execution_time * 1000,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG API] Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[RAGDocumentResponse])
async def list_documents(
    course_id: Optional[uuid.UUID] = Query(None),
    lesson_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RAGDocumentResponse]:
    """List all RAG documents (optionally filter by course / lesson)."""
    try:
        query = db.query(RAGDocument).filter(RAGDocument.is_active == 1)
        if course_id:
            query = query.filter(RAGDocument.course_id == course_id)
        if lesson_id:
            query = query.filter(RAGDocument.lesson_id == lesson_id)

        documents = query.order_by(RAGDocument.created_at.desc()).all()
        
        return [
            RAGDocumentResponse(
                doc_id=doc.doc_id,
                title=doc.title or "Untitled",
                description=doc.description,
                source_type=doc.source_type,
                chunks_count=doc.chunks_count,
                total_tokens=doc.total_tokens,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"[RAG API] List documents error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a RAG document.
    
    Args:
        doc_id: Document ID to delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success response
    """
    try:
        # Get document from DB
        doc = db.query(RAGDocument).filter(RAGDocument.doc_id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from vector store
        rag_service = get_rag_service(use_postgres=True, verbose=False)
        rag_service.delete_document(doc_id)
        
        # Mark as inactive in DB
        doc.is_active = 0
        db.commit()
        
        logger.info(f"[RAG API] Document deleted: {doc_id}")
        
        return {"status": "success", "message": f"Document {doc_id} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG API] Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=RAGStatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RAGStatsResponse:
    """Get RAG system statistics.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Statistics
    """
    try:
        # Get counts from database
        total_docs = db.query(RAGDocument).filter(RAGDocument.is_active == 1).count()
        total_chunks = db.query(RAGChunk).count()
        total_tokens = db.query(func.sum(RAGDocument.total_tokens)).scalar() or 0
        search_count = db.query(RAGSearchSession).count()
        
        # Get average relevance from search results
        avg_relevance = db.query(func.avg(RAGSearchResult.relevance_score)).scalar() or 0.0
        
        return RAGStatsResponse(
            total_documents=total_docs,
            total_chunks=total_chunks,
            total_tokens=int(total_tokens),
            search_count=search_count,
            avg_relevance=float(avg_relevance),
            system_status="ready",
        )
        
    except Exception as e:
        logger.error(f"[RAG API] Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
