# Campagne 23/08/2026 — Sonde de discrimination, PREMIER RUN (artefact)

> ⚠️ **Ce dossier est la version INVALIDÉE.** La version corrigée, avec son protocole et ses
> chiffres, est [`../23082026_v4132_discrimination_fix1/`](../23082026_v4132_discrimination_fix1/LISEZ_MOI.md).
> Conservé au titre de la Règle de Trace (« un artefact écarté : le test qui l'a écarté, pas
> seulement sa conclusion »).

## Ce qui a été mesuré ici, et pourquoi c'était faux

Question : l'agent distingue-t-il un **mur** d'une **ressource** quand `contact_frontal = 1`
(bit unique dérivé de `can_overlap()`, qui vaut 1.0 pour les deux) ?

Ce premier run donnait `consommer sur ressource = 0,0 %` sur **60/60 nuits**, alors que le
même run enregistrait **295 saisies réelles**. Incompatible ⇒ artefact.

**Cause** : `env.step` s'exécute ~370 lignes avant la sonde. MiniGrid avait déjà exécuté
`pickup`, la Ball était dans `carrying`, la case frontale était vide au moment de la lecture.
Même décalage temporel qu'en v41.25-fix1 (chaleur) et v41.5 (maturité) : une grandeur lue en
queue de tick a traversé un `env.step` qui l'a périmée.

## Ce qu'il y a dans ce dossier

| Fichier | Contenu |
|---|---|
| `E5_g11.brain` / `.log` | `Empty-5x5`, graine 11, 60 nuits |
| `N4_g11.brain` / `.log` | niveau 4, graine 11, 60 nuits |

`N4_g11.brain` est **bit-identique** (vérifié `cmp`, 02/09/2026) à
`../23082026_v4132_discrimination_fix1/N4_g11.brain` et à `base.brain` de
`../25082026_v4132_collision/` et `../25082026_v4132_thrashing_pisteC/` : c'est le cerveau
g11 de niveau 4 qui a servi de point de départ à toute la série de sondes v41.32.

Les **logs** sont les seuls fichiers propres à ce dossier — ils portent le run artefactuel.
