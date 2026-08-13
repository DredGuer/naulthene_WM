"""
L'Exocortex C3 (v28.0, expérimental) — Port Multiplexeur pour greffons externes.

Naulthène est un Cœur Organique fermé [C1 (réflexe/instinct) + C2 (raison/JEPA)],
100% autonome, ~0 dépendance externe. Ce sous-package ajoute un TROISIÈME canal,
optionnel et non-intrusif : C3, l'Exocortex.

Principe fondamental (non négociable) : si l'on coupe le courant de C3, Naulthène ne
plante pas, ne renvoie pas d'erreur et ne s'arrête pas — il bascule instantanément sur
sa curiosité intrinsèque déjà existante (voir `noyau.DetecteurCuriositeJEPA` et
`noyau.ModuleSursautVolonte`). Ce sous-package ne connaît donc jamais le cerveau lui-même
(pas d'import de `naulthene.cerveau.noyau`) — il ne définit qu'un contrat de vecteurs.

- `port_c3` : le bus multiplexeur (`PortC3`) et le contrat (`RequeteC3`, `ReponseC3`,
  `PlugC3`) — le noyau n'échange jamais qu'avec ce contrat, jamais avec un plug
  directement.
- `plugs/` : greffons interchangeables qui s'enregistrent sur le bus (`PlugNul` par
  défaut = toujours absent, `PlugSimule` pour les crash-tests, `PlugHTTP` = backend
  générique JSON/HTTP pour brancher n'importe quel service tiers).

Voir docs/fonctionnement/CHANGELOG.md (entrée v28.0-experimental) et docs/fonctionnement/explications_readme.md §14
pour le détail de la cascade de décision C1 → C2 → C3.
"""
