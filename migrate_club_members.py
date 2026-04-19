"""
Migration Script: Add name and email columns to club_members table
Run this script to update existing databases with the new denormalized fields
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Your Render PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mint:XaF4tsWwF1gb5RjDGneEoMFg6QWlJEHC@dpg-d7fnoe9f9bms73ekqgsg-a.singapore-postgres.render.com/college_concierge")

def run_migration():
    """Add name and email columns to club_members table"""

    print("Starting migration...")
    print(f"Connecting to database...")

    conn = None
    cur = None

    try:
        # Connect using DATABASE_URL directly
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cur = conn.cursor()

        print("✅ Connected to database successfully!")

        # Check if columns already exist
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'club_members' AND column_name IN ('name', 'email')
        """)

        existing_columns = [row[0] for row in cur.fetchall()]

        if 'name' in existing_columns and 'email' in existing_columns:
            print("⚠️  Columns 'name' and 'email' already exist in club_members table!")
            return

        # Add name column if it doesn't exist
        if 'name' not in existing_columns:
            print("Adding 'name' column...")
            cur.execute("ALTER TABLE club_members ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT 'Unknown'")
            print("✅ 'name' column added!")

        # Add email column if it doesn't exist
        if 'email' not in existing_columns:
            print("Adding 'email' column...")
            cur.execute("ALTER TABLE club_members ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT 'unknown@example.com'")
            print("✅ 'email' column added!")

        # Populate the new columns with data from users table
        print("Populating new columns with existing user data...")
        cur.execute("""
            UPDATE club_members
            SET name = users.name, email = users.email
            FROM users
            WHERE club_members.user_id = users.id
        """)
        print("✅ Data populated!")

        # Commit the transaction
        conn.commit()
        print("✅ Migration completed successfully!")

        # Verify the changes
        print("\nVerifying table structure...")
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'club_members'
            ORDER BY ordinal_position
        """)

        columns = cur.fetchall()
        print("\n📋 Updated club_members table columns:")
        print("-" * 60)
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
        print("-" * 60)

        # Show sample data
        cur.execute("SELECT id, user_id, name, email, role FROM club_members LIMIT 5")
        sample_data = cur.fetchall()
        if sample_data:
            print("\n📋 Sample club_members data:")
            print("-" * 60)
            for row in sample_data:
                print(f"  ID: {row[0]}, UserID: {row[1]}, Name: {row[2]}, Email: {row[3]}, Role: {row[4]}")
            print("-" * 60)

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("\n🔒 Database connection closed.")

if __name__ == "__main__":
    print("=" * 60)
    print("Club Members Table Migration")
    print("Adding name and email columns for denormalization")
    print("=" * 60)
    run_migration()