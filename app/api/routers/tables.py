from app.api.dependencies import get_current_user, get_db
from app.models.restaurant import Restaurant
from app.models.table import RestaurantTable
from app.models.user import User
from app.schemas.table import TableCreate, TableOut
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tables", tags=["tables"])


# Create table for a restaurant
@router.post("/{restaurant_id}", response_model=TableOut)
def create_table(
    restaurant_id: int,
    table: TableCreate,
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

    new_table = RestaurantTable(
        restaurant_id=restaurant.id, table_number=table.table_number
    )
    db.add(new_table)
    db.commit()
    db.refresh(new_table)
    return new_table


# List tables of a restaurant
@router.get("/{restaurant_id}", response_model=list[TableOut])
def list_tables(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(RestaurantTable)
        .join(Restaurant)
        .filter(
            Restaurant.id == restaurant_id,
            Restaurant.user_id == current_user.id,
            RestaurantTable.is_deleted.is_(False),
        )
        .all()
    )


# # Update table number
@router.put("/{table_id}", response_model=TableOut)
def update_table(
    table_id: int,
    table: TableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_table = (
        db.query(RestaurantTable)
        .join(Restaurant)
        .filter(
            RestaurantTable.id == table_id,
            Restaurant.user_id == current_user.id,
            RestaurantTable.is_deleted.is_(False),
        )
        .first()
    )
    if not db_table:
        raise HTTPException(status_code=404, detail="Table not found")

    db_table.table_number = table.table_number
    db.commit()
    db.refresh(db_table)
    return db_table


# # Soft delete table
@router.delete("/{table_id}")
def delete_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_table = (
        db.query(RestaurantTable)
        .join(Restaurant)
        .filter(
            RestaurantTable.id == table_id,
            Restaurant.user_id == current_user.id,
            RestaurantTable.is_deleted.is_(False),
        )
        .first()
    )
    if not db_table:
        raise HTTPException(status_code=404, detail="Table not found")

    db_table.is_deleted = True
    db.commit()
    return {"message": f"Table {table_id} soft deleted successfully"}
