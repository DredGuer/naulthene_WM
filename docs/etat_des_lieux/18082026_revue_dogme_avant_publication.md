# État des lieux — revue du dogme « rien en dur » avant présentation à des chercheurs

**18/08/2026** — photo horodatée, non mise à jour après cette date.
Demande : *« je ne veux pas parler d'une architecture en disant "rien en dur" s'il y a
encore des éléments en dur »*.

Audit du **code**, pas de la documentation : commentaires et docstrings exclus des
comptages, seul ce que l'interpréteur exécute a été retenu.

**Champ** : `noyau.py` (10 004 l.), `bus_sensoriel.py` (945 l.), `persistance.py` (700 l.),
`port_c3.py` (198 l.) — 161 constantes numériques triées une à une.

---

## Verdict en une phrase

> **La formule « rien en dur » est FAUSSE telle quelle et ne doit pas être prononcée
> devant un chercheur.** La formule défendable, et défendable *rigoureusement*, est :
> **« aucun seuil de déclenchement dans le chemin de décision, et aucune valeur
> d'apprentissage posée a priori — mais des constantes de calibration subsistent, toutes
> localisées. »**

La différence n'est pas cosmétique. La première est réfutable en dix minutes par un
lecteur qui fait `grep`. La seconde résiste à l'audit, parce qu'elle est vraie.

---

## 1. Ce qui tient — et c'est l'essentiel

### 1.1 Aucun seuil dans le chemin de décision ✅

C'est la propriété la plus forte du projet, et elle est **vérifiée**. Le projet a refusé
quatre fois d'introduire un `if` dans le chemin cognitif :

| Refus | Version | Ce qui a été refusé |
|---|---|---|
| Appel à C3 sur seuil d'incertitude | v28 | `si incertitude > X : demander` |
| Court-circuit C1→C2 | v29 | `si C1 confiant : sauter C2` |
| Boucle d'attention exo-sensorielle | v30 | `si erreur JEPA monte : interroger` |
| `force_planification` fonction de l'entropie | v37 | « une sigmoïde reste un `if` avec une pente » |

**C2 est consulté à chaque tick, sans condition.** L'arbitrage est une somme pondérée
continue, jamais une branche.

### 1.2 Les grandeurs d'apprentissage sont DÉRIVÉES ✅

Vérifié ligne à ligne, ce sont des **niveaux qui évoluent avec le vécu**, pas des
réglages :

| Grandeur | Dérivée de |
|---|---|
| `reference_choc_dopamine` | les chocs réellement vécus (cliquet : ↑ vite, ↓ 50× plus lentement) |
| `pourcentage_reve` | plasticité × richesse de la journée |
| `capacite_memoire` | `dim_bus × SOUVENIRS_PAR_DIM × (1 + déficit)` |
| `VIGUEUR_MIN_C1` | `(AMPLITUDE_C2 × FORCE_PLANIF) / RATIO_VISÉ` |
| `seuil_base` (neurogenèse) | deux pressions continues en `max`, aucun `if` |
| `échelle_myeline` | 3ᵉ quartile de la couche, jamais une valeur absolue |
| `DIM_BUS_MAX` | RAM et cœurs de la machine |
| `rendement_ref` (ROI) | cliquet sur le rendement vécu |
| `lambda_diffusion` (odorat/chaleur) | dimensions de la carte |
| `exigence` (mutation) | `1 + 1/fenêtre` |

**Exemple canonique** : le même choc de 0,1 vaut **100 % pour un débutant** et **11,4 %
pour le même agent devenu expert**. Aucune règle ne le dit ; le niveau a bougé.

### 1.3 Une seule règle de plasticité ✅

Une classe (`NaultheneLinearSynaptique`) gouverne les 12 couches : cycle jour/nuit,
myéline, érosion, neurogenèse. Pas d'exception, pas de cas particulier.

### 1.4 Aucune table « objet → valeur » ✅

La valence d'un type est la **moyenne des chocs vécus** sur une étiquette opaque. Il
n'existe nulle part `lave = danger`. C'est ce qui a rendu possible la mesure — embarrassante
mais vraie — que **la lave avait la valence de l'eau** pendant toute l'histoire du projet.
Un système expert n'aurait jamais pu produire ce constat : il aurait su.

---

