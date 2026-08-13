# État du projet Naulthène — 13 août 2026

> **Nature du document** : état des lieux complet, arrêté au 13 août 2026 au soir. Chaque
> affirmation est adossée à une mesure, avec son degré de confiance. Il fait suite au
> [diagnostic d'août](dia_Aout_2026.md) (run de 1300 jours) et intègre les quatre jours de
> campagne expérimentale des 11-13 août.
>
> **Ce document ne remplace pas** : [CHANGELOG.md](../CHANGELOG.md) reste la référence
> factuelle version par version, [recherche_bug_or_not_bug.md](recherche_bug_or_not_bug.md)
> le carnet d'investigation, [CHANTIER_v38_monde_continu.md](CHANTIER_v38_monde_continu.md)
> le détail du chantier en cours.

---

## Sommaire

1. [Le projet en une page](#1-le-projet-en-une-page)
2. [Ce qui fonctionne — les forces](#2-ce-qui-fonctionne--les-forces)
3. [Ce qui ne fonctionne pas — les faiblesses](#3-ce-qui-ne-fonctionne-pas--les-faiblesses)
4. [Le résultat central de la campagne](#4-le-résultat-central-de-la-campagne)
5. [Ce qui reste à faire](#5-ce-qui-reste-à-faire)
6. [Ce que ce document ne prétend pas](#6-ce-que-ce-document-ne-prétend-pas)

---

## 1. Le projet en une page

Naulthène est un **cerveau complet en attente d'un corps**, et il est **toujours en cours de
développement**. MiniGrid n'est pas la finalité : c'est un berceau — un monde peu coûteux où
élever, casser et mesurer un organe cognitif.

### 1.1 L'état en trois chiffres

| | Valeur | Sens |
|---|---|---|
| **Paramètres** | **644 632** (bus 96) | recomptés, pas estimés |
| **Synapses mortes** | **0** sur 47 runs post-v37 | contre 13 769 en médiane avant |
| **Paliers franchis** | **1 à 5 sur 6** selon les conditions | contre « bloqué à 2/15 » en juillet |

### 1.2 Ce qui a changé depuis le diagnostic d'août

Le blocage historique — *« niveau 2 sur 15, plus aucune victoire depuis 678 jours »* —
**n'apparaît dans aucun run récent**. Ce n'est pas une amélioration marginale : c'est la
disparition du symptôme qui définissait le projet depuis des mois.

Deux causes, aucune n'étant une nouvelle mécanique cognitive :

1. **Les correctifs v37** (érosion géométrique, myéline rafraîchie au bon moment, échelle de
   myéline relative, plancher vital qui n'est plus un plafond) — trois bugs qui rendaient
   l'apprentissage des têtes de décision *mathématiquement impossible*.
2. **Un cursus cohérent** : `DoorKey` à 6 paliers (une seule compétence change entre deux
   paliers voisins) au lieu de 15 niveaux hétérogènes.

---

## 2. Ce qui fonctionne — les forces

### 2.1 🟢 L'architecture est saine *(preuve forte)*

C'est le seul effet massif de toute l'histoire du projet.

| Synapses mortes (max/run) | Médiane | Max |
|---|---|---|
| Avant les correctifs v37 (30 runs) | **13 769** | 77 169 |
| Après (47 runs) | **0** | 77 729 |

Santé synaptique sur le run de référence à 1300 jours : **1 couche sur 12** au plancher
vital, contre 5 avant. `integrateur_bio` et `porte_auditive` dépassent leur norme de
naissance — le cerveau ne survit pas, il **grossit**.

### 2.2 🟢 Les mécaniques cognitives tournent *(preuve forte)*

| Mécanique | Version | Preuve mesurée |
|---|---|---|
| Plasticité structurelle | v37.0 | 0 synapse morte sur 1300 j |
| Rêve adaptatif | v13+ | 15-18 % de la journée rejouée, 70 rêves/nuit |
| Équilibre C1/C2 | v37.0 | ratio **0,58-1,12** contre 9,9-22,1× avant |
| Cliquet de la référence | v37.1-fix1 | dérive −7,4 % sur 1300 j contre −57 % |
| Abstraction mnésique | v36.0 | **108** confirmations/repère, 73 % de rappel |
| Odorat topologique | v32.0 | BFS correct, portes qui fuient, clinotaxie |
| Neurogenèse | v13+ | bus **16 → 96** |
| Rétrocompatibilité `.brain` | v24+ | aucune fausse greffe sur 1300 nuits |

### 2.3 🟢 La méthode expérimentale s'est durcie *(acquis de la campagne)*

Passage de « un run, une conclusion » à :

> **≥ 6 graines appariées, témoins sur les mêmes graines, test des signes, et publication
> APRÈS réplication — jamais avant.**

C'est cette méthode qui a permis de **réfuter mes propres annonces** trois fois en une
journée (le « ×4,5 », le « plateau de 800 jours », la « patience confirmée »). Un protocole
qui ne peut pas invalider son auteur ne mesure rien.

### 2.4 🟢 Le seul levier statistiquement solide : la continuité + densité

| Condition | Écarts appariés (paliers) | p | Régressions |
|---|---|---|---|
| **2b — continuité + densité** | **+1, +3, 0, +1, +1, +2** | **0,062** | **aucune** |

**Aucune graine ne régresse.** C'est le signal le plus régulier de toute l'investigation :
ni 2a seul, ni aucun des cinq leviers testés le 12/08, ni aucune brique postérieure n'a
évité d'avoir au moins une graine en recul.

### 2.5 🟢 Deux défauts réels du noyau, identifiés

Indépendants des runs, et ils valent d'être portés dans `src/` :

1. **`obs_auditive=None` ne produit pas un silence** (`noyau.py:548-552`) : le terme
   **disparaît** de la somme du bus latent. La norme change, donc l'échelle d'activation de
   tout l'aval. Le cerveau ne perçoit pas le calme — **il perd le canal**, sans signal.
   Défaut annoncé dans [les_sens_combinatoire.md](les_sens_combinatoire.md) §4.3, jamais
   corrigé.
2. **`Pourcentage_Reve` est affiché avec un `%` en trop** : la valeur est une fraction. A
   causé une erreur de diagnostic propagée dans deux documents.

---

## 3. Ce qui ne fonctionne pas — les faiblesses

### 3.1 🔴 La variance écrase tout *(le problème n°1)*

Une condition **identique**, rejouée sur des graines différentes :

```
victoires : 1, 2, 3, 4, 5, 25, 69      (facteur x69 entre deux exécutions)
sigma     : 0,76 (j.50) -> 1,11 (j.400-600) -> 0,47 (j.1200)
```

Conséquences directes :

- **Un seul résultat approche la significativité** en quatre jours (2b, p = 0,062) — et
  p = 0,062 **n'est pas** p < 0,05.
- Il faudrait **15 à 20 graines** par condition pour trancher un écart d'un palier, soit
  plusieurs heures de calcul par test.
- Les trajectoires **divergent** au milieu (σ max vers j.400-600) puis **convergent** à la
  fin. Comparer des états finaux revient donc à comparer les points d'arrivée d'un processus
  qui les égalise : **il faut mesurer des vitesses, pas des totaux**.

### 3.2 🔴 Les gains ne s'additionnent jamais

| Pile | Gain vs origine |
|---|---|
| 2a | +1,5 palier |
| 2a + 2b | +1,5 *(pas +3)* |
| 2a + 2b + 2c | **−0,5** |

Trois fois le même constat sur la campagne (H11+H09, A1+A2+A3, 2a+2b+2c). Ces briques ne
sont pas des additifs indépendants : la continuité **crée une possibilité**, les briques
suivantes occupent l'espace qu'elle a ouvert — ou le remplissent d'assistance.

### 3.3 🔴 Aucune mécanique cognitive testée n'a produit d'effet

| Levier | Nature | Verdict |
|---|---|---|
| C2 profond (A1) | cognitif | ❌ aucun effet |
| Promotion hybride (A2) | cursus | ❌ bloque tout |
| Grâce mnésique (H13) | cognitif | ❌ non reproduit |
| Entrelacement (H14) | pédagogique | ❌ non reproduit |
| Parent physique (2c) | social | ❌ **0/5, régression** |
| Liage multimodal (2d) | cognitif | ❌ 1/5, la perte **monte** |

**Les deux seuls leviers qui aient jamais montré quelque chose sont des propriétés du
MONDE** (patience proportionnelle à la carte, continuité temporelle), pas du cerveau.

### 3.4 🔴 Les sens sont branchés mais peu exploités

Ablation sensorielle, 4 conditions × 3 graines :

| Sens coupé | Écarts appariés | Verdict |
|---|---|---|
| **Toucher** | **−2, −2, −2** | ✅ **le seul sens démontré nécessaire** |
| Chimie (odorat + goût) | +3, −2, −2 | ❌ aucun effet mesurable |
| Mémoire spatiale | 0, −3, +1 | ⚠️ non concluant |

Le toucher porte `objet_en_main` — sur DoorKey, *savoir qu'on tient la clé* est la seule
information décisive que la vue ne donne pas. L'odorat, lui, ne fait que redire ce que l'œil
voit déjà : il est **inutile dans ce monde**, pas cassé.

Taux d'approche olfactive sur 17 runs de 1200 jours : **+0,013** d'évolution totale
(0,50 = pile ou face). L'agent n'apprend pas à suivre les odeurs.

### 3.5 🔴 MiniGrid plafonne, structurellement

**4 types d'objets × 6 couleurs, une seule apparence par objet.** On peut valider qu'un
mécanisme *fonctionne* ; on ne peut **jamais prouver qu'il produit un concept** plutôt
qu'une table de correspondance. Aucune quantité de code ne contourne cette limite — elle
appartient à l'environnement.

### 3.6 🟠 Treize erreurs de diagnostic, une cause dominante

Cinq des treize erreurs consignées viennent toutes du même défaut : **conclure depuis un
échantillon trop petit**. Les cinq premières venaient d'une métrique mal lue ; celles-ci
d'une lecture *correcte* d'un échantillon insuffisant — plus insidieux, parce que le chiffre
était juste.

---

## 4. Le résultat central de la campagne

Quatre jours, ~60 runs de 600 à 1300 jours, et un fil conducteur qui tient sur toutes les
conditions :

> ### Ce qui **rend possible** fait progresser.
> ### Ce qui **facilite** ne change rien.
> ### Ce qui **fait à la place** fait régresser.

| Intervention | Nature | Effet |
|---|---|---|
| Continuité du monde | rend possible | **+1,5 palier** |
| Densité de ressources | facilite | 0 |
| Son parcimonieux | rend possible | +0,5 *(non significatif)* |
| Parent montreur | fait à la place | **−1,0** |
| Parent nourricier | fait à la place | **−2,0** |

La démonstration la plus nette est le **parent nourricier** : en supprimant le besoin de
chercher, il fait chuter la mémoire spatiale d'un facteur **6** (74 → 12 repères) et
l'odorat de **moitié** (0,306 → 0,128). **Les six graines se figent au même palier.**

C'est le prolongement de l'intuition fondatrice — *« un cerveau qui revoit en boucle les
mêmes choses se meurt de bêtise »* — auquel la mesure ajoute son symétrique : **un cerveau à
qui on épargne l'effort désapprend aussi**.

### 4.1 Le corollaire technique : la saturation

Rencontrée **quatre fois** en un chantier, sous quatre formes :

| Forme | Symptôme | Correctif |
|---|---|---|
| États absorbants | Portage 100 %, souvenirs figés | réarmement de tâche |
| Parole permanente | `Cooc = 1,000` | plafond de fréquence |
| Portée trop large | 0 tick silencieux | vocabulaire réduit |
| Portée trop étroite | 0 % de son sur 8×8 | portée ∝ carte |

**Une seule cause** : *une variable saturée — dans un sens comme dans l'autre — cesse de
porter de l'information.* C'est la leçon la plus réutilisable du chantier, et elle vaut
au-delà du son.

---

## 5. Ce qui reste à faire

### 5.1 Priorité 1 — Consolider le seul résultat solide

**2b sur 15-20 graines.** C'est la seule condition qui approche la significativité
(p = 0,062, aucune régression). Tant qu'elle n'est pas confirmée, tout ce qui s'empile
dessus repose sur du sable.

Coût : ~4 h de calcul. Retour : la première affirmation *démontrée* du chantier.

### 5.2 Priorité 2 — Porter les correctifs identifiés dans `src/`

| Correctif | Statut |
|---|---|
| Le silence auditif perçu (bit de présence) | identifié, **non porté** |
| L'affichage `%` de `Pourcentage_Reve` | identifié, non porté |
| Patience ∝ √surface | validé 4/4, non porté |
| Continuité (réarmement de tâche) | validé, non porté |

⚠️ **Tout le travail des v34 à v38 vit dans `noyau.py`, qui est gitignoré**, et les
expériences dans `experiences/v38/`. **Un clone du dépôt n'a rien de tout cela.** C'est le
risque structurel n°1 du projet : quatre mois de mécaniques dans un fichier non versionné.

### 5.3 Priorité 3 — Changer de méthode de mesure

- Comparer des **vitesses** (jour de première promotion, pente) et non des totaux, puisque
  les trajectoires convergent en fin de run.
- Mesurer dans la fenêtre **j.400-600**, là où σ est maximal — c'est là qu'un effet réel
  serait visible.
- **≥ 8 graines** minimum, 15 pour un écart d'un palier.

### 5.4 Priorité 4 — Le berceau, pas le cerveau

Tous les leviers cognitifs ont échoué ; les deux qui marchent sont des propriétés du monde.
La suite logique n'est pas une nouvelle mécanique mais un **monde qui exige** ce que le
cerveau sait déjà faire.

Trois propriétés absentes de MiniGrid, dans l'ordre de coût croissant :

1. **La conséquence différée** — aujourd'hui chaque tick est quasi indépendant.
2. **La variété d'apparence** — condition pour distinguer un concept d'une table (§3.5).
3. **Un corps réel** — la finalité annoncée du projet.

### 5.5 Ce qui est explicitement écarté *(et pourquoi)*

| Piste | Raison de l'écart |
|---|---|
| Nouvelle mécanique cognitive | 6 testées, 6 échecs |
| Parent / assistance | mesuré nuisible (−2 paliers) |
| Densifier davantage les sens | remplir un canal ne le rend pas utile |
| Empiler une brique de plus | les gains ne s'additionnent jamais |

---

## 6. Ce que ce document ne prétend pas

- **Un seul résultat est statistiquement solide** (2b, p = 0,062 — et ce n'est pas p < 0,05).
  Le « fil conducteur » du §4 est une **hypothèse de travail** cohérente avec les mesures,
  pas un fait démontré. C'est exactement le type de synthèse séduisante qui a produit trois
  faux positifs le 12 août.
- **Aucune de ces découvertes n'est dans `src/naulthene/`.** Le cœur de référence
  (`colab.py`) est en v17 ; tout le reste vit dans un fichier gitignoré.
- **Le cas g22** (69 victoires sur la carte la plus dure, cursus complet en 239 jours) reste
  **inexpliqué et non reproduit**.
- **L'anomalie de 2c-ter** — une graine à `cooc = 0,00` atteignant le palier 5 — affaiblit
  l'idée que le son explique la progression, et n'a pas d'explication.
- MiniGrid ne permettra **jamais** de démontrer la conceptualisation (§3.5).

---

*Document arrêté au 13 août 2026. Runs de référence : `ous47258` (1300 j, diagnostic),
campagne v38 (6 conditions × 6 graines × 600 j). 142 runs synchronisés sur
[W&B](https://wandb.ai/naultadrien123-nvnc/Naulthene-AGI).*
