from datetime import datetime, timedelta
from fastapi import HTTPException
import random
from database import SessionLocal
from models import Utilisateur
from utils.security import hash_password, verify_password
from utils.token import create_access_token
from utils.email_utils import send_confirmation_email  # ✅ import ajouté


def signup_user(nom, prenom, email, mot_de_passe):
    db = SessionLocal()

    # Vérifier si l'email existe déjà
    existing = db.query(Utilisateur).filter_by(email=email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # Hasher le mot de passe
    hashed = hash_password(mot_de_passe)
    
     # Générer un code à 6 chiffres
    code = str(random.randint(100000, 999999))
    expiration = datetime.utcnow() + timedelta(minutes=15)

    # Créer un nouvel utilisateur
    user = Utilisateur(
        nom=nom,
        prenom=prenom,
        email=email,
        mot_de_passe=hashed,
        email_verifie=False,
        token_verification=code,
        token_expiration=expiration
    )

    db.add(user)
    db.commit()
    db.close()

    
    # Envoi du mail avec le code
    send_confirmation_email(email, code)

    return {"message": "Inscription réussie. Un code vous a été envoyé par e-mail."}

def verify_code(email, code):
    db = SessionLocal()
    user = db.query(Utilisateur).filter_by(email=email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if user.email_verifie:
        raise HTTPException(status_code=400, detail="Compte déjà vérifié")

    if user.token_verification != code:
        raise HTTPException(status_code=400, detail="Code incorrect")

    if user.token_expiration < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expiré")

    user.email_verifie = True
    user.token_verification = None
    user.token_expiration = None
    db.commit()
    db.close()

    return {"message": "Compte vérifié avec succès ! Vous pouvez maintenant vous connecter."}


def login_user(email, mot_de_passe):
    db = SessionLocal()
    user = db.query(Utilisateur).filter_by(email=email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if not user.email_verifie:
        raise HTTPException(status_code=403, detail="Veuillez vérifier votre e-mail avant de vous connecter.")

    if not verify_password(mot_de_passe, user.mot_de_passe):
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}