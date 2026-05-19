"""Require academic course levels.

Revision ID: 8b1c9f2d3a4e
Revises: c3d4e5f6a7b8
Create Date: 2026-05-19 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision: str = "8b1c9f2d3a4e"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """Normalize existing course levels and require the column."""
    op.execute(
        """
        UPDATE courses
        SET level = CASE
            WHEN lower(trim(coalesce(level, ''))) IN ('elementary', 'primary', 'tieu_hoc', 'tieu hoc', 'tiểu học') THEN 'elementary'
            WHEN lower(trim(coalesce(level, ''))) IN ('middle_school', 'secondary', 'junior_high', 'thcs', 'trung hoc co so', 'trung học cơ sở') THEN 'middle_school'
            WHEN lower(trim(coalesce(level, ''))) IN ('high_school', 'senior_high', 'thpt', 'trung hoc pho thong', 'trung học phổ thông') THEN 'high_school'
            WHEN lower(trim(coalesce(level, ''))) IN ('higher_education', 'university', 'college', 'graduate', 'dai hoc va sau dai hoc', 'đại học và sau đại học') THEN 'higher_education'
            ELSE 'higher_education'
        END
        WHERE level IS NULL
           OR lower(trim(level)) NOT IN ('elementary', 'middle_school', 'high_school', 'higher_education')
        """
    )
    op.alter_column(
        "courses",
        "level",
        existing_type=sa.String(length=50),
        nullable=False,
        server_default="higher_education",
    )
    op.create_check_constraint(
        "ck_courses_level_valid",
        "courses",
        "level IN ('elementary', 'middle_school', 'high_school', 'higher_education')",
    )


def downgrade() -> None:
    """Allow course levels to be nullable again."""
    op.drop_constraint("ck_courses_level_valid", "courses", type_="check")
    op.alter_column(
        "courses",
        "level",
        existing_type=sa.String(length=50),
        nullable=True,
        server_default=None,
    )
