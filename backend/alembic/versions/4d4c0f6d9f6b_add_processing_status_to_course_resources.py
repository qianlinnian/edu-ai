"""add processing status to course resources

Revision ID: 4d4c0f6d9f6b
Revises: ce7d7666077c
Create Date: 2026-04-23 20:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4d4c0f6d9f6b"
down_revision: Union[str, None] = "ce7d7666077c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "course_resources",
        sa.Column("processing_status", sa.String(length=20), nullable=False, server_default="pending"),
    )
    op.add_column(
        "course_resources",
        sa.Column("processing_error", sa.Text(), nullable=True),
    )

    op.execute(
        """
        UPDATE course_resources
        SET processing_status = CASE
            WHEN is_processed THEN 'processed'
            ELSE 'pending'
        END
        """
    )

    op.alter_column("course_resources", "processing_status", server_default=None)


def downgrade() -> None:
    op.drop_column("course_resources", "processing_error")
    op.drop_column("course_resources", "processing_status")
