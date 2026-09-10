# VIS-01 — Le Cerveau 3D : plan d'implémentation

> **Pour les agents d'exécution :** skill obligatoire — utiliser `subagent-driven-development`
> (recommandé) ou `executing-plans` pour exécuter ce plan tâche par tâche. Les étapes emploient
> des cases `- [ ]`.

**Objectif :** rendre le cerveau visible en 3D — ses 12 couches et ses 220 255 synapses allumées
par l'activité réelle — puis brancher cette représentation sur un run en cours, sans jamais le
ralentir ni le modifier.

**Architecture :** un **rapporteur** en lecture seule (`register_forward_hook` sur les 12 couches)
produit trois trames (`structure`, `activite`, `evenement`) ; un **serveur stdlib**
(`ThreadingHTTPServer` + `socket`) les diffuse en **SSE** à une page **three.js vendorisée** ; le
rapporteur publie soit en direct (spectateur-pilote, étape 1), soit par **UDP** depuis un run
séparé (étape 2).

**Stack technique :** Python 3.12 (`venv/bin/python3`), `numpy`, `torch` (déjà présents —
**aucune dépendance ajoutée**) ; `http.server`/`socket`/`json`/`base64` de la bibliothèque
standard ; three.js **v0.180.0 vendorisé** (MIT, aucun CDN au runtime) ; tests `unittest`.

