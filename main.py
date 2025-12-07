# nutrifit_api/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List

import logging


# Importe vos modules de base
from database import Base, engine, SessionLocal
from models import Utilisateur, Recette # Importe Recette
import schemas # Importe le nouveau fichier schemas
import auth # Importe le nouveau fichier d'auth

# Importe les contrôleurs
from controllers.user_controller import signup_user, login_user, verify_code
from controllers import recette_controller as rc # Renomme pour clarté
from controllers import exercice_controller as ec

# Création de la base (votre code existant)
Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

from fastapi import FastAPI

app = FastAPI(
    title="NutriFit API",
    root_path="/nutrifit-api",
)

# --- Dépendances ---
# (Celle-ci est déplacée dans auth.py, mais on la garde ici
# pour les routes non protégées si besoin)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Modèles Pydantic pour l'utilisateur (votre code existant) ---
class SignupModel(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mot_de_passe: str

class LoginModel(BaseModel):
    email: EmailStr
    mot_de_passe: str

class VerifyCodeModel(BaseModel):
    email: EmailStr
    code: str

# --- Endpoints Utilisateur (Votre code existant) ---

@app.get("/")
def home():
    return {"message": "Bienvenue sur l'API NutriFit "}

@app.post("/signup")
def signup(data: SignupModel):
    try:
        # appel normal de ton contrôleur
        return signup_user(
            data.nom,
            data.prenom,
            data.email,
            data.mot_de_passe,
        )
    except Exception as e:
        # log côté serveur
        logger.exception("Erreur pendant /signup")
        # et renvoi du détail au client pour debug
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify_code")
def verify(data: VerifyCodeModel):
    return verify_code(data.email, data.code)

@app.post("/login")
def login(data: LoginModel):
    # Note: On suppose que login_user renvoie le token
    return login_user(data.email, data.mot_de_passe)


# --- NOUVEAUX ENDPOINTS POUR LES RECETTES ---

@app.get("/recettes", response_model=List[schemas.Recette])
def get_recettes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    # SÉCURITÉ : L'utilisateur doit être au minimum connecté
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Endpoint public pour voir toutes les recettes.
    (Nécessite d'être connecté)
    """
    recettes = rc.get_all_recettes(db, skip=skip, limit=limit)
    return recettes

@app.get("/recettes/{recette_id}", response_model=schemas.Recette)
def get_recette(
    recette_id: int,
    db: Session = Depends(get_db),
    # SÉCURITÉ : L'utilisateur doit être au minimum connecté
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Endpoint public pour voir UNE recette par son ID.
    (Nécessite d'être connecté)
    """
    db_recette = rc.get_recette_by_id(db, recette_id)
    if db_recette is None:
        raise HTTPException(status_code=404, detail="Recette non trouvée")
    return db_recette

@app.post("/recettes", response_model=schemas.Recette, status_code=status.HTTP_201_CREATED)
def create_new_recette(
    recette: schemas.RecetteCreate,
    db: Session = Depends(get_db),
    # SÉCURITÉ : Seul un ADMIN peut créer une recette
    current_admin: Utilisateur = Depends(auth.get_current_admin_user)
):
    """
    [ADMIN SEULEMENT] Créer une nouvelle recette.
    """
    return rc.create_recette(db=db, recette=recette)

@app.put("/recettes/{recette_id}", response_model=schemas.Recette)
def update_existing_recette(
    recette_id: int,
    recette: schemas.RecetteCreate,
    db: Session = Depends(get_db),
    # SÉCURITÉ : Seul un ADMIN peut modifier
    current_admin: Utilisateur = Depends(auth.get_current_admin_user)
):
    """
    [ADMIN SEULEMENT] Mettre à jour une recette par son ID.
    """
    db_recette = rc.update_recette(db, recette_id, recette)
    if db_recette is None:
        raise HTTPException(status_code=404, detail="Recette non trouvée")
    return db_recette

@app.delete("/recettes/{recette_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_recette(
    recette_id: int,
    db: Session = Depends(get_db),
    # SÉCURITÉ : Seul un ADMIN peut supprimer
    current_admin: Utilisateur = Depends(auth.get_current_admin_user)
):
    """
    [ADMIN SEULEMENT] Supprimer une recette par son ID.
    """
    if not rc.delete_recette(db, recette_id):
        raise HTTPException(status_code=404, detail="Recette non trouvée")
    return {"message": "Recette supprimée avec succès"}


@app.get("/exercices", response_model=List[schemas.Exercice])
def get_exercices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    return ec.get_all_exercices(db, skip, limit)


@app.get("/exercices/{exercice_id}", response_model=schemas.Exercice)
def get_exercice(
    exercice_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    ex = ec.get_exercice_by_id(db, exercice_id)
    if not ex:
        raise HTTPException(404, "Exercice non trouvé")
    return ex


@app.post("/exercices", response_model=schemas.Exercice)
def create_exercice(
    exercice: schemas.ExerciceCreate,
    db: Session = Depends(get_db),
    current_admin: Utilisateur = Depends(auth.get_current_admin_user)
):
    return ec.create_exercice(db, exercice)


@app.put("/exercices/{exercice_id}", response_model=schemas.Exercice)
def update_exercice(
    exercice_id: int,
    exercice: schemas.ExerciceCreate,
    db: Session = Depends(get_db),
    current_admin: Utilisateur = Depends(auth.get_current_admin_user)
):
    updated = ec.update_exercice(db, exercice_id, exercice)
    if not updated:
        raise HTTPException(404, "Exercice non trouvé")
    return updated


@app.delete("/exercices/{exercice_id}")
def delete_exercice(
    exercice_id: int,
    db: Session = Depends(get_db),
    current_admin: Utilisateur = Depends(auth.get_current_admin_user)
):
    if not ec.delete_exercice(db, exercice_id):
        raise HTTPException(404, "Exercice non trouvé")
    return {"message": "Exercice supprimé"}



    
    from auth import get_current_user

    @app.get("/users/me", response_model=schemas.UserResponse)
    def read_users_me(current_user: Utilisateur = Depends(auth.get_current_user)):
        """
        Retourne le profil complet de l'utilisateur connecté.
        """
        return current_user


    @app.put("/users/me", response_model=schemas.UserResponse)
    def update_user_profile(
        user_update: schemas.UserUpdate,
        db: Session = Depends(get_db),
        current_user: Utilisateur = Depends(auth.get_current_user),
    ):
        """
        Met à jour les infos de profil de l'utilisateur connecté.
        Les champs sont tous optionnels.
        """
        if user_update.nom is not None:
            current_user.nom = user_update.nom
        if user_update.prenom is not None:
            current_user.prenom = user_update.prenom

        if user_update.sexe is not None:
            current_user.sexe = user_update.sexe
        if user_update.age is not None:
            current_user.age = user_update.age
        if user_update.poids_kg is not None:
            current_user.poids_kg = user_update.poids_kg
        if user_update.taille_cm is not None:
            current_user.taille_cm = user_update.taille_cm
        if user_update.regime_alimentaire is not None:
            current_user.regime_alimentaire = user_update.regime_alimentaire
        if user_update.objectif is not None:
            current_user.objectif = user_update.objectif
        if user_update.equipements is not None:
            current_user.equipements = user_update.equipements
        if user_update.nb_jours_entrainement is not None:
            current_user.nb_jours_entrainement = user_update.nb_jours_entrainement
        if user_update.path_pp is not None:
            current_user.path_pp = user_update.path_pp

        db.commit()
        db.refresh(current_user)
        return current_user
