"""question bank tables and question metadata

Revision ID: e4f5a6b7c8d9
Revises: c1d2e3f4a5b6
Create Date: 2026-05-07 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


question_difficulty = postgresql.ENUM("EASY", "MEDIUM", "HARD", name="questiondifficulty")
question_purpose_type = postgresql.ENUM("PRACTICE", "ASSESSMENT", "SHARED", name="questionpurposetype")
question_difficulty_column = postgresql.ENUM(
    "EASY",
    "MEDIUM",
    "HARD",
    name="questiondifficulty",
    create_type=False,
)
question_purpose_type_column = postgresql.ENUM(
    "PRACTICE",
    "ASSESSMENT",
    "SHARED",
    name="questionpurposetype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    question_difficulty.create(bind, checkfirst=True)
    question_purpose_type.create(bind, checkfirst=True)

    op.add_column(
        "assignment_questions",
        sa.Column(
            "difficulty",
            question_difficulty_column,
            nullable=False,
            server_default="EASY",
        ),
    )
    op.add_column(
        "assignment_questions",
        sa.Column(
            "purpose_type",
            question_purpose_type_column,
            nullable=False,
            server_default="SHARED",
        ),
    )
    op.create_index(op.f("ix_assignment_questions_difficulty"), "assignment_questions", ["difficulty"], unique=False)
    op.create_index(op.f("ix_assignment_questions_purpose_type"), "assignment_questions", ["purpose_type"], unique=False)

    op.create_table(
        "question_bank_questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("lesson_id", sa.UUID(), nullable=True),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("difficulty", question_difficulty_column, nullable=False, server_default="EASY"),
        sa.Column("purpose_type", question_purpose_type_column, nullable=False, server_default="SHARED"),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_bank_questions_course_id"), "question_bank_questions", ["course_id"], unique=False)
    op.create_index(op.f("ix_question_bank_questions_lesson_id"), "question_bank_questions", ["lesson_id"], unique=False)
    op.create_index(op.f("ix_question_bank_questions_difficulty"), "question_bank_questions", ["difficulty"], unique=False)
    op.create_index(op.f("ix_question_bank_questions_purpose_type"), "question_bank_questions", ["purpose_type"], unique=False)

    op.create_table(
        "question_bank_options",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["question_bank_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_bank_options_question_id"), "question_bank_options", ["question_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_question_bank_options_question_id"), table_name="question_bank_options")
    op.drop_table("question_bank_options")

    op.drop_index(op.f("ix_question_bank_questions_purpose_type"), table_name="question_bank_questions")
    op.drop_index(op.f("ix_question_bank_questions_difficulty"), table_name="question_bank_questions")
    op.drop_index(op.f("ix_question_bank_questions_lesson_id"), table_name="question_bank_questions")
    op.drop_index(op.f("ix_question_bank_questions_course_id"), table_name="question_bank_questions")
    op.drop_table("question_bank_questions")

    op.drop_index(op.f("ix_assignment_questions_purpose_type"), table_name="assignment_questions")
    op.drop_index(op.f("ix_assignment_questions_difficulty"), table_name="assignment_questions")
    op.drop_column("assignment_questions", "purpose_type")
    op.drop_column("assignment_questions", "difficulty")

    bind = op.get_bind()
    question_purpose_type.drop(bind, checkfirst=True)
    question_difficulty.drop(bind, checkfirst=True)
