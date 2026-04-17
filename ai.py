import random

import generateur_tournoi
from constants import JAUNE, ROUGE
from database import Database
from generateur_tournoi import minimax_iteratif


class IA_Tournoi:
    def __init__(self):
        self.db = Database()
        self.budget_secondes = 5.0
        self.max_profondeur = 20
        self.dernier_message = ""
        self.utiliser_bdd = True
        self.memoire_coups = {}
        self.memoire_max_taille = 20_000
        self.memoire_nb_pions_max = 12

    def _compter_pions(self, logic):
        return sum(1 for ligne in logic.grille for val in ligne if val != 0)

    def _colonne_miroir(self, logic, colonne):
        return len(logic.grille[0]) - 1 - colonne

    def _signature(self, logic, joueur_ia):
        return joueur_ia, tuple(tuple(ligne) for ligne in logic.grille)

    def _signature_miroir(self, logic, joueur_ia):
        return joueur_ia, tuple(tuple(reversed(ligne)) for ligne in logic.grille)

    def chercher_dans_memoire(self, logic, joueur_ia):
        if self._compter_pions(logic) > self.memoire_nb_pions_max:
            return None

        coup = self.memoire_coups.get(self._signature(logic, joueur_ia))
        if coup is not None and logic.colonne_valide(coup):
            return coup

        coup_miroir = self.memoire_coups.get(self._signature_miroir(logic, joueur_ia))
        if coup_miroir is None:
            return None

        coup = self._colonne_miroir(logic, coup_miroir)
        return coup if logic.colonne_valide(coup) else None

    def memoriser_coup(self, logic, joueur_ia, colonne):
        if colonne is None or self._compter_pions(logic) > self.memoire_nb_pions_max:
            return

        entrees = (
            (self._signature(logic, joueur_ia), colonne),
            (self._signature_miroir(logic, joueur_ia), self._colonne_miroir(logic, colonne)),
        )

        for cle, coup in entrees:
            if cle not in self.memoire_coups and len(self.memoire_coups) >= self.memoire_max_taille:
                self.memoire_coups.pop(next(iter(self.memoire_coups)))
            self.memoire_coups[cle] = coup

    def chercher_dans_bdd(self, coups_joues, joueur_ia):
        if not self.utiliser_bdd:
            return None

        if not self.db.assurer_connexion():
            return None

        sequence_actuelle = "".join(str(coup[1]) for coup in coups_joues)
        statut_voulu = "VICTOIRE_ROUGE" if joueur_ia == ROUGE else "VICTOIRE_JAUNE"

        requete = """
            SELECT coups_sequence
            FROM parties
            WHERE coups_sequence LIKE %s
              AND statut = %s
            ORDER BY confiance DESC
            LIMIT 1
        """

        try:
            cursor = self.db.conn.cursor()
            cursor.execute(requete, (sequence_actuelle + "%", statut_voulu))
            resultat = cursor.fetchone()
            cursor.close()

            if resultat:
                sequence_trouvee = resultat[0]
                if len(sequence_trouvee) > len(sequence_actuelle):
                    return int(sequence_trouvee[len(sequence_actuelle)])

        except Exception:
            self.db.conn = None

        return None

    def trouver_coup_evident(self, logic, joueur_ia):
        adversaire = JAUNE if joueur_ia == ROUGE else ROUGE

        for c in range(9):
            if logic.colonne_valide(c):
                l = logic.placer_pion(c, joueur_ia)
                if logic.victoire(joueur_ia):
                    logic.grille[l][c] = 0
                    return c
                logic.grille[l][c] = 0

        for c in range(9):
            if logic.colonne_valide(c):
                l = logic.placer_pion(c, adversaire)
                if logic.victoire(adversaire):
                    logic.grille[l][c] = 0
                    return c
                logic.grille[l][c] = 0

        return None
    
    def coup_bdd_est_sain(self, logic, joueur_ia, coup_bdd, profondeur_test=4, budget_test=0.20):
        if coup_bdd is None or not logic.colonne_valide(coup_bdd):
            return False

        adversaire = JAUNE if joueur_ia == ROUGE else ROUGE
        l = logic.placer_pion(coup_bdd, joueur_ia)

        try:
            # Si le coup BDD gagne immédiatement, on le garde.
            if logic.victoire(joueur_ia):
                return True

            # Sécurité 1 : refuser si l'adversaire peut gagner immédiatement derrière.
            for c in range(9):
                if logic.colonne_valide(c):
                    l2 = logic.placer_pion(c, adversaire)
                    gagne = logic.victoire(adversaire)
                    logic.grille[l2][c] = 0
                    if gagne:
                        return False

            # Sécurité 2 : mini-vérification tactique avec le moteur.
            # Important : tab_id=None pour ne pas polluer la barre de progression.
            _, score_test = minimax_iteratif(
                logic,
                est_maximisant=(adversaire == JAUNE),
                max_profondeur=profondeur_test,
                budget_secondes=budget_test,
                tab_id=None
            )

            if score_test is None:
                return True

            # score > 0 avantage JAUNE ; score < 0 avantage ROUGE
            if joueur_ia == JAUNE:
                return score_test > -35_000
            else:
                return score_test < 35_000

        finally:
            logic.grille[l][coup_bdd] = 0


    def _extraire_demi_coups(self, score, prof_atteinte):
        if score is None or abs(score) < 9_000_000:
            return None

        reste = max(0, (abs(score) - 10_000_000) // 1000)
        demi_coups = max(1, prof_atteinte - reste)
        return int(demi_coups)
    

    def jouer_coup(self, logic, coups_joues, joueur_ia, tab_id=None):
        nom_joueur = "Rouge" if joueur_ia == ROUGE else "Jaune"
        print(f"\n[IA Terminator] Reflexion pour {nom_joueur}...", flush=True)

        nb_pions = self._compter_pions(logic)

        coup_urgent = self.trouver_coup_evident(logic, joueur_ia)
        if coup_urgent is not None:
            self.memoriser_coup(logic, joueur_ia, coup_urgent)
            self.dernier_message = "Coup critique joue immediatement."
            return coup_urgent

        coup_memoire = self.chercher_dans_memoire(logic, joueur_ia)
        if coup_memoire is not None:
            self.dernier_message = "Cache memoire: coup retrouve instantanement."
            return coup_memoire

        if nb_pions < 2:
            for c in [4, 5, 3]:
                if logic.colonne_valide(c):
                    self.memoriser_coup(logic, joueur_ia, c)
                    self.dernier_message = "Ouverture centre."
                    return c

        if len(coups_joues) == nb_pions:
            coup_bdd = self.chercher_dans_bdd(coups_joues, joueur_ia)
            if coup_bdd is not None and logic.colonne_valide(coup_bdd):
                if self.coup_bdd_est_sain(logic, joueur_ia, coup_bdd):
                    self.memoriser_coup(logic, joueur_ia, coup_bdd)
                    self.dernier_message = "Base de donnees: coup theorique valide."
                    return coup_bdd
                else:
                    self.dernier_message = "Base de donnees rejetee: coup tactiquement dangereux."

        colonne, score = minimax_iteratif(
            logic,
            est_maximisant=(joueur_ia == JAUNE),
            max_profondeur=self.max_profondeur,
            budget_secondes=self.budget_secondes,
            tab_id=tab_id
        )

        prof_atteinte = generateur_tournoi.LAST_COMPLETED_DEPTH

        infos_mat = self._extraire_infos_mat(score, prof_atteinte)

        if score is None:
            self.dernier_message = "Analyse terminee sans resultat exploitable."
        elif infos_mat is not None:
            self.dernier_message = (
                f"Solution trouvee : {infos_mat['gagnant']} gagne en "
                f"{infos_mat['demi_coups']} demi-coups "
                f"(~ {infos_mat['coups']} coup(s)). "
                f"Profondeur completee : {prof_atteinte}."
            )
        else:
            self.dernier_message = (
                f"Aucune victoire forcee trouvee jusqu'a la profondeur {prof_atteinte}."
            )

        if colonne is None or not logic.colonne_valide(colonne):
            cols = [c for c in range(9) if logic.colonne_valide(c)]
            colonne = random.choice(cols) if cols else None

        self.memoriser_coup(logic, joueur_ia, colonne)
        return colonne
    
    def analyser_position(self, logic, joueur_ia, tab_id=None):
        self.utiliser_bdd = False
        self.memoire_coups.clear()

        coup_urgent = self.trouver_coup_evident(logic, joueur_ia)
        if coup_urgent is not None:
            # On vérifie si ce coup urgent est une attaque ou une défense
            l = logic.placer_pion(coup_urgent, joueur_ia)
            est_victoire = logic.victoire(joueur_ia)
            logic.grille[l][coup_urgent] = 0
            
            if est_victoire:
                self.dernier_message = "Coup critique : Victoire immédiate !"
                score_artificiel = 10_000_000 if joueur_ia == JAUNE else -10_000_000
            else:
                self.dernier_message = "Coup critique : Blocage obligatoire !"
                score_artificiel = 0 
            
            # On retourne immédiatement ce coup vital sans perdre de temps
            return coup_urgent, score_artificiel

        colonne, score = minimax_iteratif(
            logic,
            est_maximisant=(joueur_ia == JAUNE),
            max_profondeur=self.max_profondeur,
            budget_secondes=self.budget_secondes,
            tab_id=tab_id
        )

        prof_atteinte = generateur_tournoi.LAST_COMPLETED_DEPTH
        infos_mat = self._extraire_infos_mat(score, prof_atteinte)
        print("DEBUG ANALYSE:", {
            "score": score,
            "prof_atteinte": prof_atteinte,
            "infos_mat": infos_mat,
            "joueur_ia": joueur_ia
        }, flush=True)

        if score is None:
            self.dernier_message = "Analyse terminee sans resultat exploitable."
        elif infos_mat is not None:
            self.dernier_message = (
                f"Solution trouvee : {infos_mat['gagnant']} gagne en "
                f"{infos_mat['demi_coups']} demi-coups "
                f"(~ {infos_mat['coups']} coup(s)). "
                f"Profondeur completee : {prof_atteinte}."
            )
        else:
            self.dernier_message = (
                f"Aucune victoire forcee prouvee jusqu'a la profondeur {prof_atteinte}."
            )

        return colonne, score

    def _extraire_infos_mat(self, score, profondeur_completee):
        if score is None or abs(score) < 9_000_000:
            return None

        reste = max(0, (abs(score) - 10_000_000) // 1000)
        demi_coups = max(1, profondeur_completee - reste)
        coups = (demi_coups + 1) // 2  # approximation en "coups"
        gagnant = "Jaune" if score > 0 else "Rouge"

        return {
            "gagnant": gagnant,
            "demi_coups": int(demi_coups),
            "coups": int(coups),
        }


_mon_ia_tournoi = IA_Tournoi()
