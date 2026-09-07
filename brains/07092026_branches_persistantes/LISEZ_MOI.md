# LES BRANCHES PERSISTANTES — rendre au rollout des futurs distincts

**Protocole écrit AVANT le lancement** (07/09/2026). Campagne `07092026_branches_persistantes`.

## La question

Mesuré le 06/09 (40 cerveaux, zéro run) : dans le rollout mental, les 8 branches perdent
**97 % de leur séparation** avant l'horizon 7 (médiane h7/h1 = **0,0295**). C2 n'évalue donc
pas 8 plans — il évalue **une destination** vue de 8 départs.

**La cause n'est pas JEPA** : à action répétée, le modèle du monde maintient la séparation
(h7/h1 = **1,15** contre 0,043). C'est `argmax(tete_motrice)` qui reprend la conduite au
pas 2 et ramène tous les futurs au même point.

⚠️ **Vérifié le 07/09 en régime K8_NU** (le meilleur connu) : le rollout y reste **tout aussi
effondré** (médiane **0,0118**, soit pire que le témoin). Les 8 époques ont amélioré le
comportement **sans rien réparer du rollout** — `r(ratio, maîtrise) = −0,08`.

## Les bras

| Bras | Contenu | Runs |
|---|---|---|
| **TEMOIN** | `--epoques-nuit 8` seul (le meilleur régime connu) | **0** — réutilise `06092026_epoques_nuit/K8_NU` |
| **BP** | `--epoques-nuit 8 --branches-persistantes` | 20 |

20 graines appariées × 1500 jours, régime voix libre. **Un seul bras neuf** : la mécanique
est ajoutée **au meilleur régime**, pas testée isolément — c'est ce qui rend l'effet
attribuable à elle seule (règle §6.2).

## Les juges, posés d'avance

⚠️ **Bonferroni 3 métriques** ⇒ seuil `t` = **2,86**.

| Juge | Grandeur | La mécanique AIDE si | Elle est NEUTRE si |
|---|---|---|---|
| **1. Maîtrise** | δ BP − TEMOIN | δ > 0, `t` > 2,86 | δ ≈ 0 |
| **2. Niveau** | idem | δ > 0 · Fisher bras par bras | δ ≈ 0 |
| **3. Mécaniste** | ratio h7/h1 du rollout | **monte** vers 0,78 (mesuré au banc) | reste ~0,012 |
| **4. Accord C1/C2** | part des ticks d'accord | **monte** (C2 a enfin des futurs distincts) | inchangé |

**Le juge 3 est le juge de réalité** : il dit si la mécanique a fait ce qu'elle prétend,
indépendamment du comportement. Mesuré au banc sur `K8_NU_g11` : **0,0118 → 0,7791** (66×).

## ⚠️ Ce qui pourrait mal tourner, écrit d'avance

1. **Un agent qui répète 7 fois « avancer » simule une trajectoire irréaliste.** La
   séparation retrouvée peut être du bruit sémantique : des futurs distincts mais faux.
2. **C2 est mesuré INERTE** (05/09, δ = −1,375, NS) et son gradient **nuisait** (06/09).
   Améliorer ce qu'il voit peut n'avoir aucun effet — la voix reste la même.
3. **Le rollout n'est pas corrélé à la maîtrise** en régime K8 (`r` = −0,08) : rien ne dit
   qu'un meilleur rollout améliore quoi que ce soit.

⚠️ **Prédiction honnête** : effet **peu probable** sur le comportement. Cette campagne est
un **prérequis** de la tête d'intention (v42), pas un levier attendu — elle répare le canal
qui la nourrira. Un juge 3 qui passe et un juge 1 nul serait un résultat **acceptable** :
la mécanique marcherait sans que C2 sache s'en servir, ce qui est précisément l'argument
pour la tête d'intention.

## Le protocole

```bash
zsh brains/07092026_branches_persistantes/lancer.sh
```
