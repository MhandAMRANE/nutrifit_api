import os
from dotenv import load_dotenv
from datetime import date
load_dotenv()

print("Test d'insertion...")
try:
    from database import SessionLocal
    from models import PlanningRepas
    
    db = SessionLocal()
    
    # Insérer un repas
    meal = PlanningRepas(
        id_utilisateur=1,
        id_recette=1,
        jour=date(2026, 1, 22),
        repas="petit-dej",
        notes="test"
    )
    
    db.add(meal)
    db.commit()
    db.refresh(meal)
    
    print(f"Repas créé: ID={meal.id_planning_repas}")
    print(f"Jour: {meal.jour}")
    print(f"Repas: {meal.repas}")
    
    db.close()
    
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
