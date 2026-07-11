from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class GameQuestionsUpsert(BaseModel):
    teacher_id: UUID | None = None
    questions: list[dict[str, Any]] = Field(default_factory=list)


class GameQuestionsOut(BaseModel):
    game_key: str
    teacher_id: UUID | None = None
    questions: list[dict[str, Any]]
