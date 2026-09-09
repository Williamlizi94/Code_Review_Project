"""Reconcile metadata column names created by older development migrations.

Revision ID: 003
Revises: 002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Some early development databases used the Python attribute name as the
    # physical column name. The current ORM intentionally exposes
    # ``extra_metadata`` while mapping it to a database column named ``metadata``.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'review_issues' AND column_name = 'extra_metadata'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'review_issues' AND column_name = 'metadata'
            ) THEN
                ALTER TABLE review_issues RENAME COLUMN extra_metadata TO metadata;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'knowledge_chunks' AND column_name = 'extra_metadata'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'knowledge_chunks' AND column_name = 'metadata'
            ) THEN
                ALTER TABLE knowledge_chunks RENAME COLUMN extra_metadata TO metadata;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # This migration normalizes legacy schemas to the canonical schema already
    # expected by revision 001, so reversing the column names would break 002.
    pass
