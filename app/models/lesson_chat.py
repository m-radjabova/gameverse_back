import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class LessonChatThread(Base):
    __tablename__ = "lesson_chat_threads"
    __table_args__ = (
        UniqueConstraint("lesson_id", "student_id", name="uq_lesson_chat_thread_lesson_student"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lesson_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lesson = relationship("Lesson")
    student = relationship("User")
    messages = relationship(
        "LessonChatMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
    )


class LessonChatMessage(Base):
    __tablename__ = "lesson_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    thread_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lesson_chat_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    thread = relationship("LessonChatThread", back_populates="messages")
    sender = relationship("User")
