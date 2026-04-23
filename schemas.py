from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional, List, Union
from datetime import date
import json
from datetime import datetime, time

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
    privacy_settings: Optional[dict] = None

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
    privacy_settings: Optional[dict] = None

    @field_validator('age')
    @classmethod
    def validate_age(cls, v):
        if v is not None and v <= 0:
            raise ValueError("L'âge doit être positif")
        return v

    @field_validator('poids_kg')
    @classmethod
    def validate_poids(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Le poids doit être positif")
        return v


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


# --- Schémas pour le Calendrier ---

class PlanningRepasBase(BaseModel):
    id_recette: int
    jour: str  # Format: 2026-01-22
    repas: str  # petit-dej, dejeuner, diner, collation
    notes: Optional[str] = None
    heure_debut: Optional[time] = None

class PlanningRepasCreate(PlanningRepasBase):
    pass

class PlanningRepas(PlanningRepasBase):
    id_planning_repas: int
    id_utilisateur: int
    date_creation: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PlanningSeanceBase(BaseModel):
    id_seance: int
    jour: str  # Format: 2026-01-22
    notes: Optional[str] = None
    est_realise: Optional[bool] = False

class PlanningSeanceCreate(PlanningSeanceBase):
    pass

class PlanningSeance(PlanningSeanceBase):
    id_planning_seance: int
    id_utilisateur: int
    date_creation: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CalendarDay(BaseModel):
    jour: str
    repas: List[PlanningRepas] = []
    seances: List[PlanningSeance] = []

    model_config = ConfigDict(from_attributes=True)


class Calendar(BaseModel):
    id_utilisateur: int
    repas: List[PlanningRepas] = []
    seances: List[PlanningSeance] = []

    model_config = ConfigDict(from_attributes=True)


# --- Schémas pour les Favoris ---

class FavoriteBase(BaseModel):
    id_recette: int

class FavoriteCreate(FavoriteBase):
    pass

class FavoriteResponse(FavoriteBase):
    id_utilisateur: int

    model_config = ConfigDict(from_attributes=True)


# --- Schémas pour le système Social (Follow) ---

class FollowUserInfo(BaseModel):
    """Infos minimales d'un utilisateur exposées dans les listes sociales."""
    id_utilisateur: int
    nom: str
    prenom: Optional[str] = None
    path_pp: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserSearchResult(FollowUserInfo):
    """Résultat de recherche : inclut si l'utilisateur courant le suit déjà."""
    is_followed: bool = False

class FollowStatsResponse(BaseModel):
    id_utilisateur: int
    followers_count: int
    following_count: int
    is_following: bool        # est-ce que MOI je suis cet utilisateur
    is_following_back: bool   # est-ce que lui ME suit (follow-back mutuel)

# --- Schémas pour Friendships ---

class FriendshipBase(BaseModel):
    requester_id: int
    receiver_id: int
    status: str

class FriendshipResponse(FriendshipBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Infos sur l'ami (sender ou receiver en fonction de qui demande)
    ami: Optional[FollowUserInfo] = None

    model_config = ConfigDict(from_attributes=True)


class SharedRecipeBase(BaseModel):
    recipe_id: int
    receiver_ids: List[int]

class SharedRecipeResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    recipe_id: int
    created_at: datetime
    
    recette: Optional[Recette] = None
    sender: Optional[FollowUserInfo] = None

    model_config = ConfigDict(from_attributes=True)

class FriendProfileResponse(BaseModel):
    id_utilisateur: int
    nom: str
    prenom: Optional[str] = None
    path_pp: Optional[str] = None
    objectif: Optional[str] = None
    # Favoris et programmes (optionnel)
    recettes_favorites: List[Recette] = []
    programmes_actifs: List[dict] = [] # on pourrait mettre PlanningSeance, etc.

    model_config = ConfigDict(from_attributes=True)
