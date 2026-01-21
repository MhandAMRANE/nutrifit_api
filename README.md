# NutriFit API - Guide de démarrage

Ce guide explique comment installer, configurer et lancer l’API NutriFit sur votre machine, de la création de l’environnement virtuel à l’exécution complète du projet.

## 1. Prérequis
- Python 3.9 ou supérieur (recommandé : 3.9 ou 3.10)
- `pip` (installé avec Python)
- (Optionnel) `conda` si vous préférez un environnement conda
- MySQL (local ou distant, accès requis)

## 2. Cloner le projet
```bash
git clone <url-du-repo>
cd nutrifit_api
```

## 3. Créer un environnement virtuel
### Avec venv (recommandé)
```bash
python -m venv venv
```
Activez l’environnement :
- **Windows** :
  ```bash
  venv\Scripts\activate
  ```
- **Linux/Mac** :
  ```bash
  source venv/bin/activate
  ```

### Avec conda (optionnel)
```bash
conda create -n nutrifit python=3.9
conda activate nutrifit
```

## 4. Installer les dépendances
```bash
pip install -r requirements.txt
```
(Si le fichier s’appelle `requierment.txt`, renommez-le en `requirements.txt`)

## 5. Configurer les variables d’environnement
Créez un fichier `.env` à la racine du projet avec ce contenu (adaptez selon vos accès) :
```dotenv
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=3306
DB_NAME=nutrifit
DB_USE_SSL=false


# SSH Tunnel Configuration
SSH_HOST=your_ssh_host
SSH_USER= your_ssh_user
SSH_PASSWORD=your_ssh_password
SSH_PORT=22
USE_SSH_TUNNEL=true
GEMINI_API_KEY=your_GEMINI_API_KEY

## 6. Préparer la base de données
- Créez la base de données MySQL si elle n’existe pas :
  ```sql
  CREATE DATABASE nutrifit;
  ```
- Vérifiez que l’utilisateur a les droits sur cette base.

## 7. Lancer l’API
```bash
uvicorn main:app --reload
```
L’API sera accessible sur http://127.0.0.1:8000/nutrifit-api

## 8. Tester la connexion à la base
Vous pouvez utiliser le script :
```bash
python test_db_connection.py
```

## 9. Utilisation
- Documentation interactive : http://127.0.0.1:8000/nutrifit-api/docs
- Testez les endpoints via Swagger UI ou Postman.

## 10. Dépannage
- Si un module manque :
  ```bash
  pip install <nom-du-module>
  ```
- Si la connexion MySQL échoue, vérifiez le `.env` et l’accessibilité réseau.

---

**Contact** : [Votre nom/email]