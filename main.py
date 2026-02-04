from fastapi import Depends, FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import os
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from starlette.middleware.sessions import SessionMiddleware


app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="3PlRPaH7vpCUmWCy9S9SkXy2ia3ezj5dLCCQb5zhzQy5cvcM6Z", same_site="lax")
app.mount("/app", StaticFiles(directory="pwa", html=True), name="pwa")

DB_PATH = "data.db"

class CreateUserRequest(BaseModel):
    username: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    password: str
    role: str


# argon2 password hasher
ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            firstname TEXT,
            lastname TEXT,
            password TEXT NOT NULL,
            role INTEGER,
            FOREIGN KEY(role) REFERENCES roles(id)
        )
        """
    )
    roles = ["student", "teacher", "parent", "administration"]
    for r in roles:
        cursor.execute("INSERT OR IGNORE INTO roles(name) VALUES(?)", (r,))
    conn.commit()
    conn.close()


init_db()

# DEPENDENCIES
async def LoggedIn(request: Request):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="Login required")
    return request.session

def require_role(*allowed_roles: int):
    async def _role(request: Request):
        session_data = await LoggedIn(request)
        user_role = session_data["role"]
        
        if user_role not in allowed_roles:
            raise HTTPException(403, f"Allowed roles: {allowed_roles}")
        return session_data
    return _role

# ROOT
@app.get("/")
async def root():
    raise HTTPException(status_code=404, detail="Not Found")

# USERS
@app.post("/login")
async def login(request: Request, username: str = Form(...), pw: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT u.id, u.username, u.firstname, u.lastname, u.password, r.name as role "
        "FROM users u LEFT JOIN roles r ON u.role = r.id WHERE u.username = ?",
        (username,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row or not verify_password(pw, row["password"]):
        return RedirectResponse(url="/app/wrong_credentials.html", status_code=302)

    request.session["user_id"] = row["id"]
    request.session["username"] = row["username"]
    request.session["firstname"] = row["firstname"]
    request.session["lastname"] = row["lastname"]
    request.session["role"] = row["role"]

    return RedirectResponse(url="/app/index.html", status_code=302)

@app.get("/profile")
async def profile(session_data: dict = Depends(LoggedIn)):
    return session_data

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"success": True}

@app.post("/create_user")
async def create_user(payload: CreateUserRequest):
    conn = get_db()
    cursor = conn.cursor()
    # find role id
    cursor.execute("SELECT id FROM roles WHERE name = ?", (payload.role,))
    role_row = cursor.fetchone()
    if not role_row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid role")
    role_id = role_row["id"]
    # hash password
    hashed = hash_password(payload.password)
    try:
        cursor.execute(
            "INSERT INTO users(username, firstname, lastname, password, role) VALUES(?,?,?,?,?)",
            (payload.username, payload.firstname, payload.lastname, hashed, role_id),
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    conn.close()
    return {"id": user_id, "username": payload.username, "role": payload.role}

# PAGES
@app.get("/home")
async def home(session_data: dict = Depends(LoggedIn)):
    return {"message": f"Welcome to the home page, {session_data['username']}!"}