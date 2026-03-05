
"""
EXEMPLE D'ANALYSE - Mission 3.4
Exemple concret d'analyse d'une position donnée par le professeur
"""

from database_extended import DatabaseManagerExtended
from position_analyzer import PositionAnalyzer

# Configuration
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Admin@123456"  # À MODIFIER
DB_NAME = "puissance4"

def analyser_position_professeur():
    """
    Analyse une position donnée par le professeur
    
    Adaptez cette fonction selon la position donnée:
    - Soit une séquence de coups: "33445566..."
    - Soit un plateau en format texte
    """
    
    print("="*70)
    print("🎓 ANALYSE DE LA POSITION DU PROFESSEUR")
    print("="*70)
    
    # Connexion à la base
    db = DatabaseManagerExtended(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    
    if not db.connect():
        print("\n❌ Impossible de se connecter à la base de données")
        print("Vérifiez votre configuration MySQL")
        return
    
    # Créer l'analyseur
    analyzer = PositionAnalyzer(db)
    
    # ====================================================================
    # OPTION 1: Position donnée sous forme de SÉQUENCE
    # ====================================================================
    
    print("\n📝 MÉTHODE 1: Analyse depuis une séquence")
    print("-" * 70)
    
    # Exemple de séquence (À REMPLACER par celle du professeur)
    sequence_prof = "3344556623"
    
    print(f"\nSéquence donnée: {sequence_prof}")
    
    # Analyser la position
    result = analyzer.analyze_from_sequence(sequence_prof, nb_lignes=6, nb_colonnes=7)
    
    # Afficher les recommandations
    if result['recommendations']:
        print("\n💡 COUPS RECOMMANDÉS POUR CETTE POSITION:")
        print("-" * 70)
        
        for i, (col, score, nb_parties) in enumerate(result['recommendations'][:3], 1):
            print(f"{i}. Jouer en colonne {col}")
            if nb_parties > 0:
                win_rate = (score + 1) / 2 * 100
                print(f"   └─ Taux de réussite: {win_rate:.1f}%")
                print(f"   └─ Basé sur {nb_parties} parties")
            else:
                print(f"   └─ Position inconnue (pas assez de données)")
    
    # ====================================================================
    # OPTION 2: Position donnée sous forme de PLATEAU
    # ====================================================================
    
    print("\n\n📝 MÉTHODE 2: Analyse depuis un plateau")
    print("-" * 70)
    
    # Si le professeur donne le plateau en format texte:
    # Format: lignes séparées par '/', '.' pour vide, 'X' et 'O' pour les pions
    # Exemple:
    plateau_texte = "......./......./......./...XO../..XXO../..OXOX."
    
    plateau = analyzer.parse_position_string(plateau_texte)
    
    print("\nPlateau donné:")
    analyzer.display_board(plateau)
    
    # Déterminer qui doit jouer (compter les pions)
    nb_x = sum(row.count('X') for row in plateau)
    nb_o = sum(row.count('O') for row in plateau)
    joueur_suivant = 'X' if nb_x <= nb_o else 'O'
    
    print(f"Joueur suivant: {joueur_suivant}")
    
    # Analyser
    result2 = analyzer.analyze_position(plateau, joueur_suivant)
    
    # ====================================================================
    # OPTION 3: Position interactive (pour tester plusieurs coups)
    # ====================================================================
    
    print("\n\n📝 MÉTHODE 3: Mode interactif")
    print("-" * 70)
    print("\nVoulez-vous tester des coups supplémentaires ?")
    
    if input("Continuer en mode interactif ? (o/n): ").lower() == 'o':
        current_sequence = sequence_prof
        
        while True:
            print(f"\n📍 Séquence actuelle: {current_sequence}")
            result = analyzer.analyze_from_sequence(current_sequence)
            
            if not result['recommendations']:
                print("\n🏁 Plateau plein ou partie terminée")
                break
            
            print(f"\n💡 Meilleur coup: Colonne {result['best_move']}")
            
            next_move = input("\nEntrez une colonne (ou 'q' pour quitter): ").strip()
            
            if next_move.lower() == 'q':
                break
            
            if next_move.isdigit():
                current_sequence += next_move
            else:
                print("❌ Colonne invalide")
    
    # Déconnexion
    db.disconnect()
    
    print("\n" + "="*70)
    print("✅ Analyse terminée")
    print("="*70 + "\n")

def generer_donnees_pour_analyse():
    """
    Génère des données pour améliorer la qualité de l'analyse
    """
    print("="*70)
    print("📊 GÉNÉRATION DE DONNÉES POUR L'ANALYSE")
    print("="*70)
    
    db = DatabaseManagerExtended(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    
    if not db.connect():
        print("\n❌ Impossible de se connecter")
        return
    
    from random_generator import RandomGameGenerator
    
    generator = RandomGameGenerator(db)
    
    print("\n💡 Pour obtenir de meilleures recommandations, il faut:")
    print("   - Beaucoup de parties dans la base")
    print("   - Des parties de qualité (confiance élevée)")
    
    print("\n🎲 Génération rapide de 500 parties multi-niveaux...")
    
    generator.generate_multi_confidence(nb_parties_par_niveau=100)
    
    db.disconnect()
    
    print("\n✅ Données générées ! Relancez l'analyse pour voir l'amélioration")

def exemple_complet():
    """
    Exemple complet d'utilisation
    """
    print("\n" + "="*70)
    print("🎮 EXEMPLE COMPLET D'UTILISATION")
    print("="*70)
    
    print("""
CONTEXTE:
Le professeur vous donne une position de Puissance 4 et vous demande
de recommander les 3 meilleurs coups suivants.

ÉTAPES:

1. PRÉPARER LA BASE DE DONNÉES
   - Créer le schéma: mysql -u root -p < schema_updated.sql
   - Générer des données de référence (option ci-dessous)

2. ANALYSER LA POSITION
   - Convertir la position en séquence ou format texte
   - Lancer l'analyse avec ce script

3. INTERPRÉTER LES RÉSULTATS
   - Le score indique la qualité du coup (-1 à +1)
   - Le taux de réussite est un pourcentage (0-100%)
   - Plus il y a de parties, plus la recommandation est fiable

EXEMPLE DE RÉPONSE AU PROFESSEUR:

"Pour la position donnée (séquence: 33445566), voici les 3 meilleurs coups:

1. Colonne 3 (recommandé)
   - Taux de réussite: 67.8%
   - Basé sur 145 parties similaires
   - Ce coup mène généralement à la victoire

2. Colonne 5
   - Taux de réussite: 54.2%
   - Basé sur 89 parties similaires
   - Coup défensif, évite la défaite

3. Colonne 2
   - Taux de réussite: 48.1%
   - Basé sur 67 parties similaires
   - Coup risqué, peut mener au nul"

    """)
    
    print("="*70)
    print("QUE VOULEZ-VOUS FAIRE ?")
    print("="*70)
    print()
    print("1. Générer des données de référence (recommandé en premier)")
    print("2. Analyser la position du professeur")
    print("3. Quitter")
    print()
    
    choice = input("Votre choix (1-3): ").strip()
    
    if choice == "1":
        generer_donnees_pour_analyse()
    elif choice == "2":
        analyser_position_professeur()
    else:
        print("\n👋 Au revoir !")

if __name__ == "__main__":
    exemple_complet()







