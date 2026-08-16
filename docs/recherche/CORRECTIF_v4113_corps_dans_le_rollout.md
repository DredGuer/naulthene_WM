# v41.13 — C2 imaginait un monde sans corps

**16/08/2026** — carnet de recherche, non normatif.
Issu de la [confrontation JEPA multimodal](../ameliorations/CONFRONTATION_16082026_jepa_multimodal.md)
et de la réflexion développementale de l'utilisateur (bébé → enfant → ado → adulte).

---

## 1. Le lien avec le modèle développemental

La réflexion de l'utilisateur pose une boucle :

> **Action → sensation → conséquence → mémoire → nouvelle prédiction.**

Et une progression :

| Âge | Question |
|---|---|
| 👶 Bébé | « Qu'est-ce que je ressens ? » |
| 🧒 Enfant | « Qu'est-ce qui se passe ? » |
| 🧑 Ado | « Pourquoi ça se passe ? » |
| 🧔 Adulte | « Comment l'utiliser / le prédire ? » |

Confronté au code, ce cadre nomme exactement ce qui manquait. **Naulthène avait le stade
bébé (il ressent) et le stade adulte (il planifie), mais pas le pont entre les deux :
ce qu'il ressent n'entrait jamais dans ce qu'il prédit.**

L'exemple du bébé est littéralement le test : *« il attrape → secoue → entend → porte à la
bouche → lâche → observe que ça tombe »*. Chaque étape est une **conséquence sensorielle
d'une action**. Or C2 ne pouvait simuler aucune conséquence sensorielle — seulement des
conséquences visuelles.

---

## 2. Le défaut, mesuré

```python
for saut in range(nombre_sauts):
    futur_bus    = relu(_predire_bus(pensee_branche, action))
    futur_mem    = relu(hippocampe([futur_bus, mem_branche]))
    futur_pensee = relu(analyseur(futur_mem))
```

**`integrateur_bio` n'apparaît nulle part dans cette boucle.**

> Les **41 dims** du vecteur bio (toucher, odorat, goût, thermoception, pression, faim,
> soif) entraient **une seule fois**, via C1. Puis C2 simulait 7 futurs × 7 sauts **sans
> jamais reprojeter un seul sens**.

C2 ne pouvait donc pas simuler « si j'avance je serai collé au mur », ni « si je tourne
l'odeur baissera », ni « si je continue la chaleur montera ».

Et la cible JEPA est `relu(porte_visuelle(obs_suivante))` — **la vision seule**. Aucun sens
faible n'est jamais une cible de prédiction.

### Ce que ça unifie

| Mesure | Lecture jusqu'ici |
|---|---|
| Couper C2 = **0,0 pt sur 6 niveaux** (78 cellules) | « C2 est inutile » |
| C2 **36 % plus gros** chez les agents qui échouent | « renforcer C2 nuit » |
| **4 sens sur 6** ablatables sans effet (H15) | « les sens sont inutiles » |

Une seule cause candidate les explique toutes les trois : **les sens n'atteignent jamais le
modèle du monde, et le modèle du monde simule un agent désincarné.** Deux bouts du même
câblage manquant.

⚠️ **Hypothèse, pas conclusion.** Elle est *confortable* — elle explique trois mesures d'un
coup et innocente l'architecture. La règle de mesure impose de s'en méfier **davantage**.
D'où la campagne A/B ci-dessous plutôt qu'une déclaration de victoire.

---

## 3. L'étape 1 — mesurer avant de construire (coût nul)

Avant d'ajouter la moindre tête JEPA, une question : **reste-t-il quelque chose à
prédire ?** Si l'erreur visuelle était déjà quasi nulle et sans structure, ajouter des
têtes n'aurait fait que densifier un gradient éteint.

Ventilation ajoutée (télémétrie **pure**, `no_grad` + `.detach()`, run bit-identique) :

| Jour | Amplitude cible | Concentration | Pire dim |
|---|---|---|---|
| 1 | 0,2972 | 0,625 | 1,320 |
| 2 | 0,2765 | 0,650 | 1,327 |
| 3 | 0,2091 | 0,888 | 1,411 |

**Lecture** (0,25 = erreur parfaitement étalée, 1,0 = tout dans un coin) :

- l'erreur **se concentre** (0,625 → 0,888) : le modèle échoue sur un aspect **précis** du
  monde, ce n'est pas du bruit uniforme ;
- l'amplitude de la cible reste **non nulle** (0,21–0,30) : il y a bien quelque chose à
  prédire — ce n'est pas une *ablation vide* au sens de la règle de mesure ;
- la pire dimension est à **1,41** contre une erreur moyenne de 0,17, soit **8×**.

**Verdict : le modèle du monde n'est pas saturé.** L'étape 2 est justifiée.

---

## 4. L'étape 2 — le correctif, en une ligne

```python
if vecteur_bio is not None:
    futur_pensee = relu(integrateur_bio(
        torch.cat([futur_pensee, vecteur_bio.expand(...)], dim=-1)))
```

**Aucune tête nouvelle, aucun paramètre ajouté, aucune constante.** On réutilise
`integrateur_bio`, la couche qui fait déjà exactement ce travail dans C1.

L'alternative proposée (5 têtes JEPA + 5 portes dédiées) ferait grossir de ~30 % un cœur
déjà **2,85× plus lourd** qu'un PPO qui le bat — à envisager seulement **si** ce
câblage-ci produit un effet.

### Ce qui est assumé

⚠️ **Le vecteur bio est tenu CONSTANT sur tout le rollout.** L'agent imagine « mon corps
tel qu'il est maintenant » projeté dans les futurs possibles. Prédire l'**évolution** des
sens exigerait précisément les têtes JEPA de l'étape 3 — c'est la question suivante. Un
corps figé reste infiniment plus informatif qu'un corps absent.

⚠️ `vecteur_bio=None` ⇒ comportement **bit-identique** à la v41.12. Le rêve (`rever()`),
qui n'a pas de corps sous la main, retombe exactement sur l'ancien chemin.

---

## 5. Validation du banc

| Contrôle | Résultat |
|---|---|
| A/A témoin (graine 33, ×2) | **md5 identique** |
| A/A variante (graine 33, ×2) | **md5 identique** |
| Témoin ≠ variante | **oui** — empreintes différentes |
| Ablation atteint le module | **oui** — assertion runtime |

Le `C2=0.000` observé au jour 1 est présent **des deux côtés** : c'est un comportement de
naissance, pas une régression du correctif.

---

## 6. Campagne en cours

**20 graines × 2 bras × 3000 jours**, mêmes mondes des deux côtés.

- témoin : `--sans-corps-rollout` (C2 simule sans corps, v41.12)
- variante : par défaut (C2 reprojette le vecteur bio)

Analyse par `docs/recherche/scripts/analyser_campagne_v4113.py`, intervalles de Wilson
obligatoires, **aucune conclusion sous 20 graines**.

**Si l'effet est nul**, l'étape 3 (têtes JEPA par sens) devient très douteuse : elle
résoudrait plus finement un problème qui n'existe pas. **Si l'effet est réel**, alors
une seule tête proprioceptive (toucher + pression + thermoception, 8 dims) devient le
prochain candidat — pas cinq.
