# Guide de Lancement — Naulthène AGI (Cuve Persistante + Hémisphère Audio + Cursus par Ères + Cerveau Bébé + Cursus de la Parole + Port Exocortex C3 + Bus Sensoriel)

Ce guide couvre le lancement local (Mac) de l'écosystème V21-V30 : le cerveau persistant
(`daemon_cerveau.py`, dans `src/naulthene/cuve/`) et ses deux clients (`client_corps.py` pour
MiniGrid, `client_professeur.py` pour les leçons de parole ponctuelles), trois cursus
développementaux autonomes (`src/naulthene/salles_de_classe/`) : le Cursus par Ères
(`cursus_developpemental.py`, 1000 jours, voir §6), le Cerveau Bébé (`cursus_bebe.py`, 1440
jours, voir §6bis) et le Cursus de la Parole (`cursus_parole.py`, 900 jours, v27.0-expérimental,
voir §6ter), le Port Exocortex C3 (`src/naulthene/exocortex/`, v28.0-expérimental, voir §8),
le Bus Sensoriel des 5 sens (`src/naulthene/cerveau/bus_sensoriel.py`, v29.0-expérimental, voir
§9), l'Exo-Sens — le 6ᵉ sens (v30.0-expérimental, voir §10) et les métriques de calibrage
(v30.1, voir §11). Voir `readme.md` pour l'architecture complète, `CHANGELOG.md` pour
l'historique des versions, et [Old_Archive_rmd/](Old_Archive_rmd/) pour les documents de
conception historiques.

> 🆕 **v29.0/v29.1 — rien à configurer.** Le Bus Sensoriel (toucher, odorat, goût) est **actif
> automatiquement** dans tous les modes ci-dessous : aucune option de ligne de commande, aucun
> flag. Le seul point à connaître est le message de greffe `👃 integrateur_bio greffé de N à M
> dims d'entrée` au premier chargement d'un `.brain` antérieur — normal, une seule fois, les
> acquis sont préservés (voir §9 et le tableau de dépannage). Depuis la v29.1, chaque bilan de
> nuit affiche en plus une ligne « Les 5 Sens » (voir §9bis).
>
> 🆕 **v30.0 — également rien à configurer.** L'odorat devient un gradient exponentiel (plus
> discriminant en proximité) et l'agent gagne un **6ᵉ sens exogène** (l'Exo-Sens) — mais celui-ci
> reste **totalement neutre tant qu'aucun plug C3 n'est branché**, ce qui est le cas par défaut de
> tous les modes ci-dessous. Voir §10 pour brancher un plug et observer ce 6ᵉ sens.

Depuis le passage en package Python (voir `CLAUDE.md`, section « Architecture »), tous les
scripts se lancent depuis la racine du dépôt avec `PYTHONPATH=src` et l'option `-m` (module),
jamais en appelant directement le fichier `.py`.

---

## 0. Prérequis (une seule fois)

Vérifier que tout est en place avant le premier lancement :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
pip list | grep -iE "torch|gymnasium|minigrid|wandb|sounddevice|librosa|whisper"
```

Si un paquet manque :

```bash
pip install torch gymnasium minigrid wandb numpy sounddevice librosa openai-whisper requests
```

Vérifier qu'Ollama tourne (nécessaire pour le Professeur Gemma) :

```bash
curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama actif" || echo "❌ Lance l'app Ollama"
```

`say` (TTS macOS) est natif, rien à installer.

---

## 0bis. Enregistrer ta voix (facultatif, v27.0-expérimental)

**Cette étape est entièrement facultative** — tous les modes de lancement ci-dessous (Cuve,
Cursus par Ères, Cerveau Bébé, Cursus de la Parole) fonctionnent sans elle, avec un repli
automatique sur `say` exactement comme avant la v27.0. Elle sert uniquement à remplacer la
cible théorique des voyelles/mots par la voix réelle de l'utilisateur.

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src python -m naulthene.instruments.enregistreur_voix --prises 3
```

