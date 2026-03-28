from api.v1.deps import get_db
from definitions import templates

def root_s(request, session_data):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                c.id,
                c.name,
                COUNT(u.id) AS student_count
            FROM classes c
            LEFT JOIN users u
                ON u.class = c.id
            AND u.role = 1
            GROUP BY c.id, c.name
            ORDER BY c.name ASC
            LIMIT 3;
        """)
        classes = cursor.fetchall()
            
        context = {
            "request": request,
            "username": session_data.get("username", ""),
            "classes": classes
        }
        return templates.TemplateResponse("dashboard.html", context)