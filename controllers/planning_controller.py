from sqlalchemy.orm import Session
from datetime import datetime, timedelta, time
import random

from models import Utilisateur, PlanningRepas, PlanningSeance, Recette, Exercice, Seance
from utils.health_formulas import calculate_bmr, calculate_tdee, calculate_target_calories
from controllers.exercice_controller import generate_seance_relational

# =============================================================================
# 1. GÉNÉRATION (Version Complète : Heures + Séances Relationnelles)
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

    # =========================================================================
    # A. GESTION DES REPAS (INTELLIGENTE 12h / 19h)
    # =========================================================================
    if include_meals:
        # Nettoyage préalable
        db.query(PlanningRepas).filter(PlanningRepas.id_utilisateur == user_id, PlanningRepas.date >= start_date, PlanningRepas.date < end_date).delete()
        db.flush() 

        # Récupération Recettes
        all_recipes = db.query(Recette).all()
        print(f"🔧 DEBUG: {len(all_recipes)} recettes trouvées en base.")
        
        if all_recipes:
            suitable = [r for r in all_recipes if r.calories and (target_meal_cal - 300 <= float(r.calories) <= target_meal_cal + 300)]
            if not suitable: suitable = all_recipes
            
            for i in range(7):
                current_day = start_date + timedelta(days=i)
                # On normalise la date (sans l'heure) pour les comparaisons
                date_jour = current_day.date()

                for type_repas in ["Dejeuner", "Diner"]:
                    recette = random.choice(suitable)
                    
                    if recette.id_recette is None:
                        continue
                    
                    # --- LOGIQUE HORAIRE ---
                    heure_cible = time(12, 0, 0) # Midi par défaut
                    
                    # On cherche s'il y a déjà un repas à midi ce jour-là (même celui qu'on vient d'ajouter)
                    # Note: on combine date_jour + heure fixe pour comparer
                    existe_midi = db.query(PlanningRepas).filter(
                        PlanningRepas.id_utilisateur == user_id,
                        PlanningRepas.date >= datetime.combine(date_jour, time(0,0)), 
                        PlanningRepas.date <= datetime.combine(date_jour, time(23,59)),
                        PlanningRepas.heure_debut == time(12, 0, 0)
                    ).first()

                    # Si midi est pris OU si c'est le Diner -> 19h
                    if existe_midi or type_repas == "Diner":
                        heure_cible = time(19, 0, 0)
                    
                    new_meal = PlanningRepas(
                        id_utilisateur=user_id,
                        id_recette=recette.id_recette,
                        date=current_day, # La date précise
                        type_repas=type_repas,
                        heure_debut=heure_cible, # <--- La nouvelle colonne
                        est_mange=False
                    )
                    db.add(new_meal)
                    
                    # CRITIQUE : on flush pour que la boucle suivante "voie" ce repas
                    db.flush() 
            
            plan_summary.append("Repas générés avec horaires (12h/19h).")

        else:
            plan_summary.append("Aucune recette en base.")

    # =========================================================================
    # B. GESTION DU SPORT (RELATIONNELLE)
    # =========================================================================
    if include_sport:
        db.query(PlanningSeance).filter(PlanningSeance.id_utilisateur == user_id, PlanningSeance.date >= start_date, PlanningSeance.date < end_date).delete()
        
        # Paramètres utilisateur
        freq = getattr(user, 'nb_jours_entrainement', 3) or 3
        materiel_user = getattr(user, 'equipements', "poids_du_corps")
        
        # Algorithme de jours (Ex: Lundi/Mercredi/Vendredi pour freq=3)
        jours_sport_indices = []
        if freq == 1: jours_sport_indices = [2]
        elif freq == 2: jours_sport_indices = [1, 4]
        elif freq == 3: jours_sport_indices = [0, 2, 4]
        else: jours_sport_indices = [0, 1, 3, 4]
        
        focus_list = ["full_body", "legs", "upper", "cardio"]

        for i in range(7):
            if i in jours_sport_indices:
                current_day = start_date + timedelta(days=i)
                
                # On tourne les focus (Jambes, Haut, Cardio...)
                current_focus = focus_list[i % len(focus_list)]
                nom_seance = f"Séance {current_focus.capitalize()}"
                
                # 1. GÉNÉRATION DE LA SÉANCE COMPLETE (Table Seance + SeanceExercice)
                # Cette fonction crée les objets en BDD et retourne la séance créée
                nouvelle_seance = generate_seance_relational(
                    db, user_id, nom_seance, current_focus, str(materiel_user)
                )
                
                # 2. LIEN AVEC LE PLANNING
                new_planning = PlanningSeance(
                    id_utilisateur=user_id,
                    id_seance=nouvelle_seance.id_seance, # On lie l'ID de la séance créée
                    date=current_day,
                    est_realise=False
                )
                db.add(new_planning)
                
        plan_summary.append(f"Sport planifié : {freq} séances créées.")

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
    # Attention: vérifie le nom de ta PK, parfois c'est id_planning_seance
    entry = db.query(PlanningSeance).filter(PlanningSeance.id_planning_seance == id_planning).first()
    if entry:
        entry.id_seance = new_seance_id
        db.commit()
        return True
    return False