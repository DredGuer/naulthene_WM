# Chantier v41.4 — La maîtrise générale et l'héritage de sevrage

> **Statut** : implémenté, campagne 10 graines × 2 variantes en cours (15/08/2026).
> **Fichier** : `src/naulthene/cerveau/noyau.py` (expérimental — pas dans `colab.py`).
> **Décision utilisateur** : *« Tu as une maîtrise générale des cartes et une maîtrise
> carte par carte »*, et *« reporter une proportion du niveau précédent de maîtrise sur
> le suivant »*.

---

## 1. Le défaut mesuré

Le run v41.3 de 300 jours (voir `CHANTIER_v41.2_energie_modulatrice.md` §11) a produit
**deux promotions** — les premières du projet — puis un effondrement.

| Jalon | Niveau | Maîtrise 50 derniers j | Autonomie moy | Maturité moy |
|---|---|---|---|---|
| 117 j | 2/15 | 41 % | 43 % | 0,182 |
| 215 j | 3/15 | 6 % | 7 % | 0,008 |
| 300 j | 3/15 | **2 %** | **3 %** | **0,002** |

**La cause est mécanique, pas comportementale.** À chaque promotion :

```python
etat.historique_episodes_niveau = []    # invariant NON NÉGOCIABLE (v35.0)
```

Donc `_maturite_niveau()` retombe à **0,000 exactement** (régularité 0 × consolidation 0
× autonomie 0), et `facteur_guidage` remonte à **1,0 — l'aide maximale**. L'agent
**redevient un nouveau-né sur chaque carte**, quelle que soit son expérience.

Or un agent qui vient de tenir 60 % sur trois cartes n'est pas un débutant absolu : il
sait viser un but, contourner un mur, terminer un épisode. Ce qui est périmé au
changement de carte, c'est le **plan** — pas la **compétence motrice**.

## 2. La mesure préalable — le report est-il seulement justifié ?

⚠️ **Méthode du projet** (posée en v30.1) : *avant de rendre une constante adaptative,
l'instrumenter et la mesurer d'abord*. Un report de « X % » posé à la main aurait été un
chiffre arbitraire de plus.

Mesure sur les **15 niveaux du PROGRAMME**, 40 resets chacun, propriétés structurelles
lues sur la grille (`docs/recherche/` — script `mesure_parente.py`) :

| Transition | Parenté | Nouveau vocabulaire |
|---|---|---|
| Nourrisson → Éveil | **0,70** | — |
| Éveil → Maternelle | **0,59** | — |
| Maternelle → Primaire 1 | **0,85** | — |
| Primaire 1 → Primaire 2 | **0,20** ⚠️ | `lava` |
| Primaire 2 → Primaire 3 | **0,00** ⚠️ | `ball`, `key` |
| Primaire 3 → Collège 1 | **0,00** ⚠️ | `door` |
| Collège 1 → Collège 2 | **0,17** ⚠️ | `goal`, `key` |
| Collège 2 → Collège 3 | 0,66 | — |
| Collège 3 → Lycée 1 | 0,58 | — |
| Lycée 1 → Lycée 2 | 0,95 | — |
| Lycée 2 → Lycée 3 | 0,66 | `box` |
| Lycée 3 → Université | **0,31** ⚠️ | `ball` |
| Université → Doctorat 1 | **0,00** ⚠️ | `door`, `goal` |
| Doctorat 1 → Doctorat 2 | 0,74 | — |

**6 transitions sur 14 sont des ruptures** (< 0,50), dont **trois à 0,00**.

> 🎯 **Ce que la mesure tranche.** L'intuition « reporter une proportion » est juste,
> mais un report **uniforme** serait faux dans au moins six cas sur quatorze. Le report
> doit être **proportionnel à la parenté**, et la parenté doit être **mesurée**.
>
> Elle explique aussi rétrospectivement l'effondrement de v41.3 : l'agent a calé au
> niveau 3 → 4 (`SimpleCrossing` → `LavaGap`), une transition à **parenté 0,20** avec un
> vocabulaire neuf (`lava`).

