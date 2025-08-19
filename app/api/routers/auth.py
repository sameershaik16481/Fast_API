from typing import Optional

import bcrypt

# from app.core import security
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from fastapi import APIRouter, Depends, HTTPException
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

    hashed = bcrypt.hashpw(
        user_in.password.encode(), bcrypt.gensalt()
    ).decode()
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
