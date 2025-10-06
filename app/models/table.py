import enum

from app.db.base import Base
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship


class TableStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    INACTIVE = "INACTIVE"


class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(
        Integer, ForeignKey("restaurants.id"), nullable=False
    )
    table_number = Column(Integer, nullable=False)
    status = Column(Enum(TableStatus), nullable=False, default="AVAILABLE")
    is_deleted = Column(Boolean, default=False)

    restaurant = relationship("Restaurant", back_populates="tables")
