from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from models import PlanningRepas, PlanningSeance, Recette, Seance, Utilisateur
from utils.health_formulas import calculate_bmr, calculate_tdee, calculate_target_calories

def generate_weekly_plan(db: Session, user_id: int, start_date: datetime):
    """
    Génère un planning complet pour 7 jours basé sur le profil.
    """
    user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == user_id).first()
    
    # 1. Calcul des besoins
    # (On reprend votre logique de health_formulas)
    bmr = calculate_bmr(user.poids, user.taille, user.age, user.sexe)
    tdee = calculate_tdee(bmr, user.niveau_activite or "sedentaire")
    target_cal = calculate_target_calories(tdee, user.objectif)
    
    # Cible par repas (simplifiée)
    lunch_target = target_cal * 0.35
    dinner_target = target_cal * 0.35
    
    # 2. Récupérer les recettes éligibles
    # Ici, on fait simple, mais on pourrait filtrer par tags
    all_recipes = db.query(Recette).all()
    all_workouts = db.query(Seance).all()
    
    # 3. Remplir la semaine
    for i in range(7):
        current_day = start_date + timedelta(days=i)
        
        # --- REPAS (Déjeuner & Dîner) ---
        # On choisit 2 recettes au hasard qui "fit" à peu près les calories
        # (Version simple : random)
        day_recipes = random.sample(all_recipes, 2) if len(all_recipes) >= 2 else all_recipes
        
        if day_recipes:
            # Déjeuner
            db.add(PlanningRepas(
                id_utilisateur=user_id, id_recette=day_recipes[0].id_recette,
                date=current_day, type_repas="dejeuner"
            ))
            # Dîner
            db.add(PlanningRepas(
                id_utilisateur=user_id, id_recette=day_recipes[1].id_recette,
                date=current_day, type_repas="diner"
            ))
            
        # --- SPORT (1 jour sur 2 par exemple) ---
        if i % 2 == 0 and all_workouts: 
            workout = random.choice(all_workouts)
            db.add(PlanningSeance(
                id_utilisateur=user_id, id_seance=workout.id_seance,
                date=current_day
            ))
            
    db.commit()
    return {"message": "Planning généré avec succès pour 7 jours."}

def get_user_planning(db: Session, user_id: int, start_date: datetime, end_date: datetime):
    """Récupère le planning pour l'affichage ou l'IA"""
    repas = db.query(PlanningRepas).filter(
        PlanningRepas.id_utilisateur == user_id,
        PlanningRepas.date >= start_date,
        PlanningRepas.date <= end_date
    ).all()
    return repas

def update_meal_planning(db: Session, planning_id: int, new_recipe_id: int):
    """Change une recette prévue"""
    entry = db.query(PlanningRepas).filter(PlanningRepas.id == planning_id).first()
    if entry:
        entry.id_recette = new_recipe_id
        db.commit()
        return True
    return False