## 2. Ce qui ne tient PAS — les violations réelles

### 🔴 V1. Le cœur NOMME le monde — 7 sites

Le README affirme : *« nothing in it names "grid", "key" or "door" »*. **C'est faux.**

| Fichier | Ligne | Code |
|---|---|---|
| `noyau.py` | 3159-3160 | `COULEUR_FOOD = "red"` / `COULEUR_WATER = "blue"` |
| `noyau.py` | 6887 | `getattr(objet,"type") == "ball" and color in (...)` |
| `noyau.py` | 3903-3907 | table de traduction `door→porte, key→clé, lava→lave…` |
| `bus_sensoriel.py` | — | `TYPES_BRULANTS = ("lava",)`, `TYPES_BLOQUANTS_ODORAT = ("wall","lava")` |
| `bus_sensoriel.py` | — | `COULEUR_NOURRITURE = "red"`, `COULEUR_EAU = "blue"` |

**Nuance qui compte, mais qui ne sauve pas la formule** : dans `bus_sensoriel.py`, c'est
défendable — un organe sensoriel *doit* traduire le monde physique en signal, et un
capteur infrarouge « nomme » lui aussi ce qui chauffe. C'est la frontière corps/monde.

**Dans `noyau.py`, ce n'est pas défendable** : la table de traduction ligne 3903 est de la
télémétrie (lisibilité humaine), mais `COULEUR_FOOD`/`ball` ligne 6887 sont utilisés par
le **comptage des ressources**, donc sur un chemin fonctionnel.

> **À dire** : « le cœur ne nomme pas le monde **sauf pour la nourriture et l'eau, qui
> sont identifiées par couleur** ». Ou déplacer ces deux constantes dans
> `bus_sensoriel.py`, où elles ont leur place.

### 🔴 V2. Récompenses posées a priori — 4 constantes

Ce sont les plus graves : elles **façonnent ce que l'agent veut**.

| Constante | Valeur | Rôle |
|---|---|---|
| `RECOMPENSE_APPROCHE_BUT` | 0.05 | guidage vers le but (béquille, retirée au palier 5) |
| `MICRO_RECOMPENSE_CURIOSITE` | 0.04 | prime à la surprise JEPA |
| `MICRO_RECOMPENSE_VOCALE` | 0.05 | prime à la production vocale |
| `MALUS_DOULEUR` | −0.01 | coût d'un choc contre un mur |

Aucune n'est dérivée. `MALUS_DOULEUR = −0.01` est même la constante qui a **causé** le
problème de la lave : mourir coûtait `0.0`, se cogner `−0.01`, donc **mourir était moins
cher que se cogner**. Une valeur posée à la main a produit une inversion de préférence
que personne n'avait voulue — c'est l'argument le plus fort *contre* les constantes
posées, et il vient du projet lui-même.

### 🟠 V3. Constantes de calibration — ~25, toutes localisées

`TAUX_CHOC_BASE=0.9`, `TAUX_FRICTION=0.01`, `GAMMA_PLANIFICATION=0.9`,
`JOURS_ENTRE_MUTATIONS=5`, `DEMI_VIE_OKAY=300`, `POIDS_LUCIDITE=0.02`,
`PENALITE_STAGNATION_BASE=0.015`, `FACTEUR_SEUIL_SURPRISE=1.5`…

