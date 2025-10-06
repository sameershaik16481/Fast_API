from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import (  # noqa
    category,
    customer,
    menu,
    order,
    restaurant,
    table,
    user,
)
