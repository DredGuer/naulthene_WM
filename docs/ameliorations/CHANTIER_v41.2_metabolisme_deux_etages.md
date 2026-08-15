# Chantier v41.2 — Le métabolisme à deux étages (satiété / énergie)

> **Statut : PROPOSÉ — aucune ligne de code écrite.** Document de cadrage, à valider avant
> implémentation. Branche cible : `feat/v41-ligne-flottaison` (tests isolés).
>
> Date : 15 août 2026 · Origine : lecture utilisateur de la description sensorielle
> (« il souffre en permanence »), qui a identifié trois défauts d'un coup.
>
> **Prérequis de lecture** : [CONCEPTION_v34_fatigue_mortalite.md](CONCEPTION_v34_fatigue_mortalite.md)
> — la mortalité y est déjà cadrée, ses options écartées y sont consignées, et son §4
> (constantes-bornes vs variables-dérivées) est la doctrine appliquée ici.

---

## 1. Le défaut, mesuré

L'agent vit **400 ticks sur 400 en zone critique métabolique**, tous les jours, sur les
10 graines de la campagne v41. Ce n'est pas une difficulté : c'est une **erreur d'échelle
temporelle**.

| Grandeur | Mesure | Référence biologique |
|---|---|---|
| Durée d'une journée | **400 ticks** | le code dit ailleurs **3600** (`TICKS_PAR_JOUR_BEBE`, « cycle nycthéméral complet ») |
| Satiété 1.0 → 0 | **86 ticks** | 2,4 % d'une vraie journée |
| Hydratation 1.0 → 0 | **200 ticks** | 5,6 % |
| Repas nécessaires si journée = 3600 ticks | **104/jour** | 3/jour |
| Repas réellement pris | **1 à 2/jour** | — |
| Déficit typique vécu | **2,00 / 3,00** | — |
| `r_bio` d'un tick ordinaire, jauges vides | **−0,0011** constant | — |

**L'échelle est fausse d'un facteur ~35.** Et une fois les jauges au plancher, elles ne
peuvent plus descendre : `r_bio` devient un bruit constant légèrement négatif. Le vécu perd
sa variance — donc son information.

> C'est la **cause amont** du défaut corrigé en v41. La ligne de flottaison rattrapait
> après coup un signal déjà écrasé dans le corps. Ici on traite la source.

### Le lien direct avec les résultats de la campagne

| Symptôme mesuré (campagne v41) | Explication métabolique |
|---|---|
| `danger` = 676 sur **9 graines sur 10**, à l'unité près | un vécu sans variance produit un danger sans variance |
| `envie` = 1,0000 sur 10/10 depuis j263 | idem, saturation |
| 1346 victoires → 15 % de maîtrise (g111) | les victoires ne se distinguent pas du bruit de fond |
| C2 débranchable à **+0,0 pt** | un agent en famine permanente n'a rien à planifier : il n'a qu'une urgence |

Cette dernière ligne est la plus importante. **On ne reconnecte pas C2 en le forçant** — ce
serait un `if` déguisé, refusé trois fois par le projet. On lui donne un monde où délibérer
a un sens.

---

## 2. Décisions utilisateur (prises le 15/08)

| # | Question | Décision |
|---|---|---|
| 1 | Journée à 3600 ticks ? | ✅ **Oui, cible = 3600.** Tests de réglage à **400 ticks (÷9)**, runs de **300 jours** pour la chasse aux bugs |
| 2 | La mort est-elle effective ? | ✅ **Oui — la mort signe la FIN DU RUN**, qu'elle soit cérébrale ou physique |
| 3 | Où teste-t-on ? | ✅ **Tests isolés sur branche** (`feat/v41-ligne-flottaison`), `noyau.py` uniquement |

---

## 3. L'invariant d'échelle — ce que « diviser par 9 » veut dire

⚠️ **Piège à ne pas commettre.** Passer `ticks_par_jour` de 3600 à 400 **sans toucher aux
taux** ne divise pas le coût de calcul : ça change le métabolisme testé. Le run de réglage
ne mesurerait alors pas la mécanique cible.

**Ce qui doit rester invariant, c'est le VÉCU BIOLOGIQUE, pas le nombre de ticks :**

