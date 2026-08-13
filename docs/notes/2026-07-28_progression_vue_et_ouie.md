# Note — L'agent progresse-t-il à la fois sur la vue ET l'ouïe ?

**Date** : 2026-07-28
**Contexte** : question de l'utilisateur après la v27.6 (gradient vocal étendu aux 8 paramètres).

## Réponse : oui, mais via deux mécanismes distincts, pas couplés en proportion

Chaque nuit (`AGI_Naulthene.apprendre_journee`, `src/naulthene/cerveau/noyau.py:447`), une
**seule perte totale** est construite en sommant trois composantes indépendantes, puis un
**seul `backward()`** et un **seul pas d'optimiseur Adam** ajustent tous les poids du réseau
en même temps :

```python
perte_totale = perte_jepa_moyenne          # comprendre le monde — vue ET ouïe, têtes séparées
             + COEFF_PERTE_VOCALE * perte_vocale_moyenne   # la BOUCHE (tete_vocale, 8 paramètres depuis v27.6)
             + perte_acteur + perte_critique + perte_entropie  # le DÉPLACEMENT dans MiniGrid (vue)
```

Donc à chaque nuit, un seul appel met à jour :
- `porte_visuelle`, `tete_motrice`, `cortex_prefrontal` (voir, décider, se déplacer),
- `porte_auditive`, `tete_vocale` (entendre, parler),
- `generateur_attente` / `generateur_attente_audio` (JEPA, le modèle du monde des deux sens).

## Mais ce ne sont pas deux jauges qui avancent au même rythme

Chaque composante a sa **propre source de signal**, indépendante des deux autres :

| Modalité | Ce qui pilote le gradient | Rythme dépend de |
|---|---|---|
| Vue (déplacement) | Récompense MiniGrid + planification Système 2 | Difficulté du niveau, franchissement de portes/paliers |
| Ouïe (parole) | Perte MSE sur les 8 paramètres vocaux (v27.6) vs la cible extraite de la banque vocale | Richesse de la banque enregistrée, guidage du curriculum |
| JEPA (modèle du monde) | Erreur de prédiction, deux têtes séparées vision/audio (`coeff_jepa_audio` monte progressivement) | Quantité de ticks vécus dans chaque modalité |

Rien ne force les deux progressions à avancer ensemble. C'est visible concrètement sur le
cerveau `naulthene_parole.brain` observé le 2026-07-27 : palier vocal **19/19** (maximum)
atteint, alors que l'agent restait bloqué au **Collège** sur MiniGrid (palier DoorKey 7,
jamais promu au Lycée). La voix a progressé beaucoup plus vite que le déplacement.

## Correctif apporté en v27.5 : éviter qu'un canal étouffe l'autre

Avant v27.5, un score vocal élevé continuait à shooter la dopamine au même niveau qu'un
agent débutant, même après la maîtrise complète du curriculum vocal — ce qui maintenait
artificiellement `teneur_dopamine`/`plasticite_base` hauts sans pousser l'agent à progresser
sur MiniGrid. `facteur_nouveaute_vocale` (voir `docs/CHANGELOG.md [27.5-experimental]`) fait
décroître la contribution dopaminergique du canal vocal avec la maîtrise déjà acquise (100%
à un mot neuf → 10% à un mot maîtrisé), pour laisser une vraie place motivationnelle au reste
du cursus.

## En résumé

- **Un seul cerveau, une seule passe d'apprentissage par nuit** — vue et ouïe ne sont jamais
  entraînées séparément ni en alternance forcée.
- **Mais deux progressions indépendantes**, chacune pilotée par son propre signal de
  récompense/erreur — rien ne garantit qu'elles avancent à la même vitesse, et c'est
  effectivement ce qu'on observe en pratique (le vocal a été plus rapide que le moteur sur
  ce cerveau).
- Le v27.5 atténue un des effets pervers de ce déséquilibre (dopamine vocale qui étouffe la
  motivation à progresser ailleurs), mais ne force pas les deux jauges à progresser au même
  rythme — ce n'est pas l'objectif recherché non plus : chaque modalité doit rester libre de
  progresser à son propre rythme, cohérent avec les principes développementaux du projet
  (voir CLAUDE.md, réservoir dopaminergique et rêve adaptatif).
