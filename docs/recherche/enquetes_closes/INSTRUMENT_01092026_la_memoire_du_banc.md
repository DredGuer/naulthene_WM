# L'INSTRUMENT — le banc jouait à MÉMOIRE NULLE depuis le 30/08

**Date** : 2026-09-01 · **Nature** : ⚠️ **correction d'instrument** · **Portée** : toutes
les mesures de banc des 30-31/08/2026.

> Consigné au titre de la Règle de Trace, §1 : « un **instrument est corrigé** → écrire ce
> qu'il mesurait faux, et depuis quand ». Trouvé par accident, en cherchant autre chose.

---

## 1. Le défaut

`AGI_Naulthene.penser()` retourne **8 valeurs** :

| Index | Contenu | Forme (dim_bus=158) |
|---|---|---|
| 0 | `logits_finaux` | (1, 8) |
| **1** | **`valeur_etat_courant`** | **(1, 1)** |
| 2 | `parametres_vocaux` | (1, 8) |
| 3 | `pensee_enrichie` | (1, 158) |
| **4** | **`memoire_actuelle`** ← la mémoire de travail | **(1, 158)** |
| 5 | `bus_latent` | (1, 158) |
| 6 | `logits_routage` | (1, 5) |
| 7 | `indecision_c2` | float |

Les trois sondes de banc lisaient la mémoire en **[1]** au lieu de **[4]** — donc la
VALEUR d'état, un scalaire, à la place de la mémoire.

## 2. Pourquoi c'est resté invisible

Le code était protégé par un garde-fou :

```python
memoire = sortie[1] if torch.is_tensor(sortie[1]) and \
    sortie[1].shape[-1] == modele.dim_bus else memoire
```

`sortie[1]` a la forme `(1,1)`, donc `shape[-1] == 158` est **toujours faux**. Le garde-fou
faisait exactement son travail : il a **empêché le crash**. Mais du même coup :

- `memoire` restait au `torch.zeros(1, dim_bus)` de son initialisation, **à chaque tick** ;
- `episodiques` n'était **jamais** alimenté, donc `contexte` valait `contexte_vide()` en
  permanence.

**L'agent jouait sans mémoire de travail et sans contexte épisodique, du premier tick au
dernier.** Aucune exception, aucun avertissement, aucune valeur aberrante.

> 🔴 **La leçon.** Un `try`/garde-fou qui « protège » un chemin de données peut convertir
> une erreur bruyante en **mesure silencieusement fausse**. C'est le même motif que le bug
> v41.4 (le drapeau d'ablation n'atteignait pas le module) et que `SEUIL_CRISTAL` (une
> branche exécutée chaque nuit qui ne se déclenchait jamais) : **le code tournait, et ne
> faisait rien**. Un garde-fou sur une forme doit **crier** quand il rejette, jamais
> retomber en silence sur une valeur par défaut.

## 3. Ce qui est affecté

| Mesure | Date | Statut |
|---|---|---|
| Plancher géométrique (entraîné vs neuf vs aléatoire) | 30/08 | ⚠️ **à re-mesurer** |
| Directivité des 20 cerveaux (`r = −0,8225`) | 31/08 | ⚠️ **à re-mesurer** |
| Inertie motrice (λ) | 01/09 | ⚠️ **à re-mesurer** — même sonde |

**Ce qui n'est PAS affecté** (aucun `penser()` de banc dans la boucle) :

- toutes les mesures lues **dans les `.brain`** (valences, empreintes, maîtrise, poids) ;
- la ligne de base **PPO** (implémentation séparée) ;
- le témoin **aléatoire** (n'appelle pas le réseau) — 17/300 reste exact ;
- la simulation géométrique du 01/09 (aucun cerveau) ;
- les mesures de barème, de récompense, de diète (`sonde_recompense`, cohorte).

## 4. Le sens probable de l'erreur

L'agent mesuré était **amputé**, donc les scores de banc sont vraisemblablement des
**sous-estimations** de la politique réelle. Trois conséquences à vérifier, pas à supposer :

1. Le taux de succès entraîné (25,83 % agrégé, 37,33 % pour `A_g66`) peut **monter**.
2. La directivité (13,8×–22,8×) peut **baisser** — une mémoire de travail est précisément
   ce qui permettrait de tenir un cap.
3. La corrélation `r(directivité, succès) = −0,8225` peut se renforcer, s'affaiblir ou
   changer de nature. **Elle n'est pas invalidée : elle est non établie.**

⚠️ **Ce qui reste solide indépendamment de ce défaut** : le témoin aléatoire à 5,67 % et
la ligne de base PPO à 27–40 % ne passent pas par ce code. Le fait que les cerveaux
entraînés dépassent largement l'aléatoire tenait déjà **avec** l'amputation ; le corriger
ne peut que renforcer ce point, jamais l'inverser.

## 5. Le correctif

`memoire = sortie[4]`, sans garde-fou silencieux, dans les trois sondes
(`sonde_plancher_geometrique.py`, `sonde_inertie_motrice.py`, `sonde_gestes_steriles.py`),
avec le tableau des 8 sorties en commentaire au point de lecture.

## 6. Ce que cela change à la méthode

La règle de mesure interdit déjà de conclure sous 20 graines et exige un A/A. **Aucun des
deux n'aurait attrapé ce défaut** : le banc était parfaitement déterministe (δ_A/A =
0,000000) et reproductible à n=20. Il mesurait juste, avec constance, **autre chose que ce
qu'il annonçait**.

> **Règle qui en découle** : un banc qui rejoue une politique doit **vérifier que son état
> interne évolue** — au minimum, journaliser que la mémoire de travail n'est pas restée
> nulle. Un état figé est le symptôme d'un canal débranché, exactement comme un delta de
> `+0,0` sur toutes les cellules d'une ablation.
