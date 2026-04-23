from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List

import logging


from database import Base, engine, SessionLocal
from models import Utilisateur, Recette, PlanningRepas, PlanningSeance
import models
import schemas
import auth 

from controllers.user_controller import signup_user, login_user, verify_code, update_user_profile
from controllers import recette_controller as rc
from controllers import exercice_controller as ec
from controllers import chat_controller as cc
from controllers import calendar_controller as cal_c
from controllers import favoris_controller as fc
from controllers import social_controller as sc
from controllers import payment_controller as pc

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"⚠️ Erreur lors de la création des tables (vérifier la connexion BDD) : {e}")

logger = logging.getLogger(__name__)

from fastapi import FastAPI

app = FastAPI(
    title="NutriFit API",
    root_path="/nutrifit-api",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class CreatePaymentIntentModel(BaseModel):
    amount: int  # en centimes (ex: 500 = 5€, 1000 = 10€)
    currency: str = "eur"

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
    return login_user(data.email, data.mot_de_passe)

@app.get("/recettes", response_model=List[schemas.Recette])
def get_recettes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
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



    

@app.post("/chat", response_model=ChatResponse)
def chat_with_coach(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Discuter avec le coach IA (nécessite d'être connecté)"""
    ai_response = cc.handle_chat_interaction(
        user_message=request.message,
        db=db,
        current_user=current_user
    )
    return {"response": ai_response}

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: Utilisateur = Depends(auth.get_current_user)):
    """
    Affiche le profil complet (y compris poids, taille, etc.)
    """
    return current_user


@app.put("/users/me", response_model=schemas.UserResponse)
def update_my_profile(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user),
):
    """
    Met à jour les infos de profil de l'utilisateur connecté.
    Les champs sont tous optionnels.
    """
    try:
        updated_user = update_user_profile(db, current_user, user_update)
        logger.info(f"Profil mis à jour pour {current_user.email}")
        return updated_user
    except Exception as e:
        logger.exception(f"Erreur lors de la mise à jour du profil pour {current_user.email}")
        # On renvoie une erreur 500 mais avec le détail pour le client (en dev)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# ============ ROUTES CALENDRIER ============

@app.get("/calendar", response_model=schemas.Calendar)
def get_user_calendar(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Récupère le calendrier complet (repas + séances) de l'utilisateur.
    """
    calendar_data = cal_c.get_user_calendar(db, current_user.id_utilisateur)
    return {
        "id_utilisateur": current_user.id_utilisateur,
        "repas": calendar_data["repas"],
        "seances": calendar_data["seances"]
    }


@app.get("/calendar/{jour}", response_model=schemas.CalendarDay)
def get_calendar_day(
    jour: str,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Récupère les repas et séances pour un jour spécifique.
    Jour format: 2026-01-22
    """
    calendar_day = cal_c.get_calendar_by_day(db, current_user.id_utilisateur, jour)
    return calendar_day


@app.post("/calendar/meal", response_model=schemas.PlanningRepas, status_code=status.HTTP_201_CREATED)
def create_meal_planning(
    meal: schemas.PlanningRepasCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Ajoute un repas au calendrier.
    Paramètres:
    - id_recette: ID de la recette
    - jour: lundi, mardi, etc.
    - repas: petit-dej, dejeuner, diner, collation
    - notes: (optionnel)
    """
    new_meal = cal_c.add_meal_to_calendar(db, current_user.id_utilisateur, meal)
    return new_meal


@app.post("/calendar/workout", response_model=schemas.PlanningSeance, status_code=status.HTTP_201_CREATED)
def create_workout_planning(
    workout: schemas.PlanningSeanceCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Ajoute une séance d'entraînement au calendrier.
    Paramètres:
    - id_seance: ID de la séance
    - jour: lundi, mardi, etc.
    - notes: (optionnel)
    - est_realise: (optionnel, defaut False)
    """
    new_workout = cal_c.add_workout_to_calendar(db, current_user.id_utilisateur, workout)
    return new_workout


@app.put("/calendar/meal/{planning_id}", response_model=schemas.PlanningRepas)
def update_meal_planning(
    planning_id: int,
    meal_update: schemas.PlanningRepasCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Met à jour un repas du calendrier.
    """
    from datetime import datetime as dt
    
    db_meal = db.query(models.PlanningRepas).filter(
        models.PlanningRepas.id_planning_repas == planning_id,
        models.PlanningRepas.id_utilisateur == current_user.id_utilisateur
    ).first()
    
    if not db_meal:
        raise HTTPException(status_code=404, detail="Repas non trouvé")
    
    db_meal.id_recette = meal_update.id_recette
    db_meal.jour = meal_update.jour
    db_meal.repas = meal_update.repas
    db_meal.notes = meal_update.notes
    
    db.commit()
    db.refresh(db_meal)
    return db_meal


@app.put("/calendar/workout/{planning_id}", response_model=schemas.PlanningSeance)
def update_workout_planning(
    planning_id: int,
    workout_update: schemas.PlanningSeanceCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Met à jour une séance du calendrier.
    """
    from datetime import datetime as dt
    
    db_workout = db.query(models.PlanningSeance).filter(
        models.PlanningSeance.id_planning_seance == planning_id,
        models.PlanningSeance.id_utilisateur == current_user.id_utilisateur
    ).first()
    
    if not db_workout:
        raise HTTPException(status_code=404, detail="Séance non trouvée")
    
    db_workout.id_seance = workout_update.id_seance
    db_workout.jour = workout_update.jour
    db_workout.notes = workout_update.notes
    db_workout.est_realise = workout_update.est_realise
    
    db.commit()
    db.refresh(db_workout)
    return db_workout


@app.delete("/calendar/meal/{planning_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal_planning(
    planning_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Supprime un repas du calendrier.
    """
    success = cal_c.remove_meal_from_calendar(db, planning_id)
    if not success:
        raise HTTPException(status_code=404, detail="Repas non trouvé")
    return None


@app.delete("/calendar/workout/{planning_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout_planning(
    planning_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Supprime une séance du calendrier.
    """
    success = cal_c.remove_workout_from_calendar(db, planning_id)
    if not success:
        raise HTTPException(status_code=404, detail="Séance non trouvée")
    return None


# ============ ROUTES FAVORIS ============

@app.post("/favorites/{recette_id}", response_model=schemas.FavoriteResponse, status_code=status.HTTP_201_CREATED)
def add_favorite(
    recette_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Ajoute une recette aux favoris de l'utilisateur connecté.
    """
    fav = fc.add_favorite(db, current_user.id_utilisateur, recette_id)
    if not fav:
        raise HTTPException(status_code=404, detail="Recette non trouvée")
    return fav

@app.delete("/favorites/{recette_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    recette_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Supprime une recette des favoris de l'utilisateur connecté.
    """
    success = fc.remove_favorite(db, current_user.id_utilisateur, recette_id)
    if not success:
        raise HTTPException(status_code=404, detail="Favori non trouvé")
    return None

@app.get("/favorites", response_model=List[schemas.Recette])
def get_user_favorites(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """
    Récupère toutes les recettes favorites de l'utilisateur connecté.
    """
    return fc.get_user_favorites(db, current_user.id_utilisateur)


# ============ ROUTES SOCIAL (AMIS & PARTAGE) ============

@app.get("/friends", response_model=List[schemas.FollowUserInfo])
def get_my_friends(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Obtenir la liste de mes amis actuels"""
    return sc.get_friends(db, current_user.id_utilisateur)

@app.get("/friends/requests", response_model=List[schemas.FriendshipResponse])
def get_my_friend_requests(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Obtenir les demandes d'amis en attente (reçues)"""
    return sc.get_friend_requests(db, current_user.id_utilisateur)

@app.post("/friends/request", response_model=schemas.FriendshipResponse, status_code=status.HTTP_201_CREATED)
def send_friend_request(
    data: dict,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Envoyer une demande d'ami"""
    receiver_id = data.get("receiver_id")
    if not receiver_id:
        raise HTTPException(status_code=400, detail="receiver_id est requis")
    return sc.send_friend_request(db, current_user.id_utilisateur, receiver_id)

@app.put("/friends/request/{request_id}/accept", response_model=schemas.FriendshipResponse)
def accept_friend_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Accepter une demande d'ami"""
    return sc.accept_friend_request(db, request_request_id:=request_id, user_id=current_user.id_utilisateur)

@app.delete("/friends/request/{request_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
def reject_friend_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Refuser une demande d'ami"""
    sc.reject_friend_request(db, request_id, current_user.id_utilisateur)
    return None

@app.delete("/friends/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Supprimer un ami"""
    sc.remove_friend(db, current_user.id_utilisateur, user_id)
    return None

@app.get("/friends/search", response_model=List[schemas.UserSearchResult])
def search_users(
    q: str,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Recherche des utilisateurs (minimum 2 caractères)"""
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="La recherche doit contenir au moins 2 caractères")
    return sc.search_users(db, q.strip(), current_user.id_utilisateur)

@app.get("/friends/stats/{user_id}")
def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Stats sociales d'un profil"""
    return sc.get_stats(db, user_id, current_user.id_utilisateur)

@app.post("/recipes/share", response_model=List[schemas.SharedRecipeResponse], status_code=status.HTTP_201_CREATED)
def share_recipe(
    data: schemas.SharedRecipeBase,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Partager une recette avec un ou plusieurs amis"""
    return sc.share_recipe(db, current_user.id_utilisateur, data.receiver_ids, data.recipe_id)

@app.get("/recipes/shared-with-me", response_model=List[schemas.SharedRecipeResponse])
def get_shared_recipes(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Obtenir les recettes partagées par des amis"""
    return sc.get_shared_recipes_with_me(db, current_user.id_utilisateur)

@app.get("/users/{friend_id}/profile", response_model=schemas.FriendProfileResponse)
def get_friend_profile(
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(auth.get_current_user)
):
    """Le Profil Ami (Sécurisé)"""
    from controllers import favoris_controller as fc
    
    is_friend = sc.get_friends(db, current_user.id_utilisateur)
    is_friend = any(f.id_utilisateur == friend_id for f in is_friend)
    
    if not is_friend and current_user.id_utilisateur != friend_id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas ami avec cet utilisateur.")
        
    friend_user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == friend_id).first()
    if not friend_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        
    favs = fc.get_user_favorites(db, friend_id)
    
    return {
        "id_utilisateur": friend_user.id_utilisateur,
        "nom": friend_user.nom,
        "prenom": friend_user.prenom,
        "path_pp": friend_user.path_pp,
        "objectif": friend_user.objectif,
        "recettes_favorites": favs,
        "programmes_actifs": []
    }


@app.post("/payment/create-intent")
def create_payment_intent(
    data: CreatePaymentIntentModel,
    current_user: Utilisateur = Depends(auth.get_current_user),
):
    """
    [SANDBOX] Crée un PaymentIntent Stripe pour une donation simulée.
    Retourne le client_secret nécessaire pour confirmer le paiement côté frontend.
    Cartes de test : 4242 4242 4242 4242 (succès), 4000 0000 0000 9995 (échec).
    """
    return pc.create_payment_intent(data.amount, data.currency)


@app.get("/payment/status/{payment_intent_id}")
def get_payment_status(
    payment_intent_id: str,
    current_user: Utilisateur = Depends(auth.get_current_user),
):
    """
    [SANDBOX] Vérifie le statut d'un PaymentIntent Stripe.
    """
    return pc.confirm_payment_intent(payment_intent_id)
