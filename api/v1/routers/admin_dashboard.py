from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from api.v1.deps import require_role
from services.admin_dashboard_service import *
from definitions import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def root(request: Request, session_data: dict = Depends(require_role(4))):
    return root_s(request, session_data)