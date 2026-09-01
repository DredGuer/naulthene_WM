# Le plancher géométrique n'existe pas — mais la maîtrise mesure peut-être autre chose

**30/08/2026** · `recherche/campagnes/` · ⚠️ **n = 4 cerveaux** — sous la barre des 20


> 🔴 **RÉSERVE D'INSTRUMENT — ajoutée le 01/09/2026.** Les chiffres de banc de ce document
> ont été produits par une sonde qui lisait la mémoire de travail au mauvais index
> (`penser()[1]`, la VALEUR, au lieu de `[4]`), un garde-fou la rejetant **en silence** :
> l'agent jouait **sans mémoire de travail ni contexte épisodique**. Re-mesuré sur `A_g66`,
> le succès passe de **37,33 % à 40,00 %** et la directivité de **14,21× à 14,92×**.
> Le **sens** des conclusions n'est pas inversé (l'aléatoire reste à 5,67 %, la compétence
> reste réelle), mais **les valeurs numériques sont à reprendre** et `r = −0,8225` est
> **non établie** tant que la cohorte n'est pas rejouée.
> Voir `docs/recherche/enquetes_closes/INSTRUMENT_01092026_la_memoire_du_banc.md`.

## La question posée

Dix-huit variables internes ne corrèlent avec la maîtrise. D'où l'hypothèse :

> *« Les ~15 % observés ne mesurent pas un apprentissage qui plafonne. Ils mesurent la
> part des tirages où la brèche tombe sur la trajectoire par défaut d'une marche
> semi-aléatoire. Le plafond serait le plancher thermique de la carte. »*

Prédiction associée : un marcheur aléatoire ferait **10–15 %**, un cerveau neuf autant, et
l'entraîné ne s'en distinguerait pas.

---

## Verdict

> ❌ **Le plancher géométrique n'existe pas.** L'aléatoire fait **5,67 %** (pas 10–15 %) et
> les cerveaux entraînés font **25,83 %** agrégé — `z = +13,56`. La compétence est réelle.
> ✅ **Mais les victoires restent browniennes** (14–18× le plus court chemin).
> 🟡 **Et un fait non expliqué** : le succès au banc est **inversement** ordonné à la
> maîtrise en run (`r = −0,89`, `t = −2,72`, **NS à n=4**).

---

## 1. Les mesures

`SimpleCrossingS9N1`, 300 épisodes par politique, **graines de carte appariées** entre les
trois bras. Plus court chemin médian : **12 pas**. Budget : **324 ticks**.

| Cerveau | `dim_bus` | Maîtrise run | **Banc** | `z` vs aléatoire | Directivité |
|---|---:|---:|---:|---:|---:|
| A_g155 | 145 | 45,0 % | 7,67 % | +0,98 | 18,08× |
| A_g122 | 137 | 35,0 % | 27,33 % | **+7,15** | 16,33× |
| A_g166 | 132 | 25,0 % | 31,00 % | **+8,02** | 16,42× |
| A_g66 | 158 | 30,0 % | **37,33 %** | **+9,44** | **14,21×** |
| **Agrégé** | | | **25,83 %** | **+13,56** | |
| *Aléatoire (témoin)* | | | *5,67 %* | | *20,17×* |

**A_g66 à 37,33 % entre dans la fourchette de PPO** (27,1–39,8 %, mesurée le 29/08).
Naulthène *peut* égaler un PPO sur ce niveau.

Le marcheur aléatoire a par ailleurs été mesuré séparément sur **600 épisodes** :
**4,50 %**, IC95 [3,1 ; 6,5] — cohérent avec les 5,67 % du banc.

---

## 2. ✅ Ce qui est établi : la compétence est réelle

Trois cerveaux sur quatre battent le hasard avec `z` entre **+7,15 et +9,44**, intervalles
disjoints. Ce ne sont pas des victoires de tirage.

**L'hypothèse du plancher géométrique est réfutée** : elle prédisait `entraîné ≈ aléatoire`,
et prédisait le hasard à 10–15 % quand il est à 5,67 %.

---

## 3. ✅ Les victoires restent browniennes

`r(succès, directivité) = −0,92` : plus un cerveau gagne, plus ses trajets raccourcissent.
Mais même le meilleur reste à **14,21×** l'optimal — ~171 ticks pour un trajet de 12 pas.

