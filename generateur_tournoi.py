import random
import time
from database import Database
from game_logic import GameLogic
from constants import ROUGE, JAUNE

def evaluer_fenetre(fenetre, pion):
    score = 0
    adversaire = JAUNE if pion == ROUGE else ROUGE

    if fenetre.count(pion) == 4:
        score += 1000  # Victoire absolue
    elif fenetre.count(pion) == 3 and fenetre.count(0) == 1:
        score += 10    # Grosse menace
    elif fenetre.count(pion) == 2 and fenetre.count(0) == 2:
        score += 3     # Construction

    if fenetre.count(adversaire) == 3 and fenetre.count(0) == 1:
        score -= 80    # Bloquer l'adversaire est vital
        
    return score

def score_position(logic, pion):
    score = 0
    # Priorité absolue au centre absolu (colonne 4) et ses voisines (3 et 5)
    col_centre = [row[4] for row in logic.grille]
    score += col_centre.count(pion) * 6
    col_voisines = [row[3] for row in logic.grille] + [row[5] for row in logic.grille]
    score += col_voisines.count(pion) * 3

    # Évaluation de toutes les fenêtres (Lignes, colonnes)
    # Lignes (Horizontales)
    for l in range(9):
        for c in range(6):
            fenetre = logic.grille[l][c:c+4]
            score += evaluer_fenetre(fenetre, pion)
            
    # Colonnes (Verticales)
    for c in range(9):
        for l in range(6):
            fenetre = [logic.grille[l+i][c] for i in range(4)]
            score += evaluer_fenetre(fenetre, pion)

    # Diagonales descendantes et montantes
    for l in range(6):
        for c in range(6):
            fen_desc = [logic.grille[l+i][c+i] for i in range(4)]
            score += evaluer_fenetre(fen_desc, pion)
            fen_mont = [logic.grille[l+3-i][c+i] for i in range(4)]
            score += evaluer_fenetre(fen_mont, pion)

    return score

def minimax(logic, profondeur, alpha, beta, maximisant):
    colonnes_valides = [c for c in range(9) if logic.colonne_valide(c)]
    
    # Optimisation Alpha-Beta : on teste le centre en premier
    ordre_colonnes = [4, 3, 5, 2, 6, 1, 7, 0, 8]
    colonnes_valides = [c for c in ordre_colonnes if c in colonnes_valides]

    est_terminal = logic.victoire(ROUGE) or logic.victoire(JAUNE) or len(colonnes_valides) == 0

    if profondeur == 0 or est_terminal:
        if est_terminal:
            if logic.victoire(JAUNE): return (None, 10000000)
            if logic.victoire(ROUGE): return (None, -10000000)
            else: return (None, 0)
        else:
            return (None, score_position(logic, JAUNE))

    if maximisant:
        valeur = -float('inf')
        colonne = random.choice(colonnes_valides)
        for c in colonnes_valides:
            copie = GameLogic()
            copie.grille = [row[:] for row in logic.grille]
            copie.placer_pion(c, JAUNE)
            nouveau_score = minimax(copie, profondeur-1, alpha, beta, False)[1]
            if nouveau_score > valeur:
                valeur = nouveau_score
                colonne = c
            alpha = max(alpha, valeur)
            if alpha >= beta: break
        return colonne, valeur
    else:
        valeur = float('inf')
        colonne = random.choice(colonnes_valides)
        for c in colonnes_valides:
            copie = GameLogic()
            copie.grille = [row[:] for row in logic.grille]
            copie.placer_pion(c, ROUGE)
            nouveau_score = minimax(copie, profondeur-1, alpha, beta, True)[1]
            if nouveau_score < valeur:
                valeur = nouveau_score
                colonne = c
            beta = min(beta, valeur)
            if alpha >= beta: break
        return colonne, valeur

def generer_tournoi(nb=50):
    db = Database()
    print("=== DÉMARRAGE DU GÉNÉRATEUR TOURNOI (Diversité + Profondeur 6) ===")
    
    PROFONDEUR_IA = 6 

    for i in range(nb):
        logic = GameLogic()
        logic.nb_colonnes = 9
        logic.nb_lignes = 9
        logic.grille = [[0 for _ in range(9)] for _ in range(9)]
        coups = []
        
        print(f"\n--- Début de la partie {i+1}/{nb} ---")
        temps_partie_debut = time.time()
        
        while not (logic.victoire(ROUGE) or logic.victoire(JAUNE) or all(logic.grille[0][c] != 0 for c in range(9))):
            joueur = ROUGE if len(coups) % 2 == 0 else JAUNE
            
            debut_coup = time.time()
            
            # --- LE LIVRE D'OUVERTURES (Pour avoir 50 parties uniques) ---
            colonnes_valides = [c for c in range(9) if logic.colonne_valide(c)]
            
            if len(coups) == 0:
                # Premier coup : légèrement aléatoire au centre
                choix_possibles = [c for c in [3, 4, 5] if c in colonnes_valides]
                col = random.choice(choix_possibles)
            elif len(coups) == 1:
                # Deuxième coup : on élargit un peu
                choix_possibles = [c for c in [2, 3, 4, 5, 6] if c in colonnes_valides]
                col = random.choice(choix_possibles)
            else:
                # Le monstre se réveille
                col, _ = minimax(logic, PROFONDEUR_IA, -float('inf'), float('inf'), (joueur == JAUNE))
            # -------------------------------------------------------------
            
            fin_coup = time.time()
            
            # Sécurité au cas où minimax ne trouve rien
            if col is None or not logic.colonne_valide(col):
                col = random.choice(colonnes_valides)
                
            lig = logic.placer_pion(col, joueur)
            coups.append([lig, col, joueur])
            
            nom_joueur = "Jaune" if joueur == JAUNE else "Rouge"
            print(f"Coup {len(coups):02d} | {nom_joueur} joue col {col} | Calcul: {fin_coup - debut_coup:.2f} sec")
            
        vainqueur = "Rouge" if logic.victoire(ROUGE) else "Jaune" if logic.victoire(JAUNE) else "Nul"
        
        # Sauvegarde avec la confiance maximale
        db.sauvegarder(vainqueur, coups, confiance=3, nb_colonnes=9)
        
        temps_partie_fin = time.time()
        print(f">>> Partie {i+1} terminée en {temps_partie_fin - temps_partie_debut:.1f} secondes. Vainqueur: {vainqueur}")

if __name__ == "__main__":
    generer_tournoi(50)