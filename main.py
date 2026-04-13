from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from starlette.middleware.sessions import SessionMiddleware

# import deps
from api.v1.deps import get_db

# import routers
from api.v1.routers import administration, wlan, push, tutoring, parentnotification, user, data, admin_dashboard, pw, importing

# import definitions
from definitions import sl_limiter, SECRET_KEY

is_production = os.getenv("ENV") == "production"

app = FastAPI()

app.state.limiter = sl_limiter
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

app.include_router(administration.router, prefix="/api/v1/administration", tags=["administration"])
app.include_router(wlan.router, prefix="/api/v1/wlan", tags=["wlan"])
app.include_router(push.router, prefix="/api/v1/push", tags=["push"])
app.include_router(tutoring.router, prefix="/api/v1/tutoring", tags=["tutoring"])
app.include_router(parentnotification.router, prefix="/api/v1/parentnotification", tags=["parentnotification"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(pw.router, prefix="/api/v1/pw", tags=["pw"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
app.include_router(admin_dashboard.router, prefix="/dashboard", tags=["admin_dashboard"])
app.include_router(importing.router, prefix="/api/v1/import", tags=["import"])

app.mount("/app", StaticFiles(directory="pwa", html=True), name="pwa")
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.mount("/files", StaticFiles(directory="public_files"), name="files")

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                german_name TEXT UNIQUE NOT NULL
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
                name TEXT UNIQUE NOT NULL,
                german_name TEXT UNIQUE NOT NULL
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wlan_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_ids INTEGER NOT NULL,
                code TEXT NOT NULL,
                expiry DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parentnotifications (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                feedback TEXT NOT NULL,
                attachments TEXT,
                user_ids TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_keys (
                user_id INTEGER PRIMARY KEY,
                hashed_key TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                encrypted_value TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id, name)
            )
        """)

        # settings
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")

        # seed subjects
        subjects = {
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
            "nut": "Natur und Technik",
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
            "ethics": "Ethik"
        }
        for s in subjects.keys():
            cursor.execute("INSERT OR IGNORE INTO subjects(name, german_name) VALUES(?, ?)", (s, subjects[s],))
        
        # seed roles
        roles = {
            "student": "Schüler",
            "teacher": "Lehrer",
            "parent": "Elternteil",
            "administration": "Verwaltung"
        }
        for r in roles.keys():
            cursor.execute("INSERT OR IGNORE INTO roles(name, german_name) VALUES(?, ?)", (r, roles[r],))

        # standard user
        cursor.execute("INSERT OR IGNORE INTO users (username, firstname, lastname, password, role, class) VALUES ('admin', 'Max', 'Mustermann', '$argon2id$v=19$m=65536,t=3,p=4$rv8/JsLAAwnC8sC/T2cabw$bMBb9Xycyd5MMFXvEF3ni2KCcfROc/jMrIM9sGk70U8', '4', NULL)") # pw: AdminPW (change!)

        conn.commit()


init_db()

# ROOT
@app.get("/")
async def root():
    return RedirectResponse(url="/app/index.html", status_code=302)