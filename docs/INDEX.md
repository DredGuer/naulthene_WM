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

## 🔴 À lire en premier — l'état réel au 02/09/2026

**Le tableau des suspects est vide, et le motif est devenu le résultat.** Vingt-et-une
explications du plafond au niveau 4 ont été mesurées et réfutées. Les deux dernières
(rendement mécanique v41.48, ancrage cinématique v41.49) ont été **livrées puis réfutées à
n=20** et disent la même chose : qu'on retire du signal ou qu'on ajoute de l'information, le
comportement ne bouge pas — *l'information est là, le réseau ne s'en sert pas*.
✅ **Réserve d'instrument LEVÉE le 02/09** (rejeu 20/20) : la directivité **survit,
affaiblie** — `r = −0,68`, **46 %** de la variance, et elle **ne survit plus** au retrait
des 4 extrêmes. La mémoire de travail est une **source de variance**, pas un levier.
🟡 **Piste en cours** : l'amplitude de la politique est bornée par construction
(`gain_c1` asservi) — bras A codé, non mesuré.

| Question | Document |
|---|---|
| Où en est le projet, sans enjolivure ? | [`../readme_fr.md`](../readme_fr.md) · [`../readme.md`](../readme.md) (EN) |
| Qu'est-ce qui a été réfuté en dernier, et pourquoi ça converge ? | [campagnes/ELAN_02092026](recherche/campagnes/ELAN_02092026_l_information_est_la_et_ne_sert_a_rien.md) · [campagnes/RENDEMENT_01092026](recherche/campagnes/RENDEMENT_01092026_le_gradient_assaini_ne_change_rien.md) |
| Quels chiffres publiés sont à reprendre ? | [campagnes/REJEU_02092026](recherche/campagnes/REJEU_02092026_la_directivite_survit_affaiblie.md) — les valeurs des 30-31/08 sont **remplacées** |
| Pourquoi la politique n'est-elle jamais nette ? | [AMPLITUDE_02092026](recherche/AMPLITUDE_02092026_la_politique_ne_peut_pas_etre_nette.md) — hypothèse, **non testée** |
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

### `recherche/enquetes_closes/` — **les pistes réfutées, série du 23/08 → 01/09/2026**

Quatorze carnets, une série. À lire **avant de rouvrir une piste** : c'est ce qui évite de
retester une idée déjà écartée. (Les réfutations à n ≥ 20 — RENDEMENT, ELAN — sont des
**campagnes** et sont rangées dans le tableau suivant.)

