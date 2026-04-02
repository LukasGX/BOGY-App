from datetime import datetime
from api.v1.deps import get_db
from services.data_service import get_classes_s, get_users_s
from services.wlan_service import get_wlan_codes
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
                    # ISO-String parsen (Z → +00:00)
                    expiry_str = code['expiry'].replace('Z', '+00:00')
                    dt = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S.%f')
                    code['expiry_formatted'] = dt.strftime('%d.%m.%Y %H:%M')
                except ValueError:
                    code['expiry_formatted'] = code['expiry']
            else:
                code['expiry_formatted'] = 'Kein Ablaufdatum'
            
        context = {
            "request": request,
            "username": session_data.get("username", ""),
            "classes": classes[0:4],
            "users": users[0:4],
            "wlan_codes": wlan_codes[0:4]
        }
        return templates.TemplateResponse("dashboard.html", context)