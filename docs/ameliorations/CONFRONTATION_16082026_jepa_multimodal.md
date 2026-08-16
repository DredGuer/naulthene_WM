# Confrontation : la réflexion « JEPA dédié par sens » contre le code réel

**16/08/2026** — document d'améliorations (**non validé**, aucune ligne de `src/` modifiée).
Réflexion de l'utilisateur confrontée au code mesuré, point par point.

---

## Verdict global

| Section de la réflexion | Statut dans le code |
|---|---|
| §1 — les sens sont un **continuum**, pas des interrupteurs | ✅ **vrai, et déjà appliqué** (v41.11/v41.12) |
| §1 — le tableau de dimensions (147 / 130 / 2 / 4 / 2) | ✅ **exact**, chiffres vérifiés |
| §2 — **stop-gradient** sur les cibles JEPA | ✅ **déjà en place** (`torch.no_grad()`) |
| §2 — une tête JEPA **par sens** | ❌ **2 sur 5** (vue, ouïe) — toucher/odorat/goût : aucune |
| §2 — les sens faibles ont une **porte** dédiée | ❌ ils entrent par la **queue du vecteur bio**, sans porte |
| §3A — perte pondérée `Σ λ_s · L_s` | 🟡 **la structure existe** (`coeff_jepa_audio`), pour 2 sens |
| §3B — rollout multi-échelle (t+1, t+3, t+7) | ✅ **exactement ça** (`horizons=(1, 3, 7)`) |
| §3B — « C2 simule même en étant visuellement aveugle » | ❌ **impossible aujourd'hui** — voir le défaut central |
| §3C — cartographie multi-surprise par modalité | ❌ **une seule erreur JEPA**, scalaire, non ventilée |

**En résumé : ta description du continuum est juste, ton diagramme JEPA décrit un système
qui n'existe pas — et le fossé entre les deux nomme précisément ce qui bloque C2.**

---

## 1. Ce que tu as vu juste

### Les sens sont analogiques, pas binaires

C'est vrai, et c'était **faux dans le code jusqu'à aujourd'hui**. Deux correctifs livrés le
16/08 vont exactement dans ce sens :

- **v41.11 (thermoception)** — le danger était un symbole discret (`lava` = indice 9,
  indiscernable de `1` ou `8`). Il est devenu un champ : `1,000` sur la case, `0,449`
  adjacent, `0,202` à deux pas.
- **v41.12 (toucher à distance)** — `contact_frontal` était un **interrupteur à portée
  zéro** : 1 ou 0 sur la seule case devant. L'agent apprenait le mur *en le percutant*.
  Il perçoit désormais un encombrement gradué et son asymétrie gauche/droite.

Ta formulation « pas 0 marche pas et 1 ça marche » décrit littéralement le défaut corrigé.

### Le stop-gradient est déjà là

```python
with torch.no_grad():
    bus_reel_vision = F.relu(self.porte_visuelle(obs_suivante))
perte = F.mse_loss(attente, bus_reel_vision)
```

L'effondrement de représentation est bien prévenu. Idem pour l'audio.

### Le rollout multi-échelle existe déjà

`horizons=(1, 3, 7)` — exactement tes trois échelles. Avec une restriction importante :
seul le **premier pas** branche sur les 7 actions réelles, les suivants suivent le réflexe
glouton (`argmax`). Sans cela la complexité serait en 7^horizon.

---

## 2. Le défaut central que ta réflexion met au jour

C'est le point le plus utile de ton texte, et il va **plus loin que ce que tu écris**.

### Le rollout de C2 ne reprojette JAMAIS les sens

```python
for saut in range(nombre_sauts):
    futur_bus    = relu(_predire_bus(pensee_branche, action))   # generateur_attente
    futur_mem    = relu(hippocampe([futur_bus, mem_branche]))
    futur_pensee = relu(analyseur(futur_mem))
```

**`integrateur_bio` n'apparaît pas dans cette boucle.** Conséquence mesurée :

> Le vecteur bio (**41 dims** : toucher, odorat, goût, thermoception, pression, faim,
> soif…) entre **une seule fois**, via C1. Puis C2 simule 7 futurs × 7 sauts **sans jamais
> reprojeter un seul sens faible**.

Autrement dit : **C2 imagine un monde sans corps.** Il ne peut pas prédire qu'avancer va
le coller à un mur, ni que tourner va l'éloigner d'une odeur, ni que la chaleur va monter.

### La cible JEPA est la vision seule

```python
bus_reel_vision = relu(porte_visuelle(obs_suivante))   # ← la cible, entièrement
```

Aucun sens faible n'est **jamais** une cible de prédiction. Le modèle du monde de C2 est
un modèle **strictement visuel**.

### Ce que ça implique pour ton §3B

> *« C2 peut simuler une trajectoire en étant visuellement aveugle : les sous-espaces JEPA
> Toucher et Odorat continuent d'estimer les transitions. »*

**C'est l'inverse exact aujourd'hui.** Rendez C2 visuellement aveugle et il ne reste
**rien** — il n'a pas d'autre sous-espace. Ta phrase décrit l'objectif, pas l'état.

---

## 3. Le rapprochement avec les mesures du 16/08

