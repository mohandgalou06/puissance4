import tkinter as tk
from tkinter import messagebox, ttk
import os
import time
import logging
import traceback
from constants import ROUGE, JAUNE
from selenium import webdriver
from selenium.webdriver import Firefox, FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

# Import de ta base de données (Mission 3.4)
from database import Database

# Configuration du logging
logging.basicConfig(
    filename='bga_automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BGAApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BGA Tables Viewer & Scraper")
        self.root.geometry("800x650")
        
        self.driver = None
        self.connected = False
        self.table_data = [] # Stockera les URLs pour la Mission 3.4
        self.db = Database()
        
        # UI Setup
        self.status_var = tk.StringVar(value="Statut: Déconnecté")
        self.status_label = tk.Label(root, textvariable=self.status_var, fg="red", font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        self.connect_button = tk.Button(root, text="Connecter", command=self.connect, width=20)
        self.connect_button.pack(pady=5)
        
        player_frame = tk.Frame(root)
        player_frame.pack(pady=5)
        
        tk.Label(player_frame, text="ID Joueur:").pack(side=tk.LEFT)
        self.player_entry = tk.Entry(player_frame, width=20)
        self.player_entry.pack(side=tk.LEFT, padx=10)
        self.player_entry.insert(0, "97047639")
        
        # Bouton Scrutation
        self.scrute_button = tk.Button(root, text="Scruter les Tables", command=self.scrute_tables, state=tk.DISABLED)
        self.scrute_button.pack(pady=5)
        
        # Nouveau Bouton Scraping BDD (Mission 3.4)
        self.scrape_db_button = tk.Button(root, text="📥 Scraper Replays et Sauver BDD", command=self.scrape_replays_to_db, state=tk.DISABLED, bg="#27ae60", fg="white")
        self.scrape_db_button.pack(pady=5)
        
        # Tableau
        self.tree = ttk.Treeview(root, columns=('Table ID', 'Jeu', 'Joueurs'), show='headings')
        self.tree.heading('Table ID', text='Table ID')
        self.tree.heading('Jeu', text='Jeu')
        self.tree.heading('Joueurs', text='Joueurs')
        self.tree.column('Table ID', width=100)
        self.tree.column('Jeu', width=200)
        self.tree.column('Joueurs', width=400)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.disconnect_button = tk.Button(root, text="Déconnecter", command=self.disconnect, width=20)
        self.disconnect_button.pack(pady=5)
        
        if not os.path.exists("credentials.txt"):
            with open("credentials.txt", "w") as f:
                f.write("votre_email@exemple.com\nvotre_mot_de_passe")

    def log(self, message):
        logging.info(message)
        print(message)

    def connect(self):
        try:
            self.connect_button.config(state=tk.DISABLED)
            self.status_var.set("Statut: Connexion en cours...")
            self.root.update()
            
            with open("credentials.txt", "r") as f:
                credentials = f.read().splitlines()
                email, password = credentials[0].strip(), credentials[1].strip()
            
            options = FirefoxOptions()
            options.headless = False
            service = Service(GeckoDriverManager().install())
            
            self.log("Lancement de Firefox...")
            self.driver = Firefox(service=service, options=options)
            self.driver.maximize_window()
            
            self.driver.get('https://fr.boardgamearena.com/account')
            
            # 1. Tenter de fermer le pop-up des cookies ("Tout refuser")
            try:
                self.log("Recherche du bandeau de cookies...")
                cookie_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Tout refuser")]'))
                )
                cookie_btn.click()
                self.log("Cookies refusés.")
            except Exception:
                self.log("Pas de pop-up cookies, on continue.")

            time.sleep(2) # On laisse le site se stabiliser

            # 2. Chercher et remplir l'Email
            self.log("Remplissage de l'email...")
            # On cible exactement la phrase "Adresse e-mail..." visible à l'écran !
            email_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Adresse e-mail ou nom d\'utilisateur"]'))
            )
            email_field.click() # On clique pour activer le champ visuellement (important pour Svelte)
            time.sleep(0.5)
            # PAS DE .clear() ICI ! C'est ce qui faisait planter Svelte.
            email_field.send_keys(email)
            
            # 3. Cliquer sur le bouton "Suivant"
            self.log("Clic sur Suivant...")
            try:
                time.sleep(1)
                # On cherche maintenant un <a> (lien) ou un <button> !
                next_button = self.driver.find_element(By.XPATH, '//a[contains(., "Suivant")] | //button[contains(., "Suivant")]')
                next_button.click()
                time.sleep(2) # On attend l'apparition du champ mot de passe
            except Exception:
                self.log("Bouton Suivant introuvable, on continue.")

            # 4. Chercher et remplir le Mot de passe
            self.log("Remplissage du mot de passe...")
            password_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="password"]'))
            )
            password_field.click()
            time.sleep(0.5)
            password_field.send_keys(password)

            # 5. Cliquer sur Se connecter
            self.log("Clic sur le bouton de connexion...")
            try:
                time.sleep(1)
                # Même ruse ici : on cherche un <a> ou un <button>
                login_button = self.driver.find_element(By.XPATH, '//a[contains(., "Se connecter")] | //button[contains(., "Se connecter")] | //button[contains(., "Connecter")]')
                login_button.click()
            except Exception:
                self.log("Clic de connexion alternatif...")
                password_field.send_keys(u'\ue007') # Appuie sur "Entrée" si le bouton bug
            self.connected = True
            self.status_var.set("Statut: Connecté")
            self.status_label.config(fg="green")
            self.scrute_button.config(state=tk.NORMAL)
                
        except Exception as e:
            self.log(f"ERREUR: {str(e)}")
            messagebox.showerror("Erreur", f"Échec de la connexion: {str(e)}")
            self.status_var.set("Statut: Déconnecté")
            if self.driver:
                self.driver.quit()
                self.driver = None
        finally:
            self.connect_button.config(state=tk.NORMAL)

    def scrute_tables(self):
        """Lance le processus de scrutation des tables avec le nouveau format BGA"""
        try:
            player_id = self.player_entry.get().strip()
            if not player_id.isdigit():
                messagebox.showwarning("Erreur", "ID Joueur invalide.")
                return
                
            self.scrute_button.config(state=tk.DISABLED)
            self.status_var.set("Statut: Recherche des tables...")
            self.root.update()
            
            # Vider le tableau
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.table_data = []
            
            # Navigation vers les stats
            url_stats = f'https://boardgamearena.com/gamestats?player={player_id}'
            self.log(f"Navigation vers : {url_stats}")
            self.driver.get(url_stats)
            
            # Attendre que le tableau des parties soit visible (Nouvel ID détecté)
            self.log("Attente du chargement de l'historique...")
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.ID, 'gamelist_inner'))
            )
            time.sleep(2)
            
            # Extraire toutes les lignes du tableau
            rows = self.driver.find_elements(By.CSS_SELECTOR, '#gamelist_inner tr')
            self.log(f"Analyse de {len(rows)} lignes trouvées...")

            for row in rows:
                try:
                    # On cherche le nom du jeu dans la cellule
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if not cells: continue
                    
                    text_content = cells[0].text
                    
                    # On ne garde que Puissance 4
                    if 'Puissance Quatre' in text_content or 'Connect Four' in text_content:
                        # On récupère le lien de la table (celui avec le #ID que tu as inspecté)
                        link_element = cells[0].find_element(By.CSS_SELECTOR, 'a.table_name.smalltext')
                        table_url = link_element.get_attribute('href')
                        table_id = link_element.text.replace('#', '')
                        
                        # Récupération des joueurs dans la 3ème cellule (index 2)
                        player_links = cells[2].find_elements(By.TAG_NAME, 'a')
                        player_names = ', '.join([p.text for p in player_links if p.text.strip()])
                        
                        self.table_data.append({
                            'table_id': table_id,
                            'game_name': 'Puissance Quatre',
                            'player_names': player_names,
                            'url': table_url
                        })
                        
                        # Ajout dans l'interface graphique
                        self.tree.insert('', 'end', values=(table_id, 'Puissance Quatre', player_names))
                except Exception:
                    continue
            
            if not self.table_data:
                self.log("Aucune table trouvée.")
                messagebox.showinfo("Info", "Aucune table de Puissance 4 trouvée dans cet historique.")
            else:
                self.log(f"Succès : {len(self.table_data)} tables extraites.")
                self.scrape_db_button.config(state=tk.NORMAL)
            
            self.status_var.set("Statut: Connecté")
            
        except Exception as e:
            self.log(f"ERREUR: {str(e)}")
            self.status_var.set("Statut: Erreur")
        finally:
            self.scrute_button.config(state=tk.NORMAL)

    def scrape_replays_to_db(self):
        import re
        from game_logic import GameLogic
        from constants import ROUGE, JAUNE
        
        self.scrape_db_button.config(state=tk.DISABLED)
        nb_sauvegardes = 0
        self.log(f"Début du scrap sur {len(self.table_data)} tables...")

        for table in self.table_data:
            try:
                # On force l'URL vers le 'gamereview' au lieu de 'table'
                review_url = table['url'].replace('table?table=', 'gamereview?table=')
                self.log(f"Ouverture du Replay : {review_url}")
                self.driver.get(review_url)
                
                # PAUSE CRUCIALE : On attend que le journal se charge vraiment
                time.sleep(7) 
                
                # On essaie de trouver les logs
                logs = self.driver.find_elements(By.CSS_SELECTOR, ".gamelogreview.whiteblock")
                self.log(f"Logs trouvés : {len(logs)}")
                
                if len(logs) == 0:
                    # Si c'est vide, on tente de cliquer sur "Tout afficher" si le bouton existe
                    try:
                        self.log("Tentative de déplier le journal...")
                        show_all = self.driver.find_element(By.ID, "show_all_logs")
                        show_all.click()
                        time.sleep(2)
                        logs = self.driver.find_elements(By.CSS_SELECTOR, ".gamelogreview.whiteblock")
                    except:
                        pass

                temp_logic = GameLogic()
                temp_logic.nb_colonnes = 9
                temp_logic.nb_lignes = 9
                temp_logic.grille = [[0 for _ in range(9)] for _ in range(9)]
                
                moves_extraits = []
                tour_rouge = True 
                
                for log in logs:
                    texte = log.text
                    # On cherche le chiffre de la colonne
                    match = re.search(r"colonne (\d+)", texte)
                    if match:
                        col = int(match.group(1))
                        # Si BGA dit colonne 1 à 7, on garde tel quel pour ton 9x9
                        if temp_logic.colonne_valide(col):
                            joueur = ROUGE if tour_rouge else JAUNE
                            l = temp_logic.placer_pion(col, joueur)
                            moves_extraits.append([l, col, joueur])
                            tour_rouge = not tour_rouge
                
                if moves_extraits:
                    vainqueur = "Rouge" if temp_logic.victoire(ROUGE) else "Jaune" if temp_logic.victoire(JAUNE) else "Nul"
                    ok, msg = self.db.sauvegarder(vainqueur, moves_extraits, confiance=2, nb_colonnes=9)
                    if ok:
                        nb_sauvegardes += 1
                        self.log(f"SUCCÈS : Table {table['table_id']} enregistrée ({len(moves_extraits)} coups)")
                else:
                    self.log(f"ÉCHEC : Aucun coup extrait pour la table {table['table_id']}")

            except Exception as e:
                self.log(f"Erreur table {table['table_id']} : {e}")

        self.log(f"=== FIN DU SCRAPING : {nb_sauvegardes} PARTIES EN BDD ===")
        self.status_var.set(f"Terminé : {nb_sauvegardes} scrapées")
        self.scrape_db_button.config(state=tk.NORMAL)
        messagebox.showinfo("Résultat", f"{nb_sauvegardes} parties ont été ajoutées en 9x9 !")

    def disconnect(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.connected = False
            self.status_var.set("Statut: Déconnecté")
            self.status_label.config(fg="red")
            self.scrute_button.config(state=tk.DISABLED)
            self.scrape_db_button.config(state=tk.DISABLED)

    def on_closing(self):
        self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BGAApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
