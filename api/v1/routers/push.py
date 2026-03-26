from fastapi import APIRouter, Depends, HTTPException, Request
from api.v1.deps import LoggedIn, get_db
from services.push_service import *
from payloads import PushSubscription
from definitions import sl_limiter

router = APIRouter()

@router.post("/subscribe")
@sl_limiter.limit("5/minute")
async def push_subscribe(
    request: Request,
    payload: PushSubscription,
    session_data: dict = Depends(LoggedIn)
):
    return subscribe(session_data, payload)

@router.delete("/subscribe/{endpoint}")
async def push_unsubscribe(
    endpoint: str,
    session_data: dict = Depends(LoggedIn)
):
    return unsubscribe(session_data, endpoint)

@router.get("/status")
async def get_push_status(session_data: dict = Depends(LoggedIn)):
    return status(session_data)