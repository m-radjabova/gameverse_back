"""add game_feedback table

Revision ID: f24b7b1c9a11
Revises: c1b32bea57bf
Create Date: 2026-02-24 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f24b7b1c9a11'
down_revision: Union[str, None] = 'c1b32bea57bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'game_feedback' not in inspector.get_table_names():
        op.create_table(
            'game_feedback',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('game_key', sa.String(length=100), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('comment', sa.String(length=1000), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('game_key', 'user_id', name='uq_game_feedback_game_user'),
        )

    existing_indexes = {idx.get('name') for idx in inspector.get_indexes('game_feedback')}

    if 'ix_game_feedback_id' not in existing_indexes:
        op.create_index(op.f('ix_game_feedback_id'), 'game_feedback', ['id'], unique=False)
    if 'ix_game_feedback_game_key' not in existing_indexes:
        op.create_index(op.f('ix_game_feedback_game_key'), 'game_feedback', ['game_key'], unique=False)
    if 'ix_game_feedback_user_id' not in existing_indexes:
        op.create_index(op.f('ix_game_feedback_user_id'), 'game_feedback', ['user_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'game_feedback' not in inspector.get_table_names():
        return

    existing_indexes = {idx.get('name') for idx in inspector.get_indexes('game_feedback')}
    if 'ix_game_feedback_user_id' in existing_indexes:
        op.drop_index(op.f('ix_game_feedback_user_id'), table_name='game_feedback')
    if 'ix_game_feedback_game_key' in existing_indexes:
        op.drop_index(op.f('ix_game_feedback_game_key'), table_name='game_feedback')
    if 'ix_game_feedback_id' in existing_indexes:
        op.drop_index(op.f('ix_game_feedback_id'), table_name='game_feedback')

    op.drop_table('game_feedback')
