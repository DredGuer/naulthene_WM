# LES GESTES STÉRILES — le gaspillage a-t-il persisté après la v41.28 ?

**Date** : 2026-09-01 · **Protocole écrit AVANT dépouillement** (Règle de Trace §4).

## La question

La v41.28 (26/08) a mesuré **57,2 %** de gestes stériles sur `Empty-5x5` et corrigé leur
**coût** (travail tenté : un geste stérile n'est plus gratuit). `CLAUDE.md` a inscrit à
cette occasion une condition explicite :

> « Si le gaspillage persiste après ce correctif, le levier suivant est le **BÉNÉFICE**
> (un geste qui ne change rien devrait n'apprendre rien), **pas** un durcissement du coût. »

Mesure du 01/09 sur `A_g66` (n=1) : **42,0 %**. La condition semble remplie — mais n=1 ne
conclut rien. Cette campagne porte la mesure à **n=20**, sur la cohorte déjà benchée les
30-31/08, donc **appariée** avec le succès et la directivité.

## Le protocole

| Élément | Valeur |
|---|---|
| Cohorte | les **20** cerveaux de `brains/30082026_plancher_n20/agregat.json` |
| Environnement | `MiniGrid-SimpleCrossingS9N1-v0` |
| Épisodes | 60 par cerveau, graines appariées (`90210 + ep`) |
| Régime | `eval()`, lecture seule, cerveau lu depuis une COPIE |
| Instrument | `src/naulthene/instruments/sonde_gestes_steriles.py` |

**Deux mesures indépendantes**, la seconde plus stricte :

1. `part_steriles` — part des actions 3 à 6 (`pickup`/`drop`/`toggle`/`done`).
2. `part_sans_effet` — part des ticks où **position, direction ET portage sont inchangés**
   après `env.step`. Lue sur le MONDE, jamais déduite du nom de l'action : elle capture
   aussi un `forward` contre un mur.

⚠️ La stérilité est ici une propriété de la **carte** (`SimpleCrossing` n'a ni objet ni
porte), vérifiée sur l'API (`carte_a_objets`) et non déclarée par une table.

## Ce que la mesure devra départager

| Si… | Alors |
|---|---|
| `part_steriles` élevée sur les 20 | le gaspillage a persisté → la condition de `CLAUDE.md` est remplie |
| `r(part_steriles, succès) < 0` significatif | le gaspillage **prédit** l'échec — piste causale |
| `r ≈ 0` | le gaspillage est **réel mais inerte** — comme la curiosité (rente sans effet) |

⚠️ **Vérification de tautologie obligatoire.** Un cerveau qui gagne finit ses épisodes
plus tôt ; s'il gaspille surtout en fin d'épisode, la corrélation serait un artefact de
durée. Contrôle : rapporter le gaspillage au **tick**, jamais à l'épisode — c'est déjà le
cas (`part = stériles / total_ticks`), mais à re-vérifier au dépouillement.

## Limites connues d'avance

1. Un banc forcé **ne prouve rien sur le cursus** (règle de mesure §6).
2. `SimpleCrossing` rend 4 actions stériles **par construction** : sur un niveau à portes
   (7+), `toggle` cesserait de l'être. Le chiffre ne se transporte pas tel quel.
3. Politique **figée** : rien ici ne dit ce qu'un agent apprenant ferait.

---

## ⚠️ Campagne INTERROMPUE le 01/09/2026, avant tout dépouillement

Lancée puis **arrêtée après le 1er cerveau** : la sonde portait le défaut d'instrument
décrit dans `docs/recherche/enquetes_closes/INSTRUMENT_01092026_la_memoire_du_banc.md`
(mémoire de travail lue en `penser()[1]` au lieu de `[4]`, donc **agent amputé**).

Le seul résultat produit (`A_g166`) a été **supprimé** plutôt qu'archivé : un JSON de
mesure fausse dans un dossier de campagne se relit six semaines plus tard comme une
mesure valide. La sonde est corrigée ; la campagne est **à relancer intégralement**.

Mesure indicative obtenue AVANT correction, à ne pas citer : `A_g66` 42,0 % de gestes
stériles, `A_g155` 36,2 % (n=1 chacun, régime amputé).
