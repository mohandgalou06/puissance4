import random
import time
from constants import ROUGE, JAUNE

# =========================
# ETAT GLOBAL / DEBUG
# =========================
CURRENT_DEPTH = 0
LAST_COMPLETED_DEPTH = 0
CACHE_MINIMAX = {}
CACHE_MAX_SIZE = 500_000

# =========================
# ZOBRIST
# =========================
_ZOBRIST_TABLE = [[[random.getrandbits(64) for _ in range(3)] for _ in range(9)] for _ in range(9)]
_ZOBRIST_TURN = random.getrandbits(64)

# =========================
# HEURISTIQUES D'ORDRE
# =========================
KILLER_MOVES = {}   # profondeur -> [col1, col2]
HISTORY_HEURISTIC = [0] * 9

# Ordre de base centré
BASE_ORDER = [4, 3, 5, 2, 6, 1, 7, 0, 8]


class TimeOutException(Exception):
    pass


# =========================
# ZOBRIST HELPERS
# =========================
def zobrist_initial(grille, maximisant):
    h = 0
    for l in range(9):
        for c in range(9):
            val = grille[l][c]
            if val:
                h ^= _ZOBRIST_TABLE[l][c][val]
    if maximisant:
        h ^= _ZOBRIST_TURN
    return h


def zobrist_apres_coup(h, ligne, col, joueur):
    h ^= _ZOBRIST_TABLE[ligne][col][joueur]
    h ^= _ZOBRIST_TURN
    return h


# =========================
# EVALUATION
# =========================
def score_position(logic, pion):
    adversaire = JAUNE if pion == ROUGE else ROUGE
    grille = logic.grille
    score = 0

    poids_colonnes = [1, 2, 4, 8, 20, 8, 4, 2, 1]

    # Poids de centre
    for l in range(9):
        for c in range(9):
            val = grille[l][c]
            if val == pion:
                score += poids_colonnes[c]
            elif val == adversaire:
                score -= poids_colonnes[c]

    def eval_fenetre(v1, v2, v3, v4):
        vals = (v1, v2, v3, v4)
        p = vals.count(pion)
        a = vals.count(adversaire)
        vides = vals.count(0)

        # Fenêtre bloquée
        if p > 0 and a > 0:
            return 0

        # Pour nous
        if a == 0:
            if p == 4:
                return 1_000_000
            if p == 3 and vides == 1:
                return 25_000
            if p == 2 and vides == 2:
                return 800
            if p == 1 and vides == 3:
                return 20

        # Pour l'adversaire
        if p == 0:
            if a == 4:
                return -1_000_000
            if a == 3 and vides == 1:
                return -35_000
            if a == 2 and vides == 2:
                return -600

        return 0

    # Lignes
    for l in range(9):
        row = grille[l]
        for c in range(6):
            score += eval_fenetre(row[c], row[c + 1], row[c + 2], row[c + 3])

    # Colonnes
    for c in range(9):
        for l in range(6):
            score += eval_fenetre(grille[l][c], grille[l + 1][c], grille[l + 2][c], grille[l + 3][c])

    # Diagonales descendantes
    for l in range(6):
        for c in range(6):
            score += eval_fenetre(grille[l][c], grille[l + 1][c + 1], grille[l + 2][c + 2], grille[l + 3][c + 3])

    # Diagonales montantes
    for l in range(3, 9):
        for c in range(6):
            score += eval_fenetre(grille[l][c], grille[l - 1][c + 1], grille[l - 2][c + 2], grille[l - 3][c + 3])

    return score


# =========================
# VICTOIRE LOCALE
# =========================
def victoire_apres_coup(grille, ligne, col, joueur):
    for dl, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        count = 1

        # sens +
        l2, c2 = ligne + dl, col + dc
        while 0 <= l2 < 9 and 0 <= c2 < 9 and grille[l2][c2] == joueur:
            count += 1
            l2 += dl
            c2 += dc

        # sens -
        l2, c2 = ligne - dl, col - dc
        while 0 <= l2 < 9 and 0 <= c2 < 9 and grille[l2][c2] == joueur:
            count += 1
            l2 -= dl
            c2 -= dc

        if count >= 4:
            return True

    return False


def penalite_case_offerte(grille, col, joueur, ligne_posee):
    if ligne_posee is None or ligne_posee == 0:
        return 0

    adversaire = ROUGE if joueur == JAUNE else JAUNE
    ligne_dessus = ligne_posee - 1

    if grille[ligne_dessus][col] != 0:
        return 0

    if victoire_apres_coup(grille, ligne_dessus, col, adversaire):
        return -60_000

    return 0


# =========================
# ORDRE DES COUPS
# =========================
def get_ordered_moves(logic, zh, profondeur):
    # Colonnes valides
    valid_cols = [c for c in BASE_ORDER if logic.colonne_valide(c)]
    if not valid_cols:
        return []

    scored = []
    tt_move = None
    if zh in CACHE_MINIMAX:
        tt_move = CACHE_MINIMAX[zh][1]

    killers = KILLER_MOVES.get(profondeur, [])

    for c in valid_cols:
        bonus = 0

        # TT move
        if c == tt_move:
            bonus += 1_000_000

        # killer moves
        if c in killers:
            bonus += 100_000

        # history heuristic
        bonus += HISTORY_HEURISTIC[c] * 10

        # centre
        bonus += [0, 10, 20, 30, 40, 30, 20, 10, 0][c]

        # Colonnes déjà "actives"
        if logic.grille[8][c] != 0:
            bonus += 15
        if c > 0 and logic.grille[8][c - 1] != 0:
            bonus += 5
        if c < 8 and logic.grille[8][c + 1] != 0:
            bonus += 5

        scored.append((bonus, c))

    scored.sort(reverse=True)
    return [c for _, c in scored]


