from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Get Database URL from environment variable
# If using Supabase, ensure the connection string is for "transaction mode" (port 6543) or "session mode" (port 5432)
# Example: postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    # Fallback to SQLite
    SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/commissions.db"
    connect_args = {"check_same_thread": False}
else:
    # Postgres adjustments
    connect_args = {}
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create Database Engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
