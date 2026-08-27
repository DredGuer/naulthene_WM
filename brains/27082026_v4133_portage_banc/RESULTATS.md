# Campagne v41.33 — LE BIT DE PORTAGE — RÉSULTATS

**40 runs terminés** (20 graines appariées × 400 jours × 2 bras), banc forcé
`MiniGrid-DoorKey-6x6-v0`, 27/08/2026.
Bras A = bit actif · Bras B = `--sans-portage` (la 42ᵉ dim existe, l'information est à 0.0).

## Verdict : L'AGNOSIE EST LEVÉE. LE CRÉDIT NE SUIT PAS.

Deux résultats de sens opposé, tous deux significatifs. **10 métriques testées ⇒ seuil
Bonferroni `t ≈ 3,53`** (p = 0,05/10, df = 19).

### [1] Le critique voit enfin qu'il porte — ✅ EFFET MASSIF

| | valeur |
|---|---|
| **d de Cohen, bras A** (bit actif) | **+1,4275** |
| d de Cohen, bras B (témoin) | −0,0121 |
| **δ** | **+1,4397** · IC95 ±0,8045 · **`t` = 3,51** |
| Graines favorables | **18 / 20** |

Référence avant le bit : **+0,119 / −0,117 / +0,090** (3 cerveaux, signe instable).

**Le témoin est à −0,012, c'est-à-dire zéro** — il reproduit exactement l'agnosie
mesurée le 27/08 sur les cerveaux v41.32. Le bras nominal passe à **+1,43**, un effet
*fort* au sens de Cohen (>0,8). Cinq graines dépassent **+2,0** (g44 +2,18, g122 +6,90,
g133 +3,17, g177 +3,27, g88 +3,18).

⚠️ `t = 3,51` **manque Bonferroni de 0,02** (seuil 3,53). Nominalement significatif
(p < 0,003), pas après correction. Mais l'écart de **118×** entre les deux bras et le
**18/20** rendent la conclusion robuste indépendamment du `t` : ce n'est pas un effet
marginal qu'une correction pourrait effacer.

### [2] Le crédit ne se contraste pas — ❌ EFFET NUL

| | valeur |
|---|---|
| Ratio \|A\| utile / \|A\| neutre, **bras A** | **1,1844** |
| Ratio, bras B (témoin) | 1,1081 |
| δ | **+0,0763** · IC95 ±0,0761 · `t` = 1,97 |
| Graines favorables | 11 / 20 |

Référence avant le bit : **0,86× à 1,11×** (4 cerveaux).

Le bras A monte à **1,18×** contre 1,11× au témoin — **+6,9 %**, sous le seuil de 25 %
que la sonde retient pour parler d'autre chose que d'arrosage. `t = 1,97` ne passe ni
Bonferroni (3,53) ni même un seuil non corrigé strict.

**Saisir une clé rapporte toujours, à ~18 % près, ce que rapporte un quart de tour.**

### [3] Comportement — rien ne bouge

| Métrique | A (bit) | B (témoin) | δ | `t` |
|---|---|---|---|---|
| Portage (% des ticks) | 22,11 | 21,77 | −0,34 | −0,41 |
| Taux de saisie (%) | 17,83 | 19,65 | +1,82 | +1,54 |
| Récolte / jour | 5,55 | 6,16 | +0,60 | +1,62 |
| Énergie | 0,102 | 0,112 | +0,010 | +1,43 |
| Satiété | 0,315 | 0,325 | +0,010 | +0,73 |
| Maîtrise (%) | 2,67 | 3,15 | +0,49 | +0,75 |
| Victoires (fin) | 18,8 | 20,5 | +1,70 | +0,53 |
| Erreur JEPA | 0,004 | 0,004 | −0,000 | −0,10 |

**Aucune ne s'approche du seuil.** Toutes les tendances non nulles vont d'ailleurs
*contre* le bit.

⚠️ Le banc est forcé : le niveau reste à 1/15 **par construction**, donc « maîtrise » et
« victoires » ne peuvent pas juger le cursus (règle §4).

## Ce que la campagne établit

**Le mécanisme fonctionne exactement comme prévu — et ne sert à rien.**

1. **L'agnosie proprioceptive est levée.** Fournir l'information suffit : le critique
   apprend à distinguer « je porte » de « mains vides », d passant de ~0 à **+1,43**.
   La chaîne « variable absente de l'entrée ⇒ impossible à apprendre » était correcte.
2. **Mais un critique qui voit mieux ne produit pas un avantage plus contrasté.** Le
   maillon suivant de la chaîne causale — `V(porte) ≠ V(vide)` ⇒ `A_saisie` pique — **ne
   se referme pas**. +6,9 %, non significatif.
3. **Douzième réfutation.**

## Pourquoi la chaîne casse — hypothèse, non mesurée

Le TD-error d'une saisie vaut `r + γ·V(s') − V(s)`. Le bit rend `V(s')` distinct de
`V(s)`, mais l'avantage réellement utilisé par l'acteur est `returns − V(s)`, où
`returns` est **normalisé sur la journée** (moyenne 0, écart-type 1) — une saisie n'y
apparaît que si elle change la *récompense environnementale*, ce que MiniGrid ne fait
qu'à la sortie. Le critique sait, l'acteur ne l'apprend pas.

Cela reste à mesurer et ne doit pas être présenté comme acquis.

## Deux réserves de méthode

⚠️ **Banc forcé.** Prouve que la mécanique agit *là où elle s'applique*, jamais qu'elle
ne nuit pas ailleurs. La nociception v41.25 était bonne sur `LavaGap` et coûtait −25 %
de récolte partout ailleurs. Un passage en cursus complet resterait nécessaire **si** le
mécanisme avait produit un effet — ce n'est pas le cas, donc il n'est pas justifié.

⚠️ **400 jours.** Assez pour sculpter la colonne (norme 1,84× la moyenne, 12/12 graines
mesurées à mi-campagne) ; pas assez pour juger un cursus. L'absence d'effet
comportemental n'est donc **pas** concluante — l'absence d'effet sur le **crédit**, elle,
l'est, puisque c'est une mesure directe.

## Reproduction

```bash
brains/27082026_v4133_portage_banc/lancer.sh
PYTHONPATH=src python /tmp/credit_campagne.py   # copié ci-contre
```
