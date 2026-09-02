# REJEU DU BANC CORRIGÉ — figer les vraies métriques de référence

**Date** : 2026-09-02 · **Protocole écrit AVANT dépouillement** · **Lecture seule, aucun
entraînement.**

## La dette qu'on solde

Le 01/09, un défaut d'instrument a été trouvé : la sonde de banc lisait la mémoire de
travail en `penser()[1]` (la VALEUR, un scalaire `(1,1)`) au lieu de `[4]`, et un garde-fou
sur `dim_bus` la rejetait **en silence**. Tous les chiffres de banc des **30-31/08**
décrivent donc un agent **sans mémoire de travail ni contexte épisodique**.

Vérifié sur `A_g66` : succès **37,33 % → 40,00 %**, directivité **14,21× → 14,92×**.

Tant que les 20 cerveaux ne sont pas rejoués, **deux choses restent inconnues** :

1. `r(directivité, succès) = −0,8225` (`t = −5,96`, n=19) — **le seul prédicteur
   significatif jamais trouvé sur ce dépôt** — survit-il, recule-t-il, ou se renforce-t-il ?
2. La réintroduction du contexte mnésique suffit-elle, sur certaines graines, à structurer
   naturellement la persistance d'action **sans rien modifier au code** ?

## Le protocole

| Élément | Valeur |
|---|---|
| Cohorte | les **20** cerveaux de `brains/30082026_plancher_n20/agregat.json`, fichiers **identiques** |
| Source | `brains/26082026_v4132_AB3_cursus/*.brain` (vérifiés présents, aucun manquant) |
| Environnement | `MiniGrid-SimpleCrossingS9N1-v0` |
| Épisodes | **300**, graines de carte appariées (`--graine 90210`) — **identique au 30/08** |
| Instrument | `sonde_plancher_geometrique` **corrigé** (`penser()[4]` + garde-fou bruyant) |
| Écriture | aucune — les `.brain` sont lus depuis une COPIE |

⚠️ **Le protocole est rigoureusement celui du 30/08**, à l'unique exception de l'index de
la mémoire. C'est ce qui rend la comparaison ancien/nouveau interprétable : une seule
variable change.

## Ce qu'on attend, et ce qu'on ne doit PAS supposer

L'agent mesuré était **amputé**, donc les scores devraient monter. Mais :

- ⚠️ **Le sens de l'effet sur la DIRECTIVITÉ n'est pas prévisible.** Sur `A_g66` elle a
  *augmenté* (14,21 → 14,92) alors qu'on aurait pu attendre l'inverse — une mémoire de
  travail devrait aider à tenir un cap. Un cerveau qui gagne plus peut aussi gagner
  *par des chemins plus longs*.
- ⚠️ **`r = −0,8225` peut changer de signe.** Ce n'est pas exclu : elle a été calculée sur
  des directivités toutes mesurées en régime amputé.

## Vérifications prévues au dépouillement

| Vérification | Pourquoi |
|---|---|
| **δ ancien/nouveau par cerveau** | apparié, donc `t` sur 20 paires |
| **Recalcul de `r(directivité, succès)`** | la question centrale |
| **Tautologie** | la directivité n'existe que sur les VICTOIRES — rapporter `n_victoires` et les cerveaux à 0 |
| **Saturation** | plafond arithmétique 27,0× |
| **Le témoin aléatoire** | doit rester à **5,67 %** (17/300) : il ne passe pas par le code corrigé. S'il bouge, l'instrument a un autre défaut |
| **Le témoin « neuf »** | ⚠️ **inutilisable** (biais d'action Xavier, 4,33 % à 22,67 % selon la graine) — rapporté mais non interprété |

## Limites

1. **Banc forcé** : ne prouve rien sur le cursus (règle §6).
2. Politique **figée** (`eval()`) : aucun apprentissage, on mesure ce que ces cerveaux
   savent déjà faire.
3. Ces cerveaux datent du **26/08** (v41.32) : ils n'ont ni le rendement v41.48 ni l'élan
   v41.49. C'est **voulu** — on fige la référence historique, on ne teste pas une mécanique.

## Journal d'exécution (ajouté le 02/09/2026, en cours de campagne)

- ⚠️ **Une première passe est INVALIDE et rangée dans `_invalide_v4149/`** (14 fichiers
  `banc_A_*.json`). Elle a tourné sur le code courant (v41.49), où `DIM_VECTEUR_BIO = 44` :
  les cerveaux du 26/08 (42 dims) y étaient **greffés** au chargement, donc mesurés avec deux
  colonnes d'élan fraîchement initialisées — ce n'est plus « une seule variable change ».
- **Le rejeu valide tourne sur un worktree figé au commit `2d69b40` (v41.47)** —
  `/tmp/naulthene_v4147`, voir l'en-tête de `rejouer.sh` : `DIM_VECTEUR_BIO = 42`, aucune
  greffe, et la mémoire de travail déjà lue en `penser()[4]`. C'est la **seule** combinaison
  qui isole la correction d'instrument de tout le reste.
- Les `banc_*.json` de ce dossier sont commités **au fil de l'eau** (Règle de Trace §3),
  campagne non terminée : ne pas calculer de `t` avant que les 20 fichiers soient présents.
