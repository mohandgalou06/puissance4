import mysql.connector
from mysql.connector import Error
import os

def get_db_connection():
    """
    Tente de se connecter à la base de données MySQL.
    Si la connexion échoue (ex: sur Render), retourne None au lieu de faire planter le site.
    """
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"), # Utilise 'localhost' par défaut
            user=os.environ.get("DB_USER", "root"),      # 'root' par défaut (XAMPP)
            password=os.environ.get("DB_PASS", ""),      # Vide par défaut (XAMPP)
            database=os.environ.get("DB_NAME", "puissance4_db"), # Remplace par le nom de TA base
            connect_timeout=3 # Crucial : abandonne après 3 sec si pas de réponse
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"⚠️ Impossible de se connecter à MySQL : {e}")
        print("INFO: Le jeu fonctionnera en mode local sans sauvegarde de données.")
        return None

def save_game_result(winner_name, moves_sequence):
    """Exemple de fonction pour sauvegarder une partie"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO parties (vainqueur, sequence) VALUES (%s, %s)"
            cursor.execute(query, (winner_name, moves_sequence))
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Partie sauvegardée en base de données.")
        except Error as e:
            print(f"❌ Erreur lors de la sauvegarde : {e}")
    else:
        print("💾 Sauvegarde ignorée (Pas de base de données connectée).")
