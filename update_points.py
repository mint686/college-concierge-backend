"""
Script to update user points
Usage: python update_points.py
"""

from database import SessionLocal
from models import User
import sys

def update_user_points(email: str, new_points: int):
    """Update points for a specific user by email"""
    
    db = SessionLocal()
    
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found!")
            return False
        
        old_points = user.points
        user.points = new_points
        db.commit()
        
        print(f"✅ Points updated for {user.name} ({user.email})")
        print(f"   Old points: {old_points}")
        print(f"   New points: {new_points}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def add_points(email: str, points_to_add: int):
    """Add points to a user"""
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found!")
            return False
        
        old_points = user.points
        user.points += points_to_add
        db.commit()
        
        print(f"✅ Added {points_to_add} points to {user.name}")
        print(f"   Old points: {old_points}")
        print(f"   New points: {user.points}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def deduct_points(email: str, points_to_deduct: int):
    """Deduct points from a user"""
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found!")
            return False
        
        if user.points < points_to_deduct:
            print(f"❌ Insufficient points! User has {user.points}, trying to deduct {points_to_deduct}")
            return False
        
        old_points = user.points
        user.points -= points_to_deduct
        db.commit()
        
        print(f"✅ Deducted {points_to_deduct} points from {user.name}")
        print(f"   Old points: {old_points}")
        print(f"   New points: {user.points}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def show_all_users():
    """Display all users with their points"""
    
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        
        if not users:
            print("No users found!")
            return
        
        print("\n" + "=" * 60)
        print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Points':<10}")
        print("=" * 60)
        
        for user in users:
            print(f"{user.id:<5} {user.name[:20]:<20} {user.email[:30]:<30} {user.points:<10}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def show_user_points(email: str):
    """Show points for a specific user"""
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found!")
            return
        
        print(f"\n📊 User: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Points: {user.points}")
        print(f"   Role: {user.role}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🔧 College Concierge - User Points Manager")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("  1. Show all users")
        print("  2. Show specific user points")
        print("  3. Update user points")
        print("  4. Add points to user")
        print("  5. Deduct points from user")
        print("  6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            show_all_users()
            
        elif choice == "2":
            email = input("Enter user email: ").strip()
            show_user_points(email)
            
        elif choice == "3":
            email = input("Enter user email: ").strip()
            try:
                points = int(input("Enter new points: ").strip())
                update_user_points(email, points)
            except ValueError:
                print("❌ Invalid points value!")
                
        elif choice == "4":
            email = input("Enter user email: ").strip()
            try:
                points = int(input("Enter points to add: ").strip())
                add_points(email, points)
            except ValueError:
                print("❌ Invalid points value!")
                
        elif choice == "5":
            email = input("Enter user email: ").strip()
            try:
                points = int(input("Enter points to deduct: ").strip())
                deduct_points(email, points)
            except ValueError:
                print("❌ Invalid points value!")
                
        elif choice == "6":
            print("Goodbye!")
            break
            
        else:
            print("❌ Invalid choice!")