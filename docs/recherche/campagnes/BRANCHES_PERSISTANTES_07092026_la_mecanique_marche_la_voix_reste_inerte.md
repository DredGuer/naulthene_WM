# LES BRANCHES PERSISTANTES — la mécanique marche, la voix reste inerte

**Date** : 2026-09-07 · **Statut** : ✅ **DÉPOUILLÉE** (20/20 cerveaux à jour 1500) ·
**n = 20 graines appariées × 1500 jours** · bras BP (v41.63, `--branches-persistantes`)
face au témoin **K8_NU** (le meilleur régime connu, réutilisé — 0 run neuf).
**Issue conforme à la prédiction pré-enregistrée.**

> Protocole : `brains/07092026_branches_persistantes/LISEZ_MOI.md` (écrit avant lancement,
> 4 juges, seuil Bonferroni `t` = 2,86). Sortie brute :
> `brains/07092026_branches_persistantes/depouillement_BP.txt` · agrégat : `agregat_BP.json`.

---

## 1. La question (rappel)

Le 06/09, mesuré sur 40 cerveaux (zéro run) : dans le rollout mental, les 8 branches perdent
**97 % de leur séparation** avant l'horizon 7 (médiane h7/h1 = **0,0295**) — C2 n'évalue pas
8 plans, il évalue **une destination** vue de 8 départs. La cause n'est **pas JEPA** (h7/h1
= 1,15 à action répétée) mais `argmax(tete_motrice)`, qui reprend la conduite au pas 2.
Vérifié le 07/09 en régime K8_NU : le rollout y reste **effondré** (médiane 0,0118),
`r(ratio, maîtrise) = −0,08`.

La campagne teste si garder chaque branche sur **son propre geste** (v41.63) répare la
séparation — et si ce canal réparé change quelque chose au comportement. C'est le
**prérequis** de la tête d'intention de C2 (v42).

## 2. Le résultat en une ligne

**Le juge mécaniste passe massivement, tous les juges comportementaux sont nuls** — et
c'était l'issue **« acceptable » écrite d'avance** dans le LISEZ_MOI : *« la mécanique
marcherait sans que C2 sache s'en servir, ce qui est précisément l'argument pour la tête
d'intention »*.

## 3. Les juges (posés d'avance) — résultats

| Juge | Critère | BP vs K8_NU | Verdict |
|---|---|---|---|
| **Garde-fou** | `gain_c1` = 1,00 partout | 1,0000 / 1,0000 | ✅ passe |
| **1. Maîtrise** | δ > 0, `t` > 2,86 | δ **−2,10 pt** · `t` = **−0,87** · 7/20 | ❌ **nul** |
| ↳ sans les 4 extrêmes | | δ +0,125 · `t` = +0,07 (n=16) | ❌ nul |
| **2. Niveau** | δ > 0 · Fisher bras par bras | δ +0,10 · `t` = +0,70 · **Fisher `p` = 0,7311** (7/20 vs 5/20) | ❌ **nul** |
| **3. Mécaniste** (ratio h7/h1) | **monte** vers ~0,78 (banc) | médiane **0,012 → 1,28** · log10 apparié `t` = **+10,55** · **19/20** | ✅ **PASSE, massivement** |
| ↳ sans les 4 extrêmes | | `t` = **+8,58** (n=16) | ✅ survit |
| **4. Accord C1/C2** | part des ticks d'accord **monte** | δ **−2,70 pt** · `t` = −1,75 · 4/20 | ❌ **nul** |

**Compléments** : 20/20 cerveaux BP à ratio > 0,05 (contre 4/20 pour K8_NU) · ratio C2/C1
médian 0,401 (BP) vs 0,467 (K8_NU) · maîtrise moyenne **16,90 %** (BP) vs 19,00 % (K8_NU)
· **0 cerveau BP à maîtrise 0 %** (1 chez K8_NU) · victoires médianes 932 vs 882 ·
**40/40 runs couverts, 0 inachevé**.

### Maîtrise à palier égal

| | niveau 4 | niveau 5 |
|---|---|---|
| **BP** | 20,0 % (n=13) | 10,0 % (n=7) |
| **K8_NU** | 25,0 % (n=15) | 10,0 % (n=5) |

