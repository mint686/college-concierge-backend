from database import SessionLocal
from models import User

db = SessionLocal()

# Replace with the user's email
email = "student3@iiitn.ac.in"

user = db.query(User).filter(User.email == email).first()
if user:
    user.role = "club_lead"
    db.commit()
    print(f"✅ {user.name} is now a Club Lead!")
else:
    print(f"❌ User with email {email} not found")

db.close()