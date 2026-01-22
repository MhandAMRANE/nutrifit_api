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
    
    repas = db.query(PlanningRepas).filter(
        PlanningRepas.id_utilisateur == user_id,
        PlanningRepas.jour == jour
    ).all()
    
    seances = db.query(PlanningSeance).filter(
        PlanningSeance.id_utilisateur == user_id,
        PlanningSeance.jour == jour
    ).all()
    
    return {
        "jour": jour,
        "repas": repas,
        "seances": seances
    }


def add_meal_to_calendar(db: Session, user_id: int, planning_repas: PlanningRepasCreate):
    """Ajoute un repas au calendrier"""
    import sys
    print(f"[DEBUG] add_meal_to_calendar appelée", file=sys.stderr)
    print(f"[DEBUG] user_id={user_id}, planning_repas={planning_repas}", file=sys.stderr)
    
    
    db_planning = PlanningRepas(
        id_utilisateur=user_id,
        id_recette=planning_repas.id_recette,
        jour=planning_repas.jour,
        repas=planning_repas.repas,
        notes=planning_repas.notes
    )
    print(f"[DEBUG] Objet créé: {db_planning}", file=sys.stderr)
    
    db.add(db_planning)
    db.commit()
    db.refresh(db_planning)
    
    print(f"[DEBUG] Repas inséré: id={db_planning.id_planning_repas}", file=sys.stderr)
    return db_planning


def add_workout_to_calendar(db: Session, user_id: int, planning_seance: PlanningSeanceCreate):
    """Ajoute une séance d'entraînement au calendrier"""
    db_planning = PlanningSeance(
        id_utilisateur=user_id,
        id_seance=planning_seance.id_seance,
        jour=planning_seance.jour,
        notes=planning_seance.notes,
        est_realise=planning_seance.est_realise
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
