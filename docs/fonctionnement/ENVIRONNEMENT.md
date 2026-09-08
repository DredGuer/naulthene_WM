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

1. Installation dans un **environnement vierge** (nouveau venv, `pip install -c
   constraints-lock.txt -e .[tout]`).
2. **Import minimal** : `PYTHONPATH=src python -c "import naulthene.cerveau.noyau"` (CPU).
3. **Tests CPU** : `NAULTHENE_DEVICE=cpu venv/bin/python -m unittest discover -s tests`
   → 44 tests OK.
4. Campagne suivante avec le bloc §4 rempli — sert de vérification de bout en bout.

> État : livraison à froid **faite** (08/09/2026) ; clôture **en attente** des critères 1-4,
> différée pour ne pas concurrencer la campagne SCI-01 Wave 1 qui tourne (machine réservée).
