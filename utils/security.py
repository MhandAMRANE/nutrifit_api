import bcrypt

def hash_password(password: str):
    """
    Hashe un mot de passe en clair en utilisant bcrypt.
    """
    # Convertit le mot de passe (str) en bytes
    password_bytes = password.encode('utf-8')
    
    # Génère un "salt" (sel)
    salt = bcrypt.gensalt()
    
    # Hashe le mot de passe
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    
    # Retourne le hash en tant que chaîne de caractères (str)
    # pour le stocker facilement dans la base de données.
    return hashed_bytes.decode('utf-8')

def verify_password(plain: str, hashed: str):
    """
    Vérifie un mot de passe en clair (plain) 
    contre un hash stocké (hashed).
    """
    try:
        # Convertit le mot de passe en clair (str) en bytes
        plain_bytes = plain.encode('utf-8')
        
        # Convertit le hash stocké (str) en bytes
        hashed_bytes = hashed.encode('utf-8')
        
        # Vérifie si les deux correspondent
        # bcrypt.checkpw fait tout le travail pour nous
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
        
    except ValueError:
        # Si le hash est malformé ou invalide
        return False
    except Exception as e:
        # Pour toute autre erreur inattendue
        print(f"Erreur lors de la vérification du mot de passe : {e}")
        return False