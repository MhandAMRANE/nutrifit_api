# nutrifit_api/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List

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


class ExerciceBase(BaseModel):
    # Ce dont on a besoin pour créer un exercice
    nom_exercice: str
    description_exercice: Optional[str] = None
    type_exercice: Optional[str] = None
    nombre_series: Optional[int] = None
    calories_brulees: Optional[float] = None
    temps_recuperation: Optional[int] = None

class ExerciceCreate(ExerciceBase):
    pass

class Exercice(ExerciceBase):
    # Ce qu'on renvoie au client
    id_exercice: int
    id_seance: int
    model_config = ConfigDict(from_attributes=True)


class SeanceBase(BaseModel):
    nom: str
    duree: Optional[int] = None

class SeanceCreate(SeanceBase):
    # Quand on crée une séance, on passe aussi la liste des exercices
    exercices: List[ExerciceCreate]

class Seance(SeanceBase):
    # Quand on lit une séance, on renvoie la liste des exercices
    id_seance: int
    exercices: List[Exercice] = [] # La liste sera remplie par SQLAlchemy
    model_config = ConfigDict(from_attributes=True)