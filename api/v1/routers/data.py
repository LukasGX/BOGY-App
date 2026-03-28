from fastapi import APIRouter, Depends, Request
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