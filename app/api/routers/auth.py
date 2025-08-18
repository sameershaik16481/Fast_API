from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr


class OwnerCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


router = APIRouter()


@router.post("/register/owner")
def create_owner(owner: OwnerCreate):
    return {"message": "owner added succesfully"}
