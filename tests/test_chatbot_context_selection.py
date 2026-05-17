import base64
from pathlib import Path
import sys
import uuid
from types import SimpleNamespace

# ruff: noqa: E402

BACKEND_PATH = Path(__file__).resolve().parents[1] / "apps" / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.services.chatbot_service import ChatbotService, LMSChatScope
from llm.models import ChatMessage, ContextTrace
from llm.workflows.chatbot import ChatbotResult


class _FakeDB:
    def add(self, value):
        _ = value

    def commit(self):
        pass


class _CapturingWorkflow:
    def __init__(self):
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        return ChatbotResult(
            answer="ok",
            provider="test",
            model="test-model",
            finish_reason="stop",
            usage={"total_tokens": 1},
            messages=[
                ChatMessage(role="system", content=""),
                ChatMessage(role="user", content=kwargs["question"]),
                ChatMessage(role="assistant", content="ok"),
            ],
            context=ContextTrace(
                rag_context=list(kwargs.get("rag_context") or []),
                image_contexts=list(kwargs.get("image_contexts") or []),
                conversation_history=list(
                    kwargs.get("conversation_history_context") or []
                ),
                merged_context=None,
            ),
        )


class _TestChatbotService(ChatbotService):
    def __init__(self, workflow, history=None):
        super().__init__(workflow=workflow)
        self.history = list(history or [])
        self.auto_rag_called = False

    def _resolve_lms_scope(self, db, course_id, lesson_id):
        _ = db, course_id, lesson_id
        return LMSChatScope(
            course_id=uuid.uuid4(),
            course_title="AI Course",
            lesson_id=uuid.uuid4(),
            lesson_title="Vision Lesson",
            has_lesson_rag_documents=True,
            has_course_rag_documents=True,
        )

    def _get_or_create_conversation(
        self,
        db,
        user_id,
        question,
        conversation_id,
        conversation_title,
        course_id,
        lesson_id,
        reuse_existing=True,
    ):
        _ = db, user_id, question, conversation_id, course_id, lesson_id, reuse_existing
        return SimpleNamespace(
            id=uuid.uuid4(),
            title=conversation_title or "Test chat",
            updated_at=None,
        )

    def _load_conversation_history(self, db, conversation_id):
        _ = db, conversation_id
        return self.history

    def _build_auto_rag_context(self, db, question, scope):
        _ = db, question, scope
        self.auto_rag_called = True
        return ["PRIMARY_LESSON_CONTEXT: retrieved material"]


def _image_payload():
    return {
        "mime_type": "image/png",
        "data_base64": base64.b64encode(b"fake-image").decode("ascii"),
        "description": "A teaching slide screenshot",
        "source": "screen_capture",
    }


def test_chatbot_image_rule_disables_rag_and_context_docs():
    workflow = _CapturingWorkflow()
    service = _TestChatbotService(workflow=workflow)

    service.ask(
        db=_FakeDB(),
        user_id=uuid.uuid4(),
        question="Cái này đang nói về gì?",
        context_docs=["MANUAL_RAG_CONTEXT: should not be used"],
        teaching_images=[_image_payload()],
    )

    call = workflow.calls[0]
    assert service.auto_rag_called is False
    assert call["rag_context"] == []
    assert len(call["images"]) == 1
    assert call["image_contexts"]


def test_chatbot_uses_rag_when_image_rule_does_not_match():
    workflow = _CapturingWorkflow()
    service = _TestChatbotService(workflow=workflow)

    service.ask(
        db=_FakeDB(),
        user_id=uuid.uuid4(),
        question="Khái niệm chính của bài học là gì?",
        context_docs=["MANUAL_CONTEXT"],
        teaching_images=[_image_payload()],
    )

    call = workflow.calls[0]
    assert service.auto_rag_called is True
    assert call["rag_context"] == [
        "PRIMARY_LESSON_CONTEXT: retrieved material",
        "MANUAL_CONTEXT",
    ]
    assert call["images"] == []
    assert call["image_contexts"] == []


def test_chatbot_passes_recent_history_as_context():
    workflow = _CapturingWorkflow()
    service = _TestChatbotService(
        workflow=workflow,
        history=[
            ChatMessage(role="user", content="Bài trước nói về supervised learning."),
            ChatMessage(role="assistant", content="Đúng, có nhãn dữ liệu."),
        ],
    )

    service.ask(
        db=_FakeDB(),
        user_id=uuid.uuid4(),
        question="Nó khác unsupervised learning thế nào?",
    )

    history_context = workflow.calls[0]["conversation_history_context"]
    assert len(history_context) == 1
    assert "Learner: Bài trước nói về supervised learning." in history_context[0]
    assert "Assistant: Đúng, có nhãn dữ liệu." in history_context[0]
