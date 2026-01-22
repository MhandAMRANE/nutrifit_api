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
    
    poids = float(current_user.poids_kg) if current_user.poids_kg else None
    taille = float(current_user.taille_cm) if current_user.taille_cm else 175.0 # Valeur par défaut pour éviter crash
    age = current_user.age
    sexe = current_user.sexe
    objectif = current_user.objectif or "maintien"

    # B. Calcul automatique des besoins (BMR / TDEE / Cible)
    info_calorique = "Données insuffisantes pour calculer les besoins."
    if poids and age and sexe:
        try:
            bmr = calculate_bmr(poids, taille, age, sexe)
            tdee = calculate_tdee(bmr, "sedentaire") # On part sur sédentaire par défaut pour sécuriser
            cible_journaliere = calculate_target_calories(tdee, objectif)
            
            info_calorique = (
                f"Métabolisme de base (BMR): {int(bmr)} kcal | "
                f"Dépense totale (TDEE): {int(tdee)} kcal | "
                f"🎯 CIBLE JOURNALIÈRE À VISER: {int(cible_journaliere)} kcal"
            )
        except Exception as e:
            print(f"Erreur calcul: {e}")

    # C. Construction de la liste
    profile_parts = [
        f"Prénom: {current_user.prenom or 'Athlète'}",
        f"Age: {age} ans" if age else None,
        f"Poids: {poids} kg" if poids else None,
        f"Sexe: {sexe or 'Non précisé'}",
        f"OBJECTIF: {objectif}",
        f"📊 ANALYSE CALORIQUE PRÉ-CALCULÉE : [{info_calorique}]" # <--- C'est ça qui change tout !
    ]

    if hasattr(current_user, 'regime_alimentaire') and current_user.regime_alimentaire:
        profile_parts.append(f"Régime Alimentaire: {current_user.regime_alimentaire}")
    
    if hasattr(current_user, 'equipements') and current_user.equipements:
        profile_parts.append(f"Matériel disponible: {current_user.equipements}")
    else:
        profile_parts.append("Matériel: Poids du corps uniquement (par défaut)")

    if hasattr(current_user, 'nb_jours_entrainement') and current_user.nb_jours_entrainement:
        profile_parts.append(f"Fréquence entraînement: {current_user.nb_jours_entrainement} jours/semaine")

    user_info_str = " | ".join([p for p in profile_parts if p is not None])

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
        
        poids = float(current_user.poids_kg)
        taille = float(current_user.taille_cm)
        
        bmr = calculate_bmr(poids, taille, current_user.age, current_user.sexe)
        tdee = calculate_tdee(bmr, "sedentaire")
        target = calculate_target_calories(tdee, current_user.objectif or "maintien")
        
        return {
            "profil": {"nom": current_user.prenom, "objectif": current_user.objectif},
            "analyse": {"bmr": bmr, "tdee": tdee, "cible_calorique_jour": target}
        }

    def TOOL_create_custom_workout(duration_min: int = 45, intensity: str = "medium", focus: str = "full_body", material: str = "poids_du_corps"):
        """
        Crée une séance sur mesure en piochant dans la BDD.
        - intensity: 'low' (récupération), 'medium', 'high' (HIIT/Force)
        - focus: 'full_body', 'legs' (jambes), 'upper' (haut), 'cardio', 'abs'
        - material: 'poids_du_corps', 'materiel_maison', 'salle_de_sport'
        """
        
        allowed_materials = ["poids_du_corps"]
        if material == "materiel_maison":
            allowed_materials.append("materiel_maison")
        elif material == "salle_de_sport":
            allowed_materials.extend(["materiel_maison", "salle_de_sport"])
            
        
        all_exos = db.query(Exercice).filter(Exercice.materiel.in_(allowed_materials)).all()
        candidates = []

        keywords_map = {
            "legs": ["quadriceps", "ischios", "mollets", "fessiers", "jambes"],
            "upper": ["pectoraux", "dos", "epaules", "biceps", "triceps"],
            "abs": ["abdominaux", "obliques", "core"],
            "cardio": ["cardio", "full_body"]
        }
        
        target_muscles = keywords_map.get(focus, [])
        
        for exo in all_exos:
            
            if focus == "full_body":
                if exo.type_exercice in ["force", "cardio", "gainage"]:
                    candidates.append(exo)
            
            else:
                
                if any(m in target_muscles for m in exo.muscle_cible):
                    candidates.append(exo)

        if not candidates:
            return {"erreur": f"Pas assez d'exercices trouvés pour {focus} avec {material}."}

        
        nb_exos = max(3, duration_min // 5)
        
        if intensity == "low": nb_exos = max(3, nb_exos - 2)
        if intensity == "high": nb_exos += 2

        random.shuffle(candidates)
        selected_exos = candidates[:nb_exos]

        return {
            "seance_generee": {
                "objectif": f"{focus.upper()} ({duration_min} min - {intensity})",
                "exercices": [
                    {"nom": e.nom_exercice, "type": e.type_exercice, "muscles": e.muscle_cible, "materiel": e.materiel}
                    for e in selected_exos
                ],
                "conseil_coach": f"Fais 3 à 4 séries de chaque. {'Temps de repos longs (2min)' if intensity == 'high' else 'Repos courts (45s)'}."
            }
        }

    def TOOL_update_profile(age: int = None, sexe: str = None, poids: float = None, taille: int = None, objectif: str = None):
        user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == current_user.id_utilisateur).first()
        if not user: return {"erreur": "Utilisateur introuvable."}

        if sexe:
            s_clean = sexe.lower().strip()
            if s_clean in ['homme', 'h', 'masculin', 'male']: user.sexe = 'masculin'
            elif s_clean in ['femme', 'f', 'feminin', 'female']: user.sexe = 'feminin'

        if objectif:
            o_clean = objectif.lower().strip()
            
            if any(x in o_clean for x in ['perdre', 'maigrir', 'mincir', 'gras', 'weight']):
                user.objectif = 'perte_poids'
            elif any(x in o_clean for x in ['muscl', 'masse', 'gros', 'gain']):
                user.objectif = 'prise_masse'
            elif any(x in o_clean for x in ['maintien', 'stabil', 'forme']):
                user.objectif = 'maintien'
            else:
                user.objectif = objectif 

        if age: user.age = age
        if poids: user.poids_kg = poids
        if taille: user.taille_cm = taille
        
        db.commit()
        db.refresh(user)
        
        current_user.age = user.age
        current_user.sexe = user.sexe
        current_user.poids_kg = user.poids_kg
        current_user.taille_cm = user.taille_cm
        current_user.objectif = user.objectif

        return {"status": "succes", "message": f"Profil mis à jour (Objectif: {user.objectif}). Je recalcule les besoins..."}

    def TOOL_generate_planning(focus: str = "complet"):
        """
        Génère le planning. 
        focus: 'complet' (par défaut), 'alimentation' (repas seuls), 'sport' (séances seules).
        """
        do_meals = True
        do_sport = True
        
        if focus == "alimentation":
            do_sport = False
        elif focus == "sport":
            do_meals = False
            
        return pc.generate_weekly_plan(
            db, 
            current_user.id_utilisateur, 
            datetime.now(), 
            include_meals=do_meals, 
            include_sport=do_sport
        )

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
        target_meal_calories = 600 
        user_context = "Standard"
        
        if all([current_user.poids_kg, current_user.taille_cm, current_user.age, current_user.sexe]):
             try:
                 poids = float(current_user.poids_kg)
                 taille = float(current_user.taille_cm)
                 
                 bmr = calculate_bmr(poids, taille, current_user.age, current_user.sexe)
                 tdee = calculate_tdee(bmr, "sedentaire")
                 daily_target = calculate_target_calories(tdee, current_user.objectif or "maintien")
                 target_meal_calories = daily_target * 0.35
                 user_context = f"Cible repas : ~{int(target_meal_calories)} kcal"
             except: pass

        
        candidates = rc.get_all_recettes(db, limit=100, search=query if query else None)
        
        if not candidates: 
            return {"resultat": "Aucune recette trouvée."}

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
        "get_exercises": TOOL_get_exercises,
        "create_custom_workout": TOOL_create_custom_workout
    }

    # =========================================================================
    # SYSTEM PROMPT
    # =========================================================================
    
    system_instruction = f"""
    Tu es FitBot, le coach sportif et nutritionnel expert de l'application NutriFit.
    
    ===========================================================================
    📋 **CONTEXTE UTILISATEUR (PRIORITÉ ABSOLUE)**
    ===========================================================================
    Voici la "Carte d'Identité" de l'utilisateur actuel. Utilise ces infos pour adapter tes réponses SANS poser de questions :
    [{user_info_str}]
    
    *Règles d'interprétation du profil :*
    - Si l'objectif est "Perte de poids" -> Propose automatiquement des recettes hypocaloriques et des séances brûle-graisse.
    - Si "Matériel" est vide -> Considère "Poids du corps". Sinon, utilise le matériel listé.
    - Si "Régime" est précisé (ex: Vegan) -> Vérifie STRICTEMENT que les recettes respectent ce régime.

    ===========================================================================
    ⛔ **RÈGLES TECHNIQUES & COMPORTEMENTALES (ANTI-BUG)**
    ===========================================================================
    1. **INTERDICTION FORMELLE DE CODER** : Ne renvoie JAMAIS de code Python, de `print()`, de `tool_code` ou de JSON brut. Tu n'es pas un interpréteur, tu es un coach.
    2. **UTILISATION DES OUTILS** : Pour toute demande (Recette, Sport, Planning), tu DOIS appeler la fonction native correspondante (`function_call`). Ne décris pas l'action, FAIS-LA.
    3. **SILENCE RADIO** : Ne dis JAMAIS "Je cherche...", "Un instant...", "Laisse-moi regarder". Agis silencieusement et n'affiche QUE le résultat final utile.

    ===========================================================================
    🥗 **INTELLIGENCE NUTRITION (RECETTES & CONSEILS)**
    ===========================================================================
    1. **CONSEILS & ANALYSE (Priorité si question)** :
       - Si l'utilisateur demande un avis ("C'est trop 700kcal ?", "Je mange quoi avant le sport ?"), **NE CHERCHE PAS DE RECETTE**.
       - Réponds en utilisant ton expertise et les données de la "Carte d'Identité" (Cible journalière, Objectif).
       - Ex: "700 kcal c'est environ 35%% de votre cible (2000), c'est un gros repas mais acceptable si..."
    
    2. **RECHERCHE DE RECETTES (Seulement si demandé)** :
       - Si demande explicite de plat/repas ("J'ai faim", "Idée repas", "recette poulet") -> Appelle `search_recipes`.
       - **Demande vague** -> Appelle `search_recipes(query="")`.
       - **Demande précise** -> Appelle `search_recipes(query="anglais")`.

    **FORMAT DE RÉPONSE RECETTES (Uniquement pour search_recipes) :**
    "🍽️ **[Nom de la recette en Français]** (~[Calories] kcal)
    [Une phrase courte et appétissante qui décrit le plat]. [Mention spéciale SI régime spécifique, ex: "100% Vegan"]."
    *(Ne liste PAS les tags techniques type "sans arachide, sans soja" sauf si c'est pertinent pour le profil).*

    ===========================================================================
    🏋️‍♂️ **INTELLIGENCE SPORTIVE (SÉANCES & PLANNING)**
    ===========================================================================
    - **Création de séance** :
      - Analyse l'état de l'utilisateur : "Je suis fatigué" -> `intensity="low"`. "J'ai peu de temps" -> `duration_min=20`.
      - Vérifie le matériel dispo dans le profil pour remplir l'argument `material`.
    
    - **Consultation Planning** :
      - Si l'utilisateur demande "C'est quoi mon programme ?", appelle `get_week_planning`.
      - Si l'utilisateur demande une séance alors qu'il a déjà fait les jambes hier (visible dans le planning), propose le haut du corps.

    **FORMAT DE RÉPONSE OBLIGATOIRE :**
    "💪 **Séance : [Nom/Focus]** ([Durée])
    1. **[Exercice 1]** : [Courte instruction ou répétitions]
    2. **[Exercice 2]** : ..."
    
    *Adaptation :* Si un exercice semble dur, tu peux ajouter : "Si c'est trop difficile, fais [Variante simple, ex: sur les genoux]." (Mais n'invente pas d'exercices qui n'existent pas).

    ===========================================================================
    Ton objectif : Être un coach efficace, direct et motivant. Pas de blabla technique, juste des résultats.
    """

    tools_schema = [
        {"name": "get_health_profile", "description": "Profil utilisateur.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "update_profile", "description": "Maj Profil.", "parameters": {"type": "OBJECT", "properties": {"age": {"type": "INTEGER"}, "sexe": {"type": "STRING"}, "poids": {"type": "NUMBER"}, "taille": {"type": "INTEGER"}, "objectif": {"type": "STRING"}}}},
        {
            "name": "generate_planning", 
            "description": "Génère un planning hebdo. Paramètre 'focus' pour choisir.", 
            "parameters": {
                "type": "OBJECT", 
                "properties": {
                    "focus": {
                        "type": "STRING", 
                        "description": "Ce qu'il faut générer : 'complet', 'alimentation' ou 'sport'."
                    }
                }
            }
        },
        {"name": "get_week_planning", "description": "Lit planning.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "update_planning_entry", "description": "Modifie repas.", "parameters": {"type": "OBJECT", "properties": {"id_planning": {"type": "INTEGER"}, "new_recette_id": {"type": "INTEGER"}}, "required": ["id_planning", "new_recette_id"]}},
        {"name": "update_planning_seance", "description": "Modifie seance.", "parameters": {"type": "OBJECT", "properties": {"id_planning": {"type": "INTEGER"}, "new_seance_id": {"type": "INTEGER"}}, "required": ["id_planning", "new_seance_id"]}},
        {"name": "search_recipes", "description": "Cherche recette. Laisser query VIDE pour une suggestion automatique.", "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}},
        {"name": "get_catalog_exercises", "description": "Catalogue exos.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "get_exercises", "description": "Liste exos.", "parameters": {"type": "OBJECT", "properties": {}}},
        {"name": "create_custom_workout","description": "Génère une séance de sport unique et immédiate.","parameters": {"type": "OBJECT","properties": {"duration_min": {"type": "INTEGER", "description": "Durée en minutes (ex: 30, 60)."},"intensity": {"type": "STRING", "description": "'low' (fatigué), 'medium', 'high' (en forme)."},"focus": {"type": "STRING", "description": "'full_body', 'legs', 'upper', 'abs', 'cardio'."},"material": {"type": "STRING", "description": "'poids_du_corps', 'materiel_maison', 'salle_de_sport'."}}}}
    ]





    # Configuration de la sécurité pour éviter les blocages injustifiés
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    model = genai.GenerativeModel(
        model_name="models/gemini-2.5-flash", 
        tools=tools_schema, 
        system_instruction=system_instruction,
        safety_settings=safety_settings
    )
    chat = model.start_chat(enable_automatic_function_calling=False)

    try:
        response = chat.send_message(user_message)
        
        for _ in range(5):
            if not response.candidates: return "Erreur API."
            
            # Protection contre les réponses vides (bug connu Gemini ou Filtre de sécurité)
            if not response.candidates[0].content.parts:
                print(f"⚠️ [IA] Réponse vide reçue. Debug Candidate: {response.candidates[0]}")
                
                # Si bloqué par la sécurité, on le dit
                if response.candidates[0].finish_reason == 3: # 3 = SAFETY
                    return "Je ne peux pas répondre pour des raisons de sécurité (filtre déclenché)."
                
                return "Je n'ai pas réussi à formuler une réponse (Réponse vide du modèle)."

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