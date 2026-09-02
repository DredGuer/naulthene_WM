# Mesure du 01/09/2026 — La boussole latente (dossier VIDE, et pourquoi)

> ⚠️ **Ce dossier ne contient aucun fichier de résultat.** La mesure existe — elle est
> consignée dans [`docs/recherche/BOUSSOLE_01092026_le_latent_n_est_pas_metrique.md`](../../docs/recherche/BOUSSOLE_01092026_le_latent_n_est_pas_metrique.md)
> (commit `1f52c3d`) — mais son **agrégat machine n'a jamais été écrit ici**. C'est un
> manquement au §3 de la Règle de Trace, constaté le 02/09/2026 et laissé visible plutôt
> que masqué par la suppression du dossier.

## Ce qu'on cherchait

Proposition utilisateur : un vecteur de but latent `z*` maintenu dans C2 comme puits de
potentiel (`D(z_t, z*) = ‖z_t − z*‖²`). **Avant de coder**, trois questions de fait :
le but est-il visible ? son latent est-il distinguable ? la distance latente suit-elle la
distance réelle ?

## Protocole (tel que le document le rapporte)

| Élément | Valeur |
|---|---|
| Cerveau | **n = 1** — `A_g66` (`../26082026_v4132_AB3_cursus/`) |
| Épisodes | 30, banc forcé `SimpleCrossingS9N1`, lecture seule |
| Code modifié | aucun |

## Le résultat, en une ligne

Le but est visible **15,9 %** du temps (540 / 3 405 ticks) ; quand il l'est, le JEPA le
sépare à **d' = 8,89** ; mais `r(distance latente, distance réelle) = +0,13` avec σ
inter-épisodes 0,30 — **le latent n'est pas métrique**. Le bus encode ce que l'agent
*voit*, pas *où il est*. La boussole n'a pas été codée.

## Pour solder ce dossier

Si la mesure est rejouée, écrire ici `agregat.json` (par épisode : ticks, ticks but visible,
d', r) et le nom exact de la sonde utilisée — le document ne le mentionne pas.
