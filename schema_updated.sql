

-- Schéma optimisé pour visualisation et navigation

DROP DATABASE IF EXISTS puissance4;
CREATE DATABASE puissance4;
USE puissance4;

-- ==================== TABLE JOUEURS ====================
CREATE TABLE joueurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pseudo VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100),
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    est_ia BOOLEAN DEFAULT FALSE,
    
    INDEX idx_pseudo (pseudo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLE PARTIES ====================
CREATE TABLE parties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    joueur1_id INT NOT NULL,
    joueur2_id INT NOT NULL,
    gagnant_id INT,
    
    -- Identification unique de la partie
    sequence_coups VARCHAR(100) NOT NULL,
    hash_partie VARCHAR(64) UNIQUE,
    
    -- Timing
    date_debut TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_fin TIMESTAMP NULL,
    duree_secondes INT DEFAULT 0,
    
    -- Statut
    statut ENUM('en_cours', 'terminee', 'abandonnee') DEFAULT 'terminee',
    
    FOREIGN KEY (joueur1_id) REFERENCES joueurs(id) ON DELETE CASCADE,
    FOREIGN KEY (joueur2_id) REFERENCES joueurs(id) ON DELETE CASCADE,
    FOREIGN KEY (gagnant_id) REFERENCES joueurs(id) ON DELETE SET NULL,
    
    INDEX idx_joueur1 (joueur1_id),
    INDEX idx_joueur2 (joueur2_id),
    INDEX idx_hash (hash_partie),
    INDEX idx_date (date_debut)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLE COUPS ====================
CREATE TABLE coups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    partie_id INT NOT NULL,
    numero_coup TINYINT NOT NULL,
    colonne TINYINT NOT NULL,
    joueur_id INT NOT NULL,
    
    FOREIGN KEY (partie_id) REFERENCES parties(id) ON DELETE CASCADE,
    FOREIGN KEY (joueur_id) REFERENCES joueurs(id) ON DELETE CASCADE,
    
    INDEX idx_partie (partie_id),
    UNIQUE KEY unique_coup (partie_id, numero_coup)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLE SYMETRIQUES ====================
CREATE TABLE symetriques (
    id INT AUTO_INCREMENT PRIMARY KEY,
    partie_originale_id INT NOT NULL,
    partie_symetrique_id INT NOT NULL,
    
    FOREIGN KEY (partie_originale_id) REFERENCES parties(id) ON DELETE CASCADE,
    FOREIGN KEY (partie_symetrique_id) REFERENCES parties(id) ON DELETE CASCADE,
    
    INDEX idx_originale (partie_originale_id),
    INDEX idx_symetrique (partie_symetrique_id),
    UNIQUE KEY unique_lien (partie_originale_id, partie_symetrique_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== VUES ====================

-- Vue statistiques joueurs
CREATE OR REPLACE VIEW stats_joueurs AS
SELECT 
    j.id,
    j.pseudo,
    j.est_ia,
    COUNT(DISTINCT p.id) as total_parties,
    SUM(CASE WHEN p.gagnant_id = j.id THEN 1 ELSE 0 END) as victoires,
    SUM(CASE WHEN (p.joueur1_id = j.id OR p.joueur2_id = j.id) 
        AND p.gagnant_id IS NOT NULL 
        AND p.gagnant_id != j.id THEN 1 ELSE 0 END) as defaites,
    SUM(CASE WHEN (p.joueur1_id = j.id OR p.joueur2_id = j.id) 
        AND p.gagnant_id IS NULL 
        AND p.statut = 'terminee' THEN 1 ELSE 0 END) as nuls
FROM joueurs j
LEFT JOIN parties p ON (p.joueur1_id = j.id OR p.joueur2_id = j.id)
GROUP BY j.id, j.pseudo, j.est_ia;

-- ==================== DONNÉES INITIALES ====================
INSERT INTO joueurs (pseudo, email, est_ia) VALUES 
    ('IA', 'ia@puissance4.local', TRUE),
    ('Joueur1', 'joueur1@test.com', FALSE),
    ('Joueur2', 'joueur2@test.com', FALSE);

-- ==================== AFFICHAGE ====================
SHOW TABLES;
SELECT '✅ Base de données Puissance 4 créée avec succès !' as Message;                            

-- Mission 3.1 : Ajouter les nouveaux champs

-- 1. Ajouter confiance et nb_colonnes à la table parties
ALTER TABLE parties 
ADD COLUMN confiance TINYINT DEFAULT 1 COMMENT 'Niveau 0-10: 0=perdre, 1=aléatoire, 6+=expert',
ADD COLUMN nb_lignes TINYINT DEFAULT 6,
ADD COLUMN nb_colonnes TINYINT DEFAULT 7,
ADD COLUMN source ENUM('local', 'bga', 'import') DEFAULT 'local',
ADD COLUMN bga_game_id INT UNIQUE,
ADD COLUMN bga_url VARCHAR(255),
ADD COLUMN elo_joueur1 INT,
ADD COLUMN elo_joueur2 INT;

-- 2. Ajouter champs BGA aux joueurs
ALTER TABLE joueurs
ADD COLUMN bga_id INT UNIQUE,
ADD COLUMN bga_pseudo VARCHAR(50);

-- 3. Créer la table positions pour l'analyse (MISSION 3.4)
CREATE TABLE IF NOT EXISTS positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hash_position VARCHAR(64) UNIQUE NOT NULL,
    plateau TEXT NOT NULL,
    nb_lignes TINYINT NOT NULL,
    nb_colonnes TINYINT NOT NULL,
    joueur_suivant ENUM('X', 'O') NOT NULL,
    nb_parties INT DEFAULT 0,
    victoires_x INT DEFAULT 0,
    victoires_o INT DEFAULT 0,
    nuls INT DEFAULT 0,
    meilleur_coup TINYINT,
    score_confiance DECIMAL(5,3),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_hash (hash_position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Afficher confirmation
SELECT '✅ Modifications SQL appliquées avec succès !' as Message;
SELECT 'Vous pouvez maintenant utiliser les missions 3.1 à 3.4' as Info;



