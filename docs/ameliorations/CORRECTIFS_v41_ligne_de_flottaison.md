# Correctifs v41 — La Ligne de Flottaison Métabolique

> **Statut : LIVRÉ** (commit `04080c4`, branche `feat/v41-ligne-flottaison`).
> Correctifs **C1 + C2 implémentés ensemble** — la mesure §8 a montré qu'ils ne sont
> pas dissociables. **C3 (renaissance nocturne) reste proposé, non implémenté.**
>
> Date : 14 août 2026 · Origine : lecture utilisateur du run V40 en cours
>
> **Résultat en une ligne :** C2 passe de mort (2000 nuits/2000) à dominant
> (ratio 1,41×) ; la force de planification de **0,000 à 0,462**.
>
> ⚠️ La v41 rend C2 **audible**. Elle n'a **pas** démontré qu'il *sert* — voir §9.
>
> 🛑 **INFIRMÉ SUR LE FOND (15/08).** La campagne de 10 graines a tranché : **0 promotion
> sur 10 × 2000 jours**, et l'ablation donne **`c2_coupe` = +0,0 sur les 6 niveaux**. Le
> niveau 4 de g22 (§10) était une **loterie natale**, pas un effet du correctif ; le
> réveil de C2 est un **transitoire de 500 jours**. La correction d'échelle reste acquise,
> son effet sur les actes n'existe pas.
> → [CAMPAGNE_v41_population_et_ablation_aout_2026.md](../recherche/CAMPAGNE_v41_population_et_ablation_aout_2026.md)

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

## 6. Décisions prises (14 août 2026)

| # | Question | Décision |
|---|---|---|
| 1 | Couper ou laisser tourner ? | **Laisser tourner jusqu'à 2000 jours** |
| 2 | C2 seul ou C1+C2 ? | **C2 seul** — 300 jours, graine 11 |
| 3 | Branche | **`feat/v41-ligne-flottaison`** depuis `feat/v40.1-envie-de-vivre` |

### 6.1 Pourquoi laisser tourner (décision utilisateur)

Les 3 runs V40 ne sont pas un run raté à interrompre — c'est **le tout premier
benchmark de référence sur 2000 jours d'un système réflexe pur (C1 isolé)**, l'envie
de vivre étant éteinte depuis le jour ~50. Trois choses à en tirer :

1. Vérifier empiriquement si `vecu_danger` **plafonne à son asymptote théorique
   de ~221** (§1.3) ou s'arrête avant.
2. Vérifier si la **robustesse synaptique de C1 tient sans dégradation** à très
   long terme, sans aucun apport de C2.
3. Servir d'**étalon** pour mesurer le gain réel de la v41.

C'est le point important : cette référence « C1 pur » n'existait pas, et elle ne
sera pas reproductible une fois la v41 posée.

### 6.2 Pourquoi C2 seul d'abord (règle d'or du projet)

**Une seule mutation causale à la fois.** Modifier simultanément l'intégration du
vécu (C2) et la dynamique du métabolisme viscéral (C1) rendrait impossible de savoir
lequel des deux a restauré la force de planification.

Tester d'abord la correction de l'**opérateur** dans la comptabilisation nocturne du
vécu isole l'effet direct sur la résurrection de C2 (`f_planif ≈ 0.3` attendu).

---

## 7. Raffinement des deux réserves

### 7.1 La ligne de flottaison ne doit pas être un seuil en dur

**Le piège.** Écrire `cout_neutre = 0.0057` violerait le principe directeur.

**La solution — moyenne glissante + cliquet asymétrique.** La dépense basale est
suivie par une moyenne glissante du coût métabolique passif des pas **ordinaires**
(sans choc).

Le **cliquet de flottaison**, exactement comme `reference_choc_dopamine`
(v37.1-fix1) : si l'agent traverse une famine prolongée, sa ligne de flottaison ne
doit **pas s'effondrer vers le bas** — sinon la famine serait normalisée comme état
ordinaire, et le défaut §1 reviendrait sous une autre forme.

