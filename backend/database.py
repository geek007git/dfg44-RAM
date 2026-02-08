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
    # WORKAROUND: Force IPv4 for Supabase on Vercel
    # Vercel sometimes attempts IPv6 connections which fail with "Cannot assign requested address"
    # We manually resolve the hostname to an IPv4 address to bypass this.
    # -------------------------------------------------------------------------
    try:
        from urllib.parse import urlparse
        parsed = urlparse(SQLALCHEMY_DATABASE_URL)
        hostname = parsed.hostname
        
        if hostname:
            ip_address = socket.gethostbyname(hostname)
            SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(hostname, ip_address)
            print(f"✅ Resolved {hostname} to {ip_address} to force IPv4 connection")
    except Exception as e:
        print(f"⚠️ Failed to force IPv4 resolution: {e}")
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
