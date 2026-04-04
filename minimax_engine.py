

"""
MINIMAX ENGINE — Puissance 4
Moteur IA pur Python, appelé via l'API Flask.
"""

EMPTY = 0
P1    = 1   # Rouge (humain ou IA)
P2    = 2   # Jaune (IA)

ROWS = 9
COLS = 9


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def make_board():
    return [[EMPTY] * COLS for _ in range(ROWS)]


def get_valid_cols(board):
    return [c for c in range(COLS) if board[0][c] == EMPTY]


def get_lowest_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return -1


def drop(board, col, player):
    r = get_lowest_row(board, col)
    if r != -1:
        board[r][col] = player
    return r


def is_winner(board, row, col, player):
    """Vérifie si player a gagné en partant de (row,col)."""
    for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        cnt = 1
        for d in (1, -1):
            nr, nc = row + dr * d, col + dc * d
            while 0 <= nr < ROWS and 0 <= nc < COLS and board[nr][nc] == player:
                cnt += 1
                nr += dr * d
                nc += dc * d
        if cnt >= 4:
            return True
    return False


def check_win_any(board, player):
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == player and is_winner(board, r, c, player):
                return True
    return False


def is_terminal(board):
    return (check_win_any(board, P1) or check_win_any(board, P2)
            or not get_valid_cols(board))


# ──────────────────────────────────────────────
#  ÉVALUATION HEURISTIQUE
# ──────────────────────────────────────────────

def evaluate_window(window, player):
    opp   = P2 if player == P1 else P1
    score = 0
    pc    = window.count(player)
    ec    = window.count(EMPTY)
    oc    = window.count(opp)

    if oc == 0:
        if pc == 4: score += 100000
        elif pc == 3: score += 60
        elif pc == 2: score += 10
    if pc == 0:
        if oc == 3: score -= 80
        elif oc == 2: score -= 8
    return score


def evaluate_board(board, player):
    if check_win_any(board, player):
        return 100000
    opp = P2 if player == P1 else P1
    if check_win_any(board, opp):
        return -100000

    score = 0
    center = COLS // 2

    # Bonus colonnes centrales
    for r in range(ROWS):
        if board[r][center] == player:          score += 8
        if center > 0 and board[r][center-1] == player: score += 4
        if center < COLS-1 and board[r][center+1] == player: score += 4
        if center > 1 and board[r][center-2] == player: score += 2
        if center < COLS-2 and board[r][center+2] == player: score += 2

    # Bonus rangées basses
    for c in range(COLS):
        if board[ROWS-1][c] == player: score += 3
        if board[ROWS-2][c] == player: score += 2

    # Fenêtres de 4
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                window = []
                for i in range(4):
                    nr, nc = r + dr * i, c + dc * i
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        window.append(board[nr][nc])
                    else:
                        window.clear()
                        break
                if len(window) == 4:
                    score += evaluate_window(window, player)

    return score


# ──────────────────────────────────────────────
#  MINIMAX ALPHA-BETA + TABLE DE TRANSPOSITION
# ──────────────────────────────────────────────

def board_key(board, depth, maximizing):
    flat = ''.join(str(board[r][c]) for r in range(ROWS) for c in range(COLS))
    return flat + str(depth) + str(maximizing)


def minimax(board, depth, maximizing, ai_player, alpha, beta, tt=None):
    if tt is None:
        tt = {}

    key = board_key(board, depth, maximizing)
    if key in tt:
        return tt[key]

    if check_win_any(board, ai_player):
        return 100000 + depth
    opp = P2 if ai_player == P1 else P1
    if check_win_any(board, opp):
        return -100000 - depth

    valid = get_valid_cols(board)
    if depth == 0 or not valid:
        return evaluate_board(board, ai_player)

    center = COLS // 2
    valid.sort(key=lambda c: abs(c - center))
    human = P2 if ai_player == P1 else P1

    if maximizing:
        best = -float('inf')
        for col in valid:
            r = drop(board, col, ai_player)
            if r != -1:
                score = minimax(board, depth - 1, False, ai_player, alpha, beta, tt)
                board[r][col] = EMPTY
                best = max(best, score)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
        tt[key] = best
        return best
    else:
        best = float('inf')
        for col in valid:
            r = drop(board, col, human)
            if r != -1:
                score = minimax(board, depth - 1, True, ai_player, alpha, beta, tt)
                board[r][col] = EMPTY
                best = min(best, score)
                beta = min(beta, best)
                if beta <= alpha:
                    break
        tt[key] = best
        return best


