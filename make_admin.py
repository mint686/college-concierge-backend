from database import SessionLocal
from models import User

db = SessionLocal()

# Replace with the user's email
email = "student@iiitn.ac.in"

user = db.query(User).filter(User.email == email).first()
if user:
    user.role = "admin"
    db.commit()
    print(f"✅ {user.name} is now a admin!")
else:
    print(f"❌ User with email {email} not found")

db.close()