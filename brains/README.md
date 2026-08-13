# `brains/` — les cerveaux cristallisés

> Un `.brain` représente des centaines de jours de run. **On archive, on ne supprime
> jamais** (règle du projet, `CLAUDE.md`).
>
> Les `.brain` sont **gitignorés** (`brains/**/*.brain`, sous-dossiers compris) : ce fichier
> est la seule trace versionnée de ce que contient le dossier.
>
> Dernier archivage : **14 août 2026** — 166 cerveaux, 387 Mo.

---

## État actuel

**La racine est vide.** Tout cerveau à la racine est un run *en cours* ou *tout juste
terminé* ; dès qu'une campagne est close, ses cerveaux descendent dans un `old_VXX/`.

| Dossier | Contenu | Cerveaux |
|---|---|---|
| `old_V30/` | tout ce qui précède la v30.0 | — |
| `old_testV30-V34/` | tests intermédiaires v30 → v34 | — |
| `old_V37/` | lignée v34 → v37 (8 cerveaux) + `recherche_aout2026/` (70 cerveaux de la campagne d'ablation et d'hypothèses des 11-12 août) | ~78 |
| **`old_V38/`** | **campagne du chantier v38 (12-13 août)** — voir détail ci-dessous | **59** |
| `ablations/` | résultats JSON du banc d'ablation | — |

---

## `old_V38/` — le chantier du monde continu

Archivé le 14 août 2026. Ces cerveaux ont produit les résultats du
[chantier v38](../docs/ameliorations_appliquees/CHANTIER_v38_monde_continu.md).

| Sous-dossier | Condition testée | Cerveaux |
|---|---|---|
| `campagne_2a/` | continuité du monde (+ témoins) | 15 |
| `campagne_2b/` | densité de ressources | 8 |
| `campagne_2c/` | parent physique (2c, 2c-fix, 2c-bis, 2c-ter) | 27 |
| `campagne_2d/` | liage multimodal | 8 |
| `ablations_aout/` | ablations sensorielles et quête libre | 1 |

### ⚠️ Ces cerveaux ont été produits avec un banc d'essai BIAISÉ

C'est la raison principale de leur archivage. La
[revue de code du 13-14 août](../docs/recherche/REVUE_CODE_v39_aout_2026.md) a établi que
le réarmement de tâche plaçait le but **du mauvais côté de la porte** dans une proportion
importante des cas :

| Carte | Cartes gagnables **sans la clé** |
|---|---|
| `DoorKey-5x5` | 7,3 % |
| `DoorKey-8x8` | 36,7 % |
| **`DoorKey-16x16`** | **48,7 %** |

Le témoin, lui, jouait un `reset()` natif — **0 %**. Les deux conditions ne jouaient donc
pas la même tâche.

**Conséquences pour qui voudrait réutiliser ces cerveaux :**

- ✅ Ils restent **valables comme objets d'étude** — santé synaptique, structure de la
  mémoire, empreinte de type. C'est ainsi que H17/H18 ont été trouvés.
- ❌ Ils ne sont **pas comparables** aux cerveaux produits après le correctif (v39) : la
  tâche est devenue ~50× plus dure sur `8x8` (réussite aléatoire 15,3 % → 0,3 %).
- ❌ Les **résultats de performance** qu'ils ont produits (2a, 2b) sont à refaire.

Le cas `campagne_2a/120820262305_V38-2a-continu_g22_600_RMD.brain` mérite une mention :
c'est le run à **69 victoires** (record du projet), dont 65 sur `DoorKey-16x16` — la carte
la plus biaisée. Estimation par le taux de base : ~32 de ces victoires pouvaient être des
cartes triviales. **Non mesuré**, seulement estimé.

---

## Convention de nommage

```
DDMMYYYYHHMM_VXX_NMRTOUR_RMD.brain
└──────┬───┘ └┬┘ └───┬──┘ └┬┘
       │      │      │     └── initiales / identifiant du run
       │      │      └──────── nombre de jours demandé au lancement
       │      └─────────────── version de l'architecture au lancement
       └────────────────────── date + heure de LANCEMENT (jamais mise à jour)
```

L'horodatage est celui du **départ** du run : le fichier est réécrit à chaque nuit, mais
son nom garde la trace de sa naissance, pas de son état courant.

Les fichiers suffixés ` 2.brain` / ` 3.brain` sont des copies Finder. **Vérifié le
14/08 : elles ne sont PAS identiques aux originaux** (checksums différents) — ce sont des
runs distincts, conservés à ce titre.

---

## Où va un nouveau cerveau

1. **Pendant le run** : à la racine de `brains/`, nommé selon la convention.
2. **Campagne terminée** : dans `brains/old_VXX/`, éventuellement par sous-campagne.
3. **Jamais supprimé.**

Vérifier après création d'un sous-dossier que le gitignore le couvre :

```bash
git check-ignore -v brains/old_VXX/mon_cerveau.brain
```
