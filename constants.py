import json
import os

# Valeurs par défaut
LIGNES = 8
COLONNES = 9
COULEUR_DEPART = 1 # 1 = ROUGE, 2 = JAUNE

# Chargement de la configuration
if os.path.exists("config.json"):
    try:
        with open("config.json", "r") as f:
            data = json.load(f)
            LIGNES = data.get("lignes", 8)
            COLONNES = data.get("colonnes", 9)
            COULEUR_DEPART = data.get("couleur_depart", 1)
    except Exception as e:
        print("Erreur de lecture config:", e)

VIDE = 0
ROUGE = 1   # Joueur 1
JAUNE = 2   # Joueur 2 ou IA

TAILLE_CASE = 60
RAYON_PION = 25

SAVE_DIR = "sauvegardes/"