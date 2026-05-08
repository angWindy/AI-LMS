"""slide deck pdf metadata

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-05-08 13:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("slide_decks", sa.Column("pdf_url", sa.String(length=500), nullable=True))
    op.add_column("slide_decks", sa.Column("pdf_file_size", sa.Integer(), nullable=True))
    op.add_column("slide_decks", sa.Column("pdf_mime_type", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("slide_decks", "pdf_mime_type")
    op.drop_column("slide_decks", "pdf_file_size")
    op.drop_column("slide_decks", "pdf_url")
