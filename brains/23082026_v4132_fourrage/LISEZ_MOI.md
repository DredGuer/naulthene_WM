# Campagne 23/08/2026 — La sonde de fourrage (v41.32, étape 2)

## Ce qu'on cherchait

**Pourquoi un agent entraîné récolte-t-il 1,68 FOOD/jour quand un marcheur aléatoire en
récolte 3,33 ?** (mesuré le 23/08, 3 graines, même distribution d'actions).

Hypothèse testée : *le gradient aurait appris à ne plus tenter de manger*, `ACTION_CONSOMMER`
étant coûteux et sa récompense mal attribuée. L'agent choisirait l'agonie lente plutôt que
l'effort.

## Protocole

Test **A/A** (`CLAUDE.md` §5), graine 11, **60 jours**, cursus complet.
Sonde `_sonder_fourrage` — télémétrie **pure**, vérifiée statiquement (n'écrit que dans
`fourrage_*`).

**δ_A/A = 0** — les deux runs sont bit-identiques sur 60 nuits.

## Résultat

| Grandeur | Valeur |
|---|---|
| Occasions (face à une ressource) | **52,2/jour** |
| Gestes `consommer` joués | **52,5/jour** |
| **Saisies (conjonction réussie)** | **4,2/jour** |
| **Taux de saisie** | **8,1 %** |
| Gestes dans le vide | **92,0 %** |
| Faim moyenne aux occasions | **0,961** (1,0 = famine totale) |

## 🔴 L'hypothèse est RÉFUTÉE

**Prédiction** : les tentatives décroissent au fil des jours.
**Mesure** : elles **triplent** — 27,2 → 56,0 → 74,2 gestes/jour.

Le geste n'est **pas** réprimé, il est **renforcé**. Et le taux de saisie **monte** aussi
(4,2 % → 8,1 % → 13,0 %). L'agent n'est pas anorexique : il essaie de manger 52 fois par
jour, de plus en plus souvent, en famine quasi totale (0,961).

## Ce que la sonde trouve à la place

Manger exige une **conjonction** (v41.2-fix5/fix6) : faire **face** à la ressource **et**
jouer `ACTION_CONSOMMER`. Les deux termes marchent séparément — 52,2 occasions et 52,5
gestes par jour, sur 400 ticks. **C'est leur intersection qui échoue.**

### Le test d'indépendance

| | |
|---|---|
| Saisies attendues si les deux événements étaient **indépendants** | **378,9** |
| Saisies **observées** | **253** |
| **Ratio observé/attendu** | **0,67** |
| Nuits sous le hasard | **49/60 (82 %)** |

🔴 **L'agent fait MOINS BIEN que le hasard sur la conjonction.** Ses deux comportements ne
sont pas seulement décorrélés : ils sont **anti-corrélés**. Il joue le geste quand il n'est
pas en face, et se trouve en face quand il ne joue pas le geste.

## Ce que cela oriente (non tranché)

La cause n'est ni la navigation, ni la motivation, ni le coût du geste. C'est un défaut de
**coordination temporelle** entre deux sorties de la même tête motrice. Pistes :

- La ressource est-elle **perceptible** dans la case frontale au moment de décider ? (la vue
  est un cône, l'odorat est topologique — mais le contact frontal a-t-il un canal dédié ?)
- Le crédit du soulagement (v41.2-fix7) atteint-il le tick du geste, ou le suivant ?
- `ACTION_CONSOMMER` est-il joué en réponse à la faim (état interne) plutôt qu'à la présence
  (état externe) ? Un geste piloté par la faim seule serait exactement anti-corrélé à
  l'occasion.

## Fichiers

- `AA_g11_rep{1,2}.brain` / `.log` — les deux runs A/A (60 nuits chacun)
- `resultats_fourrage.json` — l'agrégat, à côté des sources (`CLAUDE.md` §7)
