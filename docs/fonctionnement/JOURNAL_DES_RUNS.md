# Journal des runs — une ligne par campagne, écrite AU LANCEMENT

> **Règle de trace, quatrième volet** (posée le 07/09/2026, demande utilisateur).
> Le `LISEZ_MOI.md` de campagne porte le **protocole** ; ce journal porte le **calendrier**.
> Les deux sont obligatoires, et tous deux s'écrivent **avant** que le premier run démarre.
>
> ⚠️ **Pourquoi ce fichier existe** : le 07/09, la campagne des branches persistantes avait
> son protocole complet mais **aucun horodatage versionné** — début, fin estimée et fin
> réelle n'existaient que dans les métadonnées du système de fichiers, qui ne survivent ni à
> un `git clone` ni à une copie. Et l'estimation annoncée à l'oral (« ~2 h ») s'est révélée
> fausse d'un facteur 3 : la mesure du rythme réel donnait **~6 h**. Un écart de cette taille
> est invisible sans trace écrite.

## Comment remplir une ligne

| Champ | Règle |
|---|---|
| **Titre** | le nom de la campagne, pas la conclusion espérée |
| **Début** | `date "+%Y-%m-%d %H:%M"` au moment du lancement, jamais reconstruit après coup |
| **Fin estimée** | dérivée du **rythme mesuré** après ~30 min, jamais devinée à l'avance |
| **Fin réelle** | remplie à la fin ; l'écart avec l'estimation est une information |
| **Pourquoi** | la question posée, en une phrase, telle qu'elle a été formulée |
| **Statut** | 🟡 en cours · ✅ terminée · ❌ échouée/annulée |

⚠️ **Une campagne annulée reste au journal**, avec la raison. Le 05/09, une campagne audio de
8 h a été annulée par son propre pré-vol : c'est ce genre d'entrée qui évite de la relancer.

---

## Runs

### ✅ `08092026_sci01_balayage_K` — Wave 1 : balayage K/ε sur l'apprenant réparé