- Sans `--mots`, enregistre tout le curriculum vocal (`professeur_gemma.CURRICULUM_VOCAL`).
- `--mots a e i o u porte clé` : ne demande que ces mots-là.
- `--prises N` (défaut 3) : nombre de prises par mot — **recommandé de rester à 3 minimum**,
  la cible F1/F2 est estimée par la médiane des prises (une prise ratée, toux ou saturation, est
  ignorée dès qu'il y en a au moins 3).
- `--duree 2.0` : durée d'enregistrement par prise, en secondes.
- `--pas-de-relecture` : désactive la relecture/validation après chaque prise (enregistrement
  plus rapide, moins de contrôle qualité).

Les prises sont écrites dans `voix/<mot>/<mot>_NN.wav` (jamais trackées par git, comme
`brains/*.brain` — voir `.gitignore`). N'importe quel cursus qui utilise
`lecons_vocales.CacheReferencesVocales` (Cursus par Ères, Cerveau Bébé, Cursus de la Parole,
l'Arène) lit automatiquement cette banque à son prochain lancement — aucune configuration
supplémentaire.

---

## 1. Démarrer la Cuve (le cerveau persistant)

**Terminal 1** — à garder ouvert tant que tu veux que le cerveau soit disponible :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src python -m naulthene.cuve.daemon_cerveau --port 9999 --brain brains/naulthene_v21.brain
```

- Ressuscite ton cerveau existant (tick_absolu, dopamine, curriculum, souvenirs intacts).
- Si c'est la première connexion depuis la V22, tu verras des messages de greffe :
  `🌱 Hémisphères nouvellement greffés` et `🔄 integrateur_bio exclu du chargement` —
  normal, une fois seulement (voir `docs/Old_Archive_rmd/CONCEPTION_v22_audio.md` §11 pour le détail).
- **Depuis la v29.0**, un `.brain` antérieur affiche en plus, une seule fois,
  `👃 integrateur_bio greffé de N à M dims d'entrée (+8 : toucher/odorat/goût)` — la couche
  n'est **plus jamais exclue** dans ce cas, elle est greffée par recopie et **tous les acquis
  sont préservés au bit près** (voir §9).
- Reste en **cryostase** (CPU ~0%) tant qu'aucun client n'est connecté.
- `Ctrl+C` pour arrêter proprement (sauvegarde d'urgence automatique).

Options utiles :
- `--brain <fichier>` : utiliser un autre fichier `.brain` (par défaut `brains/naulthene_v21.brain`).
- `--wandb` : active le logging Weights & Biases (désactivé par défaut).

⚠️ **Un seul client à la fois** — le protocole ne gère pas les connexions concurrentes.

---

## 2. Option A — Entraînement MiniGrid

**Terminal 2** :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src python -m naulthene.cuve.client_corps --port 9999 --continu
```

- `--continu` : tourne indéfiniment jusqu'à `Ctrl+C` (recommandé pour un vrai entraînement).
- `--ticks 2000` : à la place de `--continu`, pour une session bornée à N ticks.
- `--delai 0.05` : pause entre deux ticks en secondes (0 par défaut = aussi vite que possible).

`Ctrl+C` pour arrêter — le client attend la fin du tick en cours côté Cuve (jusqu'à 30s si
une nuit complète est en train de se dérouler), puis une pause de sécurité de 2s avant de
rendre la main. Le cerveau s'endort (nuit complète ou micro-sieste selon les ticks vécus)
et se sauvegarde automatiquement côté Cuve.

---

## 3. Option B — Leçon de parole (Hémisphère Audio)

**Terminal 2** (jamais en même temps que l'option A) :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src python -m naulthene.cuve.client_professeur --port 9999 --palier 2 --ticks 100
```

- `--palier N` : le palier du curriculum vocal (voir tableau ci-dessous).
- `--ticks N` : nombre de ticks de la leçon (défaut 100).
- `--micro` : utilise ton micro (2s d'enregistrement) comme référence au lieu de `say`.
- `--delai 0.5` : pause entre deux ticks (0.5s par défaut, pour laisser le temps d'écouter).

| Palier | Contenu |
|--------|---------|
| 1 | Vocaliser (n'importe quel son) |
| 2–6 | Voyelles a / e / i / o / u |
| 7–9 | Syllabes ba / ma / pa |
| 10–11 | Mots courts papa / maman |
| 12 | Mot "porte" |
| 13–14 | Combinatoire "ouvre porte" / "prends clé" |
| 15–18 (v27.0) | Nommer mur / clé / but / vide |
| 19 (v27.0) | Syntagme couleur+objet "porte jaune" |

Tu **entends l'agent babiller en temps réel**, avec un score de proximité de formants
affiché à chaque tick. En fin de leçon (si non interrompue), un jugement qualitatif de
Gemma s'affiche (~10-30 secondes d'attente, normal — voir `professeur_gemma.py`).

`Ctrl+C` interrompt proprement la leçon à tout moment (bilan + fermeture propre de la
connexion, pas de crash — voir correctif ci-dessous).

### ⚠️ Point important : le score peut stagner sur une leçon courte

Sur une leçon de quelques dizaines de ticks, le score de formants peut rester
**parfaitement figé** d'un tick à l'autre (ex. `0.079` en boucle). Ce n'est pas un bug :
une nuit complète (`apprendre_journee`, qui fait progresser la bouche) ne se déclenche
qu'après **400 ticks** accumulés (`ticks_par_jour`, voir `src/naulthene/cerveau/noyau.py`). En dessous
de ce seuil, aucun apprentissage n'a encore eu lieu — le réseau produit un vecteur vocal
stable car l'entrée (la référence audio de la leçon) est elle-même constante sur toute la
durée. **Pour voir une vraie progression du score, lance une leçon d'au moins 400-500
ticks** (`--ticks 500`), ou enchaîne plusieurs leçons courtes sur le même palier — les
ticks s'accumulent côté Cuve d'une leçon à l'autre tant que le daemon reste allumé.

---

## 4. Alterner MiniGrid et leçons de parole

Le cerveau est unique et persistant — tu peux alterner librement :

```bash
# Session MiniGrid
PYTHONPATH=src python -m naulthene.cuve.client_corps --port 9999 --continu
# Ctrl+C quand tu veux

# Puis une leçon de parole sur le MÊME cerveau
PYTHONPATH=src python -m naulthene.cuve.client_professeur --port 9999 --palier 2 --ticks 500
# Ctrl+C ou fin naturelle

# Retour à MiniGrid...
PYTHONPATH=src python -m naulthene.cuve.client_corps --port 9999 --continu
```

La Cuve (Terminal 1) reste allumée entre chaque session — aucun besoin de la relancer.

---

## 5. Arrêt complet (Cuve/daemon, sections 1-4)

Dans le Terminal 1 (la Cuve) : `Ctrl+C`. Un message confirme la sauvegarde d'urgence. Le
fichier `brains/naulthene_v21.brain` contient l'état exact du cerveau à cet instant — tu peux
relancer `daemon_cerveau.py` plus tard, il reprendra exactement où il en était.

---

## 6. Le Cursus Développemental par Ères (autonome, 1000 jours)

Contrairement aux sections 1-5 (qui utilisent la Cuve/daemon), ce mode ne passe **pas** par
`daemon_cerveau.py` — c'est un script **standalone** qui pilote directement un cerveau. Il
alterne automatiquement MiniGrid le matin et apprentissage vocal l'après-midi, sur 3 ères de
difficulté croissante (voir `readme.md`, section "Le Cursus Développemental par Ères").

⚠️ **Cerveau séparé** : `cursus_developpemental.py` charge/sauvegarde un fichier dédié
`brains/naulthene_cursus.brain` — distinct de `brains/naulthene_v21.brain` utilisé par la Cuve.
C'est un cerveau différent de celui de la Cuve ; ne lance pas le daemon (Terminal 1) en même
temps, ce n'est pas nécessaire pour ce mode.

✅ **Persistance automatique (v24.0)** : le cursus sauvegarde après CHAQUE nuit (donc chaque
jour subjectif) dans `brains/naulthene_cursus.brain`. Relancer la même commande **reprend** le
cursus là où il en était (pas de retour à zéro) — `--jours N` ajoute N jours SUPPLÉMENTAIRES à
partir de l'état repris, ce n'est pas une valeur absolue. Premier lancement : naissance d'un
cerveau neuf (bus=16), aucun fichier trouvé.

**Un seul terminal**, pas de Cuve à lancer :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_developpemental --jours 1000
```

- `--jours N` : nombre de jours subjectifs du cursus (défaut 1000 = `DUREE_ERE`).
- `--no-wandb` : désactive le logging Weights & Biases (actif par défaut, ici forcé en
  hors-ligne par `WANDB_MODE=offline` pour ne pas dépendre d'une connexion).
- Retire `WANDB_MODE=offline` si tu es connecté et veux suivre le run en direct sur wandb.ai.

**Recommandé pour un premier essai** (valider que tout tourne avant de lancer les 1000 jours,
qui prendront plusieurs heures) :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_developpemental --jours 5
```

Au démarrage, le script préchauffe les références vocales (5-10 appels `say`, une seule fois)
puis enchaîne les journées. Chaque journée affiche le bilan de nuit habituel, plus la ligne
`🎓 [PROMOTION VOCALE]` quand le palier vocal progresse. Un changement d'ère est signalé par
`🌅 [NOUVELLE ÈRE]` (jour 400 → Synesthésie, jour 600 → Intégration, avec les valeurs par
défaut de `BORNES_ERES`).

`Ctrl+C` interrompt le script proprement à tout moment — sauvegarde d'urgence automatique de la
journée déjà consolidée (seule la journée EN COURS au moment du Ctrl+C est perdue, jamais les
précédentes). Relance simplement la même commande pour reprendre.

---

## 6bis. Le Cerveau Bébé Développemental (autonome, 1440 jours)

Comme le Cursus par Ères (§6), ce mode ne passe **pas** par `daemon_cerveau.py` — c'est un
script **standalone** (`src/naulthene/salles_de_classe/cursus_bebe.py`, v25.0/v26.0,
expérimental) qui pilote directement un cerveau à travers **4 ans (1440 jours subjectifs ×
3600 ticks/jour)** découpés en 5 phases d'âge, avec récompense externe masquée pendant les 240
premiers jours (voir `readme.md`, section "Nouveautés v25.0 — Le Cerveau Bébé Développemental").

⚠️ **Cerveau séparé** : `cursus_bebe.py` charge/sauvegarde un fichier dédié
`brains/naulthene_bb.brain` — distinct à la fois de `brains/naulthene_v21.brain` (Cuve) et de
`brains/naulthene_cursus.brain` (Cursus par Ères). Les trois écosystèmes ne partagent jamais le
même cerveau ; ne lance pas le daemon (Terminal 1) en même temps, ce n'est pas nécessaire pour
ce mode.

✅ **Persistance automatique**, même garantie que le Cursus par Ères (§6) : sauvegarde après
CHAQUE nuit (donc chaque jour subjectif) dans `brains/naulthene_bb.brain`. Relancer la même
commande **reprend** le cursus là où il en était — `--jours N` ajoute N jours SUPPLÉMENTAIRES à
partir de l'état repris, ce n'est pas une valeur absolue. Premier lancement : naissance d'un
cerveau neuf (bus=16), aucun fichier trouvé.

**Un seul terminal**, pas de Cuve à lancer :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src python3 -m naulthene.salles_de_classe.cursus_bebe --jours 300
```

- `--jours N` : nombre de jours subjectifs à ajouter à partir de l'état repris (défaut
  `JOURS_TOTAUX_BEBE` = 1440, un run complet).
- `--no-wandb` : désactive le logging Weights & Biases (actif par défaut). Sans clé W&B
  configurée ou hors ligne, ajoute `WANDB_MODE=offline` avant la commande.

### Repartir d'un cerveau neuf (sans perdre l'ancien)

`cursus_bebe.py` n'a pas de flag `--brain` ni `--reset` — le chemin `brains/naulthene_bb.brain`
est fixe (`FICHIER_BRAIN_BEBE`). Pour faire naître un cerveau neuf plutôt que de reprendre
celui qui existe, **archive l'ancien fichier au lieu de le supprimer** (il représente des jours
de run, potentiellement précieux) :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
mv brains/naulthene_bb.brain brains/naulthene_bb_archive_$(date +%Y%m%d).brain

source venv/bin/activate
PYTHONPATH=src python3 -m naulthene.salles_de_classe.cursus_bebe --jours 300
```

Comme aucun fichier n'existe plus à `brains/naulthene_bb.brain`, `charger_ou_naitre()`
(`persistance.py`) affiche `🐣 Naissance d'un nouveau cerveau (Bus=16)` au lieu de `🧬
Résurrection du cerveau existant` — bus=16, tick_absolu=0, dopamine neutre, aucun souvenir.
L'ancien cerveau archivé reste utilisable normalement, y compris avec l'Arène (§7,
`--brain brains/naulthene_bb_archive_YYYYMMDD.brain`).

Au démarrage, le script ressuscite le cerveau existant (`🧬 Résurrection du cerveau existant`)
ou en fait naître un nouveau, préchauffe les références vocales (`say` → MFCC, une seule fois),
puis enchaîne les journées. Chaque nuit affiche le bilan habituel (État Mental, Plasticité,
Portes franchies, Quêtes Auto, Consolidations/rêve, Potentiomètre de patience, État Viscéral,
Métabolisme, Mémoire Épisodique, Erreur JEPA/Thermostat).

`Ctrl+C` interrompt le script proprement à tout moment — sauvegarde d'urgence automatique de la
journée déjà consolidée (seule la journée EN COURS au moment du Ctrl+C est perdue, jamais les
précédentes). Relance simplement la même commande pour reprendre.

### ⚠️ Cristallisation Souple (v26.0-experimental) active sur ce cerveau

Depuis v26.0, `NaultheneLinearSynaptique.cycle_sommeil()` (dans `noyau.py`, non versionné —
voir `CLAUDE.md`, section "Variante Locale de Test") protège de l'érosion nocturne les synapses
sollicitées fortement et régulièrement sur plusieurs nuits (`myeline_cumul`, cliquet
`cristallisee`, falaise sigmoïde `K_RAIDEUR_CRISTAL` — voir `docs/explications_readme.md` §8.5
pour le détail algorithmique). Cette mécanique est **transparente en usage normal** — aucune
nouvelle option de ligne de commande, elle s'applique automatiquement à chaque `cycle_sommeil`
sur un cerveau `naulthene_bb.brain` existant comme sur un cerveau neuf, sans distinction dans
les logs console actuels (pas encore de métrique W&B dédiée au nombre de synapses cristallisées
— à ajouter si un futur diagnostic de run en a besoin).

⚠️ **Sur un `.brain` déjà entraîné avant ce correctif** (comme un run repris depuis v25.0/avant
la Cristallisation Souple), le premier chargement peut afficher `🌱 Hémisphères nouvellement
greffés sur ce cerveau` pour toutes les couches — normal et attendu **une seule fois** : les
deux nouveaux buffers (`myeline_cumul`, `cristallisee`) sont absents de l'ancien `state_dict`
(`load_state_dict(..., strict=False)`, voir `persistance.py`), donc chaque couche est listée en
greffe même si seuls ces deux buffers sont réellement neufs — les poids `base_weight`/
`annexe_weight` déjà appris restent, eux, intacts. Si le message réapparaît à *chaque*
lancement (pas seulement le premier après la mise à jour), voir la ligne "Message Hémisphères
nouvellement greffés" du tableau de dépannage en fin de document.

---

## 6ter. Le Cursus de la Parole (autonome, 900 jours, v27.0-expérimental)

Comme les deux cursus précédents (§6, §6bis), ce mode ne passe **pas** par `daemon_cerveau.py`
— c'est un script **standalone** (`src/naulthene/salles_de_classe/cursus_parole.py`) qui pilote
directement un cerveau à travers **900 jours subjectifs × 800 ticks**, découpés en 3 phases
pédagogiques (voir `readme.md`, section "Nouveautés v27.0 — L'École de la Parole & Synesthésie") :

| Phase | Jours | Nom | Ce qui change |
|-------|-------|-----|----------------|
| 0 | 1–299 | Imprégnation totale | Le professeur nomme systématiquement le mot du curriculum, matin et après-midi (guidage 100%) — corrige même quand l'agent a bon |
| 1 | 300–599 | Autonomie guidée | Matin : synesthésie (mot lu dans la case devant l'agent) ; après-midi : curriculum. Guidage décroît de 100% vers ~40% |
| 2 | 600–899 | Émancipation | Synesthésie + syntagmes couleur+objet toute la journée. Guidage ~40% → 10% |

⚠️ **Prérequis pour la synesthésie** : les phases 1-2 ont besoin que l'agent BOUGE réellement
dans MiniGrid pour que la case devant lui change (voir `noyau.LecteurCaseFrontale`) — c'est pour
ça que le matin des phases 1-2 est en mode `"minigrid"`, jamais `"vocal_isole"`.

⚠️ **Cerveau séparé** : `cursus_parole.py` charge/sauvegarde un fichier dédié
`brains/naulthene_parole.brain` — distinct des trois autres écosystèmes (`naulthene_v21.brain`
Cuve, `naulthene_cursus.brain` Cursus par Ères, `naulthene_bb.brain` Cerveau Bébé). Les quatre
ne partagent jamais le même cerveau.

✅ **Persistance automatique**, même garantie que les cursus précédents : sauvegarde après
CHAQUE nuit. `--jours N` ajoute N jours SUPPLÉMENTAIRES à partir de l'état repris.

**Un seul terminal**, pas de Cuve à lancer :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_parole --jours 900
```

**Recommandé pour un premier essai** (valider que tout tourne avant de lancer les 900 jours) :

```bash
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_parole --jours 3 --no-wandb
```

Au démarrage, le script préchauffe les références vocales (banque disque `voix/` en priorité,
repli `say` sinon — voir §0bis) et affiche un résumé (`N mot(s) depuis la banque, M depuis say`)
puis enchaîne les journées. Chaque journée affiche le bilan de nuit habituel, plus
`🎓 [PROMOTION VOCALE]` quand le palier vocal progresse. Un changement de phase est signalé par
`🗣️ [NOUVELLE PHASE]` (jour 300 → Autonomie guidée, jour 600 → Émancipation).

`Ctrl+C` interrompt le script proprement à tout moment (même garde-fous que §6/§6bis).

---

## 7. L'Arène & Démo Live (observer un cerveau entraîné, sans jamais l'altérer)

Une fenêtre graphique qui affiche MiniGrid en direct (l'agent qui se déplace) + un panneau de
télémétrie + une bande mini-IRM, dans une seule fenêtre, avec le babil de l'agent joué en temps
réel dans les haut-parleurs.

✨ **Panneau de télémétrie complet (v26.0-experimental)** : parité avec le bilan de nuit console
(État Mental, Plasticité, Progrès Jalon/Abnégation, Mode Décision, Portes, Potentiomètre,
Curiosité JEPA, État Viscéral, Métabolisme, Mémoire Épisodique, Erreur JEPA/Thermostat) — la
plupart de ces valeurs sont recalculées EN CONTINU à chaque tick (identiques à ce que lirait un
vrai bilan de nuit au même instant). Trois d'entre elles (Plasticité base, souvenirs
rejoués/rêve, thermostat de neurogenèse) n'existent QUE après un vrai `executer_nuit` — l'Arène
n'endort jamais le cerveau qu'elle observe, donc ces trois lignes affichent un **proxy estimé**
(même formule, recalculée sans attendre la nuit), toujours marqué "≈" ou "(estimé)" pour ne
jamais laisser croire à un vrai bilan nocturne. Un bandeau temporaire signale un changement de
palier DoorKey observé en direct.

⚠️ **La promotion de NIVEAU MiniGrid (changement de carte, ex. Primaire→Collège) ne peut PAS
s'observer dans l'Arène** — elle est décidée uniquement pendant une vraie nuit (`executer_nuit`),
jamais appelée ici par garantie de non-altération. Une note l'explique au démarrage. Pour voir
une promotion de niveau, relance le Cursus (section 6/6bis) ou la Cuve (section 1-4).

✨ **Mini-IRM en direct (v26.0-experimental)** : une bande sous l'image MiniGrid affiche les
activations du bus latent à 3 étapes du tronc cérébral (vision/mémoire/pensée, une couleur par
série) — recalculées tick par tick sur le MÊME cerveau que celui qui joue dans MiniGrid, en
pygame pur (pas de fenêtre matplotlib séparée, qui serait fragile à faire cohabiter avec pygame
sur macOS). Pour un diagnostic plus poussé (heatmap de myélinisation, courbe de variance),
utiliser `irm_cerveau.py` séparément (voir sa propre commande de lancement dans
[Architecture](../CLAUDE.md#architecture)).

⚠️ **Prérequis** : il faut un `.brain` à observer — lance d'abord le Cursus (section 6) pendant
au moins une nuit pour produire `brains/naulthene_cursus.brain`, ou utilise directement le
cerveau de la Cuve avec `--brain brains/naulthene_v21.brain`.

✅ **Garantie de non-altération, validée par test** : l'Arène observe uniquement — `agent.eval()`
et aucun apprentissage ne se produit jamais pendant la démo (confirmé par comparaison directe des
poids avant/après un run d'observation, strictement identiques). Tu peux lancer l'Arène autant de
fois que tu veux, elle ne modifiera jamais le `.brain` qu'elle observe.

**Un seul terminal**, pas de Cuve à lancer :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src python -m naulthene.instruments.lancer_arene
```

- `--brain <fichier>` : quel cerveau observer (défaut `brains/naulthene_cursus.brain`, celui du
  Cursus). Exemple pour voir plutôt le cerveau de la Cuve :
  `PYTHONPATH=src python -m naulthene.instruments.lancer_arene --brain brains/naulthene_v21.brain`.

Pour fermer : `Ctrl+C` dans le terminal, ou clic sur la croix de la fenêtre — les deux sont gérés
proprement (fermeture de la fenêtre pygame + de l'environnement MiniGrid, sans traceback).

---

## 8. Le Port Exocortex C3 (v28.0-expérimental) — tester un cerveau neuf avec/sans plug

Le Port Exocortex (`src/naulthene/exocortex/`) ajoute un canal optionnel au-dessus du Cœur
Organique [C1+C2] existant : une 8ème action apprise, `ACTION_DEMANDER`, que l'agent peut jouer
pour "tendre la main" vers un greffon externe (`PlugC3`) enregistré sur `etat.agent.port_c3`. Il
n'existe **pas encore de flag CLI** dans les cursus pour enregistrer un plug (aucun
`--brain`/`--jours` n'expose ce réglage) — le plus simple est un court script Python, comme
ci-dessous. Toute cette section est facultative : sans rien faire, tous les modes des sections
1-7 se comportent exactement comme avant la v28.0.

### 8a. Faire naître un nouveau cerveau à 8 actions (aucun plug — comportement inchangé)

C'est le test le plus important à faire en premier : vérifier que la naissance et quelques
ticks se déroulent normalement, sans plug branché.

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src WANDB_MODE=disabled python3 -c "
import naulthene.cerveau.noyau as noyau

etat = noyau.initialiser_etat_cognitif()   # naissance d'un cerveau neuf (bus=16, 8 actions)
noyau.demarrer_journee(etat)

actions = set()
for _ in range(300):
    infos = noyau.traiter_tick(etat)
    actions.add(infos['action'])

print('Actions jouées sur 300 ticks :', sorted(actions))
print('ACTION_DEMANDER (7) jamais jouée sans plug ?', noyau.ACTION_DEMANDER not in actions)
"
```

Attendu : `Actions jouées sur 300 ticks : [0, 1, 2, 3, 4, 5, 6]` — jamais de `7`. C'est
l'invariant non négociable de cette version (voir `CLAUDE.md`).

### 8b. Créer un nouveau cerveau ET le persister (`brains/naulthene_c3_test.brain`)

Pour obtenir un vrai fichier `.brain` réutilisable ensuite avec l'Arène (§7) ou un cursus :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src WANDB_MODE=disabled python3 -c "
import naulthene.cerveau.noyau as noyau
from naulthene.cerveau.persistance import PersistanceAnatomique

persistance = PersistanceAnatomique(fichier='brains/naulthene_c3_test.brain')
etat = persistance.charger_ou_naitre()   # 🐣 Naissance (première fois) ou 🧬 Résurrection
noyau.demarrer_journee(etat)

for _ in range(200):
    noyau.traiter_tick(etat)

persistance.sauvegarder(etat)   # 💾 écrit brains/naulthene_c3_test.brain
print('num_actions:', etat.agent.num_actions, '| dim_bus:', etat.agent.dim_bus)
"
```

Relancer la même commande **reprend** ce cerveau (comme les cursus §6) plutôt que d'en refaire
naître un — même logique que `--jours N` ajoutant des jours supplémentaires. Supprimer
`brains/naulthene_c3_test.brain` avant de relancer si tu veux repartir d'un cerveau vierge.

### 8c. Brancher un plug de test (`PlugSimule`) et vérifier que l'action existe

`PlugSimule` (dans `naulthene.exocortex.plugs.plug_simule`) répond de façon déterministe, sans
appel réseau — c'est l'outil de test du Port Exocortex, pas un vrai greffon. Pour observer
`ACTION_DEMANDER` réellement choisie, il faut biaiser artificiellement la tête motrice (un agent
neuf, jamais entraîné, ne choisira presque jamais une action à peine plus probable que les 7
autres) :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src WANDB_MODE=disabled python3 -c "
import torch
import numpy as np
import naulthene.cerveau.noyau as noyau
from naulthene.exocortex.plugs.plug_simule import PlugSimule

etat = noyau.initialiser_etat_cognitif()
noyau.demarrer_journee(etat)

# Biais artificiel réservé au TEST — un cerveau entraîné apprendrait ce choix lui-même
with torch.no_grad():
    etat.agent.tete_motrice.base_weight[noyau.ACTION_DEMANDER, :] += 50.0

plug = PlugSimule(preferences_fixes=np.array([1,0,0,0,0,0,0,0], dtype=np.float32), confiance=0.3)
etat.agent.port_c3.enregistrer(plug)

for _ in range(50):
    infos = noyau.traiter_tick(etat)

print('requêtes envoyées :', etat.requetes_c3_jour)
print('réponses reçues   :', etat.reponses_c3_jour)
print('dopamine C3 jour  :', etat.dopamine_poids_c3_jour)
"
```

Attendu : `requêtes envoyées` et `réponses reçues` égaux (le plug répond toujours), la ligne
`🖐️` n'apparaît pas ici (elle ne s'affiche qu'au **chargement** d'un vieux `.brain` à 7 actions,
voir 8d) — c'est un cerveau neuf, déjà à 8 actions dès la naissance.

### 8d. Test de crash (déconnexion en vol) — vérifier qu'aucune panne ne remonte

```bash
PYTHONPATH=src WANDB_MODE=disabled python3 -c "
import torch
import naulthene.cerveau.noyau as noyau
from naulthene.exocortex.plugs.plug_simule import PlugSimule

etat = noyau.initialiser_etat_cognitif()
noyau.demarrer_journee(etat)
with torch.no_grad():
    etat.agent.tete_motrice.base_weight[noyau.ACTION_DEMANDER, :] += 50.0

plug = PlugSimule()
etat.agent.port_c3.enregistrer(plug)

for t in range(60):
    if t == 20:
        plug.panne = True     # simule un service qui tombe en marche
        print('--- panne simulée ---')
    infos = noyau.traiter_tick(etat)   # ne doit JAMAIS lever d'exception

print('OK — aucune exception, le plug est passé en cooldown automatiquement')
"
```

### 8e. Recharger un `.brain` pré-v28.0 (7 actions) — vérifier la greffe automatique

Si tu as un ancien `.brain` créé avant cette version (7 actions), le charger avec
`PersistanceAnatomique.charger_ou_naitre()` déclenche automatiquement la greffe par recopie
(`_greffer_action_supplementaire`, voir `docs/CHANGELOG.md` v28.0) — **jamais besoin d'y
toucher manuellement**. Le message `🖐️  <couche> greffé(e) de 7 à 8 actions` s'affiche une seule
fois, au premier chargement ; les acquis existants (7 actions) sont préservés au bit près, la
8ème naît vierge. Pour vérifier sur une COPIE d'un cerveau existant (ne jamais tester sur
l'original directement) :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
cp brains/naulthene_parole.brain /tmp/naulthene_parole_test.brain
source venv/bin/activate
PYTHONPATH=src WANDB_MODE=disabled python3 -c "
from naulthene.cerveau.persistance import PersistanceAnatomique
persistance = PersistanceAnatomique(fichier='/tmp/naulthene_parole_test.brain')
etat = persistance.charger_ou_naitre()
print('num_actions après greffe :', etat.agent.num_actions)
"
rm /tmp/naulthene_parole_test.brain
```

⚠️ Ce test **charge en lecture**, il n'écrit rien tant que `sauvegarder()` n'est pas appelé —
mais travailler sur une copie évite tout risque si un script de test futur ajoute une sauvegarde
par erreur.

---

## 9. Le Bus Sensoriel — les 5 sens (v29.0-expérimental)

Le Bus Sensoriel (`src/naulthene/cerveau/bus_sensoriel.py`) donne à l'agent les **trois sens qui
lui manquaient** — toucher, odorat, goût — en plus de la vue et de l'ouïe qu'il avait déjà.

✅ **Aucune action requise de ta part.** Contrairement au Port Exocortex (§8, qui demande
d'enregistrer un plug à la main), le Bus Sensoriel est **actif automatiquement** dans tous les
modes des sections 1-7 : la Cuve, les trois cursus et l'Arène en bénéficient sans aucun flag ni
réglage. Cette section sert uniquement à **observer** ce que l'agent sent, et à comprendre le
message de greffe au premier chargement d'un ancien `.brain`.

### 9a. Voir ce que l'agent sent, en direct

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src WANDB_MODE=disabled python3 -c "
import naulthene.cerveau.noyau as noyau

etat = noyau.initialiser_etat_cognitif()
noyau.demarrer_journee(etat)

for t in range(200):
    noyau.traiter_tick(etat)
    if t % 50 == 0:
        s = etat.bus_sensoriel.interpreter(etat.env)
        print(f'tick {t:3d} | contact={s[0]:.0f} main={s[1]:.0f} '
              f'orient=({s[2]:+.2f},{s[3]:+.2f}) | '
              f'odorat food={s[4]:.2f} eau={s[5]:.2f} | '
              f'gout food={s[6]:.2f} eau={s[7]:.2f}')
"
```

Comment lire la sortie :

| Champ | Signification |
|-------|---------------|
| `contact` | 1 = l'agent est au contact d'un mur ou d'une porte fermée devant lui, 0 = la voie est libre |
| `main` | 1 = l'agent porte un objet (la clé, typiquement), 0 = mains vides |
| `orient` | Orientation encodée sur le cercle (cos, sin) — évite la fausse discontinuité entre les directions 3 et 0 |
| `odorat` | Depuis la v30.0, **atténuation exponentielle** `exp(-0.8 × distance)` : 1.00 au contact, 0.45 à 1 case, 0.20 à 2 cases, coupé à 0.00 au-delà de ~5 cases (voir §10d) |
| `gout` | 1.00 juste après une bouchée, puis décroît (~10 ticks) jusqu'à 0 |

### 9b. Vérifier la hiérarchie des 5 sens

```bash
PYTHONPATH=src python3 -c "
from naulthene.cerveau.bus_sensoriel import BusSensoriel
for sens, info in BusSensoriel.hierarchie_sensorielle().items():
    print(f\"{sens:8s} | {info['gourmandise']:8s} | {info['dims']:3d} dims | \"
          f\"JEPA={info['jepa']} | {info['chemin']}\")
"
```

Attendu :

```
vue      | extreme  | 147 dims | JEPA=True  | porte_visuelle → bus_latent
ouie     | elevee   | 130 dims | JEPA=True  | porte_auditive → bus_latent
toucher  | moyenne  |   4 dims | JEPA=False | vecteur_bio → integrateur_bio
odorat   | faible   |   2 dims | JEPA=False | vecteur_bio → integrateur_bio
gout     | faible   |   2 dims | JEPA=False | vecteur_bio → integrateur_bio
```

`JEPA=False` sur les trois sens faibles est **voulu** : ils entrent par `integrateur_bio`, juste
avant la décision, donc ils n'entrent **jamais** dans ce que le modèle du monde doit prédire. Un
cerveau déjà entraîné sur des centaines de jours ne voit donc pas sa physique visuelle perturbée
(voir `docs/EXPLICATIONS_v29_sens.md` §4).

### 9c. Recharger un `.brain` pré-v29.0 — vérifier la greffe automatique

Le vecteur viscéral passe de 16 à 24 dims, ce qui change la forme de `integrateur_bio`. La
greffe est **automatique** (`_greffer_vecteur_bio_etendu`) et **préserve tous les acquis** —
contrairement à l'ancien comportement, qui excluait la couche et la faisait renaître à neuf. Pour
vérifier sur une **copie** (ne jamais tester sur l'original) :

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
cp brains/naulthene_parole.brain /tmp/naulthene_v29_test.brain
source venv/bin/activate
PYTHONPATH=src WANDB_MODE=disabled python3 -c "
from naulthene.cerveau.persistance import PersistanceAnatomique
from naulthene.cerveau.noyau import DIM_VECTEUR_BIO

p = PersistanceAnatomique(fichier='/tmp/naulthene_v29_test.brain')
etat = p.charger_ou_naitre()
forme = tuple(etat.agent.integrateur_bio.base_weight.shape)
print('DIM_VECTEUR_BIO :', DIM_VECTEUR_BIO)
print('integrateur_bio :', forme, '| attendu :', (etat.agent.dim_bus, etat.agent.dim_bus + DIM_VECTEUR_BIO))
print('dim_bus:', etat.agent.dim_bus, '| tick_absolu:', etat.tick_absolu)
"
rm /tmp/naulthene_v29_test.brain
```

Attendu : le message `👃 integrateur_bio greffé de N à M dims d'entrée (+8 :
toucher/odorat/goût, Bus Sensoriel v29.0) — acquis existants préservés.`, puis une forme égale à
`(dim_bus, dim_bus + 24)`. Le `tick_absolu` doit être **celui de l'ancien cerveau**, preuve que
la résurrection a bien eu lieu et qu'aucun acquis n'a été perdu.

⚠️ Ce test **charge en lecture** — il n'écrit rien tant que `sauvegarder()` n'est pas appelé. La
copie reste néanmoins la bonne pratique.

### 9bis. Suivre les 5 sens jour après jour (v29.1)

Depuis la v29.1, **chaque nuit affiche une ligne dédiée aux sens**, dans tous les modes (Cuve,
les 3 cursus) — rien à activer :

```
  ├─ Les 5 Sens     : ✋ Contact 28.5% | 🔑 Portage 20.5% | 👃 Odorat 96.0% des ticks (max 1.50) | 👅 Goût 75 tick(s)
```

| Champ | Lecture |
|-------|---------|
| `Contact` | % de ticks passés au contact d'un obstacle — un chiffre très haut durablement = agent qui se cogne / reste bloqué |
| `Portage` | % de ticks avec un objet en main. **Sur DoorKey, c'est le temps passé à porter la clé** — monte quand l'agent maîtrise les paliers 3-4 |
| `Odorat` | % de ticks avec une odeur perçue (voir l'avertissement de saturation ci-dessous) |
| `Goût` | Nombre de ticks avec une rémanence gustative — à rapprocher des Nourriture(s)/Eau(x) de la ligne Métabolisme |

Le suffixe **`⚠️ BUS DÉSACTIVÉ`** apparaît si le Bus Sensoriel est tombé en vol. C'est l'alerte à
surveiller : sans elle, la dégradation gracieuse ne laisse qu'un unique message au moment de la
panne, vite noyé dans les logs d'un run long.

Côté **W&B**, 7 métriques `Sens_*` sont loggées chaque nuit (`Sens_Bus_Actif`,
`Sens_Toucher_Contact_Ratio`, `Sens_Toucher_Portage_Ratio`, `Sens_Odorat_Moyen`,
`Sens_Odorat_Max`, `Sens_Odorat_Ticks_Actifs_Ratio`, `Sens_Gout_Ticks_Actifs`). Elles sont
**absentes** du log en mode `vocal_isole` pur (aucun environnement MiniGrid lu) — c'est normal.

> ⚠️ **Ce pourcentage mesure la PRÉSENCE d'une trace, pas son intensité.** Depuis la v30.0
> (atténuation exponentielle, voir §10d), il peut rester élevé alors même que le signal est devenu
> bien plus discriminant : le seuil de coupure est bas, donc une odeur très faible compte encore
> comme « active ». Ce qu'il faut regarder, c'est `Sens_Odorat_Moyen` dans W&B — passé de ~0.54
> (v29, rampe linéaire) à ~0.32 sur un run réel `Empty-8x8`, avec l'odeur forte (> 0.45) réduite
> à ~30 % des ticks au lieu d'être permanente. Un `Odorat` à **0 %** en revanche, sur un niveau où
> des ressources existent, mérite investigation.

### 9d. Ce que la v29.0 ne change PAS

- **Aucune régression de comportement** : le découpage C1/C2 (`_executer_c1_reflexe` /
  `_solliciter_c2_neocortex`) est une **restructuration pure** — C2 est toujours sollicité à
  chaque tick, l'arbitrage est inchangé depuis la v13.0.
- **L'invariant du Port Exocortex (§8) reste intact** : sans plug enregistré, `ACTION_DEMANDER`
  est toujours masquée à `-inf` et n'est jamais jouée.
- **Aucune nouvelle dépendance** à installer (le Bus Sensoriel est du numpy pur).

---

## 10. L'Exo-Sens — le 6ᵉ sens (v30.0-expérimental)

Depuis la v30.0, l'Exocortex C3 n'est plus un « 3ᵉ cerveau » que l'agent interroge par une action :
c'est un **6ᵉ sens**, perçu **en continu** comme le toucher ou l'odorat. L'agent ne décide jamais
de « demander » — il sent le monde numérique en permanence, et c'est son cerveau qui apprend seul
(par myélinisation de `integrateur_bio`) quelle attention y accorder.

✅ **Neutre par défaut.** Sans plug branché — le cas de **tous** les modes des sections 1-7 — le
vecteur exogène est nul et le comportement est strictement celui de la v29.1. Aucune ligne
« Exo-Sens » n'apparaît au bilan de nuit, aucune clé `Sens_Exo_*` n'est loggée.

### 10a. Brancher un plug perceptif local et observer le 6ᵉ sens

`PlugMemoireAugmentee` est 100 % local et déterministe (aucun réseau) : il traduit un résumé de la
mémoire épisodique de l'agent en 8 dims perçues. C'est le plug de validation à essayer en premier.

```bash
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
PYTHONPATH=src WANDB_MODE=disabled python3 -c "
import naulthene.cerveau.noyau as noyau
from naulthene.exocortex.plugs.plug_memoire_augmentee import (
    PlugMemoireAugmentee, source_depuis_memoire_spatiale)

etat = noyau.initialiser_etat_cognitif()
etat.agent.port_c3.enregistrer(
    PlugMemoireAugmentee(source=source_depuis_memoire_spatiale(etat)))
noyau.demarrer_journee(etat)

for _ in range(400):
    noyau.traiter_tick(etat)

s = etat.bus_sensoriel.interpreter(etat.env, reponse_c3=etat.perception_exogene_cache)
print('Z_exogene (8 dims) :', [round(v, 3) for v in s[8:]])
log = noyau.executer_nuit(etat)
for k in sorted(k for k in log if k.startswith('Sens_Exo')):
    print(f'  {k} = {log[k]}')
"
```

Attendu : une ligne `├─ Exo-Sens (C3) : 🔌 Perçu ...% des ticks` au bilan de nuit, et
**~20 rafraîchissements pour 400 ticks** — le bus n'est interrogé qu'un tick sur
`PERIODE_PERCEPTION_EXO=20`, la perception étant mise en cache entre deux appels.

### 10b. Pourquoi ce cache ? (la latence)

Un plug HTTP réel (Ollama, RAG, API) coûte de **100 ms à 30 s** par appel. L'interroger à chaque
tick rendrait un run de 300 jours × 400 ticks totalement impraticable. Le rafraîchissement
périodique est une **fréquence d'échantillonnage de capteur**, pas une règle cognitive : le cerveau,
lui, perçoit bien quelque chose à chaque tick.

### 10c. Brancher un vrai backend (Ollama, RAG, API IA)

Aucun code du noyau n'est à toucher : `PlugHTTP` (livré en v28.0) est un backend générique
JSON/HTTP. Un service doit simplement renvoyer un vecteur de 8 valeurs dans `[0, 1]` que le plug
place dans `ReponseC3.perception`. Les deux familles de plugs coexistent — un plug **perceptif**
(v30, champ `perception`) et un plug **décisionnel** (v28, champ `preferences`) peuvent être
branchés simultanément sur le même bus.

⚠️ **Le vecteur est clippé dans [0, 1] côté noyau** et un vecteur de mauvaise taille est ignoré
(perception neutre + un avertissement unique). Un service externe n'est jamais supposé fiable :
une dimension hors échelle écraserait `integrateur_bio`, et un plug défaillant **ne doit jamais**
rendre l'agent aveugle à ses 5 sens physiques.

### 10d. L'odorat a changé de forme (v30.0)

L'odorat suit désormais une **atténuation exponentielle** `exp(-0.8 × distance)` au lieu d'une
rampe linéaire : 1.00 au contact, 0.45 à une case, 0.20 à deux, négligeable au-delà. Concrètement,
sur un run réel `Empty-8x8`, l'odeur forte (> 0.45) ne survient plus que ~30 % du temps au lieu
d'être quasi permanente — le sens redevient une **boussole de proximité**. Le pourcentage brut
affiché au bilan (`👃 Odorat ...%`) peut rester élevé (le seuil de coupure est bas) : c'est
l'**intensité** qui compte désormais, pas la simple présence d'une trace.

---

## 11. Lire les métriques de calibrage (v30.1) — mémoire & sursaut

Deux constantes du projet sont encore arbitraires : `capacite_max = 200` (mémoire épisodique) et
`EXTENSION_PATIENCE_SURSAUT = 50` (Sursaut de Volonté). La v30.1 ne les change pas — elle les rend
**mesurables**, pour pouvoir les rendre adaptatives ensuite **sur données réelles** plutôt qu'à
l'intuition.

### 11a. La mémoire épisodique est-elle limitée par sa capacité ?

Le bilan de nuit affiche désormais :

```
├─ Mémoire Épiso. : 🗺️ 200/200 souvenir(s) spatial(aux) ⚠️ SATURÉE — rappel 65% des tentatives (proximité moy 0.27)
```

| Ce que tu observes | Interprétation |
|---|---|
| `⚠️ SATURÉE` **et** proximité qui **baisse** dans le temps | La capacité limite vraiment → une capacité adaptative aurait du sens |
| `⚠️ SATURÉE` mais proximité **stable/haute** | La FIFO jette des souvenirs **inutiles** → augmenter la capacité ne servirait à rien |
| Jamais saturée | La question ne se pose pas sur ce parcours |
| `Memoire_Age_Plus_Vieux_Souvenir` qui **s'effondre** | La mémoire ne remonte plus assez loin dans le temps → vrai signal de sous-capacité |

Courbes W&B : `Memoire_Taux_Saturation`, `Memoire_Taux_Rappel_Reussi`,
`Memoire_Proximite_Moyenne`, `Memoire_Fraicheur_Moyenne`, `Memoire_Age_Plus_Vieux_Souvenir`.

> À croiser impérativement : `Memoire_Taux_Saturation` **seul** ne prouve rien. Une mémoire pleine
> dont le rappel reste excellent est une mémoire **bien dimensionnée**, pas une mémoire saturée.

### 11b. Le Sursaut de Volonté sert-il à quelque chose ?

```
├─ Potentiomètre  : ⏳ Patience ... (2 abandon(s) lucide(s), 10 Sursaut(s) → 30% de victoires, ...)
```

C'est **la métrique décisive** pour trancher le sens d'une extension adaptative :

| `Sursaut_Taux_Victoire` | Lecture | Direction suggérée |
|---|---|---|
| Élevé (> ~40 %) | Le sursaut sauve réellement des épisodes | **« Muscle »** — le renforcer quand il réussit |
| Faible (< ~15 %) | Il ne fait que retarder un échec | **« Habituation »** — l'atténuer, voire le réserver |
| Intermédiaire | Dépend du niveau/palier | Croiser avec `Palier_Cible` et `Mode_Libre` |

⚠️ Ces métriques n'apparaissent qu'en **Mode Libre** (palier DoorKey ≥ 5), seul contexte où le
Sursaut est actif. Sur un run encore en Primaire/paliers bas, elles seront simplement absentes —
c'est normal, pas une panne.

### 11c. Ce que la v30.1 ne fait PAS

Aucune formule adaptative n'est écrite. `capacite_max` vaut toujours 200, l'extension de sursaut
toujours 50 ticks. **Le comportement de l'agent est strictement inchangé** — vérifié par empreinte
de la séquence d'actions à graine fixée, identique avant/après. Cette version ne fait que rendre
observable ce qui devra être calibré.

---

## Dépannage rapide

| Symptôme | Cause probable |
|----------|-----------------|
| `ConnectionRefusedError` côté client | La Cuve (Terminal 1) n'est pas lancée ou a crashé |
| Le score vocal reste figé | Normal sous 400 ticks — voir §3 ci-dessus |
| Jugement Gemma très lent (~30s) | Normal — `gemma4:e4b` est un modèle à raisonnement, mesuré à 8-30s/réponse |
| Rien ne se passe après `--micro` | Vérifie l'autorisation micro macOS (Réglages Système → Confidentialité → Micro → Terminal) |
| Message "Hémisphères nouvellement greffés" à chaque lancement | Anormal après le premier run réussi — vérifie que la Cuve sauvegarde bien avant l'arrêt (pas de `kill -9`) |
| Le cursus (§6) ne partage pas mes acquis MiniGrid de la Cuve | Normal et voulu — `brains/naulthene_cursus.brain` (Cursus), `brains/naulthene_v21.brain` (Cuve), `brains/naulthene_bb.brain` (Cerveau Bébé) et `brains/naulthene_parole.brain` (Cursus de la Parole) sont quatre cerveaux séparés, jamais mélangés. Chaque cursus reprend bien SES PROPRES acquis d'un lancement à l'autre |
| `FileNotFoundError` au lancement de l'Arène (§7) | Aucun `brains/naulthene_cursus.brain` trouvé — lance d'abord le Cursus (§6) au moins une nuit, ou pointe `--brain` vers `brains/naulthene_v21.brain` |
| La fenêtre de l'Arène reste noire/vide | Vérifie que `pygame-ce` est bien installé (`pip list \| grep pygame`) ; regarde la console pour une éventuelle erreur de rendu |
| La cible F1/F2 reste théorique malgré des prises enregistrées (§0bis) | Vérifie le chemin `voix/<mot>/<mot>_NN.wav` (le mot doit correspondre EXACTEMENT à une cible de `professeur_gemma.CURRICULUM_VOCAL`, accents compris) — au préchauffage, `resume_banque()` affiche "N mot(s) depuis la banque" ; si N=0, aucune prise n'a été trouvée pour aucun mot du curriculum |
| Message `🖐️ <couche> greffé(e) de 7 à 8 actions` au chargement (§8e) | Normal et attendu **une seule fois** sur un `.brain` créé avant la v28.0 — la greffe préserve les 7 actions déjà apprises, la 8ème (`ACTION_DEMANDER`) naît vierge. Si le message réapparaît à CHAQUE lancement, vérifie que la sauvegarde qui suit s'est bien effectuée (pas de `kill -9` avant `💾 Cerveau cristallisé avec succès`) |
| `ACTION_DEMANDER` (action 7) n'est jamais jouée même avec un plug enregistré | Comportement normal sur un cerveau jamais entraîné à ce choix — voir §8c, il faut soit biaiser artificiellement `tete_motrice` pour un test, soit laisser un vrai run apprendre ce choix par lui-même (REINFORCE, pas un seuil codé en dur) |
| Message `👃 integrateur_bio greffé de N à M dims d'entrée` au chargement (§9c) | Normal et attendu **une seule fois** sur un `.brain` créé avant la v29.0 — le vecteur viscéral passe de 16 à 24 dims (toucher/odorat/goût). La greffe **préserve tous les acquis au bit près**, les 8 nouvelles dimensions naissent vierges. Si le message réapparaît à CHAQUE lancement, vérifie que la sauvegarde qui suit s'est bien effectuée (pas de `kill -9` avant `💾 Cerveau cristallisé avec succès`) |
| Message `🔄 integrateur_bio exclu du chargement` depuis la v29.0 | **Anormal** pour un simple passage 16→24 dims — ce cas est censé être pris en charge par la greffe (`👃`, ligne ci-dessus). L'exclusion ne subsiste qu'en trappe de secours pour un mismatch qu'on ne sait pas greffer (ex. `dim_bus` incohérent entre le `.brain` et l'agent recréé). Vérifie que le `.brain` n'a pas été produit par une autre architecture/branche |
| L'odorat reste à 0.00 en permanence (§9a) | Normal si aucune source n'est proche : depuis la v30.0 le signal suit `exp(-0.8 × distance)` et tombe sous le seuil de coupure au-delà de ~5 cases. Les ressources ne sont générées que par `DetecteurRessourcesBiologiques` (Ball rouge = Nourriture, Ball bleue = Eau) — sur un niveau sans ressource générée, 0.00 est le bon résultat |
| Le toucher renvoie toujours `0.0` sur les 4 dims | Le bus s'est désactivé — cherche l'avertissement `⚠️ Bus sensoriel (toucher/odorat/goût) désactivé (API minigrid incompatible : ...)` affiché **une seule fois** dans la console. Même dégradation gracieuse que les détecteurs génériques : l'entraînement continue normalement, seuls les 3 sens faibles sont neutres. Depuis la v29.1, le suffixe `⚠️ BUS DÉSACTIVÉ` s'affiche en plus à **chaque** bilan de nuit et `Sens_Bus_Actif` passe à 0 dans W&B |
| Ligne `Les 5 Sens` absente du bilan de nuit (v29.1) | Normal en mode `vocal_isole` pur (aucun environnement MiniGrid lu ce jour-là) : `ticks_sensoriels_jour = 0`, la ligne est volontairement masquée plutôt que d'afficher des ratios vides. Elle réapparaît dès qu'une journée comporte des ticks MiniGrid |
| `Odorat` proche de 96-100 % à chaque nuit | **Ce pourcentage compte la PRÉSENCE d'une trace, pas son intensité** — il peut rester haut alors que le signal est devenu discriminant (le seuil de coupure est bas). Depuis la v30.0, regarder `Sens_Odorat_Moyen` : ~0.32 sur `Empty-8x8` contre ~0.54 en v29, avec l'odeur forte (> 0.45) réduite à ~30 % des ticks. Voir §10d |
| `Portage` reste à 0 % sur DoorKey | L'agent n'a jamais ramassé la clé de la journée — cohérent avec un palier DoorKey encore bas (< 3, « Toucher / Prendre »). Cette métrique est un bon indicateur avancé de la maîtrise des paliers 3-4, avant même que la victoire n'arrive |
