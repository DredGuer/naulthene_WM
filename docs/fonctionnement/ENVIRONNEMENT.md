# Spécification d'environnement — REP-01

> **Normatif.** Verrouille l'environnement d'exécution du projet (REP-01, livré à froid le
> 08/09/2026 ; clôture en attente de la vérification en environnement vierge, voir §6).
> Complète [`LANCEMENT.md`](LANCEMENT.md) (commandes) — celui-ci répond « comment lancer »,
> celui-là « dans quel monde ».

---

## 1. Python supporté

- **Python ≥ 3.12** (mesuré : **3.12.12** sur le venv de développement).
- macOS Apple Silicon : device `mps` (`torch.backends.mps.is_available()` = True, mesuré).
- Linux/GPU CUDA et CPU purs fonctionnent via la même détection `cuda`/`mps`/`cpu` de
  `noyau.py` — jamais de device supposé fixe.

## 2. Dépendances

Deux fichiers, deux rôles — **ne pas confondre** :

| Fichier | Rôle | Contenu |
|---|---|---|
| [`pyproject.toml`](../../pyproject.toml) | ce que le **code exige** | planchers larges (`numpy>=1.26`, `torch>=2.1`, `gymnasium>=1.0`, `minigrid>=3.0`, `wandb>=0.17`) + **extras** découpés par imports réels |
| [`constraints-lock.txt`](../../constraints-lock.txt) | le **monde mesuré** | `pip freeze` complet du venv de référence (66 paquets, versions `==`) — borne aussi les transitives |

### Extras (un module = un besoin, vérifié par imports le 08/09/2026)

| Extra | Paquet | Consommé par |
|---|---|---|
| *(cœur)* | numpy · torch · gymnasium · minigrid · wandb | `noyau.py`, cursus, persistance — toujours requis |
| `audio` | `sounddevice` | `hemisphere_audio.py` (micro) |
| `arene` | `pygame-ce` | `arene_visuelle.py`, `lancer_arene.py` |
| `irm` | `matplotlib` | `irm_cerveau.py` |
| `professeur` | `requests` | `professeur_gemma.py` (Ollama HTTP) |
| `plug-http` | `requests` | `exocortex/plugs/plug_http.py` |
| `baseline-ppo` | `stable-baselines3` | `banc_ppo*.py` |
| `visualisation` | `pygame-ce` + `matplotlib` | regroupement |
| `exocortex` | `requests` | regroupement |
| `tout` | tous | développement complet |

⚠️ Le lancement reste `PYTHONPATH=src python -m naulthene.…` depuis la racine du dépôt
(discipline CLAUDE.md §5/§10). `pyproject` **déclare**, il ne remplace pas ce mode de
lancement, et le dépôt n'est pas destiné à être `pip install`-é comme une bibliothèque.

## 3. Installation reproductible

```bash
python3.12 -m venv venv && source venv/bin/activate
# Monde exact de la campagne de référence (08/09/2026) :
pip install -c constraints-lock.txt -e .[tout]
# — ou monde minimal (cœur cognitif seul, ex. pour un banc CPU) :
pip install -c constraints-lock.txt -e .
# — ou extras choisis :
pip install -c constraints-lock.txt -e .[baseline-ppo]
```

Un environnement **vierge** doit passer la vérification REP-01 (§6) avant toute clôture.

## 4. Enregistrement d'environnement par campagne

Chaque campagne (dossier `brains/DDMMYYYY_<sujet>/`) consigne son environnement **dans son
`LISEZ_MOI.md`**, bloc ajouté au lancement :

```markdown
## Environnement (REP-01)
- Commit : <hash court> (git rev-parse --short HEAD)
- Python : 3.12.12 · device : mps (ou cuda/cpu)
- torch : <version> · gymnasium : <version> · minigrid : <version> · numpy : <version>
- Flags : la commande de lancement complète (déjà requise par la Règle de Trace)
```

⚠️ **Ne pas ajouter ces champs au `manifeste.json`** : le schéma MES-01 est strict — toute clé
inconnue fait échouer `depouillement.py` (vérifié : `clés inconnues dans le manifeste`).
L'environnement est une trace de campagne, pas une contrainte de dépouillement.

## 5. Quand et comment mettre à jour

