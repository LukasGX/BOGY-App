"""Integrationstest fuer die Fehlerbehebungen in der Datenlogik.

Ausfuehren aus dem Projektverzeichnis:

    pip install -r requirements.txt httpx
    python tests/test_correctness_fixes.py

Der Test legt eine eigene SQLite-Datenbank in einem temporaeren Verzeichnis an
und fasst das Betriebsverzeichnis nicht an.
"""
import os
import secrets
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Die Testpasswoerter werden zur Laufzeit erzeugt. Feste Zugangsdaten gehoeren
# nicht in das Repository, auch nicht in Testdateien.
TEST_ADMIN_PASSWORD = secrets.token_urlsafe(16)
TEST_STUDENT_PASSWORD = secrets.token_urlsafe(16)

_TMP = Path(tempfile.mkdtemp(prefix="bogy-test-"))
os.environ["DB_PATH"] = str(_TMP / "test.db")
os.environ["FEEDBACK_DIR"] = str(_TMP / "feedback")
os.environ["ADMIN_PASSWORD"] = TEST_ADMIN_PASSWORD
os.environ["ENV"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from api.v1.deps import get_db  # noqa: E402

admin = TestClient(main.app)
student = TestClient(main.app)

PASSED = []
FAILED = []


def check(name, condition, detail=""):
    (PASSED if condition else FAILED).append(name)
    status = "  OK   " if condition else "  FAIL "
    print(status + name + ((" -> " + str(detail)) if detail and not condition else ""))


admin.post("/api/v1/user/login", data={"username": "admin", "pw": TEST_ADMIN_PASSWORD},
           follow_redirects=False)
admin.put("/api/v1/administration/user", json={
    "username": "student1", "firstname": "Max", "lastname": "Muster",
    "password": TEST_STUDENT_PASSWORD, "role": 1, "class": None})
admin.put("/api/v1/administration/class", json={"className": "8b"})
student.post("/api/v1/user/login", data={"username": "student1", "pw": TEST_STUDENT_PASSWORD},
             follow_redirects=False)

print("\n=== 1. Elternbriefe erreichen nur Empfaenger ===")
with get_db() as conn:
    for user_id in (5, 6, 7, 8):
        conn.execute(
            "INSERT INTO parentnotifications (title, body, feedback, attachments, user_ids) VALUES (?,?,?,?,?)",
            (f"nur{user_id}", "x", "[]", "[]", str(user_id)))
    conn.commit()

r = student.get("/api/v1/parentnotification/")
titles = [n["title"] for n in r.json()["parent_notifications"]]
check("Keine fremden Elternbriefe sichtbar", titles == [], titles)

print("\n=== 2. Klassen zaehlen Schueler und Lehrer getrennt ===")
with get_db() as conn:
    for name in ("s1", "s2", "s3"):
        conn.execute(
            "INSERT INTO users (username, firstname, lastname, password, role, class) VALUES (?,?,?,?,1,1)",
            (name, name, name, "x"))
    for name in ("t1", "t2"):
        conn.execute(
            "INSERT INTO users (username, firstname, lastname, password, role, class) VALUES (?,?,?,?,2,1)",
            (name, name, name, "x"))
    conn.commit()

r = admin.get("/api/v1/data/class/1")
data = r.json()
# 3 Schueler und 2 andere in Klasse 1. Ohne COUNT(DISTINCT ...) waeren es 3 x 2 = 6.
check("student_count stimmt (3 Schueler)", data["class"]["student_count"] == 3, data["class"]["student_count"])
check("others_count stimmt (2 andere)", data["class"]["others_count"] == 2, data["class"]["others_count"])

print("\n=== 3. WLAN-Codes: Ablaufzeit und Admin-Liste ===")
import datetime as dt

with get_db() as conn:
    conn.execute("INSERT INTO wlan_codes (user_ids, code, expiry) VALUES ('1','GUT', datetime('now','+1 day'))")
    conn.execute("INSERT INTO wlan_codes (user_ids, code, expiry) VALUES ('1','ABGELAUFEN', datetime('now','-1 day'))")
    conn.commit()

now = dt.datetime.now()
future_local = (now + dt.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S.000000")
past_local = (now - dt.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S.000000")
utc_future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
with get_db() as conn:
    conn.execute("INSERT INTO wlan_codes (user_ids, code, expiry) VALUES ('2','LOKALZUKUNFT', ?)", (future_local,))
    conn.execute("INSERT INTO wlan_codes (user_ids, code, expiry) VALUES ('2','LOKALVERGANGEN', ?)", (past_local,))
    conn.execute("INSERT INTO wlan_codes (user_ids, code, expiry) VALUES ('2','UTCZUKUNFT', ?)", (utc_future,))
    conn.commit()

r = student.get("/api/v1/wlan/")
codes = [c["code"] for c in r.json()["codes"]]
check("Abgelaufene Codes werden ausgefiltert", "ABGELAUFEN" not in codes and "LOKALVERGANGEN" not in codes, codes)
check("Gueltiger Code bleibt sichtbar", "LOKALZUKUNFT" in codes, codes)
check("Fremde Codes bleiben verborgen", "GUT" not in codes, codes)

time.sleep(1.2)
r = admin.get("/api/v1/administration/wlan-codes")
all_codes = [c["code"] for c in r.json().get("codes", [])]
check("Verwaltung sieht alle Codes", "GUT" in all_codes and "LOKALZUKUNFT" in all_codes, (all_codes, r.text[:200]))
check("Verwaltung sieht keine abgelaufenen Codes", "ABGELAUFEN" not in all_codes and "LOKALVERGANGEN" not in all_codes, all_codes)
check("UTC-Ablaufzeit wird erkannt", "UTCZUKUNFT" in all_codes, all_codes)

print("\n=== 4. Push: erneutes Anmelden ===")
subscription = {"endpoint": "https://push.example/abc", "keys": {"p256dh": "p", "auth": "a"}}
r1 = student.post("/api/v1/push/subscribe", json=subscription)
r2 = student.post("/api/v1/push/subscribe", json=subscription)
check("Erstes Anmelden ok", r1.status_code == 200, r1.text)
check("Erneutes Anmelden ok (kein 409)", r2.status_code == 200, r2.text)
with get_db() as conn:
    count = conn.execute(
        "SELECT COUNT(*) c FROM push_subscriptions WHERE endpoint=?", (subscription["endpoint"],)
    ).fetchone()["c"]
check("Nur eine Subscription gespeichert", count == 1, count)

print("\n=== 5. Nachhilfe ohne Duplikate ===")
student.get("/api/v1/tutoring/register-tutoring?subject=maths", follow_redirects=False)
student.get("/api/v1/tutoring/register-tutoring?subject=maths", follow_redirects=False)
with get_db() as conn:
    count = conn.execute(
        "SELECT COUNT(*) c FROM tutoring WHERE user=(SELECT id FROM users WHERE username='student1')"
    ).fetchone()["c"]
check("Nur ein Nachhilfe-Eintrag", count == 1, count)

print("\n=== 6. Anlegen liefert eine Kennung ===")
r = admin.put("/api/v1/parentnotification/", json={
    "title": "Testbrief", "body": "Hallo", "feedback": "[]",
    "attachments": "[]", "user_ids": "all"})
check("Neuer Elternbrief liefert eine id", r.status_code == 200 and r.json().get("id"), r.text)

print("\n=== 7. Faecher bleiben fuer Schueler lesbar ===")
r = student.get("/api/v1/data/get-subjects")
check("Subjects sind fuer Schueler erlaubt", r.status_code == 200, r.status_code)

print("\n" + "=" * 60)
print(f"ERGEBNIS: {len(PASSED)} bestanden, {len(FAILED)} fehlgeschlagen")
if FAILED:
    for name in FAILED:
        print("  FEHLGESCHLAGEN:", name)
print("=" * 60)
print(f"Testdatenbank: {os.environ['DB_PATH']}")

sys.exit(1 if FAILED else 0)