**Spec :** [`docs/ameliorations/CHANTIER_VIS-01_cerveau_3d_irm_vivante.md`](CHANTIER_VIS-01_cerveau_3d_irm_vivante.md)
(validée par l'auteur le 10/09/2026).

## Contraintes globales

- **Lancement** (CLAUDE.md §5/§10) : toujours depuis la racine du dépôt, `PYTHONPATH=src
  venv/bin/python3 -m <module>` — jamais `python fichier.py`, jamais le python système.
- **Imports** : absolus de paquet (`from naulthene.cerveau.telemetrie import ...`).
- **Zéro dépendance ajoutée** : `pyproject.toml` n'est **pas** modifié par ce chantier.
- **Écoute sur `127.0.0.1` uniquement.** Aucun socket ne se bloque jamais côté cerveau.
- **Lecture seule** (étapes 0 et 1) : aucun `backward()`, aucun pas d'optimiseur, aucun appel à
  `persistance.sauvegarder`. **Le fichier `.brain` doit rester bit-identique** (prouvé par
  empreinte SHA-256).
- **Le mode observation ne modifie pas la sortie observée** : un hook de lecture ne retourne
  jamais autre chose que `None` (donc la sortie de la couche est inchangée).
- **Suite de tests** : `NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover
  -s tests` — doit rester **verte**. Durée : ~2 s aujourd'hui (44 tests). ⚠️ Le plan fait passer la
  suite à **~7 s** (deux tests instancient un vrai cerveau, un en fait vivre un pendant 1 s, un
  autre démarre deux serveurs). C'est le prix de contrats réels plutôt que de mocks ; si la durée
  devient gênante, le remède est de **déplacer** ces trois-là dans un module séparé, jamais de les
  supprimer. Les tests du navigateur (`node --check`) sont **ignorés** si `node` est absent
  (`@unittest.skipUnless(shutil.which("node"), …)`) : la suite ne doit dépendre que du venv.
- **En-tête de licence** sur chaque nouveau fichier `.py` :
  `# SPDX-License-Identifier: AGPL-3.0-or-later` + `# Copyright (C) 2026 Adrien Nault — Naulthène AGI`.
- **Commits** : mono-branche `master`, un commit ciblé par tâche, jamais de `--amend`, jamais de
  `push --force`. (⚠️ Aucun commit n'est créé tant que l'auteur ne le demande pas explicitement —
  les étapes de commit ci-dessous sont à exécuter **sur son accord**.)
- **Versionnage** : ✅ **tranché le 10/09/2026** — « le CHANGELOG fait foi ». L'en-tête de
  `noyau.py` est passé de `41.68` à **`41.75`** (dernière entrée du CHANGELOG) et la tête du
  CHANGELOG a été remise en ordre décroissant ; trace : registre **DOC-03**. L'étape 2 (tâche 9)
  touche `noyau.py` et exige donc une entrée CHANGELOG : son numéro sera **le suivant de la
  série après `v41.75`**, arrêté avec l'auteur au moment de l'écrire — la série récente avance
  de +1 par entrée, mais CLAUDE.md §1 annonce d'autres pas selon la nature du changement, et on
  ne devine pas un numéro dans un document normatif.

## Faits mesurés sur lesquels le plan s'appuie (10/09/2026)

Relevés en lecture seule sur `brains/08092026_sci01_balayage_K/K4_NU/K4_NU_g11.brain` :

| Fait | Valeur |
|---|---|
| `dim_bus` d'un cerveau de 1500 jours | **145** |
| Couches | **12**, formes : `porte_visuelle` 147→145 · `hippocampe` 290→145 · `fusion_memoire` 290→145 · `analyseur` 145→145 · `integrateur_bio` **189→145** · `tete_motrice` 145→8 · `cortex_prefrontal` 145→1 · `generateur_attente` 153→145 · `tete_requete` 145→5 · `porte_auditive` 130→145 · `tete_vocale` 145→8 · `generateur_attente_audio` 153→145 |
| Neurones de sortie | **1 182** (dérivé des formes) |
| Synapses | **220 255** (dérivé des formes) |
| `\|trace_activation\|max` | **0,000e+00** sur les 12 couches (⇒ la LTP est numériquement nulle en observation) |
| `three.module.min.js` v0.180.0 | **338 908 octets** |

**Activation appliquée par le cerveau, par couche** (relevée dans `noyau.py` — `_tronc_cerebral`
l. 1082-1125, `lecture_episodique` l. 1131, `integrer_bio` l. 1316, `penser` l. 1351-1626) :
**ReLU** sur `porte_visuelle`, `porte_auditive`, `hippocampe`, `analyseur`, `fusion_memoire`,
`integrateur_bio` ; **sigmoïde** sur `tete_vocale` ; **aucune** sur `tete_motrice`,
`cortex_prefrontal`, `tete_requete`, `generateur_attente`, `generateur_attente_audio`. Le
rapporteur reproduit **exactement** cette table, ni plus ni moins.

---

## Tâche 1 — Le codec : quantification int8 et base64

**Fichiers :**
- Créer : `src/naulthene/cerveau/telemetrie.py`
- Créer : `tests/test_cerveau_3d.py`

**Action :** livrer `quantifier_matrice`, `dequantifier_matrice`, `encoder_octets`,
`decoder_octets` — la compression des matrices de poids (`int8` + échelle par couche) et son
transport texte. Module **feuille** : il n'importe **ni `torch` ni `noyau`** (numpy seulement).

**Dépendances et interfaces :**
- Consomme : rien.
- Produit (signatures exactes, utilisées par les tâches 2, 3, 7, 9) :
  - `quantifier_matrice(m) -> tuple[bytes, float]` — `m` : array-like 2D ; renvoie `(octets int8, échelle)`
  - `dequantifier_matrice(octets: bytes, echelle: float, forme) -> np.ndarray` (float32)
  - `encoder_octets(octets: bytes) -> str` · `decoder_octets(texte: str) -> bytes`

**Critères de succès :**
- L'erreur de quantification ne dépasse jamais `max(|m|) / 254` (+ 1e-9).
- Une matrice nulle donne des octets nuls et une échelle de `1.0` (jamais 0, jamais NaN).
- L'aller-retour base64 est exact.

- [ ] **Étape 1 : écrire le test qui échoue**

Ajouter à `tests/test_cerveau_3d.py` :

```python
#!/usr/bin/env python3
"""VIS-01 — contrats du cerveau 3D (registre VIS-01, spec du 10/09/2026).

Aucune dépendance ajoutée : `http.server`/`socket`/`json` de la bibliothèque standard,
`numpy` déjà requis par le projet ; `torch` est importé UNIQUEMENT par les tests qui
instancient un vrai cerveau.

    NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests
"""
import unittest

import numpy as np


class TestCodecMatrices(unittest.TestCase):
    def test_quantification_respecte_la_borne_d_erreur(self):
        from naulthene.cerveau.telemetrie import quantifier_matrice, dequantifier_matrice
        rng = np.random.default_rng(11)
        m = rng.normal(0.0, 0.05, size=(145, 147)).astype(np.float32)
        octets, echelle = quantifier_matrice(m)
        self.assertEqual(len(octets), m.size)
        retour = dequantifier_matrice(octets, echelle, m.shape)
        erreur_max = float(np.max(np.abs(retour - m)))
        self.assertLessEqual(erreur_max, float(np.max(np.abs(m))) / 254.0 + 1e-9)

    def test_matrice_nulle_donne_echelle_un_et_octets_nuls(self):
        from naulthene.cerveau.telemetrie import quantifier_matrice, dequantifier_matrice
        m = np.zeros((8, 5), dtype=np.float32)
        octets, echelle = quantifier_matrice(m)
        self.assertEqual(echelle, 1.0)
        self.assertEqual(octets, bytes(40))
        self.assertTrue(np.array_equal(dequantifier_matrice(octets, echelle, m.shape), m))

    def test_base64_aller_retour(self):
        from naulthene.cerveau.telemetrie import encoder_octets, decoder_octets
        brut = bytes(range(256))
        self.assertEqual(decoder_octets(encoder_octets(brut)), brut)
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : **`ModuleNotFoundError: No module named 'naulthene.cerveau.telemetrie'`** (3 erreurs) —
l'échec doit venir du module absent, pas d'une faute de frappe dans le test.

- [ ] **Étape 3 : écrire l'implémentation minimale**

Créer `src/naulthene/cerveau/telemetrie.py` :

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — la télémétrie du cerveau 3D : le format des trames, et rien d'autre.

⚠️ FEUILLE : ce module n'importe NI `torch` NI `noyau` (numpy seul). C'est ce qui permet à
`noyau.py` de l'importer à l'étape 2 sans créer de cycle d'import — même motif que
`bus_sensoriel.py`. Il ne connaît ni l'agent ni ses couches : il reçoit des tableaux et des
dictionnaires DÉJÀ extraits, et les met en forme.

Voir `docs/ameliorations/CHANTIER_VIS-01_cerveau_3d_irm_vivante.md` §4 pour le contrat des
trois trames, et `docs/ameliorations/PLAN_VIS-01_cerveau_3d.md` pour l'ordre de livraison.
"""
from __future__ import annotations

import base64
import json

import numpy as np

VERSION_TRAME = 1


def quantifier_matrice(m) -> tuple[bytes, float]:
    """Compresse une matrice de poids en `int8` + une échelle scalaire.

    `echelle = max(|m|) / 127` : la quantification est donc TOUJOURS relative au poids le plus
    fort de la couche, jamais à une constante posée — une couche faible et une couche forte sont
    décrites avec la même résolution relative. L'erreur commise est bornée par `echelle / 2`,
    soit `max(|m|) / 254`.

    Cas dégénéré : une matrice entièrement nulle n'a pas d'échelle définissable — on renvoie des
    octets nuls et `1.0` (et non `0.0`, qui produirait des NaN à la déquantification).
    """
    a = np.asarray(m, dtype=np.float32)
    pic = float(np.max(np.abs(a))) if a.size else 0.0
    if pic <= 0.0:
        return bytes(int(a.size)), 1.0
    echelle = pic / 127.0
    quantifie = np.clip(np.rint(a / echelle), -127.0, 127.0).astype(np.int8)
    return quantifie.tobytes(), echelle


def dequantifier_matrice(octets: bytes, echelle: float, forme) -> np.ndarray:
    """Inverse de `quantifier_matrice` — la seule perte est l'arrondi `int8`."""
    quantifie = np.frombuffer(octets, dtype=np.int8).astype(np.float32)
    return (quantifie * float(echelle)).reshape(tuple(forme))


def encoder_octets(octets: bytes) -> str:
    """Encodes binaires → texte, pour tenir dans un flux JSON (SSE)."""
    return base64.b64encode(octets).decode("ascii")


def decoder_octets(texte: str) -> bytes:
    """Inverse de `encoder_octets` ; `validate=True` refuse un texte corrompu plutôt que de
    rendre des octets silencieusement tronqués."""
    return base64.b64decode(texte.encode("ascii"), validate=True)
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `Ran 3 tests … OK`. Puis la suite complète, qui doit rester verte :
```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests 2>&1 | tail -3
```
Attendu : `Ran 47 tests … OK`.

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite de l'auteur)*

```bash
git add src/naulthene/cerveau/telemetrie.py tests/test_cerveau_3d.py
git commit -m "feat(VIS-01): codec de télémétrie du cerveau 3D — quantification int8 + base64"
```

---

## Tâche 2 — Les trois trames, la disposition spatiale et la forme du cerveau

**Fichiers :**
- Modifier : `src/naulthene/cerveau/telemetrie.py` (ajout)
- Modifier : `tests/test_cerveau_3d.py` (ajout)

**Action :** livrer la mise en forme des trois trames, la **disposition déterministe** des plaques
et la description de la forme du cerveau (12 couches) — les trois éléments dont dépendent le
serveur, la source factice et le rapporteur.

**Dépendances et interfaces :**
- Consomme : tâche 1 (`encoder_octets`).
- Produit :
  - `trame_structure(couches: list[dict], bornes: list[dict], meta: dict) -> dict`
  - `trame_activite(neurones: dict[str, str], scalaires: dict, meta: dict) -> dict`
  - `trame_evenement(genre: str, meta: dict | None = None, **champs) -> dict`
  - `serialiser(trame: dict) -> bytes` · `deserialiser(octets: bytes) -> dict | None`
  - `definir_couches(dim_bus: int) -> list[dict]` — 12 dicts `{"nom", "rang", "entree", "sortie"}`
  - `disposition(couches: list[dict]) -> dict[str, np.ndarray]` — positions `(n, 3)` float32
  - `ACTIVATION_PAR_COUCHE: dict[str, str]` — `"relu"` / `"sigmoide"` / `"aucune"`

**Critères de succès :**
- `definir_couches(145)` reproduit **exactement** les 12 formes mesurées (tableau du haut de ce plan).
- `disposition` est déterministe : deux appels ⇒ `np.array_equal` vrai sur tous les tableaux.
- Chaque trame survit à `serialiser` → `deserialiser` sans perte.
- `deserialiser` renvoie `None` (jamais une exception) sur un datagramme tronqué, non-JSON, ou sans
  clé `type`.

- [ ] **Étape 1 : écrire le test qui échoue**

Ajouter à `tests/test_cerveau_3d.py` :

```python
class TestTramesEtDisposition(unittest.TestCase):
    def test_forme_du_cerveau_a_dim_bus_145(self):
        from naulthene.cerveau.telemetrie import definir_couches
        couches = {c["nom"]: (c["entree"], c["sortie"]) for c in definir_couches(145)}
        self.assertEqual(len(couches), 12)
        self.assertEqual(couches["porte_visuelle"], (147, 145))
        self.assertEqual(couches["hippocampe"], (290, 145))
        self.assertEqual(couches["integrateur_bio"], (189, 145))   # 145 + 44 dims bio
        self.assertEqual(couches["tete_motrice"], (145, 8))
        self.assertEqual(couches["cortex_prefrontal"], (145, 1))
        self.assertEqual(couches["generateur_attente"], (153, 145))
        self.assertEqual(couches["tete_requete"], (145, 5))

    def test_disposition_deterministe(self):
        from naulthene.cerveau.telemetrie import definir_couches, disposition
        couches = definir_couches(16)
        a, b = disposition(couches), disposition(couches)
        self.assertEqual(set(a), set(b))
        for nom in a:
            self.assertTrue(np.array_equal(a[nom], b[nom]), nom)
            self.assertEqual(a[nom].shape, (couches[[c["nom"] for c in couches].index(nom)]["sortie"], 3))

    def test_les_trois_trames_survivent_au_transport(self):
        from naulthene.cerveau.telemetrie import (
            trame_structure, trame_activite, trame_evenement, serialiser, deserialiser)
        s = trame_structure([{"nom": "analyseur", "rang": 2, "entree": 16, "sortie": 16,
                              "echelle": 0.02, "poids_i8": "AAAA"}], [], {"jour": 1, "dim_bus": 16})
        a = trame_activite({"analyseur": "AAAA"}, {"dopamine": 0.3}, {"tick": 7})
        e = trame_evenement("choc_dopamine", {"tick": 7}, intensite=1.0)
        for trame in (s, a, e):
            self.assertEqual(deserialiser(serialiser(trame)), trame)

    def test_datagramme_malforme_ne_leve_jamais(self):
        from naulthene.cerveau.telemetrie import deserialiser
        self.assertIsNone(deserialiser(b"pas du json"))
        self.assertIsNone(deserialiser(b""))
        self.assertIsNone(deserialiser(b'{"sans": "type"}'))
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `ImportError: cannot import name 'definir_couches'` (4 erreurs).

- [ ] **Étape 3 : écrire l'implémentation minimale**

Compléter `src/naulthene/cerveau/telemetrie.py` :

```python
# --- 2. La forme du cerveau et sa disposition (CONVENTION DE LECTURE, spec §5) ---

# L'ordre est celui du FLUX DE DONNÉES, pas une anatomie : Naulthène n'a ni cortex ni lobe.
# Il est déclaré ici une fois pour toutes et identique pour tous les cerveaux — c'est ce qui
# rend deux cerveaux comparables à l'écran.
RANGS = {
    "porte_visuelle": 0, "porte_auditive": 0,
    "hippocampe": 1, "analyseur": 2, "fusion_memoire": 2,
    "integrateur_bio": 3,
    "tete_motrice": 4, "cortex_prefrontal": 4, "tete_vocale": 4, "tete_requete": 4,
    "generateur_attente": 5, "generateur_attente_audio": 5,
}

# L'activation que `penser()` applique APRÈS la couche linéaire (relevé dans noyau.py, voir le
# plan) : le rapporteur applique exactement celle-ci, et rien d'autre. Un hook capture la sortie
# LINÉAIRE ; reproduire l'activation ici est un miroir, pas une réinterprétation.
ACTIVATION_PAR_COUCHE = {
    "porte_visuelle": "relu", "porte_auditive": "relu", "hippocampe": "relu",
    "analyseur": "relu", "fusion_memoire": "relu", "integrateur_bio": "relu",
    "tete_vocale": "sigmoide",
    "tete_motrice": "aucune", "cortex_prefrontal": "aucune", "tete_requete": "aucune",
    "generateur_attente": "aucune", "generateur_attente_audio": "aucune",
}

# Bornes sensorielles et têtes à sortie fixe — valeurs MESURÉES le 10/09/2026 sur un cerveau de
# 1500 jours (K4_NU_g11) ; le rapporteur, lui, les LIT sur l'agent au lieu de les supposer.
DIM_VISUELLE = 147
DIM_AUDIO_ENTREE = 130
DIM_VECTEUR_BIO = 44
NUM_ACTIONS = 8
DIM_ROUTAGE_C3 = 5

ECART_PLAQUES = 1.6    # distance entre deux rangs, sur l'axe Z
PAS_NEURONE = 0.09     # distance entre deux neurones voisins dans une plaque


def definir_couches(dim_bus: int) -> list[dict]:
    """Les 12 couches du cerveau, dans l'ordre de lecture — `(entree, sortie)` par couche.

    ⚠️ Sert de FIXTURE (source factice, tests). Le rapporteur réel ne l'utilise pas : il lit
    `in_features`/`out_features` sur l'agent, ce qui le rend insensible à une erreur ici.
    Un test compare d'ailleurs cette table à un agent neuf (`test_forme_factice_egale_forme_reelle`).
    """
    db = int(dim_bus)
    return [
        {"nom": "porte_visuelle", "rang": 0, "entree": DIM_VISUELLE, "sortie": db},
        {"nom": "porte_auditive", "rang": 0, "entree": DIM_AUDIO_ENTREE, "sortie": db},
        {"nom": "hippocampe", "rang": 1, "entree": 2 * db, "sortie": db},
        {"nom": "analyseur", "rang": 2, "entree": db, "sortie": db},
        {"nom": "fusion_memoire", "rang": 2, "entree": 2 * db, "sortie": db},
        {"nom": "integrateur_bio", "rang": 3, "entree": db + DIM_VECTEUR_BIO, "sortie": db},
        {"nom": "tete_motrice", "rang": 4, "entree": db, "sortie": NUM_ACTIONS},
        {"nom": "cortex_prefrontal", "rang": 4, "entree": db, "sortie": 1},
        {"nom": "tete_vocale", "rang": 4, "entree": db, "sortie": 8},
        {"nom": "tete_requete", "rang": 4, "entree": db, "sortie": DIM_ROUTAGE_C3},
        {"nom": "generateur_attente", "rang": 5, "entree": NUM_ACTIONS + db, "sortie": db},
        {"nom": "generateur_attente_audio", "rang": 5, "entree": NUM_ACTIONS + db, "sortie": db},
    ]


def disposition(couches: list[dict]) -> dict:
    """Positions `(n, 3)` de chaque neurone de SORTIE : une plaque par couche, sur un plan XY,
    empilée sur Z selon le rang. Grille régulière ⇒ **déterministe** (mêmes entrées, mêmes
    positions à l'octet), donc deux cerveaux se superposent exactement.
    """
    positions = {}
    for couche in couches:
        n = int(couche["sortie"])
        colonnes = max(1, int(np.ceil(np.sqrt(n))))
        lignes = int(np.ceil(n / colonnes))
        pts = np.zeros((n, 3), dtype=np.float32)
        for i in range(n):
            col, lig = i % colonnes, i // colonnes
            pts[i, 0] = (col - (colonnes - 1) / 2.0) * PAS_NEURONE
            pts[i, 1] = (lig - (lignes - 1) / 2.0) * PAS_NEURONE
            pts[i, 2] = float(couche["rang"]) * ECART_PLAQUES
        positions[couche["nom"]] = pts
    return positions


# --- 3. Les trois trames ---

def trame_structure(couches: list[dict], bornes: list[dict], meta: dict) -> dict:
    """`couches` : `{nom, rang, entree, sortie, echelle, poids_i8, positions}` — les matrices
    DÉJÀ quantifiées, et les positions DÉJÀ calculées par `disposition()` (`float16` n×3 encodé
    base64) : c'est le serveur qui calcule la géométrie, jamais le navigateur, pour que la
    disposition reste **une seule fois** définie (Python) et identique partout ·
    `bornes` : `{nom, dim, couche, rang_entree}` (vision, audio, vecteur bio, actions) ·
    `meta` : `{jour, tick_absolu, dim_bus, niveau}`."""
    return {"type": "structure", "version": VERSION_TRAME,
            "couches": couches, "bornes": bornes, **meta}


def trame_activite(neurones: dict, scalaires: dict, meta: dict) -> dict:
    """`neurones` : `{nom_couche: octets float16 encodés base64}` (déjà encodés, cf. tâche 7) ·
    `scalaires` : dopamine, faim, force_planification, action… · `meta` : `{jour, tick_absolu}`."""
    return {"type": "activite", "version": VERSION_TRAME,
            "neurones": neurones, "scalaires": scalaires, **meta}


def trame_evenement(genre: str, meta: dict | None = None, **champs) -> dict:
    """Un fait daté, pas une mesure continue : choc dopaminergique, victoire, neurogenèse."""
    return {"type": "evenement", "version": VERSION_TRAME, "genre": genre,
            **(meta or {}), **champs}


def serialiser(trame: dict) -> bytes:
    """JSON compact — la trame d'activité part 15 fois par seconde, chaque octet compte."""
    return json.dumps(trame, separators=(",", ":")).encode("utf-8")


def deserialiser(octets: bytes) -> dict | None:
    """`None` sur tout ce qui n'est pas une trame exploitable — jamais une exception : un
    datagramme tronqué ne doit pas tuer la boucle d'écoute (spec §9)."""
    try:
        trame = json.loads(octets.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(trame, dict) or "type" not in trame:
        return None
    return trame
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `Ran 7 tests … OK`, puis `Ran 51 tests … OK` pour la suite complète.

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite)*

```bash
git add src/naulthene/cerveau/telemetrie.py tests/test_cerveau_3d.py
git commit -m "feat(VIS-01): trames structure/activite/evenement + disposition déterministe"
```

---

## Tâche 3 — Le bus borné et l'émetteur UDP non bloquant

**Fichiers :**
- Modifier : `src/naulthene/cerveau/telemetrie.py`
- Modifier : `tests/test_cerveau_3d.py`

**Action :** livrer `BusTrames` (la mémoire tampon qui ne garde **que la dernière** activité) et
`EmetteurUDP` (l'envoi qui ne bloque jamais le cerveau).

**Dépendances et interfaces :**
- Consomme : tâche 2 (`serialiser`).
- Produit :
  - `BusTrames(taille_evenements: int = 32)` avec `.publier_structure(t)`, `.publier_activite(t)`,
    `.publier_evenement(t)`, `.structure()`, `.activite()`, `.sequence`, `.evenements_depuis(index)`,
    `.compteurs()`
  - `EmetteurUDP(cible: str)` avec `.envoyer(trame) -> bool`, `.fermer()`, `.compteurs()`
  - `analyser_cible_udp(cible: str) -> tuple[str, int]`

**Critères de succès :**
- Publier 3 activités ⇒ `activite()` renvoie la **3ᵉ** et `sequence == 3` (les intermédiaires sont
  perdues : on montre le présent, jamais du retard).
- 40 événements publiés dans une file de 32 ⇒ `evenements_depuis(0)` renvoie au plus 32 trames et
  le total vaut 40.
- Envoyer vers un port fermé ne lève **jamais** et n'écrase aucune exception silencieusement
  (compteur `perdues`).
- Deux `EmetteurUDP` côte à côte : ce que l'un envoie, un socket d'écoute le reçoit **à l'octet**.

- [ ] **Étape 1 : écrire le test qui échoue**

```python
class TestBusEtEmetteur(unittest.TestCase):
    def test_le_bus_ne_garde_que_la_derniere_activite(self):
        from naulthene.cerveau.telemetrie import BusTrames, trame_activite
        bus = BusTrames()
        for tick in (1, 2, 3):
            bus.publier_activite(trame_activite({}, {"tick": tick}, {"tick": tick}))
        self.assertEqual(bus.activite()["scalaires"]["tick"], 3)
        self.assertEqual(bus.sequence, 3)

    def test_file_d_evenements_bornee(self):
        from naulthene.cerveau.telemetrie import BusTrames, trame_evenement
        bus = BusTrames(taille_evenements=32)
        for i in range(40):
            bus.publier_evenement(trame_evenement("choc_dopamine", {"tick": i}))
        nouveaux, total = bus.evenements_depuis(0)
        self.assertEqual(total, 40)
        self.assertEqual(len(nouveaux), 32)
        self.assertEqual(nouveaux[-1]["tick"], 39)

    def test_cible_udp_invalide_refusee_au_demarrage(self):
        from naulthene.cerveau.telemetrie import analyser_cible_udp
        self.assertEqual(analyser_cible_udp("udp:127.0.0.1:9998"), ("127.0.0.1", 9998))
        for mauvaise in ("127.0.0.1:9998", "udp:127.0.0.1", "tcp:1.2.3.4:5"):
            with self.assertRaises(ValueError):
                analyser_cible_udp(mauvaise)

    def test_emetteur_livre_les_octets_et_ne_bloque_jamais(self):
        import socket as sock
        from naulthene.cerveau.telemetrie import EmetteurUDP, trame_evenement, serialiser
        ecoute = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        ecoute.bind(("127.0.0.1", 0))
        ecoute.settimeout(2.0)
        port = ecoute.getsockname()[1]
        emetteur = EmetteurUDP(f"udp:127.0.0.1:{port}")
        trame = trame_evenement("victoire", {"tick": 5})
        self.assertTrue(emetteur.envoyer(trame))
        recu, _ = ecoute.recvfrom(65535)
        self.assertEqual(recu, serialiser(trame))
        emetteur.fermer()
        ecoute.close()

    def test_envoi_vers_port_ferme_est_perdu_sans_exception(self):
        from naulthene.cerveau.telemetrie import EmetteurUDP, trame_evenement
        emetteur = EmetteurUDP("udp:127.0.0.1:1")   # port réservé, rien n'écoute
        for _ in range(3):
            emetteur.envoyer(trame_evenement("choc_dopamine", {"tick": 1}))
        self.assertGreaterEqual(emetteur.compteurs()["envoyees"] + emetteur.compteurs()["perdues"], 3)
        emetteur.fermer()
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `ImportError: cannot import name 'BusTrames'` (5 erreurs).

- [ ] **Étape 3 : écrire l'implémentation minimale**

```python
# --- 4. Le bus borné (le présent, jamais du retard) et l'émetteur non bloquant ---

TAILLE_FILE_EVENEMENTS = 32


class BusTrames:
    """Le point de rendez-vous entre qui produit les trames et qui les sert.

    Choix assumé (spec §9) : l'activité n'est PAS une file — seule la DERNIÈRE trame est gardée.
    Si le serveur ou le navigateur prend du retard, on saute des images plutôt que d'accumuler
    du passé : on regarde un cerveau vivant, pas un enregistrement.
    """

    def __init__(self, taille_evenements: int = TAILLE_FILE_EVENEMENTS):
        self._verrou = threading.Lock()
        self._structure = None
        self._activite = None
        self._evenements = deque(maxlen=int(taille_evenements))
        self._sequence = 0
        self._evenements_total = 0

    def publier_structure(self, trame: dict) -> None:
        with self._verrou:
            self._structure = trame

    def publier_activite(self, trame: dict) -> None:
        with self._verrou:
            self._activite = trame
            self._sequence += 1

    def publier_evenement(self, trame: dict) -> None:
        with self._verrou:
            self._evenements.append(trame)
            self._evenements_total += 1

    @property
    def sequence(self) -> int:
        with self._verrou:
            return self._sequence

    def structure(self):
        with self._verrou:
            return self._structure

    def activite(self):
        with self._verrou:
            return self._activite

    def evenements_depuis(self, index: int) -> tuple[list, int]:
        """`index` = valeur précédente de `compteurs()["evenements_total"]`. Renvoie les
        événements encore en file après cet index, et le nouveau total."""
        with self._verrou:
            total = self._evenements_total
            en_file = list(self._evenements)
        manquants = total - len(en_file)
        return en_file[max(0, index - manquants):], total

    def compteurs(self) -> dict:
        with self._verrou:
            return {"sequence": self._sequence,
                    "evenements_total": self._evenements_total,
                    "evenements_en_file": len(self._evenements)}


def analyser_cible_udp(cible: str) -> tuple:
    """`"udp:hote:port"` → `(hote, port)`. Une cible mal formée est une ERREUR DE CONFIGURATION :
    elle doit planter au démarrage, pas produire un silence qu'on prendrait pour un cerveau lent.
    """
    morceaux = str(cible).split(":")
    if len(morceaux) != 3 or morceaux[0] != "udp":
        raise ValueError(f"cible de télémétrie invalide : {cible!r} (attendu « udp:hote:port »)")
    return morceaux[1], int(morceaux[2])


class EmetteurUDP:
    """Envoie une trame sans jamais attendre. Toute erreur ⇒ trame PERDUE, comptée, jamais une
    exception qui remonterait dans la boucle du cerveau."""

    def __init__(self, cible: str):
        self._adresse = analyser_cible_udp(cible)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        self._envoyees, self._perdues = 0, 0

    def envoyer(self, trame: dict) -> bool:
        try:
            self._socket.sendto(serialiser(trame), self._adresse)
        except (OSError, ValueError):
            self._perdues += 1
            return False
        self._envoyees += 1
        return True

    def fermer(self) -> None:
        try:
            self._socket.close()
        except OSError:
            pass

    def compteurs(self) -> dict:
        return {"envoyees": self._envoyees, "perdues": self._perdues,
                "cible": f"{self._adresse[0]}:{self._adresse[1]}"}
```

Et compléter les imports en tête de `telemetrie.py` :

```python
import socket
import threading
from collections import deque
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `Ran 12 tests … OK`, puis `Ran 56 tests … OK`.

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite)*

```bash
git add src/naulthene/cerveau/telemetrie.py tests/test_cerveau_3d.py
git commit -m "feat(VIS-01): bus borné (dernière trame) + émetteur UDP non bloquant"
```

---

## Tâche 4 — Le serveur : page statique, `/structure` et flux SSE

**Fichiers :**
- Créer : `src/naulthene/instruments/cerveau_3d/__init__.py` (vide, avec l'en-tête de licence)
- Créer : `src/naulthene/instruments/cerveau_3d/serveur.py`
- Modifier : `tests/test_cerveau_3d.py`

**Action :** livrer le serveur HTTP local qui sert la page et pousse les trois canaux en SSE, plus
l'écoute UDP qui alimente le bus depuis un run extérieur.

**Dépendances et interfaces :**
- Consomme : tâches 2 et 3 (`BusTrames`, `deserialiser`).
- Produit :
  - `ServeurCerveau3D(bus, port=8770, hote="127.0.0.1", dossier_statique=None)` avec
    `.demarrer_en_thread() -> threading.Thread`, `.port` (port réellement lié), `.arreter()`
  - `EcouteurUDP(bus, port, hote="127.0.0.1")` avec `.demarrer_en_thread()`, `.arreter()`,
    `.compteurs()`
  - Routes : `GET /` · `GET /app.js` · `GET /three.module.js` · `GET /structure` ·
    `GET /flux` (SSE) · `GET /sante`

**Critères de succès :**
- `GET /flux` émet d'abord `event: structure` puis des `event: activite` — un client lit les
  trames sans jamais bloquer le serveur.
- Un datagramme malformé reçu par l'écouteur **n'interrompt pas** la réception (compté, ignoré).
- `port=0` ⇒ le serveur lie un port libre et l'expose dans `.port` (indispensable aux tests).

- [ ] **Étape 1 : écrire le test qui échoue**

```python
class TestServeur(unittest.TestCase):
    def _client_sse(self, port, nb_lignes=12):
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/flux", timeout=5) as reponse:
            lignes = []
            for ligne in reponse:
                lignes.append(ligne.decode("utf-8").rstrip())
                if len(lignes) >= nb_lignes:
                    break
        return lignes

    def test_structure_et_flux_sse(self):
        import json
        import threading
        import time
        import urllib.request
        from naulthene.cerveau.telemetrie import (BusTrames, trame_structure, trame_activite)
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        bus = BusTrames()
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}/structure") as r:
                self.assertEqual(json.loads(r.read())["dim_bus"], 16)
            bus.publier_activite(trame_activite({}, {"tick": 1}, {"tick": 1}))
            lignes = self._client_sse(serveur.port)
            self.assertIn("event: structure", lignes)
            self.assertTrue(any(l.startswith("event: activite") for l in lignes))
        finally:
            serveur.arreter()

    def test_datagramme_malforme_ignore_puis_trame_valide_acceptee(self):
        import socket as sock
        import time
        from naulthene.cerveau.telemetrie import BusTrames, trame_activite
        from naulthene.instruments.cerveau_3d.serveur import EcouteurUDP

        bus = BusTrames()
        ecouteur = EcouteurUDP(bus, port=0)
        ecouteur.demarrer_en_thread()
        try:
            emetteur = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
            emetteur.sendto(b"pas du json", ("127.0.0.1", ecouteur.port))
            emetteur.sendto(b'{"sans": "type"}', ("127.0.0.1", ecouteur.port))
            time.sleep(0.4)
            self.assertIsNone(bus.activite())
            emetteur.sendto(serialiser(trame_activite({}, {"tick": 9}, {"tick": 9})),
                            ("127.0.0.1", ecouteur.port))
            limite = time.time() + 3.0
            while bus.activite() is None and time.time() < limite:
                time.sleep(0.05)
            self.assertEqual(bus.activite()["tick"], 9)
            self.assertGreaterEqual(ecouteur.compteurs()["ignorees"], 2)
            emetteur.close()
        finally:
            ecouteur.arreter()