Trois faits mesurés, qui prennent un sens commun à la lumière de ce défaut :

| Mesure | Source |
|---|---|
| Couper C2 change le score de **0,0 point sur 6 niveaux** (78 cellules) | campagne v41 |
| C2 est **36 % plus gros chez les agents qui échouent** (1,33 vs 0,98) | scan des 20 cerveaux |
| **4 sens sur 6** sont ablatables **sans aucun effet** | H15, `bug_or_not_bug` |

Ces trois résultats ont toujours été lus comme « C2 est inutile » et « les sens sont
inutiles ». Le défaut ci-dessus propose une lecture qui les unifie :

> **Les sens faibles n'ont aucun effet parce qu'ils n'atteignent jamais le modèle du
> monde ; et C2 n'a aucun effet parce qu'il simule un monde amputé de tout sauf la vue.**
> Ce ne sont pas deux échecs indépendants — c'est le même câblage manquant, vu des deux
> bouts.

⚠️ **C'est une hypothèse, pas une conclusion.** Elle est *séduisante* — elle explique trois
mesures d'un coup et innocente l'architecture. La règle de mesure impose donc de s'en
méfier davantage, pas moins.

---

## 4. Les réserves sur la proposition

### a) Le coût

Cinq têtes JEPA + cinq portes dédiées, sur un cœur de **7 744 paramètres** (dim_bus=16).
`generateur_attente` en pèse 384. Ajouter trois têtes et trois portes ferait grossir le
cerveau de ~30 % **pour prédire 8 dimensions** (toucher 6 + odorat 4 + goût 2 − recouvrements).

Le README affirme déjà que Naulthène est **2,85× plus lourd** qu'un PPO CNN sans le
battre. Alourdir sans mesure préalable aggraverait la seule critique factuelle du dépôt.

### b) Les λ « adaptatifs »

`λ_vis · L_vis + λ_aud · L_aud + …` — d'où viennent ces λ ? S'ils sont posés en dur, c'est
cinq constantes arbitraires de plus. La méthode du projet (v30.1) impose de **mesurer
avant de rendre adaptatif**, et le précédent existe : `coeff_jepa_audio` est monté par une
**rampe**, pas par une constante.

### c) Le sens de la causalité n'est pas établi

Le scan montre que C2 est **plus gros** chez ceux qui échouent. Deux lectures opposées :

- *« C2 manque d'entrées, donc il ne sert à rien »* → il faut le nourrir (ta thèse) ;
- *« C2 capte du gradient au détriment des couches qui agissent »* → le nourrir empirerait.

**Rien dans les mesures actuelles ne tranche.**

### d) Le monde ne contient peut-être rien à prédire

Mesuré le 16/08 : sur `Empty-8x8`, **5 types pour 64 cases**, dont 63 sur 64 sont mur ou
vide. Un JEPA tactile sur une pièce vide prédirait « pas de mur » 98 % du temps — une
tâche triviale, donc un gradient nul. Voir
[`CONSTAT_16082026_pauvrete_du_monde.md`](../recherche/CONSTAT_16082026_pauvrete_du_monde.md).

---

## 5. Ce que je propose de faire, dans l'ordre

**Le principe : la mesure la moins chère d'abord, et une variable à la fois.**

### Étape 1 — mesurer avant de construire (coût : ~0)

Ventiler l'erreur JEPA **sans ajouter une seule tête** : logger séparément l'erreur de
prédiction sur les dimensions visuelles déjà prédites, par groupe. Si l'erreur est déjà
quasi nulle, un JEPA dédié n'a rien à apprendre — et la proposition tombe sans avoir coûté
un run.

### Étape 2 — le câblage manquant, pas les cinq têtes (coût : faible)

Reprojeter le **vecteur bio dans le rollout** — un seul appel à `integrateur_bio` dans la
boucle de simulation. C'est **une ligne**, aucune tête, aucun paramètre nouveau, et ça
donne à C2 un corps dans son monde imaginé. À mesurer en A/B sur 20 graines.

Si ça ne change rien, les cinq têtes ne changeront rien non plus : elles résoudraient plus
finement un problème qui n'existe pas.

### Étape 3 — une tête, pas cinq (coût : moyen)

Si l'étape 2 donne un effet, ajouter **une seule** tête JEPA proprioceptive (toucher +
pression + thermoception : 8 dims, les plus liées à l'action), sur le modèle exact de
`generateur_attente_audio` qui existe déjà. Puis mesurer.

Le goût est le dernier candidat : c'est une **conséquence** d'une action de consommation,
pas une transition du monde — sa prédiction est presque déterministe.

---

## 6. Réponse courte

**Ta section 1 est juste et déjà appliquée. Ta section 2 décrit un système qui n'existe
pas — et c'est sa valeur : elle nomme le câblage manquant. Ta section 3 est prématurée.**

Le trou que tu as trouvé est réel et important : **C2 imagine un monde sans corps.** Mais
il se comble d'abord par **une ligne** (reprojeter le vecteur bio dans le rollout), pas par
cinq têtes et cinq portes — et seulement après avoir vérifié qu'il y a quelque chose à
prédire dans un monde à 5 types.
