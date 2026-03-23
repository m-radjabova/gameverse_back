from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_admin
from app.models.user import User
from app.schemas.game_feedback import (
    GameFeedbackCommentsOut,
    GameFeedbackSaveOut,
    GameFeedbackSummaryOut,
    GameFeedbackUpsert,
)
from app.services.game_feedback_service import (
    approve_feedback,
    get_approved_feedback_comments,
    get_feedback_comments,
    get_feedback_summary,
    get_pending_feedback_comments,
    get_recent_feedback_comments,
    reject_feedback,
    unapprove_feedback,
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


@router.get("/admin/pending", response_model=GameFeedbackCommentsOut)
def game_feedback_pending(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    safe_limit = max(1, min(limit, 200))
    items = get_pending_feedback_comments(db=db, current_user=current_user, limit=safe_limit)
    return GameFeedbackCommentsOut(items=items)


@router.get("/admin/approved", response_model=GameFeedbackCommentsOut)
def game_feedback_approved(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    safe_limit = max(1, min(limit, 200))
    items = get_approved_feedback_comments(db=db, current_user=current_user, limit=safe_limit)
    return GameFeedbackCommentsOut(items=items)


@router.post("/admin/{feedback_id}/approve", response_model=GameFeedbackSaveOut)
def approve_game_feedback(
    feedback_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    approve_feedback(db=db, current_user=current_user, feedback_id=feedback_id)
    return GameFeedbackSaveOut(status="approved")


@router.post("/admin/{feedback_id}/unapprove", response_model=GameFeedbackSaveOut)
def unapprove_game_feedback(
    feedback_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    unapprove_feedback(db=db, current_user=current_user, feedback_id=feedback_id)
    return GameFeedbackSaveOut(status="pending")


@router.delete("/admin/{feedback_id}/reject", response_model=GameFeedbackSaveOut)
def reject_game_feedback(
    feedback_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    reject_feedback(db=db, current_user=current_user, feedback_id=feedback_id)
    return GameFeedbackSaveOut(status="rejected")


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
    return GameFeedbackSaveOut(status="pending")
