# Index de la documentation — Naulthène

> **Point d'entrée unique.** Ce fichier dit *où* chercher et *dans quel ordre* lire.
> Il ne contient aucune connaissance propre : uniquement des pointeurs.
>
> Dernière mise à jour : **15 août 2026**

---

## 🚦 Par où commencer selon ce que tu cherches

| Ta question | Le document | Temps |
|---|---|---|
| **« Objectifs, cerveau, parcours — tout en un »** | **[etat_des_lieux/15082026_v41.2.md](etat_des_lieux/15082026_v41.2.md)** | 20 min |
| **« Où en est le projet ? »** | [ETAT_DU_PROJET_aout_2026.md](recherche/ETAT_DU_PROJET_aout_2026.md) | 15 min |
| « Qu'est-ce qui a changé et quand ? » | [CHANGELOG.md](fonctionnement/CHANGELOG.md) | consultation |
| « Comment je lance un run ? » | [LANCEMENT.md](fonctionnement/LANCEMENT.md) | 5 min |
| « Comment ça marche, en détail ? » | [explications_readme.md](fonctionnement/explications_readme.md) | long |
| « Qu'est-ce qu'on a déjà essayé ? » | [recherche_bug_or_not_bug.md](recherche/recherche_bug_or_not_bug.md) | ⚠️ **à lire avant toute idée neuve** |
| « Qu'est-ce qu'on fait ensuite ? » | [AVIS_ET_PROPOSITIONS_aout_2026.md](ameliorations/AVIS_ET_PROPOSITIONS_aout_2026.md) | 20 min |

---

## 📚 Les trois familles de documents

Le piège classique du projet est de confondre ces trois natures. **Un seul dossier fait
autorité sur l'état courant.**

| Dossier | Nature | Fait autorité ? |
|---|---|---|
| `docs/fonctionnement/` | **normatif** — comment ça marche, comment on lance | ✅ **oui** |
| `docs/recherche/` | **enquêtes** — ce qui bloque, ce qui a été réfuté | ❌ non |
| `docs/ameliorations/` | **idées** — pistes proposées, pas encore validées | ❌ non |
| `docs/ameliorations_appliquees/` | **livré** — mécaniques posées dans le code | 🟡 partiellement |
| `docs/etat_des_lieux/` | **synthèses datées** — une photo à un instant donné | ❌ non (**périmable**) |

> ⚠️ Un document d'`etat_des_lieux/` est une **photo horodatée**, jamais une référence
> vivante : il n'est pas mis à jour après sa date. Un fichier par point d'étape
> (`DDMMYYYY_Version.md`), les anciens sont **conservés**, jamais écrasés — c'est ce qui
> permet de comparer deux dates. Pour l'état courant, aller au CHANGELOG.

> Un carnet est *vivant mais non normatif* : il raconte une enquête, avec ses erreurs.
> **Ne jamais y chercher l'état courant** (c'est le rôle du CHANGELOG) — mais **toujours
> le consulter avant de relancer une piste**, pour ne pas retester une idée déjà écartée.

---

## 🗺️ La carte complète, par thème

### A. Comprendre le projet

| Document | Ce qu'il contient |
|---|---|
| [readme.md](../readme.md) | Vitrine GitHub (anglais) — la thèse, les chiffres, l'état du blocage |
| [readme_fr.md](../readme_fr.md) | Miroir français + documentation narrative longue (v7 → v39) |
| [explications_readme.md](fonctionnement/explications_readme.md) | Détail algorithmique et mathématique complet |
| [Parcourt_readme.md](fonctionnement/Parcourt_readme.md) | Guide vulgarisé des 4 parcours d'entraînement |
| [CLAUDE.md](../CLAUDE.md) | Règles de maintenance + **tous les invariants à ne pas casser** |

### B. L'état des lieux *(à jour)*

| Document | Ce qu'il contient | Lié à |
|---|---|---|
| **[etat_des_lieux/15082026_v41.2.md](etat_des_lieux/15082026_v41.2.md)** | **Synthèse en 3 volets : les objectifs · l'état du cerveau (fonctionnement, contraintes, blocages) · le parcours (grilles, nourriture, jours, ticks).** Inclut le chantier v41.2 en cours, non encore au CHANGELOG | tout |
| **[ETAT_DU_PROJET_aout_2026.md](recherche/ETAT_DU_PROJET_aout_2026.md)** | **Forces, faiblesses, ce qui reste à faire.** Le point d'entrée | tout |
| [CHANGELOG.md](fonctionnement/CHANGELOG.md) | Historique version par version — **la référence factuelle** | tout |
| [REVUE_CODE_v39_aout_2026.md](recherche/REVUE_CODE_v39_aout_2026.md) | **6 défauts trouvés le 13-14/08**, dont le biais qui faussait 2a/2b | §B, §D |

