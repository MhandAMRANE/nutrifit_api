from sqlalchemy.orm import Session
from datetime import datetime, timedelta, time
import random

from models import Utilisateur, PlanningRepas, PlanningSeance, Recette, Seance
from utils.health_formulas import calculate_bmr, calculate_tdee, calculate_target_calories
# Import du générateur de séance corrigé
from controllers.exercice_controller import generate_seance_relational

# --- LOGIQUE DU SPLIT (Pattern d'entraînement) ---
def determine_split(freq_entrainement: int):
    """
    Définit le pattern d'entraînement (Split) selon le nombre de jours disponibles.
    """
    if freq_entrainement <= 2:
        # 1 ou 2 jours : Full Body pour solliciter tous les muscles à chaque fois
        return ["full_body"] * freq_entrainement
    elif freq_entrainement == 3:
        # 3 jours : Classique Full Body x3
        return ["full_body", "full_body", "full_body"]
    elif freq_entrainement == 4:
        # 4 jours : Upper (Haut) / Lower (Bas) x2
        return ["upper", "lower", "upper", "lower"]
    else:
        # 5 jours ou plus : Push / Pull / Legs / Upper / Lower
        return ["push", "pull", "lower", "upper", "lower"]

# =============================================================================
# GÉNÉRATION DU PLANNING HEBDOMADAIRE
# =============================================================================

