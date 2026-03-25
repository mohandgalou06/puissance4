import random

import generateur_tournoi
from constants import JAUNE, ROUGE
from database import Database
from generateur_tournoi import minimax_iteratif


class IA_Tournoi:
    def __init__(self):
        self.db = Database()
        self.budget_secondes = 14.0
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

    def jouer_coup(self, logic, coups_joues, joueur_ia):
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
                self.memoriser_coup(logic, joueur_ia, coup_bdd)
                self.dernier_message = "Base de donnees: coup theorique retrouve."
                return coup_bdd

        colonne, score = minimax_iteratif(
            logic,
            est_maximisant=(joueur_ia == JAUNE),
            max_profondeur=self.max_profondeur,
            budget_secondes=self.budget_secondes,
        )

        prof_atteinte = generateur_tournoi.LAST_COMPLETED_DEPTH

        if score is None:
            self.dernier_message = "Analyse terminee."
        elif score > 9_000_000:
            self.dernier_message = f"Mat trouve. Profondeur completee: {prof_atteinte}."
        elif score < -9_000_000:
            self.dernier_message = f"Defaite forcee detectee. Profondeur completee: {prof_atteinte}."
        else:
            self.dernier_message = f"Analyse terminee. Profondeur completee: {prof_atteinte}."

        if colonne is None or not logic.colonne_valide(colonne):
            cols = [c for c in range(9) if logic.colonne_valide(c)]
            colonne = random.choice(cols) if cols else None

        self.memoriser_coup(logic, joueur_ia, colonne)
        return colonne


_mon_ia_tournoi = IA_Tournoi()
