from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
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
    
    # Données santé
    poids = Column(Float, nullable=True)
    taille = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)
    sexe = Column(String(20), nullable=True)
    objectif = Column(String(50), nullable=True)
    # niveau_activite = Column(String(50), nullable=True) # Désactivé pour l'instant

class Recette(Base):
    __tablename__ = "Recette"

    id_recette = Column(Integer, primary_key=True, index=True)
    nom_recette = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    ingredients = Column(Text, nullable=False) 
    nombre_calories = Column(Integer, nullable=True, default=0)
    image_url = Column(String(255), nullable=True)
    # tags = Column(String(255), nullable=True) # À ajouter plus tard si besoin

# --- AJOUT DE LA CLASSE MANQUANTE ---
class Seance(Base):
    __tablename__ = "Seance"

    id_seance = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100))
    duree = Column(Integer)
    
    # Relation : Une séance contient plusieurs exercices
    exercices = relationship("Exercice", back_populates="seance", cascade="all, delete-orphan")

class Exercice(Base):
    __tablename__ = "Exercice"

    id_exercice = Column(Integer, primary_key=True, index=True)
    nom_exercice = Column(String(100), nullable=False)
    description_exercice = Column(Text, nullable=True)
    type_exercice = Column(String(50), nullable=True) # ex: 'cardio', 'renfo'
    nombre_series = Column(Integer, nullable=True)
    calories_brulees = Column(Float, nullable=True)
    temps_recuperation = Column(Integer, nullable=True)
    id_seance = Column(Integer, ForeignKey("Seance.id_seance"), nullable=True) # Nullable pour le catalogue
    
    # --- NOUVELLES COLONNES ---
    muscle_cible = Column(JSON, nullable=True)
    materiel = Column(String(50), nullable=True)
    difficulte = Column(String(20), nullable=True)

    # Relation
    seance = relationship("Seance", back_populates="exercices")
    

class PlanningRepas(Base):
    __tablename__ = "PlanningRepas"
    id = Column(Integer, primary_key=True, index=True)
    id_utilisateur = Column(Integer, ForeignKey("Utilisateur.id_utilisateur"))
    id_recette = Column(Integer, ForeignKey("Recette.id_recette"))
    date = Column(DateTime)
    type_repas = Column(String(20))
    est_mange = Column(Boolean, default=False)

class PlanningSeance(Base):
    __tablename__ = "PlanningSeance"
    id = Column(Integer, primary_key=True, index=True)
    id_utilisateur = Column(Integer, ForeignKey("Utilisateur.id_utilisateur"))
    id_seance = Column(Integer, ForeignKey("Seance.id_seance"))
    date = Column(DateTime)
    est_fait = Column(Boolean, default=False)