```
échelle_temporelle = TICKS_JOUR_REFERENCE / ticks_par_jour     # 3600/400 = 9

taux_effectif = taux_par_journee / ticks_par_jour
```

| Grandeur | Mise à l'échelle ? | Pourquoi |
|---|---|---|
| Taux de décroissance (satiété, énergie, hydratation) | ✅ **oui**, × échelle | pour que 3 repas/jour restent 3 repas/jour |
| Coûts d'action, métabolisme basal | ✅ oui | même raison |
| Jauges [0,1], bornes, dérives adaptatives | ❌ **non** | sans dimension — les mettre à l'échelle serait un bug |
| Seuils de mort | ❌ non | ce sont des états, pas des vitesses |

**Test de non-régression obligatoire** : un run à 400 ticks et un run à 3600 ticks doivent
produire le **même nombre de repas par journée** et le **même profil de jauges en % de
journée**. Si ce n'est pas le cas, l'échelle est fausse et tout le reste est ininterprétable.

---

## 4. Le principe : deux étages, pas deux jauges de plus

Formulation utilisateur : *« une jauge de satiété (qui sert pour manger), une jauge d'énergie
(lien direct entre nourriture, eau et sommeil) »*.

| Étage | Nature | Rôle |
|---|---|---|
| **Satiété** (+ hydratation) | *stock* — le réservoir | Se remplit en consommant. Ne fait **rien** directement |
| **Énergie** | *flux* — l'ATP disponible | **La seule grandeur réellement dépensée pour agir** |

```
énergie(t+1) = énergie(t)
             − dépense(basal + effort)          ← le coût d'exister et d'agir
             + conversion(satiété, hydratation)  ← digestion, débit BORNÉ
             + récupération(sommeil)             ← recharge nocturne
```

**Ce que ce découplage produit, gratuitement :** l'estomac plein mais l'énergie basse (le
coup de barre), et la faim avec de l'énergie encore disponible (le sursis). Deux états que
le modèle à une jauge ne peut pas représenter.

### La règle mortelle, sans aucun `if`

> *« Pas assez d'énergie = soit manger, soit se reposer. Mais se reposer sans manger =
> mourir. »*

C'est une **condition de solvabilité**, pas un test :

```
réserve_mobilisable = satiété × rendement_conversion
```

- **Se reposer** abaisse la dépense au minimum vital — mais **ne crée aucune matière**.
- Si `satiété ≈ 0`, alors `réserve_mobilisable ≈ 0` : le repos ne recharge rien, l'énergie
  poursuit sa descente, l'agent meurt.

**Aucune ligne ne dit « si repos et faim alors mourir ».** La mort est une conséquence
arithmétique de l'épuisement du stock. Cela satisfait la règle d'or du projet *et* l'exigence
posée en v41 : *« sa mort cognitive doit rester mathématiquement possible »*.

---

## 5. Les bornes qui ne sont pas des limites

Demande utilisateur, verbatim : *« les bornes sont la norme, cependant ce n'est pas une
limite, car certains métabolismes peuvent s'optimiser pour modifier les bornes. Mais ça aussi
a une limite de dérive exponentielle : modifier les bornes devient exponentiellement plus
complexe. »*

### La formulation retenue

```
paramètre_effectif = norme × exp(dérive)

Δdérive = pression_vécue × plasticité
        − raideur × dérive × exp(|dérive| / élasticité)
```

| Régime | Comportement |
|---|---|
| Dérive faible | rappel négligeable → adaptation **facile** |
| Dérive moyenne | rappel croissant → adaptation **coûteuse** |
| Dérive forte | rappel en `exp` → **mur asymptotique** |

Un agent vivant durablement en disette **peut** réellement abaisser son métabolisme de base —
comme un organisme en restriction calorique. Diviser ce métabolisme par 10 se heurte à un
rappel exponentiel. **La borne n'est pas une barrière : c'est une pente qui devient
verticale.**

### Ce qui dérive / ce qui ne dérive jamais

| Dérive (adaptation individuelle) | Ne dérive jamais (structure) |
|---|---|
| métabolisme de base | une jauge vide reste vide |
| rendement de conversion | la mort par épuisement |
| débit digestif | les bornes [0,1] des jauges |
| coût du sommeil | l'invariant d'échelle temporelle |

