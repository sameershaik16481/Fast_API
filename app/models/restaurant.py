from app.db.base import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    time_zone = Column(String, default="Asia/Kolkata")
    currency = Column(String, default="INR")
    location = Column(String, nullable=False)
    is_deleted = Column(Boolean, default=False)

    owner = relationship("User", back_populates="restaurants")
