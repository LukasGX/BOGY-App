import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Request
from api.v1.deps import LoggedIn, get_db
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
    with get_db() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
                VALUES (?, ?, ?, ?)
            """, (
                session_data["user_id"],
                payload.endpoint,
                payload.keys["p256dh"],
                payload.keys["auth"]
            ))
            conn.commit()
            return {"status": "subscribed", "user_id": session_data["user_id"]}
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Subscription already exists")


@router.delete("/subscribe/{endpoint}")
async def push_unsubscribe(
    endpoint: str,
    session_data: dict = Depends(LoggedIn)
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM push_subscriptions WHERE user_id = ? AND endpoint = ?",
            (session_data["user_id"], endpoint)
        )
        conn.commit()
        deleted = cursor.rowcount
        return {"deleted": deleted > 0}

@router.get("/status")
async def get_push_status(session_data: dict = Depends(LoggedIn)):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                u.username,
                u.firstname,
                u.lastname,
                COUNT(ps.id) as subscription_count,
                MAX(ps.created_at) as last_subscription
            FROM users u 
            LEFT JOIN push_subscriptions ps ON u.id = ps.user_id 
            WHERE u.id = ?
            GROUP BY u.id
        """, (session_data.get("user_id"),))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(404, "User nicht gefunden")
        
        status = {
            "user_id": session_data.get("user_id"),
            "username": result["username"],
            "has_push": result["subscription_count"] > 0,
            "subscription_count": result["subscription_count"],
            "last_subscription": result["last_subscription"]
        }
        
        return status