"""Focused checks for classroom chatbot RAG behavior.

This script runs without PostgreSQL or an external LLM. It verifies:
1. Chatbot context assembly searches lesson documents first.
2. Course supplementary context is restricted to course-level documents.
3. InMemoryVectorStore respects ``course_only=True``.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_ROOT = PROJECT_ROOT / "apps" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.chatbot_service import ChatbotService, LMSChatScope  # noqa: E402
from llm.prompts.chatbot import build_lms_chatbot_prompt  # noqa: E402
from llm.rag.chunker import Chunk, ChunkType, Document  # noqa: E402
from llm.rag.vector_store import InMemoryVectorStore  # noqa: E402


errors: list[str] = []


def ok(message: str) -> None:
    print(f"  ✓ {message}")


def fail(message: str) -> None:
    errors.append(message)
    print(f"  ✗ {message}")


class FakeRAGService:
    """Small fake that records the requested retrieval scopes."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def search(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("lesson_id"):
            return {
                "status": "success",
                "results": [
                    {
                        "chunk_id": "lesson-chunk-1",
                        "document_title": "Lesson PDF",
                        "content": "Lesson-only fact: gradient descent updates weights using the learning rate.",
                        "page_number": 2,
                        "relevance": 0.91,
                    }
                ],
            }
        if kwargs.get("course_only"):
            return {
                "status": "success",
                "results": [
                    {
                        "chunk_id": "course-chunk-1",
                        "document_title": "Course Syllabus",
                        "content": "Course-level fact: this course studies applied machine learning.",
                        "page_number": 1,
                        "relevance": 0.78,
                    }
                ],
            }
        return {"status": "success", "results": []}


def test_chatbot_context_priority() -> None:
    fake_rag = FakeRAGService()
    service = ChatbotService.__new__(ChatbotService)
    service.rag_service = fake_rag

    scope = LMSChatScope(
        course_id=uuid.uuid4(),
        course_title="Machine Learning",
        lesson_id=uuid.uuid4(),
        lesson_title="Gradient Descent",
        has_lesson_rag_documents=True,
        has_course_rag_documents=True,
    )

    contexts = service._build_auto_rag_context(  # noqa: SLF001 - script-level invariant test
        db=None,
        question="learning rate dùng để làm gì?",
        scope=scope,
    )

    if len(contexts) == 2:
        ok("chatbot assembled lesson primary + course secondary contexts")
    else:
        fail(f"expected 2 context blocks, got {len(contexts)}")

    if contexts and contexts[0].startswith("[CONTEXT_CHINH_LESSON"):
        ok("lesson context is first and marked as primary")
    else:
        fail("lesson context is not first")

    if len(contexts) > 1 and contexts[1].startswith("[CONTEXT_PHU_COURSE"):
        ok("course context is marked as supplementary")
    else:
        fail("course context is not marked as supplementary")

    lesson_call = fake_rag.calls[0] if fake_rag.calls else {}
    course_call = fake_rag.calls[1] if len(fake_rag.calls) > 1 else {}
    if lesson_call.get("lesson_id") == str(scope.lesson_id):
        ok("lesson retrieval is scoped by lesson_id")
    else:
        fail("lesson retrieval did not include lesson_id")

    if course_call.get("course_only") is True:
        ok("course retrieval uses course_only=True")
    else:
        fail("course retrieval was not restricted to course-level documents")


def test_in_memory_course_only_filter() -> None:
    store = InMemoryVectorStore(verbose=False)
    course_id = str(uuid.uuid4())
    lesson_id = str(uuid.uuid4())

    course_doc = Document(
        id="course-doc",
        title="Course Doc",
        source_path="course.pdf",
        metadata={"course_id": course_id, "material_id": str(uuid.uuid4())},
        chunks=[
            Chunk(
                id="course-chunk",
                type=ChunkType.PARAGRAPH,
                content="Course-level retrieval content",
                page_number=1,
                embedding=[1.0, 0.0],
            )
        ],
    )
    lesson_doc = Document(
        id="lesson-doc",
        title="Lesson Doc",
        source_path="lesson.pdf",
        metadata={
            "course_id": course_id,
            "lesson_id": lesson_id,
            "material_id": str(uuid.uuid4()),
        },
        chunks=[
            Chunk(
                id="lesson-chunk",
                type=ChunkType.PARAGRAPH,
                content="Lesson-level retrieval content",
                page_number=1,
                embedding=[1.0, 0.0],
            )
        ],
    )

    store.add_chunks(course_doc.chunks, course_doc)
    store.add_chunks(lesson_doc.chunks, lesson_doc)

    hits = store.search([1.0, 0.0], top_k=5, course_id=course_id, course_only=True)
    hit_ids = {hit["doc_id"] for hit in hits}
    if hit_ids == {"course-doc"}:
        ok("course_only search excludes lesson documents")
    else:
        fail(f"course_only returned unexpected docs: {sorted(hit_ids)}")


def test_prompt_allows_inference_without_full_context() -> None:
    prompt = build_lms_chatbot_prompt("Tư tưởng Hồ Chí Minh", "Chương 1: Nguồn gốc")
    required_phrases = [
        "không được trả lời kiểu xin lỗi",
        "không nói 'không đủ context'",
        "tri thức nền của bộ môn",
        "suy luận từ tên khóa học, tên bài học",
    ]
    if all(phrase in prompt.lower() for phrase in required_phrases):
        ok("prompt explicitly allows inference when context is incomplete")
    else:
        fail("prompt does not clearly instruct fallback inference")


def main() -> int:
    print("\nCHATBOT CLASSROOM RAG TEST")
    print("=" * 60)
    test_chatbot_context_priority()
    test_in_memory_course_only_filter()
    test_prompt_allows_inference_without_full_context()

    if errors:
        print("\nFAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
