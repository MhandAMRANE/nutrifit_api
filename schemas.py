from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Union, Dict

# --- Utilisateur ---
class UserBase(BaseModel):
    nom: str
    prenom: Optional[str] = None
    email: str

class UserResponse(UserBase):
    id_utilisateur: int
    type_utilisateur: str
    model_config = ConfigDict(from_attributes=True)

# --- Recette ---
class RecetteBase(BaseModel):
    nom_recette: str
    description: Optional[str] = None
    categorie: Optional[str] = None
    calories: Optional[int] = 0
    proteines: Optional[float] = None
    glucides: Optional[float] = None
    lipides: Optional[float] = None

class RecetteCreate(RecetteBase):
    pass

class Recette(RecetteBase):
    id_recette: int
    model_config = ConfigDict(from_attributes=True)

# --- Exercice ---
class ExerciceBase(BaseModel):
    nom_exercice: str
    description_exercice: Optional[str] = None
    type_exercice: Optional[str] = None
    image_path: Optional[str] = None
    muscle_cible: Optional[Union[List[str], Dict, str]] = None # Flexible pour le JSON
    materiel: Optional[str] = 'poids_du_corps'

class ExerciceCreate(ExerciceBase):
    pass

class Exercice(ExerciceBase):
    id_exercice: int
    model_config = ConfigDict(from_attributes=True)