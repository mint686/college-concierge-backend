from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from database import get_db
from models import User, Club, Task, Skill, Event, RSVP, SkillTransaction, AuditLog, ClubMember, SkillCategory, TaskComment
from auth import authenticate_user, create_access_token, get_password_hash, get_current_user, require_role, require_club_lead
from database import engine
from models import Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Ensure ClubMember table exists (for existing databases)
try:
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if 'club_members' not in inspector.get_table_names():
        ClubMember.__table__.create(engine)
        print("Created club_members table")
except Exception as e:
    print(f"Note: {e}")

# ========== CREATE FASTAPI APP ==========
app = FastAPI(title="College Concierge API")

# ========== CORS MIDDLEWARE ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== PYDANTIC MODELS ==========

# Auth Models
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

# Notification Test Model
class NotificationTest(BaseModel):
    device_token: str
    title: str
    body: str

# Skill-Share Models
class SkillCreate(BaseModel):
    title: str
    description: str
    skill_type: str
    points_required: int = 10

class SkillResponse(BaseModel):
    id: int
    title: str
    description: str
    skill_type: str
    points_required: int
    user_id: int
    user_name: str
    status: str
    created_at: datetime

class SkillRequestModel(BaseModel):
    skill_id: int

class SkillApproveModel(BaseModel):
    transaction_id: int

# Event Models
class EventCreate(BaseModel):
    title: str
    description: str
    venue: str
    event_date: datetime
    club_id: Optional[int] = None

class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    venue: str
    event_date: datetime
    club_id: Optional[int]
    club_name: Optional[str]
    created_by: int
    organizer_name: str
    rsvp_count: int
    user_rsvp_status: Optional[str]

# Club & Task Models
class ClubCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ClubResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    lead_id: int
    lead_name: str
    created_at: datetime

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    club_id: int
    assigned_to: int
    deadline: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    club_id: int
    club_name: str
    assigned_to: int
    assigned_to_name: str
    assigned_by: int
    assigned_by_name: str
    deadline: Optional[datetime]
    created_at: datetime

class MemberResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

# ========== BASIC ROUTE ==========
@app.get("/")
def root():
    return {"message": "College Concierge Backend Running"}