## 3. La mécanique

### 3.1 Deux grandeurs, deux rôles

| Grandeur | Vidée à la promotion ? | Pilote |
|---|---|---|
| `historique_episodes_niveau` (par carte) | ✅ oui | la **PROMOTION** |
| `historique_episodes_general` (transversale) | ❌ **non** | le **SEVRAGE** |

### 3.2 La parenté, lue sur la grille

`_profil_carte(env)` lit surface, espace libre, densité d'obstacles, et l'**ensemble
opaque** des étiquettes d'objets. `_parente_cartes(a, b)` en dérive :

```
parenté = forme × vocabulaire
  forme       = 1 − moyenne des écarts relatifs (surface, libres, densité)
  vocabulaire = |types(b) ∩ types(a)| / |types(b)|
```

**Multipliés, jamais sommés** — même raison que la maturité : une carte de forme
identique au vocabulaire inconnu n'est **pas** un niveau parent, et une somme laisserait
la forme compenser la nouveauté.

⚠️ **Le vocabulaire reste opaque.** Aucune table `objet → difficulté` : « lava est
dangereux » n'est écrit nulle part, seulement « `lava` est un symbole que cette carte-ci
n'avait pas ». Même discipline que l'empreinte de type (v39.0).

### 3.3 L'héritage

```python
fraîcheur       = min(1, len(historique_niveau) / FENETRE_PROMOTION)
poids_héritage  = (1 − fraîcheur) × parenté
taux_sevrage    = taux_niveau × (1 − poids) + taux_général × poids
```

Le produit de deux grandeurs mesurées décide seul. Rien n'est posé.

## 4. Les cinq invariants — tous vérifiés

| # | Invariant | Vérification |
|---|---|---|
| 1 | L'héritage ne touche **que** le sevrage | `_maturite_niveau` lit toujours la seule maîtrise par carte |
| 2 | À fenêtre pleine, héritage = **0 exact** | guidage **1,000** mesuré (= v41.3) |
| 3 | Parenté 0 (rupture) ⇒ **aucun** héritage | guidage **1,000** mesuré |
| 4 | Une baisse de compréhension **remonte** l'aide | 100 % → autonomie 100 % ; 0 % → 0 % |
| 5 | Un `.brain` antérieur repart héritage nul | vérifié sur un cerveau de **2700 jours**, **2 nuits complètes** |

> L'invariant 5 exige une **nuit complète**, pas des ticks : le bug de greffe v32.0 ne se
> manifestait **ni au chargement ni pendant la journée**, mais à la première
> `executer_nuit`.

### L'effet, sur une transition parente (0,73)

| Épisodes joués sur la nouvelle carte | Autonomie |
|---|---|
| 0 | **49 %** (au lieu de 0 %) |
| 5 | 36 % |
| 10 | 24 % |
| 15 | 12 % |
| 20 (fenêtre pleine) | **0 %** — retour exact à v41.3 |

L'héritage est une **avance**, jamais une rente : il s'efface à mesure que les données
réelles arrivent.

## 5. Le protocole de campagne

⚠️ **Une graine ne prouve rien** — précédent g22 (niveau 4 en solo, invalidé comme
loterie natale par la campagne à 10 graines). Et comparer 10 graines v41.4 à un run
antérieur ne vaudrait rien non plus : les trajectoires natales diffèrent.

**Protocole retenu** : 10 graines × 2 variantes = **20 runs de 300 jours**, mêmes
graines des deux côtés, lancés au même moment, la seule mécanique testée étant coupée
côté témoin par `--sans-heritage` (ablation vérifiée : guidage 1,000 contre 0,513).

Graines : 11, 22, 33, 44, 55, 66, 77, 88, 99, 111.

## 6. Résultats

*(en attente de la fin de campagne — cette section sera remplie par la mesure, pas par
l'attente)*
