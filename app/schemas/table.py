from enum import Enum

from pydantic import BaseModel


class TableStatusEnum(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    INACTIVE = "INACTIVE"


class TableBase(BaseModel):
    table_number: int
    status: TableStatusEnum


class TableCreate(BaseModel):
    table_number: int
    status: TableStatusEnum = TableStatusEnum.AVAILABLE


class TableUpdate(BaseModel):
    table_number: str | None = None
    status: TableStatusEnum | None = None


class TableOut(TableBase):
    id: int
    restaurant_id: int

    class Config:
        orm_mode = True
