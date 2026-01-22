from sqlalchemy.orm import Session
from models import Exercice
from schemas import ExerciceCreate

def get_all_exercices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Exercice).offset(skip).limit(limit).all()

def get_exercice_by_id(db: Session, exercice_id: int):
    return db.query(Exercice).filter(Exercice.id_exercice == exercice_id).first()

def create_exercice(db: Session, exercice: ExerciceCreate):
    db_exercice = Exercice(**exercice.model_dump())
    db.add(db_exercice)
    db.commit()
    db.refresh(db_exercice)
    return db_exercice

def delete_exercice(db: Session, exercice_id: int):
    db_exercice = get_exercice_by_id(db, exercice_id)
    if db_exercice:
        db.delete(db_exercice)
        db.commit()
        return True
    return False

def update_exercice(db: Session, exercice_id: int, exercice_data: ExerciceCreate):
    db_exercice = get_exercice_by_id(db, exercice_id)
    if db_exercice:

        db_exercice.nom_exercice = exercice_data.nom_exercice
        db_exercice.description_exercice = exercice_data.description_exercice
        db_exercice.type_exercice = exercice_data.type_exercice
        db_exercice.image_path = exercice_data.image_path
        db_exercice.muscle_cible = exercice_data.muscle_cible
        db_exercice.materiel = exercice_data.materiel

        db.commit()
        db.refresh(db_exercice)
        return db_exercice

    return None

def generate_seance_relational(db: Session, user_id: int, nom_seance: str, focus: str, materiel_user: str):
    """
    1. Crée une séance (table Seance).
    2. Sélectionne des exercices adaptés (table Exercice).
    3. Crée les liens (table SeanceExercice) avec séries/reps.
    """
    # 1. Filtrage du matériel (Logique métier)
    allowed_materials = ["poids_du_corps"]
    # On normalise en minuscule pour éviter les soucis de casse
    mat_str = str(materiel_user).lower() if materiel_user else ""
    
    if "haltere" in mat_str or "maison" in mat_str:
        allowed_materials.append("materiel_maison")
    if "salle" in mat_str or "gym" in mat_str:
        allowed_materials.extend(["materiel_maison", "salle_de_sport"])

    # 2. Récupération des exercices compatibles depuis la BDD
    all_exos = db.query(Exercice).filter(Exercice.materiel.in_(allowed_materials)).all()
    
    candidates = []
    # Dictionnaire de mots-clés pour cibler les muscles
    keywords = {
        "full_body": ["force", "cardio", "polyarticulaire"],
        "upper": ["pectoraux", "dos", "epaules", "bras", "biceps", "triceps"],
        "legs": ["jambes", "quadriceps", "ischios", "fessiers", "mollets"],
        "cardio": ["cardio"]
    }
    # Par défaut, on cherche des exos de force si le focus n'est pas reconnu
    target_tags = keywords.get(focus, ["force"])

    for exo in all_exos:
        if focus == "full_body":
            # Pour full body, on prend tout ce qui est compatible
            candidates.append(exo)
        else:
            # Sinon on cherche si le muscle cible correspond au focus
            # (On vérifie que muscle_cible n'est pas None avant)
            if exo.muscle_cible and any(tag in str(exo.muscle_cible).lower() for tag in target_tags):
                candidates.append(exo)
    
    # Sécurité : Si aucun exo n'est trouvé (ex: base vide ou critères trop stricts), on prend tout
    if not candidates:
        candidates = all_exos

    # Mélange et sélection (5 exercices max)
    random.shuffle(candidates)
    selected = candidates[:5] 

    # 3. CRÉATION DE LA SÉANCE (Le "Conteneur")
    new_seance = Seance(
        id_utilisateur=user_id,
        nom_seance=nom_seance,
        description=f"Séance {focus} générée automatiquement.",
        duree_minutes=45
    )
    db.add(new_seance)
    db.commit()      # On commit pour obtenir l'ID de la séance
    db.refresh(new_seance)

    # 4. CRÉATION DES LIENS (Le "Contenu")
    ordre = 1
    for exo in selected:
        # Logique simple pour les séries/reps
        nb_series = 4
        nb_reps = 12
        temps_repos = 60
        
        if focus == "cardio":
            nb_reps = 20
            temps_repos = 30
        
        liaison = SeanceExercice(
            id_seance=new_seance.id_seance,   # Lien vers la séance créée juste avant
            id_exercice=exo.id_exercice,      # Lien vers l'exercice choisi
            ordre=ordre,
            series=nb_series,
            repetitions=nb_reps,
            temps_recuperation=temps_repos
        )
        db.add(liaison)
        ordre += 1

    db.commit() # On valide l'ajout de tous les exercices
    
    return new_seance