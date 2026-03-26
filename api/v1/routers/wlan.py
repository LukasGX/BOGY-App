from fastapi import APIRouter, Depends
from api.v1.deps import LoggedIn, get_db, require_role
from services.wlan_service import *

router = APIRouter()

@router.get("/")
async def wlan_codes(session_data: dict = Depends(LoggedIn)):
    return get_wlan_codes(session_data)
    
@router.post("/")
async def add_wlan_code(code: str, users: str, expiry: str, session_data: dict = Depends(require_role(4))):
    return add_wlan_code_s(users, code, expiry)