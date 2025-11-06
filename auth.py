# nutrifit_api/auth.py (Version de débogage avancée)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError  # Importez ExpiredSignatureError
from sqlalchemy.orm import Session
import sys # Importez sys pour le print

# Importe vos propres modules
from database import SessionLocal
from models import Utilisateur
from utils.token import SECRET_KEY, ALGORITHM # Depuis votre fichier token.py

# Dépendance pour obtenir la session de BDD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

http_bearer_scheme = HTTPBearer()

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(http_bearer_scheme), 
    db: Session = Depends(get_db)
):
    """
    Décode le token, trouve l'utilisateur et le renvoie.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = creds.credentials
        print(f"\n--- DEBUG: TOKEN REÇU ---\n{token}\n---------------------------", file=sys.stderr)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        email: str = payload.get("sub")
        print(f"--- DEBUG: PAYLOAD DÉCODÉ, EMAIL TROUVÉ --- \n{email}\n---------------------------------", file=sys.stderr)
        
        if email is None:
            print("--- ERREUR: 'sub' (email) est None dans le payload.", file=sys.stderr)
            raise credentials_exception
    
    except ExpiredSignatureError:
        # Attrape l'erreur si le token est juste expiré
        print("--- ERREUR: LE TOKEN A EXPIRÉ (ExpiredSignatureError) ---", file=sys.stderr)
        raise credentials_exception
    except JWTError as e:
        # Attrape toutes les autres erreurs JWT (signature invalide, etc.)
        print(f"--- ERREUR: LE DÉCODAGE A ÉCHOUÉ (JWTError) --- \n{e}\n-----------------------------------", file=sys.stderr)
        raise credentials_exception
    
    # Si le décodage a réussi, on cherche l'utilisateur
    user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
    
    if user is None:
        print(f"--- ERREUR: Utilisateur non trouvé en BDD pour l'email: {email} ---", file=sys.stderr)
        raise credentials_exception
    
    print(f"--- DEBUG: UTILISATEUR TROUVÉ --- \n{user.email} (Rôle: {user.type_utilisateur})\n---------------------------", file=sys.stderr)
    return user

async def get_current_admin_user(current_user: Utilisateur = Depends(get_current_user)):
    """
    Vérifie si l'utilisateur (validé) est un admin.
    """
    
    print(f"--- DEBUG: Vérification admin pour {current_user.email}. Rôle trouvé : '{current_user.type_utilisateur}'", file=sys.stderr)
    
    if current_user.type_utilisateur != 'admin':
        print(f"--- ECHEC ADMIN: Rôle '{current_user.type_utilisateur}' n'est pas 'admin'.", file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits insuffisants : opération réservée aux administrateurs."
        )
    
    print("--- SUCCÈS ADMIN: L'utilisateur est admin.", file=sys.stderr)
    return current_user