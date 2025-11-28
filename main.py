# nutrifit_api/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi import File, UploadFile
import shutil
import uuid
import os
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

app = FastAPI(title="NutriFit API")

os.makedirs("static/images/recettes", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: Utilisateur = Depends(auth.get_current_user)):
    """
    Affiche le profil complet (y compris poids, taille, etc.)
    """
    return current_user

@app.put("/users/me", response_model=schemas.UserResponse)
def update_user_profile(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Permet à l'utilisateur de mettre à jour ses infos (poids, taille, objectif...)
    """
    # On met à jour uniquement les champs fournis
    if user_update.nom is not None:
        current_user.nom = user_update.nom
    if user_update.prenom is not None:
        current_user.prenom = user_update.prenom
    if user_update.age is not None:
        current_user.age = user_update.age
    if user_update.poids is not None:
        current_user.poids = user_update.poids
    if user_update.taille is not None:
        current_user.taille = user_update.taille
    if user_update.sexe is not None:
        current_user.sexe = user_update.sexe
    if user_update.objectif is not None:
        current_user.objectif = user_update.objectif

    db.commit()
    db.refresh(current_user)
    return current_user

@app.post("/recettes/{recette_id}/image")
def upload_recipe_image(
    recette_id: int, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # current_user... (Sécurité)
):
    # 1. Vérifier que la recette existe
    recette = rc.get_recette_by_id(db, recette_id)
    if not recette:
        raise HTTPException(status_code=404, detail="Recette non trouvée")

    # 2. Générer un nom de fichier unique (Sécurité + Anti-doublon)
    # Ex: "mon_image.png" devient "a1b2c3d4-....png"
    extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    file_path = f"static/images/recettes/{unique_filename}"

    # 3. Sauvegarder le fichier sur le disque dur
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 4. Mettre à jour l'URL dans la BDD
    # On stocke l'URL relative accessible via l'API
    url_bdd = f"/static/images/recettes/{unique_filename}"
    
    recette.image = url_bdd
    db.commit()
    db.refresh(recette)

    return {"message": "Image uploadée", "url": url_bdd}


def delete_recette(db: Session, recette_id: int):
    # 1. On récupère la recette AVANT de la supprimer
    db_recette = get_recette_by_id(db, recette_id)
    
    if db_recette:
        # 2. Si elle a une image, on essaie de supprimer le fichier
        if db_recette.image_url:
            # db_recette.image_url ressemble à "/static/images/recettes/abc.jpg"
            # On doit enlever le "/" du début pour avoir un chemin relatif correct
            file_path = db_recette.image_url.lstrip("/") 
            
            # On vérifie si le fichier existe pour éviter de planter
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Image supprimée : {file_path}")

        # 3. Suppression en base de données
        db.delete(db_recette)
        db.commit()
        return True
        
    return False