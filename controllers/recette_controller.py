from sqlalchemy.orm import Session
from models import Recette
from schemas import RecetteCreate

import json

def get_all_recettes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Recette).offset(skip).limit(limit).all()

def get_recette_by_id(db: Session, recette_id: int):
    return db.query(Recette).filter(Recette.id_recette == recette_id).first()

def create_recette(db: Session, recette: RecetteCreate):
    recette_data = recette.model_dump()
    # Serialize ingredients to JSON string
    if 'ingredients' in recette_data:
        recette_data['ingredients'] = json.dumps(recette_data['ingredients'])
        
    db_recette = Recette(**recette_data)
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
        # Met à jour les champs
        db_recette.nom_recette = recette_data.nom_recette
        db_recette.description = recette_data.description
        db_recette.categorie = recette_data.categorie
        db_recette.calories = recette_data.calories
        db_recette.proteines = recette_data.proteines
        db_recette.glucides = recette_data.glucides
        db_recette.lipides = recette_data.lipides
        
        # Serialize ingredients
        db_recette.ingredients = json.dumps([i.model_dump() for i in recette_data.ingredients])
        
        db_recette.tags = recette_data.tags
        db_recette.image_url = recette_data.image_url
        db_recette.cautions = recette_data.cautions
        
        db.commit()
        db.refresh(db_recette)
        return db_recette
    return None