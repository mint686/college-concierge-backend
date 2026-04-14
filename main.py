from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr

from database import get_db
from models import User
from auth import authenticate_user, create_access_token, get_password_hash, get_current_user, require_role, require_club_lead

# Create FastAPI app
app = FastAPI(title="College Concierge API")

# Pydantic models for request/response
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    points: int

class NotificationTest(BaseModel):
    device_token: str
    title: str
    body: str

# ========== BASIC ROUTES ==========
@app.get("/")
def root():
    return {"message": "College Concierge Backend Running"}

# ========== AUTH ROUTES ==========
@app.post("/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if not user_data.email.endswith("@yourcollege.edu"):
        raise HTTPException(status_code=400, detail="Only college email addresses allowed")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        password=hashed_password,
        college_verified=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ========== RBAC EXAMPLE ROUTES (Task 4) ==========
@app.post("/tasks/assign")
def assign_task(
    task_data: dict,
    current_user: User = Depends(require_role("club_lead"))
):
    return {"message": "Task assigned"}

@app.post("/clubs/{club_id}/manage")
def manage_club(
    club_id: int,
    current_user: User = Depends(require_club_lead("club_id"))
):
    return {"message": f"Managing club {club_id}"}

# ========== NOTIFICATION TEST ROUTE ==========
@app.post("/test/notification")
def test_notification(
    notification: NotificationTest):
    """Test endpoint to send a push notification"""
    from notification_service import send_push_notification
    
    result = send_push_notification(
        device_token=notification.device_token,
        title=notification.title,
        body=notification.body
    )
    
    if result:
        return {"success": True, "message_id": result}
    else:
        return {"success": False, "error": "Failed to send notification"}