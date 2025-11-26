# nutrifit_api/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import certifi
from urllib.parse import quote_plus  # <--- Indispensable pour la sécurité

# 1. Charger les variables
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# 2. Encoder le mot de passe (Sécurité)
# Si le mot de passe contient des caractères spéciaux, cela évite le crash
encoded_password = quote_plus(DB_PASSWORD)

# 3. Construire l'URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 4. Configuration SSL pour TiDB Cloud
ssl_args = {
    "ssl": {
        "ca": certifi.where()
    }
}

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=ssl_args,
        echo=False,
        pool_pre_ping=True
    )

    with engine.connect() as connection:
        print(f"✅ Connexion réussie à TiDB Cloud ({DB_HOST}) !")

except Exception as e:
    print("❌ ERREUR : Impossible de se connecter à TiDB.")
    print(f"Détail : {e}")
    exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()