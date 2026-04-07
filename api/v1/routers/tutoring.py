from fastapi import APIRouter, Depends, Request
from api.v1.deps import LoggedIn
from services.tutoring_service import *
from definitions import sl_limiter

router = APIRouter()

@router.get("/register-tutoring")
async def register_tutoring(request: Request, session_data: dict = Depends(LoggedIn)):
    return register(request, session_data)

@router.get("/edit-tutor-profile")
async def edit_tutor_profile(request: Request, session_data: dict = Depends(LoggedIn)):
    return edit_profile(request, session_data)

@router.get("/search-tutors")
@sl_limiter.limit("5/minute")
async def search_tutors(request: Request):
    return search_tutors_s(request)

@router.get("/all-tutors")
@sl_limiter.limit("1/second")
async def all_tutors(request: Request):
    return all_tutors_s()