```

(`serialiser` est importé en tête du fichier de test dans cette tâche.)

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `ModuleNotFoundError: No module named 'naulthene.instruments.cerveau_3d'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

Créer `src/naulthene/instruments/cerveau_3d/serveur.py` (extrait ; le fichier complet fait ~150
lignes) :

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — le serveur du cerveau 3D : sert la page, pousse les trames, écoute l'UDP.

⚠️ Bibliothèque standard UNIQUEMENT (`http.server`, `socket`, `json`, `base64`) : aucune
dépendance n'est ajoutée au projet (spec §3). Le serveur ne connaît pas le cerveau : il ne
connaît que le `BusTrames` qu'on lui donne.

⚠️ Ne PAS activer HTTP/1.1 : le flux SSE n'a ni `Content-Length` ni `chunked`, et un client
HTTP/1.1 attendrait une fin de corps qui n'arrive jamais. En HTTP/1.0 (défaut), le corps se
termine à la fermeture de la connexion — exactement ce qu'est un flux continu.
"""
from __future__ import annotations

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from naulthene.cerveau.telemetrie import deserialiser

TAILLE_MAX_DATAGRAMME = 65535       # plafond théorique d'un datagramme UDP
CADENCE_SSE = 0.05                  # 20 Hz de vérification ; le throttle réel est côté rapporteur


class ServeurCerveau3D:
    """Sert la page 3D et pousse les trames en SSE."""

    def __init__(self, bus, port=8770, hote="127.0.0.1", dossier_statique=None):
        self.bus = bus
        self.hote = hote
        self.dossier_statique = Path(dossier_statique or (Path(__file__).parent / "static"))
        self._serveur = ThreadingHTTPServer((hote, int(port)), self._fabriquer_gestionnaire())
        self._serveur.daemon_threads = True
        self.port = self._serveur.server_address[1]   # port RÉEL : `port=0` en choisit un libre
        self._arret = threading.Event()
        self._fil = None

    def _fabriquer_gestionnaire(self):
        serveur = self

        class Gestionnaire(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass   # pas de bruit dans la console d'un run en cours

            def do_GET(self):
                chemin = urlsplit(self.path).path
                if chemin == "/":
                    return self._fichier("index.html", "text/html; charset=utf-8")
                if chemin in ("/app.js", "/three.module.js"):
                    return self._fichier(chemin.lstrip("/"), "text/javascript; charset=utf-8")
                if chemin == "/structure":
                    return self._json(serveur.bus.structure() or {})
                if chemin == "/sante":
                    return self._json({"bus": serveur.bus.compteurs()})
                if chemin == "/flux":
                    return self._flux()
                self.send_error(404)

            def _fichier(self, nom, type_mime):
                fichier = serveur.dossier_statique / nom
                if not fichier.is_file():
                    return self.send_error(404, f"{nom} absent du dossier statique")
                donnees = fichier.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", type_mime)
                self.send_header("Content-Length", str(len(donnees)))
                self.end_headers()
                self.wfile.write(donnees)

            def _json(self, charge):
                donnees = json.dumps(charge, separators=(",", ":")).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(donnees)))
                self.end_headers()
                self.wfile.write(donnees)

            def _flux(self):
                """SSE : la structure d'abord (le client peut se dessiner), puis chaque nouvelle
                activité. Un navigateur qui ferme l'onglet casse le `write` — on sort sans bruit,
                le cerveau n'en sait rien."""
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()

                    derniere_sequence = -1
                    dernier_evenement = 0
                    while not serveur._arret.is_set():
                        structure = serveur.bus.structure()
                        if structure is not None:
                            self._evenement_sse("structure", structure)
                            break
                        time.sleep(CADENCE_SSE)

                    while not serveur._arret.is_set():
                        if serveur.bus.sequence != derniere_sequence:
                            activite = serveur.bus.activite()
                            if activite is not None:
                                derniere_sequence = serveur.bus.sequence
                                self._evenement_sse("activite", activite)
                        nouveaux, dernier_evenement = serveur.bus.evenements_depuis(dernier_evenement)
                        for evenement in nouveaux:
                            self._evenement_sse("evenement", evenement)
                        time.sleep(CADENCE_SSE)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return

            def _evenement_sse(self, nom, charge):
                corps = f"event: {nom}\ndata: {json.dumps(charge, separators=(',', ':'))}\n\n"
                self.wfile.write(corps.encode("utf-8"))
                self.wfile.flush()

        return Gestionnaire

    def demarrer_en_thread(self):
        self._fil = threading.Thread(target=self._serveur.serve_forever,
                                     name="serveur-cerveau-3d", daemon=True)
        self._fil.start()
        return self._fil

    def arreter(self):
        self._arret.set()
        self._serveur.shutdown()
        self._serveur.server_close()
        if self._fil is not None:
            self._fil.join(timeout=2.0)


