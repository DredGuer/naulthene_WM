#!/usr/bin/env python3
"""Contrats du lecteur de journal de cursus (registre MES-01, volet anti-copier-coller).

Les six scripts `depouiller*.py` embarquaient chacun leur copie de la même fonction
`lire()` et des mêmes expressions régulières. Ce module en fait une primitive unique,
testée une fois. Les extraits de log utilisés ici sont copiés d'un vrai bilan de nuit
(`brains/06092026_epoques_nuit/K8_NU_g11.log`).
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from naulthene.instruments.journal_cursus import (  # noqa: E402
    lire_journal,
    resumer_journal,
)

GABARIT = """🌙 Jour {j} [Primaire 1 (Contourner)]
  ├─ Arbitrage C1/C2: ✅ C1={c1} C2=0.000 (ratio 0.00x) | accord {acc}% | gain C1 ×{gain} | H jouée 1.854
  │                   🗳️ entropie des votes — C1 {hc1} | C2 0.606 (0 = voix FIGÉE)
  ├─ Chrono Victoire: 🏆 {vict} victoire(s) en {j} jour(s) | dernière il y a 0 j
  ├─ Cursus         : 🎓 Niveau {niv}/15 — maîtrise {mait}% (n=20) | 🤝 aide pleine
"""


def ecrire_journal(chemin, jours):
    with open(chemin, "w", encoding="utf-8") as fh:
        fh.write("🧠 démarrage du run, ligne hors journée\n")
        for d in jours:
            fh.write(GABARIT.format(**d))


def jour(j, niv=4, mait=10, gain=1.0, c1=1.5, hc1=0.5, acc=5.0, vict=100):
    return dict(j=j, niv=niv, mait=mait, gain=f"{gain:.2f}", c1=f"{c1:.3f}",
                hc1=f"{hc1:.3f}", acc=f"{acc:.1f}", vict=vict)


class SocleJournal(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.chemin = os.path.join(self._tmp.name, "run.log")


class TestLectureJournal(SocleJournal):
    def test_lit_une_ligne_par_nuit(self):
        ecrire_journal(self.chemin, [jour(1), jour(2), jour(3)])
        self.assertEqual([r["j"] for r in lire_journal(self.chemin)], [1, 2, 3])

    def test_extrait_les_champs_du_bilan(self):
        ecrire_journal(self.chemin, [jour(1, niv=4, mait=15, gain=1.0, c1=1.557,
                                          hc1=0.543, acc=5.0, vict=624)])
        r = lire_journal(self.chemin)[0]
        self.assertEqual(r["niv"], 4)
        self.assertEqual(r["mait"], 15)
        self.assertAlmostEqual(r["gain"], 1.0)
        self.assertAlmostEqual(r["c1"], 1.557)
        self.assertAlmostEqual(r["hc1"], 0.543)
        self.assertAlmostEqual(r["accord"], 5.0)
        self.assertEqual(r["vict"], 624)

    def test_ignore_une_nuit_sans_ligne_de_cursus(self):
        """Une nuit tronquée par un arrêt brutal n'est pas une observation."""
        ecrire_journal(self.chemin, [jour(1), jour(2)])
        with open(self.chemin, "a", encoding="utf-8") as fh:
            fh.write("🌙 Jour 3 [Primaire 1]\n  ├─ Arbitrage C1/C2: ✅ C1=1.000 C2=0.000\n")
        self.assertEqual([r["j"] for r in lire_journal(self.chemin)], [1, 2])

    def test_rend_une_liste_vide_sur_un_log_sans_journee(self):
        with open(self.chemin, "w", encoding="utf-8") as fh:
            fh.write("traceback: le run a planté au démarrage\n")
        self.assertEqual(lire_journal(self.chemin), [])


class TestResume(SocleJournal):
    def test_le_resume_expose_le_dernier_jour_atteint(self):
        ecrire_journal(self.chemin, [jour(j) for j in range(1, 51)])
        self.assertEqual(resumer_journal(lire_journal(self.chemin))["jours_final"], 50)

    def test_la_maitrise_est_la_mediane_de_la_fenetre_finale(self):
        jours = [jour(j, mait=0) for j in range(1, 41)] + \
                [jour(j, mait=20) for j in range(41, 51)]
        ecrire_journal(self.chemin, jours)
        resume = resumer_journal(lire_journal(self.chemin), fenetre=10)
        self.assertEqual(resume["mait"], 20)

    def test_le_niveau_est_celui_du_dernier_jour_jamais_une_mediane(self):
        jours = [jour(j, niv=3) for j in range(1, 10)] + [jour(10, niv=5)]
        ecrire_journal(self.chemin, jours)
        self.assertEqual(resumer_journal(lire_journal(self.chemin))["niv"], 5)

    def test_le_resume_refuse_un_journal_vide(self):
        self.assertIsNone(resumer_journal([]))


if __name__ == "__main__":
    unittest.main()
