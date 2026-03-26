import sqlite3
from fastapi import HTTPException
from api.v1.deps import get_db

def subscribe(session_data, payload):
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
        
def unsubscribe(session_data, endpoint):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM push_subscriptions WHERE user_id = ? AND endpoint = ?",
            (session_data["user_id"], endpoint)
        )
        conn.commit()
        deleted = cursor.rowcount
        return {"deleted": deleted > 0}
    
def status(session_data):
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