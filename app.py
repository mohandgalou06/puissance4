from flask import Flask, jsonify, render_template, request

from ai import IA_Tournoi
from constants import JAUNE, ROUGE
from game_logic import GameLogic

BOARD_SIZE = 9

app = Flask(__name__)
app.secret_key = "clef_secrete_super_puissance4_bga"

ia_terminator = IA_Tournoi()

# 🔥 LE SECRET : Un dictionnaire qui stocke les parties par onglet
TAB_SESSIONS = {}

def grille_vide():
    return [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def copier_grille(grille):
    return [ligne[:] for ligne in grille]

def initialiser_session(tab_id):
    if tab_id not in TAB_SESSIONS:
        TAB_SESSIONS[tab_id] = {
            "grille": grille_vide(),
            "historique": []
        }

def charger_partie(tab_id):
    initialiser_session(tab_id)
    logic = GameLogic()
    logic.grille = copier_grille(TAB_SESSIONS[tab_id]["grille"])
    historique = [list(coup) for coup in TAB_SESSIONS[tab_id].get("historique", [])]
    return logic, historique

def sauvegarder_partie(tab_id, logic, historique):
    TAB_SESSIONS[tab_id]["grille"] = copier_grille(logic.grille)
    TAB_SESSIONS[tab_id]["historique"] = [list(coup) for coup in historique]

def prochain_joueur(historique):
    return ROUGE if len(historique) % 2 == 0 else JAUNE

def normaliser_couleur(couleur, historique):
    if couleur in (ROUGE, "rouge", "1", 1):
        return ROUGE
    if couleur in (JAUNE, "jaune", "2", 2):
        return JAUNE
    return prochain_joueur(historique)

def couleur_label(couleur):
    if couleur == ROUGE:
        return "rouge"
    if couleur == JAUNE:
        return "jaune"
    return None

def nom_couleur(couleur):
    return "Rouge" if couleur == ROUGE else "Jaune"

def construire_reponse(
    logic,
    historique,
    vainqueur=None,
    winner_color=None,
    winner_type=None,
    winning_cells=None,
    message_ia="",
    played=False,
    status="ok",
):
    if winning_cells is None:
        winning_cells = []

    return jsonify(
        {
            "status": status,
            "grille": logic.grille,
            "historique_len": len(historique),
            "played": played,
            "partie_terminee": winner_type is not None,
            "next_color": None if winner_type is not None else couleur_label(prochain_joueur(historique)),
            "vainqueur": vainqueur,
            "winner_color": couleur_label(winner_color),
            "winner_type": winner_type,
            "winning_cells": winning_cells,
            "message_ia": message_ia,
        }
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status_ia", methods=["GET"])
def status_ia():
    import generateur_tournoi
    return jsonify({"profondeur": generateur_tournoi.CURRENT_DEPTH})

@app.route("/reset", methods=["POST"])
def reset():
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    
    TAB_SESSIONS[tab_id] = {
        "grille": grille_vide(),
        "historique": []
    }
    return jsonify({"status": "ok", "grille": grille_vide(), "next_color": "rouge"})

@app.route("/paint", methods=["POST"])
def paint():
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    r, c, couleur = data.get("row"), data.get("col"), data.get("color")

    logic, _ = charger_partie(tab_id)

    if r is not None and c is not None and 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
        logic.grille[r][c] = couleur

    sauvegarder_partie(tab_id, logic, [])
    return jsonify({"status": "ok", "grille": logic.grille})

@app.route("/undo", methods=["POST"])
def undo():
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    steps = int(data.get("steps", 2))
    steps = max(1, steps)

    _, historique = charger_partie(tab_id)
    historique = historique[: max(0, len(historique) - steps)]

    logic = GameLogic()
    logic.grille = grille_vide()
    for l, c, j in historique:
        logic.grille[l][c] = j

    sauvegarder_partie(tab_id, logic, historique)
    return construire_reponse(logic, historique)

@app.route("/abandon", methods=["POST"])
def abandon():
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    mode = data.get("mode", "pvia")
    logic, historique = charger_partie(tab_id)

    joueur_abandon = normaliser_couleur(data.get("color"), historique)
    human_color = normaliser_couleur(data.get("human_color"), historique)
    winner_color = JAUNE if joueur_abandon == ROUGE else ROUGE

    if mode == "pvp":
        winner_type = "human"
    elif mode == "iavia":
        winner_type = "ia"
    else:
        winner_type = "human" if winner_color == human_color else "ia"

    return construire_reponse(
        logic,
        historique,
        vainqueur=nom_couleur(winner_color),
        winner_color=winner_color,
        winner_type=winner_type,
        message_ia="Abandon enregistré.",
    )

@app.route("/play", methods=["POST"])
def play():
    data = request.get_json(silent=True) or {}
    tab_id = data.get("tab_id", "default")
    colonne = data.get("colonne")
    action = data.get("action")

    logic, historique = charger_partie(tab_id)

    message_ia = ""
    vainqueur = None
    winner_color = None
    winner_type = None
    winning_cells = []
    played = False

    joueur_actuel = normaliser_couleur(data.get("color"), historique)
    nom_joueur = nom_couleur(joueur_actuel)

    if action == "get_grid":
        return construire_reponse(logic, historique)

    if action == "analyze":
        ia_terminator.budget_secondes = 14.0
        ia_terminator.max_profondeur = 20
        ia_terminator.jouer_coup(logic, historique, joueur_actuel)
        message_ia = getattr(ia_terminator, "dernier_message", "Analyse terminee.")
        return construire_reponse(logic, historique, message_ia=message_ia)

    if action == "human":
        if colonne is None or not logic.colonne_valide(colonne):
            return construire_reponse(logic, historique, message_ia="Colonne invalide.", status="invalid")

        l = logic.placer_pion(colonne, joueur_actuel)
        historique.append([l, colonne, joueur_actuel])
        played = True

        if logic.victoire(joueur_actuel):
            vainqueur = nom_joueur
            winner_color = joueur_actuel
            winner_type = "human"
            winning_cells = [list(position) for position in logic.aligne]
        elif logic.grille_pleine():
            vainqueur = "Nul"
            winner_type = "draw"

    elif action == "ia":
        ia_terminator.budget_secondes = 14.0
        ia_terminator.max_profondeur = 17

        col_ia = ia_terminator.jouer_coup(logic, historique, joueur_actuel)
        message_ia = getattr(ia_terminator, "dernier_message", "")

        if col_ia is None or not logic.colonne_valide(col_ia):
            return construire_reponse(logic, historique, message_ia=message_ia, status="invalid")

        l = logic.placer_pion(col_ia, joueur_actuel)
        historique.append([l, col_ia, joueur_actuel])
        played = True

        if logic.victoire(joueur_actuel):
            vainqueur = nom_joueur
            winner_color = joueur_actuel
            winner_type = "ia"
            winning_cells = [list(position) for position in logic.aligne]
        elif logic.grille_pleine():
            vainqueur = "Nul"
            winner_type = "draw"

    sauvegarder_partie(tab_id, logic, historique)
    return construire_reponse(
        logic,
        historique,
        vainqueur=vainqueur,
        winner_color=winner_color,
        winner_type=winner_type,
        winning_cells=winning_cells,
        message_ia=message_ia,
        played=played,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)