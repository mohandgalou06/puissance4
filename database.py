

import mysql.connector
from mysql.connector import Error
import hashlib
import random
import json


class DatabaseManager:
    def __init__(self, host="localhost", user="root", password="", database="puissance4"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print(f"✅ Connecté à MySQL (base: {self.database})")
                return True
        except Exception as e:
            print(f"❌ Erreur connexion BDD : {e}")
            return False

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def get_or_create_joueur(self, pseudo, email="", est_ia=False):
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM joueurs WHERE pseudo = %s", (pseudo,))
            result = cursor.fetchone()
            if result:
                return result[0]
            cursor.execute(
                "INSERT INTO joueurs (pseudo, email, est_ia) VALUES (%s, %s, %s)",
                (pseudo, email if email else f"{pseudo}@local.com", est_ia)
            )
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ Erreur get_or_create_joueur : {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def import_partie_from_sequence(self, sequence, joueur1_id=None, joueur2_id=None,
                                     nb_colonnes=7, nb_lignes=6):
        cursor = None
        try:
            hash_partie = hashlib.md5(sequence.encode()).hexdigest()
            sequence_sym = self.calculer_symetrique(sequence, nb_colonnes)
            hash_sym = hashlib.md5(sequence_sym.encode()).hexdigest()
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM parties WHERE hash_partie = %s", (hash_partie,))
            existing = cursor.fetchone()
            if existing:
                return {'status': 'exists', 'partie_id': existing[0]}
            cursor.execute("SELECT id FROM parties WHERE hash_partie = %s", (hash_sym,))
            existing_sym = cursor.fetchone()
            if existing_sym:
                return {'status': 'symetrique', 'partie_id': existing_sym[0]}
            if not joueur1_id:
                joueur1_id = self.get_or_create_joueur("Joueur1")
            if not joueur2_id:
                joueur2_id = self.get_or_create_joueur("Joueur2")
            gagnant_id = self.simuler_partie(sequence, joueur1_id, joueur2_id,
                                              nb_lignes=nb_lignes, nb_colonnes=nb_colonnes)
            cursor.execute(
                """INSERT INTO parties (joueur1_id, joueur2_id, gagnant_id, sequence_coups,
                   hash_partie, statut, nb_lignes, nb_colonnes)
                   VALUES (%s, %s, %s, %s, %s, 'terminee', %s, %s)""",
                (joueur1_id, joueur2_id, gagnant_id, sequence, hash_partie, nb_lignes, nb_colonnes)
            )
            self.connection.commit()
            partie_id = cursor.lastrowid
            joueur_courant_id = joueur1_id
            for i, col_str in enumerate(sequence):
                col = int(col_str)
                cursor.execute(
                    "INSERT INTO coups (partie_id, numero_coup, colonne, joueur_id) VALUES (%s, %s, %s, %s)",
                    (partie_id, i + 1, col, joueur_courant_id)
                )
                joueur_courant_id = joueur2_id if joueur_courant_id == joueur1_id else joueur1_id
            self.connection.commit()
            return {'status': 'created', 'partie_id': partie_id}
        except Exception as e:
            print(f"❌ Erreur import_partie : {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if cursor:
                cursor.close()

    def calculer_symetrique(self, sequence, nb_colonnes=7):
        if not sequence:
            return ""
        return ''.join(str(nb_colonnes - 1 - int(c)) for c in sequence)

    def simuler_partie(self, sequence, joueur1_id, joueur2_id, nb_lignes=6, nb_colonnes=7):
        plateau = [[' '] * nb_colonnes for _ in range(nb_lignes)]
        joueur_courant = 'X'
        for col_str in sequence:
            col = int(col_str)
            if col < 0 or col >= nb_colonnes:
                continue
            for row in range(nb_lignes - 1, -1, -1):
                if plateau[row][col] == ' ':
                    plateau[row][col] = joueur_courant
                    break
            if self.check_win(plateau, joueur_courant, nb_lignes, nb_colonnes):
                return joueur1_id if joueur_courant == 'X' else joueur2_id
            joueur_courant = 'O' if joueur_courant == 'X' else 'X'
        return None

    def check_win(self, plateau, joueur, nb_lignes=6, nb_colonnes=7):
        for r in range(nb_lignes):
            for c in range(nb_colonnes - 3):
                if all(plateau[r][c + i] == joueur for i in range(4)):
                    return True
        for c in range(nb_colonnes):
            for r in range(nb_lignes - 3):
                if all(plateau[r + i][c] == joueur for i in range(4)):
                    return True
        for r in range(nb_lignes - 3):
            for c in range(nb_colonnes - 3):
                if all(plateau[r + i][c + i] == joueur for i in range(4)):
                    return True
        for r in range(3, nb_lignes):
            for c in range(nb_colonnes - 3):
                if all(plateau[r - i][c + i] == joueur for i in range(4)):
                    return True
        return False

    def get_all_parties(self):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT p.*, j1.pseudo as joueur1_pseudo, j2.pseudo as joueur2_pseudo,
                   jg.pseudo as gagnant_pseudo FROM parties p
                   JOIN joueurs j1 ON p.joueur1_id = j1.id
                   JOIN joueurs j2 ON p.joueur2_id = j2.id
                   LEFT JOIN joueurs jg ON p.gagnant_id = jg.id
                   ORDER BY p.date_debut DESC"""
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erreur get_all_parties : {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_partie_coups(self, partie_id):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT c.*, j.pseudo as joueur_pseudo FROM coups c
                   JOIN joueurs j ON c.joueur_id = j.id
                   WHERE c.partie_id = %s ORDER BY c.numero_coup""",
                (partie_id,)
            )
            return cursor.fetchall()
        except Exception as e:
            return []
        finally:
            if cursor:
                cursor.close()

    def get_stats_joueur(self, joueur_id):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM stats_joueurs WHERE id = %s", (joueur_id,))
            return cursor.fetchone()
        except Exception as e:
            return None
        finally:
            if cursor:
                cursor.close()

    def save_partie_complete(self, joueur1_id, joueur2_id, gagnant_id, sequence, duree=0,
                              nb_lignes=6, nb_colonnes=7):
        cursor = None
        try:
            if not sequence:
                return None
            hash_partie = hashlib.md5(sequence.encode()).hexdigest()
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM parties WHERE hash_partie = %s", (hash_partie,))
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            cursor.execute(
                """INSERT INTO parties (joueur1_id, joueur2_id, gagnant_id, duree_secondes,
                   statut, sequence_coups, hash_partie, nb_lignes, nb_colonnes)
                   VALUES (%s, %s, %s, %s, 'terminee', %s, %s, %s, %s)""",
                (joueur1_id, joueur2_id, gagnant_id, duree, sequence, hash_partie, nb_lignes, nb_colonnes)
            )
            self.connection.commit()
            partie_id = cursor.lastrowid
            joueur_courant_id = joueur1_id
            for i, col_str in enumerate(sequence):
                col = int(col_str)
                cursor.execute(
                    "INSERT INTO coups (partie_id, numero_coup, colonne, joueur_id) VALUES (%s, %s, %s, %s)",
                    (partie_id, i + 1, col, joueur_courant_id)
                )
                joueur_courant_id = joueur2_id if joueur_courant_id == joueur1_id else joueur1_id
            self.connection.commit()
            return partie_id
        except Exception as e:
            print(f"❌ Erreur save_partie_complete : {e}")
            if self.connection:
                self.connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()

    def save_coup(self, partie_id, numero_coup, colonne, joueur_id, temps_reflexion=0):
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO coups (partie_id, numero_coup, colonne, joueur_id) VALUES (%s, %s, %s, %s)",
                (partie_id, numero_coup, colonne, joueur_id)
            )
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            return None
        finally:
            if cursor:
                cursor.close()

    def update_position_stats(self, sequence, gagnant_id, joueur1_id, joueur2_id,
                               nb_lignes=6, nb_colonnes=7):
        try:
            cursor = self.connection.cursor(dictionary=True)
            plateau = [[' '] * nb_colonnes for _ in range(nb_lignes)]
            joueur = 'X'
            for col_str in sequence:
                col = int(col_str)
                for row in range(nb_lignes - 1, -1, -1):
                    if plateau[row][col] == ' ':
                        plateau[row][col] = joueur
                        break
                plateau_json = json.dumps(plateau)
                hash_pos = hashlib.md5(plateau_json.encode()).hexdigest()
                joueur_suivant = 'O' if joueur == 'X' else 'X'
                cursor.execute(
                    "SELECT victoires_x, victoires_o, nuls, nb_parties FROM positions WHERE hash_position = %s",
                    (hash_pos,)
                )
                pos = cursor.fetchone()
                if pos:
                    vx = pos['victoires_x'] + (1 if gagnant_id == joueur1_id else 0)
                    vo = pos['victoires_o'] + (1 if gagnant_id == joueur2_id else 0)
                    nu = pos['nuls'] + (1 if gagnant_id is None else 0)
                    nb = pos['nb_parties'] + 1
                    cursor.execute(
                        "UPDATE positions SET victoires_x=%s, victoires_o=%s, nuls=%s, nb_parties=%s WHERE hash_position=%s",
                        (vx, vo, nu, nb, hash_pos)
                    )
                else:
                    vx = 1 if gagnant_id == joueur1_id else 0
                    vo = 1 if gagnant_id == joueur2_id else 0
                    nu = 1 if gagnant_id is None else 0
                    cursor.execute(
                        """INSERT INTO positions (hash_position, plateau, nb_lignes, nb_colonnes,
                           joueur_suivant, nb_parties, victoires_x, victoires_o, nuls)
                           VALUES (%s, %s, %s, %s, %s, 1, %s, %s, %s)""",
                        (hash_pos, plateau_json, nb_lignes, nb_colonnes, joueur_suivant, vx, vo, nu)
                    )
                joueur = joueur_suivant
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"⚠️ Erreur update_position_stats : {e}")

    # ==================== MÉTHODES POUR BGA SCRAPER ====================

    def check_if_sequence_exists(self, sequence):
        cursor = None
        try:
            hash_partie = hashlib.md5(sequence.encode()).hexdigest()
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM parties WHERE hash_partie = %s", (hash_partie,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"❌ Erreur check_if_sequence_exists : {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def create_game(self, rows=6, cols=7, mode=1, confidence=1):
        cursor = None
        try:
            ia_id = self.get_or_create_joueur("BGA_Player1", est_ia=False)
            ia2_id = self.get_or_create_joueur("BGA_Player2", est_ia=False)
            cursor = self.connection.cursor()
            cursor.execute(
                """INSERT INTO parties (joueur1_id, joueur2_id, gagnant_id, sequence_coups,
                   hash_partie, statut, confiance, nb_lignes, nb_colonnes)
                   VALUES (%s, %s, NULL, '', '', 'en_cours', %s, %s, %s)""",
                (ia_id, ia2_id, confidence, rows, cols)
            )
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ Erreur create_game : {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def save_move(self, game_id, numero_coup, row, col, joueur_num):
        cursor = None
        try:
            pseudo = "BGA_Player1" if joueur_num == 1 else "BGA_Player2"
            joueur_id = self.get_or_create_joueur(pseudo)
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO coups (partie_id, numero_coup, colonne, joueur_id) VALUES (%s, %s, %s, %s)",
                (game_id, numero_coup, col, joueur_id)
            )
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ Erreur save_move : {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def update_game_result(self, game_id, winner=None):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT colonne FROM coups WHERE partie_id = %s ORDER BY numero_coup",
                (game_id,)
            )
            coups = cursor.fetchall()
            sequence = ''.join(str(c['colonne']) for c in coups)
            hash_partie = hashlib.md5(sequence.encode()).hexdigest()
            gagnant_id = None
            if winner is not None:
                pseudo = "BGA_Player1" if winner == 1 else "BGA_Player2"
                gagnant_id = self.get_or_create_joueur(pseudo)
            cursor.execute(
                """UPDATE parties SET gagnant_id=%s, sequence_coups=%s,
                   hash_partie=%s, statut='terminee' WHERE id=%s""",
                (gagnant_id, sequence, hash_partie, game_id)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Erreur update_game_result : {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def delete_partie(self, partie_id):
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM parties WHERE id = %s", (partie_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

