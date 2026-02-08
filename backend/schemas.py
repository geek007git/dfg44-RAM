from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class ApplicationBase(BaseModel):
    full_name: str
    email: EmailStr
    portfolio_url: Optional[str] = None
    cover_letter: str

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationStatusUpdate(BaseModel):
    status: str

class Application(ApplicationBase):
    id: int
    commission_id: int
    status: str 
    created_at: datetime

    class Config:
        from_attributes = True

class CommissionBase(BaseModel):
    title: str
    description: str
    category: str

class Commission(CommissionBase):
    id: int
    # applications: List[Application] = [] # Optional

    class Config:
        from_attributes = True
