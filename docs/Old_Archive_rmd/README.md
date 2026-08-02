# Old_Archive_rmd — documents historiques

Ce dossier conserve les documents dont le contenu a été **livré et absorbé ailleurs** : notes de
conception dont la mécanique est implémentée, spécifications d'origine, plans d'amélioration
partiellement réalisés.

**Ils ne sont ni obsolètes ni faux** — ce sont des archives de travail. Ils gardent la trace de
*pourquoi* les choix ont été faits, y compris des options **écartées** et de leurs raisons, ce
qu'aucun document « à jour » ne raconte. C'est précisément leur valeur : éviter qu'une idée déjà
évaluée et rejetée soit réintroduite plus tard sans connaître l'argument qui l'avait écartée.

> ⚠️ **Ne pas s'y référer pour l'état courant du projet.** Un document archivé décrit ce qui était
> vrai *au moment où il a été écrit*. Pour l'état réel, voir dans l'ordre :
> [../../readme.md](../../readme.md) (narratif), [../CHANGELOG.md](../CHANGELOG.md) (version par
> version), [../LANCEMENT.md](../LANCEMENT.md) (commandes) et
> [../../CLAUDE.md](../../CLAUDE.md) (règles de maintenance).

## Contenu

| Document | Ce qu'il contient | Statut de la mécanique |
|---|---|---|
| `CONCEPTION_v22_audio.md` | Conception de l'Hémisphère Auditif & Vocal (oreille, bouche, synthèse par formants, professeur Gemma) + les 3 défauts détectés à la revue v22.1 | ✅ Livrée (v22.0/v22.1), étendue jusqu'en v27.6 |
| `CONCEPTION_v30_exo_sens.md` | Cadrage de la v30 : pivot de C3 en 6ᵉ sens, odorat dynamique, arbitrages et **options écartées** | ✅ Livrée (v30.0) |
| `Maj_V29_readme.md` | Note de conception d'origine de la v29 : hiérarchie des 5 sens, dynamique C1/C2, distillation | ✅ Livrée (v29.0/v29.1) |
| `EXPLICATIONS_v29_sens.md` | Doc explicative détaillée de la v29 (formules du toucher/odorat/goût, pourquoi les sens faibles restent hors JEPA, identité C1/C2, distillation, options écartées) | ✅ Livrée — ⚠️ **chiffres dépassés** (24 dims, odorat linéaire) : voir `explications_readme.md` §15 |
| `AMELIORATION_V1.md` 🔒 | Plan d'amélioration « Le Parent remplace le Programme » — §A.5 (Cristallisation Souple) réalisé, les autres chantiers restent des propositions | 🟡 Partiellement réalisée |
| `1440_JOURS_NAULTHENE_V1.md` 🔒 | Analyse d'un run réel de 1440 jours (Cerveau Bébé) | 📊 Analyse de run |

> 🔒 **Locaux, jamais poussés sur GitHub.** Ces deux fichiers sont gitignorés depuis le commit
> `e6d1687` (« analyses de run personnelles ») : ce sont des diagnostics chiffrés d'un run local
> précis et des notes de travail, pas des documents de référence du projet. Leur archivage ici ne
> change pas leur nature — l'exclusion a été étendue au nouveau chemin. Si tu clones ce dépôt,
> tu ne les verras pas : c'est voulu.

## Ce qui reste dans `docs/` (documents vivants)

| Document | Rôle |
|---|---|
| `CHANGELOG.md` | Historique version par version — **la référence factuelle** |
| `LANCEMENT.md` | Guide opérationnel : toutes les commandes, options, dépannage |
| `Parcourt_readme.md` | Guide vulgarisé des 4 parcours d'entraînement |
| `explications_readme.md` | Détail algorithmique et mathématique complet — **§15 est désormais la référence à jour** des sens, de l'identité C1/C2 et de l'Exo-Sens |

## Convention

Un document rejoint cette archive quand sa mécanique est **livrée et documentée ailleurs** —
jamais parce qu'il est « vieux ». Déplacer avec `git mv` (l'historique est précieux) et corriger
les liens entrants : ces documents sont référencés depuis `readme.md`, `CLAUDE.md`, les autres
docs **et le code source** (docstrings de `bus_sensoriel.py`, `hemisphere_audio.py`,
`professeur_gemma.py`…). Vérifier après déplacement qu'aucun lien ne pointe dans le vide.
