import sqlite3
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from api.v1.deps import get_db

def register(request, session_data):
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
    
def edit_profile(request, session_data):
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
    
def search_tutors_s(request):
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