from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class FundFamilyBase(BaseModel):
    name: str
    api_code: str

class FundSchemeBase(BaseModel):
    scheme_name: str
    scheme_code: str
    is_open_ended: bool

class PortfolioCreate(BaseModel):
    scheme_id: int
    amount_invested: float
    units_held: float

class PortfolioOut(BaseModel):
    scheme_name: str
    amount_invested: float
    units_held: float
    current_value: Optional[float]
    growth: Optional[float]