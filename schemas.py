# nutrifit_api/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

# --- Schémas pour les Recettes ---

class RecetteBase(BaseModel):
    # Le modèle de base pour une recette
    nom_recette: str
    description: Optional[str] = None
    ingredients: str
    nombre_calories: Optional[int] = 0

class RecetteCreate(RecetteBase):
    # Pour la création (hérite de RecetteBase)
    pass

class Recette(RecetteBase):
    # Pour la lecture (ce qu'on renvoie au client)
    id_recette: int
    
    # Permet à Pydantic de lire depuis un objet SQLAlchemy
    model_config = ConfigDict(from_attributes=True)