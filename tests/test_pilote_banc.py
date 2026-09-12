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
  ASYMÉTRIQUE vers le haut, et retrouve les valeurs de table du chi-deux (df = 3) ;
- la **variance d'échantillonnage** `v` du taux d'un cerveau et sa **dé-convolution**
  `σ̂ = sqrt(max(0, s² − v))` sont verrouillées : c'est la correction du tour 1, sans
  laquelle la dispersion publiée est celle du PILOTE et non celle des CERVEAUX ;
- le triplet MESURÉ du premier pilote est GELÉ (`deriver_n(0,256250, 0,07180…) == 333`), et
  la tolérance de bord est plafonnée : sans ces deux verrous, porter la tolérance à 1e-3
  laisserait la suite verte tout en faisant passer ce `n` gelé à 332 en silence.

⚠️ Rien de tout ceci ne mesure quoi que ce soit : les seules mesures sont celles du
carnet `docs/recherche/campagnes/` et de `brains/EVA01_pilote_*/pilote.json`.
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from naulthene.instruments.pilote_banc import (  # noqa: E402
    TOLERANCE_RELATIVE_CONTRAINTE,
    deriver_n,
    dispersion_inter_cerveaux,
    intervalle_confiance_sd,
    variance_echantillonnage,
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

    def test_le_triplet_mesure_du_premier_pilote_est_gele(self):
        """🔒 VERROU DU TOUR 1. Ces trois nombres sont les chiffres PUBLIÉS du premier
        pilote (`brains/EVA01_pilote_13092026/pilote.json`) : `p̄ = 0,256250`,
        `s = 0,07180703308172535`, `facteur = 3` ⇒ `n = 333`.

        Sans ce test, porter `TOLERANCE_RELATIVE_CONTRAINTE` à 1e-3 laisserait tous les
        autres tests VERTS tout en faisant passer ce `n` gelé de 333 à **332** — un chiffre
        publié qui change sans qu'aucun test ne bronche. C'est exactement le « chiffre non
        reproductible » que la Règle de Trace interdit."""
        self.assertEqual(deriver_n(0.256250, 0.07180703308172535, facteur=3.0), 333)

    def test_la_tolerance_de_bord_reste_plafonnee(self):
        """🔒 La tolérance ne sert qu'à trancher l'égalité EXACTE en virgule flottante
        (l'écart mesuré vaut 6,9e-18) : elle doit rester des ordres de grandeur en dessous
        de tout effet mesurable. Au-delà de 1e-12, elle peut faire basculer un `n` publié
        (voir le test précédent) : on refuse de la voir grandir en silence."""
        self.assertGreater(TOLERANCE_RELATIVE_CONTRAINTE, 0.0)
        self.assertLessEqual(TOLERANCE_RELATIVE_CONTRAINTE, 1e-12)

    def test_une_contrainte_alteree_crie_au_lieu_de_boucler(self):
        """🔒 La correction de `deriver_n` est BORNÉE : si l'estimation analytique part
        d'un `n` trop petit, la fonction doit LEVER, pas corriger indéfiniment.

        Le cas est fabriqué en donnant au module un `math` dont le `floor` rend toujours 1
        — l'estimation analytique devient absurde, alors que la vérification, elle, reste
        juste. ⚠️ On remplace l'attribut `math` DU MODULE, jamais la fonction du module
        `math` global : aucune autre suite de tests ne peut en hériter, et le `finally`
        remet l'original en place."""
        import types
        import naulthene.instruments.pilote_banc as module
        ancien = module.math
        try:
            module.math = types.SimpleNamespace(floor=lambda _: 1, sqrt=ancien.sqrt)
            with self.assertRaises(RuntimeError) as contexte:
                deriver_n(0.5, 0.15, facteur=3.0)
            self.assertIn("corrections", str(contexte.exception))
        finally:
            module.math = ancien


class TestVarianceDEchantillonnage(unittest.TestCase):
    """`v` : la part de la dispersion observée qui vient du PILOTE, pas des cerveaux."""

    def test_une_seule_carte_rend_la_variance_binomiale(self):
        """Sur une carte, `v = p(1−p)/n` — la définition de l'erreur-type d'un taux."""
        self.assertAlmostEqual(variance_echantillonnage([0.5], [100]), 0.25 / 100,
                               places=15)

    def test_deux_cartes_de_meme_taux_rendent_le_meme_resultat_qu_une_seule(self):
        """Si les deux cartes ont le MÊME taux, le poolé se comporte comme un seul binôme
        de `2n` épisodes : c'est le contrôle qui montre que la formule par carte est bien
        une généralisation, et non une convention arbitraire."""
        self.assertAlmostEqual(variance_echantillonnage([0.5, 0.5], [200, 200]),
                               0.25 / 400, places=15)

    def test_deux_cartes_de_taux_differents_ne_sont_pas_un_seul_binome(self):
        """⚠️ Le cœur de la correction : avec `p3 = 0,35` et `p4 = 0,1625`, la formule
        « un seul binôme sur 400 épisodes » (`p̄(1−p̄)/400`) donne 0,000476, la formule
        exacte 0,000454. Confondre les deux sous-estime `v`, donc SUR-estime σ̂, donc
        sous-dimensionne `n` — exactement le travers que le tour 1 corrige."""
        exacte = variance_echantillonnage([0.35, 0.1625], [200, 200])
        p_barre = (0.35 + 0.1625) / 2
        self.assertAlmostEqual(exacte, (0.35 * 0.65 + 0.1625 * 0.8375) / 800, places=15)
        self.assertNotAlmostEqual(exacte, p_barre * (1 - p_barre) / 400, places=6)

    def test_les_entrees_incoherentes_sont_refusees(self):
        for taux, effectifs in (([0.5], [10, 10]), ([0.5], [0]), ([1.5], [10]), ([], [])):
            with self.assertRaises(ValueError):
                variance_echantillonnage(taux, effectifs)


class TestDeconvolution(unittest.TestCase):
    """σ̂ : l'estimateur NON biaisé de la dispersion réelle entre cerveaux."""

    def test_sans_v_la_deconvolution_n_est_pas_calculee(self):
        """La dé-convolution ne se déclenche que si le pilote a fourni son bruit : on ne
        remplace jamais la valeur observée par une valeur par défaut."""
        dispersion = dispersion_inter_cerveaux([0.1, 0.3])
        self.assertNotIn("sd_inter_deconvoluee", dispersion)
        self.assertEqual(dispersion["variance_echantillonnage_par_cerveau"], 0.0)

    def test_sigma_est_la_racine_de_la_variance_observee_moins_v(self):
        """`[0,10 ; 0,30]` donne `s² = 0,02` ; avec `v = 0,01`, σ̂ = sqrt(0,01) = 0,1."""
        dispersion = dispersion_inter_cerveaux([0.1, 0.3],
                                               variance_echantillonnage_par_cerveau=0.01)
        self.assertAlmostEqual(dispersion["sd_inter"], math.sqrt(0.02), places=12)
        self.assertAlmostEqual(dispersion["sd_inter_deconvoluee"], 0.1, places=12)
        self.assertAlmostEqual(dispersion["part_variance_echantillonnage"], 0.5,
                               places=12)

    def test_sigma_est_toujours_inferieur_ou_egal_a_s(self):
        """Conséquence directe : le `n` dérivé de σ̂ est TOUJOURS >= celui dérivé de `s`.
        Le `333` du premier pilote est donc bien une BORNE BASSE, jamais une estimation."""
        dispersion = dispersion_inter_cerveaux([0.05, 0.15, 0.25, 0.35],
                                               variance_echantillonnage_par_cerveau=0.005)
        self.assertLess(dispersion["sd_inter_deconvoluee"], dispersion["sd_inter"])

    def test_un_bruit_superieur_a_la_variance_observee_rend_sigma_nul(self):
        """Si `v >= s²`, la dispersion réelle n'est PAS distinguable du bruit du pilote :
        σ̂ = 0 (jamais un négatif, qui n'a pas de sens), et l'IC touche 0 — ce qui interdit
        de dériver un `n` fini, et c'est un RÉSULTAT à publier comme tel."""
        dispersion = dispersion_inter_cerveaux([0.1, 0.3],
                                               variance_echantillonnage_par_cerveau=0.05)
        self.assertEqual(dispersion["sd_inter_deconvoluee"], 0.0)
        self.assertEqual(dispersion["ic_sd_deconvoluee"][0], 0.0)
        self.assertTrue(dispersion["ic_sd_deconvoluee_touche_zero"])

    def test_l_ic_de_sigma_encadre_sigma(self):
        dispersion = dispersion_inter_cerveaux([0.05, 0.15, 0.25, 0.35],
                                               variance_echantillonnage_par_cerveau=0.002)
        bas, haut = dispersion["ic_sd_deconvoluee"]
        self.assertLess(bas, dispersion["sd_inter_deconvoluee"])
        self.assertGreater(haut, dispersion["sd_inter_deconvoluee"])
        self.assertFalse(dispersion["ic_sd_deconvoluee_touche_zero"])

    def test_une_variance_negative_est_refusee(self):
        with self.assertRaises(ValueError):
            dispersion_inter_cerveaux([0.1, 0.3],
                                      variance_echantillonnage_par_cerveau=-0.01)


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
        distingue un test d'un miroir. ⚠️ La valeur 0,35185 est `χ²(0,05 ; 3)` — et NON
        `χ²(0,95 ; 3)`, qui vaut 7,814728. Elle a été écrite ici par erreur au premier jet,
        et c'est l'implémentation, comparée à la table, qui l'a montrée : s'y tromper
        rétrécirait la borne haute de 0,559 à 0,438, c'est-à-dire ferait passer la
        dispersion d'un pilote à 4 cerveaux pour mieux connue qu'elle ne l'est."""
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
