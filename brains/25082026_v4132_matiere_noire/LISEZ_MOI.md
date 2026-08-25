# Campagne 25/08/2026 — La « matière noire » du gradient

## Ce qu'on cherchait

Les couches suivies ne semblaient couvrir que ~51 % de la norme du gradient. Qui mange le
reste — C2 ? l'hémisphère audio ?

## 🔴 Elle n'existait pas — bug de lecture (le mien)

Les **parts** étaient lues **après** `_clip_reel`, donc après division. Signature :
`racine(Σ carrés) = 1,000000 EXACTEMENT` sur 6/6 jours — la norme post-clip par construction.

Vérification structurelle : le réseau ne contient que **12 paramètres entraînables** (un
`annexe_weight` par couche). Aucun endroit où du gradient pourrait se cacher.

Troisième défaut de cette famille dans la campagne : lire une grandeur **après** l'opération
qui la modifie.

## Résultat corrigé (6 jours, graine 11)

`Σ(carrés)/n² = 100,0 %` sur 6/6 — comptabilité exacte.

| | moyenne | min | max |
|---|---|---|---|
| **corps** (`integrateur_bio`) | **92,7 %** | 90,4 % | 96,5 % |
| décision (`tete_motrice`) | 16,0 % | 9,3 % | 22,7 % |
| **vue** (`porte_visuelle`) | **0,77 %** | 0,2 % | 1,7 % |

**Rapport corps / vue : 121×.**

## Les trois faits

1. **Le corps dicte 93 % du gradient.** La vue en reçoit 0,77 % — elle ne peut pas apprendre
   à distinguer une pomme d'un mur avec ça.
2. **L'audio ne dissipe RIEN** : `porte_auditive`, `generateur_attente_audio`, `tete_vocale`,
   `tete_requete` à **0,000000 exact**, 6/6 jours. Ils coûtent des paramètres (24 %) et du
   calcul, jamais du gradient.
3. **C2 reçoit 2,02× le gradient de la décision** (0,3241 vs 0,1601) pour **0,0 pt** d'effet
   mesuré sur 6 niveaux (v41.29). Suspect non testé.

## Fichiers

- `base.brain` — cerveau de départ
- `matiere_noire.log` — run initial (parts fausses, conservé comme trace du bug)
- `matiere_noire_fix2.log` — run corrigé
