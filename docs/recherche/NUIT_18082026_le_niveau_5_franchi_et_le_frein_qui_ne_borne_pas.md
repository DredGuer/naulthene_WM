# La nuit du 18/08 — le niveau 5 tenu, et un frein qui ne borne rien

**18/08/2026** — carnet de recherche, non normatif.
Runs lancés dans la nuit après l'arbitrage utilisateur (Option B), coupés proprement au
matin (les `.brain` sont écrits chaque nuit : rien n'a été perdu).

---

## 1. Le résultat qui compte — le palier 5 est franchi ET tenu

**Option B, 20 graines × 1500 jours, plafond machine (160) :**

| Palier | Atteint | Wilson 95 % |
|---|---|---|
| niveau 4 | **20/20** | **100 %** [84–100] |
| niveau 5 | **4/20** | **20 %** [8–42] |

Et surtout, les quatre y **restent** :

| graine | niveau final | nuits passées au palier 5 |
|---|---|---|
| g6 | **5** | **1078** |
| g7 | **5** | **761** |
| g4 | **5** | **521** |
| g9 | **5** | 31 |

Trois cerveaux sur quatre vivent 500 à 1078 nuits sur `LavaGap` et y **terminent** leur
run. Ce n'est plus le cas d'`esprit_g7` (17/08), qui y était monté puis **redescendu** au
niveau 3 : là, le palier est tenu.

> **Comparaison avec l'historique du dépôt** : 0/20 au niveau 4 avant le brain-sparing
> (v41.16), puis 80 % [58–92] avec, et maintenant **100 % [84–100] au niveau 4 et 20 %
> [8–42] au niveau 5** sur 1500 jours. La durée compte : les campagnes précédentes
> faisaient 600 jours.

⚠️ Cette campagne n'a **pas de bras témoin apparié** : elle mesure un état, pas un effet.
Elle ne permet donc pas d'attribuer le gain à l'Option B plutôt qu'à la durée (1500 j
contre 600 j). C'est la mesure la plus favorable de la journée, donc celle à vérifier deux
fois (§3 de la règle de mesure).

Cerveaux archivés : `brains/nuit_18082026_V4123_optionB/`.

---

## 2. Le frein de l'Option B ne borne PAS la taille

Test décisif : plafond relevé à **512**, hors de portée (`NAULTHENE_PLAFOND_BUS`, banc de
mesure, jamais lu par la décision). Si le frein bornait la croissance, elle devait se poser
avant.

```
g7   dim_bus = 512/512   31 mutations
g11  dim_bus = 512/512   31 mutations
g33  dim_bus = 512/512   31 mutations
```

**Elle est allée jusqu'au mur.** Et la cause est mesurable :

| | erreur JEPA | `seuil_base` | rapport |
|---|---|---|---|
| cerveau **160** | 0,0047 | 0,00381 | 1,23 |
| cerveau **512** | **0,0013** | **0,00137** | 0,95 |

Les deux ont bien rattrapé leur erreur — **le frein fonctionne**. Mais le gros cerveau
prédit **3,6× mieux**, donc son seuil descend avec son erreur : il reste éternellement
« juste au bord » du déclenchement.

> Le rattrapage stabilise le **rapport** erreur/seuil, jamais la **taille**. Tant que
> grandir fait baisser l'erreur, grandir reste justifié.

⚠️ **C'est exactement le défaut de `reference_choc_dopamine`** (v37.1-fix1), documenté dans
CLAUDE.md : *une référence qui suit la décroissance ne borne plus rien.* Je l'ai reproduit
sans le reconnaître, dans un autre organe.

---

## 3. Grandir coûte cher et ne rapporte rien

Mêmes graines, 300 jours, plafond 160 contre 512 :

| | dim_bus | niveau max | énergie | effort |
|---|---|---|---|---|
| plafond 160 | 160 | 4 / 3 / 4 | **0,19** | **4,0** |
| plafond 512 | 512 | 4 / 3 / 4 | **0,017** | **12,6** |

**Niveau identique.** Énergie divisée par 11, effort triplé — `M_base = 512/16 = 32`, la loi
biologique des 2 %/20 % s'applique à la lettre. Le cerveau à 512 prédit mieux son monde et
meurt de faim.

Confirmé par la campagne partielle de la nuit (10 graines × ~750 j à plafond 512) :
énergie **0,016**, effort **13,01**, niveau 4 à 9/10 — soit *moins bien* que l'Option B à
160 pour 3,3× le coût.

**Trois campagnes convergent : agrandir le cerveau n'apporte aucune intelligence.**

---

## 4. Et la lave reste positive — même après 1078 nuits dessus

Lecture directe de l'empreinte de type des quatre cerveaux de niveau 5 :

| graine | `lava` | `WATER` | `goal` |
|---|---|---|---|
| g4 | **+0,0714** (×83) | +0,0741 (×8229) | +0,6466 |
| g6 | **+0,0728** (×144) | +0,0693 (×8592) | +0,6419 |
| g7 | **+0,0680** (×119) | +0,0595 (×9183) | +0,6841 |
| g9 | **+0,0813** (×15) | +0,0881 (×7574) | +0,6268 |

**La lave est positive et rigoureusement indiscernable de l'eau**, sur les quatre, après
des centaines de nuits passées à côté d'elle. L'agent tient le palier 5 **sans avoir appris
ce qu'est le danger** — il le traverse par vitesse et par chance, pas par compréhension.

La cause est connue et invariante : **MiniGrid punit la mort par exactement `0.0`**
(206 morts mesurées le 16/08). Un choc nul ne peut produire aucune valence négative, quel
que soit le nombre de répétitions.

---

## 5. Bilan de la nuit

**Acquis :**
- niveau 4 à **100 %** [84–100] et niveau 5 à **20 %** [8–42] sur 1500 jours, palier tenu ;
- le frein de l'Option B rattrape bien l'erreur (mécanisme validé) ;
- 4 cerveaux de niveau 5 archivés, exploitables pour toute autopsie ultérieure.

**Réfuté :**
- le frein **ne borne pas la taille** — il stabilise un rapport, pas une dimension ;
- **la croissance n'apporte rien** : 3 campagnes, 0 gain, coût métabolique ×3 à ×11.

**Inchangé, et c'est le blocage n°1 :**
- `lava` en valence **positive**. Tant que mourir ne coûte rien, « éviter le danger » est
  un palier littéralement inapprenable — et tout ce qui est franchi au-delà l'est par
  vitesse, pas par intelligence.
