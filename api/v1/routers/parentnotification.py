from fastapi import APIRouter, Depends
from api.v1.deps import LoggedIn
from services.parentnotification_service import *

router = APIRouter()

@router.get("/")
async def get_parentnotifications(session_data: dict = Depends(LoggedIn)):
    return get_parentnotifications_s(session_data)

@router.get("/list")
async def get_parentnotifications_list(session_data: dict = Depends(LoggedIn)):
    return get_parentnotifications_s(session_data, filter_user_id=False)