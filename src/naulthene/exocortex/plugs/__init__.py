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
"""
