# `EPISODES_PAR_JOURNEE_REFERENCE` — la dernière constante posée du rythme métabolique

**Statut : IDÉE, non validée.** À traiter **APRÈS** la fin de la campagne v41.29 (1500 jours).
Décision utilisateur du 20/08/2026 : *supprimer* cette constante, pas la recalibrer.

---

## 1. Ce qu'elle est aujourd'hui

`src/naulthene/cerveau/noyau.py:5155`

```python
EPISODES_PAR_JOURNEE_REFERENCE = 4.0     # borne : ordre de grandeur mesuré (patience ~95
                                         # ticks sur 400). Sert d'échelle, pas de vérité —
                                         # la patience réelle varie d'un jour à l'autre.
_OPPORTUNITES_MIN_JOUR = _BUDGET_CARTE_MINIMALE * EPISODES_PAR_JOURNEE_REFERENCE
_BESOIN_TOTAL_JOUR     = _OPPORTUNITES_MIN_JOUR / MARGE_SUBSISTANCE
_BESOIN_PAR_AXE        = (_OPPORTUNITES_MIN_JOUR / 2.0) / MARGE_SUBSISTANCE
REPAS_PAR_JOURNEE = PRISES_HYDRIQUES_PAR_JOURNEE = _BESOIN_PAR_AXE   # = 2.80
NB_SOURCES_FOOD   = max(2, round(REPAS_PAR_JOURNEE * MARGE_TROUVABILITE))  # = 6
```

Elle fixe **tout le rythme métabolique** : le besoin par axe, donc la densité de ressources.

## 2. Pourquoi c'est une brèche du dogme

Le dogme : une constante ne peut être qu'une **borne**, jamais une **valeur**.

1. **Ce n'est pas une borne, c'est une mesure figée.** Le commentaire l'avoue (« ordre de
   grandeur mesuré, patience ~95 ticks »). C'est une photo d'un instant du projet.
2. **La grandeur existe déjà, mesurée en direct, à côté.** Le `Potentiomètre` calcule
   `patience_de_base_du_jour` chaque nuit. On ne la lit pas.
3. **Elle dérive sous la mécanique même du projet.** Le Sursaut de Volonté étire la
   patience ; plus l'agent persévère, moins il joue d'épisodes, moins il a d'occasions
   de manger — alors que son besoin reste calé sur 4 épisodes/jour.

C'est le défaut de `norme_naissance` (v34.0-fix2) et de `reference_choc_dopamine`
(v37.1-fix1) reproduit : **une référence posée a priori qui ne suit pas la vie de l'agent.**

## 3. La mesure (campagne v41.29, 10 graines, ~j1200/1500)

Patience réelle, moyenne du 1er quart → dernier quart de chaque run :

| grandeur | début | fin | écart |
|---|---|---|---|
| patience | 168 ticks | **258 ticks** | **+54 %** (`t = +9,55`, SIG) |
| épisodes/jour | 2,39 | **1,55** | **−35 %** |
| écart à la constante 4,0 | ×1,68 | **×2,58** | **l'écart SE CREUSE** |

Besoin par axe qui en découlerait :

| source | besoin/axe |
|---|---|
| code (4,0) | **2,80** |
| réel début (2,39) | 1,67 |
| réel fin (1,55) | **1,08** |

L'agent a un besoin calibré pour 4 épisodes et n'en joue plus que 1,55.

**Corrélation qui relie le tout** : `maîtrise ~ énergie moyenne`, `r = +0,710`, `t = +2,85`
(SIG, n=10). Les graines qui mangent sont celles qui maîtrisent.

## 4. Ce qu'il ne faut PAS faire

**Ne pas remplacer 4.0 par 1.55.** Ce serait un chiffre posé pour un autre chiffre posé —
l'erreur que le commentaire d'à côté raconte avoir commise **trois fois** (`REPAS = 2.5`
recalibré à la main §7.3, §7.5, §8.6).

## 5. La direction (à concevoir après le run)

Supprimer la constante et **lire la patience réelle de l'agent**, sur le modèle de
`reference_choc_dopamine` : une référence dérivée du vécu, à **cliquet** (montée lente,
descente ~50× plus lente), avec une valeur de naissance pour le jour 1 où l'agent n'a
pas encore de vécu. `MARGE_SUBSISTANCE = 2.0` reste — c'est une vraie borne sur un rapport.

⚠️ **Deux risques à mesurer, pas à supposer :**

- **Boucle de rétroaction** : moins d'épisodes → moins de sources → plus de faim →
  patience modifiée. Le cliquet doit l'empêcher de s'emballer ; ça se vérifie.
