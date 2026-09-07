#!/usr/bin/env python3
"""Contrats du dépouillement strict (registre MES-01).

Lancer depuis la racine du dépôt :

    PYTHONPATH=src venv/bin/python -m unittest discover -s tests -v

Ce que ces tests verrouillent — et pourquoi :

- une campagne incomplète, inachevée ou dont un garde-fou échoue ne doit produire
  AUCUN agrégat et doit rendre un code de sortie non nul (MES-01) ;
- une exclusion doit CRIER son motif, jamais disparaître silencieusement
  (règle issue de `INSTRUMENT_01092026_la_memoire_du_banc.md`) ;
- le seuil de significativité doit être DÉRIVÉ de `n` et de la famille de tests,
  jamais posé en dur (règle du dépôt : dériver, ne pas poser).
"""
import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from naulthene.instruments.depouillement import (  # noqa: E402
    CampagneInvalide,
    Depouillement,
    Manifeste,
    seuil_t,
)

GRAINES = [11, 22, 33]


def manifeste_dict(racine, mode="confirmatoire", **surcharges):
    base = {
        "campagne": "campagne_de_test",
        "mode": mode,
        "graines": list(GRAINES),
        "jours_requis": 1500,
        "alpha": 0.05,
        "comparaisons_prevues": 5,
        "bras": {
            "A": {"dossier": racine, "prefixe": "A"},
            "B": {"dossier": racine, "prefixe": "B"},
        },
        "gardes": [],
        "exclusions_autorisees": [],
    }
    base.update(surcharges)
    return base


