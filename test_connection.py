import os
from dotenv import load_dotenv
load_dotenv()

print("Test de connexion...")
try:
    from database import engine, SessionLocal
    
    with engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text("SELECT 1"))
        print("Connexion OK!")
        
    # Test d'insertion
    db = SessionLocal()
    from models import PlanningRepas
    from datetime import date
    
    print("Tables dans la base:")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    
    db.close()
    
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
