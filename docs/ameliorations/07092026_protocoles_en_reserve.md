# Protocoles en réserve — à lancer après la campagne `branches_persistantes`

**Date** : 2026-09-07 · **Statut** : 📋 **en réserve — rien n'est lancé** · **Nature** :
propositions non validées (dossier `docs/ameliorations/`), document de décision écrit à la
demande de l'utilisateur après le [point général du 07/09](../etat_des_lieux/07092026_point_general_et_direction.md).

> Ce document gèle les **protocoles** (question, bras, juges, règle de décision) discutés le
> 07/09 — après l'évaluation d'une stratégie « tout retirer » proposée le même jour. Il ne
> change rien au cerveau. La référence factuelle reste le
> [CHANGELOG](../fonctionnement/CHANGELOG.md) et le [journal des runs](../fonctionnement/JOURNAL_DES_RUNS.md).

---

## 0. Contexte de décision — instantané au 07/09 ~12:00

| Fait mesuré | Référence |
|---|---|
| **Les 3 seuls leviers qui aient marché** (03→07/09) sont des corrections de l'apprenant : voix libre (`gain_c1 ≡ 1`), `--detach-c2` (+5,25 pt), `--epoques-nuit 8` (+10,25 pt, 5/20 promus) | point général §3.1 |
| Le mur affiché « Niveau 4/15 » est **`SimpleCrossingS9N1`** (off-by-one corrigé le 07/09 — il n'a jamais été `LavaGapS5`) | point général §2 |
| PPO sur cette carte : **36–40 %** à 152 k pas contre **25,83 %** pour les cerveaux — l'écart au mur est **~1,5×**, pas 14,6× | point général §2.3 |
| Le seuil de promotion **60 % × 20 épisodes** est **au-dessus de ce que PPO atteint** sur cette carte à ce budget → le mur est **en partie une règle du cursus** | point général §2.3.2 |
| …mais le seuil est **atteignable par un apprenant réparé** : les 5 promus K8_NU le sont passés **par la voie maîtrise** (60 % × 20), jamais par les 2 victoires | point général §1.2 |
| La politique de C1 est **plate** : ratio var inter/intra = 3,91 (vs 0,06 chez PPO) — décidée par des biais, pas par l'état | `PLATITUDE_06092026` |
| **56 % des neurones** de `pensee_bio` sont morts (activations à zéro, 40/40) — cause **non** départagée (init ? érosion ? déclencheur ?) | `PLATITUDE_06092026` §3 |
| Les réfutations d'avant le 03/09 ont été mesurées **sous les 3 pathologies actives** (1 pas/nuit, gradient C2 parasite, renormalisation C1) → **faux négatifs candidats** | point général §3.2 |

### Ce qui est tranché — à ne pas re-tester

| Piste | Verdict (n, date) |
|---|---|
| Sens secondaires coupés (ouïe, goût, odorat, Exo-Sens) | 0,0 pt chacun au banc d'ablation (78 cellules) — à re-tester **sous le meilleur régime**, pas à couper au hasard |
| Métabolisme comme cause du plafond (`maîtrise ~ énergie`) | rétracté : +0,710 (n=10) → **−0,0588** (n=20, 29/08) |
| « L'agent optimise un barème » comme explication causale | tautologie (17ᵉ réfutation) — le descriptif tient (95,6 % du signal des constantes posées), le causal non |
| « Le plafond est une pathologie de l'architecture » (formulation forte) | **plus fort que ce qui est mesuré** — le seuil 60 % est aussi en cause (point général §2.3.2) |
| Geler la mémoire de travail « aide » | vrai au banc (4/6 niveaux) mais sans levier comportemental mesuré |
| La douleur (v41.25-27) | 0 pt (`t` = −1,51, n=20) — la peur seule ne produit pas la compétence |

---

## 1. Protocole A — PPO à budget égal face à la règle du cursus

**Question** : le mur est-il la **règle du cursus** (seuil 60 % × 20 inatteignable), la **carte**, ou le **cerveau** ?

**Pourquoi maintenant** : c'est la mesure manquante du point général §5.2. Elle borne toute décision sur `TAUX_PROMOTION` (proposition de le baisser à ~35 % le 07/09) — et elle n'exige **aucun changement du cerveau**.

**Design** (banc, pas de run d'entraînement) :
- PPO `MlpPolicy` sur **`SimpleCrossingS9N1`** (la vraie carte du mur), **600 k pas**, 5 graines, observation aplatie 7×7×3, 7 actions, récompense brute — comme la baseline du 29/08 mais à budget égal à une vie (~600 k pas).
- Compter, sur chaque graine : combien de **fenêtres glissantes de 20 épisodes consécutifs passent 60 %** (la règle exacte de promotion de `noyau.py` : `TAUX_PROMOTION` = 0,60, `FENETRE_PROMOTION` = 20, `MIN_EPISODES_PROMOTION` = 10).
- Témoins : marcheur aléatoire (5,67 %, invariant), A/A.

**Juges** :
1. PPO passe-t-il 60 % × 20 (au moins une fois, sur combien de graines) ? → **oui** : le seuil n'est pas le mur, ne pas y toucher, le goulot est l'apprenant. → **non** : le seuil est une vraie porte, le débat « baisser TAUX_PROMOTION » s'ouvre **sur preuve** (attention : `TAUX_PROMOTION` dérive `SEUIL_MATURITE`, le début de sevrage, la croissance P17 — ne pas le toucher isolément).
2. PPO atteint-il ~40 %+ de réussite à ce budget ? → confirme la carte n'est pas le blocage.

**Coût** : ~1 h · **Pré-vol** : comparer deux runs (δ_A/A = 0,000000).

---

## 2. Protocole B — Balayage K et ε autour du point K8

**Question** : quelle est la **forme** de l'effet « époques de la nuit » avant de le dériver (méthode v30.1 : mesurer le fixe d'abord) ?

**Pourquoi** : `K = 8, ε = 0,2` est **un seul point mesuré** (07/09, le plus fort résultat du dépôt). Le clipping PPO « nuit » à ε = 0,2 pourrait simplement **ramener K8 vers K1** (un `lr` calibré pour 1 pas) — ce n'est pas la même chose que « nuire ».

**Design** : 20 graines appariées × 1500 jours, régime voix libre + `--detach-c2`, cerveaux neufs.
- Bras K : {2, 4, 16, 32} (+ témoin réutilisé K8_NU du 06/09, avec test bit-identique consigné au journal des runs).
- Bras ε (clipping) : {0,5 ; 1,0} à K = 8.

**Juges posés d'avance** (Bonferroni 3 métriques ⇒ `t` = 2,86) :
1. **Maîtrise** : δ > 0 vs témoin, survit au retrait des 4 extrêmes.
2. **Niveau** : franchissement, Fisher bras par bras.
3. **Forme** : l'effet est-il **monotone** en K, sature-t-il, ou **se retourne-t-il** (sur-apprentissage d'une journée de 400 ticks) ? C'est la donnée qui permettra de **dériver** K de la plasticité au lieu de le poser.
4. **Mécaniste** : entropie de C1 (le juge qui a échoué pour K8_NU — `t` = −2,47, NS).

