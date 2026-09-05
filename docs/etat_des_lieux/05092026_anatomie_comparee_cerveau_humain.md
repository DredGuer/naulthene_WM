# ANATOMIE COMPARÉE — Naulthène face au cerveau humain

**Date** : 2026-09-05 · **Nature** : photo datée, non normative · **Mesure** : décompte réel
d'un `.brain` de 1500 jours (`brains/05092026_ablation_c2/LIBRE_SANS_C2_g11.brain`).

> Ce document naît d'une analyse comparative proposée par l'utilisateur. Sa **thèse est
> retenue** (inversion architecturale) ; **deux de ses chiffres sont corrigés** par la mesure.

---

## 1. La thèse retenue — l'inversion architecturale

> *« Là où l'humain est dominé par sa surface délibérative et la coordination fine de ses
> mouvements, Naulthène fonctionne comme un tronc cérébral et un système limbique hautement
> outillés, flanqués d'un néocortex embryonnaire. »*

**La mesure confirme, et amplifie.**

## 2. Le décompte réel — 1 556 062 paramètres

| Étage fonctionnel | Modules | Params | **Part** |
|---|---|---|---|
| **Tronc + limbique** | `hippocampe`, `fusion_memoire`, `integrateur_bio`, `analyseur` | 952 100 | **61,19 %** |
| Vision | `porte_visuelle`, `generateur_attente` | 299 560 | 19,25 % |
| Audio / vocal | `porte_auditive`, `generateur_attente_audio`, `tete_vocale` | 290 976 | 18,70 % |
| **C1 moteur** | `tete_motrice` (159 → 8) | 7 634 | **0,49 %** |
| **C2 délibératif** | `cortex_prefrontal` (159 → 1) | 956 | **0,06 %** |
| Exo-Sens C3 | `tete_requete` | 4 772 | 0,31 % |

**Ratio tronc/limbique ÷ délibératif : ×996.** Chez l'humain, le rapport est inversé
(néocortex ~80 % du volume). L'inversion est donc **plus radicale** que l'analyse ne le disait.

## 3. 🔴 Deux chiffres corrigés

### (a) Le total : 55 232 → **1 556 062** (×28)

Les 55 232 sont le compte d'un cerveau **à la naissance** (`dim_bus = 16`). Après 1500 jours
de neurogenèse, `dim_bus` vaut **159** — vérifié sur les formes réelles :
`cortex_prefrontal (1, 159)`, `tete_motrice (8, 159)`.

| | Naissance | **1500 jours** |
|---|---|---|
| Paramètres | 55 232 | **1 556 062** |
| Mémoire (float32) | 0,21 Mo | **5,94 Mo** |

⚠️ **Ne jamais citer 55 232 comme la taille de Naulthène** sans préciser « à la naissance ».
Les README l'utilisent pour la comparaison à budget égal avec PPO, ce qui est légitime — mais
c'est un cerveau neuf, pas un cerveau mûr.

### (b) C2 : 8,4 % → **0,06 %**

L'analyse comptait `generateur_attente` (JEPA visuel, 159 320 params) dans le « néocortex
délibératif ». C'est un **prédicteur sensoriel**, pas un délibérateur. C2 seul —
`cortex_prefrontal` — pèse **956 paramètres**.

## 4. ⚠️ La nuance que la mesure impose : C2 est petit PAR CONSTRUCTION

`cortex_prefrontal : dim_bus → 1` est le **critique** d'un Acteur-Critique : sa sortie *est*
un scalaire. `tete_motrice : dim_bus → 8` est exactement **8× plus grosse parce qu'il y a
8 actions**.

> **Ce n'est pas une atrophie, c'est la forme d'un critique.** On ne peut pas « élargir C2 »
> sans casser la baseline de l'avantage : il faudrait **ajouter une tête** à côté du critique,
> pas remplacer celui-ci.

C'est la contrainte qui encadre toute refonte de C2 en « générateur d'intention ».

## 5. ⚠️ « L'absence de cervelet » — la version testable est DÉJÀ RÉFUTÉE

L'analyse attribue la motricité brownienne à l'absence d'un coordinateur de trajectoire.
L'hypothèse est séduisante, mais sa forme mesurable a été livrée **puis réfutée à n=20** :

| Mécanique | Verdict |
|---|---|
| **Ancrage cinématique** (v41.49) — mémoire de l'élan | ❌ réfutée à n=20 |
| **Rendement mécanique** (v41.48) | ❌ réfutée à n=20 |

Les deux convergent sur le même diagnostic : ***l'information est là, et le réseau ne s'en
sert pas.***

⚠️ **Contrainte pour toute proposition future** : deux ajouts passifs en queue du vecteur bio,
**deux effets nuls à n=20**. Une dimension supplémentaire dans `integrateur_bio` est **diluée**.
Un « cervelet » devra passer par un autre chemin que la queue du vecteur bio.

## 6. Ce que l'analyse dit juste, et qui n'est pas contesté

- **Le corps domine le gradient** : `Bio` **57,0 %** contre `Env` **21,6 %** sur 60 000 nuits
  (⚠️ pas 62,1/17,4 — chiffres corrigés le 04/09, lus à tort sur la dernière journée).
  Ratio **2,64×**.
- **Le paradoxe auditif** : **18,70 %** du réseau pour un terme `Vocal` à **σ = 0,0000** sur
  un cursus spatial silencieux. Ablation prévue (priorité 3).
- **Le cycle veille/sommeil** est fidèle au principe : rejeu hippocampique, consolidation des
  poids annexes, érosion bornée par le plancher vital.
- **L'échelle ne débloque rien** : élargir le bus n'a jamais franchi un palier, et coûte du
  métabolisme basal.

## 7. Ce que ça implique pour la suite

1. La refonte de C2 en générateur d'intention reste **suspendue à l'ablation propre en cours**
   (`brains/05092026_ablation_c2/`). Si C2 s'avère utile une fois C1 libre, il faut
   l'**amplifier**, pas le refondre.
2. Toute « piste cervelet » doit expliquer pourquoi elle échapperait au verdict de v41.48/49.
3. L'hémisphère audio est le **seul gisement franc** : 18,70 % du réseau pour σ = 0.

---

*Photo datée. Les parts sont celles d'UN cerveau à 1500 jours ; elles évoluent avec la
neurogenèse et ne valent pas pour un cerveau neuf.*
