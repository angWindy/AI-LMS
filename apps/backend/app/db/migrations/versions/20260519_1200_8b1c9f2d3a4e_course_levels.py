"""Require and constrain course level.

Revision ID: 8b1c9f2d3a4e
Revises: 20260508_1200_f6a7b8c9d0e1
Create Date: 2026-05-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b1c9f2d3a4e"
down_revision: Union[str, None] = "20260508_1200_f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_LEVEL_VALUES = (
    "primary",
    "lower_secondary",
    "upper_secondary",
    "higher_ed",
)


def upgrade() -> None:
    level_list = ", ".join(f"'{level}'" for level in _LEVEL_VALUES)
    op.execute(
        """
        UPDATE courses
        SET level = 'upper_secondary'
        WHERE level IS NULL
           OR BTRIM(level) = ''
           OR level NOT IN ({level_list})
        """.format(level_list=level_list)
    )

    op.alter_column(
        "courses",
        "level",
        existing_type=sa.String(length=50),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_courses_level",
        "courses",
        f"level IN ({level_list})",
    )


def downgrade() -> None:
    op.drop_constraint("ck_courses_level", "courses", type_="check")
    op.alter_column(
        "courses",
        "level",
        existing_type=sa.String(length=50),
        nullable=True,
    )
