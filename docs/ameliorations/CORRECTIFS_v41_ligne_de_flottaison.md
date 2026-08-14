# Correctifs v41 — La Ligne de Flottaison Métabolique

> **Statut : PROPOSÉ, non implémenté.** Aucune ligne de `src/` n'a été modifiée.
> Document de décision, rédigé pendant que les 3 runs V40 tournent (jour ~350/2000).
>
> Date : 14 août 2026 · Origine : lecture utilisateur du run V40 en cours

---

## 0. Ce que ce document n'est pas

Ce n'est **pas** un constat d'échec de la v40. La mécanique v40/v40.1 fonctionne
exactement comme spécifiée : l'envie de vivre s'éteint quand `danger ≫ okay`, et c'est
bien ce qui a été observé. Le défaut n'est pas dans la dynamique de l'envie — il est
**en amont**, dans ce qui alimente les deux réservoirs.

La v40 a rendu le défaut **visible**. C'est sa contribution.

---

## 1. Le diagnostic — une erreur d'échelle comptable

### 1.1 La mesure qui déclenche tout

Run `g11`, jour 348, graine 11 :

```
🏆 161 victoire(s) en 348 jour(s) | dernière il y a 0 j
└─ Erreur JEPA moy: 0.0047 | Réc. moyenne: 0.000 | Thermostat: Stable
├─ Planif. v40 : force 0.003 (okay 0.09 / danger 31.18)
├─ Envie v40.1 : 💀 éteint — envie 0.0024 | lucidité 0.995 ↓ foi 0.003 ↑
```

**Un agent qui gagne une fois tous les deux jours affiche une récompense moyenne de
`0.000` et un réservoir de danger 346× supérieur à son réservoir de succès.**

### 1.2 La reconstitution arithmétique

`nourrir_vecu_journee` (noyau.py:687) calcule :

```python
moyenne = sum(valeurs) / max(len(valeurs), 1)      # ← 400 ticks au dénominateur
echelle = max(self.reference_choc_dopamine, 1e-3)  # 0.208 mesuré
bilan   = clip(moyenne / echelle, -1, +1)
vecu_okay   += (|bilan| + bilan) / 2
vecu_danger += (|bilan| - bilan) / 2
```

Journée type de `g11`, reconstituée depuis les logs :

| Terme | Valeur mesurée |
|---|---|
| `r_bio` cumulé sur 400 ticks | **−2.30** |
| Victoires (≈0.46/jour × 1.0) | **+0.46** |
| **Somme de la journée** | **−1.84** |
| Divisée par 400 ticks | **−0.004593** |
| Normalisée par `réf. choc` 0.208 | **−0.0221** |

Répartition finale :

```
apport OKAY   = 0.0000      ← un jour AVEC victoire
apport DANGER = 0.0221
```

### 1.3 Le point d'équilibre prédit vs mesuré

Avec `x_eq = apport / (1 − oubli)` :

