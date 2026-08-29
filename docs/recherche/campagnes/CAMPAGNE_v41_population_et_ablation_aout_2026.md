# Campagne v41 — 10 graines × 2000 jours + 78 cellules d'ablation

> **Carnet de recherche — non normatif.** Il raconte une campagne de mesure, avec ses
> révisions de lecture successives. Pour l'état courant, voir
> [CHANGELOG.md](../../fonctionnement/CHANGELOG.md).
>
> Campagne lancée le **14 août 2026 à 19h31**, terminée le **15 août 2026**.
> Code : `feat/v41-ligne-flottaison`, commits `04080c4` (code) + `1f3854f` (cas isolé).

---

## Ce qu'on cherchait à savoir

La v41 avait produit **le premier franchissement de palier du projet** : g22 atteint le
niveau 4/15 et y tient 1223 jours, là où **zéro graine V40** n'avait quitté le niveau 1
en 2000 jours ([chantier v41 §10](../../ameliorations/CORRECTIFS_v41_ligne_de_flottaison.md)).

Mais ce résultat reposait sur **3 graines**, dont une seule avait débloqué. Le chantier
notait déjà l'ambiguïté (§10.3, « la loterie natale ») : la divergence entre les trois
graines était visible dès la **nuit 1**, avec un écart de `danger` de **38×** au jour 50.

D'où deux questions, et deux protocoles :

| Question | Protocole |
|---|---|
| **1/3 est-il le taux réel de déblocage ?** | 10 graines fraîches × 2000 jours |
| **À quoi servent réellement les organes ?** | Ablation 13 lésions × 3 niveaux × 2 cerveaux |

---

## Protocole

**Population** — 10 graines (101, 202, 303, 404, 505, 606, 707, 808, 909, 111), 2000
jours chacune, code v41 identique, aucune reprise de `.brain` existant. Relevés
automatiques aux jours 500 / 1000 / 1500 / 2000.

**Ablation** — 13 lésions × 3 niveaux × 2 cerveaux = **78 cellules**, 30 jours × 10
épisodes = 300 épisodes par cellule, graine fixée par cerveau.

> ⚠️ **Correction du défaut de protocole du 14/08.** La campagne d'ablation précédente
> avait mesuré un témoin à **0 %** — une ablation dont le témoin est nul ne mesure rien,
> puisque aucune lésion ne peut faire baisser un score déjà au plancher. Ici **chaque
> cerveau est ablaté sur SES PROPRES niveaux** : g11 sur les niveaux 0/1/2 (où il vit),
> g22 sur 3/4/5. Témoins obtenus : 44,7 % / 46,7 % / 27,0 % (g11) et 8,7 % / 8,7 % /
> 45,7 % (g22). Le défaut est corrigé.

---

## Résultat 1 — la population : **0 promotion sur 10 graines**

### Jalon terminal, 2000 jours

| Graine | Niveau | Maîtrise | Victoires | Force | okay / danger | Accord C1/C2 |
|---|---|---|---|---|---|---|
| g101 | 1/15 | 20 % | 627 | 0,372 | 402 / 676 | 2 % |
| g202 | 1/15 | 35 % | 1152 | 0,384 | 422 / 677 | 2 % |
| g303 | 1/15 | **40 %** | 710 | 0,387 | 429 / 677 | 0 % |
| g404 | 1/15 | 5 % | 601 | 0,382 | 419 / 676 | 1 % |
| g505 | 1/15 | 15 % | 789 | 0,382 | 415 / 672 | 0 % |
| g606 | 1/15 | 15 % | 196 | 0,536 | 423 / **365** | 0 % |
| g707 | 1/15 | 20 % | 864 | 0,373 | 403 / 677 | **33 %** |
| g808 | 1/15 | 20 % | 908 | 0,353 | 369 / 676 | 0 % |
| g909 | 1/15 | 30 % | 409 | 0,384 | 423 / 677 | 2 % |
| g111 | 1/15 | 15 % | **1346** | 0,386 | 427 / 676 | 0 % |

**Toutes au niveau 1/15.** Maîtrise maximale jamais atteinte sur toute la campagne :
**40 %**, pour un seuil de promotion à 60 %. Total cumulé : **7 602 victoires**, aucune
n'a suffi.

### Le verdict sur la loterie natale

> **Le déblocage de g22 n'est pas une propriété du correctif v41.**

10 graines fraîches sur le même code n'ont pas quitté le niveau 1. Le taux de déblocage
n'est donc pas « 1 sur 3 » mais au plus **1 sur 13**. Le succès de g22 était un tirage
favorable, et le chantier v41 avait raison de flaguer l'ambiguïté plutôt que de
revendiquer le résultat.

