"""Create the empty foundation baseline.

Revision ID: 0001_foundation
Revises:
Create Date: 2026-08-29
"""

from collections.abc import Sequence

revision: str = "0001_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish the migration history without product tables."""
    pass


def downgrade() -> None:
    """Remove the empty foundation revision."""
    pass