| Document | Ce qui a été réfuté |
|---|---|
| [REFUTATIONS_23082026](recherche/enquetes_closes/REFUTATIONS_23082026_trois_chantiers_avant_la_premiere_ligne.md) | trois chantiers, avant d'écrire une ligne |
| [CONDITIONNEMENT_27082026](recherche/enquetes_closes/CONDITIONNEMENT_27082026_le_signal_arrive_et_ne_sert_a_rien.md) | le signal perceptif **arrive** aux logits — pas un défaut de câblage |
| [CREDIT_27082026](recherche/enquetes_closes/CREDIT_27082026_l_arrosage_confirme_et_la_vue_orpheline.md) | l'arrosage du crédit ; l'acteur/critique envoient **0,000000** à la vue |
| [CLIC_27082026](recherche/enquetes_closes/CLIC_27082026_le_td_error_ne_sauve_rien.md) | TD(0) et GAE ne contrastent pas — **mesuré avant d'être codé** |
| [CREUX_30082026](recherche/enquetes_closes/CREUX_30082026_la_recompense_n_est_pas_creuse.md) | 🔴 la récompense **n'est pas creuse** (86 % dense) — et normaliser par épisode est **pire** (60/60) |
| [DIETE_30082026](recherche/enquetes_closes/DIETE_30082026_la_curiosite_est_une_rente_sans_effet.md) | 🔴 la curiosité est une **rente permanente** (40 % du signal) qui **ne prédit rien** — 15,0 % vs 15,0 % |
| [VALENCE_31082026](recherche/enquetes_closes/VALENCE_31082026_la_carte_est_vide_a_cet_endroit.md) | le renforcement secondaire **existe** (+0,84 sur les portes) mais **n'atteint pas la décision** — la carte est presque vide (6 confirmations contre 8 621) |
| [REBOND_04092026](recherche/enquetes_closes/REBOND_04092026_le_monde_n_est_pas_la_cause.md) | ❌ **22ᵉ réfutation, coût 0 run** — le rebond d'entropie n'est **pas** causé par le changement de carte : écart au témoin `t` = **+0,045**, les promotions expliquent **3 %** de l'amplitude, et le rebond est **massif au banc forcé où la carte ne change jamais** (+0,693). Il est **endogène** |
| [INERTIE_01092026](recherche/enquetes_closes/INERTIE_01092026_la_decision_est_deja_lisse.md) | ❌ l'inertie motrice réfutée **sur sa prémisse** — la décision est déjà autocorrélée à **0,69–0,85** |
| [INSTRUMENT_01092026](recherche/enquetes_closes/INSTRUMENT_01092026_la_memoire_du_banc.md) | 🔴 **correction d'instrument** — le banc jouait à **mémoire nulle** depuis le 30/08 (⚠️ réserve **levée** le 02/09, voir REJEU) |
| [COLLAPSE_28082026](recherche/enquetes_closes/COLLAPSE_28082026_le_plafond_est_geometrique.md) | ⚠️ **contient sa propre rétractation** : le cosinus saturait |
| [CIBLE_MOBILE_28082026](recherche/enquetes_closes/CIBLE_MOBILE_28082026_la_tete_poursuit_un_axe_qui_fuit.md) | la dérive de représentation ⚠️ chiffres ×46 **retirés** |
| [COURSE_29082026](recherche/enquetes_closes/COURSE_29082026_le_predateur_recule.md) | la course mesurée proprement : ×11,7, l'alignement **recule** |
| [CORRELATION_29082026](recherche/enquetes_closes/CORRELATION_29082026_la_derive_ne_predit_rien.md) | la dérive **ne prédit pas** la performance (n=20) |
| [DECISION_29082026](recherche/enquetes_closes/DECISION_29082026_confiant_dans_l_erreur.md) | l'agent n'est pas apathique — il se trompe avec aplomb |

### `recherche/campagnes/` — **les mesures à n ≥ 20**

