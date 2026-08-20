# Chantier v41.31 — le gradient causal et le tube digestif

**Statut : CONCEPTION, non implémenté.** Arbitré le 20/08/2026, à coder **après** la fin de
la campagne v41.30 (toucher le code invaliderait les 40 runs).

---

## Axe 1 — Le filtrage causal du gradient moteur

### 1.1 La décision

**RL SEUL est neutralisé. JEPA est conservé à 100 %.** Arbitrage utilisateur explicite.

| | gradient | pourquoi |
|---|---|---|
| **Politique motrice** (acteur-critique) | **neutralisé** | un geste sans effet ne doit rien créditer |
| **Modèle du monde** (JEPA) | **conservé** | l'immobilité face à un mur est une **prédiction déterministe valide** |

⚠️ **Le piège d'un JEPA aveugle aux murs** : sans ce gradient, `generateur_attente`
n'apprendrait jamais la condition « contact mur → immobilité ». Le rollout mental de C2
(`simuler_futur_et_planifier`) imaginerait alors traverser les parois. Or **pour planifier un
contournement, C2 doit précisément prédire « si j'avance ici, je ne bougerai pas »**. Couper
JEPA détruirait la faculté même qu'on cherche à réveiller.

### 1.2 Ce que le problème coûte aujourd'hui — mesuré

Répartition par action (DERIVE_g1, dernier jour) :

```
a0 gauche    9%   0st        a4 drop     9%  100st
a1 droite    7%   0st        a5 toggle  16%  100st
a2 avancer  26%  51st        a6 done     7%  100st
a3 pickup   24%  85st
```

**32 % des ticks (a4+a5+a6) sont stériles à 100 %** — aucun effet, sur aucun tick. Plus 85 %
des `pickup` et la moitié des `avancer`. Total : **61,7 % des ticks**.

Le poison est l'assignation de crédit : quand un épisode réussit, REINFORCE propage un retour
positif sur **toutes** les actions de la trajectoire. Un agent qui a spammé `toggle` 25 fois
dans le vide en marchant vers le but voit C1 renforcer ces gestes par simple contamination.

### 1.3 L'invariant de non-transition

```
non_transition = (pos_t == pos_{t-1}) ET (dir_t == dir_{t-1}) ET (carrying_t == carrying_{t-1})
```

Trois précisions, chacune corrigeant un piège :

1. **La ROTATION est une transition.** Tourner ne déplace pas l'agent mais **pivote son champ
   de vision** : c'est une acquisition d'information, la brique de base de l'exploration.
   L'exclure reviendrait à punir le fait de regarder.
2. **Le `vecteur_bio` est EXCLU.** Faim, soif, douleur et thermoception dérivent **à chaque
   tick** par le seul métabolisme : un critère qui les inclurait ne détecterait **jamais**
   de non-transition. La condition serait mathématiquement toujours fausse.
3. **Neutraliser ≠ pénaliser.** Gradient **nul**, jamais de malus — sinon on réintroduit une
   récompense en dur, ce que le dogme interdit. L'extinction des actions inutiles doit
   **émerger** de l'absence de crédit, pas d'une punition.

### 1.4 ⚠️ Le doublon à résorber — deux détecteurs coexistent déjà

| détecteur | définition | mesuré |
|---|---|---|
| `_stats["sterile"]` (`noyau.py:8465`) | état MiniGrid — **exactement l'invariant ci-dessus** | **61,7 %** |
| `mur_touche` (`noyau.py:8553`) | `torch.equal(etat_courant, etat_suivant)` — observation visuelle | **29,9 %** |

Les deux mesurent des choses différentes et divergent d'un **facteur 2**. `mur_touche` ne lit
que le champ visuel partiel encodé, qui peut rester identique alors que le monde a changé
(hors champ), ou différer alors que rien n'a bougé.

`mur_touche` est **déjà branché sur la douleur** (v41.27). Brancher le gradient sur
`_stats["sterile"]` sans unifier ferait punir **deux ensembles différents** par deux
mécaniques qui croient parler du même geste.

👉 **Créer un invariant UNIQUE et faire converger les deux usages dessus.** Ne pas ajouter un
troisième détecteur.

### 1.5 ⚠️ Le piège d'implémentation — l'ordre des opérations

`log_prob` est empilé **ligne 8361**, la stérilité n'est calculée que **ligne 8465** : au
moment de l'empilement, on ne sait pas encore si le geste sera stérile.

