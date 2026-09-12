# EVA-01 — Banc final standardisé — plan d'implémentation

> **Pour les agents d'exécution :** skill obligatoire : utiliser `subagent-driven-development`
> (recommandé) ou `executing-plans` pour exécuter ce plan tâche par tâche. Les étapes emploient des
> cases `- [ ]`.

**Objectif :** livrer un banc d'évaluation reproductible, à cartes figées, dont le nombre d'épisodes
est **dérivé d'une mesure** et non posé — sans jamais modifier `noyau.py`.

**Architecture :** quatre artefacts neufs (`primitives_banc.py`, `banc_final.py`,
`PROTOCOLE_BANC_FINAL.md`, `test_primitives_banc.py`), deux sondes migrées vers les primitives
partagées, un outil archivé (`evaluer_cerveau.py`). Le banc réutilise **telles quelles** les
primitives statistiques de `depouillement.py` (MES-01) : refus de cohorte incomplète, test apparié,
seuil Bonferroni.

**Stack technique :** Python 3.12 (`venv/bin/python3`), `unittest`, `torch` (`NAULTHENE_DEVICE=cpu`),
`gymnasium` + `minigrid` (déjà verrouillés dans `constraints-lock.txt`). Aucune dépendance nouvelle.

**Spec :** [`CHANTIER_EVA-01_banc_final_standardise.md`](CHANTIER_EVA-01_banc_final_standardise.md)

## Contraintes globales

- **`noyau.py` n'est JAMAIS modifié** (spec D1, ARC-01). Aucune tâche ne touche ce fichier.
- Import inter-modules : **chemins absolus de package uniquement** (`from naulthene.… import …`).
  Jamais d'import à plat. Lancement depuis la racine du dépôt, toujours `-m`.
- `primitives_banc.py` est en **pur stdlib** (`collections`, `math`) et n'importe **jamais**
  `noyau` — même règle que `bus_sensoriel.py`.
- Toute commande de test s'exécute avec `NAULTHENE_DEVICE=cpu` :
  `NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "<motif>" -v`
- **Rien n'est écrit sans mesure** : les tâches 7 et 9 produisent un **carnet**
  (`docs/recherche/`) **et** un **agrégat JSON**, pas seulement une sortie console.
- **Aucun `n` posé** : le paramètre `--episodes` vient exclusivement du pilote (tâche 7).
- `.brain` est **toujours** ouvert en lecture seule ; le banc n'importe jamais la sauvegarde de
  `PersistanceAnatomique`.
- Messages de commit : `<type>(<portée>): <description>` en français, sans accent dans le titre.

### Interfaces gelées (à respecter à l'identique dans toutes les tâches)

`src/naulthene/instruments/primitives_banc.py`

```python
def plus_court_chemin(env) -> int | None
def intervalle_wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]
def longueur_normalisee(trajet: int, optimal: int | None) -> float | None
def taux_avec_ic(k: int, n: int) -> dict
```

`src/naulthene/instruments/banc_final.py`

```python
CARTES_GELEES: tuple[int, int] = (3, 4)
GRAINE_EVAL_BASE_GELEE: int = 10000
GRAINE_EVAL_BASE_MINIMUM: int = 1000
DOSSIER_SORTIE_DEFAUT: str = "docs/recherche/evals/banc_final"
FAMILLE_METRIQUES: tuple[str, ...]          # 3 noms, pour comparaisons_prevues

class NomAmbigue(RuntimeError): ...
class GraineEvalRefusee(RuntimeError): ...
class EpisodesNonDerive(RuntimeError): ...
class CarteInvalide(RuntimeError): ...
class BrasIntrouvable(RuntimeError): ...
class InstrumentIndisponible(RuntimeError): ...

def verifier_graine_eval_base(valeur: int) -> int
def exiger_episodes(valeur) -> int
def lire_graines_du_manifeste(cohorte: str) -> list[int]
def lister_cerveaux(dossier_bras: str, prefixe: str, graines: Sequence[int]) -> dict[int, str]
def resoudre_cohorte(cohorte: str, bras: Sequence[str], graines: Sequence[int]) -> dict[str, dict[int, str]]
def evaluer_cerveau_sur_carte(etat, index_carte: int, graines: Sequence[int], max_ticks: int = 0) -> dict
def construire_depouillement(cohorte: str, bras: Sequence[str], graines: Sequence[int],
                             metriques_par_chemin: dict) -> Depouillement
def executer_banc(cohorte: str, bras: Sequence[str], cartes: Sequence[int], graines: Sequence[int],
                  episodes: int, graine_eval_base: int, dossier_sortie: str, max_ticks: int = 0,
                  cohorte_resolue: dict | None = None) -> dict
def main() -> int
```

API réutilisée de `depouillement.py` (ne pas recoder) :
`Manifeste(campagne, mode, graines, bras, alpha, comparaisons_prevues)`,
`Depouillement(manifeste, racine)`, `.collecter(lecteur)`, `.apparie(bras_a, bras_b, variable, label,
retirer_extremes=0) -> Resultat`, `.rapport() -> str`, `.publier(chemin) -> bool`,
`.code_sortie() -> int`, `Resultat.label/.delta/.t/.n/.favorables/.seuil/.significatif/.ligne()`.
Clés de run attendues par `deltas()` : **`f"{bras}_g{graine}"`**.

`src/naulthene/instruments/pilote_banc.py`

```python
def deriver_n(p_barre: float, sd_inter: float, facteur: float = 3.0) -> int
def mesurer_pilote(cohorte, bras, cartes, graines_pilote, episodes, graine_eval_base,
                   dossier_sortie) -> dict
```

---

### Tâche 1 — Primitives partagées

**Fichiers :**
- Créer : `src/naulthene/instruments/primitives_banc.py`
- Tester : `tests/test_primitives_banc.py`

**Action :** créer le foyer unique des quatre primitives, avec la convention du ratio **nommée** et la
docstring de `plus_court_chemin` **corrigée** (elle est aujourd'hui fausse dans
`sonde_inertie_motrice.py` : une borne inférieure du trajet **surestime** la directivité).

**Dépendances et interfaces :**
- Consomme : rien (pur stdlib).
- Produit : les quatre signatures gelées ci-dessus.

**Critères de succès :**
- `NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_primitives_banc.py" -v` → **12 tests OK**.
- Aucun import de `naulthene.cerveau` dans le module.

- [ ] **Étape 1 : écrire les tests qui échouent**

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Étape 2 : exécuter les tests avec `bash`**

Commande :
```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_primitives_banc.py" -v
```
Attendu : **échec** sur `ModuleNotFoundError: No module named 'naulthene.instruments.primitives_banc'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

Créer `src/naulthene/instruments/primitives_banc.py` :

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Primitives partagées du banc standardisé (chantier EVA-01).

Foyer UNIQUE de quatre primitives auparavant dupliquées ou absentes. Pur stdlib :
ce module n'importe JAMAIS `noyau` (même règle d'absence de cycle que
`bus_sensoriel.py`).

Historique : `plus_court_chemin` et `intervalle_wilson` existaient en DEUX copies
FONCTIONNELLEMENT identiques (`sonde_inertie_motrice.py`, `sonde_plancher_geometrique.py` —
seuls les noms de variables et l'accès au type d'objet différaient), sans
aucun test, et les deux copies affirmaient des conclusions OPPOSÉES de la même
prémisse. Voir CHANTIER_EVA-01 §3.4.
"""
from __future__ import annotations

import collections
import math


def plus_court_chemin(env) -> int | None:
    """Nombre de CASES du trajet minimal entre l'agent et le but, obstacles contournés.

    ⚠️ Compte les cases, pas les actions : une rotation coûte un tick de plus dans le jeu
    réel (et `N_ACTIONS` vaut 7). C'est donc une borne INFÉRIEURE du nombre de pas.

    Conséquence de lecture, et c'est le point qui avait été écrit à l'envers dans
    `sonde_inertie_motrice.py` : le rapport `trajet / plus_court_chemin` ne peut que
    SURESTIMER la directivité, jamais la sous-estimer.
    """
    u = env.unwrapped
    grille = u.grid
    depart = tuple(u.agent_pos)
    but = None
    for x in range(grille.width):
        for y in range(grille.height):
            o = grille.get(x, y)
            if o is not None and getattr(o, "type", None) == "goal":
                but = (x, y)
    if but is None:
        return None
    vus = {depart}
    file = collections.deque([(depart, 0)])
    while file:
        (x, y), d = file.popleft()
        if (x, y) == but:
            return d
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < grille.width and 0 <= ny < grille.height):
                continue
            if (nx, ny) in vus:
                continue
            o = grille.get(nx, ny)
            if o is not None and getattr(o, "type", None) in ("wall", "lava"):
                continue
            vus.add((nx, ny))
            file.append(((nx, ny), d + 1))
    return None


def intervalle_wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalle de confiance de Wilson pour `k` succès sur `n` essais.

    Wilson plutôt que l'intervalle normal : il reste valide aux taux extrêmes (0 %,
    100 %) là où l'approximation normale sort de [0, 1].
    """
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - m), min(1.0, c + m))


def longueur_normalisee(trajet: int, optimal: int | None) -> float | None:
    """`trajet / plus_court_chemin` — la convention est NOMMÉE ici, pas implicite.

    ⚠️ Cette fonction NE GARANTIT PAS `trajet >= optimal` : c'est un invariant des
    APPELANTS (le banc ne mesure que des épisodes gagnés, dont la durée ne peut pas être
    inférieure à la borne inférieure). `longueur_normalisee(2, 6)` rend donc `0.333…` —
    une version antérieure de cette docstring affirmait « >= 1 par construction », ce qui
    était faux et non vérifié par les tests.

    Un `optimal` inconnu (`None` ou `<= 0`) rend `None`, JAMAIS `0.0` : une métrique
    absente doit être absente, pas nulle.
    """
    if optimal is None or optimal <= 0:
        return None
    return trajet / optimal


def taux_avec_ic(k: int, n: int) -> dict:
    """Forme UNIQUE d'un taux et de son intervalle, pour que tous les rapports du banc
    soient comparables entre eux (mêmes clés, mêmes types)."""
    bas, haut = intervalle_wilson(k, n)
    return {
        "k": int(k),
        "n": int(n),
        "taux": (k / n) if n else 0.0,
        "ic_bas": bas,
        "ic_haut": haut,
    }
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

Même commande qu'à l'étape 2. Attendu : **12 tests OK** (5 + 3 + 4).

- [ ] **Étape 5 : commit ciblé avec `bash`**

```bash
git add src/naulthene/instruments/primitives_banc.py tests/test_primitives_banc.py && \
git commit -m "feat(EVA-01): primitives_banc — foyer unique teste (BFS, Wilson, longueur normalisee, taux+IC)"
```

---

### Tâche 2 — Migration des deux sondes

**Fichiers :**
- Modifier : `src/naulthene/instruments/sonde_inertie_motrice.py` (supprimer `def plus_court_chemin` l.67-98, `def intervalle_wilson` l.178-186, ajouter l'import, corriger la docstring l.71-72)
- Modifier : `src/naulthene/instruments/sonde_plancher_geometrique.py` (supprimer `def plus_court_chemin` l.62-97, `def intervalle_wilson` l.143-151, ajouter l'import)
- Tester : `tests/test_primitives_banc.py` (ajout d'une classe)

**Action :** supprimer les deux copies locales dans chaque sonde et importer les primitives
partagées. La docstring inversée d'`sonde_inertie_motrice.py` disparaît avec sa fonction.

**Dépendances et interfaces :**
- Consomme : `primitives_banc` (tâche 1).
- Produit : les deux sondes n'exposent plus leur propre `plus_court_chemin` — elles réutilisent
  l'objet importé. Les appels existants (l.157 et l.281 côté inertie ; l.117 et l.284 côté plancher)
  restent inchangés.

**Critères de succès :**
- `grep -c "def plus_court_chemin\|def intervalle_wilson" <chaque sonde>` → **0**.
- `sonde_inertie_motrice.plus_court_chemin is primitives_banc.plus_court_chemin` → `True` (idem plancher).
- La suite complète reste verte : **170 tests OK** (156 + 12 de la tâche 1 + 2 de migration).

- [ ] **Étape 1 : écrire le test qui échoue**

Ajouter à `tests/test_primitives_banc.py` :

```python
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

```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_primitives_banc.py" -v
```
Attendu : **échec** — `AssertionError` sur `assertIs`, car chaque sonde expose encore sa copie locale.

- [ ] **Étape 3 : écrire l'implémentation minimale**

Dans **chacune** des deux sondes :

1. supprimer le bloc `# --- 1. LE PLUS COURT CHEMIN …` et sa fonction `plus_court_chemin` ;
2. supprimer la fonction `intervalle_wilson` ;
3. ajouter, à côté des autres imports de package :

```python
from naulthene.instruments.primitives_banc import intervalle_wilson, plus_court_chemin
```

