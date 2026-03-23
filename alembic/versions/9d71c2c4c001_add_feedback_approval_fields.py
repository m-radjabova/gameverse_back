"""add feedback approval fields

Revision ID: 9d71c2c4c001
Revises: f24b7b1c9a11
Create Date: 2026-03-23 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d71c2c4c001"
down_revision: Union[str, None] = "f24b7b1c9a11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("game_feedback")}

    if "is_approved" not in columns:
        op.add_column("game_feedback", sa.Column("is_approved", sa.Boolean(), nullable=True, server_default=sa.true()))
    if "approved_at" not in columns:
        op.add_column("game_feedback", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    if "approved_by" not in columns:
        op.add_column("game_feedback", sa.Column("approved_by", sa.UUID(), nullable=True))
        op.create_foreign_key(
            "fk_game_feedback_approved_by_users",
            "game_feedback",
            "users",
            ["approved_by"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute("UPDATE game_feedback SET is_approved = TRUE WHERE is_approved IS NULL")
    op.execute("UPDATE game_feedback SET approved_at = created_at WHERE is_approved = TRUE AND approved_at IS NULL")
    op.alter_column("game_feedback", "is_approved", nullable=False, server_default=sa.text("false"))

    existing_indexes = {idx.get("name") for idx in inspector.get_indexes("game_feedback")}
    if "ix_game_feedback_is_approved" not in existing_indexes:
        op.create_index("ix_game_feedback_is_approved", "game_feedback", ["is_approved"], unique=False)
    if "ix_game_feedback_approved_by" not in existing_indexes:
        op.create_index("ix_game_feedback_approved_by", "game_feedback", ["approved_by"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("game_feedback")}
    existing_indexes = {idx.get("name") for idx in inspector.get_indexes("game_feedback")}
    existing_fks = {fk.get("name") for fk in inspector.get_foreign_keys("game_feedback")}

    if "ix_game_feedback_approved_by" in existing_indexes:
        op.drop_index("ix_game_feedback_approved_by", table_name="game_feedback")
    if "ix_game_feedback_is_approved" in existing_indexes:
        op.drop_index("ix_game_feedback_is_approved", table_name="game_feedback")
    if "fk_game_feedback_approved_by_users" in existing_fks:
        op.drop_constraint("fk_game_feedback_approved_by_users", "game_feedback", type_="foreignkey")
    if "approved_by" in columns:
        op.drop_column("game_feedback", "approved_by")
    if "approved_at" in columns:
        op.drop_column("game_feedback", "approved_at")
    if "is_approved" in columns:
        op.drop_column("game_feedback", "is_approved")
