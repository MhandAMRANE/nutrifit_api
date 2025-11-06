# nutrifit_api/database.py (Version finale avec PyMySQL)

import os
import pymysql  # Nécessaire pour que SQLAlchemy trouve le driver
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "4000")
DB_NAME = os.getenv("DB_NAME", "nutrifit")

# --- CHANGEMENT 1: Utiliser le driver pymysql ---
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- CHANGEMENT 2: Configuration SSL simplifiée ---
# PyMySQL gère très bien le SSL par défaut.
connect_args = {
    "ssl_disabled": False,
    "ssl_verify_cert": True
}

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args
    )
    
    with engine.connect() as connection:
        print(f"✅ (PyMySQL) Connexion à TiDB ({DB_HOST}) réussie !")

except ImportError:
    print("Erreur : Le driver 'PyMySQL' n'est pas installé.")
    print("Veuillez l'installer avec : pip install PyMySQL")
    exit(1)
except Exception as e:
    print(f"❌ (PyMySQL) ERREUR : Impossible de se connecter.")
    print(f"Détail : {e}")
    exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()