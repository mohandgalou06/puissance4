from constants import *

class GameLogic:
    def __init__(self):
        self.grille = [[VIDE for _ in range(COLONNES)] for _ in range(LIGNES)]
        self.partie_finie = False
        self.aligne = [] 

    def colonne_valide(self, col):
        return 0 <= col < COLONNES and self.grille[0][col] == VIDE

    def placer_pion(self, col, joueur):
        if not self.colonne_valide(col):
            return None
        for l in range(LIGNES - 1, -1, -1):
            if self.grille[l][col] == VIDE:
                self.grille[l][col] = joueur
                return l
        return None

    def dans_grille(self, l, c):
        return 0 <= l < LIGNES and 0 <= c < COLONNES

    def victoire(self, joueur):
        self.aligne = []
        directions = [(0,1), (1,0), (1,1), (1,-1)]
        for l in range(LIGNES):
            for c in range(COLONNES):
                if self.grille[l][c] != joueur:
                    continue
                for dl, dc in directions:
                    temp = [(l, c)] 
                    ok = True
                    for k in range(1,4):
                        ll, cc = l + k*dl, c + k*dc
                        if not self.dans_grille(ll, cc) or self.grille[ll][cc] != joueur:
                            ok = False
                            break
                        temp.append((ll, cc))
                    if ok:
                        self.aligne = temp  
                        return True
        return False

    def grille_pleine(self):
        return all(self.grille[0][c] != VIDE for c in range(COLONNES))
