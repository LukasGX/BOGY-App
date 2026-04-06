from datetime import datetime, timedelta
from api.v1.deps import get_db, hash_password

def get_subjects_s(session_data):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM subjects ORDER BY name")
        all_subs = cursor.fetchall()

        cursor.execute("SELECT subjects FROM tutoring WHERE user = ?", (session_data["user_id"],))
        row = cursor.fetchone()
        user_sub_ids = []
        if row and row["subjects"]:
            user_sub_ids = [int(s) for s in row["subjects"].split(",") if s]

        id_to_name = {r["id"]: r["name"] for r in all_subs}

        return {
            "subjects": [{"id": r["id"], "name": r["name"]} for r in all_subs],
            "user_subject_ids": user_sub_ids,
            "user_subjects": [id_to_name.get(i) for i in user_sub_ids],
        }
    
def encrypt(input):
    output = hash_password(input)
    return {"encrypted": output}

def get_classes_s(session_data):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                c.id,
                c.name,
                COUNT(CASE WHEN u.role = 1 THEN 1 END) AS student_count,
                COUNT(CASE WHEN u.role != 1 THEN 1 END) AS others_count
            FROM classes c
            LEFT JOIN users u ON u.class = c.id
            GROUP BY c.id, c.name
            ORDER BY c.name ASC;
        """)
        classes = cursor.fetchall()

        return {"classes": classes}
    
def get_class_s(class_id, session_data):
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
            WHERE c.id = ?
            GROUP BY c.id, c.name
            ORDER BY c.name ASC;
        """, (class_id,))
        class_info = cursor.fetchone()
        if not class_info:
            return {"error": "Class not found"}
        
        cursor.execute("""
            SELECT
                id,
                username,
                firstname,
                lastname
            FROM users
            WHERE class = ? AND role = 1
            ORDER BY lastname ASC
            LIMIT 50;
        """, (class_id,))
        students = cursor.fetchall()

        return {
            "class": class_info,
            "students": students
        }
    
def update_class_s(class_id, new_name):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
        if not cursor.fetchone():
            return {"error": "Class not found"}

        cursor.execute("UPDATE classes SET name = ? WHERE id = ?", (new_name, class_id))
        conn.commit()

        return {"success": True}
    
def get_users_s():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                u.id,
                u.username,
                u.firstname,
                u.lastname,
                r.name AS role_name,
                r.german_name AS german_role_name,
                c.name AS class_name
            FROM users u
            LEFT JOIN classes c ON u.class = c.id
            LEFT JOIN roles r ON u.role = r.id
            ORDER BY 
                u.role ASC,
                u.lastname ASC,
                u.firstname ASC
            LIMIT 100;
        """)
        users = cursor.fetchall()

        return {"users": users}
    
def get_user_s(user_id):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                u.id,
                u.username,
                u.firstname,
                u.lastname,
                r.id AS role_id,
                r.name AS role_name,
                r.german_name AS german_role_name,
                c.id AS class_id,
                c.name AS class_name
            FROM users u
            LEFT JOIN classes c ON u.class = c.id
            LEFT JOIN roles r ON u.role = r.id
            WHERE u.id = ?
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return {"error": "User not found"}

        return {"user": user}
    
def update_user_s(user_id, new_role, new_class, new_username, new_firstname, new_lastname):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            return {"error": "User not found"}

        cursor.execute("UPDATE users SET role = ?, class = ?, username = ?, firstname = ?, lastname = ? WHERE id = ?", (new_role, new_class, new_username, new_firstname, new_lastname, user_id))
        conn.commit()

        return {"success": True}
    
def get_roles_s():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, german_name FROM roles ORDER BY id ASC")
        roles = cursor.fetchall()

        return {"roles": roles}
    
def get_wlan_code_s(code_id):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, code, user_ids, expiry FROM wlan_codes WHERE id = ?", (code_id,))
        code = cursor.fetchone()
        if not code:
            return {"error": "WLAN code not found"}
        
        code_dict = dict(code)
        
        code_dict["user_ids"] = str(code_dict["user_ids"])

        return {"code": code_dict}
    
def update_wlan_code_s(code_id, new_expiry, new_user_ids):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, code, user_ids, expiry FROM wlan_codes WHERE id = ?", (code_id,))
        code = cursor.fetchone()
        if not code:
            return {"error": "WLAN code not found"}
        
        cursor.execute("UPDATE wlan_codes SET expiry = ?, user_ids = ? WHERE id = ?", (new_expiry, new_user_ids, code_id))
        conn.commit()

        return {"success": True, "new_expiry": new_expiry}