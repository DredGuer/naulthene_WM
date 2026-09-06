# CONCEPTION v42 — LA TÊTE D'INTENTION DE C2

**Date** : 2026-09-06 · **Statut** : 🔵 **CHANTIER SPÉCIFIÉ, NON CODÉ** — deux
vérifications à coût nul **doivent passer avant** la première ligne de code (§6).

> Conception proposée par l'utilisateur le 06/09, après le verdict
> [DETACH_C2](../recherche/campagnes/DETACH_C2_06092026_le_gradient_fantome_nuisait.md).
> Les §1 à §4 reprennent sa structure ; les §5 à §7 sont les réserves et les prérequis que
> la lecture du code impose.

---

## 1. Le diagnostic — pourquoi le C2 scalaire a échoué

Trois faits établis, chacun à n ≥ 20 :

| Fait | Mesure |
|---|---|
| **C2 est inerte** | couper sa voix en régime libre : δ = **−1,375 pt** (`t` = −1,15, NS, 5/20), effet minimal détectable 3,42 pt |
| **Son gradient NUISAIT** | le couper de la couche partagée : **+5,25 pt** (`t` = **+4,97**, 16/20, survit aux extrêmes) |
| **L'erreur géométrique** | `cortex_prefrontal : dim_bus → 1` est un **critique**. Un scalaire évalue un état, il ne peut pas désigner une direction |
| **L'erreur d'arbitrage** | `logits_instinct + valeurs × force` : deux voix d'échelles différentes qui s'additionnent |

⚠️ **Correction d'un chiffre souvent cité** : le « **0 % d'accord** entre C1 et C2 » est
**rétracté depuis la v39.0** — c'était un défaut de mesure (le log de nuit écrivait 0 dès la
première divergence). L'accord réel est de **26 à 31 %**, donc **~70 % de désaccord**.
L'argument tient, la magnitude change : ce n'est pas un désaccord *total*.

**L'objectif** : remplacer l'**addition** par une **modulation**. C2 ne crie plus par-dessus
C1 ; il agit comme un filtre attentionnel descendant qui valide ou inhibe les impulsions du
réflexe au vu des futurs simulés.

## 2. L'anatomie — `tete_intention`

| Élément | Décision |
|---|---|
| **Invariant strict** | `cortex_prefrontal` reste **intact** — l'élargir détruirait la ligne de base de l'avantage ([c2-petit-par-construction](../../CLAUDE.md)) |
| **Nouvel organe** | `tete_intention = NaultheneLinearSynaptique(dim_bus, num_actions)` |
| **Ce qu'elle lit** | la `pensee_branche` **finale** de chaque branche du rollout — un tenseur `(A, dim_bus)`, une pensée par action (vérifié `noyau.py:1141`) |
| **Coût** | `dim_bus × num_actions`, soit **1 160 paramètres** à `dim_bus` = 145 — 0,07 % d'un cerveau mûr |

⚠️ **Trois obligations mécaniques** (CLAUDE.md, « Before Modifying Code ») : toute couche
`NaultheneLinearSynaptique` doit être ajoutée dans `__init__`, dans `cycle_sommeil_global()`
**et** dans `declencher_neurogenese()` — en oublier une casse silencieusement le sommeil ou
la neurogenèse pour cette couche. Et `segments_in` doit répercuter les vraies dimensions.

## 3. La modulation — la fin du tir à la corde

```python
portes = torch.sigmoid(self.tete_intention(pensee_branche_finale))   # (A, num_actions)
intention = portes.diagonal()                                        # une porte par action
logits_finaux = voix_c1 * intention                                  # multiplicatif
```

| Porte | Sens physique |
|---|---|
| ≈ **1,0** | C2 valide ce futur — le réflexe de C1 s'exprime librement |
| ≈ **0,0** | C2 anticipe un désastre — **veto** sur cette action, l'agent se rabat sur sa 2ᵉ préférence |

**Pourquoi c'est structurellement meilleur que l'addition** : une porte dans [0,1] n'a pas
d'échelle propre. Il n'y a donc **plus de conflit d'amplitude**, et `gain_c1` n'a plus rien à
compenser — la boucle de compensation mesurée le 05/09 (`r` = −0,75) perd sa raison d'être.

