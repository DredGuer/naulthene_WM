# Branches archivées le 2026-09-02 — toutes contenues dans `master`

> **Photo horodatée.** Les 21 branches de travail du cycle v28 → v41.32 ont été supprimées
> **localement et sur `origin`**, après vérification que **chaque tip est un ancêtre de
> `master`** (`git merge-base --is-ancestor` : 21 OK, **0 commit orphelin**).
>
> **Rien n'est perdu.** Le contenu vit dans `master` ; le SHA ci-dessous suffit à ressusciter
> une branche à l'identique :
>
> ```bash
> git branch <nom> <sha>          # recrée la branche locale sur son tip d'origine
> ```
>
> ⚠️ Ces SHA restent valides tant que `master` les contient — ce qui est le cas par
> construction, puisqu'ils en sont des ancêtres.

## Pourquoi les supprimer

Le dépôt portait **22 branches locales et 22 distantes** pour **une seule ligne de travail
réelle**. Depuis fin août le travail se fait directement sur `master` (voir `CLAUDE.md`
§Git Workflow) : ces branches ne servaient plus qu'à faire du bruit dans `git branch` et à
laisser croire à des chantiers ouverts. Aucune ne portait un commit absent de `master`.

## Les 21 branches

| Branche | Tip (SHA) | Dernier commit |
|---|---|---|
| `docs/campagne-nociception-n20` | `6ab5c90` | docs(changelog): hash reel de l'entree v41.25-mesure |
| `docs/diagnostic-cout-douleur` | `28fb517` | docs(diagnostic): le cout de la douleur est METABOLIQUE, pas cognitif |
| `docs/revue-dogme-18082026` | `7f028c1` | docs(dogme): audit des 161 constantes — « rien en dur » est FAUX tel quel |
| `feat/v28-exocortex-c3` | `373743b` | docs: rattrape Parcourt_readme.md sur la v29 |
| `feat/v30-exo-sens` | `d3494a8` | docs(changelog): hash réel du commit v31.1-docs |
| `feat/v32-odorat-topologique` | `1291323` | feat(v32.0): odorat topologique (BFS) & clinotaxie |
| `feat/v33-memoire-emotionnelle` | `e0ba2bc` | docs(changelog): hash réel du commit de clôture v33 |
| `feat/v34-diagnostic-fatigue` | `1fed29e` | docs(changelog): hash réel du commit v36.0 |
| `feat/v37-equilibre-c1-c2` | `da24e06` | docs(diagnostic): note des bloquants en tête, avant merge |
| `feat/v38-monde-continu` | `167c046` | docs(v38): etat complet — 1 brique validee sur 6 |
| `feat/v39-memoire-abstraite` | `6e3440c` | docs(v39): dissection de g22 — le but vaut 16× le reste |
| `feat/v40-planification-emergente` | `003b3f8` | feat(v40): la planification emerge du vecu — 3 constantes supprimees |
| `feat/v40.1-envie-de-vivre` | `3fefad5` | docs(v41): decisions actees — benchmark C1 pur, C2 seul |
| `feat/v41-ligne-flottaison` | `bb1da9a` | feat(sens): v41.10 memoire par carte + v41.11 thermoception |
| `feat/v41.21-physique-et-cristallisation` | `ad9718f` | fix(changelog): rendre leurs vrais hash aux entrees v41.11+ |
| `feat/v41.25-nociception-thermique` | `36c60a1` | docs(changelog): hash reel de l'entree v41.25 |
| `feat/v41.26-thermohomeostasie` | `d273c23` | docs(changelog): hash reel de l'entree v41.26 |
| `feat/v41.27-douleur-unique` | `52c4e1a` | docs(changelog): hash reel de l'entree v41.27 |
| `feat/v41.30-constantes-fossiles` | `893d7f5` | docs(v41.32): trois pistes refutees avant d'etre codees |
| `feat/v41.32-sonde-mixage-et-refutations` | `ee7f5a1` | docs(changelog): hash reel de l'entree v41.33-licence |
| `fix/v41.25-douleur-annulee` | `c9ea1bf` | docs(changelog): hash reel de l'entree v41.25-fix1 |

## Ce qui ne change pas

- **`master` est la seule branche**, locale comme distante. Elle porte tout le cycle v28 → v41.51.
- La règle reste celle de `CLAUDE.md` : une branche `feat/…` ne se crée **que** pour un
  chantier qui doit pouvoir être **jeté**. Sinon, on travaille sur `master`.
- **Aucun `.brain` n'a été touché** : ils ne sont pas dans git (gitignorés), et la règle
  « toujours archiver, jamais supprimer » leur reste entièrement applicable.
