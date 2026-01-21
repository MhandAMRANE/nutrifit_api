from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional, List, Union
import json

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

    # Pydantic v2 : permet de lire depuis un objet SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

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

class Ingredient(BaseModel):
    food: Optional[str] = None
    text: Optional[str] = None
    weight: Optional[float] = None
    measure: Optional[str] = None
    quantity: Optional[float] = None

class RecetteBase(BaseModel):
    nom_recette: str
    description: Optional[str] = None
    categorie: Optional[str] = None
    
    calories: Optional[int] = 0
    proteines: Optional[float] = None
    glucides: Optional[float] = None
    lipides: Optional[float] = None
    
    ingredients: List[Ingredient]
    tags: Optional[str] = None
    image_url: Optional[str] = None
    cautions: Optional[str] = None

    @field_validator('ingredients', mode='before')
    @classmethod
    def parse_ingredients(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

class RecetteCreate(RecetteBase):
    pass

class Recette(RecetteBase):
    id_recette: int

    model_config = ConfigDict(from_attributes=True)


# --- Schémas Exercices ---

class ExerciceBase(BaseModel):
    nom_exercice: str
    description_exercice: str | None = None
    type_exercice: str | None = None
    image_path: str | None = None
    muscle_cible: str | None = None
    materiel: str | None = None

class ExerciceCreate(ExerciceBase):
    pass

class Exercice(ExerciceBase):
    id_exercice: int

    model_config = ConfigDict(from_attributes=True)
