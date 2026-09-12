#!/usr/bin/env python3
"""Contrats des primitives partagées du banc standardisé (chantier EVA-01).

Lancer depuis la racine du dépôt :

    NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_primitives_banc.py" -v

Ce que ces tests verrouillent — et pourquoi :

- le BFS sans obstacle doit valoir EXACTEMENT la distance de Manhattan (invariant du
  dépôt, déjà posé pour la clinotaxie v32.0) ;
- un mur et de la lave doivent FORCER un détour — c'est le seul moyen de prouver que
  le BFS ne les traverse pas ;
- la convention du ratio est `trajet / plus_court_chemin`, donc >= 1 : un trajet de 12
  cases sur un optimum de 6 vaut 2.0, JAMAIS 0.5. C'est le test qui aurait attrapé la
  docstring inversée de `sonde_inertie_motrice.py` ;
- un optimum inconnu rend None, jamais 0.0 (0.0 serait un mensonge).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from naulthene.instruments.primitives_banc import (  # noqa: E402
    intervalle_wilson,
    longueur_normalisee,
    plus_court_chemin,
    taux_avec_ic,
)


class _Objet:
    def __init__(self, type_):
        self.type = type_


class _Grille:
    """Grille factice : '#' mur, 'L' lave, 'G' but, '.' libre. `get(x, y)` = (colonne, ligne)."""

    def __init__(self, plan):
        self.plan = plan
        self.width = len(plan[0])
        self.height = len(plan)

    def get(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return _Objet("wall")
        case = self.plan[y][x]
        return {"#": _Objet("wall"), "L": _Objet("lava"), "G": _Objet("goal")}.get(case)


class _Env:
    def __init__(self, plan, depart):
        self.unwrapped = type("U", (), {})()
        self.unwrapped.grid = _Grille(plan)
        self.unwrapped.agent_pos = depart


# Agent en (1,1), but en (3,3) : Manhattan = |3-1| + |3-1| = 4, aucun obstacle.
PLAN_LIBRE = ["#####", "#...#", "#...#", "#..G#", "#####"]
# Mur plein en colonne x=2 sur les lignes 1 et 2, passage en ligne 3 : détour = 6.
PLAN_MUR = ["#####", "#.#G#", "#.#.#", "#...#", "#####"]
# Même géométrie, mais le passage direct est de la LAVE : le détour doit être pris.
PLAN_LAVE = ["#####", "#.LG#", "#.#.#", "#...#", "#####"]
# Aucun but sur la carte.
PLAN_SANS_BUT = ["#####", "#...#", "#...#", "#...#", "#####"]


class TestPlusCourtChemin(unittest.TestCase):
    def test_sans_obstacle_vaut_exactement_manhattan(self):
        env = _Env(PLAN_LIBRE, (1, 1))
        self.assertEqual(plus_court_chemin(env), 4)

    def test_un_mur_force_un_detour_strictement_plus_long(self):
        env = _Env(PLAN_MUR, (1, 1))
        self.assertEqual(plus_court_chemin(env), 6)
        self.assertGreater(plus_court_chemin(env), 2)  # Manhattan vaudrait 2

    def test_la_lave_est_bloquee(self):
        env = _Env(PLAN_LAVE, (1, 1))
        # Si la lave était traversable, le résultat serait 2 (Manhattan).
        self.assertEqual(plus_court_chemin(env), 6)

    def test_sans_but_rend_none(self):
        env = _Env(PLAN_SANS_BUT, (1, 1))
        self.assertIsNone(plus_court_chemin(env))

    def test_depart_sur_le_but_vaut_zero(self):
        env = _Env(PLAN_LIBRE, (3, 3))
        self.assertEqual(plus_court_chemin(env), 0)


class TestLongueurNormalisee(unittest.TestCase):
    def test_convention_trajet_sur_optimum(self):
        """12 cases parcourues sur un optimum de 6 => 2.0x, jamais 0.5x.

        C'est LE verrou de convention : la convention inverse (o/t) rendrait 0.5.
        """
        self.assertEqual(longueur_normalisee(12, 6), 2.0)

    def test_optimum_inconnu_rend_none_jamais_zero(self):
        self.assertIsNone(longueur_normalisee(12, None))
        self.assertIsNone(longueur_normalisee(12, 0))

    def test_le_cas_d_egalite_vaut_un(self):
        """6/6 vaut exactement 1.0 — mais ce cas NE DISCRIMINE RIEN : toute implémentation de
        la forme t/o le rend, convention inverse comprise. Le verrou de convention est
        test_convention_trajet_sur_optimum ; ici on ancre la valeur NON ENTIÈRE."""
        self.assertEqual(longueur_normalisee(6, 6), 1.0)
        self.assertAlmostEqual(longueur_normalisee(11, 6), 1.8333333, places=6)


class TestIntervalleWilson(unittest.TestCase):
    def test_n_nul_rend_zero_zero(self):
        self.assertEqual(intervalle_wilson(0, 0), (0.0, 0.0))

    def test_valeurs_de_reference(self):
        """Ancrage NUMÉRIQUE. Sans lui, trois formules fausses franchissent la suite, dont
        l'approximation NORMALE que ce module rejette : elle rend un intervalle de largeur
        nulle à 0 %, là où la référence vaut 0.27754."""
        bas, haut = intervalle_wilson(9, 10)
        self.assertAlmostEqual(bas, 0.59584, places=5)
        self.assertAlmostEqual(haut, 0.98212, places=5)
        self.assertAlmostEqual(intervalle_wilson(0, 10)[1], 0.27754, places=5)
        # k = n : ici c+m vaut EXACTEMENT 1.0 (vérifié) — le min() est un filet flottant.
        self.assertEqual(intervalle_wilson(10, 10)[1], 1.0)
        self.assertGreaterEqual(intervalle_wilson(10, 10)[0], 0.0)

    def test_la_largeur_decroit_avec_n(self):
        largeur_10 = intervalle_wilson(9, 10)[1] - intervalle_wilson(9, 10)[0]
        largeur_100 = intervalle_wilson(90, 100)[1] - intervalle_wilson(90, 100)[0]
        self.assertLess(largeur_100, largeur_10)

    def test_taux_avec_ic_forme_unique(self):
        r = taux_avec_ic(9, 10)
        self.assertEqual(set(r), {"k", "n", "taux", "ic_bas", "ic_haut"})
        self.assertAlmostEqual(r["taux"], 0.9)
        self.assertEqual(r["k"], 9)
        self.assertEqual(r["n"], 10)
        self.assertAlmostEqual(r["ic_bas"], 0.59584, places=5)
        self.assertAlmostEqual(r["ic_haut"], 0.98212, places=5)


class TestMigrationDesSondes(unittest.TestCase):
    """Les deux sondes ne doivent plus porter leur PROPRE copie : sans ce test, une
    troisième duplication réapparaîtrait au prochain chantier (défaut MES-01/MES-02)."""

    def test_les_sondes_reutilisent_la_primitive_partagee(self):
        from naulthene.instruments import (
            primitives_banc,
            sonde_inertie_motrice,
            sonde_plancher_geometrique,
        )
        for sonde in (sonde_inertie_motrice, sonde_plancher_geometrique):
            self.assertIs(sonde.plus_court_chemin, primitives_banc.plus_court_chemin)
            self.assertIs(sonde.intervalle_wilson, primitives_banc.intervalle_wilson)

    def test_aucun_nom_global_non_resolu_dans_les_sondes(self):
        """La migration a retiré deux corps de fonction, donc potentiellement des imports.
        AUCUN test n'exécute ces sondes de bout en bout : un `NameError` y dormirait jusqu'à
        ce qu'un humain lance la sonde à la main.

        Contrôle par LOAD_GLOBAL, qui est EXACT : l'accès d'attribut (`os.path`) passe par
        LOAD_ATTR, donc `os` ne peut être confondu avec `path`. Les noms liés sont déduits du
        SOURCE (STORE_NAME au niveau module) et non de l'état du module importé — c'est ce qui
        rend le détecteur capable de voir un import retiré à tort.

        (Mesure du 12/09/2026 : la preuve portée par un smoke test manuel vivait dans
        `.superpowers/`, ignoré par Git — elle disparaissait à tout clone neuf.)
        """
        import builtins
        import dis
        from pathlib import Path

        from naulthene.instruments import sonde_inertie_motrice, sonde_plancher_geometrique

        dunder_module = {"__name__", "__file__", "__doc__", "__spec__", "__package__",
                         "__loader__", "__builtins__", "__annotations__"}

        def noms_non_resolus(source, fichier):
            code = compile(source, fichier, "exec")
            lies, charges, pile = set(), set(), [code]
            while pile:
                c = pile.pop()
                est_module = c is code
                for instr in dis.get_instructions(c):
                    if est_module and instr.opname == "STORE_NAME":
                        lies.add(instr.argval)
                    elif instr.opname == "LOAD_GLOBAL":
                        charges.add(instr.argval)
                pile += [k for k in c.co_consts if hasattr(k, "co_code")]
            return sorted(charges - lies - dunder_module - set(dir(builtins)))

        for sonde in (sonde_inertie_motrice, sonde_plancher_geometrique):
            with self.subTest(sonde=sonde.__name__):
                self.assertEqual(
                    noms_non_resolus(Path(sonde.__file__).read_text(encoding="utf-8"),
                                     sonde.__file__),
                    [], f"{sonde.__name__} référence un nom global non résolu")


if __name__ == "__main__":
    unittest.main()
