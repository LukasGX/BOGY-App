from datetime import datetime

from api.v1.deps import get_db


def _parse_expiry(value):
    """Wandelt einen Ablaufzeitpunkt aus der DB in lokale, zeitzonenlose Zeit um."""
    if not value:
        return None
    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        # Zeitzonenangabe vorhanden -> in lokale Zeit umrechnen
        dt = dt.astimezone().replace(tzinfo=None)
    return dt


def _is_expired(value, now=None):
    """Prueft, ob ein Code abgelaufen ist.

    Ein nicht parsebares Ablaufdatum gilt bewusst NICHT als abgelaufen,
    damit Codes nicht ungefragt verschwinden.
    """
    now = now or datetime.now()
    dt = _parse_expiry(value)
    if dt is None:
        return False
    return dt <= now


def _cleanup_expired(conn):
    """Entfernt abgelaufene Codes.

    Der Vergleich passiert in Python, weil SQLite CURRENT_TIMESTAMP in UTC
    rechnet, die Ablaufdaten aber in lokaler Zeit gespeichert sind. Ein
    Vergleich als String wuerde Codes in der Sommerzeit um zwei Stunden
    zu spaet ablaufen lassen.
    """
    cursor = conn.cursor()
    now = datetime.now()
    rows = cursor.execute("SELECT id, expiry FROM wlan_codes").fetchall()
    expired = [r["id"] for r in rows if _is_expired(r["expiry"], now)]
    if expired:
        placeholders = ",".join("?" for _ in expired)
        cursor.execute(f"DELETE FROM wlan_codes WHERE id IN ({placeholders})", expired)
        conn.commit()


def _user_matches(user_ids_field, user_id):
    """Prueft, ob ein Nutzer (oder 'all') in der Empfaengerliste eines Codes steht.

    Das Feld user_ids hat in der bestehenden Datenbank INTEGER-Affinitaet,
    einzelne User-IDs werden daher als Zahl gespeichert -> immer als String
    normalisieren.
    """
    if user_ids_field is None:
        return False
    raw = str(user_ids_field).strip()
    if raw == "all":
        return True
    if raw == str(user_id):
        return True
    parts = [u for u in raw.split(";") if u]
    return str(user_id) in parts


def get_wlan_codes(session_data):
    """Alle Codes, die fuer den angemeldeten Nutzer bestimmt sind."""
    with get_db() as conn:
        cursor = conn.cursor()

        _cleanup_expired(conn)

        now = datetime.now()
        rows = cursor.execute("""
            SELECT id, code, expiry, user_ids FROM wlan_codes
        """).fetchall()

        codes = []
        for row in rows:
            if _is_expired(row["expiry"], now):
                continue
            if not _user_matches(row["user_ids"], session_data["user_id"]):
                continue
            codes.append({"code": row["code"], "expiry": row["expiry"], "id": row["id"]})

        return {"codes": codes}


def get_all_wlan_codes():
    """Alle Codes unabhaengig vom Empfaenger (nur fuer die Verwaltung)."""
    with get_db() as conn:
        cursor = conn.cursor()

        _cleanup_expired(conn)

        now = datetime.now()
        rows = cursor.execute("""
            SELECT id, code, expiry, user_ids FROM wlan_codes
            ORDER BY expiry ASC
        """).fetchall()

        codes = []
        for row in rows:
            if _is_expired(row["expiry"], now):
                continue
            codes.append({
                "code": row["code"],
                "expiry": row["expiry"],
                "id": row["id"],
                "user_ids": str(row["user_ids"]) if row["user_ids"] is not None else "",
            })

        return {"codes": codes}


def add_wlan_code_s(users, code, expiry):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("INSERT INTO wlan_codes (user_ids, code, expiry) VALUES (?, ?, ?)", (users, code, expiry),)
        conn.commit()

        return {"status": "success", "code":{"code": code, "users": users, "expiry": expiry}}
