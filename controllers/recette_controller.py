from sqlalchemy.orm import Session
from models import Recette
from schemas import RecetteCreate
from typing import Optional

def get_all_recettes(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(Recette)
    if search:
        query = query.filter(
            (Recette.nom_recette.ilike(f"%{search}%")) | 
            (Recette.ingredients.ilike(f"%{search}%"))
        )
    return query.offset(skip).limit(limit).all()

def get_recette_by_id(db: Session, recette_id: int):
    return db.query(Recette).filter(Recette.id_recette == recette_id).first()

def create_recette(db: Session, recette: RecetteCreate):
    db_recette = Recette(**recette.model_dump())
    db.add(db_recette)
    db.commit()
    db.refresh(db_recette)
    return db_recette

def delete_recette(db: Session, recette_id: int):
    db_recette = get_recette_by_id(db, recette_id)
    if db_recette:
        db.delete(db_recette)
        db.commit()
        return True
    return False

def update_recette(db: Session, recette_id: int, recette_data: RecetteCreate):
    db_recette = get_recette_by_id(db, recette_id)
    if db_recette:
        db_recette.nom_recette = recette_data.nom_recette
        db_recette.description = recette_data.description
        db_recette.ingredients = recette_data.ingredients
        db_recette.nombre_calories = recette_data.nombre_calories
        
        db.commit()
        db.refresh(db_recette)
        return db_recette
    return None