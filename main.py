from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import crud, models, schemas
from database import engine, SessionLocal  # Import get_db from database.py
from auth import get_current_user, create_access_token, get_password_hash, verify_password
from datetime import timedelta
import requests
from models import get_db
from typing import List

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RapidAPI configuration
RAPIDAPI_KEY = "583330d9bamshe256b334c0726c7p1c213cjsnacf754f76a10" 
RAPIDAPI_HOST = "latest-mutual-fund-nav.p.rapidapi.com"
RAPIDAPI_URL = "https://latest-mutual-fund-nav.p.rapidapi.com/latest"

@app.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):  
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = crud.create_user(db=db, user=user)
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/fund-families", response_model=List[schemas.FundFamilyBase])
def get_families(db: Session = Depends(get_db)):
    return crud.get_fund_families(db)

@app.get("/fund-schemes/{family_id}", response_model=List[schemas.FundSchemeBase])
def get_schemes(family_id: int, open_ended: bool = True, db: Session = Depends(get_db)):
    # First check if we have schemes in DB
    schemes = crud.get_fund_schemes(db, family_id, open_ended)
    
    if not schemes:
        # If no schemes in DB, fetch from RapidAPI
        family = db.query(models.FundFamily).filter(models.FundFamily.id == family_id).first()
        if not family:
            raise HTTPException(status_code=404, detail="Fund family not found")
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        params = {"family": family.api_code}
        if open_ended:
            params["type"] = "open-ended"
        
        response = requests.get(RAPIDAPI_URL, headers=headers, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch schemes from API")
        
        # Parse response and save to DB
        api_data = response.json()
        for scheme in api_data.get("schemes", []):
            db_scheme = models.FundScheme(
                family_id=family_id,
                scheme_name=scheme.get("scheme_name"),
                scheme_code=scheme.get("scheme_code"),
                is_open_ended=1 if scheme.get("type") == "open-ended" else 0
            )
            db.add(db_scheme)
        db.commit()
        
        # Now get from DB
        schemes = crud.get_fund_schemes(db, family_id, open_ended)
    
    return schemes

@app.post("/portfolio", response_model=schemas.PortfolioOut)
def add_to_portfolio(
    portfolio: schemas.PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check if scheme exists
    scheme = db.query(models.FundScheme).filter(models.FundScheme.id == portfolio.scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    
    portfolio = crud.create_user_portfolio(db, portfolio, current_user.id)
    
    # Get current NAV from RapidAPI to calculate current value
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    params = {"scheme": scheme.scheme_code}
    response = requests.get(RAPIDAPI_URL, headers=headers, params=params)
    if response.status_code != 200:
        current_nav = 0
    else:
        api_data = response.json()
        current_nav = api_data.get("nav", 0)
    
    current_value = portfolio.units_held * current_nav
    growth = ((current_value - portfolio.amount_invested) / portfolio.amount_invested) * 100
    
    return {
        "scheme_name": scheme.scheme_name,
        "amount_invested": portfolio.amount_invested,
        "units_held": portfolio.units_held,
        "current_value": current_value,
        "growth": growth
    }

@app.get("/portfolio", response_model=List[schemas.PortfolioOut])
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    portfolio_items = crud.get_user_portfolio(db, current_user.id)
    result = []
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    for item in portfolio_items:
        scheme = db.query(models.FundScheme).filter(models.FundScheme.id == item.scheme_id).first()
        if not scheme:
            raise HTTPException(status_code=404, detail=f"Scheme with ID {item.scheme_id} not found")
            
        # Get current NAV
        params = {"scheme": scheme.scheme_code}
        response = requests.get(RAPIDAPI_URL, headers=headers, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch NAV from API")
        
        api_data = response.json()
        current_nav = api_data.get("nav", 0)
        
        current_value = item.units_held * current_nav
        if item.amount_invested == 0:
            growth = 0
        else:
            growth = ((current_value - item.amount_invested) / item.amount_invested) * 100
        
        result.append({
            "scheme_name": scheme.scheme_name,
            "amount_invested": item.amount_invested,
            "units_held": item.units_held,
            "current_value": current_value,
            "growth": growth
        })
    
    return result