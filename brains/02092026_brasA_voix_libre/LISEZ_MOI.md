# BRAS A — LA VOIX LIBRE : la netteté de la politique est-elle apprenable ? (v41.50)

**Protocole écrit AVANT le lancement** (02/09/2026) · **Lancement : après la fin du rejeu**
`brains/02092026_rejeu_banc_corrige/` (20/20), qui fixe le `r(directivité, succès)` de
référence à instrument corrigé.

## La question

Hypothèse consignée dans `docs/recherche/AMPLITUDE_02092026_la_politique_ne_peut_pas_etre_nette.md` :
`gain_c1 = clamp(2,1 × f / amplitude_c1, 0,25, 4)` renormalise la voix de C1 **à chaque
tick, dans les deux sens**. Softmax est invariante par translation, pas par échelle : la
NETTETÉ de la politique n'est donc pas apprenable — sur 20 cerveaux l'amplitude C1 vit dans
[0,33 ; 0,91] et l'entropie jouée à 99 % du maximum. **Retirer le gain suffit-il ?**

Sur un nouveau-né (A/A du 02/09), le témoin a `gain ×0,25-0,45` : chez un agent neuf
(`f ≈ 0`) le gain *étouffe* C1 de 2 à 4× dès le premier jour.

## Le protocole

| Élément | Valeur |
|---|---|
| Bras | **LIBRE** (`--gain-c1-libre`, gain ≡ 1,0) vs **TÉMOIN** (gain v37.0 intact) |
| Ce qui change | **une seule chose** : la renormalisation de C1. C2, l'apprentissage, l'élan (v41.49) et le rendement (v41.48) sont identiques dans les deux bras |
| Graines | **20**, appariées (11 · 22 · … · 222) — les mêmes que `01092026_etape1_elan/` |
| Jours | 100 par run · **40 runs** · `--env-force MiniGrid-SimpleCrossingS9N1-v0` |
| Banc | `sonde_plancher_geometrique`, **300** épisodes, graine de carte 90210, force = `acceptation()` du cerveau (nouveau défaut v41.50 — voir plus bas) |
| Trait | `gain_c1_libre` est **sérialisé dans le .brain** : le banc respecte le régime sans drapeau, et le vérifie (`🔬 [BRAS A] cerveau rechargé…`) |

## Les CRITÈRES, posés avant le run

| Juge | Grandeur | Succès | Échec |
|---|---|---|---|
| **1. Le mécanisme mord-il ?** | entropie **jouée** au banc (`entropie_jouee`, max 1,946) | **< 1,75** en médiane sur LIBRE | ≥ 1,85 : le gain n'était pas ce qui bornait la netteté — **ablation vide**, rien d'autre n'est interprétable |
| **2. Succès** | taux au banc, moyenne des 20 | **> 25 %** (témoin attendu ~12 %) | δ apparié non significatif (`t` < 2,43, Bonferroni 2 métriques) |
| **3. Directivité** | médiane du plus court chemin | **< 10×** (témoin ~15-19×) | ≥ 12× |

Un juge 1 positif avec un juge 2 négatif est un **résultat** (la netteté seule ne suffit
pas) ; un juge 1 négatif rend les juges 2-3 sans objet.

## Vérifications prévues au dépouillement

| Vérification | Pourquoi |
|---|---|
| `gain C1 ×1.00` sur toutes les nuits LIBRE, jamais sur TÉMOIN | le drapeau a atteint l'individu (`lancer.sh` l'exige déjà par `grep`) |
| Amplitude C1 en fin de run, deux bras | si LIBRE reste dans [0,33 ; 0,91], la tête n'a pas grandi — voir F4 (budget d'apprentissage), pas F1 |
| **Signe du succès contre la netteté** | une entropie qui baisse pendant que le succès s'effondre est un ÉCHEC (leçon λ=0,9 du 01/09 : « confiant dans l'erreur ») |
| Tautologie / saturation (27,0×) / graines à 0 victoire | comme aux campagnes précédentes |
| Témoin aléatoire à **5,67 %** | invariant |
| **Ratio C1/C2 et accord** | si C1 libre écrase C2 (ratio < 0,3), c'est le mode d'échec v37.0-fix — à rapporter, **pas** à corriger en cours de campagne |

## ⚠️ Ce qui change dans l'INSTRUMENT, et pourquoi c'est écrit ici

`sonde_plancher_geometrique` jouait avec `force_planification = 0,5` **figée**. Le témoin
y était donc renormalisé à `2,1 × 0,5 = 1,05` d'amplitude C1, quelle que soit la force
qu'il avait vécue en run (0,7-0,9 sur la cohorte AB3). Défaut v41.50 : `acceptation()` du
cerveau — la même grandeur que la boucle de jeu. `--force 0.5` reproduit le protocole
historique. **Les chiffres de cette campagne ne sont donc pas comparables tick à tick à
ceux du rejeu**, qui garde `--force 0.5` ; ils le sont entre bras (même instrument).

## Limites, écrites d'avance

1. **Banc forcé** : ne prouve rien sur le cursus (règle §6). Un bras A positif devra
   repasser en cursus complet avant d'être revendiqué.
2. Le gain avait été posé contre un mode d'échec réel (C1 écrasant C2 à 0,21× en 30 jours
   une fois les têtes débloquées, v37.0-fix). Si LIBRE réussit **en écrasant C2**, la
   question « C2 sert-il ? » devient le bras C — elle n'est pas tranchée ici.
3. 100 jours = 100 pas d'optimiseur pour la tête motrice (F4). Si l'amplitude C1 ne grandit
   pas, le bras B (budget) est le suivant, pas une reformulation du bras A.
4. n = 20 : un effet doit dépasser δ_A/A (= 0 sur ce banc) **et** Bonferroni.
