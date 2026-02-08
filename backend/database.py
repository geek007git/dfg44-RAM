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
    # BRUTE FORCE FIX: Use Supabase Connection Pooler (IPv4)
    # -------------------------------------------------------------------------
    try:
        # Only act if we see the specific project ID in the URL
        if "dteuzkezeefjhumdlojo" in SQLALCHEMY_DATABASE_URL:
            print("✅ BRUTE FORCE: Detected Project dteuzkezeefjhumdlojo")
            
            # 1. Ensure Scheme is postgresql://
            if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
                SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
            
            # 2. Simple String Replace for Hostname
            # This handles the host switch
            if "db.dteuzkezeefjhumdlojo.supabase.co" in SQLALCHEMY_DATABASE_URL:
                SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
                    "db.dteuzkezeefjhumdlojo.supabase.co", 
                    "aws-0-ap-south-1.pooler.supabase.com"
                )
            
            # 3. Port: Keep as 5432 (Session Mode)
            # Transaction mode (6543) breaks SQLAlchemy defaults (prepared statements).
            # We stick to 5432 for maximum compatibility.
            # if ":5432" in SQLALCHEMY_DATABASE_URL:
            #     SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(":5432", ":6543")
                
            # 4. Fix Username (postgres -> postgres.dteuzkezeefjhumdlojo)
            # We need to be careful not to replace password parts.
            # Splitting by @ lets us isolate credentials.
            if "@" in SQLALCHEMY_DATABASE_URL:
                parts = SQLALCHEMY_DATABASE_URL.split("@")
                # parts[0] is 'postgresql://user:pass'
                # parts[1] is 'host:port/db'
                
                creds_section = parts[0]
                if "://" in creds_section:
                    scheme, creds = creds_section.split("://")
                    if ":" in creds:
                        user, password = creds.split(":", 1)
                        if "." not in user:
                            new_user = f"{user}.dteuzkezeefjhumdlojo"
                            # Rebuild the first part
                            parts[0] = f"{scheme}://{new_user}:{password}"
                            # Rejoin entire URL
                            SQLALCHEMY_DATABASE_URL = "@".join(parts)
                            print(f"✅ BRUTE FORCE: Updated username to {new_user}")
            
            print(f"✅ BRUTE FORCE URL: {SQLALCHEMY_DATABASE_URL.split('@')[1]}") # Log safe part
            
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
