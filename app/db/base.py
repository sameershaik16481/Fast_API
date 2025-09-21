from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import category, customer, menu, restaurant, user  # noqa
