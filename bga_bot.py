



"""
BGA BOT - Puissance 4 9x9
"""

import time
import json
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc

# ==================== CONFIG ====================
MON_PSEUDO = "galou_moumouh"
MON_ID     = "99331026"
DEPTH      = 4
ROWS       = 9
COLS       = 9

EMPTY = 0
MOI   = 1
ADV   = 2

# ==================== IA MINIMAX ====================

def check_win_board(board, player):
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c+i] == player for i in range(4)): return True
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r+i][c] == player for i in range(4)): return True
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r+i][c+i] == player for i in range(4)): return True
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r-i][c+i] == player for i in range(4)): return True
    return False

def is_terminal(board):
    return (check_win_board(board, MOI) or check_win_board(board, ADV)
            or all(board[0][c] != EMPTY for c in range(COLS)))

def drop(board, col, player):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            board[r][col] = player
            return r
    return None

def evaluate(board):
    if check_win_board(board, MOI): return  100000
    if check_win_board(board, ADV): return -100000
    score = 0
    center = COLS // 2
    for r in range(ROWS):
        if board[r][center] == MOI: score += 6
        if board[r][center] == ADV: score -= 6
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
                w = []
                for i in range(4):
                    nr, nc = r+dr*i, c+dc*i
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        w.append(board[nr][nc])
                    else:
                        w.clear(); break
                if len(w) == 4:
                    pm = w.count(MOI); pa = w.count(ADV)
                    if pa == 0:
                        if pm == 3: score += 50
                        elif pm == 2: score += 5
                    if pm == 0:
                        if pa == 3: score -= 80
                        elif pa == 2: score -= 5
    return score

def minimax(board, depth, maximizing, alpha, beta):
    if depth == 0 or is_terminal(board):
        return evaluate(board), None
    valid = [c for c in range(COLS) if board[0][c] == EMPTY]
    if not valid: return 0, None
    center = COLS // 2
    valid.sort(key=lambda c: abs(c - center))
    best_col = valid[0]
    if maximizing:
        val = -float('inf')
        for col in valid:
            r = drop(board, col, MOI)
            if r is not None:
                s, _ = minimax(board, depth-1, False, alpha, beta)
                board[r][col] = EMPTY
                if s > val: val, best_col = s, col
                alpha = max(alpha, s)
                if beta <= alpha: break
        return val, best_col
    else:
        val = float('inf')
        for col in valid:
            r = drop(board, col, ADV)
            if r is not None:
                s, _ = minimax(board, depth-1, True, alpha, beta)
                board[r][col] = EMPTY
                if s < val: val, best_col = s, col
                beta = min(beta, s)
                if beta <= alpha: break
        return val, best_col

def get_best_move(board, valid_cols):
    if not valid_cols: return None
    for col in valid_cols:
        r = drop(board, col, MOI)
        if r is not None:
            win = check_win_board(board, MOI)
            board[r][col] = EMPTY
            if win:
                print(f"  → Coup gagnant col {col+1}!")
                return col
    for col in valid_cols:
        r = drop(board, col, ADV)
        if r is not None:
            win = check_win_board(board, ADV)
            board[r][col] = EMPTY
            if win:
                print(f"  → Blocage col {col+1}!")
                return col
    _, col = minimax(board, DEPTH, True, -float('inf'), float('inf'))
    return col if col is not None else valid_cols[0]

# ==================== BGA ====================

def get_gamestate(driver):
    result = driver.execute_script("""
        try {
            var gui = window.gameui;
            if (!gui) return null;

            // ✅ gamestate = état LIVE, gamedatas.gamestate = snapshot initial
            var gs = gui.gamestate || gui.gamedatas.gamestate;

            return JSON.stringify({
                active_player: String(gs.active_player),
                state_id:      gs.id,
                state_name:    gs.name,
                possible_moves: gs.args ? gs.args.possibleMoves : null,
                board:         gui.gamedatas.board,
                move_nbr:      gui.gamedatas.notifications
                                 ? gui.gamedatas.notifications.move_nbr : 0,
                last_packet:   gui.gamedatas.notifications
                                 ? gui.gamedatas.notifications.last_packet_id : 0
            });
        } catch(e) { return null; }
    """)
    return json.loads(result) if result else None

def est_mon_tour(gs):
    if not gs: return False
    return gs.get("active_player") == MON_ID and gs.get("state_name") == "playerTurn"

def lire_plateau(gs):
    board = [[EMPTY]*COLS for _ in range(ROWS)]
    raw = gs.get("board", [])
    if not raw:
        return board
    items = raw if isinstance(raw, list) else raw.values()
    for token in items:
        try:
            col = int(token.get("x", token.get("col", 0))) - 1
            row_bga = int(token.get("y", token.get("row", 0)))
            row = ROWS - row_bga
            pid = str(token.get("player_id", token.get("player", "")))
            if 0 <= row < ROWS and 0 <= col < COLS:
                board[row][col] = MOI if pid == MON_ID else ADV
        except:
            pass
    return board

def get_valid_cols(gs):
    try:
        moves = gs["possible_moves"]
        valid = []
        for col_str, rows in moves.items():
            if any(v for v in rows.values()):
                valid.append(int(col_str) - 1)
        return sorted(valid)
    except:
        return list(range(COLS))

