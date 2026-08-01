import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData
from sqlalchemy.orm import declarative_base

# Load environment variables
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Create the database engine
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
Base = declarative_base()

# 1. Define the Patients Table
class Patient(Base):
    __tablename__ = 'patients'
    patient_nbr = Column(Integer, primary_key=True)
    race = Column(String)
    gender = Column(String)
    age = Column(String)
    weight = Column(String)

# 2. Define the Admissions Table
class Admission(Base):
    __tablename__ = 'admissions'
    encounter_id = Column(Integer, primary_key=True)
    patient_nbr = Column(Integer) # Foreign key logic will be applied later
    admission_type_id = Column(Integer)
    discharge_disposition_id = Column(Integer)
    admission_source_id = Column(Integer)
    time_in_hospital = Column(Integer)

if __name__ == "__main__":
    print("Connecting to the database...")
    # This command creates the empty tables in pgAdmin
    Base.metadata.create_all(engine)
    print("Tables created successfully!")