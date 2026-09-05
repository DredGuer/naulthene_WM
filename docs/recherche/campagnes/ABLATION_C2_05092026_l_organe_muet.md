# L'ABLATION PROPRE DE C2 — le néo-cortex ne sert à rien, cette fois sans confusion

**Date** : 2026-09-05 · **Statut** : ✅ **RÉPONSE ÉTABLIE** ·
**n = 20 graines appariées × 3 bras × 1500 jours** · **40 runs neufs**, 40/40 valides,
**0 échec** · `δ_A/A = 0,000000`.

> **Protocole et 4 juges écrits AVANT le lancement**
> (`brains/05092026_ablation_c2/LISEZ_MOI.md`). C'est la **première ablation de C2 qui isole
> C2** — voir §2.

---

## 1. Le résultat en une ligne

**Couper la voix de C2 ne change rien, et cette fois le résultat n'est pas confondu.**
Le vrai levier n'est pas C2 : c'est la **renormalisation de C1**, qui décide à elle seule si
un cerveau atteint le niveau 4 (**20/20**) ou reste au niveau 3 (**19/20**).

## 2. Pourquoi le résultat historique ne valait rien

Le dépôt affirmait depuis des mois : *« couper C2 ne change le score de 0,0 point sur les
6 niveaux »* (78 cellules d'ablation). 🔴 **Vérifié dans le code le 05/09** :

```
banc_ablation.py:246   c2_coupe  ->  force_planification = 0
noyau.py:5362          vigueur_min_c1(f) = 2.1 × f
noyau.py:1429          gain_c1 = clamp(vigueur_min_c1(f) / amplitude_c1, 0.25, 4)
```

À `force = 0` le numérateur s'annule ⇒ **`gain_c1` plaqué à sa borne basse, 0,25**.
L'ablation coupait C2 **ET étranglait C1 à un quart** (règle de mesure §6.2).

⚠️ **Deux rectifications du récit** : `c2_coupe` n'existe **que dans le banc**, jamais dans
le cursus — le « 0,0 pt » venait d'un banc court sur cerveau entraîné. Et **aucun drapeau ne
coupait C2 dans le cursus** avant `--sans-c2` (v41.57), écrit pour cette campagne.

| Ablation | `gain_c1` mesuré | C1 |
|---|---|---|
| `c2_coupe` (historique) | **0,25** | **étranglé à un quart** |
| **`--sans-c2` (ici)** | **1,0000** (LIBRE) · **2,3632** (témoin) | **intact** |

## 3. Les quatre juges

| Juge | Critère | Mesuré | Verdict |
|---|---|---|---|
| **4. Garde-fou** | `gain_c1` intact | 1,0000 / 2,3632 (vs 0,25) | ✅ **PASSE** — campagne valide |
| **1. Maîtrise** | δ LIBRE − LIBRE_SANS_C2, `t` > 2,86 | δ **−1,375** · `t` = −1,15 · 5/20 | ❌ **C2 est INERTE** |
| **2. Niveau** | δ LIBRE − LIBRE_SANS_C2 | δ **+0,000** · 0/20 | ⚠️ **SATURÉ** — voir §4 |
| **3. Confusion** | LIBRE_SANS_C2 − TEMOIN_SANS_C2 | niveau **+0,950** · `t` = **+19,00** | ✅ **la confusion est ÉNORME** |

### Juge 1 — la réponse à la question posée

δ = **−1,375 pt** (`t` = −1,15, NS), **5/20 favorables**, et le test de tautologie ne change
rien (δ = −1,375 conditionné). Sans les 4 extrêmes : δ = −1,562, `t` = −1,58, toujours NS.

> **Couper C2 ne coûte rien.** Le signe est même légèrement négatif — l'agent fait
> *marginalement mieux* sans son néo-cortex, mais l'écart n'est pas significatif.

**Puissance du test** : σ des paires = 5,35 pt ⇒ **effet minimal détectable = 3,42 pt**.
Un effet réel de C2 supérieur à 3,4 pt aurait été vu. En dessous, non — c'est la limite
honnête de cette campagne.

### Juge 3 — l'effet le plus fort du dépôt, et il ne concerne pas C2

À **C2 coupé des deux côtés**, seule la renormalisation diffère :

| | δ | `t` | favorables |
|---|---|---|---|
| **Amplitude C1** | **+3,983** | **+20,64** | **20/20** |
| **Niveau** | **+0,950** | **+19,00** | **19/20** |
| Maîtrise | −12,500 | −7,11 | 1/20 |

**Comptage** : **20/20** cerveaux `LIBRE_SANS_C2` atteignent le niveau 4, contre **1/20** au
témoin. La renormalisation de C1 décide du palier atteint ; C2 n'y est pour rien.

## 4. ⚠️ Deux vérifications qui changent la lecture

### (a) Le juge 2 est SATURÉ — `δ = 0` n'est pas une absence d'effet

Les **40 runs des deux bras LIBRE sont au niveau 4**, le plafond du dépôt. Un δ de 0 sur
0/20 est donc un **plafond**, pas une mesure. ⚠️ **Le juge 2 ne pouvait pas détecter un effet
de C2**, quel qu'il soit — c'est le juge 1 (maîtrise, plage 0-15 %, **non saturée**) qui porte
la réponse.

*Résultat « trop propre » suspecté puis expliqué, conformément à la règle §3.*

### (b) L'inversion du juge 3 est un ARTEFACT DE PALIER

Le δ maîtrise de **−12,50 pt** semblait contredire le δ niveau de +0,95. **À palier égal, il
disparaît** :

| Bras | Maîtrise médiane |
|---|---|
| LIBRE — **niveau 4** (n=20) | **10,0 %** |
| LIBRE_SANS_C2 — **niveau 4** (n=20) | **10,0 %** |
| TEMOIN_SANS_C2 — **niveau 3** (n=19) | 25,0 % |
| TEMOIN_SANS_C2 — **niveau 4** (n=1) | **10,0 %** |

Les témoins ont une maîtrise plus haute parce qu'ils jouent un **niveau plus facile**. Le seul
témoin arrivé au niveau 4 retombe exactement à **10 %**, comme les deux bras libres.
**Comparer la maîtrise de cerveaux à des paliers différents n'a aucun sens.**

## 5. Vérifications passées

| Vérification | Résultat |
|---|---|
| **A/A** (2 runs identiques, 40 j) | ✅ **bit-identiques**, `δ_A/A` = **0,000000** |
| Drapeau atteint (leçon v41.4) | ✅ 40/40, assertion runtime + contrôle post-run |
| Contamination croisée | ✅ 0/20 témoins portent `[BRAS A]` |
| Runs complets | ✅ 40/40 à 1500 nuits (garde-fou anti-run-inachevé ajouté au dépouillement) |
| Extrêmes (le test qui a tué la directivité) | ✅ juges 1 et 3 inchangés |
| Tautologie | ✅ δ maîtrise identique conditionné |
| Bonferroni 3 métriques | seuil `t` = 2,86 |
| Saturation | 🔴 **détectée sur le juge 2**, voir §4a |

## 6. Limites — écrites avant qu'on me les oppose

1. ⚠️ **Effet minimal détectable = 3,42 pt.** Un C2 qui apporterait 1 ou 2 points serait
   invisible ici. « C2 est inerte » signifie « son effet est sous 3,4 pt », pas « exactement
   zéro ».
2. ⚠️ **C2 tourne toujours** : seule sa *voix* est retirée de la fusion. Son gradient continue
   d'irriguer le tronc via `simuler_futur_et_planifier`. Cette campagne ne dit **rien** de ce
   canal-là — `--sans-gradient-c2` existe pour ça et n'a pas été rejoué ici.
3. ⚠️ **Mesuré au plafond du niveau 4 seulement.** C2 pourrait servir aux niveaux 6-7
   (DoorKey), jamais atteints — les termes `Jalons`/`Guidage` y sont d'ailleurs à σ = 0 pour
   la même raison.
4. ⚠️ **Corrélationnel sur le lien renormalisation → palier** : le juge 3 est un A/B propre,
   mais il ne dit pas *pourquoi* la voix libre débloque le niveau 4.

## 7. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** :
- ✅ **Le « 0,0 pt » historique est réhabilité** — il était confondu, mais sa conclusion tient
  une fois la confusion levée. Premier cas de la semaine où une réfutation survit à sa
  correction méthodologique.
- ❌ « C2 est bridé par l'étranglement de C1 » : **réfuté**. `gain = 1,00`, et C2 ne sert
  toujours à rien.
- ❌ « Le juge 2 prouve que C2 est inerte » : **non**, il est saturé. C'est le juge 1.

**Ouvert** :
1. 🔴 **La refonte de C2 en générateur d'intention devient justifiée par la mesure.** L'organe
   actuel (`cortex_prefrontal : dim_bus → 1`, **956 params, 0,06 %** du réseau) est un critique
   scalaire sans effet comportemental. ⚠️ Il est petit **par construction** — l'élargir
   casserait la baseline de l'avantage : il faut **ajouter une tête**, pas remplacer celle-ci.
2. 🟡 **Le gradient de C2 vers le tronc** n'est pas mesuré par cette campagne.
3. 🟡 **L'hémisphère audio** : 18,70 % du réseau, terme `Vocal` à σ = 0. Ablation non faite.
4. 🔴 **Le mur du niveau 4 tient** — 60 runs, 3 bras, aucun cerveau au niveau 5.

---

*25ᵉ explication mesurée. La question « C2 sert-il quand C1 respire ? » a désormais une
réponse : **non**, à moins de 3,4 pt près.*
