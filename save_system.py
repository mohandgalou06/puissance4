import json
import os
from constants import SAVE_DIR

os.makedirs(SAVE_DIR, exist_ok=True)

def liste_sauvegardes():
    
    if not os.path.exists(SAVE_DIR):
        return []
    fichiers = [f[:-5] for f in os.listdir(SAVE_DIR) if f.endswith('.json')]
    return sorted(fichiers)

def sauvegarder_partie(nom_partie, etat_partie):
   
    chemin = os.path.join(SAVE_DIR, f"{nom_partie}.json")
    try:
        with open(chemin, 'w') as f:
            json.dump(etat_partie, f)
        return True
    except Exception:
        return False

def charger_partie(nom_partie):
    
    chemin = os.path.join(SAVE_DIR, f"{nom_partie}.json")
    try:
        with open(chemin, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def supprimer_partie(nom_partie):
    
    chemin = os.path.join(SAVE_DIR, f"{nom_partie}.json")
    try:
        os.remove(chemin)
        return True
    except FileNotFoundError:
        return False
