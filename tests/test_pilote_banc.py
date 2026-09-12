#!/usr/bin/env python3
"""Contrats du pilote EVA-01 (tâche 7) — la règle qui DÉRIVE `n`.

    NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_pilote_banc.py" -v

Ce que ces tests verrouillent, et pourquoi chacun :

- la règle est **pure** : elle se teste SANS lancer d'évaluation (aucun cerveau, aucun
  `.brain`, aucun `noyau`) — c'est ce qui la rend contestable et rejouable ;
- elle rend le **plus petit** `n` qui satisfait `sqrt(p̄(1−p̄)/n) ≤ sd/3`, pas un `n`
  confortable : le critère `n − 1` ÉCHOUE, sinon la fonction pourrait rendre n'importe
  quoi au-dessus du seuil et personne ne le verrait ;
- une dispersion **plus grande** exige **moins** d'épisodes (sens de la règle : c'est le
  bruit de mesure qu'on domine, pas l'inverse) ;
- une dispersion **nulle** est **refusée** : SD = 0 signifie « le pilote n'a rien mesuré »,
  et rendre `n = 1` ou `n = 10000` serait un chiffre inventé ;
- un `p̄` hors de `]0, 1[` est refusé (taux saturé : la règle binomiale n'y a plus de sens) ;
- l'**intervalle de confiance de la SD estimée** encadre la valeur ponctuelle, est
  ASYMÉTRIQUE vers le haut, et retrouve les valeurs de table du chi-deux (df = 3).

⚠️ Rien de tout ceci ne mesure quoi que ce soit : les seules mesures sont celles du
carnet `docs/recherche/campagnes/` et de `brains/EVA01_pilote_*/pilote.json`.
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from naulthene.instruments.pilote_banc import (  # noqa: E402
    deriver_n,
    dispersion_inter_cerveaux,
    intervalle_confiance_sd,
)


class TestDerivationDeN(unittest.TestCase):
    """La règle doit être testable SANS lancer d'évaluation : elle est pure."""

    def test_n_est_le_plus_petit_qui_satisfait_la_contrainte(self):
        n = deriver_n(p_barre=0.5, sd_inter=0.15, facteur=3.0)
        # SE = sqrt(0.25/n) <= 0.05  =>  n >= 100
        self.assertEqual(n, 100)
        # ⚠️ ÉCART ASSUMÉ, MESURÉ, PAR RAPPORT AU BRIEF. Sa comparaison exacte
        # `(0.25/100)**0.5 <= 0.15/3.0` est FAUSSE en virgule flottante IEEE : le membre
        # de gauche vaut 0,050000000000000003 et celui de droite 0,049999999999999996 —
        # écart de 6,9e-18, dû à la représentation binaire de « 0,15 » et non à un
        # désaccord mathématique (au sens des DÉCIMALES ÉCRITES, la contrainte est tenue
        # exactement). On garde l'assertion du brief, rendue robuste par la MÊME tolérance
        # relative que la règle (1e-12), et le test suivant vérifie que le `n` rendu est
        # bien le PLUS PETIT : `n − 1` échoue, lui, largement (0,05025 > 0,05).
        self.assertLessEqual((0.25 / n) ** 0.5, (0.15 / 3.0) * (1 + 1e-12))

    def test_une_dispersion_plus_grande_exige_moins_d_episodes(self):
        self.assertLess(deriver_n(0.5, 0.3), deriver_n(0.5, 0.1))

    def test_une_dispersion_nulle_est_refusee(self):
        """SD = 0 signifie que le pilote n'a rien mesuré : on refuse plutôt que de
        rendre un n arbitraire."""
        with self.assertRaises(ValueError):
            deriver_n(0.5, 0.0)

    def test_le_n_rendu_est_vraiment_le_plus_petit(self):
        """`n − 1` DOIT échouer : sans ce verrou, rendre `n` confortablement grand
        passerait le test précédent sans rien garantir."""
        n = deriver_n(0.5, 0.15, facteur=3.0)
        self.assertEqual(n, 100)
        self.assertGreater((0.25 / (n - 1)) ** 0.5, 0.15 / 3.0)

    def test_le_facteur_est_un_parametre_et_non_une_constante_cachee(self):
        """`facteur=3` est le seul paramètre posé de la règle (spec §8bis) : le doubler
        doit quadrupler `n`, sinon il n'est pas le levier annoncé."""
        self.assertEqual(deriver_n(0.5, 0.15, facteur=6.0), 400)

    def test_un_taux_sature_est_refuse(self):
        """`p̄ = 0` ou `1` : la variance binomiale est nulle, la règle n'a plus de sens."""
        for p_sature in (0.0, 1.0, -0.2, 1.3):
            with self.assertRaises(ValueError):
                deriver_n(p_sature, 0.15)

    def test_une_dispersion_negative_ou_un_facteur_nul_est_refuse(self):
        for sd, facteur in ((-0.1, 3.0), (0.15, 0.0), (0.15, -1.0)):
            with self.assertRaises(ValueError):
                deriver_n(0.5, sd, facteur)

    def test_le_plus_petit_n_possible_reste_un(self):
        """Une dispersion énorme devant la variance binomiale ne doit pas rendre 0
        épisode : le plancher est 1."""
        self.assertEqual(deriver_n(0.5, 5.0), 1)


