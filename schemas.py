# nutrifit_api/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

# --- Schémas pour les Utilisateurs ---

class UserBase(BaseModel):
    nom: str
    prenom: Optional[str] = None
    email: EmailStr

    sexe: Optional[str] = None
    age: Optional[int] = None
    poids_kg: Optional[float] = None
    taille_cm: Optional[int] = None
    regime_alimentaire: Optional[str] = None
    objectif: Optional[str] = None
    equipements: Optional[str] = None
    nb_jours_entrainement: Optional[int] = None
    path_pp: Optional[str] = None

    class Config:
        orm_mode = True

class UserResponse(UserBase):
    id_utilisateur: int
    type_utilisateur: str

class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None

    sexe: Optional[str] = None
    age: Optional[int] = None
    poids_kg: Optional[float] = None
    taille_cm: Optional[int] = None
    regime_alimentaire: Optional[str] = None
    objectif: Optional[str] = None
    equipements: Optional[str] = None
    nb_jours_entrainement: Optional[int] = None
    path_pp: Optional[str] = None


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


# --- Schémas Exercices ---
class ExerciceBase(BaseModel):
    nom_exercice: str
    description_exercice: str | None = None
    type_exercice: str | None = None
    nombre_series: int | None = None
    calories_brulees: float | None = None
    temps_recuperation: int | None = None
    id_seance: int | None = None

class ExerciceCreate(ExerciceBase):
    pass

class Exercice(ExerciceBase):
    id_exercice: int

    model_config = ConfigDict(from_attributes=True)