def register_killer(depth, col):
    arr = KILLER_MOVES.setdefault(depth, [])
    if col in arr:
        return
    arr.insert(0, col)
    if len(arr) > 2:
        arr.pop()


# =========================
# MINIMAX
# =========================
def minimax(
    logic,
    profondeur,
    alpha,
    beta,
    maximisant,
    zh,
    debut,
    budget,
    dernier_ligne=None,
    dernier_col=None,
    dernier_joueur=None,
):
    global CACHE_MINIMAX

    if budget > 0 and (time.time() - debut) > budget:
        raise TimeOutException()

    # Terminal local : seul le dernier coup peut avoir créé une victoire
    if dernier_ligne is not None and victoire_apres_coup(logic.grille, dernier_ligne, dernier_col, dernier_joueur):
        if dernier_joueur == JAUNE:
            return None, 10_000_000 + profondeur * 1000
        return None, -10_000_000 - profondeur * 1000

    # Plus de coups
    cols_existantes = [c for c in range(9) if logic.colonne_valide(c)]
    if not cols_existantes:
        return None, 0

    # Feuille
    if profondeur == 0:
        return None, score_position(logic, JAUNE)

    alpha_orig = alpha
    beta_orig = beta

    # Transposition table
    cached = CACHE_MINIMAX.get(zh)
    if cached is not None:
        prof_s, col_s, val_s, flag = cached
        if prof_s >= profondeur:
            if flag == "EXACT":
                return col_s, val_s
            if flag == "LOWERBOUND":
                alpha = max(alpha, val_s)
            elif flag == "UPPERBOUND":
                beta = min(beta, val_s)
            if alpha >= beta:
                return col_s, val_s

    cols_valides = get_ordered_moves(logic, zh, profondeur)
    if not cols_valides:
        return None, 0

    meilleure_col = cols_valides[0]

    if maximisant:
        valeur = -float("inf")

        for c in cols_valides:
            l = logic.placer_pion(c, JAUNE)
            zh2 = zobrist_apres_coup(zh, l, c, JAUNE)

            try:
                pen = penalite_case_offerte(logic.grille, c, JAUNE, l)
                _, s = minimax(
                    logic,
                    profondeur - 1,
                    alpha,
                    beta,
                    False,
                    zh2,
                    debut,
                    budget,
                    dernier_ligne=l,
                    dernier_col=c,
                    dernier_joueur=JAUNE,
                )
                s += pen

                if s > valeur:
                    valeur = s
                    meilleure_col = c

                if valeur > alpha:
                    alpha = valeur

                if alpha >= beta:
                    HISTORY_HEURISTIC[c] += profondeur * profondeur
                    register_killer(profondeur, c)
                    break

            finally:
                logic.grille[l][c] = 0

    else:
        valeur = float("inf")

        for c in cols_valides:
            l = logic.placer_pion(c, ROUGE)
            zh2 = zobrist_apres_coup(zh, l, c, ROUGE)

            try:
                pen = penalite_case_offerte(logic.grille, c, ROUGE, l)
                _, s = minimax(
                    logic,
                    profondeur - 1,
                    alpha,
                    beta,
                    True,
                    zh2,
                    debut,
                    budget,
                    dernier_ligne=l,
                    dernier_col=c,
                    dernier_joueur=ROUGE,
                )
                s += pen

                if s < valeur:
                    valeur = s
                    meilleure_col = c

                if valeur < beta:
                    beta = valeur

                if alpha >= beta:
                    HISTORY_HEURISTIC[c] += profondeur * profondeur
                    register_killer(profondeur, c)
                    break

            finally:
                logic.grille[l][c] = 0

    # Stockage TT
    if meilleure_col is not None:
        if valeur <= alpha_orig:
            flag = "UPPERBOUND"
        elif valeur >= beta_orig:
            flag = "LOWERBOUND"
        else:
            flag = "EXACT"
        if zh not in CACHE_MINIMAX and len(CACHE_MINIMAX) >= CACHE_MAX_SIZE:
            CACHE_MINIMAX.pop(next(iter(CACHE_MINIMAX)))
        CACHE_MINIMAX[zh] = (profondeur, meilleure_col, valeur, flag)

    return meilleure_col, valeur


# =========================
# ITERATIVE DEEPENING
# =========================
def minimax_iteratif(logic, est_maximisant=True, max_profondeur=10, budget_secondes=2.0):
    global CURRENT_DEPTH, LAST_COMPLETED_DEPTH, CACHE_MINIMAX, KILLER_MOVES, HISTORY_HEURISTIC

    CURRENT_DEPTH = 0
    LAST_COMPLETED_DEPTH = 0
    KILLER_MOVES = {}
    HISTORY_HEURISTIC = [0] * 9

    meilleur_coup = None
    meilleur_score = -float("inf") if est_maximisant else float("inf")

    debut = time.time()
    zh_racine = zobrist_initial(logic.grille, est_maximisant)

    for prof in range(1, max_profondeur + 1):
        CURRENT_DEPTH = prof
        try:
            col, score = minimax(
                logic,
                prof,
                -float("inf"),
                float("inf"),
                est_maximisant,
                zh_racine,
                debut,
                budget_secondes,
            )

            if col is not None:
                meilleur_coup = col
                meilleur_score = score
                LAST_COMPLETED_DEPTH = prof
                print(f"   prof {prof} -> col {col}, score {score:+d}", flush=True)

            if abs(score) >= 9_000_000:
                break

        except TimeOutException:
            break

    print(f"Dernière profondeur complétée : {LAST_COMPLETED_DEPTH}", flush=True)
    CURRENT_DEPTH = 0
    return meilleur_coup, meilleur_score