> La descente doit rester **non nulle mais minimale** (« un variation minimal ») :
> un monde durablement plus pauvre doit pouvoir recalibrer l'agent, mais sur des
> centaines de nuits, jamais sur une saison creuse. Même formulation que le cliquet
> v37.1-fix1.

### 7.2 Le sommeil sans béquille artificielle

La phase nocturne ne doit **pas** être un « bouton magique » qui réinjecte de l'envie
de vivre arbitrairement.

Ce que le sommeil fait légitimement :
- consolider les représentations JEPA ;
- dissiper la **tension d'échec immédiate**.

Ce qu'il ne doit pas faire : garantir la survie. **Si un agent est dans une impasse
absolue sans aucun renforcement positif pendant des centaines de jours, sa mort
cognitive doit rester mathématiquement possible.**

> C'est la garantie que la réussite, quand elle advient, est une **véritable
> émergence adaptative** — et non le produit d'un filet de sécurité.

Cette décision confirme et prolonge le choix « pas de plancher » de la v40.1.

---

---

## 8. Le benchmark « C1 pur » — l'étalon (3 graines × 2000 jours)

Les 3 runs V40 ont été menés à terme **précisément pour servir de référence**. C'est le
premier benchmark d'un système réflexe pur, non reproductible une fois la v41 posée.

| | g11 | g22 | g33 |
|---|---|---|---|
| Victoires / 2000 j | 774 | **880** | 624 |
| Niveau | 1/15 | 1/15 | 1/15 |
| Maîtrise | 5 % | 10 % | 10 % |
| `vecu_danger` | 186,02 | 172,80 | 153,28 |
| `vecu_okay` | 0,04 | 0,34 | 0,25 |
| force planif. | 0,000 | 0,002 | 0,002 |
| envie | 0,0000 | 0,0000 | 0,0000 |
| erreur JEPA | 0,0116 | **0,0026** | 0,0146 |
| C2 | 0,000 | 0,000 | 0,000 |

### 8.1 L'asymptote prédite était FAUSSE — et c'est instructif

Prédiction §1.3 : `vecu_danger` plafonne vers **221**. Mesure : la trajectoire est
**linéaire**, sans aucun aplatissement.

```
g11 : 0 → 17,9 → 35,8 → 52,5 → 71,0 → 91,1 → 110,4 → 129,2 → 147,6 → 166,9 → 186,0
```

Pente sur les **200 derniers** jours : **+0,096/jour**. L'asymptote existe (~950) mais
2000 jours n'en montrent que le début.

