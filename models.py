from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
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
    type_utilisateur = Column(String(50), default='client')

    sexe = Column(Enum("masculin", "feminin", name="sexe_enum"), nullable=True)
    age = Column(TINYINT(unsigned=True), nullable=True)
    poids_kg = Column(Float, nullable=True)
    taille_cm = Column(SmallInteger, nullable=True)
    regime_alimentaire = Column(String(100), nullable=True)
    objectif = Column(String(100), nullable=True)
    equipements = Column(String(255), nullable=True)
    nb_jours_entrainement = Column(TINYINT(unsigned=True), nullable=True)
    path_pp = Column(String(255), nullable=True)

class Recette(Base):
    __tablename__ = "Recette"

    id_recette = Column(Integer, primary_key=True, index=True)
    nom_recette = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    ingredients = Column(Text, nullable=False) 
    nombre_calories = Column(Integer, nullable=True, default=0)

class Exercice(Base):
    __tablename__ = "Exercice"

    id_exercice = Column(Integer, primary_key=True, index=True)
    nom_exercice = Column(String(100), nullable=False)
    description_exercice = Column(Text, nullable=True)
    type_exercice = Column(String(50), nullable=True)
    nombre_series = Column(Integer, nullable=True)
    calories_brulees = Column(Float, nullable=True)
    temps_recuperation = Column(Integer, nullable=True)
    id_seance = Column(Integer)
