# Index de la documentation — Naulthène

> **Point d'entrée unique.** Ce fichier dit *où* chercher et *dans quel ordre* lire.
> Il ne contient aucune connaissance propre : uniquement des pointeurs.
>
> Dernière mise à jour : **14 août 2026**

---

## 🚦 Par où commencer selon ce que tu cherches

| Ta question | Le document | Temps |
|---|---|---|
| **« Où en est le projet ? »** | [ETAT_DU_PROJET_aout_2026.md](notes/ETAT_DU_PROJET_aout_2026.md) | 15 min |
| « Qu'est-ce qui a changé et quand ? » | [CHANGELOG.md](CHANGELOG.md) | consultation |
| « Comment je lance un run ? » | [LANCEMENT.md](LANCEMENT.md) | 5 min |
| « Comment ça marche, en détail ? » | [explications_readme.md](explications_readme.md) | long |
| « Qu'est-ce qu'on a déjà essayé ? » | [recherche_bug_or_not_bug.md](notes/recherche_bug_or_not_bug.md) | ⚠️ **à lire avant toute idée neuve** |
| « Qu'est-ce qu'on fait ensuite ? » | [AVIS_ET_PROPOSITIONS_aout_2026.md](notes/AVIS_ET_PROPOSITIONS_aout_2026.md) | 20 min |

---

## 📚 Les trois familles de documents

Le piège classique du projet est de confondre ces trois natures. **Un seul dossier fait
autorité sur l'état courant.**

| Dossier | Nature | Fait autorité ? |
|---|---|---|
| `docs/` | **normatif** — la référence factuelle | ✅ **oui** |
| `docs/notes/` | **carnets de recherche** — investigations, hypothèses réfutées | ❌ non |
| `docs/Old_Archive_rmd/` | **historique** — mécanique livrée ailleurs | ❌ non |

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
| [explications_readme.md](explications_readme.md) | Détail algorithmique et mathématique complet |
| [Parcourt_readme.md](Parcourt_readme.md) | Guide vulgarisé des 4 parcours d'entraînement |
| [CLAUDE.md](../CLAUDE.md) | Règles de maintenance + **tous les invariants à ne pas casser** |

### B. L'état des lieux *(à jour)*

| Document | Ce qu'il contient | Lié à |
|---|---|---|
| **[ETAT_DU_PROJET_aout_2026.md](notes/ETAT_DU_PROJET_aout_2026.md)** | **Forces, faiblesses, ce qui reste à faire.** Le point d'entrée | tout |
| [CHANGELOG.md](CHANGELOG.md) | Historique version par version — **la référence factuelle** | tout |
| [REVUE_CODE_v39_aout_2026.md](notes/REVUE_CODE_v39_aout_2026.md) | **6 défauts trouvés le 13-14/08**, dont le biais qui faussait 2a/2b | §B, §D |

### C. Les enquêtes *(pourquoi ça ne marche pas)*

| Document | La question posée | Verdict |
|---|---|---|
| [recherche_bug_or_not_bug.md](notes/recherche_bug_or_not_bug.md) | **H1 → H18** : bug ou erreur de conception ? | 15 erreurs de diagnostic consignées |
| [dia_Aout_2026.md](notes/dia_Aout_2026.md) | Pourquoi bloqué au niveau 2/15 ? | 3 causes, **aucune cognitive** |
| [CHANTIER_v37_equilibre_c1_c2.md](notes/CHANTIER_v37_equilibre_c1_c2.md) | C2 écrase-t-il C1 ? | Équilibre atteint, blocage persiste |
| [CHANTIER_v38_monde_continu.md](notes/CHANTIER_v38_monde_continu.md) | Un monde continu débloque-t-il ? | **1 brique validée sur 6** |
| [les_sens_combinatoire.md](notes/les_sens_combinatoire.md) | Les sens se lient-ils entre eux ? | Cadrage du liage multimodal |

### D. Les projets *(ce qu'on veut faire)*

| Document | Ce qu'il contient |
|---|---|
| **[AVIS_ET_PROPOSITIONS_aout_2026.md](notes/AVIS_ET_PROPOSITIONS_aout_2026.md)** | **P1 → P14** : les pistes, sous la règle « rien en dur si ça peut émerger » + la grille développementale |
| [CONCEPTION_v34_fatigue_mortalite.md](notes/CONCEPTION_v34_fatigue_mortalite.md) | Fatigue, mortalité, les 4 gestes du parent |

### E. Opérationnel

| Document | Ce qu'il contient |
|---|---|
| [LANCEMENT.md](LANCEMENT.md) | Toutes les commandes, options, dépannage |
| [Old_Archive_rmd/README.md](Old_Archive_rmd/README.md) | Ce que contient l'archive et pourquoi |

---

## 🔗 Les fils qui traversent plusieurs documents

Trois idées reviennent partout. Voici où les suivre :

### Fil 1 — « Le monde, pas le cerveau »

> Ce qui **rend possible** fait progresser · ce qui **facilite** ne change rien · ce qui
> **fait à la place** fait régresser.

Parcours : [CHANTIER_v38 §10](notes/CHANTIER_v38_monde_continu.md) *(l'origine)* →
[ETAT_DU_PROJET §4](notes/ETAT_DU_PROJET_aout_2026.md) *(la synthèse)* →
[AVIS §P0](notes/AVIS_ET_PROPOSITIONS_aout_2026.md) *(la règle de conception)*

### Fil 2 — La saturation

> Une variable saturée — dans un sens **comme dans l'autre** — cesse de porter de
> l'information.

Rencontrée 6 fois : états absorbants, parole permanente, portée sonore ×2, **et
maintenant la difficulté** (test trop facile → puis trop dur, [REVUE §R6](notes/REVUE_CODE_v39_aout_2026.md)).

### Fil 3 — « Un invariant en commentaire finit par être violé »

Trois des six défauts de la revue étaient des règles **écrites en toutes lettres** dans
une docstring, jamais transformées en test.
→ [REVUE_CODE_v39](notes/REVUE_CODE_v39_aout_2026.md) · proposition **P9**

---

## 📌 État au 14 août 2026 — l'essentiel en 6 lignes

1. **Le cerveau est sain** : 0 synapse morte (contre 13 769 avant les correctifs v37).
2. **Aucune mécanique cognitive n'a démontré son apport** — 8 testées, 8 échecs.
3. **Les deux seuls leviers qui marchent sont des propriétés du MONDE.**
4. **Le banc d'essai était biaisé** : jusqu'à 1 carte sur 2 gagnable sans clé ([R5](notes/REVUE_CODE_v39_aout_2026.md)).
5. **Corrigé — mais le test est devenu 50× trop dur** ([R6](notes/REVUE_CODE_v39_aout_2026.md)). À recalibrer.
6. **Priorité : un cursus ultra-progressif** avec retours en arrière (voir ci-dessous).

---

*Index créé le 14 août 2026. Si un document est ajouté, il doit apparaître ici — sinon il
sera oublié.*
