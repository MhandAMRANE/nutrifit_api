# nutrifit_api/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, Union, List, Dict

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
    description_exercice: Optional[str] = None
    type_exercice: Optional[str] = None
    nombre_series: Optional[int] = None
    calories_brulees: Optional[float] = None
    temps_recuperation: Optional[int] = None
    id_seance: Optional[int] = None
    
    # --- AJOUTS ---
    muscle_cible: Optional[Union[List[str], Dict]] = None
    materiel: Optional[str] = None
    difficulte: Optional[str] = None

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

class UserProfile(BaseModel):
    id_utilisateur: int
    nom: str
    prenom: str
    # Données physiques (Sans niveau_activite)
    poids: Optional[float] = None
    taille: Optional[int] = None
    age: Optional[int] = None
    sexe: Optional[str] = None
    objectif: Optional[str] = None
    # niveau_activite supprimé ici aussi

    model_config = ConfigDict(from_attributes=True)