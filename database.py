import os
import json
import time
from datetime import datetime

try:
    import mysql.connector as mysql_connector
    from mysql.connector import Error
except ImportError:
    mysql_connector = None

    class Error(Exception):
        pass

from constants import COLONNES


class Database:
    def __init__(self):
        self.config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", "Galou1646!"),
            "database": os.getenv("DB_NAME", "puissance4_btvs"),
            "port": int(os.getenv("DB_PORT", "3306")),
        }
        self.conn = None
        self.delai_reconnexion = 10.0
        self.prochaine_tentative = 0.0
        self.connecter()

    def est_connecte(self):
        if not self.conn:
            return False

        try:
            self.conn.ping(reconnect=True, attempts=1, delay=0)
            return self.conn.is_connected()
        except Error:
            self.conn = None
            return False

    def connecter(self, force=False):
        if mysql_connector is None:
            return False

        maintenant = time.time()
        if not force and self.est_connecte():
            return True

        if not force and maintenant < self.prochaine_tentative:
            return False

        try:
            if self.conn is not None:
                try:
                    self.conn.close()
                except Error:
                    pass

            self.conn = mysql_connector.connect(**self.config)
            if self.conn and self.conn.is_connected():
                self.prochaine_tentative = 0.0
                print(">>> Connexion MySQL reussie.")
                return True

        except Error as e:
            print(f">>> Erreur de connexion MySQL: {e}")

        self.conn = None
        self.prochaine_tentative = maintenant + self.delai_reconnexion
        return False

    def assurer_connexion(self, force=False):
        if self.est_connecte():
            return True
        return self.connecter(force=force)

    def _moves_to_sequence(self, moves):
        return "".join(str(m[1]) for m in moves)

    def _get_symetrie_sequence(self, sequence):
        return "".join(str(COLONNES - 1 - int(c)) for c in sequence)

    def recuperer_id_par_sequence(self, sequence):
        if not self.assurer_connexion():
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM parties WHERE coups_sequence = %s", (sequence,))
            res = cursor.fetchone()
            cursor.close()
            return res[0] if res else None
        except Error:
            self.conn = None
            return None

    def sauvegarder(self, vainqueur_nom, moves, confiance=1, nb_colonnes=9):
        if not self.assurer_connexion(force=True):
            return False, "Erreur: pas de connexion MySQL."

        if not moves:
            return False, "Partie vide, rien a sauvegarder."

        sequence = self._moves_to_sequence(moves)
        sym_seq = self._get_symetrie_sequence(sequence)

        id_existant = self.recuperer_id_par_sequence(sequence)
        if id_existant:
            return False, f"Doublon ID={id_existant}"

        id_sym = self.recuperer_id_par_sequence(sym_seq)

        statut = "EN_COURS"
        v_lower = vainqueur_nom.lower()
        if "rouge" in v_lower:
            statut = "VICTOIRE_ROUGE"
        elif "jaune" in v_lower:
            statut = "VICTOIRE_JAUNE"
        elif "nul" in v_lower:
            statut = "NUL"

        try:
            cursor = self.conn.cursor()
            coups_json = json.dumps(moves)
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            sql = (
                "INSERT INTO parties "
                "(date_creation, statut, coups_sequence, coups_json, symetrique_id, confiance, colonnes) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )
            val = (date, statut, sequence, coups_json, id_sym, confiance, nb_colonnes)

            cursor.execute(sql, val)
            self.conn.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return True, last_id

        except mysql_connector.IntegrityError:
            return False, "Doublon detecte par MySQL (IntegrityError)."
        except Error as e:
            self.conn = None
            return False, f"Erreur SQL: {e}"

    def supprimer(self, id_partie):
        if not self.assurer_connexion(force=True):
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM parties WHERE id = %s", (id_partie,))
            self.conn.commit()
            cursor.close()
        except Error as e:
            self.conn = None
            print(f"Erreur suppression: {e}")

    def recuperer_tout(self):
        if not self.assurer_connexion():
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, date_creation, statut, coups_json, symetrique_id "
                "FROM parties ORDER BY date_creation DESC"
            )
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            self.conn = None
            print(f"Erreur lecture: {e}")
            return []
