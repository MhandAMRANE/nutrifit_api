# nutrifit_api/schemas.py
from pydantic import BaseModel, ConfigDict, field_validator
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
    id_recette: int
    image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('image', mode='before')
    def set_default_image(cls, v):
        # Si la valeur est None ou vide, on renvoie l'URL par défaut
        if not v:
            return "/static/images/default.jpg"
        return v


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

# Schéma pour la MISE À JOUR du profil (PUT)
class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    age: Optional[int] = None
    poids: Optional[float] = None
    taille: Optional[float] = None
    sexe: Optional[str] = None
    objectif: Optional[str] = None

# Schéma pour l'AFFICHAGE du profil (GET)
class UserResponse(BaseModel):
    id_utilisateur: int
    nom: str
    prenom: str
    email: str
    type_utilisateur: str
    
    # Ces champs sont optionnels car ils peuvent être vides au début
    age: Optional[int] = None
    poids: Optional[float] = None
    taille: Optional[float] = None
    sexe: Optional[str] = None
    objectif: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)