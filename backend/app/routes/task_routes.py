from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.db import crud
from app.core.security import decode_jwt
from app.db.models import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Pydantic models
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    is_urgent: bool = False
    is_important: bool = False

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    is_urgent: Optional[bool] = None
    is_important: Optional[bool] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_at: Optional[datetime]
    status: str
    is_urgent: bool
    is_important: bool
    created_at: datetime

    class Config:
        orm_mode = True

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    token = authorization.replace("Bearer ", "")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    email = payload.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.get("/", response_model=List[TaskResponse])
def get_tasks(status: Optional[str] = None, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    # Map 'all' to None for crud
    status_filter = None if status == "all" else status
    # If no status provided, default to pending (or handle in crud)
    # crud.list_tasks handles status=None as "all" if not specified? 
    # Let's check crud.list_tasks implementation. 
    # It says: if status: query = query.filter(Task.status == status)
    # So if we want all, we pass None. If we want pending, we pass "pending".
    # Default behavior for dashboard usually implies pending tasks.
    
    tasks = crud.list_tasks(db, user, status=status_filter)
    return tasks

@router.post("/", response_model=TaskResponse)
def create_task(task: TaskCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    return crud.create_task(
        db, 
        user, 
        title=task.title, 
        description=task.description, 
        due_at=task.due_at, 
        is_urgent=task.is_urgent, 
        is_important=task.is_important,
        source="web"
    )

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    update_data = task_update.dict(exclude_unset=True)
    t = crud.update_task(db, user, task_id, **update_data)
    
    if not t:
        raise HTTPException(404, "Task not found")
    return t
