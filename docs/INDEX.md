# Index de la documentation — quelle question mène à quel document

> Réorganisé le 29/08/2026. **Tout document doit figurer ici**, sinon il sera oublié.
> `recherche/` était passé à 46 fichiers à plat : il est désormais découpé en trois niveaux.

## Les cinq dossiers, et ce qui fait autorité

| Dossier | Nature | Fait autorité sur l'état courant ? |
|---|---|---|
| [`fonctionnement/`](fonctionnement/) | **normatif** | ✅ **oui** |
| [`recherche/`](recherche/) | **enquêtes** — non normatif, conserve les hypothèses réfutées | ❌ non |
| [`ameliorations/`](ameliorations/) | **idées** proposées, non validées | ❌ non |
| [`ameliorations_appliquees/`](ameliorations_appliquees/) | **livré**, garde la trace des options écartées | 🟡 partiellement |
| [`etat_des_lieux/`](etat_des_lieux/) | **photos datées**, jamais mises à jour après coup | ❌ non (**périmable**) |

---

## 🔴 À lire en premier — l'état réel au 29/08/2026

**Le tableau des suspects est vide.** Seize explications du plafond au niveau 4 ont été
mesurées et réfutées, la dernière (`maîtrise ~ énergie`, `r = +0,710`) le 29/08 en passant
de n=10 à n=20 : **r = −0,0588**.

| Question | Document |
|---|---|
| Où en est le projet, sans enjolivure ? | [`../readme_fr.md`](../readme_fr.md) · [`../readme.md`](../readme.md) (EN) |
| Le barème posé explique-t-il le plafond ? | [campagnes/COHORTE_30082026](recherche/campagnes/COHORTE_30082026_le_bareme_ne_predit_rien.md) — **non, tautologie** |
| Que vaut l'agent face à un PPO ? | [campagnes/BASELINE_PPO_29082026](recherche/campagnes/BASELINE_PPO_29082026_le_mur_n_existe_pas.md) |
| Qu'est-ce qui a changé, version par version ? | [fonctionnement/CHANGELOG.md](fonctionnement/CHANGELOG.md) |
| Comment lancer quoi que ce soit ? | [fonctionnement/LANCEMENT.md](fonctionnement/LANCEMENT.md) |
| Quelles règles de mesure s'appliquent ? | [`../CLAUDE.md`](../CLAUDE.md) § *La Règle de Mesure* |

---

## `fonctionnement/` — normatif

| Document | Rôle |
|---|---|
| [CHANGELOG.md](fonctionnement/CHANGELOG.md) | **la référence factuelle**, version par version |
| [LANCEMENT.md](fonctionnement/LANCEMENT.md) | commandes, dépannage |
| [explications_readme.md](fonctionnement/explications_readme.md) | détail algorithmique, §15 sens |
| [Parcourt_readme.md](fonctionnement/Parcourt_readme.md) | parcours de lecture |

---

## `recherche/` — trois niveaux

### `recherche/enquetes_closes/` — **les pistes réfutées, série du 23-29/08/2026**

Neuf carnets, une série. À lire **avant de rouvrir une piste** : c'est ce qui évite de
retester une idée déjà écartée.

