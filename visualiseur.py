
"""
VISUALISEUR - Puissance 4
Corrections :
  - Grille dynamique selon nb_lignes/nb_colonnes de la partie en BDD
  - Vue normale / symétrique : toggle propre et fiable
  - Bouton Supprimer la partie sélectionnée
  - Tous les boutons de navigation fonctionnent
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from database import DatabaseManager

EMPTY   = " "
PLAYER_X = "X"
PLAYER_O = "O"

# Taille de cellule par défaut (réduite auto si grille > 7 colonnes)
BASE_CELL = 60


class VisualiseurBDD(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Visualiseur Puissance 4 - Base de Donnees")
        self.geometry("1450x920")

        # ---- État interne ----
        self.parties              = []      # toutes les parties récupérées
        self.partie_selectionnee  = None
        self.coups_partie         = []
        self.coup_index           = 0
        self.nb_lignes            = 6
        self.nb_colonnes          = 7
        self.cell_size            = BASE_CELL
        self.plateau              = [[EMPTY]*7 for _ in range(6)]
        # Vue symétrique : True = affichage miroir
        self.mode_symetrique      = False

        self._build_ui()
        self.refresh_parties()

    # ================================================================
    # CONSTRUCTION DE L'INTERFACE
    # ================================================================

    def _build_ui(self):
        # ---- Menu ----
        bar = tk.Menu(self)
        self.config(menu=bar)

        m_fichier = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="Fichier", menu=m_fichier)
        m_fichier.add_command(label="Rafraichir", command=self.refresh_parties)
        m_fichier.add_separator()
        m_fichier.add_command(label="Quitter", command=self.quit)

        m_bdd = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="Base de Donnees", menu=m_bdd)
        m_bdd.add_command(label="Voir toutes les tables",       command=self.voir_tables)
        m_bdd.add_command(label="Statistiques joueurs",         command=self.voir_stats_joueurs)
        m_bdd.add_separator()
        m_bdd.add_command(label="Generer des parties aleatoires", command=self.generer_parties)

        m_aide = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="Aide", menu=m_aide)
        m_aide.add_command(label="Guide", command=self.show_help)
        m_aide.add_command(label="A propos", command=self.show_about)

        # ---- Colonne gauche : liste ----
        left = tk.Frame(self, width=370, bg="#f0f0f0")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        left.pack_propagate(False)

        tk.Label(left, text="LISTE DES PARTIES",
                 font=("Arial", 13, "bold"), bg="#4CAF50", fg="white",
                 pady=8).pack(fill=tk.X)

        # Filtres
        ff = tk.Frame(left, bg="#f0f0f0")
        ff.pack(fill=tk.X, pady=4, padx=5)
        tk.Label(ff, text="Statut:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.filter_statut = ttk.Combobox(
            ff, values=["Tous", "terminee", "en_cours", "abandonnee"],
            state="readonly", width=12)
        self.filter_statut.set("Tous")
        self.filter_statut.pack(side=tk.LEFT, padx=5)
        self.filter_statut.bind("<<ComboboxSelected>>", lambda e: self.refresh_parties())
        tk.Button(ff, text="Rafraichir", command=self.refresh_parties,
                  bg="#2196F3", fg="white").pack(side=tk.LEFT)

        # Liste
        lf = tk.Frame(left)
        lf.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        sb = tk.Scrollbar(lf)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(lf, yscrollcommand=sb.set,
                                  font=("Courier", 9), selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        sb.config(command=self.listbox.yview)

        # Bouton Supprimer (en bas de la liste)
        tk.Button(left, text="Supprimer la partie selectionnee",
                  command=self.supprimer_partie,
                  bg="#f44336", fg="white",
                  font=("Arial", 10, "bold"), pady=6).pack(fill=tk.X, padx=5, pady=4)

        self.stats_lbl = tk.Label(left, text="Total: 0 parties",
                                  font=("Arial", 10), bg="#e0e0e0", pady=4)
        self.stats_lbl.pack(fill=tk.X)

        # ---- Colonne droite : visualisation ----
        right = tk.Frame(self, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.info_lbl = tk.Label(right,
            text="Selectionnez une partie dans la liste",
            font=("Arial", 12, "bold"), bg="#2196F3", fg="white", pady=8)
        self.info_lbl.pack(fill=tk.X)

        # Canvas (redimensionné dynamiquement à chaque sélection)
        canvas_frame = tk.Frame(right, bg="white")
        canvas_frame.pack(pady=8)

        self.canvas = tk.Canvas(canvas_frame,
                                width=9*BASE_CELL, height=9*BASE_CELL+40,
                                bg="#0066CC",
                                highlightthickness=2, highlightbackground="#004080")
        self.canvas.pack()

        # Navigation
        nav = tk.Frame(right, bg="white")
        nav.pack(pady=10)

        row1 = tk.Frame(nav, bg="white")
        row1.pack(pady=4)

        btn_cfg = dict(height=2, bg="#FF9800", fg="white", font=("Arial", 10, "bold"))
        tk.Button(row1, text="Debut",     command=self.goto_debut,     width=11, **btn_cfg).pack(side=tk.LEFT, padx=4)
        tk.Button(row1, text="Precedent", command=self.coup_precedent, width=11, **btn_cfg).pack(side=tk.LEFT, padx=4)

        self.coup_lbl = tk.Label(row1, text="Coup 0/0",
                                 font=("Arial", 12, "bold"), bg="#FFC107", fg="black",
                                 width=11, height=2, relief=tk.RAISED)
        self.coup_lbl.pack(side=tk.LEFT, padx=4)

        tk.Button(row1, text="Suivant", command=self.coup_suivant, width=11, **btn_cfg).pack(side=tk.LEFT, padx=4)
        tk.Button(row1, text="Fin",     command=self.goto_fin,     width=11, **btn_cfg).pack(side=tk.LEFT, padx=4)

        row2 = tk.Frame(nav, bg="white")
        row2.pack(pady=4)

        # Bouton symétrique — état géré par self.mode_symetrique
        self.btn_sym = tk.Button(row2,
            text="Voir Partie Symetrique",
            command=self.toggle_symetrique,
            width=38, height=2,
            bg="#9C27B0", fg="white",
            font=("Arial", 11, "bold"),
            state=tk.DISABLED)
        self.btn_sym.pack()

        # Détails
        det_frame = tk.LabelFrame(right, text="Details de la Partie",
                                  font=("Arial", 11, "bold"), bg="white")
        det_frame.pack(fill=tk.BOTH, expand=True, pady=8, padx=8)

        self.details_txt = scrolledtext.ScrolledText(det_frame, height=12,
                                                     font=("Courier", 10),
                                                     bg="#f9f9f9", wrap=tk.WORD)
        self.details_txt.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    # ================================================================
    # PARTIES
    # ================================================================

    def refresh_parties(self):
        self.parties = self.db.get_all_parties()
        self.listbox.delete(0, tk.END)
        filtre = self.filter_statut.get()
        icons  = {"terminee": "[OK]", "en_cours": "[..]", "abandonnee": "[XX]"}
        count  = 0
        for p in self.parties:
            if filtre != "Tous" and p["statut"] != filtre:
                continue
            count += 1
            date = p["date_debut"].strftime("%d/%m/%y %H:%M") if p["date_debut"] else "N/A"
            icon = icons.get(p["statut"], "?")
            dims = f"{p.get('nb_lignes') or 6}x{p.get('nb_colonnes') or 7}"
            ligne = f"{icon} #{p['id']:03d} [{dims}] {p['joueur1_pseudo']} vs {p['joueur2_pseudo']}"
            if p["gagnant_pseudo"]:
                ligne += f" | Gagnant: {p['gagnant_pseudo']}"
            elif p["statut"] == "terminee":
                ligne += " | Nul"
            ligne += f" | {date}"
            self.listbox.insert(tk.END, ligne)
        self.stats_lbl.config(text=f"Total: {count} partie(s)")

    def _parties_filtrees(self):
        filtre = self.filter_statut.get()
        return [p for p in self.parties
                if filtre == "Tous" or p["statut"] == filtre]

    def on_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        pf = self._parties_filtrees()
        idx = sel[0]
        if idx >= len(pf):
            return

        self.partie_selectionnee = pf[idx]
        self.coups_partie        = self.db.get_partie_coups(self.partie_selectionnee["id"])

        # Lire les dimensions RÉELLES depuis la BDD
        self.nb_lignes   = int(self.partie_selectionnee.get("nb_lignes")   or 6)
        self.nb_colonnes = int(self.partie_selectionnee.get("nb_colonnes") or 7)

        # Taille de cellule adaptée
        self.cell_size = BASE_CELL if self.nb_colonnes <= 7 else 46

        # Redimensionner le canvas
        cw = self.nb_colonnes * self.cell_size
        ch = self.nb_lignes   * self.cell_size + 40
        self.canvas.config(width=cw, height=ch)

        # RESET complet de la vue symétrique à chaque sélection
        self.mode_symetrique = False
        self.btn_sym.config(
            state=tk.NORMAL,
            text="Voir Partie Symetrique",
            bg="#9C27B0"
        )

        # Afficher l'état final
        self.coup_index = len(self.coups_partie)
        self.update_display()

    def supprimer_partie(self):
        """Supprime la partie sélectionnée de la base de données."""
        if not self.partie_selectionnee:
            messagebox.showinfo("Info", "Selectionnez d'abord une partie")
            return

        pid  = self.partie_selectionnee["id"]
        nom  = (f"#{pid} — {self.partie_selectionnee['joueur1_pseudo']}"
                f" vs {self.partie_selectionnee['joueur2_pseudo']}")

        if not messagebox.askyesno("Confirmer suppression",
                                   f"Supprimer la partie {nom} ?\n\n"
                                   "Cette action est irreversible.\n"
                                   "Les coups associes seront aussi supprimes."):
            return

        ok = self.db.delete_partie(pid)
        if ok:
            messagebox.showinfo("Suppression", f"Partie #{pid} supprimee avec succes.")
            self.partie_selectionnee = None
            self.coups_partie        = []
            self.coup_index          = 0
            self.mode_symetrique     = False
            self.btn_sym.config(state=tk.DISABLED,
                                text="Voir Partie Symetrique",
                                bg="#9C27B0")
            self.canvas.delete("all")
            self.info_lbl.config(text="Selectionnez une partie")
            self.details_txt.delete(1.0, tk.END)
            self.coup_lbl.config(text="Coup 0/0")
            self.refresh_parties()
        else:
            messagebox.showerror("Erreur", f"Impossible de supprimer la partie #{pid}")

    # ================================================================
    # AFFICHAGE
    # ================================================================

    def update_display(self):
        if not self.partie_selectionnee:
            return

        # Reconstruire le plateau jusqu'au coup_index
        self.plateau = [[EMPTY]*self.nb_colonnes for _ in range(self.nb_lignes)]

        for i in range(min(self.coup_index, len(self.coups_partie))):
            coup = self.coups_partie[i]
            col  = coup["colonne"]

            if self.mode_symetrique:
                col = (self.nb_colonnes - 1) - col

            joueur = PLAYER_X if i % 2 == 0 else PLAYER_O

            # Gravité
            for row in range(self.nb_lignes - 1, -1, -1):
                if self.plateau[row][col] == EMPTY:
                    self.plateau[row][col] = joueur
                    break

        self._draw_plateau()
        self._update_info()
        self._update_details()

    def _draw_plateau(self):
        self.canvas.delete("all")
        cs = self.cell_size

        # Numéros colonnes
        for c in range(self.nb_colonnes):
            self.canvas.create_text(c*cs + cs//2, 20, text=str(c),
                                    font=("Arial", 13, "bold"), fill="white")

        # Pions
        for r in range(self.nb_lignes):
            for c in range(self.nb_colonnes):
                x1, y1 = c*cs, r*cs + 40
                x2, y2 = x1+cs, y1+cs
                cell = self.plateau[r][c]
                color = ("#F44336" if cell == PLAYER_X else
                         "#FFEB3B" if cell == PLAYER_O else "white")
                self.canvas.create_oval(x1+4, y1+4, x2-4, y2-4,
                                        fill=color, outline="black", width=2)

        # Bandeau "mode symétrique"
        if self.mode_symetrique:
            mid  = self.nb_colonnes * cs // 2
            bot  = self.nb_lignes  * cs + 32
            self.canvas.create_text(mid, bot,
                text="[ MODE SYMETRIQUE ]",
                font=("Arial", 11, "bold"), fill="purple")

    def _update_info(self):
        p    = self.partie_selectionnee
        dims = f"{self.nb_lignes}x{self.nb_colonnes}"
        txt  = f"Partie #{p['id']} [{dims}] | {p['joueur1_pseudo']} (Rouge) vs {p['joueur2_pseudo']} (Jaune)"
        if p["gagnant_pseudo"]:
            txt += f" | Gagnant: {p['gagnant_pseudo']}"
        elif p["statut"] == "terminee":
            txt += " | Match Nul"
        if self.mode_symetrique:
            txt += " | [VUE SYMETRIQUE]"
        self.info_lbl.config(text=txt)
        self.coup_lbl.config(text=f"Coup {self.coup_index}/{len(self.coups_partie)}")

    def _update_details(self):
        self.details_txt.delete(1.0, tk.END)
        p   = self.partie_selectionnee
        seq = p["sequence_coups"] or ""

        lines = []
        lines.append("="*70)
        lines.append(f"  PARTIE #{p['id']}  [{self.nb_lignes}x{self.nb_colonnes}]")
        lines.append("="*70)
        lines.append(f"Joueur 1 (X) : {p['joueur1_pseudo']}")
        lines.append(f"Joueur 2 (O) : {p['joueur2_pseudo']}")
        lines.append(f"Statut       : {p['statut']}")
        lines.append(f"Date debut   : {p['date_debut']}")
        if p["date_fin"]:
            lines.append(f"Date fin     : {p['date_fin']}")
            lines.append(f"Duree        : {p['duree_secondes']} secondes")
        if p["gagnant_pseudo"]:
            lines.append(f"\nGAGNANT      : {p['gagnant_pseudo']}")
        elif p["statut"] == "terminee":
            lines.append("\nRESULTAT     : Match Nul")
        lines.append(f"\nSequence     : {seq}")
        if p.get("hash_partie"):
            lines.append(f"Hash         : {p['hash_partie'][:20]}...")
        if self.mode_symetrique:
            sym = self.db.calculer_symetrique(seq, self.nb_colonnes)
            lines.append(f"Seq. Sym.    : {sym}")
        lines.append(f"\n{'='*70}")
        lines.append(f"  COUPS ({len(self.coups_partie)})")
        lines.append("="*70)
        for i, coup in enumerate(self.coups_partie[:self.coup_index]):
            joueur = "Rouge" if i % 2 == 0 else "Jaune"
            col    = coup["colonne"]
            if self.mode_symetrique:
                col = (self.nb_colonnes - 1) - col
            marker = ">>>" if i == self.coup_index - 1 else "   "
            lines.append(f"{marker} Coup {i+1:2d} : Col {col} — {coup['joueur_pseudo']} ({joueur})")
        if self.coup_index < len(self.coups_partie):
            lines.append(f"\n... {len(self.coups_partie) - self.coup_index} coup(s) restant(s)")

        self.details_txt.insert(1.0, "\n".join(lines))

    # ================================================================
    # NAVIGATION
    # ================================================================

    def _need_partie(self):
        if not self.partie_selectionnee:
            messagebox.showinfo("Info", "Selectionnez d'abord une partie")
            return False
        return True

    def goto_debut(self):
        if not self._need_partie(): return
        self.coup_index = 0
        self.update_display()

    def coup_precedent(self):
        if not self._need_partie(): return
        if self.coup_index > 0:
            self.coup_index -= 1
            self.update_display()

    def coup_suivant(self):
        if not self._need_partie(): return
        if self.coup_index < len(self.coups_partie):
            self.coup_index += 1
            self.update_display()

    def goto_fin(self):
        if not self._need_partie(): return
        self.coup_index = len(self.coups_partie)
        self.update_display()

    def toggle_symetrique(self):
        """Bascule entre vue normale et vue symétrique."""
        if not self.partie_selectionnee:
            return

        self.mode_symetrique = not self.mode_symetrique   # FLIP

        if self.mode_symetrique:
            self.btn_sym.config(text="Retour Vue Normale", bg="#E91E63")
        else:
            self.btn_sym.config(text="Voir Partie Symetrique", bg="#9C27B0")

        self.update_display()   # redessine avec le bon mode

    # ================================================================
    # GÉNÉRATION
    # ================================================================

    def generer_parties(self):
        win = tk.Toplevel(self)
        win.title("Generer des Parties Aleatoires")
        win.geometry("420x460")
        win.resizable(False, False)

        tk.Label(win, text="GENERATION DE PARTIES",
                 font=("Arial", 13, "bold"), bg="#FF9800", fg="white",
                 pady=8).pack(fill=tk.X)

        frame = tk.Frame(win, padx=20, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Nombre de parties :", font=("Arial", 11)).grid(
            row=0, column=0, sticky="w", pady=8)
        nb_var = tk.IntVar(value=100)
        tk.Spinbox(frame, from_=10, to=10000, increment=50,
                   textvariable=nb_var, width=10).grid(row=0, column=1, padx=10)

        tk.Label(frame, text="Taille de grille :", font=("Arial", 11)).grid(
            row=1, column=0, sticky="w", pady=8)
        taille_var = tk.StringVar(value="6x7 (Standard)")
        ttk.Combobox(frame, textvariable=taille_var,
                     values=["6x7 (Standard)", "9x9 (Grand)"],
                     state="readonly", width=15).grid(row=1, column=1, padx=10)

        tk.Label(frame, text="Niveau de confiance :", font=("Arial", 11)).grid(
            row=2, column=0, sticky="w", pady=8)
        conf_var = tk.IntVar(value=1)
        conf_frame = tk.Frame(frame)
        conf_frame.grid(row=2, column=1, padx=10)
        tk.Scale(conf_frame, from_=0, to=10, orient=tk.HORIZONTAL,
                 variable=conf_var, length=150).pack()
        descs = {0:"Joue pour perdre",1:"Aleatoire",2:"Tres debutant",
                 3:"Debutant",4:"Amateur",5:"Intermediaire",
                 6:"Confirme",7:"Avance",8:"Expert",9:"Tres expert",10:"Maitre"}
        conf_lbl = tk.Label(conf_frame, text=descs[1], fg="gray")
        conf_lbl.pack()
        conf_var.trace("w", lambda *a: conf_lbl.config(text=descs.get(conf_var.get(),"")))

        multi_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Generer pour TOUS les niveaux (0-10)",
                       variable=multi_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=8)

        prog_lbl = tk.Label(frame, text="", fg="blue")
        prog_lbl.grid(row=4, column=0, columnspan=2, pady=4)
        prog_bar = ttk.Progressbar(frame, length=300, mode="determinate")
        prog_bar.grid(row=5, column=0, columnspan=2, pady=4)

        def lancer():
            nb     = nb_var.get()
            taille = taille_var.get()
            conf   = conf_var.get()
            multi  = multi_var.get()
            rows   = 9 if "9x9" in taille else 6
            cols   = 9 if "9x9" in taille else 7
            btn_gen.config(state=tk.DISABLED, text="En cours...")
            win.update()
            total = 0
            if multi:
                prog_bar.config(maximum=11)
                for i, niv in enumerate(range(11)):
                    prog_lbl.config(text=f"Niveau {niv}/10...")
                    win.update()
                    total += self.db.generate_random_games(nb, rows, cols, niv)
                    prog_bar["value"] = i + 1
                    win.update()
            else:
                prog_bar.config(maximum=1)
                prog_lbl.config(text=f"Generation {nb} parties...")
                win.update()
                total = self.db.generate_random_games(nb, rows, cols, conf)
                prog_bar["value"] = 1
            btn_gen.config(state=tk.NORMAL, text="Generer")
            prog_lbl.config(text=f"{total} parties creees !", fg="green")
            self.refresh_parties()

        btn_gen = tk.Button(win, text="Generer", command=lancer,
                            bg="#4CAF50", fg="white",
                            font=("Arial", 12, "bold"), height=2, width=20)
        btn_gen.pack(pady=12)

    # ================================================================
    # VISUALISATION BDD
    # ================================================================

    def voir_tables(self):
        tables = self.db.get_all_tables()
        if not tables:
            messagebox.showinfo("Info", "Aucune table trouvee")
            return
        win = tk.Toplevel(self)
        win.title("Tables de la Base de Donnees")
        win.geometry("920x600")
        tk.Label(win, text="TABLES DISPONIBLES",
                 font=("Arial", 13, "bold"), bg="#4CAF50", fg="white",
                 pady=8).pack(fill=tk.X)
        mf = tk.Frame(win)
        mf.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        lf = tk.Frame(mf)
        lf.pack(side=tk.LEFT, fill=tk.BOTH, padx=4)
        tk.Label(lf, text="Tables:", font=("Arial", 11, "bold")).pack()
        lb = tk.Listbox(lf, font=("Courier", 11), width=26)
        lb.pack(fill=tk.BOTH, expand=True)
        for t in tables:
            lb.insert(tk.END, t)
        rf = tk.Frame(mf)
        rf.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=4)
        tk.Label(rf, text="Contenu:", font=("Arial", 11, "bold")).pack()
        ta = scrolledtext.ScrolledText(rf, font=("Courier", 10))
        ta.pack(fill=tk.BOTH, expand=True)

        def show(event):
            sel = lb.curselection()
            if not sel: return
            tname = tables[sel[0]]
            data  = self.db.get_table_data(tname, limit=50)
            ta.delete(1.0, tk.END)
            ta.insert(1.0, f"TABLE: {tname}\n{'='*80}\n\n")
            if not data:
                ta.insert(tk.END, "Aucune donnee\n"); return
            for i, row in enumerate(data, 1):
                ta.insert(tk.END, f"--- Ligne {i} ---\n")
                for k, v in row.items():
                    ta.insert(tk.END, f"  {str(k):22s}: {v}\n")
                ta.insert(tk.END, "\n")
            ta.insert(tk.END, f"\nTotal: {len(data)} ligne(s)")

        lb.bind("<<ListboxSelect>>", show)
        if tables:
            lb.selection_set(0)
            lb.event_generate("<<ListboxSelect>>")

    def voir_stats_joueurs(self):
        win = tk.Toplevel(self)
        win.title("Statistiques des Joueurs")
        win.geometry("820x500")
        tk.Label(win, text="STATISTIQUES DES JOUEURS",
                 font=("Arial", 13, "bold"), bg="#2196F3", fg="white",
                 pady=8).pack(fill=tk.X)
        frame = tk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        cols = ("Pseudo", "Type", "Parties", "Victoires", "Defaites", "Nuls")
        widths = (160, 80, 100, 100, 100, 80)
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w)
        try:
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM stats_joueurs ORDER BY victoires DESC")
            for s in cursor.fetchall():
                tree.insert("", tk.END, values=(
                    s["pseudo"],
                    "IA" if s["est_ia"] else "Humain",
                    s["total_parties"] or 0,
                    s["victoires"] or 0,
                    s["defaites"] or 0,
                    s["nuls"] or 0
                ))
            cursor.close()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    # ================================================================
    # AIDE
    # ================================================================

    def show_help(self):
        txt = """GUIDE D'UTILISATION

