from app.db.base import Base
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(
        Integer, ForeignKey("restaurants.id"), nullable=False
    )
    table_id = Column(
        Integer, ForeignKey("restaurant_tables.id"), nullable=False
    )  # must select table
    total_amount = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)

    restaurant = relationship("Restaurant", back_populates="orders")
    table = relationship("RestaurantTable")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, default=1)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")
