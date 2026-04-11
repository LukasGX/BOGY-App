from contextlib import contextmanager
import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, Request

DB_PATH = "data.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

async def get_db_conn():
    with get_db() as conn:
        yield conn

async def LoggedIn(request: Request):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="Login required")
    return request.session

def require_role(*allowed_roles: int):
    async def _role(request: Request):
        with get_db() as conn:
            session_data = await LoggedIn(request)
            user_role = session_data["role"]

            cursor = conn.cursor()
            cursor.execute("SELECT id FROM roles WHERE name = ?", (user_role,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(403, "Invalid user role")
            user_role = row["id"]
            
            if user_role not in allowed_roles:
                raise HTTPException(403, f"Allowed roles: {allowed_roles}, you are: {user_role}")
            return session_data
    return _role

# argon2 password hasher
ph = PasswordHasher()

def hash_password(password: str, salt="") -> str:
    return ph.hash(password, salt=salt)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False