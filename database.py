
"""
DATABASE MANAGER - Version Corrigée
BUG FIX: nb_colonnes ajouté comme paramètre dans import_partie_from_sequence
"""

import mysql.connector
from mysql.connector import Error
import hashlib
import random
import json


class DatabaseManager:
    def __init__(self, host="localhost", user="root", password="", database="puissance4"):
        self.host     = host
        self.user     = user
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
        except Error as e:
            print(f"❌ Erreur connexion BDD : {e}")
            return False

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔌 Déconnexion MySQL")

    # ==================== GESTION JOUEURS ====================

    def get_or_create_joueur(self, pseudo, email="", est_ia=False):
        """Récupère ou crée un joueur"""
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
        except Error as e:
            print(f"❌ Erreur get_or_create_joueur : {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    # ==================== GESTION PARTIES ====================

    def import_partie_from_sequence(self, sequence, joueur1_id=None, joueur2_id=None,
                                     nb_colonnes=7, nb_lignes=6):
        """
        Importe une partie depuis une séquence de coups.
        BUG FIX: nb_colonnes est maintenant un paramètre (n'était pas défini avant).
        """
        cursor = None
        try:
            hash_partie = hashlib.md5(sequence.encode()).hexdigest()
            sequence_sym = self.calculer_symetrique(sequence, nb_colonnes)
            hash_sym = hashlib.md5(sequence_sym.encode()).hexdigest()

            cursor = self.connection.cursor()

            cursor.execute("SELECT id FROM parties WHERE hash_partie = %s", (hash_partie,))
            existing = cursor.fetchone()
            if existing:
                return {
                    'status': 'exists',
                    'partie_id': existing[0],
                    'message': f'Cette partie existe déjà (ID: {existing[0]})'
                }

            cursor.execute("SELECT id FROM parties WHERE hash_partie = %s", (hash_sym,))
            existing_sym = cursor.fetchone()
            if existing_sym:
                return {
                    'status': 'symetrique',
                    'partie_id': existing_sym[0],
                    'message': f'Une partie symétrique existe déjà (ID: {existing_sym[0]})'
                }

            if not joueur1_id:
                joueur1_id = self.get_or_create_joueur("Joueur1")
            if not joueur2_id:
                joueur2_id = self.get_or_create_joueur("Joueur2")

            gagnant_id = self.simuler_partie(sequence, joueur1_id, joueur2_id,
                                              nb_lignes=nb_lignes, nb_colonnes=nb_colonnes)

            cursor.execute(
                """INSERT INTO parties
                   (joueur1_id, joueur2_id, gagnant_id, sequence_coups, hash_partie,
                    statut, nb_lignes, nb_colonnes)
                   VALUES (%s, %s, %s, %s, %s, 'terminee', %s, %s)""",
                (joueur1_id, joueur2_id, gagnant_id, sequence, hash_partie,
                 nb_lignes, nb_colonnes)
            )
            self.connection.commit()
            partie_id = cursor.lastrowid

            joueur_courant_id = joueur1_id
            for i, col_str in enumerate(sequence):
                col = int(col_str)
                cursor.execute(
                    """INSERT INTO coups (partie_id, numero_coup, colonne, joueur_id)
                       VALUES (%s, %s, %s, %s)""",
                    (partie_id, i + 1, col, joueur_courant_id)
                )
                joueur_courant_id = joueur2_id if joueur_courant_id == joueur1_id else joueur1_id

            self.connection.commit()

            # Mettre à jour les stats de positions
            self.update_position_stats(sequence, gagnant_id, joueur1_id, joueur2_id,
                                       nb_lignes=nb_lignes, nb_colonnes=nb_colonnes)

            return {
                'status': 'created',
                'partie_id': partie_id,
                'message': f'Partie importée avec succès (ID: {partie_id})'
            }

        except Error as e:
            print(f"❌ Erreur import_partie : {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if cursor:
                cursor.close()

    def calculer_symetrique(self, sequence, nb_colonnes=7):
        """
        Calcule la séquence symétrique (miroir horizontal).
        Ex: 7 colonnes → col 0↔6, 1↔5, 2↔4, 3↔3
        Ex: 9 colonnes → col 0↔8, 1↔7, ...
        """
        if not sequence:
            return ""
        return ''.join(str(nb_colonnes - 1 - int(c)) for c in sequence)

    def simuler_partie(self, sequence, joueur1_id, joueur2_id, nb_lignes=6, nb_colonnes=7):
        """Simule une partie pour déterminer le gagnant"""
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
        """Vérifie si un joueur a gagné (4 alignés)"""
        # Horizontal
        for r in range(nb_lignes):
            for c in range(nb_colonnes - 3):
                if all(plateau[r][c + i] == joueur for i in range(4)):
                    return True
        # Vertical
        for c in range(nb_colonnes):
            for r in range(nb_lignes - 3):
                if all(plateau[r + i][c] == joueur for i in range(4)):
                    return True
        # Diagonale \
        for r in range(nb_lignes - 3):
            for c in range(nb_colonnes - 3):
                if all(plateau[r + i][c + i] == joueur for i in range(4)):
                    return True
        # Diagonale /
        for r in range(3, nb_lignes):
            for c in range(nb_colonnes - 3):
                if all(plateau[r - i][c + i] == joueur for i in range(4)):
                    return True
        return False

    # ==================== RÉCUPÉRATION DONNÉES ====================

    def get_all_parties(self):
        """Récupère toutes les parties avec pseudo des joueurs"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT p.*,
                   j1.pseudo as joueur1_pseudo,
                   j2.pseudo as joueur2_pseudo,
                   jg.pseudo as gagnant_pseudo
                   FROM parties p
                   JOIN joueurs j1 ON p.joueur1_id = j1.id
                   JOIN joueurs j2 ON p.joueur2_id = j2.id
                   LEFT JOIN joueurs jg ON p.gagnant_id = jg.id
                   ORDER BY p.date_debut DESC"""
            )
            return cursor.fetchall()
        except Error as e:
            print(f"❌ Erreur get_all_parties : {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_partie_coups(self, partie_id):
        """Récupère tous les coups d'une partie dans l'ordre"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT c.*, j.pseudo as joueur_pseudo
                   FROM coups c
                   JOIN joueurs j ON c.joueur_id = j.id
                   WHERE c.partie_id = %s
                   ORDER BY c.numero_coup""",
                (partie_id,)
            )
            return cursor.fetchall()
        except Error as e:
            print(f"❌ Erreur get_partie_coups : {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_all_tables(self):
        """Liste toutes les tables de la BDD"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES")
            return [table[0] for table in cursor.fetchall()]
        except Error as e:
            print(f"❌ Erreur get_all_tables : {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_table_data(self, table_name, limit=100):
        """Récupère les données d'une table (limite = limit lignes)"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT %s", (limit,))
            return cursor.fetchall()
        except Error as e:
            print(f"❌ Erreur get_table_data ({table_name}) : {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_stats_joueur(self, joueur_id):
        """Récupère les statistiques d'un joueur"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM stats_joueurs WHERE id = %s", (joueur_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"❌ Erreur get_stats_joueur : {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    # ==================== POUR PUISSANCE4.PY ====================

    def save_partie_complete(self, joueur1_id, joueur2_id, gagnant_id, sequence, duree=0,
                              nb_lignes=6, nb_colonnes=7):
        """
        Sauvegarde une partie complète (coups inclus).
        Utilisé depuis puissance4.py → menu Sauvegarder.
        """
        cursor = None
        try:
            if not sequence:
                print("⚠️ Séquence vide, rien à sauvegarder")
                return None

            hash_partie = hashlib.md5(sequence.encode()).hexdigest()
            cursor = self.connection.cursor()

            # Vérifier si déjà existante
            cursor.execute("SELECT id FROM parties WHERE hash_partie = %s", (hash_partie,))
            existing = cursor.fetchone()
            if existing:
                print(f"⚠️ Partie déjà existante (ID: {existing[0]})")
                return existing[0]

            # Insérer la partie
            cursor.execute(
                """INSERT INTO parties
                   (joueur1_id, joueur2_id, gagnant_id, duree_secondes,
                    statut, sequence_coups, hash_partie, nb_lignes, nb_colonnes)
                   VALUES (%s, %s, %s, %s, 'terminee', %s, %s, %s, %s)""",
                (joueur1_id, joueur2_id, gagnant_id, duree,
                 sequence, hash_partie, nb_lignes, nb_colonnes)
            )
            self.connection.commit()
            partie_id = cursor.lastrowid

            # Insérer les coups
            joueur_courant_id = joueur1_id
            for i, col_str in enumerate(sequence):
                col = int(col_str)
                cursor.execute(
                    """INSERT INTO coups (partie_id, numero_coup, colonne, joueur_id)
                       VALUES (%s, %s, %s, %s)""",
                    (partie_id, i + 1, col, joueur_courant_id)
                )
                joueur_courant_id = (
                    joueur2_id if joueur_courant_id == joueur1_id else joueur1_id
                )

            self.connection.commit()
            print(f"✅ Partie complète sauvegardée (ID: {partie_id})")
            return partie_id

        except Error as e:
            print(f"❌ Erreur save_partie_complete : {e}")
            if self.connection:
                self.connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()

    def save_partie(self, joueur1_id, joueur2_id, gagnant_id=None, duree=0):
        """Sauvegarde une partie sans les coups (version légère)"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """INSERT INTO parties
                   (joueur1_id, joueur2_id, gagnant_id, duree_secondes,
                    statut, sequence_coups, hash_partie)
                   VALUES (%s, %s, %s, %s, 'terminee', '', '')""",
                (joueur1_id, joueur2_id, gagnant_id, duree)
            )
            self.connection.commit()
            partie_id = cursor.lastrowid
            print(f"💾 Partie sauvegardée (ID: {partie_id})")
            return partie_id
        except Error as e:
            print(f"❌ Erreur save_partie : {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def save_coup(self, partie_id, numero_coup, colonne, joueur_id, temps_reflexion=0):
        """Sauvegarde un coup joué"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """INSERT INTO coups (partie_id, numero_coup, colonne, joueur_id)
                   VALUES (%s, %s, %s, %s)""",
                (partie_id, numero_coup, colonne, joueur_id)
            )
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"❌ Erreur save_coup : {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def update_partie_sequence(self, partie_id):
        """Recalcule et met à jour la séquence+hash depuis les coups enregistrés"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT colonne FROM coups WHERE partie_id = %s ORDER BY numero_coup",
                (partie_id,)
            )
            coups = cursor.fetchall()
            sequence = ''.join(str(coup['colonne']) for coup in coups)
            hash_partie = hashlib.md5(sequence.encode()).hexdigest()
            cursor.execute(
                "UPDATE parties SET sequence_coups = %s, hash_partie = %s WHERE id = %s",
                (sequence, hash_partie, partie_id)
            )
            self.connection.commit()
            print(f"📝 Séquence mise à jour pour partie {partie_id}: {sequence}")
            return True
        except Error as e:
            print(f"❌ Erreur update_partie_sequence : {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    # ==================== GÉNÉRATION ALÉATOIRE ====================

    def generate_random_games(self, nb_parties=100, nb_lignes=6, nb_colonnes=7, confiance=1):
        """
        Génère nb_parties parties aléatoires et les insère en BDD.
        confiance : 0 = joue pour perdre, 1 = aléatoire, 10 = expert
        """
        print(f"🎲 Génération de {nb_parties} parties (confiance={confiance}, {nb_lignes}×{nb_colonnes})...")

        ia1_id = self.get_or_create_joueur(f"IA_Rand_{confiance}_1", est_ia=True)
        ia2_id = self.get_or_create_joueur(f"IA_Rand_{confiance}_2", est_ia=True)

        count = 0

        for i in range(nb_parties):
            plateau    = [[' '] * nb_colonnes for _ in range(nb_lignes)]
            sequence   = ""
            joueur     = 'X'
            gagnant_id = None

            for _ in range(nb_lignes * nb_colonnes):
                colonnes_dispo = [c for c in range(nb_colonnes) if plateau[0][c] == ' ']
                if not colonnes_dispo:
                    break

                col = random.choice(colonnes_dispo)
                sequence += str(col)

                for row in range(nb_lignes - 1, -1, -1):
                    if plateau[row][col] == ' ':
                        plateau[row][col] = joueur
                        break

                if self.check_win(plateau, joueur, nb_lignes, nb_colonnes):
                    gagnant_id = ia1_id if joueur == 'X' else ia2_id
                    break

                joueur = 'O' if joueur == 'X' else 'X'

            if sequence:
                cursor = self.connection.cursor()
                hash_partie = hashlib.md5(sequence.encode()).hexdigest()
                try:
                    cursor.execute(
                        """INSERT INTO parties
                           (joueur1_id, joueur2_id, gagnant_id, sequence_coups, hash_partie,
                            statut, confiance, nb_lignes, nb_colonnes)
                           VALUES (%s, %s, %s, %s, %s, 'terminee', %s, %s, %s)""",
                        (ia1_id, ia2_id, gagnant_id, sequence, hash_partie,
                         confiance, nb_lignes, nb_colonnes)
                    )
                    self.connection.commit()
                    count += 1
                except Exception:
                    self.connection.rollback()
                finally:
                    cursor.close()

            if (i + 1) % 100 == 0:
                print(f"   {i + 1}/{nb_parties}...")

        print(f"✅ {count} parties créées")
        return count

    # ==================== ANALYSE DE POSITIONS ====================

    def analyze_position(self, sequence, nb_lignes=6, nb_colonnes=7):
        """
        Analyse une position et recommande les meilleurs coups.
        Retourne : [(colonne, score, nb_parties)] triés par meilleur score
        """
        plateau  = [[' '] * nb_colonnes for _ in range(nb_lignes)]
        joueur   = 'X'

        for col_str in sequence:
            col = int(col_str)
            for row in range(nb_lignes - 1, -1, -1):
                if plateau[row][col] == ' ':
                    plateau[row][col] = joueur
                    break
            joueur = 'O' if joueur == 'X' else 'X'

        joueur_suivant   = joueur
        recommendations  = []

        for col in range(nb_colonnes):
            if plateau[0][col] != ' ':
                continue

            plateau_test = [row[:] for row in plateau]
            for row in range(nb_lignes - 1, -1, -1):
                if plateau_test[row][col] == ' ':
                    plateau_test[row][col] = joueur_suivant
                    break

            plateau_json = json.dumps(plateau_test)
            hash_pos     = hashlib.md5(plateau_json.encode()).hexdigest()

            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT victoires_x, victoires_o, nuls, nb_parties FROM positions "
                "WHERE hash_position = %s",
                (hash_pos,)
            )
            pos = cursor.fetchone()
            cursor.close()

            if pos and pos['nb_parties'] > 0:
                if joueur_suivant == 'X':
                    score = (pos['victoires_x'] - pos['victoires_o']) / pos['nb_parties']
                else:
                    score = (pos['victoires_o'] - pos['victoires_x']) / pos['nb_parties']
                recommendations.append((col, score, pos['nb_parties']))
            else:
                recommendations.append((col, 0.0, 0))

        recommendations.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return recommendations

    def update_position_stats(self, sequence, gagnant_id, joueur1_id, joueur2_id,
                               nb_lignes=6, nb_colonnes=7):
        """Met à jour les statistiques de positions après une partie"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            plateau  = [[' '] * nb_colonnes for _ in range(nb_lignes)]
            joueur   = 'X'

            for col_str in sequence:
                col = int(col_str)

                for row in range(nb_lignes - 1, -1, -1):
                    if plateau[row][col] == ' ':
                        plateau[row][col] = joueur
                        break

                plateau_json   = json.dumps(plateau)
                hash_pos       = hashlib.md5(plateau_json.encode()).hexdigest()
                joueur_suivant = 'O' if joueur == 'X' else 'X'

                cursor.execute(
                    "SELECT victoires_x, victoires_o, nuls, nb_parties "
                    "FROM positions WHERE hash_position = %s",
                    (hash_pos,)
                )
                pos = cursor.fetchone()

                if pos:
                    vx = pos['victoires_x'] + (1 if gagnant_id == joueur1_id else 0)
                    vo = pos['victoires_o'] + (1 if gagnant_id == joueur2_id else 0)
                    nu = pos['nuls']        + (1 if gagnant_id is None else 0)
                    nb = pos['nb_parties']  + 1
                    cursor.execute(
                        "UPDATE positions SET victoires_x=%s, victoires_o=%s, "
                        "nuls=%s, nb_parties=%s WHERE hash_position=%s",
                        (vx, vo, nu, nb, hash_pos)
                    )
                else:
                    vx = 1 if gagnant_id == joueur1_id else 0
                    vo = 1 if gagnant_id == joueur2_id else 0
                    nu = 1 if gagnant_id is None else 0
                    cursor.execute(
                        """INSERT INTO positions
                           (hash_position, plateau, nb_lignes, nb_colonnes,
                            joueur_suivant, nb_parties, victoires_x, victoires_o, nuls)
                           VALUES (%s, %s, %s, %s, %s, 1, %s, %s, %s)""",
                        (hash_pos, plateau_json, nb_lignes, nb_colonnes,
                         joueur_suivant, vx, vo, nu)
                    )

                joueur = joueur_suivant

            self.connection.commit()
            cursor.close()

        except Error as e:
            print(f"⚠️ Erreur update_position_stats : {e}")

    def delete_partie(self, partie_id):
        """Supprime une partie et ses coups de la base de données."""
        cursor = None
        try:
            cursor = self.connection.cursor()
            # Les coups sont supprimés en cascade (ON DELETE CASCADE)
            cursor.execute("DELETE FROM parties WHERE id = %s", (partie_id,))
            self.connection.commit()
            deleted = cursor.rowcount
            print(f"Partie #{partie_id} supprimee ({deleted} ligne(s))")
            return deleted > 0
        except Error as e:
            print(f"Erreur delete_partie : {e}")
            if self.connection:
                self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

