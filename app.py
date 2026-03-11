from flask import Flask, render_template, request, jsonify, session
from game_logic import GameLogic
from ai import IA_Tournoi
from constants import ROUGE, JAUNE
import random

app = Flask(__name__)
app.secret_key = "clef_secrete_super_puissance4_bga" 

ia_terminator = IA_Tournoi()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reset', methods=['POST'])
def reset():
    session['grille'] = [[0 for _ in range(9)] for _ in range(9)]
    session['historique'] = []
    return jsonify({"status": "ok"})

@app.route('/play', methods=['POST'])
def play():
    data = request.json
    colonne = data.get('colonne')
    ia_type = data.get('ia_type', 'minimax')
    ia_depth = int(data.get('ia_depth', 6))
    action = data.get('action') # 'human' ou 'ia'

    logic = GameLogic()
    logic.nb_lignes = 9
    logic.nb_colonnes = 9
    
    logic.grille = session.get('grille')
    if logic.grille is None:
        logic.grille = [[0 for _ in range(9)] for _ in range(9)]
    historique = session.get('historique', [])

    vainqueur = None
    # Déduire à qui c'est le tour
    joueur_actuel = ROUGE if len(historique) % 2 == 0 else JAUNE
    nom_joueur = "Rouge" if joueur_actuel == ROUGE else "Jaune"

    def executer_ia(joueur_ia):
        if ia_type == 'random':
            valides = [c for c in range(9) if logic.colonne_valide(c)]
            return random.choice(valides) if valides else None
        else:
            ia_terminator.profondeur_secours = ia_depth
            return ia_terminator.jouer_coup(logic, historique, joueur_ia)

    # ACTION 1 : C'est un humain qui joue
    if action == 'human':
        if colonne is not None and logic.colonne_valide(colonne):
            logic.placer_pion(colonne, joueur_actuel)
            historique.append([0, colonne, joueur_actuel])
            if logic.victoire(joueur_actuel):
                vainqueur = nom_joueur

    # ACTION 2 : C'est l'IA qui joue
    elif action == 'ia':
        col_ia = executer_ia(joueur_actuel)
        if col_ia is not None:
            logic.placer_pion(col_ia, joueur_actuel)
            historique.append([0, col_ia, joueur_actuel])
            if logic.victoire(joueur_actuel):
                vainqueur = f"IA {nom_joueur}"

    session['grille'] = logic.grille
    session['historique'] = historique

    return jsonify({"grille": logic.grille, "vainqueur": vainqueur})

if __name__ == '__main__':
    app.run(debug=True)