from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.game_result import GameResult
from app.models.user import User
from app.schemas.game_result import GameResultCreate


def normalize_game_key(game_key: str) -> str:
    key = (game_key or "").strip().lower()
    if not key:
        raise HTTPException(status_code=400, detail="game_key is required")
    return key


def create_game_result(
    db: Session,
    game_key: str,
    payload: GameResultCreate,
    current_user: User | None = None,
) -> GameResult:
    key = normalize_game_key(game_key)

    item = GameResult(
        game_key=key,
        user_id=getattr(current_user, "id", None),
        participant_name=payload.participant_name.strip(),
        participant_mode=payload.participant_mode.strip(),
        score=payload.score,
        metadata_json=payload.metadata or None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_game_leaderboard(db: Session, game_key: str, limit: int = 10) -> list[dict]:
    key = normalize_game_key(game_key)
    rows = (
        db.query(GameResult)
        .filter(GameResult.game_key == key, GameResult.user_id.isnot(None))
        .order_by(GameResult.score.desc(), GameResult.created_at.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "game_key": row.game_key,
            "user_id": row.user_id,
            "participant_name": row.participant_name,
            "participant_mode": row.participant_mode,
            "score": row.score,
            "metadata": row.metadata_json,
            "created_at": row.created_at,
        }
        for row in rows
    ]
