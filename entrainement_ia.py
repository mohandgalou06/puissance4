

import random
import time
import json
import os
from multiprocessing import Pool, cpu_count
from database import DatabaseManager

# ==================== CONFIG ====================
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = "Galou1646!"
DB_NAME     = "puissance4"

OBJECTIF    = 1000
DEPTH       = 6
NB_PROCESS  = 6   # 🔥 ICI

# ==================== CONFIG GRILLE ====================
def get_grid_config():
    if os.path.exists("config.json"):
        try:
            with open("config.json") as f:
                cfg = json.load(f)
            return cfg.get("rows", 9), cfg.get("cols", 9)
        except:
            pass
    return 9, 9

ROWS, COLS = get_grid_config()

EMPTY    = " "
PLAYER_X = "X"
PLAYER_O = "O"

# ==================== LOGIQUE JEU ====================
# (inchangée)
def check_win(board, player, rows, cols):
    for r in range(rows):
        for c in range(cols - 3):
            if all(board[r][c+i] == player for i in range(4)): return True
    for c in range(cols):
        for r in range(rows - 3):
            if all(board[r+i][c] == player for i in range(4)): return True
    for r in range(rows - 3):
        for c in range(cols - 3):
            if all(board[r+i][c+i] == player for i in range(4)): return True
    for r in range(3, rows):
        for c in range(cols - 3):
            if all(board[r-i][c+i] == player for i in range(4)): return True
    return False

def is_terminal(board, rows, cols):
    return (check_win(board, PLAYER_X, rows, cols)
            or check_win(board, PLAYER_O, rows, cols)
            or all(board[0][c] != EMPTY for c in range(cols)))

def simulate_drop(board, col, player, rows):
    for r in range(rows - 1, -1, -1):
        if board[r][col] == EMPTY:
            board[r][col] = player
            return r
    return None

def evaluate_board(board, rows, cols):
    if check_win(board, PLAYER_X, rows, cols): return 10000
    if check_win(board, PLAYER_O, rows, cols): return -10000
    return 0

def minimax(board, depth, is_max, alpha, beta, rows, cols):
    if depth == 0 or is_terminal(board, rows, cols):
        return evaluate_board(board, rows, cols), None

    valid = [c for c in range(cols) if board[0][c] == EMPTY]
    if not valid:
        return 0, None

    best_col = valid[0]

    if is_max:
        val = -float('inf')
        for col in valid:
            row = simulate_drop(board, col, PLAYER_X, rows)
            if row is not None:
                s, _ = minimax(board, depth-1, False, alpha, beta, rows, cols)
                board[row][col] = EMPTY
                if s > val:
                    val, best_col = s, col
                alpha = max(alpha, s)
                if beta <= alpha:
                    break
        return val, best_col
    else:
        val = float('inf')
        for col in valid:
            row = simulate_drop(board, col, PLAYER_O, rows)
            if row is not None:
                s, _ = minimax(board, depth-1, True, alpha, beta, rows, cols)
                board[row][col] = EMPTY
                if s < val:
                    val, best_col = s, col
                beta = min(beta, s)
                if beta <= alpha:
                    break
        return val, best_col

def get_best_move(board, player, depth, rows, cols):
    valid = [c for c in range(cols) if board[0][c] == EMPTY]
    if not valid:
        return None

    is_max = (player == PLAYER_X)
    _, best = minimax(board, depth, is_max, -float('inf'), float('inf'), rows, cols)
    return best if best is not None else valid[0]

# ==================== PARTIE ====================
def jouer_une_partie(_):
    board = [[EMPTY]*COLS for _ in range(ROWS)]
    player = PLAYER_X
    sequence = []
    
    # 🔥 Les 2 premiers coups sont aléatoires → parties toutes différentes
    premiers_coups_aleatoires = 2

    while True:
        valid = [c for c in range(COLS) if board[0][c] == EMPTY]
        if not valid:
            break

        if len(sequence) < premiers_coups_aleatoires:
            col = random.choice(valid)   # aléatoire au début
        else:
            col = get_best_move(board, player, DEPTH, ROWS, COLS)

        if col is None:
            break

        row = simulate_drop(board, col, player, ROWS)
        if row is None:
            break

        sequence.append(str(col))

        if check_win(board, player, ROWS, COLS):
            return ''.join(sequence), player

        if all(board[0][c] != EMPTY for c in range(COLS)):
            return ''.join(sequence), None

        player = PLAYER_O if player == PLAYER_X else PLAYER_X

    return ''.join(sequence), None

# ==================== WORKER ====================
def worker(_):
    db = DatabaseManager(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    db.connect()

    ia1_id = db.get_or_create_joueur("IA_X_depth6", est_ia=True)
    ia2_id = db.get_or_create_joueur("IA_O_depth6", est_ia=True)

    sequence, gagnant_sym = jouer_une_partie(None)

    gagnant_id = None
    if gagnant_sym == PLAYER_X:
        gagnant_id = ia1_id
    elif gagnant_sym == PLAYER_O:
        gagnant_id = ia2_id

    partie_id = db.save_partie_complete(
        ia1_id, ia2_id, gagnant_id,
        sequence, 0,
        nb_lignes=ROWS, nb_colonnes=COLS
    )

    db.disconnect()
    return partie_id, gagnant_sym, len(sequence)

# ==================== MAIN ====================
def main():
    print("🚀 Entrainement parallèle (6 processus)\n")

    start = time.time()

    with Pool(NB_PROCESS) as p:
        results = []

        for i, res in enumerate(p.imap_unordered(worker, range(OBJECTIF)), 1):
            partie_id, gagnant, coups = res

            print(f"[{i}/{OBJECTIF}] Partie #{partie_id} | "
                  f"{'Gagnant: '+gagnant if gagnant else 'NUL'} | {coups} coups")

    print(f"\n✅ Terminé en {int(time.time() - start)}s")

if __name__ == "__main__":
    main()