| | |
|---|---|
| **Début** | 2026-09-08 (v41.68) |
| **Fin estimée** | ~18-22 h *(Wave 1 : 60 runs × 1500 j, 6 en parallèle — rythme mesuré sur le pré-vol 2 nuits)* |
| **Fin réelle** | 2026-09-09 ~18:55 — **60/60 runs, 0 échec** (écart ~×2 sur l'estimation : les bras lourds K16/K8_CLIP sont ~2× plus lents que K1-K8, rythme mesuré ~2,7 j/min K16 · ~5,8 j/min K8_CLIP) |
| **Coût** | Wave 1 : 6 bras × 10 graines × 1500 jours · Wave 2 (différée) : n=20 ciblé (graines 122→222) |
| **Statut** | ✅ Wave 1 terminée et **dépouillée** (09/09) — verdict final en attente de la Wave 2 (n=20) |

**Pourquoi** : le point K=8 du 07/09 a été mesuré avec le **rejeu faussé** (APP-01) — il
n'est plus un témoin valide. Le balayage re-mesure la **forme** de l'effet de K (2/4/8/16)
et le signe du clip (ε = 0,2 à K=8) sur le socle sain (voix libre + `--detach-c2` constants
sur tous les bras, témoin K=1 inclus). Indicateurs clés extractibles des logs : maîtrise,
niveau, **distribution du ratio `exp(lp − lp_old)` et fraction clippée** (ligne console
`Rejouer (v41.68)`, v41.64/68).

**Pré-vol (08/09)** : manifeste validé (format strict MES-01) · 2 nuits réelles K8_NU :
exit 0, 2 bilans, **0 violation** du garde de parité de forme, 2 lignes `Rejouer` ;
drapeau `[VARIANTE] 8 epoques` présent.

**Résultat Wave 1 (dépouillement strict 09/09, n=10 par bras — voir le
[carnet](../recherche/campagnes/SCI01_WAVE1_09092026_la_forme_en_cloche.md))** :
franchissements du mur `SimpleCrossingS9N1` → `LavaGapS5` : **0/10 · 0/10 · 8/10 · 10/10 ·
3/10** pour K = 1, 2, 4, 8, 16 — **forme en cloche, optimum K=8**. Le clip ε=0,2 **ne nuit
plus** (K8_CLIP_e02 = 10/10 ; fraction clippée ~8 % — clip quasi inerte car le ratio est
déjà sain). ⚠️ Aucun `t` ne passe Bonferroni à n=10 ; le juge maîtrise est confondu par le
palier — le niveau porte la réponse. Wave 2 (graines 122→222) requise pour le verdict final.

[Protocole](../../brains/08092026_sci01_balayage_K/LISEZ_MOI.md) ·
[Dépouillement Wave 1](../../brains/08092026_sci01_balayage_K/depouillement_wave1.txt)

### 🟡 `08092026_sci01_balayage_K` — Wave 2 : n=20 ciblé (graines 122→222)

| | |
|---|---|
| **Début** | 2026-09-09 (v41.68 — même code que la Wave 1, aucun changement de logique depuis) |
| **Fin estimée** | ~40-45 h *(dérivée du rythme mesuré Wave 1 : ~43 h pour 60 runs, bras lourds dominants)* |
| **Fin réelle** | — |
| **Coût** | 6 bras × 10 graines (122, 133, 144, 155, 166, 177, 188, 199, 211, 222) × 1500 jours |
| **Statut** | 🟡 en cours |

**Pourquoi** : compléter la cohorte à **n=20 par bras** (règle cardinale : aucun test formel
sous 20 graines). La Wave 1 (n=10) a montré une **cloche 0/0/8/10/3** (optimum K=8) et un
**clip inerte** (~8 % de fraction clippée) — la Wave 2 absorbera la variance inter-individuelle
et tranchera si K=8 est le socle moteur, au dépouillement final sur `manifeste.json` (20
graines).

**Pré-vol** : aucun nouveau nécessaire — code identique à la Wave 1 (le seul commit sur
`noyau.py` depuis, ARC-01 `7849f4d`, ne touche que des commentaires d'en-tête) ; pré-vol Wave 1
(manifeste validé, 2 nuits K8_NU exit 0, garde de parité 0 violation) déjà couvert.

[Protocole](../../brains/08092026_sci01_balayage_K/LISEZ_MOI.md)

#### 🗒️ Point d'étape — 08/09/2026 09:37 (24 runs terminés / 60)

**Avancement** : K1_TEMOIN **10/10** · K2_NU **10/10** · K4_NU **4/10** (g11, g22, g33, g44) ·
K8_NU / K16_NU / K8_CLIP_e02 non lancés. 0 échec sur les 24 runs terminés.

**Premières mesures directes (fin de run, aucun `t` — cohorte incomplète, pas de verdict)** :

- **K1_TEMOIN** : maîtrise finale moyenne **11,5 %** (médiane 12,5, min 5, max 20) · niveau
  4/15 partout · **0/10** franchissements.
- **K2_NU** : maîtrise finale moyenne **13,0 %** (médiane 15,0, min 5, max 20) · niveau 4/15
  partout · **0/10** franchissements.
- **K4_NU** (4 terminés) : **3/4** au niveau 5/15 (`LavaGapS5`, l'étage au-delà du mur
  `SimpleCrossingS9N1` — g11, g33, g44) · g22 reste en 4/15 (maîtrise 30 %). Signal précoce
  cohérent avec l'effet seuil de K=8 du 07/09, mais **n=4 = anecdote statistique** : rien ne
  sera calculé avant les 10 runs du bras.

**⚠️ Réserve méthodologique — Juge 4 (mécaniste, ratio/clippés) sur les bras NU** : dans
`noyau.py`, `ratios_epochs` n'est rempli que si `RATIO_CLIPPE_ACTIF` (`~2224`) — les bras NU
(K1→K16) ne loguent donc que `parité max · entropie moy` en console, et W&B étant offline,
la distribution du ratio n'est **pas** consignée sur disque pour eux. Seul K8_CLIP_e02 (non
lancé) portera la télémétrie ratio/p90/fraction clippée dans cette Wave 1. Acté : pas de
modification de code pendant que la campagne tourne ; correction prévue pour la Wave 2
(observation pure du ratio sur tous les bras, `RATIO_CLIPPE_ACTIF` inactif compris).

#### 🗒️ Point d'étape — 09/09/2026 15:42 (55 runs terminés / 60 — bras K16 et K8_CLIP en cours de bouclage)

**Avancement** : K1_TEMOIN 10/10 · K2_NU 10/10 · K4_NU 10/10 · K8_NU 10/10 · **K16_NU 10/10**
(terminé ~15:20) · **K8_CLIP_e02 5/10** terminés + 5 en cours (g66 ~1457 j, g77 ~682, g88 ~211,
g99 ~197, g111 ~92). 0 échec sur les 55 runs terminés.

**Forme provisoire des franchissements du mur `SimpleCrossingS9N1` → `LavaGapS5` (comptage
sur bras complets — AUCUN test, le dépouillement MES-01 attendra `WAVE 1 TERMINEE`) :**

| K | Franchissements / 10 | Lecture |
|---|---|---|
| K=1 | 0/10 | sous le seuil |
| K=2 | 0/10 | sous le seuil |
| K=4 | 8/10 | saut de phase |
| K=8 (nu) | 10/10 | maximum apparent |
| K=16 | **3/10** | retombée — **forme en cloche, optimum ~K=8** |
| K=8 + clip ε=0,2 | **5/5 sur terminés** | ⚠️ signal **renversé** vs 07/09 (où le clip « nuisait ») — maîtrises 15-35 %, plus saines que K8_NU pur (souvent 0-10 %) |

⚠️ **K8_CLIP inverse la conclusion du 07/09** (le « clipping nuit » avait été mesuré nuisible à
−1,00 pt sur le rejeu faussé) : sur le socle réparé, 5/5 des terminés franchissent avec des
maîtrises finales élevées. **n=5, pas de verdict** — mais c'est le fil le plus chaud du
dépouillement à venir. L'estimation de lancement (~18-22 h) est **dépassée d'un facteur ~2**
(rythme réel des bras lourds : ~2,7 j/min K16 · ~5,8 j/min K8_CLIP) — écart consigné, la fin
réelle sera reportée dans l'en-tête de campagne.

---

### ✅ `07092026_protoA_ppo_seuil60` — PPO face à la règle 60 % du cursus

| | |
|---|---|
| **Début** | 2026-09-07 18:13 |
| **Fin estimée** | ~18:50 *(dérivée du pré-vol A/A : 2 × 20 k pas en ~1 min, dont import torch)* |
| **Fin réelle** | 2026-09-07 ~18:15 — 5/5 runs terminés, **0 échec** |
| **Coût** | 5 runs PPO × 152 043 pas (arch [69,69]) · **banc** — zéro ligne de `noyau.py` |
| **Statut** | ✅ terminée |

**Écart estimé / réel** : ~35 min d'avance — l'estimation dérivée du pré-vol sur-comptait
l'import torch ; 5 runs PPO en parallèle sur `mps` ≈ 2 min de calcul réel.

**Pourquoi** : le seuil de promotion (`TAUX_PROMOTION` = 60 % × 20 épisodes) est au-dessus de
ce que PPO atteint (36-40 %) sur `SimpleCrossingS9N1` — le mur du niveau 4 est-il en partie
une **règle du cursus** ? Le banc capture le vecteur binaire victoire/défaite épisode par
épisode pendant l'entraînement → fenêtres glissantes ≥ 12/20 **et** route série (2 victoires
consécutives, l'autre branche du OU).

**Pré-vol (18:13)** : A/A 2 × 20 k pas — **vecteurs bit-identiques** (64 épisodes ×2) :
la capture est valide.

**Résultat ([carnet](../recherche/campagnes/PPO_AU_SEUIL_07092026_la_porte_60_n_est_pas_le_mur.md))** :
**2/5 graines** passent au moins une fenêtre ≥ 12/20 (g11, g33 — celles qui convergent à
~45-50 %) → verdict pré-enregistré : **le seuil 60 % n'est pas à lui seul le mur, le goulot
est l'apprenant**. Route série : **4/5 graines** déclenchent la voie des 2 victoires
consécutives (jusqu'à 47 occurrences) → un PPO dans le cursus (OU) ne resterait pas bloqué
par la porte 60 %. ⚠️ n = 5, arch 69 seul, deux graines (g22, g44) convergent mal —
instabilité de PPO lui-même, pas du script.

[Protocole complet](../../brains/07092026_protoA_ppo_seuil60/LISEZ_MOI.md)

---

### ✅ `07092026_branches_persistantes` — les branches persistantes du rollout

| | |
|---|---|
| **Début** | 2026-09-07 09:03 |
| **Fin estimée** | 2026-09-07 ~15:15 *(mesurée sur le rythme réel à 09:35 : 8,7 % en 32 min)* |
| **Fin réelle** | 2026-09-07 ~16:05 — 20/20, « CAMPAGNE TERMINEE », **0 échec** |
| **Coût** | 20 runs × 1500 jours, 6 en parallèle |
| **Statut** | ✅ terminée |

**Écart estimé / réel** : ~50 min de retard — le rythme **ralentit** en fin de course (les
cerveaux grossissent) : c'est exactement l'information que la règle « fin estimée mesurée »
voulait capturer.

**Pourquoi** : les 8 branches du rollout mental perdent **97 % de leur séparation** avant
l'horizon 7 — C2 n'évalue pas 8 plans, il évalue **une destination** vue de 8 départs. La
cause est `argmax(tete_motrice)`, pas JEPA (h7/h1 = 1,15 à action répétée contre 0,043).
Cette campagne teste si rendre les branches persistantes change quelque chose au
comportement — c'est le **prérequis** de la tête d'intention de C2 (v42).

**Prédiction écrite d'avance** : effet comportemental **peu probable**. C2 est mesuré inerte
et son gradient nuisait ; `r(ratio rollout, maîtrise) = −0,08`. Un juge 3 qui passe avec un
juge 1 nul serait **acceptable** — la mécanique marcherait sans que C2 sache s'en servir.

**Résultat (dépouillé le 07/09 soir — [carnet](../recherche/campagnes/BRANCHES_PERSISTANTES_07092026_la_mecanique_marche_la_voix_reste_inerte.md))** :
conforme à la prédiction. Juge 3 (mécaniste) **passe massivement** — h7/h1 médian
**0,0073 → 1,01**, log10 apparié `t` = **+18,76** (20/20, survit aux extrêmes à +19,31 ;
🔴 requalifié le 08/09 par la sonde MES-02, contexte et corps réels — CHANGELOG [v41.66]) ;
juges 1 (maîtrise δ **−2,10 pt**, NS), 2 (niveau 7/20 vs 5/20, Fisher `p` = 0,73) et 4 (accord,
NS) **nuls**. Sortie brute : `depouillement_BP.txt` · agrégat : `agregat_BP.json`.

[Protocole complet](../../brains/07092026_branches_persistantes/LISEZ_MOI.md)

---

### ✅ `06092026_epoques_nuit` — les époques de la nuit

| | |
|---|---|
| **Début** | 2026-09-06 ~22:00 |
| **Fin réelle** | 2026-09-07 ~00:30 *(~2 h 30, 3 bras)* |
| **Coût** | 40 runs neufs × 1500 jours, 6 en parallèle · **0 échec** |
| **Statut** | ✅ terminée |

**Pourquoi** : la politique ne recevait qu'**un seul pas de gradient par journée** de
400 ticks, contre 23 680 pour PPO sur le même banc. Un pas déplace les logits de 0,0107 pour
une marge de 0,392 : il en faudrait **~37** pour changer une décision.

**Résultat** : maîtrise **8,75 % → 19,00 %** (δ +10,25 pt, `t` = +4,81, 15/20, survit aux
extrêmes) et **5 cerveaux sur 20 franchissent le niveau 5**. 🔴 Le clipping de PPO **nuit**,
à l'inverse de l'attente théorique. [Carnet](../recherche/campagnes/EPOQUES_07092026_le_mur_du_niveau_4_est_franchi.md)

---

### ✅ `05092026_detach_c2` — le gradient fantôme de C2

| | |
|---|---|
| **Début** | 2026-09-05 23:09 |
| **Fin réelle** | 2026-09-06 ~07:00 *(~8 h)* |
| **Coût** | 20 runs neufs × 1500 jours, 6 en parallèle · **0 échec** |
| **Statut** | ✅ terminée |

**Pourquoi** : lever la réserve écrite dans le carnet de l'ablation C2 — sa *voix* est inerte,
mais son *gradient* irrigue encore `integrateur_bio`, la couche partagée.

**Résultat** : **+5,25 pt** de maîtrise (`t` = +4,97, 16/20, survit aux extrêmes). Prédiction
« probablement rien » **réfutée**. [Carnet](../recherche/campagnes/DETACH_C2_06092026_le_gradient_fantome_nuisait.md)

---

### ✅ `06092026_ppo_lavagap` — PPO au niveau du mur

| | |
|---|---|
| **Début** | 2026-09-06 ~00:30 · **Fin** ~01:10 *(~40 min)* |
| **Coût** | 5 graines + A/A + témoin aléatoire |
| **Statut** | ✅ terminée |

**Pourquoi** : la baseline « le mur n'existe pas » avait été mesurée au niveau **3**, que
Naulthène franchit — jamais au niveau **4**, où 40 runs sur 40 s'arrêtent.

**Résultat** : PPO résout `LavaGapS5` à **97,27 %** contre 6,67 % pour un marcheur aléatoire.
🔴 **RECTIFIÉ le 07/09 — mauvaise carte** : « Niveau 4/15 » est `SimpleCrossingS9N1`, pas
`LavaGapS5` (le log affiche `niveau_actuel + 1`). Ce banc a testé **une carte plus loin**
que le blocage. Sur la vraie carte du mur : PPO **36–40 %** contre **25,83 %** — ~1,5×. [Carnet](../recherche/campagnes/PPO_LAVAGAP_06092026_le_mur_n_est_pas_la_carte.md)

---

### ❌ `05092026_audio` — l'ablation de l'hémisphère audio (ANNULÉE)

| | |
|---|---|
| **Début** | 2026-09-05 · **Fin** : annulée avant lancement |
| **Coût évité** | **~8 h** |
| **Statut** | ❌ annulée par son propre pré-vol |

**Pourquoi elle devait tourner** : 19 % du réseau alloué à l'audio pour un terme `Vocal` à
σ = 0,0000 sur un cursus spatial.

**Pourquoi elle a été annulée** : le run `--sans-audio` est sorti **bit-identique** au bras de
référence. Cause mesurée sur 80 cerveaux : **aucune synapse audio n'a jamais reçu de
gradient** — geler un membre déjà gelé ne change rien. Une ablation **vide**, pas négative.
[Carnet](../recherche/enquetes_closes/AUDIO_05092026_un_hemisphere_deja_gele.md)

---

*Une campagne sans ligne ici n'a pas eu lieu.*
