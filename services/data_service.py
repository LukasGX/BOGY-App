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