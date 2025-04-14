from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base, SessionLocal  # Import SessionLocal
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
class FundFamily(Base):
    __tablename__ = "fund_families"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    api_code = Column(String)  # Code used in RapidAPI
    
class FundScheme(Base):
    __tablename__ = "fund_schemes"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("fund_families.id"))
    scheme_name = Column(String)
    scheme_code = Column(String)  # Code used in RapidAPI
    is_open_ended = Column(Integer, default=1)  # 1 for open-ended
    
class UserPortfolio(Base):
    __tablename__ = "user_portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    scheme_id = Column(Integer, ForeignKey("fund_schemes.id"))
    amount_invested = Column(Float)
    units_held = Column(Float)
    last_updated = Column(DateTime, default=func.now())