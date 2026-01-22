from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import Favoris, Recette
from schemas import FavoriteCreate

def add_favorite(db: Session, user_id: int, recette_id: int):
    """Ajoute une recette aux favoris de l'utilisateur."""
    # Vérifier si déjà en favori
    existing = db.query(Favoris).filter(
        and_(
            Favoris.id_utilisateur == user_id,
            Favoris.id_recette == recette_id
        )
    ).first()
    
    if existing:
        return existing
        
    # Vérifier si la recette existe
    recette = db.query(Recette).filter(Recette.id_recette == recette_id).first()
    if not recette:
        return None

    new_fav = Favoris(id_utilisateur=user_id, id_recette=recette_id)
    db.add(new_fav)
    db.commit()
    db.refresh(new_fav)
    return new_fav

def remove_favorite(db: Session, user_id: int, recette_id: int):
    """Supprime une recette des favoris."""
    fav = db.query(Favoris).filter(
        and_(
            Favoris.id_utilisateur == user_id,
            Favoris.id_recette == recette_id
        )
    ).first()
    
    if fav:
        db.delete(fav)
        db.commit()
        return True
    return False

def get_user_favorites(db: Session, user_id: int):
    """Récupère la liste des recettes favorites d'un utilisateur."""
    # On fait une jointure pour récupérer directement les objets Recette
    return db.query(Recette).join(Favoris).filter(Favoris.id_utilisateur == user_id).all()
