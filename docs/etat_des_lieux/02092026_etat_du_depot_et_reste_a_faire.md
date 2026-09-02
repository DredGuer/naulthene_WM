# État du dépôt au 2 septembre 2026 — 21 réfutations, et ce qui reste à faire

> **Photo horodatée**, jamais réécrite après coup. Descriptive et **non normative** : la
> référence factuelle reste [CHANGELOG.md](../fonctionnement/CHANGELOG.md) (138 entrées).
>
> Écrite après le rangement du dépôt (21 branches archivées) pour répondre à une question
> simple : **où en est-on, et que reste-t-il à faire ?**

---

## 1. L'état en une page

| | Valeur | Lecture |
|---|---|---|
| **Version** | `noyau.py` **v41.50** · `colab.py` **v17** | le portage noyau → colab n'a **jamais** eu lieu |
| **Branches** | **1** (`master`) | 21 archivées ce jour, 0 commit orphelin |
| **Entrées CHANGELOG** | 138 | |
| **Explications du plafond mesurées puis réfutées** | **21** | le tableau des suspects est **vide** |
| **Mécaniques cognitives ayant amélioré quelque chose** | **0** | les 2 seuls leviers sont des propriétés du **monde** |
| **Niveau atteint** | **4/15** sur 10 graines / 10 | le blocage s'est **déplacé** (était 1/15) |

### Ce qui est acquis, et solide

1. **Le cerveau est sain.** 0 synapse morte (contre 13 769 en médiane avant v37), bus grandi
   de 16 → 64 dims, aucune couche éteinte. Le blocage **n'est pas une panne**.
2. **La compétence est réelle** — mesuré le 30/08. Sur `SimpleCrossingS9N1`, un marcheur
   aléatoire fait **5,67 %** quand les cerveaux entraînés font **25,83 %** agrégé
   (`z = +13,56`), l'un d'eux **37,33 %** — dans la fourchette de PPO (27–40 %).
3. **Le mur informationnel de MiniGrid n'existe pas.** Un PPO **4× plus léger** réussit
   **2,3× mieux** : le plafond est une pathologie de **cette architecture**, pas de la tâche.
4. **La méthode expérimentale est devenue le vrai actif du dépôt** — A/A avant tout A/B,
   n ≥ 20, Bonferroni, témoin non nul, et trois dogmes écrits (*rien en dur*, *rien sans
   témoin*, *rien sans écrit*).

### Ce qui bloque

- **Aucune cause mesurée ne survit.** 21 explications réfutées, dont **deux tautologies**
  (le ratio C2/C1, puis le barème) et **cinq chiffres publiés rétractés** en une semaine.
- **C2 reste causalement déconnecté** : le couper ne change le score de **0,0 point** sur
  6 niveaux (78 cellules).
- **Les victoires sont browniennes** : 14,2× à 18,1× le plus court chemin.

---

## 2. Le motif qui a émergé — et qui oriente la suite

C'est le résultat le plus important des trois derniers jours, et il n'est pas un chiffre
mais une **forme** :

> Qu'on **retire** du signal (curiosité, barème, rendement mécanique) ou qu'on en
> **ajoute** (bit de portage, élan cinématique), **le comportement ne bouge pas.**

L'ancrage cinématique (v41.49) était censé être différent — il *ajoutait* une information
égocentrique réelle. Les **deux juges fixés d'avance** sont négatifs.

**L'hypothèse qui survit** : ce n'est ni le signal d'apprentissage, ni l'information
disponible qui limite l'agent, mais **sa capacité à convertir une information disponible en
politique**. `integrateur_bio` reçoit déjà 44 dimensions ; **la 45ᵉ ne change rien.**

⚠️ Conséquence directe pour toute idée neuve : **une piste qui consiste à ajouter une
dimension en queue du vecteur bio est réputée morte jusqu'à preuve du contraire.** Deux ont
été mesurées à n=20, deux effets nuls.

---

## 3. Ce qui reste ouvert — les 5 chantiers, classés par ce que la mesure justifie

### 🥇 1. La conversion information → politique *(ce que le motif désigne)*

Le seul chantier que la mesure **désigne** plutôt que suggère. Rien n'est spécifié : c'est
la question à instruire, pas une solution à coder.

- **Ce qu'on sait** : l'information est là, elle n'est pas convertie.
- **Ce qu'on ne sait pas** : si c'est une question de **capacité** (le réseau ne *peut* pas),
  d'**objectif** (rien ne l'y pousse), ou d'**échelle de gradient**.
- ⚠️ **Ne pas coder avant d'avoir formulé un juge falsifiable**, comme pour la brique B.

### 🥈 2. La directivité — symptôme ou levier ?

Le **seul prédicteur significatif** du dépôt, mais **requalifié à la baisse** le 02/09 après
le rejeu à instrument corrigé :

