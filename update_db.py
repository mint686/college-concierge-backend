import psycopg2
import os

# Your Render database connection details (from Render dashboard)
DATABASE_URL = "postgresql://mint:XaF4tsWwF1gb5RjDGneEoMFg6QWlJEHC@dpg-d7fnoe9f9bms73ekqgsg-a.singapore-postgres.render.com/college_concierge"
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
        
        print("✅ Database migration completed successfully!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_migration()