import json
from pywebpush import webpush
from fastapi import Depends, FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlite3
import os
from dotenv import load_dotenv
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from contextlib import contextmanager

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

is_production = os.getenv("ENV") == "production"

# Load VAPID credentials from environment for security (set in .env)
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_EMAIL = os.getenv("VAPID_EMAIL")
SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

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

app = FastAPI()

limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="strict",
    https_only=is_production,
    max_age=60*60*24*7 # 7 days
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Später einschränken
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
app.mount("/app", StaticFiles(directory="pwa", html=True), name="pwa")

DB_PATH = "data.db"

class CreateUserRequest(BaseModel):
    username: str = Field(..., max_length=50)
    firstname: Optional[str] = Field(..., max_length=50)
    lastname: Optional[str] = Field(..., max_length=50)
    password: str = Field(..., max_length=50)
    role: str = Field(..., max_length=15)
    class_id: Optional[int] = Field(None, alias="class", ge=0, le=9999)

class PushSubscription(BaseModel):
    endpoint: str = Field(..., max_length=500)
    keys: dict[str, str]

class CreateClassRequest(BaseModel):
    name: str = Field(..., max_length=50)

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


def init_db():
    with get_db() as conn:
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
                class INTEGER,
                FOREIGN KEY(role) REFERENCES roles(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tutoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user INTEGER NOT NULL,
                subjects TEXT,
                FOREIGN KEY(user) REFERENCES users(id)
            )
            """
        )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                endpoint TEXT NOT NULL,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(endpoint)
            )
        """)

        # settings
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")

        # seed subjects
        subjects = [
            "german",
            "english",
            "french",
            "latin",
            "spanish",
            "italian",
            "maths",
            "physics",
            "chemistry",
            "biology",
            "cs",
            "nut",
            "history",
            "geography",
            "economics",
            "politics",
            "business-cs",
            "art",
            "music",
            "pe",
            "catholic",
            "evangelic",
            "ethics",
        ]
        for s in subjects:
            cursor.execute("INSERT OR IGNORE INTO subjects(name) VALUES(?)", (s,))
        
        roles = ["student", "teacher", "parent", "administration"]
        for r in roles:
            cursor.execute("INSERT OR IGNORE INTO roles(name) VALUES(?)", (r,))
        conn.commit()


init_db()

# DEPENDENCIES
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

# ROOT
@app.get("/")
async def root():
    raise HTTPException(status_code=404, detail="Not Found")

