import json
import secrets
import sqlite3
from fastapi import HTTPException
import webpush
from api.v1.deps import get_db, hash_password
from definitions import VAPID_EMAIL, VAPID_PRIVATE_KEY

def create_user_s(payload):
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
    
def create_class_s(payload):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO classes(name) VALUES(?)", (payload.name,))
            conn.commit()
            class_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Class already exists")
        return {"id": class_id, "name": payload.name}
    
def push_all(title, body):
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
    
def push_user(user_id, title, body):
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
    
def delete_class_s(class_id):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(id) AS student_count FROM users WHERE class = ?", (class_id,))
        count_row = cursor.fetchone()
        if not count_row:
            raise HTTPException(status_code=404, detail="Class not found")

        if count_row[0] > 0:
            cursor.execute("""
                SELECT id, firstname, lastname, username 
                FROM users 
                WHERE class = ?
            """, (class_id,))
            all_students = [dict(row) for row in cursor.fetchall()]
            
            raise HTTPException(
                status_code=409,
                detail=[
                    {
                        "message": "Class has users assigned, cannot delete",
                        "users": all_students
                    }
                ]
            )

        cursor.execute("DELETE FROM classes WHERE id = ?", (class_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Class not found")
        conn.commit()
        return {"status": "success"}
    
def delete_user_s(user_id):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
        return {"status": "success"}
    
def reset_user_password_s(user_id):
    with get_db() as conn:
        cursor = conn.cursor()

        new_password = secrets.token_hex(8)
        hashed = hash_password(new_password)

        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, user_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
        return {"status": "success", "new_password": new_password}