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
**r_bio = −0,791** sur un vrai pas dans la lave (banc intra-tick), soit ~3300× le
coût d'un tick ordinaire.

⚠️ **Le `−1,000` initialement publié était FAUX** : mesuré à la main hors du tick réel,
alors que le moteur produisait **0,000000** de douleur (annulation arithmétique — voir
§8).

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

---

## 8. L'ERREUR — la douleur annulée par sa propre soustraction (fix1)

**La campagne a mesuré du vide.** 5 paires de graines, valences **identiques à la 6ᵉ
décimale** — et pas seulement sur la lave :

```
FOOD  +0.254431   (ON et OFF)
sol   +0.160835   (ON et OFF)
lava  +0.059012   (ON et OFF)
```

`FOOD` et `sol` n'ont **aucun rapport** avec la lave. Ce n'était donc pas « la douleur
n'atteint pas la lave » : **les deux cerveaux étaient le même cerveau**. J'ai lu la ligne
`lava` en premier et raisonné dessus, au lieu de voir que la colonne entière était
identique. C'est exactement le « résultat trop propre » du §3 de la règle de mesure.

### La cause

```python
def step_metabolisme(self, ...):
    deficit_avant = self.calculer_deficit()   # ← calculé ICI, en interne
    ...
    r_bio = deficit_avant - deficit_apres
```

J'écrivais `moteur_bio.chaleur` **avant** l'appel. Les deux déficits portaient donc la
**même** valeur de `T²`, éliminée par la soustraction :

```
r_bio en entrant dans la lave : −0,000238
r_bio sans aucune chaleur     : −0,000238
ÉCART                         :  0,000000
```

### Le chiffre faux

Le **`r_bio = −1,000`** publié en v41.25 était mesuré **à la main** — deux appels à
`calculer_deficit` encadrant une affectation, hors du tick réel. **Le moteur ne l'a
jamais produit.** Il a été inscrit au CHANGELOG et dans les deux README comme une mesure ;
c'en était une, mais d'autre chose que ce que le code exécute.

> **Leçon.** Une grandeur calculée par une fonction doit être vérifiée **à la sortie de
> cette fonction**. La reconstruire à côté vérifie l'arithmétique de l'expérimentateur,
> jamais le chemin réel. D'où `banc_intra_tick_douleur.py`, à qui il est **interdit** de
> recalculer un déficit lui-même.

### Le diagnostic intermédiaire était faux aussi

L'hypothèse retenue sur le moment : `poids_evenement = 1.0 if recompense_env > 0 else
0.0` fermerait la porte du choc dopaminergique, donc la valence ne serait jamais mise à
jour sur un échec.

**Vérification faite, ce n'est pas ce chemin.** La valence ne lit **jamais**
`poids_evenement` : `_memoriser_si_saillant` reçoit `recompense_interne`, dans laquelle
`r_bio` **est** présent (`noyau.py:8194`), et `enregistrer_evenement` en fait une moyenne
glissante. La porte décrite existe, mais gouverne la **dopamine** et la **fortification
synaptique**, pas la valence. Une explication plausible et cohérente peut désigner le
mauvais organe — seule la lecture du chemin réel tranche.

### Le correctif

`chaleur_apres` devient un **argument**, appliqué **entre** les deux mesures. C'est la
**transition** thermique qui fait mal, jamais le niveau seul.

| transition | `r_bio` (produit par le moteur) |
|---|---|
| 0,00 → 0,00 (témoin) | −0,000238 |
| 0,00 → 0,46 (case adjacente) | −0,211838 |
| **0,46 → 1,00 (pas réel dans la lave)** | **−0,791111** |
| **1,00 → 0,00 (fuite)** | **+0,999762** — soulagement |
| même pas, `--sans-douleur` | −0,000238 (écart **−1,000000**) |

**Effet sur la valence apprise** (25 jours, graine 1) :

| | douleur ON | témoin OFF |
|---|---|---|
| **`lava`** | **−0,752562** | **+0,062455** |

**Négative pour la première fois du projet.** Elle était positive sur *tous* les cerveaux
mesurés depuis l'origine.

⚠️ Cela prouve que **le canal fonctionne**, pas que le comportement s'améliore. La
campagne 20 graines × 2 bras × 300 jours est relancée pour mesurer la **survie** — et
elle peut parfaitement revenir négative.
