from sqlalchemy.orm import Session
import random
from models import Exercice, Seance, SeanceExercice
from schemas import ExerciceCreate

def get_all_exercices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Exercice).offset(skip).limit(limit).all()

def get_exercice_by_id(db: Session, exercice_id: int):
    return db.query(Exercice).filter(Exercice.id_exercice == exercice_id).first()

# =============================================================================
# GÉNÉRATEUR SÉANCE (Aligné sur vos colonnes BDD)
# =============================================================================
def generate_seance_relational(db: Session, nom_seance: str, focus: str, materiel_user: str):
    
    # 1. Sélection Matériel & Exercices ( inchangé )
    allowed_materials = ["poids_du_corps"]
    mat_str = str(materiel_user).lower() if materiel_user else ""
    if "haltere" in mat_str or "maison" in mat_str: allowed_materials.append("materiel_maison")
    if "salle" in mat_str or "gym" in mat_str: allowed_materials.extend(["materiel_maison", "salle_de_sport"])

    all_exos = db.query(Exercice).filter(Exercice.materiel.in_(allowed_materials)).all()
    
    candidates = []
    keywords = {
        "full_body": ["force", "cardio", "polyarticulaire"],
        "upper": ["pectoraux", "dos", "epaules", "bras", "biceps", "triceps"],
        "lower": ["jambes", "quadriceps", "ischios", "fessiers", "mollets"],
        "push": ["pectoraux", "epaules", "triceps", "pompes"],
        "pull": ["dos", "biceps", "tractions"],
        "cardio": ["cardio"]
    }
    target_tags = keywords.get(focus, ["force"])

    for exo in all_exos:
        if focus == "full_body":
            candidates.append(exo)
        else:
            if exo.muscle_cible and any(tag in str(exo.muscle_cible).lower() for tag in target_tags):
                candidates.append(exo)
    
    if not candidates: candidates = all_exos

    selected = []
    if candidates:
        random.shuffle(candidates)
        selected = candidates[:5]

    # 2. CRÉATION SÉANCE (Uniquement : nom, duree, id_calendrier)
    new_seance = Seance(
        nom=nom_seance,     
        duree=45,           
        id_calendrier=None  
    )
    db.add(new_seance)
    db.commit()      
    db.refresh(new_seance)

    # 3. CRÉATION LIENS
    ordre = 1
    for exo in selected:
        liaison = SeanceExercice(
            id_seance=new_seance.id_seance,
            id_exercice=exo.id_exercice,
            ordre=ordre,
            series=4,
            repetitions=12,
            temps_recuperation=60
        )
        db.add(liaison)
        ordre += 1

    db.commit() 
    return new_seance