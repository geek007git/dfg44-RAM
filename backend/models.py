from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Commission(Base):
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(String)
    
    applications = relationship("Application", back_populates="commission")

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"))
    full_name = Column(String)
    email = Column(String)
    portfolio_url = Column(String)
    cover_letter = Column(Text)
    status = Column(String, default="Pending") # Added status field
    created_at = Column(DateTime, default=datetime.utcnow)

    commission = relationship("Commission", back_populates="applications")
