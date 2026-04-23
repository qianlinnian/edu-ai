"""change embedding dimension to 1024

Revision ID: 7a1f9a0e2b3c
Revises: 4d4c0f6d9f6b
Create Date: 2026-04-23 23:40:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "7a1f9a0e2b3c"
down_revision: Union[str, None] = "4d4c0f6d9f6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE knowledge_units ALTER COLUMN embedding TYPE vector(1024)")
    op.execute("ALTER TABLE resource_chunks ALTER COLUMN embedding TYPE vector(1024)")


def downgrade() -> None:
    op.execute("ALTER TABLE knowledge_units ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("ALTER TABLE resource_chunks ALTER COLUMN embedding TYPE vector(1536)")
