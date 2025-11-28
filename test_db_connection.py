import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import certifi
from urllib.parse import quote_plus

# Charger les variables
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

print("--- Debug Info ---")
print(f"DB_USER: {DB_USER}")
print(f"DB_HOST: {DB_HOST}")
print(f"DB_PORT: {DB_PORT}")
print(f"DB_NAME: {DB_NAME}")
if DB_PASSWORD:
    print(f"DB_PASSWORD: {DB_PASSWORD[:2]}****{DB_PASSWORD[-2:]} (Length: {len(DB_PASSWORD)})")
else:
    print("DB_PASSWORD: Not set!")
print("------------------")

if not DB_USER or not DB_PASSWORD or not DB_HOST:
    print("❌ Missing required environment variables.")
    exit(1)

encoded_password = quote_plus(DB_PASSWORD)
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

ssl_args = {
    "ssl": {
        "ca": certifi.where()
    }
}

try:
    print(f"Attempting to connect to {DB_HOST}...")
    engine = create_engine(
        DATABASE_URL,
        connect_args=ssl_args,
        echo=False,
        pool_pre_ping=True
    )

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(f"✅ Connexion réussie ! Result: {result.scalar()}")

except Exception as e:
    print("❌ ERREUR de connexion.")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {e}")
