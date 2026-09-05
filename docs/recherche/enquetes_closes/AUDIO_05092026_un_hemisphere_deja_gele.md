# L'HÉMISPHÈRE AUDIO — il n'y a rien à geler, il est déjà gelé

**Date** : 2026-09-05 · **Statut** : ✅ **TRANCHÉ À COÛT ZÉRO** — la campagne prévue est
**annulée** · **80 cerveaux × 1500 jours**.

---

## 1. La question posée

L'hémisphère audio/vocal (`porte_auditive`, `generateur_attente_audio`, `tete_vocale`) pèse
**290 976 paramètres — 18,70 %** du réseau à 1500 jours, pour un terme `Vocal` à
**σ = 0,0000** sur 60 000 nuits de cursus MiniGrid, monde silencieux.

Hypothèse : *« entretenir un cortex auditif dans un monde muet est une taxe computationnelle
absurde ; le geler doit libérer de la capacité »*. Campagne prévue : 20 paires × 1500 j, ~8 h.

## 2. Le drapeau a été écrit, et son pré-vol a tout arrêté

`--sans-audio` (v41.59) gèle les trois couches (`requires_grad = False`), avec assertion de
réalité (`0 restant entraînable`). Il **mord** : *« 2 592 paramètres audio gelés (33,26 % du
réseau) »*.

🔴 **Mais le run est BIT-IDENTIQUE au bras de référence.** Zéro ligne de différence sur toute
la trace — le motif exact du bug v41.4, qui impose de ne rien lancer avant d'avoir compris.

## 3. La cause : l'audio ne recevait déjà AUCUN gradient

La **myéline ne vient que du gradient** (invariant v34.0/v37.0). Mesurée sur un cerveau de
1500 jours :

| Couche | `myeline_cumul` moyenne |
|---|---|
| **`porte_auditive`** | **0,00000000** |
| **`generateur_attente_audio`** | **0,00000000** |
| **`tete_vocale`** | **0,00000000** |
| `porte_visuelle` | 0,00156474 |
| `tete_motrice` | 0,00149060 |
| `cortex_prefrontal` | 0,00121881 |
| `integrateur_bio` | 0,00084821 |

### Vérifié sur toute la population disponible

| | |
|---|---|
| Cerveaux examinés | **80** (campagnes `04092026_cursus_complet` + `05092026_ablation_c2`) |
| **Cerveaux avec myéline audio > 0** | **0 / 80** |
| Maximum observé, toutes couches audio, tous cerveaux | **0,0000000000** |
| Myéline moyenne des autres couches | 0,00108566 (min 0,00080, max 0,00164) |

> **L'hémisphère audio n'a reçu aucun gradient sur 80 cerveaux × 1500 jours.**
> Le geler ne change rien **parce qu'il est déjà gelé**.

## 4. Pourquoi le forward ne coûte rien non plus

`porte_auditive` est **sans biais** (documenté l. 438) : `relu(porte_auditive(zeros))` vaut
**0,000000 exactement**. En cursus silencieux, l'hémisphère n'ajoute donc rien au bus **et**
n'apprend rien.

⚠️ **Le coût réel n'est ni le gradient ni le forward** — c'est la **mémoire** (290 976
paramètres portés, sérialisés, agrandis par la neurogenèse) et le temps d'optimiseur sur des
gradients nuls. Un coût **computationnel**, jamais cognitif.

## 5. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** :
- ❌ « Geler l'audio libérera de la capacité cognitive » : **il n'y a rien à libérer.**
  L'hémisphère ne consomme aucune capacité d'apprentissage.
- ✅ **La campagne de 20 paires est annulée** — elle aurait mesuré un δ nul garanti par
  construction, soit **8 h de machine pour un résultat connu d'avance**.
- ✅ Le drapeau `--sans-audio` est **conservé** : il devient le témoin propre du jour où une
  leçon vocale sera active (cursus de la Parole), où la comparaison aura enfin un sens.

**Ouvert** :
1. 🟡 **Le coût mémoire reste réel** : 18,70 % du réseau à 1500 j (**33,26 % à la naissance**
   — la part dépend de `dim_bus`, ne jamais la coder en dur). Le **supprimer** est une autre
   question que le **geler**, et elle casserait la rétrocompatibilité des `.brain`.
2. 🔴 **Pourquoi la neurogenèse agrandit-elle des couches qui n'apprennent jamais ?**
   `porte_auditive` et `generateur_attente_audio` grandissent avec `dim_bus` sans jamais
   recevoir un gradient. Question ouverte, non mesurée.

## 6. Leçon de méthode

> **Un pré-vol qui donne un résultat bit-identique n'est pas forcément un drapeau mort.**

Ce matin, un run bit-identique signalait un bug de harnais (zsh et `$FLAGS`). Cet après-midi,
le même symptôme est **le résultat lui-même**. La différence ne s'établit pas en regardant le
drapeau, mais en mesurant **ce que la lésion était censée retirer** — ici la myéline, trace
directe du gradient.

*Une campagne de 8 h évitée par une lecture de 80 fichiers.*

---

*26ᵉ mesure. Elle ne réfute pas le plafond : elle annule une piste avant qu'elle ne coûte.*