class EcouteurUDP:
    """Reçoit les trames d'un run extérieur (étape 2). Un datagramme illisible est COMPTÉ et
    ignoré : la boucle d'écoute ne meurt jamais d'une entrée malformée (spec §9)."""

    def __init__(self, bus, port=9998, hote="127.0.0.1"):
        self.bus = bus
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((hote, int(port)))
        self._socket.settimeout(0.2)     # pour pouvoir s'arrêter proprement
        self.port = self._socket.getsockname()[1]
        self._arret = threading.Event()
        self._recues, self._ignorees = 0, 0
        self._fil = None

    def _boucle(self):
        while not self._arret.is_set():
            try:
                octets, _ = self._socket.recvfrom(TAILLE_MAX_DATAGRAMME)
            except socket.timeout:
                continue
            except OSError:
                break
            trame = deserialiser(octets)
            if trame is None:
                self._ignorees += 1
                continue
            self._recues += 1
            genre = trame.get("type")
            if genre == "structure":
                self.bus.publier_structure(trame)
            elif genre == "activite":
                self.bus.publier_activite(trame)
            elif genre == "evenement":
                self.bus.publier_evenement(trame)

    def demarrer_en_thread(self):
        self._fil = threading.Thread(target=self._boucle, name="ecouteur-udp", daemon=True)
        self._fil.start()
        return self._fil

    def arreter(self):
        self._arret.set()
        if self._fil is not None:
            self._fil.join(timeout=2.0)
        try:
            self._socket.close()
        except OSError:
            pass

    def compteurs(self):
        return {"recues": self._recues, "ignorees": self._ignorees, "port": self.port}
```

Et créer `src/naulthene/instruments/cerveau_3d/__init__.py` :

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""VIS-01 — le cerveau 3D (instrument de visualisation, lecture seule)."""
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `Ran 14 tests … OK` en moins de 10 s (deux serveurs éphémères), puis `Ran 58 tests … OK`.

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite)*

```bash
git add src/naulthene/instruments/cerveau_3d/ tests/test_cerveau_3d.py
git commit -m "feat(VIS-01): serveur stdlib (page, /structure, flux SSE) + écoute UDP tolérante"
```

---

## Tâche 5 — La page three.js et le vendor

**Fichiers :**
- Créer : `src/naulthene/instruments/cerveau_3d/static/index.html`
- Créer : `src/naulthene/instruments/cerveau_3d/static/app.js`
- Créer : `src/naulthene/instruments/cerveau_3d/static/three.module.js` (**vendorisé**)
- Créer : `src/naulthene/instruments/cerveau_3d/static/LICENSE-three.txt`
- Modifier : `tests/test_cerveau_3d.py`

**Action :** la scène 3D : une sphère par neurone (InstancedMesh), une arête par synapse sous
seuil (LineSegments), les couleurs du §5 de la spec, et un curseur de seuil.

**Dépendances et interfaces :**
- Consomme : les trames (tâches 2-4) et l'API SSE `/flux`, `/structure`.
- Produit : rien pour le Python — la page consomme le contrat de la tâche 2 (**aucun changement de
  format sans mettre à jour les deux côtés**).

**Critères de succès :**
- `node --check app.js` sort **0** (le fichier est du JavaScript valide).
- La page est servie en `text/html`, `app.js` et `three.module.js` en `text/javascript`.
- Le vendor est **pinné** : `three.module.js` = 338 908 octets (v0.180.0 minifié), licence MIT
  présente à côté.
- **Vérification visuelle** : ouvrir `http://127.0.0.1:8770` sur la source factice ⇒ 12 plaques +
  une colonne centrale, neurones qui s'allument, curseur de seuil qui change le nombre d'arêtes.