LISTE DES PARTIES
  Cliquez sur une partie pour la visualiser.
  Filtrez par statut. Rafraichissez si besoin.

NAVIGATION
  Debut      : Plateau vide
  Precedent  : Reculer d'un coup
  Suivant    : Avancer d'un coup
  Fin        : Etat final de la partie

VUE SYMETRIQUE
  Affiche le miroir horizontal de la partie.
  Cliquez sur "Retour Vue Normale" pour revenir.

SUPPRIMER UNE PARTIE
  Selectionnez une partie puis cliquez sur
  "Supprimer la partie selectionnee".
  Confirmation demandee avant suppression.

SAUVEGARDER DEPUIS LE JEU
  Jeu -> Sauvegarder durant une partie.
  La partie est enregistree en BDD automatiquement.
"""
        win = tk.Toplevel(self)
        win.title("Guide")
        win.geometry("600x450")
        st = scrolledtext.ScrolledText(win, font=("Courier", 10), wrap=tk.WORD)
        st.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        st.insert(1.0, txt)
        st.config(state=tk.DISABLED)

    def show_about(self):
        messagebox.showinfo("A propos",
            "Visualiseur Puissance 4\nVersion 3.0\n\n"
            "Toutes les fonctionnalites corrigees :\n"
            "  - Grille dynamique (6x7 et 9x9)\n"
            "  - Vue normale / symetrique fiable\n"
            "  - Suppression de parties\n"
            "  - Navigation complete\n"
            "  - Statistiques joueurs")


# ================================================================
# MAIN
# ================================================================

if __name__ == "__main__":
    DB_HOST     = "localhost"
    DB_USER     = "root"
    DB_PASSWORD = "Admin@123456"
    DB_NAME     = "puissance4"

    db = DatabaseManager(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    if not db.connect():
        print("Impossible de se connecter a la base de donnees")
        exit()

    app = VisualiseurBDD(db)
    app.mainloop()
    db.disconnect()