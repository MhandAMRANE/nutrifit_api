# controllers/seance_controller.py
from sqlalchemy.orm import Session
from models import Seance, Exercice
from schemas import SeanceCreate, ExerciceCreate

def get_all_seances(db: Session, skip: int = 0, limit: int = 100):
    print("\n--- DEBUG: Appel de get_all_seances ---")
    seances = db.query(Seance).offset(skip).limit(limit).all()
    print(f"--- DEBUG: {len(seances)} séances trouvées en BDD ---")
    return seances

def get_seance_by_id(db: Session, seance_id: int):
    return db.query(Seance).filter(Seance.id_seance == seance_id).first()

def create_seance(db: Session, seance: SeanceCreate):
    print("\n--- DEBUG: Appel de create_seance ---")
    
    # Sépare les données
    exercices_data = seance.exercices
    seance_data = seance.model_dump(exclude={"exercices"})
    
    # Crée l'objet Seance
    db_seance = Seance(**seance_data)
    print(f"--- DEBUG: Objet Seance créé (nom: {db_seance.nom}) ---")

    # Crée les objets Exercice
    for exercice_data in exercices_data:
        db_exercice = Exercice(**exercice_data.model_dump(), seance=db_seance)
        db_seance.exercices.append(db_exercice)
    
    print(f"--- DEBUG: {len(db_seance.exercices)} exercices créés ---")

    try:
        #  Ajouter à la session
        db.add(db_seance)
        print("--- DEBUG: db.add(db_seance) exécuté ---")
        
        #  Sauvegarder
        db.commit()
        print("--- DEBUG: db.commit() RÉUSSI ---")
        
        #  Rafraîchir
        db.refresh(db_seance)
        print(f"--- DEBUG: db.refresh() RÉUSSI (ID: {db_seance.id_seance}) ---")
        
        return db_seance

    except Exception as e:
        # --- C'EST PROBABLEMENT ICI QUE ÇA CASSE ---
        print("\n!!!!!!!!!!!! ERREUR LORS DU COMMIT !!!!!!!!!!!!")
        print(f"--- DEBUG: L'erreur est: {e} ---")
        print("--- DEBUG: Annulation (rollback) en cours... ---")
        
        # Annule la transaction
        db.rollback() 
        
        # Renvoie une erreur claire à l'utilisateur
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne du serveur lors de la création : {e}"
        )

def delete_seance(db: Session, seance_id: int):
    db_seance = get_seance_by_id(db, seance_id)
    if db_seance:
        db.delete(db_seance)
        db.commit()
        return True
    return False

def update_seance(db: Session, seance_id: int, seance_data: SeanceCreate):
    db_seance = get_seance_by_id(db, seance_id)
    if not db_seance:
        return None

    
    db_seance.nom = seance_data.nom
    db_seance.duree = seance_data.duree

   
    db_seance.exercices.clear() 
    

    for exercice_data in seance_data.exercices:
        db_exercice = Exercice(**exercice_data.model_dump(), seance=db_seance)
        db.add(db_exercice)

    db.commit()
    db.refresh(db_seance)
    return db_seance