- [ ] **Étape 1 : écrire le test qui échoue**

```python
class TestPageEtVendor(unittest.TestCase):
    def test_fichiers_statiques_presents(self):
        from pathlib import Path
        statique = Path("src/naulthene/instruments/cerveau_3d/static")
        for nom in ("index.html", "app.js", "three.module.js", "LICENSE-three.txt"):
            self.assertTrue((statique / nom).is_file(), nom)
        self.assertEqual((statique / "three.module.js").stat().st_size, 338908)

    @unittest.skipUnless(shutil.which("node"), "node absent : la page n'est pas vérifiée")
    def test_app_js_est_du_javascript_valide(self):
        import subprocess
        resultat = subprocess.run(["node", "--check",
                                   "src/naulthene/instruments/cerveau_3d/static/app.js"],
                                  capture_output=True, text=True)
        self.assertEqual(resultat.returncode, 0, resultat.stderr)

    def test_index_reference_le_module_et_le_vendor(self):
        page = open("src/naulthene/instruments/cerveau_3d/static/index.html").read()
        self.assertIn("./app.js", page)
        self.assertIn("./three.module.js", page)
```

(`import shutil` est ajouté en tête du fichier de test dans cette tâche.)

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `AssertionError: index.html` (le dossier `static/` n'existe pas).

- [ ] **Étape 3 : écrire la page et vendoriser three.js**

```bash
mkdir -p src/naulthene/instruments/cerveau_3d/static
curl -sL --max-time 60 https://unpkg.com/three@0.180.0/build/three.module.min.js \
     -o src/naulthene/instruments/cerveau_3d/static/three.module.js
curl -sL --max-time 60 https://unpkg.com/three@0.180.0/LICENSE \
     -o src/naulthene/instruments/cerveau_3d/static/LICENSE-three.txt
stat -f "%z octets" src/naulthene/instruments/cerveau_3d/static/three.module.js
```
Attendu : `338908 octets`. Si le nombre diffère, **corriger le test** — c'est la version vendorisée
qui fait foi, pas l'inverse.

Puis écrire les deux fichiers de la page.

`index.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Naulthène — le cerveau 3D (VIS-01)</title>
  <style>
    html, body { margin: 0; height: 100%; background: #0b0b12; color: #e6e6eb;
                 font: 13px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; overflow: hidden; }
    #panneau { position: fixed; top: 10px; left: 10px; background: #14141ecc; padding: 10px 12px;
               border: 1px solid #2a2a3a; border-radius: 8px; max-width: 330px; }
    #panneau b { color: #ffc83c; }
    #seuil { width: 100%; }
    #infos { margin-top: 6px; color: #9a9aa8; }
    #etat { position: fixed; bottom: 10px; left: 10px; color: #9a9aa8; }
  </style>
</head>
<body>
  <div id="panneau">
    <div>🧠 <b>Naulthène</b> — IRM 3D <span id="source"></span></div>
    <div id="structure">en attente de la structure…</div>
    <hr>
    <label>Seuil d'affichage des synapses : <span id="valeur-seuil">0.15</span></label>
    <input id="seuil" type="range" min="0" max="100" value="15">
    <div id="infos">…</div>
  </div>
  <div id="etat">connexion…</div>
  <script type="module" src="./app.js"></script>
</body>
</html>
```

`app.js` :

```js
// VIS-01 — la scène 3D du cerveau. Contrat : spec §4 (trames) et §5 (encodage visuel).
import * as THREE from './three.module.js';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0b12);
const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.1, 500);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(devicePixelRatio);
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff, 0.75));
const lumiere = new THREE.DirectionalLight(0xffffff, 1.1);
lumiere.position.set(6, 9, 8);
scene.add(lumiere);

// Caméra orbitale minimale (pas d'OrbitControls : trois lignes suffisent et évitent un import).
const vue = { theta: 0.8, phi: 1.15, distance: 26, cible: new THREE.Vector3(0, 0, 4) };
let souris = null;
renderer.domElement.addEventListener('pointerdown', e => { souris = { x: e.clientX, y: e.clientY }; });
addEventListener('pointerup', () => { souris = null; });
addEventListener('pointermove', e => {
  if (!souris) return;
  vue.theta -= (e.clientX - souris.x) * 0.006;
  vue.phi = Math.max(0.15, Math.min(Math.PI - 0.15, vue.phi - (e.clientY - souris.y) * 0.006));
  souris = { x: e.clientX, y: e.clientY };
});
renderer.domElement.addEventListener('wheel', e => {
  vue.distance = Math.max(3, Math.min(120, vue.distance * (1 + Math.sign(e.deltaY) * 0.1)));
}, { passive: true });

function majCamera() {
  camera.position.set(
    vue.cible.x + vue.distance * Math.sin(vue.phi) * Math.cos(vue.theta),
    vue.cible.y + vue.distance * Math.cos(vue.phi),
    vue.cible.z + vue.distance * Math.sin(vue.phi) * Math.sin(vue.theta));
  camera.lookAt(vue.cible);
}

// --- Décodage : les trames transportent du base64 (float16 pour l'activité, int8 pour les poids).
function base64EnOctets(texte) {
  return Uint8Array.from(atob(texte), c => c.charCodeAt(0));
}
function float16VersFloat32(octets) {
  const sortie = new Float32Array(octets.length / 2);
  const vue16 = new DataView(octets.buffer, octets.byteOffset, octets.byteLength);
  for (let i = 0; i < sortie.length; i++) sortie[i] = vue16.getFloat16(i * 2);
  return sortie;
}

const noeuds = { maillage: null, couches: [] };   // InstancedMesh des neurones
const aretes = { lignes: null, paires: [] };      // LineSegments des synapses affichées
let seuil = 0.15;

// Couleur d'un neurone : du gris sourd (mort) au jaune vif (actif), §5 de la spec.
const couleur = new THREE.Color();
function couleurActivation(valeur, maximum) {
  const t = maximum > 0 ? Math.min(1, valeur / maximum) : 0;
  return couleur.setRGB(0.12 + 0.88 * t, 0.12 + 0.72 * t * t, 0.16 + 0.2 * t);
}

function construireStructure(trame) {
  if (noeuds.maillage) { scene.remove(noeuds.maillage); noeuds.maillage.dispose(); }
  if (aretes.lignes) { scene.remove(aretes.lignes); aretes.lignes.geometry.dispose(); }

  const couches = trame.couches;
  const total = couches.reduce((n, c) => n + c.sortie, 0);
  const geometrie = new THREE.SphereGeometry(0.035, 8, 6);
  const materiau = new THREE.MeshLambertMaterial({ vertexColors: false });
  noeuds.maillage = new THREE.InstancedMesh(geometrie, materiau, total);

  const matrice = new THREE.Matrix4();
  const positions = [];
  let index = 0;
  for (const couche of couches) {
    const pts = float16VersFloat32(base64EnOctets(couche.positions));
    const debut = index;
    for (let i = 0; i < couche.sortie; i++, index++) {
      positions.push([pts[i * 3], pts[i * 3 + 1], pts[i * 3 + 2]]);
      matrice.makeTranslation(pts[i * 3], pts[i * 3 + 1], pts[i * 3 + 2]);
      noeuds.maillage.setMatrixAt(index, matrice);
      noeuds.maillage.setColorAt(index, couleur.setRGB(0.15, 0.15, 0.18));
    }
    couche._debut = debut;
  }
  noeuds.couches = couches;
  noeuds.maillage.instanceMatrix.needsUpdate = true;
  scene.add(noeuds.maillage);
  noeuds.positions = positions;

  construireAretes();
  document.getElementById('structure').textContent =
    `${couches.length} couches · ${total} neurones · ${aretes.paires.length} synapses affichées`;
}

// Arêtes : toutes les paires (sortie de la couche A → entrée consommée dans la couche B) dont le
// poids dépasse le seuil. La topologie est DENSE et implicite (§4 de la spec) : ce sont les poids
// quantifiés qui décident de ce qu'on voit.
function construireAretes() {
  const paires = [];
  for (const couche of noeuds.couches) {
    const poids = base64EnOctets(couche.poids_i8);
    const echelle = couche.echelle;
    for (let o = 0; o < couche.sortie; o++) {
      for (let i = 0; i < couche.entree; i++) {
        const valeur = Math.abs((poids[o * couche.entree + i] << 24 >> 24) * echelle);
        if (valeur >= seuil) paires.push([couche._debut + o, couche.nom, i, valeur]);
      }
    }
  }
  aretes.paires = paires;
  if (aretes.lignes) { scene.remove(aretes.lignes); aretes.lignes.geometry.dispose(); }
  const sommets = new Float32Array(paires.length * 6);
  aretes.lignes = new THREE.LineSegments(
    new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(sommets, 3)),
    new THREE.LineBasicMaterial({ color: 0x3a5a8a, transparent: true, opacity: 0.35 }));
  scene.add(aretes.lignes);
  rafraichirAretes();
}

function rafraichirAretes() {
  const attribut = aretes.lignes.geometry.getAttribute('position');
  const tableau = attribut.array;
  for (let k = 0; k < aretes.paires.length; k++) {
    const [indiceNoeud] = aretes.paires[k];
    const a = noeuds.positions[indiceNoeud];
    const b = noeuds.positions[indiceNoeud];   // extrémité : centre de la plaque suivante
    tableau[k * 6 + 0] = a[0]; tableau[k * 6 + 1] = a[1]; tableau[k * 6 + 2] = a[2];
    tableau[k * 6 + 3] = b[0]; tableau[k * 6 + 4] = b[1]; tableau[k * 6 + 5] = b[2];
  }
  attribut.needsUpdate = true;
}

function appliquerActivite(trame) {
  let maximum = 1e-6;
  const parCouche = {};
  for (const couche of noeuds.couches) {
    const valeurs = float16VersFloat32(base64EnOctets(trame.neurones[couche.nom]));
    parCouche[couche.nom] = valeurs;
    for (const v of valeurs) maximum = Math.max(maximum, v);
  }
  for (const couche of noeuds.couches) {
    const valeurs = parCouche[couche.nom];
    for (let i = 0; i < valeurs.length; i++) {
      noeuds.maillage.setColorAt(couche._debut + i, couleurActivation(valeurs[i], maximum));
    }
  }
  noeuds.maillage.instanceColor.needsUpdate = true;
  const s = trame.scalaires || {};
  document.getElementById('infos').textContent =
    `jour ${trame.jour} · tick ${trame.tick} · dopamine ${(s.dopamine ?? 0).toFixed(3)}` +
    ` · planification ${(s.force_planification ?? 0).toFixed(2)} · action ${s.action ?? '—'}`;
}

// --- Le flux : un seul canal, trois types d'événements (§4 de la spec).
const flux = new EventSource('/flux');
flux.addEventListener('structure', e => construireStructure(JSON.parse(e.data)));
flux.addEventListener('activite', e => appliquerActivite(JSON.parse(e.data)));
flux.addEventListener('evenement', e => {
  const evenement = JSON.parse(e.data);
  document.getElementById('etat').textContent = `⚡ ${evenement.genre} (tick ${evenement.tick})`;
});
flux.onopen = () => { document.getElementById('etat').textContent = 'flux connecté'; };
flux.onerror = () => { document.getElementById('etat').textContent = 'flux interrompu — reconnexion…'; };

const curseur = document.getElementById('seuil');
curseur.addEventListener('input', () => {
  seuil = Number(curseur.value) / 100;
  document.getElementById('valeur-seuil').textContent = seuil.toFixed(2);
  if (noeuds.couches.length) { construireAretes(); }
});

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

(function animer() {
  requestAnimationFrame(animer);
  majCamera();
  renderer.render(scene, camera);
})();
```

⚠️ **Deux points à traiter à l'implémentation, écrits ici pour ne pas les découvrir à l'exécution :**
1. `rafraichirAretes` doit relier un neurone de sortie au neurone **d'entrée** consommé — l'extrémité
   dépend de la façon dont `entree` se décompose (bus, dims bio, actions). La version minimale relie
   deux plaques voisines ; la version fidèle utilise la table des **bornes** du canal `structure`.
   Le critère de succès ne change pas : **le seuil doit changer visiblement le nombre d'arêtes**.
2. `getFloat16` sur `DataView` nécessite un navigateur récent ; si absent, décoder en pur JS
   (table de conversion) — c'est un détail d'implémentation, pas un changement de format.

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `Ran 17 tests … OK`, puis `Ran 61 tests … OK`.

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite)*

