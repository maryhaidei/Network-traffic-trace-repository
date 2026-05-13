from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.deps_auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import PasswordResetIn, StatusOut, UserCreate, UserOut
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("", response_model=UserOut)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if len(data.login) != 8:
        raise HTTPException(status_code=422, detail="login must be exactly 8 characters")

    exists = db.query(User).filter(User.login == data.login).first()
    if exists:
        raise HTTPException(status_code=409, detail="login already exists")

    u = User(
        login=data.login,
        password_hash=hash_password(data.password),
        last_name=data.last_name,
        first_name=data.first_name,
        organization=data.organization,
        email=data.email,
        role=data.role,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.get("/by-login/{login}", response_model=UserOut)
def get_user_by_login(
    login: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    u = db.query(User).filter(User.login == login).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


@router.delete("/by-login/{login}", response_model=StatusOut)
def delete_user_by_login(
    login: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    u = db.query(User).filter(User.login == login).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    if u.id == current_user.id:
        raise HTTPException(status_code=422, detail="Admin cannot delete self")

    db.delete(u)
    db.commit()
    return StatusOut()


@router.post("/by-login/{login}/reset-password", response_model=StatusOut)
def reset_password_by_login(
    login: str,
    body: PasswordResetIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    u = db.query(User).filter(User.login == login).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    u.password_hash = hash_password(body.new_password)
    db.commit()
    return StatusOut()


@router.delete("/{user_id}", response_model=StatusOut)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Not found")

    if u.id == current_user.id:
        raise HTTPException(status_code=422, detail="Admin cannot delete self")

    db.delete(u)
    db.commit()
    return StatusOut()


@router.post("/{user_id}/reset-password", response_model=StatusOut)
def reset_password(
    user_id: int,
    body: PasswordResetIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Not found")

    u.password_hash = hash_password(body.new_password)
    db.commit()
    return StatusOut()