"""
Plugs C3 (v28.0, expérimental) — greffons interchangeables pour le Port Multiplexeur.

Chaque plug hérite de `naulthene.exocortex.port_c3.PlugC3` et n'est connu du noyau que
via ce contrat. Aucun plug n'est enregistré par défaut sur un `AGI_Naulthene` neuf —
c'est l'appelant (un cursus, un script de test) qui choisit d'en brancher un.

- `plug_nul` : toujours indisponible. C'est le mode nominal, celui de tous les runs
  existants avant v28.0 — aucun comportement, juste un contrat qui répond "absent".
- `plug_simule` : préférences déterministes + un flag `panne` activable en vol, pour
  les crash-tests (Chantier "Test de Déconnexion en Vol").
- `plug_http` : backend générique JSON/HTTP, URL configurable, aucune logique propre à
  un fournisseur — le socle sur lequel de futurs Plug_Ollama / Plug_VectorDB / Plug_Web
  / Plug_BrainToBrain pourront se brancher sans toucher au noyau.
- `plug_memoire_augmentee` (v30.0) : le premier plug **perceptif** — il rend un vecteur
  `ReponseC3.perception` (8 dims) au lieu d'un avis sur les actions. 100 % local et
  déterministe (résumé de la mémoire épisodique spatiale de l'agent), pour valider que
  C1/C2 digèrent un signal exogène avant d'introduire la latence d'un vrai service.

Deux familles de plugs coexistent depuis la v30.0, et le port transporte les deux sans
juger : les plugs **décisionnels** (v28.0, champ `preferences`) et les plugs
**perceptifs** (v30.0, champ `perception`, alimentant l'Exo-Sens). Un même plug peut
remplir les deux champs.
"""
