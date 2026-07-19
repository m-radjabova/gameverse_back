from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.game_result import GameLeaderboardOut, GameResultCreate, GameResultSaveOut
from app.services.game_result_service import create_game_result, get_game_leaderboard

router = APIRouter(prefix="/game-results", tags=["Game Results"])


@router.get("/{game_key}/leaderboard", response_model=GameLeaderboardOut)
def game_results_leaderboard(
    game_key: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    safe_limit = max(1, min(limit, 100))
    items = get_game_leaderboard(db=db, game_key=game_key, limit=safe_limit)
    return GameLeaderboardOut(items=items)


@router.post("/{game_key}", response_model=GameResultSaveOut)
def save_game_result(
    game_key: str,
    payload: GameResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    create_game_result(db=db, game_key=game_key, payload=payload, current_user=current_user)
    return GameResultSaveOut(status="ok")
