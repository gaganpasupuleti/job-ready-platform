"""Merge google-auth line with library join head.

Revision ID: 030_merge_auth_and_library_heads
Revises: 023_google_auth_identities, 029_join_runtime_and_library
"""

from typing import Sequence, Union

revision: str = "030_merge_auth_and_library_heads"
down_revision: Union[str, Sequence[str], None] = (
    "023_google_auth_identities",
    "029_join_runtime_and_library",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