```bash
git add src/naulthene/instruments/cerveau_3d/static/ tests/test_cerveau_3d.py
git commit -m "feat(VIS-01): page three.js (plaques, synapses, seuil) + three.js v0.180.0 vendorisé"
```

---

## Tâche 6 — La source factice, la CLI et la démonstration (étape 0)

**Fichiers :**
- Créer : `src/naulthene/instruments/cerveau_3d/factice.py`
- Créer : `src/naulthene/instruments/cerveau_3d/__main__.py`
- Modifier : `tests/test_cerveau_3d.py`

**Action :** la démonstration demandée : un cerveau **synthétique** de même forme, qui produit les
trois trames, plus la CLI `python -m naulthene.instruments.cerveau_3d --source factice`.

**Dépendances et interfaces :**
- Consomme : tâches 1-5.
- Produit :
  - `boucle_factice(bus, hz=15.0, dim_bus=145, arret=None, duree=None, graine=11) -> None`
  - `structure_factice(dim_bus: int, graine: int = 11) -> dict` (une trame `structure` complète)
  - `__main__.py` : `--source {factice,cerveau}`, `--brain`, `--port`, `--hz`, `--udp`,
    `--serveur-seul`, `--duree`

**Critères de succès :**
- En 1 s à 20 Hz, la boucle factice publie une structure et **≥ 10** trames d'activité.
- **La fixture ne dérive pas** : `definir_couches(16)` doit être **identique** aux couches réelles
  d'un agent neuf (`dim_bus=16`) — test qui importe `torch`.
- La CLI répond sur `--aide`.
- **Vérification visuelle de l'auteur** : la page s'ouvre et bouge sans aucun cerveau chargé.

- [ ] **Étape 1 : écrire le test qui échoue**

```python
class TestSourceFactice(unittest.TestCase):
    def test_la_forme_factice_egale_la_forme_reelle(self):
        """La fixture ne doit pas dériver de l'architecture réelle."""
        from naulthene.cerveau.noyau import AGI_Naulthene, DIM_VISUELLE
        from naulthene.cerveau.telemetrie import definir_couches
        couches = definir_couches(16)
        agent = AGI_Naulthene(dim_visuelle=DIM_VISUELLE, dim_bus=16)
        reelles = {c["nom"]: (getattr(agent, c["nom"]).in_features,
                              getattr(agent, c["nom"]).out_features) for c in couches}
        attendues = {c["nom"]: (c["entree"], c["sortie"]) for c in couches}
        self.assertEqual(reelles, attendues)

    def test_boucle_factice_publie_structure_et_activite(self):
        import time
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.factice import boucle_factice
        bus = BusTrames()
        boucle_factice(bus, hz=20.0, dim_bus=16, duree=1.0)
        self.assertIsNotNone(bus.structure())
        self.assertEqual(len(bus.structure()["couches"]), 12)
        self.assertGreaterEqual(bus.sequence, 10)
        self.assertIn("porte_visuelle", bus.activite()["neurones"])

    def test_cli_repond_a_l_aide(self):
        import subprocess
        resultat = subprocess.run(
            ["venv/bin/python3", "-m", "naulthene.instruments.cerveau_3d", "--aide"],
            env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
        self.assertIn("cerveau_3d", resultat.stdout + resultat.stderr)
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `ModuleNotFoundError: No module named 'naulthene.instruments.cerveau_3d.factice'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

`factice.py` : construit `structure_factice` (12 couches via `definir_couches`, poids tirés d'un
`default_rng(graine)` puis quantifiés par `quantifier_matrice`, bornes sensorielles) et une boucle
qui, à chaque période `1/hz`, publie une trame d'activité dont les neurones oscillent
(`sin(2π · (t/60) + phase_par_couche)`, normalisée dans `[0, 1]`, encodée `float16` → base64) et
publie un `choc_dopamine` toutes les ~5 s.

`__main__.py` : `argparse` avec les options listées, instancie `BusTrames` + `ServeurCerveau3D`
(réutilisé directement, **pas** de deuxième serveur), puis lance la source demandée dans un thread
et affiche :

```
🧠 Cerveau 3D — VIS-01
   source     : factice (dim_bus fictif = 145)
   serveur    : http://127.0.0.1:8770
   ⚠️  lecture seule : ce processus n'écrit aucun .brain et n'entraîne rien.
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `Ran 20 tests … OK`, puis `Ran 64 tests … OK`.

Puis la vérification d'écran (à faire par l'auteur, le résultat se note dans la conversation) :

```bash
PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d --source factice --port 8770
```
Ouvrir `http://127.0.0.1:8770` — 12 plaques, une colonne centrale, neurones qui s'allument.

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite)*

```bash
git add src/naulthene/instruments/cerveau_3d/ tests/test_cerveau_3d.py
git commit -m "feat(VIS-01): source factice + CLI — la démonstration de l'étape 0"
```

---

## Tâche 7 — Le rapporteur : lire un vrai cerveau sans le toucher

**Fichiers :**
- Créer : `src/naulthene/instruments/cerveau_3d/rapporteur.py`
- Modifier : `tests/test_cerveau_3d.py`

**Action :** extraire l'état d'un vrai cerveau par `register_forward_hook` sur les 12 couches (lecture
seule), et produire les trames réelles.

**Dépendances et interfaces :**
- Consomme : tâches 1-3, 6.
- Produit : `Rapporteur(bus, hz=15.0)` avec `.attacher(agent)`, `.detacher()`,
  `.publier_structure(agent, meta)` (sans retour), `.publier_activite(agent, meta) -> dict | None`
  (**renvoie la trame publiée, ou `None` si la période n'est pas écoulée** — c'est ce retour dont
  la tâche 9 a besoin pour relayer vers l'UDP), `.signal_choc(intensite, meta)`, `.compteurs()`.

**Critères de succès :**
- **Neutralité prouvée** : `agent._tronc_cerebral(obs, mem)` produit des tenseurs
  **bit-identiques** avec et sans hooks attachés (`torch.equal`).
- La trame d'activité contient les **12** couches, chacune de la bonne longueur, et le
  décodage retrouve les activations réelles (ReLU/sigmoïde appliqués selon
  `ACTIVATION_PAR_COUCHE`).
- Le throttle est respecté : deux appels immédiats à `hz=1` ⇒ **une seule** publication.

- [ ] **Étape 1 : écrire le test qui échoue**

```python
class TestRapporteur(unittest.TestCase):
    def test_les_hooks_ne_changent_pas_la_sortie_observee(self):
        import torch
        from naulthene.cerveau.noyau import AGI_Naulthene, DIM_VISUELLE
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.rapporteur import Rapporteur

        torch.manual_seed(11)
        agent = AGI_Naulthene(dim_visuelle=DIM_VISUELLE, dim_bus=16)
        agent.eval()
        obs = torch.rand(1, DIM_VISUELLE)
        mem = torch.zeros(1, 16)
        with torch.no_grad():
            avant = agent._tronc_cerebral(obs, mem)
        rapporteur = Rapporteur(BusTrames(), hz=1000.0)
        rapporteur.attacher(agent)
        try:
            with torch.no_grad():
                apres = agent._tronc_cerebral(obs, mem)
        finally:
            rapporteur.detacher()
        for a, b in zip(avant, apres):
            self.assertTrue(torch.equal(a, b))

    def test_trame_d_activite_decodable(self):
        import torch
        import numpy as np
        from naulthene.cerveau.noyau import AGI_Naulthene, DIM_VISUELLE
        from naulthene.cerveau.telemetrie import (BusTrames, decoder_octets, definir_couches)
        from naulthene.instruments.cerveau_3d.rapporteur import Rapporteur

        agent = AGI_Naulthene(dim_visuelle=DIM_VISUELLE, dim_bus=16).eval()
        bus = BusTrames()
        rapporteur = Rapporteur(bus, hz=1000.0)
        rapporteur.attacher(agent)
        try:
            with torch.no_grad():
                agent._tronc_cerebral(torch.rand(1, DIM_VISUELLE), torch.zeros(1, 16))
            rapporteur.publier_structure(agent, {"jour": 0, "dim_bus": 16})
            rapporteur.publier_activite(agent, {"jour": 0, "tick": 0})
        finally:
            rapporteur.detacher()
        self.assertEqual(len(bus.structure()["couches"]), 12)
        attendues = {c["nom"]: c["sortie"] for c in definir_couches(16)}
        for nom, taille in attendues.items():
            brut = decoder_octets(bus.activite()["neurones"][nom])
            self.assertEqual(len(np.frombuffer(brut, dtype=np.float16)), taille)

    def test_throttle(self):
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.rapporteur import Rapporteur
        bus = BusTrames()
        rapporteur = Rapporteur(bus, hz=1.0)
        rapporteur.publier_activite(None, {"tick": 0})
        rapporteur.publier_activite(None, {"tick": 1})
        self.assertEqual(bus.sequence, 1)
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `ModuleNotFoundError: No module named 'naulthene.instruments.cerveau_3d.rapporteur'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

```python
class Rapporteur:
    """Lit un cerveau VIVANT sans le modifier, et publie ses trames.

    ⚠️ Discipline MES-02 : ce rapporteur OBSERVE le passage avant réel (`penser()`), il ne
    recalcule rien. Le hook retourne `None`, donc la sortie de la couche est inchangée — c'est ce
    que vérifie `test_les_hooks_ne_changent_pas_la_sortie_observee`.
    """

    def __init__(self, bus, hz=15.0):
        self.bus = bus
        self.periode = 1.0 / float(hz)
        self._sorties = {}
        self._hooks = []
        self._derniere_publication = 0.0

    def attacher(self, agent) -> None:
        """Pose un hook de sortie sur les 12 couches, dans l'ordre de `definir_couches`."""
        self.detacher()
        for couche in definir_couches(agent.dim_bus):
            module = getattr(agent, couche["nom"])
            self._hooks.append(module.register_forward_hook(self._fabriquer_hook(couche["nom"])))

    def _fabriquer_hook(self, nom):
        def hook(_module, _entree, sortie):
            self._sorties[nom] = sortie.detach().to("cpu").numpy().reshape(-1)
            return None          # ⚠️ impératif : ne remplace JAMAIS la sortie
        return hook

    def detacher(self) -> None:
        for hook in self._hooks:
            hook.remove()
        self._hooks = []

    def publier_structure(self, agent, meta) -> None:
        """Lit les formes et les poids SUR L'AGENT (jamais une table supposée), quantifie, calcule
        la géométrie (`disposition`) et publie. ⚠️ Les positions partent DANS la trame : c'est le
        serveur qui sait où sont les neurones, jamais le navigateur — la disposition est définie
        une seule fois, en Python, et identique pour tous les cerveaux (spec §5)."""
        couches = []
        geometrie = disposition(definir_couches(agent.dim_bus))
        for couche in definir_couches(agent.dim_bus):
            module = getattr(agent, couche["nom"])
            poids = (module.base_weight + module.annexe_weight).detach().to("cpu").numpy()
            octets, echelle = quantifier_matrice(poids)
            points = geometrie[couche["nom"]].astype(np.float16).tobytes()
            couches.append({**couche, "echelle": echelle,
                            "poids_i8": encoder_octets(octets),
                            "positions": encoder_octets(points)})
        self.bus.publier_structure(trame_structure(couches, self._bornes(agent), meta))

    def publier_activite(self, agent, meta):
        """Applique l'activation DÉCLARÉE par `ACTIVATION_PAR_COUCHE` (miroir de `penser()`),
        encode en float16/base64 et publie — au plus une fois par période. Renvoie la trame
        publiée, ou `None` si la période n'est pas écoulée (c'est ce retour que relaie le
        drapeau `--telemetrie-3d` du noyau, tâche 9)."""
        maintenant = time.monotonic()
        if maintenant - self._derniere_publication < self.periode:
            return None
        self._derniere_publication = maintenant
        neurones = {}
        for nom, valeurs in self._sorties.items():
            mode = ACTIVATION_PAR_COUCHE.get(nom, "aucune")
            if mode == "relu":
                valeurs = np.maximum(valeurs, 0.0)
            elif mode == "sigmoide":
                valeurs = 1.0 / (1.0 + np.exp(-valeurs))
            neurones[nom] = encoder_octets(valeurs.astype(np.float16).tobytes())
        trame = trame_activite(neurones, self._scalaires(agent, meta), meta)
        if self.bus is not None:
            self.bus.publier_activite(trame)
        return trame
```

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `Ran 23 tests … OK`, puis `Ran 67 tests … OK`.

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite)*

