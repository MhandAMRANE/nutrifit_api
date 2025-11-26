import google.generativeai as genai
from sqlalchemy.orm import Session
from models import Utilisateur
from controllers import recette_controller as rc
from controllers import exercice_controller as ec
from utils.health_formulas import calculate_bmr, calculate_tdee, calculate_target_calories

# Configurez votre clé ici ou via .env
API_KEY = "AIzaSyBF3jnfMb6MnkdoDIg0fusb_FHvfPg1XZc"
genai.configure(api_key=API_KEY)

def handle_chat_interaction(user_message: str, db: Session, current_user: Utilisateur):
    
    # --- 1. Définition des outils ---
    
    def TOOL_get_health_profile():
        """Récupère le profil santé et calcule les calories cibles."""
        if not all([current_user.poids, current_user.taille, current_user.age, current_user.sexe]):
            return {"erreur": "Profil incomplet. Demandez à l'utilisateur ses infos (poids/taille/age/sexe)."}
            
        bmr = calculate_bmr(current_user.poids, current_user.taille, current_user.age, current_user.sexe)
        tdee = calculate_tdee(bmr, current_user.niveau_activite or "sedentaire")
        target = calculate_target_calories(tdee, current_user.objectif or "maintien")
        
        return {
            "profil": {"nom": current_user.prenom, "objectif": current_user.objectif},
            "analyse": {"bmr": bmr, "tdee": tdee, "cible_calorique_jour": target}
        }

    def TOOL_search_recipes(query: str):
        """Cherche des recettes (ex: 'poulet', 'vegan')."""
        # On utilise votre contrôleur modifié
        recettes = rc.get_all_recettes(db, limit=5, search=query)
        if not recettes: return "Aucune recette trouvée."
        return [{"nom": r.nom_recette, "calories": r.nombre_calories} for r in recettes]

    def TOOL_get_exercises():
        """Liste les exercices disponibles."""
        exos = ec.get_all_exercices(db, limit=10)
        return [{"nom": e.nom_exercice, "type": e.type_exercice} for e in exos]

    tools = {
        "get_health_profile": TOOL_get_health_profile,
        "search_recipes": TOOL_search_recipes,
        "get_exercises": TOOL_get_exercises
    }

    # --- 2. Configuration Gemini avec les outils ---
    
    tools_schema = [
        {"name": "get_health_profile", "description": "Récupère le profil métabolique.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "search_recipes", "description": "Cherche des recettes.", "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}},
        {"name": "get_exercises", "description": "Liste les exercices.", "parameters": {"type": "OBJECT", "properties": {}}}
    ]

    model = genai.GenerativeModel(model_name="models/gemini-2.5-pro", tools=tools_schema)
    chat = model.start_chat(enable_automatic_function_calling=False)

    # --- 3. Boucle d'exécution ---
    response = chat.send_message(user_message)
    
    try:
        part = response.candidates[0].content.parts[0]
        
        # Si Gemini veut appeler un outil (Function Calling)
        if part.function_call:
            fc = part.function_call
            if fc.name in tools:
                args = {k: v for k, v in fc.args.items()}
                print(f"🤖 Appel outil : {fc.name} {args}")
                
                result = tools[fc.name](**args)
                
                # On renvoie le résultat à Gemini pour la réponse finale
                response = chat.send_message(
                    genai.protos.Part(function_response={"name": fc.name, "response": result})
                )
                return response.text
        
        return response.text
    except Exception as e:
        print(f"Erreur LLM: {e}")
        return "Désolé, je n'ai pas réussi à traiter votre demande."