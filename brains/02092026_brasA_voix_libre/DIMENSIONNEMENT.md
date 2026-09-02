# Dimensionnement du bras A — combien de graines, combien de jours ?

> **Écrit le 02/09/2026, PENDANT la campagne, avant tout dépouillement de succès.**
> Analyse de puissance sur la variance réelle du dépôt, et test de plateau sur les
> 15 paires déjà terminées. Aucun taux de succès n'est lu ici — seulement l'entropie
> jouée (juge n°1) et la dispersion inter-graines.

---

## 1. Combien de GRAINES — l'analyse de puissance

La variance qui compte est celle **inter-graines** au banc. Mesurée sur le rejeu 20/20
(`02092026_rejeu_banc_corrige/`, banc 300 épisodes, instrument corrigé) :

| Grandeur | Valeur |
|---|---|
| Succès moyen | **15,02 %** |
| **Écart-type inter-graines** | **11,58 pt** |
| Étendue | 1,00 % → 40,00 % |

C'est énorme : **l'écart-type vaut 77 % de la moyenne**. Deux cerveaux au même régime vont
de 1 % à 40 %.

**Effet minimal détectable** (test apparié, Bonferroni 2 métriques ⇒ `t* = 2,43`,
corrélation de paires ρ ≈ 0,5) :

| n graines | Effet minimal détectable |
|---|---|
| 10 | **8,90 pt** |
| 15 | 7,26 pt |
| **20** | **6,29 pt** ← le protocole |
| 30 | 5,14 pt |
| 40 | 4,45 pt |

**Lecture.** À n=20, on ne verra un effet que s'il dépasse **~6,3 points** de taux de
succès. Le protocole vise « témoin ~12 % → LIBRE > 25 % », soit **+13 pt** : largement
au-dessus du seuil. **n=20 est donc suffisant pour l'effet espéré** — et c'est aussi le
plancher imposé par la règle des 20 graines.

⚠️ **Mais n=20 ne verra PAS un effet modeste.** Un vrai +4 pt (une amélioration réelle du
tiers) serait rendu « non significatif ». Passer à n=40 double le coût pour gagner 1,8 pt
de sensibilité : **ça ne vaut le coup que si le résultat à n=20 tombe entre 4 et 6 pt**,
c'est-à-dire dans la zone d'ambiguïté. Décider **après**, pas avant.

---

## 2. Combien de JOURS — le test de plateau

C'est ici que le protocole initial est **sous-dimensionné**, et la mesure le dit.

Entropie jouée (juge n°1, max 1,946), sur les 15 paires terminées :

| Bras | n | H(début) | H(j50) | H(fin) | Pente des 20 derniers jours |
|---|---|---|---|---|---|
| **LIBRE** | 15 | 1,890 | 1,477 | **1,234** | **−0,00745/j** — **12/15 encore en baisse** |
| **TÉMOIN** | 15 | 1,942 | 1,480 | 1,595 | +0,00090/j — 4/15 (plateau) |

**Le témoin a convergé. Le bras LIBRE, non.** À 100 jours il descend encore, dans
**12 graines sur 15**.

Extrapolation linéaire de la pente courante :

| Cible | Jour atteint (extrapolé) |
|---|---|
| H = 1,0 | ~131 |
| H = 0,7 | ~172 |
| H = 0,5 | ~199 |

### Ce que ça implique

1. **Le juge n°1 est déjà tranché — et largement.** Critère : H < 1,75 en médiane sur
   LIBRE. Mesuré : **1,234** (témoin 1,595). Le mécanisme **mord**, sans ambiguïté.
   L'hypothèse « la netteté n'est pas apprenable parce que le gain la renormalise » est
   **confirmée sur son versant mécanique** : retirer le gain libère bien la netteté.
2. **Les juges 2 et 3 sont lus TROP TÔT.** Le succès et la directivité sont mesurés sur un
   cerveau dont la politique **n'a pas fini de se durcir**. Un δ nul à j100 ne dira pas
   « la netteté ne sert à rien » mais « la netteté à H=1,23 ne sert à rien » — ce qui n'est
   pas la même affirmation, et pas celle que l'hypothèse voulait tester.
3. ⚠️ **Et une netteté qui continue de monter n'est pas gratuite.** C'est le mode d'échec
   du 01/09 (λ=0,9, « confiant dans l'erreur ») : une politique qui se durcit **sur une
   mauvaise direction** empire. Le signe du δ succès contre la netteté est donc à lire, et
   il peut être **négatif** — ce serait un résultat, pas un raté.

### La recommandation

| | Jours | Pourquoi |
|---|---|---|
| Campagne en cours | **100** | ✅ **à terminer telle quelle** — elle tranche le juge n°1, qui conditionne tout le reste. Coût déjà engagé à 78 %. |
| **Si le juge 1 passe** (c'est le cas) | **200** | le plateau de LIBRE est extrapolé vers j170-200. C'est le premier jour où « le succès sous politique nette » veut dire quelque chose. |
| Au-delà | ❌ | 300+ jours n'apporte rien tant que le plateau n'est pas franchi ; et le banc forcé ne prouve toujours rien sur le cursus (limite n°1 du protocole). |

**Coût mesuré** : ~6-7 min par run de 100 jours (Apple Silicon, `mps`). Donc :

- 40 runs × 100 j ≈ **4 h 30** (la campagne actuelle)
- 40 runs × 200 j ≈ **9 h** (la suite, si juge 1 positif)

---

## 3. L'incident de collision — consigné

⚠️ **Deux lanceurs ont tourné simultanément** le 02/09 vers 21h01 : un lanceur d'origine
(PID 17163, démarré à 17h42) et un second lancé par erreur (PID 71838), tous deux écrivant
`LIBRE_g177` et `TEMOIN_g177`. C'est exactement la collision que `CLAUDE.md` interdit
(« deux runs partageant le même fichier s'écrasent mutuellement »).

**Traitement** : le second lanceur a été tué ; le `.brain` qu'il avait commencé à écrire
(`TEMOIN_g177`, ~5 nuits au lieu de 100) est **archivé, pas supprimé**, dans
`_ecarte_collision/`. Le lanceur d'origine, étant idempotent (`[ -f ] && continue`), aurait
**sauté** cette graine en la croyant faite : sans ce retrait, la cohorte aurait contenu un
cerveau de 5 nuits parmi 19 cerveaux de 100 nuits, **en silence**.

> **Leçon, à ajouter à la règle de mesure** : avant de lancer une campagne, vérifier qu'un
> lanceur ne tourne pas déjà (`ps aux | grep lancer.sh`). Un script idempotent protège
> contre le doublon de *travail*, pas contre le doublon d'*écrivain*.

---

*Analyse écrite avant dépouillement des juges 2 et 3, conformément à la Règle de Trace.*
