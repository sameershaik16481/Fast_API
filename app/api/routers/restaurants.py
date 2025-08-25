from app.api.dependencies import get_current_user
from app.models.user import User
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.get("/")
def list_restaurants(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Hello {current_user.fullname}, here are your restaurants"
    }
