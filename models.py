from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum, Float, SmallInteger, Text, Date, Time, ForeignKey
)
from sqlalchemy.dialects.mysql import TINYINT
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
    categorie = Column(String(50), nullable=True)
    calories = Column(Integer, nullable=True, default=0)
    proteines = Column(Float, nullable=True)
    glucides = Column(Float, nullable=True)
    lipides = Column(Float, nullable=True)
    ingredients = Column(Text, nullable=False) 
    tags = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    cautions = Column(Text, nullable=True)

class Exercice(Base):
    __tablename__ = "Exercice"
    id_exercice = Column(Integer, primary_key=True, index=True)
    nom_exercice = Column(String(100), nullable=False)
    description_exercice = Column(Text, nullable=True)
    type_exercice = Column(String(50), nullable=True)
    image_path = Column(String(255), nullable=True)
    muscle_cible = Column(Text, nullable=True)
    materiel = Column(Enum('poids_du_corps','materiel_maison','salle_de_sport'), default='poids_du_corps')

class PlanningRepas(Base):
    __tablename__ = "PlanningRepas"
    id_planning_repas = Column(Integer, primary_key=True, index=True)
    id_utilisateur = Column(Integer, nullable=False, index=True)
    id_recette = Column(Integer, nullable=False, index=True)
    jour = Column(Date, nullable=False)
    repas = Column(String(20), nullable=False) 
    date_creation = Column(DateTime, default=datetime.utcnow)
    heure_debut = Column(Time, nullable=True)
    notes = Column(Text, nullable=True)

class PlanningSeance(Base):
    __tablename__ = "PlanningSeance"
    id_planning_seance = Column(Integer, primary_key=True, index=True)
    id_utilisateur = Column(Integer, nullable=False, index=True)
    id_seance = Column(Integer, nullable=False, index=True) 
    jour = Column(Date, nullable=False)
    
    # INDISPENSABLE : Il faut cette colonne pour cocher la séance
    # Si elle n'est pas dans votre BDD, lancez le script SQL ci-dessous
    est_realise = Column(Boolean, default=False)
    
    # Vous avez dit avoir 'date_creation' dans PlanningSeance, on le garde donc ici
    date_creation = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # SUPPRIMÉS DU MODÈLE : ordre, series, repetitions, poids_kg, repos_secondes

class Seance(Base):
    __tablename__ = "Seance"
    id_seance = Column(Integer, primary_key=True, index=True)
    id_calendrier = Column(Integer, nullable=True)
    
    # STRICTEMENT VOS COLONNES
    nom = Column(String(100), nullable=False)
    duree = Column(Integer, nullable=True)

class SeanceExercice(Base):
    __tablename__ = "SeanceExercice"
    id = Column(Integer, primary_key=True, index=True)
    id_seance = Column(Integer, nullable=False, index=True)
    id_exercice = Column(Integer, nullable=False, index=True)
    
    # C'est ICI que sont les infos techniques
    ordre = Column(Integer, default=1)
    series = Column(Integer, default=4)
    repetitions = Column(Integer, default=12)
    temps_recuperation = Column(Integer, default=60)