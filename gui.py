import tkinter as tk
from tkinter import messagebox, Toplevel, Listbox, END, filedialog
import json
import os
import random
from constants import *
from game_logic import GameLogic
from save_system import *
from ai import coup_ia_minimax
from database import Database

class Puissance4GUI:
    def __init__(self):
        self.logic = GameLogic()
        self.db = Database()      # Connexion BDD SQL
        self.tour_rouge = (COULEUR_DEPART == ROUGE)
        self.mode = "ia"          # "ia", "pvp", "ia_ia"
        self.ai_running = False   # pour IA vs IA
        self.moves = []           # pile des coups (l, c, joueur)
        self.dernier_coup = None  # (l, c) du dernier jeton posé
        
        self.root = tk.Tk()
        self.root.title("Puissance 4 - Expert L3 (Missions 2.0 - 2.2)")
        self.root.configure(bg="black")
        self.creer_ui()
        self.dessiner_grille()

    def creer_ui(self):
        main_frame = tk.Frame(self.root, bg="black")
        main_frame.pack(padx=10, pady=10)
        
        # --- Zone Plateau (Canvas) ---
        self.canvas = tk.Canvas(
            main_frame,
            width=COLONNES * TAILLE_CASE,
            height=LIGNES * TAILLE_CASE + 40,
            bg="black"
        )
        self.canvas.pack(side="left")
        self.canvas.bind("<Button-1>", self.clic)

        # --- Panneau de Contrôle (Droite) ---
        info_frame = tk.Frame(main_frame, bg="black", padx=20)
        info_frame.pack(side="right", fill="y")

        # Modes de jeu
        tk.Label(info_frame, text="Mode de Jeu", font=("Arial", 12, "bold"), bg="black", fg="white").pack(pady=5)
        self.mode_var = tk.StringVar(value="ia")
        tk.Radiobutton(info_frame, text="Joueur vs IA", variable=self.mode_var, value="ia", 
                       command=self.reset_mode, bg="black", fg="white", selectcolor="gray").pack(anchor="w")
        tk.Radiobutton(info_frame, text="Joueur vs Joueur", variable=self.mode_var, value="pvp", 
                       command=self.reset_mode, bg="black", fg="white", selectcolor="gray").pack(anchor="w")
        tk.Radiobutton(info_frame, text="🤖 IA vs IA", variable=self.mode_var, value="ia_ia", 
                       command=self.reset_mode, bg="black", fg="yellow", selectcolor="gray").pack(anchor="w")

        # --- Type d'IA ---
        tk.Label(info_frame, text="Comportement IA", font=("Arial", 10, "bold"), bg="black", fg="white").pack(pady=(10, 0))
        self.type_ia_var = tk.StringVar(value="minimax")
        tk.Radiobutton(info_frame, text="Aléatoire", variable=self.type_ia_var, value="aleatoire", bg="black", fg="white", selectcolor="gray").pack(anchor="w")
        tk.Radiobutton(info_frame, text="Minimax", variable=self.type_ia_var, value="minimax", bg="black", fg="white", selectcolor="gray").pack(anchor="w")

        # Labels Tour / État
        self.tour_label = tk.Label(info_frame, text="Tour: Rouge", font=("Arial", 11), bg="black", fg="white")
        self.tour_label.pack(pady=10)
        self.etat_label = tk.Label(info_frame, text="Prêt", font=("Arial", 11), bg="black", fg="gray")
        self.etat_label.pack(pady=5)

        # --- Mission 2.0 : Réglages IA ---
        tk.Label(info_frame, text="--- IA Minimax ---", bg="black", fg="cyan").pack(pady=(15, 2))
        tk.Label(info_frame, text="Profondeur:", bg="black", fg="white").pack()
        self.scale_prof = tk.Scale(info_frame, from_=1, to=8, orient="horizontal", bg="gray20", fg="white")
        self.scale_prof.set(4)
        self.scale_prof.pack(pady=2)

        # --- Mission 2.1 & 2.2 : Base de Données ---
        tk.Label(info_frame, text="--- BDD & Outils ---", bg="black", fg="orange").pack(pady=(15, 2))
        tk.Button(info_frame, text="💾 Sauver en BDD", command=self.sauver_bdd, bg="#00aa00", fg="white", width=18).pack(pady=2)
        tk.Button(info_frame, text="📂 Voir / Reprendre", command=self.voir_bdd, bg="#0066cc", fg="white", width=18).pack(pady=2)
        tk.Button(info_frame, text="📄 Importer Fichier", command=self.importer_fichier, bg="#e67e22", fg="white", width=18).pack(pady=2)

        # --- Contrôles Jeu (Undo / Reset / Paramètres) ---
        tk.Label(info_frame, text="--- Actions ---", bg="black", fg="white").pack(pady=(15, 2))
        btn_box = tk.Frame(info_frame, bg="black")
        btn_box.pack()
        tk.Button(btn_box, text="↩ Undo", command=self.undo, bg="purple", fg="white").pack(side="left", padx=2)
        tk.Button(btn_box, text="🔄 Reset", command=self.reset_mode, bg="red", fg="white").pack(side="left", padx=2)
        
        tk.Button(info_frame, text="⚙️ Paramètres", command=self.ouvrir_parametres, bg="gray", fg="white", width=18).pack(pady=5)

        # --- Zone Basse : Affichage Poids IA ---
        self.lbl_poids = tk.Label(self.root, text="Poids IA: En attente...", bg="black", fg="lime", font=("Consolas", 10))
        self.lbl_poids.pack(side="bottom", fill="x", pady=5)

    def _update_progress(self, col_en_cours, dict_poids):
        """Met à jour l'interface pendant que le Minimax tourne"""
        txt = f"L'IA réfléchit... Analyse Col {col_en_cours} | "
        txt += " ".join([f"{k}:{v}" for k,v in dict_poids.items() if v != "X"])
        self.lbl_poids.config(text=txt)
        self.root.update()

    def ouvrir_parametres(self):
        """Ouvre la fenêtre de configuration (Mission 1.2)"""
        top = Toplevel(self.root)
        top.title("Configuration")
        top.geometry("300x250")
        
        tk.Label(top, text="Lignes :").pack(pady=5)
        var_l = tk.IntVar(value=LIGNES)
        tk.Entry(top, textvariable=var_l).pack()

        tk.Label(top, text="Colonnes :").pack(pady=5)
        var_c = tk.IntVar(value=COLONNES)
        tk.Entry(top, textvariable=var_c).pack()

        tk.Label(top, text="Qui commence ? (1=Rouge, 2=Jaune) :").pack(pady=5)
        var_j = tk.IntVar(value=COULEUR_DEPART)
        tk.Entry(top, textvariable=var_j).pack()

        def sauver_et_quitter():
            data = {"lignes": var_l.get(), "colonnes": var_c.get(), "couleur_depart": var_j.get()}
            with open("config.json", "w") as f:
                json.dump(data, f)
            messagebox.showinfo("Succès", "Configuration sauvegardée !\nVeuillez relancer le jeu pour appliquer les dimensions.")
            top.destroy()

        tk.Button(top, text="Enregistrer", command=sauver_et_quitter, bg="green", fg="white").pack(pady=15)

    def update_labels(self):
        modes = {
            "ia": ("Joueur vs IA", "Joueur" if self.tour_rouge else "IA"),
            "pvp": ("Joueur vs Joueur", f"Joueur {'1' if self.tour_rouge else '2'}"),
            "ia_ia": ("🤖 IA vs IA", "IA Rouge" if self.tour_rouge else "IA Jaune")
        }
        mode_text, tour_text = modes.get(self.mode, ("Inconnu", "Inconnu"))
        self.tour_label.config(text=f"Tour: {tour_text}")
        self.etat_label.config(text=mode_text)

    def reset_mode(self):
        self.ai_running = False
        self.canvas.unbind("<Button-1>")
        self.canvas.bind("<Button-1>", self.clic)
        
        self.logic = GameLogic()
        self.tour_rouge = (COULEUR_DEPART == ROUGE)
        self.mode = self.mode_var.get()
        self.logic.partie_finie = False
        self.moves = []
        self.dernier_coup = None
        self.logic.aligne = []

        self.update_labels()
        self.dessiner_grille()
        self.lbl_poids.config(text="Poids IA: Nouvelle partie")
        
        if self.mode == "ia_ia":
            self.ai_running = True
            self.root.after(500, self.ia_auto)

    def dessiner_grille(self):
        self.canvas.delete("all")
        for l in range(LIGNES):
            for c in range(COLONNES):
                x = c * TAILLE_CASE + TAILLE_CASE//2
                y = l * TAILLE_CASE + TAILLE_CASE//2
                val = self.logic.grille[l][c]
                
                col = "lightgray"
                if val == ROUGE: col = "red"
                elif val == JAUNE: col = "yellow"
                
                outline = "white"
                width = 2
                
                if (l, c) in getattr(self.logic, "aligne", []):
                    outline = "#00ff00"
                    width = 5
                elif self.dernier_coup == (l, c):
                    outline = "cyan"
                    width = 4
                
                self.canvas.create_oval(
                    x - RAYON_PION, y - RAYON_PION,
                    x + RAYON_PION, y + RAYON_PION,
                    fill=col, outline=outline, width=width
                )

        y_text = LIGNES * TAILLE_CASE + 20
        for c in range(COLONNES):
            x = c * TAILLE_CASE + TAILLE_CASE//2
            self.canvas.create_text(
                x, y_text,
                text=str(c),
                fill="white", font=("Arial", 12, "bold")
            )

    def clic(self, event):
        if self.logic.partie_finie or self.mode == "ia_ia": return
        col = event.x // TAILLE_CASE
        if not self.logic.colonne_valide(col): return
        
        joueur = ROUGE if self.tour_rouge else JAUNE
        if self.mode == "ia" and not self.tour_rouge: return
        
        l = self.logic.placer_pion(col, joueur)
        if l is None: return

        self.moves.append((l, col, joueur))
        self.dernier_coup = (l, col)
        self.dessiner_grille()
        self.check_fin(joueur)

    def check_fin(self, joueur):
        if self.logic.victoire(joueur):
            self.dessiner_grille()
            win_txt = "GAGNÉ !"
            if self.mode == "ia": win_txt = "Tu gagnes !" if joueur == ROUGE else "L'IA gagne !"
            elif self.mode == "ia_ia": win_txt = f"IA {'Rouge' if joueur==ROUGE else 'Jaune'} gagne"
            self.fin_partie(win_txt)
            return
        
        if self.logic.grille_pleine():
            self.fin_partie("Match nul !")
            return
        
        self.tour_rouge = not self.tour_rouge
        self.update_labels()
        
        if self.mode == "ia" and not self.tour_rouge:
            self.root.after(100, self.ia_turn)

    def ia_turn(self):
        if self.logic.partie_finie: return
        
        if self.type_ia_var.get() == "aleatoire":
            valid_cols = [c for c in range(COLONNES) if self.logic.colonne_valide(c)]
            col = random.choice(valid_cols) if valid_cols else None
            self.lbl_poids.config(text="[IA Aléatoire] Coup joué au hasard.")
        else:
            prof = self.scale_prof.get()
            col, poids = coup_ia_minimax(self.logic, prof, self._update_progress)
            txt_poids = " | ".join([f"{k}:{v}" for k,v in poids.items()])
            self.lbl_poids.config(text=f"[IA Minimax Prof {prof}] Terminé ! Poids: {txt_poids}")

        if col is None:
            self.fin_partie("Match nul")
            return
            
        l = self.logic.placer_pion(col, JAUNE)
        self.moves.append((l, col, JAUNE))
        self.dernier_coup = (l, col)
        self.dessiner_grille()
        self.check_fin(JAUNE)

    def ia_auto(self):
        if not self.ai_running or self.logic.partie_finie: return
        joueur = ROUGE if self.tour_rouge else JAUNE

        if self.type_ia_var.get() == "aleatoire":
            valid_cols = [c for c in range(COLONNES) if self.logic.colonne_valide(c)]
            col = random.choice(valid_cols) if valid_cols else None
            self.lbl_poids.config(text="[IA Aléatoire] Coup joué au hasard.")
        else:
            prof = self.scale_prof.get()
            col, _ = coup_ia_minimax(self.logic, prof, self._update_progress) 
        
        if col is None:
            self.fin_partie("Match nul")
            return

        l = self.logic.placer_pion(col, joueur)
        self.moves.append((l, col, joueur))
        self.dernier_coup = (l, col)
        self.dessiner_grille()
        
        if self.logic.victoire(joueur):
            self.dessiner_grille()
            self.fin_partie(f"IA {'Rouge' if joueur==ROUGE else 'Jaune'} gagne")
            self.ai_running = False
            return
        
        if self.logic.grille_pleine():
            self.fin_partie("Match nul")
            self.ai_running = False
            return

        self.tour_rouge = not self.tour_rouge
        self.update_labels()
        self.root.after(200, self.ia_auto)

    def undo(self):
        if self.mode == "ia_ia" or self.logic.partie_finie: return
        if not self.moves: return

        l, c, joueur = self.moves.pop()
        self.logic.grille[l][c] = VIDE
        
        if self.moves:
            last = self.moves[-1]
            self.dernier_coup = (last[0], last[1])
        else:
            self.dernier_coup = None

        self.tour_rouge = (joueur == ROUGE)
        self.logic.partie_finie = False
        self.logic.aligne = []
        
        self.update_labels()
        self.dessiner_grille()
        self.lbl_poids.config(text="Coup annulé")

    # --- Gestion BDD ---
    def sauver_bdd(self):
        vainqueur = "Indéfini"
        if self.logic.partie_finie:
            last_j = self.moves[-1][2] if self.moves else 0
            vainqueur = "Rouge" if last_j == ROUGE else "Jaune"
        
        ok, msg = self.db.sauvegarder(vainqueur, self.moves)
        if ok: messagebox.showinfo("BDD", f"Partie sauvegardée !\nID: {msg}")
        else: messagebox.showwarning("BDD", f"Erreur ou doublon:\n{msg}")

    # --- Import Fichier ---
    def importer_fichier(self):
        filepath = filedialog.askopenfilename(filetypes=[("Fichiers Texte", "*.txt")])
        if not filepath: return
        
        filename = os.path.basename(filepath)
        moves_str = filename.split('.')[0] 
        
        if not moves_str.isdigit():
            messagebox.showerror("Erreur", "Le nom du fichier doit contenir uniquement des chiffres.")
            return
            
        temp_logic = GameLogic()
        temp_moves = []
        tour_r = True
        
        for char in moves_str:
            col = int(char)
            if not temp_logic.colonne_valide(col):
                messagebox.showerror("Erreur", f"Coup invalide col {col}")
                return
            j = ROUGE if tour_r else JAUNE
            l = temp_logic.placer_pion(col, j)
            temp_moves.append((l, col, j))
            if temp_logic.victoire(j) or temp_logic.grille_pleine():
                break
            tour_r = not tour_r
            
        vainqueur = "Indéfini"
        if temp_logic.victoire(ROUGE): vainqueur = "Rouge"
        elif temp_logic.victoire(JAUNE): vainqueur = "Jaune"
        
        ok, msg = self.db.sauvegarder(vainqueur, temp_moves)
        if ok: messagebox.showinfo("Import", f"Partie importée ID {msg}")
        else: messagebox.showwarning("Import", f"Erreur: {msg}")

    # --- Replay & Reprise ---
    def voir_bdd(self):
        top = Toplevel(self.root)
        top.title("Explorateur BDD")
        top.geometry("600x500")
        
        lb = Listbox(top, font=("Consolas", 10))
        lb.pack(fill="both", expand=True, padx=10, pady=5)
        
        parties_cache = []

        def rafraichir_liste():
            nonlocal parties_cache
            lb.delete(0, END)
            parties_cache = self.db.recuperer_tout()
            for p in parties_cache:
                info_sym = f" (Sym: {p[4]})" if p[4] else ""
                lb.insert(END, f"ID {p[0]} | {p[1]} | {p[2]}{info_sym}")

        rafraichir_liste()

        def charger_pour_jouer():
            sel = lb.curselection()
            if not sel: return
            idx = sel[0]
            coups = json.loads(parties_cache[idx][3])
            
            self.reset_mode()
            for l, c, j in coups:
                self.logic.grille[l][c] = j
                self.moves.append((l, c, j))
            
            if self.moves:
                last = self.moves[-1]
                self.dernier_coup = (last[0], last[1])
                self.tour_rouge = (last[2] != ROUGE)
            
            victoire = False
            for j in [ROUGE, JAUNE]:
                if self.logic.victoire(j):
                    self.logic.partie_finie = True
                    self.etat_label.config(text=f"Finie: {j} gagne")
                    victoire = True
            
            if not victoire:
                self.etat_label.config(text="Partie chargée - À vous !")
                
            self.dessiner_grille()
            self.update_labels()
            top.destroy()

        def lancer_replay():
            sel = lb.curselection()
            if not sel: return
            idx = sel[0]
            coups = json.loads(parties_cache[idx][3])
            self.ouvrir_replay(coups, parties_cache[idx][0])

        def supprimer_selection():
            sel = lb.curselection()
            if not sel: return
            idx = sel[0]
            p_id = parties_cache[idx][0]
            if messagebox.askyesno("Confirmer", f"Supprimer ID {p_id} ?"):
                self.db.supprimer(p_id)
                rafraichir_liste()

        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="🎮 Reprendre", command=charger_pour_jouer, bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="▶️ Replay", command=lancer_replay, bg="#2980b9", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ Supprimer", command=supprimer_selection, bg="#c0392b", fg="white").pack(side="left", padx=5)
        
        tk.Button(top, text="📂 Importer Fichier", command=self.importer_fichier, bg="orange").pack(pady=5)

    def ouvrir_replay(self, coups_complets, p_id):
        rep = Toplevel(self.root)
        rep.title(f"Replay ID {p_id}")
        rep.geometry("550x600")
        rep.configure(bg="black")
        
        cv = tk.Canvas(rep, width=COLONNES*TAILLE_CASE, height=LIGNES*TAILLE_CASE, bg="black")
        cv.pack(pady=10)
        
        lbl_info = tk.Label(rep, text="Début du replay", fg="white", bg="black", font=("Arial", 12))
        lbl_info.pack()
        
        index_coup = 0 
        replay_logic = GameLogic()
        
        def dessiner_replay(last_played=None):
            cv.delete("all")
            for l in range(LIGNES):
                for c in range(COLONNES):
                    x, y = c*TAILLE_CASE+30, l*TAILLE_CASE+30
                    val = replay_logic.grille[l][c]
                    
                    col = "lightgray"
                    if val == ROUGE: col = "red"
                    elif val == JAUNE: col = "yellow"
                    
                    outline = "white"
                    width = 2
                    if last_played == (l,c):
                         outline = "cyan"
                         width = 4
                         
                    cv.create_oval(x-25, y-25, x+25, y+25, fill=col, outline=outline, width=width)
        
        def coup_suivant():
            nonlocal index_coup
            if index_coup < len(coups_complets):
                l, c, j = coups_complets[index_coup]
                replay_logic.grille[l][c] = j
                index_coup += 1
                dessiner_replay((l,c))
                lbl_info.config(text=f"Coup {index_coup} / {len(coups_complets)}")
        
        def coup_precedent():
            nonlocal index_coup
            if index_coup > 0:
                index_coup -= 1
                l, c, j = coups_complets[index_coup]
                replay_logic.grille[l][c] = VIDE
                
                prev = None
                if index_coup > 0:
                    pl, pc, _ = coups_complets[index_coup-1]
                    prev = (pl, pc)
                    
                dessiner_replay(prev)
                lbl_info.config(text=f"Coup {index_coup} / {len(coups_complets)}")

        frm_btn = tk.Frame(rep, bg="black")
        frm_btn.pack(pady=10)
        tk.Button(frm_btn, text="<< Précédent", command=coup_precedent, bg="gray", fg="white", width=15).pack(side="left", padx=5)
        tk.Button(frm_btn, text="Suivant >>", command=coup_suivant, bg="gray", fg="white", width=15).pack(side="left", padx=5)
        
        dessiner_replay()

    def fin_partie(self, msg):
        self.logic.partie_finie = True
        self.ai_running = False
        self.canvas.unbind("<Button-1>")
        self.canvas.create_text(
            COLONNES * TAILLE_CASE//2,
            LIGNES * TAILLE_CASE//2,
            text=msg, fill="white", font=("Arial", 26, "bold"), justify="center"
        )
        self.etat_label.config(text="Partie terminée")

    def run(self):
        self.root.mainloop()