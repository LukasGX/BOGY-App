from fastapi import APIRouter, Body, Depends, Request
from api.v1.deps import LoggedIn, get_db, hash_password, require_role
from services.import_service import *
from definitions import sl_limiter

router = APIRouter()

@router.get("/untis/classes")
@sl_limiter.limit("1/second")
async def get_untis_classes(request: Request, session_data: dict = Depends(require_role(4))):
    return get_untis_classes_s()

@router.post("/untis/classes")
@sl_limiter.limit("10/hour")
async def import_untis_classes(request: Request, session_data: dict = Depends(require_role(4))):
    return import_untis_classes_s()

@router.get("/untis/users")
@sl_limiter.limit("1/second")
async def get_untis_users(request: Request, session_data: dict = Depends(require_role(4))):
    return get_untis_users_s()

@router.post("/untis/users")
@sl_limiter.limit("10/hour")
async def import_untis_users(request: Request, session_data: dict = Depends(require_role(4))):
    return import_untis_users_s()