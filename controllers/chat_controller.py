# nutrifit_api/controllers/chat_controller.py
import google.generativeai as genai
from sqlalchemy.orm import Session
from models import Utilisateur
from controllers import recette_controller as rc
from controllers import exercice_controller as ec
from utils.health_formulas import calculate_bmr, calculate_tdee, calculate_target_calories
import os

# --- CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY") 

if not API_KEY:
    raise ValueError("La clé API Gemini est manquante dans le fichier .env")

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

    def TOOL_get_week_planning():
        """Récupère le planning de la semaine en cours pour voir ce qui est prévu."""
        today = datetime.now()
        end = today + timedelta(days=7)
        # On récupère les objets bruts
        planning_entries = pc.get_user_planning(db, current_user.id_utilisateur, today, end)
        
        # On les transforme en texte lisible pour l'IA
        # Il faut faire une jointure pour avoir le nom de la recette
        result_text = []
        for entry in planning_entries:
            recette = rc.get_recette_by_id(db, entry.id_recette) # Fonction existante
            date_str = entry.date.strftime("%A") # Jour de la semaine (Lundi, Mardi...)
            result_text.append(f"- {date_str} ({entry.type_repas}) : {recette.nom_recette} (ID_PLANNING: {entry.id})")
            
        return "\n".join(result_text)

    def TOOL_replace_planned_meal(day_name: str, meal_type: str, new_ingredient_query: str):
        """
        Remplace un repas du planning.
        1. Cherche le repas prévu ce jour-là.
        2. Cherche une nouvelle recette avec 'new_ingredient_query'.
        3. Fait l'échange.
        """
        
        pass 
    
    # --- APPROCHE RECOMMANDÉE POUR L'IA (Step-by-Step) ---
    
    def TOOL_update_planning_entry(planning_id: int, new_recette_id: int):
        """Met à jour une entrée précise du planning avec une nouvelle recette."""
        success = pc.update_meal_planning(db, planning_id, new_recette_id)
        if success:
            return {"status": "success", "message": "Le planning a été modifié."}
        return {"error": "Entrée de planning introuvable."}

    def TOOL_search_recipes(query: str = None):
        """
        Cherche des recettes. 
        Si 'query' est vide, sélectionne les recettes adaptées aux besoins caloriques de l'utilisateur.
        """
        # 1. Calculer la cible calorique pour un repas (environ 30-35% de la journée)
        target_meal_calories = 600 # Valeur par défaut moyenne
        user_context = "Profil standard"

        if all([current_user.poids, current_user.taille, current_user.age, current_user.sexe]):
             bmr = calculate_bmr(current_user.poids, current_user.taille, current_user.age, current_user.sexe)
             tdee = calculate_tdee(bmr, "sedentaire") # Ou current_user.niveau_activite
             daily_target = calculate_target_calories(tdee, current_user.objectif or "maintien")
             
             # On estime qu'un repas principal (Dîner) fait ~35% des apports
             target_meal_calories = daily_target * 0.35
             user_context = f"Objectif {current_user.objectif or 'maintien'} ({int(daily_target)} kcal/jour)"

        # 2. Récupérer un large choix de recettes (50) pour pouvoir filtrer
        # Si query est renseigné, on cherche par mot clé, sinon on prend tout
        candidates = rc.get_all_recettes(db, limit=50, search=query)
        
        if not candidates: 
            return {"resultat": "Aucune recette trouvée dans la base de données."}

        # 3. Filtrage Intelligent (Logique Métier)
        # On cherche des recettes proches de la cible (+/- 200 kcal de tolérance)
        # Ex: Si je dois manger 600kcal, j'accepte entre 400 et 800.
        
        suitable_recipes = []
        for r in candidates:
            cal = r.nombre_calories or 0 # Sécurité si null
            
            # Si l'utilisateur veut perdre du poids, on évite ce qui dépasse trop la cible
            if (target_meal_calories - 250) <= cal <= (target_meal_calories + 250):
                suitable_recipes.append(r)
        
        # Fallback : Si aucune recette ne correspond parfaitement, on garde les candidats initiaux
        # pour ne pas renvoyer une liste vide (ce serait frustrant).
        if not suitable_recipes:
            suitable_recipes = candidates

        # 4. Sélection aléatoire parmi les recettes adaptées
        import random
        random.shuffle(suitable_recipes)
        selected = suitable_recipes[:5] # On en garde 5

        return {
            "info_coaching": f"Basé sur votre {user_context}, je vise un repas autour de {int(target_meal_calories)} kcal.",
            "recettes_trouvees": [
                {"nom": r.nom_recette, "calories": r.nombre_calories, "description": r.description} 
                for r in selected
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