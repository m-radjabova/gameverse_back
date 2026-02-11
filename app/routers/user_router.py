from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])

class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str

@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
def update_me(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.update_current_user(db, current_user, user_data)


@router.patch("/me/password", response_model=UserOut)
def change_my_password(
    data: ChangePasswordSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.change_my_password(db, current_user, data.current_password, data.new_password)
@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user)


@router.post("/me/avatar", response_model=UserOut)
def upload_my_avatar(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.update_user_avatar(db, current_user, image)


@router.post("/{user_id}/avatar", response_model=UserOut)
def upload_user_avatar(
    user_id: UUID,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_service.update_user_avatar(db, user, image)


@router.get("/", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return user_service.get_users(db)


@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(
    user_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    db_user = user_service.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return user_service.update_user(db, user_id, user_data)


@router.patch("/{user_id}", response_model=UserOut)
def update_password(
    user_id: UUID,
    new_password: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_service.change_password(db, user, new_password)


@router.patch("/{user_id}/roles", response_model=UserOut)
def update_roles(
    user_id: UUID,
    roles: list[str],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return user_service.update_user_roles(db, user_id, roles)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user_service.delete_user(db, user_id)
    return