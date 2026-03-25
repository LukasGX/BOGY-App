from fastapi import APIRouter, Depends
from api.v1.deps import LoggedIn, get_db, require_role

router = APIRouter()

@router.get("/")
async def wlan_codes(session_data: dict = Depends(LoggedIn)):
    with get_db() as conn:
        cursor = conn.cursor()

        # remove expired codes first
        cursor.execute("DELETE FROM wlan_codes WHERE expiry <= CURRENT_TIMESTAMP")
        conn.commit()

        uid = str(session_data["user_id"])
        exact = uid
        prefix = uid + ";%"
        suffix = "%;" + uid
        in_middle = "%;" + uid + ";%"

        cursor.execute(
            """
            SELECT code, expiry FROM wlan_codes
            WHERE (user_ids = 'all' OR user_ids = ? OR user_ids LIKE ? OR user_ids LIKE ? OR user_ids LIKE ?)
            AND expiry > CURRENT_TIMESTAMP
            """,
            (exact, prefix, suffix, in_middle),
        )

        codes = []
        for row in cursor.fetchall():
            codes.append({"code": row["code"], "expiry": row["expiry"]})

        return {"codes": codes}
    
@router.post("/")
async def add_wlan_code(code: str, users: str, expiry: str, session_data: dict = Depends(require_role(4))):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("INSERT INTO wlan_codes (user_ids, code, expiry) VALUES (?, ?, ?)", (users, code, expiry),)
        conn.commit()

        return {"status": "success", "code":{"code": code, "users": users, "expiry": expiry}}