# Point général du 7 septembre 2026 — où en est Naulthène, et ce qui ne va pas dans le bon sens

> **Photo horodatée**, jamais réécrite après coup. Descriptive et **non normative** : la
> référence factuelle reste [CHANGELOG.md](../fonctionnement/CHANGELOG.md) (149 entrées).
>
> Écrit à la demande de l'utilisateur (*« un point général du projet, ton avis sur la
> direction, et les éléments qui ne vont pas dans le bon sens »*), à partir de `readme.md`,
> `CLAUDE.md`, du CHANGELOG, de l'INDEX, du journal des runs, des 24 carnets de campagne, des
> plans v42 et du 05/09, et d'une **vérification directe sur les logs et le code** pour le
> point §3. Rédigé le 07/09/2026 à 10 h, pendant que la campagne `07092026_branches_persistantes`
> tourne (jour ~585/1500 à 09:48).

---

## 0. En une page

| | |
|---|---|
| **Où on en est** | `noyau.py` **v41.63** · 417 commits · 149 entrées de CHANGELOG · 42 instruments · **27 hypothèses** sur le plafond testées depuis le 23/08 |
| **Le blocage** | l'agent s'arrête à l'affichage **« Niveau 4/15 »**, qui est **`SimpleCrossingS9N1`** (voir §3) — 40 runs sur 40 en régime libre, 15/20 même avec les 8 époques |
| **Ce qui a marché** | **3 leviers**, tous trouvés entre le 03/09 et le 07/09, tous sur le **cœur RL** : voix libre (`gain_c1 ≡ 1`), `--detach-c2` (+5,25 pt), `--epoques-nuit 8` (+10,25 pt, 5/20 promus au niveau suivant) |
| **Ce qui n'a rien donné** | **tout ce qui a été ajouté au cerveau** entre la v29 et la v41.49 : 5 sens, thermoception, douleur, digestion, travail tenté, élan, rendement, bit de portage — 0 effet cognitif mesuré à n=20 |
| **Le meilleur actif** | la **méthode** (A/A, n≥20, Bonferroni, retrait des extrêmes, protocole écrit avant, journal des runs) — c'est elle qui a trouvé les 3 leviers et rétracté ~7 chiffres faux |
| **Ce qui ne va pas** | §5 : une **erreur de numérotation** qui a produit une fausse conclusion le 06/09 ; les **organes avant l'apprenant** ; une **neurogenèse aveugle** (56 % de neurones morts, 19 % du réseau jamais entraîné) ; un « script de référence » **fictif** ; une **dette documentaire** qui commence à coûter |

**Mon avis en une phrase** : le projet a passé six semaines à chercher *quel organe manquait*
alors que la réponse mesurée est que **l'apprenant sous les organes était infirme** (un pas de
gradient par jour, un critique qui mangeait 89 % du gradient partagé, une renormalisation qui
masquait l'atrophie). Les trois seuls résultats positifs du dépôt sont des **corrections de ce
learner**, pas des ajouts. La direction à prendre est donc : **réparer l'apprenant jusqu'à
parité avec PPO à budget égal, organes gelés, puis rallumer les organes un par un en exigeant
de chacun un effet ≥ 0.** C'est la « campagne de soustraction » proposée en août (P3) et jamais
faite.

---

## 1. L'état factuel

### 1.1 Les trois derniers jours — la semaine la plus productive du dépôt