4. vérifier que `import collections` et `import math` sont **encore utilisés** dans le fichier ; les
   retirer sinon (`grep -n "collections\.\|math\." <fichier>`).

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -v
```
Attendu : **170 tests OK**, aucune régression.

- [ ] **Étape 5 : commit ciblé avec `bash`**

```bash
git add src/naulthene/instruments/sonde_inertie_motrice.py src/naulthene/instruments/sonde_plancher_geometrique.py tests/test_primitives_banc.py && \
git commit -m "refactor(EVA-01): les 2 sondes migrent vers primitives_banc — fin de la duplication, docstring inverse supprimee"
```

---

### Tâche 3 — Résolution de cohorte et refus

**Fichiers :**
- Créer : `src/naulthene/instruments/banc_final.py`
- Tester : `tests/test_banc_final.py`

**Action :** créer le module avec ses constantes gelées, ses quatre exceptions, la lecture des graines
du manifeste de campagne, la résolution de cohorte qui **refuse tout nom ambigu**, et la fonction
`main()` limitée pour l'instant à la validation des arguments.

**Dépendances et interfaces :**
- Consomme : `primitives_banc` (tâche 1) ; `depouillement.Manifeste` pour la déclaration de cohorte.
- Produit : `lire_graines_du_manifeste`, `lister_cerveaux`, `resoudre_cohorte`, les quatre
  exceptions, les constantes — utilisés par les tâches 4 et 5.

**Critères de succès :**
- Un dossier contenant `K8_NU_g11.brain` **et** `K8_NU_g11 2.brain` lève `NomAmbigue` en **listant**
  le fichier fautif (ligne 453 ci-dessus : le message doit citer le nom exact).
- `--graine-eval-base 500` lève `GraineEvalRefusee` ; `--episodes` absent lève `EpisodesNonDerive`.
- `NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v` → **11 tests OK**.

- [ ] **Étape 1 : écrire les tests qui échouent**

```python
#!/usr/bin/env python3
"""Contrats du banc final standardisé (chantier EVA-01).

    NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v

Ce que ces tests verrouillent :

- un nom de cerveau ambigu (`X_g11 2.brain`) doit faire ÉCHOUER le banc en le NOMMANT :
  ces fichiers existent réellement dans brains/08092026_sci01_balayage_K/ et leurs
  contenus diffèrent (CHANTIER_EVA-01 §3.5). Choisir en silence fausserait l'appariement ;
- le pool de graines d'évaluation ne doit jamais pouvoir collisionner avec le pool
  d'entraînement (5…199) ;
- `--episodes` n'a PAS de valeur par défaut : `n` est un résultat du pilote, pas une
  constante de confort (spec §8bis).
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from naulthene.instruments.banc_final import (  # noqa: E402
    BrasIntrouvable,
    EpisodesNonDerive,
    GraineEvalRefusee,
    NomAmbigue,
    exiger_episodes,
    lire_cohorte_explicite,
    lire_graines_du_manifeste,
    lister_cerveaux,
    main,
    resoudre_cohorte,
    verifier_graine_eval_base,
)


def _toucher(chemin):
    with open(chemin, "wb") as f:
        f.write(b"")


class TestListerCerveaux(unittest.TestCase):
    def test_trouve_les_noms_canoniques(self):
        with tempfile.TemporaryDirectory() as d:
            for g in (11, 22):
                _toucher(os.path.join(d, f"K8_NU_g{g}.brain"))
            trouves = lister_cerveaux(d, "K8_NU", [11, 22])
            self.assertEqual(sorted(trouves), [11, 22])
            self.assertTrue(trouves[11].endswith("K8_NU_g11.brain"))

    def test_refuse_un_nom_ambigu_en_le_nommant(self):
        with tempfile.TemporaryDirectory() as d:
            _toucher(os.path.join(d, "K8_NU_g11.brain"))
            _toucher(os.path.join(d, "K8_NU_g11 2.brain"))
            with self.assertRaises(NomAmbigue) as ctx:
                lister_cerveaux(d, "K8_NU", [11])
            self.assertIn("K8_NU_g11 2.brain", str(ctx.exception))

    def test_ignore_les_autres_bras(self):
        """Ne pas se contenter des CLÉS : le retour est indexé par graine, donc un cerveau
        d'un AUTRE bras écrase la même clé sans changer la liste des clés. Un motif qui
        ignorerait le préfixe de bras rendrait `{11: 'K8_NU_g11.brain'}` quand on demande
        K16_NU — contamination inter-bras invisible, et d'autant plus dangereuse que les
        6 bras partagent les MÊMES 20 graines.

        Les DEUX sens sont nécessaires : `sorted(os.listdir)` rend
        ['K16_NU_g11.brain', 'K8_NU_g11.brain'], donc pour le bras K8_NU le fichier demandé
        est traité EN DERNIER — un mutant « le dernier gagne » tombe alors sur le bon fichier
        par accident alphabétique. Seul le sens K16_NU, où le fichier demandé est traité en
        PREMIER, rend ce mutant visible — et « le dernier gagne » est exactement la sémantique
        du code réel (`canoniques[graine] = ...`, sans condition).
        """
        with tempfile.TemporaryDirectory() as d:
            _toucher(os.path.join(d, "K8_NU_g11.brain"))
            _toucher(os.path.join(d, "K16_NU_g11.brain"))
            for bras in ("K8_NU", "K16_NU"):
                with self.subTest(bras=bras):
                    trouves = lister_cerveaux(d, bras, [11])
                    self.assertEqual(sorted(trouves), [11])
                    self.assertTrue(
                        trouves[11].endswith(f"{bras}_g11.brain"),
                        f"le chemin résolu doit être celui du bras DEMANDÉ ({bras}) : {trouves[11]}")


class TestGardeFous(unittest.TestCase):
    def test_graine_eval_base_sous_le_minimum_est_refusee(self):
        with self.assertRaises(GraineEvalRefusee):
            verifier_graine_eval_base(500)
        verifier_graine_eval_base(10000)  # ne lève pas

    def test_episodes_non_derive_est_refuse(self):
        with self.assertRaises(EpisodesNonDerive):
            exiger_episodes(None)
        with self.assertRaises(EpisodesNonDerive):
            exiger_episodes(0)
        self.assertEqual(exiger_episodes(37), 37)


class TestManifesteDeCampagne(unittest.TestCase):
    def test_lit_les_graines_du_manifeste(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "manifeste.json"), "w", encoding="utf-8") as f:
                json.dump({"campagne": "essai", "graines": [11, 22, 33]}, f)
            self.assertEqual(lire_graines_du_manifeste(d), [11, 22, 33])

    def test_lit_les_graines_d_une_cohorte_explicite_runs(self):
        """Le manifeste connaît DEUX formes ; `runs` est une LISTE de dicts `{"nom": ...}`.
        N'en lire qu'une rendait un diagnostic FAUX sur un manifeste valide (cas réel :
        brains/02092026_rejeu_banc_corrige, 20 runs, mode explicite)."""
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "manifeste.json"), "w", encoding="utf-8") as f:
                json.dump({"campagne": "essai", "mode": "confirmatoire",
                           "runs": [{"nom": "A_g11", "fichier": "banc_A_g11.json"},
                                    {"nom": "B_g11", "fichier": "banc_B_g11.json"},
                                    {"nom": "B_g22", "fichier": "banc_B_g22.json"}]}, f)
            self.assertEqual(lire_graines_du_manifeste(d), [11, 22])





class TestCohorteExplicite(unittest.TestCase):
    """La spec exige une cohorte ENUMEREE quand un bras porte des surnumeraires : le glob
    refuserait K8_NU (2 doublons mesures le 12/09/2026), rendant le test d'acceptation
    impossible. Cette voie est l'echappatoire EXPLICITE et tracee."""

    def test_enumere_les_chemins_et_verifie_leur_existence(self):
        with tempfile.TemporaryDirectory() as d:
            a = os.path.join(d, "K8_NU_g11.brain")
            b = os.path.join(d, "K16_NU_g11.brain")
            _toucher(a)
            _toucher(b)
            inventaire = os.path.join(d, "cohorte.json")
            with open(inventaire, "w", encoding="utf-8") as f:
                json.dump({"K8_NU": {"11": a}, "K16_NU": {"11": b}}, f)
            cohorte = lire_cohorte_explicite(inventaire)
            self.assertEqual(sorted(cohorte), ["K16_NU", "K8_NU"])
            self.assertEqual(cohorte["K8_NU"][11], a)

    def test_un_chemin_absent_est_refuse_en_le_nommant(self):
        with tempfile.TemporaryDirectory() as d:
            inventaire = os.path.join(d, "cohorte.json")
            manquant = os.path.join(d, "absent.brain")
            with open(inventaire, "w", encoding="utf-8") as f:
                json.dump({"K8_NU": {"11": manquant}}, f)
            with self.assertRaises(ValueError) as ctx:
                lire_cohorte_explicite(inventaire)
            self.assertIn("absent.brain", str(ctx.exception))


class TestMainRefuseUnInventaireAMasVide(unittest.TestCase):
    """Le défaut I-3 était dans `main()`, pas dans le garde : il faut donc l'exercer par
    `main()` elle-même. Un garde posé sur le seul chemin glob laissait le succès silencieux
    intact sur la voie explicite — le chemin OBLIGATOIRE de la tâche 9."""

    def test_main_refuse_un_inventaire_explicite_avec_un_bras_vide(self):
        with tempfile.TemporaryDirectory() as d:
            chemin_brain = os.path.join(d, "K8_NU_g11.brain")
            _toucher(chemin_brain)
            with open(os.path.join(d, "manifeste.json"), "w", encoding="utf-8") as f:
                json.dump({"campagne": "essai", "graines": [11]}, f)
            inventaire = os.path.join(d, "cohorte.json")
            with open(inventaire, "w", encoding="utf-8") as f:
                json.dump({"K8_NU": {"11": chemin_brain}, "K2_NU": {}}, f)
            argv = ["banc_final", "--cohorte", d, "--bras", "K8_NU", "K2_NU",
                    "--episodes", "1", "--cohorte-explicite", inventaire]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(BrasIntrouvable) as ctx:
                    main()
            self.assertIn("K2_NU", str(ctx.exception))


class TestBrasIntrouvable(unittest.TestCase):
    """Un bras qui ne résout RIEN est une faute de frappe, pas une cohorte vide : sortir en 0
    en affichant `{'K16_NU_TYPO': 0}` était un succès silencieux (constat I-3)."""

    def test_un_bras_sans_cerveau_est_refuse_en_le_nommant(self):
        with tempfile.TemporaryDirectory() as d:
            _toucher(os.path.join(d, "K8_NU_g11.brain"))
            with self.assertRaises(BrasIntrouvable) as ctx:
                resoudre_cohorte(d, ["K8_NU_TYPO"], [11])
            self.assertIn("K8_NU_TYPO", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Étape 2 : exécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v
```
Attendu : **échec** sur `ModuleNotFoundError: No module named 'naulthene.instruments.banc_final'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

Créer `src/naulthene/instruments/banc_final.py` :

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Le banc final standardisé (chantier EVA-01) — juge à cartes figées.

Rejoue un ou plusieurs `.brain` sur des cartes et des graines IMPOSÉES à tous, en
lecture seule. Le banc ne s'entraîne jamais, ne promeut jamais un niveau, et n'écrit
jamais de `.brain`.

⚠️ Ce que ce banc ne prouve PAS : il mesure une compétence sur cartes imposées et ne dit
RIEN du cursus (règle « un banc forcé ne prouve rien sur le cursus », CLAUDE.md §7).

Protocole gelé : docs/fonctionnement/PROTOCOLE_BANC_FINAL.md
Conception : docs/ameliorations/CHANTIER_EVA-01_banc_final_standardise.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Sequence

CARTES_GELEES: tuple[int, int] = (3, 4)
GRAINE_EVAL_BASE_GELEE: int = 10000
GRAINE_EVAL_BASE_MINIMUM: int = 1000
DOSSIER_SORTIE_DEFAUT: str = "docs/recherche/evals/banc_final"

# Les 3 métriques de la famille pré-enregistrée (MES-04) : 1 primaire + 2 secondaires.
FAMILLE_METRIQUES: tuple[str, ...] = (
    "taux_franchissement",   # PRIMAIRE
    "retour_moyen",          # secondaire
    "longueur_normalisee",   # secondaire
)


class NomAmbigue(RuntimeError):
    """Plusieurs fichiers prétendent au même (bras, graine) — refus, jamais un choix."""


class GraineEvalRefusee(RuntimeError):
    """La base de graines d'évaluation empiéterait sur le pool d'entraînement."""


class EpisodesNonDerive(RuntimeError):
    """Le nombre d'épisodes doit venir du pilote : aucune valeur par défaut."""


class CarteInvalide(RuntimeError):
    """Index de carte hors du PROGRAMME."""


class BrasIntrouvable(RuntimeError):
    """Un bras déclaré ne résout AUCUN cerveau : faute de frappe, pas cohorte vide.

    Sans ce refus, `--bras K16_NU_TYPO` affichait `{'K16_NU_TYPO': 0}` et sortait en 0 —
    un succès silencieux, exactement ce que MES-01 interdit.
    """


def verifier_graine_eval_base(valeur: int) -> int:
    """Refuse une base de graines d'évaluation sous `GRAINE_EVAL_BASE_MINIMUM`.

    Le pool d'entraînement des campagnes réelles est 5…199 (multiples de 11). Une base
    à 0 — le défaut historique de `evaluer_cerveau.py` — collisionnait conceptuellement
    avec lui.
    """
    if int(valeur) < GRAINE_EVAL_BASE_MINIMUM:
        raise GraineEvalRefusee(
            f"--graine-eval-base {valeur} < {GRAINE_EVAL_BASE_MINIMUM} : risque de collision "
            f"avec le pool d'entraînement (5…199)")
    return int(valeur)


def exiger_episodes(valeur) -> int:
    """`n` est un RÉSULTAT du pilote (spec §8bis), jamais une constante de confort."""
    if valeur is None:
        raise EpisodesNonDerive(
            "--episodes est obligatoire : la valeur doit être DÉRIVÉE au pilote "
            "(spec §8bis), pas posée par défaut")
    valeur = int(valeur)
    if valeur < 1:
        raise EpisodesNonDerive(f"--episodes {valeur} invalide (minimum 1)")
    return valeur


def lire_graines_du_manifeste(cohorte: str) -> list[int]:
    """Lit `graines` dans `<cohorte>/manifeste.json` — la cohorte attendue est celle
    déclarée AVANT les runs (règle de Trace), jamais devinée après coup."""
    chemin = os.path.join(cohorte, "manifeste.json")
    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)

    graines = donnees.get("graines")
    if not graines and donnees.get("runs"):
        # Le manifeste du dépôt connaît DEUX formes (voir `depouillement.Manifeste`) :
        # `bras` × `graines`, ou une cohorte explicite `runs` — une LISTE de dicts
        # `{"nom": "A_g11", "fichier": "banc_A_g11.json"}`. N'en lire qu'une rendait un
        # diagnostic FAUX (« ne déclare aucune graine ») sur un manifeste parfaitement
        # valide (cas réel : brains/02092026_rejeu_banc_corrige, 20 runs).
        graines = sorted({int(m.group(1))
                          for entree in donnees["runs"]
                          for m in [re.search(r"_g(\d+)", str(entree.get("nom", "")))] if m})
    if not graines:
        raise ValueError(
            f"{chemin} : aucune graine lisible — formes reconnues : la clé `graines`, ou une "
            f"cohorte explicite `runs` dont les entrées portent « _g<graine> » dans `nom`")
    return [int(g) for g in graines]


