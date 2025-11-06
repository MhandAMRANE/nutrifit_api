from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#  Adapter ton mot de passe MySQL si besoin
DATABASE_URL = "mysql+mysqlconnector://root:@localhost/nutrifit"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