**Cause : `OUBLI_DANGER = 0,99990` a une demi-vie de 6931 jours.** Sur un run de 2000
jours, l'oubli n'existe pas — le réservoir *accumule*. Le cliquet n'était pas
asymétrique, il était **inopérant des deux côtés** (`OUBLI_OKAY` : 1386 jours, encore
70 % de la durée d'un run).

> **Leçon** : une constante d'oubli ne se lit pas en « pour mille par jour », elle se
> lit en **DEMI-VIE** — et la demi-vie doit être comparable à l'échelle de temps du
> vécu. C'est un cas de plus du fil « une échelle absolue posée a priori, jamais
> confrontée à une mesure » (cf. `SEUIL_CRISTAL`, `q_ref = 1.0`).

### 8.2 Le résultat le plus troublant

**g22 est le meilleur partout** — 880 victoires, JEPA à 0,0026 (4× meilleur que g33),
accord C1/C2 à **100 %** — et il est bloqué au **niveau 1/15 à 10 % de maîtrise**,
comme les deux autres.

Un agent qui prédit son monde presque parfaitement, dont les deux têtes s'accordent sur
100 % des ticks, et qui gagne tous les 2 jours, ne progresse **pas d'un seul palier en
2000 jours**. La compétence est là ; c'est sa **conversion en progression** qui est
cassée.

### 8.3 Zéro tick de repos — la contrainte imprévue

`ticks en zone critique : 400/400` sur **les trois graines**. L'agent n'a **aucun tick
de repos** dont dériver une flottaison. C'est ce qui a imposé de la dériver de la
**médiane du jour** plutôt que d'un état de repos observé.

---

## 9. Résultat de la v41 — run test 300 jours (graine 11)

| Critère fixé | Cible | Résultat |
|---|---|---|
| 1. `danger` ne sature plus les jours de victoire | — | ✅ 245,6 vs `okay` 211,5 |
| 2. `okay` décolle proportionnellement | — | ✅ **0 → 211,50** |
| 3. `force` en zone utile | 0,20–0,40 | ✅ **0,462** |
| 4. `envie` s'anime | > 0,30 | ✅ **1,0000** |

| | V40 (2000 j) | **V41 (300 j)** |
|---|---|---|
| `vecu_okay` | 0,04 | **211,50** |
| **force planif.** | 0,000 | **0,462** |
| **envie** | 0,0000 💀 | **1,0000** 🔥 |
| C2 | 0,000 | **1,425** |
| ratio C1/C2 | 0,00× | **1,41×** |
| erreur JEPA | 0,0116 | **0,0035** |

**C2 mort 1 nuit sur 300** (contre 2000/2000 en V40). Le rapport de force s'est
**inversé** — C2 (1,425) parle plus fort que C1 (1,010) — et se stabilise dès le jour
~30 (ratio 0,96×–1,32× sur tout le run).

### 9.1 ⚠️ Ce que ce run ne démontre PAS

**Niveau 1/15, maîtrise 0 %, 54 victoires en 300 jours** — intervalle de 5 jours, contre
**3 jours** en V40 avec C2 éteint.

La v41 a rendu C2 **vivant et audible**. Elle n'a **pas** montré qu'il **sert**. Sur
300 jours c'est trop court pour trancher : à lire comme « pas encore de bénéfice
mesurable sur la tâche », **jamais** comme « C2 nuit ». Un run 2000 j × 3 graines,
directement comparable à §8, est en cours.

### 9.2 Une projection démentie — note de méthode

La projection annonçait une envie stabilisée à **0,11–0,20**, donc **sous** le critère 4.
Mesure : **1,0000**.

L'erreur venait d'une hypothèse `lucidité ≈ 0,99`. Elle vaut **0,574** : la lucidité est
le produit `compréhension_C2 × expérience_C1`, et C1 s'étant affaibli *relativement*
(gain ×1,01), le second terme reste bas. L'érosion (`0,02 × 0,574 = 0,0115`) est donc
battue par l'apport (`0,03 × 0,462 = 0,0139`).

> **La foi n'avait pas besoin d'atteindre 0,66 — il suffisait que la lucidité reste
> modérée.** Une projection à un seul paramètre libre, sur une mécanique où deux
> grandeurs bougent ensemble, n'est pas une prédiction : c'est une intuition chiffrée.

---

## 10. LE RÉSULTAT — 2000 jours × 3 graines

**Le premier franchissement de palier du projet.** Zéro graine V40 n'a quitté le
niveau 1 en 2000 jours ; g22 atteint le **niveau 4** et y tient 1223 jours.

| | g11 | **g22** | g33 |
|---|---|---|---|
| **Niveau** | 1/15 | **4/15** | 1/15 |
| Victoires | **1266** | 1011 | 503 |
| Maîtrise | 25 % | 30 % | 15 % |
| force | 0,383 | **0,724** | 0,370 |
| envie | 1,0000 | 1,0000 | 0,4563 |
| ratio C1/C2 | 1,58× | **4,59×** | 0,08× |
| `okay`/`danger` | 420/676 | **426/161** | 397/676 |

### 10.1 Face à l'étalon « C1 pur »

| | V40 | **V41** |
|---|---|---|
| Niveau max (3 graines) | **1/15** | **4/15** |
| Victoires g11 | 774 | **1266** (+64 %) |
| Victoires g22 | 880 | **1011** (+15 %) |
| Victoires g33 | 624 | 503 (−19 %) |
| force | 0,000–0,002 | 0,370–**0,724** |
| envie | 0,0000 sur les 3 | 0,46–**1,00** |
| C2 mort | **2000 nuits/2000** | ~0 |

### 10.2 La promotion est un DÉBLOCAGE, pas une montée

```
jour 770 → niveau 2
jour 775 → niveau 3
jour 778 → niveau 4     puis PLUS RIEN pendant 1223 jours
```

**Trois paliers en 8 jours après 769 jours de plateau.** L'agent avait la compétence
bien avant ; il lui manquait le seuil de maturité. Une fois franchi, les deux suivants
tombent presque immédiatement — puis le niveau 4 se révèle un vrai mur.

### 10.3 ⚠️ LA LOTERIE NATALE — le résultat le plus dérangeant

Les trois graines partent du **postulat strictement identique** : même code, mêmes
constantes, `.brain` vierge. Seule la graine change (init des poids, cartes MiniGrid,
échantillonnage des actions).

**La divergence est visible dès la NUIT 1.**

| | g11 | **g22** | g33 |
|---|---|---|---|
| Nuit 1 — `okay`/`danger` | 1,00 / **1,00** | 1,00 / **0,00** | 1,00 / **1,00** |
| Nuit 1 — force | 0,333 | **0,500** | 0,333 |
| 1ʳᵉ victoire | jour 7 | **jour 2** | jour 6 |
| Jour 50 — `danger` | 48,34 | **1,28** | 41,53 |

g22 a eu une première nuit **sans aucun danger** — pas moins : *zéro*. Au jour 50,
l'écart est déjà de **38×**.

**Le mécanisme s'auto-entretient :**

```
carte facile au départ → danger bas → force haute → C2 délibère
   → C2 fait gagner → okay monte, danger stagne → force encore plus haute
```

Et symétriquement pour g33 : danger élevé → force basse → C2 se tait → C1 seul →
moins de victoires → danger monte. À 2000 jours, C1 = 6,788 contre C2 = 0,567.

**Les demi-vies rendent la divergence quasi irréversible** : un danger accumulé au
jour 50 met 500 jours à s'effacer de moitié. L'écart de 38× ne se rattrape pas.

> C'est à double tranchant. **Le bon côté** : la boule de neige demandée en v40.1
> (« effet boule de neige, mais certains éléments peuvent changer le sens ») est là,
> mesurable, dans les deux directions. **Le côté gênant** : la trajectoire se joue dans
> les **50 premiers jours**, donc on mesure aussi une part de chance natale.
>
> `PRUDENCE_NAISSANCE = 1,0` — une seule observation fictive — ne pèse rien face à un
> écart de 38×. C'est le candidat de correctif direct, mais il exige d'abord de savoir
> si le taux de réussite est de 1/3 ou si g22 était un coup de chance : **campagne de
> 10 graines lancée** le 14/08 à 19h35.

---

## 11. Ce qui reste ouvert

| # | Sujet | État |
|---|---|---|
| **Population** | 1/3 est-il le taux réel ? | ✅ **TRANCHÉ — non.** 0/10 graines. Au plus 1/13 |
| **Ablation** | Que porte réellement g22 ? | ✅ **TRANCHÉ** — C2 à +0,0 × 6 ; 6 lésions sur 13 sans effet |
| **C3** | Renaissance nocturne | proposé, non implémenté (§2) |
| **P-lucidité** | Rapport `POIDS_LUCIDITE`/`POIDS_FOI` | jamais confronté à une mesure |
| **`PRUDENCE_NAISSANCE`** | Amortir la loterie natale | candidat — **en réserve** (arbitrage utilisateur) |
| **Le mur du niveau 4** | 1223 jours sans bouger | diagnostic à part entière |
| **Les 3 variables mortes** | `envie` 1,0000 · `danger` 676 · accord 0 % | **nouveau** — issu de la campagne |
| **Les mémoires nuisibles** | couper l'hippocampe **améliore** sur 4/6 niveaux | **nouveau** — issu de l'ablation |
| **README faux** | « couper C2 double le taux de succès » → **0,0 pt** | à corriger des deux côtés |

> Les pistes de correctif issues de la campagne sont **tenues en réserve** à la demande
> explicite de l'utilisateur (15/08) — ne rien implémenter sans arbitrage.

---

*Document créé le 14 août 2026 pendant les runs V40 ; mis à jour après livraison.*
*Mesures §1 : `/private/tmp/v40_g11.log` (j348) · §8 : les 3 logs V40 à 2000 j ·*
*§9 : `/private/tmp/v41_g11.log`.*
