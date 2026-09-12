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
- `NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v` → **10 tests OK**.

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
        6 bras partagent les MÊMES 20 graines."""
        with tempfile.TemporaryDirectory() as d:
            _toucher(os.path.join(d, "K8_NU_g11.brain"))
            _toucher(os.path.join(d, "K16_NU_g11.brain"))
            trouves = lister_cerveaux(d, "K8_NU", [11])
            self.assertEqual(sorted(trouves), [11])
            self.assertTrue(trouves[11].endswith("K8_NU_g11.brain"),
                            f"le chemin résolu doit être celui du bras DEMANDÉ : {trouves[11]}")


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


def resoudre_cohorte(cohorte: str, bras: Sequence[str],
                     graines: Sequence[int]) -> dict[str, dict[int, str]]:
    """Rend `{bras: {graine: chemin}}`. L'absence d'un cerveau DANS une cohorte résolue
    n'est PAS traitée ici : c'est `Depouillement.collecter` qui refuse une cohorte
    incomplète (MES-01).

    En revanche un bras qui ne résout RIEN est refusé ici : c'est une faute de frappe, pas
    une cohorte vide. Sans ce garde, `--bras K16_NU_TYPO` affichait `0` cerveau et sortait
    en 0 — un succès silencieux.
    """
    resolue = {b: lister_cerveaux(os.path.join(cohorte, b), b, graines) for b in bras}
    vides = sorted(b for b, v in resolue.items() if not v)
    if vides:
        raise BrasIntrouvable(
            f"aucun cerveau résolu pour {len(vides)} bras : {', '.join(vides)} — "
            f"vérifie l'orthographe du bras et la présence des fichiers canoniques "
            f"`<bras>_g<graine>.brain` dans {cohorte}")
    return resolue


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
Attendu : **10 tests OK**.

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
- `tronques` compte les épisodes non terminés ; aucun épisode n'est absent du rapport.

- [ ] **Étape 1 : écrire le test qui échoue**

Ajouter à `tests/test_banc_final.py` :

```python
class TestReproductibilite(unittest.TestCase):
    """Le banc ACTUEL n'est pas reproductible : noyau.py échantillonne l'action
    (Categorical(...).sample()) et evaluer_cerveau.py ne fixe aucune graine torch.
    Ce test verrouille le correctif : même cerveau + mêmes graines => mêmes résultats."""

    def test_deux_evaluations_identiques_donnent_le_meme_resultat(self):
        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.instruments.banc_final import evaluer_cerveau_sur_carte

        def une_passe():
            with tempfile.TemporaryDirectory() as d:
                etat = PersistanceAnatomique(
                    fichier=os.path.join(d, "neuf.brain")).charger_ou_naitre()
                etat.agent.eval()
                r = evaluer_cerveau_sur_carte(etat, 0, [10000, 10001, 10002])
                etat.env.close()
                return r["gagnes"], r["tronques"], r["optimal"]

        self.assertEqual(une_passe(), une_passe())


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
def evaluer_cerveau_sur_carte(etat, index_carte: int, graines: Sequence[int],
                              max_ticks: int = 0) -> dict:
    """Rejoue `graines` épisodes SEEDÉS sur `PROGRAMME[index_carte]`, en lecture seule.

    Reproductibilité (décision D1) : pour un épisode d'identité `s`, on pose la graine de
    l'ENVIRONNEMENT (`env.reset(seed=s)`) **et** celle du RNG torch (`torch.manual_seed(s)`).
    La seconde est l'apport d'EVA-01 : sans elle, `Categorical(...).sample()` dans
    `noyau.py` tire une suite d'actions différente à chaque exécution.

    ⚠️ Le forçage remplace `etat.env` mais ne touche PAS `etat.niveau_actuel` : le niveau du
    cursus reste une mesure de développement (exigence 5 du registre).
    """
    if not 0 <= index_carte < len(PROGRAMME):
        raise CarteInvalide(f"index de carte {index_carte} hors PROGRAMME (0…{len(PROGRAMME) - 1})")

    env_id, nom_classe = PROGRAMME[index_carte]
    etat.env.close()
    etat.env = creer_env(env_id, DIM_VISUELLE)
    etat.env_id = env_id
    etat.nom_classe = nom_classe
    # Un détecteur neuf par carte : celui d'un autre niveau resterait accroché (leçon
    # d'evaluer_cerveau.py l.77-81).
    etat.detecteur = None
    etat.palier_cible = 1

    budget = int(max_ticks) if max_ticks > 0 else _budget_natif_carte(etat.env)
    episodes = []
    for graine in graines:
        graine = int(graine)
        # On seede l'env AVANT demarrer_journee : celui-ci appelle env.reset() sans seed et
        # consomme donc la graine posée ici (comportement Gymnasium). Un second reset
        # désynchroniserait les détecteurs déjà calibrés sur la carte tirée.
        etat.env.reset(seed=graine)
        demarrer_journee(etat)
        torch.manual_seed(graine)  # D1 — reproductibilité de l'échantillonnage d'action

        optimal = plus_court_chemin(etat.env)
        recompense_avant = float(etat.recompense_env)
        gagne, ticks, tronque, recompense = False, None, True, 0.0
        with torch.no_grad():
            for _tick in range(budget):
                ticks_avant = etat.ticks_episode_courant
                traiter_tick(etat)
                # `traiter_tick` enchaîne LUI-MÊME sur un nouvel épisode dès que
                # `fin_episode` bascule : on lit la victoire au tick MÊME de la bascule.
                if etat.fin_episode:
                    gagne = bool(etat.victoire_aujourdhui)
                    ticks = ticks_avant + 1
                    tronque = False
                    recompense = float(etat.recompense_env) - recompense_avant
                    break
            if tronque:
                # Un épisode tronqué n'a pas de victoire, mais sa récompense partielle
                # reste une information MESURÉE : on la calcule, on ne la laisse pas à 0,0.
                recompense = float(etat.recompense_env) - recompense_avant
        episodes.append({
            "graine": graine,
            "gagne": gagne,
            "tronque": tronque,
            "ticks": ticks,
            "retour": recompense,
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
Attendu : **12 tests OK**. Le test de reproductibilité peut prendre ~30 s (deux passes de 3 épisodes
sur 5×5) ; c'est normal.

- [ ] **Étape 5 : commit ciblé avec `bash`**

```bash
git add src/naulthene/instruments/banc_final.py tests/test_banc_final.py && \
git commit -m "feat(EVA-01): coeur d'evaluation reproductible — graine env ET torch par episode, victoire captivee au tick de bascule"
```

---

### Tâche 5 — Rapport de cohorte et statistiques MES-01

**Fichiers :**
- Modifier : `src/naulthene/instruments/banc_final.py` (`executer_banc`, `main` complété)
- Tester : `tests/test_banc_final.py` (ajout d'un test de refus de cohorte incomplète)

**Action :** orchestrer l'évaluation de la cohorte et déléguer **toute** la statistique à
`depouillement.py` : refus de cohorte incomplète, appariement par graine d'entraînement, seuil
Bonferroni pour une famille de 3.

**Dépendances et interfaces :**
- Consomme : tâches 3 et 4 ; `depouillement.Manifeste`, `depouillement.Depouillement`.
- Produit : `executer_banc(...) -> dict` ; écrit un JSON horodaté dans `--dossier-sortie` et
  imprime `Depouillement.rapport()`.

**Critères de succès :**
- Un bras amputé d'un cerveau fait lever `CampagneInvalide` (règle MES-01), et **aucun** agrégat
  n'est publié.
- Le rapport imprime le seuil Bonferroni de la famille de 3 (`seuil_t(n, 3, 0.05)`).
- `NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v` → **13 tests OK**.

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
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v
```
Attendu : **échec** sur `ImportError: cannot import name 'construire_depouillement'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

Ajouter à `banc_final.py` :

```python
from datetime import datetime, timezone

from naulthene.instruments.depouillement import Depouillement, Manifeste


def construire_depouillement(cohorte: str, bras: Sequence[str], graines: Sequence[int],
                             metriques_par_chemin: dict) -> Depouillement:
    """Déclare la cohorte puis la collecte, en déléguant à MES-01.

    Le `lecteur` rend les métriques DÉJÀ calculées, indexées par chemin de `.brain` ; un
    cerveau absent ou non évalué rend `None`, ce que `collecter` transforme en violation
    — c'est ainsi que la cohorte incomplète devient structurellement impossible.
    """
    manifeste = Manifeste(
        campagne=os.path.basename(os.path.normpath(cohorte)),
        mode="confirmatoire",
        graines=[int(g) for g in graines],
        bras={b: {"dossier": os.path.join(cohorte, b), "prefixe": b} for b in bras},
        alpha=0.05,
        comparaisons_prevues=len(FAMILLE_METRIQUES),
    )
    dp = Depouillement(manifeste, racine=cohorte)
    dp.collecter(lambda chemin: metriques_par_chemin.get(chemin))
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
            etat = PersistanceAnatomique(fichier=chemin).charger_ou_naitre()
            etat.agent.eval()  # jamais d'entraînement, jamais de sauvegarde
            par_carte = {}
            t0 = time.time()
            for index_carte in cartes:
                resultat = evaluer_cerveau_sur_carte(etat, index_carte, graines_eval, max_ticks)
                par_carte[resultat["nom_classe"]] = resultat
                print(f"   ✅ {cle:22s} {resultat['nom_classe']:32s} "
                      f"{resultat['taux']['taux'] * 100:5.1f}% "
                      f"({resultat['gagnes']}/{resultat['taux']['n']}), "
                      f"tronqués {resultat['tronques']}")
            etat.env.close()
            duree = time.time() - t0
            par_cerveau[cle] = {"chemin": chemin, "cartes": par_carte, "duree_s": duree}
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
Attendu : **13 tests OK**.

- [ ] **Étape 5 : commit ciblé avec `bash`**

```bash
git add src/naulthene/instruments/banc_final.py tests/test_banc_final.py && \
git commit -m "feat(EVA-01): rapport de cohorte — refus MES-01, appariement par graine, seuil Bonferroni de la famille de 3"
```

---

### Tâche 6 — Archivage d'`evaluer_cerveau.py`

**Fichiers :**
- Modifier : `src/naulthene/instruments/evaluer_cerveau.py` (bandeau + constante)

**Action :** marquer l'outil comme **archive historique** (précédent exact : `colab.py` / ARC-01) et
corriger `DOSSIER_EVALS_DEFAUT`, qui désigne un dossier **inexistant**.

**Dépendances et interfaces :**
- Consomme : rien.
- Produit : plus aucun outil ne produit son défaut dans un dossier fantôme.

**Critères de succès :**
- `grep -n "docs/notes/evals" src/naulthene/instruments/evaluer_cerveau.py` → **0 occurrence**.
- Le bandeau nomme le successeur (`banc_final.py`) et la raison.
- La suite complète reste verte : **184 tests OK** (156 + 12 + 2 + 10 + 2 + 1 + 1).

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
Attendu : **184 tests OK**.

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
