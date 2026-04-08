from datetime import datetime
import json
from api.v1.deps import get_db
from services.data_service import get_classes_s, get_users_s
from services.wlan_service import get_wlan_codes
from services.tutoring_service import all_tutors_s
from services.parentnotification_service import get_parentnotifications_s
from definitions import templates

def root_s(request, session_data):
    with get_db() as conn:
        classes_raw = get_classes_s(session_data)
        classes = classes_raw.get("classes", [])

        users_raw = get_users_s()
        users = users_raw.get("users", [])

        wlan_codes_raw = get_wlan_codes(session_data)
        wlan_codes = wlan_codes_raw.get("codes", [])

        for code in wlan_codes:
            if code.get('expiry'):
                try:
                    expiry_str = code['expiry'].replace('Z', '+00:00')
                    dt = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S.%f')
                    code['expiry_formatted'] = dt.strftime('%d.%m.%Y %H:%M')
                except ValueError:
                    code['expiry_formatted'] = code['expiry']
            else:
                code['expiry_formatted'] = 'Kein Ablaufdatum'

        tutors_raw = all_tutors_s()
        tutors = tutors_raw.get("results", [])

        notifications_raw = get_parentnotifications_s(session_data, False)
        notifications = [dict(row) for row in notifications_raw.get("parent_notifications", [])]

        for pn in notifications:
            pn["feedback_field_count"] = len(json.loads(pn["feedback"]))
            pn["attachments_count"] = len(json.loads(pn["attachments"]))
            try:
                expiry_str = pn['created_at'].replace('Z', '+00:00')
                dt = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                pn['date'] = dt.strftime('%d.%m.%Y %H:%M')
            except ValueError:
                pn['date'] = pn['created_at']
            
        context = {
            "request": request,
            "username": session_data.get("username", ""),
            "classes": classes[0:4],
            "users": users[0:4],
            "wlan_codes": wlan_codes[0:4],
            "tutors": tutors[0:3],
            "notifications": notifications[0:4]
        }
        return templates.TemplateResponse("dashboard.html", context)