# Guide de Lancement — Naulthène AGI (Cuve Persistante + Hémisphère Audio + Cursus par Ères + Cerveau Bébé + Cursus de la Parole)

Ce guide couvre le lancement local (Mac) de l'écosystème V21-V27 : le cerveau persistant
(`daemon_cerveau.py`, dans `src/naulthene/cuve/`) et ses deux clients (`client_corps.py` pour
MiniGrid, `client_professeur.py` pour les leçons de parole ponctuelles), ainsi que trois cursus
développementaux autonomes (`src/naulthene/salles_de_classe/`) : le Cursus par Ères
(`cursus_developpemental.py`, 1000 jours, voir §6), le Cerveau Bébé (`cursus_bebe.py`, 1440
jours, voir §6bis) et le Cursus de la Parole (`cursus_parole.py`, 900 jours, v27.0-expérimental,
voir §6ter). Voir `readme.md` pour l'architecture complète, `CHANGELOG.md` pour l'historique
des versions.

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
  normal, une fois seulement (voir `CONCEPTION_v22_audio.md` §11 pour le détail).
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
