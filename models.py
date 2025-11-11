from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
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

class Recette(Base):
    __tablename__ = "Recette"

    id_recette = Column(Integer, primary_key=True, index=True)
    nom_recette = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    ingredients = Column(Text, nullable=False) 
    nombre_calories = Column(Integer, nullable=True, default=0)

class Seance(Base):
    __tablename__ = "Seance"

    id_seance = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100))
    duree = Column(Integer)
    
    # Définit la relation : "Cette séance a plusieurs exercices"
    exercices = relationship("Exercice", back_populates="seance", cascade="all, delete-orphan")

class Exercice(Base):
    __tablename__ = "Exercice"

    id_exercice = Column(Integer, primary_key=True, index=True)
    nom_exercice = Column(String(100), nullable=False)
    description_exercice = Column(Text)
    type_exercice = Column(String(50))
    nombre_series = Column(Integer)
    calories_brulees = Column(Float)
    temps_recuperation = Column(Integer)
    
    # Clé étrangère pour lier à la Seance
    id_seance = Column(Integer, ForeignKey("Seance.id_seance"))
    
    # Définit la relation inverse : "Cet exercice appartient à une séance"
    seance = relationship("Seance", back_populates="exercices")