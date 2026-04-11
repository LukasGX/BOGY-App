from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from api.v1.deps import LoggedIn, get_db
from services.pw_service import *
from definitions import sl_limiter

router = APIRouter()

class SecretCreate(BaseModel):
    name: str
    value: str
    unlock_key: str

class SecretUpdate(BaseModel):
    value: str
    unlock_key: str

class ChangeUnlockKey(BaseModel):
    old_unlock_key: str
    new_unlock_key: str

@router.post("/create")
@sl_limiter.limit("100/minute")
async def create_secret(request: Request, secret: SecretCreate, session_data: dict = Depends(LoggedIn)):
    user_id = session_data["user_id"]
    return create_secret_s(user_id, secret.name, secret.value, secret.unlock_key)

@router.get("/read/{name}")
@sl_limiter.limit("100/minute")
async def read_secret(request: Request, name: str, unlock_key: str, session_data: dict = Depends(LoggedIn)):
    user_id = session_data["user_id"]
    return get_secret_s(user_id, name, unlock_key)

@router.put("/modify/{name}")
@sl_limiter.limit("100/minute")
async def modify_secret(request: Request, name: str, secret: SecretUpdate, session_data: dict = Depends(LoggedIn)):
    user_id = session_data["user_id"]
    return update_secret_s(user_id, name, secret.value, secret.unlock_key)

@router.delete("/delete/{name}")
@sl_limiter.limit("100/minute")
async def delete_secret(request: Request, name: str, session_data: dict = Depends(LoggedIn)):
    user_id = session_data["user_id"]
    return delete_secret_s(user_id, name)

@router.get("/list")
@sl_limiter.limit("100/minute")
async def list_secrets(request: Request, session_data: dict = Depends(LoggedIn)):
    user_id = session_data["user_id"]
    return list_secrets_s(user_id)

@router.get("/key")
@sl_limiter.limit("100/minute")
async def get_key_status(request: Request, session_data: dict = Depends(LoggedIn)):
    user_id = session_data["user_id"]
    return {"key_set": has_user_key(user_id)}

@router.put("/change-unlock-key")
@sl_limiter.limit("10/minute")
async def change_unlock_key(request: Request, change: ChangeUnlockKey, session_data: dict = Depends(LoggedIn)):
    user_id = session_data["user_id"]
    return change_unlock_key_s(user_id, change.old_unlock_key, change.new_unlock_key)