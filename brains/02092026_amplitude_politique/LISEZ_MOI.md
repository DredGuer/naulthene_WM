# 02/09/2026 — L'amplitude de la politique (réanalyse, aucun run)

Question : l'amplitude des logits joués est-elle bornée par construction (`gain_c1` asservi à
`2,1 × f`, C2 z-scoré), et cette borne est-elle liée au succès au banc ?

- **Sources** : `brains/26082026_v4132_AB3_cursus/*.log` (100 dernières nuits, 20 cerveaux) ×
  `brains/30082026_plancher_n20/agregat.json` (⚠️ banc amputé, v41.47) + rejeu partiel
  `brains/02092026_rejeu_banc_corrige/` (13/20).
- **Agrégat** : `agregat.json` (points, corrélations, rejeu partiel, budget d'apprentissage).
- **Document** : `docs/recherche/AMPLITUDE_02092026_la_politique_ne_peut_pas_etre_nette.md`.
- **Résultat** : aucune corrélation ne passe Bonferroni (2,88) ; signes tous dans le sens de
  l'hypothèse ; plage d'amplitude C1 [0,33 ; 0,91] sur 20 cerveaux — la boîte est le
  résultat. L'ablation « C2 coupé = 0,0 » est **confondue** (force = 0 ⇒ gain C1 = 0,25).
- **À faire** : le banc à 3 bras décrit au §6 du document. Rien n'est démontré ici.