def jouer_colonne(driver, col_0indexed):
    col_bga = col_0indexed + 1
    success = driver.execute_script(f"""
        var col = {col_bga};

        // Méthode 1 : ajaxcall BGA natif (la plus fiable)
        try {{
            window.gameui.ajaxcall(
                '/' + window.gameui.game_name + '/' + window.gameui.game_name + '/playDisc.html',
                {{ col: col, lock: true }},
                window.gameui, function() {{}}, function() {{}}
            );
            return 'ajax';
        }} catch(e) {{}}

        // Méthode 2 : cliquer cellule
        for (var row = {ROWS}; row >= 1; row--) {{
            var ids = [
                'cell_' + row + '_' + col,
                'square_' + row + '_' + col,
                'connectfour_cell_' + (row-1) + '_' + (col-1)
            ];
            for (var i = 0; i < ids.length; i++) {{
                var el = document.getElementById(ids[i]);
                if (el) {{ el.click(); return 'cell_' + ids[i]; }}
            }}
        }}

        // Méthode 3 : cliquer colonne
        var elcol = document.getElementById('col_' + col);
        if (elcol) {{ elcol.click(); return 'col'; }}

        return null;
    """)
    print(f"  → Méthode: {success}")
    return success is not None

def afficher_board(board):
    print("  ┌" + "─"*COLS*2 + "┐")
    for r in range(ROWS):
        ligne = "  │"
        for c in range(COLS):
            if board[r][c] == MOI:   ligne += "● "
            elif board[r][c] == ADV: ligne += "○ "
            else:                    ligne += ". "
        print(ligne + "│")
    print("  └" + "─"*COLS*2 + "┘")
    print("   " + " ".join(str(i+1) for i in range(COLS)))

# ==================== BOUCLE JEU ====================

def jouer_partie(driver):
    print(f"\n🎮 Bot actif — {ROWS}x{COLS} — depth {DEPTH}")
    coups = 0
    dernier_move_nbr = -1   # ← remplace dernier_packet

    while True:
        time.sleep(0.6)
        try:
            gs = get_gamestate(driver)
            if not gs:
                continue

            state_name = gs.get("state_name", "")
            if state_name == "gameEnd" or int(gs.get("state_id", 0)) == 99:
                print("\n🏁 Partie terminée !")
                return

            if not est_mon_tour(gs):
                continue

            move_nbr = int(gs.get("move_nbr", 0))

            # ✅ Garde anti-doublon basée sur move_nbr (incrémenté à chaque coup)
            if move_nbr == dernier_move_nbr:
                continue

            print(f"\n  Tour {coups+1} — C'est mon tour ! (move #{move_nbr})")

            board = lire_plateau(gs)
            afficher_board(board)

            valid_cols = get_valid_cols(gs)
            print(f"  Colonnes valides: {[c+1 for c in valid_cols]}")

            if not valid_cols:
                print("  ⚠ Aucun coup valide !")
                break

            t0 = time.time()
            col = get_best_move(board, valid_cols)
            print(f"  🤖 IA choisit colonne {col+1} ({time.time()-t0:.2f}s)")

            if jouer_colonne(driver, col):
                coups += 1
                dernier_move_nbr = move_nbr

                print("  ⏳ Attente confirmation BGA...")
                for _ in range(50):
                    time.sleep(0.3)
                    gs2 = get_gamestate(driver)
                    if not gs2:
                        continue
                    new_move = int(gs2.get("move_nbr", 0))
                    # ✅ On attend que move_nbr augmente (BGA a bien enregistré le coup)
                    if new_move > move_nbr:
                        print(f"  ✅ Coup confirmé (move #{new_move})")
                        dernier_move_nbr = new_move
                        break
                else:
                    print("  ⚠ Timeout confirmation — on continue quand même")
            else:
                print("  ❌ Clic échoué")
                time.sleep(2)

        except KeyboardInterrupt:
            print("\n⚠ Arrêt")
            return
        except Exception as e:
            print(f"  ⚠ {e}")
            time.sleep(2)
# ==================== DRIVER ====================

def get_driver():
    import os
    options = uc.ChromeOptions()

    profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bga_profile")
    options.add_argument(f"--user-data-dir={profile_path}")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")

    return uc.Chrome(options=options)

# ==================== MAIN ====================

def main():
    print("="*50)
    print(f"  BGA BOT | {MON_PSEUDO} | Depth {DEPTH} | {ROWS}x{COLS}")
    print("="*50)

    print("\n[1] Ouvrir BGA manuellement")
    print("[2] Bot automatique")
    choix = input("\nChoix: ").strip()

    driver = get_driver()

    if choix == "1":
        driver.get("https://boardgamearena.com")
        print("✅ BGA ouvert")
        input("Entrée pour fermer...")
        driver.quit()
        return

    try:
        driver.get("https://boardgamearena.com/account")
        print("⏳ Connecte-toi dans le navigateur (120s)...")
        WebDriverWait(driver, 120).until(
            lambda d: "account" not in d.current_url and "login" not in d.current_url
        )
        print("✅ Connecté !")
        print("\n⏳ Va sur ta partie — le bot démarre automatiquement.\n")

        while True:
            try:
                url = driver.current_url
                if "game" in url or "table" in url:
                    gs = get_gamestate(driver)
                    if gs:
                        state_id   = int(gs.get("state_id", 99))
                        state_name = gs.get("state_name", "")
                        # Lancer seulement si partie vraiment active
                        if state_id != 99 and state_name != "gameEnd":
                            jouer_partie(driver)
                            print("\n⏳ En attente d'une nouvelle partie...")
                time.sleep(3)

            except KeyboardInterrupt:
                print("\n⚠ Arrêt du bot.")
                break
            except Exception as e:
                print(f"⚠ {e}")
                time.sleep(3)

    finally:
        driver.quit()
        print("✅ Bot arrêté.")

if __name__ == "__main__":
    main()