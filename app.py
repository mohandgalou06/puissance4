

"""
APP.PY — Puissance 4 Flask Backend
Routes API + serveur statique
"""

import os
import copy
import json
import base64
import io
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from minimax_engine import (
    make_board, get_valid_cols, drop, is_winner,
    get_best_move, find_winning_path, evaluate_position,
    check_win_any, EMPTY, P1, P2, ROWS, COLS
)
from database import DatabaseManager 

# ──────────────────────────────────────────────
#  INIT
# ──────────────────────────────────────────────

app  = Flask(__name__, static_folder='static')
CORS(app)

import os
db = DatabaseManager(
    host=os.environ.get("MYSQLHOST", "localhost"),
    user=os.environ.get("MYSQLUSER", "root"),
    password=os.environ.get("MYSQLPASSWORD", ""),
    database=os.environ.get("MYSQLDATABASE", "railway")
)
DB_OK = db.connect()

# ──────────────────────────────────────────────
#  FRONTEND
# ──────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# ──────────────────────────────────────────────
#  API — IA
# ──────────────────────────────────────────────

@app.route('/api/ai/move', methods=['POST'])
def ai_move():
    """
    POST { board: [[...]], player: 1|2, depth: int }
    → { col, scores, prediction }
    """
    data   = request.json
    board  = data.get('board', make_board())
    player = int(data.get('player', P2))
    depth  = min(int(data.get('depth', 5)), 7)   # max depth 7

    try:
        col, scores, prediction = get_best_move(board, player, depth)
        return jsonify({
            'col':        col,
            'scores':     {str(k): v for k, v in scores.items()},
            'prediction': prediction
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/evaluate', methods=['POST'])
def ai_evaluate():
    """
    POST { board: [[...]], player: 1|2 }
    → { score, prediction }
    """
    data   = request.json
    board  = data.get('board', make_board())
    player = int(data.get('player', P1))

    score, prediction = evaluate_position(board, player)
    return jsonify({'score': score, 'prediction': prediction})


@app.route('/api/ai/winning-path', methods=['POST'])
def ai_winning_path():
    """
    POST { board: [[...]], player: 1|2 }
    → { path: [col, ...] }
    Cherche la séquence de coups gagnants depuis la position fournie.
    """
    data   = request.json
    board  = data.get('board', make_board())
    player = int(data.get('player', P1))

    path = find_winning_path(board, player, max_depth=8)
    return jsonify({'path': path})


@app.route('/api/ai/hints', methods=['POST'])
def ai_hints():
    """
    POST { board: [[...]], player: 1|2, depth: int }
    → { hints: {col: score}, best_col, prediction }
    Indique le meilleur coup pour le joueur HUMAIN.
    """
    data   = request.json
    board  = data.get('board', make_board())
    player = int(data.get('player', P1))
    depth  = min(int(data.get('depth', 4)), 6)

    col, scores, prediction = get_best_move(board, player, depth)
    return jsonify({
        'best_col':   col,
        'scores':     {str(k): v for k, v in scores.items()},
        'prediction': prediction
    })


# ──────────────────────────────────────────────
#  API — ANALYSE IMAGE
# ──────────────────────────────────────────────

@app.route('/api/ai/analyze-image', methods=['POST'])
def analyze_image():
    """
    POST multipart/form-data avec image= (fichier)
    OU POST JSON { image_b64: "data:image/...;base64,..." }

    Retourne { board: [[...]], player: 1|2, message: str }
    La détection se base sur les couleurs rouge/jaune du plateau.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return jsonify({'error': 'Pillow non installé'}), 500

    img = None

    # Cas 1 : fichier uploadé
    if 'image' in request.files:
        f = request.files['image']
        img = Image.open(f).convert('RGB')

    # Cas 2 : base64 dans JSON
    elif request.is_json and 'image_b64' in request.json:
        b64 = request.json['image_b64']
        if ',' in b64:
            b64 = b64.split(',', 1)[1]
        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')

    else:
        return jsonify({'error': 'Aucune image fournie'}), 400

    # ── Détection de la grille ──
    board, player, msg = _detect_board(img)
    return jsonify({'board': board, 'player': player, 'message': msg})


def _detect_board(img):
    """
    Détecte automatiquement un plateau Puissance 4 dans l'image.
    Retourne (board 9x9, joueur_suivant, message).
    """
    from PIL import Image
    import numpy as np

    # Redimensionner à une taille standard
    w, h   = img.size
    target = min(w, h)
    # Rogner au carré central
    left   = (w - target) // 2
    top    = (h - target) // 2
    img    = img.crop((left, top, left + target, top + target))
    img    = img.resize((COLS * 60, ROWS * 60), Image.LANCZOS)

    pixels = np.array(img)
    board  = [[EMPTY] * COLS for _ in range(ROWS)]
    count  = {P1: 0, P2: 0}

    cell_w = pixels.shape[1] // COLS
    cell_h = pixels.shape[0] // ROWS

    for r in range(ROWS):
        for c in range(COLS):
            x1 = c * cell_w + cell_w // 4
            x2 = c * cell_w + 3 * cell_w // 4
            y1 = r * cell_h + cell_h // 4
            y2 = r * cell_h + 3 * cell_h // 4
            patch = pixels[y1:y2, x1:x2]
            avg   = patch.mean(axis=(0, 1))
            R, G, B = avg[0], avg[1], avg[2]

            # Rouge : R élevé, G et B faibles
            if R > 160 and G < 100 and B < 100:
                board[r][c] = P1
                count[P1] += 1
            # Jaune : R et G élevés, B faible
            elif R > 160 and G > 130 and B < 80:
                board[r][c] = P2
                count[P2] += 1
            else:
                board[r][c] = EMPTY

    # Le joueur suivant est celui qui a joué le moins
    total = count[P1] + count[P2]
    if count[P1] <= count[P2]:
        player = P1
    else:
        player = P2

    msg = f"Détecté : {count[P1]} rouge(s), {count[P2]} jaune(s) — {total} pièces"
    return board, player, msg


# ──────────────────────────────────────────────
#  API — BASE DE DONNÉES
# ──────────────────────────────────────────────

@app.route('/api/partie', methods=['POST'])
def save_partie():
    data      = request.json
    sequence  = data.get('sequence', '')
    joueur1   = data.get('joueur1', 'Joueur1')
    joueur2   = data.get('joueur2', 'Joueur2')
    mode      = data.get('mode', 'pvp')
    gagnant   = data.get('gagnant')     # pseudo du gagnant ou None

    if not sequence:
        return jsonify({'status': 'error', 'message': 'Séquence vide'}), 400

    if not DB_OK:
        return jsonify({'status': 'error', 'message': 'DB non connectée'}), 503

    pid = db.save_partie(joueur1, joueur2, sequence, mode, gagnant)
    if pid:
        return jsonify({'status': 'created', 'partie_id': pid})
    return jsonify({'status': 'error', 'message': 'Erreur BDD'}), 500


@app.route('/api/parties', methods=['GET'])
def get_parties():
    if not DB_OK:
        return jsonify([])
    return jsonify(db.get_all_parties())


@app.route('/api/partie/<int:pid>', methods=['GET'])
def get_partie(pid):
    if not DB_OK:
        return jsonify({'error': 'DB non connectée'}), 503
    partie = db.get_partie_detail(pid)
    if not partie:
        return jsonify({'error': 'Partie non trouvée'}), 404
    return jsonify(partie)


@app.route('/api/stats/global', methods=['GET'])
def stats_global():
    if not DB_OK:
        return jsonify({'parties': 0, 'joueurs': 0})
    return jsonify(db.get_global_stats())


@app.route('/api/stats', methods=['GET'])
def stats_leaderboard():
    if not DB_OK:
        return jsonify([])
    return jsonify(db.get_leaderboard())


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

