# Campagne AB3 — `.detach()` asymétrique de C2 — RÉSULTATS

**40 runs terminés** (20 graines appariées × 1440 jours × 2 bras), 26/08/2026.
Bras A = nominal · Bras B = `--detach-c2` (C2 lit `pensee_bio` détaché).
Cursus complet, pas de `--env-force`. Métriques moyennées sur les **400 dernières nuits**.

## Verdict : AB3 N'AMÉLIORE RIEN. La correction ne se transmet pas au comportement.

| Métrique | A | B | δ | IC95 | t | B>A |
|---|---|---|---|---|---|---|
| **Niveau max atteint** | 4,150 | 4,050 | **−0,100** | ±0,281 | −0,70 | 3/20 |
| **Maîtrise (%)** | 15,61 | 9,52 | **−6,09** | ±6,17 | −1,93 | 7/20 |
| Énergie moyenne | 0,223 | 0,248 | +0,025 | ±0,037 | +1,36 | 11/20 |
| Satiété | 0,504 | 0,490 | −0,015 | ±0,024 | −1,20 | 6/20 |
| **Ratio C2/C1** | 3,210 | 4,262 | **+1,052** | ±0,540 | **+3,82** | 15/20 |
| Accord C1/C2 (%) | 14,56 | 12,41 | −2,15 | ±6,38 | −0,66 | 7/20 |
| Erreur JEPA | 0,012 | 0,013 | +0,001 | ±0,002 | +0,56 | 10/20 |
| Récolte/jour | 11,18 | 11,24 | +0,05 | ±1,12 | +0,09 | 7/20 |

**Bonferroni, 8 métriques, df=19 ⇒ seuil `t ≈ 3,25`.** Une seule le franchit : le ratio C2/C1.

## Le seul effet significatif est une TAUTOLOGIE

Décomposition du ratio (400 dernières nuits) :

| Composante | A | B | δ | t |
|---|---|---|---|---|
| **Amplitude C1** | 0,631 | 0,463 | **−0,168** | **−3,57** |
| Amplitude C2 | 1,807 | 1,861 | +0,054 | +1,70 |
| Actions distinctes C1 | 4,44 | 5,03 | +0,59 | +2,77 |
| Actions distinctes C2 | 4,71 | 4,75 | +0,05 | +0,14 |

Le ratio monte parce que **C1 s'affaiblit**, pas parce que C2 se renforce (`t=+1,70`, NS).
C'est exactement ce que le detach fait par construction : il retire à `integrateur_bio` le
gradient de C2, donc C1 hérite d'un tronc moins sculpté. **Ce n'est pas un gain cognitif,
c'est l'empreinte mécanique de l'ablation.**

## Robustesse du signe négatif sur la maîtrise

| Fenêtre | δ maîtrise | t | B>A |
|---|---|---|---|
| 100 nuits | −7,46 | −2,15 | 8/20 |
| 400 nuits | −6,09 | −1,93 | 7/20 |
| 720 nuits | −4,42 | −1,68 | 10/20 |
| 1440 nuits | −2,74 | −1,66 | 9/20 |

Le signe est **stable sur quatre fenêtres** et aucun `t` ne passe. C'est une tendance
défavorable non concluante — pas une preuve de nuisance, mais assez pour interdire toute
revendication de gain.

## Niveau par graine

5 graines bougent dans chaque sens : **4 en faveur de A** (g33, g111, g144, g188, g211),
**3 en faveur de B** (g11, g44, g66). Le reste est identique. Aucun bras ne dépasse le
**niveau 5/15** — le plafond de la v41.29 est intact.

## Ce que la campagne établit

1. **Le thrashing du gradient n'est PAS la cause du plafond.** AB3 corrige l'alignement
   (+25 % au banc) et ne déplace ni le niveau, ni la maîtrise, ni la récolte.
2. **La collision C1/C2 dans `integrateur_bio` est réelle mais bénigne** : la supprimer coûte
   16 % d'amplitude à C1 et ne rend rien.
3. **Le plafond au niveau 4 tient une neuvième réfutation.**

## Ce qui reste ouvert

- La chute au jour 9 observée au banc **n'apparaît pas** en cursus : aucun run n'a divergé.
  L'hypothèse de dérive du baseline n'est ni confirmée ni réfutée — elle est **sans objet ici**.
- L'anti-corrélation du fourrage (taux de saisie 10,7 % pour une faim de 0,963) reste
  inexpliquée et devient le suspect n°1.

## Reproduction

```bash
brains/26082026_v4132_AB3_cursus/lancer.sh
python /tmp/extract.py && python /tmp/stats.py   # scripts recopiés ci-dessous
```
