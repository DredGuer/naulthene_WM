# Pourquoi la douleur coûte des victoires — le carburant, pas le raisonnement

**18/08/2026** — carnet de recherche, non normatif. **Enquête en cours.**
Question utilisateur : *« la perte de vitesse de gain, est-ce lié à l'intelligence
(C1/C2), au nombre de jours, ou autre ? Il manque de l'équilibre ou du temps. »*

Décision prise : **la douleur est conservée**. L'enquête porte sur son coût.

---

## 1. Réponse courte

> Ce n'est **ni C1/C2, ni le nombre de jours**. C'est le **métabolisme** : la douleur
> creuse le déficit, le déficit vide l'énergie, l'énergie effondre la vigueur, et la
> vigueur éteint la délibération. **L'agent a appris la peur et n'a plus les moyens de
> s'en servir.**

L'intuition « il manque de l'équilibre » est la bonne : le déséquilibre est entre le
**coût d'exister** et le **budget disponible**.

---

## 2. Les trois hypothèses, tranchées par la mesure

### 2.1 ❌ C1/C2 — écartée, et c'est une bonne nouvelle

| | accord | ratio C2/C1 | actions distinctes C1 / C2 |
|---|---|---|---|
| ON | 16,2 % | 1,68× | 4,0 / **4,3** |
| OFF | 17,6 % | 1,91× | 4,5 / **5,6** |

C2 vote **4 à 6 actions différentes** — il n'est plus la « voix figée » des campagnes
antérieures (1 seule action, accord 0 %, ratio 22×). Sur ce banc, **C1/C2 est en meilleure
santé qu'il ne l'a jamais été**. Ce n'est pas là que ça bloque.

### 2.2 🟡 Le temps — facteur réel mais mineur

Survie par quart de run :

| bras | Q1 | Q2 | Q3 | Q4 | tendance |
|---|---|---|---|---|---|
| ON | 5,04 % | 5,44 % | 6,15 % | 6,71 % | **+1,67** |
| OFF | 6,40 % | 7,25 % | 8,63 % | 8,57 % | **+2,17** |

**Ça monte encore à la fin, sans plateau** : 300 jours ne suffisent pas à voir la
convergence. Mais la pente est faible, et **l'écart entre les deux bras ne se réduit pas**
avec le temps. Rallonger aiderait un peu ; ça ne réglerait pas le fond.

### 2.3 ✅ Le métabolisme — la cause

| | énergie | vigueur | ticks en basse énergie |
|---|---|---|---|
| **ON** | **0,156** | **0,170** | **86 %** |
| OFF | 0,259 | 0,200 | 68 % |
| *plancher* | | *0,150* | |

**L'agent qui a mal passe 86 % de sa vie en hypoglycémie**, vigueur à **0,020 du plancher
absolu**. Or la vigueur module toute la décision :

| vigueur | voix de C1 | voix de C2 |
|---|---|---|
| 1,00 | 100 % | 100 % |
| **0,17** | **~17 %** | **~3 %** |

**À cette vigueur, C2 est éteint à ~97 %.** La délibération n'est pas mauvaise : elle n'a
pas la force de s'exprimer. C'est un effet de bord **métabolique**, pas cognitif.

---

## 3. ⚠️ Une hypothèse que je dois retirer

Le carnet de campagne avançait : *« sur `LavaGap` le but est DERRIÈRE le couloir de lave,
donc fuir le danger c'est fuir l'objectif »*. Elle était présentée comme hypothèse non
testée. **Elle est FAUSSE, et la mesure l'établit** :

| environnement | chemin sûr existe | détour vs plus court chemin |
|---|---|---|
| `LavaGapS5` | **10/10 graines** | **+0,0 case** |
| `LavaCrossingS9N1` | **10/10 graines** | **+0,0 case** |

**Éviter la lave ne coûte RIEN géométriquement**, dans les deux environnements. Le chemin
sûr est exactement aussi court que le plus court chemin. L'agent n'a jamais eu à choisir
entre sa sécurité et son but.

> L'explication géométrique était séduisante et cohérente avec les chiffres — elle était
> simplement fausse. Une hypothèse plausible n'est pas une mesure ; celle-ci a coûté cinq
> minutes de vérification et aurait pu orienter tout le chantier suivant dans le vide.

---

## 4. Ce que la mesure dit réellement

| | épisodes par jour | durée moyenne |
|---|---|---|
| ON | 5,73 | **~70 ticks** |
| OFF | 13,52 | **~30 ticks** |

L'agent qui a mal fait des épisodes **2,3× plus longs**. Il ne meurt plus vite (2,4× moins
de morts) — **il erre**. Combiné à l'hypoglycémie à 86 %, le tableau est cohérent :

1. La douleur creuse `D(t)` → `r_bio` chroniquement négatif
2. L'énergie s'effondre (0,26 → 0,16)
3. La vigueur touche son plancher → C2 s'éteint
4. L'agent survit plus longtemps mais **sans direction** → moins de victoires

**Ce n'est pas un problème de peur mal apprise. C'est une famine induite par la douleur.**

---

## 5. Le test en cours

`LavaCrossingS9N1`, 20 graines × 2 bras × 300 jours (lancé le 18/08 à 21h46).

⚠️ **Ce banc ne teste plus l'hypothèse géométrique** (réfutée au §3). Il teste autre chose,
qui reste utile : **le coût de la douleur dépend-il de la densité du danger ?**

| | grille | cases de lave | chemin |
|---|---|---|---|
| `LavaGapS5` | 5×5 | 2 | 4 cases |
| `LavaCrossingS9N1` | 9×9 | 6 | 12 cases |

Sur une carte 3× plus grande avec 3× plus de lave, la chaleur ambiante devrait être plus
diffuse (le champ `e^{−λd}` s'atténue avec la distance, et `λ` dérive des dimensions).
**Si la dégradation suit la chaleur moyenne ressentie**, la cause métabolique est
confirmée. Si elle disparaît, autre chose est en jeu.

⚠️ **Confond assumé** : la carte est aussi plus grande et le trajet plus long. Ce banc
n'isole donc pas parfaitement un facteur — il indique une direction, il ne conclut pas.

---

## 6. Pistes, si la cause métabolique se confirme

**La douleur et la faim se disputent le même budget.** Chez le vivant, une douleur aiguë
ne consomme pas les réserves comme une famine : elle **mobilise** (adrénaline), elle
n'affame pas. Ici les deux entrent dans `D(t)` à la même échelle — une brûlure « coûte »
autant qu'un jeûne prolongé.

Piste conforme au dogme : la douleur pourrait être un signal aversif **fort mais non
métabolique** — présente dans le déficit sans passer par l'énergie. C'est une question de
**structure de `D(t)`**, pas de coefficient à régler.

**Ce qui n'est PAS recommandé** :
- toucher au plancher de vigueur → masquerait le symptôme
- rallonger les runs à l'aveugle → des heures pour +1,7 point
