# nutrifit_api/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import certifi

# 1. Charger les variables d'environnement depuis le fichier .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# 2. Construire l'URL de connexion
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 3. Configuration SSL pour TiDB Cloud
# TiDB exige une connexion sécurisée. Sur Linux (ton environnement), 
# les certificats sont généralement ici.
ssl_args = {
    "ssl": {
        "ca": certifi.where()
    }
}

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=ssl_args,  # On passe les arguments SSL ici
        echo=False,
        pool_pre_ping=True
    )

    with engine.connect() as connection:
        print(f"✅ Connexion réussie à TiDB Cloud ({DB_HOST}) !")

except Exception as e:
    print("❌ ERREUR : Impossible de se connecter à TiDB.")
    print(f"Détail : {e}")
    # Si le chemin SSL échoue, essaie de commenter la ligne 'connect_args' pour tester
    exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()