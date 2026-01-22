from sqlalchemy.orm import Session
from datetime import datetime, date
from models import PlanningRepas, PlanningSeance
from schemas import PlanningRepasCreate, PlanningSeanceCreate

def get_user_calendar(db: Session, user_id: int):
    """Récupère le calendrier complet d'un utilisateur"""
    planning_repas = db.query(PlanningRepas).filter(
        PlanningRepas.id_utilisateur == user_id
    ).all()
    
    planning_seances = db.query(PlanningSeance).filter(
        PlanningSeance.id_utilisateur == user_id
    ).all()
    
    return {
        "repas": planning_repas,
        "seances": planning_seances
    }


def get_calendar_by_day(db: Session, user_id: int, jour: str):
    """Récupère toutes les planifications pour un jour spécifique"""
    try:
        # Convertir la chaîne en date
        jour_date = datetime.strptime(jour, "%Y-%m-%d").date()
    except ValueError:
        return {
            "jour": jour,
            "repas": [],
            "seances": []
        }
    
    repas = db.query(PlanningRepas).filter(
        PlanningRepas.id_utilisateur == user_id,
        PlanningRepas.jour == jour_date
    ).all()
    
    seances = db.query(PlanningSeance).filter(
        PlanningSeance.id_utilisateur == user_id,
        PlanningSeance.jour == jour_date
    ).all()
    
    return {
        "jour": jour_date,
        "repas": repas,
        "seances": seances
    }


def add_meal_to_calendar(db: Session, user_id: int, planning_repas: PlanningRepasCreate):
    """Ajoute un repas au calendrier"""
    import sys
    print(f"[DEBUG] add_meal_to_calendar appelée", file=sys.stderr)
    print(f"[DEBUG] user_id={user_id}, planning_repas={planning_repas}", file=sys.stderr)
    
    try:
        jour_date = datetime.strptime(planning_repas.jour, "%Y-%m-%d").date()
        print(f"[DEBUG] jour convertie: {jour_date}", file=sys.stderr)
    except (ValueError, AttributeError) as e:
        print(f"[DEBUG] Erreur conversion jour: {e}", file=sys.stderr)
        jour_date = planning_repas.jour
    
    try:
        db_planning = PlanningRepas(
            id_utilisateur=user_id,
            id_recette=planning_repas.id_recette,
            jour=jour_date,
            repas=planning_repas.repas,
            notes=planning_repas.notes
        )
        print(f"[DEBUG] Objet créé: {db_planning}", file=sys.stderr)
        
        db.add(db_planning)
        db.commit()
        db.refresh(db_planning)
        
        print(f"[DEBUG] Repas inséré: id={db_planning.id_planning_repas}", file=sys.stderr)
        return db_planning
    except Exception as e:
        print(f"[DEBUG] Erreur lors de l'insertion: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


def add_workout_to_calendar(db: Session, user_id: int, planning_seance: PlanningSeanceCreate):
    """Ajoute une séance d'entraînement au calendrier"""
    try:
        jour_date = datetime.strptime(planning_seance.jour, "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        jour_date = planning_seance.jour
    
    db_planning = PlanningSeance(
        id_utilisateur=user_id,
        id_exercice=planning_seance.id_exercice,
        jour=jour_date,
        ordre=planning_seance.ordre,
        series=planning_seance.series,
        repetitions=planning_seance.repetitions,
        poids_kg=planning_seance.poids_kg,
        repos_secondes=planning_seance.repos_secondes,
        notes=planning_seance.notes
    )
    db.add(db_planning)
    db.commit()
    db.refresh(db_planning)
    return db_planning


def remove_meal_from_calendar(db: Session, planning_id: int):
    """Supprime un repas du calendrier"""
    db_planning = db.query(PlanningRepas).filter(
        PlanningRepas.id_planning_repas == planning_id
    ).first()
    if db_planning:
        db.delete(db_planning)
        db.commit()
        return True
    return False


def remove_workout_from_calendar(db: Session, planning_id: int):
    """Supprime une séance du calendrier"""
    db_planning = db.query(PlanningSeance).filter(
        PlanningSeance.id_planning_seance == planning_id
    ).first()
    if db_planning:
        db.delete(db_planning)
        db.commit()
        return True
    return False
