
import sys
import os

print("--- TENTATIVE D'IMPORT DE L'APPLICATION ---")

try:
    # On ajoute le dossier courant au path pour simuler le lancement depuis la racine
    sys.path.append(os.getcwd())
    
    import main
    print("✅ Succès : 'import main' a fonctionné sans erreur.")
    print(f"App object: {main.app}")
except Exception as e:
    print("❌ ECHEC : L'application a planté lors de l'import.")
    print(f"Erreur : {e}")
    import traceback
    traceback.print_exc()
