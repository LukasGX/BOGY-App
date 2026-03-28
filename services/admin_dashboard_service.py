from api.v1.deps import get_db
from services.data_service import get_classes_s
from definitions import templates

def root_s(request, session_data):
    with get_db() as conn:
        classes_raw = get_classes_s(session_data)
        classes = classes_raw.get("classes", [])
            
        context = {
            "request": request,
            "username": session_data.get("username", ""),
            "classes": classes[0:4],
        }
        return templates.TemplateResponse("dashboard.html", context)