### C. Les enquêtes *(pourquoi ça ne marche pas)*

| Document | La question posée | Verdict |
|---|---|---|
| [recherche_bug_or_not_bug.md](recherche/recherche_bug_or_not_bug.md) | **H1 → H18** : bug ou erreur de conception ? | 15 erreurs de diagnostic consignées · **H15 tranchée** : 4 sens sur 6 sont inertes |
| [dia_Aout_2026.md](recherche/dia_Aout_2026.md) | Pourquoi bloqué au niveau 2/15 ? | 3 causes, **aucune cognitive** |
| **[DISSECTION_g22_aout_2026.md](recherche/DISSECTION_g22_aout_2026.md)** | Que contient le cerveau le plus avancé (248 victoires) ? | **Le but vaut 16× le reste — appris, jamais déclaré** |
| [CAMPAGNE_P17_ABLATION_aout_2026.md](recherche/CAMPAGNE_P17_ABLATION_aout_2026.md) | Le cursus gaussien aide-t-il ? À quoi servent les organes ? | ⚠️ **verdict C2 contredit** par la campagne v41 (témoin au plancher) |
| **[CAMPAGNE_v41_population_et_ablation_aout_2026.md](recherche/CAMPAGNE_v41_population_et_ablation_aout_2026.md)** | Le déblocage v41 est-il reproductible ? À quoi servent les organes, témoin non nul ? | **0 promotion sur 10 graines** · **C2 débranchable à +0,0 sur 6 niveaux** · 6 lésions sur 13 sans effet |
| **[CHANTIER_v40_planification_emergente.md](ameliorations_appliquees/CHANTIER_v40_planification_emergente.md)** | Peut-on supprimer les constantes de l'arbitrage ? | **3 supprimées** · l'envie de vivre peut tuer l'agent |
| [CHANTIER_v37_equilibre_c1_c2.md](ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md) | C2 écrase-t-il C1 ? | Équilibre atteint, blocage persiste |
| [CHANTIER_v38_monde_continu.md](ameliorations_appliquees/CHANTIER_v38_monde_continu.md) | Un monde continu débloque-t-il ? | **1 brique validée sur 6** |
| [les_sens_combinatoire.md](ameliorations/les_sens_combinatoire.md) | Les sens se lient-ils entre eux ? | Cadrage du liage multimodal |

### D. Les projets *(ce qu'on veut faire)*

| Document | Ce qu'il contient |
|---|---|
| **[AVIS_ET_PROPOSITIONS_aout_2026.md](ameliorations/AVIS_ET_PROPOSITIONS_aout_2026.md)** | **P1 → P17** : les pistes, sous la règle « rien en dur si ça peut émerger » + la grille développementale + **la gaussienne d'apprentissage (P17)** |
| **[CORRECTIFS_v41_ligne_de_flottaison.md](ameliorations/CORRECTIFS_v41_ligne_de_flottaison.md)** | **LIVRÉ (C1+C2)** — la moyenne sur 400 ticks noyait la victoire sous le coût métabolique. Le vécu se compte désormais en saillances au-dessus du coût d'exister : **C2 passe de mort (2000 nuits/2000) à dominant**. Contient aussi le benchmark « C1 pur » (§8) |
| **[CHANTIER_v41.2_metabolisme_deux_etages.md](ameliorations/CHANTIER_v41.2_metabolisme_deux_etages.md)** | **PROPOSÉ** — l'agent vit **400 ticks sur 400 en zone critique** : l'échelle temporelle est fausse d'un facteur ~35. Deux étages (satiété *stock* / énergie *flux*), mort par insolvabilité **sans aucun `if`**, et des bornes qu'un métabolisme peut déplacer à coût **exponentiel** |
| **[CHANTIER_v41.2_energie_modulatrice.md](ameliorations/CHANTIER_v41.2_energie_modulatrice.md)** | **EN COURS** — l'énergie module C1, C2, le déficit et la plasticité via `vigueur = énergie ** κ`. Contient les **4 erreurs de diagnostic** du chantier (dont « la carte était saturée : 13 ressources demandées sur 8 cases libres ») |
| **[CHANTIER_v41.4_maitrise_generale_et_heritage.md](ameliorations/CHANTIER_v41.4_maitrise_generale_et_heritage.md)** | **EN COURS** — deux maîtrises (générale / par carte). À chaque promotion l'agent redevenait un nouveau-né : aide à **100 %**, maturité **0,000**. Le sevrage hérite désormais **à proportion de la parenté mesurée** entre les deux cartes — mesurée sur les 15 niveaux : de **0,85** à **0,00**, **6 ruptures sur 14** |
| [CONCEPTION_v34_fatigue_mortalite.md](ameliorations/CONCEPTION_v34_fatigue_mortalite.md) | Fatigue, mortalité, les 4 gestes du parent — **prérequis de lecture du v41.2** |

