"""add lesson chat tables

Revision ID: d98f0b8e9d21
Revises: c3f4b76fd2a1
Create Date: 2026-02-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d98f0b8e9d21"
down_revision: Union[str, None] = "c3f4b76fd2a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lesson_chat_threads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lesson_id", "student_id", name="uq_lesson_chat_thread_lesson_student"),
    )
    op.create_index(op.f("ix_lesson_chat_threads_id"), "lesson_chat_threads", ["id"], unique=False)
    op.create_index(op.f("ix_lesson_chat_threads_lesson_id"), "lesson_chat_threads", ["lesson_id"], unique=False)
    op.create_index(op.f("ix_lesson_chat_threads_student_id"), "lesson_chat_threads", ["student_id"], unique=False)

    op.create_table(
        "lesson_chat_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("thread_id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["lesson_chat_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lesson_chat_messages_id"), "lesson_chat_messages", ["id"], unique=False)
    op.create_index(op.f("ix_lesson_chat_messages_thread_id"), "lesson_chat_messages", ["thread_id"], unique=False)
    op.create_index(op.f("ix_lesson_chat_messages_sender_id"), "lesson_chat_messages", ["sender_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lesson_chat_messages_sender_id"), table_name="lesson_chat_messages")
    op.drop_index(op.f("ix_lesson_chat_messages_thread_id"), table_name="lesson_chat_messages")
    op.drop_index(op.f("ix_lesson_chat_messages_id"), table_name="lesson_chat_messages")
    op.drop_table("lesson_chat_messages")

    op.drop_index(op.f("ix_lesson_chat_threads_student_id"), table_name="lesson_chat_threads")
    op.drop_index(op.f("ix_lesson_chat_threads_lesson_id"), table_name="lesson_chat_threads")
    op.drop_index(op.f("ix_lesson_chat_threads_id"), table_name="lesson_chat_threads")
    op.drop_table("lesson_chat_threads")
