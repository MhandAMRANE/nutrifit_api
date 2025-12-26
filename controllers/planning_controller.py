from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from models import PlanningRepas, PlanningSeance, Recette, Seance, Utilisateur
from utils.health_formulas import calculate_bmr, calculate_tdee, calculate_target_calories

def generate_weekly_plan(db: Session, user_id: int, start_date: datetime):
    """
    Génère un planning intelligent : sélectionne des recettes adaptées
    aux besoins caloriques calculés de l'utilisateur.
    """
    user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == user_id).first()
    
    bmr = calculate_bmr(user.poids_kg, user.taille_cm, user.age, user.sexe)
    tdee = calculate_tdee(bmr, user.nb_jours_entrainement or "sedentaire")
    daily_target = calculate_target_calories(tdee, user.objectif)
    
    target_per_meal = daily_target * 0.35
    
    all_recipes = db.query(Recette).all()
    all_workouts = db.query(Seance).all()

    compatible_recipes = [
        r for r in all_recipes 
        if r.calories is not None and (target_per_meal - 250) <= r.calories <= (target_per_meal + 250)
    ]
    
    if not compatible_recipes:
        compatible_recipes = all_recipes

    for i in range(7):
        current_day = start_date + timedelta(days=i)
        
        if len(compatible_recipes) >= 2:
            day_recipes = random.sample(compatible_recipes, 2)
            
            db.add(PlanningRepas(
                id_utilisateur=user_id, id_recette=day_recipes[0].id_recette,
                date=current_day, type_repas="dejeuner"
            ))
            db.add(PlanningRepas(
                id_utilisateur=user_id, id_recette=day_recipes[1].id_recette,
                date=current_day, type_repas="diner"
            ))

        if i % 2 == 0 and all_workouts: 
            workout = random.choice(all_workouts)
            db.add(PlanningSeance(
                id_utilisateur=user_id, id_seance=workout.id_seance,
                date=current_day
            ))
            
    db.commit()
    return {
        "message": "Planning intelligent généré.", 
        "cible_jour": daily_target, 
        "cible_repas": int(target_per_meal)
    }

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

def update_seance_planning(db: Session, planning_id: int, new_seance_id: int):
    """Change une séance prévue dans le planning."""
    entry = db.query(PlanningSeance).filter(PlanningSeance.id == planning_id).first()
    if entry:
        entry.id_seance = new_seance_id
        db.commit()
        return True
    return False