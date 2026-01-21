import requests
import json
from database import SessionLocal
from models import Exercice

# --- 1. CONFIGURATION ---
DATASET_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
BASE_IMAGE_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"

# --- 2. LA LISTE D'OR (Les seuls exos qu'on accepte) ---
# Les noms doivent correspondre EXACTEMENT à ceux du dataset JSON.
GOLDEN_LIST = [
    # --- PECTORAUX ---
    "Pushups", "Barbell Bench Press", "Dumbbell Bench Press", "Incline Hammer Curls", 
    "Chest Dip", "Cable Crossover", "Decline Pushups", "Diamond Pushup",
    
    # --- DOS ---
    "Pullups", "Chin-up", "Barbell Deadlift", "Bent Over Barbell Row", 
    "Seated Cable Row", "Lat Pulldown", "Back extension", "T-Bar Row",
    
    # --- JAMBES ---
    "Air Squat", "Barbell Squat", "Barbell Lunges", "Leg Press", 
    "Lying Leg Curls", "Leg Extensions", "Calf Raises", "Goblet Squat", 
    "Glute Bridge", "Romanian Deadlift",
    
    # --- EPAULES ---
    "Military Press", "Side Lateral Raise", "Front Plate Raise", 
    "Seated Dumbbell Press", "Reverse Flyes", "Arnold Press",
    
    # --- BRAS ---
    "Barbell Curl", "Dumbbell Bicep Curl", "Hammer Curls", "Preacher Curl",
    "Triceps Dip", "Skullcrushers", "Cable Tricep Pushdown", "Close Grip Barbell Bench Press",
    
    # --- ABS / CARDIO ---
    "Plank", "Crunches", "Leg Raise", "Russian Twist", "Mountain Climbers",
    "Burpees", "Jumping Jacks", "High Knees"
]

# --- 3. FONCTIONS DE MAPPING (Pour tes ENUMs) ---
def map_materiel(equipment_list):
    if not equipment_list: return "poids_du_corps"
    eq_str = str(equipment_list).lower()
    
    if any(x in eq_str for x in ["body", "none"]): return "poids_du_corps"
    if any(x in eq_str for x in ["dumbbell", "kettlebell", "band", "plate"]): return "materiel_maison"
    return "salle_de_sport" # Par défaut pour barbell, cable, machine

def map_type(mechanic):
    if mechanic == "compound": return "force"
    if mechanic == "isolation": return "isolation"
    return "cardio"

# --- 4. LE SCRIPT PRINCIPAL ---
def run_seed():
    print(f"🌍 Téléchargement du dataset...")
    try:
        data = requests.get(DATASET_URL).json()
    except Exception as e:
        print(f"❌ Erreur réseau : {e}")
        return

    print(f"📦 Dataset reçu ({len(data)} items). Filtrage des {len(GOLDEN_LIST)} meilleurs...")
    
    db = SessionLocal()
    
    # Optionnel : Vider la table avant
    # db.query(Exercice).delete()
    # db.commit()

    count = 0
    
    for item in data:
        original_name = item.get("name")
        
        # Le filtrage MAGIQUE est ici : On ne prend que ce qui est dans la Golden List
        if original_name in GOLDEN_LIST:
            
            # Gestion Image
            image_filename = item.get("images", [])[0] if item.get("images") else None
            full_image_url = f"{BASE_IMAGE_URL}{image_filename}" if image_filename else None

            # Traduction basique des muscles pour l'affichage
            targets = item.get("primaryMuscles", []) + item.get("secondaryMuscles", [])
            targets_fr = [t.replace("shoulders", "epaules")
                           .replace("chest", "pectoraux")
                           .replace("back", "dos")
                           .replace("legs", "jambes")
                           .replace("calves", "mollets")
                           .replace("hams", "ischios")
                           .replace("quads", "quadriceps")
                           .replace("abs", "abdominaux") 
                           for t in targets]

            # Vérif doublon
            exists = db.query(Exercice).filter(Exercice.nom_exercice == original_name).first()
            
            if not exists:
                new_exo = Exercice(
                    nom_exercice=original_name,
                    description_exercice=f"Instructions : {', '.join(item.get('instructions', []))[:600]}",
                    type_exercice=map_type(item.get("mechanic")),
                    muscle_cible=targets_fr,
                    materiel=map_materiel(item.get("equipment")),
                    image_path=full_image_url
                )
                db.add(new_exo)
                count += 1
                print(f"✅ Ajouté : {original_name}")

    db.commit()
    db.close()
    print(f"\n🎉 Terminé ! {count} exercices de qualité (avec images) ont été importés.")

if __name__ == "__main__":
    run_seed()