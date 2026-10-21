import os
import secrets

from fastapi import HTTPException

import untis
from services.administration_service import create_class_s, create_user_s
from payloads import CreateClassRequest, CreateUserRequest


def _existing_usernames():
    from api.v1.deps import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users")
        return {row["username"] for row in cursor.fetchall()}


def _existing_classes():
    from api.v1.deps import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM classes")
        return {row["name"] for row in cursor.fetchall()}


def get_untis_classes_s():
    classes = untis.get_classes()
    return classes


def import_untis_classes_s():
    classes = untis.get_classes()

    created = 0
    skipped = 0
    existing = _existing_classes()

    for cl in classes.get("result", []):
        name = cl.get("name")
        if not name or name in existing:
            skipped += 1
            continue
        try:
            create_class_s(CreateClassRequest(className=name))
            existing.add(name)
            created += 1
        except HTTPException:
            # Bereits vorhanden -> ueberspringen, statt den Import abzubrechen
            skipped += 1

    return {"status": "success", "created": created, "skipped": skipped}


def get_untis_users_s():
    users = untis.get_users()
    return users


def import_untis_users_s():
    users = untis.get_users()

    # Ein gemeinsames Startpasswort kann per Umgebung gesetzt werden. Ohne
    # Vorgabe wird fuer jeden Nutzer ein eigenes Zufallspasswort vergeben,
    # damit nicht alle Konten dasselbe Passwort haben.
    default_password = os.getenv("UNTIS_DEFAULT_PASSWORD")

    existing = _existing_usernames()
    accounts = []
    skipped = 0

    groups = [
        (users.get("teachers", {}).get("result", []), 2),
        (users.get("students", {}).get("result", []), 1),
    ]

    for people, role in groups:
        for person in people:
            fore = (person.get("foreName") or "").strip()
            long = (person.get("longName") or "").strip()
            username = (fore.lower().replace(" ", "") + "." + long.lower().replace(" ", "")).strip(".")

            if not username or username in existing:
                skipped += 1
                continue

            password = default_password or secrets.token_urlsafe(9)

            try:
                result = create_user_s(CreateUserRequest(
                    username=username,
                    firstname=fore,
                    lastname=long,
                    password=password,
                    role=role,
                    **{"class": None}
                ))
            except HTTPException:
                # Bereits vorhanden -> ueberspringen, statt den Import abzubrechen
                skipped += 1
                continue

            existing.add(username)
            accounts.append({
                "id": result.get("id"),
                "username": username,
                "password": password,
            })

    return {"status": "success", "created": len(accounts), "skipped": skipped, "accounts": accounts}
