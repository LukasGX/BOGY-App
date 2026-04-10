from fastapi import APIRouter, Body, Depends, Request
from api.v1.deps import LoggedIn, get_db, hash_password
from services.data_service import *
from definitions import sl_limiter

router = APIRouter()

@router.get("/get-subjects")
@sl_limiter.limit("1/second")
async def get_subjects(request: Request, session_data: dict = Depends(LoggedIn)):
    return get_subjects_s(session_data)
    
@router.get("/encrypt")
@sl_limiter.limit("3/hour")
async def encrypt_string(request: Request, input: str):
    return encrypt(input)

@router.get("/get-classes")
@sl_limiter.limit("1/second")
async def get_classes(request: Request, session_data: dict = Depends(LoggedIn)):
    return get_classes_s(session_data)

@router.get("/class/{class_id}")
@sl_limiter.limit("1/second")
async def get_class(request: Request, class_id: int, session_data: dict = Depends(LoggedIn)):
    return get_class_s(class_id, session_data)

@router.patch("/class/{class_id}")
@sl_limiter.limit("10/minute")
async def update_class(request: Request, class_id: int, new_name: str = Body(embed=True), session_data: dict = Depends(LoggedIn)):
    return update_class_s(class_id, new_name)

@router.get("/get-users")
@sl_limiter.limit("1/second")
async def get_users(request: Request, session_data: dict = Depends(LoggedIn)):
    return get_users_s()

@router.get("/user/{user_id}")
@sl_limiter.limit("100/second")
async def get_user(request: Request, user_id: int, session_data: dict = Depends(LoggedIn)):
    return get_user_s(user_id)

@router.patch("/user/{user_id}")
@sl_limiter.limit("1/second")
async def update_user(request: Request, user_id: int, new_role: int = Body(embed=True), new_class: int = Body(embed=True), new_username: str = Body(embed=True), new_firstname: str = Body(embed=True), new_lastname: str = Body(embed=True), session_data: dict = Depends(LoggedIn)):
    return update_user_s(user_id, new_role, new_class, new_username, new_firstname, new_lastname)

@router.get("/roles")
@sl_limiter.limit("1/second")
async def get_roles(request: Request, session_data: dict = Depends(LoggedIn)):
    return get_roles_s()

@router.get("/wlan-code/{code_id}")
@sl_limiter.limit("1/second")
async def get_wlan_code(request: Request, code_id: int, session_data: dict = Depends(LoggedIn)):
    return get_wlan_code_s(code_id)

@router.patch("/wlan-code/{code_id}")
@sl_limiter.limit("1/second")
async def update_wlan_code(request: Request, code_id: int, new_expiry: str = Body(embed=True), new_user_ids: str = Body(embed=True), session_data: dict = Depends(LoggedIn)):
    return update_wlan_code_s(code_id, new_expiry, new_user_ids)

@router.get("/get-files")
@sl_limiter.limit("1/second")
async def get_files(request: Request, session_data: dict = Depends(LoggedIn)):
    return get_files_s(session_data)