# ========== AUTH ROUTES ==========
@app.post("/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if not user_data.email.endswith("@iiitn.ac.in"):
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

# ========== NOTIFICATION TEST ROUTE ==========
@app.post("/test/notification")
def test_notification(notification: NotificationTest):
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

# ========== SKILL-SHARE ENDPOINTS ==========
@app.get("/skills", response_model=List[SkillResponse])
def get_skills(
    skill_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Skill).filter(Skill.status == "active")
    
    if skill_type:
        query = query.filter(Skill.skill_type == skill_type)
    
    skills = query.order_by(Skill.created_at.desc()).all()
    
    result = []
    for skill in skills:
        user = db.query(User).filter(User.id == skill.user_id).first()
        result.append({
            "id": skill.id,
            "title": skill.title,
            "description": skill.description,
            "skill_type": skill.skill_type,
            "points_required": skill.points_required,
            "user_id": skill.user_id,
            "user_name": user.name if user else "Unknown",
            "status": skill.status,
            "created_at": skill.created_at
        })
    return result

@app.post("/skills", response_model=SkillResponse)
def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_skill = Skill(
        title=skill_data.title,
        description=skill_data.description,
        skill_type=skill_data.skill_type,
        points_required=skill_data.points_required,
        user_id=current_user.id,
        status="active"
    )
    
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    
    return {
        "id": new_skill.id,
        "title": new_skill.title,
        "description": new_skill.description,
        "skill_type": new_skill.skill_type,
        "points_required": new_skill.points_required,
        "user_id": new_skill.user_id,
        "user_name": current_user.name,
        "status": new_skill.status,
        "created_at": new_skill.created_at
    }

@app.post("/skills/request")
def request_skill(
    request_data: SkillRequestModel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skill = db.query(Skill).filter(Skill.id == request_data.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    if skill.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot request your own skill")
    
    if current_user.points < skill.points_required:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient points. Need {skill.points_required}, you have {current_user.points}"
        )
    
    existing = db.query(SkillTransaction).filter(
        SkillTransaction.skill_id == request_data.skill_id,
        SkillTransaction.from_user_id == current_user.id,
        SkillTransaction.status == "pending"
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Request already pending")
    
    transaction = SkillTransaction(
        skill_id=skill.id,
        from_user_id=current_user.id,
        to_user_id=skill.user_id,
        points=skill.points_required,
        status="pending"
    )
    
    db.add(transaction)
    db.commit()
    
    return {"message": "Request sent", "transaction_id": transaction.id}

@app.post("/skills/approve")
def approve_skill(
    approve_data: SkillApproveModel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(SkillTransaction).filter(
        SkillTransaction.id == approve_data.transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    skill = db.query(Skill).filter(Skill.id == transaction.skill_id).first()
    if skill.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if transaction.status != "pending":
        raise HTTPException(status_code=400, detail="Transaction already processed")
    
    from_user = db.query(User).filter(User.id == transaction.from_user_id).first()
    to_user = db.query(User).filter(User.id == transaction.to_user_id).first()
    
    from_user.points -= transaction.points
    to_user.points += transaction.points
    transaction.status = "completed"
    
    if skill.skill_type == "offering":
        skill.status = "completed"
    
    db.commit()
    
    return {"message": "Skill exchange completed", "points_deducted": transaction.points}

@app.get("/skills/my")
def get_my_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    return skills

@app.get("/skills/requests/pending")
def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transactions = db.query(SkillTransaction).join(Skill).filter(
        Skill.user_id == current_user.id,
        SkillTransaction.status == "pending"
    ).all()
    
    result = []
    for txn in transactions:
        skill = db.query(Skill).filter(Skill.id == txn.skill_id).first()
        requester = db.query(User).filter(User.id == txn.from_user_id).first()
        result.append({
            "transaction_id": txn.id,
            "skill_title": skill.title,
            "requester_name": requester.name,
            "points": txn.points,
            "requested_at": txn.created_at
        })
    
    return result

# ========== EVENTS ENDPOINTS ==========
@app.get("/events", response_model=List[EventResponse])
def get_events(
    upcoming_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    
    if upcoming_only:
        query = query.filter(Event.event_date > datetime.utcnow())
    
    query = query.order_by(Event.event_date)
    events = query.all()
    
    result = []
    for event in events:
        rsvp_count = db.query(RSVP).filter(
            RSVP.event_id == event.id,
            RSVP.status == "going"
        ).count()
        
        user_rsvp = db.query(RSVP).filter(
            RSVP.event_id == event.id,
            RSVP.user_id == current_user.id
        ).first()
        
        organizer = db.query(User).filter(User.id == event.created_by).first()
        
        club_name = None
        if event.club_id:
            club = db.query(Club).filter(Club.id == event.club_id).first()
            club_name = club.name if club else None
        
        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "venue": event.venue,
            "event_date": event.event_date,
            "club_id": event.club_id,
            "club_name": club_name,
            "created_by": event.created_by,
            "organizer_name": organizer.name if organizer else "Unknown",
            "rsvp_count": rsvp_count,
            "user_rsvp_status": user_rsvp.status if user_rsvp else None
        })
    
    return result

@app.post("/events", response_model=EventResponse)
def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if event_data.club_id:
        club = db.query(Club).filter(Club.id == event_data.club_id).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        if club.lead_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only club lead can create club events")
    
    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        venue=event_data.venue,
        event_date=event_data.event_date,
        club_id=event_data.club_id,
        created_by=current_user.id
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return new_event

@app.post("/events/{event_id}/rsvp")
def rsvp_event(
    event_id: int,
    status: str = "going",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    existing = db.query(RSVP).filter(
        RSVP.event_id == event_id,
        RSVP.user_id == current_user.id
    ).first()
    
    if existing:
        existing.status = status
        message = f"RSVP updated to {status}"
    else:
        new_rsvp = RSVP(
            event_id=event_id,
            user_id=current_user.id,
            status=status
        )
        db.add(new_rsvp)
        message = f"RSVP'd as {status}"
    
    db.commit()
    
    return {"message": message, "event_id": event_id, "status": status}

@app.get("/events/my")
def get_my_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rsvps = db.query(RSVP).filter(
        RSVP.user_id == current_user.id,
        RSVP.status == "going"
    ).all()
    
    event_ids = [r.event_id for r in rsvps]
    events = db.query(Event).filter(Event.id.in_(event_ids)).order_by(Event.event_date).all()
    
    result = []
    for event in events:
        result.append({
            "id": event.id,
            "title": event.title,
            "venue": event.venue,
            "event_date": event.event_date
        })
    
    return result

@app.get("/events/calendar/{year}/{month}")
def get_calendar_events(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get events for calendar view"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    events = db.query(Event).filter(
        Event.event_date >= start_date,
        Event.event_date < end_date
    ).all()
    
    return events

# ========== CLUB ENDPOINTS ==========
@app.get("/clubs", response_model=List[ClubResponse])
def get_clubs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clubs = db.query(Club).all()
    
    result = []
    for club in clubs:
        lead = db.query(User).filter(User.id == club.lead_id).first()
        result.append({
            "id": club.id,
            "name": club.name,
            "description": club.description,
            "lead_id": club.lead_id,
            "lead_name": lead.name if lead else "Unknown",
            "created_at": club.created_at
        })
    return result

@app.post("/clubs", response_model=ClubResponse)
def create_club(
    club_data: ClubCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Club).filter(Club.name == club_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Club name already exists")
    
    new_club = Club(
        name=club_data.name,
        description=club_data.description,
        lead_id=current_user.id
    )
    
    db.add(new_club)
    db.commit()
    db.refresh(new_club)
    
    return {
        "id": new_club.id,
        "name": new_club.name,
        "description": new_club.description,
        "lead_id": new_club.lead_id,
        "lead_name": current_user.name,
        "created_at": new_club.created_at
    }

@app.get("/clubs/list")
def get_clubs_list(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Get list of all clubs for admin panel"""
    clubs = db.query(Club).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "lead_id": c.lead_id
        }
        for c in clubs
    ]

@app.post("/clubs/{club_id}/join")
def join_club(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    return {"message": f"Join request sent to {club.name}"}

# ========== CLUB MEMBER MANAGEMENT ==========
@app.post("/clubs/{club_id}/members/add")
def add_club_member(
    club_id: int,
    email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a member to club (Club Lead only)"""
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    if club.lead_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only club lead can add members")
    
    user_to_add = db.query(User).filter(User.email == email).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = db.query(ClubMember).filter(
        ClubMember.club_id == club_id,
        ClubMember.user_id == user_to_add.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already a member")
    
    new_member = ClubMember(
        club_id=club_id,
        user_id=user_to_add.id,
        name=user_to_add.name,  # Store name directly
        email=user_to_add.email,  # Store email directly
        role="member"
    )
    
    db.add(new_member)
    db.commit()
    
    return {"message": f"{user_to_add.name} added to {club.name}", "user_id": user_to_add.id, "user_name": user_to_add.name}

@app.get("/clubs/{club_id}/members")
def get_club_members(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all members of a club (Club Lead only)"""
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    if club.lead_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only club lead can view members")
    
    members = db.query(ClubMember).filter(ClubMember.club_id == club_id).all()
    
    result = []
    
    for member in members:
        result.append({
            "id": member.user_id,  # Use stored user_id
            "name": member.name,   # Use stored name
            "email": member.email, # Use stored email
            "role": member.role,
            "joined_at": member.joined_at
        })
    
    lead = db.query(User).filter(User.id == club.lead_id).first()
    if lead:
        lead_already_included = any(m.get('id') == lead.id for m in result)
        if not lead_already_included:
            result.insert(0, {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "role": "lead",
                "joined_at": club.created_at
            })
    
    return result

@app.get("/clubs/{club_id}/members/assignable")
def get_assignable_members(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get club members available for task assignment (Club Lead or Admin only)"""
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Only club lead or admin can assign tasks
    if club.lead_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only club lead can assign tasks")
    
    # Get all club members
    members = db.query(ClubMember).filter(ClubMember.club_id == club_id).all()
    
    result = []
    
    # Add all members
    for member in members:
        result.append({
            "id": member.user_id,
            "name": member.name,   # Use stored name
            "email": member.email  # Use stored email
        })
    
    # Add club lead
    lead = db.query(User).filter(User.id == club.lead_id).first()
    if lead:
        # Check if lead is already in the list
        lead_already_included = any(m.get('id') == lead.id for m in result)
        if not lead_already_included:
            result.insert(0, {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email
            })
    
    return result

@app.get("/clubs/my")
def get_my_clubs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get clubs where user is lead or member"""
    
    lead_clubs = db.query(Club).filter(Club.lead_id == current_user.id).all()
    
    memberships = db.query(ClubMember).filter(ClubMember.user_id == current_user.id).all()
    member_clubs = []
    for membership in memberships:
        club = db.query(Club).filter(Club.id == membership.club_id).first()
        if club:
            member_clubs.append({
                "id": club.id,
                "name": club.name,
                "role": membership.role,
                "joined_at": membership.joined_at
            })
    
    return {
        "lead_clubs": [{"id": c.id, "name": c.name, "description": c.description, "created_at": c.created_at} for c in lead_clubs],
        "member_clubs": member_clubs
    }

# ========== TASK ENDPOINTS ==========
@app.get("/tasks", response_model=List[TaskResponse])
def get_my_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
    
    result = []
    for task in tasks:
        club = db.query(Club).filter(Club.id == task.club_id).first()
        assigned_to_user = db.query(User).filter(User.id == task.assigned_to).first()
        assigned_by_user = db.query(User).filter(User.id == task.assigned_by).first()
        
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "club_id": task.club_id,
            "club_name": club.name if club else "Unknown",
            "assigned_to": task.assigned_to,
            "assigned_to_name": assigned_to_user.name if assigned_to_user else "Unknown",
            "assigned_by": task.assigned_by,
            "assigned_by_name": assigned_by_user.name if assigned_by_user else "Unknown",
            "deadline": task.deadline,
            "created_at": task.created_at
        })
    
    return result

@app.post("/tasks", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == task_data.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    if club.lead_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only club lead can create tasks")
    
    assigned_user = db.query(User).filter(User.id == task_data.assigned_to).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="Assigned user not found")
    
    # Check if assigned user is a member of the club (or is the club lead)
    if assigned_user.id != club.lead_id:
        is_member = db.query(ClubMember).filter(
            ClubMember.club_id == task_data.club_id,
            ClubMember.user_id == assigned_user.id
        ).first()
        
        if not is_member:
            raise HTTPException(status_code=400, detail="Assigned user is not a member of this club")
    
    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        club_id=task_data.club_id,
        assigned_to=task_data.assigned_to,
        assigned_by=current_user.id,
        deadline=task_data.deadline,
        status="pending"
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return {
        "id": new_task.id,
        "title": new_task.title,
        "description": new_task.description,
        "status": new_task.status,
        "club_id": new_task.club_id,
        "club_name": club.name,
        "assigned_to": new_task.assigned_to,
        "assigned_to_name": assigned_user.name,
        "assigned_by": new_task.assigned_by,
        "assigned_by_name": current_user.name,
        "deadline": new_task.deadline,
        "created_at": new_task.created_at
    }

@app.put("/tasks/{task_id}/status")
def update_task_status(
    task_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    club = db.query(Club).filter(Club.id == task.club_id).first()
    is_authorized = (task.assigned_to == current_user.id) or \
                    (club and club.lead_id == current_user.id) or \
                    (current_user.role == "admin")
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
    
    if status not in ["pending", "in_progress", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    old_status = task.status
    task.status = status
    db.commit()
    
    from audit_middleware import log_action
    log_action(
        db=db,
        user_id=current_user.id,
        action="UPDATE_TASK_STATUS",
        table_name="tasks",
        record_id=task_id,
        old_value={"status": old_status},
        new_value={"status": status}
    )
    
    return {"message": f"Task status updated from {old_status} to {status}"}

@app.get("/tasks/pending/count")
def get_pending_tasks_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(Task).filter(
        Task.assigned_to == current_user.id,
        Task.status == "pending"
    ).count()
    
    return {"pending_count": count}

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a task (only if status is 'pending')"""
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    club = db.query(Club).filter(Club.id == task.club_id).first()
    is_authorized = (club and club.lead_id == current_user.id) or (current_user.role == "admin")
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Only club lead can delete tasks")
    
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot delete task that is in progress or completed")
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}

@app.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a task (only if status is 'pending')"""
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    club = db.query(Club).filter(Club.id == task.club_id).first()
    is_authorized = (club and club.lead_id == current_user.id) or (current_user.role == "admin")
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Only club lead can edit tasks")
    
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot edit task that is in progress or completed")
    
    task.title = task_data.title
    task.description = task_data.description
    task.assigned_to = task_data.assigned_to
    task.deadline = task_data.deadline
    
    db.commit()
    db.refresh(task)
    
    return task

@app.post("/tasks/{task_id}/comments")
def add_task_comment(
    task_id: int,
    comment: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add comment to a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    new_comment = TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        comment=comment
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return new_comment

@app.get("/tasks/{task_id}/comments")
def get_task_comments(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all comments for a task"""
    comments = db.query(TaskComment).filter(TaskComment.task_id == task_id).all()
    result = []
    for comment in comments:
        user = db.query(User).filter(User.id == comment.user_id).first()
        result.append({
            "id": comment.id,
            "comment": comment.comment,
            "name": user.name if user else "Unknown",
            "created_at": comment.created_at,
            "attachment_url": comment.attachment_url
        })
    
    return result

# ========== USER CLUBS ENDPOINT ==========
@app.get("/users/my-clubs")
def get_my_clubs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get clubs where user is a member"""
    lead_clubs = db.query(Club).filter(Club.lead_id == current_user.id).all()
    
    memberships = db.query(ClubMember).filter(ClubMember.user_id == current_user.id).all()
    member_clubs = []
    for membership in memberships:
        club = db.query(Club).filter(Club.id == membership.club_id).first()
        if club:
            member_clubs.append({
                "id": club.id,
                "name": club.name,
                "role": membership.role,
                "joined_at": membership.joined_at
            })
    
    return {
        "lead_clubs": [{"id": c.id, "name": c.name} for c in lead_clubs],
        "member_clubs": member_clubs
    }

# ========== SKILL CATEGORIES & SEARCH ==========
@app.get("/skill-categories")
def get_skill_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all skill categories"""
    categories = db.query(SkillCategory).all()
    return [{"id": c.id, "name": c.name, "icon": c.icon} for c in categories]

@app.get("/skills/search")
def search_skills(
    q: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    skill_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search skills with filters"""
    query = db.query(Skill).filter(Skill.status == "active")
    
    if q:
        query = query.filter(
            (Skill.title.ilike(f"%{q}%")) | 
            (Skill.description.ilike(f"%{q}%"))
        )
    
    if skill_type:
        query = query.filter(Skill.skill_type == skill_type)
    
    skills = query.all()
    return skills

# ========== ADMIN ENDPOINTS ==========
@app.get("/admin/users")
def get_all_users(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Get all users (Admin only)"""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "points": u.points
        }
        for u in users
    ]

@app.put("/admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: str,
    club_id: Optional[int] = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Update a user's role (Admin only)"""
    
    if new_role not in ["student", "club_lead", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    old_role = user.role
    user.role = new_role
    
    if new_role == "club_lead" and club_id:
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        club.lead_id = user_id
    
    db.commit()
    
    return {
        "message": f"User {user.name} role changed from {old_role} to {new_role}",
        "user_id": user.id,
        "email": user.email,
        "new_role": user.role,
        "club_id": club_id if new_role == "club_lead" else None
    }

@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Delete a user (Admin only)"""
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove user from all club memberships
    db.query(ClubMember).filter(ClubMember.user_id == user_id).delete()

    # Handle clubs where user is lead
    lead_clubs = db.query(Club).filter(Club.lead_id == user_id).all()
    for club in lead_clubs:
        # You might want to assign a new lead or handle this differently
        # For now, we'll just remove the lead_id
        club.lead_id = None

    db.delete(user)
    db.commit()
    
    return {"message": f"User {user.email} deleted successfully"}

@app.delete("/admin/clubs/{club_id}")
def delete_club(
    club_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Delete a club (Admin only)"""
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    db.query(Task).filter(Task.club_id == club_id).delete()
    db.query(Event).filter(Event.club_id == club_id).delete()
    db.query(ClubMember).filter(ClubMember.club_id == club_id).delete()
    
    db.delete(club)
    db.commit()
    
    return {"message": f"Club '{club.name}' deleted successfully"}