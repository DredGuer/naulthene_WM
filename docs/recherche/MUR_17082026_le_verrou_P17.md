# Le mur du palier suivant — une boucle vicieuse dans P17

**17/08/2026** — carnet de recherche, non normatif.
Point 3 de la feuille de route : *« analyser sur les logs si le blocage provient de la
patience, de l'exploration ou de l'inhibition face aux nouveaux objets. »*

**Réponse : aucun des trois. Le blocage vient du cursus lui-même.**

---

## 1. Ce que les logs montrent au niveau 4 (`LavaGapS5`)

Les 6 runs qui ont franchi le niveau 4 grâce au brain-sparing y restent bloqués :

| graine | jours au niv. 4 | maîtrise max | approche du danger | patience |
|---|---|---|---|---|
| g1 | 357 | 45 % | 40 % | 270 |
| g2 | 518 | 35 % | 36 % | 259 |
| g4 | 274 | 35 % | 28 % | 259 |
| g6 | 256 | 25 % | 48 % | 254 |
| g7 | 448 | 35 % | 34 % | 266 |
| g8 | 307 | 35 % | 22 % | 268 |

Seuil de promotion : **60 %**. Aucun ne dépasse 45 %.

### Les trois hypothèses de la feuille de route sont écartées

| Hypothèse | Mesure | Verdict |
|---|---|---|
| **Patience** | 254–270 ticks, 0,1 abandon lucide/jour | ❌ la patience est large et peu consommée |
| **Exploration** | 0,7 sursaut de volonté/jour | ❌ l'agent explore |
| **Inhibition** face au danger | approche 22–48 % (baisse avec les runs les plus longs) | ❌ il évite déjà partiellement |

---

## 2. La vraie cause : P17 dilue l'entraînement là où il manque

Mesure sur g1, 357 jours passés au niveau 4 :

```
révisions/jour ............ 1,17
incursions/jour ........... 0,12
part de DÉFI visée ........ 34 %
épisodes hors palier ...... 621 (dont 362 réussis)
thermoception active ...... 32 jours sur 357  (9 %)
```

**L'agent ne joue son propre niveau qu'un tiers du temps.** Il perçoit donc la lave 9 %
des jours seulement — non parce que le capteur est défaillant (vérifié : la chaleur est
non nulle sur **100 %** des cases libres de `LavaGapS5`), mais parce qu'il est ailleurs.

### La boucle vicieuse, dans la formule elle-même

`_distribution_cursus` fait varier la part de défi avec la maîtrise :

| maîtrise | révision | **défi** | incursion |
|---|---|---|---|
| 0,00 | 66 % | **33 %** | 2 % |
| 0,20 ← *l'agent réel* | 61 % | **33 %** | 6 % |
| 0,30 | 58 % | **33 %** | 9 % |
| 0,45 | 36 % | **49 %** | 14 % |
| 0,60 ← *le seuil* | 15 % | **65 %** | 20 % |

> **Pour maîtriser, il faut s'entraîner. Pour s'entraîner, il faut déjà maîtriser.**

Ce n'est pas un bug : la formule fait exactement ce qu'elle décrit. Mais son intention
— *« un agent qui échoue révise ce qu'il sait faire »* — produit un **verrou** quand le
palier courant est précisément ce qu'il faut apprendre. La révision est pertinente pour
consolider ; elle est contre-productive quand elle remplace l'entraînement.

⚠️ **Le brain-sparing n'a pas supprimé ce verrou, il l'a déplacé d'un cran** — de
`SimpleCrossing` (niveau 3) vers `LavaGapS5` (niveau 4). C'est cohérent : il rend la
décision nette, il ne change rien à la distribution du cursus.

---

## 3. Ce que ça n'établit pas

- Le lien de causalité **n'est pas testé** : je mesure une corrélation (défi 33 % ↔
  maîtrise 20 %) et j'en propose un mécanisme. Une campagne A/B sur la part de défi est
  nécessaire pour trancher.
- **Le sens de la boucle est ambigu.** « Peu de défi ⇒ peu de maîtrise » et « peu de
  maîtrise ⇒ peu de défi » sont tous deux compatibles avec ces chiffres. La formule impose
  le second ; le premier reste à démontrer.
- Il est possible que `LavaGapS5` soit simplement **trop dur** à 33 % de défi comme à
  100 % — auquel cas le verrou n'est pas la cause mais un facteur aggravant.

---

## 4. Pistes, non tranchées

1. **Un plancher de défi dérivé, pas posé.** Faire dépendre la part de défi du *temps
   passé* sur le palier autant que de la maîtrise : un agent qui stagne 300 jours devrait
   voir sa part de défi monter, pas rester à 33 %. Attention : ce serait un second
   paramètre de pilotage, à dériver d'une grandeur vécue (jours de stagnation, déjà
   mesurée par `jours_stagnation_niveau`).
2. **Vérifier d'abord que le défi est le facteur limitant** : un run forcé à 100 % de défi
   sur `LavaGapS5` dirait en quelques heures si la maîtrise décolle. C'est le test le moins
   cher et il doit précéder toute modification de la formule.
3. Ne rien changer avant les résultats des campagnes n=20 et du plan factoriel en cours.
