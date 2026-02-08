from fastapi import FastAPI, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import os
import json

from . import models, schemas, database
from .models import Commission, Application

# Create tables
# Create tables (safely)
try:
    models.Base.metadata.create_all(bind=database.engine)
except Exception as e:
    print(f"Failed to create tables. Verify DB connection: {e}")

app = FastAPI()

# Determine absolute path to frontend directory
# current file is in backend/main.py, so we go up one level
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Static Files & Pages
if not os.path.exists(FRONTEND_DIR):
    os.makedirs(FRONTEND_DIR)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Database dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. Fetch All Commissions
@app.get("/api/commissions", response_model=List[schemas.Commission])
def get_commissions(db: Session = Depends(get_db)):
    commissions = db.query(Commission).all()
    return commissions

# 2. Fetch Single Commission
@app.get("/api/commissions/{commission_id}", response_model=schemas.Commission)
def get_commission(commission_id: int, db: Session = Depends(get_db)):
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if commission is None:
        raise HTTPException(status_code=404, detail="Commission not found")
    return commission

# 3. Create Application
@app.post("/api/commissions/{commission_id}/apply", response_model=schemas.Application)
def create_application(commission_id: int, application: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if commission is None:
        raise HTTPException(status_code=404, detail="Commission not found")
    
    db_application = models.Application(
        commission_id=commission_id,
        full_name=application.full_name,
        email=application.email,
        portfolio_url=application.portfolio_url,
        cover_letter=application.cover_letter,
        status="Pending"
    )
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

# 4. Get Application Status
@app.get("/api/applications/{application_id}", response_model=schemas.Application)
def get_application_status(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

# 5. Admin: Get All Applications
@app.get("/api/admin/applications", response_model=List[schemas.Application])
def get_all_applications(db: Session = Depends(get_db)):
    return db.query(Application).order_by(Application.created_at.desc()).all()

# 6. Admin: Update Application Status
@app.put("/api/applications/{application_id}/status", response_model=schemas.Application)
def update_application_status(application_id: int, status_update: schemas.ApplicationStatusUpdate, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = status_update.status
    db.commit()
    db.refresh(application)
    return application

# WebSocket
@app.websocket("/ws/application/{application_id}")
async def websocket_endpoint(websocket: WebSocket, application_id: int):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Server received: {data}")
    except Exception:
        pass

@app.get("/api/debug-db")
def debug_database():
    import os
    import socket
    from urllib.parse import urlparse
    
    db_url = os.getenv("DATABASE_URL")
    
    status = {
        "database_url_present": bool(db_url),
        "engine_initialized": database.engine is not None,
        "connection_error": None,
        "dns_resolution": "Not attempted"
    }
    
    # Test DNS Resolution Logic
    if db_url:
        try:
            parsed = urlparse(db_url)
            hostname = parsed.hostname
            if hostname:
                ip = socket.gethostbyname(hostname)
                status["dns_resolution"] = f"Hostname: {hostname} -> IP: {ip}"
                status["hostname"] = hostname
                status["resolved_ip"] = ip
                
                # Check what the engine is actually using
                if database.engine:
                    status["engine_url_host"] = database.engine.url.host
            else:
                status["dns_resolution"] = "Could not parse hostname from URL"
        except Exception as e:
            status["dns_resolution"] = f"DNS Error: {str(e)}"

    # Mask URL for security if present
    if db_url:
        status["masked_url"] = db_url[:15] + "..." if len(db_url) > 15 else "Short URL"

    if database.engine:
        try:
            with database.engine.connect() as connection:
                from sqlalchemy import text
                result = connection.execute(text("SELECT 1"))
                status["connection_test"] = "Success - SELECT 1 returned row"
        except Exception as e:
            status["connection_error"] = str(e)
    
    return status

@app.get("/")
def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))

@app.get("/commission/{id}")
def read_commission_page(id: int):
    return FileResponse(os.path.join(FRONTEND_DIR, 'commission.html'))

@app.get("/status/{id}")
def read_status_page(id: int):
    return FileResponse(os.path.join(FRONTEND_DIR, 'status.html'))

@app.get("/admin")
def read_admin_page():
    return FileResponse(os.path.join(FRONTEND_DIR, 'admin.html'))

@app.get("/interview")
def read_interview_page():
    return FileResponse(os.path.join(FRONTEND_DIR, 'interview.html'))
