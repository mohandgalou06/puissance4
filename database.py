import os

def get_db_connection():
    # On force le retour à None pour ne même pas tenter la connexion sur Render
    print("Mode Render détecté : Connexion DB ignorée.")
    return None

def save_game_result(winner_name, moves_sequence):
    print(f"Sauvegarde simulée : {winner_name} a gagné avec {moves_sequence}")
