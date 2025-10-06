from app.api.dependencies import get_current_user, get_db
from app.models.category import Category
from app.models.restaurant import Restaurant
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/categories", tags=["categories"])


# Create category
@router.post("/{restaurant_id}", response_model=CategoryOut)
def create_category(
    restaurant_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id,
            Restaurant.user_id == current_user.id,
        )
        .first()
    )
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    new_category = Category(restaurant_id=restaurant.id, name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


# List categories
@router.get("/{restaurant_id}", response_model=list[CategoryOut])
def list_categories(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Category)
        .join(Restaurant)
        .filter(
            Restaurant.id == restaurant_id,
            Restaurant.user_id == current_user.id,
            Category.is_deleted.is_(False),
        )
        .all()
    )


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_category = (
        db.query(Category)
        .join(Restaurant)
        .filter(
            Category.id == category_id,
            Restaurant.user_id == current_user.id,
            Category.is_deleted.is_(False),
        )
        .first()
    )
    if not existing_category:
        raise HTTPException(status_code=404, detail="Category not found")

    existing_category.name = category.name
    db.commit()
    db.refresh(existing_category)
    return existing_category
