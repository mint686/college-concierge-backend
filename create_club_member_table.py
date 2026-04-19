"""
Script to add ClubMember table to existing database
Run this once to create the missing table
"""
from database import engine
from models import Base, ClubMember
from sqlalchemy import inspect

# Check if table exists
inspector = inspect(engine)
tables = inspector.get_table_names()

if 'club_members' in tables:
    print("ClubMember table already exists!")
else:
    print("Creating ClubMember table...")
    ClubMember.__table__.create(engine)
    print("ClubMember table created successfully!")