- **La direction de l'effet est contre-intuitive** : suivre la patience réelle ferait
  *baisser* le besoin (2,80 → 1,08), donc *baisser* la densité de ressources. Or
  l'énergie est déjà au plancher. Il faut vérifier laquelle des deux lectures est juste :
  soit le besoin est trop haut (l'agent ne peut pas le satisfaire), soit les occasions
  sont trop rares (il faudrait plus de sources, pas moins). **Les deux corrections sont
  opposées et une seule est bonne.**

## 6. Protocole de validation

- A/A d'abord (règle de mesure §1)
- **20 graines minimum**, IC de Wilson à côté de chaque taux
- Témoin d'ablation conservant la constante figée
- Mesurer : énergie moyenne, ticks en zone critique, maîtrise au palier, **et** la
  stabilité de la référence (pas d'emballement)

---

# ADDENDUM du 20/08/2026 — le volet PATIENCE (décision utilisateur)

La campagne v41.29 a révélé que le problème ne se limite pas au `4.0`. **Trois** constantes
posées décrivent le même agent d'août 2026 et doivent disparaître ensemble.

## 7. La mesure qui a tout déclenché

`patience_min` relevée dans les 10 runs à j1350 :

```
LIBRE_g1..g5, MORT_g1, g2, g4, g5 : 350   ← PLAFOND EXACT
MORT_g3                            : 330
```

**9 graines sur 10 sont collées au mur `PATIENCE_MAX = 350`.**

Mécanisme actuel (`augmenter_patience_de_base_definitivement`, noyau.py:2241) :

| victoires-sursaut | patience_min | gain de la suivante |
|---|---|---|
| 5 | 100 | +10 |
| 20 | 250 | +10 |
| 30 | **350** | **+0** |
| 100 | 350 | **+0** |

Le gain est **constant** jusqu'au mur, puis **nul**. 30 victoires suffisent à saturer, puis
plus rien ne bouge pendant 1200 jours. C'est l'inverse d'une difficulté croissante.

## 8. La direction (formulation utilisateur, 20/08/2026)

> « La patience doit être un genre d'exponentielle qui part de 1 jusqu'à l'infini, mais
> exponentiel — plus tu gagnes en patience, plus c'est dur de gagner à nouveau de la
> patience. Le gain de patience est lié directement à l'écart entre le raté et la
> réussite, ce qui permet de gagner en proportion une quantité de patience. »

### 8.1 Rendement exponentiellement décroissant, sans plafond

`PATIENCE_MAX = 350` est un chiffre posé au même titre que le `4.0`. Il est remplacé par une
pente qui devient verticale :

```
patience = PATIENCE_NAISSANCE × exp(capital)
```

où chaque gain ajoute au capital une quantité **divisée par ce qu'on a déjà**. La patience
croît sans borne, mais atteindre 700 ticks coûte incomparablement plus que d'atteindre 100.

C'est le motif **déjà employé** par la dérive métabolique (noyau.py:5304) :
`Δdérive = pression × plasticité − raideur × dérive × exp(|dérive| / élasticité)`,
documenté comme « une PENTE QUI DEVIENT VERTICALE, pas une barrière ». Précédent et
vocabulaire existent déjà dans le projet.

### 8.2 Le gain dérivé de l'écart raté ↔ réussite

Aujourd'hui le gain dépend d'un **compteur d'événements** (+10 par victoire-sursaut, quelle
que soit sa difficulté). Il doit dépendre d'une **grandeur mesurée** : l'écart entre la durée
des ratés et celle des réussites.

Sens biologique :
- réussites à 80 ticks, abandons à 100 → écart faible → **attendre plus ne sert à rien** →
  gain faible
- réussites à 300 ticks, abandons à 150 → écart grand → **il coupe trop tôt** → gain fort

La patience se cale sur ce que le monde exige réellement, mesuré par l'agent lui-même.

⚠️ **`historique_vitesses` n'enregistre que les RÉUSSITES** (noyau.py:2251,
`if reussi: historique_vitesses.append(...)`). Mesurer un écart exige aussi la durée des
ratés — une ligne à ajouter, faute de quoi l'écart se calcule avec une moitié manquante.

## 9. Les trois suppressions

| constante | valeur | remplacée par |
|---|---|---|
| `EPISODES_PAR_JOURNEE_REFERENCE` | 4.0 | `etat.episodes_jour` vécu, à inertie |
| `PATIENCE_MAX` | 350 | rendement exponentiellement décroissant, sans borne |
| `BOOST_PATIENCE_MIN_PAR_RECURRENCE` | 10 | écart mesuré raté ↔ réussite |

**Bornes CONSERVÉES** (ce sont des rapports, pas des valeurs) : `MARGE_SUBSISTANCE`,
`MARGE_TROUVABILITE`, `FRACTION_CASES_RESSOURCES_MAX`.

## 10. Risques à MESURER, pas à supposer

1. **Sans plafond, rien n'empêche la fuite.** Une patience tendant vers l'infini avec
   `TICKS_PAR_JOUR = 400` produirait **moins d'un épisode par jour** — l'agent ne verrait
   plus jamais de `reset()`. L'exponentielle rend cela très coûteux, mais « très coûteux »
   n'est pas « impossible ». Vérifier au banc que le rendement décroissant mord avant.
2. **Ablation confondue.** Patience et rythme métabolique sont **couplés**
   (`épisodes/jour` est l'entrée du besoin). Changer les deux dans un même bras rend
   impossible de savoir lequel a agi → **un bras d'ablation par constante**.
3. **Le sens de la correction n'est pas tranché** (cf. §5) : suivre la patience réelle fait
   *baisser* le besoin (2,80 → ~1,1/axe), donc *moins* de sources, alors que l'énergie est
   déjà au plancher. Les deux lectures restent ouvertes et **la mesure les départagera**.

## 11. Question ouverte laissée à l'utilisateur

L'écart raté ↔ réussite se calcule-t-il sur la **fenêtre glissante de 20 épisodes**
(oublie au changement de carte) ou sur **toute la vie de l'agent** (trait de caractère
acquis) ? Les deux se défendent ; le comportement au changement de palier diffère
radicalement. **Non tranché au 20/08/2026.**
