

import tkinter as tk
from tkinter import messagebox, filedialog
import json
import copy
import time
import os
import random

# ==================== CONSTANTES ====================

CELL_SIZE = 80
CONFIG_FILE = "config.json"
SAVES_DIR = "saves"

EMPTY = " "
PLAYER_X = "X"
PLAYER_O = "O"

# ==================== CONFIG ====================

def load_config():
    default_config = {
        "rows": 6,
        "cols": 7,
        "first_player": "X",
        "color_x": "red",
        "color_o": "yellow"
    }
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config

    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return default_config

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ==================== MENU ====================

class MenuSelection(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.choice = None

        self.title("Puissance 4 - Menu")
        self.geometry("300x450") 
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.quit_game)

        tk.Label(self, text="🎮 PUISSANCE 4 🎮",
                 font=("Arial", 20, "bold")).pack(pady=20)

        tk.Button(self, text="👥 Joueur vs Joueur",
                  width=25, height=2,
                  command=lambda: self.select("pvp")).pack(pady=5)

        tk.Button(self, text="🤖 Joueur vs IA",
                  width=25, height=2,                        
                  command=lambda: self.select("ai")).pack(pady=5)

        tk.Button(self, text="🤖🆚🤖 IA vs IA",
                  width=25, height=2,                        
                  command=lambda: self.select("ai_vs_ai")).pack(pady=5)

        tk.Button(self, text="❌ Quitter",
                  width=25, height=2,
                  command=self.quit_game).pack(pady=5)

        self.grab_set()
        self.wait_window()

    def select(self, mode):
        self.choice = mode
        self.destroy()

    def quit_game(self):
        self.choice = "quit"
        self.destroy()

# ==================== JEU ====================