- Une **borne** de `pyproject.toml` ne bouge que si le code l'exige (nouvel import, API
  rompue) — jamais « pour être à jour ».
- Le **lock** se régénère par mesure, jamais à la main :
  `venv/bin/pip freeze > constraints-lock.txt` après une mise à jour volontaire, avec entrée
  CHANGELOG et mention dans ce document.
- Toute campagne lancée sous un lock différent de celui-ci est signalée par l'écart entre
  son `LISEZ_MOI.md` (§4) et `constraints-lock.txt`.

## 6. Critères de clôture REP-01 (à exécuter après la campagne en cours)

### Outil presse-bouton : `scripts/verifier_environnement.sh`

Le script [`scripts/verifier_environnement.sh`](../../scripts/verifier_environnement.sh)
automatise toute la clôture : il crée un venv **vierge hors dépôt** (`/tmp/venv_rep01_validation`,
hors iCloud), installe depuis le lock, et exécute les trois vérifications. Il **refuse de
s'exécuter si un processus `noyau.py` tourne** (garde anti-contention).

```bash
bash scripts/verifier_environnement.sh            # venv par défaut /tmp/venv_rep01_validation
bash scripts/verifier_environnement.sh /tmp/venv_rep01_v2   # chemin explicite
```

Code de sortie : `0` = validation OK · `≠0` = échec (log détaillé à
`<venv>_validation.log`, freeze à `<venv>_freeze.txt`).

### Les quatre critères (ce que le script vérifie)

1. **Installation dans un environnement vierge** (nouveau venv hors dépôt, `pip install -c
   constraints-lock.txt -e '.[tout]'`).
2. **Import minimal** : `PYTHONPATH=src python -c "import naulthene.cerveau.noyau"` (CPU).
3. **Tests CPU** : `NAULTHENE_DEVICE=cpu venv/bin/python -m unittest discover -s tests`.
   ⚠️ Le script **ne fige aucun nombre** de tests (il a déjà annoncé « 44 » alors que le dépôt
   en comptait 156) : il lit ce que le log dit.
4. **Versions installées vs lock** : le script compare numpy/torch/gymnasium/minigrid/wandb
   au lock et signale tout écart.
5. Campagne suivante avec le bloc §4 rempli — sert de vérification de bout en bout.

### ✅ Validation exécutée le 12/09/2026 — REP-01 CLOS

`bash scripts/verifier_environnement.sh` → **code de sortie 0**, venv vierge
`/tmp/venv_rep01_validation` (Python 3.12.12), hors dépôt et hors iCloud :

| Critère | Résultat |
|---|---|
| Installation vierge (`-c constraints-lock.txt -e '.[tout]'`) | ✅ `Successfully installed` |
| Import minimal du cœur (CPU) | ✅ |
| Suite de tests CPU | ✅ **156 tests OK** (30,2 s) |
| Versions vs lock | ✅ numpy 2.4.6 · torch 2.13.0 · gymnasium 1.3.0 · minigrid 3.1.0 · wandb 0.28.1 — **toutes identiques au lock** |

🔴 **La validation a attrapé deux défauts réels de `pyproject.toml`** (que rien d'autre
n'aurait vus, puisque le dépôt se lance par `PYTHONPATH=src` et ne builde jamais) :
1. `project` sans champ `version` → setuptools refuse le build ;
2. un classifier `License ::` **incompatible avec l'expression SPDX** `license = "..."` (PEP 639).
Les deux sont corrigés dans le même commit.

⚠️ Le premier passage avait aussi masqué son code de sortie (pipe vers `tail`) : lancer le
script **sans pipe**, ou lire le fichier de log, pour voir l'échec.

⚠️ **Ne jamais exécuter le script pendant qu'une campagne tourne** : l'installation
télécharge plusieurs Go (torch, scipy, librosa…) — la contention I/O fausserait les mesures
et risquerait un OOM. Attendre `WAVE X TERMINEE` dans le `campagne.log`.

> État : **✅ REP-01 CLOS le 12/09/2026** — livraison à froid (08/09), script de clôture
> (09/09), validation exécutée sur machine libre après `WAVE 2 TERMINEE` (12/09) : code de
> sortie **0**, **156 tests OK**, versions conformes au lock.
