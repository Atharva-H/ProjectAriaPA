# app/routes/contacts_routes.py
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db import get_db, crud
from app.core.security import decode_jwt

router = APIRouter(prefix="/contacts", tags=["Contacts"])

def _auth(db: Session, authorization: str):
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        return None
    return crud.get_user_by_email(db, data.get("sub"))

@router.get("")
async def list_contacts(authorization: str = Header(None), q: str = None, db: Session = Depends(get_db)):
    user = _auth(db, authorization)
    if not user:
        return {"error": "Unauthorized"}
    contacts = crud.list_contacts(db, user, q)
    return [{"id": c.id, "name": c.name, "email": c.email, "phone": c.phone, "designation": c.designation, "tags": c.tags} for c in contacts]

@router.post("")
async def create_contact(payload: dict, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _auth(db, authorization)
    if not user:
        return {"error": "Unauthorized"}
    c = crud.create_contact(db, user, payload.get("name"), payload.get("email"), payload.get("phone"), payload.get("designation"), payload.get("tags"))
    return {"id": c.id}

@router.put("/{contact_id}")
async def update_contact(contact_id: int, payload: dict, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _auth(db, authorization)
    if not user:
        return {"error": "Unauthorized"}
    c = crud.update_contact(db, contact_id, user, **payload)
    if not c:
        return {"error": "Not found"}
    return {"status": "ok"}

@router.delete("/{contact_id}")
async def delete_contact(contact_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _auth(db, authorization)
    if not user:
        return {"error": "Unauthorized"}
    ok = crud.delete_contact(db, contact_id, user)
    return {"deleted": ok}


