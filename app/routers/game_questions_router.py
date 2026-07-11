from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.game_question_set import GameQuestionSet
from app.models.user import User
from app.schemas.game_questions import GameQuestionsOut, GameQuestionsUpsert

router = APIRouter(prefix="/game-questions", tags=["Game Questions"])


@router.get("/{game_key}", response_model=GameQuestionsOut)
def get_game_questions(
    game_key: str,
    teacher_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = game_key.strip().lower()
    if not key:
        raise HTTPException(status_code=400, detail="game_key is required")

    if teacher_id and teacher_id != current_user.id and "admin" not in (current_user.roles or []):
        raise HTTPException(status_code=403, detail="Cannot access another teacher's questions")

    owner_id = teacher_id if teacher_id and "admin" in (current_user.roles or []) else current_user.id
    data = (
        db.query(GameQuestionSet)
        .filter(
            GameQuestionSet.teacher_id == owner_id,
            GameQuestionSet.game_key == key,
        )
        .first()
    )
    if not data:
        return GameQuestionsOut(game_key=key, teacher_id=owner_id, questions=[])

    return GameQuestionsOut(game_key=key, teacher_id=data.teacher_id, questions=data.questions or [])


@router.put("/{game_key}", response_model=GameQuestionsOut)
def upsert_game_questions(
    game_key: str,
    payload: GameQuestionsUpsert,
    teacher_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = game_key.strip().lower()
    if not key:
        raise HTTPException(status_code=400, detail="game_key is required")

    requested_teacher_id = teacher_id or payload.teacher_id
    if requested_teacher_id and requested_teacher_id != current_user.id and "admin" not in (current_user.roles or []):
        raise HTTPException(status_code=403, detail="Cannot save another teacher's questions")

    owner_id = requested_teacher_id if requested_teacher_id and "admin" in (current_user.roles or []) else current_user.id
    data = (
        db.query(GameQuestionSet)
        .filter(
            GameQuestionSet.teacher_id == owner_id,
            GameQuestionSet.game_key == key,
        )
        .first()
    )
    if data is None:
        data = GameQuestionSet(teacher_id=owner_id, game_key=key, questions=payload.questions)
        db.add(data)
    else:
        data.questions = payload.questions

    db.commit()
    db.refresh(data)
    return GameQuestionsOut(game_key=key, teacher_id=data.teacher_id, questions=data.questions or [])
