from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
import socket
from dotenv import load_dotenv
from fastapi import HTTPException

# WORKAROUND: Force IPv4 to avoid "Cannot assign requested address" on Vercel (IPv6 issues)
# This filters out IPv6 addresses from DNS resolution
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

load_dotenv()

# Get Database URL from environment variable
# If using Supabase, ensure the connection string is for "transaction mode" (port 6543) or "session mode" (port 5432)
# Example: postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    # Fallback to SQLite
    SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/commissions.db"
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args=connect_args
    )
else:
    # Postgres usage
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    connect_args = {
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
    
    # Supabase/Postgres on Vercel often requires SSL
    if "supabase" in SQLALCHEMY_DATABASE_URL and "sslmode" not in SQLALCHEMY_DATABASE_URL:
        connect_args["sslmode"] = "require"

    # Create Database Engine with NullPool for Serverless
    try:
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args=connect_args, poolclass=NullPool
        )
    except Exception as e:
        print(f"CRITICAL: Error creating DB engine: {e}")
        engine = None

# Create SessionLocal class
# If engine is None, this will create an unbound session factory.
# Attempts to use the session for DB operations will fail, but the app will start.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency
def get_db():
    if engine is None:
        raise HTTPException(status_code=500, detail="Database connection failed to initialize")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