Face à l'étalon V40 (zéro graine hors du niveau 1 en 2000 jours) : **match nul**.

### Le découplage victoires / progression

C'est le fait le plus net de la population :

| | g111 | g909 |
|---|---|---|
| Victoires | **1346** | 409 (3,3× moins) |
| Maîtrise finale | 15 % | **30 %** (2× mieux) |

Et à mi-parcours, le même découplage sur le vécu — j500, g303 (42 victoires) contre g707
(353 victoires, ×8,4) : `okay` 296 contre 297, `danger` 360 contre 360, force 0,450
contre 0,451. **Huit fois plus de victoires, vécu identique au millième.**

Le nombre de victoires ne prédit ni la maîtrise ni le vécu. Le mur du cursus n'est pas
le nombre de succès mais leur **régularité** sur la fenêtre glissante de 20 épisodes.

### L'accord C1/C2 : un transitoire de 500 jours

| Jalon | 500 | 1000 | 1500 | **2000** |
|---|---|---|---|---|
| Accord médian | **37 %** | 21 % | 4 % | **0,5 %** |

Décroissance monotone. Au jalon 500, l'accord montait à 36–86 % contre **0 % historique**
(mesure de référence du [chantier v37](../../ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md),
où les deux têtes n'étaient d'accord sur *aucun tick*). C'était le gain le plus visible
de la v41 — **il ne survit pas à 2000 jours** et retourne au niveau d'avant-correctif.

### Les variables mortes

| Variable | État terminal |
|---|---|
| `envie` | **1,0000 sur 10/10**, à tous les jalons depuis j263 |
| `danger` | **676 sur 9/10**, à l'unité près |
| accord C1/C2 | 0 % sur 7/10 |

Trois des grandeurs censées piloter l'arbitrage ne portent plus d'information au terme du
run. C'est le **fil n°2** de l'[INDEX](../../INDEX.md) (« une variable saturée cesse de
porter de l'information ») rencontré pour la septième fois.

---

## Résultat 2 — l'ablation : **C2 est déconnecté du comportement**

### Le zéro qui domine la campagne

`c2_coupe` : **+0,0 sur les 6 niveaux.** `c2_horizon_court` : **+0,0 sur les 6 niveaux.**
Douze mesures, douze zéros exacts, deux cerveaux indépendants, 300 épisodes par cellule.

Ce n'est plus « C2 n'apporte rien » — c'est **C2 n'a aucun effet mesurable sur le
comportement**. Un système qu'on débranche entièrement sans que le score bouge d'un
dixième de point ne participe pas à la décision.

**Deux mesures indépendantes convergent** : l'accord C1/C2 tombé à 0,5 % (population) et
l'ablation nulle de C2 (banc). La v41 a bien réanimé C2 dans les métriques — amplitude,
ratio, non-extinction — mais **ce réveil est décoratif** : C2 parle, et personne
n'écoute.

### Les six mécaniques inertes

| Lésion | Effet sur les 6 niveaux |
|---|---|
| `ouie_coupee` | **+0,0 × 6** |
| `gout_coupe` | **+0,0 × 6** |
| `exo_coupe` | **+0,0 × 6** |
| `odorat_coupe` | +0,0 × 5, −0,7 × 1 |
| `c2_coupe` | **+0,0 × 6** |
| `c2_horizon_court` | **+0,0 × 6** |

**Six lésions sur treize ne changent rien.** Quatre des six sens — ouïe, goût, odorat,
Exo-Sens — sont coupables sans conséquence.

### Ce qui porte réellement quelque chose

| Lésion | g11 : N0 / N1 / N2 | g22 : N3 / N4 / N5 |
|---|---|---|
| `toucher_coupe` | −4,4 / −5,4 / −6,7 | −5,0 / −1,7 / **+3,3** |
| `bio_coupe` | −4,4 / −3,4 / **−8,0** | −3,4 / −0,7 / +1,0 |
| `vue_coupee` | −3,4 / **+3,0** / −3,3 | −2,7 / +1,0 / +1,6 |

Le **toucher** et le **vecteur bio** sont les deux seuls organes dont la perte coûte de
façon consistante, et l'effet **grandit avec la difficulté** (bio : −4,4 sur `Empty-5x5`
→ **−8,0** sur `Longue distance`). La **vue est instable** : elle aide sur trois niveaux
et nuit sur trois autres.

### L'anomalie — les mémoires sont nuisibles

| Lésion | Niveaux où couper AMÉLIORE |
|---|---|
| `hippocampe_fige` | +2,0 · +1,6 · **+4,7** · +2,6 → **4 sur 6** |
| `episodique_coupe` | +1,3 · +1,6 · +2,0 · +2,3 → **4 sur 6** |
| `spatiale_coupee` | +3,6 · +1,0 → 2 sur 6 |

