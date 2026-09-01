# LA BOUSSOLE LATENTE — le bus reconnaît le but, il ne sait pas où il est

**Date** : 2026-09-01 · **Nature** : mesure exploratoire · **n = 1 cerveau** (`A_g66`),
30 épisodes, banc forcé, lecture seule · **Aucun code modifié.**

> Consigné au titre de la Règle de Trace §1 (« une mesure est produite »). Cette mesure
> **précède** toute implémentation : elle sert à décider s'il faut coder, pas à justifier
> ce qui aurait déjà été codé.

---

## 1. La question posée

Proposition de l'utilisateur (01/09/2026) : il manquerait à l'architecture un **ancrage
vectoriel persistant** — un vecteur de but latent `z*` maintenu dans C2, transformant
l'état cible en **puits de potentiel** :

> `D(z_t, z*) = ||z_t − z*||²` — « la décision motrice cesse d'être un choix aveugle parmi
> sept actions : elle devient la sélection de l'action qui minimise cette distance ».

**Avant de coder** (leçon de la brique C, tombée le jour même comme doublon d'un mécanisme
existant), trois questions de fait.

## 2. Les chiffres bruts

| Question | Mesure | Verdict |
|---|---|---|
| Le but est-il visible ? | **540 / 3 405 ticks = 15,9 %** | 🔴 l'agent est **aveugle au but 84,1 %** du temps |
| Le latent du but est-il distinguable ? | **d' = 8,89** (distance 1,1185 / σ 0,1259) | ✅ **éclatant** — bien au-delà du d' ≈ 3 des objets ordinaires |
| `z*` est-il constructible ? | but vu ≥ 1 fois dans **27/30 épisodes = 90 %** | ✅ oui |
| **La distance latente suit-elle la distance réelle ?** | **r = +0,1329**, σ inter-épisodes **0,3021** | 🔴 **NON** — le signe s'inverse d'un épisode à l'autre |

## 3. Ce que ça établit

**Les deux premières prémisses de la proposition sont CONFIRMÉES.** L'agent est bien
spatialement amnésique dès que le but sort du cône 7×7, et cela 84 % du temps. Et la
reconnaissance n'est pas en cause : quand le but est visible, le JEPA le sépare à
**d' = 8,89**, presque trois fois mieux que les objets ordinaires. **Un signal d'une clarté
extrême, disponible 16 % du temps, jeté au tick suivant.**

🔴 **Mais le troisième principe — le paysage de potentiel — ne peut pas fonctionner en
l'état.** `r = +0,133` avec un écart-type de 0,302 : descendre le gradient de `D(z_t, z*)`
ne rapproche du but ni de façon fiable, ni même de façon cohérente entre épisodes.

**La raison est structurelle** : le bus latent encode ce que l'agent **VOIT**, pas **OÙ il
est**. Deux couloirs qui se ressemblent produisent des latents voisins tout en étant
spatialement éloignés. Le JEPA est un excellent **classificateur de scène** ; ce n'est pas
une **carte**.

> **L'espace latent n'est pas MÉTRIQUE.** Poser une boussole dessus reviendrait à donner un
> cap dans un espace où « proche » ne signifie pas « proche ».

C'est précisément ce que le premier principe de la proposition (les *grid cells*) dit qu'il
faut construire : la biologie ne dérive pas la position de la reconnaissance visuelle, elle
l'**intègre** à partir de la vitesse et des virages.

## 4. Les vérifications

| Vérification | Résultat |
|---|---|
| Doublon avec un mécanisme existant ? | 🟡 `contexte_episodique` est une **moyenne** des latents de l'épisode (l. 8813) — donc un attracteur existe, mais c'est le **centre de gravité du vécu**, pas une cible. `z*` n'en serait pas un doublon |
| Tautologie ? | ✅ écartée — la distance BFS est lue sur la grille, jamais dérivée de la récompense |
| Le but est-il détecté correctement ? | ✅ index 8 de `OBJECT_TO_IDX`, API MiniGrid |

## 5. Limites

1. **n = 1 cerveau** (`A_g66`, le meilleur de la cohorte), 30 épisodes, **banc forcé**.
2. Politique **figée** (`eval()`) : décrit l'espace latent tel qu'il est, pas tel qu'il
   deviendrait sous un entraînement qui l'y contraindrait.
3. `z*` est pris au **premier** tick où le but est vu. Une autre définition (moyenne des
   vues, dernier tick avant disparition) pourrait donner un autre `r` — non testé.

## 6. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** : `z*` comme puits de potentiel **directement branché sur le bus latent actuel**.
Le prérequis manque.

**Ouvert** — trois voies, par coût croissant :

1. **Attendre la brique B** (v41.49, campagne en cours). Si l'ancrage cinématique mord, le
   réseau reçoit pour la première fois de quoi *intégrer un chemin* — la métrique latente
   pourrait émerger de là. Re-mesurable avec le même script en trois minutes. **Coût zéro.**
2. **Brancher le rappel spatial** (`DIM_RAPPEL_MARQUANT`, `rappel_le_plus_marquant`), qui
   porte déjà des **coordonnées**, donc une vraie métrique. ⚠️ Mais c'est un dispositif
   spatial explicite, plus proche du GPS que de l'émergence — **arbitrage dogme requis**.
3. **Un vrai réseau d'attracteurs continus** : une couche récurrente entraînée à prédire son
   propre état futur à partir de l'élan. C'est ainsi que les *grid cells* apparaissent dans
   la littérature. **Chantier d'architecture, pas un ajout.**
