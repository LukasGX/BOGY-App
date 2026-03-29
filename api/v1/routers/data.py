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