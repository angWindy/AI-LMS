"""Tests for slide PDF rendering."""
from pathlib import Path
import sys
import uuid


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "apps" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402
from app.services.slide_generator_service import SlideGeneratorService  # noqa: E402


def test_slide_generator_renders_pdf(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path))

    service = SlideGeneratorService.__new__(SlideGeneratorService)
    slide_deck_id = uuid.uuid4()
    lesson_id = uuid.uuid4()
    pdf_info = service.render_pdf(
        slides_json={
            "document_type": "slides",
            "title": "Bài giảng thử nghiệm",
            "slides": [
                {
                    "id": 1,
                    "slide_type": "title",
                    "title": "Tổng quan",
                    "content": ["Mục tiêu học tập", "Khái niệm chính"],
                    "speaker_notes": "Giới thiệu mục tiêu của bài học.",
                    "source_sections": [1],
                }
            ],
        },
        lesson_id=lesson_id,
        slide_deck_id=slide_deck_id,
    )

    pdf_path = tmp_path / pdf_info["pdf_url"].replace("/storage/", "")
    assert pdf_info["pdf_mime_type"] == "application/pdf"
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