# ──────────────────────────────────────────────
#  GET BEST MOVE  (avec scores par colonne)
# ──────────────────────────────────────────────

def get_best_move(board, player, depth=5):
    """
    Retourne (best_col, scores_dict, prediction).
    scores_dict = {col: score, ...}
    prediction  = 'win' | 'lose' | 'draw' | 'uncertain'
    """
    valid = get_valid_cols(board)
    if not valid:
        return None, {}, 'draw'

    opp = P2 if player == P1 else P1

    # Coup gagnant immédiat
    for col in valid:
        r = drop(board, col, player)
        if r != -1:
            won = is_winner(board, r, col, player)
            board[r][col] = EMPTY
            if won:
                scores = {c: (100000 if c == col else 0) for c in valid}
                return col, scores, 'win'

    # Bloquer victoire adversaire
    block_col = None
    for col in valid:
        r = drop(board, col, opp)
        if r != -1:
            won = is_winner(board, r, col, opp)
            board[r][col] = EMPTY
            if won:
                block_col = col
                break

    # Calcul minimax pour chaque colonne
    center   = COLS // 2
    ordered  = sorted(valid, key=lambda c: abs(c - center))
    scores   = {}
    tt       = {}

    for col in ordered:
        r = drop(board, col, player)
        if r != -1:
            score = minimax(board, depth - 1, False, player, -float('inf'), float('inf'), tt)
            board[r][col] = EMPTY
            scores[col] = score

    if not scores:
        return valid[0], {}, 'uncertain'

    best_col   = max(scores, key=lambda c: scores[c])
    best_score = scores[best_col]

    # Si on a un blocage urgent ET que le minimax ne préfère pas ce coup
    if block_col is not None and best_score < 90000:
        best_col = block_col

    # Prédiction
    if best_score >= 90000:
        prediction = 'win'
    elif best_score <= -90000:
        prediction = 'lose'
    elif abs(best_score) < 30:
        prediction = 'draw'
    else:
        prediction = 'uncertain'

    return best_col, scores, prediction


# ──────────────────────────────────────────────
#  ANALYSE D'UNE POSITION : COUPS GAGNANTS
# ──────────────────────────────────────────────

def find_winning_path(board, player, max_depth=6):
    """
    Cherche la séquence de coups menant à la victoire.
    Retourne une liste de colonnes (0-indexed) ou [] si pas trouvé.
    """
    def search(b, p, depth, path):
        if depth == 0:
            return None
        valid = get_valid_cols(b)
        opp   = P2 if p == P1 else P1
        for col in valid:
            r = drop(b, col, p)
            if r != -1:
                if is_winner(b, r, col, p):
                    b[r][col] = EMPTY
                    return path + [col]
                result = search(b, opp, depth - 1, path + [col])
                b[r][col] = EMPTY
                if result:
                    return result
        return None

    import copy
    board_copy = copy.deepcopy(board)
    return search(board_copy, player, max_depth, []) or []


def evaluate_position(board, player):
    """
    Évalue la position courante pour `player`.
    Retourne (score, prediction_label).
    """
    valid = get_valid_cols(board)
    if not valid:
        return 0, 'draw'

    opp = P2 if player == P1 else P1

    # Victoire/défaite immédiates
    if check_win_any(board, player):
        return 100000, 'win'
    if check_win_any(board, opp):
        return -100000, 'lose'

    # Coup gagnant dispo ?
    for col in valid:
        r = drop(board, col, player)
        if r != -1:
            won = is_winner(board, r, col, player)
            board[r][col] = EMPTY
            if won:
                return 90000, 'win'

    # Adversaire peut gagner au prochain coup ?
    for col in valid:
        r = drop(board, col, opp)
        if r != -1:
            won = is_winner(board, r, col, opp)
            board[r][col] = EMPTY
            if won:
                return -80000, 'lose'

    score = evaluate_board(board, player)
    if score > 200:
        label = 'winning'
    elif score < -200:
        label = 'losing'
    elif abs(score) < 50:
        label = 'draw'
    else:
        label = 'uncertain'

    return score, label
