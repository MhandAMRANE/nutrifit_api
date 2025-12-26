import google.generativeai as genai
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import random

from models import Utilisateur, Exercice, PlanningRepas, PlanningSeance
from controllers import recette_controller as rc
from controllers import exercice_controller as ec
from controllers import planning_controller as pc 
from utils.health_formulas import calculate_bmr, calculate_tdee, calculate_target_calories

# --- CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY") 
if not API_KEY:
    raise ValueError("La clé API Gemini est manquante dans le fichier .env")

genai.configure(api_key=API_KEY)

def handle_chat_interaction(user_message: str, db: Session, current_user: Utilisateur):
    
    # =========================================================================
    # 1. OUTILS TRANSVERSES (Profil & Planning Global)
    # =========================================================================
    
    def TOOL_get_health_profile():
        """Récupère le profil santé et calcule les calories cibles."""
        if not all([current_user.poids, current_user.taille, current_user.age, current_user.sexe]):
            missing = []
            if not current_user.poids: missing.append("poids")
            if not current_user.taille: missing.append("taille")
            if not current_user.age: missing.append("âge")
            if not current_user.sexe: missing.append("sexe")
            return {"erreur": f"Profil incomplet. Demandez : {', '.join(missing)}."}
        
        bmr = calculate_bmr(current_user.poids, current_user.taille, current_user.age, current_user.sexe)
        tdee = calculate_tdee(bmr, "sedentaire")
        target = calculate_target_calories(tdee, current_user.objectif or "maintien")
        
        return {
            "profil": {"nom": current_user.prenom, "objectif": current_user.objectif},
            "analyse": {"bmr": bmr, "tdee": tdee, "cible_calorique_jour": target}
        }

    def TOOL_update_profile(age: int = None, sexe: str = None, poids: float = None, taille: int = None, objectif: str = None):
        """Met à jour le profil."""
        user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == current_user.id_utilisateur).first()
        if not user: return {"erreur": "Utilisateur introuvable."}

        if age: user.age = age
        if sexe: user.sexe = sexe
        if poids: user.poids = poids
        if taille: user.taille = taille
        if objectif: user.objectif = objectif
        
        db.commit()
        db.refresh(user)
        current_user.age, current_user.sexe = user.age, user.sexe
        current_user.poids, current_user.taille = user.poids, user.taille
        current_user.objectif = user.objectif

        return {"status": "succes", "message": "Profil mis à jour."}

    def TOOL_generate_planning():
        """Génère un planning auto (Repas + Sport)."""
        return pc.generate_weekly_plan(db, current_user.id_utilisateur, datetime.now())

    def TOOL_get_week_planning():
        """Lit le planning complet (Repas + Sport) de la semaine."""
        today = datetime.now()
        end = today + timedelta(days=7)
        
        # 1. Récupérer les REPAS
        entries_repas = pc.get_user_planning(db, current_user.id_utilisateur, today, end)
        planning_data = []
        
        if entries_repas:
            for entry in entries_repas:
                recette = rc.get_recette_by_id(db, entry.id_recette)
                if recette:
                    date_str = entry.date.strftime("%A %d")
                    planning_data.append(f"[REPAS] {date_str} ({entry.type_repas}) : {recette.nom_recette} (ID_PLANNING: {entry.id})")

        # 2. Récupérer le SPORT (requête directe car pas de fonction dans pc pour l'instant)
        entries_sport = db.query(PlanningSeance).filter(
            PlanningSeance.id_utilisateur == current_user.id_utilisateur,
            PlanningSeance.date >= today,
            PlanningSeance.date <= end
        ).all()

        if entries_sport:
            for entry in entries_sport:
                # On suppose qu'on a une fonction ou une relation pour avoir le nom, sinon on fait une requête
                seance = db.query(ec.models.Seance).filter(ec.models.Seance.id_seance == entry.id_seance).first()
                if seance:
                    date_str = entry.date.strftime("%A %d")
                    planning_data.append(f"[SPORT] {date_str} : {seance.nom} (ID_PLANNING: {entry.id})")

        return {"agenda_semaine": planning_data if planning_data else "Planning vide."}

    # =========================================================================
    # 2. OUTILS NUTRITION (Intelligents)
    # =========================================================================

    def TOOL_search_recipes(query: str = None):
        """
        Cherche des recettes. 
        Si 'query' est VIDE, sélectionne automatiquement des recettes adaptées aux calories de l'utilisateur.
        """
        target_meal_calories = 600 
        user_context = "Standard"

        if all([current_user.poids, current_user.taille, current_user.age, current_user.sexe]):
             bmr = calculate_bmr(current_user.poids, current_user.taille, current_user.age, current_user.sexe)
             tdee = calculate_tdee(bmr, "sedentaire")
             daily_target = calculate_target_calories(tdee, current_user.objectif or "maintien")
             target_meal_calories = daily_target * 0.35
             user_context = f"Objectif {current_user.objectif} ({int(daily_target)} kcal/j)"

        candidates = rc.get_all_recettes(db, limit=50, search=query)
        if not candidates: return {"resultat": "Aucune recette trouvée."}

        suitable = []
        if not query:
            for r in candidates:
                cal = r.nombre_calories or 0
                if (target_meal_calories - 250) <= cal <= (target_meal_calories + 250):
                    suitable.append(r)
            if not suitable: suitable = candidates
        else:
            suitable = candidates

        random.shuffle(suitable)
        selected = suitable[:5]

        return {
            "info_coaching": f"Contexte : {user_context}. Cible repas : ~{int(target_meal_calories)} kcal.",
            "recettes_trouvees": [
                {"id": r.id_recette, "nom": r.nom_recette, "calories": r.nombre_calories, "desc": r.description} 
                for r in selected
            ]
        }

    def TOOL_update_planning_entry(id_planning: int, new_recette_id: int):
        """Change une recette du planning."""
        success = pc.update_meal_planning(db, id_planning, new_recette_id)
        if success:
            recette = rc.get_recette_by_id(db, new_recette_id)
            return {"status": "succes", "message": f"Nouveau repas : {recette.nom_recette if recette else 'OK'}"}
        return {"erreur": "Entrée planning introuvable."}

    # =========================================================================
    # 3. OUTILS SPORT (Intelligents)
    # =========================================================================

    def TOOL_get_catalog_exercises():
        """Catalogue complet pour créer une séance."""
        exos = db.query(Exercice).all()
        return {"catalogue": [{"nom": e.nom_exercice, "categorie": e.type_exercice, "muscles": e.muscle_cible, "materiel": e.materiel, "difficulte": e.difficulte} for e in exos]}

    def TOOL_update_planning_seance(id_planning: int, new_seance_id: int):
        """Change une séance du planning."""
        try:
            success = pc.update_seance_planning(db, id_planning, new_seance_id)
            if success: return {"status": "succes", "message": "Séance modifiée."}
            return {"erreur": "Entrée planning introuvable."}
        except AttributeError:
            return {"erreur": "Fonction update_seance_planning manquante dans planning_controller."}

    def TOOL_get_exercises():
        """Liste simple."""
        exos = ec.get_all_exercices(db, limit=10)
        return {"exercices": [{"nom": e.nom_exercice} for e in exos]}

    # MAPPING GLOBAL
    tools_map = {
        "get_health_profile": TOOL_get_health_profile,
        "update_profile": TOOL_update_profile,
        "generate_planning": TOOL_generate_planning,
        "get_week_planning": TOOL_get_week_planning,
        "update_planning_entry": TOOL_update_planning_entry,
        "search_recipes": TOOL_search_recipes, # Version SMART
        "get_catalog_exercises": TOOL_get_catalog_exercises,
        "update_planning_seance": TOOL_update_planning_seance,
        "get_exercises": TOOL_get_exercises
    }

    # =========================================================================
    # 4. SYSTEM PROMPT (Le Cerveau Fusionné)
    # =========================================================================
    
    system_instruction = """
    Tu es FitBot, le coach expert NutriFit.
    
    RÈGLES DE COMPORTEMENT :
    1. **SOIS DIRECT** : Pas de "Je regarde...", "Un instant". Agis et donne le résultat.
    2. **AGIS EN SILENCE** : Appelle les outils nécessaires avant de répondre.
    
    --- GESTION NUTRITION (RECETTES & PLANNING) ---
    1. **RECETTES** : Utilise 'search_recipes'. 
       - Si l'utilisateur dit "Je ne sais pas quoi manger", appelle l'outil SANS argument (query=None) pour avoir une suggestion intelligente basée sur les calories.
       - Si l'utilisateur n'aime pas un ingrédient, propose une substitution (ex: yaourt grec au lieu de crème) grâce à tes connaissances, sans outil.
    2. **MODIFICATION PLANNING** :
       - Trouve l'ID du repas avec 'get_week_planning'.
       - Cherche une alternative avec 'search_recipes'.
       - Valide avec 'update_planning_entry'.
    
    --- GESTION SPORT (SÉANCES & PLANNING) ---
    1. **CRÉATION SÉANCE** : Si on te demande une séance :
       - Utilise 'get_catalog_exercises' pour voir le matériel.
       - CONSTRUIS la séance toi-même (Liste d'exos + Séries/Reps) selon l'objectif :
         * **PERTE DE POIDS** : Circuit/HIIT, Repos court (30s), Polyarticulaire.
         * **PRISE DE MASSE** : Séries classiques, Repos long (1m30).
       - Estime la durée (~3 min par exercice).
    2. **PLANNING SPORT** :
       - Vérifie toujours 'get_week_planning' pour éviter de travailler le même muscle que la veille.
       - Pour changer une séance, utilise 'update_planning_seance'.
    """

    tools_schema = [
        {"name": "get_health_profile", "description": "Récupère le profil.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "update_profile", "description": "Met à jour le profil.", "parameters": {"type": "OBJECT", "properties": {"age": {"type": "INTEGER"}, "sexe": {"type": "STRING"}, "poids": {"type": "NUMBER"}, "taille": {"type": "INTEGER"}, "objectif": {"type": "STRING"}}}},
        {"name": "generate_planning", "description": "Génère un planning complet.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "get_week_planning", "description": "Lit le planning (Repas + Sport).", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "update_planning_entry", "description": "Change un repas.", "parameters": {"type": "OBJECT", "properties": {"id_planning": {"type": "INTEGER"}, "new_recette_id": {"type": "INTEGER"}}, "required": ["id_planning", "new_recette_id"]}},
        {"name": "update_planning_seance", "description": "Change une séance.", "parameters": {"type": "OBJECT", "properties": {"id_planning": {"type": "INTEGER"}, "new_seance_id": {"type": "INTEGER"}}, "required": ["id_planning", "new_seance_id"]}},
        {"name": "search_recipes", "description": "Cherche des recettes. Si pas d'ingrédient précis, ne rien mettre dans query.", "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}},
        {"name": "get_catalog_exercises", "description": "Catalogue complet des exercices.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "get_exercises", "description": "Liste simple exercices.", "parameters": {"type": "OBJECT", "properties": {}}}
    ]

    model = genai.GenerativeModel(model_name="models/gemini-2.5-pro", tools=tools_schema, system_instruction=system_instruction)
    chat = model.start_chat(enable_automatic_function_calling=False)

    # --- 5. BOUCLE ---
    try:
        response = chat.send_message(user_message)
        
        while True:
            if not response.candidates: return "Désolé, blocage sécurité ou erreur API."
            
            part = response.candidates[0].content.parts[0]
            
            if part.function_call:
                fc = part.function_call
                name = fc.name
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
                response = chat.send_message(genai.protos.Part(function_response={"name": name, "response": res}))
                continue
            
            return part.text

    except Exception as e:
        print(f"❌ Erreur : {e}")
        return "Désolé, une erreur technique est survenue."