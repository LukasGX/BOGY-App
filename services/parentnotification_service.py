import json
import os
from pathlib import Path
import tempfile

import portalocker
from fastapi import HTTPException

from api.v1.deps import get_db

# Verzeichnis fuer die Rueckmeldungsdateien. Ueberschreibbar per Umgebungsvariable.
FEEDBACK_DIR = os.getenv("FEEDBACK_DIR", "parent_notification_feedback")


def _user_is_recipient(user_ids_field: str, user_id) -> bool:
    """Prueft, ob der Nutzer (oder alle) in der Empfaengerliste steht."""
    user_ids = [u for u in (user_ids_field or "").split(";") if u]
    if "all" in user_ids:
        return True
    return str(user_id) in user_ids


def get_parentnotifications_s(session_data, filter_user_id=True):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                pn.id,
                pn.title,
                pn.body,
                pn.feedback,
                pn.attachments,
                pn.user_ids,
                pn.created_at
            FROM parentnotifications pn
            ORDER BY pn.created_at ASC
        """)
        notifications = cursor.fetchall()

        if filter_user_id:
            # Neue Liste bauen statt waehrend der Iteration zu entfernen
            # (remove() wuerde sonst jedes zweite Element ueberspringen).
            notifications = [
                n for n in notifications
                if _user_is_recipient(n["user_ids"], session_data["user_id"])
            ]

        return {"parent_notifications": notifications}


def feedback_s(session_data, notification_id, feedback):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_ids FROM parentnotifications WHERE id = ?", (notification_id,))
        check_row = cursor.fetchone()
        if not check_row:
            return {"error": "Notification not found"}

        # Nur Empfaenger duerfen Rueckmeldungen abgeben
        if not _user_is_recipient(check_row["user_ids"], session_data["user_id"]):
            raise HTTPException(status_code=403, detail="You are not a recipient of this notification")

        file = Path(FEEDBACK_DIR) / f"{notification_id}.json"
        file.parent.mkdir(parents=True, exist_ok=True)

        # Ein eigener Lock-File serialisiert gleichzeitige Schreibvorgaenge.
        # Die eigentliche Datei wird atomar ersetzt, damit Leser nie eine
        # halb geschriebene Datei sehen.
        lock_path = file.with_name(file.name + ".lock")
        with portalocker.Lock(str(lock_path), mode="w", timeout=10):
            data = {}
            if file.exists():
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, ValueError, OSError):
                    data = {}

            if not isinstance(data, dict):
                data = {}
            if not isinstance(data.get("feedbacks"), dict):
                data["feedbacks"] = {}

            data["feedbacks"][str(session_data["user_id"])] = feedback

            fd, tmp_path = tempfile.mkstemp(dir=str(file.parent), prefix=file.name, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, file)
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

    return {"status": "success"}


def get_feedback_s(session_data, notification_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM parentnotifications WHERE id = ?", (notification_id,))
        check_row = cursor.fetchone()
        if not check_row:
            return {"error": "Notification not found"}

        file = Path(FEEDBACK_DIR) / f"{notification_id}.json"

        if not file.exists():
            return {"notification": notification_id, "notification_title": check_row["title"], "error": "Notification feedback not found"}

        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, ValueError, OSError):
            data = {}

        return {"notification": notification_id, "notification_title": check_row["title"], "data": data}


def create_parentnotification_s(session_data, title, body, feedback, attachments, user_ids):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO parentnotifications (title, body, feedback, attachments, user_ids) VALUES (?, ?, ?, ?, ?)", (title, body, feedback, attachments, user_ids,))
        conn.commit()
        return {"id": cursor.lastrowid, "status": "success"}