class SocleCampagne(unittest.TestCase):
    """Fabrique une campagne jouet sur disque : deux bras × trois graines."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        # valeurs par run : (jours_final, maitrise, gain)
        self.runs = {}
        for i, g in enumerate(GRAINES):
            self.runs[f"A_g{g}"] = (1500, 20.0 + i, 1.0)
            self.runs[f"B_g{g}"] = (1500, 10.0 + i, 1.0)
        for cle in self.runs:
            open(os.path.join(self.racine, f"{cle.split('_g')[0]}_g{cle.split('_g')[1]}.log"), "w").close()

    def lecteur(self, chemin):
        cle = os.path.basename(chemin)[: -len(".log")]
        if cle not in self.runs:
            return None
        jours, mait, gain = self.runs[cle]
        return {"jours_final": jours, "mait": mait, "gain": gain}

    def depouillement(self, **surcharges):
        manifeste = Manifeste.depuis_dict(manifeste_dict(self.racine, **surcharges))
        return Depouillement(manifeste, racine=self.racine)

    def supprimer_run(self, cle):
        self.runs.pop(cle)
        os.remove(os.path.join(self.racine, f"{cle}.log"))


def _densite_student(t, df):
    return math.exp(
        math.lgamma((df + 1) / 2) - math.lgamma(df / 2)
        - 0.5 * math.log(df * math.pi)
        - ((df + 1) / 2) * math.log1p(t * t / df)
    )


def _masse_bilaterale_au_dela(t, df, pas=20000, borne=1000.0):
    """P(|T| > t) par Simpson — référence indépendante de la bêta incomplète."""
    h = (borne - t) / pas
    total = _densite_student(t, df) + _densite_student(borne, df)
    for i in range(1, pas):
        total += (4 if i % 2 else 2) * _densite_student(t + i * h, df)
    return 2 * total * h / 3


class TestSeuilDerive(unittest.TestCase):
    # Table de Student publiée, valeurs bilatérales : (df, alpha) -> t critique.
    TABLE = {
        (4, 0.05): 2.776, (9, 0.05): 2.262, (19, 0.05): 2.093, (29, 0.05): 2.045,
        (19, 0.01): 2.861, (9, 0.01): 3.250, (4, 0.01): 4.604,
    }

    def test_reproduit_la_table_de_student(self):
        for (df, alpha), attendu in self.TABLE.items():
            self.assertAlmostEqual(
                seuil_t(df + 1, comparaisons=1, alpha=alpha), attendu, places=3,
                msg=f"df={df} alpha={alpha}",
            )

    def test_le_seuil_rend_bien_la_masse_bilaterale_demandee(self):
        """Vérification indépendante : intégrer la densité au-delà du seuil rend alpha."""
        for n, comparaisons in ((20, 5), (12, 3), (40, 1)):
            t = seuil_t(n, comparaisons, alpha=0.05)
            masse = _masse_bilaterale_au_dela(t, n - 1)
            self.assertAlmostEqual(masse, 0.05 / comparaisons, places=5,
                                   msg=f"n={n} comparaisons={comparaisons}")

    def test_le_seuil_change_quand_n_change(self):
        """Retirer des observations doit relever le seuil, jamais le laisser figé."""
        self.assertGreater(seuil_t(16, 5), seuil_t(20, 5))

    def test_le_seuil_de_reference_du_depot_est_bien_derive(self):
        """2,86 n'était pas magique : c'est t(df=19, alpha=0,01 bilatéral)."""
        self.assertAlmostEqual(seuil_t(20, 5, alpha=0.05), 2.861, places=3)


class TestCouverture(SocleCampagne):
    def test_campagne_complete_est_valide(self):
        d = self.depouillement()
        d.collecter(self.lecteur)
        self.assertTrue(d.valide())

    def test_run_manquant_invalide_la_campagne(self):
        self.supprimer_run("A_g22")
        d = self.depouillement()
        d.collecter(self.lecteur)
        self.assertFalse(d.valide())

    def test_run_inacheve_invalide_la_campagne(self):
        self.runs["A_g22"] = (1200, 20.0, 1.0)
        d = self.depouillement()
        d.collecter(self.lecteur)
        self.assertFalse(d.valide())

    def test_l_exclusion_crie_son_motif(self):
        """Une graine écartée doit être nommée ET motivée dans le rapport."""
        self.runs["A_g33"] = (900, 20.0, 1.0)
        self.supprimer_run("B_g11")
        d = self.depouillement()
        d.collecter(self.lecteur)
        rapport = d.rapport()
        self.assertIn("A_g33", rapport)
        self.assertIn("900", rapport)
        self.assertIn("B_g11", rapport)
        self.assertIn("absent", rapport.lower())

    def test_exclusion_prevue_au_manifeste_ne_bloque_pas(self):
        """Une exclusion documentée d'avance est licite ; elle reste rapportée."""
        self.supprimer_run("B_g11")
        d = self.depouillement(
            exclusions_autorisees=[{"run": "B_g11", "motif": "crash disque documenté le 06/09"}]
        )
        d.collecter(self.lecteur)
        self.assertTrue(d.valide())
        self.assertIn("crash disque documenté", d.rapport())


class TestGardeFou(SocleCampagne):
    GARDE = [{
        "nom": "voix libre : gain_c1 ≡ 1",
        "variable": "gain",
        "bras": ["A", "B"],
        "cible": 1.0,
        "tolerance": 0.02,
    }]

    def test_garde_fou_satisfait_laisse_la_campagne_valide(self):
        d = self.depouillement(gardes=self.GARDE)
        d.collecter(self.lecteur)
        d.verifier_gardes()
        self.assertTrue(d.valide())

    def test_garde_fou_echoue_invalide_la_campagne(self):
        for g in GRAINES:
            jours, mait, _ = self.runs[f"A_g{g}"]
            self.runs[f"A_g{g}"] = (jours, mait, 0.25)
        d = self.depouillement(gardes=self.GARDE)
        d.collecter(self.lecteur)
        d.verifier_gardes()
        self.assertFalse(d.valide())