Au niveau 5 atteint, la maîtrise est **identique** (10,0 %) : BP ne fait pas mieux une fois
le palier franchi — il n'y a **pas** d'apprentissage gagné sur `LavaGapS5` non plus.

## 4. Ce que ça établit, ce que ça n'établit pas

**Établi** :
- Les branches persistantes **suppriment l'effondrement du rollout** sur les 20 cerveaux
  entraînés avec elles (médiane h7/h1 = 1,28, au-dessus de la cible banc 0,78). La
  mécanique fait **exactement** ce qu'elle prétend (juge de réalité).
- Ce canal réparé **ne change aucun comportement mesuré** : maîtrise, niveau, accord —
  tous nuls au seuil corrigé, y compris après retrait des extrêmes.
- La campagne confirme le pattern du dépôt : **réparer ce que C2 voit ne suffit pas** —
  C2 est inerte (05/09) et son gradient nuisait (06/09) ; la voix reste la même.

**NON établi** :
- La **causalité** mécanique → comportement reste ouverte ; la corrélation `r(ratio,
  maîtrise)` en régime K8 était −0,08 et BP ne la fait pas bouger.
- Rien ne dit qu'une **tête d'intention** (v42) lira utilement ces futurs enfin distincts —
  c'est la **prochaine question**, et son prérequis est désormais rempli.

## 5. Notes méthodologiques

1. **Mesure sous drapeau forcé** : `sonde_horizon_branches` lancée telle quelle n'exécute
   jamais le parse d'arguments de `noyau.py` — `BRANCHES_PERSISTANTES` serait resté False et
   la sonde aurait mesuré l'**ancien** rollout sur des cerveaux BP (le piège du 01/09).
   `mesure_rollout_BP.py` force le drapeau dans les deux copies du module, puis délègue à la
   sonde (lecture seule : copie du `.brain`, jamais l'original).
2. **Incident de lancement** : le premier `xargs` a été cassé par des fichiers de reprise
   nommés « BP_gXX N.brain » (espaces) présents dans le dossier de campagne. Les 20 mesures
   ont été **rejouées sur les 20 cerveaux nominaux** (`BP_g<G>.brain`, ceux des logs à 1500
   jours) — vérifié 20/20 (`rollout_h7h1/BP_g*.json`).
3. La maîtrise est quantifiée à **5 %** (1 victoire = 5 % sur n=20) : la fenêtre finale
   moyenne (14 %) et la médiane sur les 100 derniers jours (16,9 %) sont à lire à cette
   résolution.

## 6. Fichiers

| Fichier | Rôle |
|---|---|
| `brains/07092026_branches_persistantes/depouiller_BP.py` | **créé** — 4 juges, apparié, Fisher, retrait des extrêmes, garde-fou |
| `brains/07092026_branches_persistantes/mesure_rollout_BP.py` | **créé** — mesure h7/h1 sous drapeau `BRANCHES_PERSISTANTES` forcé |
| `brains/07092026_branches_persistantes/agregat_BP.json` | **créé** — 40 runs |
| `brains/07092026_branches_persistantes/depouillement_BP.txt` | sortie brute |
| `brains/07092026_branches_persistantes/rollout_h7h1/` | 20 mesures (20 JSON) |

## 7. Liens

- [ROLLOUT_06092026](ROLLOUT_06092026_le_trou_noir_du_reflexe.md) — le trou noir du réflexe (cause mesurée)
- [EPOQUES_07092026](EPOQUES_07092026_le_mur_du_niveau_4_est_franchi.md) — le régime de base (K8_NU, témoin)
- [ABLATION_C2_05092026](ABLATION_C2_05092026_l_organe_muet.md) · [DETACH_C2_06092026](DETACH_C2_06092026_le_gradient_fantome_nuisait.md)
- [Point général du 07/09](../../etat_des_lieux/07092026_point_general_et_direction.md) §5 — ordre des décisions
- [Protocoles en réserve](../../ameliorations/07092026_protocoles_en_reserve.md) §5 — portes de décision (la v42 après la campagne de soustraction)

---

*27ᵉ campagne mesurée depuis le 23/08. La première dont le juge mécaniste passe à ce point
sans qu'aucun juge comportemental ne suive — le pattern « le canal est réparé, l'organe ne
s'en sert pas », écrit d'avance comme résultat acceptable.*
