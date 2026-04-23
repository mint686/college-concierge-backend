import psycopg2
import os

# Your Render database connection details (from Render dashboard)
DATABASE_URL = "postgresql://postgres:Runya%40686@localhost:5432/college_concierge"
def run_migration():
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Create club_members table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_members (
                id SERIAL PRIMARY KEY,
                club_id INTEGER REFERENCES clubs(id),
                user_id INTEGER REFERENCES users(id),
                role VARCHAR(20) DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Add club_id to users table
        cur.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS club_id INTEGER REFERENCES clubs(id)
        """)

        # Add missing skill transaction confirmation columns
        cur.execute("""
            ALTER TABLE skill_transactions
            ADD COLUMN IF NOT EXISTS learner_confirmed BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS teacher_confirmed BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP NULL
        """)

        # Add missing max_rsvps column to events table
        cur.execute("""
            ALTER TABLE events
            ADD COLUMN IF NOT EXISTS max_rsvps INTEGER NULL
        """)
        
        print("✅ Database migration completed successfully!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_migration()