**Coût** : 2 × ~6 h · **Règle** : ne pas publier de `t` sur un run en cours (leçon du 31/08).

---

## 3. Protocole C — Banc moteur minimal sous régime réparé

**Question** : la politique **dépend-elle de l'état** ? (la version mesurable de « sait-il marcher droit ? »)

**Pourquoi** : la platitude de C1 est le mécanisme le mieux établi des 06-07/09 — la décision est dictée par des biais moyens, pas par l'état (ratio inter/intra **3,91 vs 0,06** chez PPO, σ temporel d'un logit 0,108 vs 2,923). Les victoires browniennes (14–18× le plus court chemin) en sont le symptôme. C'est un **banc de diagnostic**, pas une modification du cerveau.

**Design** (sondes + bancs, zéro run d'entraînement) :
- Lire les métriques de platitude sur les cerveaux du **meilleur régime connu** (K8_NU aujourd'hui ; BP s'il passe ses juges) : variance inter-actions vs intra-temps, σ temporel d'un logit, actions distinctes jouées, entropie.
- **300 épisodes forcés** sur `SimpleCrossingS9N1` **et** sur le niveau suivant (`LavaGapS5`), avec l'**instrument corrigé du 02/09** (mémoire de travail branchée — le banc 30-31/08 lisait le mauvais indice).
- Témoin : PPO sur le même banc.

**Juges** :
1. Le ratio inter/intra **s'approche-t-il** de celui de PPO (~0,1 au lieu de 3,91) ? → si non, le banc re-mesure la platitude : l'apprenant n'est pas réparé, ne pas conclure.
2. **Directivité** ≤ 6× le plus court chemin (la cible fixée avant la campagne directivité).
3. Actions distinctes jouées sur les 7.

**⚠️ Condition** : tourner **sous l'apprenant réparé**, sinon ce banc re-mesure un fait déjà établi. Il ne tranche pas « peut-il apprendre ? » (déjà oui, 15 pts au-dessus du hasard sur `Empty-5x5`) mais « pourquoi sa politique ne bouge-t-elle pas avec l'état ? ».

**Coût** : ~sondes (quasi nul) + bancs (~1-2 h).

---

## 4. Protocole D — Campagne de soustraction (P3, jamais faite)

**Question** : sous le meilleur régime, que **coûte ou apporte** la superstructure (5 sens, corps, C2) à l'apprenant réparé ?

**Pourquoi** : toutes les réfutations d'avant le 03/09 ont été mesurées **avec les 3 pathologies actives** — un organe jugé « sans effet » sur un apprenant qui ne bougeait pas n'a pas été jugé. C'est la mesure la plus informative du dépôt selon le point général §5.4, et la bonne façon de répondre à la stratégie « tout retirer » : **en A/B, jamais en acte de foi**.

**Design** : 20 graines appariées × 1500 jours, sous le **meilleur régime connu** (K8 + detach + voix libre, et K/ε issus du protocole B s'ils sont meilleurs) :
- Bras **minimal** : « vue seule + corps constant + C2 coupé ».
- Bras **complet** (le régime de référence).

⚠️ Si des drapeaux n'existent pas (couper un sens, « corps constant »), les **coder en options** avec vérification **bit-identique** à l'absence de l'option (leçon v41.4 : un drapeau accepté et affiché peut ne rien faire — seul le δ sur deux runs le prouve).

**Juges** (Bonferroni `t` = 2,86) : maîtrise, niveau, **banc final standard** (300 épisodes forcés sur `SimpleCrossingS9N1` et `LavaGapS5`, instrument corrigé).
- Verdict possible 1 : le minimal fait **aussi bien** → la superstructure ne coûte rien mais n'apporte rien : ré-allumer les organes un par un en exigeant un effet ≥ 0.
- Verdict possible 2 : le minimal fait **mieux** → la superstructure coûte : campagne d'élagage ciblée, organe par organe.
- Verdict possible 3 : le complet fait **mieux** → premier effet mesuré d'un organe sur un apprenant qui fonctionne : la thèse respire.

**Peut inclure** : la ré-ablation des 4 sens « sans effet » (ouïe, goût, odorat, Exo-Sens) **sous le meilleur régime** — les faux négatifs candidats de la liste §3.2 du point général.

**Coût** : ~6 h.

---

## 5. Portes de décision — dans l'ordre

| Après… | On décide | Selon |
|---|---|---|
| **Campagne BP** (fin estimée ~15:15 le 07/09) | si la tête d'intention v42 a un canal réparé — dépouiller avec ses 4 juges écrits (maîtrise, niveau, ratio h7/h1, accord C1/C2) ; **juge 3 qui passe + juge 1 nul = acceptable** (la mécanique marche, C2 ne sait pas s'en servir) | `LISEZ_MOI` de la campagne |
| **Protocole A** (~1 h) | toucher ou non à `TAUX_PROMOTION` | PPO passe-t-il 60 % × 20 ? |
| **Protocole B** (2 × 6 h) | la **forme** de K (monotone, saturé, retourné) avant de le dériver | juges 1-4 |
| **Protocole D** (6 h) | si C2 (et les organes) ont une raison d'exister — **avant** de coder la v42 | verdicts 1-3 |
| **Neurones morts** (zéro run d'abord) | si la neurogenèse est un frein (mort à la naissance ou au fil des nuits ? proportion croît-elle avec chaque `agrandir()` ?) | sondes + témoin `dim_bus` figé |

**Ordre recommandé** : A et C peuvent partir dès maintenant (bancs, zéro risque) ; B après A (pour ne pas mélanger deux variables) ; D après B ; la v42 seulement après D.

---

## 6. Résumé de l'évaluation de la stratégie « tout retirer » (07/09)

**Utilisable, reformulé en protocoles ci-dessus** :
- « Savoir marcher droit » → Protocole C (banc moteur minimal), la bonne question étant *la politique dépend-elle de l'état ?*
- « Baisser le seuil de promotion » → Protocole A (mesure d'abord : PPO face à la règle 60 % × 20). Le seuil de 60 % n'est **pas** un « mur mathématique » : il est atteignable par un apprenant réparé (5/20 K8_NU par la voie maîtrise) — baisser à 35 % avant la mesure promouvrait du bruit (3,5 succès sur 10 épisodes à `MIN_EPISODES_PROMOTION` = 10).
- « Retirer le superflu » → Protocole D, en **A/B à n=20**, jamais par principe.

**Écarté** :
- Le chiffre « 98 % du temps à gérer la survie » : **aucune mesure du dépôt ne le soutient** (vrais ordres : Bio = 57 % de la dispersion du gradient vs Env 21,6 % ; 82-87 % des nuits à satiété zéro ; 57,2 % de gestes stériles sur `Empty-5x5`). Et l'hypothèse « le bruit interne explique le plafond » est de la famille des pistes **réfutées** (métabolisme rétracté 29/08 ; barème = tautologie 30/08) — sauf à la reformuler en Protocole D.
- « Éteindre odorat/goût/ouïe/Exo-Sens pour nettoyer » : ces 4 sens sont ceux à **0,0 pt** au banc d'ablation — les couper par principe ne nettoie rien ; les **re-tester sous le meilleur régime** (Protocole D) est la version qui apprend quelque chose.
- « Ne plus toucher à rien d'autre » : geler tout abandonnerait le point chaud du moment — le **balayage K/ε** autour du résultat le plus fort du dépôt (Protocole B).

---

## 7. Règles de mesure applicables à tous les protocoles ci-dessus

1. Protocole écrit **avant** lancement, avec **prédiction explicite** (le dépôt a 3 prédictions « probablement rien » réfutées par la mesure).
2. Ligne au [journal des runs](../fonctionnement/JOURNAL_DES_RUNS.md) **au lancement** (début, fin estimée mesurée après ~30 min, pourquoi).
3. Vérifier que la **variable indépendante varie** avant de lancer (leçon de la campagne tuée du 27/08 : ablation vide).
4. Drapeau : vérification **bit-identique** à l'absence de l'option (leçons v41.4 et v41.62 : un drapeau affiché peut ne rien faire).
5. n ≥ 20 graines appariées · Bonferroni · retrait des 4 extrêmes · A/A sur les bancs.
6. Ne **jamais** publier de `t` sur un run en cours.
7. Ne pas corréler à la maîtrise une métrique dérivée de la récompense (règle anti-tautologie).
8. Garde-fou de forme : **crier** quand il rejette (leçon de l'instrument du banc, 02/09).

---

*Document de décision — 07/09/2026, 12:00. Aucun de ces protocoles n'est lancé. La campagne `07092026_branches_persistantes` tourne (voir journal des runs) et n'est pas jugée ici.*