**Figer la mémoire tampon court terme rend l'agent meilleur** sur la majorité des
niveaux. Les trois mécaniques mnésiques injectent du contexte qui **dégrade** la décision
au lieu de l'informer.

Une seule exception, et elle est nette : sur `Primaire 3 (Ramasser)`, `spatiale_coupee`
coûte **−7,4** — le plus gros effet positif d'un organe mnésique de toute la campagne.
C'est le seul niveau où la mémoire spatiale gagne son existence.

### Précaution de lecture — le plancher g22

Les niveaux `Contourner` et `Éviter le danger` ont un témoin à **8,7 %** (≈ 26 succès sur
300 épisodes). À ce plancher, les écarts de ±1 à 2 points sont dans le bruit et ne
doivent pas être interprétés. En revanche **les zéros exacts restent lisibles** : un
effet nul reste nul quel que soit le plancher.

---

## Révisions de lecture — ce que j'ai lu de travers en cours de route

Consignées parce que le carnet sert autant à garder les erreurs de diagnostic que les
résultats.

| Jalon | Lecture initiale | Correction |
|---|---|---|
| j500 | « g606 est une **seconde solution stable** » (danger 27 contre 360, plus de victoires que g303) | Faux — à j1000 il est à **551 jours sans victoire**. C'était un décrochage en cours, pas un régime. |
| j1000 | « `danger` **sature** à 541, borne atteinte, 8 graines au même millième » | Faux — le plafond monte : 541 → 631 → 676. Ce n'est pas une butée dure mais une **convergence forcée qui dérive**. La conclusion pratique (danger ne discrimine rien) tient, le mécanisme décrit était faux. |
| j1000 | « g111 est **la seule trajectoire ascendante** », 50 % pour un seuil à 60 % | Faux — redescend à 30 % puis **15 %**, avec 1346 victoires. Les 50 % étaient une fluctuation de la fenêtre glissante de 20 épisodes. Un point unique n'est pas une tendance. |
| j1500 | g606 « mort cognitive » | Nuancé — remonte à 89 de danger et regagne à j1424 après 551 jours. Trois révisions sur cette graine : **je m'abstiens de lui prêter une trajectoire.** |

La leçon commune : **sur une métrique à fenêtre glissante, un jalon isolé ne porte pas de
tendance.** Même défaut de méthode que la projection d'envie démentie en v41
(cf. CHANGELOG, « Note de méthode »).

---

## Conséquence directe — une affirmation du README est fausse

Les deux README affirment que **« couper C2 double le taux de succès »**. La mesure de
cette campagne, sur 6 niveaux et 2 cerveaux, donne **0,0 point d'écart**.

L'affirmation doit être corrigée dans `readme.md` **et** `readme_fr.md` dans le même
commit (règle de miroir, CLAUDE.md §Projet Overview). C'est le genre de chiffre qu'un lecteur
vérifie en cinq minutes.

---

## Bilan

Deux résultats solides, appuyés sur **20 000 jours simulés + 78 cellules** :

1. **Le déblocage de g22 n'est pas reproductible** — 0 promotion sur 10 graines. La v41
   corrige une erreur d'échelle réelle, mais ne fait pas franchir le cursus.
2. **C2 est déconnecté du comportement** — débranchable sans effet, sur aucun niveau,
   dans aucun des deux cerveaux. Et quatre sens sur six sont inertes, tandis que les
   trois mémoires sont plutôt nuisibles.

Ce que la v41 corrigeait — l'erreur comptable qui tuait C2 — était réel et reste acquis.
Ce qu'elle n'a pas produit, c'est un effet de ce réveil sur les actes.

**9ᵉ mécanique cognitive testée, 9ᵉ sans apport démontré.** Le constat de
l'[ETAT_DU_PROJET](../ETAT_DU_PROJET_aout_2026.md) — « les deux seuls leviers qui marchent
sont des propriétés du MONDE » — sort renforcé de cette campagne.

---

## Données brutes

| Quoi | Où |
|---|---|
| Logs population (10 × 2000 j) | `/private/tmp/v41_pop_g*.log` (non versionnés) |
| Logs ablation | `/private/tmp/abl_g11.log`, `/private/tmp/abl_g22.log` |
| Cerveaux population | `brains/140820261931_V41_2000_g*_RMD.brain` |
| Cas isolé g22/g11 | `brains/cas_isole_g22_v41/` |

---

*Carnet ouvert le 15 août 2026. Les pistes de correctif issues de cette campagne sont
tenues en réserve à la demande de l'utilisateur — voir
[chantier v41 §11](../../ameliorations/CORRECTIFS_v41_ligne_de_flottaison.md).*