class TestCohorteExplicite(unittest.TestCase):
    """Certaines cohortes ne sont pas un produit bras × graines mais une LISTE.

    Cas réel : `02092026_rejeu_banc_corrige` (14 cerveaux du bras A + 6 du bras B,
    sur des sous-ensembles de graines différents) et les campagnes de banc, qui
    n'ont pas de critère de jours.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.attendus = ["A_g66", "A_g111", "B_g11"]
        for nom in self.attendus:
            open(os.path.join(self.racine, f"banc_{nom}.json"), "w").close()

    def depouillement(self, runs=None):
        manifeste = Manifeste.depuis_dict({
            "campagne": "banc_de_test",
            "mode": "confirmatoire",
            "runs": [{"nom": n, "fichier": f"banc_{n}.json"} for n in (runs or self.attendus)],
            "alpha": 0.05,
            "comparaisons_prevues": 3,
        })
        return Depouillement(manifeste, racine=self.racine)

    def test_la_cohorte_explicite_est_complete(self):
        d = self.depouillement()
        d.collecter(lambda chemin: {"succes": 10.0})
        self.assertTrue(d.valide())
        self.assertEqual(sorted(d.runs), sorted(self.attendus))

    def test_un_run_attendu_absent_invalide_la_campagne(self):
        d = self.depouillement(runs=self.attendus + ["B_g999"])
        d.collecter(lambda chemin: {"succes": 10.0})
        self.assertFalse(d.valide())
        self.assertIn("B_g999", d.rapport())

    def test_sans_critere_de_jours_le_lecteur_n_a_pas_a_en_fournir(self):
        """Un banc n'a pas de « jour 1500 » : l'absence de `jours_final` est licite."""
        d = self.depouillement()
        d.collecter(lambda chemin: {"succes": 10.0})
        self.assertNotIn("jours_final", d.rapport())
        self.assertTrue(d.valide())


class TestGardeFouMinimum(SocleCampagne):
    """Certains garde-fous sont des planchers, pas des cibles (ex. « gain ≫ 0,25 »)."""

    GARDE = [{
        "nom": "régime renormalisé : gain_c1 nettement au-dessus du plancher",
        "variable": "gain",
        "bras": ["A"],
        "minimum": 0.5,
    }]

    def test_plancher_respecte_laisse_la_campagne_valide(self):
        d = self.depouillement(gardes=self.GARDE)
        d.collecter(self.lecteur)
        d.verifier_gardes()
        self.assertTrue(d.valide())

    def test_plancher_franchi_par_le_bas_invalide_la_campagne(self):
        for g in GRAINES:
            jours, mait, _ = self.runs[f"A_g{g}"]
            self.runs[f"A_g{g}"] = (jours, mait, 0.25)
        d = self.depouillement(gardes=self.GARDE)
        d.collecter(self.lecteur)
        d.verifier_gardes()
        self.assertFalse(d.valide())
        self.assertIn("0.2500", d.rapport())


class TestExigenceAdHoc(SocleCampagne):
    """Une campagne peut exiger autre chose que ses logs (ex. les JSON de rollout)."""

    def test_une_exigence_non_satisfaite_invalide_la_campagne(self):
        d = self.depouillement()
        d.collecter(self.lecteur)
        d.exiger(False, "rollout BP_g44 : fichier absent")
        self.assertFalse(d.valide())
        self.assertIn("rollout BP_g44", d.rapport())

    def test_une_exigence_satisfaite_ne_change_rien(self):
        d = self.depouillement()
        d.collecter(self.lecteur)
        d.exiger(True, "rollout complet")
        self.assertTrue(d.valide())


class TestPublication(SocleCampagne):
    def test_agregat_ecrit_sur_campagne_valide(self):
        d = self.depouillement()
        d.collecter(self.lecteur)
        chemin = os.path.join(self.racine, "agregat.json")
        self.assertTrue(d.publier(chemin))
        with open(chemin, encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh)["runs"]), 6)

    def test_aucun_agregat_ecrit_sur_campagne_invalide(self):
        self.supprimer_run("A_g22")
        d = self.depouillement()
        d.collecter(self.lecteur)
        chemin = os.path.join(self.racine, "agregat.json")
        self.assertFalse(d.publier(chemin))
        self.assertFalse(os.path.exists(chemin))

    def test_code_de_sortie_non_nul_sur_campagne_invalide(self):
        self.supprimer_run("A_g22")
        d = self.depouillement()
        d.collecter(self.lecteur)
        self.assertNotEqual(d.code_sortie(), 0)

    def test_code_de_sortie_nul_sur_campagne_valide(self):
        d = self.depouillement()
        d.collecter(self.lecteur)
        self.assertEqual(d.code_sortie(), 0)


class TestApparie(SocleCampagne):
    def test_refuse_de_calculer_sur_une_campagne_invalide(self):
        self.supprimer_run("A_g22")
        d = self.depouillement()
        d.collecter(self.lecteur)
        with self.assertRaises(CampagneInvalide):
            d.apparie("A", "B", "mait", "A - B")

    def test_calcule_le_delta_apparie_sur_la_cohorte_complete(self):
        d = self.depouillement()
        d.collecter(self.lecteur)
        res = d.apparie("A", "B", "mait", "A - B")
        self.assertEqual(res.n, 3)
        self.assertAlmostEqual(res.delta, 10.0)
        self.assertEqual(res.favorables, 3)

    def test_le_seuil_du_resultat_est_derive_de_n_et_de_la_famille(self):
        d = self.depouillement()
        d.collecter(self.lecteur)
        res = d.apparie("A", "B", "mait", "A - B")
        self.assertAlmostEqual(res.seuil, seuil_t(3, 5, alpha=0.05), places=9)


class TestRetraitDesExtremes(SocleCampagne):
    """La vérification « sans les 4 extrêmes » du dépôt, avec un seuil recalculé."""

    DELTAS = [1.0, 1.2, 0.8, 1.1, 0.9, 1.3, 0.7, 1.05, 0.95, 1.15,
              40.0, -35.0, 30.0, -28.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

    def test_le_retrait_ecarte_les_quatre_plus_grands_ecarts(self):
        d = self.depouillement()
        res = d.resultat_de(self.DELTAS, "essai", retirer_extremes=4)
        self.assertEqual(res.n, 20)
        self.assertEqual(res.reduit.n, 16)
        self.assertAlmostEqual(res.reduit.delta, 1.009375, places=6)

    def test_le_seuil_du_resultat_reduit_est_recalcule_a_n_reduit(self):
        """Le défaut central de MES-01 : le seuil restait figé à 2,86 après retrait."""
        d = self.depouillement()
        res = d.resultat_de(self.DELTAS, "essai", retirer_extremes=4)
        self.assertAlmostEqual(res.reduit.seuil, seuil_t(16, 5, alpha=0.05), places=9)
        self.assertNotAlmostEqual(res.reduit.seuil, res.seuil, places=3)

    def test_le_retrait_est_refuse_quand_il_reste_moins_de_trois_observations(self):
        d = self.depouillement()
        res = d.resultat_de([1.0, 2.0, 3.0, 4.0, 5.0], "essai", retirer_extremes=4)
        self.assertIsNone(res.reduit)

    def test_sans_retrait_demande_il_n_y_a_pas_de_resultat_reduit(self):
        d = self.depouillement()
        res = d.resultat_de(self.DELTAS, "essai")
        self.assertIsNone(res.reduit)


class TestModeExploratoire(SocleCampagne):
    def test_une_cohorte_incomplete_reste_calculable(self):
        self.supprimer_run("A_g22")
        d = self.depouillement(mode="exploratoire")
        d.collecter(self.lecteur)
        res = d.apparie("A", "B", "mait", "A - B")
        self.assertEqual(res.n, 2)

    def test_le_verdict_est_estampille_sans_valeur_confirmatoire(self):
        d = self.depouillement(mode="exploratoire")
        d.collecter(self.lecteur)
        res = d.apparie("A", "B", "mait", "A - B")
        self.assertIn("EXPLORATOIRE", res.ligne())
        self.assertNotIn("SIG", res.ligne())

    def test_n_ecrit_jamais_le_fichier_confirmatoire(self):
        d = self.depouillement(mode="exploratoire")
        d.collecter(self.lecteur)
        chemin = os.path.join(self.racine, "agregat.json")
        d.publier(chemin)
        self.assertFalse(os.path.exists(chemin))
        self.assertTrue(os.path.exists(os.path.join(self.racine, "agregat_exploratoire.json")))


if __name__ == "__main__":
    unittest.main()
