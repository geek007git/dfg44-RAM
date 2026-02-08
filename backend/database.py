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
    # TARGETED FIX: Use Supabase Connection Pooler (IPv4)
    # -------------------------------------------------------------------------
    try:
        from urllib.parse import urlparse, urlunparse, quote_plus
        
        # Use standard urllib to parse
        parsed = urlparse(SQLALCHEMY_DATABASE_URL)
        
        # Check for specific project hostname to be absolutely sure
        if "dteuzkezeefjhumdlojo" in parsed.hostname:
            print("✅ Detected Project: dteuzkezeefjhumdlojo")
            
            # 1. Host -> Pooler
            new_hostname = "aws-0-ap-south-1.pooler.supabase.com"
            
            # 2. Port -> 6543 (Transaction Mode)
            new_port = 6543
            
            # 3. User -> user.project_ref
            username = parsed.username
            project_ref = "dteuzkezeefjhumdlojo"
            if username and "." not in username:
                new_username = f"{username}.{project_ref}"
            else:
                new_username = username
                
            # Reconstruct the URL manually to avoid library issues
            # scheme://user:pass@host:port/path
            
            # Handle password safely (it might have special chars)
            password = parsed.password
            path = parsed.path
            query = parsed.query
            
            # Rebuild netloc
            new_netloc = f"{new_username}:{password}@{new_hostname}:{new_port}"
            
            # Update the URL
            # _replace method is available on the named tuple returned by urlparse
            new_parsed = parsed._replace(netloc=new_netloc)
            SQLALCHEMY_DATABASE_URL = urlunparse(new_parsed)
            
            print(f"✅ REWRITTEN URL TO: {new_hostname}:{new_port}")
            
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
