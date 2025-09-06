from app.api.dependencies import get_current_user, get_db
from app.models.restaurant import Restaurant
from app.models.user import User
from app.schemas.restaurant import RestaurantCreate, RestaurantOut
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


# ---------------- CREATE ----------------
@router.post("/hotels/", response_model=RestaurantOut)
def create_restaurant(
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_restaurant = Restaurant(
        user_id=current_user.id,
        name=restaurant.name,
        time_zone=restaurant.time_zone,
        currency=restaurant.currency,
        location=restaurant.location,
    )
    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)
    return new_restaurant


# ---------------- READ (LIST ALL BY OWNER) ----------------
@router.get("/", response_model=list[RestaurantOut])
def list_restaurants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_deleted: bool = False,  # optional query param
):
    query = db.query(Restaurant).filter(Restaurant.user_id == current_user.id)
    if not include_deleted:
        query = query.filter(Restaurant.is_deleted.is_(False))
    return query.all()


# ---------------- READ (SINGLE BY ID) ----------------
@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(
    restaurant_id: int,
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
    return restaurant


# ---------------- UPDATE ----------------
@router.put("/{restaurant_id}", response_model=RestaurantOut)
def update_restaurant(
    restaurant_id: int,
    data: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id,
            Restaurant.user_id == current_user.id,
            Restaurant.is_deleted.is_(False),  # don’t update deleted
        )
        .first()
    )

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    for key, value in data.dict().items():
        setattr(restaurant, key, value)

    db.commit()
    db.refresh(restaurant)
    return restaurant


# ---------------- SOFT DELETE ----------------
@router.delete("/{restaurant_id}")
def soft_delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id,
            Restaurant.user_id == current_user.id,
            Restaurant.is_deleted.is_(
                False
            ),  # only delete if not already deleted
        )
        .first()
    )

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant.is_deleted = True
    db.commit()
    return {"message": f"Restaurant {restaurant_id} soft deleted successfully"}


# ---------------- RESTORE ----------------
@router.put("/restore/{restaurant_id}", response_model=RestaurantOut)
def restore_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id,
            Restaurant.user_id == current_user.id,
            Restaurant.is_deleted.is_(True),  # only restore if deleted
        )
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=404, detail="Restaurant not found or not deleted"
        )

    restaurant.is_deleted = False
    db.commit()
    db.refresh(restaurant)
    return restaurant
