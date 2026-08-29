# 29/08/2026 — La course-poursuite, mesurée proprement : le prédateur RECULE

> Non normatif — carnet d'enquête. Corrige et clôt `CIBLE_MOBILE_28082026_*.md`.

## Ce que ce carnet corrige

Le 28/08, la dérive de représentation était annoncée avec un rapport proie/prédateur de
**×46** (g11) et **×14** (g22). **Ces chiffres sont retirés.** Deux biais :

1. **La proie était mesurée sans graine fixée** — l'environnement de mesure tirait ses
   cartes au hasard à chaque appel, donc une part de la « rotation » était du bruit
   d'échantillonnage. Le plancher de bruit n'existait pas encore dans la sonde.
2. **La vitesse du prédateur était DÉRIVÉE d'une formule**
   (`arctan(pas_relatif · cos / alignement)`), jamais mesurée.

Les deux grandeurs sortent désormais du **même protocole**, graine fixée, plancher publié.

## [1] La maturation est réelle — puis elle s'inverse

Rotation de l'axe, 300 nuits, graine de mesure fixée (plancher de bruit : **0,0198°**) :

| Bloc de 30 nuits | axe visuel | axe complet | ratio | erreur JEPA |
|---|---|---|---|---|
| 1–30 | **1,148°** | 1,622° | 1,41 | 0,00735 |
| 31–60 | 0,443° | 0,736° | 1,66 | 0,00434 |
| 61–90 | 0,242° | 0,353° | 1,46 | 0,00349 |
| **91–120** | **0,166°** | 0,283° | 1,70 | 0,00324 |
| 121–150 | 0,270° | 0,366° | 1,36 | 0,00315 |
| 151–180 | 0,328° | 0,417° | 1,27 | 0,00314 |
| 211–240 | 0,207° | 0,299° | 1,45 | 0,00304 |
| **271–300** | **0,409°** | 0,468° | 1,15 | 0,00290 |

**La décroissance s'arrête vers la nuit 100 (facteur 7), puis la rotation REMONTE.** Pente
sur la seconde moitié : **+0,00044 °/nuit**. Les 20 dernières nuits valent **0,506°**,
soit **2,1×** les nuits 61–80 (0,238°).

⚠️ **L'erreur JEPA, elle, converge proprement** — 0,00735 → 0,00290, décroissance monotone
sur les 10 blocs. **La remontée n'est donc pas causée par le modèle du monde**, qui a fini
d'apprendre. `dim_bus` est resté à 147 sur tout le run : la neurogenèse est écartée aussi.

⚠️ Le **ratio complet/visuel reste entre 1,15 et 1,70**, sans tendance à la baisse : le
corps continue de faire osciller la représentation même quand la vue se stabilise.

## [2] La course, les deux vitesses mesurées ensemble — 200 nuits

| | vitesse mesurée |
|---|---|
| **La proie** — l'axe informatif | **0,4203 °/nuit** |
| **Le prédateur** — `W` (rotation réelle des 7 lignes) | **0,0359 °/nuit** |
| **Rapport** | **×11,7** |

## [3] Le résultat décisif : l'alignement RECULE

```
alignement W↔axe :  0,1051  →  0,0917     (200 nuits)
gain net         : −0,000069 / nuit
```

Ce n'est pas que la tête est trop lente pour rattraper : sur ce run, elle **s'éloigne**.
La colonne `gain` est nulle ou négative sur toute la table, sans une seule séquence
positive durable.

## [4] Les deux mouvements sont COUPLÉS

Nuits 90–130 : `rot_axe` descend à 0,101–0,115° — la cible ralentit fortement — et `rot_W`
tombe **en même temps** à 0,012–0,017°.

**Le prédateur ne profite pas du ralentissement de la proie : il ralentit avec elle.** Les
deux mouvements viennent du même gradient. Ce n'est pas une course entre deux entités
indépendantes, c'est un système couplé dont le rapport reste à peu près invariant.

⚠️ **Conséquence directe pour toute intervention** : geler le tronc pourrait geler `W` du
même coup, rendant le ratio de rattrapage inopérant. Le « 12 nuits de gel pour regagner une
nuit de dérive » n'est **pas** une posologie utilisable — c'est un ordre de grandeur dont
la prémisse (que `W` continue d'avancer une fois la cible figée) n'est **pas mesurée**.

## Ce que ce carnet établit — et ce qu'il n'établit pas

**Établi**, sur ce protocole :
- la rotation de l'axe ne converge pas vers zéro : elle atteint un plancher vers 0,17° puis remonte ;
- le rapport de vitesse est **×11,7** ;
- l'alignement **recule** de 0,1051 à 0,0917 sur 200 nuits ;
- proie et prédateur ralentissent **ensemble** — ils sont couplés.

⚠️ **Non établi** :
1. **Que c'est LA cause du plafond au niveau 4.** L'axe mesuré est « but visible / absent » ;
   le lien avec la promotion du cursus reste **non mesuré**, réserve inchangée depuis le 28/08.
2. **Que c'est une impossibilité.** C'est un **recul mesuré sur 200 nuits, sur UN cerveau**
   (A_g11) — pas une preuve mathématique. La règle des 20 graines s'applique : ce résultat
   est une tendance forte, pas une conclusion de population.
3. **Que 0,42 °/nuit est anormal.** Aucune référence externe. Un PPO à tronc partagé sur la
   même tâche donnerait le point de comparaison ; **non fait**.
4. **Qu'une intervention marcherait.** Aucune testée, et [4] donne une raison de penser que
   la plus évidente (le gel) pourrait être inopérante.

## Ce que ce carnet ferme

L'hypothèse « il suffit d'attendre que le tronc se stabilise » est **réfutée sur ce run** :
la stabilisation a lieu (facteur 7 en 100 nuits) puis s'inverse, et l'alignement ne progresse
à aucun moment.

## Instruments (versionnés)

```bash
PYTHONPATH=src python -m naulthene.instruments.sonde_derive_longue <brain> --jours 300
PYTHONPATH=src python -m naulthene.instruments.sonde_course_poursuite <brain> --jours 200
```

⚠️ Les deux **entraînent** le cerveau fourni (elles le font vieillir) sans jamais le
sauvegarder. Travailler sur une **copie** reste la règle (§8).
