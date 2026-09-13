"""One answer row per practice session and question.

Revision ID: 016_practice_answer_uniqueness
Revises: 015_mistake_source_events

Duplicate rows were possible because autosave and submit each inserted when
they did not see the other row. Existing extras are collapsed before the
constraint is added:

- keep a finalized row (answered_at set) over a draft sibling
- otherwise keep the latest updated_at, then created_at, then id

Do not drop unrelated tables to force an alembic table count.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "016_practice_answer_uniqueness"
down_revision: Union[str, None] = "015_mistake_source_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM practice_answers AS extra
        USING practice_answers AS keep
        WHERE extra.session_id = keep.session_id
          AND extra.question_id = keep.question_id
          AND extra.id <> keep.id
          AND (
            (extra.answered_at IS NULL AND keep.answered_at IS NOT NULL)
            OR (
              (extra.answered_at IS NULL) = (keep.answered_at IS NULL)
              AND (
                extra.updated_at < keep.updated_at
                OR (
                  extra.updated_at = keep.updated_at
                  AND extra.created_at < keep.created_at
                )
                OR (
                  extra.updated_at = keep.updated_at
                  AND extra.created_at = keep.created_at
                  AND extra.id < keep.id
                )
              )
            )
          )
        """
    )
    op.create_unique_constraint(
        "uq_practice_answer_session_question",
        "practice_answers",
        ["session_id", "question_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_practice_answer_session_question",
        "practice_answers",
        type_="unique",
    )
