import json
import sqlite3
from fastapi import APIRouter, Depends, Form, HTTPException, Request
import webpush
from api.v1.deps import get_db, hash_password, require_role
from payloads import CreateUserRequest, CreateClassRequest
from definitions import sl_limiter, VAPID_PRIVATE_KEY, VAPID_EMAIL

router = APIRouter()

@router.post("/create_user")
@sl_limiter.limit("1000/hour")
async def create_user(request: Request, payload: CreateUserRequest, session_data: dict = Depends(require_role(4))):
    with get_db() as conn:
        cursor = conn.cursor()
        # find role id
        cursor.execute("SELECT id FROM roles WHERE name = ?", (payload.role,))
        role_row = cursor.fetchone()
        if not role_row:
            raise HTTPException(status_code=400, detail="Invalid role")
        role_id = role_row["id"]
        # validate class id if provided
        class_id = payload.class_id
        if class_id is not None:
            cursor.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Invalid class")
        # hash password
        hashed = hash_password(payload.password)
        try:
            cursor.execute(
                "INSERT INTO users(username, firstname, lastname, password, role, class) VALUES(?,?,?,?,?,?)",
                (payload.username, payload.firstname, payload.lastname, hashed, role_id, class_id),
            )
            conn.commit()
            user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Username already exists")
        return {"id": user_id, "username": payload.username, "role": payload.role}


@router.post("/create_class")
@sl_limiter.limit("1000/hour")
async def create_class(request: Request, payload: CreateClassRequest, session_data: dict = Depends(require_role(4))):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO classes(name) VALUES(?)", (payload.name,))
            conn.commit()
            class_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Class already exists")
        return {"id": class_id, "name": payload.name}
    
@router.post("/send-all")
@sl_limiter.limit("10/hour")
async def send_push_all(request: Request, title: str = Form(..., max_length=100), body: str = Form(..., max_length=800), session_data: dict = Depends(require_role(4))):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT endpoint, p256dh, auth FROM push_subscriptions")
        
        subs = []
        for row in cursor.fetchall():
            sub = {
                "endpoint": row["endpoint"],
                "keys": {"p256dh": row["p256dh"], "auth": row["auth"]}
            }
            subs.append(sub)
        
        successful = 0
        for subscription_info in subs:
            try:
                response = webpush(
                    subscription_info=subscription_info,
                    data=json.dumps({"title": title, "body": body, "icon": "/icon.png"}),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": VAPID_EMAIL}
                )
                successful += 1
            except Exception as e:
                print(f"Failed to send push to {subscription_info['endpoint']} - {str(e)}")
        
        return {
            "sent": successful,
            "failed": len(subs) - successful,
            "total": len(subs),
            "target": "ALLE NUTZER"
        }

@router.post("/send-user")
@sl_limiter.limit("200/hour")
async def send_push_user(
    request: Request,
    user_id: int = Form(..., ge=0, le=9999), 
    title: str = Form(..., max_length=100), 
    body: str = Form(..., max_length=800), 
    session_data: dict = Depends(require_role(4))
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT endpoint, p256dh, auth FROM push_subscriptions 
            WHERE user_id = ?
        """, (user_id,))
        
        subs = []
        row = cursor.fetchone()
        if row:
            sub = {
                "endpoint": row["endpoint"],
                "keys": {"p256dh": row["p256dh"], "auth": row["auth"]}
            }
            subs.append(sub)
        
        if not subs:
            return {"sent": 0, "failed": 0, "total": 0, "error": "Kein User oder keine Subscription"}
        
        successful = 0
        for subscription_info in subs:
            try:
                response = webpush(
                    subscription_info=subscription_info,
                    data=json.dumps({"title": title, "body": body, "icon": "/icon.png"}),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": "mailto:noreply@deineapp.de"}
                )
                successful += 1
            except:
                pass
        
        return {
            "sent": successful,
            "failed": len(subs) - successful,
            "total": len(subs),
            "target": f"USER #{user_id}"
        }