⚠️ **Aucun seuil, aucun `if`** : la porte est continue et apprise. Le dépôt a refusé un
déclenchement sur seuil trois fois (v28 pour C3, v29 pour le court-circuit C1→C2, v30 pour
la boucle d'attention) — une sigmoïde reste un `if` avec une pente **si on l'utilise pour
brancher**, pas pour moduler.

## 4. Le protocole et les juges

| Élément | Décision |
|---|---|
| **Témoin** | `--sans-intention` : force `intention ≡ 1,0` ⇒ bras **bit-identique** au régime libre actuel. Assertion runtime dans le module (bug v41.4) |
| **Juge primaire — J2 directivité** | l'inhibition doit rendre les trajets **moins browniens** : ratio distance/plus court chemin visé **< 5×** (aujourd'hui **14 à 18×**) |
| **Juge secondaire — J1 maîtrise** | δ apparié, `t` > 2,86 (Bonferroni 3 métriques, n=20) |
| **Juge saturé — niveau** | ⚠️ **40/40 runs au plafond du niveau 4** : un δ = 0 y est un **plafond**, pas une absence d'effet |
| **Coût** | 20 paires × 1500 j ≈ **5 h** |

⚠️ **J2 est corrélationnel** : à λ = 0,9 (v41.47), la **meilleure** directivité de la campagne
allait avec le **pire** succès. La directivité peut être un *symptôme* de la compétence, pas
son levier. À reporter, jamais à revendiquer seul.

---

## 5. 🔴 LA RÉSERVE PRINCIPALE — la porte regarde un futur produit par C1

C'est le point que la conception ne peut pas voir, et il est structurel. Dans le rollout
(`noyau.py:1153`) :

```python
choix = torch.argmax(self.tete_motrice(pensee_branche), dim=-1)
actions_pas = self.actions_eye[choix]      # continuation gourmande
```

**Après le premier pas, chaque branche est conduite par l'argmax de `tete_motrice` — donc
par C1 lui-même.** La `pensee_branche` finale ne signifie pas *« où mène l'action a »* mais
*« où j'arrive si je fais a **puis laisse C1 conduire** »*.

Deux conséquences :

1. `tete_intention` lirait un futur **produit par C1** pour ensuite **filtrer C1**. Elle
   risque de ne mesurer que la cohérence de C1 avec lui-même.
2. Sur un C1 brownien (**14 à 18×** le plus court chemin), les 8 futurs sont 8 marches
   aléatoires. **S'ils convergent, la porte n'a rien à filtrer.**

⚠️ Ce n'est **pas** rédhibitoire — mais c'est **mesurable avant de coder** (§6.a), et
l'instrument existe déjà.

## 6. Les deux prérequis, à coût nul

### 6.a Les branches divergent-elles À L'HORIZON 7 ?

La sonde [`sonde_jepa_action.py`](../../src/naulthene/instruments/sonde_jepa_action.py) a
mesuré la séparation des branches **au tick immédiat** : ratio **0,48** (médiane 0,46, aucun
cerveau sous 0,10). Il faut la même mesure **au bout du rollout**.

| Résultat | Conséquence |
|---|---|
| ratio à h=7 **comparable** à h=1 | ✅ la porte a de la matière — coder |
| ratio à h=7 **≈ 0** | 🔴 les branches convergent : la porte filtrerait du bruit. **Corriger le rollout d'abord** (ne pas laisser C1 conduire), ou renoncer |

**Coût : zéro run** — 40 `.brain` existants, la sonde est écrite, il suffit d'itérer les horizons.

### 🔴 MESURÉ LE 06/09/2026 — LE PRÉREQUIS ÉCHOUE, ET LA CAUSE EST IDENTIFIÉE

**40 cerveaux, zéro run.** La séparation moyenne entre branches, par horizon :

| Horizon | Séparation moyenne | Médiane |
|---|---|---|
| **h = 1** | 0,12328 | 0,10522 |
| h = 3 | 0,03052 | 0,01440 |
| **h = 7** | **0,01039** | **0,00368** |

**Ratio h7/h1 : médiane 0,0295 — les branches perdent 97 % de leur séparation.**
**33 cerveaux sur 40** sont sous 0,10. Identique dans les deux régimes (apparié
LIBRE−TÉMOIN : `t` = −1,09, NS) : c'est une propriété de **l'architecture**, pas du gain.

> **Une tête d'intention lisant la `pensee_branche` FINALE lirait 8 vecteurs quasi
> identiques.** Elle filtrerait du bruit.

### ✅ MAIS LA CAUSE N'EST PAS JEPA — C'EST LA CONDUITE PAR C1

Diagnostic sur `LIBRE_g11`, deux rollouts comparés pas à pas :

| Rollout | pas 1 | pas 2 | pas 3 | pas 7 | **h7/h1** |
|---|---|---|---|---|---|
| **Conduite par C1** (code actuel) | 0,199 | 0,057 | 0,025 | **0,0086** | **0,043** |
| **Action répétée** (chaque branche garde son geste) | 0,199 | 0,243 | 0,218 | **0,229** | **1,15** |

