from typing import Optional

# import bcrypt
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)

# from app.core import security
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class OwnerCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register/owner", response_model=UserRead)
def create_users(user_in: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == user_in.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        fullname=user_in.fullname,
        phone=user_in.phone,
        password=hashed,
        role="OWNER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)

    return {"access_token": access_token, "token_type": "bearer"}