> La compétence existe et elle **n'est pas** une trajectoire dirigée. Une politique ayant
> compris la tâche serait à 1,5–3× l'optimal.

---

## 4. 🔴 L'anomalie qui a failli passer : le témoin « neuf » est inutilisable

Le cerveau **neuf (Xavier)** de A_g66 a fait **22,67 %** — 4× le hasard. Un réseau non
entraîné ne devrait rien savoir.

Vérification : **un réseau Xavier a un biais d'action arbitraire selon sa graine.**

| `dim_bus` | Action favorite | Part des ticks | Entropie |
|---:|---:|---:|---:|
| 132 | 2 (avancer) | 42,2 % | 1,269 |
| 145 | 1 (tourner) | 70,0 % | 0,967 |
| 158 | 6 (done) | **87,0 %** | 0,524 |

Ce n'est pas une politique : c'est un déséquilibre aléatoire des poids. Celui de g66 est
tombé sur un biais favorable à l'exploration.

**Conséquence de protocole** : le témoin « neuf » est une **variable aléatoire à variance
énorme** (4,33 % · 5,67 % · 7,00 % · 22,67 %) et **une seule initialisation par cerveau ne
le représente pas**. Le comparer à un tirage unique est une faute.

✅ Le témoin **aléatoire** est stable : **17/300 sur les quatre runs** (mêmes graines de
carte ⇒ mêmes cartes). C'est lui la référence de ce banc.

---

## 5. 🟡 Le fait non expliqué — et le confondage qui a failli me tromper

Le succès au banc est **inversement ordonné** à la maîtrise en run :

| | Maîtrise run | Banc |
|---|---:|---:|
| A_g155 | **45,0 %** | **7,67 %** |
| A_g122 | 35,0 % | 27,33 % |
| A_g66 | 30,0 % | 37,33 % |
| A_g166 | 25,0 % | 31,00 % |

`r(maîtrise, banc) = −0,8873`, `t = −2,72`, **n = 4** — seuil à 4,30, donc **NON
significatif**.

> ⚠️ **Un confondage a failli produire une fausse découverte.** Sur les **trois premiers**
> cerveaux, `dim_bus` valait 145 · 137 · 132 — décroissant **exactement** dans l'ordre du
> succès. `r(dim_bus, maîtrise)` valait **+0,99** : les deux variables étaient
> **indiscernables**, et j'allais annoncer que la maîtrise ne mesure rien.
> Le **quatrième** cerveau (bus 158, succès le plus haut) a cassé le confondage :
> `r(dim_bus, banc)` est tombé de **−0,97 à +0,16**. La taille n'explique rien ;
> l'inversion, elle, survit.

**Ce que cela vaut** : rien encore. `n = 4` est très loin des 20 graines exigées. Le motif
est frappant et monotone, mais quatre points font une impression, pas une mesure.

**Ce que cela vaudrait si confirmé** : `historique_episodes_niveau` — la maîtrise qui
déclenche les promotions et à laquelle **dix-huit hypothèses ont été corrélées** — ne
mesurerait pas la compétence. Toutes ces réfutations auraient utilisé la mauvaise variable
de sortie. C'est testable en ~2 h sur 16 cerveaux de plus.

---

## 6. Limites du banc — à lire avant d'en tirer quoi que ce soit

| Limite | Effet |
|---|---|
| **Vecteur bio figé** au régime neutre | en run il évolue (faim, énergie, odorat) : l'agent est privé de signal métabolique variable |
| **Aucun apprentissage** (`eval()`) | mesure la politique gelée, pas la dynamique |
| **Patience** = `max_steps` par défaut | en run l'agent abandonne vers ~258 ticks — le banc lui accorde *plus* de temps |
| `n = 4` cerveaux | sous la barre des 20 ; puissance insuffisante sous ~3 points d'écart |

⚠️ **Deux versions antérieures de ce banc ont été jetées**, pour deux biais trouvés en les
cherchant : (1) un **vecteur bio nul** alors que cinq dimensions ont un neutre à **0,5**
(clinotaxie v32.0, thermique v41.11, rappel marquant v36.0) — des zéros font croire à
l'agent qu'il est affamé et en fuite permanente ; (2) une **fuite de mémoire de travail**
entre épisodes (un `reset()` écrit mais jamais appelé) et un **contexte épisodique nul** là
où le run utilise `contexte_vide()` puis une moyenne glissante. Tous les chiffres produits
avant ces correctifs sont **caducs**.