def lister_cerveaux(dossier_bras: str, prefixe: str, graines: Sequence[int]) -> dict[int, str]:
    """Rend `{graine: chemin}` pour les noms CANONIQUES `{prefixe}_g{graine}.brain`.

    Refuse tout doublon `<...> N.brain` : ces fichiers portent une espace, existent
    réellement dans la campagne SCI-01, et leurs contenus DIFFÈRENT du canonique
    (mesuré le 12/09/2026). Choisir en silence fausserait l'appariement.
    """
    attendues = {int(g) for g in graines}
    canoniques: dict[int, str] = {}
    suspects: list[str] = []
    motif = re.compile(rf"^{re.escape(prefixe)}_g(\d+)(?: (\d+))?\.brain$")
    if not os.path.isdir(dossier_bras):
        return {}
    for nom in sorted(os.listdir(dossier_bras)):
        m = motif.match(nom)
        if m is None:
            continue
        graine, suffixe = int(m.group(1)), m.group(2)
        if suffixe is not None:
            if graine in attendues:
                suspects.append(nom)
            continue
        if graine in attendues:
            canoniques[graine] = os.path.join(dossier_bras, nom)
    if suspects:
        raise NomAmbigue(
            f"{dossier_bras} : {len(suspects)} fichier(s) surnuméraire(s) pour le même "
            f"(bras, graine) — refus, aucun choix silencieux : {', '.join(sorted(suspects))}")
    return canoniques


def refuser_bras_vides(resolue: dict[str, dict[int, str]]) -> dict[str, dict[int, str]]:
    """Refuse tout bras qui ne résout AUCUN cerveau : faute de frappe, pas cohorte vide.

    Appelé par `resoudre_cohorte` (chemin GLOB) **et** par `main()` APRÈS les deux branches —
    car la voie EXPLICITE ne passe pas par `resoudre_cohorte`, et c'est pourtant le chemin
    OBLIGATOIRE de la tâche 9 (5 bras sur 6 sont refusés par le glob). Un garde posé sur le
    seul chemin glob laissait donc le succès silencieux intact précisément là où il compte.
    """
    vides = sorted(b for b, v in resolue.items() if not v)
    if vides:
        raise BrasIntrouvable(
            f"aucun cerveau résolu pour {len(vides)} bras : {', '.join(vides)} — "
            f"vérifie l'orthographe du bras et la présence des fichiers canoniques "
            f"`<bras>_g<graine>.brain`")
    return resolue


def resoudre_cohorte(cohorte: str, bras: Sequence[str],
                     graines: Sequence[int]) -> dict[str, dict[int, str]]:
    """Rend `{bras: {graine: chemin}}`. L'absence d'un cerveau DANS une cohorte résolue
    n'est PAS traitée ici : c'est `Depouillement.collecter` qui refuse une cohorte
    incomplète (MES-01).

    En revanche un bras qui ne résout RIEN est refusé ici : c'est une faute de frappe, pas
    une cohorte vide. Sans ce garde, `--bras K16_NU_TYPO` affichait `0` cerveau et sortait
    en 0 — un succès silencieux.
    """
    return refuser_bras_vides(
        {b: lister_cerveaux(os.path.join(cohorte, b), b, graines) for b in bras})


def lire_cohorte_explicite(chemin: str) -> dict[str, dict[int, str]]:
    """Enumere la cohorte UN PAR UN : `{bras: {graine: chemin de .brain}}`.

    La spec exige cette voie quand un bras contient des surnumeraires — le glob refuse
    alors le bras entier (K8_NU en porte 2, mesures). Le glob reste le chemin par defaut
    avec son refus d'ambiguite ; ici rien n'est devine, et CHAQUE chemin declare doit
    exister, sinon le refus nomme les absents.
    """
    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)
    cohorte: dict[str, dict[int, str]] = {}
    absents: list[str] = []
    for nom_bras, par_graine in donnees.items():
        cohorte[nom_bras] = {}
        for graine, chemin_brain in par_graine.items():
            if not os.path.exists(chemin_brain):
                absents.append(chemin_brain)
                continue
            cohorte[nom_bras][int(graine)] = chemin_brain
    if absents:
        raise ValueError(
            f"cohorte explicite : {len(absents)} chemin(s) declare(s) mais absent(s) — "
            f"{', '.join(sorted(absents))}")
    return cohorte


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Le banc final standardisé (EVA-01) — cartes figées, graines d'éval dédiées")
    parser.add_argument("--cohorte", type=str, required=True,
                        help="Dossier de campagne (contient manifeste.json et un dossier par bras)")
    parser.add_argument("--bras", type=str, nargs="+", required=True,
                        help="Noms des bras à comparer (ex. K8_NU K16_NU)")
    parser.add_argument("--cohorte-explicite", type=str, default=None,
                        help="JSON {bras: {graine: chemin}} enumerant les cerveaux UN PAR UN. "
                             "Contourne volontairement le glob, qui refuse un bras portant des "
                             "surnumeraires (K8_NU en a 2). Chaque chemin doit exister.")
    parser.add_argument("--cartes", type=int, nargs="+", default=list(CARTES_GELEES),
                        help=f"Indices PROGRAMME (défaut gelé : {list(CARTES_GELEES)})")
    parser.add_argument("--episodes", type=int, default=None,
                        help="Nombre d'épisodes par carte. OBLIGATOIRE : vient du pilote (§8bis)")
    parser.add_argument("--graine-eval-base", type=int, default=GRAINE_EVAL_BASE_GELEE,
                        help=f"Première graine d'évaluation (défaut {GRAINE_EVAL_BASE_GELEE})")
    parser.add_argument("--max-ticks", type=int, default=0,
                        help="0 = budget natif du monde (max_steps). Jamais un plafond posé.")
    parser.add_argument("--dossier-sortie", type=str, default=DOSSIER_SORTIE_DEFAUT)
    args = parser.parse_args()

    verifier_graine_eval_base(args.graine_eval_base)
    exiger_episodes(args.episodes)
    graines = lire_graines_du_manifeste(args.cohorte)
    if args.cohorte_explicite:
        cohorte = lire_cohorte_explicite(args.cohorte_explicite)
    else:
        cohorte = resoudre_cohorte(args.cohorte, args.bras, graines)
    # APRÈS les deux branches : la voie explicite ne passe pas par `resoudre_cohorte`.
    cohorte = refuser_bras_vides(cohorte)
    print(f"📋 {len(args.bras)} bras × {len(graines)} graines d'entraînement, "
          f"cartes {args.cartes}, {args.episodes} épisodes "
          f"(graines d'éval {args.graine_eval_base}…"
          f"{args.graine_eval_base + args.episodes - 1}).")
    print(f"   cerveaux résolus : "
          f"{ {b: len(v) for b, v in cohorte.items()} }")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v
```
Attendu : **11 tests OK**.

Vérifier aussi le refus réel, sur le bras dont les doublons sont **mesurés** (`K1_TEMOIN` :
40 `.brain` pour 20 graines, contenus divergents — CHANTIER_EVA-01 §3.5) :
```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m naulthene.instruments.banc_final \
  --cohorte brains/08092026_sci01_balayage_K --bras K1_TEMOIN --episodes 20
```
Attendu : sortie non nulle et message `NomAmbigue` listant les surnuméraires de `K1_TEMOIN`.

- [ ] **Étape 5 : commit ciblé avec `bash`**

```bash
git add src/naulthene/instruments/banc_final.py tests/test_banc_final.py && \
git commit -m "feat(EVA-01): banc_final — resolution de cohorte, refus des noms ambigus et des graines d'eval collisionnantes"
```

---

### Tâche 4 — Cœur d'évaluation : une carte, des épisodes seedés

**Fichiers :**
- Modifier : `src/naulthene/instruments/banc_final.py` (imports + `evaluer_cerveau_sur_carte`)
- Tester : `tests/test_banc_final.py` (ajout d'un test d'intégration léger)
- Nettoyage (Minor différé de la tâche 3) : retirer de `tests/test_banc_final.py` la ligne d'import
  `refuser_bras_vides`, **inutilisée**. Le CONTRÔLEUR l'avait ajoutée à tort au tour 2 de la tâche 3 ;
  le fichier livré l'a conservée verbatim puisqu'elle figurait dans la référence gelée.

**Action :** ajouter la boucle d'évaluation d'un cerveau sur une carte. **La reproductibilité est le
cœur de la tâche** : graine d'environnement **et** graine torch, pour la même valeur `s`.

**Dépendances et interfaces :**
- Consomme : `primitives_banc` (`plus_court_chemin`, `longueur_normalisee`, `taux_avec_ic`) ;
  depuis `naulthene.cerveau.noyau` : `PROGRAMME`, `creer_env`, `DIM_VISUELLE`, `demarrer_journee`,
  `traiter_tick`, `_budget_natif_carte` ; depuis `naulthene.cerveau.persistance` :
  `PersistanceAnatomique`.
- Produit : `evaluer_cerveau_sur_carte(etat, index_carte, graines) -> dict` avec les clés
  `index_carte`, `env_id`, `nom_classe`, `episodes` (liste), `gagnes`, `tronques`, `taux` (dict de
  `taux_avec_ic`), `retour_moyen`, `longueur_mediane`, `optimal`.

**Critères de succès :**
- Sur un cerveau neuf et la carte 0 (`MiniGrid-Empty-5x5-v0`), 3 épisodes seedés : le même appel
  répété deux fois rend **exactement** les mêmes `gagnes` (c'est le δ_A/A du banc, attendu nul).
- `tronques` compte les épisodes tronqués **par le banc**, aucun épisode n'est absent du rapport.
- ⚠️ **Réserve écrite** : avec `max_ticks = 0` (budget natif du monde), `tronques` vaut toujours 0. Un
  épisode coupé par le `max_steps` du monde bascule `fin_episode` et est compté `tronque=False` : c'est
  un **échec légitime du monde** (l'agent n'a pas gagné dans le temps accordé), pas une mesure tronquée.
  Le drapeau signale une troncature **du banc**, jamais un délai du monde.

- [ ] **Étape 1 : écrire le test qui échoue**

Ajouter à `tests/test_banc_final.py` :

```python
class TestReproductibilite(unittest.TestCase):
    """Le banc ACTUEL du dépôt n'est pas reproductible : `noyau.py` échantillonne l'action
    (`Categorical(...).sample()`) et l'ancien outil ne fixait aucune graine torch.

    ⚠️ Ce test évalue DEUX cerveaux NÉS SOUS LA MÊME GRAINE, chacun évalué UNE FOIS. Une
    version antérieure évaluait UN seul `etat` deux fois de suite : deux appels sur le même
    état ne mesurent pas la même chose, le cerveau portant un état d'un appel à l'autre
    (mesuré par la revue indépendante : carte 4, victoires **0, 0, 1** selon les appels, et un
    épisode qui passe de 61 à **88** ticks, soit **+44 %** sur `longueur_normalisee` ; ce
    constat est un prérequis de la tâche 5, qui doit fournir un état FRAIS par (bras, carte)).

    ⚠️ L'assertion porte sur le résultat COMPLET, pas sur un triplet. Trois générateurs
    décident d'un épisode (le monde via `_graine_episode`, le `np.random` global, torch) :
    deux passes peuvent partager un nombre de victoires tout en ayant joué des trajectoires
    différentes. Comparer `(gagnes, tronques, optimal)` est un critère FAIBLE ; ce que D1
    promet — un δ_A/A nul — est l'identité de l'évaluation, pas celle d'un résumé. Ce qui est
    comparé inclut donc `trajectoire`, le seul champ sensible au COMPORTEMENT.

    ⚠️ LA CARTE ÉVALUÉE EST LA 3, PAS LA 0 — et c'est mesuré. Sur la carte 0, un cerveau neuf
    est SUR SA PROPRE CARTE DE CURSUS : le tirage vaut 0 trois fois sur trois, donc
    `_appliquer_niveau_episode` ne remplace jamais l'environnement et un re-forçage manquant
    est **invisible** — mutation rejouée : 13 tests `OK` malgré le retrait. Sur la carte 3 (une
    carte du plan, `CARTES_GELEES = (3, 4)`), la dérive est réelle : épisode 1 à 324 ticks,
    puis les suivants sur `Empty-5x5` à 100 ticks. C'est aussi pourquoi la carte IMPOSÉE est
    nommée explicitement pour chaque épisode, au lieu de dépendre d'une égalité globale.

    ⚠️ DEUX MUTANTS SURVIVAIENT À LA SEULE ÉGALITÉ DES DEUX PASSES, ET C'EST MESURÉ — d'où les
    deux ajouts qui les tuent, chacun justifié par sa propre mesure :
      - **M4, le levier `torch.manual_seed(graine)`** : la graine de NAISSANCE resynchronise
        déjà le flux torch des deux passes, qui consomment ensuite exactement la même suite.
        Une ligne retirée dans la boucle d'évaluation restait donc invisible. D'où
        `BRUIT_AMBIANT` : les deux passes partent d'états ambiants DIFFÉRENTS, comme les
        évaluations successives du banc réel. M4 est alors tué — et tué par le SEUL champ
        `trajectoire` (mesuré : M4 + retrait de `trajectoire` redevient vert), ce qui prouve du
        même coup la nécessité du résumé de trajectoire exigé au correctif I2 ;
      - **M2, la graine du monde (`graine_run` / `episodes_vecus`)** : à la naissance,
        `graine_run` est ABSENT et `episodes_vecus` vaut **0** — dans les DEUX passes. Le
        compteur redémarre donc à l'identique, et deux passes également fausses restent égales
        entre elles. Aucune comparaison de passes ne peut voir ce mutant ; seule l'assertion
        `monde["graine"] == graine` le nomme, et c'est littéralement la promesse de D-2
        (« le monde est exactement `s` »).
    """

    def test_deux_evaluations_identiques_donnent_le_meme_resultat(self):
        import numpy as np
        import torch

        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.instruments.banc_final import evaluer_cerveau_sur_carte

        def une_passe(bruit_ambiant: int):
            # La NAISSANCE est tirée du RNG torch : on seede AVANT de naître, sans quoi les
            # deux cerveaux comparés seraient deux individus différents.
            torch.manual_seed(GRAINE_DE_NAISSANCE)
            with tempfile.TemporaryDirectory() as d:
                etat = PersistanceAnatomique(
                    fichier=os.path.join(d, "neuf.brain")).charger_ou_naitre()
                etat.agent.eval()
                # ⚠️ LE BRUIT AMBIANT DIFFÈRE ENTRE LES DEUX PASSES (voir BRUIT_AMBIANT) :
                # c'est la condition du banc réel, où les évaluations se SUIVENT dans le même
                # processus. Un résultat ne vaut que s'il ne dépend ni de ce bruit, ni de
                # l'ordre des appels — c'est exactement ce que D1 promet.
                torch.manual_seed(0)
                np.random.seed(0)
                for _ in range(bruit_ambiant):
                    torch.rand(1)
                    np.random.random()
                resultat = evaluer_cerveau_sur_carte(etat, 3, [10000, 10001, 10002])
                etat.env.close()
                return resultat

        premiere, seconde = une_passe(0), une_passe(BRUIT_AMBIANT)

        from naulthene.cerveau.noyau import PROGRAMME
        carte_imposee = PROGRAMME[3][0]
        for episode in premiere["episodes"]:
            self.assertEqual(
                episode["env_id"], carte_imposee,
                "chaque épisode doit avoir joué la carte IMPOSÉE, pas une carte du cursus")
            # ⚠️ L'IDENTITÉ D'ÉPISODE EST `graine`, ET LE MONDE DOIT ÊTRE CETTE GRAINE.
            # C'est la promesse d'appariement des tâches 5-9 : à graine égale, deux bras
            # affrontent le MÊME monde. L'égalité des deux passes ne peut PAS la vérifier
            # seule — mesuré : `graine_run` est ABSENT et `episodes_vecus` vaut **0** à la
            # naissance dans les DEUX passes, donc le compteur redémarre à la même valeur et
            # un `episodes_vecus = graine` retiré laisse les deux passes se ressembler
            # (mutant M2 : vert sans cette assertion, rouge avec).
            self.assertEqual(
                episode["monde"]["graine"], episode["graine"],
                "le monde de l'épisode doit être celui de son identité `graine`")

        self.assertEqual(premiere, seconde,
                         "deux évaluations du MÊME cerveau doivent être identiques en tout")


