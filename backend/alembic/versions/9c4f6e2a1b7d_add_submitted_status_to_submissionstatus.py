"""add submitted status to submissionstatus

Revision ID: 9c4f6e2a1b7d
Revises: 7a1f9a0e2b3c
Create Date: 2026-06-28 00:00:00
"""

from alembic import op


revision = "9c4f6e2a1b7d"
down_revision = "7a1f9a0e2b3c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE submissionstatus ADD VALUE IF NOT EXISTS 'SUBMITTED'")


def downgrade() -> None:
    # PostgreSQL enums cannot drop a value in-place safely.
    pass