| Date | Campagne | Résultat | n | Survit aux extrêmes ? |
|---|---|---|---|---|
| 03-04/09 | Voix libre (`gain_c1 ≡ 1`) | +19,5 pt au banc forcé ; en cursus, arrête l'**hémorragie** (9 témoins/20 à 0 % → 1) sans lever le mur | 20 | ❌ en cursus |
| 05/09 | Ablation propre de C2 (`--sans-c2`) | C2 est **inerte** (δ −1,4 pt NS) | 20 | — |
| 05/09 | Atrophie de C1 (zéro run) | boucle de compensation, `r(ΔC1, Δgain) = −0,75`, 20/20 | 20 | ✅ |
| 06/09 | `--detach-c2` | **+5,25 pt** de maîtrise, `t` +4,97, 16/20 | 20 | ✅ |
| 06/09 | Sondes (zéro run) | rollout effondré à 97 % par `argmax(tete_motrice)` ; politique de C1 **plate** (ratio inter/intra 3,91 vs 0,06 chez PPO) ; **56 % de neurones morts** | 40 | — |
| 07/09 | `--epoques-nuit 8` | **+10,25 pt**, `t` +4,81, 15/20 ; **5/20 promus** ; le clipping PPO **nuit** | 20×3 | ✅ (`t` +3,62) |
| 07/09 | Branches persistantes (v41.63) | 🟡 **en cours**, prédiction écrite : « effet peu probable » | 20 | — |

### 1.2 Ce que la campagne K8 dit de plus que son carnet

J'ai vérifié sur les logs **par quelle voie** les 5 cerveaux K8_NU ont été promus. Les cinq
(`g22`, `g44`, `g111`, `g177`, `g188`) l'ont été par la voie **maîtrise** — « régularité 60 % ×
20 épisodes », jamais par la série de 2 victoires. C'est un point **plus fort** que ne le dit
le carnet : en août, les 2 seuls passages au niveau suivant (v41.29) étaient passés par la
voie rapide et fragile.

### 1.3 Ce qui reste établi de la période 23/08 → 02/09

- Le cerveau est **sain** (0 synapse morte) mais **à moitié éteint** (56 % de neurones de
  `pensee_bio` toujours à zéro, 63 % dans le tronc — 40/40 cerveaux).
- La compétence est **réelle** (25,8 % contre 5,7 % pour un marcheur aléatoire sur
  `SimpleCrossingS9N1`) mais **brownienne** (14 à 18× le plus court chemin).
- L'agent optimise **un barème** : 95,6 % de son signal vient de constantes posées, le corps
  pèse **2,64×** la victoire dans le gradient. Ratio non tranché (pathologie ou homéostasie).
- **23 explications réfutées**, dont 2 tautologies et ~7 chiffres publiés rétractés.

---

## 2. 🔴 Le point qui change la lecture — les numéros de niveau

### 2.1 Ce que j'ai vérifié

Le code affiche le niveau **en base 1** :

```python
# noyau.py:11344
print(f"  ├─ Cursus         : 🎓 Niveau {etat.niveau_actuel + 1}/{len(PROGRAMME)} — "
```

| Index `PROGRAMME` | Affiché | Environnement | Nom du palier |
|---|---|---|---|
| 2 | Niveau 3/15 | `Empty-8x8` | Maternelle |
| **3** | **Niveau 4/15** | **`SimpleCrossingS9N1`** | Primaire 1 (Contourner) |
| 4 | Niveau 5/15 | `LavaGapS5` | Primaire 2 (Éviter le danger) |
| 5 | Niveau 6/15 | `Fetch-5x5-N2` | Primaire 3 |

Sur les logs :

- `LIBRE_g11` (témoin, bloqué « Niveau 4/15 ») : sa dernière promotion est
  *« L'Agent passe en **Primaire 1 (Contourner)** »*. Il joue `SimpleCrossingS9N1`.
- `K8_NU_g22` (promu « Niveau 5/15 ») : *« L'Agent passe en **Primaire 2 (Éviter le
  danger)** »*. Il vient d'**entrer** dans `LavaGapS5`, il ne l'a pas résolu.
- L'agrégat `agregat.json` porte `niv: 4` pour les témoins, la valeur **affichée**.

**Le mur est `SimpleCrossingS9N1`. Il ne l'a jamais été `LavaGapS5`.**

### 2.2 Où le décalage est entré, et ce qu'il a produit

