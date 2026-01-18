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
    available_tags = rc.get_available_tags(db)
    tags_context_str = ", ".join(available_tags[:50]) 
    
    # =========================================================================
    # OUTILS
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

        # --- NORMALISATION INTELLIGENTE ---
        if sexe:
            s_clean = sexe.lower().strip()
            if s_clean in ['homme', 'h', 'masculin', 'male']: user.sexe = 'masculin'
            elif s_clean in ['femme', 'f', 'feminin', 'female']: user.sexe = 'feminin'

        if objectif:
            o_clean = objectif.lower().strip()
            # On standardise pour que l'IA ne pose pas de questions bêtes
            if any(x in o_clean for x in ['perdre', 'maigrir', 'mincir', 'gras', 'weight']):
                user.objectif = 'perte_poids'
            elif any(x in o_clean for x in ['muscl', 'masse', 'gros', 'gain']):
                user.objectif = 'prise_masse'
            elif any(x in o_clean for x in ['maintien', 'stabil', 'forme']):
                user.objectif = 'maintien'
            else:
                user.objectif = objectif # On garde le texte brut si on sait pas

        if age: user.age = age
        if poids: user.poids_kg = poids
        if taille: user.taille_cm = taille
        
        db.commit()
        db.refresh(user)
        
        # Update objet local
        current_user.age = user.age
        current_user.sexe = user.sexe
        current_user.poids_kg = user.poids_kg
        current_user.taille_cm = user.taille_cm
        current_user.objectif = user.objectif

        return {"status": "succes", "message": f"Profil mis à jour (Objectif: {user.objectif}). Je recalcule les besoins..."}

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

    def TOOL_search_recipes(query: str = ""):
        """
        Si query est vide, on cherche juste par calories.
        Si query est rempli, on cherche par mot clé/tag + calories.
        """
        # 1. Calcul des besoins caloriques pour un repas
        target_meal_calories = 600 
        user_context = "Standard"
        
        if all([current_user.poids_kg, current_user.taille_cm, current_user.age, current_user.sexe]):
             try:
                 bmr = calculate_bmr(current_user.poids_kg, current_user.taille_cm, current_user.age, current_user.sexe)
                 tdee = calculate_tdee(bmr, "sedentaire")
                 daily_target = calculate_target_calories(tdee, current_user.objectif or "maintien")
                 target_meal_calories = daily_target * 0.35
                 user_context = f"Cible repas : ~{int(target_meal_calories)} kcal"
             except: pass

        # 2. Récupération des candidats
        candidates = rc.get_all_recettes(db, limit=100, search=query if query else None)
        
        if not candidates: 
            return {"resultat": "Aucune recette trouvée."}

        # 3. Filtrage intelligent
        suitable = []
        min_cal = target_meal_calories - 200
        max_cal = target_meal_calories + 200

        for r in candidates:
            cal = r.calories or 0
            if min_cal <= cal <= max_cal:
                suitable.append(r)
        
        if not suitable: suitable = candidates

        random.shuffle(suitable)
        selected = suitable[:3] 

        return {
            "info_context": user_context,
            "recettes_trouvees": [
                {
                    "id": r.id_recette, 
                    "original_name_en": r.nom_recette, 
                    "tags": r.tags, 
                    "calories": r.calories, 
                    "desc_en": r.description
                } 
                for r in selected
            ],
            "instruction": "Traduis les titres en français. Ne pose pas de question."
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
    # SYSTEM PROMPT
    # =========================================================================
    
    system_instruction = f"""
    Tu es FitBot, le coach expert NutriFit.
    
    CONTEXTE TAGS DISPONIBLES : [{tags_context_str}]
    
    RÈGLES CRITIQUES :
    1. **TRADUCTION** : Traduis toujours les inputs utilisateur en Anglais pour la recherche, et les outputs recettes en Français.
    
    2. **ZÉRO FRICTION (IMPORTANT)** : 
       - Si l'utilisateur dit juste "Donne une recette", "J'ai faim" : Appelle `search_recipes(query="")`.
       - Si l'utilisateur donne un objectif (ex: "maigrir"), ACCEPTE-LE. **Ne demande jamais** "Quel est ton objectif de perte de poids ?". Considère que "maigrir" suffit.
    
    3. **TAGS** : Utilise les tags SEULEMENT si l'utilisateur demande une spécificité (ex: "Vegan"). Sinon, laisse faire le hasard.
    """

    tools_schema = [
        {"name": "get_health_profile", "description": "Profil utilisateur.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "update_profile", "description": "Maj Profil.", "parameters": {"type": "OBJECT", "properties": {"age": {"type": "INTEGER"}, "sexe": {"type": "STRING"}, "poids": {"type": "NUMBER"}, "taille": {"type": "INTEGER"}, "objectif": {"type": "STRING"}}}},
        {"name": "generate_planning", "description": "Genere planning.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "get_week_planning", "description": "Lit planning.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "update_planning_entry", "description": "Modifie repas.", "parameters": {"type": "OBJECT", "properties": {"id_planning": {"type": "INTEGER"}, "new_recette_id": {"type": "INTEGER"}}, "required": ["id_planning", "new_recette_id"]}},
        {"name": "update_planning_seance", "description": "Modifie seance.", "parameters": {"type": "OBJECT", "properties": {"id_planning": {"type": "INTEGER"}, "new_seance_id": {"type": "INTEGER"}}, "required": ["id_planning", "new_seance_id"]}},
        {"name": "search_recipes", "description": "Cherche recette. Laisser query VIDE pour une suggestion automatique.", "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}},
        {"name": "get_catalog_exercises", "description": "Catalogue exos.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "get_exercises", "description": "Liste exos.", "parameters": {"type": "OBJECT", "properties": {}}}
    ]

    model = genai.GenerativeModel(model_name="models/gemini-2.5-flash-lite", tools=tools_schema, system_instruction=system_instruction)
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

        return "Trop d'actions."

    except Exception as e:
        print(f"❌ Erreur Chat : {e}")
        return "Une erreur technique est survenue."