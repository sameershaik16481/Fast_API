from pydantic import BaseModel


class MenuItemBase(BaseModel):
    name: str
    price: float
    is_available: bool = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemOut(MenuItemBase):
    id: int
    is_deleted: bool

    class Config:
        orm_mode = True
