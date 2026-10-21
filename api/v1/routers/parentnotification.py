from fastapi import APIRouter, Body, Depends
from api.v1.deps import LoggedIn, require_role
from services.parentnotification_service import *

router = APIRouter()

@router.get("/")
async def get_parentnotifications(session_data: dict = Depends(LoggedIn)):
    return get_parentnotifications_s(session_data)

# Die ungefilterte Liste (alle Elternbriefe aller Klassen) und das Anlegen neuer
# Briefe sind ausschliesslich der Verwaltung vorbehalten.
@router.get("/list")
async def get_parentnotifications_list(session_data: dict = Depends(require_role(4))):
    return get_parentnotifications_s(session_data, filter_user_id=False)

@router.post("/feedback")
async def feedback(notification_id: int = Body(embed=True), feedback: dict = Body(embed=True), session_data: dict = Depends(LoggedIn)):
    return feedback_s(session_data, notification_id, feedback)

# Rueckmeldungen werden nur von der Verwaltung eingesehen.
@router.get("/feedback/{notification_id}")
async def get_feedback(notification_id: int, session_data: dict = Depends(require_role(4))):
    return get_feedback_s(session_data, notification_id)

@router.put("/")
async def create_parentnotification(title: str = Body(embed=True), body: str = Body(embed=True), feedback: str = Body(embed=True), attachments: str = Body(embed=True), user_ids: str = Body(embed=True), session_data: dict = Depends(require_role(4))):
    return create_parentnotification_s(session_data, title, body, feedback, attachments, user_ids)
