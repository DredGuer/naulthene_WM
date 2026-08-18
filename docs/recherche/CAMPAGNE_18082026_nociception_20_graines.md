# Campagne nociception thermique — 20 graines × 2 bras — la peur s'apprend, la survie baisse

**18/08/2026** — carnet de recherche, non normatif.
Banc : `MiniGrid-LavaGapS5-v0` forcé (`--env-force`), 300 jours, témoin `--sans-douleur`.
**40 runs terminés sur 40.**

---

## 1. Le résultat en une ligne

> **La boucle nociceptive fonctionne de bout en bout — et elle DÉGRADE la survie.**
> La valence de la lave devient négative sur **20 graines sur 20**, l'agent approche
> significativement moins du danger, et il gagne **2,9× moins souvent**.

C'est un résultat **négatif sur l'objectif** et **positif sur le mécanisme**. Les deux
doivent être rapportés ensemble.

---

## 2. Le mécanisme : validé sans ambiguïté

| | ON (douleur) | OFF (témoin) |
|---|---|---|
| **Valence apprise de `lava`** | **−0,7614** | **+0,0615** |
| Graines à valence négative | **20/20** | **0/20** |

```
delta moyen = −0,8229   écart-type 0,0034
t apparié   = −1066     (seuil de significativité à n=20 : |t| > 2,09)
```

**Aucun chevauchement entre les deux groupes** — la graine la moins négative du bras ON
(−0,7564) reste très loin de la plus faible du bras OFF (+0,0551).

C'est la **première fois du projet** que la lave porte une valence négative. Elle était
positive (+0,059 à +0,081 — soit celle de l'eau) sur *tous* les cerveaux mesurés depuis
l'origine, sur 17 graines × 2000 jours encore la veille.

### Le comportement suit

```
taux d'approche du danger : −5,60 points   t = −5,51   SIGNIFICATIF
```

Ce n'est donc pas qu'une valeur dans un fichier : la clinotaxie mesure que l'agent
**s'écarte réellement** des sources de chaleur. Le canal va jusqu'au comportement moteur.

---

## 3. Le résultat qui déçoit : la survie baisse

| | survie | IC95 (Wilson) |
|---|---|---|
| **ON (douleur)** | **6,71 %** | [6,19 – 7,27] |
| **OFF (témoin)** | **8,57 %** | [8,19 – 8,96] |

```
delta apparié = −3,10 points   t = −3,36   SIGNIFICATIF
14 graines sur 20 vont dans le sens de la dégradation
```

**Les intervalles de confiance ne se chevauchent pas.** Ce n'est pas du bruit.

---

## 4. Ce que les chiffres disent vraiment — l'agent ne meurt plus, il n'arrive plus

C'est le point le plus intéressant de la campagne, et il n'était pas prévu.

| | ON | OFF | ratio |
|---|---|---|---|
| Morts | **7 800** | 18 531 | **2,4× moins** |
| Victoires | **561** | 1 736 | **3,1× moins** |
| Fins d'épisode | 8 361 | 20 267 | **2,4× moins** |
| **Victoires par jour** | **0,40** | **1,16** | **2,9× moins** |

L'agent qui a mal **meurt 2,4× moins souvent** — la peur fonctionne, littéralement. Mais
il **gagne 2,9× moins**, et pas seulement en proportion : en valeur absolue.

Ses épisodes sont **2,4× plus longs** (moins de fins pour un budget de jours comparable) :
il ne se jette plus dans la lave, il tourne autour sans jamais franchir.

> **Sur `LavaGapS5`, le but est DERRIÈRE le couloir de lave. Fuir le danger, c'est fuir
> l'objectif.** La douleur enseigne l'évitement, pas le franchissement prudent.

⚠️ Cette lecture est une **hypothèse cohérente avec les chiffres**, pas une mesure directe :
elle n'a pas été testée sur une carte où le danger serait latéral au chemin. C'est le test
qui la trancherait.

---

## 5. Contrôles de validité

| Contrôle | Résultat |
|---|---|
| Runs terminés | **40/40**, aucun coupé |
| Chaleur moyenne ressentie | ON 0,3617 · OFF 0,3553 — **exposition équivalente** |
| Banc réellement actif | 300-400 ticks chauds / 400 (cursus normal : 1/400) |
| Test A/A (avant campagne) | identique ✅ |
| Ablation atteignant le module | déficit 1,107 (ON) vs 0,998 (OFF) ✅ |
| n | **20 paires** — conforme à la règle du projet |

L'exposition thermique quasi identique entre les deux bras (0,3617 vs 0,3553) est
importante : les deux agents **voient** autant de danger. Seule la douleur diffère.

---

## 6. Ce que la campagne établit

1. ✅ **Une contrainte homéostatique peut faire émerger une aversion** sans qu'aucune règle
   ne nomme le danger. `+T²` dans le déficit suffit : 20/20, `t = −1066`.
2. ✅ **L'aversion se transmet au comportement** (−5,6 pts d'approche).
3. ❌ **La peur seule ne produit pas la compétence.** Un organisme qui craint sans savoir
   contourner devient prudent et **moins performant**.
4. 📌 Ceci rejoint le bilan général du projet : **1 mécanique cognitive sur 13 testées** a
   amélioré une métrique de tâche (le brain-sparing, v41.16).

---

## 7. Ce qui reste ouvert

- **Le couplage douleur/but.** La douleur doit rendre le danger coûteux *sans* rendre
  l'objectif inatteignable. C'est une question de **conception**, pas de réglage — et
  aucune constante ne la résoudra.
- **Tester sur un danger latéral** (`LavaCrossing` plutôt que `LavaGap`) : si la
  dégradation disparaît quand le danger n'est plus sur le chemin, l'hypothèse du §4 est
  confirmée. C'est le test le moins cher et le plus informatif.
- **Faut-il garder la douleur ?** Le mécanisme est juste et biologiquement fondé, mais il
  coûte 3,1 points de survie sur ce banc. Décision utilisateur — la mesure est fournie,
  elle ne tranche pas seule.
