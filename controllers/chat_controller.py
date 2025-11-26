# nutrifit_api/controllers/chat_controller.py
import google.generativeai as genai
from sqlalchemy.orm import Session
from models import Utilisateur
from controllers import recette_controller as rc
from controllers import exercice_controller as ec
from utils.health_formulas import calculate_bmr, calculate_tdee, calculate_target_calories

# --- CONFIGURATION ---
API_KEY = "AIzaSyBF3jnfMb6MnkdoDIg0fusb_FHvfPg1XZc" # <--- Vérifiez votre clé
genai.configure(api_key=API_KEY)

def handle_chat_interaction(user_message: str, db: Session, current_user: Utilisateur):
    
    # --- 1. DÉFINITION DES OUTILS ---
    
    def TOOL_get_health_profile():
        """Récupère le profil santé et calcule les calories cibles."""
        if not all([current_user.poids, current_user.taille, current_user.age, current_user.sexe]):
            missing = []
            if not current_user.poids: missing.append("poids")
            if not current_user.taille: missing.append("taille")
            if not current_user.age: missing.append("âge")
            if not current_user.sexe: missing.append("sexe")
            # RETOURNE UN DICTIONNAIRE
            return {"erreur": f"Profil incomplet. Demandez à l'utilisateur : {', '.join(missing)}."}
            
        bmr = calculate_bmr(current_user.poids, current_user.taille, current_user.age, current_user.sexe)
        tdee = calculate_tdee(bmr, "sedentaire") 
        target = calculate_target_calories(tdee, current_user.objectif or "maintien")
        
        # RETOURNE UN DICTIONNAIRE
        return {
            "profil": {"nom": current_user.prenom, "age": current_user.age, "objectif": current_user.objectif},
            "analyse": {
                "bmr": bmr, 
                "tdee": tdee, 
                "cible_calorique_jour": target
            }
        }

    def TOOL_update_profile(age: int = None, sexe: str = None, poids: float = None, taille: int = None, objectif: str = None):
        """Enregistre ou met à jour les informations de l'utilisateur."""
        
        user_to_update = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == current_user.id_utilisateur).first()
        
        if not user_to_update:
            return {"erreur": "Utilisateur introuvable en base."}

        if age is not None: user_to_update.age = age
        if sexe is not None: user_to_update.sexe = sexe
        if poids is not None: user_to_update.poids = poids
        if taille is not None: user_to_update.taille = taille
        if objectif is not None: user_to_update.objectif = objectif
        
        db.commit()
        db.refresh(user_to_update)
        
        # Mise à jour de l'objet local
        current_user.age = user_to_update.age
        current_user.sexe = user_to_update.sexe
        current_user.poids = user_to_update.poids
        current_user.taille = user_to_update.taille
        current_user.objectif = user_to_update.objectif

        # --- CORRECTION ICI : RENVOYER UN DICT, PAS UN STRING ---
        return {
            "status": "succes", 
            "message": "Profil mis à jour avec succès dans la base de données."
        }

    def TOOL_search_recipes(query: str):
        """Cherche des recettes."""
        recettes = rc.get_all_recettes(db, limit=5, search=query)
        if not recettes: 
            return {"resultat": "Aucune recette trouvée."}
        
        # --- CORRECTION ICI : ENCAPSULER LA LISTE DANS UN DICT ---
        return {
            "recettes_trouvees": [
                {"nom": r.nom_recette, "calories": r.nombre_calories, "description": r.description} 
                for r in recettes
            ]
        }

    def TOOL_get_exercises():
        """Liste les exercices."""
        exos = ec.get_all_exercices(db, limit=10)
        
        # --- CORRECTION ICI : ENCAPSULER LA LISTE DANS UN DICT ---
        return {
            "exercices_disponibles": [
                {"nom": e.nom_exercice, "type": e.type_exercice} 
                for e in exos
            ]
        }

    # Mapping
    tools_map = {
        "get_health_profile": TOOL_get_health_profile,
        "update_profile": TOOL_update_profile,
        "search_recipes": TOOL_search_recipes,
        "get_exercises": TOOL_get_exercises
    }

    # --- 2. CONFIGURATION DU MODÈLE ---
    
    tools_schema = [
        {
            "name": "get_health_profile",
            "description": "Récupère le profil complet. À appeler au début.",
            "parameters": {"type": "OBJECT", "properties": {}}
        },
        {
            "name": "update_profile",
            "description": "Enregistre les infos physiques (âge, sexe, poids, taille, objectif).",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "age": {"type": "INTEGER"},
                    "sexe": {"type": "STRING"},
                    "poids": {"type": "NUMBER"},
                    "taille": {"type": "INTEGER"},
                    "objectif": {"type": "STRING", "enum": ["perte_poids", "prise_masse", "maintien"]}
                }
            }
        },
        {
            "name": "search_recipes",
            "description": "Cherche des recettes.",
            "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}
        },
        {
            "name": "get_exercises",
            "description": "Liste les exercices.",
            "parameters": {"type": "OBJECT", "properties": {}}
        }
    ]

    model = genai.GenerativeModel(model_name="models/gemini-2.5-pro", tools=tools_schema)
    chat = model.start_chat(enable_automatic_function_calling=False)

    # --- 3. BOUCLE ---
    try:
        response = chat.send_message(user_message)
        
        while True:
            part = response.candidates[0].content.parts[0]
            
            if part.function_call:
                fc = part.function_call
                name = fc.name
                
                # Sécurisation des arguments (au cas où)
                args = {}
                if fc.args and hasattr(fc.args, 'items'):
                    args = {k: v for k, v in fc.args.items()}
                
                print(f"🤖 [IA] Appel outil : {name} {args}")
                
                if name in tools_map:
                    try:
                        res = tools_map[name](**args)
                    except Exception as e_tool:
                        res = {"erreur_outil": str(e_tool)}
                else:
                    res = {"erreur": "Outil inconnu"}
                
                print(f"✅ [API] Résultat : {res}")

                response = chat.send_message(
                    genai.protos.Part(function_response={"name": name, "response": res})
                )
                continue
            
            # On renvoie le texte final
            return part.text

    except Exception as e:
        print(f"❌ Erreur : {e}")
        return "Désolé, une erreur technique est survenue."