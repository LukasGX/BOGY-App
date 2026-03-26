from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from api.v1.deps import LoggedIn, get_db, verify_password
from services.user_service import *
from definitions import sl_limiter

router = APIRouter()

@router.post("/login")
@sl_limiter.limit("300/minute")
async def login(request: Request, username: str = Form(..., max_length=50), pw: str = Form(..., max_length=50)):
    return login_s(request, username, pw)

@router.get("/profile")
async def profile(session_data: dict = Depends(LoggedIn)):
    return get_profile(session_data)

@router.post("/logout")
async def logout(request: Request):
    return logout_s(request)