import json
from pywebpush import webpush, WebPushException
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

from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

# Load VAPID credentials from environment for security (set in .env)
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_EMAIL = os.getenv("VAPID_EMAIL")

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="3PlRPaH7vpCUmWCy9S9SkXy2ia3ezj5dLCCQb5zhzQy5cvcM6Z", same_site="lax")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Später einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/app", StaticFiles(directory="pwa", html=True), name="pwa")

DB_PATH = "data.db"

class CreateUserRequest(BaseModel):
    username: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    password: str
    role: str
    class_id: Optional[int] = Field(None, alias="class")

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict  # {p256dh, auth}

class CreateClassRequest(BaseModel):
    name: str

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

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM roles WHERE name = ?", (user_role,))
        row = cursor.fetchone()
        conn.close()
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
async def login(request: Request, username: str = Form(...), pw: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT u.id, u.username, u.firstname, u.lastname, u.password, r.name as role, u.class as class "
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
    request.session["class"] = row["class"]

    return RedirectResponse(url="/app/index.html", status_code=302)

@app.get("/profile")
async def profile(session_data: dict = Depends(LoggedIn)):
    # return session_data

    conn = get_db()
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
        conn.close()
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
    # validate class id if provided
    class_id = payload.class_id
    if class_id is not None:
        cursor.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
        if not cursor.fetchone():
            conn.close()
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
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    conn.close()
    return {"id": user_id, "username": payload.username, "role": payload.role}


@app.post("/create_class")
async def create_class(payload: CreateClassRequest):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO classes(name) VALUES(?)", (payload.name,))
        conn.commit()
        class_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Class already exists")
    conn.close()
    return {"id": class_id, "name": payload.name}


@app.get("/register-tutoring")
async def register_tutoring(request: Request, session_data: dict = Depends(LoggedIn)):
    q = request.query_params

    conn = get_db()
    cursor = conn.cursor()

    subject_names = request.query_params.getlist("subject")
    subject_ids = []
    for name in subject_names:
        cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
        s = cursor.fetchone()
        if not s:
            conn.close()
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
        conn.close()
        raise HTTPException(status_code=400, detail="Could not create tutoring entry")
    conn.close()

    return {"id": tutoring_id, "user": session_data["user_id"], "subjects": subject_ids}



@app.get("/edit-tutor-profile")
async def edit_tutor_profile(request: Request, session_data: dict = Depends(LoggedIn)):
    # allow teachers to update their tutoring subjects (insert if none exists)
    subject_names = request.query_params.getlist("subject")

    conn = get_db()
    cursor = conn.cursor()

    subject_ids = []
    for name in subject_names:
        cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
        s = cursor.fetchone()
        if not s:
            conn.close()
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
        conn.close()
        raise HTTPException(status_code=400, detail="Could not update tutoring entry")
    conn.close()

    return {"id": tutoring_id, "user": session_data["user_id"], "subjects": subject_ids}

@app.get("/search-tutors")
async def search_tutors(request: Request):
    # collect requested subject names from query params
    subject_names = request.query_params.getlist("subject")
    if not subject_names:
        return {"results": [], "count": 0}

    conn = get_db()
    cursor = conn.cursor()

    # resolve provided subject names to ids
    placeholders = ",".join("?" for _ in subject_names)
    cursor.execute(f"SELECT id, name FROM subjects WHERE name IN ({placeholders})", tuple(subject_names))
    found = cursor.fetchall()
    if not found:
        conn.close()
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

    conn.close()
    return {"results": results, "count": len(results)}


@app.get("/get-subjects")
async def get_subjects(session_data: dict = Depends(LoggedIn)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM subjects ORDER BY name")
    all_subs = cursor.fetchall()

    cursor.execute("SELECT subjects FROM tutoring WHERE user = ?", (session_data["user_id"],))
    row = cursor.fetchone()
    user_sub_ids = []
    if row and row["subjects"]:
        user_sub_ids = [int(s) for s in row["subjects"].split(",") if s]

    id_to_name = {r["id"]: r["name"] for r in all_subs}
    conn.close()

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
async def push_subscribe(
    payload: PushSubscription, 
    session_data: dict = Depends(LoggedIn)
):
    conn = get_db()
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
        conn.close()
        return {"status": "subscribed", "user_id": session_data["user_id"]}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(409, "Subscription already exists")


@app.delete("/api/push/subscribe/{endpoint}")
async def push_unsubscribe(
    endpoint: str,
    session_data: dict = Depends(LoggedIn)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM push_subscriptions WHERE user_id = ? AND endpoint = ?",
        (session_data["user_id"], endpoint)
    )
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return {"deleted": deleted > 0}

@app.post("/api/push/send-all")
async def send_push_all(title: str = Form(...), body: str = Form(...), session_data: dict = Depends(LoggedIn)):
    print(f"Sending push to all users: {title}")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT endpoint, p256dh, auth FROM push_subscriptions")
    
    subs = []
    for row in cursor.fetchall():
        sub = {
            "endpoint": row["endpoint"],
            "keys": {"p256dh": row["p256dh"], "auth": row["auth"]}
        }
        subs.append(sub)
    
    conn.close()
    
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
        except Exception as e:
            print(f"Failed to send push to {subscription_info['endpoint']} - {str(e)}")
    
    return {
        "sent": successful,
        "failed": len(subs) - successful,
        "total": len(subs),
        "target": "ALLE NUTZER"
    }

@app.post("/api/push/send-user")
async def send_push_user(
    user_id: int = Form(...), 
    title: str = Form(...), 
    body: str = Form(...), 
    session_data: dict = Depends(LoggedIn)
):
    conn = get_db()
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
    
    conn.close()
    
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
    conn = get_db()
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
    conn.close()
    
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