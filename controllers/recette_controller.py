from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import Recette

def get_all_recettes(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(Recette)
    
    if search:
        # Recherche insensible à la casse dans le NOM ou les TAGS
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Recette.nom_recette.ilike(search_fmt),
                Recette.tags.ilike(search_fmt)
            )
        )
    
    return query.offset(skip).limit(limit).all()

def get_recette_by_id(db: Session, recette_id: int):
    return db.query(Recette).filter(Recette.id_recette == recette_id).first()

def get_available_tags(db: Session):
    """
    Récupère tous les tags uniques.
    Format supporté : "Vegan, Gluten-Free, Low-Carb" (String simple séparée par virgules)
    """
    # On récupère toutes les lignes qui ont des tags
    all_tags_rows = db.query(Recette.tags).filter(Recette.tags != None).all()
    
    unique_tags = set()
    
    for row in all_tags_rows:
        if row.tags:
            # 1. On découpe la chaine par les virgules
            raw_tags = row.tags.split(',')
            
            # 2. On nettoie chaque tag (enlève les espaces autour) et on l'ajoute au set
            for t in raw_tags:
                clean_tag = t.strip()
                if clean_tag: # Si le tag n'est pas vide
                    unique_tags.add(clean_tag)
            
    # On retourne la liste triée alphabétiquement
    return sorted(list(unique_tags))