🔴 **Le modèle du monde maintient parfaitement la séparation** (ratio **1,15**) quand chaque
branche conserve son action. **L'effondrement vient entièrement de l'argmax de
`tete_motrice`** : dès que C1 reprend la conduite, les 8 futurs convergent vers un point
unique **en 3 pas**.

**C1 ramène toutes les branches au même endroit, quel que soit le premier geste.**

C'est la confirmation mécanique de la réserve §5 : la `pensee_branche` finale ne dit pas
*« où mène l'action a »*, elle dit *« où C1 va de toute façon »*.

### Ce que ça impose à la conception

| Option | Conséquence |
|---|---|
| **A — coder la tête telle quelle** | ❌ elle lirait 8 vecteurs identiques. À exclure. |
| **B — lire `pensee_branche` au pas 1** | 🟡 la séparation y est intacte (0,123) — mais la tête ne voit alors **plus loin** que C1, et perd sa raison d'être |
| **C — changer le rollout d'abord** | 🟢 rendre les branches persistantes (action répétée, ou conduite par la tête d'intention elle-même) **restaure la séparation à 1,15** |

⚠️ **L'option C touche `simuler_futur_et_planifier`**, dont CLAUDE.md protège explicitement
la restriction : le premier pas branche sur les 7 actions réelles, les suivants suivent le
réflexe glouton — *« ne pas changer cette restriction sans une raison explicite de
l'utilisateur »*. **La raison existe désormais, mesurée** ; la décision reste à l'utilisateur.

⚠️ **Et le coût est borné** : répéter l'action ne change **pas** la complexité (toujours
`O(A × horizon)`, jamais `7^N`) — c'est une substitution de l'action choisie à chaque pas,
pas un rebranchement.

⚠️ **Ce que ça ne dit pas** : qu'un rollout à branches persistantes serait *meilleur*. Un
agent qui répète 7 fois « avancer » simule une trajectoire irréaliste. La forme correcte
(action répétée ? conduite par la tête d'intention ? décroissance progressive ?) **n'est pas
tranchée** et demande son propre A/B.

### 6.b Le `lr` du critique — ⚠️ le ratio 0,073 sur-corrigerait

La proposition d'utiliser **6,57 / 89,24 ≈ 0,073** comme poids de `perte_critique` mérite
deux nuances avant d'être codée :

1. **89,24 / 6,57 est un rapport de NORMES DE GRADIENT, pas de poids de perte.** Il intègre
   déjà l'écart d'échelle entre une MSE (|perte| médiane **1,02**) et un policy gradient
   (**0,29**). Multiplier la perte par 0,073 diviserait le gradient par 13,6 **en plus** de
   cet écart — ce n'est pas la parité, c'est une sous-correction du critique.
2. **`--detach-c2` n'ampute PAS le critique.** Il coupe son gradient vers `pensee_bio`
   **seulement** ; `cortex_prefrontal` reçoit 100 % du sien (`noyau.py:1556`). Le « garrot »
   ne porte que sur la couche partagée.

**La forme correcte reste à dériver**, et c'est un chantier distinct de celui-ci. Une piste :
égaliser les normes **mesurées** sur `integrateur_bio` plutôt que les poids de perte — ce qui
suppose une mesure par nuit, donc une mécanique adaptative (méthode v30.1 : mesurer le fixe
avant de dériver).

## 7. Ce que ce chantier ne résout pas

⚠️ **Le mur du niveau 4 tient** (20/20 des deux côtés au dernier verdict). Aucune mesure ne
relie l'inertie de C2 au plafond, et **PPO n'a pas de C2 tout en résolvant `LavaGapS5` à
97,27 %**. Ce chantier sert la **thèse du projet** (un cerveau à deux couches dont la
délibérative existe vraiment) — il n'est **pas** le candidat le mieux placé pour franchir le
niveau 5. Ce candidat reste
[§3 du plan](PLAN_05092026_toutes_les_pistes_classees.md) : **la politique ne reçoit qu'un
seul pas de gradient par journée**, contre 63× plus par tick chez PPO.

**Les deux ne s'excluent pas** — mais l'ordre compte, et il doit être choisi en connaissance
de cause.

---

*Spécifié, non codé. **§6.a a été mesuré le 06/09 et il ÉCHOUE** : les branches perdent 97 %
de leur séparation avant l'horizon 7, **à cause de C1 et non de JEPA**. La tête d'intention
telle que spécifiée lirait du bruit — le rollout doit être corrigé d'abord (option C), et
cette correction touche un invariant protégé qui exige une décision utilisateur.*
