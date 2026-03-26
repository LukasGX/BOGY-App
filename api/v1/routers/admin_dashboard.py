from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from api.v1.deps import require_role
from api.v1.routers.user import get_profile
from definitions import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def root(request: Request, session_data: dict = Depends(require_role(4))):
    context = {
        "request": request,
        "username": session_data.get("username", "")
    }
    return templates.TemplateResponse("dashboard.html", context)