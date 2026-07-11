"""add teacher_id to game_question_sets

Revision ID: e7c2d9a1b4f6
Revises: b7e1a5c2d4f0
Create Date: 2026-07-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7c2d9a1b4f6"
down_revision: Union[str, None] = "b7e1a5c2d4f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_RE = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"


def _create_table() -> None:
    op.create_table(
        "game_question_sets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("teacher_id", sa.UUID(), nullable=False),
        sa.Column("game_key", sa.String(length=100), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("teacher_id", "game_key", name="uq_game_question_sets_teacher_game"),
    )
    op.create_index("ix_game_question_sets_id", "game_question_sets", ["id"], unique=False)
    op.create_index("ix_game_question_sets_teacher_id", "game_question_sets", ["teacher_id"], unique=False)
    op.create_index("ix_game_question_sets_game_key", "game_question_sets", ["game_key"], unique=False)
    op.create_index("ix_game_question_sets_teacher_game", "game_question_sets", ["teacher_id", "game_key"], unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "game_question_sets" not in inspector.get_table_names():
        _create_table()
        return

    columns = {column["name"] for column in inspector.get_columns("game_question_sets")}
    unique_constraints = inspector.get_unique_constraints("game_question_sets")
    existing_indexes = inspector.get_indexes("game_question_sets")

    for constraint in unique_constraints:
        if constraint.get("column_names") == ["game_key"]:
            op.drop_constraint(constraint["name"], "game_question_sets", type_="unique")

    for index in existing_indexes:
        if index.get("column_names") == ["game_key"] and index.get("unique"):
            op.drop_index(index["name"], table_name="game_question_sets")

    if "teacher_id" not in columns:
        op.add_column("game_question_sets", sa.Column("teacher_id", sa.UUID(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE game_question_sets AS g
            SET
                teacher_id = split_part(g.game_key, ':', 1)::uuid,
                game_key = split_part(g.game_key, ':', 2)
            WHERE g.teacher_id IS NULL
              AND position(':' in g.game_key) > 0
              AND split_part(g.game_key, ':', 1) ~ :uuid_re
            """
        ).bindparams(uuid_re=UUID_RE)
    )

    unmigrated = bind.execute(
        sa.text("SELECT COUNT(*) FROM game_question_sets WHERE teacher_id IS NULL")
    ).scalar()
    if unmigrated:
        raise RuntimeError(
            "Cannot migrate game_question_sets: some rows do not contain a valid teacher id in game_key"
        )

    op.alter_column("game_question_sets", "teacher_id", nullable=False)

    unique_constraints = sa.inspect(bind).get_unique_constraints("game_question_sets")
    unique_names = {constraint.get("name") for constraint in unique_constraints}
    if "uq_game_question_sets_teacher_game" not in unique_names:
        op.create_unique_constraint(
            "uq_game_question_sets_teacher_game",
            "game_question_sets",
            ["teacher_id", "game_key"],
        )

    indexes = {idx.get("name") for idx in sa.inspect(bind).get_indexes("game_question_sets")}
    if "ix_game_question_sets_teacher_id" not in indexes:
        op.create_index("ix_game_question_sets_teacher_id", "game_question_sets", ["teacher_id"], unique=False)
    if "ix_game_question_sets_game_key" not in indexes:
        op.create_index("ix_game_question_sets_game_key", "game_question_sets", ["game_key"], unique=False)
    if "ix_game_question_sets_teacher_game" not in indexes:
        op.create_index(
            "ix_game_question_sets_teacher_game",
            "game_question_sets",
            ["teacher_id", "game_key"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "game_question_sets" not in inspector.get_table_names():
        return

    indexes = {idx.get("name") for idx in inspector.get_indexes("game_question_sets")}
    unique_constraints = {constraint.get("name") for constraint in inspector.get_unique_constraints("game_question_sets")}
    columns = {column["name"] for column in inspector.get_columns("game_question_sets")}

    if "ix_game_question_sets_teacher_game" in indexes:
        op.drop_index("ix_game_question_sets_teacher_game", table_name="game_question_sets")
    if "ix_game_question_sets_teacher_id" in indexes:
        op.drop_index("ix_game_question_sets_teacher_id", table_name="game_question_sets")
    if "uq_game_question_sets_teacher_game" in unique_constraints:
        op.drop_constraint("uq_game_question_sets_teacher_game", "game_question_sets", type_="unique")

    if "teacher_id" in columns:
        op.execute("UPDATE game_question_sets SET game_key = teacher_id::text || ':' || game_key")
        op.drop_column("game_question_sets", "teacher_id")

    op.create_unique_constraint("uq_game_question_sets_game_key", "game_question_sets", ["game_key"])