def generate_weekly_plan(db: Session, user_id: int, start_date: datetime, include_meals: bool = True, include_sport: bool = True):
    print(f"🔧 DEBUG: Démarrage génération pour User {user_id}")
    
    # 1. Vérification Utilisateur
    user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == user_id).first()
    if not user: return {"erreur": "Utilisateur introuvable"}

    # 2. Calculs Caloriques (Pour les repas)
    target_meal_cal = 600
    try:
        if include_meals:
            poids = float(user.poids_kg) if user.poids_kg else 70.0
            taille = float(user.taille_cm) if user.taille_cm else 175.0
            bmr = calculate_bmr(poids, taille, user.age or 30, user.sexe or "masculin")
            tdee = calculate_tdee(bmr, "sedentaire")
            daily = calculate_target_calories(tdee, user.objectif or "maintien")
            target_meal_cal = daily * 0.35 # 35% pour un repas principal
    except: pass

    # Gestion des dates (Conversion en date simple pour SQL)
    start_date_only = start_date.date()
    end_date_only = start_date_only + timedelta(days=7)
    
    plan_summary = []

    # =========================================================================
    # A. GESTION DES REPAS (INTELLIGENTE 12h / 19h)
    # =========================================================================
    if include_meals:
        # Nettoyage préalable des repas sur la période
        db.query(PlanningRepas).filter(
            PlanningRepas.id_utilisateur == user_id, 
            PlanningRepas.jour >= start_date_only, 
            PlanningRepas.jour < end_date_only
        ).delete()
        db.flush() 

        # Récupération Recettes
        all_recipes = db.query(Recette).all()
        
        if all_recipes:
            # Filtrage par calories (+/- 300kcal)
            suitable = [r for r in all_recipes if r.calories and (target_meal_cal - 300 <= float(r.calories) <= target_meal_cal + 300)]
            if not suitable: suitable = all_recipes
            
            for i in range(7):
                current_day_date = start_date_only + timedelta(days=i)

                for type_repas in ["Dejeuner", "Diner"]:
                    recette = random.choice(suitable)
                    if recette.id_recette is None: continue
                    
                    # --- LOGIQUE HORAIRE ---
                    heure_cible = time(12, 0, 0) # Midi par défaut
                    
                    # On vérifie si midi est déjà pris ce jour-là
                    existe_midi = db.query(PlanningRepas).filter(
                        PlanningRepas.id_utilisateur == user_id,
                        PlanningRepas.jour == current_day_date, 
                        PlanningRepas.heure_debut == time(12, 0, 0)
                    ).first()

                    # Si midi est pris OU si c'est explicitement le Diner -> 19h
                    if existe_midi or type_repas == "Diner":
                        heure_cible = time(19, 0, 0)
                    
                    new_meal = PlanningRepas(
                        id_utilisateur=user_id,
                        id_recette=recette.id_recette,
                        jour=current_day_date, 
                        repas=type_repas, 
                        heure_debut=heure_cible,
                        notes=""
                    )
                    db.add(new_meal)
                    db.flush() # Important pour que la boucle suivante voie ce repas
            
            plan_summary.append("Repas générés avec horaires (12h/19h).")
        else:
            plan_summary.append("Aucune recette en base.")

    # =========================================================================
    # B. GESTION DU SPORT (LOGIQUE INTELLIGENTE SPLIT/PATTERN)
    # =========================================================================
    if include_sport:
        # 1. Nettoyage des séances sur la période
        db.query(PlanningSeance).filter(
            PlanningSeance.id_utilisateur == user_id, 
            PlanningSeance.jour >= start_date_only, 
            PlanningSeance.jour < end_date_only
        ).delete()
        
        # 2. Définition du Pattern selon la fréquence
        freq = getattr(user, 'nb_jours_entrainement', 3) or 3
        pattern = determine_split(freq) # ex: ['push', 'pull', 'lower']
        
        materiel_user = getattr(user, 'equipements', "poids_du_corps")
        
        # Calcul des jours d'entraînement (Répartition)
        jours_indices = []
        if freq == 1: jours_indices = [2] # Mercredi
        elif freq == 2: jours_indices = [1, 4] # Mardi, Vendredi
        elif freq == 3: jours_indices = [0, 2, 4] # Lundi, Mercredi, Vendredi
        elif freq == 4: jours_indices = [0, 1, 3, 4] # Lun, Mar, Jeu, Ven
        elif freq >= 5: jours_indices = [0, 1, 2, 3, 4] # Lun -> Ven
        
        pattern_index = 0

        for i in range(7):
            if i in jours_indices:
                current_day_date = start_date_only + timedelta(days=i)
                
                # Choix du focus du jour dans le pattern cyclique
                if pattern_index < len(pattern):
                    current_focus = pattern[pattern_index]
                    pattern_index += 1
                else:
                    current_focus = "full_body" # Sécurité

                nom_seance = f"Séance {current_focus.capitalize()}"
                
                # 3. CRÉATION DE LA SÉANCE (Appel 4 arguments : db, nom, focus, materiel)
                # Note: On ne passe PLUS user_id ici car la séance est générique
                nouvelle_seance = generate_seance_relational(
                    db, 
                    nom_seance, 
                    current_focus, 
                    str(materiel_user)
                )
                
                # 4. INSERTION DANS LE PLANNING (Le lien User <-> Séance se fait ici)
                new_planning = PlanningSeance(
                    id_utilisateur=user_id,
                    id_seance=nouvelle_seance.id_seance, # On récupère l'ID de la séance créée
                    jour=current_day_date,
                    est_realise=False,
                    notes=f"Objectif: {current_focus}"
                )
                db.add(new_planning)
                
        plan_summary.append(f"Sport planifié : {freq} séances ({', '.join(pattern)}).")
        db.flush()

    try:
        db.commit()
        return {"status": "succes", "message": "Planning généré.", "details": plan_summary}
    except Exception as e:
        db.rollback()
        return {"erreur": f"Erreur BDD Finale: {str(e)}"}

# =============================================================================
# 2. LECTURE & MODIFICATION
# =============================================================================

def get_user_planning(db: Session, user_id: int, start_date: datetime, end_date: datetime):
    # Conversion dates
    s_date = start_date.date()
    e_date = end_date.date()
    
    return db.query(PlanningRepas).filter(
        PlanningRepas.id_utilisateur == user_id,
        PlanningRepas.jour >= s_date,
        PlanningRepas.jour <= e_date
    ).order_by(PlanningRepas.jour, PlanningRepas.heure_debut).all()

def update_meal_planning(db: Session, id_planning: int, new_recette_id: int):
    entry = db.query(PlanningRepas).filter(PlanningRepas.id_planning_repas == id_planning).first()
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