Les carnets d'août avaient la bonne carte : l'audit du génome (30/08) note « N3
`SimpleCrossingS9N1` *(le plafond)* », le plancher (30/08) mesure la compétence « là où
l'agent bloque — `SimpleCrossingS9N1` », le CLAUDE.md dit « la lave n'apparaît qu'au niveau 5
et l'agent est bloqué au 4 ». Le décalage apparaît le **05/09** dans le PLAN (§4 : « le
niveau 4, où 40 runs sur 40 s'arrêtent, est `MiniGrid-LavaGapS5-v0` ») et se propage :

| Document | Affirmation | Statut |
|---|---|---|
| `PLAN_05092026` §4 | le mur est `LavaGapS5` | ❌ faux |
| `PPO_LAVAGAP_06092026` | « PPO résout `LavaGapS5` à 97 % là où Naulthène ne passe jamais » ; « `SimpleCrossing` = niveau 3, que Naulthène franchit 20/20 » | ❌ la mesure est juste, la **conclusion est fausse** : PPO a été testé **une carte trop loin** |
| CHANGELOG `v41.60-mesure` | « l'écart se creuse : 2,3× au niveau 3, essentiellement tout au niveau 4 » | ❌ |
| `JOURNAL_DES_RUNS` | « PPO au niveau du mur » | ❌ |
| `readme.md` l. ~490 | « Naulthène never clears it. At level 3 the gap was 2.3×; at level 4 it is 14.6× » | ❌ **publié sur la vitrine** |
| `readme_fr.md` l. 248 | « **Naulthène n'y franchit jamais.** Au niveau 3 l'écart… » — le miroir exact | ❌ **publié sur la vitrine** |
| `EPOQUES_07092026` | « 5 cerveaux franchissent le niveau 5 » | 🟡 ambigu — ils **atteignent** le niveau 5 (ils franchissent le 4) |

### 2.3 Ce que ça change

1. **« Le mur n'est pas la carte » n'a pas été testé.** La question reste ouverte, mais la
   donnée pour y répondre **existe déjà** : la baseline du 29/08 a mesuré PPO **sur
   `SimpleCrossingS9N1`**, la vraie carte du mur — **27 à 40 %** de réussite à 152 k pas, contre
   25,8 % pour les cerveaux Naulthène au banc (A_g66 : 37 %). L'écart au mur n'est pas 14,6×,
   il est **~1,5×**, et à un budget PPO 4× plus petit que la vie d'un cerveau.
2. **Le seuil de promotion (60 % sur 20 épisodes) est au-dessus de ce que PPO atteint sur
   cette carte à ce budget.** Un PPO standard mis dans ce cursus resterait lui aussi au
   « niveau 4 » avec 152 k pas. Le mur est donc **en partie une règle du cursus**, pas
   seulement une pathologie du cerveau. Ce n'est pas un blanc-seing pour Naulthène (PPO
   converge, Naulthène reste brownien) mais la phrase « le plafond est une pathologie de cette
   architecture » est **plus forte que ce qui est mesuré**.
3. **Les mécaniques « lave » (v41.11 → v41.27) n'ont jamais été dans le chemin du mur.**
   Cinq versions de thermoception, nociception, douleur unique, pour une carte que l'agent
   n'atteint qu'en K8 et sur 5 cerveaux. C'est cohérent avec « `Bio` pèse 57 % du gradient et
   n'explique rien » — mais ça devait être su avant de les construire.

