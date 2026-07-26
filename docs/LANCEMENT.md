# Guide de Lancement — Naulthène AGI (Cuve Persistante + Hémisphère Audio + Cursus par Ères)

Ce guide couvre le lancement local (Mac) de l'écosystème V21/V22/V23 : le cerveau persistant
(`daemon_cerveau.py`, dans `src/naulthene/cuve/`) et ses deux clients (`client_corps.py` pour
MiniGrid, `client_professeur.py` pour les leçons de parole ponctuelles), ainsi que le Cursus
Développemental par Ères (`cursus_developpemental.py`, dans `src/naulthene/salles_de_classe/`,
un programme autonome de 1000 jours, voir §6). Voir `readme.md` pour l'architecture complète,
`CHANGELOG.md` pour l'historique des versions.

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

## 7. L'Arène & Démo Live (observer un cerveau entraîné, sans jamais l'altérer)

Une fenêtre graphique qui affiche MiniGrid en direct (l'agent qui se déplace) + un panneau de
télémétrie (dopamine, jauges biologiques, curriculum MiniGrid/DoorKey, ère et palier vocal) dans
une seule fenêtre, avec le babil de l'agent joué en temps réel dans les haut-parleurs.

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
| Le cursus (§6) ne partage pas mes acquis MiniGrid de la Cuve | Normal et voulu — `brains/naulthene_cursus.brain` (Cursus) et `brains/naulthene_v21.brain` (Cuve) sont deux cerveaux séparés, jamais mélangés (voir §6). Le cursus reprend bien SES PROPRES acquis d'un lancement à l'autre |
| `FileNotFoundError` au lancement de l'Arène (§7) | Aucun `brains/naulthene_cursus.brain` trouvé — lance d'abord le Cursus (§6) au moins une nuit, ou pointe `--brain` vers `brains/naulthene_v21.brain` |
| La fenêtre de l'Arène reste noire/vide | Vérifie que `pygame-ce` est bien installé (`pip list \| grep pygame`) ; regarde la console pour une éventuelle erreur de rendu |
