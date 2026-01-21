from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from models import Utilisateur, PlanningRepas, PlanningSeance, Recette, Exercice, Seance
from utils.health_formulas import calculate_bmr, calculate_tdee, calculate_target_calories

# =============================================================================
# 1. GÉNÉRATION (Version Blindée & Debug)
# =============================================================================

def generate_weekly_plan(db: Session, user_id: int, start_date: datetime, include_meals: bool = True, include_sport: bool = True):
    print(f"🔧 DEBUG: Démarrage génération pour User {user_id}")
    
    # 1. Vérif Utilisateur
    user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == user_id).first()
    if not user: return {"erreur": "Utilisateur introuvable"}

    # 2. Calculs Caloriques
    target_meal_cal = 600
    try:
        if include_meals:
            poids = float(user.poids_kg) if user.poids_kg else 70.0
            taille = float(user.taille_cm) if user.taille_cm else 175.0
            bmr = calculate_bmr(poids, taille, user.age or 30, user.sexe or "masculin")
            tdee = calculate_tdee(bmr, "sedentaire")
            daily = calculate_target_calories(tdee, user.objectif or "maintien")
            target_meal_cal = daily * 0.35
    except: pass

    end_date = start_date + timedelta(days=7)
    plan_summary = []

    # A. GESTION DES REPAS
    if include_meals:
        # Nettoyage préalable
        db.query(PlanningRepas).filter(PlanningRepas.id_utilisateur == user_id, PlanningRepas.date >= start_date, PlanningRepas.date < end_date).delete()
        db.flush() # On valide la suppression

        # Récupération Recettes
        all_recipes = db.query(Recette).all()
        print(f"🔧 DEBUG: {len(all_recipes)} recettes trouvées en base.")
        
        if all_recipes:
            # Petit check visuel des IDs
            print(f"🔧 DEBUG: Exemple ID recette: {all_recipes[0].id_recette}")

            suitable = [r for r in all_recipes if r.calories and (target_meal_cal - 300 <= float(r.calories) <= target_meal_cal + 300)]
            if not suitable: suitable = all_recipes
            
            for i in range(7):
                current_day = start_date + timedelta(days=i)
                for type_repas in ["Dejeuner", "Diner"]:
                    recette = random.choice(suitable)
                    
                    # Vérification CRITIQUE avant insertion
                    if recette.id_recette is None:
                        print(f"❌ ERREUR: La recette '{recette.nom_recette}' a un ID NULL !")
                        continue
                    
                    new_meal = PlanningRepas(
                        id_utilisateur=user_id,
                        id_recette=recette.id_recette, # C'est ici que ça plantait
                        date=current_day,
                        type_repas=type_repas
                    )
                    db.add(new_meal)
            
            try:
                db.flush() # Test d'écriture immédiat pour voir si ça casse ici
                plan_summary.append("Repas générés.")
            except Exception as e:
                print(f"❌ ERREUR INSERTION REPAS: {e}")
                db.rollback()
                return {"erreur": f"Erreur technique insertion repas: {e}"}

        else:
            plan_summary.append("Aucune recette en base (tableau vide).")

    # B. GESTION DU SPORT
    if include_sport:
        db.query(PlanningSeance).filter(PlanningSeance.id_utilisateur == user_id, PlanningSeance.date >= start_date, PlanningSeance.date < end_date).delete()
        
        seance_type = db.query(Seance).first()
        if seance_type:
            freq = getattr(user, 'nb_jours_entrainement', 3) or 3
            jours_sport = []
            if freq == 1: jours_sport = [2]
            elif freq == 2: jours_sport = [1, 4]
            elif freq == 3: jours_sport = [0, 2, 4]
            elif freq >= 4: jours_sport = [0, 1, 3, 4]
            
            for i in range(7):
                if i in jours_sport:
                    current_day = start_date + timedelta(days=i)
                    new_session = PlanningSeance(
                        id_utilisateur=user_id,
                        id_seance=seance_type.id_seance,
                        date=current_day,
                        est_realise=False
                    )
                    db.add(new_session)
            plan_summary.append(f"Sport planifié ({freq} séances).")

    try:
        db.commit()
        return {"status": "succes", "message": "Planning mis à jour.", "details": plan_summary}
    except Exception as e:
        db.rollback()
        return {"erreur": f"Erreur BDD Finale: {str(e)}"}

# =============================================================================
# 2. LECTURE & MODIFICATION
# =============================================================================

def get_user_planning(db: Session, user_id: int, start_date: datetime, end_date: datetime):
    return db.query(PlanningRepas).filter(
        PlanningRepas.id_utilisateur == user_id,
        PlanningRepas.date >= start_date,
        PlanningRepas.date <= end_date
    ).order_by(PlanningRepas.date).all()

def update_meal_planning(db: Session, id_planning: int, new_recette_id: int):
    entry = db.query(PlanningRepas).filter(PlanningRepas.id_planning == id_planning).first()
    if entry:
        entry.id_recette = new_recette_id
        db.commit()
        return True
    return False

def update_seance_planning(db: Session, id_planning: int, new_seance_id: int):
    entry = db.query(PlanningSeance).filter(PlanningSeance.id_planning_seance == id_planning).first()
    if entry:
        entry.id_seance = new_seance_id
        db.commit()
        return True
    return False