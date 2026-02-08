from fastapi import Depends, FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
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
    class_id: Optional[int] = Field(None, alias="class")


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
# PAGES
@app.get("/home")
async def home(session_data: dict = Depends(LoggedIn)):
    return {"message": f"Welcome to the home page, {session_data['username']}!"}