⚠️ **La dérive doit être sérialisée dans le `.brain`** (elle fait partie de l'individu) et
rechargée par `.get(..., défaut_neutre)` — un `.brain` antérieur repart avec une dérive nulle,
donc au métabolisme d'espèce, sans greffe ni erreur. Même discipline que `empreinte_types`
(v39.0) et `flottaison_metabolique` (v41.0).

---

## 6. Les proportions biologiques de référence

Ancrées sur le réel, pas choisies :

| Grandeur | Réalité | Traduction sur 3600 ticks |
|---|---|---|
| Repas / jour | 3 | un repas doit couvrir **~1200 ticks** |
| Survie sans nourriture | ~30 jours | mort par faim **très lente** |
| Survie sans eau | ~3 jours | l'eau tue **~10× plus vite** que la faim |
| Sommeil / jour | ~1/3 | le cycle nocturne existe déjà (`rever`) |
| **Métabolisme basal / dépense totale** | **~60–70 %** | **le repos coûte déjà la majorité** |

### Le défaut que cette dernière ligne corrige

Aujourd'hui : `done` (ne rien faire) = 0,1 · `pickup` = 0,8. Le basal représente donc **12 %**
de la dépense, contre ~65 % dans le vivant.

**Conséquence** : bouger est massivement puni par rapport à l'immobilité. C'est cohérent avec
le biais anti-mouvement déjà mesuré (**5,5 % de `forward`**, cf. CONCEPTION_v34 §4) et avec
`toucher_coupe` / `bio_coupe` qui sont les deux seules lésions coûteuses de l'ablation.

Après : **une dépense de fond incompressible, et l'action comme surcoût modeste.** C'est la
ligne de flottaison v41 posée *dans le corps* plutôt que dérivée après coup.

⚠️ **Piège hérité de CONCEPTION_v34 §4, à traiter explicitement** : le coût doit pénaliser
l'**effort inutile**, pas le déplacement. Rebrancher naïvement la dépense sur
`COUT_CORPOREL_PAR_ACTION` renforcerait le biais anti-mouvement au lieu de le corriger.

---

## 7. La mort — décision 2, et ses conséquences

**La mort signe la fin du run** (cérébrale ou physique).

C'est plus fort que les deux options envisagées en CONCEPTION_v34 §7.1 (reset propre / coût
persistant) : ici, **le `.brain` s'arrête**. Conséquences à assumer :

| Point | Traitement |
|---|---|
| **Le `.brain` est-il sauvegardé à la mort ?** | ✅ oui — un cerveau mort reste une donnée de recherche. Archivé, **jamais supprimé** |
| **Cause de mort tracée** | ✅ dans le `.brain` et le log : famine, déshydratation, épuisement |
| **Niveaux sans ressources** | ⚠️ **bloquant** — cf. CONCEPTION_v34 §7.4 : un agent mortel sur une carte sans nourriture meurt quoi qu'il fasse. Peupler via `DetecteurRessourcesBiologiques`, jamais une exception codée en dur |
| **Campagne multi-graines** | une graine morte au jour 300 n'est pas comparable à une graine vivante à 2000 — **la durée de vie devient une métrique**, pas un échec de run |

> **Ce point change la nature des campagnes.** Jusqu'ici toutes les graines allaient au bout.
> Désormais « combien de jours a-t-il vécu » est un résultat en soi.

---

## 8. Ce qu'on attend, et comment on saura que c'est faux

**Instrumenter d'abord** (doctrine v30.1). Métriques nécessaires **avant** toute conclusion :
`Meta_Energie_Moy/Min`, `Meta_Satiete_Moy`, `Meta_Repas_Jour`, `Meta_Ticks_Critique_Pct`,
`Meta_Derive_*`, `Meta_Cause_Mort`, `Meta_Jours_Vecus`.

