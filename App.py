

from flask import Flask, jsonify, request, send_from_directory
from database import DatabaseManager
import os

app = Flask(__name__, static_folder='static')

# ===== CONFIGURATION MySQL PythonAnywhere =====
# Remplace ces valeurs par les tiennes sur PythonAnywhere
DB_HOST     = "galou.mysql.pythonanywhere-services.com"  # ton_username.mysql.pythonanywhere-services.com
DB_USER     = "galou"           # ton username PythonAnywhere
DB_PASSWORD = "galou1646"       # ton mot de passe MySQL PythonAnywhere
DB_NAME     = "galou$puissance4"  # toujours username$nomdb sur PythonAnywhere

db = DatabaseManager(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
db.connect()

# ==================== ROUTES ====================

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/joueur', methods=['POST'])
def create_joueur():
    data = request.json
    pseudo = data.get('pseudo', 'Joueur')
    joueur_id = db.get_or_create_joueur(pseudo)
    return jsonify({'id': joueur_id, 'pseudo': pseudo})

@app.route('/api/parties', methods=['GET'])
def get_parties():
    parties = db.get_all_parties()
    result = []
    for p in parties:
        p2 = dict(p)
        for k, v in p2.items():
            if hasattr(v, 'strftime'):
                p2[k] = v.strftime('%d/%m/%Y %H:%M')
        result.append(p2)
    return jsonify(result)

@app.route('/api/partie', methods=['POST'])
def save_partie():
    data = request.json
    sequence = data.get('sequence', '')
    joueur1  = data.get('joueur1', 'Joueur 1')
    joueur2  = data.get('joueur2', 'Joueur 2')
    mode     = data.get('mode', 'pvp')
    if not sequence:
        return jsonify({'status': 'error', 'message': 'Séquence vide'})
    j1_id = db.get_or_create_joueur(joueur1)
    j2_id = db.get_or_create_joueur(joueur2 if mode == 'pvp' else 'IA', est_ia=(mode != 'pvp'))
    result = db.import_partie_from_sequence(
        sequence=sequence, joueur1_id=j1_id, joueur2_id=j2_id, nb_colonnes=7)
    return jsonify(result)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        cur = db.connection.cursor(dictionary=True)
        cur.execute("SELECT * FROM stats_joueurs ORDER BY victoires DESC LIMIT 20")
        stats = cur.fetchall()
        cur.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/stats/global', methods=['GET'])
def get_global_stats():
    try:
        cur = db.connection.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) as total FROM parties")
        total = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as total FROM joueurs")
        joueurs = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as total FROM coups")
        coups = cur.fetchone()['total']
        cur.close()
        return jsonify({'parties': total, 'joueurs': joueurs, 'coups': coups})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/analyse', methods=['POST'])
def analyse_position():
    data = request.json
    sequence = data.get('sequence', '')
    try:
        recs = db.analyze_position(sequence)
        return jsonify([{'col': r[0], 'score': r[1], 'nb_parties': r[2]} for r in recs])
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=False)








