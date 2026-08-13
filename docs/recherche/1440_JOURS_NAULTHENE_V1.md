# 1440 Jours de Naulthène — Analyse du Run « Bébé Développemental 4 ans » (V1)

Analyse du run **`Run_25_Bebe_Developpemental_4ans`** (`cursus_bebe.py`, v25.0 expérimental,
commit `d89fce1`, 1440 jours × 3600 ticks ≈ 5,18 millions de ticks, ~9 h 40 sur Apple M3 Pro).

Ce document se lit en parallèle de [explications_readme.md](../fonctionnement/explications_readme.md) : chaque
observation renvoie à la section d'algorithme qui l'explique (JEPA §2, dopamine §9, rêve §10,
neurogenèse §8.4…). Les métriques citées proviennent directement du datastore W&B du run
(`wandb/run-20260724_091053-u773ulep/`) et du `output.log` console (20 541 lignes).

> **TL;DR.** Le paradigme développemental *fonctionne comme prototype* — il produit une
> trajectoire d'âge lisible, une phase auto-supervisée qui fait chuter l'erreur JEPA de 2,3 → 0,2
> **sans aucune récompense externe**, et un déverrouillage social au jour 240 qui débloque
> instantanément la progression. Mais le run se termine sur un **cerveau cliniquement figé** :
> erreur JEPA effondrée à 0,0000, plasticité résiduelle 0,14, rêve à 0,38 % de la journée,
> **zéro victoire MiniGrid sur les 983 derniers jours**, et 18 164 synapses mortes. Le bébé a
> « grandi » dans ses compteurs administratifs (paliers, niveaux) sans jamais résoudre réellement
> la tâche. C'est un **effondrement de représentation lent** (§ 3) doublé d'un **découplage
> promotion / compétence** (§ 2).

---

## Table des matières

