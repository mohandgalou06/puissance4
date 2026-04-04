


"""
DB MANAGER — Puissance 4
Compatible MySQL (Clever Cloud) via mysql-connector-python.
Utilise les variables d'environnement pour la connexion.
"""

import os
import hashlib
import json
import mysql.connector
from mysql.connector import Error


class DatabaseManager:
    def __init__(self):
        self.host     = os.environ.get("MYSQL_HOST",     "localhost")
        self.port     = int(os.environ.get("MYSQL_PORT", 3306))
        self.user     = os.environ.get("MYSQL_USER",     "root")
        self.password = os.environ.get("MYSQL_PASSWORD", "")
        self.database = os.environ.get("MYSQL_DATABASE", "puissance4")
        self.conn     = None

    # ──────────────────────────────────────────
    #  CONNEXION
    # ──────────────────────────────────────────

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                connection_timeout=10,
                autocommit=False,
            )
            if self.conn.is_connected():
                print(f"✅ MySQL connecté ({self.host}:{self.port}/{self.database})")
                self._init_schema()
                return True
        except Error as e:
            print(f"❌ MySQL erreur: {e}")
            self.conn = None
            return False

    def disconnect(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()

    def _ensure_connected(self):
        """Reconnecte si la connexion est perdue."""
        try:
            if self.conn and self.conn.is_connected():
                return True
        except Exception:
            pass
        return self.connect()

    # ──────────────────────────────────────────
    #  SCHÉMA
    # ──────────────────────────────────────────

    def _init_schema(self):
        """Crée les tables si elles n'existent pas."""
        ddl = """
        CREATE TABLE IF NOT EXISTS joueurs (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            pseudo           VARCHAR(50) NOT NULL UNIQUE,
            est_ia           BOOLEAN DEFAULT FALSE,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_pseudo (pseudo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS parties (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            joueur1_id       INT NOT NULL,
            joueur2_id       INT NOT NULL,
            gagnant_id       INT,
            sequence_coups   VARCHAR(200) NOT NULL,
            hash_partie      VARCHAR(64) UNIQUE,
            mode_jeu         VARCHAR(20) DEFAULT 'pvp',
            nb_lignes        TINYINT DEFAULT 9,
            nb_colonnes      TINYINT DEFAULT 9,
            nb_coups         TINYINT DEFAULT 0,
            statut           ENUM('en_cours','terminee','abandonnee') DEFAULT 'terminee',
            date_debut       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (joueur1_id) REFERENCES joueurs(id) ON DELETE CASCADE,
            FOREIGN KEY (joueur2_id) REFERENCES joueurs(id) ON DELETE CASCADE,
            FOREIGN KEY (gagnant_id) REFERENCES joueurs(id) ON DELETE SET NULL,
            INDEX idx_date (date_debut)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS coups (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            partie_id   INT NOT NULL,
            numero_coup TINYINT NOT NULL,
            colonne     TINYINT NOT NULL,
            joueur_id   INT NOT NULL,
            FOREIGN KEY (partie_id) REFERENCES parties(id) ON DELETE CASCADE,
            FOREIGN KEY (joueur_id) REFERENCES joueurs(id) ON DELETE CASCADE,
            UNIQUE KEY unique_coup (partie_id, numero_coup)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        try:
            cur = self.conn.cursor()
            for stmt in [s.strip() for s in ddl.split(';') if s.strip()]:
                cur.execute(stmt)
            self.conn.commit()
            cur.close()
        except Error as e:
            print(f"⚠️ Schema init: {e}")

    # ──────────────────────────────────────────
    #  JOUEURS
    # ──────────────────────────────────────────

    def get_or_create_joueur(self, pseudo, est_ia=False):
        if not self._ensure_connected():
            return None
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT id FROM joueurs WHERE pseudo = %s", (pseudo,))
            row = cur.fetchone()
            if row:
                cur.close()
                return row[0]
            cur.execute(
                "INSERT INTO joueurs (pseudo, est_ia) VALUES (%s, %s)",
                (pseudo, est_ia)
            )
            self.conn.commit()
            jid = cur.lastrowid
            cur.close()
            return jid
        except Error as e:
            print(f"❌ get_or_create_joueur: {e}")
            return None

    # ──────────────────────────────────────────
    #  PARTIES
    # ──────────────────────────────────────────

    def save_partie(self, joueur1, joueur2, sequence, mode='pvp',
                    gagnant=None, nb_lignes=9, nb_colonnes=9):
        """
        Sauvegarde une partie.
        joueur1, joueur2, gagnant = pseudos (str).
        sequence = "345671..." (colonnes jouées, 0-indexed).
        Retourne partie_id ou None.
        """
        if not sequence:
            return None
        if not self._ensure_connected():
            return None

        hash_p = hashlib.md5(sequence.encode()).hexdigest()

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT id FROM parties WHERE hash_partie = %s", (hash_p,))
            existing = cur.fetchone()
            if existing:
                cur.close()
                return existing[0]

            j1_id = self.get_or_create_joueur(joueur1, est_ia=(mode == 'iavsia'))
            j2_id = self.get_or_create_joueur(joueur2, est_ia=(mode in ('pvia', 'iavsia')))
            gagnant_id = None
            if gagnant == joueur1:
                gagnant_id = j1_id
            elif gagnant == joueur2:
                gagnant_id = j2_id

            cur.execute(
                """INSERT INTO parties
                   (joueur1_id, joueur2_id, gagnant_id, sequence_coups,
                    hash_partie, mode_jeu, nb_lignes, nb_colonnes, nb_coups, statut)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'terminee')""",
                (j1_id, j2_id, gagnant_id, sequence, hash_p, mode,
                 nb_lignes, nb_colonnes, len(sequence))
            )
            self.conn.commit()
            partie_id = cur.lastrowid

            # Coups
            j_cur_id = j1_id
            for i, col_str in enumerate(sequence):
                cur.execute(
                    "INSERT INTO coups (partie_id, numero_coup, colonne, joueur_id)"
                    " VALUES (%s,%s,%s,%s)",
                    (partie_id, i + 1, int(col_str), j_cur_id)
                )
                j_cur_id = j2_id if j_cur_id == j1_id else j1_id
            self.conn.commit()
            cur.close()
            return partie_id

        except Error as e:
            print(f"❌ save_partie: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return None

    # ──────────────────────────────────────────
    #  LECTURE
    # ──────────────────────────────────────────

    def get_all_parties(self, limit=200):
        if not self._ensure_connected():
            return []
        try:
            cur = self.conn.cursor(dictionary=True)
            cur.execute("""
                SELECT p.id, p.mode_jeu, p.statut,
                       p.nb_coups, p.nb_lignes, p.nb_colonnes,
                       p.sequence_coups, p.date_debut,
                       j1.pseudo  AS joueur1,
                       j2.pseudo  AS joueur2,
                       jg.pseudo  AS gagnant
                FROM parties p
                JOIN joueurs j1 ON p.joueur1_id = j1.id
                JOIN joueurs j2 ON p.joueur2_id = j2.id
                LEFT JOIN joueurs jg ON p.gagnant_id = jg.id
                ORDER BY p.date_debut DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()
            # Convertir datetime en string
            for r in rows:
                if r.get('date_debut'):
                    r['date_debut'] = r['date_debut'].strftime('%d/%m/%Y %H:%M')
            return rows
        except Error as e:
            print(f"❌ get_all_parties: {e}")
            return []

    def get_partie_detail(self, partie_id):
        if not self._ensure_connected():
            return None
        try:
            cur = self.conn.cursor(dictionary=True)
            cur.execute("""
                SELECT p.*, j1.pseudo AS joueur1, j2.pseudo AS joueur2,
                       jg.pseudo AS gagnant
                FROM parties p
                JOIN joueurs j1 ON p.joueur1_id = j1.id
                JOIN joueurs j2 ON p.joueur2_id = j2.id
                LEFT JOIN joueurs jg ON p.gagnant_id = jg.id
                WHERE p.id = %s
            """, (partie_id,))
            partie = cur.fetchone()
            if not partie:
                cur.close()
                return None
            if partie.get('date_debut'):
                partie['date_debut'] = partie['date_debut'].strftime('%d/%m/%Y %H:%M')

            cur.execute("""
                SELECT c.numero_coup, c.colonne, j.pseudo AS joueur
                FROM coups c
                JOIN joueurs j ON c.joueur_id = j.id
                WHERE c.partie_id = %s
                ORDER BY c.numero_coup
            """, (partie_id,))
            partie['coups'] = cur.fetchall()
            cur.close()
            return partie
        except Error as e:
            print(f"❌ get_partie_detail: {e}")
            return None

    def get_global_stats(self):
        if not self._ensure_connected():
            return {'parties': 0, 'joueurs': 0}
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM parties WHERE statut='terminee'")
            nb_p = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM joueurs")
            nb_j = cur.fetchone()[0]
            cur.close()
            return {'parties': nb_p, 'joueurs': nb_j}
        except Error as e:
            return {'parties': 0, 'joueurs': 0}

    def get_leaderboard(self, limit=10):
        if not self._ensure_connected():
            return []
        try:
            cur = self.conn.cursor(dictionary=True)
            cur.execute("""
                SELECT j.pseudo, j.est_ia,
                       COUNT(DISTINCT p.id) AS total_parties,
                       SUM(CASE WHEN p.gagnant_id = j.id THEN 1 ELSE 0 END) AS victoires
                FROM joueurs j
                LEFT JOIN parties p ON (p.joueur1_id=j.id OR p.joueur2_id=j.id)
                GROUP BY j.id, j.pseudo, j.est_ia
                ORDER BY victoires DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Error as e:
            print(f"❌ get_leaderboard: {e}")
            return []


