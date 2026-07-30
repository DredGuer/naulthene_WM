# Le Parcours de Naulthène — Guide Complet du Système de Cursus

Ce document explique, en langage clair, **comment Naulthène apprend au fil du temps** : les
commandes pour lancer chaque parcours, combien de temps ça prend, ce que chaque palier signifie
concrètement, et comment lire les logs/W&B pour suivre la progression. C'est le complément
pratique de [readme.md](readme.md) (vision d'ensemble et formules) et
[docs/explications_readme.md](docs/explications_readme.md) (détail algorithmique) — ici, l'angle
est **"je veux lancer un run et comprendre ce qui se passe"**.

Référence code : `src/naulthene/cerveau/noyau.py` (v28.0) et les trois scripts de
`src/naulthene/salles_de_classe/`.

---

## Table des matières

1. [Les 4 parcours possibles — vue d'ensemble](#1-les-4-parcours-possibles--vue-densemble)
2. [Le Cursus par Ères (`cursus_developpemental.py`)](#2-le-cursus-par-ères-cursus_developpementalpy)
3. [Le Cerveau Bébé (`cursus_bebe.py`)](#3-le-cerveau-bébé-cursus_bebepy)
4. [Le Cursus de la Parole (`cursus_parole.py`)](#4-le-cursus-de-la-parole-cursus_parolepy)
5. [La Cuve (mode manuel client-serveur)](#5-la-cuve-mode-manuel-client-serveur)
6. [Les 5 niveaux MiniGrid (`PROGRAMME`)](#6-les-5-niveaux-minigrid-programme)
7. [Les 7 paliers DoorKey — le détail complet](#7-les-7-paliers-doorkey--le-détail-complet)
8. [Le curriculum vocal — les 19 paliers](#8-le-curriculum-vocal--les-19-paliers)
9. [Mode Guidé vs Mode Libre](#9-mode-guidé-vs-mode-libre)
10. [La patience adaptative — pourquoi un épisode s'arrête](#10-la-patience-adaptative--pourquoi-un-épisode-sarrête)
11. [Ce qui NE régresse jamais (et comment le savoir quand même)](#11-ce-qui-ne-régresse-jamais-et-comment-le-savoir-quand-même)
12. [Où trouver chaque cerveau (`brains/*.brain`)](#12-où-trouver-chaque-cerveau-brainsbrain)
13. [Lire un bilan de nuit — exemple annoté](#13-lire-un-bilan-de-nuit--exemple-annoté)
14. [Foire aux questions](#14-foire-aux-questions)

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

**Tous les 4 lancent le même cerveau (`AGI_Naulthene`)** avec la même architecture (v28.0 : 8
actions, dont l'action C3 optionnelle — voir `docs/CHANGELOG.md` v28.0) — seule la boucle qui
pilote les journées change.

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
1. **Le niveau MiniGrid** (`PROGRAMME`, 5 niveaux — voir §6) et, à l'intérieur du niveau
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
macOS (`say`). Voir `docs/LANCEMENT.md` §0bis pour le détail complet.

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
autonomes, mais tu contrôles quand arrêter chaque session. Voir `docs/LANCEMENT.md` §1-5 pour le
détail complet (options, dépannage).

---

## 6. Les 5 niveaux MiniGrid (`PROGRAMME`)

C'est la progression "scolaire" de base, commune à **tous** les parcours (elle vit dans le
cerveau, pas dans un cursus particulier).

| # | Environnement | Nom | Ce que ça teste |
|---|---|---|---|
| 0 | `MiniGrid-Empty-8x8-v0` | **Primaire** (Mouvement basique) | Se déplacer sans se cogner |
| 1 | `MiniGrid-DoorKey-6x6-v0` | **Collège** (Logique Simple) | Trouver une clé, ouvrir une porte (7 paliers, voir §7) |
| 2 | `MiniGrid-Unlock-v0` | **Lycée** (Manipulation Avancée) | Déverrouiller un coffre |
| 3 | `MiniGrid-MemoryS7-v0` | **Université** (Mémoire Épisodique) | Se souvenir d'un indice vu plus tôt |
| 4 | `MiniGrid-MultiRoom-N4-S5-v0` | **Doctorat** (Planification Longue) | Traverser plusieurs pièces jusqu'au but |

**Comment on passe au niveau suivant** : il faut **2 victoires consécutives** sur le niveau
courant (`VICTOIRES_REQUISES=2`). Une seule défaite entre-temps remet le compteur à zéro (mais le
niveau lui-même ne recule jamais). Un message `🎓 [PROMOTION]` s'affiche au changement de niveau.

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
`docs/explications_readme.md` §11.3 pour le détail.

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
proprement plutôt que de tourner à vide (voir `docs/LANCEMENT.md`, section Dépannage).

**Comment observer un cerveau entraîné sans risquer de l'abîmer ?**
L'Arène (`PYTHONPATH=src python -m naulthene.instruments.lancer_arene --brain <fichier>`) —
lecture seule garantie, ne modifie jamais le `.brain`. Voir `docs/LANCEMENT.md` §7.

**Est-ce que le Port Exocortex C3 (v28.0) change quelque chose à ces cursus ?**
Non, par défaut. Les 3 cursus autonomes n'enregistrent aucun plug C3 — l'action supplémentaire
`ACTION_DEMANDER` reste masquée et le comportement est identique à avant la v28.0. Voir
`docs/CHANGELOG.md` (entrée v28.0-experimental) et `docs/LANCEMENT.md` §8 pour tester ce canal
séparément.