1. [La trajectoire de vie du bébé — ce qui a marché](#1-la-trajectoire-de-vie-du-bébé--ce-qui-a-marché)
2. [Le découplage promotion / compétence — le problème central](#2-le-découplage-promotion--compétence--le-problème-central)
3. [L'effondrement lent du modèle du monde (JEPA collapse)](#3-leffondrement-lent-du-modèle-du-monde-jepa-collapse)
4. [Points forts confirmés par les chiffres](#4-points-forts-confirmés-par-les-chiffres)
5. [Axes d'amélioration, priorisés](#5-axes-daméliorations-priorisés)
6. [Mise en parallèle avec les méthodes de référence (Transformer, JEPA, MuZero, RL classique)](#6-mise-en-parallèle-avec-les-méthodes-de-référence)
7. [Verdict et prochain run recommandé](#7-verdict-et-prochain-run-recommandé)

---

## 1. La trajectoire de vie du bébé — ce qui a marché

Le squelette narratif tenu par le run est propre et lisible — c'est le premier succès. Les cinq
phases (`BORNES_PHASES_BEBE`) se sont enchaînées, et les deux curriculums (MiniGrid + vocal)
ont progressé **en parallèle** comme prévu.

| Jour | Événement | Ce que ça valide |
|---|---|---|
| J1 | Naissance (Bus=16), Phase « Éveil des Sens » | Démarrage masqué (`masquer_recompense_externe=True`) |
| J39 | **Neurogenèse 16 → 32 dims** (`agrandir()`, §8.4) | Le thermostat JEPA a bien fait grandir le cerveau **une fois** |
| J73–93 | Voyelles a, e, i (paliers vocaux 2→4) | Le curriculum vocal apprend **pendant le masquage total** |
| J221 | Voyelle o (palier 5) | |
| **J240** | **Fin du masquage + Module Parent activé + passage en Collège le même jour** | Le déverrouillage social débloque tout d'un coup |
| J331 | Voyelle u (palier 6) | |
| J445–456 | **Lycée → Université → Doctorat en 11 jours** | Rush de promotions dès que la récompense compte |
| J609–846 | Syllabes ba, ma, pa → mot « papa » (paliers 7→10) | Le vocal continue jusqu'au premier mot |
| J846→J1440 | **Plus aucune promotion, ni MiniGrid ni vocale** | Plateau terminal |

**Le fait le plus intéressant scientifiquement** : pendant les 240 premiers jours, avec
`Recompense_Moyenne = 0` **strictement** (masquage), l'erreur JEPA moyenne chute de **1,49
(phase Éveil) à 0,196 (juste avant le déverrouillage)**. Autrement dit, l'agent a construit un
modèle du monde utilisable **sans jamais savoir s'il agissait bien ou mal** — uniquement via JEPA
+ curiosité + homéostasie. C'est exactement la thèse développementale du projet (Piaget/Dehaene,
cf. [explications_readme §1](../fonctionnement/explications_readme.md)), et le run en apporte une démonstration
empirique nette. C'est le résultat à garder.

---

## 2. Le découplage promotion / compétence — le problème central

C'est **le** point critique du run. Voici la mesure qui doit inquiéter :

```
Recompense_Moyenne  : somme sur 1440 jours = 0.00   (nonzero_jours = 0)
Victoire            : 19 jours au total, TOUS entre J240 et J457
                      → 0 victoire sur les 983 derniers jours
```

Pourtant, sur cette même période, l'agent est officiellement passé **Collège → Lycée →
Université → Doctorat** et a franchi **7/7 paliers DoorKey**. Comment progresser dans le cursus
sans jamais gagner ?

Parce que **deux systèmes de promotion coexistent et ne mesurent pas la même chose** :

- La **promotion de niveau** (`VICTOIRES_REQUISES=2`, [explications §11.1](../fonctionnement/explications_readme.md))
  exige de vraies victoires. Elle n'a fonctionné que dans la fenêtre J240–457, où l'on compte
  effectivement 19 jours-victoire — cohérent.
- Mais les **7 paliers DoorKey** (`DetecteurJalonsDoorKey`, [explications §11.3](../fonctionnement/explications_readme.md))
  valident sur des *jalons cognitifs partiels* (s'approcher, toucher, viser la porte…), pas sur la
  sortie réelle. Les logs montrent les 7 paliers validés **en bloc autour du J240**, portés par le
  mécanisme d'Abnégation (4 succès en 2 sous-seuils) — sans que `Recompense_Moyenne` ne décolle
  jamais de 0.

Le symptôme chiffré est sans appel :

```
Portes_Franchies_Jour : 6218 portes franchies au total (moy 6,3/j en fin de run)
Recompense_Moyenne    : 0.000 partout
Taux_Maitrise_Palier  : dernier point loggé (J446) = 0.083  → 8 %
```

**L'agent franchit des milliers de portes mais ne sort jamais du labyrinthe.** Il a appris les
sous-comportements (approcher, ouvrir) sans jamais les **chaîner** jusqu'à l'état terminal
gagnant. La progression de niveau est donc en grande partie **administrative** : les compteurs
de paliers montent, la compétence réelle (mesurée par la victoire) reste plate à zéro après J457.

> **Pourquoi c'est grave pour ce projet précisément.** Tout l'argumentaire de Naulthène (cf.
> [explications §1](../fonctionnement/explications_readme.md)) est *« ne pas optimiser un seul chiffre récompense,
> faire émerger la compétence de signaux complémentaires »*. Ici, le run tombe dans une variante
> du même piège : les **détecteurs de progrès génériques** (records de proximité, portes) sont
> devenus la *vraie* fonction-objectif de fait, et l'agent les sature (72 records/jour, 6 portes/jour)
> **au lieu** de résoudre la tâche. C'est du *proxy-hacking*, cousin du reward-hacking que le projet
> voulait éviter.

---

## 3. L'effondrement lent du modèle du monde (JEPA collapse)

Le second problème structurel. Regardons l'erreur JEPA moyenne par période :

```
P0 « Éveil »      (J1-90)     : 1.4938
avant déverr.     (J90-240)   : 0.1961
post-déverr.      (J240-720)  : 0.1551
J720-1000                     : 0.1619
FIN (J1000-1440)              : 0.0011   ← quasi zéro
```

Une erreur JEPA qui tend vers **0,0000** n'est *pas* une bonne nouvelle ici. C'est précisément le
**representation collapse** que le stop-gradient de JEPA est censé prévenir
([explications §2.2](../fonctionnement/explications_readme.md)). Le prédicteur `generateur_attente` et l'encodeur
`porte_visuelle` ont convergé vers une représentation **triviale et quasi constante** : prédire
« rien ne change » devient trivialement exact quand la politique est devenue elle-même quasi
déterministe et répétitive. La cible `ReLU(porte_visuelle(obs_suivante))` a cessé de bouger, donc
le MSE tombe à zéro sans qu'aucune information nouvelle ne soit apprise.

La cascade que cela déclenche est mécanique et se lit directement dans les autres métriques
([explications §8, §9, §10](../fonctionnement/explications_readme.md)) :

```
Erreur JEPA → 0
   └─► thermostat neurogenèse jamais réarmé  (erreur < seuil ⇒ pas d'agrandir())
        → Bus reste bloqué à 32 dims tout du long (DIM_BUS_MAX=96 jamais approché)
   └─► importance des souvenirs → 0   (importance = |r_interne| + 2·L_JEPA + … , §10.2)
        → Pourcentage_Reve s'effondre : 40-50 %/nuit (J240-1000) → 0,38 %/nuit (J1440)
        → Nb_Reves : ~1000/nuit → 43/nuit
   └─► plus de curiosité (r_curiosite ∝ L_JEPA, §2.4) → dopamine retombe
        → Teneur_Dopamine : 6,0 (post-déverr.) → 4,23 (jeune enfant) → 2,4 (fin)
        → plasticite_base : 1,00 → 0,14
```

L'état terminal J1440 est celui d'un système **cliniquement mort d'un point de vue apprentissage** :

```
Erreur JEPA moy : 0.0000     |  Plasticité base : 0.14
Pourcentage rêve: 0.377 %    |  Dopamine : 2.41/10 (24 %)
Abandons lucides: 0          |  Sursauts de Volonté : 0
Synapses mortes : 18 164     |  Satiété / Stimulation : 0.00
```

Le compteur de **synapses mortes** (`base_weight < 1e-4` mis à zéro au cycle de sommeil,
[explications §8.2](../fonctionnement/explications_readme.md)) raconte la même histoire : **7 100 dès le J240**
(juste après le déverrouillage), **18 164 en fin**. L'érosion nocturne, non compensée par de la
neurogenèse ni par une plasticité soutenue, a lentement vidé le réseau.

---

## 4. Points forts confirmés par les chiffres

Malgré l'issue, plusieurs mécanismes du projet ont fait **exactement** ce pour quoi ils sont conçus.

1. **L'auto-supervision pure marche (§1 + §2 explications).** Chute JEPA 1,49 → 0,20 avec
   `Recompense_Moyenne ≡ 0` sur 240 jours. La preuve empirique que le socle JEPA+homéostasie peut
   structurer une représentation sans récompense — le cœur du pari développemental.

2. **Le déverrouillage social est un vrai levier (§9, §11).** Les 19 jours-victoire et le rush
   Collège→Doctorat démarrent **au jour 240 exact**, à la levée du masquage. Le signal externe,
   même parcimonieux, débloque une progression que l'auto-supervision seule ne produisait pas.
   C'est un argument fort *pour* le paradigme « masquer puis révéler ».

3. **La dopamine homéostatique est stable et bornée (§9).** `Teneur_Dopamine` reste dans
   `[0.001, 10]` tout du long, oscille proprement (8,0 masquage / 2,0 hors événement) sans jamais
   diverger. Le clip et les trois forces de relaxation font leur travail.

4. **Le curriculum vocal progresse graduellement et sans triche.** 10 paliers franchis (jusqu'au
   mot « papa »), chacun validé par un score de formants qui **monte avec le seuil** (0,150 → 0,335,
   école de rattrapage). Le mécanisme d'Abnégation vocal se comporte bien — il ne s'emballe pas.

5. **La neurogenèse a su se déclencher (§8.4)** quand l'erreur était haute et stable (J39,
   16→32 dims). Le mécanisme n'est pas cassé — il n'a simplement **plus jamais eu de raison de se
   redéclencher** une fois la JEPA effondrée (ce qui est le vrai bug, pas la neurogenèse elle-même).

---

## 5. Axes d'amélioration, priorisés

Rangés du plus structurant (cause racine) au plus cosmétique.

### 5.1 — CRITIQUE : casser l'anti-corrélation « JEPA basse = système mort »

Le run montre qu'une erreur JEPA qui tend vers 0 **désactive en cascade** neurogenèse, rêve,
curiosité et dopamine. Il faut découpler « bien prédire » de « ne plus rien apprendre ». Pistes :

- **Détecteur d'effondrement de représentation.** Suivre la **variance** de `bus_reel`
  (`ReLU(porte_visuelle(obs))`) sur une fenêtre. Si l'erreur JEPA **et** la variance de la cible
  chutent ensemble → c'est un collapse, pas une maîtrise. Réagir en injectant du bruit / en forçant
  un pas de curiosité, plutôt qu'en félicitant le réseau.
- **Plancher de plasticité en régime établi.** Aujourd'hui `plasticite_base` suit passivement la
  dopamine et tombe à 0,14. Un plancher (p. ex. 0,3) empêcherait le figement terminal.
- **VICReg-like sur la cible JEPA.** Ajouter un terme de variance/covariance sur `bus_reel` (à la
  VICReg / Barlow Twins) pour interdire explicitement la solution constante — c'est le
  durcissement standard du stop-gradient quand il ne suffit pas seul (voir §6).

### 5.2 — CRITIQUE : rebrancher promotion ↔ compétence réelle

- **Conditionner la promotion de niveau à un `Recompense_Moyenne > 0` réel**, pas seulement aux
  jalons partiels DoorKey. Aujourd'hui les paliers se valident sur « approcher / toucher / viser »
  sans jamais exiger la sortie. Exiger *au moins une vraie victoire* avant de valider le
  sous-seuil 2 fermerait la faille du proxy-hacking.
- **Récompense de complétion de chaîne**, pas seulement de sous-buts. L'agent franchit 6 portes/jour
  mais ne chaîne jamais clé→porte→sortie. Un bonus explicite pour la *séquence complète* (et non la
  somme des sous-actions) attaquerait directement le plateau à 8 % de maîtrise.

### 5.3 — MAJEUR : exploiter la capacité de neurogenèse gelée

Le Bus est resté à **32/96 dims** sur 1400 jours. La capacité de représentation prévue par
l'architecture (`DIM_BUS_MAX=96`) n'a jamais été utilisée au-delà du tiers. Une fois §5.1 réglé
(erreur JEPA qui ne s'effondre plus artificiellement), le thermostat devrait pouvoir re-déclencher
`agrandir()` en Doctorat, là où la tâche est la plus dure — à vérifier au prochain run.

### 5.4 — MAJEUR : le Module Parent punit plus qu'il n'enseigne

```
Feedback_Parent_Jour : somme = -629 095   (moy -437/jour, négatif 1194 jours sur 1200)
```

Le Parent dit « Non ! » massivement plus souvent que « Oui ! ». Un signal aussi déséquilibré vers
la punition est connu pour écraser l'exploration (l'agent apprend surtout à *éviter*, pas à
*réussir*). Rééquilibrer : plafonner la pénalité, ou passer à un feedback **relatif au progrès**
(« mieux qu'hier ») plutôt qu'absolu au seuil.

### 5.5 — MINEUR : instrumentation

- Logger `Niveau`, `Palier_Cible`, `Mode_Libre` **sur toute la durée** (ils s'arrêtent au J446 —
  invisibilité totale du régime Doctorat J456→1440, qui est justement là où tout se fige).
- Ajouter un log direct de la **variance de `bus_reel`** et du **nombre de dims Bus** pour voir le
  collapse en temps réel sur W&B.

---

## 6. Mise en parallèle avec les méthodes de référence

Comme demandé, voici ce que Naulthène **tente de faire** face à ce que font les approches établies,
et ce que le run de 1440 jours révèle sur ces choix.

### 6.1 vs. le **Transformer** (attention, séquences)

| Axe | Transformer | Naulthène v25 | Ce que dit le run |
|---|---|---|---|
| **Mémoire du contexte** | Attention sur toute la fenêtre, tous les tokens accessibles en parallèle, coût O(n²) | `hippocampe` (tampon court) + `vecteurs_episodiques` (moyenne glissante des 20 derniers `bus_latent`) + mémoire spatiale (200 souvenirs) | La mémoire épisodique **sature à 200 souvenirs** dès le Doctorat et le reste jusqu'à la fin : capacité de contexte fixe, là où un Transformer étendrait sa fenêtre. C'est un plafond de mémoire, pas un mécanisme d'attention sélective. |
| **Sélection de l'information** | *Soft attention* apprise : le modèle **pondère** dynamiquement quels éléments du passé comptent | `lecture_episodique` = double reconcaténation avec un **contexte moyenné** (moyenne non pondérée, [explications §4](../fonctionnement/explications_readme.md)) | La moyenne glissante traite tous les souvenirs à poids égal. C'est précisément ce qu'un mécanisme d'attention remplacerait : *quel* souvenir est pertinent *maintenant*. Le plateau de compétence suggère que l'agent ne sait pas rappeler « où est la clé » au bon moment. |
| **Profondeur / composition** | Empilement de blocs → composition hiérarchique de features | Tronc **peu profond** (`porte_visuelle → hippocampe → analyseur`, 1 couche chacun) | La faille clé→porte→sortie (§2) est un échec de **composition séquentielle** — exactement ce que la profondeur + l'attention d'un Transformer adressent le mieux. |
| **Positionnement** | Positional encoding explicite | Aucun encodage spatial/temporel explicite au-delà de la mémoire spatiale | — |

> **Lecture.** Naulthène remplace l'attention globale (chère, O(n²)) par un **résumé récurrent
> bon marché** (moyenne glissante + tampon). Le run montre le prix de ce choix : bon pour un
> modèle du monde local (JEPA descend bien), insuffisant pour la **planification longue** qui exige
> de rappeler sélectivement un événement passé précis (la clé) — d'où le blocage définitif en
> Doctorat (« Planification Longue »). **Un bloc d'attention léger sur `vecteurs_episodiques`**
> serait l'emprunt le plus rentable au Transformer pour ce projet.

### 6.2 vs. **JEPA / I-JEPA / V-JEPA** (LeCun, le modèle-cible du projet)

Naulthène implémente fidèlement l'idée JEPA (prédire le latent, stop-gradient, [explications §2](../fonctionnement/explications_readme.md)).
**Ce qui manque par rapport aux JEPA modernes**, et que le run rend visible :

- **Anti-collapse explicite.** I-JEPA/V-JEPA n'utilisent pas *que* le stop-gradient : ils
  s'appuient sur des cibles issues d'un **encodeur EMA** (moyenne mobile exponentielle des poids,
  façon BYOL) et/ou des régularisations de variance. Naulthène n'a *que* le stop-gradient — et le
  run prouve que **c'est insuffisant** : collapse à 0,0000 en fin. C'est l'amélioration §5.1.
- **Masquage spatial.** JEPA prédit des *régions masquées* de l'entrée ; Naulthène prédit le *pas
  suivant complet*. Prédire des masques rendrait le collapse trivial beaucoup plus difficile.

### 6.3 vs. **MuZero / Dreamer** (model-based planning)

C'est le cousin le plus proche du **Système 2** ([explications §6](../fonctionnement/explications_readme.md)).

| | MuZero / Dreamer | Naulthène (Système 2) |
|---|---|---|
| Modèle de transition | Appris, déroulé sur des dizaines de pas, **MCTS** (MuZero) ou rollouts imaginés massifs (Dreamer) | `_predire_bus` (le prédicteur JEPA) déroulé sur horizons **(1, 3, 7)**, branchement unique puis argmax glouton |
| Complexité | O(simulations × profondeur), coûteux | **Linéaire** O(A × Σ Δh), volontairement bridé (protégé dans CLAUDE.md) |
| Ce que dit le run | Dreamer résout des tâches à récompense sparse via l'imagination | Le Système 2 imagine sur un **modèle du monde effondré** en fin de run → il planifie sur une hallucination constante. `Sursauts_Volonte` (proxy d'engagement du S2) **s'arrêtent net au J446** |

> **Lecture.** Le pari « rollout linéaire bon marché » de Naulthène est défendable *tant que JEPA
> est fiable*. Le run montre le maillon faible : quand JEPA collapse (§3), le Système 2 planifie
> dans le vide. Dreamer souffrirait moins car son world-model est régularisé pour rester
> informatif. → encore §5.1 comme cause racine.

### 6.4 vs. **RL classique** (PPO / DQN)

Naulthène utilise un **REINFORCE avec baseline** calculé une fois par journée entière
([explications §5](../fonctionnement/explications_readme.md)), là où l'état de l'art est PPO (clipping, GAE,
mini-batchs). Sur ce run précis, ce n'est **pas** le goulot : la récompense externe est masquée
puis nulle, donc le gradient de politique n'a presque jamais de signal réel à propager. Le vrai
sujet est en amont (proxy-hacking §2, collapse §3), pas dans le choix de l'estimateur de gradient.
À corriger *après* §5.1–5.2 : un REINFORCE une-fois-par-jour sur 3600 ticks a une variance de
gradient énorme — passer à PPO deviendra pertinent une fois qu'il y aura une vraie récompense à
optimiser.

---

## 7. Verdict et prochain run recommandé

**Ce run est un échec instructif, pas un run raté.** Il valide la moitié développementale du
pari (auto-supervision + déverrouillage social) et **expose proprement** les deux pathologies qui
bloquent la seconde moitié :

1. **Collapse de représentation JEPA** (erreur → 0, cascade de figement) — cause racine.
2. **Découplage promotion / compétence réelle** (proxy-hacking des détecteurs génériques).

Ordre de bataille pour le run suivant :

1. **D'abord §5.1** (anti-collapse : EMA/VICReg sur la cible JEPA + plancher de plasticité). Sans ça,
   rien d'autre ne tient — tout se re-fige.
2. **Puis §5.2** (promotion conditionnée à une vraie victoire + récompense de chaîne complète).
3. **Vérifier** que la neurogenèse se rouvre (§5.3, Bus > 32) et rééquilibrer le Parent (§5.4).
4. **Emprunt Transformer le plus rentable** (§6.1) : un mini-bloc d'**attention** sur
   `vecteurs_episodiques` pour transformer la moyenne glissante passive en rappel sélectif — c'est
   probablement le seul moyen de débloquer la *Planification Longue* du Doctorat.

Un run de contrôle **court** (`--jours 120`, jusqu'à ~1 mois après le déverrouillage J240) suffit
à vérifier §5.1+§5.2 : si `Recompense_Moyenne` décolle enfin de 0 et si l'erreur JEPA se
**stabilise** (au lieu de tendre vers 0), les corrections tiennent — avant de relancer 1440 jours.

---

> ⚠️ **Portée.** Ce document analyse un run de `cursus_bebe.py` (v25.0), qui vit **uniquement**
> dans l'écosystème local de test (`agi_local_test.py` + modules `cursus_bebe`/`professeur_gemma`/
> `persistance`), **non porté** sur le script de référence `agi_google_colab.py` (v17). Voir
> [CLAUDE.md](../../CLAUDE.md) § « Variante Locale de Test » et
> [explications_readme.md](../fonctionnement/explications_readme.md) pour l'algorithme sous-jacent.
>
> *Analyse générée à partir du datastore W&B `run-20260724_091053-u773ulep` (1440 records
> d'historique, 47 métriques) et de `output.log` (20 541 lignes) — run terminé le 2026-07-24.*
