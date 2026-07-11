import uuid
from sqlalchemy import Column, String, DateTime, JSON, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class GameQuestionSet(Base):
    __tablename__ = "game_question_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    teacher_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    game_key = Column(String(100), nullable=False, index=True)
    questions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("teacher_id", "game_key", name="uq_game_question_sets_teacher_game"),
        Index("ix_game_question_sets_teacher_game", "teacher_id", "game_key"),
    )
