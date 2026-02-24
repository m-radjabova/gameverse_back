from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

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
        )
        db.add(item)
    else:
        item.rating = payload.rating
        item.comment = payload.comment.strip()

    db.commit()
    db.refresh(item)
    return item


def get_feedback_summary(db: Session, game_key: str, current_user: User) -> dict:
    key = normalize_game_key(game_key)

    avg_value, ratings_count = (
        db.query(func.avg(GameFeedback.rating), func.count(GameFeedback.id))
        .filter(GameFeedback.game_key == key)
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
        .filter(GameFeedback.game_key == key)
        .order_by(GameFeedback.created_at.desc())
        .limit(limit)
        .all()
    )

    items: list[dict] = []
    for feedback, username, avatar in rows:
        items.append(
            {
                "id": feedback.id,
                "game_key": feedback.game_key,
                "user_id": feedback.user_id,
                "username": username,
                "avatar": avatar,
                "rating": feedback.rating,
                "comment": feedback.comment,
                "created_at": feedback.created_at,
            }
        )

    return items


def get_recent_feedback_comments(db: Session, limit: int = 20) -> list[dict]:
    rows = (
        db.query(GameFeedback, User.username, User.avatar)
        .join(User, User.id == GameFeedback.user_id)
        .order_by(GameFeedback.created_at.desc())
        .limit(limit)
        .all()
    )

    items: list[dict] = []
    for feedback, username, avatar in rows:
        items.append(
            {
                "id": feedback.id,
                "game_key": feedback.game_key,
                "user_id": feedback.user_id,
                "username": username,
                "avatar": avatar,
                "rating": feedback.rating,
                "comment": feedback.comment,
                "created_at": feedback.created_at,
            }
        )

    return items
