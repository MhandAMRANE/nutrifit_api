# nutrifit_api/utils/health_formulas.py

def calculate_bmr(poids: float, taille: int, age: int, sexe: str) -> int:
    """
    Mifflin-St Jeor : Calcul du métabolisme de base.
    """
    if not all([poids, taille, age, sexe]):
        return 0

    bmr = (10 * poids) + (6.25 * taille) - (5 * age)
    
    s = sexe.lower().strip()
    if s in ['h', 'homme', 'm', 'masculin']:
        bmr += 5
    elif s in ['f', 'femme', 'female', 'feminin']:
        bmr -= 161
    else:
        bmr -= 78 
    return int(bmr)

def calculate_tdee(bmr: int, niveau_activite: str) -> int:
    """
    Applique le multiplicateur d'activité (PAL).
    """
    if not niveau_activite:
        return int(bmr * 1.2)

    act = niveau_activite.lower().strip()
    
    # Mapping précis fréquence -> multiplicateur
    if "sedentaire" in act: # 0 sport
        return int(bmr * 1.2)
    elif "leger" in act:    # 1-3 fois
        return int(bmr * 1.375)
    elif "modere" in act:   # 3-5 fois
        return int(bmr * 1.55)
    elif "tres" in act or "actif" in act: # 6-7 fois (gestion simple pour 'actif' et 'tres_actif')
        if "tres" in act:
             return int(bmr * 1.9)
        return int(bmr * 1.725)
    
    return int(bmr * 1.2)

def calculate_target_calories(tdee: int, objectif: str) -> int:
    if not objectif:
        return tdee
    
    obj = objectif.lower()
    if "perte" in obj or "seche" in obj:
        return tdee - 500
    elif "prise" in obj or "masse" in obj:
        return tdee + 300
    return tdee