# USERS
@app.post("/login")
@limiter.limit("3/minute")
async def login(request: Request, username: str = Form(..., max_length=50), pw: str = Form(..., max_length=50)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT u.id, u.username, u.firstname, u.lastname, u.password, r.name as role, u.class as class "
            "FROM users u LEFT JOIN roles r ON u.role = r.id WHERE u.username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if not row or not verify_password(pw, row["password"]):
            return RedirectResponse(url="/app/wrong_credentials.html", status_code=302)

        request.session.clear()
        request.session["user_id"] = row["id"]
        request.session["username"] = row["username"]
        request.session["firstname"] = row["firstname"]
        request.session["lastname"] = row["lastname"]
        request.session["role"] = row["role"]
        request.session["class"] = row["class"]

    return RedirectResponse(url="/app/index.html", status_code=302)

@app.get("/profile")
async def profile(session_data: dict = Depends(LoggedIn)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.id,
            u.username,
            u.firstname,
            u.lastname,
            r.name as role,
            c.name as class,
            CASE 
                WHEN t.user IS NULL THEN 0
                ELSE 1
            END AS tutoring,
            t.subjects AS tutoring_subjects
            FROM users u
            LEFT JOIN roles r ON u.role = r.id
            LEFT JOIN classes c ON u.class = c.id
            LEFT JOIN tutoring t ON u.id = t.user
            WHERE u.id = ?""",
            (session_data["user_id"],),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="Internal server error")
        
        data = dict(row)
        
        if data["tutoring"] == 0: data["tutoring"] = False
        else: data["tutoring"] = True

        return data

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"success": True}

@app.post("/create_user")
@limiter.limit("3/hour")
async def create_user(request:Request, payload: CreateUserRequest):
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


@app.post("/create_class")
@limiter.limit("5/hour")
async def create_class(request: Request, payload: CreateClassRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO classes(name) VALUES(?)", (payload.name,))
            conn.commit()
            class_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Class already exists")
        return {"id": class_id, "name": payload.name}


@app.get("/register-tutoring")
async def register_tutoring(request: Request, session_data: dict = Depends(LoggedIn)):
    with get_db() as conn:
        q = request.query_params
        cursor = conn.cursor()

        subject_names = request.query_params.getlist("subject")
        subject_ids = []
        for name in subject_names:
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
            s = cursor.fetchone()
            if not s:
                raise HTTPException(status_code=400, detail=f"Invalid subject: {name}")
            subject_ids.append(str(s["id"]))

        subjects_field = ",".join(subject_ids) if subject_ids else None

        try:
            cursor.execute(
                "INSERT INTO tutoring(user, subjects) VALUES(?,?)",
                (session_data["user_id"], subjects_field),
            )
            conn.commit()
            tutoring_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Could not create tutoring entry")

        return RedirectResponse(url="/app/tutoring_registering_success.html", status_code=302)

@app.get("/edit-tutor-profile")
async def edit_tutor_profile(request: Request, session_data: dict = Depends(LoggedIn)):
    with get_db() as conn:
        subject_names = request.query_params.getlist("subject")
        cursor = conn.cursor()

        subject_ids = []
        for name in subject_names:
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
            s = cursor.fetchone()
            if not s:
                raise HTTPException(status_code=400, detail=f"Invalid subject: {name}")
            subject_ids.append(str(s["id"]))

        subjects_field = ",".join(subject_ids) if subject_ids else None

        cursor.execute("SELECT id FROM tutoring WHERE user = ?", (session_data["user_id"],))
        existing = cursor.fetchone()
        try:
            if existing:
                cursor.execute("UPDATE tutoring SET subjects = ? WHERE user = ?", (subjects_field, session_data["user_id"]))
                tutoring_id = existing["id"]
            else:
                cursor.execute("INSERT INTO tutoring(user, subjects) VALUES(?,?)", (session_data["user_id"], subjects_field))
                tutoring_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Could not update tutoring entry")

        return {"id": tutoring_id, "user": session_data["user_id"], "subjects": subject_ids}

@app.get("/search-tutors")
@limiter.limit("5/minute")
async def search_tutors(request: Request):
    with get_db() as conn:
        # collect requested subject names from query params
        subject_names = request.query_params.getlist("subject")
        if not subject_names:
            return {"results": [], "count": 0}

        cursor = conn.cursor()

        # resolve provided subject names to ids
        placeholders = ",".join("?" for _ in subject_names)
        cursor.execute(f"SELECT id, name FROM subjects WHERE name IN ({placeholders})", tuple(subject_names))
        found = cursor.fetchall()
        if not found:
            return {"results": [], "count": 0}

        searched_ids = {str(r["id"]) for r in found}

        # build id->name map for all subjects
        cursor.execute("SELECT id, name FROM subjects")
        all_subs = cursor.fetchall()
        id_to_name = {str(r["id"]): r["name"] for r in all_subs}

        # fetch tutoring entries joined with user info
        cursor.execute(
            "SELECT t.id as tutoring_id, t.user as user_id, t.subjects, u.username, u.firstname, u.lastname, r.name as role, c.name as class "
            "FROM tutoring t JOIN users u ON t.user = u.id LEFT JOIN roles r ON u.role = r.id LEFT JOIN classes c ON u.class = c.id"
        )

        results = []
        for row in cursor.fetchall():
            subjects_field = row["subjects"]
            if not subjects_field:
                continue
            subject_ids = [s for s in subjects_field.split(",") if s]

            # match if any selected subject id is present
            if not (set(subject_ids) & searched_ids):
                continue

            subject_labels = {
                "german": "Deutsch",
                "english": "Englisch",
                "french": "Französisch",
                "latin": "Latein",
                "spanish": "Spanisch",
                "italian": "Italienisch",
                "maths": "Mathematik",
                "physics": "Physik",
                "chemistry": "Chemie",
                "biology": "Biologie",
                "cs": "Informatik",
                "nut": "Natur und Technik (NuT)",
                "history": "Geschichte",
                "geography": "Geographie",
                "economics": "Wirtschaft und Recht",
                "politics": "Politik und Gesellschaft",
                "business-cs": "Wirtschaftsinformatik",
                "art": "Kunst",
                "music": "Musik",
                "pe": "Sport",
                "catholic": "Katholische Religionslehre",
                "evangelic": "Evangelische Religionslehre",
                "ethics": "Ethik",
            }

            # include all users who created a tutoring entry; expose role as well
            # translate stored subject ids -> code names -> German labels
            results.append(
                {
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "firstname": row["firstname"],
                    "lastname": row["lastname"],
                    "class": row["class"],
                    "role": row["role"],
                    "subjects": [
                        subject_labels.get(id_to_name.get(s, s), id_to_name.get(s, s))
                        for s in subject_ids
                    ],
                }
            )

        return {"results": results, "count": len(results)}


@app.get("/get-subjects")
async def get_subjects(session_data: dict = Depends(LoggedIn)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM subjects ORDER BY name")
        all_subs = cursor.fetchall()

        cursor.execute("SELECT subjects FROM tutoring WHERE user = ?", (session_data["user_id"],))
        row = cursor.fetchone()
        user_sub_ids = []
        if row and row["subjects"]:
            user_sub_ids = [int(s) for s in row["subjects"].split(",") if s]

        id_to_name = {r["id"]: r["name"] for r in all_subs}

        return {
            "subjects": [{"id": r["id"], "name": r["name"]} for r in all_subs],
            "user_subject_ids": user_sub_ids,
            "user_subjects": [id_to_name.get(i) for i in user_sub_ids],
        }

# PAGES
@app.get("/home")
async def home(session_data: dict = Depends(LoggedIn)):
    return {"message": f"Welcome to the home page, {session_data['username']}!"}

# PUSH NOTIFICATIONS
@app.post("/api/push/subscribe")
@limiter.limit("5/minute")
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


@app.delete("/api/push/subscribe/{endpoint}")
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

@app.post("/api/push/send-all")
@limiter.limit("10/hour")
async def send_push_all(request: Request, title: str = Form(..., max_length=100), body: str = Form(..., max_length=800), session_data: dict = Depends(require_role(4))):
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

@app.post("/api/push/send-user")
@limiter.limit("10/hour")
async def send_push_user(
    request: Request,
    user_id: int = Form(..., ge=0, le=9999), 
    title: str = Form(..., max_length=100), 
    body: str = Form(..., max_length=800), 
    session_data: dict = Depends(require_role(4))
):
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

@app.get("/api/push/status")
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