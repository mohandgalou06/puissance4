

"""
MAIN - Point d'entrée principal du projet Puissance 4
Choix entre Jouer une partie ou Visualiser la base de données
"""

import tkinter as tk
from tkinter import simpledialog, messagebox
from database import DatabaseManager
import sys

# ==================== CONFIGURATION MYSQL ====================
# ⚠️ MODIFIEZ CES VALEURS SELON VOTRE CONFIGURATION
DB_HOST = "localhost"
DB_USER = "root"            # ou "pythonuser"
DB_PASSWORD = "Galou1646!"  # Votre mot de passe MySQL
DB_NAME = "puissance4"

def launch_game():
    """Lancer le jeu Puissance 4"""
    try:
        from puissance4 import Puissance4, MenuSelection
    except ImportError as e:
        messagebox.showerror(
            "Erreur Import",
            f"Impossible d'importer puissance4.py\n\n{e}\n\n"
            "Assurez-vous que puissance4.py est dans le même répertoire"
        )
        return
    
    root = tk.Tk()   
    root.withdraw()  # Cacher la fenêtre principale au démarrage

    # ==================== CONNEXION À LA BASE DE DONNÉES ====================
    print("🔌 Tentative de connexion à MySQL...")
    db = DatabaseManager(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    
    if not db.connect():
        messagebox.showerror(
            "❌ Erreur MySQL",
            "Impossible de se connecter à MySQL.\n\n"
            "Vérifiez que :\n"
            "1. MySQL est démarré (XAMPP ou 'sudo systemctl start mysql')\n"
            "2. Le mot de passe dans main.py est correct\n"
            "3. La base 'puissance4' existe\n\n"
            "Pour créer la base :\n"
            "mysql -u root -p < schema_simplifie.sql"
        )
        return

    # ==================== AUTHENTIFICATION JOUEUR ====================
    pseudo = simpledialog.askstring(
        "👤 Connexion",
        "Entrez votre pseudo :",
        parent=root
    )
    
    if not pseudo:
        print("❌ Aucun pseudo saisi, fermeture...")
        db.disconnect()
        return
    
    joueur_id = db.get_or_create_joueur(pseudo)          
    
    if not joueur_id:
        messagebox.showerror("Erreur", "Impossible de créer/récupérer le joueur")
        db.disconnect()
        return

    # ==================== MENU DE SÉLECTION ====================
    menu = MenuSelection(root)

    if menu.choice == "quit":
        print("👋 Fermeture du programme")
        root.destroy()
        db.disconnect()
        return

    # ==================== LANCEMENT DU JEU ====================
    root.deiconify()  # Afficher la fenêtre principale
    game = Puissance4(root, mode=menu.choice, joueur1_id=joueur_id, db=db)
    root.mainloop()
    
    # ==================== DÉCONNEXION ====================
    db.disconnect()

def launch_visualiseur():
    """Lancer l'outil de visualisation de la BDD"""
    try:
        from visualiseur import VisualiseurBDD
    except ImportError as e:
        messagebox.showerror(
            "Erreur Import",
            f"Impossible d'importer visualiseur.py\n\n{e}\n\n"
            "Assurez-vous que visualiseur.py est dans le même répertoire"
        )
        return
    
    print("🔍 Lancement du visualiseur...")
    db = DatabaseManager(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    
    if not db.connect():
        messagebox.showerror(
            "❌ Erreur MySQL",
            "Impossible de se connecter à MySQL.\n\n"
            "Vérifiez que :\n"
            "1. MySQL est démarré\n"
            "2. Le mot de passe dans main.py est correct\n"
            "3. La base 'puissance4' existe"
        )
        return
    
    try:
        app = VisualiseurBDD(db)
        app.mainloop()
    except KeyboardInterrupt:
        print("\n⚠️  Interruption par l'utilisateur")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()

def main():
    """Point d'entrée principal avec choix entre jeu et visualiseur"""
    print("\n" + "="*60)
    print("🎮 PUISSANCE 4 - MENU PRINCIPAL")
    print("="*60 + "\n")
    
    root = tk.Tk()
    root.withdraw()
    
    choice = messagebox.askyesnocancel(
        "🎮 Puissance 4 - Menu Principal",
        "Que voulez-vous faire ?\n\n"
        "• OUI     : 🎮 Jouer une partie\n"
        "• NON     : 🔍 Visualiser la base de données\n"
        "• ANNULER : ❌ Quitter",
        icon='question'
    )
    
    root.destroy()
    
    if choice is True:
        # Lancer le jeu
        print("✅ Lancement du jeu...\n")
        launch_game()
    elif choice is False:
        # Lancer le visualiseur
        print("✅ Lancement du visualiseur...\n")
        launch_visualiseur()
    else:
        # Annulé
        print("👋 Au revoir !")
    
    print("\n" + "="*60)
    print("🎮 Fin du programme")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()