class TestEpisodeTronque(unittest.TestCase):
    def test_un_episode_non_termine_est_compte_comme_echec_et_marque(self):
        """Un épisode qui n'atteint pas `fin_episode` dans le budget doit apparaître
        comme ÉCHEC avec `tronque=True` — jamais disparaître du dénominateur."""
        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.instruments.banc_final import evaluer_cerveau_sur_carte

        with tempfile.TemporaryDirectory() as d:
            etat = PersistanceAnatomique(
                fichier=os.path.join(d, "neuf.brain")).charger_ou_naitre()
            etat.agent.eval()
            r = evaluer_cerveau_sur_carte(etat, 0, [10000], max_ticks=3)  # budget ridicule
            etat.env.close()
        self.assertEqual(len(r["episodes"]), 1)
        self.assertTrue(r["episodes"][0]["tronque"])
        self.assertFalse(r["episodes"][0]["gagne"])
        self.assertEqual(r["gagnes"], 0)
        self.assertIsInstance(r["episodes"][0]["retour"], float)
        self.assertIsNone(r["episodes"][0]["longueur_normalisee"])  # pas de gain => absente


class TestInstrumentIndisponible(unittest.TestCase):
    """Un garde non PROUVÉ branché ne garde rien — leçon de la tâche 3, où un garde posé sur
    le seul chemin glob laissait le succès silencieux intact sur la voie explicite. Ce test
    retire donc les instruments EN MÉMOIRE et exige que la mesure soit REFUSÉE.

    Sans ces gardes, un renommage dans `noyau.py` ferait tomber tous les `retour` à 0,0
    (`mix_somme.get("Env", 0.0)`) et toutes les empreintes de monde à vide
    (`getattr(detecteur, "positions_food", None)`) : des métriques fausses, publiées sans une
    seule erreur, alors que `retour_moyen` appartient à la famille de métriques gelée.
    """

    def test_un_instrument_retire_empeche_la_mesure(self):
        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.instruments.banc_final import (InstrumentIndisponible,
                                                      evaluer_cerveau_sur_carte)

        with tempfile.TemporaryDirectory() as d:
            etat = PersistanceAnatomique(
                fichier=os.path.join(d, "neuf.brain")).charger_ou_naitre()
            etat.agent.eval()
            evaluer_cerveau_sur_carte(etat, 0, [10000], max_ticks=5)  # la sonde a parlé

            # 1. L'instrument RETIRÉ en mémoire : le canal de récompense d'environnement.
            etat.mix_somme.pop("Env")
            with self.assertRaises(InstrumentIndisponible) as ctx:
                evaluer_cerveau_sur_carte(etat, 0, [10001], max_ticks=5)
            self.assertIn("Env", str(ctx.exception))

            # 2. Le second instrument : les positions semées, sans lesquelles l'empreinte du
            #    monde serait publiée VIDE. On restaure d'abord le canal de récompense, sinon
            #    le garde n° 1 crierait avant que celui-ci ne soit atteint.
            etat.mix_somme["Env"] = 0.0
            del etat.detecteur_ressources_bio.positions_food
            with self.assertRaises(InstrumentIndisponible) as ctx:
                evaluer_cerveau_sur_carte(etat, 0, [10002], max_ticks=5)
            self.assertIn("positions_food", str(ctx.exception))

            etat.env.close()


if __name__ == "__main__":
    unittest.main()

```



- [ ] **Étape 2 : exécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v
```
Attendu : **échec** sur `ImportError: cannot import name 'evaluer_cerveau_sur_carte'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

Ajouter aux imports de `banc_final.py` :

```python
import statistics
import time

import torch

from naulthene.cerveau.noyau import (
    DIM_VISUELLE,
    PROGRAMME,
    _budget_natif_carte,
    creer_env,
    demarrer_journee,
    traiter_tick,
)
from naulthene.cerveau.persistance import PersistanceAnatomique
from naulthene.instruments.primitives_banc import (
    longueur_normalisee,
    plus_court_chemin,
    taux_avec_ic,
)
```

> `_budget_natif_carte` est réutilisé **volontairement** bien que privé : c'est la seule lecture du
> budget réel du monde, et la recopier créerait exactement la duplication que ce chantier supprime.

Puis ajouter la fonction :

```python
def _recompense_env_cumulee(etat) -> float:
    """Σ des récompenses d'ENVIRONNEMENT depuis le début de la journée courante.

    ⚠️ `noyau.py` n'expose PAS `etat.recompense_env` : la récompense rendue par
    `env.step` n'y vit que le temps du tick (variable locale de `traiter_tick`) et
    n'est portée par AUCUN champ de l'état (vérifié : `vars(etat)` ne contient que
    `recompenses_journee`, qui cumule la récompense INTERNE, pas celle du monde). La
    seule lecture possible sans modifier `noyau.py` (ARC-01) est celle de la sonde de
    mixage, qui la CUMULE tick par tick dans `etat.mix_somme["Env"]` — et que
    `demarrer_journee` réarme (via `_reinitialiser_buffers_journee`). Le retour d'un
    épisode est donc la DIFFÉRENCE de cette accumulation sur la fenêtre de l'épisode.

    ⚠️ Lecture seule : le banc n'ajoute rien à la sonde, ne la réarme pas, et ne
    dépend d'aucune mécanique de `noyau.py` pour la mesurer.

    ⚠️ Le `0,0` de repli n'est PAS un silence : `_exiger_instruments` passe avant **et** après
    les ticks de chaque épisode, et refuse la mesure si la sonde a disparu ou s'est tue. Ici,
    un accumulateur vide est l'état LÉGITIME du début d'épisode (`demarrer_journee` vient de
    le réarmer).
    """
    return float(etat.mix_somme.get("Env", 0.0))


def _exiger_instruments(etat, ticks_joues: bool = False) -> None:
    """CRIE si un instrument dont le banc dépend a disparu ou s'est tu (voir la classe).

    Appelé DEUX fois par épisode :
      - AVANT la journée : l'accumulateur porte encore les canaux de l'épisode précédent, ce
        qui permet de voir un canal DISPARU sous un buffer non vide ;
      - APRÈS les ticks : la sonde doit avoir accumulé, sinon elle est morte et tous les
        retours seraient publiés à `0,0`.

    Ce qu'il exige, et pourquoi chacun :
      - `etat.mix_somme` est un dict — sans lui, `retour` tombe à `0,0` en silence ;
      - il n'a pas PERDU le canal `"Env"` — un buffer non vide qui ne le porte plus signale
        une sonde changée sous nos pieds ;
      - après ≥ 1 tick, il PORTE `"Env"` — une sonde muette rendrait tous les retours nuls ;
      - `detecteur_ressources_bio` expose `positions_food`/`positions_water` — sans eux,
        l'empreinte du monde serait publiée VIDE et un tirage de ressources différent
        redeviendrait invisible (c'est par ce champ que M1 est tué).

    Doctrine : une mesure REFUSÉE bruyamment vaut mieux qu'une mesure fausse et silencieuse.
    """
    accumulateur = getattr(etat, "mix_somme", None)
    if not isinstance(accumulateur, dict):
        raise InstrumentIndisponible(
            "etat.mix_somme a disparu (ou n'est plus un dict) : la sonde de mixage de "
            "`noyau.py` (v41.32) n'alimente plus le retour d'épisode, qui serait publié à "
            "0,0 SANS erreur. Vérifier `_sonder_mixage` et son réarmement dans "
            "`_reinitialiser_buffers_journee`.")
    if accumulateur and "Env" not in accumulateur:
        raise InstrumentIndisponible(
            f"etat.mix_somme cumule {len(accumulateur)} canal(aux) mais plus « Env » : la "
            f"récompense d'environnement n'est plus cumulée par la sonde de mixage de "
            f"`noyau.py`. Or `retour_moyen` appartient à la famille de métriques gelée — "
            f"vérifier `_sonder_mixage(etat, Env=…)` dans `traiter_tick`.")
    if ticks_joues and "Env" not in accumulateur:
        raise InstrumentIndisponible(
            "aucune récompense d'environnement accumulée alors que des ticks ont été joués : "
            "la sonde de mixage est MUETTE. Tous les retours seraient mesurés à 0,0 sans "
            "erreur — vérifier `_sonder_mixage(etat, Env=…)` dans `traiter_tick`.")
    detecteur = getattr(etat, "detecteur_ressources_bio", None)
    for attribut in ("positions_food", "positions_water"):
        if not hasattr(detecteur, attribut):
            raise InstrumentIndisponible(
                f"etat.detecteur_ressources_bio.{attribut} a disparu : l'empreinte du monde "
                f"serait publiée VIDE, et un tirage de ressources différent redeviendrait "
                f"invisible. Vérifier "
                f"`DetecteurRessourcesBiologiques.reinitialiser_episode`.")


def _forcer_carte(etat, index_carte: int) -> tuple[str, str]:
    """Remplace l'environnement de `etat` par `PROGRAMME[index_carte]` ; rend `(env_id, nom_classe)`.

    ⚠️ Ne touche PAS `etat.niveau_actuel` : le niveau du cursus reste une mesure de
    développement (exigence 5 du registre) — le banc n'impose qu'une carte de travail.

    ⚠️ Appelé aussi À CHAQUE ÉPISODE, et c'est nécessaire : dès que `fin_episode` bascule,
    `traiter_tick` rebascule lui-même sur une carte TIRÉE DU CURSUS
    (`_appliquer_niveau_episode(_tirer_niveau_episode(etat))`). Sans ce rappel, les épisodes
    suivants n'étaient plus joués sur la carte imposée — le rapport aurait décrit une carte
    jamais mesurée.

    Un détecteur neuf par carte : celui d'un autre niveau resterait accroché (leçon
    d'evaluer_cerveau.py l.77-81).
    """
    env_id, nom_classe = PROGRAMME[index_carte]
    etat.env.close()
    etat.env = creer_env(env_id, DIM_VISUELLE)
    etat.env_id = env_id
    etat.nom_classe = nom_classe
    etat.detecteur = None
    etat.palier_cible = 1
    return env_id, nom_classe


def _empreinte_monde(etat, graine_monde: int) -> dict:
    """Empreinte LISIBLE du monde réellement semé pour l'épisode en cours.

    ⚠️ POURQUOI ELLE EXISTE. Sans elle, le rapport ne disait RIEN de la carte jouée ni du
    tirage : deux évaluations pouvaient diverger (mondes différents) en publiant un résultat
    identique, et la dérive de carte était **invisible dans l'artefact** — il fallait muter
    le code pour la voir. Mesuré : les trois leviers de graine retirés, les positions de
    ressources différaient d'une passe à l'autre (`((3,1),(1,2))` contre `((2,1),(1,2))`)
    pendant que le rapport, lui, restait identique.

    Ce qu'elle porte, et pourquoi chaque champ :
      - `graine` : la graine que le monde VA consommer (`_graine_episode(etat)` au moment du
        reset). C'est le seul moyen de rendre lisible une carte dont le contenu ne dépend pas
        du tirage — `MiniGrid-Empty-5x5-v0` a un but et un départ FIXES, donc son contenu ne
        varie jamais avec la graine, alors que des cartes à disposition aléatoire, si ;
      - `but`, `depart`, `direction` : la disposition engendrée par cette graine ;
      - `food`, `water`, `nid` : les sources SEMÉES par `DetecteurRessourcesBiologiques`, qui
        dépendent du `np.random` GLOBAL, pas de la graine d'environnement.

    Tout est rendu en listes (jamais un `set` de tuples, qui ne se sérialise pas en JSON) et
    TRIÉ, pour que deux mondes identiques donnent une empreinte identique au bit près.

    ⚠️ Lecture seule : on lit la grille et les positions semées, on n'écrit rien. Le balayage
    du but est local parce que `plus_court_chemin` rend la DISTANCE au but, pas sa position.
    """
    u = etat.env.unwrapped
    but = None
    for x in range(u.grid.width):
        for y in range(u.grid.height):
            objet = u.grid.get(x, y)
            if objet is not None and getattr(objet, "type", None) == "goal":
                but = [int(x), int(y)]
    detecteur = getattr(etat, "detecteur_ressources_bio", None)

    def _cases(positions):
        return sorted([int(x), int(y)] for x, y in (positions or ()))

    nid = getattr(detecteur, "nid_position", None)
    return {
        "graine": int(graine_monde),
        "but": but,
        "depart": [int(u.agent_pos[0]), int(u.agent_pos[1])],
        "direction": int(u.agent_dir),
        "food": _cases(getattr(detecteur, "positions_food", None)),
        "water": _cases(getattr(detecteur, "positions_water", None)),
        "nid": [int(nid[0]), int(nid[1])] if nid is not None else None,
    }


