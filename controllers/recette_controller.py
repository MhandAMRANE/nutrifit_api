from sqlalchemy.orm import Session
from models import Recette
from schemas import RecetteCreate
from sqlalchemy import or_
import json

def get_all_recettes(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    """
    Récupère les recettes, avec une option de recherche textuelle.
    """
    query = db.query(Recette)
    
    # Si un terme de recherche est fourni, on filtre
    if search:
        # On cherche dans le nom OU la description OU les ingrédients
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Recette.nom_recette.ilike(search_term),
                Recette.description.ilike(search_term),
                Recette.ingredients.ilike(search_term),
                Recette.tags.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()

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

def get_available_tags(db: Session):
    """Récupère la liste unique des tags présents dans la base."""
    # On récupère tous les champs 'tags' non nuls
    results = db.query(Recette.tags).filter(Recette.tags != None).all()
    
    unique_tags = set()
    for row in results:
        tags_str = row[0] # row est un tuple (ex: "Vegan, Facile",)
        if tags_str:
            # On découpe par virgule et on nettoie les espaces
            for t in tags_str.split(','):
                clean = t.strip()
                if clean:
                    unique_tags.add(clean)
    
    return list(unique_tags)