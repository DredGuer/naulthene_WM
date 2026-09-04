# LA TABLE DE MIXAGE — les 5 termes morts ne sont pas du code mort

**Date** : 2026-09-04 · **Statut** : ✅ **DIAGNOSTIC ÉTABLI**, hypothèse de départ **retournée** ·
**60 000 nuits de bilan, 40 runs, n = 20 paires** · coût : **zéro run**.

---

## 1. La question posée

`recompense_interne` somme **11 termes à poids 1** (`noyau.py` ~l. 9965). Une addition
`a + b + c` est en réalité une pondération `1a + 1b + 1c` **codée en dur** : si un terme a
une variance très supérieure aux autres, il dicte le gradient.

La sonde `_sonder_mixage` (v41.32) mesure `n, Σx, Σx²` par terme. La question posée était
double :

1. **Quelle est la pondération réelle ?**
2. **Les 5 termes à σ = 0 sont-ils jamais déclenchés, ou déclenchés à valeur constante ?**
   (Deux pathologies opposées : le premier est inerte, le second est un décalage d'origine
   qui déplace toutes les valeurs sans jamais distinguer une action d'une autre.)

## 2. La pondération réelle — 60 000 nuits

| Terme | σ moyen | **Part du gradient** | Nuits où σ > 0 |
|---|---|---|---|
| **Bio** (le corps) | 0,054177 | **57,0 %** | 100 % |
| **Env** (la victoire) | 0,020516 | **21,6 %** | **51 %** |
| SousObjectif | 0,010198 | 10,7 % | 99 % |
| Progres | 0,004929 | 5,2 % | 100 % |
| Curiosite | 0,004622 | 4,9 % | 100 % |
| Stagnation | 0,000526 | 0,6 % | 100 % |
| Jalons | 0,000007 | 0,0 % | **0 %** (43/60000) |
| Guidage | 0,000000 | 0,0 % | **0 %** (3/60000) |
| Portes | 0,000000 | 0,0 % | **0 %** (3/60000) |
| Vocal | 0,000000 | 0,0 % | **0 %** (0/60000) |
| CoutC3 | 0,000000 | 0,0 % | **0 %** (0/60000) |

**Le corps pèse 2,6× la victoire.** L'agent consacre l'essentiel de sa puissance
d'apprentissage à ses viscères ; le signal de la tâche est minoritaire.

## 3. Les 5 termes morts : **jamais déclenchés**, et c'est NORMAL

Diagnostic : `μ = 0` **et** `σ = 0` sur 40 runs ⇒ **jamais déclenchés**, aucun n'est un
décalage d'origine. Et la cause est la même pour tous : **ils n'ont rien à mesurer sur les
niveaux joués.**

Niveaux réellement traversés par les 40 runs : **1, 2, 3, 4** — soit `Empty-Random-6x6`,
`Empty-8x8`, `SimpleCrossingS9N1`, `LavaGapS5`.

| Terme | Pourquoi il est nul |
|---|---|
| **Jalons** | garde `if etat.doorkey_actif` — `DoorKey` est au **niveau 7+**, jamais atteint |
| **Guidage** | même garde : `recompense_continue` vient du détecteur DoorKey |
| **Portes** | détecteur générique, mais **aucune porte** sur les niveaux 0-4 |
| **Vocal** | cursus MiniGrid pur, aucune leçon vocale ⇒ `avec_micro_recompense=False` |
| **CoutC3** | aucun plug C3 enregistré ⇒ `ACTION_DEMANDER` masquée à `-inf` (invariant v28.0) |

> 🔴 **L'hypothèse de départ est retournée.** Ces termes ne sont **pas** « du code mort
> exécuté dans le chemin critique de l'optimiseur ». Ce sont des capteurs **corrects, mais
> hors de leur domaine d'application** — l'agent est bloqué avant d'atteindre les
> environnements où ils ont un sens.
>
> **Les supprimer serait une erreur** : ils redeviendraient nécessaires au niveau 6-7.
> Ils ne coûtent rien (une addition de zéro), et leur nullité est un **symptôme du
> plafond**, pas sa cause.

## 4. La correction d'une mesure publiée le même jour

⚠️ Les chiffres publiés dans `CHANGELOG` v41.54 (`Bio` 62,1 % · `Env` 17,4 %) étaient lus
sur **la dernière journée de chaque run seulement**. Or `Env` est nul **51 % des nuits**
— non parce que l'agent ne gagne jamais, mais parce qu'il **ne gagne pas ce jour-là**.

Sur la vie entière, **tous les cerveaux gagnent** : victoires cumulées médianes
**860** (LIBRE) et **682** (TÉMOIN), **0 cerveau à zéro victoire** dans les deux bras.

| Mesure | `Bio` | `Env` |
|---|---|---|
| Dernière journée (publié en v41.54) | 62,1 % | 17,4 % |
| **60 000 nuits (correct)** | **57,0 %** | **21,6 %** |

La conclusion qualitative **ne change pas** (le corps domine la victoire), mais le ratio
passe de **3,57×** à **2,64×**. C'est cette valeur qui fait foi.

## 5. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** :
- « 5 termes morts = code mort à nettoyer » : **faux**. Ils sont hors domaine, pas défectueux.
- Le diagnostic « jamais déclenché vs constant » : tranché, c'est **jamais déclenché** pour les cinq.

**Ouvert — et c'est là qu'est le vrai sujet** :

🔴 **Le ratio Bio/Env de 2,64×.** Le corps porte 57 % du gradient, la tâche 21,6 %. Deux
lectures possibles, **non départagées** :

1. **Pathologie** — l'agent optimise sa survie et résout le labyrinthe par accident.
2. **Fonctionnement voulu** — c'est un organisme homéostatique ; un vrai animal consacre
   aussi l'essentiel de son apprentissage à ne pas mourir.

⚠️ **Rien dans cette mesure ne tranche.** Et le dépôt a déjà réfuté deux fois une corrélation
métabolique (`maîtrise ~ énergie` : +0,710 à n=10 → **−0,0588** à n=20).

⚠️ **Ne pas normaliser par σ.** Aplatir mathématiquement les 6 termes vivants remplacerait
une pondération arbitraire par une autre, plus difficile à remettre en cause. Si une échelle
doit être posée, elle doit être **dérivée** du monde ou du corps — comme
`GAIN_MINIMAL_VICTOIRE / max_steps` l'a été en v41.43.

**Le test qui trancherait** : un bras où `Bio` est mis à l'échelle par une grandeur dérivée
(ex. le déficit maximal survivable), témoin apparié, 20 graines. **Non lancé.**

---

*Diagnostic établi à coût nul, sur les données de la campagne `04092026_cursus_complet`.*
