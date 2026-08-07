# Le Parcours de Naulthène — Guide Complet du Système de Cursus

Ce document explique, en langage clair, **comment Naulthène apprend au fil du temps** : les
commandes pour lancer chaque parcours, combien de temps ça prend, ce que chaque palier signifie
concrètement, et comment lire les logs/W&B pour suivre la progression. C'est le complément
pratique de [readme.md](../readme.md) (vision d'ensemble et formules) et
[docs/explications_readme.md](explications_readme.md) (détail algorithmique) — ici, l'angle
est **"je veux lancer un run et comprendre ce qui se passe"**.

Référence code : `src/naulthene/cerveau/noyau.py` (jusqu'à v32.0) et les trois
scripts de `src/naulthene/salles_de_classe/`.

> 📍 **État (2026-08-07)** : `master` porte les v28.0 → v29.1. Les **v30.0/v30.1** (l'Exo-Sens),
> **v31.0/v31.1** (Mémoire Proportionnelle), **v32.0** (Odorat Topologique & Clinotaxie),
> **v33.1** (banc d'ablation) et **v34.0-fix1/fix2** (correctif de l'extinction synaptique) sont
> **implémentées et validées** sur leurs branches. **Aucune ne change les commandes de ce
> guide** — toutes sont automatiques, sans flag ni option. Voir [CHANGELOG.md](CHANGELOG.md).
>
> 🆕 **v35.0/v35.1 — le cursus est passé de 5 à 15 niveaux, et l'aide est devenue
> adaptative.** Le [§6](#6-les-15-niveaux-minigrid-programme-v350) décrit le programme et la
> nouvelle promotion (2 victoires **OU** 60 % de maîtrise sur 20 épisodes) ; le
> [§6ter](#6ter-le-guidage-dégressif--le-filet-de-sécurité-v351) le **sevrage** (plus il
> comprend, moins on l'aide) et le **filet** (quand il bloque, on l'aide plus) ; le
> [§6bis](#6bis--pourquoi-ce-programme-est-trop-court-et-trop-brutal-diagnostic-2026-08-07)
> garde le diagnostic qui a motivé la refonte (2000 jours de blocage mesurés).
> **Rien à activer** — un ancien `.brain` est remappé automatiquement.

---

## Table des matières

1. [Les 4 parcours possibles — vue d'ensemble](#1-les-4-parcours-possibles--vue-densemble)
2. [Le Cursus par Ères (`cursus_developpemental.py`)](#2-le-cursus-par-ères-cursus_developpementalpy)
3. [Le Cerveau Bébé (`cursus_bebe.py`)](#3-le-cerveau-bébé-cursus_bebepy)
4. [Le Cursus de la Parole (`cursus_parole.py`)](#4-le-cursus-de-la-parole-cursus_parolepy)
5. [La Cuve (mode manuel client-serveur)](#5-la-cuve-mode-manuel-client-serveur)
6. [Les 15 niveaux MiniGrid (`PROGRAMME`, v35.0)](#6-les-15-niveaux-minigrid-programme-v350)
6bis. [⚠️ Pourquoi ce programme est trop court et trop brutal](#6bis--pourquoi-ce-programme-est-trop-court-et-trop-brutal-diagnostic-2026-08-07)
6ter. [Le Guidage Dégressif & le Filet de Sécurité (v35.1)](#6ter-le-guidage-dégressif--le-filet-de-sécurité-v351)
7. [Les 7 paliers DoorKey — le détail complet](#7-les-7-paliers-doorkey--le-détail-complet)
8. [Le curriculum vocal — les 19 paliers](#8-le-curriculum-vocal--les-19-paliers)
9. [Mode Guidé vs Mode Libre](#9-mode-guidé-vs-mode-libre)
10. [La patience adaptative — pourquoi un épisode s'arrête](#10-la-patience-adaptative--pourquoi-un-épisode-sarrête)
11. [Ce qui NE régresse jamais (et comment le savoir quand même)](#11-ce-qui-ne-régresse-jamais-et-comment-le-savoir-quand-même)
12. [Où trouver chaque cerveau (`brains/*.brain`)](#12-où-trouver-chaque-cerveau-brainsbrain)
13. [Lire un bilan de nuit — exemple annoté](#13-lire-un-bilan-de-nuit--exemple-annoté)
14. [Foire aux questions](#14-foire-aux-questions)
15. [Les 5 sens de l'agent (v29)](#15-les-5-sens-de-lagent-v29)

---

## 1. Les 4 parcours possibles — vue d'ensemble

Naulthène n'a **pas un seul cursus** : il y a 4 écosystèmes distincts, chacun avec **son propre
fichier `.brain`** (un cerveau ne partage jamais son parcours avec un autre). Le choix dépend de
ce que tu veux observer.

| Parcours | Script | Fichier cerveau | Durée totale visée | Ticks/jour | Ce qu'il ajoute |
|---|---|---|---|---|---|
| **Cursus par Ères** | `cursus_developpemental.py` | `brains/naulthene_cursus.brain` | 1000 jours | **400** | MiniGrid + vocal, en alternance puis fusionnés |
| **Cerveau Bébé** | `cursus_bebe.py` | `brains/naulthene_bb.brain` | 1440 jours (~4 ans) | **3600** | Récompense externe masquée les 240 premiers jours, feedback "Parent" |
| **Cursus de la Parole** | `cursus_parole.py` | `brains/naulthene_parole.brain` | 900 jours | **800** | Voix réelle de l'utilisateur, synesthésie (mot ancré sur l'objet regardé) |
| **La Cuve** | `daemon_cerveau.py` + clients | `brains/naulthene_v21.brain` | illimité, manuel | pas de notion de "jour" fixe | Contrôle manuel tick par tick, alterner MiniGrid/vocal à la demande |

**Tous les 4 lancent le même cerveau (`AGI_Naulthene`)** avec la même architecture (8 actions dont
l'action C3 devenue dormante, les **5 sens** + l'Exo-Sens, et depuis la v32.0 l'odorat topologique
et la clinotaxie — voir [docs/CHANGELOG.md](CHANGELOG.md)) — seule la boucle qui pilote les
journées change.

**Convention commune aux 3 cursus autonomes** (par Ères, Bébé, Parole) :
- Chacun **sauvegarde après chaque nuit** — interrompre avec `Ctrl+C` ne perd au pire que la
  journée en cours, jamais les précédentes.
- `--jours N` ajoute **N jours SUPPLÉMENTAIRES** à partir de l'état repris — ce n'est jamais une
  valeur absolue. Relancer la même commande reprend exactement où le cerveau en était.
- `--no-wandb` désactive le logging Weights & Biases. Sans connexion internet, préfixer la
  commande par `WANDB_MODE=offline`.
- Toutes les commandes se lancent **depuis la racine du dépôt**, avec `PYTHONPATH=src` et
  l'option `-m` (jamais `python fichier.py` directement — voir `CLAUDE.md`).

---

## 2. Le Cursus par Ères (`cursus_developpemental.py`)

**Ce que c'est, en une phrase** : l'agent va à l'école tous les jours pendant 1000 jours — le
matin il apprend à bouger/résoudre des problèmes (MiniGrid), l'après-midi il apprend à parler.

### Commande

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate

# Premier essai (5 jours, quelques minutes) — recommandé avant de lancer le run complet
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_developpemental --jours 5

# Run complet (1000 jours, plusieurs heures)
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_developpemental --jours 1000
```

Un seul terminal — pas de Cuve à lancer en parallèle pour ce mode.

### Le rythme d'une journée : 400 ticks

Une "journée subjective" = **400 ticks** (`ticks_par_jour`), coupée en deux :
- **Ticks 0 à 199** (matin, `TICKS_MATIN=200`) : selon l'Ère (voir plus bas), focus MiniGrid.
- **Ticks 200 à 399** (après-midi) : focus vocal.

Un "tick" = une décision de l'agent (une action jouée ou une itération de babillage). 400
ticks/jour est aussi le seuil minimal en dessous duquel l'apprentissage réel (`apprendre_journee`)
ne se déclenche pas — c'est pour ça que ce chiffre n'est pas arbitraire.

### Les 3 Ères — comment matin/après-midi évoluent avec le temps

| Ère | Jours | Le matin | L'après-midi |
|---|---|---|---|
| **Alternance** | 1 – 399 | MiniGrid seul (silence total) | Vocal seul, agent immobile (`vocal_isole`) |
| **Synesthésie** | 400 – 599 | MiniGrid **+ audio en même temps** | Vocal seul (comme l'Alternance) |
| **Intégration** | ≥ 600 | MiniGrid **+ verbalisation de l'action jouée** (l'agent "dit" ce qu'il fait) | Journée continue, même mécanique que le matin |

Le passage d'une Ère à l'autre est **automatique**, basé uniquement sur `etat.jour` — rien à faire
manuellement, un message `🌅 [NOUVELLE ÈRE]` s'affiche au bon moment.

### Ce qui progresse pendant ce cursus

Deux progressions **indépendantes**, en parallèle, sur le même cerveau :
1. **Le niveau MiniGrid** (`PROGRAMME`, 15 niveaux depuis la v35.0 — voir §6) et, à l'intérieur du niveau
   "Collège", **les 7 paliers DoorKey** (voir §7).
2. **Le palier vocal** (1 à 19 — voir §8), totalement indépendant du niveau MiniGrid.

### Où voir la progression

- **Console**, chaque nuit : bilan complet (dopamine, palier DoorKey, palier vocal, portes
  franchies, erreur JEPA...) — voir §13 pour un exemple annoté.
- **W&B** (si activé) : courbes `Niveau`, `Palier_Cible`, `Palier_Vocal`, `Taux_Maitrise_Palier`,
  `Recompense_Moyenne`, `Erreur_JEPA`, etc.

---

## 3. Le Cerveau Bébé (`cursus_bebe.py`)

**Ce que c'est, en une phrase** : au lieu de récompenser l'agent dès le premier jour, on le
laisse "grandir" sans notation pendant 8 mois (240 jours), pour ne pas perturber la construction
de ses représentations visuelles/auditives — inspiré de la psychologie développementale
(Piaget/Dehaene).

### Commande

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate

# Premier essai
PYTHONPATH=src python3 -m naulthene.salles_de_classe.cursus_bebe --jours 30 --no-wandb

# Run complet (1440 jours ≈ 4 ans subjectifs)
PYTHONPATH=src python3 -m naulthene.salles_de_classe.cursus_bebe --jours 1440
```

### Le rythme d'une journée : 3600 ticks

Une journée = **3600 ticks** (`TICKS_PAR_JOUR_BEBE`), un "cycle nycthéméral complet" — 9× plus
long qu'une journée du Cursus par Ères. 1800 ticks matin / 1800 ticks après-midi.

### Les 5 phases d'âge

| Phase | Jours | % Dodo (plafond de rêve) | Ce qui se passe |
|---|---|---|---|
| Éveil des Sens (0-3 mois) | 1-90 | 70% | Vision floue, réflexes, babil brut — **aucune récompense externe** |
| Exploration Motrice (3-6 mois) | 91-180 | 60% | Coordination œil-main, voyelles a/e/i/o/u |
| Locomotion & Concepts (6-12 mois) | 181-360 | 50% | Déplacements, objets, syllabes ba/ma/pa — **feedback "Parent" dès le jour 240** |
| Association Forte (12-24 mois) | 361-720 | 40% | Navigation ciblée, mots papa/maman/porte |
| Jeune Enfant (24-48 mois) | 721-1440 | 35% | Planification complexe, combinatoire Action+Objet |

**Le point le plus important** : jusqu'au **jour 240** (`JOUR_FIN_MASQUAGE_EXTERNE`), la
récompense de l'environnement (gagner/perdre) est gelée à 0 — l'agent apprend uniquement par
curiosité (JEPA) et besoins biologiques (faim, soif, stimulation), jamais par "bien/mal" externe.
À partir du jour 240, un feedback social simple s'active : un "Oui !" ou un "Non !" selon la
qualité de sa prononciation, comme un parent qui encourage.

### Où voir la progression

Même bilan de nuit que le Cursus par Ères, plus une ligne `Feedback_Parent_Jour` (compteur net
Oui/Non) une fois la phase 3 atteinte.

---

## 4. Le Cursus de la Parole (`cursus_parole.py`)

**Ce que c'est, en une phrase** : un cursus dédié à bien apprendre à parler, avec **ta propre
voix enregistrée** comme référence (au lieu d'une voix de synthèse théorique), et une
"synesthésie" — l'agent apprend à nommer l'objet qu'il regarde réellement, pas un mot théorique
déconnecté de ce qu'il voit.

### Commande

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate

# Premier essai (3 jours)
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_parole --jours 3 --no-wandb

# Run complet (900 jours)
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_parole --jours 900
```

### (Facultatif) Enregistrer ta voix avant de lancer

```bash
PYTHONPATH=src python -m naulthene.instruments.enregistreur_voix --prises 3
```

Sans cette étape, le cursus fonctionne quand même — repli automatique sur la voix de synthèse
macOS (`say`). Voir [docs/LANCEMENT.md](LANCEMENT.md) §0bis pour le détail complet.

### Le rythme d'une journée : 800 ticks

Une journée = **800 ticks** (`TICKS_PAR_JOUR_PAROLE`), 400 matin / 400 après-midi. Ce chiffre est
volontairement **supérieur à 400** (le seuil minimal d'apprentissage, voir §2) pour garantir une
vraie progression même sur les journées les plus courtes du cursus.

### Les 3 phases pédagogiques

| Phase | Jours | Nom | Ce qui change |
|---|---|---|---|
| 0 | 1 – 299 | Imprégnation totale | Le professeur nomme systématiquement le mot du curriculum, matin ET après-midi (guidage 100%) |
| 1 | 300 – 599 | Autonomie guidée | Matin : synesthésie (mot lu dans la case devant l'agent) — Après-midi : curriculum classique. Guidage décroît de 100% vers ~40% |
| 2 | 600 – 899 | Émancipation | Synesthésie + syntagmes couleur+objet toute la journée. Guidage ~40% → 10% |

Un changement de phase est signalé par `🗣️ [NOUVELLE PHASE]`.

### Où voir la progression

Bilan de nuit habituel + `Phase_Parole`, `Taux_Guidage`, `Palier_Vocal`, `Mot_Frontal_Dernier`
(le dernier mot que l'agent regardait).

---

## 5. La Cuve (mode manuel client-serveur)

**Ce que c'est, en une phrase** : au lieu d'un script automatique qui tourne pendant des
centaines de jours, tu pilotes le cerveau **toi-même, tick par tick**, en alternant librement
MiniGrid et leçons de parole. Utile pour observer/déboguer en direct, pas pour un entraînement
long non supervisé.

### Commande (deux terminaux)

**Terminal 1 — la Cuve (à garder ouvert)** :
```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src python -m naulthene.cuve.daemon_cerveau --port 9999 --brain brains/naulthene_v21.brain
```

**Terminal 2 — MiniGrid** :
```bash
PYTHONPATH=src python -m naulthene.cuve.client_corps --port 9999 --continu
```

**Terminal 2 (à un autre moment) — leçon de parole** :
```bash
PYTHONPATH=src python -m naulthene.cuve.client_professeur --port 9999 --palier 2 --ticks 100
```

Il n'y a **pas de notion de "jour" fixe** ici — une nuit (`executer_nuit`) se déclenche
automatiquement dès qu'un certain nombre de ticks s'est accumulé, comme dans les cursus
autonomes, mais tu contrôles quand arrêter chaque session. Voir [docs/LANCEMENT.md](LANCEMENT.md) §1-5 pour le
détail complet (options, dépannage).

---

## 6. Les 15 niveaux MiniGrid (`PROGRAMME`, v35.0)

C'est la progression "scolaire" de base, commune à **tous** les parcours (elle vit dans le
cerveau, pas dans un cursus particulier).

> 🆕 **v35.0** — le programme est passé de **5 à 15 niveaux**. Le §6bis explique pourquoi
> (2000 jours de blocage mesurés) ; ici, ce que ça donne concrètement.

| # | Environnement | Nom | Nouveauté par rapport au précédent |
|---|---|---|---|
| 0 | `Empty-5x5` | **Nourrisson** (Premiers pas) | avancer, tourner |
| 1 | `Empty-Random-6x6` | **Éveil** (Départ aléatoire) | départ variable → généraliser |
| 2 | `Empty-8x8` | **Maternelle** (Longue distance) | trajet plus long |
| 3 | `SimpleCrossingS9N1` | **Primaire 1** (Contourner) | un mur sur le chemin |
| 4 | `LavaGapS5` | **Primaire 2** (Éviter le danger) | la lave tue |
| 5 | `Fetch-5x5-N2` | **Primaire 3** (Ramasser) | manipuler un objet |
| 6 | `GoToDoor-6x6` | **Collège 1** (Viser une porte) | la porte devient une cible |
| 7 | `DoorKey-5x5` | **Collège 2** (Clé & porte, minimal) | clé + porte, carte minimale |
| 8 | `DoorKey-6x6` | **Collège 3** (Clé & porte) | même tâche, plus grand |
| 9 | `DoorKey-8x8` | **Lycée 1** (Clé & porte, distance) | même tâche, distance longue |
| 10 | `Unlock` | **Lycée 2** (Déverrouiller) | plus de but visible |
| 11 | `UnlockPickup` | **Lycée 3** (Déverrouiller & prendre) | + récupérer derrière la porte |
| 12 | `MemoryS7` | **Université** (Mémoire Épisodique) | se souvenir d'un indice |
| 13 | `MultiRoom-N2-S4` | **Doctorat 1** (Deux pièces) | enchaîner deux salles |
| 14 | `MultiRoom-N4-S5` | **Doctorat 2** (Planification Longue) | 4 salles, 5 portes |

**Le principe** : entre deux paliers voisins, **une seule chose change**. `DoorKey-5x5` →
`6x6` → `8x8` est la *même tâche à trois échelles* — l'agent consolide au lieu de tout
réapprendre à chaque étage.

### Comment on passe au niveau suivant — deux voies (v35.0)

| Voie | Critère | Caractère |
|---|---|---|
| **Série** (historique) | 2 victoires **consécutives** | rapide, mais une défaite remet à zéro |
| **Maîtrise** (nouveau) | **60 %** de réussite sur les **20** derniers épisodes | lent à établir, mais robuste |

Les deux coexistent en **OU** : la première reste la voie rapide, la seconde rattrape le cas
qui bloquait — un agent à 80 % de réussite qui perd un épisode sur cinq restait coincé à vie
avec l'ancien critère seul.

Le taux n'est calculé qu'à partir de **10 épisodes** observés (avant, il affiche `—` : « pas
encore mesurable » n'est pas « mesuré à zéro »). La fenêtre est **vidée à chaque promotion**
— sinon un taux hérité d'un niveau facile promouvrait en chaîne.

Une ligne le montre chaque nuit :

```
├─ Cursus         : 🎓 Niveau 8/15 — maîtrise 45% (n=20), seuil 60% | série 0/2
```

### Reprendre un ancien cerveau : le remappage automatique

`niveau_actuel` est un **index** dans `PROGRAMME`. Un `.brain` sauvegardé au niveau 4
(ex-Doctorat) se retrouverait sinon à l'index 4 du nouveau programme (`LavaGapS5`),
c'est-à-dire **rétrogradé de dix crans**. La persistance remappe donc par `env_id` :

```
🔀 Niveau remappé : index 4 → 14 (Doctorat (Planification Longue)) — le PROGRAMME
   a changé de taille (v35.0), aucune progression n'est perdue.
```

Message **normal**, affiché une seule fois par cerveau. Vérifié sur deux `.brain` réels
(Collège 1 → 8, Doctorat 4 → 14), nuit complète incluse.

---

## 6bis. ⚠️ Pourquoi ce programme est trop court et trop brutal (diagnostic 2026-08-07)

> ✅ **Statut : refonte LIVRÉE en v35.0** (2026-08-07). Cette section garde le diagnostic
> qui l'a motivée — les chiffres mesurés sur l'ancien programme à 5 niveaux, et les options
> écartées. Le programme livré est décrit au [§6](#6-les-15-niveaux-minigrid-programme-v350).

### Le constat

Un run de 2700 jours sur un cerveau sain (post-correctif d'extinction synaptique) :

| Mesure | Valeur |
|---|---|
| Jours passés au **Collège** | **2000** — sans jamais en sortir |
| Palier atteint | **7** (le dernier) dès le jour 701 |
| Victoires | 22 en 2700 jours, **tendance 1,08 → stationnaire** |
| Δt1 (atteindre la clé) | **JAMAIS ATTEINT** |
| Contact avec les murs | **82 %** des ticks |
| Records de proximité | **0,00 par jour** sur 2000 jours |

L'agent porte la clé 58 % du temps mais n'atteint jamais la porte. Il ne progresse plus,
il ne régresse pas non plus : il est **bloqué dans un optimum local**.

### Les trois défauts de conception

**1. Le saut Primaire → Collège demande 5 compétences d'un coup**

| | Objets sur la carte | Compétences requises |
|---|---|---|
| `Empty-8x8` | **1** (le but) | avancer, tourner |
| `DoorKey-6x6` | **3** (clé, porte, but) | + repérer, ramasser, porter, viser, ouvrir |

Deux victoires sur une salle vide suffisent pour affronter une tâche à 5 sous-objectifs.
Aucun palier intermédiaire ne fait le pont.

**2. Le guidage est retiré au pire moment**

Au **Palier 5**, le Mode Libre coupe `RECOMPENSE_APPROCHE_BUT` d'un coup (§9). Résultat
mesuré : **0,00 record de proximité par jour** pendant 2000 jours. L'agent perd tout signal
de progression spatiale exactement quand la tâche devient la plus dure.

**3. Le dernier niveau exige une efficacité 10× supérieure**

Mesuré par BFS sur l'espace `(x, y, direction)` — le **coût réel en ACTIONS** (rotations +
avances + `toggle` des portes), sur 30 graines par niveau :

| Niveau | `max_steps` | Coût optimal (moy) | **Marge** |
|---|---|---|---|
| Collège (`DoorKey-6x6`) | 360 | 9,7 | **37,0×** |
| Primaire (`Empty-8x8`) | 256 | 11,0 | **23,3×** |
| Doctorat 1 (`MultiRoom-N2-S4`) | 40 | 7,3 | 5,5× |
| **Doctorat (`MultiRoom-N4-S5`)** | **120** | **33,7** (max 43) | **3,6×** ⚠️ |

> ✅ **Correction d'un diagnostic erroné (2026-08-07).** Une première lecture concluait que
> le Doctorat était « infaisable ». **C'est faux** : avec 33,7 actions optimales pour 120
> disponibles, le but est atteignable — la marge est de 3,6×, jamais négative.
>
> Le vrai problème est **le saut d'exigence** : l'agent peut se permettre 37 fois le trajet
> optimal au Collège, mais seulement 3,6 fois au Doctorat. Il doit devenir **10× plus
> efficace** d'un niveau à l'autre, sans qu'aucun palier intermédiaire ne l'y prépare.
>
> C'est exactement ce que `MultiRoom-N2-S4` (marge 5,5×) apporte comme étape manquante.

### La refonte proposée : 14 paliers au lieu de 5

MiniGrid expose **58 environnements** ; le projet n'en utilise que 5. De quoi construire une
vraie progression, où chaque étape n'ajoute **qu'une seule compétence nouvelle**.

| # | Environnement | Nom | Nouveauté | Grille / steps |
|---|---|---|---|---|
| 0 | `Empty-5x5` | Nourrisson | avancer, tourner | 5×5 / 100 |
| 1 | `Empty-Random-6x6` | Éveil | départ aléatoire (généraliser) | 6×6 / 144 |
| 2 | `Empty-8x8` | Maternelle | distance plus longue | 8×8 / 256 |
| 3 | `SimpleCrossingS9N1` | Primaire 1 | **contourner un mur** | 9×9 / 324 |
| 4 | `LavaGapS5` | Primaire 2 | **éviter le danger** (lave) | 5×5 / 100 |
| 5 | `Fetch-5x5-N2` | Primaire 3 | **ramasser un objet** | 5×5 / 125 |
| 6 | `GoToDoor-6x6` | Collège 1 | **aller vers une porte** | 6×6 / 144 |
| 7 | `DoorKey-5x5` | Collège 2 | **clé + porte**, carte minimale | 5×5 / 250 |
| 8 | `DoorKey-6x6` | Collège 3 | même tâche, plus grand | 6×6 / 360 |
| 9 | `DoorKey-8x8` | Lycée 1 | même tâche, distance longue | 8×8 / 640 |
| 10 | `Unlock` | Lycée 2 | déverrouiller sans but visible | 11×6 / 288 |
| 11 | `UnlockPickup` | Lycée 3 | + récupérer un objet derrière | 11×6 / 288 |
| 12 | `MemoryS7` | Université | **mémoriser un indice** | 7×7 / 245 |
| 13 | `MultiRoom-N2-S4` | Doctorat 1 | **2 pièces** (avant les 4) | 25×25 / 40 |
| 14 | `MultiRoom-N4-S5` | Doctorat 2 | 4 pièces, 5 portes | 25×25 / 120 |

**Le principe** : entre deux paliers voisins, une seule chose change. `DoorKey-5x5` →
`DoorKey-6x6` → `DoorKey-8x8` est la même tâche à trois échelles — l'agent consolide au lieu
de tout réapprendre.

### Les trois changements d'accompagnement — état

**a. ✅ LIVRÉ (v35.0) — Promotion par taux de maîtrise.** `VICTOIRES_REQUISES = 2`
consécutives était fragile (une défaite remet à zéro) et faible (2 réussites peuvent être de
la chance). La v35.0 **ajoute** une seconde voie — 60 % sur 20 épisodes — sans retirer la
première. Détail au [§6](#6-les-15-niveaux-minigrid-programme-v350).

**b. ✅ LIVRÉ (v35.1) — Un guidage qui s'estompe.** `RECOMPENSE_APPROCHE_BUT` ne tombe plus
à 0 d'un coup : l'aide décroît avec la maîtrise mesurée. Voir
[§6ter](#6ter-le-guidage-dégressif--le-filet-de-sécurité-v351).

**c. ✅ LIVRÉ AUTREMENT (v35.1) — pas de redescente, mais un filet.** La redescente est
**écartée** (décision utilisateur : *« il ne peut pas aller faire un palier impossible — et
quand il bloque, on l'aide un peu »*). Un agent qui stagne reçoit un **surplus** d'aide,
jusqu'à ×3, replié dès sa première victoire. Voir §6ter.

### Ce qui reste à mesurer

Conformément à la doctrine du projet (instrumenter avant de calibrer) :

1. **Le taux de réussite par niveau** — un palier que l'agent traverse en 2 jours n'apporte
   rien ; la métrique `Cursus_Taux_Maitrise_Niveau` le dira. À lire sur un run long.
2. **Le temps réel jusqu'à la première victoire** sur chaque nouvel environnement.
3. ✅ **Fait** : la faisabilité du Doctorat, mesurée par BFS (marge ×3,6 — faisable, mais
   10× plus exigeant que le Collège). Voir le défaut 3 ci-dessus.

---

## 6ter. Le Guidage Dégressif & le Filet de Sécurité (v35.1)

Deux mécaniques opposées, pilotées par **un seul curseur** — le facteur de guidage, affiché
chaque nuit sur la ligne `Cursus`.

### 📉 Le sevrage — « plus il comprend, moins on l'aide »

L'aide décroît à mesure que la maîtrise monte, comme un enfant qu'on accompagne de moins en
moins :

| Maîtrise du niveau | Guidage | Ce que ça veut dire |
|---|---|---|
| pas encore mesurable (< 10 épisodes) | **1,00** | un débutant reste un débutant |
| ≤ 60 % | 1,00 | 🤝 aide pleine |
| 70 % | 0,67 | 📉 sevrage en cours |
| 80 % | 0,33 | 📉 sevrage avancé |
| ≥ 90 % | **0,00** | 🕊️ autonome |

**Ce que ça remplace** : le guidage était coupé d'un seul coup au palier 5 (Mode Libre) —
c'est-à-dire au moment le plus dur. Mesuré : **0,00 record de proximité par jour** sur
2000 jours. Une falaise, là où il fallait une pente.

Le curseur pilote **les deux** sources d'aide à la fois (`RECOMPENSE_APPROCHE_BUT` sur
DoorKey et les records de proximité ailleurs), au lieu de deux mécaniques qui s'éteignaient
différemment.

### 🛟 Le filet — « quand il bloque, on l'aide un peu »

Un agent qui stagne longtemps reçoit un **surplus** d'aide, progressif :

| Jours sans victoire | Renfort |
|---|---|
| ≤ 30 | ×1,0 — un échec est normal, pas un blocage |
| 45 | ×1,5 |
| 60 | ×2,0 |
| ≥ 90 | **×3,0** (maximum) |

Trois garanties : le renfort se replie **dès la première victoire** (une bouée, pas une
rente) ; il ne touche **jamais la récompense terminale** (on aide à trouver le chemin, on
n'offre pas la victoire) ; et il se remet à zéro **à chaque promotion** (sinon un agent
promu arriverait avec un renfort déjà armé).

> ℹ️ **Pas de redescente de palier.** Décision utilisateur : un agent ne doit pas se
> retrouver face à un palier impossible, mais on ne le fait pas non plus reculer — on
> l'aide davantage. « Ce qui ne régresse jamais » (§11) reste vrai.

### Ce que ça donne — mesuré

Cerveau neuf, 100 jours. L'agent cale à `Maternelle` après 3 promotions rapides :

```
 jour  niv  nom                          maîtrise  guidage  stagn  vict
    5    2  Maternelle (Longue distance)     —      1.00      0      4
   40    2  Maternelle                      0.00    1.13     35      4   ← le filet s'arme
   60    2  Maternelle                      0.00    1.80     55      4
   80    2  Maternelle                      0.00    2.47     75      4
  100    2  Maternelle                      0.05    1.00      5      7   ← VICTOIRES, filet replié
```

Sans filet, ce cerveau serait resté à 4 victoires. Le run de référence sans cette mécanique
calait à **0 % de maîtrise pendant 79 jours**.

### Où le lire

Ligne console, chaque nuit :

```
├─ Cursus : 🎓 Niveau 3/15 — maîtrise 0% (n=20), seuil 60% | série 0/2 | 🛟 filet ×2.5 (75 j sans victoire)
```

Côté W&B : `Cursus_Facteur_Guidage` (< 1 = sevrage, > 1 = filet, **1,0 constant = aucune des
deux ne sert**) et `Cursus_Jours_Stagnation`.

---

## 7. Les 7 paliers DoorKey — le détail complet

Actifs uniquement sur le niveau "Collège" (`MiniGrid-DoorKey-6x6-v0`). C'est le cursus le plus
détaillé du projet — chaque palier récompense un sous-objectif logique vers "ouvrir la porte et
sortir".

| Palier | Nom | Ce que l'agent doit faire | Poids de choc dopaminergique |
|---|---|---|---|
| 1 | Regarder | Repérer la clé du regard | 0.15 |
| 2 | S'approcher | Se rapprocher de la clé | 0.10 |
| 3 | Toucher/Prendre | Ramasser la clé | 0.85 |
| 4 | Transporter | Se déplacer en la portant | 0.10 |
| 5 | Viser la Porte | S'approcher de la porte, clé en main | 0.15 |
| 6 | Déverrouiller | Ouvrir la porte verrouillée | 0.90 |
| 7 | Franchir & Sortir | Passer la porte et atteindre le but | 1.00 |

### Comment on passe au palier suivant : le système "2+2" (Abnégation)

Chaque palier exige **4 succès cumulés**, en deux temps :
- **Sous-Seuil 1 (Amorçage)** : 2 succès, patience normale.
- **Sous-Seuil 2 (Abnégation)** : 2 succès **supplémentaires**, mais avec une patience étirée
  ×1.6 — l'agent doit prouver qu'il réussit même quand on lui laisse moins de marge, avant la
  vraie promotion.

Dès le **palier 5**, le **Mode Libre** s'active automatiquement (voir §9) — le guidage artificiel
disparaît, l'agent doit se débrouiller avec sa propre planification.

---

## 8. Le curriculum vocal — les 19 paliers

Complètement **indépendant** du niveau MiniGrid — un agent peut être au palier vocal 15 tout en
étant encore au niveau "Primaire". Progression :

| Paliers | Contenu |
|---|---|
| 1 | Vocaliser (n'importe quel son) |
| 2 – 6 | Voyelles a / e / i / o / u |
| 7 – 9 | Syllabes ba / ma / pa |
| 10 – 11 | Mots courts papa / maman |
| 12 | Mot "porte" |
| 13 – 14 | Combinatoire "ouvre porte" / "prends clé" |
| 15 – 18 | Nommer mur / clé / but / vide (synesthésie, v27.0) |
| 19 | Syntagme couleur+objet, ex. "porte jaune" (dernier palier) |

### Comment on passe au palier suivant

Même mécanique 2+2 que les paliers DoorKey, mais le **seuil de réussite du jour** n'est pas fixe
— il **augmente progressivement** avec le palier déjà atteint : `0.15` (très permissif, palier 1)
jusqu'à `0.45` (exigeant, palier 19). C'est volontaire : un seuil fixe trop haut avait bloqué un
run réel de 1000 jours à 0 promotion (l'oreille n'apprenait jamais rien) — voir
[docs/explications_readme.md](explications_readme.md) §11.3 pour le détail.

---

## 9. Mode Guidé vs Mode Libre

Deux réglages globaux qui changent la façon dont l'agent décide, appliqués automatiquement selon
la progression DoorKey :

| | Mode Guidé (paliers 1-4) | Mode Libre (palier ≥ 5) |
|---|---|---|
| Poids du Système 2 (planification mentale) | 0.5 | **0.85** — l'agent s'appuie bien plus sur sa propre réflexion |
| Entropie (exploration) | 0.02 | **0.06** — plus d'exploration spontanée |
| Récompense de guidage continue (approche du but) | Active | **Retirée** — plus de béquille artificielle |
| Curiosité JEPA (sous-quêtes spontanées) | Inactive | **Active** |
| Sursaut de Volonté (2ème souffle avant l'abandon) | Inactif | **Actif** |

En clair : au début, l'agent est "aidé" par des récompenses intermédiaires généreuses ; passé le
palier 5, on lui retire cette béquille et on le laisse s'appuyer sur ses propres capacités
(planification, curiosité, persévérance).

---

## 10. La patience adaptative — pourquoi un épisode s'arrête

Chaque épisode (une tentative dans MiniGrid) n'a **pas** un nombre de ticks fixe — la patience
s'adapte entre `PATIENCE_MIN=50` et `PATIENCE_MAX=350` ticks, selon deux facteurs :
- **Le taux de succès récent** (sur les 20 derniers épisodes) — un agent qui réussit souvent
  obtient plus de patience de base (contre-intuitif, mais ça évite d'abandonner trop tôt un
  épisode qui dérape alors que l'agent maîtrise généralement la tâche).
- **La vitesse de succès** — un agent rapide obtient un bonus supplémentaire.

En Mode Libre, un mécanisme supplémentaire (le **Sursaut de Volonté**, `🔥` dans les logs) peut
étirer la patience une fois par épisode, à 95% du budget déjà consommé — un "2ème souffle" avant
l'abandon.

---

## 11. Ce qui NE régresse jamais (et comment le savoir quand même)

**Aucune des progressions ci-dessus ne peut redescendre** — ni le niveau MiniGrid, ni le palier
DoorKey, ni le palier vocal. Un agent qui devient moins bon sur un palier déjà acquis reste
officiellement à ce palier, pour toujours.

Ce que tu peux regarder à la place pour détecter une dégradation réelle :
- **`Taux_Maitrise_Palier`** (W&B) — pourcentage d'épisodes réussis dans la journée, peut chuter
  même si `Palier_Cible` reste figé.
- **`Recompense_Moyenne`** et **`Erreur_JEPA`** — une hausse durable de l'erreur JEPA ou une
  chute de la récompense moyenne, sur plusieurs jours, est le signal le plus fiable qu'il y a un
  problème.
- **`Teneur_Dopamine`** — un agent en échec prolongé voit sa dopamine baisser durablement (état
  "Démotivé"/"Léthargique" dans les logs), ce qui ralentit aussi sa plasticité (protection contre
  la dégradation, pas un symptôme séparé).

Il n'existe pas (encore) de mécanisme qui ferait explicitement redescendre un palier. Si tu veux
ça, c'est une mécanique à ajouter — ce n'est pas dans le projet aujourd'hui.

---

## 12. Où trouver chaque cerveau (`brains/*.brain`)

| Fichier | Utilisé par | Note |
|---|---|---|
| `brains/naulthene_cursus.brain` | Cursus par Ères | |
| `brains/naulthene_bb.brain` | Cerveau Bébé | |
| `brains/naulthene_parole.brain` | Cursus de la Parole | |
| `brains/naulthene_v21.brain` | La Cuve | |

Ces 4 fichiers sont **totalement indépendants** — jamais partagés, jamais fusionnés entre eux.
Ils sont gitignorés (`brains/*.brain`), donc jamais poussés sur GitHub : chaque machine a ses
propres cerveaux, localement.

### Repartir d'un cerveau neuf sans perdre l'ancien

Aucun des scripts n'a de flag `--reset` — le chemin `.brain` est fixe par cursus. Pour faire
naître un cerveau neuf, **archive l'ancien plutôt que de le supprimer** :

```bash
mv brains/naulthene_cursus.brain brains/naulthene_cursus_archive_$(date +%Y%m%d).brain
```

Le prochain lancement affichera `🐣 Naissance d'un nouveau cerveau` au lieu de `🧬 Résurrection`.
L'ancien reste utilisable normalement (avec l'Arène par exemple, `--brain
brains/naulthene_cursus_archive_YYYYMMDD.brain`).

---

## 13. Lire un bilan de nuit — exemple annoté

Chaque nuit (tous cursus confondus) affiche un bilan de ce type :

```
🌙 Jour 001 [Primaire (Mouvement basique)]
  ├─ État Mental    : ⚡ Motivé (Dopamine: 8.000/10.0 [80%])
  ├─ Plasticité     : 🧠 Empreinte Enfance Forte (Bus: 16 dims, Empreinte: 1.00, Plasticité base: 1.00)
  ├─ Quête Auto     : 🧭 10 nouveaux records de proximité au But
  ├─ Consolidations : 💤 117 souvenirs rejoués (58.746% de la journée, perte rêves: 0.1631)
  ├─ Potentiomètre  : ⏳ Patience de base du jour: 200 ticks/épisode (1 abandon(s) lucide(s), 0 Sursaut(s) de Volonté)
  ├─ État Viscéral  : 🍎 Satiété 0.00 | 💧 Hydratation 0.40 | ✨ Stimulation 1.00
  ├─ Les 5 Sens     : ✋ Contact 28.5% | 🔑 Portage 20.5% | 👃 Odorat 96.0% des ticks (max 1.50) | 👅 Goût 75 tick(s)
  ├─ Clinotaxie     : 🧭 Approche 70.4% des ticks de variation (|ΔS| moyen 0.124 sur 27 tick(s))
  ├─ Métabolisme    : r_bio cumulé -1.756 — 0 Nourriture(s), 1 Eau(x) consommée(s)
  ├─ Mémoire Épiso. : 🗺️ 1 souvenir(s) spatial(aux) actif(s)
  └─ Erreur JEPA moy: 0.1400 | Réc. moyenne: 0.000 | Thermostat: Stable
```

| Ligne | Ce que ça veut dire |
|---|---|
| **État Mental** | La dopamine du jour (0 à 10), traduite en émotion lisible (Motivé/Neutre/Démotivé...) |
| **Plasticité** | Taille actuelle du "cerveau" (Bus, en dimensions — grandit par neurogenèse) et à quel point il apprend vite cette nuit |
| **Quête Auto** | Progrès génériques, indépendants de tout palier codé en dur (se rapprocher du but) |
| **Consolidations** | Le "rêve" nocturne — combien de souvenirs ont été rejoués pour consolider l'apprentissage |
| **Potentiomètre** | La patience du jour (combien de ticks avant d'abandonner un épisode qui dérape) |
| **État Viscéral** | Faim/soif/stimulation — motivations biologiques internes |
| **Les 5 Sens** (v29.1) | Ce que l'agent a *senti* dans la journée — voir §15 pour la lecture détaillée |
| **Clinotaxie** (v32.0) | S'il s'est *rapproché* ou *éloigné* des ressources qu'il sentait. Absente si l'odeur n'a jamais varié — voir §15 |
| **Erreur JEPA / Thermostat** | À quel point le modèle du monde se trompe encore ; `MUTATION !` = le cerveau vient de grandir (+16 dimensions) |

Sur le niveau "Collège" (DoorKey actif), une ligne supplémentaire apparaît :
```
  ├─ Progrès Jalon  : 🎯 Palier 3 (Toucher/Prendre) — 2/5 épisodes réussis (taux: 40%)
  ├─ Abnégation     : 📿 Sous-Seuil 1 (Amorçage) — 2/2 succès (complexité: x1.0)
```

---

## 14. Foire aux questions

**Je peux lancer deux cursus en même temps ?**
Techniquement oui (chacun a son propre fichier `.brain`), mais ne lance jamais deux scripts sur
**le même** fichier `.brain` simultanément — risque d'écrasement lors de la sauvegarde.

**Combien de temps prend un run complet ?**
Ça dépend entièrement de ta machine (device `mps`/`cuda`/`cpu`) — aucune estimation fiable n'est
documentée dans le projet. Le plus simple est de lancer un run court (`--jours 5`) et d'observer
le temps réel par jour affiché en console, puis d'extrapoler.

**Le cursus s'est arrêté tout seul, pourquoi ?**
Vérifie le message affiché juste avant la fin. Le Cursus par Ères a un garde-fou : si après 100
jours le palier vocal n'a jamais quitté le palier 1 (aucun premier succès), le script s'arrête
proprement plutôt que de tourner à vide (voir [docs/LANCEMENT.md](LANCEMENT.md), section Dépannage).

**Comment observer un cerveau entraîné sans risquer de l'abîmer ?**
L'Arène (`PYTHONPATH=src python -m naulthene.instruments.lancer_arene --brain <fichier>`) —
lecture seule garantie, ne modifie jamais le `.brain`. Voir [docs/LANCEMENT.md](LANCEMENT.md) §7.

**Est-ce que le Port Exocortex C3 (v28.0) change quelque chose à ces cursus ?**
Non, par défaut. Les 3 cursus autonomes n'enregistrent aucun plug C3 — l'action supplémentaire
`ACTION_DEMANDER` reste masquée et le comportement est identique à avant la v28.0. Voir
[docs/CHANGELOG.md](CHANGELOG.md) (entrée v28.0-experimental) et [docs/LANCEMENT.md](LANCEMENT.md) §8 pour tester ce canal
séparément.

**Et les 5 sens (v29) — il y a quelque chose à activer ?**
Non, rien. Le Bus Sensoriel est actif automatiquement dans les 4 parcours, sans option ni flag.
La seule chose à savoir : au premier chargement d'un `.brain` créé avant la v29, un message
`👃 integrateur_bio greffé de N à M dims d'entrée` s'affiche **une seule fois** — c'est normal,
tous les acquis sont conservés. Voir §15 ci-dessous.

**Et l'odorat topologique / la clinotaxie (v32) ?**
Rien à activer non plus. Deux messages apparaissent une seule fois sur un `.brain` antérieur :
la greffe `👃 ... 80 à 82 dims` **et** `🔄 Optimiseur réinitialisé`. Les deux sont normaux et
aucun poids appris n'est perdu — seule la dynamique Adam repart à neuf. Cette seconde ligne
corrige un bug qui faisait planter la **première nuit** d'un cerveau greffé (latent depuis la
v29.0, invisible tant qu'on ne validait qu'en ticks sans aller jusqu'à la nuit).

---

## 15. Les 5 sens de l'agent (v29)

Jusqu'à la v28, Naulthène ne percevait le monde que par **deux** sens : la vue et l'ouïe. Depuis
la v29, il en a **cinq** — les trois nouveaux étant justement les moins coûteux à calculer et les
plus directement liés à la survie.

| Sens | Ce que l'agent perçoit | Coût de calcul |
|---|---|---|
| 👁 **Vue** | La grille MiniGrid (147 valeurs) | Très élevé |
| 👂 **Ouïe** | Le son brut (130 coefficients MFCC) | Élevé |
| ✋ **Toucher** | Un obstacle devant lui, un objet dans sa main, son orientation | Moyen |
| 👃 **Odorat** | Une source de nourriture/eau proche — **en contournant les murs** depuis la v32.0, avec le sens de variation (« je me rapproche / je m'éloigne ») | Faible |
| 👅 **Goût** | Ce qu'il vient d'avaler (persiste ~10 ticks) | Faible |

**Ce que ça change concrètement** : avant, l'agent ne savait qu'il tenait la clé que de façon
*indirecte*, en le déduisant de son champ visuel. Maintenant il la « sent » dans sa main. De même,
il peut détecter une ressource proche **avant même de la voir**.

### Suivre les sens jour après jour

Chaque nuit, une ligne dédiée s'affiche (voir §13) :

```
├─ Les 5 Sens : ✋ Contact 28.5% | 🔑 Portage 20.5% | 👃 Odorat 96.0% des ticks (max 1.50) | 👅 Goût 75 tick(s)
```

| Champ | Comment le lire |
|---|---|
| **Contact** | % du temps passé au contact d'un mur/porte. Très haut durablement = l'agent se cogne ou reste bloqué |
| **Portage** | % du temps avec un objet en main. **Sur DoorKey, c'est le temps passé à porter la clé** — c'est le meilleur indicateur *avancé* : il monte quand l'agent commence à maîtriser les paliers 3-4, souvent avant que les victoires n'arrivent |
| **Odorat** | % de ticks où il sent quelque chose (voir l'avertissement ci-dessous) |
| **Goût** | Nombre de ticks avec un goût rémanent — à rapprocher des Nourriture(s)/Eau(x) de la ligne Métabolisme |

Si le suffixe **`⚠️ BUS DÉSACTIVÉ`** apparaît, les 3 sens faibles ne fonctionnent plus (API
MiniGrid incompatible). L'entraînement continue normalement, mais l'agent est « anesthésié » —
c'est l'alerte à surveiller.

Côté W&B, 7 courbes `Sens_*` sont enregistrées chaque nuit.

> ⚠️ **Un `Odorat` élevé (90-100 %) reste NORMAL** : ce pourcentage compte la **présence** d'une
> trace, pas son intensité. La saturation diagnostiquée en v29.1 a été corrigée deux fois depuis —
> par l'atténuation exponentielle (v30.0), puis par la distance topologique (v32.0) — mais le
> seuil de coupure étant bas, un signal faible compte quand même comme « actif ». Ce qu'il faut
> regarder, c'est **`Sens_Odorat_Moyen`** dans W&B (~0.32 contre ~0.54 en v29).
> Un `Odorat` à **0 %** sur un niveau où des ressources existent mérite en revanche un coup d'œil
> — sauf si un mur sépare l'agent des sources, ce qui les rend **volontairement inodores** depuis
> la v32.0.

### La clinotaxie — « est-ce que je me rapproche ? » (v32.0)

Depuis la v32.0, une ligne supplémentaire peut apparaître :

```
├─ Clinotaxie     : 🧭 Approche 70.4% des ticks de variation (|ΔS| moyen 0.124 sur 27 tick(s))
```

Jusque-là, l'agent percevait l'**intensité** d'une odeur mais était incapable de savoir si son
dernier pas l'avait rapproché ou éloigné de la source — il était aveugle au mouvement. Il perçoit
désormais aussi la **variation**.

`Approche X%` se lit comme suit : ≈ 50 % signifie que l'agent monte et descend le gradient au
hasard (la clinotaxie ne l'oriente pas), nettement au-dessus qu'elle fait son travail. **Toujours
regarder le nombre de ticks entre parenthèses d'abord** : sur un agent qui bouge peu, le
pourcentage est du bruit. Voir [docs/LANCEMENT.md](LANCEMENT.md) §13 pour le détail.

📖 Pour le détail complet (formules, pourquoi ces sens n'entrent pas dans le modèle du monde,
compatibilité des anciens cerveaux) : **[EXPLICATIONS_v29_sens.md](Old_Archive_rmd/EXPLICATIONS_v29_sens.md)**.
