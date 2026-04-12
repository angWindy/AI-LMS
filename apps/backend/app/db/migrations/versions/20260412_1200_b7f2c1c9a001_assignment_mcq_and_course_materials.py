"""assignment mcq and course materials

Revision ID: b7f2c1c9a001
Revises: 299a7a8507ce
Create Date: 2026-04-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7f2c1c9a001"
down_revision: Union[str, None] = "299a7a8507ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Materials: allow course-level records.
    op.add_column("materials", sa.Column("course_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_materials_course_id"), "materials", ["course_id"], unique=False)
    op.create_foreign_key(
        "fk_materials_course_id_courses",
        "materials",
        "courses",
        ["course_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.execute(
        """
        UPDATE materials m
        SET course_id = l.course_id
        FROM lessons l
        WHERE m.lesson_id = l.id AND m.course_id IS NULL
        """
    )

    op.alter_column("materials", "lesson_id", existing_type=sa.UUID(), nullable=True)
    op.create_check_constraint(
        "ck_material_course_or_lesson",
        "materials",
        "(course_id IS NOT NULL OR lesson_id IS NOT NULL)",
    )

    # Assignments: simplify assignment table and add question/option tables.
    op.drop_column("assignments", "description")
    op.drop_column("assignments", "instructions")
    op.drop_column("assignments", "due_date")
    op.drop_column("assignments", "max_score")
    op.drop_column("assignments", "allow_late_submission")
    op.drop_column("assignments", "late_penalty_percent")

    op.create_table(
        "assignment_questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("assignment_id", sa.UUID(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assignment_questions_assignment_id"), "assignment_questions", ["assignment_id"], unique=False)

    op.create_table(
        "assignment_options",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["assignment_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assignment_options_question_id"), "assignment_options", ["question_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_assignment_options_question_id"), table_name="assignment_options")
    op.drop_table("assignment_options")

    op.drop_index(op.f("ix_assignment_questions_assignment_id"), table_name="assignment_questions")
    op.drop_table("assignment_questions")

    op.add_column("assignments", sa.Column("late_penalty_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"))
    op.add_column("assignments", sa.Column("allow_late_submission", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("assignments", sa.Column("max_score", sa.Numeric(precision=5, scale=2), nullable=False, server_default="100"))
    op.add_column("assignments", sa.Column("due_date", sa.DateTime(), nullable=True))
    op.add_column("assignments", sa.Column("instructions", sa.Text(), nullable=True))
    op.add_column("assignments", sa.Column("description", sa.Text(), nullable=False, server_default=""))

    op.drop_constraint("ck_material_course_or_lesson", "materials", type_="check")
    op.alter_column("materials", "lesson_id", existing_type=sa.UUID(), nullable=False)
    op.drop_constraint("fk_materials_course_id_courses", "materials", type_="foreignkey")
    op.drop_index(op.f("ix_materials_course_id"), table_name="materials")
    op.drop_column("materials", "course_id")
