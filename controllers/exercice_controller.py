from sqlalchemy.orm import Session
from models import Exercice
from schemas import ExerciceCreate

def get_all_exercices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Exercice).offset(skip).limit(limit).all()

def get_exercice_by_id(db: Session, exercice_id: int):
    return db.query(Exercice).filter(Exercice.id_exercice == exercice_id).first()

def create_exercice(db: Session, exercice: ExerciceCreate):
    db_exercice = Exercice(**exercice.model_dump())
    db.add(db_exercice)
    db.commit()
    db.refresh(db_exercice)
    return db_exercice

def delete_exercice(db: Session, exercice_id: int):
    db_exercice = get_exercice_by_id(db, exercice_id)
    if db_exercice:
        db.delete(db_exercice)
        db.commit()
        return True
    return False

def update_exercice(db: Session, exercice_id: int, exercice_data: ExerciceCreate):
    db_exercice = get_exercice_by_id(db, exercice_id)
    if db_exercice:

        db_exercice.nom_exercice = exercice_data.nom_exercice
        db_exercice.description_exercice = exercice_data.description_exercice
        db_exercice.type_exercice = exercice_data.type_exercice
        db_exercice.image_path = exercice_data.image_path
        db_exercice.muscle_cible = exercice_data.muscle_cible
        db_exercice.materiel = exercice_data.materiel

        db.commit()
        db.refresh(db_exercice)
        return db_exercice

    return None
