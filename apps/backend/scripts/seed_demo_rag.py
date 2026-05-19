"""Seed a demo course + lessons + RAG-indexed materials.

Creates / refreshes:

* User ``demo-instructor@example.com`` (Instructor)
* Course "T\u01b0 t\u01b0\u1edfng H\u1ed3 Ch\u00ed Minh" (slug ``tu-tuong-ho-chi-minh``)
* Two lessons:
    - Ch\u01b0\u01a1ng 1 \u2014 Ngu\u1ed3n g\u1ed1c, qu\u00e1 tr\u00ecnh h\u00ecnh th\u00e0nh \u2026
    - Ch\u01b0\u01a1ng 2 \u2014 T\u01b0 t\u01b0\u1edfng H\u1ed3 Ch\u00ed Minh v\u1ec1 v\u1ea5n \u0111\u1ec1 d\u00e2n t\u1ed9c \u2026
* Materials uploaded from ``llm/rag/data_sample/``:
    Course_Detail.pdf      \u2192 course-level material
    Lesson_1_Part_1.pdf    \u2192 Ch\u01b0\u01a1ng 1
    Lesson_1_Part_2.pdf    \u2192 Ch\u01b0\u01a1ng 1
    Lesson_2_Part_1.pdf    \u2192 Ch\u01b0\u01a1ng 2
    Lesson_2_Part_2.pdf    \u2192 Ch\u01b0\u01a1ng 2
    Lesson_2_Part_3.pdf    \u2192 Ch\u01b0\u01a1ng 2

Each Material is also indexed into the RAG vector store via
``app.services.rag_ingestion.index_material``.

Usage (from project root)::

    python -m apps.backend.scripts.seed_demo_rag
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import uuid
from pathlib import Path

# Make ``apps/backend`` importable when run as a plain script.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Host layout: <repo>/apps/backend/scripts/...
# Container layout: /app/scripts/... with /app/llm copied beside /app/app.
PROJECT_ROOT = BACKEND_DIR if (BACKEND_DIR / "llm").exists() else BACKEND_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env if dotenv is available.
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


from app.core.config import settings  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.course import Course, CourseLevel, CourseStatus  # noqa: E402
from app.models.lesson import Lesson  # noqa: E402
from app.models.material import Material, MaterialType  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.services.rag_ingestion import index_material, remove_material_index  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("seed_demo_rag")


# ---------------------------------------------------------------------------
# Demo data definition
# ---------------------------------------------------------------------------

DEMO_INSTRUCTOR_EMAIL = "demo-instructor@example.com"
DEMO_INSTRUCTOR_PASSWORD = "DemoInstructor123!"
DEMO_INSTRUCTOR_NAME = "Demo Instructor"

DEMO_COURSE_SLUG = "tu-tuong-ho-chi-minh"
DEMO_COURSE_TITLE = "T\u01b0 t\u01b0\u1edfng H\u1ed3 Ch\u00ed Minh"
DEMO_COURSE_SHORT = (
    "Kh\u00f3a h\u1ecdc m\u1eabu cho RAG: ngu\u1ed3n g\u1ed1c, qu\u00e1 tr\u00ecnh "
    "h\u00ecnh th\u00e0nh v\u00e0 c\u00e1c lu\u1eadn \u0111i\u1ec3m c\u1ed1t l\u00f5i."
)

DATA_SAMPLE_DIR = PROJECT_ROOT / "llm" / "rag" / "data_sample"

LESSON_1_TITLE = (
    "Ch\u01b0\u01a1ng 1: Ngu\u1ed3n g\u1ed1c, qu\u00e1 tr\u00ecnh h\u00ecnh th\u00e0nh "
    "v\u00e0 ph\u00e1t tri\u1ec3n \u0111\u1ed1i t\u01b0\u1ee3ng, nhi\u1ec7m v\u1ee5 v\u00e0 "
    "\u00fd ngh\u0129a h\u1ecdc t\u1eadp t\u01b0 t\u01b0\u1edfng H\u1ed3 Ch\u00ed Minh"
)
LESSON_2_TITLE = (
    "Ch\u01b0\u01a1ng 2: T\u01b0 t\u01b0\u1edfng H\u1ed3 Ch\u00ed Minh v\u1ec1 v\u1ea5n "
    "\u0111\u1ec1 d\u00e2n t\u1ed9c v\u00e0 c\u00e1ch m\u1ea1ng gi\u1ea3i ph\u00f3ng d\u00e2n t\u1ed9c"
)

# Ordered list of (filename, attach_to). attach_to is "course", "lesson1" or "lesson2".
ATTACHMENTS = [
    ("Course_Detail.pdf", "course"),
    ("Lesson_1_Part_1.pdf", "lesson1"),
    ("Lesson_1_Part_2.pdf", "lesson1"),
    ("Lesson_2_Part_1.pdf", "lesson2"),
    ("Lesson_2_Part_2.pdf", "lesson2"),
    ("Lesson_2_Part_3.pdf", "lesson2"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_or_create_instructor(db) -> User:
    user = db.query(User).filter(User.email == DEMO_INSTRUCTOR_EMAIL).first()
    if user:
        return user
    user = User(
        email=DEMO_INSTRUCTOR_EMAIL,
        password_hash=get_password_hash(DEMO_INSTRUCTOR_PASSWORD),
        full_name=DEMO_INSTRUCTOR_NAME,
        role=UserRole.INSTRUCTOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created instructor %s", user.email)
    return user


def _get_or_create_course(db, instructor: User) -> Course:
    course = db.query(Course).filter(Course.slug == DEMO_COURSE_SLUG).first()
    if course:
        course.instructor_id = instructor.id
        course.title = DEMO_COURSE_TITLE
        course.short_description = DEMO_COURSE_SHORT
        course.status = CourseStatus.PUBLISHED
        course.level = CourseLevel.HIGHER_ED
        db.commit()
        db.refresh(course)
        return course
    course = Course(
        instructor_id=instructor.id,
        title=DEMO_COURSE_TITLE,
        slug=DEMO_COURSE_SLUG,
        description=(
            "Kh\u00f3a h\u1ecdc m\u1eabu \u0111\u1ec3 ki\u1ec3m th\u1eed h\u1ec7 th\u1ed1ng "
            "RAG ti\u1ebfng Vi\u1ec7t v\u1edbi t\u00e0i li\u1ec7u th\u1ef1c t\u1ebf."
        ),
        short_description=DEMO_COURSE_SHORT,
        status=CourseStatus.PUBLISHED,
        language="vi",
        level=CourseLevel.HIGHER_ED,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    logger.info("Created course %s (id=%s)", course.title, course.id)
    return course


def _get_or_create_lesson(db, course: Course, title: str, order: int) -> Lesson:
    lesson = (
        db.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.title == title)
        .first()
    )
    if lesson:
        return lesson
    lesson = Lesson(
        course_id=course.id,
        title=title,
        order_index=order,
        is_published=True,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    logger.info("Created lesson #%s: %s (id=%s)", order, title[:60], lesson.id)
    return lesson


def _copy_pdf_into_storage(src: Path, course_id: uuid.UUID, lesson_id: uuid.UUID | None) -> tuple[str, int]:
    """Copy a sample PDF into the configured storage path and return (file_url, size)."""
    storage_root = Path(settings.STORAGE_PATH)
    if lesson_id is not None:
        sub = storage_root / "materials" / str(lesson_id)
    else:
        sub = storage_root / "materials" / "courses" / str(course_id)
    sub.mkdir(parents=True, exist_ok=True)
    dest = sub / f"{uuid.uuid4().hex[:16]}_{src.name}"
    shutil.copyfile(src, dest)
    relative = dest.relative_to(storage_root)
    return f"/storage/{relative.as_posix()}", dest.stat().st_size


def _attach_material(
    db,
    src: Path,
    course: Course,
    lesson: Lesson | None,
    title: str,
    order: int,
) -> Material:
    file_url, file_size = _copy_pdf_into_storage(src, course.id, lesson.id if lesson else None)
    material = Material(
        course_id=course.id,
        lesson_id=lesson.id if lesson else None,
        title=title,
        description=f"Demo seed: {src.name}",
        type=MaterialType.DOCUMENT,
        file_url=file_url,
        file_size=file_size,
        mime_type="application/pdf",
        order_index=order,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    logger.info(
        "Attached %s to %s (material_id=%s)",
        src.name, "course" if lesson is None else f"lesson '{lesson.title[:40]}\u2026'", material.id,
    )

    # Run RAG ingestion synchronously so we can report results.
    rag_doc = index_material(db, material)
    if rag_doc is not None:
        logger.info(
            "  \u2514\u2500 indexed: doc_id=%s chunks=%s tokens=%s",
            rag_doc.doc_id, rag_doc.chunks_count, rag_doc.total_tokens,
        )
    else:
        logger.warning("  \u2514\u2500 RAG indexing skipped/failed for %s", src.name)
    return material


def _purge_existing_materials(db, course: Course) -> None:
    """Remove all current materials of the demo course (and their RAG entries)."""
    materials = db.query(Material).filter(Material.course_id == course.id).all()
    for material in materials:
        try:
            remove_material_index(db, material.id)
        except Exception as exc:  # pragma: no cover - cleanup is best-effort
            logger.warning("Failed to remove RAG index for %s: %s", material.id, exc)
        if material.file_url and material.file_url.startswith("/storage/"):
            disk = Path(settings.STORAGE_PATH) / material.file_url.replace("/storage/", "", 1)
            try:
                if disk.exists():
                    disk.unlink()
            except OSError:
                pass
        db.delete(material)
    db.commit()
    if materials:
        logger.info("Purged %s existing material(s) from course", len(materials))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if not DATA_SAMPLE_DIR.exists():
        logger.error("data_sample directory missing: %s", DATA_SAMPLE_DIR)
        return 1

    missing = [name for name, _ in ATTACHMENTS if not (DATA_SAMPLE_DIR / name).exists()]
    if missing:
        logger.error("Missing PDFs in data_sample/: %s", ", ".join(missing))
        return 1

    db = SessionLocal()
    try:
        instructor = _get_or_create_instructor(db)
        course = _get_or_create_course(db, instructor)
        lesson1 = _get_or_create_lesson(db, course, LESSON_1_TITLE, order=1)
        lesson2 = _get_or_create_lesson(db, course, LESSON_2_TITLE, order=2)

        _purge_existing_materials(db, course)

        order_counter = {"course": 1, "lesson1": 1, "lesson2": 1}
        for filename, attach_to in ATTACHMENTS:
            src = DATA_SAMPLE_DIR / filename
            order = order_counter[attach_to]
            order_counter[attach_to] += 1
            target_lesson = None if attach_to == "course" else (lesson1 if attach_to == "lesson1" else lesson2)
            title = src.stem.replace("_", " ")
            _attach_material(db, src, course, target_lesson, title, order)

        logger.info("\u2705 Demo seed completed.")
        logger.info("   Course id  = %s", course.id)
        logger.info("   Lesson 1   = %s", lesson1.id)
        logger.info("   Lesson 2   = %s", lesson2.id)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
