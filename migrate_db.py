"""
Database Migration Script for Render PostgreSQL
Run this script to create the club_members table
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Your Render PostgreSQL connection string
DATABASE_URL = "postgresql://postgres:Runya%40686@localhost:5432/college_concierge"

def run_migration():
    """Create club_members table"""
    
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
        
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'club_members'
            )
        """)
        
        exists = cur.fetchone()[0]
        
        if exists:
            print("⚠️  Table 'club_members' already exists!")
        else:
            print("Creating table 'club_members'...")
            
            # Create table
            cur.execute("""
                CREATE TABLE club_members (
                    id SERIAL PRIMARY KEY,
                    club_id INTEGER REFERENCES clubs(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    role VARCHAR(20) DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ Table 'club_members' created!")
            
            # Create indexes
            print("Creating indexes...")
            cur.execute("CREATE INDEX idx_club_members_club_id ON club_members(club_id)")
            cur.execute("CREATE INDEX idx_club_members_user_id ON club_members(user_id)")
            print("✅ Indexes created!")
        
        # Commit the transaction
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Verify the table
        print("\nVerifying table structure...")
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'club_members'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        print("\n📋 Table 'club_members' columns:")
        print("-" * 50)
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
        print("-" * 50)
        
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
    print("=" * 50)
    print("College Concierge Database Migration")
    print("=" * 50)
    run_migration()
    print("\n" + "=" * 50)