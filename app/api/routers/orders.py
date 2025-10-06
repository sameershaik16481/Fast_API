from app.api.dependencies import get_current_user, get_db
from app.models.category import Category
from app.models.menu import MenuItem
from app.models.order import Order, OrderItem
from app.models.restaurant import Restaurant
from app.models.table import RestaurantTable
from app.models.user import User
from app.schemas.order import OrderCreate, OrderOut
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/{restaurant_id}/", response_model=OrderOut)
def place_order(
    restaurant_id: int,
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate restaurant (must belong to logged-in user)
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

    # Validate table
    table = (
        db.query(RestaurantTable)
        .filter(
            RestaurantTable.id == order_data.table_id,
            RestaurantTable.restaurant_id == restaurant_id,
            RestaurantTable.is_deleted.is_(False),
        )
        .first()
    )
    if not table:
        raise HTTPException(
            status_code=400, detail="Please select table number"
        )

    existing_order = (
        db.query(Order)
        .filter(
            Order.table_id == table.id,
            Order.restaurant_id == restaurant_id,
            Order.is_completed.is_(False),
        )
        .first()
    )
    if existing_order:
        new_order = existing_order
    else:
        # Create new order
        new_order = Order(
            restaurant_id=restaurant_id, table_id=table.id, total_amount=0.0
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

    total_price = new_order.total_amount

    # Add each ordered menu item
    for item in order_data.items:
        # FIXED QUERY — fetch by category’s restaurant_id
        menu_item = (
            db.query(MenuItem)
            .join(Category, MenuItem.category_id == Category.id)
            .filter(
                MenuItem.id == item.menu_item_id,
                Category.restaurant_id == restaurant_id,
                MenuItem.is_deleted.is_(False),
            )
            .first()
        )

        if not menu_item:
            raise HTTPException(
                status_code=404,
                detail=f"Menu item {item.menu_item_id} not found",
            )

        # Create order item
        order_item = OrderItem(
            order_id=new_order.id,
            menu_item_id=menu_item.id,
            quantity=item.quantity,
        )
        db.add(order_item)

        # Add to total
        total_price += menu_item.price * item.quantity

    # Update total price
    new_order.total_amount = total_price
    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/{restaurant_id}/bill/{order_id}/")
def get_bill(
    restaurant_id: int,
    table_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate restaurant (must belong to logged-in user)
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

    table = (
        db.query(RestaurantTable)
        .filter(
            RestaurantTable.table_number == table_number,
            RestaurantTable.restaurant_id == restaurant_id,
            RestaurantTable.is_deleted.is_(False),
        )
        .first()
    )
    if not table:
        raise HTTPException(
            status_code=404, detail=f"Table number {table_number} not found"
        )

    # Validate order
    orders = (
        db.query(Order)
        .filter(
            Order.table_id == table.id, Order.restaurant_id == restaurant_id
        )
        .all()
    )
    if not orders:
        raise HTTPException(
            status_code=404,
            detail=f"No orders found for this table{table_number}",
        )

    bill_details = []
    grand_total = 0.0

    for order in orders:
        order_items = (
            db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        )

        for item in order_items:
            item_total = item.menu_item.price * item.quantity
            grand_total += item_total

            bill_details.append(
                {
                    "item_name": item.menu_item.name,
                    "quantity": item.quantity,
                    "unit_price": item.menu_item.price,
                    "total_price": item_total,
                }
            )
    return {
        "restaurant_name": restaurant.name,
        "table_number": table.table_number,
        "grand_total": grand_total,
        "ordered_items": bill_details,
    }
