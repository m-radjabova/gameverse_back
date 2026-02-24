from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.game_feedback import (
    GameFeedbackCommentsOut,
    GameFeedbackSaveOut,
    GameFeedbackSummaryOut,
    GameFeedbackUpsert,
)
from app.services.game_feedback_service import (
    get_feedback_comments,
    get_recent_feedback_comments,
    get_feedback_summary,
    upsert_my_feedback,
)

router = APIRouter(prefix="/game-feedback", tags=["Game Feedback"])


@router.get("/recent", response_model=GameFeedbackCommentsOut)
def game_feedback_recent(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    safe_limit = max(1, min(limit, 100))
    items = get_recent_feedback_comments(db=db, limit=safe_limit)
    return GameFeedbackCommentsOut(items=items)


@router.get("/{game_key}/summary", response_model=GameFeedbackSummaryOut)
def game_feedback_summary(
    game_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = get_feedback_summary(db=db, game_key=game_key, current_user=current_user)
    return GameFeedbackSummaryOut(**data)


@router.get("/{game_key}/comments", response_model=GameFeedbackCommentsOut)
def game_feedback_comments(
    game_key: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    safe_limit = max(1, min(limit, 100))
    items = get_feedback_comments(db=db, game_key=game_key, limit=safe_limit)
    return GameFeedbackCommentsOut(items=items)


@router.put("/{game_key}/my", response_model=GameFeedbackSaveOut)
def upsert_feedback_for_current_teacher(
    game_key: str,
    payload: GameFeedbackUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upsert_my_feedback(db=db, current_user=current_user, game_key=game_key, payload=payload)
    return GameFeedbackSaveOut(status="ok")
