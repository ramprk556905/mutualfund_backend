from sqlalchemy.orm import Session
import models
import schemas
from auth import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_fund_families(db: Session):
    return db.query(models.FundFamily).all()

def get_fund_schemes(db: Session, family_id: int, open_ended_only: bool = True):
    query = db.query(models.FundScheme).filter(models.FundScheme.family_id == family_id)
    if open_ended_only:
        query = query.filter(models.FundScheme.is_open_ended == 1)
    return query.all()

def create_user_portfolio(db: Session, portfolio: schemas.PortfolioCreate, user_id: int):
    db_portfolio = models.UserPortfolio(**portfolio.dict(), user_id=user_id)
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

def get_user_portfolio(db: Session, user_id: int):
    return db.query(models.UserPortfolio).filter(models.UserPortfolio.user_id == user_id).all()