⚠️ Ce point est une **lecture des logs et du code**, pas une campagne. Il demande : (a) une
correction des 6 documents ci-dessus avec l'ancien texte en regard (Règle de Trace §1),
(b) une convention écrite **une fois pour toutes** — je propose de toujours écrire
`niveau 4/15 (SimpleCrossingS9N1)`, l'env_id entre parenthèses, puisque c'est la seule donnée
non ambiguë (c'est déjà ce que fait `persistance` pour le remappage).

---

## 3. Mon avis sur la direction

### 3.1 Les seuls leviers sont des corrections de l'apprenant — 3 sur 3

| Levier | Nature | Ce qu'il répare |
|---|---|---|
| Voix libre | retirer une renormalisation | C1 s'atrophiait en silence |
| `--detach-c2` | couper un gradient parasite | le critique mangeait 89 % du gradient partagé |
| `--epoques-nuit 8` | faire plus de pas d'optimiseur | 1 pas/jour contre 23 680 pour PPO |

Aucun n'ajoute quoi que ce soit au cerveau. Chacun **retire un obstacle à l'apprentissage**.
À l'inverse, les 20 mécaniques ajoutées de la v29 à la v41.49 n'ont produit **aucun effet
cognitif mesuré**. Ce n'est pas un hasard de six semaines : c'est une propriété du projet
telle qu'il a été construit — **la superstructure a été érigée sur un apprenant qui ne
pouvait pas apprendre**, et chaque organe a été jugé sur un juge que l'apprenant plafonnait.

### 3.2 Conséquence : une partie des 23 réfutations sont des faux négatifs candidats

Toutes les réfutations d'avant le 03/09 ont été mesurées avec **les trois pathologies
actives** (1 pas/nuit, gradient de C2 sur la couche partagée, renormalisation de C1). Une
mécanique jugée « sans effet » sur un apprenant qui ne bouge pas de toute façon n'a pas été
jugée. Ça ne les rouvre pas toutes — ça impose de les **reclasser** :

| Réfutation | Retester sous K8 + detach + libre ? | Pourquoi |
|---|---|---|
| **Tronc connecté** (attention descendante) | 🟢 **oui, en priorité** | c'est le seul mécanisme qui ferait que la perception soit sculptée par la décision ; il a été testé au régime témoin, avec un C1 qui s'atrophiait, et le carnet PLATITUDE le liste comme candidat (c) non testé |
| Crédit temporel (TD/GAE) | 🟡 peut-être | mesuré « moins mauvais » à 1 pas/nuit ; à 8 pas la variance de MC coûte plus |
| Coefficient d'entropie | 🟡 peut-être | à 1 pas son gradient pesait 1 % ; c'est mécanique, ça change avec K |
| Bit de portage, élan, rendement | ⚫ non | le verdict « l'information est là, le réseau ne s'en sert pas » tient ; c'est le réseau qu'il faut réparer |
| Curiosité, barème, récompense creuse, métabolisme | ⚫ non | tautologies ou prémisses fausses, indépendantes du régime |

### 3.3 La neurogenèse va dans le mauvais sens

Trois mesures indépendantes convergent :

- **56 % des neurones** de `pensee_bio` sont toujours à zéro (40/40 cerveaux).
- **19 % du réseau** (l'hémisphère audio) n'a **jamais reçu un gradient** sur 80 cerveaux —
  et grandit quand même, parce que la fusion des sens est une addition qui impose
  `dim_bus` à toutes les couches.
- `r(dim_bus, victoires) = +0,68` > `r(dim_bus, maîtrise) = +0,50` : **le bus mesure la
  survie**, pas la compétence.

Le mécanisme dépense donc du calcul (24× la taille de naissance, 1,3 M de paramètres, un
run de 6 h là où PPO en fait 40 min) pour de la capacité qui s'éteint. Le thermostat d'erreur
JEPA déclenche une croissance **globale et aveugle** : c'est le contraire de la neurogenèse
biologique, qui est locale et sélectionnée par l'usage. Deux questions à coût zéro avant
tout chantier : les neurones morts le sont-ils **à la naissance** (init Xavier + ReLU) ou
**meurent-ils** au fil des nuits (érosion sans myéline) ? Et la proportion croît-elle avec
chaque neurogenèse ? La réponse dit s'il faut corriger l'init, l'érosion, ou le déclencheur.

### 3.4 La thèse contre les mesures

La thèse — *un cerveau complet en attente d'un corps* — est belle et défendable. Mais le
dépôt dit maintenant, chiffres à l'appui : C2 est inerte, les 5 sens sont sans effet, l'audio
n'a jamais appris, le corps pèse 2,6× la tâche sans rien expliquer, et PPO sans aucun organe
fait ~1,5× mieux au mur avec 4× moins de paramètres et 4× moins de pas. **Continuer à
construire des organes maintenant, c'est construire sur du sable.** Ce n'est pas abandonner
la thèse : c'est la mettre dans le bon ordre. Un cerveau complet se juge à ce que chaque
organe **apporte** à un apprenant qui fonctionne — aujourd'hui personne ne peut le mesurer.

C'est pour ça que la piste v42 (tête d'intention de C2) me paraît **prématurée**, même si
elle est la plus fidèle à la thèse. Son propre carnet dit que PPO n'a pas de C2, que le
gradient de C2 nuisait, et que la campagne prérequis en cours a un « effet peu probable ».
Elle n'est pas fausse, elle est **troisième**, derrière la réparation de l'apprenant et la
campagne de soustraction.

### 3.5 Sur K = 8 et le clipping — ne pas dériver trop tôt

Le résultat est solide, mais **un seul point** (K=8, ε=0,2) a été mesuré. Avant de
« dériver » K de la plasticité (méthode v30.1, à raison) : un **balayage** K ∈ {2, 4, 16, 32}
pour savoir si l'effet est monotone, sature, ou se retourne (sur-apprentissage d'une journée
de 400 ticks). Et pour le clipping, ε ∈ {0,5 ; 1,0} avant de conclure que « le garde-fou de
PPO nuit » — à ε=0,2 avec un `lr` calibré pour 1 pas, il est possible que le clip ne fasse
que **ramener K8 vers K1**, ce qui n'est pas la même chose que « nuire ».

