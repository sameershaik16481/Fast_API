# from datetime import datetime

from app.db.base import Base
from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, Integer, String, text

user_role = Enum(
    "OWNER", "STAFF", "ADMIN", name="user_role", create_type=False
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    fullname = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    role = Column(user_role, nullable=False, server_default="OWNER")
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