**Défendable** — tout modèle a des constantes de temps, et un cerveau biologique aussi
(vitesse de recapture de la dopamine, demi-vie d'une trace). Mais ce ne sont pas « rien ».

### 🟠 V4. Vestiges DoorKey — code mort mais chargé

`SUCCES_PAR_SOUS_SEUIL=2`, `COEFF_ABNEGATION_SOUS_SEUIL_2=1.6`,
`SEUIL_PALIER_MODE_LIBRE=5`, les 7 paliers de `DetecteurJalonsDoorKey`. Spécifiques à
**un** environnement, alors que le cursus en compte 15. À isoler ou supprimer avant
publication : un lecteur y verra un solveur MiniGrid déguisé.

### 🟠 V5. `SEUIL_CRISTAL = 0.80` — un seuil qui n'a jamais servi

10 usages, **jamais franchi** (myéline réelle max mesurée : **0.0038**, soit 200× moins).
La « Cristallisation Souple v26.0 » ne s'est enclenchée sur **aucun** cerveau du dépôt.
C'est un seuil absolu posé a priori, jamais confronté à une mesure — exactement le défaut
que la v37.0 a corrigé ailleurs (`echelle_myeline` rendue relative).

---

## 3. Le décompte honnête

| Catégorie | Nombre | Verdict |
|---|---|---|
| Bornes légitimes (`MIN`/`MAX`/plancher/plafond) | ~60 | ✅ conformes — le dogme les autorise |
| Grandeurs dérivées du vécu | ~15 | ✅ le cœur de la thèse |
| Constantes de calibration | ~25 | 🟠 défendables, à assumer |
| **Récompenses posées** | **4** | 🔴 **violation** |
| **Noms du monde dans le cœur** | **7 sites** | 🔴 **violation** |
| Vestiges DoorKey | ~10 | 🟠 code mort à isoler |
| Seuil jamais atteint (`SEUIL_CRISTAL`) | 1 | 🟠 à retirer ou dériver |

---

## 4. Ce qu'il faut dire à un chercheur

**❌ Ne pas dire** : « rien n'est en dur ».
Réfutable en un `grep`, et la crédibilité ne s'en remet pas.

**✅ Dire** :

> « L'architecture ne contient **aucun seuil de déclenchement dans le chemin de
> décision** — c'est vérifiable et documenté, quatre propositions en ce sens ont été
> refusées explicitement. Les grandeurs d'apprentissage sont **dérivées du vécu de
> l'agent**, pas réglées : la même récompense vaut 100 % pour un débutant et 11 % pour un
> expert, sans qu'aucune règle ne le dise. Il subsiste **quatre récompenses posées** et
> **un jeu de constantes de calibration**, toutes localisées et documentées. Et la
> thèse défendue est **l'unification** — une seule règle de plasticité pour douze couches,
> un seul espace latent — pas la légèreté, qui n'est pas démontrée : l'agent est 2,85×
> plus lourd qu'un PPO CNN et **ne résout pas** `Empty-8x8`. »

Cette version **résiste à l'audit**. Elle est plus forte que « rien en dur », parce
qu'elle est vraie et qu'elle montre qu'on a compté.

---

## 5. Correctifs proposés, par rapport bénéfice/risque

| # | Correctif | Effort | Effet |
|---|---|---|---|
| 1 | **Corriger la phrase des deux README** | 10 min | ⭐⭐⭐ supprime la seule affirmation réfutable |
| 2 | Déplacer `COULEUR_FOOD/WATER` + test `ball` vers `bus_sensoriel.py` | 1 h | ⭐⭐⭐ rend « le cœur ne nomme rien » **vrai** |
| 3 | Isoler les vestiges DoorKey dans un module à part | 2 h | ⭐⭐ enlève l'air de solveur MiniGrid |
| 4 | Dériver `MALUS_DOULEUR` du coût métabolique réel | 3 h | ⭐⭐ supprime l'inversion mourir/se cogner |
| 5 | Retirer ou dériver `SEUIL_CRISTAL` | 1 h | ⭐ supprime un seuil mort |
| 6 | Dériver les 3 micro-récompenses | ~1 j | ⭐⭐ la violation la plus profonde |

**Le correctif n°1 est le seul indispensable avant de parler à quiconque.** Il ne coûte
rien et supprime le seul énoncé qu'un chercheur peut réfuter en une commande.

---

## 6. État scientifique du projet à cette date

Pour mémoire, et parce que ces chiffres doivent accompagner toute présentation :

- Niveau atteint : **4/15**, la lave franchie **par vitesse, pas par compréhension**
- **Couper C2 ne change le score de 0,0 point** sur 6 niveaux (78 cellules)
- **Grossir le cerveau n'apporte rien** : `r = +0,018`, IC95 [−0,45 ; +0,48], n=18
- La **valence de la lave** vient de devenir négative (**+0,062 → −0,753**) pour la
  première fois — canal validé, **effet comportemental non mesuré**
- Toute comparaison appariée **antérieure à la v41.9 est non concluante** (`env.reset()`
  n'était pas seedé)

C'est un **carnet de recherche ouvert**, pas un système livré — et c'est ce qui en fait
la valeur : les échecs y sont datés et chiffrés.
