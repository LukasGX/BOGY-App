from fastapi import APIRouter, Depends, Request
from fastapi.params import Body
from api.v1.deps import require_role
from services.administration_service import *
from payloads import CreateUserRequest, CreateClassRequest
from definitions import sl_limiter

router = APIRouter()

@router.put("/user")
@sl_limiter.limit("1000/hour")
async def create_user(request: Request, payload: CreateUserRequest, session_data: dict = Depends(require_role(4))):
    return create_user_s(payload)

@router.put("/class")
@sl_limiter.limit("1000/hour")
async def create_class(request: Request, payload: CreateClassRequest, session_data: dict = Depends(require_role(4))):
    return create_class_s(payload)
    
@router.post("/send-all")
@sl_limiter.limit("10/hour")
async def send_push_all(request: Request, title: str = Body(..., max_length=100, embed=True), body: str = Body(..., max_length=800, embed=True), session_data: dict = Depends(require_role(4))):
    return push_all(title, body)

@router.post("/send-user")
@sl_limiter.limit("200/hour")
async def send_push_user(
    request: Request,
    user_id: int = Body(..., ge=0, le=9999, embed=True), 
    title: str = Body(..., max_length=100, embed=True), 
    body: str = Body(..., max_length=800, embed=True), 
    session_data: dict = Depends(require_role(4))
):
    return push_user(user_id, title, body)

@router.delete("/class/{class_id}")
@sl_limiter.limit("10/minute")
async def delete_class(request: Request, class_id: int, session_data: dict = Depends(require_role(4))):
    return delete_class_s(class_id)

@router.delete("/user/{user_id}")
@sl_limiter.limit("10/minute")
async def delete_user(request: Request, user_id: int, session_data: dict = Depends(require_role(4))):
    return delete_user_s(user_id)

@router.post("/user/{user_id}/reset-pw")
@sl_limiter.limit("10/minute")
async def reset_user_password(request: Request, user_id: int, session_data: dict = Depends(require_role(4))):
    return reset_user_password_s(user_id)

@router.put("/wlan-code")
@sl_limiter.limit("10/minute")
async def add_wlan_code(request: Request, code: str = Body(embed=True), user_ids: str = Body(embed=True), expiry: str = Body(embed=True), session_data: dict = Depends(require_role(4))):
    return add_wlan_code_s(user_ids, code, expiry)

@router.delete("/wlan-code/{code_id}")
@sl_limiter.limit("10/minute")
async def delete_wlan_code(request: Request, code_id: int, session_data: dict = Depends(require_role(4))):
    return delete_wlan_code_s(code_id)