from app.db.base import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    # restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    time_zone = Column(String, default="Asia/Kolkata")
    currency = Column(String, default="INR")
    location = Column(String, nullable=False)
    is_deleted = Column(Boolean, default=False)

    owner = relationship("User", back_populates="restaurants")
    categories = relationship("Category", back_populates="restaurant")
    tables = relationship("RestaurantTable", back_populates="restaurant")
    orders = relationship("Order", back_populates="restaurant")
    menu_items = relationship("MenuItem", back_populates="restaurant")
