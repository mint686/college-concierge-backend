import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable (Render provides this)
DATABASE_URL = os.getenv("postgresql://postgres:HEFcxuJEsEjmNmMTQhndmNqFLXjJbzqM@hopper.proxy.rlwy.net:54778/railway")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()