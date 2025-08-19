from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    fullname: str | None = None
    phone: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    role: str
    is_active: bool

    class Config:
        from_attributes = True