### E. Opérationnel

| Document | Ce qu'il contient |
|---|---|
| [LANCEMENT.md](fonctionnement/LANCEMENT.md) | Toutes les commandes, options, dépannage |

---

## 🔗 Les fils qui traversent plusieurs documents

Trois idées reviennent partout. Voici où les suivre :

### Fil 1 — « Le monde, pas le cerveau »

> Ce qui **rend possible** fait progresser · ce qui **facilite** ne change rien · ce qui
> **fait à la place** fait régresser.

Parcours : [CHANTIER_v38 §10](ameliorations_appliquees/CHANTIER_v38_monde_continu.md) *(l'origine)* →
[ETAT_DU_PROJET §4](recherche/ETAT_DU_PROJET_aout_2026.md) *(la synthèse)* →
[AVIS §P0](ameliorations/AVIS_ET_PROPOSITIONS_aout_2026.md) *(la règle de conception)*

### Fil 2 — La saturation

> Une variable saturée — dans un sens **comme dans l'autre** — cesse de porter de
> l'information.

Rencontrée 6 fois : états absorbants, parole permanente, portée sonore ×2, **et
maintenant la difficulté** (test trop facile → puis trop dur, [REVUE §R6](recherche/REVUE_CODE_v39_aout_2026.md)).

### Fil 3 — « Un invariant en commentaire finit par être violé »

Trois des six défauts de la revue étaient des règles **écrites en toutes lettres** dans
une docstring, jamais transformées en test.
→ [REVUE_CODE_v39](recherche/REVUE_CODE_v39_aout_2026.md) · proposition **P9**

---

## 📌 État au 15 août 2026 — l'essentiel en 9 lignes

1. **La v41 ne débloque pas le cursus** — 0 promotion sur 10 graines × 2000 jours. Le
   niveau 4 atteint par g22 était une **loterie natale**, pas un effet du correctif
   ([campagne v41](recherche/CAMPAGNE_v41_population_et_ablation_aout_2026.md)).
2. **C2 est débranchable sans effet** : `c2_coupe` = **+0,0 sur les 6 niveaux**. Quatre
   sens sur six sont inertes ; les trois mémoires sont plutôt **nuisibles**.
3. **Le cerveau est sain** : 0 synapse morte (contre 13 769 avant les correctifs v37).
4. **Aucune mécanique cognitive n'a démontré son apport** — **9 testées, 9 échecs**.
5. **Les deux seuls leviers qui marchent sont des propriétés du MONDE.**
6. **Le banc d'essai était biaisé** : jusqu'à 1 carte sur 2 gagnable sans clé ([R5](recherche/REVUE_CODE_v39_aout_2026.md)).
7. **Corrigé — mais le test est devenu 50× trop dur** ([R6](recherche/REVUE_CODE_v39_aout_2026.md)). À recalibrer.
8. **Le prior d'empreinte (P12) a échoué** — 2/5 graines positives, p = 1,000. 8ᵉ mécanique, 8ᵉ échec.
9. **Priorité : la gaussienne d'apprentissage** ([P17](ameliorations/AVIS_ET_PROPOSITIONS_aout_2026.md)) —
   le palier joué est *tiré au sort* autour du niveau courant, au lieu d'être un pointeur qui
   ne recule jamais. Retours en arrière et « pas au-delà tant que ce n'est pas acquis »
   **émergent** de la distribution, sans un seul seuil.
10. **En cours — v41.2, le métabolisme à deux étages** ([chantier](ameliorations/CHANTIER_v41.2_metabolisme_deux_etages.md) ·
    [énergie modulatrice](ameliorations/CHANTIER_v41.2_energie_modulatrice.md)) : l'agent vivait
    **400 ticks sur 400 en zone critique**, un vécu sans variance — cause amont plausible du
    C2 déconnecté. L'agent **ne meurt plus et regagne** (26 victoires/65 j), mais le déficit
    de **trouvabilité** est structurel (1,92 trouvée/jour pour 2,5 demandées).
    ⏳ **Arbitrage ouvert** : caler le barème sur ce que l'agent trouve déjà ne démontrerait
    rien — agir sur le **monde** est le seul levier qui ait jamais marché.

---

*Index créé le 14 août 2026. Si un document est ajouté, il doit apparaître ici — sinon il
sera oublié. Dernier ajout : `etat_des_lieux/` (15/08/2026).*
