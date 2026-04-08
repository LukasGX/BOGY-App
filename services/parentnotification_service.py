import fcntl
import json
import os
import portalocker
from pathlib import Path
import tempfile
from api.v1.deps import get_db

def get_parentnotifications_s(session_data, filter_user_id=True):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                pn.title,
                pn.body,
                pn.feedback,
                pn.attachments,
                pn.user_ids,
                pn.created_at
            FROM parentnotifications pn
        """)
        notifications = cursor.fetchall()

        if filter_user_id:
            for notification in notifications:
                user_ids = notification["user_ids"].split(";")
                if not str(session_data["user_id"]) in user_ids:
                    notifications.remove(notification)

        return {"parent_notifications": notifications}
    
def feedback_s(session_data, notification_id, feedback):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM parentnotifications WHERE id = ?", (notification_id,))
        check_row = cursor.fetchone()
        if not check_row:
            return {"error": "Notification not found"}
        
        file = Path(f"parent_notification_feedback/{notification_id}.json")
        file.parent.mkdir(exist_ok=True)
        
        with open(file, 'r+', encoding='utf-8') as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            
            f.seek(0)
            
            try:
                data = json.load(f)
            except:
                data = {}
            
            if "feedbacks" not in data:
                data["feedbacks"] = {}
            
            user_id = str(session_data["user_id"])
            data["feedbacks"][user_id] = feedback
            
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=4)
            f.flush()
            
            portalocker.unlock(f)
    
    return {"status": "success"}

def get_feedback_s(session_data, notification_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM parentnotifications WHERE id = ?", (notification_id,))
        check_row = cursor.fetchone()
        if not check_row:
            return {"error": "Notification not found"}
        
        file = Path(f"parent_notification_feedback/{notification_id}.json")
        
        with open(file, "r", encoding='utf-8') as f:
            data = json.load(f)

        return {"notification": notification_id, "data": data}