| Document | Ce qui a été réfuté |
|---|---|
| [REFUTATIONS_23082026](recherche/enquetes_closes/REFUTATIONS_23082026_trois_chantiers_avant_la_premiere_ligne.md) | trois chantiers, avant d'écrire une ligne |
| [CONDITIONNEMENT_27082026](recherche/enquetes_closes/CONDITIONNEMENT_27082026_le_signal_arrive_et_ne_sert_a_rien.md) | le signal perceptif **arrive** aux logits — pas un défaut de câblage |
| [CREDIT_27082026](recherche/enquetes_closes/CREDIT_27082026_l_arrosage_confirme_et_la_vue_orpheline.md) | l'arrosage du crédit ; l'acteur/critique envoient **0,000000** à la vue |
| [CLIC_27082026](recherche/enquetes_closes/CLIC_27082026_le_td_error_ne_sauve_rien.md) | TD(0) et GAE ne contrastent pas — **mesuré avant d'être codé** |
| [CREUX_30082026](recherche/enquetes_closes/CREUX_30082026_la_recompense_n_est_pas_creuse.md) | 🔴 la récompense **n'est pas creuse** (86 % dense) — et normaliser par épisode est **pire** (60/60) |
| [DIETE_30082026](recherche/enquetes_closes/DIETE_30082026_la_curiosite_est_une_rente_sans_effet.md) | 🔴 la curiosité est une **rente permanente** (40 % du signal) qui **ne prédit rien** — 15,0 % vs 15,0 % |
| [VALENCE_31082026](recherche/enquetes_closes/VALENCE_31082026_la_carte_est_vide_a_cet_endroit.md) | le renforcement secondaire **existe** (+0,84 sur les portes) mais **n'atteint pas la décision** — la carte est presque vide (6 confirmations contre 8 621) |
| [COLLAPSE_28082026](recherche/enquetes_closes/COLLAPSE_28082026_le_plafond_est_geometrique.md) | ⚠️ **contient sa propre rétractation** : le cosinus saturait |
| [CIBLE_MOBILE_28082026](recherche/enquetes_closes/CIBLE_MOBILE_28082026_la_tete_poursuit_un_axe_qui_fuit.md) | la dérive de représentation ⚠️ chiffres ×46 **retirés** |
| [COURSE_29082026](recherche/enquetes_closes/COURSE_29082026_le_predateur_recule.md) | la course mesurée proprement : ×11,7, l'alignement **recule** |
| [CORRELATION_29082026](recherche/enquetes_closes/CORRELATION_29082026_la_derive_ne_predit_rien.md) | la dérive **ne prédit pas** la performance (n=20) |
| [DECISION_29082026](recherche/enquetes_closes/DECISION_29082026_confiant_dans_l_erreur.md) | l'agent n'est pas apathique — il se trompe avec aplomb |

### `recherche/campagnes/` — **les mesures à n ≥ 20**

