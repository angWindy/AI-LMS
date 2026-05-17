"""tests and submission answers

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-17 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


assignment_type = postgresql.ENUM("PRACTICE", "TEST", name="assignmenttype")
assignment_question_type = postgresql.ENUM(
    "MULTIPLE_CHOICE",
    "ESSAY",
    name="assignmentquestiontype",
)
assignment_type_column = postgresql.ENUM(
    "PRACTICE",
    "TEST",
    name="assignmenttype",
    create_type=False,
)
assignment_question_type_column = postgresql.ENUM(
    "MULTIPLE_CHOICE",
    "ESSAY",
    name="assignmentquestiontype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    assignment_type.create(bind, checkfirst=True)
    assignment_question_type.create(bind, checkfirst=True)

    op.add_column(
        "assignments",
        sa.Column(
            "assignment_type",
            assignment_type_column,
            nullable=False,
            server_default="PRACTICE",
        ),
    )
    op.create_index(op.f("ix_assignments_assignment_type"), "assignments", ["assignment_type"], unique=False)

    op.add_column(
        "assignment_questions",
        sa.Column(
            "question_type",
            assignment_question_type_column,
            nullable=False,
            server_default="MULTIPLE_CHOICE",
        ),
    )
    op.add_column("assignment_questions", sa.Column("correct_answer_text", sa.Text(), nullable=True))
    op.create_index(op.f("ix_assignment_questions_question_type"), "assignment_questions", ["question_type"], unique=False)

    op.create_table(
        "assignment_lesson_scopes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("assignment_id", sa.UUID(), nullable=False),
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assignment_lesson_scopes_assignment_id"), "assignment_lesson_scopes", ["assignment_id"], unique=False)
    op.create_index(op.f("ix_assignment_lesson_scopes_lesson_id"), "assignment_lesson_scopes", ["lesson_id"], unique=False)

    op.create_table(
        "submission_answers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("submission_id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("selected_option_id", sa.UUID(), nullable=True),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("correct_answer_text", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["question_id"], ["assignment_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["selected_option_id"], ["assignment_options.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_submission_answers_submission_id"), "submission_answers", ["submission_id"], unique=False)
    op.create_index(op.f("ix_submission_answers_question_id"), "submission_answers", ["question_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_submission_answers_question_id"), table_name="submission_answers")
    op.drop_index(op.f("ix_submission_answers_submission_id"), table_name="submission_answers")
    op.drop_table("submission_answers")

    op.drop_index(op.f("ix_assignment_lesson_scopes_lesson_id"), table_name="assignment_lesson_scopes")
    op.drop_index(op.f("ix_assignment_lesson_scopes_assignment_id"), table_name="assignment_lesson_scopes")
    op.drop_table("assignment_lesson_scopes")

    op.drop_index(op.f("ix_assignment_questions_question_type"), table_name="assignment_questions")
    op.drop_column("assignment_questions", "correct_answer_text")
    op.drop_column("assignment_questions", "question_type")

    op.drop_index(op.f("ix_assignments_assignment_type"), table_name="assignments")
    op.drop_column("assignments", "assignment_type")

    bind = op.get_bind()
    assignment_question_type.drop(bind, checkfirst=True)
    assignment_type.drop(bind, checkfirst=True)
