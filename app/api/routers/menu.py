from app.api.dependencies import get_current_user, get_db
from app.models.category import Category
from app.models.menu import MenuItem
from app.models.restaurant import Restaurant
from app.models.user import User
from app.schemas.menu import MenuItemCreate, MenuItemOut
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/menu", tags=["menu"])


# Create menu item
@router.post("/{category_id}", response_model=MenuItemOut)
def create_menu_item(
    category_id: int,
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = (
        db.query(Category)
        .join(Restaurant)
        .filter(
            Category.id == category_id, Restaurant.user_id == current_user.id
        )
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    new_item = MenuItem(
        category_id=category.id,
        name=item.name,
        price=item.price,
        is_available=item.is_available,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


# List menu items by category
@router.get("/{category_id}", response_model=list[MenuItemOut])
def list_menu_items(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(MenuItem)
        .join(Category)
        .join(Restaurant)
        .filter(
            Category.id == category_id,
            Restaurant.user_id == current_user.id,
            MenuItem.is_deleted.is_(False),
        )
        .all()
    )


# Soft delete menu item
@router.delete("/{item_id}")
def soft_delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(MenuItem)
        .join(Category)
        .join(Restaurant)
        .filter(
            MenuItem.id == item_id,
            Restaurant.user_id == current_user.id,
            MenuItem.is_deleted.is_(False),
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    item.is_deleted = True
    db.commit()
    return {"message": f"Menu item {item_id} soft deleted successfully"}
