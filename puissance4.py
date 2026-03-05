
from tkinter import simpledialog
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import copy
import time
import os
import random

CONFIG_FILE = "config.json"
SAVES_DIR   = "saves"
EMPTY       = " "
PLAYER_X    = "X"
PLAYER_O    = "O"

def load_config():
    default = {
        "rows": 6, "cols": 7,
        "first_player": "X",
        "color_x": "red", "color_o": "yellow",
        "ai_mode": "minimax", "minimax_depth": 4
    }
    if not os.path.exists(CONFIG_FILE):
        save_config(default)
        return default
    try:
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
        for k, v in default.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return default

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


class MenuSelection(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.choice = None
        self.title("Puissance 4 - Menu")
        self.geometry("300x260")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: self.select("quit"))

        tk.Label(self, text="PUISSANCE 4", font=("Arial", 18, "bold")).pack(pady=20)
        for text, mode in [
            ("Joueur vs Joueur", "pvp"),
            ("Joueur vs IA",     "ai"),
            ("IA vs IA",         "ai_vs_ai"),
            ("Quitter",          "quit"),
        ]:
            tk.Button(self, text=text, width=25, height=2,
                      command=lambda m=mode: self.select(m)).pack(pady=4)
        self.grab_set()
        self.wait_window()

    def select(self, mode):
        self.choice = mode
        self.destroy()


