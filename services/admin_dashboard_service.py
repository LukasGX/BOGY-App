import json

from api.v1.deps import get_db
from services.data_service import get_classes_s, get_users_s
from services.wlan_service import get_all_wlan_codes, _parse_expiry
from services.tutoring_service import all_tutors_s
from services.parentnotification_service import get_parentnotifications_s
from definitions import templates


def _format_datetime(value):
    """Formatiert einen Zeitstempel fuer das Dashboard (ohne Absturz bei ungueltigen Werten)."""
    if not value:
        return ""
    dt = _parse_expiry(value)
    if dt is None:
        return str(value)
    return dt.strftime("%d.%m.%Y %H:%M")


def _json_len(value):
    """Laenge eines JSON-Feldes; ungueltiges JSON liefert 0 statt einer Exception."""
    try:
        parsed = json.loads(value) if value else []
    except (json.JSONDecodeError, ValueError, TypeError):
        return 0
    try:
        return len(parsed)
    except TypeError:
        return 0


def root_s(request, session_data):
    with get_db() as conn:
        classes_raw = get_classes_s(session_data)
        classes = classes_raw.get("classes", [])

        users_raw = get_users_s()
        users = users_raw.get("users", [])

        # Alle Codes (nicht nur die der eigenen User-ID) - die Verwaltung
        # sieht sonst keine Codes, die an Schueler gebunden sind.
        wlan_codes_raw = get_all_wlan_codes()
        wlan_codes = wlan_codes_raw.get("codes", [])

        for code in wlan_codes:
            code["expiry_formatted"] = _format_datetime(code.get("expiry")) or "Kein Ablaufdatum"

        tutors_raw = all_tutors_s()
        tutors = tutors_raw.get("results", [])

        notifications_raw = get_parentnotifications_s(session_data, False)
        notifications = [dict(row) for row in notifications_raw.get("parent_notifications", [])]

        for pn in notifications:
            pn["feedback_field_count"] = _json_len(pn.get("feedback"))
            pn["attachments_count"] = _json_len(pn.get("attachments"))
            pn["date"] = _format_datetime(pn.get("created_at"))

        context = {
            "request": request,
            "username": session_data.get("username", ""),
            "classes": classes[0:4],
            "users": users[0:4],
            "wlan_codes": wlan_codes[0:4],
            "tutors": tutors[0:3],
            "notifications": notifications[0:4]
        }
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context=context
        )
