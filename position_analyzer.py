

"""
ANALYSEUR DE POSITIONS SIMPLE - MISSION 3.4
Analyse une position et recommande les meilleurs coups
"""

class PositionAnalyzer:
    def __init__(self, db):
        """
        Args:
            db: Instance de votre DatabaseManager
        """
        self.db = db
    
    def afficher_plateau(self, sequence, nb_lignes=6, nb_colonnes=7):
        """
        Affiche le plateau depuis une séquence
        """
        plateau = [[' '] * nb_colonnes for _ in range(nb_lignes)]
        joueur = 'X'
        
        # Reconstruire
        for col_str in sequence:
            col = int(col_str)
            for row in range(nb_lignes-1, -1, -1):
                if plateau[row][col] == ' ':
                    plateau[row][col] = joueur
                    break
            joueur = 'O' if joueur == 'X' else 'X'
        
        # Afficher
        print("\n  " + " ".join(str(i) for i in range(nb_colonnes)))
        print("  " + "-" * (nb_colonnes * 2 - 1))
        
        for row in plateau:
            print("| " + " ".join(cell if cell != ' ' else '·' for cell in row) + " |")
        
        print("  " + "-" * (nb_colonnes * 2 - 1))
        print()
    
    def analyser(self, sequence, nb_lignes=6, nb_colonnes=7):
        """
        MISSION 3.4 : Analyse une position et recommande les meilleurs coups
        
        Args:
            sequence: Séquence de coups (ex: "3344556")
            
        Returns:
            list: Recommandations triées
        """
        print("="*60)
        print("🎯 ANALYSE DE POSITION - MISSION 3.4")
        print("="*60)
        
        print(f"\n📝 Séquence: {sequence}")
        
        # Afficher le plateau
        self.afficher_plateau(sequence, nb_lignes, nb_colonnes)
        
        # Analyser avec la fonction de database.py
        recommendations = self.db.analyze_position(sequence, nb_lignes, nb_colonnes)
        
        if not recommendations:
            print("❌ Plateau plein ou aucun coup disponible")
            return []
        
        # Afficher les recommandations
        print("🎯 COUPS RECOMMANDÉS:")
        print("-" * 60)
        
        for i, (col, score, nb_parties) in enumerate(recommendations[:3], 1):
            if nb_parties > 0:
                taux = (score + 1) / 2 * 100  # Convertir en %
                print(f"{i}. Colonne {col} | Score: {score:+.3f} | Taux réussite: {taux:.1f}% | Parties: {nb_parties}")
            else:
                print(f"{i}. Colonne {col} | Position inconnue (pas de données)")
        
        if recommendations:
            meilleur = recommendations[0]
            print(f"\n💡 MEILLEUR COUP: Colonne {meilleur[0]}")
        
        print("="*60)
        
        return recommendations


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    from database import DatabaseManager
    
    # Connexion
    db = DatabaseManager(
        host="localhost",
        user="root",
        password="VOTRE_MOT_DE_PASSE",  # ← À MODIFIER
        database="puissance4"
    )
    
    if not db.connect():
        print("❌ Erreur de connexion")
        exit()
    
    # Vérifier qu'il y a des données
    cursor = db.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM parties")
    nb_parties = cursor.fetchone()[0]
    cursor.close()
    
    if nb_parties == 0:
        print("⚠️  Aucune partie dans la base !")
        print("\nGénérez des parties d'abord avec:")
        print("  db.generate_random_games(100)")
        db.disconnect()
        exit()
    
    print(f"✅ {nb_parties} parties dans la base")
    
    # Créer l'analyseur
    analyzer = PositionAnalyzer(db)
    
    # Exemple d'analyse
    print("\n" + "="*60)
    print("📌 EXEMPLE 1 : Position simple")
    print("="*60)
    
    sequence_exemple = "3344556"
    analyzer.analyser(sequence_exemple)
    
    # Mode interactif
    print("\n" + "="*60)
    print("🎮 MODE INTERACTIF")
    print("="*60)
    
    while True:
        sequence = input("\nEntrez une séquence (ou 'q' pour quitter): ").strip()
        
        if sequence.lower() == 'q':
            break
        
        if sequence:
            analyzer.analyser(sequence)
    
    db.disconnect()
    print("\n👋 Au revoir !")


"""
============================================================
COMMENT UTILISER POUR LA QUESTION DU PROFESSEUR:
============================================================

1. Générez d'abord des parties (Mission 3.2):
   
   from database import DatabaseManager
   db = DatabaseManager(...)
   db.connect()
   db.generate_random_games(500)  # Générer 500 parties

2. Analysez la position donnée par le prof:
   
   from position_analyzer import PositionAnalyzer
   analyzer = PositionAnalyzer(db)
   
   # Remplacez par la séquence du prof:
   sequence_prof = "33445566234..."
   
   analyzer.analyser(sequence_prof)

3. Le programme affiche:
   - Le plateau visuel
   - Les 3 meilleurs coups
   - Leur taux de réussite
   - Le meilleur coup recommandé

============================================================
"""