| | 30/08 (banc amputé) | **02/09 (corrigé, n=20)** |
|---|---|---|
| global | −0,8225 (`t` = −5,96) | **−0,6794** (`t` = −3,93) ✅ |
| sans les 4 extrêmes | −0,789 ✅ | **−0,478** (`t` = −2,04) ❌ **NS** |
| variance expliquée | 68 % | **46 %** |

⚠️ **Corrélationnel, causalité non établie** — et v41.47 a mesuré qu'à λ=0,9 la *meilleure*
directivité allait avec le *pire* succès. Trancher **symptôme vs levier** est un chantier en
soi, et il conditionne le n°1.

### 🥉 3. Le portage `noyau.py` → `colab.py` *(dette structurelle)*

`colab.py` est en **v17** : **aucune** mécanique de v18 à v41.50 n'y a été portée. Le script
présenté comme « de référence » ne reflète plus rien de ce que fait le projet.

Deux options honnêtes, à arbitrer : **(a)** porter, mécanique par mécanique ; **(b)** acter
que `noyau.py` **est** la référence et rétrograder `colab.py` en archive. Continuer à
l'appeler « référence » sans le mettre à jour est la seule option à écarter.

### 4. P17 — le cursus gaussien *(implémenté, jamais évalué)*

Le palier joué est **tiré au sort** autour du niveau courant, au lieu d'un pointeur qui ne
recule jamais. Vit dans `experiences/v39/v39_p17_gaussienne.py`, **hors du noyau**, et n'a
**aucune entrée au CHANGELOG** — donc jamais mesuré à n ≥ 20.

### 5. La dette documentaire *(petite, mais elle ment)*

- `CHANTIER_v41.4_…` et `CHANTIER_v41.6_P17_…` annoncent une *« campagne en cours (15/08) »*
  — depuis **18 jours**. À clore ou à requalifier.
- 4 dossiers de `brains/` sans `LISEZ_MOI.md`, dont 3 antérieurs à la convention
  (`ablations/`, `cas_isole_*`, `old_testV30-V34`).

---

## 4. Ce qu'il ne faut PAS refaire

Le coût le plus cher du dépôt est de reprendre une piste morte. Les 21 réfutations sont dans
[`enquetes_closes/`](../recherche/enquetes_closes/) et [`campagnes/`](../recherche/campagnes/) ;
les plus coûteuses à retester :

| Piste | Verdict |
|---|---|
| Thrashing du gradient · crédit temporel (TD/GAE) | ❌ le code actuel est le **moins mauvais** |
| Attention descendante · dérive de représentation | ❌ bruit +48 % · PPO dérive 10× **plus** en réussissant mieux |
| Coefficient d'entropie · métabolisme | ❌ 0,44–1,05 % du gradient · `r = −0,0588` à n=20 |
| Curiosité · récompense creuse · barème | ❌ rente sans effet · prémisse **fausse** (86 % dense) · **tautologie** |
| Ajout d'une dimension en queue du vecteur bio | ❌ **2 fois mesuré, 2 effets nuls** |

**Deux règles de méthode nées de ces échecs :**

1. **Une métrique dérivée de la récompense ne peut pas prédire la réussite** — la récompense
   *est* la réussite. Test : conditionner sur « a gagné au moins une fois » et voir si le
   signal survit.
2. **Un garde-fou de forme doit CRIER quand il rejette.** Une sonde lisait la mémoire de
   travail au mauvais index et un garde-fou la rejetait **en silence** : tous les chiffres de
   banc des 30-31/08 décrivaient un agent **sans mémoire de travail**. Ni l'A/A
   (δ = 0,000000) ni 20 graines ne l'ont attrapé — le banc était déterministe et
   reproductible, il mesurait simplement **autre chose que ce qu'il annonçait**.

---

## 5. L'état du dépôt lui-même

| | Avant | Après |
|---|---|---|
| Branches locales | 22 | **1** (`master`) |
| Branches distantes | 22 | 22 — ⏳ **suppression à faire par toi** |
| Commits hors `master` | **0** | 0 |
| Arbre de travail | propre | propre, synchro `origin/master` |

Les 21 branches locales ont été supprimées avec `git branch -d` (mode sûr, refuse toute
branche non mergée) après vérification que **chaque tip est un ancêtre de `master`**. Leurs
SHA sont consignés dans [branches archivées](02092026_branches_archivees.md).

⏳ **Reste à faire, côté distant** — la suppression des 21 branches sur `origin` n'a pas été
exécutée (action irréversible et sortante) :

```bash
git branch -r --format='%(refname:short)' | grep -v HEAD | grep -v '^origin/master$' \
  | sed 's|^origin/||' | xargs -n1 git push origin --delete
```

**Volumes locaux** (hors git, sains) : `brains/` **1,8 Go** · `wandb/` **2,8 Go** ·
`venv/` 529 Mo. Correctement gitignorés — rien de tout cela n'est ni ne doit être versionné.
Le `wandb/` local (906 runs) peut être purgé sans perte : les runs sont sur le projet public.

---

*Photo arrêtée au 02/09/2026. Pour l'état courant, voir le CHANGELOG.*
