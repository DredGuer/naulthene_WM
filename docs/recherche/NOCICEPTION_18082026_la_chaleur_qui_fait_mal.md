# La nociception thermique — fermer la boucle entre percevoir et souffrir

**18/08/2026** — carnet de recherche, non normatif.
Arbitrage utilisateur : `+T²` dans le déficit, **sans** drain de jauge au contact.

---

## 1. Le constat de départ

Mesuré sur la campagne v41.24 (17 graines × 2000 jours) :

```
↓ 'lava' +0.059   ↓ 'lava' +0.064   ↓ 'lava' +0.066
```

**La valence de la lave est POSITIVE**, à peu près celle de l'eau. Cause directe :
MiniGrid punit la mort par **exactement `0.0`**, quand toucher un mur coûte `−0,01`.
Mourir était donc *infiniment moins cher* que se cogner.

---

## 2. Ce qui existait déjà — et ce qui manquait

La v41.11 avait livré **le sens**, pas la **douleur**.

| Élément | État avant v41.25 |
|---|---|
| Champ de rayonnement `T = e^{−λd}`, BFS topologique, murs = ombre | ✅ livré |
| `λ` dérivé de la carte (`lambda_diffusion_carte`) | ✅ livré |
| 2 dims (chaleur + ΔT), neutre asymétrique `[0.0, 0.5]` | ✅ livré |
| Entrée en queue du `vecteur_bio`, hors cible JEPA | ✅ livré |
| **Couplage dans le déficit homéostatique** | ❌ **manquant** |

L'agent **percevait** la chaleur sans qu'elle lui **coûte** quoi que ce soit. Le sens
existait, la boucle était ouverte.

---

## 3. Le correctif — une ligne, aucun coefficient

```python
D(t) = (1−satiété)² + (1−hydratation)² + (1−stimulation)² + (1−énergie)² + T(t)²
```

`r_bio = D(t−1) − D(t)` étant une **dérivée**, tout en découle sans qu'aucune règle ne
le décrive : approcher fait mal proportionnellement, entrer dans la source produit
**r_bio = −1,000** (mesuré), soit 5 à 10× un choc de mur.

**Aucune échelle n'est posée** : les trois jauges donnent `(1−x)² ∈ [0,1]`, la chaleur
donne `T² ∈ [0,1]` par construction du champ. C'est la géométrie de la carte qui règle
seule la pente.

### Ce qui a été refusé
- ❌ `si mort: récompense −= X` — seuil en dur sur un type nommé (invariant v41.11).
- ❌ Drain d'hydratation au contact (**arbitrage utilisateur**) — double comptage, le
  risque n°3 déjà écarté dans `calculer_deficit`. À `T=1` le déficit est déjà maximal.

---

## 4. Le piège trouvé en chemin — le décalage d'un tick

La thermoception est lue **en tête de tick**, donc **avant** `env.step`. La facturation
homéostatique, elle, a lieu **après**. Sans correctif, l'agent qui marche dans la lave
aurait payé la température de la case **quittée** (~0,457) et, l'épisode s'arrêtant
aussitôt, **n'aurait jamais ressenti `T=1`** — le signal le plus important du mécanisme
aurait été précisément celui qui n'arrive pas.

C'est le défaut de décalage temporel corrigé en v41.5 sur la maturité, reproduit ici
pour la même raison : une grandeur lue en tête et consommée en queue traverse un
`env.step` qui l'a périmée.

**Correctif** : relecture post-step via `chaleur_seule()`, un accesseur **sans effet de
bord**. Rappeler `lire_thermoception()` aurait écrasé `_chaleur_precedente` et divisé
par deux la clinotaxie du tick suivant — le signal d'approche, seul moyen d'apprendre à
FUIR, aurait été silencieusement faussé.

Vérifié : `chaleur moy. à la mort = 1.000`.

---

## 5. Le banc — pourquoi PAS le cursus normal

```
Cursus (niveau 4)  : chaleur moy 0.001 — 1 tick actif / 400
LavaGapS5 forcé    : chaleur moy 0.245 à 0.405 — 300 à 400 ticks / 400
```

La lave n'apparaît qu'au **niveau 5**, et l'agent est bloqué au **4**. Un A/B lancé sur
le cursus aurait comparé deux bras dont le terme mesuré vaut zéro dans **99,7 %** des
ticks : une ablation **VIDE**, pas négative (§4 de la règle de mesure). D'où
`--env-force`.

---

## 6. Contrôles avant lancement

| Contrôle | Résultat |
|---|---|
| Champ actif sur le banc | 40/40 ticks, moyenne 0,80 |
| `chaleur_seule` sans effet de bord | `_chaleur_precedente` **INTACT** |
| Déficit réagit | T=0 → 0,000 · T=0,45 → 0,203 · T=1 → 1,000 |
| Ablation VIDE sur monde sans lave | chaleur max **0,000000** |
| **Test A/A** (même bras, même graine) | **IDENTIQUES** ✅ |
| Ablation atteint le module | déficit **1,107 (ON) vs 0,998 (OFF)** |

⚠️ **À 5 jours, la survie est identique dans les deux bras** (0 %, 15 %, 0 %…). Le
déficit diffère bien, mais la douleur n'a pas encore changé les **décisions**. C'est
attendu : la valence s'apprend par moyenne des chocs vécus. C'est précisément ce que la
campagne longue doit trancher.

---

## 7. Campagne en cours

**20 graines × 2 bras × 800 jours**, banc `LavaGapS5`.

Critères :
1. La valence de `'lava'` bascule-t-elle **sous zéro** dans le bras ON ?
2. Le **taux de survie** monte-t-il, avec intervalle de Wilson ?
3. Le taux d'**approche** (clinotaxie) baisse-t-il avec l'âge ?

⚠️ Aucune conclusion ne sera tirée sous 20 graines, et chaque taux sera donné **avec son
intervalle de confiance**, jamais seul.
