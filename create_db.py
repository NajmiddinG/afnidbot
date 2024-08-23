from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Contact(Base):
    __tablename__ = 'Kontaktlar'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    telefon_raqam = Column(String)
    username = Column(String)
    ism = Column(String)
    familiya = Column(String)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
