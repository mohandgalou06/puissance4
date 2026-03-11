import random
from game_logic import GameLogic
from constants import *
from database import Database

def generer_parties(nombre_parties):
    db = Database()
    parties_sauvees = 0

    print(f"Lancement de la génération de {nombre_parties} parties aléatoires en {LIGNES}x{COLONNES}...")
    
    for i in range(nombre_parties):
        logic = GameLogic()
        moves = []
        tour_r = True
        
        while not logic.partie_finie and not logic.grille_pleine():
            valid_cols = [c for c in range(COLONNES) if logic.colonne_valide(c)]
            if not valid_cols:
                break
            
            col = random.choice(valid_cols)
            joueur = ROUGE if tour_r else JAUNE
            l = logic.placer_pion(col, joueur)
            moves.append((l, col, joueur))
            
            if logic.victoire(joueur):
                break
                
            tour_r = not tour_r
            
        vainqueur = "Indéfini"
        if logic.victoire(ROUGE): vainqueur = "Rouge"
        elif logic.victoire(JAUNE): vainqueur = "Jaune"
        elif logic.grille_pleine(): vainqueur = "Nul"
        
        # Sauvegarde avec confiance=1 (Aléatoire) et le nombre de colonnes actuel
        ok, msg = db.sauvegarder(vainqueur, moves, confiance=1, nb_colonnes=COLONNES)
        if ok:
            parties_sauvees += 1

    print(f"Terminé ! {parties_sauvees}/{nombre_parties} parties uniques sauvegardées en base.")

if __name__ == "__main__":
    generer_parties(50) 