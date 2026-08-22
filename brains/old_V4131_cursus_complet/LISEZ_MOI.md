# ⚠️ Dossier VIDE — les données de cette campagne sont PERDUES

**Campagne v41.31-cursus** — 20 graines × 2 bras × 1500 jours = **40 runs, tous complets**,
terminée le 22/08/2026.

Les 40 `.brain` et 40 `.log` ont été écrits dans un **scratchpad de session**, purgé
quelques minutes après la fin des runs. Aucune copie n'a survécu.

**Cause : erreur de méthode.** La convention du projet impose `brains/`, pas un répertoire
temporaire. Les runs auraient dû y être copiés dès la fin de la première vague.

## Ce qui survit

Les chiffres, extraits **avant** la purge et donc exacts :

| métrique | CAUSAL | TEMOIN | Δ | t |
|---|---|---|---|---|
| niveau final | 4,10 | 4,05 | +0,050 | **+0,37** |
| maîtrise (100 dern.) | 11,50 | 10,41 | +1,09 | **+0,39** |
| énergie (100 dern.) | 0,228 | 0,227 | +0,001 | **+0,07** |
| satiété min | 0,061 | 0,029 | +0,032 | +2,17 ⚠️ NS après Bonferroni |

**0 run sur 40 ne dépasse le niveau 5/15.**

Compte rendu complet :
[`docs/etat_des_lieux/22082026_campagne_v41.31_cursus_complet.md`](../../docs/etat_des_lieux/22082026_campagne_v41.31_cursus_complet.md)

## Ce qui est perdu

Toute **réanalyse**. Aucune métrique non calculée avant la purge n'est accessible, et les
calculs ci-dessus ne sont plus vérifiables par relecture des fichiers.

## La règle qui en découle

> **Une campagne écrit directement dans `brains/<nom_campagne>/`, dès le premier run.**
> Le dossier se crée **avant** le lancement, jamais « on rangera à la fin ».
