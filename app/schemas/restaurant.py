from pydantic import BaseModel


class RestaurantBase(BaseModel):
    name: str
    time_zone: str = "Asia/Kolkata"
    currency: str = "INR"
    location: str


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantOut(RestaurantBase):
    id: int
    is_deleted: bool

    class Config:
        orm_mode = True
        from_attributes = True
