from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
import socket
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

# Get Database URL from environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    # Fallback to SQLite
    SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/commissions.db"
    connect_args = {"check_same_thread": False}
    try:
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args=connect_args
        )
    except Exception as e:
        print(f"CRITICAL: Error creating SQLite DB engine: {e}")
        engine = None
else:
    # Postgres usage
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # -------------------------------------------------------------------------
    # SMART FIX: Use Supabase Connection Pooler (IPv4) - Transaction Mode
    # -------------------------------------------------------------------------
    try:
        from sqlalchemy.engine.url import make_url
        
        # Safe URL parsing
        db_url = make_url(SQLALCHEMY_DATABASE_URL)
        
        # Check if direct Supabase URL (db.project.supabase.co)
        if db_url.host and db_url.host.endswith(".supabase.co") and "db." in db_url.host:
            project_ref = db_url.host.split(".")[0].replace("db.", "")
            
            # Switch to Transaction Mode Pooler (IPv4 compatible, Port 6543)
            # This is cleaner for Serverless environments
            pooler_hostname = "aws-0-ap-south-1.pooler.supabase.com"
            
            # Update User: postgres -> postgres.project_ref
            current_user = db_url.username
            if current_user and "." not in current_user:
                new_user = f"{current_user}.{project_ref}"
            else:
                new_user = current_user
                
            # Construct new robust URL
            # Note: set() returns a NEW URL object in newer SQLAlchemy versions
            db_url = db_url.set(
                host=pooler_hostname,
                username=new_user,
                port=6543
            )
            
            SQLALCHEMY_DATABASE_URL = str(db_url)
            print(f"✅ Auto-Switched to IPv4 Pooler (Tx Mode): {pooler_hostname}")
            
    except Exception as e:
        print(f"⚠️ Failed to apply Pooler fix: {e}")
    # -------------------------------------------------------------------------

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
