#!/usr/bin/env python3
import subprocess
import sys
import time
import os

os.chdir(r"c:\Users\Etudiant\Desktop\nutrifit_api")

# Lancer le serveur
print("Démarrage du serveur...")
proc = subprocess.Popen([
    r".venv\Scripts\python.exe",
    "-m", "uvicorn",
    "main:app",
    "--host", "127.0.0.1",
    "--port", "8000"
])

# Garder le processus vivant
try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
    proc.wait()
