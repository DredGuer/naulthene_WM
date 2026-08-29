# Le brain-sparing validé à n=20 — le premier effet démontré du projet

**17/08/2026** — carnet de recherche, non normatif.
Point 1 de la feuille de route utilisateur : *« La campagne n=20 pour consolider
définitivement les intervalles de Wilson sur la nouvelle dynamique de décision. »*

**Verdict : l'effet est réel, il est le plus fort jamais mesuré sur ce projet, et il
survit à la taille d'échantillon exigée par la règle de mesure.**

---

## 1. Le protocole

| Paramètre | Valeur |
|---|---|
| Graines | **20**, appariées (mêmes mondes des deux côtés) |
| Bras | témoin `--vigueur-sur-logits` (v41.15) · variante par défaut (v41.16) |
| Durée | 600 jours × 40 runs |
| Device | CPU forcé, 1 thread (`NAULTHENE_DEVICE=cpu`) — pas de mélange CPU/MPS |

Contrôles passés **avant** de lire les chiffres :

- les 40 logs comptent bien **600 jours** — aucun run tronqué ;
- **aucun crash**, aucune trace d'exception ;
- l'assertion runtime du drapeau apparaît côté témoin uniquement
  (`🔬 [ABLATION] brain-sparing v41.16 COUPÉ`) — l'ablation **atteint** le module,
  ce n'est pas une *ablation vide* ;
- à graine égale, les deux bras voient le **même monde** (10 ressources au jour 1 des
  deux côtés) — la correction de seedage v41.9 tient.

---

## 2. Le résultat principal — intervalles disjoints sur trois paliers

| Palier | témoin | variante | disjoints ? |
|---|---|---|---|
| niv 1 | 20/20 · 100 % [84–100] | 20/20 · 100 % [84–100] | — |
| **niv 2** | 13/20 · **65 %** [43–82] | 20/20 · **100 %** [84–100] | ✅ |
| **niv 3** | 13/20 · **65 %** [43–82] | 20/20 · **100 %** [84–100] | ✅ |
| **niv 4** | 0/20 · **0 %** [0–16] | 16/20 · **80 %** [58–92] | ✅ |

Le palier 4 est le plus parlant : **aucun témoin ne l'atteint, 16 variantes sur 20 y
arrivent.** Les intervalles ne se touchent pas ([0–16] contre [58–92]).

### Comparaison appariée

```
variante gagne 18 · perd 0 · nul 2   (n = 20)
test des signes, 18 paires discordantes : p = 0,0000
```

**Zéro défaite sur 20 graines.** C'est le seul résultat du projet où un bras ne perd
jamais une seule paire.

### Vitesse

| Palier | témoin (médiane) | variante (médiane) |
|---|---|---|
| niv 2 | jour **249** (n=13) | jour **80** (n=19) |
| niv 3 | jour **399** (n=13) | jour **125** (n=20) |
| niv 4 | *jamais* | jour **228** (n=16) |

La variante atteint au jour 125 le palier que le témoin atteint au jour 399 — **3,2× plus
vite**, quand il l'atteint.

---

## 3. Le paradoxe des victoires, et sa résolution

Une ligne contredit apparemment tout le reste :

```
victoires    témoin 386,2    variante 366,4    écart −19,8
```

**La variante gagne MOINS d'épisodes.** J'ai failli traiter ça comme un coût à signaler.
C'est un artefact de composition :

| | niv 1 | niv 2 | niv 3 | niv 4 |
|---|---|---|---|---|
| témoin | **60 %** | 12 % | 26 % | 0 % |
| variante | 21 % | 3 % | 30 % | **44 %** |

Le témoin passe **60 % de sa vie au niveau 1** — le plus facile, celui où l'on gagne
presque à chaque épisode. La variante y passe 21 % et vit **44 % de sa vie au niveau 4**,
qu'aucun témoin n'atteint.

> Un compteur de victoires brut **récompense la stagnation**. Il ne doit jamais servir de
> critère de comparaison entre deux bras qui ne vivent pas dans les mêmes mondes.

---

## 4. Le second résultat : C1 s'est remis à parler

C'est la mesure que je n'attendais pas, et elle explique le mécanisme.

| Grandeur (dernier quart du run) | témoin | variante | écart |
|---|---|---|---|
| énergie | 0,382 | 0,548 | **+0,166** |
| vigueur | 0,306 | 0,429 | **+0,122** |
| **ratio C2/C1** | 0,413 | **3,129** | **+2,715** |
| **entropie des votes C1** | **0,120** | **0,599** | **+0,479** |
| actions distinctes proposées par C1 | **1,78** | **4,58** | **+2,80** |

**Chez le témoin, C1 ne propose que 1,78 action distincte sur 7.** C'est une voix quasi
figée — la signature exacte du défaut : `softmax` n'est pas invariant par échelle,
multiplier les logits par `vigueur = 0,15` n'atténuait pas une préférence, il l'effaçait.

Chez la variante, C1 propose **4,58 actions distinctes** et son entropie de vote passe de
0,120 à 0,599. **La voix réflexe est redevenue une voix.**

⚠️ Et le ratio C2/C1 passe de 0,41× à **3,13×** — C2 pèse désormais **trois fois** C1 dans
la fusion. C'est un renversement complet de la situation historique du projet (« C2 est
éteint »). Ce n'est pas nécessairement un bien : voir §6.

---

## 5. Ce que ce résultat établit — et ce qu'il n'établit pas

**Établi :**

- retirer `vigueur` du produit sur les logits fait passer le taux d'atteinte du niveau 4 de
  **0 % [0–16]** à **80 % [58–92]**, sur 20 graines appariées, sans une seule défaite ;
- le mécanisme est identifié et mesuré : la voix C1 cesse d'être écrasée (1,78 → 4,58
  actions distinctes) ;
- le mur du niveau 4 documenté dans `MUR_17082026_le_verrou_P17.md` **n'était pas** un mur
  du curriculum P17 — il était en aval, dans la décision.

**Non établi :**

- **la part respective des deux lois.** Le bras « variante » active *à la fois*
  le brain-sparing (loi A) *et* l'économie d'action (loi B, `vigueur` déplacée sur le coût
  moteur). Cette campagne mesure leur **somme**. C'est exactement l'objet du plan factoriel
  en cours ;
- **rien au-delà du niveau 4.** 0/20 atteint le niveau 5 dans les deux bras. Le mur a
  reculé de trois paliers, il n'a pas disparu ;
- **rien sur 3000 jours.** Ces runs font 600 jours. La supériorité pourrait n'être qu'une
  avance de vitesse que le témoin rattraperait.

---

## 6. La question que ce résultat ouvre

Le ratio C2/C1 est passé de 0,41× à **3,13×**. C2 domine désormais la fusion.

Or le carnet [`SONDE_17082026_utilite_de_C2.md`](../SONDE_17082026_utilite_de_C2.md) mesure
que dans **43 %** des cerveaux, C2 est une **copie** de C1 (corrélation > +0,7). Un
doublon qui pèse trois fois plus n'est pas un progrès cognitif — c'est le même avis, plus
fort.

**La sonde d'utilité causale doit être repassée sur les cerveaux de cette campagne**, avant
d'attribuer le gain à « C2 est enfin écouté ». L'explication concurrente — et pour l'instant
la mieux étayée — est plus modeste : **l'agent a cessé de décider au hasard**, ce qui
suffit à expliquer les trois paliers gagnés sans qu'aucune délibération n'ait eu lieu.

C'est la lecture que je retiens tant qu'une mesure ne la contredit pas.
