from typing import List

from pydantic import BaseModel


# For creating individual menu items in an order
class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int


# Request schema for placing an order
class OrderCreate(BaseModel):
    table_id: int
    items: List[OrderItemCreate]


# Response schema for order items
class OrderItemOut(BaseModel):
    id: int
    menu_item_id: int
    quantity: int

    class Config:
        orm_mode = True


# Response schema for the entire order
class OrderOut(BaseModel):
    id: int
    restaurant_id: int
    table_id: int
    total_amount: float
    is_completed: bool
    items: List[OrderItemOut]

    class Config:
        orm_mode = True