def evaluer_cerveau_sur_carte(etat, index_carte: int, graines: Sequence[int],
                              max_ticks: int = 0) -> dict:
    """Rejoue `graines` épisodes SEEDÉS sur `PROGRAMME[index_carte]`, en lecture seule.

    Reproductibilité (décision D1) : pour un épisode d'identité `s`, on pose la graine de
    l'ENVIRONNEMENT (`env.reset(seed=s)`) **et** celle du RNG torch (`torch.manual_seed(s)`).
    La seconde est l'apport d'EVA-01 : sans elle, `Categorical(...).sample()` dans
    `noyau.py` tire une suite d'actions différente à chaque exécution.

    ⚠️ La première ne suffit PAS seule : depuis la v41.9, `demarrer_journee` réamorce
    l'environnement avec une graine DÉRIVÉE (`_graine_episode`), ce qui rend
    `env.reset(seed=s)` inopérant. Le banc fixe donc aussi les deux termes de cette
    dérivation (`graine_run`, `episodes_vecus`) — voir le commentaire de la boucle, qui
    porte la mesure du défaut.

    ⚠️ Le forçage remplace `etat.env` mais ne touche PAS `etat.niveau_actuel` : le niveau du
    cursus reste une mesure de développement (exigence 5 du registre).

    ⚠️ CE QUE CHAQUE ÉPISODE PUBLIE, EN PLUS DE SES MÉTRIQUES. La mesure ne suffit pas : il
    faut pouvoir AUDITER le monde qui l'a produite **et le comportement qu'elle a suivi**.
    Chaque entrée d'`episodes` porte donc `env_id` (la carte réellement jouée), `budget` (les
    ticks réellement reçus), `monde` (empreinte du tirage : graine consommée, but, départ,
    ressources semées) et `trajectoire` (positions occupées, distinctes, dans l'ordre de
    première visite). Sans `monde`, un épisode joué dans un AUTRE monde restait invisible ;
    sans `trajectoire`, deux politiques différentes produisaient le MÊME rapport — mesuré par
    la revue indépendante : **176 ticks divergents sur 972 avec un dict publié identique**.
    Le `budget` de tête est celui de la carte imposée ; les `budget` par épisode doivent lui
    être égaux (re-forçage oblige), et une divergence se lit désormais au lieu d'être tue.

    ⚠️ AUCUN INSTRUMENT MANQUANT NE DÉGRADE LA MESURE EN SILENCE : `_exiger_instruments`
    passe avant chaque épisode **et** après ses ticks, et lève `InstrumentIndisponible`
    plutôt que de publier des retours à `0,0` ou une empreinte vide.

    ⚠️ LES TROIS LEVIERS DE GRAINE SONT L'ENSEMBLE DU DISPOSITIF (voir le commentaire de la
    boucle) — un quatrième a été cherché et **écarté par la mesure**. Hypothèse testée : la
    NAISSANCE d'un cerveau tirerait elle aussi du `np.random` GLOBAL, ce qui exigerait un `np.random.seed(...)` avant
    `charger_ou_naitre()`. Mesuré : faux, et de trois façons — `np.random.get_state()[2]` vaut
    **624 avant et après** une naissance complète (zéro tirage consommé) ; deux naissances
    seedées en torch donnent le même `state_dict` (`sha256 = 134895af4844680b`) que
    `np.random` soit seedé ou non ; leur empreinte LARGE (`4817393f8d31475d`) reste identique
    quand les deux naissances partent d'états `np.random` DIFFÉRENTS. La naissance est tirée
    par `nn.init.xavier_uniform_` sur `base_weight`, donc par torch seul.
    """
    if not 0 <= index_carte < len(PROGRAMME):
        raise CarteInvalide(f"index de carte {index_carte} hors PROGRAMME (0…{len(PROGRAMME) - 1})")

    env_id, nom_classe = _forcer_carte(etat, index_carte)

    budget = int(max_ticks) if max_ticks > 0 else _budget_natif_carte(etat.env)
    episodes = []
    for graine in graines:
        graine = int(graine)
        # AVANT la journée : l'accumulateur de la sonde porte encore l'épisode précédent, donc
        # un canal disparu s'y voit. Un instrument manquant REFUSE la mesure (voir la classe).
        _exiger_instruments(etat)
        if etat.env_id != env_id:
            # ⚠️ LA CARTE DÉRIVE EN COURS D'ÉVALUATION. `traiter_tick` appelle, à la bascule
            # de `fin_episode`, `_appliquer_niveau_episode(_tirer_niveau_episode(etat))` :
            # l'épisode suivant partait alors sur la carte du CURSUS, plus sur la carte
            # imposée. Mesuré sur la carte 3 (`SimpleCrossingS9N1`, budget 324) : premier
            # épisode à 324 ticks, second à **100** — le budget de `Empty-5x5`, avec
            # `env_id` final `MiniGrid-Empty-5x5-v0`. Le rapport aurait donc attribué à la
            # carte 3 des épisodes joués ailleurs. On re-force à CHAQUE épisode.
            _forcer_carte(etat, index_carte)
        # --- L'IDENTITÉ D'ÉPISODE EST `graine` : LES TROIS GÉNÉRATEURS QUI EN DÉCIDENT ---
        #
        # 1. LE MONDE. `demarrer_journee` ne consomme PAS la graine posée par
        #    `env.reset(seed=…)` : il appelle `_reset_seede`, qui réamorce l'environnement
        #    avec `_graine_episode(etat)` = `etat.graine_run × GRAINE_ECART_ENTRE_RUNS +
        #    etat.episodes_vecus` (v41.9). Un `env.reset(seed=graine)` seul est donc un
        #    NO-OP — mesuré : deux passes du même cerveau gagnaient l'épisode 10001 en
        #    **64** puis en **82** ticks. Le banc fixe les DEUX termes de cette dérivation,
        #    sans quoi la carte d'un épisode dépend du nombre d'épisodes déjà vécus dans le
        #    processus : deux bras n'affronteraient plus le même monde pour la même graine.
        #    (`episodes_vecus` n'a qu'un rôle mécanique dans tout `noyau.py` — vérifié.)
        # 2. LES RESSOURCES SEMÉES dans le monde et le TIRAGE DU CURSUS passent, eux, par le
        #    `np.random` GLOBAL (`DetecteurRessourcesBiologiques`, `_tirer_niveau_episode`) —
        #    que ni la graine d'environnement ni `torch.manual_seed` ne contrôlent. Mesuré :
        #    sans ce seed, deux passes identiques divergeaient (graine 10000 gagnée en 75
        #    ticks d'un côté, perdue de l'autre) ; avec lui, elles sont bit-identiques.
        # 3. L'ACTION est échantillonnée par `torch` (`Categorical(...).sample()` dans
        #    `noyau.py`) — c'est l'apport D1 d'EVA-01, sans lequel la suite d'actions
        #    change à chaque exécution.
        #
        # On seede AVANT `demarrer_journee` : c'est là que le monde est semé, et un second
        # reset après coup désynchroniserait les détecteurs déjà calibrés sur la carte tirée.
        etat.graine_run = 0
        etat.episodes_vecus = graine
        etat.env.reset(seed=graine)
        np.random.seed(graine)
        # La graine que `_reset_seede` va consommer DANS `demarrer_journee` : lue ici, avant
        # l'incrément du compteur, c'est exactement celle du monde de CET épisode. Elle entre
        # dans l'empreinte publiée, sinon une carte à disposition FIXE (`Empty-5x5` : but et
        # départ constants) ne laisserait aucune trace d'un changement de graine.
        graine_monde = _graine_episode(etat)
        demarrer_journee(etat)
        torch.manual_seed(graine)  # D1 — reproductibilité de l'échantillonnage d'action

        # --- CE QUE L'ÉPISODE A RÉELLEMENT JOUÉ, PUBLIÉ DANS LE RÉSULTAT ---
        # La carte est lue ICI, après le forçage et le reset : c'est celle dans laquelle les
        # ticks vont se dérouler. Le budget est celui de CETTE carte (borné par `max_ticks`
        # s'il est posé) — avec le re-forçage il vaut le budget annoncé ; s'il en divergeait,
        # l'artefact le DIRAIT au lieu de le taire.
        carte_jouee = etat.env_id
        budget_episode = int(max_ticks) if max_ticks > 0 else _budget_natif_carte(etat.env)
        empreinte = _empreinte_monde(etat, graine_monde)

        optimal = plus_court_chemin(etat.env)
        recompense_avant = _recompense_env_cumulee(etat)
        gagne, ticks, tronque, recompense = False, None, True, 0.0
        # --- LA TRAJECTOIRE, SANS LAQUELLE L'ARTEFACT EST AVEUGLE AU COMPORTEMENT ---
        # Mesuré par la revue indépendante : sur la carte 3, 176 ticks sur 972 divergeaient
        # entre deux passes ALORS QUE le rapport publié était identique — les 3 épisodes
        # donnent `gagne=False`, `ticks=324` (le budget entier), `retour=0.0`, et le monde
        # semé est constant. Tout ce qui était publié était donc aveugle à la trajectoire.
        # On publie les positions OCCUPÉES, distinctes, dans l'ordre de première visite :
        # compact (une carte 9×9 en compte quelques dizaines) et fidèle à ce qui a été joué.
        #
        # ⚠️ Lues dans `environnement_episode`, JAMAIS dans `etat.env` : au tick de bascule,
        # `traiter_tick` peut avoir remplacé `etat.env` par une carte du CURSUS — la position
        # lue serait alors celle d'un autre monde.
        environnement_episode = etat.env
        positions_vues: list[list[int]] = []
        vues = set()
        with torch.no_grad():
            for _tick in range(budget_episode):
                ticks_avant = etat.ticks_episode_courant
                traiter_tick(etat)
                position = environnement_episode.unwrapped.agent_pos
                cle = (int(position[0]), int(position[1]))
                if cle not in vues:
                    vues.add(cle)
                    positions_vues.append([cle[0], cle[1]])
                # `traiter_tick` enchaîne LUI-MÊME sur un nouvel épisode dès que
                # `fin_episode` bascule : on lit la victoire au tick MÊME de la bascule.
                if etat.fin_episode:
                    _exiger_instruments(etat, ticks_joues=True)
                    gagne = bool(etat.victoire_aujourdhui)
                    ticks = ticks_avant + 1
                    tronque = False
                    recompense = _recompense_env_cumulee(etat) - recompense_avant
                    break
            if tronque:
                # Un épisode tronqué n'a pas de victoire, mais sa récompense partielle
                # reste une information MESURÉE : on la calcule, on ne la laisse pas à 0,0.
                _exiger_instruments(etat, ticks_joues=True)
                recompense = _recompense_env_cumulee(etat) - recompense_avant
        episodes.append({
            "graine": graine,
            "gagne": gagne,
            "tronque": tronque,
            "ticks": ticks,
            "retour": recompense,
            # --- Ce que l'épisode a RÉELLEMENT joué (audit du JSON, sans muter le code) ---
            # `env_id` : la carte des ticks. Un épisode joué ailleurs qu'annoncé se lit ici,
            # au lieu d'être invisible dans l'artefact.
            "env_id": carte_jouee,
            # `budget` : le nombre de ticks que CET épisode a reçus. Avec le re-forçage il
            # vaut le budget annoncé en tête de résultat ; une divergence signalerait que la
            # carte n'a pas été tenue.
            "budget": budget_episode,
            # `monde` : empreinte du monde semé (graine consommée, but, départ, ressources).
            "monde": empreinte,
            # `trajectoire` : les positions occupées, distinctes, dans l'ordre de première
            # visite. C'est le seul champ SENSIBLE AU COMPORTEMENT — sans lui, deux
            # trajectoires différentes (donc deux politiques) produisent le MÊME rapport :
            # mesuré, 176 ticks divergents sur 972 avec un dict publié identique.
            "trajectoire": positions_vues,
            # La longueur n'a de sens que sur un épisode GAGNÉ : sur un échec, le
            # « trajet » est la durée du budget et le rapport ne mesurerait rien.
            "longueur_normalisee": longueur_normalisee(ticks, optimal) if gagne else None,
        })

    gagnes = sum(1 for e in episodes if e["gagne"])
    longueurs = [e["longueur_normalisee"] for e in episodes
                 if e["longueur_normalisee"] is not None]
    return {
        "index_carte": index_carte,
        "env_id": env_id,
        "nom_classe": nom_classe,
        "optimal": optimal,
        "budget": budget,
        "episodes": episodes,
        "gagnes": gagnes,
        "tronques": sum(1 for e in episodes if e["tronque"]),
        "taux": taux_avec_ic(gagnes, len(episodes)),
        "retour_moyen": float(statistics.mean([e["retour"] for e in episodes])) if episodes else 0.0,
        "longueur_mediane": (float(statistics.median(longueurs)) if longueurs else None),
    }

```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v
```
Attendu : **14 tests OK**. Le test de reproductibilité peut prendre ~30 s (deux passes de 3 épisodes
sur 5×5) ; c'est normal.

- [ ] **Étape 5 : commit ciblé avec `bash`**

```bash
git add src/naulthene/instruments/banc_final.py tests/test_banc_final.py && \
git commit -m "feat(EVA-01): coeur d'evaluation reproductible — graine env ET torch par episode, victoire captivee au tick de bascule"
```

### Correctif C1 / I2 / I3 — revue indépendante du 12/09/2026

La revue a établi que **la propriété centrale de la tâche n'était PAS démontrée**, mesure à l'appui :
dans le scénario du test (cerveau neuf, carte 3, deux passes), **176 ticks sur 972 divergent** — le
premier au tick 36 — **alors que l'égalité passe**. Raison : sur la carte 3, tout ce qui est publié est
**aveugle à la trajectoire** (3 épisodes `gagne=False`, `ticks=324` = le budget entier, `retour=0.0`,
but/départ/direction constants). Et le levier **torch** — celui que D1 nomme — n'est tué par **aucun**
test : retirer la ligne `torch.manual_seed(graine)` laisse **13/13 verts**.

**1. Rendre l'artefact sensible à la TRAJECTOIRE** (tue I2, et rend C1 testable). Chaque épisode publie
un résumé de trajectoire : les positions occupées par l'agent au fil des ticks, sous forme compacte mais
**fidèle** — au minimum la liste des positions visitées distinctes dans l'ordre de première visite.
Lecture seule, via `env.unwrapped.agent_pos` après chaque `traiter_tick`. Sans cela, **deux trajectoires
différentes produisent le même rapport**.

**2. Rendre le test INDÉPENDANT DE L'ORDRE** (tue C1). La fonction n'est pas pure : l'état du cerveau
(mémoire, dopamine, patience) **persiste entre deux appels**, donc deux passes sur le MÊME `etat` ne
mesurent pas la même chose. Le test compare désormais **deux cerveaux nés sous la même graine**, chacun
évalué **une fois** — la revue a mesuré que deux naissances seedées donnent des trajectoires identiques
(0/261 ticks divergents). La carte reste **3** (la seule où la dérive est réelle) et l'assertion
explicite `env_id == carte_imposée` est conservée. La naissance est donc seedée : `torch.manual_seed`
AVANT `charger_ou_naitre()`.

