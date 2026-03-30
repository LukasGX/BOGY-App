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
@sl_limiter.limit("1/second")
async def get_user(request: Request, user_id: int, session_data: dict = Depends(LoggedIn)):
    return get_user_s(user_id)

@router.get("/roles")
@sl_limiter.limit("1/second")
async def get_roles(request: Request, session_data: dict = Depends(LoggedIn)):
    return get_roles_s()