class TestDispersionInterCerveaux(unittest.TestCase):
    """La SD qui entre dans la règle est celle des CERVEAUX, jamais celle des épisodes."""

    def test_la_sd_est_celle_des_cerveaux(self):
        dispersion = dispersion_inter_cerveaux([0.1, 0.3])
        self.assertEqual(dispersion["n_cerveaux"], 2)
        self.assertAlmostEqual(dispersion["sd_inter"], math.sqrt(0.02), places=12)

    def test_une_seule_valeur_ne_mesure_aucune_dispersion(self):
        with self.assertRaises(ValueError):
            dispersion_inter_cerveaux([0.2])

    def test_l_ic_de_la_sd_encadre_la_valeur_ponctuelle(self):
        dispersion = dispersion_inter_cerveaux([0.05, 0.15, 0.25, 0.35])
        bas, haut = dispersion["ic_sd"]
        self.assertLess(bas, dispersion["sd_inter"])
        self.assertGreater(haut, dispersion["sd_inter"])
        self.assertGreater(bas, 0.0)


class TestIntervalleDeConfianceDeLaSD(unittest.TestCase):
    """La pièce que le carnet doit publier : une SD de pilote est INSTABLE."""

    def test_les_bornes_retrouvent_la_table_du_chi_deux(self):
        """Pour `s = 0,15` sur 4 cerveaux (df = 3), la table donne
        `χ²(0,975 ; 3) = 9,34840` et `χ²(0,025 ; 3) = 0,215795` :
        bas = sqrt(3 × 0,0225 / 9,34840) = 0,08497 et
        haut = sqrt(3 × 0,0225 / 0,215795) = 0,55928.

        Ces deux nombres viennent de la TABLE, jamais de l'implémentation : c'est ce qui
        distingue un test d'un miroir. ⚠️ La valeur 0,35185, souvent citée pour df = 3,
        est `χ²(0,95 ; 3)` et NON `χ²(0,025 ; 3)` — elle a été écrite ici par erreur au
        premier jet, et c'est l'implémentation, comparée à la table, qui l'a montrée :
        s'y tromper rétrécirait la borne haute de 0,559 à 0,438, c'est-à-dire ferait
        passer la dispersion d'un pilote à 4 cerveaux pour mieux connue qu'elle ne l'est."""
        bas, haut = intervalle_confiance_sd(sd=0.15, n=4)
        self.assertAlmostEqual(bas, 0.08497, places=4)
        self.assertAlmostEqual(haut, 0.55928, places=4)

    def test_l_intervalle_est_asymetrique_vers_le_haut(self):
        """Le chi-deux n'est pas symétrique : à petit `n`, la borne haute s'envole.
        Un intervalle symétrique serait un mensonge sur l'instabilité."""
        sd = 0.15
        bas, haut = intervalle_confiance_sd(sd=sd, n=4)
        self.assertGreater(haut - sd, sd - bas)

    def test_une_sd_nulle_a_un_intervalle_nul(self):
        self.assertEqual(intervalle_confiance_sd(sd=0.0, n=4), (0.0, 0.0))

    def test_l_intervalle_se_resserre_quand_n_grandit(self):
        largeur_petit = intervalle_confiance_sd(sd=0.15, n=4)
        largeur_grand = intervalle_confiance_sd(sd=0.15, n=40)
        self.assertGreater(largeur_petit[1] - largeur_petit[0],
                           largeur_grand[1] - largeur_grand[0])

    def test_un_effectif_insuffisant_est_refuse(self):
        with self.assertRaises(ValueError):
            intervalle_confiance_sd(sd=0.15, n=1)


if __name__ == "__main__":
    unittest.main()
