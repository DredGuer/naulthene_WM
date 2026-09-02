# A/A du bras A (v41.50) — 02/09/2026, graine 11, 2 jours, `SimpleCrossingS9N1`

| Run | Ce que c'est | Résultat |
|---|---|---|
| `AVANT_g11` | code **d'avant** le drapeau (`git stash`) | référence |
| `TEMOIN_g11` | nouveau code, drapeau **off** | **bit-identique** à AVANT (diff : noms de fichiers seulement) |
| `LIBRE_g11` | nouveau code, `--gain-c1-libre` | diffère : `gain C1 ×1.00`, H jouée 1,860 → 1,747 (témoin 1,939 → 1,861) |
| `LIBRE_g11_reprise` | copie de LIBRE rejouée 1 jour **sans** drapeau | le trait sérialisé est relu (`🔬 [BRAS A] … trait sérialisé`), nuit complète passée |

Contrôles passés : drapeau dans le module (assertion) · trait sur l'individu (assertion) ·
`.brain` porte `gain_c1_libre` (True/False lu par `torch.load`) · le banc le relit et l'annonce ·
`entropie_jouee` écrite dans le JSON du banc. ⚠️ 2 jours d'un nouveau-né : **aucune** lecture
de performance. Sur un agent neuf, le témoin a `gain ×0,25-0,45` — le gain *étouffe* C1.
