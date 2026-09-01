# LE RENDEMENT MÉCANIQUE — assainir 65 % du gradient ne change RIEN

**Date** : 2026-09-01 · **Statut** : ❌ **ÉCHEC sur le critère fixé d'avance** ·
**n = 20 graines appariées × 2 bras × 100 jours** · banc 150 épisodes, instrument corrigé.

---

## 1. La question posée

> « Un geste qui brasse du vent consomme de l'énergie métabolique mais n'ancre aucun
> renforcement synaptique. La politique motrice élimine d'elle-même les gestes à coût non
> nul et à rendement nul. »
>
> Juge de paix fixé par l'utilisateur **avant** la mesure : la **directivité**.
> *Succès* si elle chute **sous 6×** l'optimal. *Échec* si elle reste **≥ 12×**.

Mécanique livrée en v41.48 (commit `be7358f`), formule décidée par l'utilisateur :

```
A_t > 0  →  A_t × rendement     un succès stérile n'ancre RIEN
A_t ≤ 0  →  A_t                 un échec stérile reste PUNI
```

## 2. Le protocole

| Élément | Valeur |
|---|---|
| Bras | **ACTIF** (v41.48) vs **TÉMOIN** (`--sans-rendement`) |
| Graines | **20**, appariées (11 · 22 · … · 222) |
| Jours | 100 par run · **40 runs** |
| Environnement | `--env-force MiniGrid-SimpleCrossingS9N1-v0` |
| Banc | `sonde_plancher_geometrique`, 150 épisodes, graines appariées |

## 3. Les chiffres bruts

| Graine | ACTIF % | TÉM % | ACTIF dir | TÉM dir |
|---|---|---|---|---|
| 11 | 5,33 | 0,00 | 22,38 | — |
| 22 | 2,00 | 2,00 | 18,08 | 22,75 |
| 33 | 4,67 | 10,00 | 15,25 | 21,00 |
| 44 | 3,33 | 3,33 | 20,42 | 20,83 |
| 55 | 5,33 | 1,33 | 17,54 | 15,96 |
| 66 | 1,33 | 1,33 | 20,67 | 21,29 |
| 77 | 19,33 | 0,67 | 18,92 | 17,42 |
| 88 | 1,33 | 1,33 | 21,46 | 19,88 |
| 99 | 8,00 | 17,33 | 17,12 | 15,33 |
| 111 | 28,67 | 8,00 | 17,58 | 18,38 |
| 122 | 11,33 | 13,33 | 19,00 | 16,38 |
| 133 | 17,33 | 15,33 | 17,42 | 17,92 |
| 144 | 0,67 | 6,00 | 19,75 | 20,92 |
| 155 | 18,00 | 12,67 | 19,58 | 19,33 |
| 166 | 8,00 | 20,00 | 20,79 | 13,58 |
| 177 | 35,33 | 23,33 | 14,25 | 16,42 |
| 188 | 0,00 | 1,33 | — | 19,54 |
| 199 | 0,00 | 2,00 | — | 18,67 |
| 211 | 1,33 | 6,00 | 21,62 | 17,25 |
| 222 | 4,67 | 22,67 | 19,50 | 18,75 |

### Les agrégats

| Grandeur | Valeur | `t` apparié |
|---|---|---|
| **δ succès** | **+0,400 pt** | **+0,193** (NS) |
| **δ directivité** | **+0,328×** (mauvais sens) | **+0,443** (NS), n=17 |
| **Directivité ACTIF médiane** | **19,25×** | — |
| Directivité TÉMOIN médiane | 18,67× | — |

🔴 **VERDICT : ÉCHEC.** Le seuil d'échec était **≥ 12×** ; on mesure **19,25×**, soit
**1,6× ce seuil**. La cible de succès (< 6×) n'est pas approchée. Le δ de directivité est
non seulement non significatif, il est **du mauvais signe**.

## 4. Les vérifications passées

