from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from database import Base

class Utilisateur(Base):
    __tablename__ = "Utilisateur"

    id_utilisateur = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100))
    prenom = Column(String(100))
    email = Column(String(100), unique=True)
    mot_de_passe = Column(String(255))
    email_verifie = Column(Boolean, default=False)
    token_verification = Column(String(255))
    token_expiration = Column(DateTime)
