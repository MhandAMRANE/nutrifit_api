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
if not DB_PORT:
    print("⚠️ DB_PORT non défini, utilisation du port 3306 par défaut.")
    DB_PORT = "3306"
DB_NAME = os.getenv("DB_NAME")
DB_USE_SSL = os.getenv("DB_USE_SSL", "false").lower() == "true"

if DB_PASSWORD is None:
    DB_PASSWORD = ""
    
encoded_password = quote_plus(DB_PASSWORD)

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Création de l'engine (ne connecte pas encore)
try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
except Exception as e:
    print(f"❌ ERREUR CRITIQUE : Impossible de configurer l'engine SQLAlchemy. URL: {DATABASE_URL}")
    print(f"Détail : {e}")
    # Ici on peut exit car sans engine rien ne marche
    exit(1)

# Test de connexion (non bloquant pour éviter le crash immédiat du serveur)
try:
    with engine.connect() as connection:
        print(f"✅ Connexion réussie à la base de données ({DB_HOST}) !")
except Exception as e:
    print(DB_HOST)
    print("⚠️ AVERTISSEMENT : Impossible de se connecter à la base de données au démarrage.")
    print(f"Détail : {e}")
    # On n'exit PAS, pour laisser le serveur démarrer et remonter les erreurs HTTP 500


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()