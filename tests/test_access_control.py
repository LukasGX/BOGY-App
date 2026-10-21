"""Integrationstest fuer die Zugriffskontrolle.

Ausfuehren aus dem Projektverzeichnis:

    pip install -r requirements.txt httpx
    python tests/test_access_control.py

Der Test legt eine eigene SQLite-Datenbank in einem temporaeren Verzeichnis an
und fasst das Betriebsverzeichnis nicht an.
"""
import os
import re
import secrets
import sqlite3
import sys
import tempfile
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

from argon2 import PasswordHasher  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from api.v1.deps import get_db  # noqa: E402

admin = TestClient(main.app)
student = TestClient(main.app)
anon = TestClient(main.app)

PASSED = []
FAILED = []


def check(name, condition, detail=""):
    (PASSED if condition else FAILED).append(name)
    status = "  OK   " if condition else "  FAIL "
    print(status + name + ((" -> " + str(detail)) if detail and not condition else ""))


def login(client, username, password):
    return client.post(
        "/api/v1/user/login",
        data={"username": username, "pw": password},
        follow_redirects=False,
    )


print("\n=== 1. Admin-Login und Standard-Admin ===")
r = login(admin, "admin", TEST_ADMIN_PASSWORD)
check("Admin kann sich anmelden", r.status_code == 302 and "/app/index.html" in r.headers.get("location", ""))

admin_hash = sqlite3.connect(os.environ["DB_PATH"]).execute(
    "SELECT password FROM users WHERE username='admin'").fetchone()[0]
check("Admin-Passwort stammt aus der Umgebung",
      PasswordHasher().verify(admin_hash, TEST_ADMIN_PASSWORD))
# Ein fest verdrahteter Hash im Quellcode waere eine offene Hintertuer.
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
check("Kein verdrahteter Passwort-Hash im Quellcode", "$argon2" not in main_source)

print("\n=== 2. Nutzer anlegen ===")
r = admin.put("/api/v1/administration/user", json={
    "username": "student1", "firstname": "Max", "lastname": "Muster",
    "password": TEST_STUDENT_PASSWORD, "role": 1, "class": None})
check("Schueler angelegt", r.status_code == 200, r.text)
r = login(student, "student1", TEST_STUDENT_PASSWORD)
check("Schueler kann sich anmelden", r.status_code == 302)

print("\n=== 3. Schueler darf keine Verwaltungsdaten aendern ===")
r = student.patch("/api/v1/data/user/1", json={
    "new_role": 4, "new_class": 0, "new_username": "hacker",
    "new_firstname": "H", "new_lastname": "H"})
check("Schueler kann keine Rolle aendern (403)", r.status_code == 403, r.status_code)

r = student.patch("/api/v1/data/class/1", json={"new_name": "GEF"})
check("Schueler kann keine Klasse umbenennen (403)", r.status_code == 403, r.status_code)

r = student.patch("/api/v1/data/wlan-code/1", json={"new_expiry": "2099-01-01 00:00:00", "new_user_ids": "1"})
check("Schueler kann keinen WLAN-Code aendern (403)", r.status_code == 403, r.status_code)

print("\n=== 4. Schueler darf keine Verwaltungsdaten auslesen ===")
for path, label in [
    ("/api/v1/data/get-users", "alle Nutzer"),
    ("/api/v1/data/get-classes", "alle Klassen"),
    ("/api/v1/data/user/1", "einen Nutzer"),
    ("/api/v1/data/roles", "die Rollenliste"),
    ("/api/v1/data/get-files", "die Dateiliste"),
]:
    r = student.get(path)
    check(f"Schueler kann {label} nicht auslesen (403)", r.status_code == 403, r.status_code)

print("\n=== 5. Elternbriefe ===")
r = student.put("/api/v1/parentnotification/", json={
    "title": "XSS-Test", "body": "<img src=x onerror=alert(1)>", "feedback": "[]",
    "attachments": "[]", "user_ids": "all"})
check("Schueler kann keinen Elternbrief erstellen (403)", r.status_code == 403, r.status_code)

r = student.get("/api/v1/parentnotification/list")
check("Schueler kann nicht alle Elternbriefe listen (403)", r.status_code == 403, r.status_code)

r = student.get("/api/v1/parentnotification/feedback/1")
check("Schueler kann keine Rueckmeldungen auslesen (403)", r.status_code == 403, r.status_code)