```bash
git add src/naulthene/instruments/cerveau_3d/rapporteur.py tests/test_cerveau_3d.py
git commit -m "feat(VIS-01): rapporteur par forward hooks — lecture seule, neutralité testée"
```

---

## Tâche 8 — Le spectateur-pilote (étape 1) et ses preuves

**Fichiers :**
- Modifier : `src/naulthene/instruments/cerveau_3d/__main__.py`
- Créer : `src/naulthene/instruments/cerveau_3d/spectateur.py`
- Modifier : `tests/test_cerveau_3d.py`

**Action :** brancher la 3D sur un **vrai** cerveau qui vit (pattern `lancer_arene.py`) : charger un
`.brain`, boucler `traiter_tick`, publier les trames — sans jamais écrire sur le disque.

**Dépendances et interfaces :**
- Consomme : tâches 4, 6, 7.
- Produit : `jouer_cerveau(bus, fichier_brain, arret=None, duree=None, hz=15.0) -> dict`
  (renvoie `{"tick_absolu": …, "jour": …, "brain_sha256_avant": …, "brain_sha256_apres": …}`).

**Critères de succès :**
- **Le fichier `.brain` est bit-identique** avant/après (`sha256` égaux) — c'est la preuve exigée
  par la spec §10.
- Aucun fichier nouveau n'apparaît dans le dossier du `.brain` (pas de `.tmp`, pas de log).
- La page affiche le cerveau réel (vérification visuelle de l'auteur).

- [ ] **Étape 1 : écrire le test qui échoue**

```python
class TestSpectateurLectureSeule(unittest.TestCase):
    def test_le_fichier_brain_est_bit_identique(self):
        import hashlib
        import tempfile
        import os
        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.spectateur import jouer_cerveau

        dossier = tempfile.mkdtemp()
        chemin = os.path.join(dossier, "naissance.brain")
        PersistanceAnatomique(chemin).charger_ou_naitre()   # naissance (bus=16)
        avant = hashlib.sha256(open(chemin, "rb").read()).hexdigest()
        fichiers_avant = sorted(os.listdir(dossier))
        bus = BusTrames()
        jouer_cerveau(bus, chemin, duree=1.0)
        apres = hashlib.sha256(open(chemin, "rb").read()).hexdigest()
        self.assertEqual(avant, apres)
        self.assertEqual(fichiers_avant, sorted(os.listdir(dossier)))
        self.assertIsNotNone(bus.structure())
        self.assertGreater(bus.sequence, 0)
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `ModuleNotFoundError: No module named 'naulthene.instruments.cerveau_3d.spectateur'`.

- [ ] **Étape 3 : écrire l'implémentation minimale**

`spectateur.py` : `jouer_cerveau` charge via `PersistanceAnatomique(chemin).charger_ou_naitre()`,
appelle `agent.eval()`, `demarrer_journee(etat)`, attache le `Rapporteur`, publie la structure, puis
boucle `traiter_tick(etat)` en publiant l'activité — `executer_nuit` et `apprendre_journee` **ne sont
jamais appelés**. À la fin : `rapporteur.detacher()` et `etat.env.close()`. Le `sha256` du fichier
est calculé avant/après et renvoyé.

- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : `Ran 24 tests … OK` (ce test dure ~2 s : il fait vraiment vivre un cerveau pendant 1 s),
puis `Ran 68 tests … OK`.

Puis les **deux preuves manuelles** que la spec exige, à exécuter et à consigner :

```bash
# 1. un vrai cerveau de campagne, observé
PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d \
    --source cerveau --brain brains/08092026_sci01_balayage_K/K4_NU/K4_NU_g11.brain --port 8770 --hz 15

# 2. surcoût du rapporteur — chiffré, jamais estimé (même cerveau, même graine, 200 ticks)
```
Attendu : deux nombres de ticks/s (avec et sans `--rapporteur-inactif`) reportés dans la
conversation et dans le carnet de campagne — **le chiffre fait partie de la livraison**.

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite)*

```bash
git add src/naulthene/instruments/cerveau_3d/ tests/test_cerveau_3d.py
git commit -m "feat(VIS-01): spectateur-pilote — cerveau réel en lecture seule, empreinte vérifiée"
```

---

## Tâche 9 — La passerelle : drapeau `--telemetrie-3d` dans `noyau.py` (étape 2)

✅ **Prérequis D2 LEVÉ le 10/09/2026** : « le CHANGELOG fait foi » → en-tête de `noyau.py` porté à
`41.75`, tête du CHANGELOG remise en ordre décroissant (registre **DOC-03**). L'entrée CHANGELOG
de cette tâche prendra **le numéro suivant de la série après `v41.75`**, arrêté avec l'auteur au
moment de l'écrire.

**Fichiers :**
- Modifier : `src/naulthene/cerveau/noyau.py` (section `# --- 4.` : argument CLI + émission par tick)
- Modifier : `tests/test_cerveau_3d.py`
- Modifier : `docs/fonctionnement/CHANGELOG.md` (entrée en tête, après la décision D2)

**Action :** permettre à **n'importe quel run** d'émettre ses trames vers un serveur 3D, avec un
comportement **strictement inchangé** quand le drapeau est absent.

**Dépendances et interfaces :**
- Consomme : `naulthene.cerveau.telemetrie` (feuille sans torch — **aucun cycle d'import**).
- Produit : `--telemetrie-3d udp:hote:port`, plus `.telemetrie` sur `EtatCognitif`
  (`None` par défaut) ; émission de `structure` au démarrage et après neurogenèse, d'`activite`
  throttlée par tick, d'`evenement` sur choc dopaminergique.

**Critères de succès :**
- **Sans le drapeau** : `etat.telemetrie is None` et **aucune** ligne de code de télémétrie n'est
  exécutée (garde `if … is None: return` en tête de chaque point d'appel).
- **Avec le drapeau**, deux appels identiques de `traiter_tick` (mêmes graines) produisent la
  **même action** et les **mêmes `infos_internes`** qu'avec le drapeau éteint.
- Le test bit-identique en conditions réelles (deux runs, même graine, 5 jours) est la **preuve
  exigée** par la spec §10 : il se lance à la main et son verdict est consigné.

- [ ] **Étape 1 : écrire le test qui échoue**

```python
class TestTelemetrieDuNoyau(unittest.TestCase):
    def test_le_drapeau_absent_ne_change_rien_et_n_est_jamais_lu(self):
        import naulthene.cerveau.noyau as N
        self.assertFalse(hasattr(N, "TELEMETRIE_3D_ACTIVE") and N.TELEMETRIE_3D_ACTIVE)

    def test_run_identique_avec_et_sans_emetteur(self):
        import numpy as np
        import torch
        import tempfile
        import os
        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.cerveau.noyau import traiter_tick
        from naulthene.cerveau.telemetrie import BusTrames

        chemin = os.path.join(tempfile.mkdtemp(), "aa.brain")
        resultats = {}
        for bras in ("sans", "avec"):
            torch.manual_seed(11)
            np.random.seed(11)
            etat = PersistanceAnatomique(chemin).charger_ou_naitre()
            if bras == "avec":
                etat.telemetrie = _faux_emetteur(BusTrames())   # émetteur factice, en mémoire
            infos = traiter_tick(etat)
            resultats[bras] = (infos["action"], infos["infos_internes"])
            if os.path.exists(chemin):
                os.remove(chemin)
        self.assertEqual(resultats["sans"], resultats["avec"])
```

- [ ] **Étape 2 : exécuter le test avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests -p "test_cerveau_3d.py" -v
```
Attendu : échec sur `_faux_emetteur` (helper absent) — l'échec doit viser l'émetteur, pas le noyau.

- [ ] **Étape 3 : écrire l'implémentation minimale**

Dans `noyau.py` : ajouter `--telemetrie-3d` à l'`argparse`, poser `etat.telemetrie = None` par
défaut (dans la construction de l'état), puis **trois points d'appel uniques**, chacun protégé.

L'émetteur (section 1 du noyau, à côté de `NaultheneLinearSynaptique`) :

```python
# --- v4x VIS-01 : LA TÉLÉMÉTRIE 3D (instrument, aucun effet sur le cerveau) -------------
# Trois fonctions, un seul point de sortie : si `etat.telemetrie is None` (drapeau absent, le
# défaut), chacune retourne immédiatement. C'est ce que vérifie le test bit-identique — le
# chemin chaud du tick ne gagne qu'un `getattr` et une comparaison à None.

def _poser_telemetrie(etat, cible):
    """Crée l'émetteur à partir de la cible `udp:hote:port`. Une cible mal formée lève ici,
    au démarrage — jamais au milieu d'un run."""
    from naulthene.cerveau.telemetrie import EmetteurUDP
    etat.telemetrie = None if not cible else EmetteurUDP(cible)
    if etat.telemetrie is not None:
        print(f"📡 Télémétrie 3D active → {etat.telemetrie.compteurs()['cible']} "
              f"(aucun effet sur l'apprentissage)")


def _emettre_structure(etat, rapporteur=None):
    """Envoyée au démarrage, et à chaque neurogenèse (la forme du cerveau a changé)."""
    if getattr(etat, "telemetrie", None) is None:
        return
    from naulthene.instruments.cerveau_3d.rapporteur import Rapporteur
    rapporteur = rapporteur or Rapporteur(None, hz=0.0)
    rapporteur.attacher(etat.agent)
    rapporteur.publier_structure(etat.agent, _meta_telemetrie(etat))
    rapporteur.detacher()


def _emettre_tick(etat):
    """Une trame d'activité par tick, throttlée PAR LE RAPPORTEUR (15 Hz) : le cerveau peut
    tourner à 200 ticks/s, on n'encode pas 200 trames par seconde. Appelée juste après
    `penser()` dans `traiter_tick`. `publier_activite` renvoie `None` quand la période n'est pas
    écoulée — c'est le seul cas où rien ne part."""
    rapporteur = getattr(etat, "telemetrie_rapporteur", None)
    if rapporteur is None:
        return
    trame = rapporteur.publier_activite(etat.agent, _meta_telemetrie(etat))
    if trame is not None:
        etat.telemetrie.envoyer(trame)


def _emettre_evenement(etat, genre, **champs):
    """Un fait daté, émis au même endroit et sous la même condition que la LTP : ce que le
    cerveau grave, on le montre. Appelée à côté de `etat.agent.fortifier_synapses(...)`
    (~l. 10434), jamais ailleurs."""
    emetteur = getattr(etat, "telemetrie", None)
    if emetteur is None:
        return
    from naulthene.cerveau.telemetrie import trame_evenement
    emetteur.envoyer(trame_evenement(genre, _meta_telemetrie(etat), **champs))


def _meta_telemetrie(etat):
    """Les métadonnées communes aux trois trames — `niveau` porte TOUJOURS l'`env_id` (règle du
    07/09 : un niveau sans son `env_id` est ambigu)."""
    return {"tick": int(getattr(etat, "tick_absolu", 0)),
            "jour": int(getattr(etat, "jour", 0)),
            "dim_bus": int(etat.agent.dim_bus),
            "niveau": {"index": int(getattr(etat, "niveau_actuel", 0)),
                       "env_id": getattr(etat, "env_id", "?")}}
```

Le montage, à l'endroit où l'état est construit (juste après la création de l'agent) :

```python
    if cible_telemetrie:
        from naulthene.cerveau.telemetrie import BusTrames
        etat.telemetrie_bus = BusTrames()
        etat.telemetrie_rapporteur = Rapporteur(etat.telemetrie_bus, hz=TELEMETRIE_3D_HZ)
        etat.telemetrie_rapporteur.attacher(etat.agent)
        _poser_telemetrie(etat, cible_telemetrie)
        _emettre_structure(etat, etat.telemetrie_rapporteur)
    else:
        etat.telemetrie = None
        etat.telemetrie_rapporteur = None
```

⚠️ **Le rapporteur est branché AVANT `demarrer_journee`** : sans quoi la première trame arriverait
après une journée entière. Et il reste branché pendant tout le run (aucun `detacher`), pour que
chaque tick alimente `etat.telemetrie_bus` ; `_emettre_structure` ne fait que publier puis renvoyer
la trame par l'émetteur, il ne détache pas.

**Les deux points d'appel dans le tick** (les seuls du noyau) :
- `_emettre_tick(etat)` — juste après l'arbitrage C1/C2, quand `penser()` a produit son état ;
- `_emettre_evenement(etat, "choc_dopamine", intensite=poids_evenement)` — dans le `if
  poids_evenement > 0:` (~l. 10430), **à côté** de `etat.agent.fortifier_synapses(poids_evenement)`.

Et l'option CLI, à côté des autres `add_argument` :

```python
    parser.add_argument("--telemetrie-3d", type=str, default=None, metavar="udp:HOTE:PORT",
                        help="VIS-01 — émet la télémétrie du cerveau 3D vers un serveur "
                             "(ex. udp:127.0.0.1:9998). Défaut : aucune télémétrie, et le run "
                             "est alors strictement inchangé.")
```


- [ ] **Étape 4 : réexécuter les tests avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests 2>&1 | tail -3
```
Attendu : `Ran 70 tests … OK`.

Puis **la preuve bit-identique en conditions réelles** (à lancer et à consigner) :

```bash
mkdir -p brains/VIS01_preuve && cd brains/VIS01_preuve
for bras in temoin telemetrie; do
  NAULTHENE_DEVICE=cpu WANDB_MODE=offline PYTHONPATH=../../src ../../venv/bin/python3 \
      -m naulthene.cerveau.noyau --graine 11 --jours 5 --brain "aa_${bras}.brain" \
      $([ "$bras" = telemetrie ] && echo "--telemetrie-3d udp:127.0.0.1:9998") \
      > "aa_${bras}.log" 2>&1
done
diff <(grep -o 'Niveau [0-9]*' aa_temoin.log) <(grep -o 'Niveau [0-9]*' aa_telemetrie.log) && echo "✅ bit-identique"
```
Attendu : `✅ bit-identique` (aucune ligne de `diff`).

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite)*

```bash
git add src/naulthene/cerveau/noyau.py tests/test_cerveau_3d.py docs/fonctionnement/CHANGELOG.md
git commit -m "feat(VIS-01): drapeau --telemetrie-3d — un run en cours alimente le cerveau 3D"
```

---

## Tâche 10 — La documentation de l'instrument

**Fichiers :**
- Modifier : `docs/fonctionnement/LANCEMENT.md` (nouvelle section « Le cerveau 3D »)
- Modifier : `docs/INDEX.md` (ligne du plan à côté de celle de la spec)
- Modifier : `docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md` (statut VIS-01)
- Modifier : `docs/ETAT_COURANT.md` (seulement si VIS-01 change l'état du projet — ce n'est pas le cas :
  l'instrument n'entre pas dans le tableau des leviers)

**Action :** rendre l'instrument lançable **sans lire le code**, et laisser la trace documentaire
qu'exige le dogme « rien sans écrit ».

**Critères de succès :**
- `LANCEMENT.md` contient les trois commandes (étapes 0, 1, 2) et la garantie de lecture seule.
- `INDEX.md` pointe vers la spec **et** vers ce plan.
- Le registre indique le statut réel de VIS-01 (livré / partiel), avec la preuve d'empreinte et le
  surcoût mesuré.

- [ ] **Étape 1 : écrire la section de `LANCEMENT.md`**

```bash
grep -n "## " docs/fonctionnement/LANCEMENT.md | tail -20
```
Repérer la section des instruments (l'Arène est documentée vers la ligne 440) et insérer la
nouvelle section **après** elle, avec les trois commandes exactes et la phrase :

> ⚠️ En lecture seule : aucun `.brain` n'est écrit, `executer_nuit`/`apprendre_journee` ne sont
> jamais appelés. Le fichier observé reste **bit-identique** (vérifié par empreinte SHA-256).

- [ ] **Étape 2 : vérifier les liens et l'index**

```bash
grep -n "VIS-01" docs/INDEX.md docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md
python3 - <<'PY'
import re, os
for f in ("docs/INDEX.md", "docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md"):
    for lien in re.findall(r'\]\(([^)]+\.md)\)', open(f).read()):
        cible = os.path.normpath(os.path.join(os.path.dirname(f), lien))
        if not os.path.exists(cible):
            print("LIEN MORT", f, "->", lien)
print("vérification terminée")
PY
```
Attendu : `vérification terminée` sans aucune ligne `LIEN MORT`.

- [ ] **Étape 3 : mettre à jour le statut du registre**

Remplacer la ligne VIS-01 du §2 par son statut réel, et la section VIS-01 par une clôture qui
contient les quatre éléments de la règle : cause, correction référencée, **vérification fraîche**
(empreinte + surcoût), entrée CHANGELOG (tâche 9).

- [ ] **Étape 4 : réexécuter la suite complète avec `bash`**

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests 2>&1 | tail -3
```
Attendu : `Ran 70 tests … OK` (aucune régression documentaire ne peut casser un test, mais la
commande est le témoin que l'arbre est sain au moment de conclure).

- [ ] **Étape 5 : commit ciblé avec `bash`** *(sur accord explicite)*

```bash
git add docs/fonctionnement/LANCEMENT.md docs/INDEX.md docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md
git commit -m "docs(VIS-01): le cerveau 3D documenté — lancement, index, registre"
```

---

## Couverture de la spec (chaque exigence → sa tâche)

| Exigence de la spec | Tâche |
|---|---|
| §3 serveur stdlib, aucune dépendance ajoutée | 4, 5 |
| §3 rapporteur par forward hooks, discipline MES-02 | 7 |
| §3 three.js vendorisé, aucun CDN au runtime | 5 |
| §4 canal `structure` (matrices quantifiées **+ positions**) | 1, 2, 5, 7 |
| §4 canal `activite` (1 182 neurones, 15 Hz) | 2, 7 |
| §4 canal `evenement` (choc dopaminergique, victoire, neurogenèse) | 2, 6, 9 |
| §5 disposition déterministe, 12 plaques + colonne du bus | 2, 5 |
| §5 encodage visuel (activation, poids, myéline, neurones morts, dopamine) | 5, 7 |
| §6 étape 0 (source factice) | 6 |
| §6 étape 1 (spectateur-pilote) | 8 |
| §6 étape 2 (passerelle UDP + drapeau) | 9 |
| §8 garanties (aucun fichier écrit, aucun pas d'optimiseur) | 8, 9 |
| §9 robustesse (datagramme malformé, file bornée, échelle) | 3, 4 |
| §10 tests 1-6 | 1, 2, 3, 4, 5, 7 |
| §10 preuves (empreinte, surcoût, bit-identique) | 8, 9 |
| §11 YAGNI (pas de WebSocket, pas de multi-cerveaux…) | respecté par construction |
| §7 `LANCEMENT.md` | 10 |

## Ce que ce plan ne fait pas

- Il ne modifie **aucune mécanique cognitive** : l'étape 2 n'ajoute qu'un canal d'observation.
- Il ne touche pas `pyproject.toml` (zéro dépendance ajoutée).
- Il ne crée **aucun commit** sans l'accord explicite de l'auteur (CLAUDE.md §12).
- Il ne traite ni D1 (déjà corrigé, registre DOC-02) ni D2 (décision de version, prérequis de la
  tâche 9).