| Vérification | Résultat |
|---|---|
| **Ablation vide ou négative ?** | ✅ **NÉGATIVE** — télémétrie présente sur les 20 runs ACTIF, **absente** sur les 20 TÉMOIN. Le mécanisme a bien agi |
| **Le rendement varie-t-il ?** | ✅ **0,007 à 0,171** selon la graine — l'agent livre 0,7 % à 17 % du travail engagé |
| **Saturation du budget ?** | ✅ **NON** — max ACTIF 22,38×, max TÉMOIN 22,75×, plafond arithmétique **27,0×** |
| **Tautologie** (directivité définie sur les seules victoires) | ✅ contrôlée — 3 graines à zéro victoire (ACTIF : 188, 199 · TÉMOIN : 11), **n tombe à 17** |
| **Répartition graine par graine** | 🔴 **pile ou face** : succès ACTIF mieux sur **7**, pire sur **9**, égal sur 4 ; directivité mieux sur **8**, pire sur **9** |
| **A/A préalable** | ✅ δ = 0 sur les deux bras (2 réplicats chacun) |
| **Nuit complète** | ✅ 3 nuits, 0 erreur |

⚠️ **Victoires au banc** : ACTIF 264, TÉMOIN 252 sur 3 000 épisodes par bras. L'écart de
12 victoires est du bruit à cette échelle.

## 5. Ce que ça réfute exactement

**La prémisse était juste, la conclusion ne suit pas.** L'Étape 0 avait correctement mesuré
que **64,6 % du budget** est un travail à rendement nul ou quasi nul, et le mécanisme a bien
retiré ce crédit du gradient d'acteur. **La politique n'a pas changé pour autant.**

C'est la **vingtième** explication mesurée et réfutée. Elle rejoint un motif déjà vu trois
fois sur ce dépôt :

| Mécanique | Ce qu'elle corrigeait | Effet comportemental |
|---|---|---|
| Curiosité (30/08) | rente de 40 % du signal | **15,0 % vs 15,0 %** de maîtrise |
| Agnosie proprioceptive (23-30/08) | d' : −0,012 → +1,428 | **aucun** |
| Cristallisation (v41.44) | 0 synapse sur 1,9 M | non mesuré en comportement |
| **Rendement mécanique (01/09)** | **64,6 % du gradient assaini** | **+0,4 pt (`t` = +0,19)** |

> **Le signal d'apprentissage n'est pas le goulot.** On l'a nettoyé de la curiosité, du
> barème, du crédit temporel, et maintenant du travail stérile. À chaque fois la mesure
> confirme que le défaut existait ; à chaque fois le comportement ne bouge pas.

## 6. Les limites — écrites d'avance, au protocole

1. **Un banc forcé ne prouve rien sur le cursus** (règle de mesure §6). `--env-force`
   court-circuite la promotion : le niveau reste à 1/15 **par construction**.
2. **100 jours est court.** Un effet n'apparaissant qu'à 1 500 jours serait invisible ici.
   ⚠️ Mais l'Étape 2 était **conditionnée** à une baisse nette de la directivité — elle
   n'a pas lieu d'être lancée.
3. `SimpleCrossing` **n'a ni porte ni clé** : trois des quatre gestes stériles le sont par
   construction. Un gain y aurait été **surestimé**, pas sous-estimé — ce qui rend le
   résultat nul d'autant plus net.
4. **n = 17** pour la directivité (3 graines sans victoire), pas 20.

## 7. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** : la brique C. Assainir le bénéfice du gradient ne tend pas le trajet, et ne
change pas le taux de succès. Le levier que `CLAUDE.md` désignait depuis la v41.28 (« le
levier suivant est le BÉNÉFICE, pas le coût ») **a été actionné et ne donne rien**.

**Ouvert** :
- La **brique B** (inertie proprioceptive — injecter le vecteur vitesse dans le bus). Sa
  prémisse est **confirmée** par l'Étape 0 : `P(avancer|avancer)/P(avancer) = 0,9959`,
  autocorrélation motrice **nulle**. Elle est intacte, et c'est la seule des trois qui
  ajoute une **information** au réseau au lieu de retoucher son barème.
- ⚠️ **Le code v41.48 reste en place, ACTIF par défaut.** Il n'est pas nuisible (δ succès
  +0,4 pt, `t` = +0,19) et son témoin `--sans-rendement` est câblé. Décision utilisateur
  requise : le laisser ou le passer à `False` par défaut.