---

## 4. Ce qui ne va pas dans le bon sens — la liste

Classée par ce que ça coûte si on ne le corrige pas.

1. 🔴 **L'off-by-one de niveau** (§2). Une fausse conclusion publiée jusque sur la vitrine,
   un plan réordonné dessus, et cinq versions de mécaniques « lave » construites pour une
   carte hors du chemin. À corriger **avant** toute autre écriture.
2. 🔴 **Les organes avant l'apprenant** (§3.1, §3.4). Six semaines d'ajouts à effet nul, trois
   jours de corrections à effet mesuré. L'ordre est à inverser explicitement, dans CLAUDE.md.
3. 🔴 **La neurogenèse aveugle** (§3.3). Le mécanisme le plus coûteux du projet produit de la
   capacité morte, et il n'a **aucun témoin** (`dim_bus` figé) à n=20.
4. 🟠 **`colab.py` « script de référence » en v17** quand `noyau.py` est en v41.63. Le CLAUDE.md
   consacre des paragraphes entiers à un portage qui n'a jamais eu lieu et n'aura pas lieu.
   Décider : `noyau.py` **est** la référence, `colab.py` devient une archive datée. C'est une
   ligne à écrire, pas un chantier.
5. 🟠 **La dette documentaire commence à coûter.** `CLAUDE.md` fait **1 060 lignes** et
   contient des paragraphes de résultats de campagne qui appartiennent aux carnets ; le README
   « court et factuel » fait 896 lignes ; le CHANGELOG 8 957. Chaque session relit tout ça, et
   les règles se perdent dans le bruit : **aujourd'hui même**, la v41.63 (un `feat` sur
   `noyau.py`) n'a **pas d'entrée CHANGELOG**, et l'en-tête de `noyau.py` dit encore
   `41.59` — exactement la dérive corrigée le 02/09. Proposition : CLAUDE.md = règles + liens ;
   un seul `ETAT_COURANT.md` de 60 lignes, réécrit à chaque campagne, pour l'état.
6. 🟡 **Le juge principal est faible.** La maîtrise est quantifiée à 5 % (fenêtre de 20),
   n'explique que 16 % de la variance de la compétence réelle, et le juge « niveau » est
   saturé. Chaque campagne devrait ajouter un **banc final standard** : 300 épisodes forcés
   sur `SimpleCrossingS9N1` **et** sur le niveau suivant, avec l'instrument corrigé du 02/09.
   Il existe (`evaluer_cerveau`), il n'est pas systématique.
