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