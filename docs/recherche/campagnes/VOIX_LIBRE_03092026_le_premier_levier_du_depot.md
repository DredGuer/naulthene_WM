# LA VOIX LIBRE — le premier levier interne mesuré du dépôt

**Date** : 2026-09-03 · **Statut** : ✅ **JUGES 1 ET 2 PASSÉS, JUGE 3 REQUALIFIÉ** ·
**n = 20 graines appariées × 2 bras × 100 jours** · banc 300 épisodes, instrument v41.50.

> **Protocole écrit AVANT le lancement** (`brains/02092026_brasA_voix_libre/LISEZ_MOI.md`,
> 02/09), critères pré-enregistrés, A/A passé. Le dimensionnement
> (`DIMENSIONNEMENT.md`) a été écrit **pendant** la campagne, avant tout dépouillement des
> juges 2 et 3.

---

## 1. La question posée

Les 21 réfutations précédentes ont toutes manipulé ce qui **ENTRE** dans le réseau. Aucune
n'avait regardé ce qui en **SORT**.

Or `penser()` calcule `gain_c1 = clamp(2,1 × f / amplitude_c1, 0,25, 4)` : la voix de C1 est
renormalisée **à chaque tick, dans les deux sens**. Softmax étant invariante par translation
mais **pas par échelle**, la **netteté de la politique n'est pas apprenable** — le réseau a
beau apprendre à être sûr de lui, on lui remet le volume à zéro juste avant de décider.

**Le bras A retire ce mécanisme** (`--gain-c1-libre` : `gain_c1 ≡ 1,0`). On **retire**, on
n'ajoute rien. C2 intact, un seul bras par mécanique.

## 2. Les trois juges, posés d'avance

| Juge | Critère | Mesuré | Verdict |
|---|---|---|---|
| **1. Le mécanisme mord-il ?** | H jouée médiane LIBRE **< 1,75** | **1,513** (témoin 1,702) | ✅ **PASSE** |
| **2. Succès** | > 25 %, δ apparié significatif | **24,17 %** vs 11,73 % — δ **+12,43 pt** | ✅ **PASSE** |
| **3. Directivité** | médiane **< 10×** | **13,21×** (témoin 17,33×) | 🟡 **échoue en absolu** |

### Juge 2 — le chiffre central

| | Valeur |
|---|---|
| LIBRE | **24,17 %** |
| TÉMOIN | **11,73 %** |
| **δ apparié** | **+12,43 pt** (écart-type 10,66) |
| **`t`** | **+5,214** — seuil Bonferroni (2 métriques) : 2,43 |
| Favorables | **18 / 20** |

**Le taux de succès double.** C'est le premier effet interne significatif du dépôt après
21 réfutations.

### Juge 1 — la mécanique est bien la cause

δ apparié d'entropie **−0,1706** (`t = −4,934`), **16/20** plus nettes. Retirer le gain
libère bien la netteté : le mécanisme visé est celui qui a bougé.

### Juge 3 — amélioration massive, seuil absolu manqué

δ apparié **−5,25×** (`t = −6,296`, n=19), **18/19** plus directifs. Les trajets se
raccourcissent fortement (17,33× → 13,21×) mais restent **browniens** : le critère `< 10×`
n'est pas atteint.

> **Lecture** : la netteté rend l'agent **plus efficace**, pas **dirigé**. Il gagne deux fois
> plus souvent en errant un peu moins — il ne marche toujours pas droit vers le but.

---

## 3. Les vérifications — toutes passées

| # | Vérification | Résultat |
|---|---|---|
| 1 | **Témoin aléatoire** | **5,67 % sur 40/40** — l'invariant du dépôt, à la décimale |
| 2 | Saturation de budget (≥ 27,0×) | **0** cerveau |
| 3 | Graines à 0 victoire | LIBRE **0** · TÉMOIN **1** (g155) |
| 4 | **Sans les 4 extrêmes** | δ = **+8,44 pt**, `t = +4,855` (n=16) ✅ |
| 5 | Sans les témoins au plancher (< 5 %) | δ = **+9,11 pt**, `t = +4,651` (n=15) ✅ |
| 6 | Mode d'échec v37.0 (C1 écrase C2) | ratio médian **0,535** · **0/20** sous 0,3 |
| 7 | Régime sérialisé | `gain_c1_libre` = True sur 20/20 LIBRE, False sur 20/20 TÉMOIN |
| 8 | Drapeau atteint l'individu | 20/20 logs LIBRE, **0/20** témoins contaminés |

