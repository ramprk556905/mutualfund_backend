from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import models
load_dotenv()

SQLALCHEMY_DATABASE_URL = f"postgresql://ramprk97:{os.getenv("db_password")}@dpg-cvtsah1r0fns73dvt7rg-a.frankfurt-postgres.render.com/mutual_fund_kxds"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Import all models here so that Base.metadata.create_all() can detect them
  # Ensure this imports all your SQLAlchemy models

# Create tables if they do not exist
def create_tables():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Check if each model's table exists, and create it if not
    for table_name in Base.metadata.tables.keys():
        if table_name not in existing_tables:
            print(f"Creating table: {table_name}")
            Base.metadata.tables[table_name].create(bind=engine)
        else:
            print(f"Table already exists: {table_name}")

# Call this function during application startup or initialization
create_tables()