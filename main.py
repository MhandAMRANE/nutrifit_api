# nutrifit_api/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List

# Importe vos modules de base
from database import Base, engine, SessionLocal
from models import Utilisateur, Recette # Importe Recette
import schemas # Importe le nouveau fichier schemas
import auth # Importe le nouveau fichier d'auth

# Importe les contrôleurs
from controllers.user_controller import signup_user, login_user, verify_code
from controllers import recette_controller as rc # Renomme pour clarté

# Création de la base (votre code existant)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NutriFit API")

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
    return signup_user(data.nom, data.prenom, data.email, data.mot_de_passe)

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