from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.models.game_feedback import GameFeedback
from app.models.user import User
from app.schemas.game_feedback import GameFeedbackUpsert


def normalize_game_key(game_key: str) -> str:
    key = (game_key or "").strip().lower()
    if not key:
        raise HTTPException(status_code=400, detail="game_key is required")
    return key


def ensure_teacher(user: User) -> None:
    roles = {role.lower() for role in (user.roles or [])}
    if "teacher" not in roles:
        raise HTTPException(status_code=403, detail="Only teachers can leave feedback")


def ensure_admin(user: User) -> None:
    roles = {role.lower() for role in (user.roles or [])}
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Only admins can moderate feedback")


def serialize_feedback(feedback: GameFeedback, username: str | None, avatar: str | None, approver_username: str | None = None) -> dict:
    return {
        "id": feedback.id,
        "game_key": feedback.game_key,
        "user_id": feedback.user_id,
        "username": username,
        "avatar": avatar,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "created_at": feedback.created_at,
        "updated_at": feedback.updated_at,
        "is_approved": bool(feedback.is_approved),
        "approved_at": feedback.approved_at,
        "approved_by": feedback.approved_by,
        "approver_username": approver_username,
    }


def upsert_my_feedback(
    db: Session,
    current_user: User,
    game_key: str,
    payload: GameFeedbackUpsert,
) -> GameFeedback:
    ensure_teacher(current_user)
    key = normalize_game_key(game_key)

    item = (
        db.query(GameFeedback)
        .filter(GameFeedback.game_key == key, GameFeedback.user_id == current_user.id)
        .first()
    )

    if item is None:
        item = GameFeedback(
            game_key=key,
            user_id=current_user.id,
            rating=payload.rating,
            comment=payload.comment.strip(),
            is_approved=False,
            approved_at=None,
            approved_by=None,
        )
        db.add(item)
    else:
        item.rating = payload.rating
        item.comment = payload.comment.strip()
        item.is_approved = False
        item.approved_at = None
        item.approved_by = None

    db.commit()
    db.refresh(item)
    return item


def get_feedback_summary(db: Session, game_key: str, current_user: User) -> dict:
    key = normalize_game_key(game_key)

    avg_value, ratings_count = (
        db.query(func.avg(GameFeedback.rating), func.count(GameFeedback.id))
        .filter(GameFeedback.game_key == key, GameFeedback.is_approved.is_(True))
        .one()
    )

    my_rating_row = (
        db.query(GameFeedback.rating)
        .filter(GameFeedback.game_key == key, GameFeedback.user_id == current_user.id)
        .first()
    )

    return {
        "game_key": key,
        "average_rating": float(avg_value or 0),
        "ratings_count": int(ratings_count or 0),
        "my_rating": int(my_rating_row[0]) if my_rating_row else None,
    }


def get_feedback_comments(db: Session, game_key: str, limit: int = 20) -> list[dict]:
    key = normalize_game_key(game_key)

    rows = (
        db.query(GameFeedback, User.username, User.avatar)
        .join(User, User.id == GameFeedback.user_id)
        .filter(GameFeedback.game_key == key, GameFeedback.is_approved.is_(True))
        .order_by(GameFeedback.approved_at.desc().nullslast(), GameFeedback.created_at.desc())
        .limit(limit)
        .all()
    )

    return [serialize_feedback(feedback, username, avatar) for feedback, username, avatar in rows]


def get_recent_feedback_comments(db: Session, limit: int = 20) -> list[dict]:
    rows = (
        db.query(GameFeedback, User.username, User.avatar)
        .join(User, User.id == GameFeedback.user_id)
        .filter(GameFeedback.is_approved.is_(True))
        .order_by(GameFeedback.approved_at.desc().nullslast(), GameFeedback.created_at.desc())
        .limit(limit)
        .all()
    )

    return [serialize_feedback(feedback, username, avatar) for feedback, username, avatar in rows]


def get_pending_feedback_comments(db: Session, current_user: User, limit: int = 100) -> list[dict]:
    ensure_admin(current_user)
    approver = aliased(User)

    rows = (
        db.query(GameFeedback, User.username, User.avatar, approver.username)
        .join(User, User.id == GameFeedback.user_id)
        .outerjoin(approver, approver.id == GameFeedback.approved_by)
        .filter(GameFeedback.is_approved.is_(False))
        .order_by(GameFeedback.created_at.desc())
        .limit(limit)
        .all()
    )

    return [serialize_feedback(feedback, username, avatar, approver_username) for feedback, username, avatar, approver_username in rows]


def get_approved_feedback_comments(db: Session, current_user: User, limit: int = 100) -> list[dict]:
    ensure_admin(current_user)
    approver = aliased(User)

    rows = (
        db.query(GameFeedback, User.username, User.avatar, approver.username)
        .join(User, User.id == GameFeedback.user_id)
        .outerjoin(approver, approver.id == GameFeedback.approved_by)
        .filter(GameFeedback.is_approved.is_(True))
        .order_by(GameFeedback.approved_at.desc().nullslast(), GameFeedback.created_at.desc())
        .limit(limit)
        .all()
    )

    return [serialize_feedback(feedback, username, avatar, approver_username) for feedback, username, avatar, approver_username in rows]


def approve_feedback(db: Session, current_user: User, feedback_id: UUID) -> GameFeedback:
    ensure_admin(current_user)

    item = db.query(GameFeedback).filter(GameFeedback.id == feedback_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Feedback not found")

    item.is_approved = True
    item.approved_at = datetime.now(timezone.utc)
    item.approved_by = current_user.id
    db.commit()
    db.refresh(item)
    return item


def unapprove_feedback(db: Session, current_user: User, feedback_id: UUID) -> GameFeedback:
    ensure_admin(current_user)

    item = db.query(GameFeedback).filter(GameFeedback.id == feedback_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Feedback not found")

    item.is_approved = False
    item.approved_at = None
    item.approved_by = None
    db.commit()
    db.refresh(item)
    return item


def reject_feedback(db: Session, current_user: User, feedback_id: UUID) -> None:
    ensure_admin(current_user)

    item = db.query(GameFeedback).filter(GameFeedback.id == feedback_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Feedback not found")

    db.delete(item)
    db.commit()
