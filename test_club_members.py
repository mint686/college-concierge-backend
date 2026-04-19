"""
Test script to verify the denormalized ClubMember table works correctly
"""

from models import ClubMember, User, Club, Base
from database import engine
from sqlalchemy.orm import sessionmaker

def test_club_member_denormalization():
    """Test that ClubMember table now stores name and email directly"""

    print("Testing ClubMember denormalization...")

    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if we have any club members
        members = db.query(ClubMember).limit(3).all()

        if not members:
            print("⚠️  No club members found in database. Skipping detailed test.")
            return

        print(f"Found {len(members)} club members to test")

        for i, member in enumerate(members, 1):
            print(f"\nMember {i}:")
            print(f"  ID: {member.id}")
            print(f"  User ID: {member.user_id}")
            print(f"  Stored Name: {member.name}")
            print(f"  Stored Email: {member.email}")
            print(f"  Role: {member.role}")
            print(f"  Joined At: {member.joined_at}")

            # Verify the data matches the User table
            user = db.query(User).filter(User.id == member.user_id).first()
            if user:
                name_match = member.name == user.name
                email_match = member.email == user.email
                print(f"  Name Match: {'✅' if name_match else '❌'}")
                print(f"  Email Match: {'✅' if email_match else '❌'}")

                if not name_match or not email_match:
                    print("  ❌ Data inconsistency detected!")
                else:
                    print("  ✅ Data is consistent")
            else:
                print("  ❌ User not found in users table!")

        print("\n✅ ClubMember denormalization test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("ClubMember Denormalization Test")
    print("=" * 60)
    test_club_member_denormalization()