7. 🟡 **Les témoins recyclés entre versions.** K8 a réutilisé le bras LIBRE du 04/09 (code
   v41.54) comme témoin d'un code v41.62 ; BP réutilise K8_NU. Le test « K=1 bit-identique,
   9 lignes clés » a été fait et c'est ce qui rend la pratique acceptable — mais il doit
   figurer **dans le journal des runs**, pas seulement dans un LISEZ_MOI, et « 9 lignes » sur
   1500 jours est un contrôle mince. Une paire A/A complète (60 jours) coûte 10 minutes.
8. 🟡 **Le coût de calcul monte.** Une campagne de 20 paires prend 6 à 8 h parce que le
   cerveau grossit à 1,3 M de paramètres et que la queue des 1500 jours est la plus lente.
   `brains/` fait 4,2 Go, `wandb/` 6,3 Go (purgeable, les runs sont en ligne).

---

## 5. Ce que je ferais, dans l'ordre

| # | Action | Coût | Ce qu'elle tranche |
|---|---|---|---|
| 1 | **Corriger l'off-by-one** dans les 6 documents (ancien texte en regard), fixer la convention « niveau N/15 (env_id) », entrée CHANGELOG v41.63, en-tête `noyau.py` | 1 h, zéro run | la vitrine ne ment plus |
| 2 | **PPO à budget égal sur `SimpleCrossingS9N1`** (600 k pas, 5 graines) et compter combien de fenêtres de 20 épisodes passent 60 % | ~1 h | le mur est-il la règle du cursus, la carte, ou le cerveau ? |
| 3 | **Balayage K** {2, 4, 16, 32} et ε {0,5 ; 1,0}, cerveaux neufs, 20 graines par bras | 2 × 6 h | la forme de l'effet avant de le dériver |
| 4 | **Campagne de soustraction** (P3, jamais faite) : sous le meilleur régime, bras « vue seule + corps constant + C2 coupé » contre bras complet | 6 h | ce que la superstructure **apporte ou coûte** — la mesure la plus informative du dépôt |
| 5 | **Neurones morts** : à la naissance ou au fil de la vie, par nuit, par neurogenèse (zéro run) puis, selon la réponse, témoin `dim_bus` figé | 0 puis 6 h | si la neurogenèse est un frein |
| 6 | **Tronc connecté sous K8 + detach** | 6 h | le premier faux négatif candidat |
| 7 | Décision `colab.py` ; CLAUDE.md réduit aux règles ; `ETAT_COURANT.md` | 2 h | la dette |
| 8 | **Tête d'intention v42** — après 4 et 6, si C2 a encore une raison d'exister | 8 h + code | la thèse |

Les points 1, 2, 5 et 7 ne demandent aucune décision : ils ne changent rien au cerveau. Les
points 3, 4, 6 sont des campagnes à protocole écrit d'avance, dans l'ordre. Le point 8 est
une décision utilisateur, et je recommande de la prendre **après** le 4.

---

## 6. Limites de ce point

- Je n'ai pas relu les 12 800 lignes de `noyau.py` ; l'off-by-one est vérifié sur la ligne
  d'affichage, deux logs de promotion, et l'agrégat. Je n'ai pas vérifié les 15 entrées du
  `PROGRAMME` une à une dans chaque carnet.
- Les chiffres PPO sur `SimpleCrossingS9N1` (27–40 %) viennent du carnet du 29/08, à 152 k
  pas ; je n'ai pas relancé le banc. Le point 2 ci-dessus est précisément la mesure manquante.
- La campagne des branches persistantes n'est pas finie ; rien ici n'en préjuge.
- « Prématurée » pour la v42 est un jugement d'ordre, pas de valeur : il se réfute par une
  campagne de soustraction qui montrerait que C2, une fois l'apprenant réparé, apporte quelque
  chose.

---

*Photo arrêtée au 07/09/2026, 10 h. Pour l'état courant, voir le CHANGELOG — une fois
l'entrée v41.63 écrite.*