⚠️ **La vérification n°4 est celle qui avait fait tomber la directivité** le 02/09 (`r`
passait de −0,679 à −0,478, NS). Ici l'effet **survit** au retrait des extrêmes : il n'est
pas porté par quelques graines chanceuses.

### La tête motrice a réellement grandi

| Bras | Amplitude C1 médiane (fin de run) | Ratio C2/C1 |
|---|---|---|
| TÉMOIN | 1,215 | 2,055 |
| **LIBRE** | **4,526** (**×3,7**) | 0,535 |

C'est la réponse à la question ouverte du protocole (« si LIBRE reste dans [0,33 ; 0,91], la
tête n'a pas grandi — voir F4 »). **Elle a grandi.** Le budget d'apprentissage (bras B)
n'est donc **pas** le goulot ici.

---

## 4. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** — l'affirmation « aucune mécanique cognitive n'a jamais rien amélioré » (0/9 puis
0/21). **Elle est fausse depuis ce matin.** Il existe un levier interne, et c'est une
**contrainte de sortie**, pas une entrée sensorielle.

Cela confirme aussi le motif du 02/09 par l'autre bout : ajouter de l'information ne servait
à rien parce que **la conversion information → politique était bridée en aval**. Le réseau
savait ; il n'avait pas le droit de le dire.

**Ouvert, et important :**

1. ⚠️ **La politique n'a PAS atteint son asymptote.** L'entropie descendait encore à
   −0,00745/jour dans 12/15 graines à j100 (plateau extrapolé vers **j170-200**). Ce δ de
   **+12,43 pt** est donc mesuré sur une politique **intermédiaire** (H ≈ 1,5 au banc). Le
   résultat vaut pour « la netteté à H ≈ 1,5 » — l'effet à l'asymptote est **inconnu**, et
   peut être plus grand comme plus petit.
2. ⚠️ **Banc forcé** : ne prouve **rien** sur le cursus (règle de mesure §6). `--env-force`
   court-circuite la promotion. **Un run en cursus complet est obligatoire** avant toute
   revendication.
3. 🔴 **L'ablation « C2 coupé = 0,0 pt » est confondue et doit être refaite.** `c2_coupe`
   pose `force = 0`, donc `vigueur_min_c1(0) = 0`, donc `gain_c1 = 0,25` : couper C2
   divisait **aussi** C1 par 6 à 14. Les deux bras étaient quasi uniformes. Avec
   `gain_c1_libre`, le test redevient propre — **« C2 ne sert à rien » n'est pas réfuté, il
   n'est pas établi.**
4. La directivité reste brownienne : elle n'est donc **pas** le levier, plutôt un
   **symptôme** — cohérent avec la mesure du 01/09 (λ=0,9 : meilleure directivité, pire
   succès).

---

## 5. Ce qu'il faut faire ensuite, par ordre

| # | Chantier | Pourquoi |
|---|---|---|
| 1 | **Rejouer à 200 jours** | le seul moyen de savoir ce que vaut la netteté à l'asymptote. ~9 h. |
| 2 | **Cursus complet, sans `--env-force`** | obligatoire avant toute revendication publique |
| 3 | **Refaire l'ablation C2** sous régime libre | l'un des résultats les plus cités du dépôt est confondu |
| 4 | Bras C (C2 seul) | seulement après 3 |

⚠️ **Rien de ceci n'autorise encore à modifier les README.** Le résultat est acquis **au banc
forcé** ; la règle de mesure exige le cursus complet avant publication.

---

## 6. Protocole exact (reproductible)

```bash
# 40 runs — 20 graines × 2 bras × 100 jours
zsh brains/02092026_brasA_voix_libre/lancer.sh     # ~4 h 30
# 40 bancs — 300 épisodes, force = acceptation() du cerveau
zsh brains/02092026_brasA_voix_libre/banc.sh       # ~9 h 24
```

Graines : 11 · 22 · 33 · 44 · 55 · 66 · 77 · 88 · 99 · 111 · 122 · 133 · 144 · 155 · 166 ·
177 · 188 · 199 · 211 · 222. Agrégat machine : `brains/02092026_brasA_voix_libre/agregat.json`.

⚠️ **Incident consigné** : deux lanceurs ont tourné simultanément sur `g177` le 02/09 à
21h01. Le `.brain` tronqué (~5 nuits) est archivé dans `_ecarte_collision/`, la graine a été
rejouée proprement. **Un script idempotent protège du doublon de travail, pas du doublon
d'écrivain** — vérifier `ps aux | grep lancer.sh` avant tout lancement.
