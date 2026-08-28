# Campagne v41.34 — LE TRONC PERCEPTIF CONNECTÉ — RÉSULTATS

**40 runs terminés** (20 graines appariées × 400 jours × 2 bras), **cursus complet**,
28/08/2026. Bras A = `.detach()` historique · Bras B = `--tronc-connecte`.

## Verdict : L'HYPOTHÈSE EST FALSIFIÉE. Le bruit AUGMENTE de 48 %.

### [1] Le test de falsification — ❌ ÉCHEC FRANC

Prédiction : un signal de valeur atteignant `porte_visuelle` apprend à taire ce qui ne
vaut rien, donc `|V(t+1) − V(t)|` doit **baisser**.

| | valeur |
|---|---|
| **A** (tronc détaché) | **0,024016** |
| **B** (tronc connecté) | **0,035532** |
| δ | **+0,011516** · IC95 ±0,008328 · **`t` = +2,71** · **14/20** |

**Le bruit augmente de 48,0 %.** Le signe est l'inverse exact de la prédiction, et
l'effet est significatif au seuil nominal.

### [2] La garde — le bruit ne monte pas par effondrement de V

Un bruit qui *baisse* pourrait signifier un `V` aplati ; ici il monte, et `V` s'élargit
avec lui :

| | A | B | δ | `t` |
|---|---|---|---|---|
| écart-type de V | 0,0574 | 0,0871 | **+0,0297** | +2,87 |
| étendue de V | 0,3117 | 0,4013 | **+0,0896** | +2,03 |

Connecter le tronc **agite** la fonction de valeur : elle bouge davantage, dans une plage
plus large. C'est exactement le risque de collision inscrit au protocole — trois pertes
(JEPA, acteur, critique) tirant les mêmes couches perceptives.

### [3] ⚠️ MÉTRIQUE INVALIDE — à ne pas lire

La sonde publiait aussi un « rapport signal/bruit », le signal étant l'effet causal du
bit de portage. **Ce chiffre ne mesure rien ici** : ces cerveaux ont vécu les niveaux 1 à
4, où `🔑 Portage 0.0%` sur toute la campagne. Le bit n'a jamais rien porté de leur vie —
sa colonne n'a jamais été entraînée, et l'effet mesuré (0,0036 contre **+0,325** sur les
cerveaux v41.33, entraînés sur `DoorKey`) est celui d'un poids resté à son
initialisation.

C'est la **même erreur que la campagne du 27/08** — mesurer une variable là où elle est
inactive — attrapée cette fois *avant* publication et non après. Les métriques [1] et [2]
ne dépendent pas du bit et restent valides.

### [4] Comportement — 10 métriques, seuil Bonferroni `t ≈ 3,53`

| Métrique | A | B | δ | `t` |
|---|---|---|---|---|
| **Niveau max atteint** | **3,95** | **3,95** | **+0,00** | **+0,00** |
| Taux de saisie (%) | 22,93 | 18,27 | **−4,66** | **−3,63** |
| Maîtrise (%) | 16,18 | 19,87 | +3,68 | +2,25 |
| Victoires (fin) | 258,3 | 270,7 | +12,40 | +2,39 |
| Énergie | 0,219 | 0,251 | +0,032 | +2,33 |
| Erreur JEPA | 0,006 | 0,005 | −0,001 | −1,94 |
| Récolte / jour | 12,43 | 11,71 | −0,72 | −1,62 |
| Satiété | 0,507 | 0,495 | −0,012 | −0,88 |

**Le niveau ne bouge pas d'un iota** — 18 graines sur 20 identiques, une inversion dans
chaque sens (g44 A=3/B=4, g122 A=4/B=3). Le plafond au niveau 4 tient.

**Aucune métrique ne passe Bonferroni.** La plus forte est le **taux de saisie à
`t = −3,63`**, et elle est **défavorable** au bras connecté (−4,66 pts) — cohérent avec
un tronc plus agité. Trois métriques entre `t = +2,2` et `+2,4` (maîtrise, victoires,
énergie) sont favorables mais **ne survivent pas à la correction** (p corrigé ≈ 0,3).

## Ce que la campagne établit

1. **L'attention descendante ne réduit pas le bruit perceptif — elle l'augmente.** +48 %,
   `t = +2,71`, 14/20. L'hypothèse « la récompense apprend à l'œil ce qu'il faut taire »
   est réfutée dans cette architecture.
2. **La cause probable est la collision**, inscrite au protocole avant la mesure : trois
   pertes sculptent désormais les mêmes couches. `V` bouge plus (σ +52 %) et s'étale plus
   (étendue +29 %) — le tronc est agité, pas orienté.
3. **Le `.detach()` historique n'est donc pas de la dette technique** : il protège quelque
   chose de réel. Sa raison n'était pas documentée, elle est maintenant **mesurée**.
4. **Quatorzième réfutation.**

## Ce qui reste ouvert

Le résultat ne dit **pas** que l'attention descendante est une mauvaise idée en général —
il dit qu'elle échoue **sans découplage**. Une variante où seul le *critique* sculpte la
vue (l'acteur restant détaché) n'a pas été testée, et serait un bras à elle seule
(règle §6.2 : une mécanique par bras). Ce n'est pas une piste recommandée pour autant :
elle demanderait un run complet pour un mécanisme dont la version forte vient d'échouer.

## Décision sur le code

`TRONC_PERCEPTIF_DETACHE = True` reste la valeur par défaut — le comportement historique
est **bit-identique** (A/A vérifié, δ = 0). Le drapeau `--tronc-connecte` est conservé
comme témoin d'ablation, au même titre que `--sans-portage`.

## Reproduction

```bash
brains/28082026_v4134_tronc/lancer.sh
PYTHONPATH=src python /tmp/bruit_perceptif.py
```
