# Le monde est trop pauvre pour qu'une corrélation émerge

**16/08/2026** — carnet de recherche, non normatif.
Constat de l'utilisateur : *« C'est la map qui manque d'éléments pour l'émergence par
corrélation ! »* — mesuré ici, et rapproché du scan des cerveaux.

---

## 1. L'inventaire

Contenu réel des cartes où l'agent est bloqué :

| Carte | Contenu |
|---|---|
| `Empty-5x5` | `wall` ×16, vide ×8, `goal` ×1 |
| `Empty-Random-6x6` | `wall` ×20, vide ×15, `goal` ×1 |
| **`Empty-8x8`** *(le blocage)* | `wall` ×28, vide ×35, `goal` ×1 |
| **`SimpleCrossing`** *(le mur, 0/20)* | `wall` ×38, vide ×42, `goal` ×1 |

Plus 2 balles rouges (`FOOD`) et 2 bleues (`WATER`) injectées par le projet.

**Cinq types pour 64 cases.** Le vocabulaire MiniGrid en offre huit (`wall`, `floor`,
`door`, `key`, `ball`, `box`, `goal`, `lava`) et six couleurs — le berceau en utilise
**trois**.

## 2. Ce que ça interdit

L'abstraction par récurrence (v36.0) apprend la valence de chaque type par accumulation.
Sur `Empty-8x8` :

- **63 cases sur 64 sont `wall` ou vide** → ~98 % du flux mnésique est du bruit de fond ;
- le `goal` n'est vu que dans un épisode **réussi**, soit ~25 % des épisodes ;
- surtout : **il n'y a aucune structure à découvrir.** Pas de séquence, pas de condition,
  pas de relation entre deux objets. Rien à comprendre — seulement quelque chose à
  atteindre.

Le premier niveau porteur d'une **causalité** est `DoorKey` (niveau 8) : `key → door →
goal`. C'est le premier palier où C2 aurait quelque chose à planifier.

## 3. Le rapprochement avec le scan des cerveaux

Le [scan du 16/08](SCAN_CERVEAUX_16082026.md) mesure que **C2 est 36 % plus gros chez les
agents qui échouent** (norme 1,33 contre 0,98). J'en avais tiré : « renforcer C2 est
corrélé à l'échec ».

Ce constat suggère une lecture plus juste :

> **C2 n'est pas inutile — il est sans objet.** Sur une pièce vide, il n'existe aucune
> séquence à simuler. Un organe de planification dans un monde sans structure ne peut que
> capter du gradient au détriment des couches qui agissent. Ce n'est pas un défaut de C2,
> c'est un défaut d'**environnement**.

Le cursus place les six premiers paliers dans des mondes sans causalité, puis attend de
l'agent qu'il franchisse un mur (`SimpleCrossing`, **0/20 graines**) avant d'avoir jamais
rencontré une seule relation entre deux objets.

## 4. Ce qui reste à arbitrer

Trois voies, non tranchées — c'est une décision de conception :

1. **Enrichir les cartes existantes** (ajouter `box`, `key`, des couleurs) sans changer la
   tâche : plus de types à corréler, même objectif. Risque : des objets décoratifs qui ne
   servent à rien produisent du bruit, pas de la structure.
2. **Réordonner le cursus** pour amener une causalité plus tôt (`DoorKey-5x5` avant
   `SimpleCrossing`). Le principe « une seule compétence change entre deux paliers »
   (invariant v35.0) devrait être revérifié.
3. **Accepter que les 3 premiers paliers soient moteurs** (décision utilisateur du 16/08 :
   *« c'est un moyen de comprendre les concepts en douceur »*) et ne mesurer C2 qu'à
   partir du premier palier structuré.

⚠️ **Aucune de ces voies n'est testée.** Et la mesure disponible ne permet pas encore de
trancher : la campagne A/B en cours porte sur la mémoire par carte, pas sur le contenu du
monde.

⚠️ **Attention au piège méthodologique** : « le monde est trop pauvre » est une hypothèse
*confortable* — elle déplace la cause hors de l'architecture. Elle doit donc être vérifiée
**deux fois plus** qu'une hypothèse défavorable (règle de mesure, §3). Le test décisif
existe et n'a pas été fait : **mesurer C2 sur `DoorKey`**, où la causalité existe. S'il y
est tout aussi inerte, le monde n'est pas la cause.
