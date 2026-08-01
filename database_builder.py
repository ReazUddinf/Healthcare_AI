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
    patient_nbr = Column(Integer) 
    admission_type_id = Column(Integer)
    discharge_disposition_id = Column(Integer)
    admission_source_id = Column(Integer)
    time_in_hospital = Column(Integer)

if __name__ == "__main__":
    print("Connecting to the database...")
    # 1. Create tables 
    Base.metadata.create_all(engine)
    print("Tables verified!")

    # 2. Extract: Read the raw CSV
    print("Reading raw CSV file...")
    df = pd.read_csv('raw_data/diabetic_data.csv') 

    # 3. Transform: Separate into Patients and Admissions
    print("Transforming data...")
    # Get unique patients by dropping duplicate patient numbers
    patients_df = df[['patient_nbr', 'race', 'gender', 'age', 'weight']].drop_duplicates(subset=['patient_nbr'])
    
    # Get all admission records
    admissions_df = df[['encounter_id', 'patient_nbr', 'admission_type_id', 'discharge_disposition_id', 'admission_source_id', 'time_in_hospital']]

    # 4. Load: Insert the data into PostgreSQL
    print(f"Loading {len(patients_df)} unique patients into the database...")
    patients_df.to_sql('patients', engine, if_exists='append', index=False)

    print(f"Loading {len(admissions_df)} admissions into the database...")
    admissions_df.to_sql('admissions', engine, if_exists='append', index=False)

    print("ETL Pipeline completed successfully! Data is now in PostgreSQL.")