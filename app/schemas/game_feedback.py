from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GameFeedbackUpsert(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=2, max_length=1000)


class GameFeedbackCommentOut(BaseModel):
    id: UUID
    game_key: str
    user_id: UUID
    username: str | None = None
    avatar: str | None = None
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime
    is_approved: bool
    approved_at: datetime | None = None
    approved_by: UUID | None = None
    approver_username: str | None = None


class GameFeedbackCommentsOut(BaseModel):
    items: list[GameFeedbackCommentOut]


class GameFeedbackSummaryOut(BaseModel):
    game_key: str
    average_rating: float
    ratings_count: int
    my_rating: int | None = None


class GameFeedbackSaveOut(BaseModel):
    status: str
