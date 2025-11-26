# nutrifit_api/database.py

import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ⚠️ CONFIG MYSQL — adapte si besoin
DB_USER = "root"            # ou ton user MySQL
DB_PASSWORD = ""            # si vide, mets ""
DB_HOST = "127.0.0.1"       # MySQL en local
DB_PORT = "3306"            # port MySQL standard
DB_NAME = "nutrifit"        # nom de ta base

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    with engine.connect() as connection:
        print("Connexion MySQL réussie !")

except Exception as e:
    print(" ERREUR : Impossible de se connecter à MySQL.")
    print(f"Détail : {e}")
    exit(1)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
