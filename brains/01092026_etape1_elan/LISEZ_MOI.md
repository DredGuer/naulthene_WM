# ÉTAPE 1 — l'ancrage cinématique tend-il le trajet ? (brique B, v41.49)

**Date de lancement** : 2026-09-01 · **Protocole écrit AVANT dépouillement.**

## La question

L'agent n'a **aucun repère de son propre élan** : mesuré à l'Étape 0,
`P(avancer|avancer)/P(avancer) = 0,9959`. La brique B lui injecte, en queue du vecteur bio,
un couple **égocentrique** (avance ressentie, dérive latérale) lissé sur une demi-vie
**dérivée de la carte**.

## ⚠️ Le juge de paix est DOUBLE cette fois — leçon de la brique C

La brique C avait un seul critère (la directivité) et a échoué sans qu'on sache **si le
mécanisme n'avait pas mordu, ou s'il avait mordu sans effet**. Ici les deux sont séparés :

| Niveau | Grandeur | Ce qu'elle dit |
|---|---|---|
| **1. Le mécanisme mord-il ?** | `P(avancer\|avancer) / P(avancer)` | mesuré à **0,9959** avant. S'il ne monte pas, l'information n'a pas été captée par C1 — **et rien d'autre n'est interprétable** |
| **2. Le comportement change-t-il ?** | **directivité** (< 6× succès · ≥ 12× échec) | le critère utilisateur, inchangé |

C'est la distinction « ablation vide / ablation négative » appliquée en amont : un ratio
resté à 1,00 rendrait toute lecture de la directivité **sans objet**.

## Le protocole

| Élément | Valeur |
|---|---|
| Bras | **ACTIF** (v41.49) vs **TÉMOIN** (`--sans-elan`) |
| Graines | **20**, appariées (11 · 22 · … · 222) |
| Jours | 100 par run · **40 runs** |
| Environnement | `--env-force MiniGrid-SimpleCrossingS9N1-v0` |
| Banc | `sonde_plancher_geometrique` (instrument corrigé), 150 épisodes |

⚠️ **Le témoin conserve la LARGEUR** (44 dims dans les deux bras) et ne coupe que
l'**information** : les 2 dims restent au neutre 0,5. On mesure donc l'apport du **signal**,
jamais l'effet d'un réseau plus large — même discipline que `PORTAGE_PERCU_ACTIF` (v41.33).

⚠️ **Un seul bras par mécanique.** `--sans-rendement` (v41.48) n'est **pas** activé : la
brique C reste ACTIVE dans les deux bras, donc elle ne peut pas confondre la mesure.

## Les contrôles déjà passés (`brains/01092026_AA_elan/`)

δ_A/A = 0 sur les deux bras · les bras diffèrent · drapeau vérifié dans le module ·
greffe 42 → 44 dims validée sur une **nuit complète** · amplitude du signal 0,167–0,211.

## Vérifications prévues au dépouillement

| Vérification | Pourquoi |
|---|---|
| **Le ratio d'autocorrélation a-t-il bougé ?** | si non, l'ablation est **vide** et la directivité n'est pas interprétable |
| **Tautologie** | la directivité n'existe que sur les VICTOIRES : rapporter `n_victoires` |
| **Saturation** | plafond arithmétique 27,0× sur cette carte |
| **Graines à 0 victoire** | directivité indéfinie — combien de points perdus |
| **Signe du succès** | une directivité qui baisse pendant que le succès s'effondre est un ÉCHEC (leçon λ=0,9 du 01/09) |
| **Amplitude de l'élan** | si elle tombe à ~0, la dimension est morte et le bras ACTIF vaut le témoin |

## Limites, écrites d'avance

1. **Un banc forcé ne prouve rien sur le cursus** (règle §6) : le niveau reste à 1/15.
2. **100 jours est court.**
3. `SimpleCrossing` n'a ni porte ni clé.
4. La brique B **ajoute une information** au réseau ; contrairement aux 20 réfutations
   précédentes, elle ne retouche pas le barème. C'est ce qui la distingue — et c'est
   précisément ce que cette campagne doit éprouver, pas supposer.