**3. Des garde-fous qui CRIENT** (tue I3). `etat.mix_somme.get("Env", 0.0)` et les
`getattr(detecteur, "positions_food", None)` dégradent en **silence** : désactiver la sonde de mixage
fait tomber **tous les retours à 0,0** — et `retour_moyen` est une métrique de la **famille gelée** —
tandis que renommer les positions rend des listes **vides sans erreur**, or M1 n'est tué que par ces
deux champs. Ajouter l'exception nommée `InstrumentIndisponible(RuntimeError)` et **exiger** la
présence : de la clé `"Env"`, et des attributs de positions. Un instrument absent doit **empêcher** la
mesure, jamais la fausser.

**4. Prouver que le garde est BRANCHÉ** (leçon de la tâche 3 : un garde non prouvé branché ne garde
rien). Un test retire l'instrument en mémoire et exige `InstrumentIndisponible`.

**Preuve exigée à la livraison** : le tableau de mutations passe à **six mutants + un contrôle**, et le
levier **torch** doit désormais être tué : M1 sans `np.random.seed` · M2 sans graine du monde · M3 les
trois leviers · **M4 sans `torch.manual_seed`** · M5 sans re-forçage · T tous ensemble · C contrôle vert.

---

### Tâche 5 — Rapport de cohorte et statistiques MES-01

