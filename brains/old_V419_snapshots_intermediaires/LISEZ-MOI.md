# Snapshots intermédiaires — NE PAS SUPPRIMER

Ce dossier s'appelait `doublons_icloud/`. **Le nom était faux.**

Vérifié le 17/08/2026 sur les 57 fichiers : **aucun n'est un doublon**. Chacun porte un
`tick_absolu` et un `dim_bus` qui n'existent nulle part ailleurs dans `brains/`.

Le suffixe ` 2`, ` 3`, ` 5` n'est pas une copie de synchronisation macOS mais un **état
intermédiaire** du même run, sauvegardé à un âge différent. Exemple mesuré :

```
150820262155_V416_1000_g55_RMD 2.brain   dim=32  ticks=  2 400  niveau 0
150820262155_V416_1000_g55_RMD 3.brain   dim=48  ticks=  5 600  niveau 0
150820262155_V416_1000_g55_RMD.brain     dim=48  ticks=400 000  niveau 2
```

Ce sont donc trois âges d'un même cerveau, pas trois copies d'un même fichier — et les
états jeunes sont précisément ce qui manque pour étudier une trajectoire de croissance.

> **Règle du projet** : toujours archiver, jamais supprimer. Un `.brain` représente des
> centaines de jours de run.
