# La récompense n'est pas creuse — et la normalisation par épisode est pire

**30/08/2026** · document `recherche/enquetes_closes/` : **non normatif**, mais à lire
avant de rouvrir cette piste.

## La question posée

> *« Dans un épisode de 150 ticks où la récompense environnementale est à 0.0000 sur
> 149 pas et ne tombe qu'au dernier, comment l'information remonte-t-elle le temps ?
> Le pas décisif se retrouve dilué dans la masse des pas d'exploration. »*

Hypothèse implicite : **le problème est l'attribution du crédit face à une récompense
creuse** (*sparse reward*), et le coupable serait la normalisation des retours sur la
journée entière plutôt que par épisode.

---

## Verdict en deux phrases

> ❌ **La prémisse est fausse : la récompense n'est PAS creuse.** 86 % du signal reçu est
> **dense** — versé à chaque tick. Et la correction proposée (normaliser par épisode) est
> **mesurée comme PIRE** que le code actuel sur les récompenses réelles.

---

## 1. Ce qui était déjà mesuré, et qu'il faut savoir avant de rouvrir

Deux enquêtes closes couvrent déjà le cœur de la question :

| Piste | Verdict | Où |
|---|---|---|
| Passer l'acteur en **TD(0)** ou en **GAE** | ❌ **fermé** — MC (le code actuel) est le **moins mauvais** des trois : 1,275× contre 1,125× (TD) et 1,161× (GAE), 8 cerveaux | [CLIC_27082026](CLIC_27082026_le_td_error_ne_sauve_rien.md) |
| Connecter le tronc perceptif aux têtes | ❌ **fermé** — bruit perceptif **+48 %**, niveau δ = **0,00** | [CONDITIONNEMENT_27082026](CONDITIONNEMENT_27082026_le_signal_arrive_et_ne_sert_a_rien.md) |

La note du 27/08 concluait déjà : *« le problème n'est pas **quand** on paie, mais que le
signal de paiement est mélangé à trois autres au moment où on le lit. »*

**Changer la formule de l'avantage est donc une piste fermée.** Elle a été comparée à ses
deux alternatives standard, sur les mêmes trajectoires, sans lancer de campagne.

---

## 2. Ce qui n'avait PAS été mesuré : la fenêtre de normalisation

Le code (`apprendre_journee`) calcule le retour **en respectant les frontières
d'épisode** — c'est correct :

```python
R = r + gamma * (0.0 if d else R)          # coupé aux `dones` ✅
```

Mais il le **normalise sur la journée entière**, tous épisodes confondus :

```python
returns = (returns - returns.mean()) / (returns.std() + 1e-8)   # ~400 ticks, N épisodes
```

C'est une asymétrie réelle, et elle n'avait jamais été mesurée.

### 🔴 Sur une récompense purement creuse, la dilution est réelle

Simulation, 6 épisodes × 150 ticks, **un seul** réussi (récompense au dernier tick) :

| | Globale (actuel) | Par épisode |
|---|---:|---:|
| \|retour\| moyen, épisode gagnant | 0,9248 | 0,5804 |
| \|retour\| moyen, épisodes perdants | **0,1469** | **0,0000** |
| **Contraste** | **6,30×** | ~∞ |

Les épisodes perdants reçoivent **0,1469 de signal alors qu'ils n'ont rien gagné** : du
bruit appris comme s'il portait de l'information.

**C'est sur cette base que la correction paraissait évidente.** Elle ne l'est pas.

---

## 3. 🔴 Le retournement : sur les récompenses RÉELLES, la correction est PIRE

Le test ci-dessus supposait une récompense creuse. Refait avec les valeurs **réellement
mesurées** (curiosité ~+0,0091/tick, `r_bio` ~+0,0037/tick, stagnation −0,0005) :

| Cas | Globale (actuel) | Par épisode |
|---|---:|---:|
| **Avec** une victoire dans la journée | **3,00×** | **0,94×** |
| **Sans** aucune victoire (le cas du niveau 3) | 0,74× | 0,86× |

Normaliser par épisode **détruit** le contraste (3,00× → 0,94×, soit *aucune* distinction
entre l'épisode gagnant et les autres). La raison est mécanique : chaque épisode étant
centré-réduit **sur lui-même**, l'information « celui-ci a gagné, les autres non »
disparaît — c'est précisément l'information qu'on voulait préserver.

> **Leçon** : une correction validée sur un cas synthétique doit être re-testée sur les
> grandeurs réelles avant d'être codée. Ici l'écart entre les deux tests est un
> **renversement de signe**, pas une nuance.

### Robustesse du renversement — 20 graines × 3 régimes

Un renversement de signe se contre-vérifie (règle de mesure §3 : *un résultat favorable se
vérifie deux fois plus qu'un défavorable* — et ici le résultat défavorable **à ma propre
proposition** mérite le même soin) :

| Régime | Globale | Par épisode | Globale meilleure |
|---|---:|---:|---:|
| 6 ép. × 150, 1 victoire | **2,59×** | 0,91× | **20/20** |
| 4 ép. × 200, 1 victoire | **2,23×** | 0,84× | **20/20** |
| 10 ép. × 100, 2 victoires | **2,93×** | 0,98× | **20/20** |

**60 tirages sur 60** donnent le même sens. Ce n'est pas un artefact de graine ni de
découpage.

---

## 4. Pourquoi : la récompense n'est pas creuse

Mesuré sur **40 cerveaux** (cohorte AB3, niveau 3, 800 ticks) :

| Composante | Somme | Part |
|---|---:|---:|
| Signal positif total | 16,9552 | 100 % |
| dont **récompense du monde** (creuse, terminale) | 2,3732 | **14,0 %** |
| dont **barème interne** (dense, chaque tick) | 14,5820 | **86,0 %** |

La curiosité est versée sur **100 % des ticks**, `r_bio` sur **100 % des ticks**.

> **L'agent ne fait pas face à une récompense creuse. Il fait face à une récompense DENSE
> qui ne parle pas de la tâche.**

C'est une reformulation, pas un détail : les techniques du *sparse reward* (shaping,
curiosité, hindsight, options) visent à **densifier** un signal absent. Ici le signal est
déjà dense — et c'est peut-être le problème, pas la solution.

---

## Ce que cela ferme et ce que cela ouvre

**Fermé** :
- Changer la formule de l'avantage (MC → TD/GAE) — mesuré le 27/08.
- Normaliser les retours par épisode — mesuré ici, **effet inverse**.
- Traiter le plafond comme un problème de *sparse reward* — la prémisse est fausse.

**Ouvert, et non mesuré** : le barème dense **domine** le signal terminal à 86/14. Un agent
optimise donc principalement des grandeurs internes. Est-ce que réduire cette domination
(sans supprimer le signal, ce qui l'effondrerait) change quoi que ce soit ? **Personne ne
l'a testé** — et la cohorte du 30/08 a montré que les *parts* du barème ne prédisent rien,
ce qui rend cette piste peu prometteuse a priori.

⚠️ **Aucune de ces mesures n'établit une cause du plafond.** Ce sont des lectures directes
et des simulations, pas des comparaisons appariées. Le tableau des suspects reste **vide**.
