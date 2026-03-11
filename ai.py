import random
from database import Database
from game_logic import GameLogic
from generateur_tournoi import minimax
from constants import ROUGE, JAUNE

class IA_Tournoi:
    def __init__(self):
        self.db = Database()
        # On garde 6 pour exploiter ton processeur à fond !
        self.profondeur_secours = 6 

    def chercher_dans_bdd(self, coups_joues, joueur_ia):
        """
        Analyse l'historique actuel, le transforme en séquence (ex: "443") 
        et cherche la suite parfaite dans la base de données MySQL.
        """
        # 1. On fabrique la séquence actuelle à partir des colonnes jouées
        # On part du principe que coup[1] contient le numéro de la colonne
        sequence_actuelle = "".join([str(coup[1]) for coup in coups_joues])
        
        # 2. On cherche une partie où notre IA gagne
        statut_voulu = "VICTOIRE_ROUGE" if joueur_ia == ROUGE else "VICTOIRE_JAUNE"
        
        # 3. La requête SQL
        # ATTENTION : Si ta table ne s'appelle pas 'parties', change le nom ici !
        requete = f"""
            SELECT coups_sequence FROM parties 
            WHERE coups_sequence LIKE '{sequence_actuelle}%' 
            AND statut = '{statut_voulu}'
            ORDER BY confiance DESC 
            LIMIT 1
        """
        
        try:
            self.db.cursor.execute(requete)
            resultat = self.db.cursor.fetchone()
            
            if resultat:
                sequence_trouvee = resultat[0] # ex: "44353421..."
                
                # On s'assure que la partie trouvée est plus longue que la partie en cours
                if len(sequence_trouvee) > len(sequence_actuelle):
                    # On récupère le chiffre (la colonne) qui suit exactement notre séquence
                    prochain_coup = int(sequence_trouvee[len(sequence_actuelle)])
                    return prochain_coup
                    
        except Exception as e:
            print(f"[IA] Info BDD : Impossible de lire la séquence (Erreur: {e})")
            
        return None # Si on ne trouve rien, on renvoie None pour déclencher le Minimax

    def jouer_coup(self, logic, coups_joues, joueur_ia):
        nom_joueur = "Rouge" if joueur_ia == ROUGE else "Jaune"
        print(f"\n[IA Terminator] Réflexion pour le joueur {nom_joueur}...")
        
        # --- ÉTAPE 1 : Chercher dans le Livre de Connaissances (BDD) ---
        coup_bdd = self.chercher_dans_bdd(coups_joues, joueur_ia)
        
        if coup_bdd is not None and logic.colonne_valide(coup_bdd):
            print(f"😎 COUP TROUVÉ EN BDD ! Je joue instantanément la colonne {coup_bdd}.")
            return coup_bdd

        # --- ÉTAPE 2 : Le Calcul Brutal (Minimax Ryzen) ---
        print(f"🤖 Situation inconnue en BDD. Allumage des réacteurs (Minimax Profondeur {self.profondeur_secours})...")
        
        est_maximisant = True if joueur_ia == JAUNE else False 
        
        colonne, score = minimax(logic, self.profondeur_secours, -float('inf'), float('inf'), est_maximisant)
        
        # --- SÉCURITÉ ANTI-CRASH ---
        if colonne is None or not logic.colonne_valide(colonne):
            colonnes_valides = [c for c in range(9) if logic.colonne_valide(c)]
            if colonnes_valides:
                colonne = random.choice(colonnes_valides)
                print("⚠️ Coup de secours d'urgence joué.")
            else:
                print("❌ Impossible de jouer, le plateau est plein.")
                return None
        else:
            print(f"🧠 Calcul Minimax terminé ! Je joue la colonne {colonne}.")
            
        return colonne

_mon_ia_tournoi = IA_Tournoi()


def coup_ia_minimax(logic, *args, **kwargs):
    
    if hasattr(logic, 'historique_coups'):
        coups_joues = logic.historique_coups
    elif hasattr(logic, 'historique'):
        coups_joues = logic.historique
    else:
        coups_joues = []
        
    joueur_actuel = ROUGE if len(coups_joues) % 2 == 0 else JAUNE
        
    colonne = _mon_ia_tournoi.jouer_coup(logic, coups_joues, joueur_actuel)
    
    return colonne, 0