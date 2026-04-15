import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable (Render provides this)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mint:XaF4tsWwF1gb5RjDGneEoMFg6QWlJEHC@dpg-d7fnoe9f9bms73ekqgsg-a.singapore-postgres.render.com/college_concierge")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()