class Puissance4(tk.Frame):
    def __init__(self, master, mode, joueur1_id, db):
        super().__init__(master)
        self.master_win  = master
        self.joueur1_id  = joueur1_id
        self.db          = db
        self.mode        = mode
        self.pack()

        os.makedirs(SAVES_DIR, exist_ok=True)

        self.cfg  = load_config()
        self.rows = self.cfg["rows"]
        self.cols = self.cfg["cols"]

        # Taille de cellule adaptée à l'écran
        sw = master.winfo_screenwidth()
        sh = master.winfo_screenheight()
        self.CS = min(80, (sh - 220) // (self.rows + 1), (sw - 60) // self.cols)

        self.player         = self.cfg["first_player"]
        self.ai_busy        = False
        self.joueur2_id     = None
        self.partie_id      = None
        self.numero_coup    = 0
        self.temps_debut    = time.time()
        self.coups_sequence = []
        self.replay_mode    = False
        self.replay_index   = -1
        self.board          = [[EMPTY]*self.cols for _ in range(self.rows)]
        self.history        = []
        self.game_over      = False
        self.paused         = False
        self.minimax_scores = {}
        self.show_scores    = False
        self.total_nodes    = 0

        if self.mode in ("ai", "ai_vs_ai"):
            self.joueur2_id = self.db.get_or_create_joueur("IA", est_ia=True)
        else:
            p2 = simpledialog.askstring("Joueur 2", "Pseudo du Joueur 2 :") or "Joueur2"
            self.joueur2_id = self.db.get_or_create_joueur(p2)

        master.title(f"Puissance 4 — {self.rows}x{self.cols}")

        # Canvas : 50px numéros + grille + 40px scores
        cw = self.cols * self.CS
        ch = self.rows * self.CS + 50 + 40
        self.canvas = tk.Canvas(self, width=cw, height=ch, bg="#0000AA")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.click)

        self.status = tk.Label(self, font=("Arial", 12, "bold"))
        self.status.pack(fill="x")
        self.default_bg = self.status.cget("bg")

        self.progress_label = tk.Label(self, font=("Arial", 10), fg="blue")
        self.progress_label.pack(fill="x")

        self.create_menu(master)
        self.draw_board()
        self.update_status()
        self.maybe_trigger_ai()

    def create_menu(self, root):
        bar = tk.Menu(root)
        root.config(menu=bar)

        g = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="Jeu", menu=g)
        g.add_command(label="Nouvelle partie",   command=self.new_game)
        g.add_command(label="Pause / Reprendre", command=self.toggle_pause)
        g.add_separator()
        g.add_command(label="Sauvegarder", command=self.save_game)
        g.add_command(label="Charger",     command=self.load_game)
        g.add_separator()
        g.add_command(label="Quitter", command=root.quit)

        e = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="Edition", menu=e)
        e.add_command(label="Annuler coup",      command=self.undo)
        e.add_separator()
        e.add_command(label="Debut",             command=self.replay_first)
        e.add_command(label="Coup precedent",    command=self.replay_previous)
        e.add_command(label="Coup suivant",      command=self.replay_next)
        e.add_command(label="Fin",               command=self.replay_last)

        ia = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="IA", menu=ia)
        ia.add_command(label="Mode: Aleatoire", command=lambda: self.set_ai_mode("random"))
        ia.add_command(label="Mode: Minimax",   command=lambda: self.set_ai_mode("minimax"))
        ia.add_separator()
        ia.add_command(label="Profondeur 2 (Facile)",    command=lambda: self.set_depth(2))
        ia.add_command(label="Profondeur 4 (Normal)",    command=lambda: self.set_depth(4))
        ia.add_command(label="Profondeur 5 (Difficile)", command=lambda: self.set_depth(5))

    def set_ai_mode(self, m):
        self.cfg["ai_mode"] = m
        save_config(self.cfg)
        messagebox.showinfo("IA", f"Mode : {m.upper()}")

    def set_depth(self, d):
        self.cfg["minimax_depth"] = d
        save_config(self.cfg)
        messagebox.showinfo("Profondeur", f"Minimax : {d}")

    def draw_board(self):
        self.canvas.delete("all")
        CS = self.CS
        for c in range(self.cols):
            self.canvas.create_text(c*CS + CS//2, 25, text=str(c),
                                    font=("Arial", 12, "bold"), fill="white")
        for r in range(self.rows):
            for c in range(self.cols):
                x1, y1 = c*CS, r*CS + 50
                x2, y2 = x1+CS, y1+CS
                cell = self.board[r][c]
                color = (self.cfg["color_x"] if cell == PLAYER_X else
                         self.cfg["color_o"] if cell == PLAYER_O else "white")
                self.canvas.create_oval(x1+4, y1+4, x2-4, y2-4,
                                        fill=color, outline="black", width=2)
        if self.show_scores and self.minimax_scores:
            y = self.rows*CS + 50 + 20
            for col, score in self.minimax_scores.items():
                x = col*CS + CS//2
                color = ("lime" if score > 100 else "green" if score > 0
                         else "red" if score < -100 else "orange" if score < 0 else "white")
                self.canvas.create_text(x, y, text=str(score),
                                        fill=color, font=("Arial", 11, "bold"))

    def click(self, event):
        if self.game_over or self.paused or self.ai_busy or self.replay_mode:
            return
        if self.mode == "ai_vs_ai":
            return
        if event.y < 50:
            return
        col = event.x // self.CS
        if 0 <= col < self.cols:
            self.show_scores = False
            self.minimax_scores = {}
            if self.drop_piece(col):
                self.maybe_trigger_ai()

    def drop_piece(self, col):
        for r in range(self.rows-1, -1, -1):
            if self.board[r][col] == EMPTY:
                self.history.append(copy.deepcopy(self.board))
                self.board[r][col] = self.player
                self.coups_sequence.append(str(col))
                self.numero_coup += 1
                self.draw_board()
                if self.check_end():
                    return True
                self.player = PLAYER_O if self.player == PLAYER_X else PLAYER_X
                self.update_status()
                return True
        return False

    def check_end(self):
        if self.check_win(self.player):
            self.game_over = True
            if self.mode == "ai_vs_ai":
                name = f"IA {self.player}"
            elif self.mode == "ai":
                name = "IA" if self.player == PLAYER_O else "Joueur"
            else:
                name = self.player
            self.status.config(text=f"VICTOIRE {name}", bg="green")
            self.progress_label.config(text="")
            self.show_scores = False
            self.draw_board()
            return True
        if all(self.board[0][c] != EMPTY for c in range(self.cols)):
            self.game_over = True
            self.status.config(text="MATCH NUL", bg="gray")
            self.progress_label.config(text="")
            return True
        return False

    def check_win(self, p):
        b, R, C = self.board, self.rows, self.cols
        for r in range(R):
            for c in range(C-3):
                if all(b[r][c+i] == p for i in range(4)): return True
        for c in range(C):
            for r in range(R-3):
                if all(b[r+i][c] == p for i in range(4)): return True
        for r in range(R-3):
            for c in range(C-3):
                if all(b[r+i][c+i] == p for i in range(4)): return True
        for r in range(3, R):
            for c in range(C-3):
                if all(b[r-i][c+i] == p for i in range(4)): return True
        return False

    def maybe_trigger_ai(self):
        if self.game_over or self.paused or self.ai_busy:
            return
        if self.mode == "pvp":
            return
        if self.mode == "ai" and self.player == PLAYER_X:
            return
        self.after(500, self.ai_turn)

    def ai_turn(self):
        if self.game_over or self.paused or self.ai_busy:
            return
        self.ai_busy = True
        valid = [c for c in range(self.cols) if self.board[0][c] == EMPTY]
        if not valid:
            self.ai_busy = False
            return
        if self.cfg.get("ai_mode") == "random":
            self.progress_label.config(text="Aleatoire")
            best = random.choice(valid)
            self.minimax_scores = {}
            self.show_scores = False
            self.after(300, lambda: self.execute_ai_move(best))
        else:
            depth = self.cfg.get("minimax_depth", 4)
            self.total_nodes = 0
            self.progress_label.config(text=f"Calcul (prof. {depth})...")
            self.progress_label.update_idletasks()
            self.minimax_scores = {}
            best, best_score = valid[0], None
            cur = self.player
            for col in valid:
                row = self.simulate_drop(col, cur)
                if row is not None:
                    opp_is_max = ((PLAYER_O if cur == PLAYER_X else PLAYER_X) == PLAYER_X)
                    score, _ = self.minimax(depth-1, opp_is_max)
                    self.board[row][col] = EMPTY
                    self.minimax_scores[col] = score
                    if best_score is None:
                        best_score, best = score, col
                    elif cur == PLAYER_X and score > best_score:
                        best_score, best = score, col
                    elif cur == PLAYER_O and score < best_score:
                        best_score, best = score, col
            self.show_scores = True
            self.draw_board()
            if best_score is not None:
                self.progress_label.config(
                    text=f"{self.total_nodes} pos | col {best} (score {best_score})")
            self.after(800, lambda: self.execute_ai_move(best))

    def execute_ai_move(self, col):
        if not self.game_over:
            self.drop_piece(col)
        self.show_scores = False
        self.minimax_scores = {}
        self.draw_board()
        self.ai_busy = False
        self.maybe_trigger_ai()

    def minimax(self, depth, is_max, alpha=-float('inf'), beta=float('inf')):
        self.total_nodes += 1
        if self.total_nodes % 500 == 0:
            self.progress_label.config(text=f"{self.total_nodes} pos...")
            self.progress_label.update_idletasks()
        if depth == 0 or self.is_terminal():
            return self.evaluate_board(), None
        valid = [c for c in range(self.cols) if self.board[0][c] == EMPTY]
        if not valid:
            return 0, None
        best_col = valid[0]
        if is_max:
            val = -float('inf')
            for col in valid:
                row = self.simulate_drop(col, PLAYER_X)
                if row is not None:
                    s, _ = self.minimax(depth-1, False, alpha, beta)
                    self.board[row][col] = EMPTY
                    if s > val: val, best_col = s, col
                    alpha = max(alpha, s)
                    if beta <= alpha: break
            return val, best_col
        else:
            val = float('inf')
            for col in valid:
                row = self.simulate_drop(col, PLAYER_O)
                if row is not None:
                    s, _ = self.minimax(depth-1, True, alpha, beta)
                    self.board[row][col] = EMPTY
                    if s < val: val, best_col = s, col
                    beta = min(beta, s)
                    if beta <= alpha: break
            return val, best_col

    def simulate_drop(self, col, player):
        for r in range(self.rows-1, -1, -1):
            if self.board[r][col] == EMPTY:
                self.board[r][col] = player
                return r
        return None

    def is_terminal(self):
        return (self.check_win(PLAYER_X) or self.check_win(PLAYER_O)
                or all(self.board[0][c] != EMPTY for c in range(self.cols)))

    def evaluate_board(self):
        if self.check_win(PLAYER_X):  return  10000
        if self.check_win(PLAYER_O):  return -10000
        score = sum(1 for r in range(self.rows)
                    if self.board[r][self.cols//2] == PLAYER_X) * 3
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != EMPTY:
                    score += self.count_patterns(r, c, self.board[r][c])
        return score

    def count_patterns(self, r, c, player):
        score = 0
        for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
            cnt = 1
            for i in range(1, 4):
                nr, nc = r+dr*i, c+dc*i
                if 0 <= nr < self.rows and 0 <= nc < self.cols and self.board[nr][nc] == player:
                    cnt += 1
                else:
                    break
            mul = 1 if player == PLAYER_X else -1
            if cnt == 2: score += 10  * mul
            if cnt == 3: score += 100 * mul
        return score

    def undo(self):
        if self.history and not self.game_over and not self.ai_busy:
            self.board = self.history.pop()
            if self.coups_sequence: self.coups_sequence.pop()
            self.numero_coup = max(0, self.numero_coup - 1)
            self.player = PLAYER_O if self.player == PLAYER_X else PLAYER_X
            self.show_scores = False
            self.minimax_scores = {}
            self.game_over = False
            self.draw_board()
            self.update_status()

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.status.config(text="PAUSE")
        else:
            self.update_status()
            self.maybe_trigger_ai()

    def update_status(self):
        if self.game_over or self.paused:
            return
        if self.replay_mode:
            self.status.config(
                text=f"REPLAY — Coup {self.replay_index+1}/{len(self.history)}",
                bg="lightblue")
        elif self.mode == "ai_vs_ai":
            self.status.config(text=f"Tour : IA {self.player}", bg=self.default_bg)
        elif self.mode == "ai":
            who = "Joueur (X)" if self.player == PLAYER_X else "IA (O)"
            self.status.config(text=f"Tour : {who}", bg=self.default_bg)
        else:
            self.status.config(text=f"Tour : {self.player}", bg=self.default_bg)

    def replay_first(self):
        if not self.history:
            messagebox.showinfo("Replay", "Aucun historique"); return
        self.replay_mode  = True
        self.replay_index = 0
        self.board = copy.deepcopy(self.history[0])
        self.draw_board(); self.update_status()

    def replay_previous(self):
        if not self.history:
            messagebox.showinfo("Replay", "Aucun historique"); return
        if not self.replay_mode:
            self.replay_mode  = True
            self.replay_index = len(self.history) - 1
        elif self.replay_index > 0:
            self.replay_index -= 1
        else:
            messagebox.showinfo("Replay", "Deja au premier coup"); return
        self.board = copy.deepcopy(self.history[self.replay_index])
        self.draw_board(); self.update_status()

    def replay_next(self):
        if not self.history:
            messagebox.showinfo("Replay", "Aucun historique"); return
        if not self.replay_mode:
            messagebox.showinfo("Replay", "Commencez par Debut"); return
        if self.replay_index < len(self.history) - 1:
            self.replay_index += 1
            self.board = copy.deepcopy(self.history[self.replay_index])
        else:
            self.replay_mode  = False
            self.replay_index = -1
            messagebox.showinfo("Replay", "Fin du replay")
        self.draw_board(); self.update_status()

    def replay_last(self):
        if not self.history:
            messagebox.showinfo("Replay", "Aucun historique"); return
        self.replay_mode  = False
        self.replay_index = -1
        self.board = copy.deepcopy(self.history[-1])
        self.draw_board(); self.update_status()

    def new_game(self):
        self.board          = [[EMPTY]*self.cols for _ in range(self.rows)]
        self.history        = []
        self.game_over      = False
        self.paused         = False
        self.ai_busy        = False
        self.player         = self.cfg["first_player"]
        self.minimax_scores = {}
        self.show_scores    = False
        self.numero_coup    = 0
        self.partie_id      = None
        self.coups_sequence = []
        self.temps_debut    = time.time()
        self.replay_mode    = False
        self.replay_index   = -1
        self.draw_board(); self.update_status()
        self.progress_label.config(text="")
        self.maybe_trigger_ai()

    def save_game(self):
        os.makedirs(SAVES_DIR, exist_ok=True)
        f = filedialog.asksaveasfilename(
            defaultextension=".json", initialdir=SAVES_DIR,
            filetypes=[("JSON", "*.json"), ("Tous", "*.*")])
        if not f: return

        sequence = ''.join(self.coups_sequence)
        with open(f, "w") as fh:
            json.dump({
                "board": self.board, "player": self.player, "mode": self.mode,
                "history": self.history, "game_over": self.game_over,
                "numero_coup": self.numero_coup, "sequence": sequence,
                "rows": self.rows, "cols": self.cols
            }, fh, indent=2)

        duree = int(time.time() - self.temps_debut)
        gagnant_id = None
        if self.game_over:
            if self.check_win(PLAYER_X):   gagnant_id = self.joueur1_id
            elif self.check_win(PLAYER_O): gagnant_id = self.joueur2_id

        if self.db and self.joueur1_id and self.joueur2_id and sequence:
            self.partie_id = self.db.save_partie_complete(
                self.joueur1_id, self.joueur2_id, gagnant_id,
                sequence, duree,
                nb_lignes=self.rows, nb_colonnes=self.cols
            )
            if self.partie_id:
                messagebox.showinfo("Sauvegarde",
                    f"Sauvegarde reussie !\nFichier : {f}\nBDD (ID: {self.partie_id})\nSequence: {sequence}")
            else:
                messagebox.showwarning("Partiel", "Fichier local OK\nEchec BDD")
        else:
            messagebox.showinfo("Sauvegarde locale", f"Sauvegarde reussie !\n{f}")

    def load_game(self):
        f = filedialog.askopenfilename(initialdir=SAVES_DIR)
        if not f: return
        with open(f, "r") as fh:
            d = json.load(fh)
        self.board          = d["board"]
        self.player         = d["player"]
        self.mode           = d.get("mode", self.mode)
        self.history        = d.get("history", [])
        self.game_over      = d.get("game_over", False)
        self.numero_coup    = d.get("numero_coup", 0)
        self.coups_sequence = list(d.get("sequence", ""))
        self.rows           = d.get("rows", self.rows)
        self.cols           = d.get("cols", self.cols)
        self.paused         = False
        self.ai_busy        = False
        self.show_scores    = False
        self.minimax_scores = {}
        self.draw_board(); self.update_status()
        messagebox.showinfo("Chargement", "Partie chargee !")
        self.maybe_trigger_ai()
