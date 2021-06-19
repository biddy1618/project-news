from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

import os

SQLALCHEMY_DATABASE_URL = os.getenv('DB_URI')

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

