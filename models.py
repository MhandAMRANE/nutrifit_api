from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON, Enum, Date, DECIMAL, SmallInteger
from sqlalchemy.orm import relationship
from database import Base

class Utilisateur(Base):
    __tablename__ = "Utilisateur"

    id_utilisateur = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100))
    email = Column(String(100), unique=True, nullable=False)
    mot_de_passe = Column(String(255), nullable=False)
    
    # Infos physiques & Profil
    sexe = Column(Enum('masculin', 'feminin'), nullable=True)
    age = Column(Integer, nullable=True) # tinyint unsigned en SQL
    poids_kg = Column(DECIMAL(5, 2), nullable=True)
    taille_cm = Column(SmallInteger, nullable=True)
    regime_alimentaire = Column(String(100))
    objectif = Column(String(100))
    equipements = Column(String(255))
    nb_jours_entrainement = Column(Integer)
    path_pp = Column(String(255))
    
    # Sécurité / Système
    email_verifie = Column(Boolean, default=False)
    token_verification = Column(String(10))
    token_expiration = Column(DateTime)
    type_utilisateur = Column(Enum('admin', 'client'), default='client')

    # Relations
    calendriers = relationship("Calendrier", back_populates="utilisateur")


class Calendrier(Base):
    __tablename__ = "Calendrier"
    
    id_calendrier = Column(Integer, primary_key=True, index=True)
    id_utilisateur = Column(Integer, ForeignKey("Utilisateur.id_utilisateur"))
    jour = Column(Date, nullable=False)

    utilisateur = relationship("Utilisateur", back_populates="calendriers")
    repas = relationship("Repas", back_populates="calendrier")
    seances = relationship("Seance", back_populates="calendrier")


class Recette(Base):
    __tablename__ = "Recette"

    id_recette = Column(Integer, primary_key=True, index=True)
    nom_recette = Column(String(100), nullable=False)
    description = Column(Text)
    categorie = Column(String(50))
    calories = Column(Integer)   # Attention: s'appelle 'calories' dans votre SQL, pas 'nombre_calories'
    proteines = Column(Float)
    glucides = Column(Float)
    lipides = Column(Float)
    
    # Relation Many-to-Many avec Repas via Repas_Recette
    repas_associes = relationship("RepasRecette", back_populates="recette")


class Repas(Base):
    __tablename__ = "Repas"

    id_repas = Column(Integer, primary_key=True, index=True)
    id_calendrier = Column(Integer, ForeignKey("Calendrier.id_calendrier"))
    categorie = Column(Enum('petit_dejeuner', 'dejeuner', 'diner', 'collation'))
    est_mange = Column(Boolean, default=False)

    calendrier = relationship("Calendrier", back_populates="repas")
    recettes_associees = relationship("RepasRecette", back_populates="repas")


class RepasRecette(Base):
    __tablename__ = "Repas_Recette"
    
    # Table d'association (pas de clé primaire 'id' dans votre SQL, c'est une clé composite)
    id_repas = Column(Integer, ForeignKey("Repas.id_repas"), primary_key=True)
    id_recette = Column(Integer, ForeignKey("Recette.id_recette"), primary_key=True)

    repas = relationship("Repas", back_populates="recettes_associees")
    recette = relationship("Recette", back_populates="repas_associes")


class Exercice(Base):
    __tablename__ = "Exercice"

    id_exercice = Column(Integer, primary_key=True, index=True)
    nom_exercice = Column(String(100), nullable=False)
    description_exercice = Column(Text)
    type_exercice = Column(String(50))
    image_path = Column(String(255))
    muscle_cible = Column(JSON) # JSON supporté par MariaDB/MySQL récents
    materiel = Column(Enum('poids_du_corps', 'materiel_maison', 'salle_de_sport'), default='poids_du_corps')


class Seance(Base):
    __tablename__ = "Seance"

    id_seance = Column(Integer, primary_key=True, index=True)
    id_calendrier = Column(Integer, ForeignKey("Calendrier.id_calendrier"))
    nom = Column(String(100))
    duree = Column(Integer)

    calendrier = relationship("Calendrier", back_populates="seances")
    seance_exercices = relationship("SeanceExercice", back_populates="seance")


class SeanceExercice(Base):
    __tablename__ = "Seance_Exercice"

    id = Column(Integer, primary_key=True, index=True)
    id_seance = Column(Integer, ForeignKey("Seance.id_seance"))
    id_exercice = Column(Integer, ForeignKey("Exercice.id_exercice"))
    
    nombre_series = Column(Integer, default=4)
    temps_recuperation = Column(Integer, default=60)
    ordre = Column(Integer, default=1)
    repetitions = Column(String(20))

    seance = relationship("Seance", back_populates="seance_exercices")
    exercice = relationship("Exercice")