| Document | Ce qu'il mesure |
|---|---|
| [COHORTE_30082026](recherche/campagnes/COHORTE_30082026_le_bareme_ne_predit_rien.md) | 🔴 **17ᵉ réfutation** — le barème ne prédit rien, la corrélation est une **tautologie** (n=40, 0 run) |
| [DIRECTIVITE_31082026](recherche/campagnes/DIRECTIVITE_31082026_le_goulot_est_moteur.md) | 🔴 **le premier prédicteur significatif** — `r(directivité, succès) = −0,82` (`t = −5,96`, n=19), **68 % de la variance** |
| [PLANCHER_30082026](recherche/campagnes/PLANCHER_30082026_la_competence_existe_et_la_maitrise_ment.md) | ✅ la compétence **existe** (25,8 % vs 5,7 % aléatoire) mais les victoires sont **browniennes** (14–18× l'optimal) — n=4 |
| [BASELINE_PPO_29082026](recherche/campagnes/BASELINE_PPO_29082026_le_mur_n_existe_pas.md) | 🔴 **la ligne de base**, 60 runs — le mur informationnel n'existe pas |
| [CAMPAGNE_v41_population_et_ablation](recherche/campagnes/CAMPAGNE_v41_population_et_ablation_aout_2026.md) | population + ablation sensorielle, 78 cellules |
| [CAMPAGNE_n20_17082026](recherche/campagnes/CAMPAGNE_n20_17082026_brain_sparing_valide.md) | brain-sparing validé à n=20 |
| [CAMPAGNE_18082026](recherche/campagnes/CAMPAGNE_18082026_nociception_20_graines.md) | nociception, 20 graines |
| [CAMPAGNE_16082026](recherche/campagnes/CAMPAGNE_16082026_banc_reproductible.md) | le banc reproductible |
| [CAMPAGNE_17082026](recherche/campagnes/CAMPAGNE_17082026_brain_sparing.md) | brain-sparing, première mesure |
| [CAMPAGNE_P17_ABLATION](recherche/campagnes/CAMPAGNE_P17_ABLATION_aout_2026.md) | ablation P17 |

### `recherche/` — enquêtes antérieures

| Document | Sujet |
|---|---|
| [dia_Aout_2026.md](recherche/dia_Aout_2026.md) | **le diagnostic système** — plus utile que le README |
| [recherche_bug_or_not_bug.md](recherche/recherche_bug_or_not_bug.md) | **les 18 erreurs de diagnostic**, H1→H18 |
| [ETAT_DU_PROJET_aout_2026.md](recherche/ETAT_DU_PROJET_aout_2026.md) | état du projet |
| [REVUE_CODE_v39_aout_2026.md](recherche/REVUE_CODE_v39_aout_2026.md) | les 6 défauts trouvés dans le code |
| [REVUE_DOGME_17082026_rien_en_dur.md](recherche/REVUE_DOGME_17082026_rien_en_dur.md) | audit « rien en dur » |
| [METABOLISME_20082026_la_variable_morte.md](recherche/METABOLISME_20082026_la_variable_morte.md) | `taux_satiete` est une variable morte |
| [NAVIGATION_20082026_le_vrai_blocage.md](recherche/NAVIGATION_20082026_le_vrai_blocage.md) | la navigation sur `Empty-5x5` |
| [POURQUOI_20082026_l_agent_economise.md](recherche/POURQUOI_20082026_l_agent_economise.md) | pourquoi l'agent économise ses gestes |
| [DOULEUR_UNIQUE_19082026_refonte.md](recherche/DOULEUR_UNIQUE_19082026_refonte.md) | la refonte de la douleur |
| [DIAGNOSTIC_17082026](recherche/DIAGNOSTIC_17082026_pourquoi_C2_est_etouffe.md) · [SONDE_17082026](recherche/SONDE_17082026_utilite_de_C2.md) | pourquoi C2 est étouffé, et son utilité |
| [AUTOPSIE_17082026](recherche/AUTOPSIE_17082026_esprit_g7_le_seul_niveau_5.md) · [DISSECTION_g22](recherche/DISSECTION_g22_aout_2026.md) | autopsies de cerveaux |
| [EXPANSION_17082026](recherche/EXPANSION_17082026_le_frein_de_la_neurogenese.md) · [MUR_17082026](recherche/MUR_17082026_le_verrou_P17.md) | neurogenèse, verrou P17 |
| [FACTORIEL_17082026](recherche/FACTORIEL_17082026_esprit_contre_corps.md) · [CONSTAT_16082026](recherche/CONSTAT_16082026_pauvrete_du_monde.md) | esprit contre corps, pauvreté du monde |
| [CORRECTIF_v4110](recherche/CORRECTIF_v4110_memoire_par_carte.md) · [CORRECTIF_v4113](recherche/CORRECTIF_v4113_corps_dans_le_rollout.md) | correctifs documentés |
| [1440_JOURS_NAULTHENE_V1.md](recherche/1440_JOURS_NAULTHENE_V1.md) · [2026-07-28_progression_vue_et_ouie.md](recherche/2026-07-28_progression_vue_et_ouie.md) | archives anciennes |
| [NOCICEPTION_18082026](recherche/NOCICEPTION_18082026_la_chaleur_qui_fait_mal.md) · [THERMOHOMEOSTASIE_18082026](recherche/THERMOHOMEOSTASIE_18082026_la_douleur_graduee.md) · [DIAGNOSTIC_18082026](recherche/DIAGNOSTIC_18082026_pourquoi_la_douleur_coute.md) | la douleur : nociception, gradation, coût |
| [TRADUCTEUR_17082026](recherche/TRADUCTEUR_17082026_ce_que_C2_dit_a_C1.md) · [SCAN_CERVEAUX_16082026.md](recherche/SCAN_CERVEAUX_16082026.md) | ce que C2 dit à C1 · scan de population |
| [NUIT_18082026](recherche/NUIT_18082026_le_niveau_5_franchi_et_le_frein_qui_ne_borne_pas.md) · [NUIT_15082026](recherche/NUIT_15082026_trois_questions.md) | carnets de nuit |
| [evals/](recherche/evals/) | sorties JSON |

---

## `ameliorations/` — idées non validées

| Document | Sujet |
|---|---|
| [AVIS_ET_PROPOSITIONS_aout_2026.md](ameliorations/AVIS_ET_PROPOSITIONS_aout_2026.md) | P1 → P16 |
| [PLAN_v41.32_table_de_mixage_et_neurogenese_dirigee.md](ameliorations/PLAN_v41.32_table_de_mixage_et_neurogenese_dirigee.md) | table de mixage, neurogenèse dirigée |
| [EPISODES_REFERENCE_20082026_la_derniere_constante_posee.md](ameliorations/EPISODES_REFERENCE_20082026_la_derniere_constante_posee.md) | la dernière constante posée |
| [les_sens_combinatoire.md](ameliorations/les_sens_combinatoire.md) | les dix paires sensorielles |
| [CONCEPTION_v33](ameliorations/CONCEPTION_v33_memoire_emotionnelle.md) · [CONCEPTION_v34](ameliorations/CONCEPTION_v34_fatigue_mortalite.md) | mémoire émotionnelle, fatigue/mortalité |
| [CHANTIER_v41.2 énergie](ameliorations/CHANTIER_v41.2_energie_modulatrice.md) · [métabolisme](ameliorations/CHANTIER_v41.2_metabolisme_deux_etages.md) | métabolisme à deux étages |
| [CHANTIER_v41.31](ameliorations/CHANTIER_v41.31_gradient_causal_et_tube_digestif.md) · [v41.4](ameliorations/CHANTIER_v41.4_maitrise_generale_et_heritage.md) · [v41.6](ameliorations/CHANTIER_v41.6_P17_cursus_distribution.md) | chantiers v41 |
| [CORRECTIFS_v41_ligne_de_flottaison.md](ameliorations/CORRECTIFS_v41_ligne_de_flottaison.md) · [CONFRONTATION_16082026](ameliorations/CONFRONTATION_16082026_jepa_multimodal.md) · [AMELIORATION_V1.md](ameliorations/AMELIORATION_V1.md) | divers |

---

## `ameliorations_appliquees/` — livré, avec les options écartées

| Document | Mécanique |
|---|---|
| [CHANTIER_v37_equilibre_c1_c2.md](ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md) | équilibre C1/C2 — ⚠️ contient le §5.6 à lire avant de toucher à l'échelle de C2 |
| [CHANTIER_v38_monde_continu.md](ameliorations_appliquees/CHANTIER_v38_monde_continu.md) | monde continu |
| [CHANTIER_v41.43](ameliorations_appliquees/CHANTIER_v41.43_hygiene_du_genome.md) | hygiène du génome : `MALUS_DOULEUR` supprimé, échelle de stagnation **dérivée du monde** |
| [CHANTIER_v41.44](ameliorations_appliquees/CHANTIER_v41.44_p6_p8_audit_solde.md) | P6/P8 — cristallisation **relative** (morte depuis v26.0), noms du monde sortis du cœur |
| [CHANTIER_v40_planification_emergente.md](ameliorations_appliquees/CHANTIER_v40_planification_emergente.md) | planification émergente |
| [CONCEPTION_v22_audio.md](ameliorations_appliquees/CONCEPTION_v22_audio.md) · [CONCEPTION_v30_exo_sens.md](ameliorations_appliquees/CONCEPTION_v30_exo_sens.md) | audio, Exo-Sens |
| [EXPLICATIONS_v29_sens.md](ameliorations_appliquees/EXPLICATIONS_v29_sens.md) · [Maj_V29_readme.md](ameliorations_appliquees/Maj_V29_readme.md) | les 5 sens |

---

## `etat_des_lieux/` — photos datées, jamais réécrites

| Date | Document |
|---|---|
| 30/08/2026 | [**le génome — audit des constantes**](etat_des_lieux/30082026_le_genome_audit_des_constantes.md) — ce qui fixe la forme ET les désirs d'un cerveau avant tout vécu ; **95,6 % du signal vient de constantes posées** |
| 22/08/2026 | [campagne v41.31, cursus complet](etat_des_lieux/22082026_campagne_v41.31_cursus_complet.md) |
| 21/08/2026 | [anatomie du noyau](etat_des_lieux/21082026_anatomie_du_noyau.md) |
| 19/08/2026 | [rapport de nuit](etat_des_lieux/19082026_rapport_de_nuit.md) |
| 18/08/2026 | [revue du dogme avant publication](etat_des_lieux/18082026_revue_dogme_avant_publication.md) |
| 16/08/2026 | [bilan de nuit](etat_des_lieux/16082026_bilan_nuit.md) |
| 15/08/2026 | [v41.4](etat_des_lieux/15082026_v41.4.md) |
