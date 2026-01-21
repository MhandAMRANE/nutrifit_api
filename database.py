# nutrifit_api/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import certifi
from urllib.parse import quote_plus  


load_dotenv()


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USE_SSL = os.getenv("DB_USE_SSL", "false").lower() == "true"

encoded_password = quote_plus(DB_PASSWORD)

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    with engine.connect() as connection:
        print(f"✅ Connexion réussie à la base de données ({DB_HOST}) !")

except Exception as e:
    print(DB_HOST)
    print("❌ ERREUR : Impossible de se connecter à la base de données.")
    print(f"Détail : {e}")
    exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()