r = admin.put("/api/v1/parentnotification/", json={
    "title": "Testbrief", "body": "Hallo", "feedback": "[]",
    "attachments": "[]", "user_ids": "all"})
check("Verwaltung darf Elternbriefe erstellen", r.status_code == 200, r.text)
with get_db() as conn:
    pn_id = conn.execute(
        "SELECT id FROM parentnotifications WHERE title='Testbrief'").fetchone()["id"]

r = student.post("/api/v1/parentnotification/feedback", json={"notification_id": pn_id, "feedback": {"0": "ok"}})
check("Feedback als Empfaenger erlaubt", r.status_code == 200, r.text)

with get_db() as conn:
    conn.execute(
        "INSERT INTO parentnotifications (title, body, feedback, attachments, user_ids) VALUES ('NUR5','x','[]','[]','5')")
    conn.commit()
    pn5 = conn.execute("SELECT id FROM parentnotifications WHERE title='NUR5'").fetchone()["id"]
r = student.post("/api/v1/parentnotification/feedback", json={"notification_id": pn5, "feedback": {"0": "ok"}})
check("Feedback als Nicht-Empfaenger abgelehnt (403)", r.status_code == 403, r.status_code)

print("\n=== 6. Tutorverzeichnisse und Hashing ===")
r = anon.get("/api/v1/tutoring/all-tutors")
check("/all-tutors anonym gesperrt (401)", r.status_code == 401, r.status_code)
r = anon.get("/api/v1/tutoring/search-tutors?subject=maths")
check("/search-tutors anonym gesperrt (401)", r.status_code == 401, r.status_code)
r = student.get("/api/v1/tutoring/all-tutors")
check("/all-tutors fuer Eingeloggte erlaubt (200)", r.status_code == 200, r.status_code)
r = anon.get("/api/v1/data/encrypt?input=x")
check("Hashing-Endpunkt erfordert Login (401)", r.status_code == 401, r.status_code)

print("\n=== 7. Verwaltung darf weiterhin alles ===")
r = admin.get("/api/v1/data/get-users")
check("Verwaltung darf Nutzer listen", r.status_code == 200, r.status_code)
r = admin.get("/api/v1/parentnotification/list")
check("Verwaltung darf alle Elternbriefe listen", r.status_code == 200, r.status_code)

print("\n=== 8. Quelltextpruefung: keine unescapeten Werte im HTML ===")
# Felder, die Text aus der Datenbank enthalten koennen und deshalb vor der
# Ausgabe escaped werden muessen.
STRING_FIELDS = {
    "title", "body", "name", "username", "firstname", "lastname", "label",
    "code", "subtitle", "foreName", "longName", "german_name",
    "german_role_name", "class_name",
}


def unescaped_interpolations(source):
    """Findet Textfelder aus der Datenbank, die ohne escapeHtml() ausgegeben werden."""
    findings = []
    for number, line in enumerate(source.splitlines(), start=1):
        if ".toLowerCase()" in line:
            # Suchindex, wird nicht als HTML gerendert
            continue
        if "alert(" in line:
            # Dialogfenster, kein HTML
            continue
        if "subtitle:" in line:
            # Suchergebnis, wird beim Rendern escaped
            continue
        for match in re.finditer(r"\$\{([A-Za-z_][\w.]*)\}", line):
            expression = match.group(1)
            field = expression.split(".")[-1]
            if field not in STRING_FIELDS:
                continue
            if line[:match.start()].endswith("escapeHtml("):
                continue
            findings.append(f"Zeile {number}: {expression}")
    return findings


for filename in ("pwa/js/parentnotification.js", "static/admin_dashboard.js", "pwa/js/pw.js"):
    source = (ROOT / filename).read_text(encoding="utf-8")
    findings = unescaped_interpolations(source)
    check(f"{filename} escaped alle Datenbankwerte", not findings, findings[:5])

print("\n" + "=" * 60)
print(f"ERGEBNIS: {len(PASSED)} bestanden, {len(FAILED)} fehlgeschlagen")
if FAILED:
    for name in FAILED:
        print("  FEHLGESCHLAGEN:", name)
print("=" * 60)
print(f"Testdatenbank: {os.environ['DB_PATH']}")

sys.exit(1 if FAILED else 0)
