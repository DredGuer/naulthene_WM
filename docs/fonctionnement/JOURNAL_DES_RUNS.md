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
**0,012 → 1,28**, log10 apparié `t` = **+10,55** (19/20, survit aux extrêmes) ; juges
1 (maîtrise δ **−2,10 pt**, NS), 2 (niveau 7/20 vs 5/20, Fisher `p` = 0,73) et 4 (accord,
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
