from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON, Enum, Date, DECIMAL, SmallInteger
from sqlalchemy.orm import relationship
from database import Base

class Utilisateur(Base):
    __tablename__ = "Utilisateur"  # <--- On garde ton nom d'origine (Singulier/Majuscule)

    id_utilisateur = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100))
    email = Column(String(100), unique=True, nullable=False)
    mot_de_passe = Column(String(255), nullable=False)
    
    # Infos physiques & Profil
    sexe = Column(Enum('masculin', 'feminin'), nullable=True)
    age = Column(Integer, nullable=True) 
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
    # Correction : On pointe vers "Utilisateur" (ton vrai nom de table)
    id_utilisateur = Column(Integer, ForeignKey("Utilisateur.id_utilisateur")) 
    jour = Column(Date, nullable=False)

    utilisateur = relationship("Utilisateur", back_populates="calendriers")
    repas = relationship("Repas", back_populates="calendrier")
    seances = relationship("Seance", back_populates="calendrier")


class Recette(Base):
    __tablename__ = "Recette"  # <--- On revient sur ta table existante

    id_recette = Column(Integer, primary_key=True, index=True)
    nom_recette = Column(String(100), nullable=False)
    description = Column(Text)
    categorie = Column(String(50))
    calories = Column(Integer)   
    proteines = Column(Float)
    glucides = Column(Float)
    lipides = Column(Float)
    ingredients = Column(Text)
    tags = Column(Text)
    image_url = Column(String(255))
    cautions = Column(Text)
    
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
    muscle_cible = Column(JSON)
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
    # Correction des FK pour pointer vers "Seance" et "Exercice"
    id_seance = Column(Integer, ForeignKey("Seance.id_seance"))
    id_exercice = Column(Integer, ForeignKey("Exercice.id_exercice"))
    
    nombre_series = Column(Integer, default=4)
    temps_recuperation = Column(Integer, default=60)
    ordre = Column(Integer, default=1)
    repetitions = Column(String(20))

    seance = relationship("Seance", back_populates="seance_exercices")
    exercice = relationship("Exercice")


class PlanningRepas(Base):
    __tablename__ = "planning_repas"

    id_planning = Column(Integer, primary_key=True, index=True)
    
    # C'EST ICI QUE C'ETAIT FAUX : On corrige pour pointer vers "Utilisateur" et "Recette"
    id_utilisateur = Column(Integer, ForeignKey("Utilisateur.id_utilisateur"))
    id_recette = Column(Integer, ForeignKey("Recette.id_recette"))
    
    date = Column(Date)
    type_repas = Column(String(50))


class PlanningSeance(Base):
    __tablename__ = "planning_seances"

    id_planning_seance = Column(Integer, primary_key=True, index=True)
    
    # Correction ici aussi : "Utilisateur" et "Seance"
    id_utilisateur = Column(Integer, ForeignKey("Utilisateur.id_utilisateur"))
    id_seance = Column(Integer, ForeignKey("Seance.id_seance"))
    
    date = Column(Date)
    statut = Column(String(50), default="prevu")