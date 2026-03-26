from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from api.v1.deps import get_db, verify_password

def login_s(request, username, pw):
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

def get_profile(session_data):
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
    
def logout_s(request):
    request.session.clear()
    return {"success": True}