Le masque doit donc être appliqué **au calcul de la perte** (`apprendre_journee`,
`noyau.py:1660`), pas à l'empilement — en accumulant un buffer de stérilité par tick,
exactement comme `log_probs_journee`.

⚠️ Ce buffer doit être vidé **dans tous les cas** en fin de journée, y compris si la branche
est inactive : sinon il grossit indéfiniment et désaligne les tenseurs (piège déjà documenté
pour le buffer de distillation v37.1).

⚠️ La perte est une **moyenne** (`.mean()`). Masquer par multiplication laisserait le
dénominateur inchangé, donc **diluerait** le gradient des gestes utiles au lieu de le
préserver. Il faut diviser par le nombre de ticks **retenus**, pas par le total — même
discipline que la moyenne pondérée de la distillation v37.1.

### 1.6 Risque à mesurer

Le levier touche **la majorité** de l'apprentissage (61,7 % des ticks). Deux effets opposés
sont plausibles et seule la mesure les départagera :

- **favorable** : l'entropie motrice se nettoie, `a4/a5/a6` s'éteignent là où elles ne servent
  à rien, le crédit se concentre sur les gestes qui agissent ;
- **défavorable** : sur une carte où l'agent bouge peu, l'acteur ne reçoit presque plus de
  signal — on aurait supprimé l'apprentissage au lieu de le focaliser.

**Drapeau d'ablation obligatoire** : `--gradient-non-filtre`.

---

## Axe 2 — L'assainissement du tube digestif

### 2.1 Le fait

`DEBIT_DIGESTIF_JOUR = DEPENSE_ENERGIE_JOUR × MARGE_DIGESTIVE = 3.0` impose une vidange de
**3,333 estomacs/jour identique dans les deux bras** de la campagne v41.30, quel que soit le
besoin. C'est l'explication complète de l'invariance énergétique mesurée (`t = +1,40`, NS).

`DEPENSE_ENERGIE_JOUR = 2.0` porte le même défaut que le `4.0` : son propre commentaire dit
*« calibré par mesure… **à 3 repas/jour** »*, un régime qui n'a plus cours (le besoin dérivé
vaut 1,7 à 2,0).

### 2.2 La direction

Indexer `debit_digestif` sur le **besoin réellement vécu** plutôt que sur une constante. Le
tube digestif d'un organisme qui mange peu ne peut pas traiter le débit d'un organisme qui
mange beaucoup.

⚠️ **Contrainte non négociable** : `MARGE_DIGESTIVE` garantit que le débit **dépasse** la
dépense. Si le débit passait sous la dépense, la mort deviendrait certaine **par
construction** et la mécanique ne mesurerait plus rien. Cette marge est une borne sur un
**rapport** : elle reste.

### 2.3 Vérifier `taux_satiete`

Variable **morte** depuis la v41.2 (rien ne la soustrait). Deux issues : la rebrancher, ou la
supprimer. ⚠️ Si on la rebranche, la satiété serait vidée **deux fois** (par elle et par la
digestion) — le double comptage que `calculer_deficit` interdit explicitement.

---

## Axe 3 — Le commentaire trompeur (documentation seule)

`noyau.py:2991` affirme que `taux_satiete` prélève le basal à chaque tick. **Faux** — mais
✅ **le basal EST bien facturé**, par `METABOLISME_BASAL_PART` dans la dépense énergétique
(vérifié : un agent totalement inactif à l'estomac vide perd **0,325000** en 100 ticks, soit
exactement le basal ; l'inaction coûte 65 % du tarif plein).

**C'est le texte à réparer, pas le comportement.** Aucune urgence fonctionnelle.

---

## Protocole

1. A/A avant tout A/B (règle de mesure §1)
2. Banc d'isolation court (3 graines × 10 jours) comme filtre rapide — il a détecté la faute
   du monde caméléon en 20 minutes
3. **Puis 20 graines**, un drapeau d'ablation **par axe** (les deux sont indépendants, mais
   les grouper rendrait impossible d'attribuer un effet)
4. ⚠️ **Ne jamais annoncer une significativité sur un run en cours** — leçon du 20/08 : le
   ratio C2/C1 donnait `t = +3,68` sur 5/5 graines au jour 1046 et `t = +1,93` sur 3/5 au
   jour 1479