class Puissance4(tk.Frame):
    def __init__(self, master, mode):
        super().__init__(master)
        self.pack()

        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR)

        self.cfg = load_config()
        self.rows = self.cfg["rows"]
        self.cols = self.cfg["cols"]
        self.player = self.cfg["first_player"]
        self.mode = mode  # "pvp", "ai", "ai_vs_ai"

        self.board = [[EMPTY]*self.cols for _ in range(self.rows)]
        self.history = []
        self.game_index = int(time.time())
        self.game_over = False
        self.paused = False
        self.winner = None

        title_text = f"Puissance 4 | Partie #{self.game_index}"
        if self.mode == "ai_vs_ai":
            title_text += " | IA vs IA"
        master.title(title_text)

        self.canvas = tk.Canvas(
            self,
            width=self.cols * CELL_SIZE,
            height=self.rows * CELL_SIZE,
            bg="#0000AA"
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.click)

        self.status = tk.Label(self, font=("Arial", 12, "bold"))
        self.status.pack(fill="x")

        self.create_menu(master)
        self.draw_board()
        self.update_status()

        # Si mode IA vs IA, lancer le premier coup automatiquement
        if self.mode == "ai_vs_ai":
            self.after(1000, self.ai_turn)

    # ==================== MENU BAR ====================

    def create_menu(self, root):
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        game = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Jeu", menu=game)
        game.add_command(label="Nouvelle partie", command=self.new_game)
        game.add_command(label="Pause / Reprendre", command=self.toggle_pause)
        game.add_separator()
        game.add_command(label="Sauvegarder", command=self.save_game)
        game.add_command(label="Charger", command=self.load_game)
        game.add_separator()
        game.add_command(label="Quitter", command=root.quit)

        edit = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edition", menu=edit)
        edit.add_command(label="Annuler coup", command=self.undo)

    # ==================== AFFICHAGE ====================

    def draw_board(self):
        self.canvas.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                x1, y1 = c*CELL_SIZE, r*CELL_SIZE
                x2, y2 = x1+CELL_SIZE, y1+CELL_SIZE
                color = "white"
                if self.board[r][c] == PLAYER_X:
                    color = self.cfg["color_x"]
                elif self.board[r][c] == PLAYER_O:
                    color = self.cfg["color_o"]
                self.canvas.create_oval(x1+5, y1+5, x2-5, y2-5,
                                        fill=color, outline="black")

    # ==================== JEU ====================

    def click(self, event):
        if self.game_over or self.paused:
            return
        
        # En mode IA vs IA, empêcher le joueur de cliquer
        if self.mode == "ai_vs_ai":
            return
            
        col = event.x // CELL_SIZE
        if 0 <= col < self.cols:
            if self.drop_piece(col) and self.mode == "ai" and self.player == PLAYER_O:
                self.after(500, self.ai_turn)

    def drop_piece(self, col):
        for r in range(self.rows-1, -1, -1):
            if self.board[r][col] == EMPTY:
                self.history.append(copy.deepcopy(self.board))
                self.board[r][col] = self.player
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
            winner_name = "IA X" if self.mode == "ai_vs_ai" else self.player
            if self.mode == "ai_vs_ai" and self.player == PLAYER_O:
                winner_name = "IA O"
            self.status.config(text=f"VICTOIRE {winner_name}", bg="green")
            return True
        if all(self.board[0][c] != EMPTY for c in range(self.cols)):
            self.game_over = True
            self.status.config(text="MATCH NUL", bg="gray")
            return True
        return False

    def check_win(self, p):
        for r in range(self.rows):
            for c in range(self.cols-3):
                if all(self.board[r][c+i] == p for i in range(4)):
                    return True
        for c in range(self.cols):
            for r in range(self.rows-3):
                if all(self.board[r+i][c] == p for i in range(4)):
                    return True
        for r in range(self.rows-3):
            for c in range(self.cols-3):
                if all(self.board[r+i][c+i] == p for i in range(4)):
                    return True
        for r in range(3, self.rows):
            for c in range(self.cols-3):
                if all(self.board[r-i][c+i] == p for i in range(4)):
                    return True
        return False

    # ==================== IA ====================

    def ai_turn(self):
        if self.game_over or self.paused:
            return
       valid = [c for c in range(self.cols) if self.board[0][c] == EMPTY]
        if valid:
        # Utiliser Minimax avec profondeur 4
            _, best_col = self.minimax(depth=4, is_maximizing=(self.player == PLAYER_X))  # ← ICI !
        
            if best_col is not None:
                self.drop_piece(best_col)
            else:
            # Fallback sur aléatoire si erreur
                self.drop_piece(random.choice(valid))
        
        # En mode IA vs IA, continuer à jouer automatiquement
            if self.mode == "ai_vs_ai" and not self.game_over:
                self.after(800, self.ai_turn)
    # ==================== UTILITAIRES ====================

    def undo(self):
        if self.history and not self.game_over:
            self.board = self.history.pop()
            self.player = PLAYER_O if self.player == PLAYER_X else PLAYER_X
            self.draw_board()
            self.update_status()

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.status.config(text="⏸ PAUSE")
        else:
            self.update_status()
            # Reprendre le jeu IA vs IA si nécessaire
            if self.mode == "ai_vs_ai" and not self.game_over:
                self.after(800, self.ai_turn)

    def update_status(self):    
        if not self.game_over and not self.paused:
            if self.mode == "ai_vs_ai":
                self.status.config(text=f"Tour : IA {self.player}")
            else:
                self.status.config(text=f"Tour : {self.player}")

    def new_game(self):
        self.board = [[EMPTY]*self.cols for _ in range(self.rows)]  
        self.history.clear()
        self.game_over = False   
        self.paused = False
        self.player = self.cfg["first_player"]
        self.draw_board()
        self.update_status()
        
        # Relancer l'IA vs IA si c'est le mode actif
        if self.mode == "ai_vs_ai":
            self.after(1000, self.ai_turn)

    def save_game(self):
        f = filedialog.asksaveasfilename(defaultextension=".json")
        if f:
            json.dump({
                "board": self.board,
                "player": self.player,
                "mode": self.mode
            }, open(f, "w"))

    def load_game(self):
        f = filedialog.askopenfilename()
        if f:
            data = json.load(open(f))
            self.board = data["board"]
            self.player = data["player"]
            if "mode" in data:
                self.mode = data["mode"]
            self.draw_board()
            self.update_status()

# ==================== MAIN ====================

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()   

    menu = MenuSelection(root)

    if menu.choice == "quit":
        root.destroy()
        exit()

    root.deiconify()
    Puissance4(root, mode=menu.choice)
    root.mainloop()
    