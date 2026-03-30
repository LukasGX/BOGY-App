from fastapi import Depends, FastAPI
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
from api.v1.routers import administration, wlan, push, tutoring, user, data, admin_dashboard

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
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
app.include_router(admin_dashboard.router, prefix="/dashboard", tags=["admin_dashboard"])

app.mount("/app", StaticFiles(directory="pwa", html=True), name="pwa")
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wlan_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_ids INTEGER NOT NULL,
                code TEXT NOT NULL,
                expiry DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
        roles = {
            "student": "Schüler",
            "teacher": "Lehrer",
            "parent": "Elternteil",
            "administration": "Verwaltung"
        }
        for r in roles.keys():
            cursor.execute("INSERT OR IGNORE INTO roles(name, german_name) VALUES(?, ?)", (r, roles[r],))
        conn.commit()


init_db()

# ROOT
@app.get("/")
async def root():
    return RedirectResponse(url="/app/index.html", status_code=302)