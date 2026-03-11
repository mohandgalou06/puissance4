import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from constants import COLONNES

class Database:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',           
            'password': '',           
            'database': 'puissance4'  
        }
        
        self.conn = None
        self.connecter()

    def connecter(self):
        """Etablit la connexion à MySQL"""
        try:
            self.conn = mysql.connector.connect(**self.config)
            if self.conn.is_connected():
                print(">>> Connexion MySQL réussie.")
        except Error as e:
            print(f">>> Erreur de connexion MySQL: {e}")
            print("Vérifiez que XAMPP/WAMP est lancé et que les identifiants dans database.py sont bons.")
            self.conn = None

    def _moves_to_sequence(self, moves):
        """Convertit la liste des coups en string (ex: '34343') pour l'unicité"""
        return "".join([str(m[1]) for m in moves])

    def _get_symetrie_sequence(self, sequence):
        """Calcule la séquence symétrique (Col X devient (NbColonnes-1)-X)"""
        return "".join([str(COLONNES - 1 - int(c)) for c in sequence])

    def recuperer_id_par_sequence(self, sequence):
        """Vérifie si une suite de coups existe déjà"""
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM parties WHERE coups_sequence = %s", (sequence,))
            res = cursor.fetchone()
            cursor.close()
            return res[0] if res else None
        except Error:
            return None

    def sauvegarder(self, vainqueur_nom, moves, confiance=1, nb_colonnes=9):
        """Enregistre la partie avec gestion des doublons, symétries, confiance et dimensions"""
        if not self.conn: 
            self.connecter()
            if not self.conn:
                return False, "Erreur: Pas de connexion MySQL."

        if not moves: 
            return False, "Partie vide, rien à sauvegarder."

        sequence = self._moves_to_sequence(moves)
        sym_seq = self._get_symetrie_sequence(sequence)
        
        if self.recuperer_id_par_sequence(sequence):
            return False, "Cette partie existe déjà en base (Doublon)."

        id_sym = self.recuperer_id_par_sequence(sym_seq)
        
        statut = "EN_COURS"
        v_lower = vainqueur_nom.lower()
        if "rouge" in v_lower: statut = "VICTOIRE_ROUGE"
        elif "jaune" in v_lower: statut = "VICTOIRE_JAUNE"
        elif "nul" in v_lower: statut = "NUL"

        try:
            cursor = self.conn.cursor()
            coups_json = json.dumps(moves)
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Ajout de confiance et colonnes (Mission 3.1)
            sql = """INSERT INTO parties (date_creation, statut, coups_sequence, coups_json, symetrique_id, confiance, colonnes)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            val = (date, statut, sequence, coups_json, id_sym, confiance, nb_colonnes)
            
            cursor.execute(sql, val)
            self.conn.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return True, last_id
            
        except mysql.connector.IntegrityError:
            return False, "Doublon détecté par MySQL (IntegrityError)."
        except Error as e:
            return False, f"Erreur SQL: {e}"

    def supprimer(self, id_partie):
        if not self.conn: return
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM parties WHERE id = %s", (id_partie,))
            self.conn.commit()
            cursor.close()
        except Error as e:
            print(f"Erreur suppression: {e}")

    def recuperer_tout(self):
        """Récupère la liste pour l'affichage GUI"""
        if not self.conn: 
            self.connecter()
            if not self.conn: return []

        try:
            cursor = self.conn.cursor()
            sql = "SELECT id, date_creation, statut, coups_json, symetrique_id FROM parties ORDER BY date_creation DESC"
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            print(f"Erreur lecture: {e}")
            return []
