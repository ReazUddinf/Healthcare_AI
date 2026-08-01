import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String
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

# 1. Define Patients Table
class Patient(Base):
    __tablename__ = 'patients'
    patient_nbr = Column(Integer, primary_key=True)
    race = Column(String)
    gender = Column(String)
    age = Column(String)

# 2. Define Admissions Table
class Admission(Base):
    __tablename__ = 'admissions'
    encounter_id = Column(Integer, primary_key=True)
    patient_nbr = Column(Integer) 
    admission_type_id = Column(Integer)
    discharge_disposition_id = Column(Integer)
    admission_source_id = Column(Integer)
    time_in_hospital = Column(Integer)

# 3. Define Diagnoses Table
class Diagnosis(Base):
    __tablename__ = 'diagnoses'
    encounter_id = Column(Integer, primary_key=True)
    diag_1 = Column(String)
    diag_2 = Column(String)
    diag_3 = Column(String)
    number_diagnoses = Column(Integer)

# 4. Define Medications Table
class Medication(Base):
    __tablename__ = 'medications'
    encounter_id = Column(Integer, primary_key=True)
    num_medications = Column(Integer)
    diabetesMed = Column(String)
    change = Column(String)
    insulin = Column(String)

# 5. Define Lab Tests Table
class LabTest(Base):
    __tablename__ = 'lab_tests'
    encounter_id = Column(Integer, primary_key=True)
    num_lab_procedures = Column(Integer)
    max_glu_serum = Column(String)
    A1Cresult = Column(String)

if __name__ == "__main__":
    print("Connecting to the database...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("All 5 tables reset and verified!")

    # Extract
    print("Reading raw CSV file...")
    df = pd.read_csv('raw_data/diabetic_data.csv') 

    # Clean
    print("Cleaning missing values and dropping dead columns...")
    df.replace('?', np.nan, inplace=True)
    columns_to_drop = ['weight', 'payer_code', 'medical_specialty']
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    # Transform
    print("Transforming data into relational schemas...")
    patients_df = df[['patient_nbr', 'race', 'gender', 'age']].drop_duplicates(subset=['patient_nbr'])
    admissions_df = df[['encounter_id', 'patient_nbr', 'admission_type_id', 'discharge_disposition_id', 'admission_source_id', 'time_in_hospital']]
    diagnoses_df = df[['encounter_id', 'diag_1', 'diag_2', 'diag_3', 'number_diagnoses']]
    medications_df = df[['encounter_id', 'num_medications', 'diabetesMed', 'change', 'insulin']]
    lab_tests_df = df[['encounter_id', 'num_lab_procedures', 'max_glu_serum', 'A1Cresult']]

    # Load
    print("Loading data into PostgreSQL (This might take a minute)...")
    patients_df.to_sql('patients', engine, if_exists='append', index=False)
    admissions_df.to_sql('admissions', engine, if_exists='append', index=False)
    diagnoses_df.to_sql('diagnoses', engine, if_exists='append', index=False)
    medications_df.to_sql('medications', engine, if_exists='append', index=False)
    lab_tests_df.to_sql('lab_tests', engine, if_exists='append', index=False)

    print("ETL Pipeline completed successfully! Full database is populated.")