| Réservoir | Prédit | Mesuré (log g11) |
|---|---|---|
| DANGER | 221.0 | 31.18 *(pas encore à l'équilibre, j348)* |
| OKAY | 0.00 | 0.09 |
| **force = okay/(okay+danger+1)** | **0.0028** | **0.003** ✅ |

**Le modèle reproduit la mesure au millième.** La cause est établie sans ambiguïté :
la moyenne sur 400 ticks écrase la victoire (+1.0, un tick) sous le coût métabolique
(−2.30, réparti sur 400 ticks). *Le succès est noyé, la dépense de vivre subsiste.*

### 1.4 La formulation utilisateur

> « En moyennant 399 ticks d'effort continu avec 1 tick de victoire, on forçait
> l'algorithme à conclure que **vivre est une punition**. »

C'est exact, et c'est démontré ci-dessus. Il faut ajouter que `r_bio` est défini
(noyau.py:2184) comme :

```python
r_bio = deficit_avant - deficit_apres
```

C'est une **dérivée de déficit**. Quand les jauges dérivent vers zéro — état normal
d'un organisme qui dépense — ce terme est structurellement négatif. Il n'existe
aujourd'hui **aucun zéro de référence** : tout coût de fonctionnement est compté comme
une perte, donc comme du danger.

---

## 2. Les trois correctifs proposés

### C1 — Le zéro n'est pas 0.0, c'est la ligne de flottaison métabolique

**Principe.** Le métabolisme de base est le coût *incompressible* d'un organisme
vivant. Un pas qui consomme −0.02 de satiété est un pas **neutre** : ni danger, ni
succès.

| Ce qui doit compter comme… | Définition |
|---|---|
| **Neutre** | la dépense passive de repos — le coût d'exister |
| **DANGER** | l'asphyxie, le jeûne extrême (jauge proche de 0), le choc brutal, l'agonie |
| **OKAY** | toute élévation *au-dessus* du coût de flottaison : trouver de l'eau, ramasser un objet utile, franchir une porte, atteindre un but |

**Conséquence de conception.** Le bilan ne se mesure plus contre 0.0 mais contre un
`cout_neutre` — et ce coût doit être **dérivé, jamais posé** (règle n°1). Il est
mesurable : c'est la dépense métabolique d'un agent immobile, que l'agent peut
apprendre comme il apprend `reference_choc_dopamine`.

> ⚠️ **Piège à éviter** : `cout_neutre` ne doit pas devenir une constante `= 0.0057`.
> Il doit être une moyenne glissante de la dépense passive observée, avec la même
> discipline que `reference_choc_dopamine` — et probablement le même **cliquet**
> (v37.1-fix1), sinon un agent qui souffre longtemps recalibrera sa flottaison
> *vers le bas* et retrouvera le défaut actuel sous une autre forme.

### C2 — Séparer l'intégration du succès et du traumatisme (phasique vs tonique)

**Principe neurobiologique.** Deux voies distinctes :

| Voie | Nature | Ce qu'elle enregistre |
|---|---|---|
| **Dopamine phasique** (les pics) | événementielle | l'accomplissement — **jamais divisé par 400 ticks** |
| **Alerte viscérale** (les creux) | tonique | les vrais déficits critiques, pas la marche active |

**Formulation proposée :**

```
vecu_okay += Σ max(0, r_bio − cout_neutre)          # somme, pas moyenne
```

Une victoire à +1.0 s'inscrit **directement** comme événement marquant. Le danger, lui,
n'enregistre que les franchissements critiques (jauge proche de zéro), pas le simple
fait de bouger.

**C'est le correctif central.** Il change l'opérateur : `sum(...)/400` → `Σ` des
excédents. Une journée à 1 victoire cesse d'être arithmétiquement identique à une
journée à 0 victoire.

### C3 — Le rêve et le sommeil comme moteur de renaissance

**Principe.** Le sommeil ne fait pas que consolider — il **recharge**. Pendant la nuit :

1. Le cerveau consolide ce qu'il a compris (rêve JEPA) — *déjà implémenté*
2. L'organisme évacue la fatigue diurne — *partiellement implémenté*
3. **L'élan vital se régénère** — *absent* : un être vivant qui a dormi se réveille
   avec la pulsion intrinsèque de bouger et d'interagir

**Lien avec la v40.1.** Le correctif `fix1` avait déjà ajouté un terme additif
`∝ foi²` pour rendre la résurrection possible depuis un état quasi nul. C3 en est la
version **biologiquement fondée** : la régénération ne doit pas dépendre uniquement de
la foi (qui est nulle quand tout va mal) mais du **cycle de sommeil lui-même**.

> ⚠️ **Attention** : ceci ne doit pas réintroduire un plancher. La décision utilisateur
> « pas de plancher, certains runs mourront » reste valide. La différence est qu'un
> agent doit pouvoir *se relever s'il dort*, pas être *empêché de tomber*.

---

## 3. Ce que le run de 348 jours a démontré

**Ce n'est pas une faiblesse du projet, c'est une clarification théorique majeure.**

| Constat | Chiffre |
|---|---|
| **C1 est d'une robustesse spectaculaire** | 161 victoires / 348 jours, tête motrice + intégration sensorielle nominales |
| **Le JEPA comprend son monde** | erreur 0.0047 |
| **La « dépression » de C2 est comptable, pas cognitive** | force 0.003 reproduite au millième par le modèle §1.3 |
| **La v40 a rendu le défaut visible** | avant elle, la constante `FORCE_PLANIFICATION_LIBRE = 0.85` masquait le problème |

Le point le plus important : **l'agent n'était pas « découragé » au sens cognitif.**
Il faisait une comptabilité juste sur des données mal cadrées. C'est réparable en
amont, sans toucher à la dynamique v40/v40.1.

---

## 4. Effet attendu des correctifs (à vérifier, non mesuré)

Avec C1+C2 appliqués et les mêmes journées mesurées :

```
apport OKAY   ≈ 0.46/jour   (les victoires, non noyées)
apport DANGER ≈ 0.00        (les jauges ne franchissent pas le critique)
force         → okay/(okay+danger+1) tend vers ~0.3, puis croît
```

Au lieu de `0.003`. **Chiffre théorique — à confirmer par un run**, pas à annoncer.

---

## 5. Ordre d'implémentation proposé

| # | Correctif | Coût | Risque |
|---|---|---|---|
| 1 | **C2** (somme des excédents) | faible — un opérateur | change la dynamique, mesurable immédiatement |
| 2 | **C1** (`cout_neutre` dérivé) | moyen — nouvelle grandeur apprise | doit être un cliquet, sinon défaut sous autre forme |
| 3 | **C3** (régénération nocturne) | moyen | ne doit pas devenir un plancher déguisé |

**Recommandation : C2 seul d'abord**, sur une graine, 300 jours. C'est le correctif
dont l'effet est le plus isolable — si la force de planification décolle, la cause
§1 est confirmée expérimentalement et non plus seulement arithmétiquement.

---

## 6. Ce qui reste à trancher (décision utilisateur)

1. **Attendre la fin des 3 runs V40** (~16h25) pour avoir la courbe complète à
   2000 jours, ou couper maintenant ? *Le jour 348 suffit déjà au diagnostic.*
2. **C2 seul ou C1+C2 ensemble ?** Ensemble va plus vite mais rend l'attribution
   impossible si le résultat est mitigé.
3. **Branche `feat/v41-ligne-flottaison` depuis `feat/v40.1-envie-de-vivre` ?**

---

*Document créé le 14 août 2026 pendant les runs V40. Aucun code modifié.*
*Les mesures §1 proviennent de `/private/tmp/v40_g11.log`, jour 348.*
