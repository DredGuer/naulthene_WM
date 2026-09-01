# INERTIE MOTRICE — le trajet se tend-il si la décision a une masse ?

**Date de lancement** : 2026-09-01 · **Statut** : protocole écrit AVANT le premier run
(Règle de Trace, §4 « écrire avant de conclure »).

---

## La question posée, telle qu'elle a été formulée

> « À chaque tick, la tête motrice tire une action dans une distribution multinomiale
> indépendante. Tirer des virages à gauche et à droite de façon stochastique à haute
> fréquence produit une annulation géométrique immédiate : l'agent oscille sur place.
> Donner une **masse cinématique** à la décision : `L_t = λ·L_{t-1} + (1−λ)·logits_t`.
> Vérifier si λ = 0,7 fait chuter la directivité de 18× vers 3×–5× l'optimal. »

Formulée par l'utilisateur le 01/09/2026, après la mesure du 31/08 établissant que
`r(directivité, succès) = −0,8225` (`t = −5,96`, n=19, 68 % de la variance).

## Ce que la mesure du 31/08 contraint déjà

| Fait acquis | Valeur |
|---|---|
| Directivité médiane des cerveaux entraînés | **13,8× à 22,8×** le plus court chemin |
| Plus court chemin médian (BFS réel) | **12 pas** |
| Budget de la carte (`max_steps`) | **324 ticks** |
| Plafond arithmétique de la directivité | **27,0×** |
| Corrélation directivité ↔ succès au banc | **−0,8225** (`t = −5,96`, n=19) |
| Marcheur aléatoire | 5,67 % (17/300, stable sur 4 runs) |

⚠️ La corrélation est **corrélationnelle**. Ce banc est la première tentative
d'**intervention** : si tendre le trajet fait monter le succès, le lien devient causal
dans ce sens. S'il ne le fait pas, la directivité est un *symptôme* et non une cause.

## Le protocole exact

- **Cohorte** : les 20 cerveaux de `brains/26082026_v4132_AB3_cursus/` déjà passés au banc
  le 30-31/08 (mêmes fichiers, mêmes noms) — donc **appariement parfait** avec `agregat.json`
  de `brains/30082026_plancher_n20/`.
- **Environnement** : `MiniGrid-SimpleCrossingS9N1-v0`, 300 épisodes, **graines de carte
  appariées** (`--graine 90210`, identique au banc du 30/08).
- **Lecture seule** : aucun apprentissage, `eval()`, cerveaux lus depuis une COPIE.
- **Bras** : λ ∈ {0,0 ; 0,5 ; 0,7 ; 0,9}. **λ = 0,0 est le témoin** — il doit reproduire
  le banc du 30/08 au chiffre près, sinon l'instrument a dérivé.
- **Deux sorties par bras** : taux de succès (IC95 Wilson) et directivité médiane.

### Le test A/A, avant tout A/B

λ = 0,0 rejoué contre les valeurs déjà publiées le 30/08. Si `δ_A/A ≠ 0`, le banc ne
mesure rien et la campagne s'arrête là.

## Les vérifications prévues (avec leur résultat, même nul)

| Vérification | Pourquoi | Résultat |
|---|---|---|
| **A/A λ=0 vs banc 30/08** | l'instrument a-t-il dérivé ? | *à remplir* |
| **Tautologie** | la directivité n'est-elle qu'une mesure de victoire ? | *à remplir* |
| **Saturation du budget** | un trajet tendu ne peut-il pas juste refléter moins de ticks disponibles ? | *à remplir* |
| **Cerveaux à 0 victoire** | directivité indéfinie — combien de points perdus par bras ? | *à remplir* |
| **Inertie ≠ biais vers `forward`** | λ élevé fige-t-il simplement l'action la plus probable ? | *à remplir* |

⚠️ **La 5ᵉ vérification est la plus importante.** Un filtre AR sur les logits **n'est pas
neutre** : il favorise mécaniquement l'action déjà dominante. Si `forward` est le mode de
la politique, l'inertie produit « avancer tout droit » — ce qui *tendrait le trajet sans
rien apprendre*. Le témoin obligatoire est donc un **marcheur aléatoire sous inertie** :
s'il gagne autant que le cerveau entraîné sous inertie, l'effet n'est pas cognitif, c'est
une **rectification mécanique de la trajectoire**.

## Ce que ce banc NE peut PAS établir

1. Il ne teste **que l'axe 1** (inertie motrice). Les axes 2 (intention persistante de C2)
   et 3 (saturation de la curiosité) touchent la boucle d'apprentissage et ne sont pas
   mesurables en lecture seule.
2. Il mesure une politique **figée**. Un agent qui *apprendrait* sous inertie pourrait
   diverger — l'inertie change la distribution d'exploration, donc les données vues.
3. `SimpleCrossingS9N1` **n'a ni porte ni clé** : un gain ici ne prédit rien sur les
   niveaux 7+.
4. Un banc forcé **ne prouve rien sur le cursus** (règle de mesure §6).

## Fichiers

- `res_lam<λ>_<cerveau>.json` — un par cerveau et par λ
- `agregat.json` — régénéré après CHAQUE vague, jamais à la fin
- `run.log` — sortie console complète
