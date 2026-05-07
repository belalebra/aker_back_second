from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.services import user_service
from app.routers.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/users", tags=["Users"])


class UpdateProfileRequest(BaseModel):
    f_name:       Optional[str] = None
    l_name:       Optional[str] = None
    phone:        Optional[str] = None
    new_password: Optional[str] = None

class UpdateRoleRequest(BaseModel):
    role: str


@router.get("/me")
def get_me(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    from app.services.booking_service import get_user_profile
    return get_user_profile(conn, current_user["username"])


@router.put("/me")
def update_profile(data: UpdateProfileRequest, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    return user_service.update_my_profile(conn, current_user["username"], data.model_dump(exclude_none=True))


@router.get("")
def get_all_users(conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return user_service.get_all_users(conn)


@router.patch("/{username}/role")
def update_role(username: str, data: UpdateRoleRequest, conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return user_service.update_user_role(conn, username, data.role)