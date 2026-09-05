# NEUROSCIENCES DÉVELOPPEMENTALES — ce que Naulthène modélise, et les contresens

**Date** : 2026-09-05 · **Statut** : 🟡 **IDÉES** — non validé, sauf les 2 blocs marqués ✅
mesurés · Suite de
[`05092026_anatomie_comparee`](../etat_des_lieux/05092026_anatomie_comparee_cerveau_humain.md).

> Analyse proposée par l'utilisateur (développement individuel, relation parent-enfant,
> hérédité). Deux de ses pistes étaient **mesurables sur les données existantes** : elles le
> sont ci-dessous. Le reste demeure hypothèse.

---

## 1. ✅ MESURÉ — L'élagage n'existe pas : **0 synapse morte sur 259 329**

La piste la plus forte de l'analyse, et la mesure la confirme.

| Grandeur (cerveau `LIBRE_SANS_C2_g11`, 1500 j) | Valeur |
|---|---|
| Synapses de base | 259 329 |
| **Synapses mortes** (`|w| < 1e-8`) | **0 — 0,000 %** |
| Synapses cristallisées | 3 198 — **1,233 %** |

**Chez l'humain, 40 à 50 % des synapses sont éliminées pendant le développement. Chez
Naulthène : aucune.**

🔴 **Cause mécanique, et elle est structurelle** : l'érosion nocturne est **géométrique**
(`base *= 1 − λ(1 − myéline)`) — elle fait *tendre* vers zéro sans jamais y arriver — et le
**plancher vital** (`PLANCHER_POIDS_VITAL`) l'en empêche explicitement. Ce plancher n'est pas
un défaut : sans lui, un agent sans récompense s'érode à taux plein et **meurt en ~121 nuits**
(mesuré, v34.0-fix1). Il protège la survie **au prix de l'élagage**.

> **Une synapse inutile coûte donc éternellement.** C'est un écart réel avec la biologie, et
> il est *structurel*, pas accidentel.

⚠️ **Mais aucune mesure ne dit que l'élagage aiderait.** Le lien « pas d'élagage → plafond »
n'est **pas établi** — c'est précisément l'erreur que le dépôt a commise 24 fois.

## 2. ❌ RÉFUTÉ — « le cerveau obèse » : le bus n'est pas corrélé négativement à la réussite

L'analyse suppose que l'inflation dimensionnelle (16 → 159) étouffe l'agent. **Mesuré sur les
18 runs complets** de la campagne en cours :

| Test | `r(dim_bus, maîtrise)` | `t` |
|---|---|---|
| Brut | **+0,4991** | +2,30 |
| Conditionné (a gagné) | +0,4991 | +2,30 |
| Sans les 4 extrêmes | +0,5397 | +2,22 |
| **bras LIBRE_SANS_C2** | **+0,5644** | +1,81 |
| **bras TEMOIN_SANS_C2** | **−0,2235** | −0,61 |

Le signe est **positif**, à l'inverse de l'hypothèse. **Mais il ne survit pas non plus** :

🔴 **`r(dim_bus, victoires cumulées) = +0,6780` (`t` = +3,69) — plus fort que la maîtrise.**
La neurogenèse est déclenchée par un thermostat d'erreur JEPA : un agent qui vit et joue plus
d'épisodes a simplement **plus d'occasions de grandir**. Le bus mesure donc surtout la
**survie**, pas la compétence.

🔴 **Le signe s'inverse entre bras** (+0,56 / −0,22) — signature exacte de la curiosité
(v41.x, +0,23 / −0,26) et de `maîtrise ~ énergie` (+0,710 à n=10 → −0,0588 à n=20).

**Verdict : ni « l'obésité nuit » ni « la croissance aide » n'est établi.** À n=18, aucun `t`
ne passe Bonferroni (2,86). ⚠️ **Ne pas conclure dans un sens ni dans l'autre.**

✅ **Ce qui reste acquis, et qui est ancien** : élargir le bus à 160 ou 512 dimensions n'a
**jamais franchi un palier** et alourdit le métabolisme basal. L'échelle ne débloque rien.

## 3. Ce que l'analyse dit juste, sans mesure nouvelle

| Point | Statut |
|---|---|
| **Myélinisation `W_base` + `W_annexe`** — jour plastique / nuit consolidante | ✅ conforme, c'est le mécanisme réel |
| **Empreinte développementale précoce** | ✅ **confirmé le 05/09** — les 3 témoins bloqués atteignent le niveau 1 au **jour 2-3** et n'en repartent jamais sur 1497 jours ([ATROPHIE](../recherche/campagnes/ATROPHIE_05092026_la_boucle_de_compensation.md)) |
| **L'assistanat atrophie** (parent nourricier v38-2c : mémoire ÷6) | ✅ déjà mesuré, à préserver |
| **Hériter `W₀`, jamais l'expérience finie** | 🟡 principe retenu, **jamais testé** |

⚠️ **Nuance sur l'empreinte précoce** : ce n'est **pas** la « loterie natale g22 » — cette
lecture est **périmée depuis le 20/08/2026** (campagne v41.29 : 10/10 graines au niveau 4).
Ce qui est vrai est que *certains* cerveaux se figent au jour 2-3, pas que la graine décide
tout.

## 4. 🔴 La contrainte que toute proposition doit franchir

Le tableau de l'analyse propose « privilégier la taille fixe avec élagage dense ». Avant
d'écrire une ligne de code, trois obstacles mesurés :

1. **Le plancher vital ne peut pas être retiré** : 6 couches sur 11 y sont collées sur un run
   réel, et sans lui l'agent meurt en 121 nuits.
2. **Deux ajouts passifs en queue du vecteur bio = deux effets nuls à n=20.** Tout mécanisme
   nouveau doit passer **ailleurs** que par une dimension diluée dans `integrateur_bio`.
3. **24 explications du plafond mesurées puis réfutées.** Une hypothèse séduisante et non
   mesurée a une probabilité empirique élevée d'être fausse **sur ce dépôt précisément**.

## 5. Ce qui serait mesurable, et à quel coût

| Piste | Test | Coût |
|---|---|---|
| **Élagage dur** | seuil d'élimination définitive sous X % de la norme de couche, témoin apparié | 20 paires, ~8 h |
| **Bus plafonné** | `dim_bus` figé à 64 contre neurogenèse libre | 20 paires, ~8 h |
| **Hérédité `W₀`** | lignées sur N générations, sélection par surplus énergétique | campagne longue, non chiffrée |

⚠️ **Aucune n'est justifiée tant que l'ablation C2 en cours n'a pas rendu son verdict** — elle
décide si le délibératif est cassé ou seulement bridé, ce qui réordonne toute la suite.

---

*Idées, pas résultats. Les deux blocs ✅/❌ sont mesurés ; le reste attend un protocole.*