| Attendu | Falsifié si… |
|---|---|
| La zone critique redevient un **événement** (< 20 % des ticks) | reste > 80 % → l'échelle est encore fausse |
| `r_bio` retrouve de la **variance** | écart-type toujours ≈ 0 → le défaut n'était pas là |
| `danger` **diverge** entre graines | reste à ±1 unité sur 9/10 → la saturation a une autre cause |
| ~3 repas/jour | 0 ou > 20 → conversion mal calibrée |
| Le sommeil devient une **décision** | jamais choisi, ou choisi en permanence |

⚠️ **Ce qui ne serait PAS une preuve.** Si le cursus se débloque, ce ne sera **pas** une
démonstration que la mécanique est bonne : la campagne v41 a montré qu'une seule graine peut
débloquer par **loterie natale** (§10.3 du chantier v41). Il faudra ≥ 10 graines, comme cette
fois-ci. Une amélioration sur 1 à 3 graines ne vaudra rien.

---

## 9. Le plan par étapes

| Étape | Contenu | Validation |
|---|---|---|
| **0** | Instrumenter le métabolisme actuel (les 7 métriques ci-dessus), **sans rien changer** | run 300 j, on connaît la ligne de base |
| **1** | Échelle temporelle : `ticks_par_jour` paramétrable + taux dérivés par journée | run 400 vs 3600 → **même nb de repas/jour** |
| **2** | Deux étages (satiété/énergie), conversion bornée. **Mort désactivée** | l'énergie oscille, la zone critique redescend |
| **3** | Dérive adaptative des bornes (`exp`) | la dérive bouge, sature, et est sérialisée |
| **4** | Activer la mort + peupler les niveaux en ressources | durée de vie mesurée, causes tracées |
| **5** | Campagne ≥ 10 graines | seule étape qui autorise une conclusion |

Chaque étape : **run 300 jours à graine fixée**, comparaison à la ligne de base, aucune étape
suivante tant que la précédente n'est pas lisible.

---

## 10. Risques identifiés

1. **La mort masque tout.** Si les agents meurent au jour 50, aucune autre métrique n'est
   interprétable. D'où l'étape 4 en avant-dernier, mort désactivée jusque-là.
2. **Le coût de calcul.** 3600 ticks = **×9**. Un run de 2000 jours passerait de ~4 h à ~36 h.
   Les réglages se font à 400 ticks ; seule la campagne finale tourne à 3600 — et il faudra
   peut-être accepter 1000 jours plutôt que 2000.
3. **Double comptage** (CONCEPTION_v34 §7.2) : si l'énergie entre dans `calculer_deficit()`,
   elle compte dans `r_bio` **alors que l'effort y est déjà facturé**. À trancher **avant**
   d'écrire, pas après.
4. **Interaction avec la flottaison v41.** `flottaison_metabolique` est dérivée de la médiane
   des `|r|`. Si `r_bio` change d'échelle, la flottaison suit — c'est voulu (cliquet), mais un
   `.brain` v41 rechargé arrivera avec une flottaison calibrée sur l'**ancien** métabolisme.
   Vérifier que le cliquet la ramène, ou repartir de cerveaux neufs.
5. **Le biais anti-mouvement** (§6) : la refonte doit le corriger, pas l'aggraver.

---

## 11. Ce que ce document ne prétend pas

- Il **ne prétend pas** que ceci débloquera le cursus. 9 mécaniques cognitives ont été
  testées, 9 sans apport démontré ; les deux seuls leviers ayant marché sont des propriétés
  du **monde**. Celui-ci en est un — c'est son seul argument a priori, et il ne suffit pas.
- Il **ne prétend pas** que C2 se reconnectera. L'hypothèse « un agent qui n'est plus en
  famine a enfin quelque chose à planifier » est **plausible et non testée**.
- Il ne remplace pas [CONCEPTION_v34](CONCEPTION_v34_fatigue_mortalite.md), dont le cadrage
  de la mortalité et les options écartées restent valides.

---

*Document créé le 15 août 2026, avant toute ligne de code, conformément à la méthode du
chantier v41. Mesures §1 : logs de la campagne 10 graines (`/private/tmp/v41_pop_g*.log`) et
lecture de `noyau.py` (`BiologicalHomeostasisEngine`, `COUT_CORPOREL_PAR_ACTION`,
`TICKS_PAR_JOUR_BEBE`).*
