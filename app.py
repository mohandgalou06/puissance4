import os
import json
from flask import Flask, jsonify, render_template, request
from database import Database
from ai import IA_Tournoi
from constants import JAUNE, ROUGE, SAVE_DIR
from game_logic import GameLogic

BOARD_SIZE = 9

app = Flask(__name__)
app.secret_key = "clef_secrete_super_puissance4_bga"
db_site = Database()

# Fonctions utilitaires pour la structure des données
def grille_vide():
    return [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def copier_grille(grille):
    return [ligne[:] for ligne in grille]

# --- SYSTÈME DE GESTION DES SESSIONS PAR FICHIER (Isolation des onglets) ---

def initialiser_session(tab_id):
    """Crée le dossier de sauvegarde et le fichier de session s'ils n'existent pas."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    chemin = os.path.join(SAVE_DIR, f"{tab_id}.json")
    if not os.path.exists(chemin):
        with open(chemin, 'w') as f:
            json.dump({"grille": grille_vide(), "historique": []}, f)

def charger_partie(tab_id):
    """Charge l'état du jeu depuis le fichier correspondant au tab_id."""
    initialiser_session(tab_id)
    chemin = os.path.join(SAVE_DIR, f"{tab_id}.json")
    with open(chemin, 'r') as f:
        data = json.load(f)
    
    logic = GameLogic()
    logic.grille = copier_grille(data["grille"])
    # On s'assure que l'historique est une liste de listes
    historique = [list(coup) for coup in data.get("historique", [])]
    return logic, historique

def sauvegarder_partie(tab_id, logic, historique):
    """Enregistre l'état actuel dans le fichier JSON du tab_id."""
    chemin = os.path.join(SAVE_DIR, f"{tab_id}.json")
    with open(chemin, 'w') as f:
        json.dump({
            "grille": copier_grille(logic.grille), 
            "historique": historique
        }, f)

def sauvegarder_en_bdd_si_finie(vainqueur, historique):
    if not vainqueur or not historique:
        return False, "Partie non terminee."

    return db_site.sauvegarder(
        vainqueur,
        historique,
        confiance=3,
        nb_colonnes=BOARD_SIZE
    )

def prochain_joueur(historique):
    """Détermine qui doit jouer selon l'historique des coups."""
    return JAUNE if len(historique) % 2 != 0 else ROUGE

def construire_reponse(logic, historique, vainqueur=None, winner_color=None, winner_type=None, winning_cells=None, message_ia="", status="ok",best_move=None):
    """Prépare le dictionnaire JSON de réponse pour le client."""
    return jsonify({
        "status": status,
        "grille": logic.grille,
        "historique": historique,
        "vainqueur": vainqueur,
        "winner_color": winner_color,
        "winner_type": winner_type,
        "winning_cells": winning_cells,
        "message_ia": message_ia,
        "au_tour_de": prochain_joueur(historique),
        "best_move": best_move
    })

# --- ROUTES FLASK ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reset", methods=["POST"])
def reset():
    """Réinitialise la partie pour un onglet spécifique sans recharger la page."""
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    
    logic = GameLogic()
    historique = []
    sauvegarder_partie(tab_id, logic, historique)
    
    return construire_reponse(logic, historique)

@app.route("/undo", methods=["POST"])
def undo():
    """Annule le dernier coup joué."""
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    
    logic, historique = charger_partie(tab_id)
    if historique:
        historique.pop()
        # On reconstruit la grille à partir de l'historique restant
        nouvelle_grille = grille_vide()
        temp_logic = GameLogic()
        temp_logic.grille = nouvelle_grille
        for l, c, j in historique:
            temp_logic.grille[l][c] = j
        logic.grille = temp_logic.grille
        sauvegarder_partie(tab_id, logic, historique)
        
    return construire_reponse(logic, historique)

@app.route("/paint", methods=["POST"])
def paint():
    """Permet de modifier la grille manuellement sans perdre l'historique précédent."""
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    r, c, couleur = data.get("row"), data.get("col"), data.get("color")

    logic, historique = charger_partie(tab_id)

    if r is not None and c is not None:
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            logic.grille[r][c] = couleur

    sauvegarder_partie(tab_id, logic, historique)
    return construire_reponse(logic, historique)

@app.route("/play", methods=["POST"])
def play():
    """Gère un coup joué par un humain, par l'IA, ou une analyse non destructive."""
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    action = data.get("action")

    logic, historique = charger_partie(tab_id)

    couleur_forcee = data.get("color")
    try:
        couleur_forcee = int(couleur_forcee) if couleur_forcee is not None else None
    except (TypeError, ValueError):
        couleur_forcee = None

    joueur_actuel = prochain_joueur(historique)

    # En mode analyse, on respecte la couleur choisie côté front si elle est fournie
    if action == "analyze" and couleur_forcee in (ROUGE, JAUNE):
        joueur_actuel = couleur_forcee

    nom_joueur = "Rouge" if joueur_actuel == ROUGE else "Jaune"

    vainqueur = None
    winner_color = None
    winner_type = None
    winning_cells = None
    message_ia = ""

    # -------------------------------------------------
    # 1) Coup humain
    # -------------------------------------------------
    if action == "human":
        col = data.get("colonne")

        if col is None or not logic.colonne_valide(col):
            return construire_reponse(logic, historique, status="error")

        l = logic.placer_pion(col, joueur_actuel)
        historique.append([l, col, joueur_actuel])

        if logic.victoire(joueur_actuel):
            vainqueur = nom_joueur
            winner_color = joueur_actuel
            winner_type = "human"
            winning_cells = [list(pos) for pos in logic.aligne]
        elif logic.grille_pleine():
            vainqueur = "Nul"
            winner_type = "draw"
        if vainqueur:
            ok_bdd, msg_bdd = sauvegarder_en_bdd_si_finie(vainqueur, historique)
            print(f"[BDD SITE] {ok_bdd} - {msg_bdd}")

        sauvegarder_partie(tab_id, logic, historique)
        return construire_reponse(
            logic, historique,
            vainqueur=vainqueur,
            winner_color=winner_color,
            winner_type=winner_type,
            winning_cells=winning_cells,
            message_ia=message_ia
        )

    # -------------------------------------------------
    # 2) Analyse NON destructive
    # -------------------------------------------------
    elif action == "analyze":
        budget_client = float(data.get("budget", 14.0))

        ia_terminator = IA_Tournoi()
        ia_terminator.budget_secondes = budget_client
        ia_terminator.max_profondeur = 25

        best_move = ia_terminator.jouer_coup(logic, historique, joueur_actuel, tab_id=tab_id)
        message_ia = getattr(ia_terminator, "dernier_message", "")

        return construire_reponse(
            logic, historique,
            message_ia=message_ia,
            status="ok",
            best_move=best_move
        )

    # -------------------------------------------------
    # 3) Coup IA réel
    # -------------------------------------------------
    elif action == "ia":
        budget_client = float(data.get("budget", 14.0))

        ia_terminator = IA_Tournoi()
        ia_terminator.budget_secondes = budget_client
        ia_terminator.max_profondeur = 17

        col_ia = ia_terminator.jouer_coup(logic, historique, joueur_actuel, tab_id=tab_id)
        message_ia = getattr(ia_terminator, "dernier_message", "")

        if col_ia is None or not logic.colonne_valide(col_ia):
            return construire_reponse(logic, historique, message_ia=message_ia, status="invalid")

        l = logic.placer_pion(col_ia, joueur_actuel)
        historique.append([l, col_ia, joueur_actuel])

        if logic.victoire(joueur_actuel):
            vainqueur = nom_joueur
            winner_color = joueur_actuel
            winner_type = "ia"
            winning_cells = [list(pos) for pos in logic.aligne]
        elif logic.grille_pleine():
            vainqueur = "Nul"
            winner_type = "draw"
        if vainqueur:
            ok_bdd, msg_bdd = sauvegarder_en_bdd_si_finie(vainqueur, historique)
            print(f"[BDD SITE] {ok_bdd} - {msg_bdd}")

        sauvegarder_partie(tab_id, logic, historique)
        return construire_reponse(
            logic, historique,
            vainqueur=vainqueur,
            winner_color=winner_color,
            winner_type=winner_type,
            winning_cells=winning_cells,
            message_ia=message_ia
        )

    # -------------------------------------------------
    # 4) Récupération simple de la grille courante
    # -------------------------------------------------
    elif action == "get_grid":
        return construire_reponse(logic, historique, status="ok")

    # -------------------------------------------------
    # 5) Action inconnue
    # -------------------------------------------------
    return construire_reponse(logic, historique, status="error")

@app.route("/ai_status", methods=["POST"])
def ai_status():
    """Route appelée par le navigateur pour lire la profondeur de l'IA en direct."""
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    chemin = os.path.join(SAVE_DIR, f"{tab_id}_status.json")
    
    try:
        if os.path.exists(chemin):
            with open(chemin, 'r') as f:
                return jsonify(json.load(f))
    except:
        pass
    
    return jsonify({"depth": 0})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