**Fichiers :**
- Modifier : `src/naulthene/instruments/banc_final.py` (`executer_banc`, `main` complété)
- Tester : `tests/test_banc_final.py` (ajout d'un test de refus de cohorte incomplète)

**Action :** orchestrer l'évaluation de la cohorte et déléguer **toute** la statistique à
`depouillement.py` : refus de cohorte incomplète, appariement par graine d'entraînement, seuil
Bonferroni pour une famille de 3.

### Nettoyage (Minor différé de la tâche 4)

Le message d'échec du test de reproductibilité est **périmé** : il dit « deux évaluations du MÊME
cerveau » alors que le test compare désormais **deux cerveaux nés sous la même graine**. Un échec futur
serait mal lu. Reformule-le dans `tests/test_banc_final.py`.

### PRÉREQUIS — l'évaluation n'est PAS pure : chaque (bras, carte) part d'un état FRAIS

La revue indépendante de la tâche 4 a **mesuré** que `evaluer_cerveau_sur_carte` n'est pas une fonction
pure de `(fichier .brain, carte, graines)` : l'état du cerveau (mémoire, dopamine, patience) **persiste
entre deux appels**, si bien que le MÊME appel donne des résultats différents — carte 0 : victoires
**1, 2, 2** ; carte **4** (une carte GELÉE du plan) : **0, 0, 1** ; et évaluer une autre carte intercalée
déplace le même épisode de 61 à **88** ticks, soit **+44 %** sur `longueur_normalisee`, une métrique de
la famille. La cause est **exclue du seeding** : deux cerveaux nés sous la même graine, évalués une fois
chacun, donnent des trajectoires identiques.

**Conséquence OBLIGATOIRE pour `executer_banc`** : un **état FRAIS par (bras, carte)** — recharger le
`.brain` (ou repartir d'une naissance identique au même point) avant CHAQUE évaluation, pour que le
chiffre d'une carte ne dépende pas de l'**ordre** d'évaluation dans le processus. Sans cela, deux bras
évalués dans un ordre différent ne sont plus comparables, et l'appariement par graine de la tâche 9 perd
son sens.

**Dépendances et interfaces :**
- Consomme : tâches 3 et 4 ; `depouillement.Manifeste`, `depouillement.Depouillement`.
- Produit : `executer_banc(...) -> dict` ; écrit un JSON horodaté dans `--dossier-sortie` et
  imprime `Depouillement.rapport()`.

**Critères de succès :**
- Un bras amputé d'un cerveau fait lever `CampagneInvalide` (règle MES-01), et **aucun** agrégat
  n'est publié.
- Le rapport imprime le seuil Bonferroni de la famille de 3 (`seuil_t(n, 3, 0.05)`).
- `NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v` → **20 tests OK**.

- [ ] **Étape 1 : écrire le test qui échoue**

Ajouter à `tests/test_banc_final.py` :

```python
class TestCohorteIncomplete(unittest.TestCase):
    """Règle MES-01 : une cohorte incomplète ne produit AUCUN résultat confirmatoire.
    On la réutilise — on ne la réécrit pas."""

    def test_un_cerveau_manquant_rend_la_campagne_invalide(self):
        with tempfile.TemporaryDirectory() as d:
            # manifeste : 2 graines, 2 bras ; on ne pose QUE 3 des 4 cerveaux.
            with open(os.path.join(d, "manifeste.json"), "w", encoding="utf-8") as f:
                json.dump({"campagne": "essai", "graines": [11, 22]}, f)
            for bras in ("A", "B"):
                os.mkdir(os.path.join(d, bras))
            _toucher(os.path.join(d, "A", "A_g11.brain"))
            _toucher(os.path.join(d, "A", "A_g22.brain"))
            _toucher(os.path.join(d, "B", "B_g11.brain"))
            # B_g22 manquant
            metriques = {
                os.path.join(d, "A", "A_g11.brain"): {"taux_franchissement": 0.5},
                os.path.join(d, "A", "A_g22.brain"): {"taux_franchissement": 0.4},
                os.path.join(d, "B", "B_g11.brain"): {"taux_franchissement": 0.2},
            }
            from naulthene.instruments.depouillement import CampagneInvalide
            from naulthene.instruments.banc_final import construire_depouillement

            with self.assertRaises(CampagneInvalide):
                dp = construire_depouillement(d, ["A", "B"], [11, 22], metriques)
                dp.apparie("A", "B", "taux_franchissement", "primaire")

    def test_main_refuse_un_bras_absent_de_l_inventaire(self):
        """Un bras listé dans `--bras` mais ABSENT de l'inventaire n'est pas dans le dict
        résolu : `refuser_bras_vides` ne peut pas le voir. Sans ce second contrôle,
        `--bras K8_NU K2_NU` avec un inventaire sans K2_NU sortait en 0 — même classe de
        succès silencieux que I-3, sur le chemin OBLIGATOIRE de la tâche 9."""
        with tempfile.TemporaryDirectory() as d:
            chemin_brain = os.path.join(d, "K8_NU_g11.brain")
            _toucher(chemin_brain)
            with open(os.path.join(d, "manifeste.json"), "w", encoding="utf-8") as f:
                json.dump({"campagne": "essai", "graines": [11]}, f)
            inventaire = os.path.join(d, "cohorte.json")
            with open(inventaire, "w", encoding="utf-8") as f:
                json.dump({"K8_NU": {"11": chemin_brain}}, f)  # K2_NU absent
            argv = ["banc_final", "--cohorte", d, "--bras", "K8_NU", "K2_NU",
                    "--episodes", "1", "--cohorte-explicite", inventaire]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(BrasIntrouvable) as ctx:
                    main()
            self.assertIn("K2_NU", str(ctx.exception))
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v
```
Attendu : **échec** sur `ImportError: cannot import name 'construire_depouillement'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

Ajouter à `banc_final.py` :

```python
def construire_depouillement(cohorte: str, bras: Sequence[str], graines: Sequence[int],
                             metriques_par_chemin: dict) -> Depouillement:
    """Déclare la cohorte puis la collecte, en déléguant à MES-01.

    Le `lecteur` rend les métriques DÉJÀ calculées, indexées par chemin de `.brain` ; un
    cerveau absent ou non évalué rend `None`, ce que `collecter` transforme en violation
    — c'est ainsi que la cohorte incomplète devient structurellement impossible.

    ⚠️ `extension_log=".brain"` N'EST PAS COSMÉTIQUE : sans lui, le banc ne publie JAMAIS rien.
    `Manifeste.cohorte` compose ses chemins en `<cohorte>/<bras>/<bras>_g<graine>` +
    `extension_log`, dont le défaut est `.log`. Or `collecter` exige d'abord
    `os.path.exists(chemin)`, et le `lecteur` cherche ensuite ce chemin dans
    `metriques_par_chemin`, INDEXÉ PAR CHEMIN DE `.brain` (la seule grandeur que le banc
    mesure). Mesuré : `Manifeste(...).cohorte` rend
    `[('A_g11', '/cohorte/A/A_g11.log'), ('A_g22', '/cohorte/A/A_g22.log')]` par défaut, et
    `[… '/cohorte/A/A_g11.brain']` avec `.brain`. Avec le défaut, les 4 (bras, graine) seraient
    donc exclus pour « fichier absent », `dp.runs` resterait VIDE, et une campagne pourtant
    complète serait déclarée invalide à chacune de ses exécutions.

    Aucune statistique n'est recodée ici : appariement par graine d'entraînement, seuil de
    Bonferroni (`seuil_t(n, comparaisons_prevues, alpha)`) et refus de publier viennent tous de
    `depouillement.py` (MES-01).

    ⚠️ `dossier` EST LE NOM DU BRAS, JAMAIS `os.path.join(cohorte, b)` — ET CE DÉFAUT RENDAIT LE BANC
    INUTILISABLE SUR SON PROPRE CHEMIN DOCUMENTÉ. `Manifeste.cohorte` compose
    `<dossier>/<prefixe>_g<graine>.brain`, et `Depouillement.chemin_run` RE-préfixe ce chemin par sa
    `racine` (posée à `cohorte` ici). Un `dossier` déjà préfixé DOUBLAIT donc tout : mesuré sur la
    cohorte réelle (`--cohorte brains/08092026_sci01_balayage_K`, invocation du plan, 40 `.brain`),
    le manifeste réclamait `brains/08092026_sci01_balayage_K/brains/08092026_sci01_balayage_K/
    K16_NU/K16_NU_g11.brain` → **0 run collecté, 40 violations « fichier absent », aucun agrégat,
    dossier de sortie non créé**. Avec une cohorte ABSOLUE, `os.path.join(racine, chemin_absolu)`
    rend le chemin absolu : le doublage disparaissait **par accident**, et TOUS les tests, qui
    passent par `tempfile` donc par des chemins absolus, étaient aveugles à ce défaut.

    ⚠️ LA RENCONTRE ENTRE LE MANIFESTE ET LES MÉTRIQUES EST CANONICALISÉE (`os.path.abspath`), ET NE
    DOIT PAS ÊTRE UNE COÏNCIDENCE TEXTUELLE. Le manifeste recompose ses chemins, et les clés de
    `metriques_par_chemin` viennent de la résolution (`resoudre_cohorte`) ou, en voie EXPLICITE,
    d'un inventaire JSON écrit à la main : rien ne garantit la même écriture des deux côtés
    (`./brains/…` contre `brains/…`, relatif contre absolu). Mesuré : des clés relatives face à une
    racine absolue suffisaient à tout exclure en « source illisible ou vide ». On compare donc les
    chemins canoniques, jamais leur orthographe.
    """
    manifeste = Manifeste(
        campagne=os.path.basename(os.path.normpath(cohorte)),
        mode="confirmatoire",
        graines=[int(g) for g in graines],
        bras={b: {"dossier": b, "prefixe": b} for b in bras},
        alpha=0.05,
        comparaisons_prevues=len(FAMILLE_METRIQUES),
        extension_log=".brain",
    )
    dp = Depouillement(manifeste, racine=cohorte)
    metriques_canoniques = {os.path.abspath(chemin): metriques
                            for chemin, metriques in metriques_par_chemin.items()}
    dp.collecter(lambda chemin: metriques_canoniques.get(os.path.abspath(chemin)))
    return dp


def executer_banc(cohorte: str, bras: Sequence[str], cartes: Sequence[int],
                  graines: Sequence[int], episodes: int, graine_eval_base: int,
                  dossier_sortie: str, max_ticks: int = 0,
                  cohorte_resolue: dict | None = None) -> dict:
    """Évalue toute la cohorte, puis publie le rapport et l'agrégat JSON.

    ⚠️ `cohorte_resolue` est le SEUL moyen de faire entrer la voie EXPLICITE jusqu'ici :
    `resoudre_cohorte` passe par le glob, qui REFUSE 5 des 6 bras de la campagne SCI-01
    (mesuré : 113 surnuméraires). Sans ce paramètre, `--cohorte-explicite` serait perdu au
    moment de l'évaluation et la tâche 9 échouerait à la résolution — après dix tâches.
    """
    cartes = [int(c) for c in cartes]
    graines_eval = list(range(int(graine_eval_base), int(graine_eval_base) + int(episodes)))
    if cohorte_resolue is None:
        cohorte_resolue = resoudre_cohorte(cohorte, bras, graines)

    par_cerveau, metriques_par_chemin = {}, {}
    for nom_bras, cerveaux in cohorte_resolue.items():
        for graine, chemin in sorted(cerveaux.items()):
            cle = f"{nom_bras}_g{graine}"
            par_carte = {}
            # L'empreinte de l'état de DÉPART de chaque carte : publiée plus bas à côté de
            # `cartes`, elle est la seule pièce qui rend la fraîcheur de l'état AUDITABLE.
            empreintes_etat_initial = {}
            t0 = time.time()
            for index_carte in cartes:
                # ⚠️ L'ÉTAT EST RECHARGÉ ICI, DONC PAR (bras, carte) — ET C'EST STRUCTURANT.
                # `evaluer_cerveau_sur_carte` n'est PAS une fonction pure de
                # (fichier .brain, carte, graines) : le cerveau GARDE son état d'un appel à
                # l'autre (mémoire, dopamine, patience), si bien que le MÊME épisode ne rend
                # plus le même résultat selon ce qui a été joué avant lui. Mesuré par la revue
                # indépendante de la tâche 4 : carte 0 → victoires **1, 2, 2** ; carte 4 (une
                # carte GELÉE du plan) → **0, 0, 1** ; et une autre carte intercalée déplace un
                # même épisode de 61 à **88** ticks, soit **+44 %** sur `longueur_normalisee`,
                # une métrique de la FAMILLE. Ce n'est PAS un défaut de seeding : deux cerveaux
                # nés sous la même graine, évalués UNE fois chacun, donnent des trajectoires
                # identiques — c'est bien l'état du cerveau qui survit.
                # Conséquence : recharger le `.brain` avant CHAQUE (bras, carte), pour que le
                # chiffre d'une carte ne dépende pas de l'ORDRE d'évaluation dans le processus.
                # Sans cela, deux bras évalués dans un ordre différent ne sont plus comparables
                # et l'appariement par graine (tâche 9) perd son sens.
                # Parade VÉRIFIÉE : deux `charger_ou_naitre()` du même `.brain` rendent un
                # `state_dict` BIT-IDENTIQUE. Coût : une relecture de fichier par (bras, carte),
                # négligeable devant les épisodes joués. Le flux aléatoire, lui, n'est pas
                # décalé par cette relecture : `evaluer_cerveau_sur_carte` réamorce torch ET
                # `np.random` à chaque épisode.
                # REPRODUIT ET CHIFFRÉ ICI, sur un cerveau RÉEL de la campagne SCI-01
                # (`brains/08092026_sci01_balayage_K/K8_NU/K8_NU_g11.brain`), carte 0, graines
                # 10000-10002, MÊME carte évaluée 3 fois de suite — l'état partagé dérive,
                # l'état frais non :
                #   état PARTAGÉ : ticks de la graine 10000 = **10, 44, 25** et
                #                 `longueur_normalisee` = **2,5 → 11,0 → 6,25** (+340 % du 1er
                #                 au 2e appel) ;
                #   état FRAIS   : les trois appels rendent le MÊME triplet `[10, 6, 5]`.
                # (Sur la carte 4 du même cerveau l'effet n'est pas visible : il perd les trois
                # épisodes au budget entier — l'effet dépend donc de la carte, ce qui est une
                # raison de plus pour ne pas s'en remettre à l'ordre.)
                # ⚠️ La parade suppose que le `.brain` EXISTE : les deux voies de résolution le
                # garantissent (`lister_cerveaux` ne rend que des noms présents,
                # `lire_cohorte_explicite` refuse un chemin absent) — sinon `charger_ou_naitre`
                # ferait NAÎTRE un cerveau différent à chaque carte, ce qui serait pire.
                etat = PersistanceAnatomique(fichier=chemin).charger_ou_naitre()
                etat.agent.eval()  # jamais d'entraînement, jamais de sauvegarde
                # ⚠️ L'EMPREINTE DE L'ÉTAT DE DÉPART, CALCULÉE JUSTE APRÈS LE CHARGEMENT ET
                # PUBLIÉE PAR (bras, carte). C'est l'artefact qui rend la promesse ci-dessus
                # AUDITABLE : les deux cartes d'un même cerveau doivent porter la MÊME empreinte,
                # et une divergence se LIT dans le rapport au lieu d'exiger une sonde externe.
                # Elle est prise AVANT `evaluer_cerveau_sur_carte` : elle décrit l'état depuis
                # lequel la mesure PART, pas celui qu'elle laisse derrière elle.
                # ⚠️ ELLE DOIT RESTER ICI, DANS LA BOUCLE DES CARTES, ET PAS SEULEMENT PARCE QU'ELLE
                # Y TROUVE SON SENS : hissée à côté du chargement, elle publierait DEUX FOIS la
                # même empreinte alors que l'état serait partagé — l'artefact CERTIFIERAIT une
                # fraîcheur qu'il n'aurait pas vérifiée (mesuré : la variante « squelette du plan »
                # laisse le verrou d'empreinte VERT). La propriété qui garde réellement ce banc est
                # l'INDÉPENDANCE À L'ORDRE, tenue par le test `TestIndependanceALOrdre`.
                empreinte_etat = _empreinte_etat(etat)
                try:
                    resultat = evaluer_cerveau_sur_carte(etat, index_carte, graines_eval,
                                                         max_ticks)
                finally:
                    # `_forcer_carte` a ouvert un monde : on le referme même si la mesure est
                    # refusée (`InstrumentIndisponible`), sinon l'évaluation suivante hériterait
                    # d'un environnement resté ouvert.
                    etat.env.close()
                par_carte[resultat["nom_classe"]] = resultat
                empreintes_etat_initial[resultat["nom_classe"]] = empreinte_etat
                print(f"   ✅ {cle:22s} {resultat['nom_classe']:32s} "
                      f"{resultat['taux']['taux'] * 100:5.1f}% "
                      f"({resultat['gagnes']}/{resultat['taux']['n']}), "
                      f"tronqués {resultat['tronques']}")
            par_cerveau[cle] = {"chemin": chemin, "cartes": par_carte,
                                "empreinte_etat_initial": empreintes_etat_initial,
                                "duree_s": time.time() - t0}
            # Vue plate pour le test apparié MES-01 (une valeur scalaire par métrique).
            premiere = par_carte[PROGRAMME[cartes[0]][1]]
            metriques_par_chemin[chemin] = {
                "taux_franchissement": premiere["taux"]["taux"],
                "retour_moyen": premiere["retour_moyen"],
                # None (jamais NaN, qui empoisonnerait le t, ni 0.0, qui serait un mensonge)
                "longueur_normalisee": premiere["longueur_mediane"],
                "jours_final": 0,  # le banc n'a pas de notion de jours
            }

    dp = construire_depouillement(cohorte, bras, graines, metriques_par_chemin)
    print("\n" + dp.rapport())

    comparaisons, ignorees = [], []
    for i, bras_a in enumerate(bras):
        for bras_b in list(bras)[i + 1:]:
            for metrique in FAMILLE_METRIQUES:
                manquants = [f"{b}_g{g}" for b in (bras_a, bras_b)
                             for g in dp.manifeste.graines
                             if dp.runs.get(f"{b}_g{g}", {}).get(metrique) is None]
                if manquants:
                    # Une métrique absente n'est PAS zéro : on refuse de la tester et on
                    # DIT pourquoi, plutôt que de moyenner un NaN ou un faux 0,0.
                    ignorees.append(
                        f"{metrique} — {bras_a} vs {bras_b} : indisponible pour "
                        f"{len(manquants)} cerveau(x) ({', '.join(manquants[:5])}"
                        + ("…" if len(manquants) > 5 else "") + ")")
                    continue
                comparaisons.append(dp.apparie(bras_a, bras_b, metrique,
                                               f"{metrique} — {bras_a} vs {bras_b}"))
    print("\n=== TESTS APPARIÉS (famille de "
          f"{len(FAMILLE_METRIQUES)} métriques, seuil Bonferroni) ===")
    for resultat in comparaisons:
        print("  " + resultat.ligne())
    if ignorees:
        print(f"\n⚠️  {len(ignorees)} comparaison(s) IGNORÉE(S) — métrique absente, jamais zéro :")
        for motif in ignorees:
            print("   - " + motif)

    rapport = {
        "campagne": os.path.basename(os.path.normpath(cohorte)),
        "date_evaluation": datetime.now(timezone.utc).isoformat(),
        "protocole": "PROTOCOLE_BANC_FINAL v1",
        "cartes": cartes,
        "episodes_par_carte": int(episodes),
        "graine_eval_base": int(graine_eval_base),
        "graines_entrainement": [int(g) for g in graines],
        "bras": list(bras),
        "cerveaux": par_cerveau,
        "couverture": {"obtenus": len(dp.runs), "attendus": len(bras) * len(graines)},
        "exclusions": dp.exclusions,
        "violations": dp.violations,
        "seuil_bonferroni": (comparaisons[0].seuil if comparaisons else None),
        "comparaisons_ignorees": ignorees,
        "comparaisons": [
            {"label": r.label, "delta": r.delta, "t": r.t, "n": r.n,
             "favorables": r.favorables, "seuil": r.seuil,
             "significatif": r.significatif} for r in comparaisons],
    }
    if dp.violations:
        # ⚠️ AUCUN AGRÉGAT N'EST PUBLIÉ SUR UNE CAMPAGNE INVALIDE — critère de succès de la
        # tâche, et doctrine de `Depouillement.publier` (MES-01 : « à la moindre violation :
        # aucun agrégat écrit et code de sortie non nul »). Le garde est nécessaire ICI, et pas
        # seulement dans `apparie` : quand un cerveau manque, TOUTES les métriques des paires
        # concernées sont absentes, donc aucune comparaison n'est tentée, donc rien ne lève —
        # et le fichier s'écrirait sans une erreur. Il serait pourtant parfaitement lisible :
        # `couverture` inférieure à `attendus`, `comparaisons` vide — un lecteur pressé y
        # verrait un résultat. `main()` sort en 1, et le rapport ci-dessus nomme les exclusions.
        print(f"\n⛔ Agrégat NON publié : campagne INVALIDE ({len(dp.violations)} violation(s), "
              f"voir le rapport ci-dessus) — règle MES-01. Rien n'a été écrit dans "
              f"{dossier_sortie}.")
        return rapport
    os.makedirs(dossier_sortie, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = os.path.join(dossier_sortie, f"banc_final_{horodatage}.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Agrégat écrit dans {chemin} (aucun .brain n'a été modifié).")
    return rapport

```

Puis compléter `main()` en remplaçant le bloc `print` final par :

```python
    # Cohérence --bras / inventaire (Minor différé de la tâche 3) : un bras déclaré dans --bras
    # mais ABSENT de l'inventaire n'est pas dans le dict résolu, donc `refuser_bras_vides` ne peut
    # pas le voir — `--bras K8_NU K2_NU` avec un inventaire sans K2_NU sortait en 0 en affichant
    # `{'K8_NU': 1}`. Même classe de défaut que I-3 : succès silencieux.
    absents = sorted(set(args.bras) - set(cohorte))
    if absents:
        raise BrasIntrouvable(
            f"bras déclarés dans --bras mais ABSENTS de l'inventaire : {', '.join(absents)}")
    rapport = executer_banc(
        cohorte=args.cohorte, bras=args.bras, cartes=args.cartes, graines=graines,
        episodes=args.episodes, graine_eval_base=args.graine_eval_base,
        dossier_sortie=args.dossier_sortie, max_ticks=args.max_ticks,
        cohorte_resolue=cohorte)  # la voie explicite doit SURVIVRE jusqu'ici
    return 0 if not rapport["violations"] else 1
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v
```
Attendu : **20 tests OK**.

- [ ] **Étape 5 : commit ciblé avec `bash`**

```bash
git add src/naulthene/instruments/banc_final.py tests/test_banc_final.py && \
git commit -m "feat(EVA-01): rapport de cohorte — refus MES-01, appariement par graine, seuil Bonferroni de la famille de 3"
```

### Correctif — deux coquilles de ce plan, mesurées à l'implémentation

L'implémentation a établi DEUX défauts de ce plan, **tous deux vérifiés par le contrôleur** :

1. **`extension_log=".brain"` manquait.** `Manifeste.cohorte` construit ses chemins avec
   `self.extension_log`, dont le DÉFAUT est `.log` (`depouillement.py:151` et `:180`). Sur une cohorte
   **COMPLÈTE**, le banc collectait donc **0 run sur 4** et déclarait **4 violations** (au lieu de 4/0) :
   tel quel, il ne publiait **JAMAIS rien**, et la tâche 9 aurait échoué.
2. **L'agrégat était écrit INCONDITIONNELLEMENT**, contredisant le critère de cette tâche (« aucun
   agrégat n'est publié » sur cohorte incomplète). Le garde `if dp.violations: return rapport` est
   **nécessaire** : sans cerveau manquant, aucune comparaison n'est tentée, donc **rien ne lève**.

### Deux garanties à VERROUILLER par un test (le compte passe de 16 à 18)

Leçon des tâches 1, 3 et 4 : **un correctif non verrouillé par un test régresse en silence.** Ces deux
propriétés ont été prouvées par sonde et par mutation, mais **aucun test de la suite ne les défend** —
or ce sont les deux piliers de cette tâche.

1. **`extension_log=".brain"`** : un test exige qu'une cohorte **complète** soit collectée **entièrement**
   (autant de runs que de cerveaux attendus, **aucune** violation). Sous la mutation « extension_log
   retiré », ce test doit **ÉCHOUER**. C'est la plus grave des deux coquilles : sans elle, le banc
   n'écrit rien du tout.
2. **L'état FRAIS par (bras, carte)** — prérequis I1, cœur de cette tâche. Pour qu'un mutant
   « états mis en cache » soit **visible dans l'artefact** et pas seulement détectable par sonde, chaque
   (bras, carte) du rapport publie une **empreinte de l'état de départ** du cerveau chargé (au minimum
   un hachage du `state_dict`), et un test exige que **les deux cartes d'un même cerveau partent de la
   MÊME empreinte**. Sous un cache, la seconde carte porterait une empreinte différente → le test
   ÉCHOUE.

Instrumenter est ici la bonne réponse, pas un luxe : c'est exactement ce qui a débloqué C1 à la
tâche 4 — **un artefact qui ne montre pas ce qu'il a mesuré ne peut pas être audité.**

### Correctif 2 — chemin DOUBLÉ (Critical) et verrou d'état frais AVEUGLE

La revue indépendante a établi DEUX défauts, tous deux mesurés.

**1. Critical — chemin doublé sur une cohorte RELATIVE.** `construire_depouillement` pose
`dossier=os.path.join(cohorte, b)` ET `Depouillement(..., racine=cohorte)` ; or `Depouillement.chemin_run`
rejoint `racine` au chemin **déjà préfixé** (`depouillement.py:248-249`, `:178-180`). Avec une
`--cohorte` **relative** — celle de l'invocation documentée — **tout chemin est doublé**. Mesuré sur la
cohorte RÉELLE (40 `.brain`, invocation exacte de la tâche 9) : **exit 1, 40 violations « fichier
absent (brains/…/brains/…/K8_NU/K8_NU_g11.brain) », 0 run collecté, AUCUN agrégat**. Le banc est
inutilisable sur son propre chemin documenté.

⚠️ Le défaut **échappait aux tests parce qu'ils n'utilisent que des chemins ABSOLUS** (`tempfile`) : avec
un chemin absolu, `os.path.join(racine, chemin_absolu)` rend le chemin absolu, donc le doublage
disparaît **par accident**. Même cécité que le verrou `extension_log` — la leçon commence à être claire :
**une garantie éprouvée seulement sur le chemin absolu ne dit rien du chemin relatif, qui est celui que
le plan documente.**

Correction : `"dossier": b` (prouvé : 4 runs / 0 violation sur le même cas relatif), **plus un cas de
test à chemin de cohorte RELATIF** qui ÉCHOUE sous l'ancien code.

**2. Important — le verrou d'état frais est aveugle au RETOUR du défaut qu'il annonce fermer.** Un
mutant plus naturel que le mien — le **squelette du plan** : charger **une fois** par cerveau et calculer
l'empreinte **à côté du chargement**, donc **HORS de la boucle des cartes** — laisse **18/18 VERTS** alors
qu'il reproduit le défaut : mesuré sur cerveau réel, la carte 0 donne `traj=[3,2]` au lieu de `[8,2]`, et
les empreintes publiées sont **identiques** — donc **l'artefact MENT**. Une empreinte calculée au mauvais
endroit est un témoin qui atteste une propriété que le code n'a pas.

Correction : une assertion d'**INDÉPENDANCE À L'ORDRE** — le même cerveau évalué avec `cartes=[0, 3]`
puis `cartes=[3, 0]` doit rendre des résultats **par carte** ÉGAUX. Vraie sur le code livré, fausse sous
le mutant.

---

### Tâche 6 — Archivage d'`evaluer_cerveau.py`

**Fichiers :**
- Modifier : `src/naulthene/instruments/evaluer_cerveau.py` (bandeau + constante)

**Nettoyage inclus (Minor différé de la tâche 5)** : dans `tests/test_banc_final.py`, la docstring de
`TestEtatFraisParCarte` affirme « M-ETAT-NATUREL → VERT, 20 tests, 0 échec » — mesuré aujourd'hui :
**1 échec sur 20** (le test d'ordre le tue). La parenthèse doit se lire « le verrou d'empreinte SEUL
reste vert », sinon elle contredit la phrase suivante du même paragraphe. Corrige la formulation, rien
d'autre.

**Action :** marquer l'outil comme **archive historique** (précédent exact : `colab.py` / ARC-01) et
corriger `DOSSIER_EVALS_DEFAUT`, qui désigne un dossier **inexistant**.

**Dépendances et interfaces :**
- Consomme : rien.
- Produit : plus aucun outil ne produit son défaut dans un dossier fantôme.

**Critères de succès :**
- `grep -n "docs/notes/evals" src/naulthene/instruments/evaluer_cerveau.py` → **0 occurrence**.
- Le bandeau nomme le successeur (`banc_final.py`) et la raison.
- La suite complète reste verte : **191 tests OK** (156 + 12 + 2 + 11 + 3 + 6 + 1).

- [ ] **Étape 1 : écrire le test qui échoue**

Ajouter à `tests/test_banc_final.py` :

```python
class TestOutilsArchives(unittest.TestCase):
    def test_le_dossier_de_sortie_de_l_outil_archive_existe_vraiment(self):
        """`docs/notes/evals` n'a jamais existé : chaque évaluation écrivait dans un
        dossier fantôme (constat EVA-01 §3.3)."""
        from naulthene.instruments import evaluer_cerveau
        chemin = evaluer_cerveau.DOSSIER_EVALS_DEFAUT
        self.assertEqual(chemin, "docs/recherche/evals")
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v
```
Attendu : **échec** — `'docs/notes/evals' != 'docs/recherche/evals'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

1. Remplacer la constante :
```python
DOSSIER_EVALS_DEFAUT = "docs/recherche/evals"
```
2. Corriger la docstring de module (l.19) et le `--dossier-sortie` qui la citent.
3. Ajouter au début de la docstring de module, juste sous le titre :
```
⚠️ ARCHIVE HISTORIQUE (chantier EVA-01, 12/09/2026). Remplacé par
`naulthene.instruments.banc_final`, seul juge standardisé : celui-ci fige les cartes,
dédie un pool de graines d'évaluation et fixe une graine torch par épisode (cet outil ne
le faisait pas — ses mesures n'étaient pas reproductibles). Conservé pour ses rapports
déjà publiés dans `docs/recherche/evals/` et pour l'exploration ponctuelle. Aucune
mécanique nouvelle ne doit y être ajoutée.
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -v
```
Attendu : **191 tests OK**.

- [ ] **Étape 5 : commit ciblé avec `bash`**

```bash
git add src/naulthene/instruments/evaluer_cerveau.py tests/test_banc_final.py && \
git commit -m "docs(EVA-01): evaluer_cerveau archive (successeur banc_final) + dossier de sortie fantome corrige"
```

---

### Tâche 7 — Pilote : dérivation de `n` par la règle de domination du bruit

**Fichiers :**
- Créer : `src/naulthene/instruments/pilote_banc.py`
- Créer : `brains/EVA01_pilote_<JJMMAAAA>/LISEZ_MOI.md`
- Créer : `docs/recherche/campagnes/EVA01_<JJMMAAAA>_la_derivation_de_n.md`
- Créer : `brains/EVA01_pilote_<JJMMAAAA>/pilote.json`

**Action :** **mesurer** la dispersion inter-cerveaux du taux de franchissement sur cartes figées,
puis en **dériver** `n`. C'est l'étape qui remplace la constante posée `n=100`.

**Dépendances et interfaces :**
- Consomme : tâches 4 et 5.
- Produit : `deriver_n(p_barre, sd_inter, facteur=3.0) -> int` et `pilote.json` contenant
  `p_barre`, `sd_inter`, `ic_sd`, `n_derive`.

**Critères de succès :**
- `pilote.json` existe et contient les quatre grandeurs.
- Le carnet publie la règle, `p̄`, la SD **et l'IC de la SD** (un pilote à petit `n` donne une SD
  instable : publier sa valeur seule serait trompeur).
- `n` retenu est **dérivé**, avec la ligne de calcul visible.

- [ ] **Étape 1 : écrire le test de la règle (avant toute mesure)**

```python
class TestDerivationDeN(unittest.TestCase):
    """La règle doit être testable SANS lancer d'évaluation : elle est pure."""

    def test_n_est_le_plus_petit_qui_satisfait_la_contrainte(self):
        from naulthene.instruments.pilote_banc import deriver_n
        n = deriver_n(p_barre=0.5, sd_inter=0.15, facteur=3.0)
        # SE = sqrt(0.25/n) <= 0.05  =>  n >= 100
        self.assertEqual(n, 100)
        self.assertLessEqual((0.25 / n) ** 0.5, 0.15 / 3.0)

    def test_une_dispersion_plus_grande_exige_moins_d_episodes(self):
        from naulthene.instruments.pilote_banc import deriver_n
        self.assertLess(deriver_n(0.5, 0.3), deriver_n(0.5, 0.1))

    def test_une_dispersion_nulle_est_refusee(self):
        """SD = 0 signifie que le pilote n'a rien mesuré : on refuse plutôt que de
        rendre un n arbitraire."""
        from naulthene.instruments.pilote_banc import deriver_n
        with self.assertRaises(ValueError):
            deriver_n(0.5, 0.0)
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_pilote_banc.py" -v
```
Attendu : **échec** sur `ModuleNotFoundError`.

- [ ] **Étape 3 : écrire l'implémentation**

`src/naulthene/instruments/pilote_banc.py` : exposer `deriver_n(p_barre, sd_inter, facteur=3.0) ->
int`, qui rend le plus petit `n ≥ 1` tel que `sqrt(p̄(1−p̄)/n) ≤ sd_inter / facteur`, et lève
`ValueError` si `sd_inter <= 0` ou `p_barre` hors `]0, 1[`. Le module expose aussi une fonction
`mesurer_pilote(cohorte, bras, cartes, graines_pilote, episodes, ...)` qui appelle
`evaluer_cerveau_sur_carte` sur 2 à 4 cerveaux et rend `p̄`, la SD inter-cerveaux, et l'IC de cette SD.

- [ ] **Étape 4 : exécuter le pilote (mesure réelle) avec `bash`**

D'abord créer le dossier de campagne **avant** le premier run (règle de Trace : une campagne
s'archive avant de tourner), avec son `LISEZ_MOI.md` portant le protocole. Puis :

⚠️ Le `20` ci-dessous est un **budget de MESURE du pilote**, PAS le `n` du protocole : le pilote
mesure la dispersion, puis `n` en est **dérivé**. Les deux nombres sont distincts, et seul le second
entre au protocole (tâche 8). `K8_NU` porte 2 surnuméraires mesurés : la voie explicite est
obligatoire, le glob refuserait le bras.

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m naulthene.instruments.banc_final \
  --cohorte brains/08092026_sci01_balayage_K --bras K8_NU --cartes 3 4 --episodes 20 \
  --cohorte-explicite brains/EVA01_pilote_<JJMMAAAA>/cohorte_explicite.json \
  --graine-eval-base 10000 --dossier-sortie brains/EVA01_pilote_<JJMMAAAA>
```
Attendu : un JSON contenant les taux par cerveau, puis `pilote.json` avec `n_derive`.

- [ ] **Étape 5 : commit ciblé avec `bash`**

```bash
git add src/naulthene/instruments/pilote_banc.py tests/test_pilote_banc.py \
  brains/EVA01_pilote_<JJMMAAAA>/LISEZ_MOI.md brains/EVA01_pilote_<JJMMAAAA>/pilote.json \
  docs/recherche/campagnes/EVA01_<JJMMAAAA>_la_derivation_de_n.md && \
git commit -m "mesure(EVA-01): pilote — p barre et dispersion inter-cerveaux mesures, n derive par la regle de domination du bruit"
```

---

### Tâche 8 — Gel du protocole avec le `n` dérivé

**Fichiers :**
- Créer : `docs/fonctionnement/PROTOCOLE_BANC_FINAL.md`
- Modifier : `docs/INDEX.md` (section `fonctionnement/`)

**Action :** écrire le protocole **gelé et versionné** en y inscrivant le `n` **dérivé** (tâche 7) et
la règle qui l'a produit.

**Dépendances et interfaces :**
- Consomme : tâche 7 (`n` dérivé, `p̄`, SD).
- Produit : le document normatif que tout rapport du banc doit référencer.

**Critères de succès :**
- Le document contient : les deux cartes et leurs index, le pool `10000…10099`, le `n` **dérivé avec
  sa ligne de calcul**, la famille de 3 métriques, le seuil Bonferroni, la règle de version, et
  l'interdit « banc forcé ».
- `docs/INDEX.md` référence le document.

- [ ] **Étape 1 :** rédiger le document avec les valeurs **mesurées** à la tâche 7.
- [ ] **Étape 2 :** vérifier la cohérence par `grep` : `n` du protocole ≡ `n_derive` de `pilote.json`.
- [ ] **Étape 3 :** inscrire le document dans `docs/INDEX.md` (section `fonctionnement/`).
- [ ] **Étape 4 :** relire le document et retirer tout énoncé non mesuré.
- [ ] **Étape 5 :** commit.

```bash
git add docs/fonctionnement/PROTOCOLE_BANC_FINAL.md docs/INDEX.md && \
git commit -m "docs(EVA-01): protocole du banc final gele v1 — n derive au pilote, cartes et pool d'eval figes"
```

---

### Tâche 9 — Test d'acceptation D3

**Fichiers :**
- Créer : `docs/recherche/campagnes/EVA01_<JJMMAAAA>_le_banc_est_accepte.md`
- Créer : `brains/EVA01_acceptation_<JJMMAAAA>/banc_final_*.json`

**Action :** rejouer la cohorte SCI-01 **énumérée explicitement** (`K8_NU`, `K16_NU` — les
surnuméraires de `K8_NU` sont mis en quarantaine, pas devinés) sur les cartes 3 et 4, et vérifier que
le banc reproduit l'**ordre** connu : `K8_NU` devant `K16_NU`. **L'ordre, jamais les valeurs.**

**Dépendances et interfaces :**
- Consomme : tâches 5 et 8.
- Produit : le carnet d'acceptation + l'agrégat. **La publication du banc est conditionnée à ce test.**

**Critères de succès :**
- Le rapport montre `K8_NU` > `K16_NU` sur la métrique primaire.
- δ_A/A du banc mesuré et publié (deux passes du même cerveau).
- Si l'ordre n'est pas reproduit : **le banc est refusé**, l'écart est enquêté, et **aucune
  supériorité n'est revendiquée**.

- [ ] **Étape 1 :** créer le dossier de campagne et son `LISEZ_MOI.md` **avant** le run.
- [ ] **Étape 2 :** écrire `cohorte_explicite.json` énumérant les 40 cerveaux **canoniques**
      (`K8_NU_g<g>.brain` et `K16_NU_g<g>.brain` pour les 20 graines du manifeste), en **nommant**
      les surnuméraires écartés — puis lancer avec le `n` du protocole :

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m naulthene.instruments.banc_final \
  --cohorte brains/08092026_sci01_balayage_K --bras K8_NU K16_NU --cartes 3 4 \
  --episodes <n_du_protocole> --graine-eval-base 10000 \
  --cohorte-explicite brains/EVA01_acceptation_<JJMMAAAA>/cohorte_explicite.json \
  --dossier-sortie brains/EVA01_acceptation_<JJMMAAAA>
```
- [ ] **Étape 3 :** lancer deux fois le même cerveau pour mesurer δ_A/A ; le publier.
- [ ] **Étape 4 :** écrire le carnet (question, protocole, chiffres bruts, vérifications, limites,
      ce que ça ferme et laisse ouvert).
- [ ] **Étape 5 :** commit.

```bash
git add brains/EVA01_acceptation_<JJMMAAAA>/LISEZ_MOI.md \
  brains/EVA01_acceptation_<JJMMAAAA>/banc_final_*.json \
  docs/recherche/campagnes/EVA01_<JJMMAAAA>_le_banc_est_accepte.md && \
git commit -m "mesure(EVA-01): test d'acceptation — le banc reproduit l'ordre SCI-01 (K8 devant K16)"
```

---

### Tâche 10 — Clôture documentaire

**Fichiers :**
- Modifier : `docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md` (EVA-01 + ligne de suivi)
- Modifier : `docs/INDEX.md` (carnet et campagne)
- Modifier : `docs/fonctionnement/JOURNAL_DES_RUNS.md` (fin réelle du pilote et de l'acceptation)

**Action :** clore EVA-01 dans le registre avec ses **quatre éléments** (cause/décision, correction
référencée, vérification fraîche, CHANGELOG **ou** carnet).

**Dépendances et interfaces :**
- Consomme : tâches 1 à 9.

**Critères de succès :**
- EVA-01 passe à ✅ Clos avec les quatre éléments, chacun pointant un artefact réel.
- Les trois critères de clôture du registre sont cochés explicitement.
- Aucune supériorité non mesurée n'est écrite.

- [ ] **Étape 1 :** mettre à jour la ligne EVA-01 du tableau de suivi.
- [ ] **Étape 2 :** écrire la section de clôture (cause → correction → vérification → trace).
- [ ] **Étape 3 :** mettre à jour `docs/INDEX.md` et le journal des runs (fin réelle).
- [ ] **Étape 4 :** passer la suite complète une dernière fois, noter le nombre de tests.
- [ ] **Étape 5 :** commit et push.

```bash
git add docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md docs/INDEX.md \
  docs/fonctionnement/JOURNAL_DES_RUNS.md && \
git commit -m "docs(EVA-01): cloture — banc standardise livre, protocole gele, ordre SCI-01 reproduit"
```

---

## Ce que ce plan ne fait pas

- **Aucune modification de `noyau.py`** — vérifiable par `git diff --stat` à la fin.
- **Aucun `n` posé** : `n` sort du pilote (tâche 7) et nulle part ailleurs.
- **Aucune supériorité revendiquée** avant la réussite du test d'acceptation (tâche 9).
- Les cerveaux surnuméraires (`X_g11 2.brain`) ne sont **ni réparés ni supprimés** : l'audit de
  `brains/` est un chantier **distinct**, hors de ce plan.
