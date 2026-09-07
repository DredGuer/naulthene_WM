# Snapshots intermédiaires — archive du 07/09/2026

Ces `.brain` portaient un suffixe ` 2` / ` 3` / ` 4` dans leur dossier de campagne d'origine
(nom d'origine préfixé par `<campagne>__`).

⚠️ **Ce ne sont PAS des doublons.** Vérifié le 07/09 : **0 sur 226** est identique bit à bit
à son fichier de référence — ce sont des **états sauvegardés à des nuits différentes** du
même run (le `.brain` est réécrit à chaque nuit par `PersistanceAnatomique.sauvegarder()`).

**Ils sont archivés, jamais supprimés** — règle de gestion des données §7 : *« un `.brain`
représente des centaines de jours de run. Ranger dans `brains/old_VXX/`, ne jamais
effacer. »*

⚠️ **Ne pas les utiliser pour une comparaison appariée** : leur nuit de sauvegarde est
inconnue et diffère de celle du fichier de référence. Ils servent de filet de sécurité, pas
de données de campagne.

25 d'entre eux n'ont **plus de fichier de référence** dans leur campagne d'origine — ce sont
les seuls exemplaires survivants de ces états.
