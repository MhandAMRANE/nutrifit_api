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
    
    # 1. RÉCUPÉRATION DU CONTEXTE (TAGS DISPONIBLES)
    # On récupère la liste des tags pour que l'IA sache ce qui existe
    available_tags = rc.get_available_tags(db)
    tags_context_str = ", ".join(available_tags[:50]) # On en garde 50 max pour pas surcharger le prompt
    
    # =========================================================================
    # OUTILS (Code identique à avant, je ne change que search_recipes pour le commentaire)
    # =========================================================================
    
    def TOOL_get_health_profile():
        missing = []
        if not current_user.poids_kg: missing.append("poids")
        if not current_user.taille_cm: missing.append("taille")
        if not current_user.age: missing.append("âge")
        if not current_user.sexe: missing.append("sexe")
        
        if missing:
            return {"erreur": f"Profil incomplet. Il manque : {', '.join(missing)}."}
        
        bmr = calculate_bmr(current_user.poids_kg, current_user.taille_cm, current_user.age, current_user.sexe)
        tdee = calculate_tdee(bmr, "sedentaire")
        target = calculate_target_calories(tdee, current_user.objectif or "maintien")
        
        return {
            "profil": {"nom": current_user.prenom, "objectif": current_user.objectif},
            "analyse": {"bmr": bmr, "tdee": tdee, "cible_calorique_jour": target}
        }

    def TOOL_update_profile(age: int = None, sexe: str = None, poids: float = None, taille: int = None, objectif: str = None):
        user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == current_user.id_utilisateur).first()
        if not user: return {"erreur": "Utilisateur introuvable."}

        if sexe:
            s_clean = sexe.lower().strip()
            if s_clean in ['homme', 'h', 'masculin', 'male']: user.sexe = 'masculin'
            elif s_clean in ['femme', 'f', 'feminin', 'female']: user.sexe = 'feminin'

        if age: user.age = age
        if poids: user.poids_kg = poids
        if taille: user.taille_cm = taille
        if objectif: user.objectif = objectif
        
        db.commit()
        db.refresh(user)
        current_user.age = user.age
        current_user.sexe = user.sexe
        current_user.poids_kg = user.poids_kg
        current_user.taille_cm = user.taille_cm
        current_user.objectif = user.objectif

        return {"status": "succes", "message": "Profil mis à jour. ANALYSE LE RESTE DU MESSAGE : Veut-il une recette ?"}

    def TOOL_generate_planning():
        return pc.generate_weekly_plan(db, current_user.id_utilisateur, datetime.now())

    def TOOL_get_week_planning():
        today = datetime.now()
        end = today + timedelta(days=7)
        entries_repas = pc.get_user_planning(db, current_user.id_utilisateur, today, end)
        planning_data = []
        if entries_repas:
            for entry in entries_repas:
                recette = rc.get_recette_by_id(db, entry.id_recette)
                if recette:
                    date_str = entry.date.strftime("%A %d")
                    planning_data.append(f"[REPAS] {date_str} ({entry.type_repas}) : {recette.nom_recette} (ID: {entry.id_planning})")

        entries_sport = db.query(PlanningSeance).filter(PlanningSeance.id_utilisateur == current_user.id_utilisateur, PlanningSeance.date >= today, PlanningSeance.date <= end).all()
        if entries_sport:
            for entry in entries_sport:
                seance = db.query(ec.models.Seance).filter(ec.models.Seance.id_seance == entry.id_seance).first()
                if seance:
                    date_str = entry.date.strftime("%A %d")
                    planning_data.append(f"[SPORT] {date_str} : {seance.nom} (ID: {entry.id_planning_seance})")

        return {"agenda_semaine": planning_data if planning_data else "Planning vide."}

    def TOOL_search_recipes(query: str = None):
        """Cherche par Nom OU par Tag."""
        target_meal_calories = 600 
        if all([current_user.poids_kg, current_user.taille_cm, current_user.age, current_user.sexe]):
             try:
                 bmr = calculate_bmr(current_user.poids_kg, current_user.taille_cm, current_user.age, current_user.sexe)
                 tdee = calculate_tdee(bmr, "sedentaire")
                 daily_target = calculate_target_calories(tdee, current_user.objectif or "maintien")
                 target_meal_calories = daily_target * 0.35
             except: pass

        # La recherche regarde maintenant aussi dans les TAGS grâce à la modif dans recette_controller
        candidates = rc.get_all_recettes(db, limit=50, search=query)
        
        if not candidates: 
            return {"resultat": "Aucune recette trouvée."}

        suitable = []
        if not query:
            for r in candidates:
                cal = r.calories or 0
                if (target_meal_calories - 300) <= cal <= (target_meal_calories + 300):
                    suitable.append(r)
            if not suitable: suitable = candidates[:10]
        else:
            suitable = candidates

        random.shuffle(suitable)
        selected = suitable[:3] 

        return {
            "resultat": "Succès",
            "recettes": [
                {"id": r.id_recette, "original_name_en": r.nom_recette, "tags": r.tags, "calories": r.calories, "desc_en": r.description} 
                for r in selected
            ],
            "conseil": "Traduis les titres en français."
        }

    def TOOL_update_planning_entry(id_planning: int, new_recette_id: int):
        success = pc.update_meal_planning(db, id_planning, new_recette_id)
        if success:
            recette = rc.get_recette_by_id(db, new_recette_id)
            return {"status": "succes", "message": f"Repas modifié par : {recette.nom_recette}"}
        return {"erreur": "Impossible de modifier."}

    def TOOL_get_catalog_exercises():
        exos = db.query(Exercice).all()
        return {"catalogue": [{"nom": e.nom_exercice, "categorie": e.type_exercice} for e in exos]}

    def TOOL_update_planning_seance(id_planning: int, new_seance_id: int):
        try:
            success = pc.update_seance_planning(db, id_planning, new_seance_id)
            if success: return {"status": "succes"}
            return {"erreur": "Erreur update."}
        except: return {"erreur": "Fonction manquante."}

    def TOOL_get_exercises():
        exos = ec.get_all_exercices(db, limit=10)
        return {"exercices": [{"nom": e.nom_exercice} for e in exos]}

    tools_map = {
        "get_health_profile": TOOL_get_health_profile,
        "update_profile": TOOL_update_profile,
        "generate_planning": TOOL_generate_planning,
        "get_week_planning": TOOL_get_week_planning,
        "update_planning_entry": TOOL_update_planning_entry,
        "search_recipes": TOOL_search_recipes,
        "get_catalog_exercises": TOOL_get_catalog_exercises,
        "update_planning_seance": TOOL_update_planning_seance,
        "get_exercises": TOOL_get_exercises
    }

    # =========================================================================
    # SYSTEM PROMPT (AVEC LISTE DES TAGS)
    # =========================================================================
    
    system_instruction = f"""
    Tu es FitBot, le coach expert NutriFit.
    
    CONTEXTE DONNÉES :
    - Langue utilisateur : FRANÇAIS.
    - Base de données : ANGLAIS.
    
    🔥 INFO IMPORTANTE : Voici la liste des TAGS disponibles dans la base de recettes :
    [{tags_context_str}]
    
    UTILISATION DES TAGS :
    - Si l'utilisateur dit "Je suis Vegan", utilise le tag exact "Vegan" dans `search_recipes(query="Vegan")`.
    - Si l'utilisateur dit "Sans gluten", utilise "Gluten-Free".
    - Si l'utilisateur dit "Un truc léger", cherche des tags comme "Low-Carb" ou "Low-Fat".
    
    RÈGLES :
    1. Traduis toujours la recherche en Anglais.
    2. Si tu identifies un besoin alimentaire, utilise un des tags de la liste ci-dessus.
    3. Enchaîne les actions (Update profil -> Recherche -> Réponse).
    """

    tools_schema = [
        {"name": "get_health_profile", "description": "Profil utilisateur.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "update_profile", "description": "Maj Profil.", "parameters": {"type": "OBJECT", "properties": {"age": {"type": "INTEGER"}, "sexe": {"type": "STRING"}, "poids": {"type": "NUMBER"}, "taille": {"type": "INTEGER"}, "objectif": {"type": "STRING"}}}},
        {"name": "generate_planning", "description": "Genere planning.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "get_week_planning", "description": "Lit planning.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "update_planning_entry", "description": "Modifie repas.", "parameters": {"type": "OBJECT", "properties": {"id_planning": {"type": "INTEGER"}, "new_recette_id": {"type": "INTEGER"}}, "required": ["id_planning", "new_recette_id"]}},
        {"name": "update_planning_seance", "description": "Modifie seance.", "parameters": {"type": "OBJECT", "properties": {"id_planning": {"type": "INTEGER"}, "new_seance_id": {"type": "INTEGER"}}, "required": ["id_planning", "new_seance_id"]}},
        {"name": "search_recipes", "description": "Cherche recette (QUERY EN ANGLAIS ou TAG).", "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}},
        {"name": "get_catalog_exercises", "description": "Catalogue exos.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "get_exercises", "description": "Liste exos.", "parameters": {"type": "OBJECT", "properties": {}}}
    ]

    model = genai.GenerativeModel(model_name="models/gemini-3-flash-preview", tools=tools_schema, system_instruction=system_instruction)
    chat = model.start_chat(enable_automatic_function_calling=False)

    try:
        response = chat.send_message(user_message)
        
        for _ in range(5):
            if not response.candidates: return "Erreur API."
            
            part = response.candidates[0].content.parts[0]
            
            if part.function_call:
                fc = part.function_call
                name = fc.name
                args = {k: v for k, v in fc.args.items()}
                
                print(f"🤖 [IA] Appel outil : {name} {args}")
                
                if name in tools_map:
                    try:
                        res = tools_map[name](**args)
                    except Exception as tool_err:
                        res = {"erreur_interne": str(tool_err)}
                else:
                    res = {"erreur": "Outil inconnu"}
                
                print(f"✅ [API] Résultat : {str(res)[:150]}...") 
                
                response = chat.send_message(genai.protos.Part(function_response={"name": name, "response": res}))
                continue
            
            if part.text:
                return part.text
            
            return "Action effectuée."

        return "J'ai mis à jour les informations, mais je n'ai pas pu finaliser toute la demande."

    except Exception as e:
        print(f"❌ Erreur Chat : {e}")
        return "Une erreur technique est survenue."