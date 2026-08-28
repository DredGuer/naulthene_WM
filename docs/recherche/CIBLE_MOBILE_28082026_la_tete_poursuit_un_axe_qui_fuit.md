# 28/08/2026 — La tête motrice poursuit une cible qui fuit 14× à 46× plus vite qu'elle

> Non normatif — carnet d'enquête. Conclusion de la série ouverte le 23/08.
> À lire après l'addendum de `COLLAPSE_28082026_*.md`, qui rétracte le diagnostic précédent.

## La chaîne complète, mesurée bout en bout

| Maillon | État | Mesure |
|---|---|---|
| L'œil voit | ✅ | d' = 0,824 sur « but visible » dans l'observation brute |
| Le tronc **amplifie** | ✅ | d' → **2,891 / 3,613 / 3,017** dans `pensee_bio` (×3,5 à ×4,4) |
| Le gradient arrive | ✅ | 0,234 / 0,056 sur `tete_motrice`, non nul |
| Le clipping épargne | ✅ | g22 : **0 nuit clippée sur 5** (norme 0,26 / plafond 1,0) |
| Adam fait son pas | ✅ | 0,93 % de \|W\| par 5 nuits, contre 0,034 théorique (`lr·√n`) |
| La nuit n'érode pas | ✅ | norme à **90–98 %** de la naissance (plancher vital : 10 %) |
| Les pas sont **dirigés** | ✅ | \|cos(ΔW, axe)\| = 0,0925 / **0,2617** contre 0,029 au hasard |
| Les pas **s'additionnent** | ✅ | alignement temporel **0,780 / 0,969** (marche aléatoire : 0,316) |
| **La cible bouge** | 🔴 | **l'axe tourne de 4,81° / 3,35° par nuit** |

**Tout fonctionne, sauf que la cible se dérobe.**

## Le calibrage qui donne l'échelle

Un chiffre de rotation ne veut rien dire sans la vitesse du poursuivant :

| Cerveau | l'axe tourne (la proie) | `W` se rapproche (le prédateur) | rapport |
|---|---|---|---|
| A_g11 | ~~4,81 °/nuit~~ | ~~0,106 °/nuit~~ | ~~×46~~ |
| A_g22 | ~~3,35 °/nuit~~ | ~~0,245 °/nuit~~ | ~~×14~~ |

🔴 **CES CHIFFRES SONT RETIRÉS — voir `COURSE_29082026_*.md`.** Deux biais : la proie était
mesurée **sans graine fixée** (bruit d'échantillonnage compté comme rotation) et la vitesse
du prédateur était **dérivée d'une formule**, jamais mesurée. Sur un protocole unifié et
sur 200 nuits, le rapport réel est **×11,7**, et l'alignement **recule** au lieu de stagner.

## Pourquoi la cible bouge

L'axe informatif est défini dans `pensee_bio`, qui dépend d'`integrateur_bio` et de tout le
tronc — **entraînés simultanément avec la tête**. Chaque nuit, l'espace de représentation
lui-même pivote. `tete_motrice` s'aligne sur un repère qui n'existe déjà plus.

C'est la **dérive de représentation** (*representation drift*), un phénomène connu des
architectures à tronc partagé et jamais mesuré ici.

## Trois hypothèses réfutées en route (dont deux miennes)

| Hypothèse | Verdict |
|---|---|
| « Le clipping global écrase la tête motrice » | ❌ g22 n'est **jamais** clippé et ne progresse pas mieux |
| « Le ratio \|∇W\|/\|W\| est trop faible » | ❌ **Adam normalise le pas** : ce ratio ne détermine pas le déplacement |
| « La couche est en stase depuis sa naissance » *(la mienne)* | ❌ alignement temporel **0,97** — elle avance presque en ligne droite |

## Ce que cela n'établit PAS

1. **Que c'est LA cause du plafond au niveau 4.** L'axe mesuré est « but visible / absent ».
   Le lien avec la promotion reste **non mesuré** — c'est la même réserve que pour le
   diagnostic du matin, et elle n'a pas été levée.
2. **Que 4°/nuit est anormal.** Aucune référence externe. Un PPO à tronc partagé sur la même
   tâche donnerait le point de comparaison ; **non fait**.
3. **Qu'une correction marcherait.** Aucune n'a été testée.

Le fait solide est le **rapport de vitesse ×14 à ×46**, mesuré sur deux cerveaux.

## Pistes de correction — aucune testée, et toutes coûteuses

| Piste | Ce qu'elle ferait | Objection à lever d'abord |
|---|---|---|
| **Geler le tronc périodiquement** | immobilise la cible le temps que `W` rattrape | fige aussi le JEPA, seul à sculpter la perception (v41.34) ; et « périodiquement » serait une **constante posée** — le dogme exige qu'elle dérive du vécu |
| **Réseau cible (target network)** | lisse la cible par EMA | ajoute une copie du tronc (+50 % de mémoire) et une constante de lissage τ, encore posée |
| **Découpler les taux d'apprentissage** | tronc plus lent que la tête | l'optimiseur est **unique** pour tout le réseau (`Adam(params, lr)`) ; deux groupes = un vrai changement d'architecture, et le rapport des lr serait posé |

⚠️ **Les trois introduisent au moins une constante arbitraire.** C'est exactement ce que la
règle « rien en dur » interdit, et ce que la méthode du projet impose de **mesurer avant**
de rendre adaptatif (v30.1). Aucune ne doit être écrite sans avoir d'abord instrumenté la
grandeur dont elle dériverait.

**La mesure préalable qui manque** : la vitesse de rotation de l'axe est-elle stable, ou
décroît-elle avec la maturité ? Si elle décroît naturellement, le problème se résout seul
avec le temps et aucune correction n'est justifiée. **Non mesuré** — c'est le prochain pas,
et il ne coûte qu'un run long instrumenté, pas une campagne appariée.

## Instruments (lecture seule sauf mention, versionnés)

```bash
PYTHONPATH=src python -m naulthene.instruments.sonde_etat_synapses <brain> [env]
PYTHONPATH=src python -m naulthene.instruments.sonde_gradient_recu <brain>        # entraîne une copie
PYTHONPATH=src python -m naulthene.instruments.sonde_derive_representation <brain> # entraîne une copie
```

⚠️ Les deux dernières **font tourner des nuits réelles** sur le cerveau chargé : elles ne
sauvegardent jamais, mais travailler sur une **copie** reste la règle (§8).
