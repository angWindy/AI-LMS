"""End-to-end test for the LMS \u2194 RAG integration.

This test exercises the full hierarchy without a running PostgreSQL instance:

    Course
      \u2514\u2500 Lesson
           \u2514\u2500 Material (PDF)
                \u2514\u2500 RAGDocument
                     \u2514\u2500 RAGChunk[]

Verifies:
1.  Ingestion: 1 RAG document is created per indexed PDF, carrying the
    course/lesson/material UUIDs.
2.  Course-scoped search returns only chunks from that course.
3.  Lesson-scoped search returns only chunks from that lesson.
4.  Deleting a material cascades to its RAG document.
5.  Deleting a lesson removes its RAG documents.
6.  Deleting a course removes everything attached to it.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional .env load.
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from llm.rag.service import RAGService, reset_rag_service  # noqa: E402
from llm.rag.vector_store import InMemoryVectorStore  # noqa: E402


# ---------------------------------------------------------------------------
# Test harness output helpers
# ---------------------------------------------------------------------------

errors: list[str] = []


def ok(msg: str) -> None:
    print(f"  \u2713 {msg}")


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"  \u2717 {msg}")


def warn(msg: str) -> None:
    print(f"  \u26a0 {msg}")


def sec(title: str) -> None:
    print(f"\n[{title}]")
    print("-" * 60)


# ---------------------------------------------------------------------------
# Mock embedder so the test runs without an API key.
# ---------------------------------------------------------------------------

class _DeterministicMockEmbedder:
    """Cheap, hash-based embedder used purely for invariant tests."""

    embedding_dimension = 3072

    def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        import hashlib
        import math

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:4], "big") / 2**32
        vec = [math.cos(seed + i * 0.001) for i in range(self.embedding_dimension)]
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_text(query, "RETRIEVAL_QUERY")

    def embed_chunks(self, chunks, task_type: str = "RETRIEVAL_DOCUMENT"):
        for chunk in chunks:
            if chunk.metadata.get("is_structural"):
                continue
            chunk.embedding = self.embed_text(chunk.content, task_type)
        return chunks

    def embed_document(self, document):
        document.chunks = self.embed_chunks(document.chunks)
        return document


# ---------------------------------------------------------------------------
# Test fixture: course / lesson / material UUIDs
# ---------------------------------------------------------------------------

DATA_SAMPLE = PROJECT_ROOT / "llm" / "rag" / "data_sample"

COURSE_ID = uuid.uuid4()
LESSON_1_ID = uuid.uuid4()
LESSON_2_ID = uuid.uuid4()
USER_ID = uuid.uuid4()

PLAN = [
    # (filename, attach_to, material_id)
    ("Course_Detail.pdf", None,         uuid.uuid4()),  # course-level
    ("Lesson_1_Part_1.pdf", LESSON_1_ID, uuid.uuid4()),
    ("Lesson_1_Part_2.pdf", LESSON_1_ID, uuid.uuid4()),
    ("Lesson_2_Part_1.pdf", LESSON_2_ID, uuid.uuid4()),
    ("Lesson_2_Part_2.pdf", LESSON_2_ID, uuid.uuid4()),
    ("Lesson_2_Part_3.pdf", LESSON_2_ID, uuid.uuid4()),
]


def main() -> int:
    if not DATA_SAMPLE.exists():
        fail(f"data_sample not found at {DATA_SAMPLE}")
        return 1

    # Always rebuild the singleton with our mock dependencies.
    reset_rag_service()
    store = InMemoryVectorStore(verbose=False)
    embedder = _DeterministicMockEmbedder()
    service = RAGService(vector_store=store, embedding_service=embedder, verbose=False)

    sec("STAGE 1 \u00b7 Ingest 6 PDFs into course / lessons")
    ingested: dict[uuid.UUID, dict] = {}
    for filename, lesson_id, material_id in PLAN:
        path = DATA_SAMPLE / filename
        if not path.exists():
            fail(f"missing file: {filename}")
            continue
        result = service.ingest_pdf(
            pdf_path=path,
            document_id=f"material_{material_id}",
            course_id=str(COURSE_ID),
            lesson_id=str(lesson_id) if lesson_id else None,
            material_id=str(material_id),
            uploaded_by=str(USER_ID),
            title=path.stem.replace("_", " "),
        )
        if result.get("status") != "success":
            fail(f"ingest failed for {filename}: {result.get('error')}")
            continue
        ingested[material_id] = result
        scope = "course" if lesson_id is None else f"lesson={str(lesson_id)[:8]}"
        ok(f"{filename:<22s} \u2192 chunks={result['chunks']:>3d}  scope={scope}")

    if len(ingested) != len(PLAN):
        fail(f"ingested {len(ingested)}/{len(PLAN)} expected")

    # ------------------------------------------------------------------
    sec("STAGE 2 \u00b7 Hierarchy invariants")
    docs = store.documents
    if len(docs) == len(PLAN):
        ok(f"vector store has {len(docs)} documents (matches plan)")
    else:
        fail(f"vector store has {len(docs)} docs, expected {len(PLAN)}")

    for material_id in (m for _, _, m in PLAN):
        doc = next((d for d in docs.values() if d["material_id"] == str(material_id)), None)
        if doc is None:
            fail(f"no doc for material_id={material_id}")
            continue
        if doc["course_id"] != str(COURSE_ID):
            fail(f"doc {doc['id']} course_id mismatch")
            continue
    ok("every doc carries the right course_id / material_id")

    # ------------------------------------------------------------------
    sec("STAGE 3 \u00b7 Course-scoped search")
    res = service.search("ngu\u1ed3n g\u1ed1c h\u00ecnh th\u00e0nh", top_k=5, course_id=str(COURSE_ID))
    if res["status"] == "success" and res["results_count"] > 0:
        ok(f"course-scope returned {res['results_count']} hits")
        if all(r["course_id"] == str(COURSE_ID) for r in res["results"]):
            ok("all hits belong to the demo course")
        else:
            fail("course-scope leakage: foreign course_id seen in results")
    else:
        fail(f"course search returned 0 results: {res}")

    # ------------------------------------------------------------------
    sec("STAGE 4 \u00b7 Lesson-scoped search (Ch\u01b0\u01a1ng 2)")
    res = service.search(
        "c\u00e1ch m\u1ea1ng gi\u1ea3i ph\u00f3ng d\u00e2n t\u1ed9c",
        top_k=5, lesson_id=str(LESSON_2_ID),
    )
    if res["status"] == "success" and res["results_count"] > 0:
        ok(f"lesson-scope returned {res['results_count']} hits")
        if all(r["lesson_id"] == str(LESSON_2_ID) for r in res["results"]):
            ok("every hit is from Ch\u01b0\u01a1ng 2")
        else:
            fail("lesson-scope leakage: foreign lesson_id seen in results")
    else:
        fail(f"lesson search returned 0 results: {res}")

    # Negative test: must not return Lesson 1 / course-level docs.
    bad = [r for r in res.get("results", []) if r["lesson_id"] != str(LESSON_2_ID)]
    if not bad:
        ok("no chunks from Ch\u01b0\u01a1ng 1 / course-level material in lesson scope")
    else:
        fail(f"{len(bad)} chunks leaked from outside Ch\u01b0\u01a1ng 2")

    # ------------------------------------------------------------------
    sec("STAGE 5 \u00b7 Material delete cascade")
    target_material_id = PLAN[1][2]  # first lesson-1 material
    deleted = service.delete_by_material(str(target_material_id))
    if deleted.get("deleted") == 1:
        ok(f"delete_by_material removed 1 doc for material_id={str(target_material_id)[:8]}\u2026")
    else:
        fail(f"delete_by_material unexpected result: {deleted}")
    if not any(d["material_id"] == str(target_material_id) for d in store.documents.values()):
        ok("vector store no longer references that material")
    else:
        fail("doc still present after delete")

    # ------------------------------------------------------------------
    sec("STAGE 6 \u00b7 Lesson delete cascade")
    deleted = service.delete_by_lesson(str(LESSON_2_ID))
    if deleted.get("status") == "success" and deleted.get("deleted", 0) >= 1:
        ok(f"delete_by_lesson removed {deleted['deleted']} doc(s) for Ch\u01b0\u01a1ng 2")
    else:
        fail(f"delete_by_lesson unexpected result: {deleted}")
    leftovers = [d for d in store.documents.values() if d["lesson_id"] == str(LESSON_2_ID)]
    if not leftovers:
        ok("no Ch\u01b0\u01a1ng 2 docs remain")
    else:
        fail(f"{len(leftovers)} Ch\u01b0\u01a1ng 2 docs still present")

    # ------------------------------------------------------------------
    sec("STAGE 7 \u00b7 Course delete cascade")
    before = len(store.documents)
    deleted = service.delete_by_course(str(COURSE_ID))
    if deleted.get("status") == "success":
        ok(f"delete_by_course removed {deleted['deleted']} remaining doc(s) (was {before})")
    else:
        fail(f"delete_by_course failed: {deleted}")
    if not store.documents:
        ok("vector store fully empty")
    else:
        fail(f"{len(store.documents)} docs leaked after course delete")

    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    if errors:
        print(f"  FAILED: {len(errors)} error(s)")
        for e in errors:
            print(f"    \u2717 {e}")
        return 1
    print("  ALL STAGES PASSED \u2713")
    print()
    print("  Verified:")
    print("    \u2022 Course \u2192 Lesson \u2192 Material \u2192 RAGDocument \u2192 RAGChunk hierarchy")
    print("    \u2022 Course-scoped search isolation")
    print("    \u2022 Lesson-scoped search isolation")
    print("    \u2022 Cascade delete: material \u2192 lesson \u2192 course")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