| Document | Ce qu'il mesure |
|---|---|
| **[VOIX_LIBRE_04092026](recherche/campagnes/VOIX_LIBRE_04092026_200_jours_le_temoin_s_effondre.md)** | ✅ **À 200 JOURS L'EFFET SE CONFIRME** — δ **+19,50 pt** (`t` = +9,58, 19/20), tient sans les 4 extrêmes (`t` = +8,54). 🔴 **Mais la cause change de sens** : LIBRE stagne (+1,58 pt, NS) et **c'est le TÉMOIN qui s'effondre** (−5,48 pt, `t` = −3,05, 17/20). ⚠️ **Pas d'asymptote** : 20/20 cerveaux sur-durcissent puis se relâchent |
| **[VOIX_LIBRE_03092026](recherche/campagnes/VOIX_LIBRE_03092026_le_premier_levier_du_depot.md)** | ✅ **LE PREMIER LEVIER INTERNE DU DÉPÔT** — retirer la renormalisation de C1 (`gain_c1 ≡ 1`) **double le succès** : 24,17 % contre 11,73 %, δ **+12,43 pt** (`t = +5,21`, 18/20), et l'effet **survit au retrait des 4 extrêmes** (`t = +4,86`). ⚠️ banc forcé, politique **non asymptotique** (H descend encore à j100) ; l'ablation « C2 = 0,0 pt » est **confondue** et à refaire |
| [ELAN_02092026](recherche/campagnes/ELAN_02092026_l_information_est_la_et_ne_sert_a_rien.md) | ❌ **21ᵉ réfutation** — l'ancrage cinématique : l'information EST là (amplitude 0,09–0,16) et C1 ne s'en sert pas — ratio `t` = +0,04, myéline identique aux deux bras (n=20) |
| [RENDEMENT_01092026](recherche/campagnes/RENDEMENT_01092026_le_gradient_assaini_ne_change_rien.md) | ❌ **20ᵉ réfutation** — assainir **64,6 % du gradient** ne change RIEN — directivité 19,25× contre un seuil d'échec à 12× (n=20) |
| [COHORTE_30082026](recherche/campagnes/COHORTE_30082026_le_bareme_ne_predit_rien.md) | 🔴 **17ᵉ réfutation** — le barème ne prédit rien, la corrélation est une **tautologie** (n=40, 0 run) |
| [REJEU_02092026](recherche/campagnes/REJEU_02092026_la_directivite_survit_affaiblie.md) | 🟡 **la directivité SURVIT, AFFAIBLIE** (n=20, instrument corrigé) — `r = −0,68` (`t = −3,93`), **46 %** de la variance, mais **ne survit plus** au retrait des 4 extrêmes (`t = −2,04`, NS). La mémoire de travail est une **source de variance**, pas un levier (+0,63 pt en moyenne, ±17 pt par cerveau) |
| [DIRECTIVITE_31082026](recherche/campagnes/DIRECTIVITE_31082026_le_goulot_est_moteur.md) | ⚠️ **chiffres remplacés par REJEU_02092026** — mesurés sur le banc amputé (`r = −0,82`, 68 % de la variance). Garder pour le protocole et la rétractation de l'inversion `r = −0,89` |
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
| [AMPLITUDE_02092026](recherche/AMPLITUDE_02092026_la_politique_ne_peut_pas_etre_nette.md) | 🟡 **hypothèse mécanique, non testée** : `gain_c1` asservi à `2,1 × f` et C2 z-scoré bornent l'amplitude des logits joués — la politique **ne peut pas** devenir nette ; 1 pas d'optimiseur/nuit contre ≈ 23 700 pour PPO (**59×**) ; l'ablation « C2 coupé = 0,0 » est **confondue** (force = 0 ⇒ gain C1 = 0,25). Corrélations n=20 toutes NS, banc à 3 bras proposé |
| [BOUSSOLE_01092026](recherche/BOUSSOLE_01092026_le_latent_n_est_pas_metrique.md) | 🟡 mesure exploratoire (n=1) **avant de coder** : l'agent est **aveugle au but 84 %** du temps et le reconnaît à **d' = 8,89** — mais le latent **n'est pas métrique** (`r = +0,13`). Boussole non codée |
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
| 02/09/2026 | [**état du dépôt — 21 réfutations, et ce qui reste**](etat_des_lieux/02092026_etat_du_depot_et_reste_a_faire.md) — où en est le projet, ce qui est acquis, ce qui est ouvert, et les 5 chantiers classés par ce que la mesure justifie |
| 02/09/2026 | [branches archivées](etat_des_lieux/02092026_branches_archivees.md) — les 21 branches supprimées, leurs SHA pour les ressusciter |
| 30/08/2026 | [**le génome — audit des constantes**](etat_des_lieux/30082026_le_genome_audit_des_constantes.md) — ce qui fixe la forme ET les désirs d'un cerveau avant tout vécu ; **95,6 % du signal vient de constantes posées** |
| 22/08/2026 | [campagne v41.31, cursus complet](etat_des_lieux/22082026_campagne_v41.31_cursus_complet.md) |
| 21/08/2026 | [anatomie du noyau](etat_des_lieux/21082026_anatomie_du_noyau.md) |
| 19/08/2026 | [rapport de nuit](etat_des_lieux/19082026_rapport_de_nuit.md) |
| 18/08/2026 | [revue du dogme avant publication](etat_des_lieux/18082026_revue_dogme_avant_publication.md) |
| 16/08/2026 | [bilan de nuit](etat_des_lieux/16082026_bilan_nuit.md) |
| 15/08/2026 | [v41.4](etat_des_lieux/15082026_v41.4.md) |
