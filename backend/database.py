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
    
    # Postgres usage
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # -------------------------------------------------------------------------
    # SMART FIX: Use Supabase Connection Pooler (IPv4)
    # Direct connection (db.xxx.supabase.co) resolves to IPv6-only on Vercel, causing failure.
    # We rewrite the URL to use the IPv4-compatible connection pooler.
    # Assumed Region: ap-south-1 (based on user location)
    # -------------------------------------------------------------------------
    try:
        from urllib.parse import urlparse, urlunparse
        
        parsed = urlparse(SQLALCHEMY_DATABASE_URL)
        hostname = parsed.hostname
        
        # Check if direct Supabase URL
        if hostname and hostname.endswith(".supabase.co") and "db." in hostname:
            project_ref = hostname.split(".")[0].replace("db.", "")
            
            # 1. Update Hostname to Pooler (IPv4 compatible)
            # Defaulting to ap-south-1 (Mumbai) based on user location
            pooler_hostname = "aws-0-ap-south-1.pooler.supabase.com"
            
            # 2. Update Username to [user].[project_ref] for Pooler
            username = parsed.username
            if username and "." not in username:
                new_username = f"{username}.{project_ref}"
            else:
                new_username = username
            
            # Reconstruct URL with new host and username
            # scheme://user:pass@host:port/path?query
            port = parsed.port or 5432
            
            # Fix: urlparse is immutable, construct string manually or use replacement
            # Password might have special chars, so we use string replacement carefully
            # A safer way to replace netloc:
            new_netloc = f"{new_username}:{parsed.password}@{pooler_hostname}:{port}"
            
            # Replace netloc in the parsed object (requires converting to list/dict or using format)
            # Simplest: String replacement on the URL if it matches standard format
            # But let's be robust.
            
            SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(hostname, pooler_hostname)
            
            # Replace username in URL if needed
            if username != new_username:
                 SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(f"{username}:", f"{new_username}:", 1)
            
            print(f"✅ Auto-Switched to IPv4 Pooler: {pooler_hostname}")
            
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
    # Pooler usually supports it but might not strictly require 'sslmode=require' in query
    # We keep it as is, or relax it if pooler rejects. 
    # Usually pooler accepts sslmode=require.
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
