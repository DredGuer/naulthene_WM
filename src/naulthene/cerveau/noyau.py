# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
#Version actuelle 29. — Variante LOCALE de test (Mac, non versionnée dans le script Colab de référence)
# Différences avec agi_google_colab.py : détection du device MPS (Apple Silicon) et
# jours_totaux (500) réglé pour des runs locaux plus courts que les 400 jours de Colab.

import torch
import torch.nn as nn
import torch.nn.functional as F
import gymnasium as gym
import minigrid
import wandb
import numpy as np
import math  # v41.2 — exp() pour la dérive métabolique et le seuil non linéaire
import os    # v41.15 — NAULTHENE_DEVICE/THREADS, lus AVANT le choix du device ci-dessous

# v27.0 — hemisphere_audio est pur numpy (aucune dépendance PyTorch/réseau), donc
# importable au chargement du module sans risque de cycle. Remonté ici plutôt que
# réimporté paresseusement à chaque tick vocal (4 sites avant v27.0) — Python cache de
# toute façon le module, mais ce remontage supprime le lookup répété dans sys.modules.
from naulthene.audio.hemisphere_audio import (
    SynthetiseurFormants, recompense_formants, recompense_vocale_mixte,
    BORNES_F0, BORNES_F1, BORNES_F2, BORNES_F3, BORNES_BW, BORNES_DUREE, BORNES_AMPLITUDE,
)

# v28.0 (expérimental) — Le Port Exocortex C3 (Cœur Organique [C1+C2] + greffon
# optionnel C3). Ce module ne connaît QUE des vecteurs numpy et un contrat neutre
# (RequeteC3/ReponseC3/PlugC3) — il ne dépend d'aucun réseau, aucun cerveau, aucun
# service tiers ; c'est ce qui garantit que noyau.py reste 100% importable et
# fonctionnel même si aucun plug n'est jamais enregistré (voir Chantier 3, la trappe
# de secours biologique).
from naulthene.exocortex.port_c3 import PortC3, RequeteC3

# v29.0 (expérimental) — Le Bus Sensoriel Multimodal (l'Interpréteur des 5 Sens). Comme
# port_c3 ci-dessus, ce module est pur numpy et n'importe JAMAIS noyau.py : il ne fait que
# traduire l'environnement en signaux normalisés (toucher, odorat, goût), sans jamais
# connaître le réseau qui les consomme. La vue et l'ouïe, elles, gardent leur porte
# synaptique dédiée dans AGI_Naulthene — voir bus_sensoriel.BusSensoriel.hierarchie_sensorielle.
from naulthene.cerveau.bus_sensoriel import (BusSensoriel, DIM_TOUCHER, DIM_CHIMIE,
                                             DIM_EXO, DIM_ODORAT_DELTA,
                                             DIM_THERMOCEPTION, DIM_PRESSION,
                                             COULEUR_NOURRITURE, COULEUR_EAU,
                                             TYPE_RESSOURCE,   # v41.44 — P8
                                             # v41.27 — signatures nociceptives : le
                                             # « type » de douleur est un couple de
                                             # nombres, jamais un nom (le cœur ignore ce
                                             # qui l'a blessé).
                                             DEMI_VIE_BRULURE, DEMI_VIE_CHOC)

# --- v41.15 : LE BON DEVICE POUR CE RÉSEAU-CI (mesuré le 17/08) ---
#
# 🔴 CE QUE ÇA CORRIGE. Le device était choisi par simple disponibilité — cuda, sinon mps,
# sinon cpu. C'est le bon réflexe pour un gros modèle ; c'est le mauvais ici. Mesuré sur
# `penser()` complet, dim_bus=64, batch=1 :
#
#     mps          : 8,039 ms/tick
#     cpu (6 thr)  : 3,226 ms/tick
#     cpu (1 thr)  : 2,822 ms/tick     ← 2,85× PLUS RAPIDE que le GPU
#
# La raison est structurelle : ce cerveau fait des dizaines de très petits produits
# matriciels (64×64) en séquence, un par branche du rollout. Le coût de lancement d'un
# noyau GPU dépasse alors largement le calcul lui-même, et aucune parallélisation ne
# rattrape ça à batch=1. Un GPU sert quand les matrices sont grandes, pas quand elles sont
# nombreuses et minuscules.
#
# Le mono-thread gagne encore : à cette taille, la synchronisation entre 6 threads coûte
# plus que le travail réparti. Et surtout, il rend une CAMPAGNE parallèle saine — 12 runs
# mono-thread sur 12 cœurs, au lieu de 12 runs × 6 threads qui se battent pour la machine
# (load mesuré : 12,4 sur 12 cœurs, soit une saturation complète).
#
# ⚠️ Ce choix est propre à MiniGrid + dim_bus ≲ 128. Le jour où le berceau sera remplacé
# par une caméra (vecteurs d'entrée bien plus larges), il faudra REMESURER — d'où
# `NAULTHENE_DEVICE` qui laisse la main plutôt qu'un chiffre gravé.
#
# ⚠️⚠️ RÈGLE DE CAMPAGNE — NE JAMAIS MÉLANGER LES DEVICES DANS UNE MÊME COMPARAISON.
# Mesuré : à graine identique, CPU et MPS produisent des trajectoires DIFFÉRENTES
# (md5 des bilans distincts sur 5 jours), alors que chacun est parfaitement déterministe
# chez lui (A/A bit-identique en CPU). L'ordre des sommations flottantes diffère d'un
# backend à l'autre, et un agent chaotique amplifie cet écart jusqu'à changer de
# trajectoire. Comparer un témoin MPS à une variante CPU mesurerait donc le BACKEND, pas
# la mécanique — exactement le défaut de reproductibilité corrigé en v41.9, réintroduit
# par une autre porte. Un bras entamé sur un device doit être TERMINÉ sur ce device.
_DEVICE_DEMANDE = os.environ.get("NAULTHENE_DEVICE", "").strip().lower()
if _DEVICE_DEMANDE in ("cpu", "mps", "cuda"):
    DEVICE = torch.device(_DEVICE_DEMANDE)
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
elif torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
else:
    DEVICE = torch.device("cpu")

# Idem : borner les threads est un GAIN sur ce réseau, pas une bride. Réglable par
# NAULTHENE_THREADS pour un futur modèle plus large.
_THREADS = os.environ.get("NAULTHENE_THREADS", "").strip()
if _THREADS.isdigit() and int(_THREADS) > 0:
    torch.set_num_threads(int(_THREADS))

print(f"🚀 Exécution sur : {DEVICE} ({torch.get_num_threads()} thread(s))")

torch.manual_seed(42)
np.random.seed(42)

# Accès aux internes de MiniGrid pour la détection de jalons. Se désactive proprement
# si l'API a changé d'une version de minigrid à l'autre, au lieu de faire planter
# l'entraînement.
try:
    from minigrid.core.world_object import Key, Door, Goal, Ball
    from minigrid.core.actions import Actions
    _MINIGRID_INTERNALS_OK = True
except Exception:
    _MINIGRID_INTERNALS_OK = False


# --- 1. LE SCALPEL (Plasticité Structurelle) ---
class NaultheneLinearSynaptique(nn.Module):
    """
    Myélinisation Hebbienne (v20.0) : en plus du poids de base (mémoire cristallisée)
    et du poids annexe (apprentissage de la journée), une `trace_activation` marque les
    synapses récemment très actives (accumulation exponentielle, comme une trace
    d'éligibilité classique en RL). Quand un pic de dopamine survient (voir
    `fortification_dopaminergique`, appelé par tick depuis la boucle principale sur
    `poids_evenement` — pas une seule fois par jour sur la moyenne des récompenses,
    qui diluerait un bon repas isolé dans une journée difficile), les synapses
    marquées sont gravées instantanément dans `base_weight` : une vraie Potentiation à
    Long Terme (LTP) pilotée par l'événement, pas seulement par le cycle de sommeil.
    """
    def __init__(self, in_features, out_features):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features

        self.register_buffer('base_weight', torch.empty(out_features, in_features))
        nn.init.xavier_uniform_(self.base_weight)
        self.annexe_weight = nn.Parameter(torch.zeros(out_features, in_features))
        self.register_buffer('myeline_M', torch.zeros(out_features, in_features))
        self.register_buffer('trace_activation', torch.zeros(out_features, in_features))
        # Cristallisation Souple (v26.0-experimental, §A.5 AMELIORATION_V1.md) : myeline_cumul
        # accumule la myéline consolidée nuit après nuit (relaxation exponentielle maison,
        # ALPHA_CRISTAL, voir cycle_sommeil), distincte de myeline_M qui ne retient que le
        # maximum courant intra-journée. cristallisee est le flag d'immunité par poids
        # individuel — un cliquet à sens unique : une fois levé il ne redescend jamais (le
        # poids protégé reste librement modifiable par le gradient diurne, seule son érosion
        # nocturne est plafonnée, voir la règle dissymétrique dans cycle_sommeil).
        self.register_buffer('myeline_cumul', torch.zeros(out_features, in_features))
        self.register_buffer('cristallisee', torch.zeros(out_features, in_features, dtype=torch.bool))
        # v34.0-fix1 — LA NORME DE NAISSANCE : référence ABSOLUE du plancher vital.
        # Indispensable pour que la borne de couche soit cumulative : une borne relative à
        # la nuit précédente (0.95 × norme_veille) ne borne RIEN sur la durée, puisque la
        # référence suit la décroissance. C'est l'erreur que la première version de ce
        # correctif contenait, détectée par simulation (norme tombée à 1 % malgré la borne).
        # Mise à jour par `agrandir()` lors de la neurogenèse — jamais ailleurs.
        self.register_buffer('norme_naissance', self.base_weight.norm().clone())
        # v37.0-fix — échelle de référence de la myéline DE CETTE COUCHE : le maximum
        # historique de `myeline_M`. Remplace le `q_ref=1.0` absolu, qui rendait
        # `myeline_norm` structurellement nulle (myéline réelle mesurée : ~0,002 à 0,004,
        # soit 250 à 500× sous l'échelle supposée). Monotone croissante, jamais réduite.
        self.register_buffer('echelle_myeline', torch.zeros(()))

    def forward(self, x):
        weight_total = self.base_weight + self.annexe_weight
        if self.training:
            with torch.no_grad():
                activation_instantanee = torch.abs(self.annexe_weight.detach())
                self.myeline_M = torch.max(self.myeline_M, activation_instantanee)
                # Trace d'éligibilité : accumulation exponentielle des synapses actives
                # au fil des ticks de l'épisode, remise à zéro seulement à la
                # fortification (LTP) ou au sommeil — jamais à chaque tick.
                self.trace_activation = 0.9 * self.trace_activation + 0.1 * activation_instantanee
        return F.linear(x, weight_total)

    def fortification_dopaminergique(self, pic_dopamine: float):
        """LTP (v20.0) : un pic de dopamine (ex: manger, franchir une porte — voir
        `poids_evenement` dans la boucle principale) grave instantanément dans
        `base_weight` les synapses marquées par la trace d'éligibilité, proportionnellement
        à leur activité récente ET à l'intensité du pic. La trace est ensuite remise à
        zéro : chaque pic ne récompense que ce qui vient d'être actif, pas un historique
        qui s'accumulerait indéfiniment."""
        if pic_dopamine <= 0:
            return
        with torch.no_grad():
            ancrage = self.trace_activation * pic_dopamine
            self.myeline_M += ancrage
            self.base_weight += self.annexe_weight * torch.clamp(ancrage, 0.0, 1.0)
            self.trace_activation.zero_()

    def cycle_sommeil(self, lambda_erosion=0.05, q_ref=1.0):
        """Cristallisation Souple (v26.0-experimental, §A.5, correctif "Falaise" sigmoïde) :
        l'érosion (Étape 3) utilise désormais une myéline effective plancher-protégée
        (`myeline_norm_effectif`) plutôt que la myéline brute. Le plancher n'est plus une
        constante rigide (MYELINE_MIN_CRISTAL appliqué en tout ou rien) mais une falaise
        continue — une sigmoïde de `myeline_cumul` centrée sur SEUIL_CRISTAL — pour rester
        fidèle au principe du projet « régulation dynamique continue, jamais de règle en
        dur ». Le cliquet `cristallisee` (irréversible, voir Étape 3.5) reste la mémoire de
        consolidation : la falaise ne lisse que la MONTÉE en protection d'une synapse en
        train de se cristalliser ; une fois `cristallisee=True`, p_protection→1.0 et
        l'érosion devient quasi nulle, pour toujours. Rien d'autre ne change dans la
        formule : même patron, appliqué à un plancher au lieu du brut. Règle dissymétrique
        sommeil ≠ gradient : cette méthode ne touche jamais annexe_weight avant sa remise à
        zéro finale (identique à avant), et le gradient diurne (forward()) ne lit jamais
        myeline_cumul/cristallisee — la cristallisation ne fige que l'oubli passif, jamais
        l'apprentissage actif."""
        with torch.no_grad():
            # --- v37.0-fix : LA MYÉLINE VOIT L'APPRENTISSAGE AVANT D'ÊTRE CONSOMMÉE ---
            #
            # `myeline_M = max(myeline_M, |annexe|)` était calculée UNIQUEMENT dans
            # `forward()`, donc pendant la journée — à un moment où `annexe_weight` vaut
            # encore ce que le dernier `optimizer.step()` y avait laissé, c'est-à-dire zéro
            # au premier jour et la valeur de la VEILLE ensuite. Or la séquence nocturne est
            # `apprendre_journee` (step #1) → `rever` (step #2) → `cycle_sommeil` : aucun
            # `forward` n'a lieu entre le dernier step et l'érosion. La myéline qui protège
            # une couche ignorait donc systématiquement tout ce qu'elle venait d'apprendre.
            #
            # Conséquence mesurée sur `tete_motrice` : consolidation +0,0036, érosion
            # −0,0162 au taux PLEIN, remontée au plancher → 0,319490 avant, 0,319490 après,
            # au millionième. La couche était mathématiquement incapable de progresser.
            #
            # On rafraîchit ici, au seul endroit qui voit l'état FINAL de `annexe_weight`,
            # juste avant qu'il ne soit consommé. L'invariant du projet est intact : la
            # myéline ne peut toujours venir QUE du gradient, jamais d'une récompense
            # déclarée. Seul le MOMENT de la lecture change, pas sa source.
            self.myeline_M = torch.max(self.myeline_M,
                                       torch.abs(self.annexe_weight.detach()))

            # --- Étape 1 : consolidation (inchangée) ---
            self.base_weight += self.annexe_weight

            # --- Étape 2+3 : érosion, désormais plancher-protégée par la cristallisation ---
            # --- v37.0-fix : L'ÉCHELLE DE LA MYÉLINE EST RELATIVE, PLUS ABSOLUE ---
            #
            # `q_ref` valait 1.0 depuis toujours (paramètre jamais passé par aucun
            # appelant), ce qui suppose que `|annexe_weight|` atteint l'ordre de 1. La
            # mesure dit l'inverse : la myéline réelle plafonne à 0,0021 sur `tete_motrice`
            # et à 0,0043 sur les meilleures couches du cerveau V36. L'échelle est donc
            # ~500× trop grande, et `myeline_norm` reste collée à ~0 quoi qu'il arrive :
            # TOUTE couche s'érode au taux plein, myélinisée ou non. La protection promise
            # par la Cristallisation Souple n'a jamais pu s'exercer.
            #
            # C'est le même défaut, à l'identique, que `SEUIL_CRISTAL = 0.80` confronté à
            # une myéline réelle de 0,0038 (v34.0) : une échelle absolue posée a priori,
            # jamais vérifiée contre une mesure. La leçon du projet est déjà écrite —
            # `reference_richesse` a dû devenir proportionnelle à `empreinte_enfance` en
            # v31.0 pour la même raison.
            #
            # `echelle_myeline` suit donc une référence mesurée SUR CETTE COUCHE, et non
            # une unité arbitraire. On prend le QUANTILE HAUT plutôt que le maximum strict :
            # normaliser par le max fait porter toute l'échelle par une seule synapse
            # extrême, et écrase les 99 % restantes vers 0 (distribution mesurée sur
            # `tete_motrice` : médiane 0,027, p90 0,197, p99 1,000 — protection moyenne
            # 12,7 % seulement, contre une érosion de 5 % qu'il fallait battre).
            #
            # Avec le quantile, une synapse dans le peloton de tête de sa propre couche est
            # pleinement protégée, et non la seule championne. La hiérarchie entre synapses
            # est strictement conservée — c'est l'unité qui change, jamais l'ordre.
            # `q_ref` reste accepté en paramètre pour compatibilité, mais ne sert plus que
            # de borne minimale.
            quantile_courant = torch.quantile(self.myeline_M.flatten().float(),
                                              QUANTILE_ECHELLE_MYELINE)
            self.echelle_myeline = torch.maximum(self.echelle_myeline, quantile_courant)
            echelle = torch.clamp(self.echelle_myeline, min=PLANCHER_ECHELLE_MYELINE)
            myeline_norm = torch.clamp(self.myeline_M / echelle, 0.0, 1.0)
            # La falaise ne s'applique qu'aux synapses déjà cristallisées (cliquet Étape 3.5) :
            # p_protection→1.0 (érosion nulle) bien au-delà du seuil, →0.0 en dessous — mais
            # seul un myeline_cumul consolidé peut avoir levé le flag, donc une synapse
            # cristallisée reste dans la zone p_protection≈1.0 par construction (elle ne peut
            # plus reculer sous le seuil au sens du flag, même si myeline_cumul fluctue ensuite).
            # v41.44 — le seuil est RELATIF à ce que cette couche a atteint, jamais un
            # chiffre absolu (mesuré : 0 synapse sur 1 906 360 franchissait le 0,80 posé).
            # `echelle` est déjà calculée juste au-dessus : quantile 0,75 de `myeline_M`,
            # monotone croissante. On la réutilise pour ne pas dériver deux échelles.
            seuil_cristal = (echelle * FRACTION_SEUIL_CRISTAL
                             if CRISTALLISATION_RELATIVE_ACTIVE
                             else torch.as_tensor(SEUIL_CRISTAL_FOSSILE,
                                                  device=echelle.device,
                                                  dtype=echelle.dtype))
            p_protection = torch.sigmoid(K_RAIDEUR_CRISTAL * (self.myeline_cumul - seuil_cristal))
            plancher_cristal = self.cristallisee.float() * p_protection
            myeline_norm_effectif = torch.max(myeline_norm, plancher_cristal)

            # --- v34.0-fix1 : LE PLANCHER VITAL (correctif de l'extinction synaptique) ---
            #
            # Deux garde-fous qui ne dépendent d'AUCUN seuil absolu de myéline — c'est
            # précisément ce qui a fait échouer la Cristallisation Souple (SEUIL_CRISTAL=0.80
            # contre une myéline réelle de 0.0038 : jamais franchi, sur aucun cerveau).
            #
            # (a) Une synapse déjà FAIBLE mais vivante n'est plus érodée. Sans ça, tout poids
            #     non myélinisé converge géométriquement vers 0 puis passe au pruning — la
            #     mort est garantie par construction, pas par manque d'utilité.
            facteur = 1.0 - (lambda_erosion * (1.0 - myeline_norm_effectif))
            trop_faible = self.base_weight.abs() < PLANCHER_POIDS_VITAL
            facteur = torch.where(trop_faible, torch.ones_like(facteur), facteur)
            self.base_weight *= facteur

            # (b) La COUCHE entière conserve une fraction minimale de sa norme DE NAISSANCE.
            #     Garantit qu'aucun canal (vue, ouïe, mémoire…) ne peut s'éteindre
            #     globalement. L'oubli reste possible — l'extinction, non.
            #
            #     ⚠️ La référence est `norme_naissance`, PAS la norme de la nuit précédente :
            #     une borne relative à la veille ne borne rien cumulativement (0.95 × N_veille
            #     décroît indéfiniment avec N_veille). Erreur commise par la première version
            #     de ce correctif, détectée par simulation sur 2000 nuits.
            #     ⚠️⚠️ v37.0-fix — LE PLANCHER NE DOIT JAMAIS ÊTRE UN PLAFOND.
            #
            #     La v34.0 renormalisait à `norme_plancher` DEPUIS la norme post-érosion,
            #     ce qui ramenait la couche à EXACTEMENT 10 % de sa naissance — quelle que
            #     soit sa valeur d'entrée de nuit. Pour une couche collée au plancher, tout
            #     ce que le gradient avait consolidé quelques lignes plus haut
            #     (`base_weight += annexe_weight`, Étape 1) était donc intégralement effacé
            #     par cette ligne, chaque nuit.
            #
            #     Mesuré : `tete_motrice` à 0.319490 avant la journée, annexe consolidée de
            #     0.0139, norme après sommeil = 0.319490 — la valeur EXACTE d'avant, au
            #     millionième. La couche était mathématiquement incapable d'apprendre : le
            #     garde-fou censé la sauver la maintenait figée. 5 couches sur 12 du cerveau
            #     V36 étaient dans cet état, dont les DEUX têtes de décision.
            #
            #     Le correctif : ne remonter que ce qui manque, sans jamais redescendre.
            #     `torch.clamp(..., min=1.0)` garantit que le facteur ne peut qu'amplifier.
            #     Une couche qui a progressé au-dessus du plancher garde son acquis ; une
            #     couche qui s'est érodée en dessous est relevée, comme le voulait la v34.
            norme_apres = self.base_weight.norm()
            norme_plancher = self.norme_naissance * FRACTION_NORME_MIN_COUCHE
            if norme_apres > 0:
                facteur_plancher = torch.clamp(norme_plancher / norme_apres, min=1.0)
                self.base_weight *= facteur_plancher

            # --- Étape 3.5 (v26.0-experimental, §A.5) : accumulation inter-nuits de la
            # myéline consolidée de CETTE nuit (post-érosion, donc myeline_M actuel, avant
            # le pruning de l'Étape 4 qui suit) — même patron de relaxation exponentielle que
            # partout ailleurs dans le projet (x_{t+1} = x_t + (x_cible - x_t) * tau, voir
            # explications_readme.md §1), ici avec x_cible = myeline_M du jour et
            # tau = (1 - ALPHA_CRISTAL) puisque ALPHA_CRISTAL est le poids de PERSISTANCE
            # (mémoire longue), pas le taux de convergence. cristallisee est un cliquet à
            # sens unique (|=) : une fois consolidée, la protection ne se perd jamais, même
            # si la synapse redevient calme ensuite — seul le poids lui-même (via le gradient
            # diurne) peut encore évoluer. Les synapses jamais consolidées (cristallisee=False)
            # ne bénéficient d'aucun plancher : sous la falaise, elles s'érodent au taux plein
            # et tombent sous le masque de mort (Étape 4) sans traîner pendant des centaines
            # de nuits — "zéro synapse fantôme".
            self.myeline_cumul += (self.myeline_M - self.myeline_cumul) * (1.0 - ALPHA_CRISTAL)
            # v41.44 — même seuil relatif que la falaise ci-dessus. Le cliquet reste à
            # SENS UNIQUE (`|=`) : une synapse cristallisée ne se décristallise jamais,
            # même si l'échelle de sa couche continue de monter ensuite.
            if CRISTALLISATION_ACTIVE:
                self.cristallisee |= (self.myeline_cumul >= seuil_cristal)

            # --- Étape 4 : élagage des synapses mortes ---
            #
            # v34.0-fix1 : le pruning ne s'applique plus qu'aux synapses EXACTEMENT nulles
            # ou dénormalisées. Auparavant le seuil 1e-4 était le dernier maillon de la
            # chaîne d'extinction : l'érosion géométrique amenait sous 1e-4 en ~121 nuits,
            # puis ce masque figeait la mort à 0.0 définitivement (base ET myeline_M, donc
            # sans retour possible). Avec le plancher vital (a) ci-dessus, plus aucune
            # synapse ne descend sous PLANCHER_POIDS_VITAL par simple érosion — ce masque
            # ne doit donc plus servir qu'à nettoyer ce qui est déjà mort.
            masque_mort = torch.abs(self.base_weight) < 1e-12
            self.base_weight[masque_mort] = 0.0
            self.myeline_M[masque_mort] = 0.0
            self.annexe_weight.zero_()
            self.trace_activation.zero_()
            return int(masque_mort.sum().item())

    def agrandir(self, segments_in, extra_out):
        total_ancien = sum(o for o, _ in segments_in)
        assert total_ancien == self.in_features, \
            f"Segmentation incohérente : {total_ancien} != {self.in_features}"

        extra_in = sum(e for _, e in segments_in)
        if extra_in == 0 and extra_out == 0:
            return

        new_in = self.in_features + extra_in
        new_out = self.out_features + extra_out
        dev = self.base_weight.device

        new_base = torch.empty(new_out, new_in, device=dev)
        nn.init.xavier_uniform_(new_base)
        new_base *= 0.1
        new_annexe = torch.zeros(new_out, new_in, device=dev)
        new_myeline = torch.zeros(new_out, new_in, device=dev)
        new_trace = torch.zeros(new_out, new_in, device=dev)
        # Cristallisation Souple (v26.0-experimental, §A.5) : les nouvelles dimensions
        # (colonnes/lignes ajoutées par la neurogenèse) n'ont aucun historique d'usage —
        # elles naissent à myeline_cumul=0 / cristallisee=False, jamais héritées des
        # anciennes positions ni pré-cristallisées. Même triptyque que myeline_M/
        # trace_activation ci-dessous : resize + copie par segment.
        new_myeline_cumul = torch.zeros(new_out, new_in, device=dev)
        new_cristallisee = torch.zeros(new_out, new_in, device=dev, dtype=torch.bool)

        src = 0
        dst = 0
        for taille, ajout in segments_in:
            new_base[:self.out_features, dst:dst + taille] = self.base_weight[:, src:src + taille]
            new_myeline[:self.out_features, dst:dst + taille] = self.myeline_M[:, src:src + taille]
            new_trace[:self.out_features, dst:dst + taille] = self.trace_activation[:, src:src + taille]
            new_myeline_cumul[:self.out_features, dst:dst + taille] = self.myeline_cumul[:, src:src + taille]
            new_cristallisee[:self.out_features, dst:dst + taille] = self.cristallisee[:, src:src + taille]
            src += taille
            dst += taille + ajout

        self.base_weight = new_base
        self.myeline_M = new_myeline
        self.trace_activation = new_trace
        self.myeline_cumul = new_myeline_cumul
        self.cristallisee = new_cristallisee
        self.annexe_weight = nn.Parameter(new_annexe)
        self.in_features, self.out_features = new_in, new_out

        # v34.0-fix2 — LA RÉFÉRENCE NE DOIT JAMAIS RÉTRÉCIR.
        #
        # La neurogenèse recopie les poids ANCIENS (déjà érodés, potentiellement au
        # plancher) et n'initialise à neuf que les dimensions ajoutées. La norme du tenseur
        # agrandi peut donc être BIEN PLUS PETITE que la norme d'origine — mesuré : une
        # couche née à 5.31, érodée à 0.53, puis agrandie de 16→32 dims retombait à une
        # `norme_naissance` de 0.74. Le plancher chutait alors de 0.53 à 0.074, soit une
        # protection divisée par 7 : chaque neurogenèse affaiblissait le garde-fou, et un
        # cerveau qui grandit beaucoup aurait fini par ne plus être protégé du tout.
        #
        # On prend donc le MAXIMUM entre l'ancienne référence et la nouvelle : la
        # protection ne peut que croître avec le substrat, jamais décroître avec l'usure.
        self.norme_naissance = torch.maximum(self.norme_naissance,
                                              self.base_weight.norm()).clone()


# v36.0 — LE RAPPEL MARQUANT : 2 dims ajoutées EN QUEUE (contrat append-only, invariant 2
# du Bus Sensoriel). `[valence, confiance]` du repère le plus pesant près de l'agent, toutes
# étiquettes confondues — c'est ce qui permet à un danger appris de devenir évitable sans
# qu'aucune ligne de code ne mentionne « lave ». Neutre = [0.5, 0.0] : valence indifférente
# (0.5 après normalisation dans [0,1]) et confiance nulle, donc `integrateur_bio` apprend à
# ignorer le canal tant qu'il ne porte rien.
DIM_RAPPEL_MARQUANT = 2

# --- v39.2 : LE BIT DE PRÉSENCE AUDITIVE — écouter le calme ≠ ne pas avoir d'oreilles ---
#
# 🔴 CE QUE ÇA CORRIGE (mesuré) : `porte_auditive` est SANS BIAIS, donc
#
#     relu(porte_auditive(zeros)).norm() == 0.000000   (exact)
#     norme du bus avec obs_auditive=None : 6.3323
#     norme du bus avec un silence numérique : 6.3323  (écart 0.0000)
#
# Un silence PARFAIT et une oreille ABSENTE produisaient rigoureusement le même état
# interne. Le correctif v39.0 avait rendu ce défaut explicite (il est bit-identique par
# construction) ; il ne l'avait PAS levé. L'agent était toujours sourd sans le savoir.
#
# C'est la remarque de l'utilisateur, et elle vise juste :
#   « Le silence n'est pas 0. Le silence, c'est quand il y a presque plus rien à établir. »
#
# La dimension porte l'AMPLITUDE MOYENNE réellement perçue, pas un booléen : le calme est
# un continuum (un murmure n'est pas un silence, qui n'est pas une absence d'oreille).
#   0.0 = aucun canal auditif ce tick (rêve, vocal hors-ligne)
#   >0  = le canal existe, et voici ce qu'il porte
#
# ⚠️ AJOUTÉE EN QUEUE, jamais au milieu (contrat append-only du vecteur bio) : une
# insertion décalerait silencieusement tous les acquis des `.brain` existants. La greffe
# `_greffer_vecteur_bio_etendu` recopie les N premières colonnes, donc un `.brain` v39.1
# se recharge en héritant d'un canal neutre à 0.
DIM_PRESENCE_AUDITIVE = 1

# --- v41.33 : LA PROPRIOCEPTION DE LA CHARGE (le « bit de portage ») ---
#
# 🔴 CE QUE ÇA CORRIGE (mesuré le 27/08/2026, 3 cerveaux × 6000 ticks). Le critique
# distingue TRÈS BIEN un objet en face d'un mur (d de Cohen +0,651 à +1,214) — il n'est
# donc pas aveugle au monde. Mais il ne distingue PAS « je porte un objet » de « j'ai les
# mains vides » : d = +0,119 / −0,117 / +0,090, le signe s'inversant d'un cerveau à
# l'autre. Or c'est exactement la variable dont dépend le TD-error d'une saisie : si
# V(porte) ≈ V(mains vides), l'avantage d'une saisie ne peut PAS produire de pic, et c'est
# ce qui a été mesuré (|A| utile / |A| neutre entre 0,86× et 1,11× sur 4 cerveaux).
#
# LA CAUSE N'ÉTAIT PAS UN DÉFAUT D'APPRENTISSAGE, MAIS UNE ABSENCE D'ENTRÉE. Vérifié sur
# 4000 ticks : des 41 dims du vecteur bio, **ZÉRO** ne séparait les deux états (écart max
# 0,00001013). L'inventaire n'était encodé nulle part. Aucune quantité de gradient ne fait
# apprendre une variable absente de l'entrée.
#
# L'information existe pourtant dans la VUE (d de Cohen global 6,73 : l'objet a disparu de
# la grille), mais elle y arrive comme un indice INDIRECT, confondu avec « un objet a été
# déplacé quelque part ». Rien n'oblige le réseau à le lire comme « je possède ».
#
# ⚠️ CE N'EST PAS UNE RÉCOMPENSE EN DUR. La dimension porte une PERCEPTION, au même titre
# que la faim ou la pression tactile : rien ne déclare qu'être chargé est bon. Le réseau
# reste libre de l'ignorer — c'est à lui de découvrir, par la résolution ultérieure de sa
# faim, si porter tel objet mène quelque part. Le dogme est intact.
#
# ⚠️ AJOUTÉE EN QUEUE, jamais au milieu (contrat append-only, invariant v29.0) : la greffe
# `_greffer_vecteur_bio_etendu` recopie les N premières colonnes, donc un `.brain` à 41
# dims se recharge en héritant d'un canal neutre à 0.
#
# Le neutre est **0.0**, et ici c'est JUSTE (contrairement à la clinotaxie v32.0 ou au
# rappel marquant v36.0, dont le 0.0 signifierait « pire cas ») : 0.0 veut dire « je ne
# porte rien », ce qui est exactement l'information à porter, pas une inconnue.
DIM_PORTAGE = 1

# Interrupteur d'ablation (v41.33). False = la 42ᵉ dim existe toujours mais reste à 0.0 :
# le témoin conserve la LARGEUR du réseau et ne coupe que l'INFORMATION.
PORTAGE_PERCU_ACTIF = True

# --- v41.34 : LE TRONC PERCEPTIF EST-IL COUPÉ POUR RIEN ? ---
#
# `_executer_c1_reflexe` contient `pensee_enrichie.detach()` — présent dans `colab.py`
# DEPUIS L'ORIGINE du projet, **jamais commenté, jamais justifié, jamais mesuré**. C'est
# le dernier choix structurel du cœur dont personne ne connaît la raison.
#
# 🔴 CE QU'IL FAIT (mesuré le 27/08/2026, 3 pertes injectées séparément) :
#
#   couche              JEPA        ACTEUR      CRITIQUE
#   porte_visuelle      0.033868    0.000000    0.000000
#   hippocampe          0.042690    0.000000    0.000000
#   analyseur           0.105406    0.000000    0.000000
#   fusion_memoire      0.000000    0.000000    0.000000
#   integrateur_bio     0.000000    3.370580    4.332367
#
# **Seul le JEPA sculpte la perception.** L'acteur et le critique n'y envoient rien —
# exactement 0,000000. Ils travaillent sur une représentation qu'il ne leur est pas permis
# de modifier, optimisée pour PRÉDIRE la dynamique, jamais pour distinguer ce qui a de la
# valeur.
#
# 🔴 POURQUOI ÇA POURRAIT COMPTER. Le bit de portage vaut **+0,325 de valeur** en
# contrefactuel pur, soit 361 % du mouvement typique de `V` — et pourtant le saut RÉEL au
# moment d'une saisie ne vaut que **+0,006**, contre +0,015 sur un tick banal. Le signal
# est noyé par le bruit de la vue (±0,090/tick, non orienté), parce que la perception
# n'a aucune raison d'apprendre à taire ce qui ne vaut rien. C'est ce qui a réfuté le
# passage en TD(0) (13ᵉ réfutation, `docs/recherche/CLIC_27082026_*.md`).
#
# ⚠️ CE DRAPEAU N'EST PAS UNE CORRECTION, C'EST UNE QUESTION. Le `.detach()` protège
# peut-être quelque chose de réel : sans lui, le gradient de l'acteur remonte dans un
# tronc RÉCURRENT (`hippocampe` lit `memoire_precedente`), et les deux têtes se
# rétropropagent désormais dans les MÊMES couches perceptives — c'est précisément la
# collision C1/C2 mesurée en v41.32 sur `integrateur_bio`, mais étendue à quatre couches
# de plus. Le bras peut donc être NUISIBLE, et l'A/B doit pouvoir le dire.
#
# True = comportement strictement identique à toutes les versions antérieures.
TRONC_PERCEPTIF_DETACHE = True

DIM_VECTEUR_BIO = (16 + DIM_TOUCHER + DIM_CHIMIE + DIM_EXO
                   + DIM_ODORAT_DELTA + DIM_THERMOCEPTION + DIM_PRESSION
                   + DIM_RAPPEL_MARQUANT
                   + DIM_PRESENCE_AUDITIVE
                   + DIM_PORTAGE)  # = 42 depuis la v41.33
                       # 3 jauges (satiete, hydratation, stimulation) + 3 quête (target_vector one-hot)
                       # + 2 rappel spatial (v20.0 : distance normalisée + fraîcheur du souvenir)
                       # + 8 quête vocale (v22.1 : formants cibles de la leçon en cours, ou [0]*8
                       # hors leçon — voir BiologicalHomeostasisEngine.obtenir_vecteur_bio)
                       # + 4 toucher (v29.0 : contact frontal, objet en main, orientation cos/sin)
                       # + 4 chimie (v29.0 : odorat nourriture/eau + goût nourriture/eau)
                       # + 8 Exo-Sens (v30.0 : le 6ème sens — perception continue du monde
                       #   numérique via PortC3 ; vecteur NUL si aucun plug branché, auquel cas
                       #   le comportement est strictement celui de la v29.1)
                       # + 2 clinotaxie (v32.0 : ΔS de l'odorat food/eau entre deux ticks,
                       #   normalisé dans [0,1] avec 0.5 = neutre. Sans elles, integrateur_bio
                       #   n'avait aucun état interne lui permettant de dériver S_t : il était
                       #   AVEUGLE AU MOUVEMENT, incapable de savoir si son dernier pas l'avait
                       #   rapproché d'une ressource. Voir bus_sensoriel.DIM_ODORAT_DELTA.)
                       # + 2 thermoception (v41.11 : chaleur perçue du danger + sa variation,
                       #   même loi de diffusion que l'odorat. Mesuré avant l'ajout : le
                       #   vecteur bio était RIGOUREUSEMENT IDENTIQUE sur la case adjacente à
                       #   la lave et à trois cases de là, et MiniGrid punit la mort par
                       #   exactement 0.0 — l'agent ne pouvait apprendre le danger ni par les
                       #   sens ni par l'expérience. Voir bus_sensoriel.DIM_THERMOCEPTION.)
                       #
                       # v29.0 — les 3 sens faibles à moyens (toucher, odorat, goût) entrent par la
                       # QUEUE de ce vecteur, jamais par une porte sommée dans le bus latent : ils
                       # ne polluent donc jamais la cible JEPA (perte_jepa compare toujours le bus
                       # prédit au bus réel de la VISION seule), et un .brain pré-v29.0 se greffe par
                       # recopie des 16 premières dims (voir persistance._greffer_vecteur_bio_etendu).
                       # Toute nouvelle dimension future doit s'ajouter EN QUEUE, jamais au milieu.

# --- Hémisphère Auditif & Vocal (v22.0/v22.1, expérimental — voir CONCEPTION_v22_audio.md) ---
# Dimensions FIXES comme DIM_VECTEUR_BIO : elles ne grandissent JAMAIS avec la
# neurogenèse (voir declencher_neurogenese, segments_in des couches porte_auditive/
# tete_vocale).
#
# v22.1 — correctif du "court-circuit de la double entrée" (défaut détecté à la revue) :
# l'oreille (porte_auditive) ne reçoit plus QUE le son brut (MFCC). En v22.0, l'embedding
# sémantique du mot était concaténé directement à l'entrée de l'oreille — un réseau
# paresseux recevant le concept parfait en même temps que le son bruité apprend à
# ignorer le son (il n'écoute jamais vraiment). Le concept-cible est désormais une
# QUÊTE dans vecteur_bio (voir DIM_VECTEUR_BIO ci-dessus), pas un cadeau en entrée —
# l'agent doit traduire ce qu'il perçoit vers la cible, il ne peut plus tricher.
DIM_MFCC = 130                 # 13 coefficients MFCC × 10 frames aplatis (son brut, lobe temporal)
DIM_EMBED_SEMANTIQUE = 32      # embedding sémantique du mot (Ollama all-minilm-l6-v2, réduit de 384
                                # dims natives) — conservé pour un usage futur (v23+), n'entre plus
                                # dans porte_auditive depuis v22.1 (voir Question ouverte B du plan v22.1)
DIM_AUDIO_ENTREE = DIM_MFCC    # entrée de porte_auditive (l'OREILLE) — MFCC seul depuis v22.1
DIM_VOCALE = 8                 # sortie de tete_vocale (la BOUCHE) : f0, F1, F2, F3, F1_bw, F2_bw,
                                # duree, amplitude — paramètres physiques du synthétiseur de formants


# --- 2. LE CERVEAU C1 (RÉFLEXE) & C2 (NÉO-CORTEX) ---
#
# v29.0 (expérimental) — Identité C1/C2 explicite. Jusqu'en v28.0, la distinction
# "Système 1 instinctif / Système 2 délibératif" existait bien dans le code (tete_motrice
# d'un côté, simuler_futur_et_planifier de l'autre) mais restait implicite : les deux
# étaient entrelacés dans le corps de penser(), sans frontière nommée. Elle est désormais
# encapsulée dans deux méthodes explicites — _executer_c1_reflexe() et
# _solliciter_c2_neocortex() — qui délimitent noir sur blanc qui fait quoi :
#
#   C1 (LE CERVEAU AUTOMATIQUE, léger) : tronc cérébral multimodal, compression du flux
#      des 5 sens vers bus_latent, lecture épisodique, intégration viscérale, et le
#      réflexe moteur immédiat (tete_motrice). C'est lui qui porte la chimie (dopamine,
#      homéostasie) et les représentations DÉJÀ distillées (base_weight de chaque couche).
#
#   C2 (LE NÉO-CORTEX, lourd) : le modèle du monde JEPA (generateur_attente) et la
#      simulation mentale multi-horizons (simuler_futur_et_planifier). Il ne reçoit
#      JAMAIS le flux sensoriel brut — toujours l'état DÉJÀ COMPRESSÉ par C1 (pensee_bio),
#      exactement comme dans le schéma de docs/ameliorations_appliquees/Maj_V29_readme.md.
#
# Ce découpage est une RESTRUCTURATION PURE (décision utilisateur explicite, v29.0) :
# C2 continue d'être sollicité à chaque tick comme avant, et le comportement d'un cerveau
# existant reste bit-identique à la v28.0. Ne PAS y introduire de court-circuit
# conditionnel ("C1 saute C2 s'il est confiant") sans demande explicite de l'utilisateur :
# ce serait un déclenchement sur seuil codé en dur dans le chemin de décision, de la même
# nature que ce que CLAUDE.md interdit déjà pour l'appel à C3.
#
# La distillation C2 → C1 (transformer la réflexion lourde en réflexe léger), elle, n'est
# PAS un nouveau mécanisme : elle est déjà réalisée par le cycle jour/nuit existant —
# annexe_weight accumule le gradient diurne, cycle_sommeil() le consolide dans base_weight
# et la Cristallisation Souple (v26.0) fige les synapses les plus myélinisées. Voir
# NaultheneLinearSynaptique.cycle_sommeil et cycle_sommeil_global.

# Cascade C1 → C2 → C3 (v28.0, expérimental). La 8ème action ("tendre la main vers
# l'Exocortex") n'est PAS un déclencheur codé en dur — c'est une action apprise comme
# les 7 autres, par le même REINFORCE que tete_motrice. Elle n'est disponible (logit
# non masqué à -inf, voir penser()) que si au moins un plug est enregistré sur le
# PortC3 ET disponible ce tick-là — sans quoi le comportement reste bit-identique à la
# v27.6 (aucun plug ⇒ action 7 strictement inexistante, jamais échantillonnée).
NUM_ACTIONS_BASE = 7
# v41.28 — index de `forward` dans l'énumération MiniGrid (`unwrapped.actions`). Ce n'est
# pas un réglage : c'est le contrat de l'API du monde, au même titre que les index déjà
# utilisés pour `ACTION_CONSOMMER`. Sert à distinguer une locomotion TENTÉE (pousser un
# mur) d'une manipulation tentée — les deux coûtent, mais pas le même travail.
ACTION_AVANCER = 2
ACTION_DEMANDER = 7        # index de la 8ème action dans actions_eye
# v41.2-fix5 — l'action par laquelle l'agent CONSOMME une ressource. C'est le `pickup` de
# MiniGrid (index 3), réutilisé plutôt qu'une 9ème action ajoutée : le geste « je saisis ce
# qui est devant moi » existe déjà, et c'est la plus coûteuse du barème corporel
# (COUT_CORPOREL_PAR_ACTION[3] = 0,8, contre 0,2 pour tourner). Manger a donc un prix, et
# l'agent doit choisir de le payer — ce qui n'était pas le cas quand marcher sur une case
# suffisait.
ACTION_CONSOMMER = 3
NUM_ACTIONS_AVEC_C3 = 8
# Routage (Chantier 2b) : DIM_ROUTAGE_C3 = nombre max de plugs simultanés + 1 canal de
# diffusion ("1_X"). Volontairement petit et fixe — comme DIM_VECTEUR_BIO/DIM_VOCALE,
# ne grandit jamais avec la neurogenèse (segments_in de tete_requete dans
# declencher_neurogenese n'inclut donc pas ce vecteur, il n'existe même pas en entrée).
DIM_ROUTAGE_C3 = 5         # jusqu'à 4 plugs adressables en 1_1 + 1 canal 1_X


class AGI_Naulthene(nn.Module):
    def __init__(self, dim_visuelle=147, dim_bus=16, num_actions=NUM_ACTIONS_AVEC_C3, lr=1e-3):
        super().__init__()
        self.dim_visuelle = dim_visuelle
        self.dim_bus = dim_bus
        self.num_actions = num_actions
        self.lr = lr

        self.porte_visuelle = NaultheneLinearSynaptique(dim_visuelle, dim_bus)
        self.hippocampe = NaultheneLinearSynaptique(dim_bus * 2, dim_bus)
        self.fusion_memoire = NaultheneLinearSynaptique(dim_bus * 2, dim_bus)
        self.analyseur = NaultheneLinearSynaptique(dim_bus, dim_bus)
        # Intégrateur bio (v18.0, étendu en v20.0) : fusionne la pensée avec l'état
        # viscéral (jauges + quête intrinsèque + rappel de mémoire épisodique spatiale,
        # DIM_VECTEUR_BIO=8) juste avant la prise de décision. Le vecteur bio ne grandit
        # JAMAIS avec la neurogenèse (toujours DIM_VECTEUR_BIO dims) — seul le cerveau
        # autour grandit, cohérent avec segments_in dans declencher_neurogenese.
        self.integrateur_bio = NaultheneLinearSynaptique(dim_bus + DIM_VECTEUR_BIO, dim_bus)
        self.tete_motrice = NaultheneLinearSynaptique(dim_bus, num_actions)
        self.cortex_prefrontal = NaultheneLinearSynaptique(dim_bus, 1)
        self.generateur_attente = NaultheneLinearSynaptique(num_actions + dim_bus, dim_bus)
        # Tête de routage C3 (v28.0, expérimental) : depuis pensee_bio, choisit VERS
        # QUEL plug émettre (ou le canal de diffusion 1_X) — miroir de tete_motrice
        # mais sortie fixe (comme cortex_prefrontal/tete_vocale, jamais agrandie par
        # la neurogenèse, voir declencher_neurogenese).
        self.tete_requete = NaultheneLinearSynaptique(dim_bus, DIM_ROUTAGE_C3)

        # --- Hémisphère Auditif & Vocal (v22.0, expérimental ; corrigé v22.1) ---
        # L'OREILLE (lobe temporal) : miroir exact de porte_visuelle. Entrée fixe
        # DIM_AUDIO_ENTREE (le MFCC seul depuis v22.1 — l'embedding sémantique est
        # désormais une quête dans vecteur_bio, pas un cadeau en entrée, voir
        # DIM_VECTEUR_BIO ci-dessus), sortie dim_bus (grandit avec la neurogenèse).
        self.porte_auditive = NaultheneLinearSynaptique(DIM_AUDIO_ENTREE, dim_bus)
        # La BOUCHE (aire de Broca) : miroir exact de tete_motrice. Entrée dim_bus
        # (grandit), sortie fixe DIM_VOCALE=8 (les paramètres physiques de formants,
        # comme num_actions ne grandit jamais pour tete_motrice).
        self.tete_vocale = NaultheneLinearSynaptique(dim_bus, DIM_VOCALE)
        # Cortex auditif prédictif (v22.1, correctif défaut 3) : tête JEPA SÉPARÉE de
        # generateur_attente, plutôt qu'une seule tête mélangeant les deux cibles sans
        # pondération (risque d'empoisonnement du JEPA visuel par le signal audio dès
        # le tick 0). Miroir exact de generateur_attente — voir perte_jepa pour le
        # coefficient de pondération progressif (coeff_jepa_audio).
        self.generateur_attente_audio = NaultheneLinearSynaptique(num_actions + dim_bus, dim_bus)

        self.register_buffer('actions_eye', torch.eye(num_actions))

        # Port Exocortex C3 (v28.0, expérimental) — infrastructure, PAS un état
        # cognitif : jamais sérialisé dans le .brain (voir persistance.py), toujours
        # recréé vide à chaque `AGI_Naulthene()`. C'est l'appelant (un cursus, un
        # script de test) qui enregistre explicitement des plugs dessus après
        # instanciation — un cerveau neuf n'a donc jamais de plug par défaut, cohérent
        # avec l'invariance biologique pure (Chantier "Test d'Invariance").
        self.port_c3 = PortC3()

        # Auto-distillation C2 → C1 (v37.0, Mesure 3) — buffer de travail de la journée,
        # jamais un état cognitif : rempli tick par tick par `penser()`, vidé par
        # `apprendre_journee()`. Une liste Python ordinaire, donc jamais sérialisée dans
        # le .brain — un cerveau rechargé repart avec un buffer vide, ce qui est correct
        # (les pertes d'une journée passée n'ont aucun sens le lendemain).
        self._pertes_distillation = []

        # v37.1 — L'échelle à laquelle CET agent juge un choc dopaminergique fort ou
        # faible. Ce n'est pas un seuil : c'est un NIVEAU, moyenne glissante de ce qu'il a
        # lui-même vécu, qui évolue avec son âge et ses habitudes. Un agent qui n'a jamais
        # connu mieux qu'un micro-progrès le trouve marquant ; devenu expert, il ne le
        # remarque plus. État cognitif à part entière → sérialisé dans le .brain.
        # `None` = jamais mesuré (la 1re journée avec un choc l'établit).
        self.reference_choc_dopamine = None

        # v40.0 — LE VÉCU QUI DÉTERMINE LA FORCE DE PLANIFICATION.
        #
        # Deux compteurs, et rien d'autre : la somme pondérée de ce qui a marché (OKAY) et
        # de ce qui a fait mal (DANGER). Ils ne contiennent aucune connaissance déclarée —
        # l'agent ne sait pas ce qu'est une victoire, il a juste ressenti des chocs.
        #
        # À la naissance les deux valent 0, donc f = 0/(0+0+1) = 0 : C1 SEUL. La confiance
        # en la planification se GAGNE, elle n'est jamais accordée. Sérialisés dans le
        # .brain — c'est de l'état cognitif, au même titre que `reference_choc_dopamine`.
        self.vecu_okay = 0.0
        self.vecu_danger = 0.0

        # v41.0 — LA LIGNE DE FLOTTAISON MÉTABOLIQUE : le coût du tick ordinaire, tel que
        # l'agent le vit. `None` (et non 0.0) à la naissance : c'est « jamais mesuré », un
        # état que l'arithmétique ne peut pas représenter — une flottaison de 0.0 est une
        # mesure valide (un organisme sans coût), pas une absence de mesure. Initialisée à
        # la première nuit sur la médiane observée, puis suivie par cliquet. Sérialisée
        # dans le .brain — c'est de l'état cognitif acquis.
        self.flottaison_metabolique = None
        self.mesure_flottaison = {}

        # v40.1 — L'ENVIE DE VIVRE. Naît au MAXIMUM (le nourrisson tente tout) et se
        # compose multiplicativement chaque nuit. Peut atteindre zéro : aucun plancher.
        # État cognitif à part entière → sérialisé dans le .brain.
        self.envie_de_vivre = ENVIE_NAISSANCE
        # Amplitude BRUTE de C1 au dernier tick (avant gain) : c'est la mesure de « ce que
        # C1 a construit » qu'utilise `reviser_envie_de_vivre`. Alimentée par `penser`.
        # 0.0 à la naissance = une expérience nulle, donc aucune lucidité, donc envie MAX.
        self.amplitude_c1_recente = 0.0
        self.mesure_envie = {}

        self._reset_optimizer()

    def acceptation(self):
        """v40.1 — la force d'ACCEPTATION de C1, couplée à la compréhension de C2.

        « C1 est lui-même lié à cet élément comme une force qui est comme de l'acceptation
        et devient exponentielle liée à la compréhension de C2. »

        L'acceptation est le produit de l'envie de vivre et de la confiance en la
        planification : C1 accepte d'autant plus que C2 comprend. Comme les deux facteurs
        vivent dans [0, 1], leur produit ne peut pas s'emballer — l'exponentielle vient de
        la COMPOSITION dans le temps (voir `reviser_envie_de_vivre`), jamais d'un `exp()`.

        C'est ce nombre, et non `force_planification` seule, qui module l'ensemble des
        décisions : exploration, patience, et poids de C2.
        """
        return self.envie_de_vivre * self.force_planification_vecue()

    def reviser_envie_de_vivre(self, erreur_jepa_moyenne):
        """v40.1 — la composition multiplicative de l'envie de vivre (une fois par nuit).

        Deux forces opposées, appliquées comme des FACTEURS (jamais des termes) :

          LUCIDITÉ ↓  — ce que C2 comprend × ce que C1 a construit. Plus l'agent prévoit
                        juste, plus il VOIT le risque, moins il ose. La compétence produit
                        sa propre paralysie.
          FOI      ↑  — la part de son vécu qui a été bonne. Tant qu'il accumule des
                        réussites, il reste en mouvement malgré la prudence croissante.

        La composition produit les trois propriétés demandées sans qu'aucune ne soit
        écrite séparément : une série de facteurs > 1 s'emballe (boule de neige), un
        facteur bas casse la série (inversion), et rien n'est moyenné (les deux réservoirs
        de vécu restent parallèles).

        ⚠️ Aucun plancher : l'envie peut atteindre 0 et l'agent s'y figer. C'est voulu.
        """
        # Ce que C2 comprend du monde : l'inverse de son erreur de prédiction, borné dans
        # [0, 1]. Un agent qui prédit mal ne voit pas le risque, donc n'a pas peur.
        erreur = max(float(erreur_jepa_moyenne or 0.0), 0.0)
        comprehension_c2 = 1.0 / (1.0 + erreur)

        # Ce que C1 a construit : sa vigueur réelle, rapportée à l'échelle naturelle de
        # l'arbitrage (`AMPLITUDE_C2_NORMALISEE`, l'amplitude d'un z-score sur 7 actions).
        # Aucune constante nouvelle — c'est la même échelle que celle qui sert déjà à la
        # parité C1/C2.
        #
        # v40.1-fix2 — l'échelle est AMPLITUDE_C2_NORMALISEE, PAS `vigueur_min_c1(f)`.
        # Avec cette dernière, un agent à foi nulle donnait cible = 0, donc experience_c1
        # forcée à 0, donc lucidité nulle : L'AGENT LE PLUS DÉSESPÉRÉ ÉTAIT LE SEUL
        # IMMUNISÉ CONTRE LA PERTE D'ENVIE (mesuré : envie restait à 1,000000 après 1000
        # nuits sans la moindre réussite). L'expérience de C1 est une propriété de C1, elle
        # ne doit pas dépendre de la confiance accordée à C2.
        experience_c1 = min(1.0, self.amplitude_c1_recente / AMPLITUDE_C2_NORMALISEE)

        lucidite = comprehension_c2 * experience_c1        # ∈ [0, 1]
        foi = self.force_planification_vecue()             # ∈ [0, 1[

        # LES DEUX FACTEURS. Ils ne s'additionnent pas et ne s'annulent pas : ils se
        # composent, l'un après l'autre, sur l'état de la nuit précédente.
        self.envie_de_vivre *= (1.0 - POIDS_LUCIDITE * lucidite)
        self.envie_de_vivre *= (1.0 + POIDS_FOI * foi)

        # v40.1-fix1 — LA FOI EST AUSSI UN APPORT, PAS SEULEMENT UN FACTEUR.
        #
        # Défaut mesuré à l'implémentation : en purement multiplicatif, ZÉRO EST ABSORBANT.
        # Un agent tombé à 0,0001 puis redevenu très performant remontait de 0,0001 à…
        # 0,0001 (+3 % de presque rien reste presque rien). L'« inversion » demandée —
        # « certains éléments peuvent littéralement changer le sens » — était donc
        # nominalement vraie et pratiquement impossible : la mort était le seul état
        # absorbant, et la mécanique ne racontait plus qu'une histoire à sens unique.
        #
        # Le terme additif est ce qui rend la résurrection possible : il ne dépend PAS de
        # l'état courant, donc il fonctionne même depuis zéro. Il reste proportionnel à la
        # foi — un agent qui ne réussit rien ne ressuscite pas — et au carré, pour qu'une
        # foi tiède ne suffise pas : il faut une vraie série de réussites pour rallumer
        # quelqu'un qui s'était éteint.
        #
        # ⚠️ Ceci ne réintroduit PAS de plancher : envie = 0 reste atteignable et STABLE
        # tant que la foi est nulle. On ne garantit pas la survie, on garantit seulement
        # qu'une rédemption reste possible pour qui recommence à réussir.
        self.envie_de_vivre += POIDS_FOI * (foi ** 2)

        self.envie_de_vivre = max(0.0, min(ENVIE_PLAFOND, self.envie_de_vivre))

        # Télémétrie : sans elle, une mécanique latente est indémontrable (leçon v29.1).
        self.mesure_envie = {
            "envie": self.envie_de_vivre,
            "lucidite": lucidite,
            "foi": foi,
            "comprehension_c2": comprehension_c2,
            "experience_c1": experience_c1,
            "acceptation": self.acceptation(),
        }

    def force_planification_vecue(self):
        """v40.0 — la force de planification, DÉRIVÉE du vécu (jamais une constante).

        « C1 a toujours raison, sauf si C2 estime que le bénéfice dépasse le risque au vu
        des expériences passées. » Cette méthode est cette phrase.

        Retourne une fraction dans [0, 1[ : la part de son vécu que l'agent a trouvée
        bénéfique. `PRUDENCE_NAISSANCE` (a priori de Laplace, une observation fictive de
        prudence) donne un sens à la fraction quand rien n'a encore été vécu, et garantit
        qu'elle reste strictement inférieure à 1 — un agent ne peut jamais devenir
        certain au point de faire taire son réflexe.
        """
        total = self.vecu_okay + self.vecu_danger + PRUDENCE_NAISSANCE
        return self.vecu_okay / total

    def nourrir_vecu_journee(self, recompenses):
        """v41.0 — LE VÉCU SE COMPTE EN SAILLANCES, PAS EN MOYENNE.

        ══ Ce que la v40.0-fix1 faisait, et pourquoi c'était faux ══

        La version précédente prenait la MOYENNE signée des 400 ticks de la journée. Le
        raisonnement était juste (« l'unité est la journée, pas le tick ») mais l'opérateur
        ne l'était pas : moyenner revient à demander « comment s'est passée la journée EN
        MOYENNE ? », or une victoire n'est pas une propriété moyenne d'une journée. C'est
        un ÉVÉNEMENT.

        Mesure du benchmark « C1 pur » (3 graines × 2000 jours, 14/08/2026), journée type
        de g11 reconstituée depuis les logs :

            r_bio cumulé sur 400 ticks .............. −2,30
            victoires (0,46/jour × 1,0) ............. +0,46
            ─────────────────────────────────────────────────
            somme de la journée ..................... −1,84
            ÷ 400 ticks ............................. −0,004593
            ÷ référence de choc (0,208) ............. −0,0221

            → apport OKAY   = 0,0000   ← UN JOUR AVEC VICTOIRE
            → apport DANGER = 0,0221

        Le point d'équilibre prédit par ce modèle donne f = 0,0028 ; la mesure sur le run
        affichait **0,003**. Le modèle reproduisait l'observation au millième : la cause
        était établie sans ambiguïté.

        Formulation utilisateur : « en moyennant 399 ticks d'effort continu avec 1 tick de
        victoire, on forçait l'algorithme à conclure que VIVRE EST UNE PUNITION. »

        C'était exact. Le coût métabolique (`r_bio`, une DÉRIVÉE de déficit, donc
        structurellement négative dès que les jauges dérivent vers zéro) est présent à
        CHAQUE tick, tandis que la victoire n'occupe qu'UN tick. La moyenne noyait
        systématiquement le succès sous le coût d'exister.

        ══ Ce que la v41.0 fait ══

        Deux voies distinctes, comme en neurobiologie — c'est la correction demandée :

          • DOPAMINE PHASIQUE (les pics) : le succès s'inscrit par SOMME des saillances
            positives. Une victoire à +1,0 n'est plus divisée par 400. Elle compte pour ce
            qu'elle est : un accomplissement.

                vecu_okay += Σ max(0, r − 0) / échelle

          • ALERTE VISCÉRALE (les creux) : le danger s'inscrit par somme des saillances
            NÉGATIVES, selon la même règle. Le coût de fonctionnement ordinaire, réparti en
            micro-négatifs sur des centaines de ticks, ne pèse plus qu'à proportion de sa
            saillance réelle — il ne peut plus, par accumulation, écraser un événement.

        La flottaison (le zéro) et l'échelle (l'unité) sont TOUTES DEUX dérivées de ce que
        l'agent vit — jamais posées. La borne finale reste ±1 par journée, ce qui préserve
        l'acquis v40.0-fix1 : **une journée ne peut pas valoir plus qu'une journée**. Sans
        cette borne, sommer 400 ticks reproduirait exactement le défaut inverse (f à 0,906
        en une nuit) que fix1 avait corrigé.
        """
        valeurs = [float(r) for r in (recompenses or ())]

        # L'oubli court TOUJOURS, y compris une journée sans le moindre retour : c'est ce
        # qui permet à un monde durablement muet de recalibrer l'agent. Écrit avant tout
        # apport, donc sans avoir à distinguer les deux cas.
        self.vecu_okay *= OUBLI_OKAY
        self.vecu_danger *= OUBLI_DANGER

        # --- LA LIGNE DE FLOTTAISON DU JOUR (v41.0) ---
        #
        # La médiane des |r| de la journée EST le coût du tick ordinaire de cette
        # journée-là : rien n'est déclaré, la référence naît de l'expérience vécue. Le
        # `or [0.0]` couvre la journée vide sans branche de garde (median([]) lèverait).
        amplitudes = sorted(abs(v) for v in valeurs) or [0.0]
        milieu = len(amplitudes) // 2
        # Médiane sans dépendance externe, valide pour les deux parités.
        flottaison_jour = (amplitudes[milieu] + amplitudes[~milieu]) / 2.0

        # LE CLIQUET : montée rapide, descente `FREIN_DESCENTE_FLOTTAISON` fois plus lente.
        # `max(delta, 0)` et `min(delta, 0)` séparent les deux régimes sans `if` — même
        # écriture que le cliquet de `reference_choc_dopamine` (v37.1-fix1). Le premier
        # jour, `flottaison_metabolique` vaut None (aucune donnée) : on l'initialise sur la
        # mesure du jour. C'est une garde technique, pas un seuil — elle distingue
        # « jamais mesuré » de « mesuré à zéro », distinction que l'arithmétique ne peut
        # pas porter.
        if self.flottaison_metabolique is None:
            self.flottaison_metabolique = flottaison_jour
        else:
            delta = flottaison_jour - self.flottaison_metabolique
            montee = (1.0 - INERTIE_FLOTTAISON) * max(delta, 0.0)
            descente = (1.0 - INERTIE_FLOTTAISON) / FREIN_DESCENTE_FLOTTAISON * min(delta, 0.0)
            self.flottaison_metabolique += montee + descente

        flottaison = self.flottaison_metabolique

        # L'échelle qui juge « fort » ou « faible » est celle de l'agent lui-même, jamais
        # une constante : même principe que `reference_choc_dopamine` (v37.1), dont on
        # réutilise directement la valeur quand elle existe.
        echelle = max(self.reference_choc_dopamine or 0.0, 1e-3)

        # LE TRI DU SIGNE SANS BRANCHE, appliqué TICK PAR TICK avant sommation. `if r > 0`
        # bifurquerait sur le signe ; ici les deux parts sont calculées arithmétiquement et
        # l'une des deux vaut exactement 0 pour chaque tick :
        #     part⁺ = (|x| + x)/2      part⁻ = (|x| − x)/2
        # L'EXCÉDENT au-dessus de la flottaison — `max(|v| − flottaison, 0)` — est ce qui
        # transforme un tick en événement : un pas qui coûte le prix ordinaire de la vie
        # contribue EXACTEMENT 0 aux deux réservoirs. C'est la traduction directe de « un
        # pas qui consomme −0,02 de satiété est un pas neutre ».
        # Une journée vide donne deux sommes nulles — le cas dégénéré est absorbé par
        # l'arithmétique (`sum([]) == 0`) au lieu d'être intercepté par une garde.
        excedents = [(v, max(abs(v) - flottaison, 0.0)) for v in valeurs]
        saillance_positive = sum(e * (abs(v) + v) / (2.0 * abs(v) + 1e-12)
                                 for v, e in excedents)
        saillance_negative = sum(e * (abs(v) - v) / (2.0 * abs(v) + 1e-12)
                                 for v, e in excedents)

        # La borne à 1,0 par journée et par réservoir préserve l'invariant v40.0-fix1 :
        # une journée vécue apporte AU PLUS un point de vécu. Elle s'applique après
        # sommation, donc une journée à trois victoires sature comme une journée à une
        # seule — c'est voulu : ce qui doit croître avec l'expérience, c'est le NOMBRE de
        # journées réussies, pas l'intensité d'une seule.
        self.vecu_okay += min(1.0, saillance_positive / echelle)
        self.vecu_danger += min(1.0, saillance_negative / echelle)

        # Télémétrie (leçon v29.1 : une mécanique non instrumentée est indémontrable).
        self.mesure_flottaison = {
            "flottaison": flottaison,
            "flottaison_jour": flottaison_jour,
            "saillance_positive": saillance_positive,
            "saillance_negative": saillance_negative,
        }

    def _reset_optimizer(self):
        params = [p for p in self.parameters() if p.requires_grad]
        self.optimizer = torch.optim.Adam(params, lr=self.lr)

    def contexte_vide(self, batch=1):
        return torch.zeros(batch, self.dim_bus, device=self.actions_eye.device)

    def _tronc_cerebral(self, obs, memoire_precedente, obs_auditive=None):
        """Tronc cérébral commun, désormais multimodal (v22.0) : la vision ET l'audio
        se fondent dans le MÊME bus latent, par simple somme (pas de concaténation) —
        c'est ce qui réalise concrètement "voir et entendre en même temps" dans un seul
        espace cognitif (décision utilisateur : cerveau unifié, pas de mode isolé).
        `obs_auditive=None` (silence) est le cas par défaut, rétrocompatible avec tout
        appelant qui ne fournit pas de son (ex: rever(), qui ne rejoue pour l'instant que
        la mémoire visuelle) — le bus se réduit alors exactement au comportement d'avant
        v22.0."""
        stimulus_visuel = F.relu(self.porte_visuelle(obs))
        if obs_auditive is not None:
            stimulus_auditif = F.relu(self.porte_auditive(obs_auditive))
            bus_latent = stimulus_visuel + stimulus_auditif
        else:
            # --- v39.0 : LE SILENCE N'EST PAS L'ABSENCE ---
            #
            # 🔴 CE QUE ÇA CORRIGE (mesuré) : `porte_auditive` n'a PAS de biais, donc
            #
            #     relu(porte_auditive(zeros)).norm() == 0.000000   (exact)
            #
            # Autrement dit, un silence PARFAIT et une oreille ABSENTE produisaient
            # rigoureusement le même bus latent (6.3323 dans les deux cas, écart 0.0000).
            # Le cerveau ne pouvait pas les distinguer : rien, nulle part, ne lui disait
            # si le canal auditif existait et se taisait, ou n'existait pas du tout.
            #
            # C'est la remarque de l'utilisateur, et elle vise juste :
            #
            #     « Le silence n'est pas 0. Le silence, c'est quand il y a presque plus
            #       rien à établir. »
            #
            # Un silence est une INFORMATION — « j'écoute et je n'entends rien » n'est pas
            # « je n'ai pas d'oreilles ». Le rêve (`rever()`), qui ne rejoue que la
            # mémoire visuelle, était dans le même cas : il présentait au cerveau un monde
            # sourd indiscernable d'un monde muet.
            #
            # LE CORRECTIF, minimal et neutre : le canal auditif reste présent, alimenté
            # par un vecteur nul. Comme la couche est sans biais, la contribution reste
            # EXACTEMENT nulle — le comportement numérique est donc **bit-identique** à
            # l'ancien, aucun `.brain` n'est affecté, aucune échelle ne bouge.
            #
            # ⚠️ Ce que ce correctif fait vraiment : il rend le défaut EXPLICITE et
            # localisé, au lieu de le laisser implicite dans une branche `else`. La vraie
            # levée du défaut demande un BIT DE PRÉSENCE dans le vecteur bio (« l'ouïe
            # est-elle active ce tick ? »), qui change la dimension du vecteur et exige
            # une greffe `persistance` — donc un chantier à part entière, à mesurer.
            # Le noter ici sans le faire est délibéré : v29.0 avait livré cinq sens sans
            # télémétrie, on ne recommence pas en livrant une dimension sans greffe.
            silence = torch.zeros(obs.shape[0], self.porte_auditive.in_features,
                                  device=obs.device, dtype=obs.dtype)
            bus_latent = stimulus_visuel + F.relu(self.porte_auditive(silence))
        fusion_temporelle = torch.cat([bus_latent, memoire_precedente], dim=-1)
        memoire_actuelle = F.relu(self.hippocampe(fusion_temporelle))
        pensee = F.relu(self.analyseur(memoire_actuelle))
        return bus_latent, memoire_actuelle, pensee

    def lecture_episodique(self, pensee, contexte):
        x = pensee
        for _ in range(2):
            x = F.relu(self.fusion_memoire(torch.cat([x, contexte], dim=-1)))
        return x

    def _predire_bus(self, pensee, actions_onehot):
        return self.generateur_attente(torch.cat([actions_onehot, pensee], dim=-1))

    def _predire_bus_audio(self, pensee, actions_onehot):
        """Tête JEPA auditive séparée (v22.1) — miroir exact de _predire_bus mais via
        generateur_attente_audio, pour que la perte audio ne pollue jamais le gradient
        de la tête visuelle (voir perte_jepa)."""
        return self.generateur_attente_audio(torch.cat([actions_onehot, pensee], dim=-1))

    @torch.no_grad()
    def simuler_futur_et_planifier(self, pensee, memoire_actuelle, horizons=(1, 3, 7),
                                    gamma_planif=0.9, vecteur_bio=None):
        """Rollout imaginé NON-LINÉAIRE, à sauts temporels exponentiels (ex: t+1, t+3, t+7)
        plutôt qu'une chaîne pas-à-pas stricte t+1 → t+2 → t+3.

        Le PREMIER horizon (toujours le plus petit, ex: 1) branche sur les 7 actions
        réelles — c'est la décision qu'on évalue maintenant. Chaque horizon SUIVANT ne
        rebranche jamais sur 7 nouvelles actions : il poursuit le déroulement en suivant
        le réflexe du réseau (argmax de la tête motrice) pour COMBLER l'écart de ticks
        avec l'horizon précédent, puis évalue la valeur à ce point d'arrivée. Cela
        maintient la même complexité linéaire O(7 × somme(écarts)) que l'ancien rollout
        pas-à-pas — jamais d'explosion combinatoire en 7^N — tout en donnant au Système 2
        une vision de tendance à moyen terme (utile sur les longs couloirs de MultiRoom /
        Doctorat) sans calculer chaque micro-état intermédiaire un par un pour la
        décision. La valeur finale est une somme actualisée par gamma_planif**horizon des
        valeurs évaluées à CHAQUE horizon (pas seulement le dernier) : un chemin qui
        traverse un bon état à t+3 compte, même si t+7 reste incertain.

        v28.0 (expérimental) : retourne désormais aussi `indecision_c2`, l'écart-type
        BRUT de `valeur_cumulee` calculé juste AVANT la normalisation ci-dessous — geste
        auparavant jeté (voir noyau.py historique) alors qu'il mesure exactement à quel
        point les 7 (ou 8) actions se valent aux yeux du Système 2. Un std proche de 0
        signifie "C2 n'a pas d'avis tranché" ; un std élevé signifie "C2 voit clairement
        une meilleure branche". Ce n'est PAS un déclencheur d'appel à C3 (décision
        utilisateur explicite : interroger C3 est un choix appris, pas un seuil) — c'est
        un simple contexte transmis dans RequeteC3.indecision_c2, et une métrique de
        télémétrie W&B."""
        A = self.num_actions
        pensee_branche = pensee.expand(A, -1)
        mem_branche = memoire_actuelle.expand(A, -1)

        valeur_cumulee = torch.zeros(1, A, device=pensee.device)
        horizons_tries = sorted(horizons)
        pas_precedent = 0

        for i, horizon in enumerate(horizons_tries):
            nombre_sauts = horizon - pas_precedent
            for saut in range(nombre_sauts):
                if i == 0 and saut == 0:
                    actions_pas = self.actions_eye  # les 7 (ou 8) choix réels, un par branche
                else:
                    choix = torch.argmax(self.tete_motrice(pensee_branche), dim=-1)
                    actions_pas = self.actions_eye[choix]  # continuation gourmande, 1 par branche

                futur_bus = F.relu(self._predire_bus(pensee_branche, actions_pas))
                futur_mem = F.relu(self.hippocampe(torch.cat([futur_bus, mem_branche], dim=-1)))
                futur_pensee = F.relu(self.analyseur(futur_mem))

                # --- v41.13 : LE CORPS SURVIT DANS LE FUTUR IMAGINÉ ---
                #
                # 🔴 CE QUE ÇA CORRIGE (mesuré le 16/08). `integrateur_bio` n'apparaissait
                # NULLE PART dans cette boucle : les 41 dims du vecteur bio (toucher,
                # odorat, goût, thermoception, pression, faim, soif) entraient UNE FOIS via
                # C1, puis C2 simulait 7 futurs × 7 sauts **sans jamais reprojeter un seul
                # sens**. Autrement dit : **C2 imaginait un monde sans corps.**
                #
                # Conséquence directe : C2 ne pouvait pas simuler « si j'avance je serai
                # collé au mur », « si je tourne l'odeur baissera », « si je continue la
                # chaleur montera ». Il ne délibérait que sur une projection visuelle.
                #
                # Cela unifie trois mesures qu'on lisait jusqu'ici séparément :
                #   - couper C2 change le score de 0,0 pt sur 6 niveaux (78 cellules) ;
                #   - C2 est 36 % PLUS GROS chez les agents qui échouent (scan 20 cerveaux) ;
                #   - 4 sens sur 6 sont ablatables sans aucun effet (H15).
                # Ce ne sont pas trois échecs indépendants : c'est le même câblage manquant
                # vu des deux bouts — les sens n'atteignent pas le modèle du monde, et le
                # modèle du monde simule un agent désincarné.
                #
                # LE GESTE EST MINIMAL, et c'est délibéré : on réutilise `integrateur_bio`,
                # la couche qui fait DÉJÀ exactement ce travail dans C1. Aucune tête
                # nouvelle, aucun paramètre ajouté, aucune constante. L'alternative
                # proposée (cinq têtes JEPA + cinq portes dédiées) ferait grossir de ~30 %
                # un cœur déjà 2,85× plus lourd qu'un PPO qui le bat — à mesurer seulement
                # SI ce câblage-ci produit un effet.
                #
                # ⚠️ LE VECTEUR BIO EST TENU CONSTANT sur tout le rollout. C'est une
                # approximation assumée et bornée : l'agent imagine « mon corps tel qu'il
                # est maintenant » projeté dans les futurs possibles. Prédire l'évolution
                # des sens exigerait précisément les têtes JEPA de l'étape 3 — c'est la
                # question suivante, pas celle-ci. Un corps figé reste infiniment plus
                # informatif qu'un corps absent.
                #
                # ⚠️ `vecteur_bio=None` ⇒ comportement **bit-identique** à la v41.12 : le
                # rêve (`rever()`) et tout appelant qui n'a pas de corps sous la main
                # retombent exactement sur l'ancien chemin, sans branche coûteuse.
                if vecteur_bio is not None:
                    futur_pensee = F.relu(self.integrateur_bio(
                        torch.cat([futur_pensee,
                                   vecteur_bio.expand(futur_pensee.shape[0], -1)], dim=-1)))

                pensee_branche, mem_branche = futur_pensee, futur_mem

            valeur_horizon = self.cortex_prefrontal(pensee_branche).view(1, A)
            valeur_cumulee = valeur_cumulee + (gamma_planif ** horizon) * valeur_horizon
            pas_precedent = horizon

        indecision_c2 = float(valeur_cumulee.std().item())

        # v37.0-fix — la normalisation est désormais INCONDITIONNELLE. L'ancien
        # `if std > 1e-6` laissait, en dessous du seuil, `valeur_cumulee` à son échelle
        # BRUTE (~1e-7), c'est-à-dire un C2 numériquement éteint qui disparaissait de la
        # fusion sans que rien ne le signale. Observé sur les runs de validation : des
        # journées entières à `C2=0.000` alternant avec des journées normales, selon que
        # le std passait ou non sous le seuil.
        #
        # Or « C2 hésite entre des branches très proches » ne veut pas dire « C2 n'a pas
        # d'avis » : la hiérarchie relative entre les 7 actions reste porteuse
        # d'information, et c'est précisément ce que la normalisation sert à extraire.
        # L'epsilon au dénominateur suffit à couvrir le cas dégénéré (std exactement nul,
        # 7 branches strictement identiques) sans jamais éteindre le module.
        valeur_cumulee = (valeur_cumulee - valeur_cumulee.mean()) / (valeur_cumulee.std() + 1e-8)

        # ⚠️ v37.0 — « L'ÉCHELLE DE C2 PORTE SA CONFIANCE » (Mesure 1) : IMPLÉMENTÉE,
        # MESURÉE, PUIS RETIRÉE. Traçabilité, pour que l'idée ne soit pas réintroduite sans
        # connaître les deux mesures qui l'ont écartée — c'est ici qu'elle aurait vécu.
        #
        # L'intention était juste : la normalisation ci-dessus efface la confiance de C2 (un
        # C2 sans avis et un C2 certain sortent tous deux à std=1 — mesuré : amplitude
        # 2,10 ± 0,02 IDENTIQUE sur trois cartes très différentes), alors que C1 garde son
        # échelle brute. Le rapport de force 1:18 était donc un artefact de la normalisation
        # d'un seul des deux termes, pas un choix d'architecture.
        #
        # Deux façons de réinjecter cette confiance ont été essayées, toutes deux ÉCHOUÉES :
        #
        #   1. Échelle ABSOLUE (`valeur * std_brut`) → ÉTEINT C2 (ratio tombé à 0,01×). Le
        #      std brut vaut ~0,0008 et ne varie que de 1,00× entre min et max sur 300
        #      ticks : il n'y a aucune confiance variable à réinjecter, parce que
        #      `cortex_prefrontal` est lui aussi érodé au plancher vital.
        #   2. Échelle RELATIVE (rapport à une moyenne glissante de son propre std) →
        #      SATURE. Mesuré sur 40 jours : `confiance = 2.0000` en permanence, collée au
        #      plafond, la moyenne glissante décroissant plus vite que le signal. Effet net :
        #      un facteur constant, donc rien.
        #
        # Conclusion : tant que `cortex_prefrontal` est au plancher, C2 n'a pas de confiance
        # variable à exprimer — il n'y a rien à réinjecter. Le déséquilibre se corrige côté
        # C1 (Mesure 2, gain à double sens) et par le déblocage réel des deux têtes
        # (correctifs myéline/plancher). À reconsidérer seulement si un run montre
        # `indecision_c2` réellement variable.
        return valeur_cumulee, indecision_c2

    def integrer_bio(self, pensee, vecteur_bio):
        """Fusionne la pensée avec l'état viscéral courant (v18.0) — voir
        BiologicalHomeostasisEngine. Appliqué UNE SEULE FOIS avant la prise de décision
        (tête motrice + rollout mental), jamais réappliqué à chaque pas du rollout
        imaginé : sur un horizon court (7 ticks), les jauges bougent trop peu pour que
        réintégrer le bio à chaque pas simulé change la décision, et cela évite de
        complexifier le rollout ou generer_attente_reelle (qui n'a pas besoin de savoir
        que l'agent a faim pour prédire l'état visuel suivant)."""
        return F.relu(self.integrateur_bio(torch.cat([pensee, vecteur_bio], dim=-1)))

    def _executer_c1_reflexe(self, obs_visuelle, memoire_precedente, contexte_episodique,
                              vecteur_bio, obs_auditive=None):
        """C1 — LE CERVEAU AUTOMATIQUE & RÉFLEXE (v29.0, restructuration explicite).

        Tout ce que le cerveau fait à coût quasi nul, avant toute délibération :

        1. COMPRESSION du flux des 5 sens. La vue et l'ouïe (les deux sens gourmands)
           passent par leur porte synaptique dédiée et se somment dans `bus_latent`
           (`_tronc_cerebral`) ; le toucher, l'odorat et le goût (les 3 sens faibles à
           moyens, v29.0) arrivent déjà normalisés par `bus_sensoriel.BusSensoriel` dans
           la queue de `vecteur_bio`. C'est ici que le monde devient un vecteur compact.
        2. CONTEXTE ÉPISODIQUE : `lecture_episodique` mêle la pensée courante à la
           moyenne des états latents récents de l'épisode.
        3. INTÉGRATION VISCÉRALE : `integrer_bio` fusionne cette pensée avec l'état
           biologique (jauges, quête active, rappel spatial, quête vocale, et depuis la
           v29.0 les sens tactiles/chimiques).
        4. RÉFLEXE MOTEUR IMMÉDIAT : `tete_motrice` produit ses logits directement depuis
           `pensee_bio`, en latence zéro et sans jamais dérouler la moindre simulation.

        Retourne le tuple (bus_latent, memoire_actuelle, pensee_enrichie, pensee_bio,
        logits_instinct) — `pensee_bio` est l'état COMPRESSÉ qui sera transmis à C2, qui
        ne voit jamais autre chose que ça (jamais l'observation brute)."""
        bus_latent, memoire_actuelle, pensee = self._tronc_cerebral(
            obs_visuelle, memoire_precedente.detach(), obs_auditive=obs_auditive
        )
        pensee_enrichie = self.lecture_episodique(pensee, contexte_episodique)

        # v41.34 — le tronc perceptif est-il coupé pour rien ? Voir TRONC_PERCEPTIF_DETACHE.
        # `True` reproduit bit à bit tout ce qui précède ; `False` laisse l'acteur et le
        # critique rétropropager jusqu'à `porte_visuelle`.
        pensee_detachee = (pensee_enrichie.detach() if TRONC_PERCEPTIF_DETACHE
                           else pensee_enrichie)
        pensee_bio = self.integrer_bio(pensee_detachee, vecteur_bio)
        logits_instinct = self.tete_motrice(pensee_bio)
        return bus_latent, memoire_actuelle, pensee_enrichie, pensee_bio, logits_instinct

    def _solliciter_c2_neocortex(self, pensee_bio, memoire_actuelle,
                                  horizons_planification=(1, 3, 7), gamma_planif=0.9,
                                  vecteur_bio=None):
        """C2 — LE NÉO-CORTEX (v29.0, restructuration explicite).

        Le moteur analytique lourd : déroule la simulation mentale multi-horizons via le
        modèle du monde JEPA (`simuler_futur_et_planifier`, qui appelle `_predire_bus`).
        Il ne reçoit QUE l'état déjà compressé par C1 (`pensee_bio`) — jamais les pixels,
        jamais le MFCC brut, jamais l'environnement.

        Retourne (valeurs_simulees, indecision_c2), exactement comme avant la v29.0.
        Sollicité à chaque tick (voir la note de restructuration pure en tête de section) :
        cette méthode existe pour NOMMER la frontière C1/C2, pas pour la conditionner."""
        return self.simuler_futur_et_planifier(
            pensee_bio, memoire_actuelle.detach(),
            horizons=horizons_planification, gamma_planif=gamma_planif,
            vecteur_bio=vecteur_bio
        )

    def penser(self, obs_visuelle, memoire_precedente, contexte_episodique, vecteur_bio,
              force_planification=0.5, horizons_planification=(1, 3, 7), gamma_planif=0.9,
              obs_auditive=None, plugs_c3_disponibles=None, vigueur=1.0):
        """La cascade complète C1 → C2 (→ C3), tick par tick.

        v29.0 (expérimental) — le corps de cette méthode est désormais l'ARBITRAGE seul :
        C1 (`_executer_c1_reflexe`) produit le réflexe, C2 (`_solliciter_c2_neocortex`)
        produit son avis délibéré, et la fusion `logits_instinct + valeurs * force` reste
        strictement identique à la v28.0 — seule la lisibilité de la frontière change.

        v28.0 (expérimental) — `plugs_c3_disponibles` : liste des noms de plugs
        actuellement disponibles sur `self.port_c3` (voir PortC3.plugs_disponibles),
        ou None/liste vide si aucun greffon n'est branché. C'est la SEULE chose que
        `penser()` sait de C3 : jamais l'objet PortC3 lui-même, jamais un plug — juste
        "quelqu'un répond-il en ce moment ?". Sans plug disponible, l'action
        ACTION_DEMANDER est masquée à -inf : le comportement redevient bit-identique
        à la v27.6 (7 actions, aucune trace de C3 dans les logits)."""
        # --- C1 : le réflexe, à coût quasi nul ---
        (bus_latent, memoire_actuelle, pensee_enrichie,
         pensee_bio, logits_instinct) = self._executer_c1_reflexe(
            obs_visuelle, memoire_precedente, contexte_episodique, vecteur_bio,
            obs_auditive=obs_auditive
        )

        # --- C2 : la délibération lourde, sur l'état déjà compressé par C1 ---
        # v41.13 — le corps accompagne C2 dans sa simulation. `.detach()` : le rollout ne
        # doit jamais renvoyer de gradient dans la perception du tick courant — même
        # discipline que `memoire_actuelle.detach()` juste à côté.
        _corps_c2 = (vecteur_bio.detach() if (CORPS_DANS_ROLLOUT_ACTIF
                                              and vecteur_bio is not None) else None)
        valeurs_simulees, indecision_c2 = self._solliciter_c2_neocortex(
            pensee_bio, memoire_actuelle,
            horizons_planification=horizons_planification, gamma_planif=gamma_planif,
            vecteur_bio=_corps_c2
        )

        # --- v41.2 : LE SEUIL NON LINÉAIRE DE L'ÉNERGIE ---
        #
        # `vigueur = énergie ** κ` (voir BiologicalHomeostasisEngine.vigueur). C2 la subit
        # DEUX FOIS — une fois ici sur sa force, une fois via le gain de C1 qui suit la même
        # force — donc la délibération s'éteint en `vigueur²` quand le réflexe s'éteint en
        # `vigueur`. À énergie 0.5 : C1 garde 25 % de sa voix, C2 seulement 6 % (mesuré).
        # C'est biologiquement juste — un organisme épuisé cesse de simuler l'avenir bien
        # avant de cesser de marcher — et ça produit gratuitement une hiérarchie de survie.
        #
        # ⚠️ Ce n'est PAS le court-circuit C1→C2 refusé en v29.0, ni un déclenchement sur
        # seuil d'incertitude (refusé trois fois). C2 est TOUJOURS sollicité, à chaque tick,
        # sans aucune condition — l'appel ci-dessus a déjà eu lieu. Seul son POIDS dans la
        # fusion varie, continûment. Il n'y a pas de branche : il y a un facteur.
        # v41.16 — LE BRAIN-SPARING S'APPLIQUE AUSSI ICI, et c'est ce qui rend le geste
        # NEUTRE POUR L'ARBITRAGE. La v41.2 éteignait C2 en `vigueur²` (une fois ici, une
        # fois via le gain de C1) au nom d'une hiérarchie de survie. Or la mesure montre
        # que les deux voix subissaient le MÊME facteur : la part de C2 dans la décision
        # reste à 61,3 % de vigueur 1,00 à 0,30 — C2 n'était donc pas « sacrifié en
        # premier », il coulait avec C1. Ce que la vigueur détruisait n'était pas la
        # hiérarchie entre les deux voix, c'était la NETTETÉ de leur somme.
        #
        # Retirer le facteur des DEUX côtés laisse donc l'arbitrage rigoureusement
        # identique, et rend à la décision son relief. La délibération redevient ce que la
        # biologie en fait : le dernier organe qu'on éteint, pas le premier.
        #
        # ⚠️ La vigueur n'est pas neutralisée pour autant — elle module toujours le coût
        # métabolique des actions, le déficit, la plasticité nocturne et l'envie de vivre.
        # Le corps ralentit toujours ; seul l'esprit reste allumé.
        if not BRAIN_SPARING_ACTIF:
            force_planification = force_planification * vigueur

        # --- v37.0 : LA VOIX DE C1 EST RENDUE AUDIBLE (Mesure 2) ---
        #
        # Une couche collée au plancher vital est vivante mais MUETTE : `tete_motrice` à
        # 10,00 % de sa norme de naissance produit des logits d'amplitude ~0,1, contre ~1,8
        # pour C2 après pondération. C1 n'était donc pas ignoré parce qu'il avait tort,
        # mais parce qu'il était PETIT — l'érosion décidait du rapport de force à la place
        # de l'arbitrage.
        #
        # On réamplifie donc C1 à échelle constante quand son amplitude tombe sous
        # VIGUEUR_MIN_C1. Le geste est délibérément minimal : c'est un facteur SCALAIRE,
        # donc les rapports entre les 7 logits sont strictement préservés. On rend à C1 sa
        # voix, jamais son opinion — un C1 qui vote mal continuera de voter mal, mais il
        # sera entendu, donc corrigible par le gradient (voir Mesure 3).
        #
        # Pourquoi pas simplement baisser force_planification : ce serait remplacer une
        # constante arbitraire par une autre, sans traiter la cause (l'asymétrie d'échelle),
        # et cela casserait C2 sur un futur cerveau sain dont C1 serait fort. Ici, un C1
        # vigoureux (amplitude > VIGUEUR_MIN_C1) n'est PAS touché : le facteur vaut 1.0.
        #
        # v37.0-fix — LE GAIN EST À DOUBLE SENS. La première version ne faisait
        # qu'amplifier (`min=1.0`), au motif qu'un C1 érodé ne pouvait qu'être trop faible.
        # Mesuré sur 30 jours : une fois les têtes débloquées (correctifs myéline +
        # plancher), la distillation renforce C1 bien plus vite que C2 ne progresse, et le
        # ratio s'est INVERSÉ à 0,21-0,38× — C1 écrasant C2 d'un facteur 3 à 5, exactement
        # le mode d'échec que ce chantier s'était engagé à surveiller.
        #
        # Le gain ramène donc l'amplitude de C1 vers `VIGUEUR_MIN_C1` dans les DEUX sens :
        # il relève un réflexe étouffé par l'érosion, et tempère un réflexe devenu tonitruant.
        # Ce n'est toujours qu'un facteur SCALAIRE — l'opinion de C1 (les rapports entre ses
        # 7 logits) reste rigoureusement intacte, seul son volume est réglé. Les bornes
        # empêchent l'un ou l'autre module de disparaître de l'arbitrage.
        #
        # v40.0 — la cible de vigueur suit `force_planification`, qui n'est plus une
        # constante mais la confiance que l'agent a GAGNÉE dans sa propre planification
        # (voir `vigueur_min_c1` et `PRUDENCE_NAISSANCE`). Un agent inexpérimenté a f≈0 :
        # la cible tend vers 0, le gain vers sa borne basse, et C1 domine sans qu'aucune
        # règle ne l'ait décrété. « C1 a toujours raison, sauf si… » est ici, en une ligne.
        amplitude_c1 = (logits_instinct.max(dim=-1, keepdim=True).values
                        - logits_instinct.min(dim=-1, keepdim=True).values)
        gain_c1 = torch.clamp(vigueur_min_c1(force_planification) / (amplitude_c1 + 1e-8),
                              min=GAIN_C1_MIN, max=GAIN_C1_MAX)
        # v40.1 — trace de ce que C1 a CONSTRUIT (amplitude brute, avant gain). Lue une
        # fois par nuit par `reviser_envie_de_vivre` : c'est la moitié « expérience de C1 »
        # de la lucidité. Purement observationnel, aucune influence sur ce tick.
        with torch.no_grad():
            self.amplitude_c1_recente = float(amplitude_c1.mean().item())
        # --- v41.16 : LE BRAIN-SPARING — LA VIGUEUR MODULE LE CORPS, PAS LA LUCIDITÉ ---
        #
        # 🔴 CE QUE ÇA CORRIGE (mesuré le 17/08). La v41.2 multipliait les LOGITS par la
        # vigueur, et son commentaire promettait : « le plancher garantit qu'il reste
        # COHÉRENT — sans lui l'action deviendrait ALÉATOIRE ». La mesure dit l'inverse
        # exact, **plancher compris** :
        #
        #     vigueur 1.00 → amplitude 1.219 → proba de l'action favorite 0.231
        #     vigueur 0.15 → amplitude 0.191 → proba de l'action favorite 0.158
        #                                      entropie 0.999  (1/7 = 0.143 = HASARD PUR)
        #
        # Multiplier des logits par 0,15 ne rend pas la décision « moins affirmée » : ça
        # l'aplatit vers l'uniforme, parce que `softmax` est invariante par translation
        # mais PAS par échelle. Diviser l'écart entre les 7 logits, c'est effacer la
        # préférence. **L'agent affamé ne devenait pas prudent : il devenait aléatoire.**
        # Le plancher n'y change rien — il fixe seulement le niveau du hasard.
        #
        # Et c'est le régime NORMAL de cet agent : énergie moyenne 0,041 sur les runs
        # longs, `400/400 ticks en basse énergie` dès le premier jour. Toute sa vie, il a
        # donc décidé au hasard.
        #
        # LA LOI DU VIVANT (formulation utilisateur, 17/08) : *« en pénurie sévère le corps
        # ne coupe jamais le cerveau en premier — il sacrifie la périphérie pour maintenir
        # le métabolisme cérébral. Un animal affamé qui perd sa motricité peut survivre
        # immobile ; un animal qui perd sa lucidité est condamné. »*
        #
        # LE CORRECTIF, minimal : la vigueur cesse de multiplier les logits. Elle continue
        # de moduler tout le reste — `force_planification`, le déficit, la plasticité, le
        # coût des actions — donc le corps ralentit toujours quand l'énergie manque. Seule
        # la NETTETÉ de la décision est préservée : un organisme épuisé décide moins vite
        # et bouge moins, il ne décide pas plus mal.
        #
        # ⚠️ Ce n'est PAS « rendre C2 plus fort ». Le rapport C1/C2 est rigoureusement
        # inchangé (61,3 % pour C2 avant comme après) : les deux voix étaient multipliées
        # par le même facteur, le retirer des deux ne déplace pas l'arbitrage d'un iota.
        # Ce qui change est la SÉPARATION des 7 actions, donc la capacité à choisir.
        #
        # ⚠️ Aucun seuil, aucune branche : on retire un facteur, on n'en ajoute pas.
        voix_c1 = logits_instinct * gain_c1 * (1.0 if BRAIN_SPARING_ACTIF else vigueur)

        # Télémétrie de l'arbitrage (v37.0) — déposée sur le module plutôt que retournée,
        # pour ne pas élargir un tuple de retour déjà consommé en plusieurs points du
        # fichier. Purement observationnelle : rien ici n'influence la décision.
        with torch.no_grad():
            voix_c2_ponderee = valeurs_simulees * force_planification
            self.mesure_arbitrage = {
                "amplitude_c1": float(amplitude_c1.mean().item()),
                "amplitude_c2": float((voix_c2_ponderee.max(dim=-1).values
                                       - voix_c2_ponderee.min(dim=-1).values).mean().item()),
                "gain_c1": float(gain_c1.mean().item()),
                # v39.2-fix — L'ACCORD EST UNE FRACTION, PLUS UN « TOUT OU RIEN ».
                #
                # L'ancienne version fermait sur `.all()` : l'accord ne valait 1 que si les
                # 400 lignes du batch votaient la même action. Une seule divergence écrivait
                # 0 — le résultat était donc quasiment garanti à 0 % PAR CONSTRUCTION, quel
                # que soit l'état réel du cerveau. Mesuré le 14/08 : les logs de nuit
                # affichaient 0,0 % sur six runs longs, là où le banc d'ablation, qui compte
                # tick par tick, trouvait 26 à 31 % sur le MÊME cerveau.
                #
                # Ce 0 % circulait dans le projet depuis le chantier v37 et faisait paraître
                # le désaccord total (100 %) alors qu'il est de ~70 %. C'est un défaut de
                # MESURE, pas de cognition : rien dans la décision ne change ici.
                "accord": float((logits_instinct.argmax(dim=-1)
                                 == valeurs_simulees.argmax(dim=-1)).float().mean().item()),
                # --- v41.14 : QUI VOTE QUOI (le témoin qui manquait à `accord`) ---
                #
                # 🔴 CE QUE ÇA CORRIGE (mesuré le 17/08 sur la campagne v41.13).
                # `accord` compare deux argmax. Deux voix qui votent CHACUNE une action
                # CONSTANTE s'accordent donc à 100 % sans qu'aucune délibération n'ait eu
                # lieu. Observé, témoin g1/g3 : `accord 100.0%` avec `C2=0.370` figé
                # pendant que C1 oscillait de 1,70 à 2,72.
                #
                # Pire : le témoin (C2 SANS corps) affichait un accord PLUS HAUT que la
                # variante (84,8/96,8/100 % contre 61,8/78,2/58,2 %). Lu naïvement, le
                # correctif « dégradait » l'entente — alors qu'il faisait exactement ce
                # qu'on attend de lui : donner à C2 un avis DISTINCT.
                #
                # Ces deux clés lèvent l'ambiguïté en enregistrant l'action votée par
                # chaque voix. L'appelant en dérive l'entropie sur la journée : une
                # entropie nulle = une voix figée, donc un accord dénué de sens.
                #
                # ⚠️ Télémétrie PURE. Aucune de ces valeurs n'est relue par la décision,
                # le gradient ou la dopamine — le run reste bit-identique.
                "vote_c1": int(logits_instinct.argmax(dim=-1).view(-1)[0].item()),
                "vote_c2": int(valeurs_simulees.argmax(dim=-1).view(-1)[0].item()),
            }

        # --- Arbitrage C1 + C2 (structure inchangée depuis la v13.0) ---
        # `force_planification` retrouve enfin le rôle qu'elle prétendait tenir : arbitrer
        # entre deux voix comparables, au lieu de multiplier la seule qui avait une échelle.
        logits_finaux = voix_c1 + (valeurs_simulees * force_planification)

        # Masquage PERMANENT de la 8ème action (v30.0, décision utilisateur explicite).
        #
        # En v28.0/v29.x, ACTION_DEMANDER était une action apprise, démasquée dès qu'un
        # plug C3 était disponible : C3 était alors un canal de DÉCISION. Depuis la v30.0,
        # C3 est un canal de PERCEPTION (l'Exo-Sens, voir bus_sensoriel.percevoir_exogene)
        # — l'agent ne « demande » plus rien, il perçoit en continu. Cette action n'a donc
        # plus de rôle et reste masquée QUELLE QUE SOIT la disponibilité du bus.
        #
        # Pourquoi masquer plutôt que revenir à num_actions=7 : 4 des .brain du dépôt sont
        # déjà à 8 actions (dont le cerveau actif du Cursus, bus 48). Repasser à 7
        # imposerait une greffe INVERSE qui JETTERAIT des poids appris — la première
        # violation de la règle « greffe par recopie, jamais par exclusion » (CLAUDE.md).
        # Ici, la colonne 8 devient simplement dormante : jamais échantillonnée, ses poids
        # conservés intacts, réactivable plus tard sans nouvelle greffe si un usage se
        # présente. Le comportement moteur redevient strictement équivalent à 7 actions.
        if self.num_actions > NUM_ACTIONS_BASE:
            logits_finaux = logits_finaux.clone()
            logits_finaux[..., ACTION_DEMANDER] = float("-inf")

        # v41.32 — detach asymétrique : C2 lit le corps sans le sculpter (voir
        # DETACH_C2_ASYMETRIQUE). `pensee_bio` reste identique en VALEUR — seul le
        # chemin de gradient change, donc le comportement du tick est inchangé.
        _bio_pour_c2 = pensee_bio.detach() if DETACH_C2_ASYMETRIQUE else pensee_bio
        valeur_etat_courant = self.cortex_prefrontal(_bio_pour_c2)
        # La BOUCHE (v22.0) : produit ses paramètres vocaux à CHAQUE pensée, comme la
        # tête motrice produit ses logits d'action — l'agent peut bouger ET vocaliser
        # simultanément (décision utilisateur), même quand aucune leçon n'est active
        # (le tuteur choisit alors d'ignorer/ne pas jouer ce son, voir traiter_tick).
        # sigmoid borne dans [0,1], démappé vers les unités physiques par
        # SynthetiseurFormants.parametres_depuis_vecteur (hemisphere_audio.py).
        parametres_vocaux = torch.sigmoid(self.tete_vocale(pensee_bio))
        # Tête de routage C3 (v28.0, Chantier 2b) : "vers quel plug émettre" — calculée
        # systématiquement (coût négligeable), mais n'est consommée par traiter_tick
        # que si l'action 7 est effectivement échantillonnée. Softmax appliqué côté
        # appelant, une fois les plugs disponibles connus (masquage des indices
        # correspondant à des plugs absents), pas ici — cette méthode ne connaît pas
        # la liste des plugs, seulement leur disponibilité globale.
        logits_routage = self.tete_requete(pensee_bio)

        # --- v37.0 : LE RÉFLEXE APPREND DU NÉO-CORTEX (Mesure 3) ---
        #
        # Sans cette branche, `tete_motrice` ne reçoit de gradient QUE par REINFORCE,
        # c'est-à-dire uniquement quand l'agent gagne. Mesuré sur le cerveau V36 après 600
        # jours : `myeline_M = 0.000000` EXACT sur tete_motrice ET cortex_prefrontal — les
        # deux têtes de décision, et elles seules avec integrateur_bio. Les autres couches
        # tournent à ~0,004. Le cercle est fermé : il faut gagner pour myéliniser, et ses
        # poids pour gagner. Le plancher vital coupe la chute mais ne relance rien.
        #
        # On ouvre donc un second canal, qui ne dépend d'aucune victoire : C1 est tiré vers
        # ce que C2 a jugé meilleur APRÈS délibération. C'est de l'auto-distillation, et
        # c'est exactement le rapport biologique visé par le projet — C2 fait émerger
        # l'intelligence, C1 automatise ce qui est acquis pour le rejouer à coût nul.
        #
        # RIEN N'EST EXPLIQUÉ EN DUR : la cible n'est pas une table « action 2 = bien »,
        # c'est la sortie d'un module du cerveau lui-même, détachée du graphe. Le signal
        # vient de la cohérence interne entre les deux voix, jamais d'une connaissance
        # injectée de l'extérieur. Si C2 se trompe, C1 apprend l'erreur de C2 — et c'est
        # REINFORCE qui les corrigera tous les deux.
        #
        # `.detach()` sur la cible est ESSENTIEL : sans lui, le gradient remonterait dans
        # le rollout mental et C2 apprendrait à se rendre prévisible plutôt que juste.
        # v37.1 — LA DISTILLATION EST SÉLECTIVE, PLUS AVEUGLE.
        #
        # La v37.0 imitait C2 à CHAQUE tick avec le MÊME poids, qu'il ait eu raison ou
        # tort. Sur un C2 médiocre, cela revient à faire apprendre à C1 les erreurs de C2 —
        # on n'automatise pas tous ses gestes, on automatise ceux qui ont marché.
        #
        # La perte est donc stockée SANS être moyennée ici : c'est `apprendre_journee` qui
        # la pondérera, une fois connu ce que chaque tick a réellement produit (crédit
        # rétrograde, voir `_ponderer_distillation`). Un tick suivi d'un choc dopaminergique
        # pèse ; un tick suivi de rien s'efface.
        if self.training and TAUX_DISTILLATION_C1 > 0.0:
            cible_c2 = torch.softmax(valeurs_simulees.detach(), dim=-1)
            self._pertes_distillation.append(
                F.cross_entropy(logits_instinct, cible_c2)
            )

        return (logits_finaux, valeur_etat_courant, parametres_vocaux,
                pensee_enrichie, memoire_actuelle, bus_latent,
                logits_routage, indecision_c2)

    def generer_attente_reelle(self, pensee_enrichie, actions_idx):
        onehot = self.actions_eye[actions_idx]
        if onehot.dim() == 1:
            onehot = onehot.unsqueeze(0)
        return self._predire_bus(pensee_enrichie, onehot)

    def generer_attente_audio_reelle(self, pensee_enrichie, actions_idx):
        """v22.1 (correctif défaut 3) : pendant JEPA audio via une tête SÉPARÉE
        (generateur_attente_audio), miroir exact de generer_attente_reelle."""
        onehot = self.actions_eye[actions_idx]
        if onehot.dim() == 1:
            onehot = onehot.unsqueeze(0)
        return self._predire_bus_audio(pensee_enrichie, onehot)

    def perte_jepa(self, attente, obs_suivante, attente_audio=None,
                   obs_auditive_suivante=None, coeff_jepa_audio=0.0):
        """Cible JEPA dans l'espace bus.

        v22.1 (correctif défaut 3, "empoisonnement du JEPA") : la contribution audio
        de v22.0 (une SEULE tête prédictive mélangeant vision+audio dans la même
        cible, sans pondération) risquait de laisser un signal audio bruyant perturber
        les gradients de la vision dès le tick 0 — dangereux pour les 481 jours de
        physique MiniGrid déjà appris. Désormais DEUX pertes complètement séparées :
        - la perte vision (inchangée, jamais affectée par l'audio) ;
        - la perte audio (tête generateur_attente_audio dédiée), pondérée par
          `coeff_jepa_audio` — monté PROGRESSIVEMENT par l'appelant (voir
          COEFF_JEPA_AUDIO_MAX/RAMPE_JEPA_AUDIO dans la boucle principale), 0.0 par
          défaut ici pour ne jamais activer l'audio sans décision explicite.

        Retourne la perte totale (vision + coeff*audio) — la branche vision seule
        reste strictement identique à avant v22.0 quand obs_auditive_suivante=None."""
        with torch.no_grad():
            bus_reel_vision = F.relu(self.porte_visuelle(obs_suivante))
        perte = F.mse_loss(attente, bus_reel_vision)

        # --- v41.13 : VENTILATION DE L'ERREUR (télémétrie PURE, aucun effet) ---
        #
        # ÉTAPE 1 de la confrontation du 16/08 (voir
        # docs/ameliorations/CONFRONTATION_16082026_jepa_multimodal.md) : avant d'ajouter
        # des têtes JEPA par sens, vérifier qu'il reste quelque chose à prédire.
        #
        # La question posée : le modèle du monde de C2 est-il déjà saturé ? Si l'erreur
        # visuelle est quasi nulle et sans structure, ajouter trois têtes ne ferait que
        # densifier un gradient déjà éteint — et la proposition tombe SANS avoir coûté un
        # seul run long. Si au contraire l'erreur reste forte et concentrée sur quelques
        # dimensions, c'est le signe qu'un modèle plus riche a de quoi mordre.
        #
        # ⚠️ Aucune de ces valeurs n'est consommée par la décision, le gradient ou la
        # dopamine. `.detach()` partout, sous `no_grad` — c'est ce qui garantit l'invariance
        # d'empreinte à graine fixée (le run reste bit-identique à la v41.12).
        with torch.no_grad():
            _err = (attente.detach() - bus_reel_vision).pow(2)
            # Erreur par dimension du bus : une erreur CONCENTRÉE sur peu de dims signale
            # un modèle qui échoue sur un aspect précis du monde ; une erreur ÉTALÉE
            # signale un modèle uniformément mauvais (ou un monde imprévisible).
            _par_dim = _err.mean(dim=0)
            self.jepa_diag_erreur_moyenne = float(_par_dim.mean().item())
            self.jepa_diag_erreur_max_dim = float(_par_dim.max().item())
            # Concentration = part de l'erreur portée par le quart le plus fautif des dims.
            # 0.25 = parfaitement étalé, 1.0 = tout dans un coin.
            _k = max(1, _par_dim.numel() // 4)
            _top = torch.topk(_par_dim, _k).values.sum()
            _tot = _par_dim.sum() + 1e-12
            self.jepa_diag_concentration = float((_top / _tot).item())
            # Amplitude du signal à prédire : une cible plate rend la prédiction triviale.
            # C'est le témoin qui distingue « C2 prédit bien » de « il n'y a rien à prédire »
            # — exactement la distinction ablation NÉGATIVE / ablation VIDE de la règle de
            # mesure. Sans lui, une erreur nulle serait ininterprétable.
            self.jepa_diag_amplitude_cible = float(bus_reel_vision.std().item())

        if obs_auditive_suivante is not None and attente_audio is not None and coeff_jepa_audio > 0.0:
            with torch.no_grad():
                bus_reel_audio = F.relu(self.porte_auditive(obs_auditive_suivante))
            perte = perte + coeff_jepa_audio * F.mse_loss(attente_audio, bus_reel_audio)

        return perte

    def _ponderer_distillation(self, chocs_dopamine, dones):
        """v37.1 — Le crédit rétrograde : quels ticks méritent d'être automatisés ?

        Répond à une question simple que la v37.0 ne posait pas : *le conseil de C2 a-t-il
        mené quelque part ?* Un tick est crédité si un choc dopaminergique le suit, et le
        crédit décroît exponentiellement à mesure qu'on remonte le temps — le geste juste
        avant la récompense compte plus que celui d'il y a trente ticks. C'est le patron
        de trace d'éligibilité déjà utilisé par `trace_activation` (LTP v20.0), appliqué
        ici à la sélection de ce qui vaut la peine d'être gravé dans le réflexe.

        La propagation s'ARRÊTE aux frontières d'épisode (`dones`) : créditer un tick de
        l'épisode précédent pour une réussite du suivant serait une superstition, l'agent
        ayant été téléporté entre les deux.

        RIEN N'EST EN DUR ICI. Le seuil qui décide « ce choc mérite-t-il d'être imité ? »
        n'existe pas : le crédit est CONTINU et proportionnel au choc. Et l'échelle à
        laquelle on juge un choc « fort » n'est pas une constante — c'est
        `reference_choc_dopamine`, la moyenne glissante de ce que CET agent a lui-même
        vécu. Un agent qui n'a jamais rien connu de mieux qu'un micro-progrès trouvera ce
        micro-progrès marquant ; le même agent, devenu expert et habitué aux victoires,
        ne le remarquera plus. Le niveau évolue avec l'âge et les habitudes, exactement
        comme la faim ou la soif — pas de seuil, un niveau relatif à une histoire.

        Retourne un tenseur de poids dans [0,1] aligné sur les ticks, ou None si aucun
        choc n'a jamais été mesuré (l'appelant retombe alors sur la moyenne plate v37.0).
        """
        if not chocs_dopamine:
            return None

        # --- L'échelle de référence : ce que cet agent considère comme un « bon » choc ---
        #
        # Moyenne des chocs NON NULS uniquement : inclure les ticks sans événement
        # (l'écrasante majorité) écraserait la référence vers 0 et rendrait le moindre
        # frémissement « exceptionnel ».
        #
        # v37.1-fix — LE CLIQUET : la référence monte vite, redescend très lentement.
        #
        # La v37.1 utilisait une moyenne glissante SYMÉTRIQUE, et c'était un bug. Mesuré sur
        # 600 jours : quand l'agent cesse de gagner, il ne reste que des micro-chocs ; la
        # référence descend donc VERS EUX (0,2149 → 0,0932, −57 %) et, le crédit valant
        # `choc / référence`, le même événement médiocre se met à créditer de plus en plus
        # (10 % → 69 %, ×7). L'agent devenait progressivement plus FACILE à impressionner —
        # l'inverse exact du principe voulu — et C1 finissait par distiller 70 % de bruit.
        #
        # Une boucle s'installait : moins de victoires → référence plus basse → tout paraît
        # marquant → distillation de n'importe quoi → encore moins de victoires. La
        # protection « une journée stérile ne distille rien » n'y pouvait rien : la journée
        # n'était jamais stérile, elle était MÉDIOCRE, et la référence s'adaptait à la
        # médiocrité.
        #
        # C'est exactement le défaut de `norme_naissance` corrigé en v34.0-fix2 : une
        # référence qui suit la décroissance ne borne plus rien. Même remède — un cliquet.
        #
        # La montée reste rapide (`INERTIE_REFERENCE_CHOC`) : découvrir qu'on peut vivre
        # mieux doit relever la barre sans tarder. La descente est ~50× plus lente
        # (`INERTIE_OUBLI_REFERENCE_CHOC`) : c'est de l'OUBLI, pas de l'adaptation — un
        # agent qui traverse une mauvaise passe ne doit pas réviser à la baisse ce qu'il
        # sait être un bon jour. Elle n'est pas nulle pour autant : un cerveau dont le monde
        # change durablement (nouveau niveau, ressources plus rares) doit pouvoir se
        # recalibrer, mais sur des centaines de nuits, jamais sur une saison creuse.
        chocs_reels = [c for c in chocs_dopamine if c > 0.0]
        if chocs_reels:
            moyenne_jour = sum(chocs_reels) / len(chocs_reels)
            if self.reference_choc_dopamine is None:
                self.reference_choc_dopamine = moyenne_jour
            else:
                # v40.1-fix4 — le cliquet écrit en FORMULE, plus en branche (règle « pas de
                # if/else hors mesure »). L'ancienne forme choisissait l'inertie selon le
                # sens (`A if monte else B`) ; la décomposition partie positive / partie
                # négative de l'écart est STRICTEMENT équivalente : la montée n'emprunte
                # que max(Δ,0), la descente que min(Δ,0), et l'un des deux vaut toujours 0.
                # Même patron que le tri du signe de `nourrir_vecu_journee`.
                delta = moyenne_jour - self.reference_choc_dopamine
                self.reference_choc_dopamine += (
                    (1.0 - INERTIE_REFERENCE_CHOC) * max(delta, 0.0)
                    + (1.0 - INERTIE_OUBLI_REFERENCE_CHOC) * min(delta, 0.0))
        if not self.reference_choc_dopamine:
            return None

        # --- Crédit rétrograde, en une seule passe arrière ---
        reference = max(self.reference_choc_dopamine, 1e-6)
        poids = [0.0] * len(chocs_dopamine)
        credit = 0.0
        for i in range(len(chocs_dopamine) - 1, -1, -1):
            # Frontière d'épisode : ce qui suit appartient à une autre vie.
            if i < len(dones) and dones[i]:
                credit = 0.0
            credit *= DECROISSANCE_CREDIT_DISTILLATION
            if chocs_dopamine[i] > 0.0:
                # Saillance RELATIVE : le choc rapporté à l'ordinaire de cet agent.
                credit = max(credit, min(chocs_dopamine[i] / reference, 1.0))
            poids[i] = credit

        return torch.tensor(poids, dtype=torch.float32, device=DEVICE)

    def apprendre_journee(self, jepa_losses, log_probs, entropies, valeurs, rewards, dones,
                          gamma=0.95, coeff_entropie=0.02, pertes_vocales=None,
                          chocs_dopamine=None, transitions=None, rendements=None):
        self.optimizer.zero_grad(set_to_none=True)
        perte_totale = torch.zeros((), device=DEVICE)

        if jepa_losses:
            perte_totale = perte_totale + torch.stack(jepa_losses).mean()

        # v22.1 (correctif défaut 1, CRITIQUE) : la perte qui donne enfin un vrai
        # gradient à tete_vocale — voir traiter_tick pour la construction de chaque
        # perte_vocale_tick (MSE sur F1/F2 uniquement, les dimensions réellement
        # contraintes par la leçon en cours). Sans cette branche, la bouche n'apprenait
        # que par LTP hebbien/rêve, jamais par une erreur dirigée vers la cible.
        if pertes_vocales:
            perte_totale = perte_totale + COEFF_PERTE_VOCALE * torch.stack(pertes_vocales).mean()

        if log_probs:
            returns = []
            R = 0.0
            for r, d in zip(reversed(rewards), reversed(dones)):
                R = r + gamma * (0.0 if d else R)
                returns.insert(0, R)
            returns = torch.tensor(returns, dtype=torch.float32, device=DEVICE)
            if returns.numel() > 1 and returns.std() > 1e-6:
                returns = (returns - returns.mean()) / (returns.std() + 1e-8)

            valeurs_tensor = torch.cat(valeurs).squeeze(-1)
            avantages = (returns - valeurs_tensor.detach())

            log_probs_tensor = torch.cat(log_probs).squeeze(-1)
            entropies_tensor = torch.cat(entropies).squeeze(-1)

            # --- v41.48 : LE RENDEMENT MÉCANIQUE ASYMÉTRIQUE (brique C) ---
            #
            #     A_t > 0  →  A_t × rendement_t     un succès stérile n'ancre RIEN
            #     A_t ≤ 0  →  A_t                   un échec stérile reste PUNI
            #
            # ⚠️ L'ASYMÉTRIE N'EST PAS UN DÉTAIL. Pondérer les deux signes rendrait le
            # geste stérile INVISIBLE à l'apprentissage au lieu de le rendre indésirable :
            # son gradient serait nul dans les deux sens, donc la politique n'aurait
            # aucune raison de cesser de le jouer. C'est la faute symétrique de celle que
            # la v41.28 a corrigée côté COÛT (`travail = 0.0` faisait du geste inutile le
            # MOINS CHER du barème) — ici elle en ferait le moins INSTRUCTIF.
            # `RENDEMENT_SYMETRIQUE_TEMOIN` existe pour mesurer précisément ça.
            #
            # ⚠️ Le rendement pondère l'AVANTAGE, jamais la log-probabilité ni l'entropie :
            # l'exploration doit rester libre de tenter un geste au rendement inconnu.
            # C'est la même frontière qu'en v41.31, où le masque épargne explicitement
            # l'entropie, le critique et JEPA.
            if (RENDEMENT_MECANIQUE_ACTIF and rendements is not None
                    and len(rendements) == log_probs_tensor.numel()):
                rendement_t = torch.tensor(rendements, dtype=torch.float32, device=DEVICE)
                if RENDEMENT_SYMETRIQUE_TEMOIN:
                    avantages = avantages * rendement_t
                else:
                    positif = (avantages > 0).float()
                    avantages = avantages * (positif * rendement_t + (1.0 - positif))

            # --- v41.31 : LE GRADIENT CAUSAL — la politique n'apprend que des gestes
            # qui ont CHANGÉ QUELQUE CHOSE ---
            #
            # 🔴 CE QUE ÇA CORRIGE. REINFORCE propage le retour d'un épisode réussi sur
            # TOUTES les actions de la trajectoire. Un agent qui a spammé `toggle` 25 fois
            # dans le vide en marchant vers le but voit C1 renforcer ces gestes par simple
            # contamination de voisinage. Mesuré (DERIVE_g1, dernier jour) :
            #
            #   a4 drop 9%/100st · a5 toggle 16%/100st · a6 done 7%/100st
            #   a3 pickup 24%/85st · a2 avancer 26%/51st
            #   => 32 % des ticks stériles à 100 %, 61,7 % au total.
            #
            # ⚠️ NEUTRALISER N'EST PAS PÉNALISER : gradient NUL, jamais de malus. Un malus
            # serait une récompense en dur, ce que le dogme interdit. L'extinction des
            # actions inutiles doit ÉMERGER de l'absence de crédit.
            #
            # ⚠️ LE DÉNOMINATEUR EST LE NOMBRE DE TICKS RETENUS, jamais le total. Un
            # `.mean()` naïf laisserait `T` au dénominateur : à 61,7 % de masquage, le
            # gradient des gestes UTILES serait divisé par ~2,6 — on aurait dilué
            # l'apprentissage au lieu de le concentrer, l'inverse exact de l'intention.
            # Même discipline que la moyenne pondérée de la distillation v37.1.
            #
            # ⚠️ LE MASQUE NE PORTE QUE SUR L'ACTEUR. Le critique estime la valeur d'un
            # ÉTAT (un état où l'agent vient de pousser un mur en a une) : le masquer le
            # rendrait aveugle à 61,7 % des états et fausserait les AVANTAGES qu'il
            # fournit à l'acteur. L'entropie pousse à explorer sur TOUS les états : la
            # masquer reviendrait à n'explorer que là où l'agent bouge déjà, soit
            # l'inverse du but — sortir d'un blocage. JEPA non plus : l'immobilité face à
            # un mur est une PRÉDICTION DÉTERMINISTE VALIDE, et C2 en a besoin pour
            # planifier un contournement (« si j'avance ici, je ne bougerai pas »).
            if GRADIENT_CAUSAL_ACTIF and transitions is not None and len(transitions) == log_probs_tensor.numel():
                masque = torch.tensor([1.0 if t else 0.0 for t in transitions],
                                      dtype=torch.float32, device=DEVICE)
                # max(1, ·) : une journée 100 % stérile donne une perte NULLE sans jamais
                # diviser par zéro — la politique n'apprend rien ce jour-là, et c'est
                # voulu (« une journée stérile ne distille rien », v37.1). Le critique,
                # l'entropie et JEPA continuent, eux, d'apprendre.
                n_retenus = torch.clamp(masque.sum(), min=1.0)
                perte_acteur = -((log_probs_tensor * avantages * masque).sum() / n_retenus)
            elif GAIN_ACTEUR_CONTROLE != 1.0:
                # v41.31-controle — LE BRAS DE FALSIFICATION.
                #
                # Le masque divise par `Σ m_t` au lieu de `T`, ce qui multiplie
                # mécaniquement le gradient de l'acteur par ~T/Σm ≈ 2,6 à 61,7 % de
                # masquage. La question : le gain mesuré (+2,57 pts de maîtrise, +48 % de
                # victoires, SIG à n=20) vient-il du FILTRAGE ou de cette MULTIPLICATION ?
                #
                # Ce bras applique le facteur SANS filtrer : `.mean()` classique, gradient
                # ×2,6. Si le score égale celui du bras causal, le filtrage n'y est pour
                # rien — l'agent avait juste besoin d'apprendre plus vite.
                #
                # ⚠️ Le facteur porte sur la PERTE, pas sur `lr` : l'optimiseur est unique
                # pour tout le réseau, donc changer `lr` accélérerait aussi JEPA, le
                # critique et la tête vocale — on mesurerait « apprendre plus vite
                # partout », pas « acteur ×2,6 ».
                #
                # ⚠️ Vérifié au banc : Adam ABSORBE un facteur constant sur un paramètre
                # isolé (résultats identiques à la 4ᵉ décimale, 200 pas). Le facteur n'agit
                # que parce que le TRONC est PARTAGÉ entre l'acteur et le critique : le
                # gradient du tronc est la somme des deux, et le rapport entre elles change.
                # Mesuré sur un réseau jouet à tronc partagé : normes 1,14937 contre
                # 1,09665. Le contrôle est donc valide — mais il mesure un déplacement
                # d'équilibre acteur/critique, pas un simple « learning rate ».
                perte_acteur = -GAIN_ACTEUR_CONTROLE * (log_probs_tensor * avantages).mean()
            else:
                perte_acteur = -(log_probs_tensor * avantages).mean()
            # v41.32 — ablation de la collision : le critique n'apprend plus, donc plus
            # aucun gradient ne part de C2 vers `integrateur_bio`. Le forward est intact.
            perte_critique = (F.mse_loss(valeurs_tensor, returns) if GRADIENT_C2_ACTIF
                              else F.mse_loss(valeurs_tensor.detach(), returns))
            perte_entropie = -coeff_entropie * entropies_tensor.mean()

            perte_totale = perte_totale + perte_acteur + perte_critique + perte_entropie

        # --- v37.1 : DISTILLATION SÉLECTIVE — C1 n'automatise que ce qui a marché ---
        #
        # Le buffer est vidé DANS TOUS LES CAS (même si la branche est désactivée ou si la
        # perte n'a pas de gradient), sinon il grossirait indéfiniment d'un jour à l'autre
        # en retenant tout le graphe de la journée — piège du compteur non réinitialisé
        # déjà rencontré en v27.0 (`score_vocal_jour`).
        self.derniere_perte_distillation = 0.0
        self.dernier_credit_distillation = 0.0
        if self._pertes_distillation:
            poids = self._ponderer_distillation(chocs_dopamine, dones)
            pertes = torch.stack(self._pertes_distillation)
            if poids is not None:
                n = min(len(poids), len(pertes))
                poids, pertes = poids[:n], pertes[:n]
                # Moyenne PONDÉRÉE : la somme des poids fait office de dénominateur, si
                # bien qu'une journée entièrement stérile (tous poids nuls) ne distille
                # rien du tout, au lieu de distiller uniformément du bruit.
                total = poids.sum()
                perte_distill = ((pertes * poids).sum() / total) if total > 1e-8 \
                    else pertes.mean() * 0.0
                self.dernier_credit_distillation = float(poids.mean().item())
            else:
                perte_distill = pertes.mean()
                self.dernier_credit_distillation = 1.0

            self.derniere_perte_distillation = float(perte_distill.item())
            perte_totale = perte_totale + TAUX_DISTILLATION_C1 * perte_distill
        self._pertes_distillation = []

        if not perte_totale.requires_grad:
            return 0.0

        perte_totale.backward()
        torch.nn.utils.clip_grad_norm_([p for p in self.parameters() if p.requires_grad], 1.0)
        self.optimizer.step()

        return float(perte_totale.item())

    def rever(self, memoire_moyen_terme, batch_size=32, coeff_jepa_audio=0.0):
        """batch_size est désormais calculé par l'appelant comme un POURCENTAGE adaptatif
        de la journée (voir la boucle principale) plutôt qu'une constante fixe.

        `coeff_jepa_audio` (v27.0) : consolidation nocturne de l'audio — jusqu'ici, le
        rêve ne rejouait QUE la mémoire visuelle (obs_auditive=None systématique dans
        _tronc_cerebral/perte_jepa), alors que l'érosion nocturne (cycle_sommeil_global)
        grignote porte_auditive/tete_vocale comme les autres couches : tout
        l'apprentissage vocal du jour se faisait éroder sans jamais être consolidé.
        Le batch audio n'est reconstruit QUE si TOUS les souvenirs tirés en ont un
        (sinon obs_auditive=None, comportement pré-v27.0 strict) — un lot mélangeant
        silence et son introduirait un biais de padding arbitraire (quel vecteur mettre
        pour les souvenirs muets ?) plutôt qu'un signal réel. `coeff_jepa_audio` (même
        rampe progressive que traiter_tick, voir COEFF_JEPA_AUDIO_MAX/RAMPE_JEPA_AUDIO)
        pondère la contribution audio pour ne jamais perturber le JEPA visuel déjà mature."""
        n = len(memoire_moyen_terme)
        if n < batch_size or batch_size <= 0:
            return 0.0, 0

        importances = np.array([s['importance'] for s in memoire_moyen_terme], dtype=np.float64)
        total = importances.sum()
        probs = importances / total if total > 0 else np.full(n, 1.0 / n)
        indices = np.random.choice(n, batch_size, p=probs, replace=False)
        lot = [memoire_moyen_terme[i] for i in indices]

        obs_courante = torch.cat([s['obs_courante'] for s in lot], dim=0)
        memoire_prec = torch.cat([s['memoire_prec'] for s in lot], dim=0)
        contexte = torch.cat([s['contexte'] for s in lot], dim=0)
        obs_suivante = torch.cat([s['obs_suivante'] for s in lot], dim=0)
        actions = torch.tensor([s['action'] for s in lot], device=DEVICE, dtype=torch.long)

        obs_auditive = None
        if coeff_jepa_audio > 0.0 and all(s.get('obs_auditive') is not None for s in lot):
            obs_auditive = torch.cat([s['obs_auditive'] for s in lot], dim=0)

        self.optimizer.zero_grad(set_to_none=True)
        _, _, pensee = self._tronc_cerebral(obs_courante, memoire_prec, obs_auditive=obs_auditive)
        pensee_enrichie = self.lecture_episodique(pensee, contexte)
        attente = self.generer_attente_reelle(pensee_enrichie, actions)
        attente_audio = None
        if obs_auditive is not None:
            attente_audio = self.generer_attente_audio_reelle(pensee_enrichie, actions)
        perte_reves = self.perte_jepa(
            attente, obs_suivante, attente_audio=attente_audio,
            obs_auditive_suivante=obs_auditive, coeff_jepa_audio=coeff_jepa_audio,
        )

        perte_reves.backward()
        torch.nn.utils.clip_grad_norm_([p for p in self.parameters() if p.requires_grad], 1.0)
        self.optimizer.step()
        return float(perte_reves.item()), batch_size

    def fortifier_synapses(self, pic_dopamine: float):
        """LTP par tick (v20.0) : appelée depuis la boucle principale sur chaque
        événement marquant (poids_evenement > 0 — manger, franchir une porte, valider
        un palier...), pas une seule fois par jour sur une moyenne diluée. Grave les
        synapses actives de TOUTES les couches plastiques, dans le même ordre que
        cycle_sommeil_global/declencher_neurogenese pour rester cohérent avec les deux
        autres cycles de vie de NaultheneLinearSynaptique."""
        if pic_dopamine <= 0:
            return
        for couche in (self.porte_visuelle, self.hippocampe, self.fusion_memoire,
                       self.analyseur, self.integrateur_bio, self.tete_motrice,
                       self.cortex_prefrontal, self.generateur_attente,
                       self.porte_auditive, self.tete_vocale, self.generateur_attente_audio,
                       self.tete_requete):
            couche.fortification_dopaminergique(pic_dopamine)

    def cycle_sommeil_global(self, plasticite=1.0, attenuation_erosion_audio=1.0):
        """`attenuation_erosion_audio` (v24.0-fix1, École de Rattrapage Vocal) : facteur
        multiplicatif appliqué à `lambda_erosion` UNIQUEMENT sur les 3 couches audio
        (porte_auditive, tete_vocale, generateur_attente_audio). 1.0 par défaut =
        comportement strictement identique à avant v24.0-fix1. Voir
        ATTENUATION_EROSION_AUDIO_DEBUT et son usage dans executer_nuit — protège le tout
        premier apprentissage vocal d'un cerveau neuf (diagnostiqué à zéro exact après
        1000 nuits d'érosion non amortie sur un run réel)."""
        lam = 0.05 * plasticite
        lam_audio = lam * attenuation_erosion_audio
        return sum([
            self.porte_visuelle.cycle_sommeil(lambda_erosion=lam),
            self.hippocampe.cycle_sommeil(lambda_erosion=lam),
            self.fusion_memoire.cycle_sommeil(lambda_erosion=lam),
            self.analyseur.cycle_sommeil(lambda_erosion=lam),
            self.integrateur_bio.cycle_sommeil(lambda_erosion=lam),
            self.tete_motrice.cycle_sommeil(lambda_erosion=lam),
            self.cortex_prefrontal.cycle_sommeil(lambda_erosion=lam),
            self.generateur_attente.cycle_sommeil(lambda_erosion=lam),
            self.porte_auditive.cycle_sommeil(lambda_erosion=lam_audio),
            self.tete_vocale.cycle_sommeil(lambda_erosion=lam_audio),
            self.generateur_attente_audio.cycle_sommeil(lambda_erosion=lam_audio),
            self.tete_requete.cycle_sommeil(lambda_erosion=lam),
        ])

    def declencher_neurogenese(self, ajout_dim=16):
        d = self.dim_bus
        a = ajout_dim
        A = self.num_actions

        self.porte_visuelle.agrandir([(self.dim_visuelle, 0)], a)
        self.hippocampe.agrandir([(d, a), (d, a)], a)
        self.fusion_memoire.agrandir([(d, a), (d, a)], a)
        self.analyseur.agrandir([(d, a)], a)
        # Le vecteur bio (DIM_VECTEUR_BIO) ne grandit jamais — seul le segment "pensée"
        # de l'entrée de integrateur_bio s'agrandit, dans le même ordre que la
        # concaténation faite dans integrer_bio() : [pensee, vecteur_bio].
        self.integrateur_bio.agrandir([(d, a), (DIM_VECTEUR_BIO, 0)], a)
        self.tete_motrice.agrandir([(d, a)], 0)
        self.cortex_prefrontal.agrandir([(d, a)], 0)
        self.generateur_attente.agrandir([(A, 0), (d, a)], a)

        # Hémisphère Auditif & Vocal (v22.0) : même logique de symétrie que
        # porte_visuelle/tete_motrice. L'entrée audio brute (DIM_AUDIO_ENTREE) ne
        # grandit jamais (comme dim_visuelle) ; la sortie vers le bus grandit de a.
        # La bouche : l'entrée bus grandit de a, la sortie DIM_VOCALE=8 est fixe
        # (comme num_actions pour tete_motrice).
        self.porte_auditive.agrandir([(DIM_AUDIO_ENTREE, 0)], a)
        self.tete_vocale.agrandir([(d, a)], 0)
        # Tête JEPA audio séparée (v22.1) : même segments_in que generateur_attente,
        # miroir exact.
        self.generateur_attente_audio.agrandir([(A, 0), (d, a)], a)

        # Tête de routage C3 (v28.0, expérimental) : entrée pensee_bio grandit de a
        # (comme tete_motrice), sortie DIM_ROUTAGE_C3 fixe (comme cortex_prefrontal/
        # tete_vocale — le nombre de plugs adressables ne dépend pas de dim_bus).
        self.tete_requete.agrandir([(d, a)], 0)

        self.dim_bus += a
        self.to(DEVICE)
        self._reset_optimizer()


def encoder(obs):
    return torch.as_tensor(obs['image'].flatten(), dtype=torch.float32, device=DEVICE).unsqueeze(0) / 10.0


# --- v39-fix (R3) : LES PALIERS INTERMÉDIAIRES APPARTIENNENT AU NOYAU ---
#
# MiniGrid ne fournit que quatre DoorKey : 5x5, 6x6, 8x8, 16x16. Les cursus du projet en
# utilisent six — les deux manquants (10x10, 12x12) étaient enregistrés à la volée PAR LE
# BANC D'ESSAI, donc invisibles pour tout autre point d'entrée.
#
# 🔴 CE QUE ÇA CORRIGE (vérifié, 2 instruments sur 2) : un `.brain` sauvegardé sur l'un de
# ces paliers était ILLISIBLE par les outils de diagnostic —
#
#     $ python -m naulthene.instruments.sonde_poids <brain>
#     gymnasium.error.NameNotFound: Environment `MiniGrid-DoorKey-12x12` doesn't exist.
#
# C'est un échec silencieux DIFFÉRÉ : rien ne prévient pendant le run, la panne
# n'apparaît que le jour où l'on veut auditer le cerveau, souvent des semaines plus tard.
#
# L'enregistrement est donc remonté ici, près de `creer_env` : il devient effectif partout
# où le noyau est importé (bancs, instruments, Cuve, Arène). Idempotent — un
# ré-enregistrement par un banc ne fait qu'émettre un avertissement gymnasium bénin.
try:
    from gymnasium.envs.registration import register as _gym_register
    for _taille_doorkey in (10, 12):
        try:
            _gym_register(
                id=f"MiniGrid-DoorKey-{_taille_doorkey}x{_taille_doorkey}-v0",
                entry_point="minigrid.envs:DoorKeyEnv",
                kwargs={"size": _taille_doorkey})
        except Exception:
            pass    # déjà enregistré : sans conséquence (idempotent)
except Exception:
    pass            # gymnasium/minigrid absent : le noyau reste importable


def creer_env(env_id, dim_attendue, render_mode=None):
    """`render_mode` (v24.0, Arène & Démo Live) : None par défaut (comportement
    identique à avant v24.0, aucun rendu — c'est le cas de tous les appels existants
    dans ce fichier et dans persistance.py) ou "rgb_array" (utilisé par
    lancer_arene.py pour récupérer une image numpy via env.render(), composée ensuite
    avec le panneau de télémétrie dans arene_visuelle.FenetreArene)."""
    e = gym.make(env_id, render_mode=render_mode)
    o, _ = e.reset()
    taille = int(np.prod(o['image'].shape))
    if taille != dim_attendue:
        e.close()
        raise ValueError(f"{env_id} produit une observation de {taille} valeurs, "
                         f"le réseau en attend {dim_attendue}.")
    return e


def est_doorkey(env_id):
    return "DoorKey" in env_id


# --- 3a. CURSUS SPÉCIFIQUE DOORKEY (7 paliers, inchangé depuis la version précédente) ---
class DetecteurJalonsDoorKey:
    """
    Palier 1-6 : mécanique clé/serrure spécifique à DoorKey. Palier 7 : franchir la
    porte et toucher le But, détecté via la récompense terminale de MiniGrid elle-même.

    Le guidage continu (RECOMPENSE_APPROCHE_BUT) reste une BÉQUILLE TEMPORAIRE retirée
    en Mode Libre dès que le Palier 7 est promu — voir la boucle principale.
    """
    NOMS = ["Regarder", "S'approcher", "Toucher/Prendre", "Transporter",
            "Viser la Porte", "Déverrouiller", "Franchir & Sortir"]
    POIDS_CHOC = [0.15, 0.10, 0.85, 0.10, 0.15, 0.90, 1.00]
    MICRO_RECOMPENSE = [0.01, 0.01, 0.30, 0.01, 0.02, 0.50, 0.00]
    RECOMPENSE_APPROCHE_BUT = 0.05

    def __init__(self):
        self.actif = _MINIGRID_INTERNALS_OK
        self._avertissement_donne = False
        self.reinitialiser_episode(None)

    def _avertir(self, exception):
        if not self._avertissement_donne:
            print(f"⚠️  Détecteur de jalons DoorKey désactivé (API minigrid incompatible : {exception})")
            self._avertissement_donne = True
        self.actif = False

    def reinitialiser_episode(self, env):
        self.pos_cle = None
        self.pos_porte = None
        self.pos_but = None
        self.dist_cle_precedente = None
        self.dist_porte_precedente = None
        self.dist_but_precedente = None
        self.carrying_precedent = None
        self.meilleur_palier_episode = 0
        if env is None or not self.actif:
            return
        try:
            grille = env.unwrapped.grid
            for x in range(grille.width):
                for y in range(grille.height):
                    obj = grille.get(x, y)
                    if isinstance(obj, Key) and self.pos_cle is None:
                        self.pos_cle = (x, y)
                    elif isinstance(obj, Door) and self.pos_porte is None:
                        self.pos_porte = (x, y)
                    elif isinstance(obj, Goal) and self.pos_but is None:
                        self.pos_but = (x, y)
        except Exception as e:
            self._avertir(e)

    @staticmethod
    def _distance(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def evaluer_tick(self, env, action_item, recompense_env):
        if not self.actif:
            return 0, 0.0, 0.0, 0.0
        try:
            carrying_apres = env.unwrapped.carrying
            agent_pos = tuple(env.unwrapped.agent_pos)
            palier = 0
            recompense_continue = 0.0

            if self.pos_cle is not None:
                palier = max(palier, 1)
                dist_cle = self._distance(agent_pos, self.pos_cle)
                if self.dist_cle_precedente is not None and dist_cle < self.dist_cle_precedente:
                    palier = max(palier, 2)
                self.dist_cle_precedente = dist_cle

            pickup_reussi = (self.carrying_precedent is None
                             and isinstance(carrying_apres, Key)
                             and action_item == Actions.pickup)
            if pickup_reussi:
                palier = max(palier, 3)

            if isinstance(carrying_apres, Key) and action_item in (Actions.forward, Actions.left, Actions.right):
                palier = max(palier, 4)

            if isinstance(carrying_apres, Key) and self.pos_porte is not None:
                dist_porte = self._distance(agent_pos, self.pos_porte)
                if self.dist_porte_precedente is not None and dist_porte < self.dist_porte_precedente:
                    palier = max(palier, 5)
                self.dist_porte_precedente = dist_porte

            porte_ouverte = False
            if self.pos_porte is not None:
                porte = env.unwrapped.grid.get(*self.pos_porte)
                if isinstance(porte, Door):
                    if action_item == Actions.toggle and not porte.is_locked:
                        palier = max(palier, 6)
                    porte_ouverte = porte.is_open

            if recompense_env > 0:
                palier = max(palier, 7)

            if porte_ouverte and self.pos_but is not None:
                dist_but = self._distance(agent_pos, self.pos_but)
                if self.dist_but_precedente is not None and dist_but < self.dist_but_precedente:
                    recompense_continue = self.RECOMPENSE_APPROCHE_BUT
                self.dist_but_precedente = dist_but

            self.carrying_precedent = carrying_apres

            if palier > self.meilleur_palier_episode:
                idx = palier - 1
                self.meilleur_palier_episode = palier
                return palier, self.MICRO_RECOMPENSE[idx], self.POIDS_CHOC[idx], recompense_continue
            return 0, 0.0, 0.0, recompense_continue
        except Exception as e:
            self._avertir(e)
            return 0, 0.0, 0.0, 0.0


# --- 3b. DÉTECTEURS GÉNÉRIQUES (aucun palier écrit en dur, actifs sur N'IMPORTE quel niveau) ---
class DetecteurFranchissementPortes:
    """
    Contrairement à DetecteurJalonsDoorKey (qui encode la mécanique clé/serrure
    spécifique à un seul niveau), celui-ci ne connaît qu'UN principe générique :
    "une porte ouverte que je viens de franchir = un petit point de dopamine". Il
    scanne TOUTES les portes de la grille (une seule dans DoorKey/Unlock, plusieurs
    dans MultiRoom — Porte 1 → Porte 2 → Porte 3) sans rien savoir de leur nombre ou
    de leur rôle à l'avance. Sur un niveau sans porte (Empty, MemoryS7), il ne trouve
    simplement rien à faire et reste inerte : pas besoin de le désactiver niveau par
    niveau. C'est ce mécanisme structurel, et non une liste d'étapes nommées, qui doit
    lui apprendre le PRINCIPE de la récompense plutôt qu'un script figé.
    """
    MICRO_RECOMPENSE = 0.05
    POIDS_CHOC = 0.30

    def __init__(self):
        self.actif = _MINIGRID_INTERNALS_OK
        self._avertissement_donne = False
        self.reinitialiser_episode(None)

    def _avertir(self, exception):
        if not self._avertissement_donne:
            print(f"⚠️  Détecteur de franchissement désactivé (API minigrid incompatible : {exception})")
            self._avertissement_donne = True
        self.actif = False

    def reinitialiser_episode(self, env):
        self.portes = []
        self.franchies = set()
        if env is None or not self.actif:
            return
        try:
            grille = env.unwrapped.grid
            for x in range(grille.width):
                for y in range(grille.height):
                    if isinstance(grille.get(x, y), Door):
                        self.portes.append((x, y))
        except Exception as e:
            self._avertir(e)

    def evaluer_tick(self, env):
        """Retourne (nb_nouvelles_portes_franchies, micro_recompense, poids_choc)."""
        if not self.actif or not self.portes:
            return 0, 0.0, 0.0
        try:
            agent_pos = tuple(env.unwrapped.agent_pos)
            for pos in self.portes:
                if pos in self.franchies:
                    continue
                if agent_pos == pos:
                    porte = env.unwrapped.grid.get(*pos)
                    if isinstance(porte, Door) and porte.is_open:
                        self.franchies.add(pos)
                        return 1, self.MICRO_RECOMPENSE, self.POIDS_CHOC
            return 0, 0.0, 0.0
        except Exception as e:
            self._avertir(e)
            return 0, 0.0, 0.0


class DetecteurProgresPersonnel:
    """
    La version la plus générique du renforcement : pas de paliers nommés, pas de
    mécanique supposée (clé, porte...), juste "ai-je battu mon record de proximité au
    But cet épisode ?". Fonctionne sur n'importe quelle disposition de grille tant
    qu'un objet Goal existe quelque part — y compris les longs couloirs de MultiRoom
    où aucun cursus détaillé n'a été écrit à la main. C'est la "quête auto-générée" :
    elle n'est jamais codée en dur pour un niveau précis, elle se déduit de la carte
    du jour.

    Volontairement INACTIF sur les niveaux DoorKey, qui disposent déjà de leur propre
    guidage vers le but (DetecteurJalonsDoorKey.RECOMPENSE_APPROCHE_BUT) avec son
    propre mécanisme de retrait progressif (Mode Libre) : faire tourner les deux en
    même temps créerait un guidage qui ne s'éteint jamais complètement.
    """
    MICRO_RECOMPENSE = 0.03
    POIDS_CHOC = 0.20

    def __init__(self):
        self.actif = _MINIGRID_INTERNALS_OK
        self._avertissement_donne = False
        self.reinitialiser_episode(None)

    def _avertir(self, exception):
        if not self._avertissement_donne:
            print(f"⚠️  Détecteur de progrès personnel désactivé (API minigrid incompatible : {exception})")
            self._avertissement_donne = True
        self.actif = False

    def reinitialiser_episode(self, env):
        self.pos_but = None
        self.meilleure_distance = None
        if env is None or not self.actif:
            return
        try:
            grille = env.unwrapped.grid
            trouve = False
            for x in range(grille.width):
                for y in range(grille.height):
                    if isinstance(grille.get(x, y), Goal):
                        self.pos_but = (x, y)
                        trouve = True
                        break
                if trouve:
                    break
        except Exception as e:
            self._avertir(e)

    def evaluer_tick(self, env):
        """Retourne (micro_recompense, poids_choc)."""
        if not self.actif or self.pos_but is None:
            return 0.0, 0.0
        try:
            agent_pos = tuple(env.unwrapped.agent_pos)
            dist = abs(agent_pos[0] - self.pos_but[0]) + abs(agent_pos[1] - self.pos_but[1])
            if self.meilleure_distance is None or dist < self.meilleure_distance:
                self.meilleure_distance = dist
                return self.MICRO_RECOMPENSE, self.POIDS_CHOC
            return 0.0, 0.0
        except Exception as e:
            self._avertir(e)
            return 0.0, 0.0


# --- 3c. THERMOSTAT CINÉTIQUE MULTIMODAL & PATIENCE PAR ABNÉGATION (génériques, actifs partout) ---
class ThermostatCinetiqueMultimodal:
    """
    Pression cinétique ("envie de bouger"), version multimodale (v16.0) : générique
    comme DetecteurFranchissementPortes et DetecteurProgresPersonnel, sans connaissance
    de la carte. Mesure la trajectoire récente de l'agent (agent_pos) pour calculer une
    pénalité BRUTE de stagnation (immobilité stricte, piétinement), puis MODULE cette
    pénalité par le contexte multimodal du tick plutôt que de l'appliquer à plein
    partout :

    - Manipuler un objet transporté (`carrying`) ou interagir face à un objet d'intérêt
      (`Key`/`Door`/`Goal`, via `pickup`/`toggle`) justifie légitimement des arrêts et
      changements de direction — la pénalité y est fortement atténuée, presque effacée
      pendant une interaction en cours.
    - Rester immobile en déplacement libre (rien en main, rien en face) reste
      considéré comme de la léthargie — la pénalité s'y applique à pleine intensité.

    Cela évite de punir des comportements légitimes (s'arrêter pour ouvrir une porte)
    de la même façon qu'une vraie léthargie (tourner en rond sans but).
    """
    def __init__(self, taille_memoire_pos=6, penalite_base=0.015,
                 facteur_manipulation=0.30, facteur_interaction=0.05, facteur_libre=1.00):
        self.taille_memoire_pos = taille_memoire_pos
        self.penalite_base = penalite_base
        # v41.43 — repli pour les contextes SANS carte (vocal isolé, rêve), où
        # `max_steps` n'existe pas : on retombe sur la valeur reçue à la construction.
        self._penalite_base_initiale = penalite_base
        self.facteur_manipulation = facteur_manipulation
        self.facteur_interaction = facteur_interaction
        self.facteur_libre = facteur_libre
        self.actif = _MINIGRID_INTERNALS_OK
        self._avertissement_donne = False
        self.reinitialiser_episode(None)

    def _avertir(self, exception):
        if not self._avertissement_donne:
            print(f"⚠️  Thermostat cinétique multimodal désactivé (API minigrid incompatible : {exception})")
            self._avertissement_donne = True
        self.actif = False

    def reinitialiser_episode(self, env):
        self.historique_positions = []
        # v41.43 — L'ÉCHELLE SE RECALCULE À CHAQUE CARTE, jamais par tick.
        # Le budget (`max_steps`) est une propriété du monde courant : il change au
        # changement de niveau, et c'est le SEUL moment où il peut changer. Même
        # discipline que `ajuster_capacite` (v31.0, une fois par nuit) et que le rythme
        # métabolique (v41.30, une fois par nuit) — une échelle qui fluctuerait en cours
        # d'épisode rendrait la douleur illisible pour l'agent comme pour le diagnostic.
        if env is not None:
            self.penalite_base = _penalite_stagnation_du_monde(
                env, defaut=self._penalite_base_initiale)

    def evaluer_tick(self, env, action_item):
        """Retourne une pénalité (valeur <= 0) à ajouter à la récompense interne."""
        if not self.actif:
            return 0.0
        try:
            pos_actuelle = tuple(env.unwrapped.agent_pos)
            penalite_brute = 0.0

            if self.historique_positions:
                if pos_actuelle == self.historique_positions[-1]:
                    penalite_brute += self.penalite_base * 2.0
                elif pos_actuelle in self.historique_positions:
                    occurrences = self.historique_positions.count(pos_actuelle)
                    penalite_brute += self.penalite_base * (1.5 ** occurrences)

            self.historique_positions.append(pos_actuelle)
            if len(self.historique_positions) > self.taille_memoire_pos:
                self.historique_positions.pop(0)

            if penalite_brute == 0.0:
                return 0.0

            carrying_obj = env.unwrapped.carrying
            objet_en_face = env.unwrapped.grid.get(*env.unwrapped.front_pos)

            en_train_d_interagir = action_item in (Actions.pickup, Actions.toggle)
            face_a_objet_cle = isinstance(objet_en_face, (Key, Door, Goal))

            if en_train_d_interagir or face_a_objet_cle:
                facteur = self.facteur_interaction
            elif carrying_obj is not None:
                facteur = self.facteur_manipulation
            else:
                facteur = self.facteur_libre

            return -(penalite_brute * facteur)
        except Exception as e:
            self._avertir(e)
            return 0.0


class ModuleAcceptationAbnegation:
    """
    Potentiomètre d'acceptation (patience par Abnégation, v16.0) : au lieu d'un plafond
    de ticks par épisode fixe et écrit en dur, la patience maximale tolérée est
    recalculée chaque jour à partir du taux de succès récent et de la vitesse (en
    ticks) des succès passés. Un agent qui a l'habitude de réussir vite garde une
    patience courte (il coupe court plus tôt un épisode qui dérape) ; un agent encore
    en phase d'exploration/apprentissage conserve une patience plus longue.

    Nouveauté v16.0 : `obtenir_seuil_patience` accepte un `facteur_complexite_sous_seuil`
    (voir GestionnaireCursusAbnegation) qui ÉTIRE cette patience de base lors du
    Sous-Seuil 2 (Consolidation/Abnégation) d'un palier — l'agent apprend ainsi que
    l'effort prolongé n'est pas un échec mais une condition naturelle des sous-étapes
    plus complexes, plutôt que de subir un abandon prématuré à seuil constant.

    Quand le compteur de ticks de l'épisode courant dépasse ce seuil (base ou étiré)
    sans que l'environnement n'ait lui-même conclu, l'agent DÉCLENCHE une troncature
    volontaire (abandon lucide) plutôt que d'épuiser ses ressources cognitives dans un
    épisode déjà mal engagé.
    """
    def __init__(self, patience_min=50, plafond_hors_monde=400, fenetre_historique=20):
        self.patience_min = patience_min
        # v41.30 — plus de `patience_max` posé : le plafond vient du MONDE
        # (`_budget_natif_carte` → `max_steps`). Celui-ci ne sert qu'aux contextes SANS
        # carte (vocal isolé, rêve), où `max_steps` n'existe pas.
        self.plafond_hors_monde = plafond_hors_monde
        self.fenetre_historique = fenetre_historique
        self.historique_succes = []
        self.historique_vitesses = []
        # v41.30 — LE TRAIT D'ENDURANCE, lissé sur la VIE ENTIÈRE de l'agent.
        #
        # Décision utilisateur du 20/08/2026 : *« La solution la plus élégante et la plus
        # fidèle au Dogme est de calculer l'écart sur la dynamique continue de la vie de
        # l'agent via un lissage exponentiel, SANS réinitialisation au changement de
        # carte. »* Trois propriétés qui en découlent et qu'il ne faut pas casser :
        #
        #   • **Pas d'amnésie** — promu, l'agent conserve son endurance acquise. Il arrive
        #     sur le palier suivant armé de sa capacité à chercher longtemps, au lieu de
        #     s'effondrer à chaque promotion.
        #   • **Pas d'écrasement par le passé** — l'EMA pèse davantage le récent que les
        #     jours lointains de la naissance : quand les durées s'étirent sur une carte
        #     neuve, la référence glisse vers le haut sans rupture.
        #   • **Zéro division par zéro** — 20 échecs d'affilée ne détruisent pas la mémoire
        #     des réussites antérieures, donc le contraste reste estimable.
        #
        # `None` = jamais vécu. On ne pose PAS de valeur de départ : la première expérience
        # l'amorce (voir `_lisser`), au lieu qu'un chiffre inventé doive être « oublié ».
        self.duree_reussite_vie = None   # EMA des durées d'épisodes RÉUSSIS
        self.duree_echec_vie = None      # EMA des durées d'épisodes RATÉS
        self.capital_endurance = 0.0     # exposant : patience = patience_min × exp(capital)

    def _lisser(self, ancienne, valeur):
        """EMA à amorçage par la première mesure — jamais par une constante posée."""
        if ancienne is None:
            return float(valeur)
        return ancienne + (float(valeur) - ancienne) * INERTIE_TRAIT_ENDURANCE

    def augmenter_patience_de_base_definitivement(self):
        """Phase C (v17.0), refondue en v41.30 — LE GAIN EST DÉRIVÉ DE L'ÉCART VÉCU,
        et son RENDEMENT DÉCROÎT EXPONENTIELLEMENT.

        🔴 Ce que faisait l'ancienne version : `patience_min += 10`, plafonné à 350. Gain
        CONSTANT jusqu'au mur, puis NUL. Mesuré sur la campagne v41.29 : **9 graines sur
        10 collées au plafond exact**, saturées après ~30 victoires, puis 1200 jours sans
        que rien ne bouge.

        Deux corrections, toutes deux dérivées :

        (1) **COMBIEN mérite-t-il ?** — plus par un compteur d'événements (+10 quelle que
            soit la difficulté), mais par l'ÉCART MESURÉ entre le temps qu'il faut pour
            réussir et celui au bout duquel il abandonne. Si ses réussites arrivent à 80
            ticks et qu'il coupe à 100, attendre plus ne sert à rien → gain quasi nul. Si
            elles arrivent à 300 alors qu'il coupe à 150, il tranche systématiquement trop
            tôt → gain fort. La patience se cale sur ce que le MONDE exige réellement,
            mesuré par l'agent lui-même.

        (2) **RENDEMENT DÉCROISSANT, SANS PLAFOND** — formulation utilisateur : *« un genre
            d'exponentielle qui part de 1 jusqu'à l'infini, mais exponentiel : plus tu
            gagnes en patience, plus c'est dur d'en gagner à nouveau. »* Le gain est donc
            divisé par le capital déjà acquis. La patience croît sans borne, mais chaque
            palier coûte plus cher que le précédent — c'est le motif déjà employé par la
            dérive métabolique (« une PENTE QUI DEVIENT VERTICALE, pas une barrière »).
        """
        if not ENDURANCE_DERIVEE_ACTIVE:
            # Témoin `--patience-fossile` : le régime EXACT d'avant v41.30 (gain constant
            # +10, plafonné à 350). Fidèle, pas approximatif — sinon le témoin mesure une
            # troisième chose.
            self.patience_min = min(PATIENCE_MAX_FOSSILE,
                                    self.patience_min + BOOST_PATIENCE_FOSSILE)
            return

        # Sans les deux mesures, aucun écart n'est estimable : on ne crédite RIEN plutôt
        # que d'inventer un gain (même discipline que « une journée stérile ne distille
        # rien », v37.1).
        if self.duree_reussite_vie is None or self.duree_echec_vie is None:
            return

        # L'écart est RELATIF à ce que l'agent tient déjà : un retard de 50 ticks n'a pas
        # le même sens pour qui abandonne à 60 ou à 600. Négatif (il réussit plus vite
        # qu'il n'abandonne) ⇒ rien à gagner.
        reference = max(1.0, self.duree_echec_vie)
        contraste = max(0.0, (self.duree_reussite_vie - self.duree_echec_vie) / reference)
        if contraste <= 0.0:
            return

        # Rendement décroissant : divisé par le capital déjà acquis. Le +1 évite la
        # division par zéro à la naissance ET donne au premier gain son plein effet.
        self.capital_endurance += contraste / (1.0 + self.capital_endurance)

    def patience_de_vie(self) -> float:
        """La patience de base, sans borne supérieure — le monde la plafonnera."""
        if not ENDURANCE_DERIVEE_ACTIVE:
            return float(min(PATIENCE_MAX_FOSSILE, self.patience_min))
        return self.patience_min * math.exp(self.capital_endurance)

    def enregistrer_episode(self, reussi: bool, nombre_ticks: int):
        self.historique_succes.append(1.0 if reussi else 0.0)
        # v41.30 — LES RATÉS SONT ENREGISTRÉS EUX AUSSI. Avant, seules les réussites
        # l'étaient : mesurer un ÉCART avec une seule moitié était impossible.
        if reussi:
            self.historique_vitesses.append(nombre_ticks)
            self.duree_reussite_vie = self._lisser(self.duree_reussite_vie, nombre_ticks)
        else:
            self.duree_echec_vie = self._lisser(self.duree_echec_vie, nombre_ticks)

        if len(self.historique_succes) > self.fenetre_historique:
            self.historique_succes.pop(0)
        if len(self.historique_vitesses) > self.fenetre_historique:
            self.historique_vitesses.pop(0)

    def obtenir_seuil_patience(self, facteur_complexite_sous_seuil: float = 1.0) -> int:
        """v41.30 — L'ÉCHELLE EST LA PATIENCE DE VIE, plus une borne posée.

        Les trois usages de `patience_max` disparaissent ensemble : il servait à la fois
        de valeur de départ, d'échelle de normalisation de la vitesse et de plafond. Tous
        trois sont remplacés par `patience_de_vie()`, dérivée du vécu — et le plafond
        réel est appliqué en aval par `_patience_budget` (`max_steps` de la carte).
        """
        echelle = self.patience_de_vie()

        if not self.historique_succes:
            # Naissance : rien de vécu, donc rien à moduler. L'agent part de son endurance
            # de base — c'est `_patience_budget` qui lui accordera l'épisode entier tant
            # qu'il n'a démontré aucune maîtrise (« le bénéfice du doute va au temps »).
            base_patience = echelle
        else:
            taux_succes = sum(self.historique_succes) / len(self.historique_succes)

            if self.historique_vitesses:
                vitesse_moyenne = sum(self.historique_vitesses) / len(self.historique_vitesses)
                facteur_vitesse = max(0.2, 1.0 - (vitesse_moyenne / max(1.0, echelle)))
            else:
                facteur_vitesse = 0.5

            potentiometre = 0.7 * taux_succes + 0.3 * facteur_vitesse
            base_patience = self.patience_min + potentiometre * max(0.0, echelle - self.patience_min)

        patience_effective = base_patience * facteur_complexite_sous_seuil
        # Le seul plafond ici est celui des contextes SANS carte ; le budget natif de la
        # carte (`max_steps`) est appliqué en aval par `_patience_budget`.
        return int(max(self.patience_min, min(self.plafond_hors_monde, patience_effective)))


class GestionnaireCursusAbnegation:
    """
    Gestionnaire de cursus à deux sous-seuils (v16.0), spécifique au cursus à 7 paliers
    DoorKey (voir DetecteurJalonsDoorKey). Remplace la validation de palier par taux de
    réussite journalier (SEUIL_MAITRISE_PALIER) par un compteur cumulatif de succès du
    palier cible, indépendant des frontières de journée :

    - Sous-Seuil 1 (Amorçage) : les 2 premiers succès du palier valident l'acquisition
      de base, sans exigence temporelle particulière (facteur de complexité = 1.0).
    - Sous-Seuil 2 (Consolidation/Abnégation) : les 2 succès suivants, sous une patience
      étirée (`COEFF_ABNEGATION_SOUS_SEUIL_2`) — l'agent doit démontrer qu'il peut
      persévérer plus longtemps sur le même palier avant d'être promu au suivant.

    4 succès au total (2+2) sont donc requis pour promouvoir un palier, contre 1 seul
    jour à ≥80% de réussite auparavant : la promotion devient plus lente mais plus
    robuste, moins sensible à une bonne journée isolée.
    """
    def __init__(self, succes_par_sous_seuil=2, coeff_abnegation_sous_seuil_2=1.6):
        self.succes_par_sous_seuil = succes_par_sous_seuil
        self.coeff_abnegation_sous_seuil_2 = coeff_abnegation_sous_seuil_2
        self.sous_seuil_actuel = 1  # 1 (Amorçage) ou 2 (Consolidation/Abnégation)
        self.succes_sous_seuil_courant = 0

    def reinitialiser_palier(self):
        """À appeler quand palier_cible change (nouveau palier = nouvel amorçage)."""
        self.sous_seuil_actuel = 1
        self.succes_sous_seuil_courant = 0

    def obtenir_facteur_complexite(self) -> float:
        return 1.0 if self.sous_seuil_actuel == 1 else self.coeff_abnegation_sous_seuil_2

    def enregistrer_resultat_episode(self, reussi_palier: bool):
        """Retourne (promotion_palier_validee, message_log ou None)."""
        if not reussi_palier:
            return False, None

        self.succes_sous_seuil_courant += 1
        if self.succes_sous_seuil_courant < self.succes_par_sous_seuil:
            return False, None

        if self.sous_seuil_actuel == 1:
            self.sous_seuil_actuel = 2
            self.succes_sous_seuil_courant = 0
            return False, "🎯 [PROGRESSION INTERMÉDIAIRE] Passage au Sous-Seuil 2 (Abnégation)"

        self.succes_sous_seuil_courant = 0
        return True, "🎓 [PROMOTION DE PALIER] 4/4 succès validés (Amorçage + Abnégation)"


# --- 3d. VOLONTÉ ÉMERGENTE : SOUS-QUÊTES INTRINSÈQUES & SURSAUT (v17.0, actifs en Mode Libre) ---
class DetecteurCuriositeJEPA:
    """
    Sous-objectif intrinsèque généré par le Modèle du Monde lui-même (v17.0) : en Mode
    Libre, il n'y a plus de récompense externe de guidage (RECOMPENSE_APPROCHE_BUT). Au
    lieu d'attendre passivement la récompense terminale de l'environnement, l'agent doit
    trouver sa propre motivation à explorer — ce détecteur transforme une erreur de
    prédiction JEPA anormalement élevée (une "zone d'ombre", un état que le World Model
    n'a pas su anticiper) en une micro-récompense de curiosité.

    Distinct de `dopamine_curiosite` (déjà existant, un scaling continu et global de la
    teneur en dopamine par l'erreur JEPA du tick) : ce détecteur ne s'active que sur un
    DÉPASSEMENT relatif à la moyenne récente de l'agent (sa propre notion de surprise,
    pas un seuil absolu), et ne produit une micro-récompense ponctuelle que si l'écart
    est franchi — un vrai signal de sous-quête, pas un simple facteur d'échelle.
    """
    def __init__(self, fenetre_historique=50, facteur_seuil_surprise=1.5,
                 micro_recompense=0.04, poids_choc=0.15):
        self.fenetre_historique = fenetre_historique
        self.facteur_seuil_surprise = facteur_seuil_surprise
        self.micro_recompense = micro_recompense
        self.poids_choc = poids_choc
        self.historique_erreurs = []

    def evaluer_tick(self, erreur_jepa_tick: float):
        """Retourne (sous_objectif_intrinseque, poids_choc). N'enregistre l'erreur dans
        l'historique qu'APRÈS comparaison, pour que le seuil reflète la surprise passée,
        pas le tick courant lui-même."""
        sous_objectif, poids = 0.0, 0.0
        if len(self.historique_erreurs) >= 5:
            moyenne_recente = sum(self.historique_erreurs) / len(self.historique_erreurs)
            if moyenne_recente > 1e-8 and erreur_jepa_tick > moyenne_recente * self.facteur_seuil_surprise:
                sous_objectif, poids = self.micro_recompense, self.poids_choc

        self.historique_erreurs.append(erreur_jepa_tick)
        if len(self.historique_erreurs) > self.fenetre_historique:
            self.historique_erreurs.pop(0)

        return sous_objectif, poids


class ModuleSursautVolonte:
    """
    Le Muscle de la Volonté (v17.0) : quand l'agent est sur le point d'abandonner par
    épuisement de patience (95% du seuil du jour, voir ModuleAcceptationAbnegation), au
    lieu de le laisser s'effondrer, un SURSAUT est déclenché — jamais une solution
    donnée (pas de béquille de triche), mais un renfort de ses propres ressources :

    1. Un boost dopaminergique ponctuel lié à l'effort (`BOOST_SECOND_SOUFFLE`).
    2. Une extension mathématique de la patience de l'épisode courant
       (`EXTENSION_PATIENCE_SURSAUT` ticks), plafonnée au budget natif de la carte
       (`max_steps`, v41.30) — plus à une constante posée.

    Volontairement OMIS par rapport à la spécification initiale : le "chuchotement
    d'indice visuel" (illuminer l'objet pertinent dans le champ de vision) — cela
    demanderait de modifier l'observation renvoyée par MiniGrid à l'agent, hors de
    portée de l'architecture actuelle sans toucher au moteur de rendu de l'environnement
    lui-même. Le sursaut reste donc purement interne (dopamine + temps), jamais une
    correction de la perception.

    Un seul sursaut par épisode (`disponible`) : ce n'est pas un mécanisme qui se
    répète en boucle jusqu'à épuisement total, sinon la patience s'étirerait sans limite
    réelle.
    """
    def __init__(self, seuil_declenchement=0.95, boost_second_souffle=0.5,
                 extension_patience=50):
        self.seuil_declenchement = seuil_declenchement
        self.boost_second_souffle = boost_second_souffle
        self.extension_patience = extension_patience
        self.disponible = True

    def reinitialiser_episode(self):
        self.disponible = True

    def evaluer_tick(self, tick_episode: int, patience_courante: int, patience_max: int,
                     fin_episode: bool, facteur: float = 1.0):
        """Retourne (declenche: bool, nouvelle_patience: int).

        v40.1-fix4 — `facteur` (∈ [0, 1], l'envie de vivre) dose l'AMPLEUR de l'extension
        sans toucher au déclenchement : l'événement reste discret, sa force est continue.
        """
        if fin_episode or not self.disponible:
            return False, patience_courante
        if tick_episode < patience_courante * self.seuil_declenchement:
            return False, patience_courante

        self.disponible = False
        extension = int(round(self.extension_patience * facteur))
        nouvelle_patience = min(patience_max, patience_courante + extension)
        return True, nouvelle_patience


# --- 3e. MOTEUR HOMÉOSTATIQUE BIOLOGIQUE (v18.0, générique, actif sur tous les niveaux) ---
class BiologicalHomeostasisEngine:
    """
    Régulation biologique par Réduction de Drive (Hull, v18.0) : trois jauges vitales
    (satiété, hydratation, stimulation) se dégradent à chaque tick, indépendamment de
    la teneur en dopamine existante. Le déficit homéostatique global D(t) est la somme
    des écarts au carré à l'équilibre idéal (1.0) ; la récompense biologique r_bio est
    la RÉDUCTION de ce déficit entre deux ticks — positive si l'agent comble un manque,
    négative s'il continue de se dégrader.

    Volontairement PAS de réservoir de dopamine séparé ici (contrairement au pseudo-code
    initial qui introduisait un second self.dopamine) : r_bio est injecté dans le
    réservoir TENEUR_DOPAMINE déjà existant (voir boucle principale) via le même
    mécanisme poids_evenement/TAUX_CHOC_BASE que les autres détecteurs, pour ne jamais
    faire cohabiter deux notions concurrentes de "motivation".

    Dès qu'une jauge passe sous SEUIL_CRITIQUE_BIO, une quête intrinsèque est générée
    (voir eval_biological_quests) — la stimulation reste volontairement la moins
    prioritaire des trois : mourir de faim/soif est un risque plus urgent que
    s'ennuyer.

    Moteur Métabolique 20/80 (v19.0) : le coût énergétique d'un tick n'est plus une
    constante fixe (COUT_ACTION_METABOLIQUE de la v18.0) mais une fusion pondérée de
    deux efforts distincts :

    - Effort Corporel (80% du poids) : dépend du TYPE d'action réellement exécutée —
      tourner coûte peu, avancer coûte moyen, manipuler un objet (pickup/drop) coûte
      cher. Recalé sur les vraies actions MiniGrid (Actions.left/right/forward/pickup/
      drop/toggle/done), pas sur un mapping numérique arbitraire.
    - Effort Cognitif (20% du poids) : dérivé de `force_planification` et de la somme
      des horizons du rollout mental (HORIZONS_PLANIFICATION) — en Mode Libre
      (force_planification=0.85), le Système 2 pèse structurellement plus lourd qu'en
      Mode Guidé (0.5), reflétant une planification mentale plus intense sans
      inventer de notion de "profondeur MCTS variable" qui n'existe pas dans
      l'architecture réelle (le rollout est toujours aux horizons fixes 1,3,7).
    """
    # v41.21 — LES DEUX POIDS NE SONT PLUS POSÉS : ILS DÉRIVENT D'UNE LOI BIOLOGIQUE.
    #
    # Chez l'humain adulte, le cerveau pèse ~2 % de la masse corporelle et consomme ~20 %
    # de l'énergie au repos. Ces deux nombres sont des MESURES sur le vivant, pas des
    # réglages du projet — et ils suffisent à produire tout le reste :
    #
    #   POIDS_CERVEAU = FRACTION_ENERGIE_CERVEAU        = 0,20
    #   POIDS_CORPS   = 1 − FRACTION_ENERGIE_CERVEAU    = 0,80
    #
    # Les valeurs numériques sont inchangées (le « 20/80 » de la v19.0 tombait juste),
    # mais leur STATUT change : ce ne sont plus deux constantes arbitraires tolérées comme
    # facteurs d'échelle, ce sont les conséquences d'une loi mesurable et vérifiable.
    #
    # Le rapport 20/2 = 10 est la DENSITÉ MÉTABOLIQUE cérébrale : un gramme de cerveau
    # coûte dix grammes de corps. C'est ce qui rend la neurogenèse réellement chère, et
    # c'est la loi qui donne son sens au coût moteur physique (v41.20).
    FRACTION_MASSE_CERVEAU = 0.02      # mesure biologique : 2 % de la masse
    FRACTION_ENERGIE_CERVEAU = 0.20    # mesure biologique : 20 % de l'énergie au repos
    POIDS_CERVEAU = FRACTION_ENERGIE_CERVEAU
    POIDS_CORPS = 1.0 - FRACTION_ENERGIE_CERVEAU

    # Coût corporel par action MiniGrid réelle (Actions.left=0, right=1, forward=2,
    # pickup=3, drop=4, toggle=5, done=6) — tourner est faible, avancer moyen,
    # manipuler (pickup/drop) est le plus coûteux physiquement, toggle intermédiaire.
    COUT_CORPOREL_PAR_ACTION = {
        0: 0.2,  # left
        1: 0.2,  # right
        2: 0.5,  # forward
        3: 0.8,  # pickup
        4: 0.8,  # drop
        5: 0.6,  # toggle
        6: 0.1,  # done — quasi inaction
    }

    def __init__(self, taux_satiete=0.008, taux_hydratation=0.005, taux_stimulation=0.012,
                 seuil_critique=0.35, ticks_par_jour=None):
        self.satiete = 1.0
        self.hydratation = 1.0
        self.stimulation = 1.0
        # v41.2 — LE SECOND ÉTAGE. `energie` est le FLUX réellement dépensé pour agir ;
        # satiété et hydratation ne sont que le STOCK qui le ravitaille. Ce découplage
        # produit gratuitement deux états qu'une jauge unique ne peut pas représenter :
        # l'estomac plein mais l'énergie basse (le coup de barre), et la faim avec de
        # l'énergie encore disponible (le sursis).
        self.energie = 1.0
        # v41.2-fix8 — la RÉSERVE (la graisse). Naît à zéro : un nouveau-né n'a pas encore
        # constitué d'avance, il la construit en mangeant plus que son besoin du moment.
        self.reserve = 0.0
        # Dérive adaptative du métabolisme (log-écart à la norme d'espèce). 0.0 = norme.
        # Sérialisée dans le `.brain` ; un cerveau antérieur repart à 0.0, donc au
        # métabolisme d'espèce, sans greffe ni erreur.
        self.derive_metabolique = 0.0
        self.derive_kappa = 0.0
        # v41.30 — LE RYTHME VÉCU : combien d'épisodes l'agent joue réellement par journée,
        # lissé sur sa vie. C'est ce qui remplace `EPISODES_PAR_JOURNEE_REFERENCE = 4.0`.
        #
        # Naît à la valeur PRUDENTE (1 épisode/jour) : au jour 1 l'agent n'a rien vécu, et
        # supposer peu d'occasions est le cas défavorable — même discipline que le plancher
        # vital. Sérialisé dans le `.brain` avec lecture défensive `.get()` : un cerveau
        # antérieur repart à la naissance, sans greffe ni erreur.
        self.rythme_episodes = EPISODES_PAR_JOURNEE_NAISSANCE
        # v41.25 — LA NOCICEPTION THERMIQUE. La chaleur ressentie au tick courant, dans
        # [0,1], lue depuis le champ de rayonnement (bus_sensoriel.lire_thermoception).
        # Ce n'est PAS un sens de plus : le sens existe depuis la v41.11. C'est le
        # CHAINON MANQUANT — jusqu'ici l'agent percevait la chaleur sans qu'elle lui
        # coûte quoi que ce soit, donc sans aucune raison de l'éviter (mesuré sur
        # 6 graines : valence de 'lava' à +0,059 / +0,066, soit celle de l'EAU).
        # Écrite une fois par tick AVANT calculer_deficit ; 0.0 = ambiante, et un monde
        # sans source brûlante laisse ce terme rigoureusement nul (ablation VIDE, pas
        # négative — la distinction est celle du §4 de la règle de mesure).
        self.chaleur = 0.0
        # --- v41.26 : LA THERMOHOMÉOSTASIE — la douleur devient GRADUÉE ---
        #
        # 🔴 CE QUE ÇA CORRIGE. En v41.25 la douleur valait `T²`, donc elle était NON NULLE
        # PARTOUT : mesuré sur les cartes du banc, **77 % des cases libres** portent une
        # chaleur > 0,25 et **100 %** une chaleur > 0,10. L'agent n'avait donc **aucun lieu
        # de repos** — son déficit restait creusé en permanence, `r_bio` négatif partout, et
        # il fuyait sans jamais pouvoir cesser de fuir. Conséquence mesurée : **−26 % de
        # ressources récoltées** (8,88 contre 11,98/jour), énergie 0,156 contre 0,259, donc
        # vigueur au plancher et C2 éteint à ~97 %.
        #
        # ⚠️ La cause n'était PAS métabolique : `chaleur` ne touche ni l'énergie, ni la
        # satiété, ni la dépense — vérifié. C'était **comportemental** : l'agent fuyait le
        # danger, et sur ces cartes les ressources sont à 1,23 case de la lave en moyenne.
        # Fuir la lave, c'est fuir le garde-manger.
        #
        # LA FORME (gradation utilisateur, 18/08) :
        #   1. « ça va, c'est chaud »            → douleur RIGOUREUSEMENT NULLE
        #   2. « gênant mais supportable »       → croissance très lente
        #   3. « douloureux, tenable qq secondes »→ croissance rapide ET cumul temporel
        #   4. « intense, recul réflexe + dégât »→ explosif
        #
        # `chaleur_habituee` : le niveau thermique auquel CET agent s'est habitué. C'est un
        # CLIQUET, exactement comme `reference_choc_dopamine` (v37.1-fix1) — montée rapide,
        # descente ~50× plus lente. Aucune structure nouvelle n'est introduite : c'est la
        # même dynamique, déjà validée, appliquée à une autre grandeur. C'est ce qui crée le
        # palier 1 SANS poser de seuil : le zéro est DÉRIVÉ du vécu de l'agent, pas décrété.
        self.chaleur_habituee = 0.0
        # --- v41.27 : LA DOULEUR UNIQUE (refonte, décision utilisateur du 19/08) ---
        #
        # 🔴 CE QUE ÇA REMPLACE. Il existait DEUX douleurs sans rapport : `MALUS_DOULEUR`
        # (−0,01, constante, dans la récompense) pour le mur, et `chaleur²` (dans le
        # déficit) pour le feu. Deux canaux, deux échelles, deux traitements — l'empilement
        # que le projet refuse. Formulation utilisateur : *« le seul élément à gérer dans
        # la gestion du corps, c'est la douleur, avec ses facteurs de points de douleur, de
        # temps, et sa dégradation proportionnelle au pic et au type »*.
        #
        # LA FORME. Un SEUL état corporel, alimenté par des couples (pic, dégradation) que
        # les organes sensoriels fournissent. Le « type » de douleur n'est PAS un canal :
        # c'est le couple lui-même.
        #
        #     douleur(t) = douleur(t−1) × (1 − dégradation(t)) + pic(t)
        #
        #   • brûlure      : pic ∝ chaleur,          dégradation LENTE   → s'installe
        #   • choc mural   : pic ∝ vitesse d'impact, dégradation RAPIDE  → passe vite
        #
        # ⚠️ LE TEMPS N'AUGMENTE PAS LA DOULEUR AIGUË, IL RALLONGE LA RÉCUPÉRATION.
        # C'est la correction utilisateur du 19/08, et c'est l'inverse exact de la v41.26 :
        # sa `brulure` s'accumulait jusqu'à saturer à 0,375 (point fixe pic/dissipation
        # = ×6,67), ce qui ANNULAIT le gain de la gradation — mesuré 0,2365 de douleur en
        # run contre 0,087 attendu au banc. Ici l'exposition n'alimente pas le pic : elle
        # ralentit la descente.
        self.douleur = 0.0
        # Exposition cumulée, dans [0,1] : mémoire de « combien de temps ça a fait mal ».
        # C'est elle qui ralentit la récupération, jamais qui augmente le pic.
        self.exposition = 0.0
        # `brulure` : la douleur ACCUMULÉE. C'est ce qui donne un sens à « tenable quelques
        # secondes » — rester coûte, partir soulage. Sans elle, un tick au contact et vingt
        # ticks au contact coûtent identiquement, ce qui est faux de toute brûlure réelle.
        self.brulure = 0.0
        self.cause_mort = None

        # v41.2 — L'ÉCHELLE TEMPORELLE. Les taux sont exprimés PAR JOURNÉE et divisés par
        # la longueur réelle de la journée, pour que le VÉCU (3 repas/journée) soit
        # invariant : un run de réglage à 400 ticks doit produire le même profil de jauges,
        # en pourcentage de journée, qu'un run cible à 3600 ticks.
        # `ticks_par_jour=None` ⇒ on retombe sur les anciens taux par tick (compatibilité).
        self.ticks_par_jour = ticks_par_jour
        if ticks_par_jour:
            self.taux_satiete = TAUX_SATIETE_JOUR / float(ticks_par_jour)
            self.taux_hydratation = TAUX_HYDRATATION_JOUR / float(ticks_par_jour)
            self.taux_stimulation = TAUX_STIMULATION_JOUR / float(ticks_par_jour)
            self.depense_energie = DEPENSE_ENERGIE_JOUR / float(ticks_par_jour)
            self.debit_digestif = DEBIT_DIGESTIF_JOUR / float(ticks_par_jour)
            self.debit_reserve = (RESERVE_MAX * FRACTION_RESERVE_MOBILISABLE_JOUR
                                  / float(ticks_par_jour))
        else:
            self.taux_satiete = taux_satiete
            self.taux_hydratation = taux_hydratation
            self.taux_stimulation = taux_stimulation
            self.depense_energie = DEPENSE_ENERGIE_JOUR / 400.0
            self.debit_digestif = DEBIT_DIGESTIF_JOUR / 400.0
            self.debit_reserve = RESERVE_MAX * FRACTION_RESERVE_MOBILISABLE_JOUR / 400.0
        self.seuil_critique = seuil_critique
        self.quete_active = None

    # --- v41.2 : les grandeurs DÉRIVÉES (aucune n'est une constante de fonctionnement) ---

    def kappa_effectif(self) -> float:
        """L'exposant de non-linéarité, dérivé de la norme d'espèce et de la dérive
        individuelle. Borné : un métabolisme peut s'optimiser, jamais s'affranchir."""
        return float(np.clip(KAPPA_VIGUEUR * math.exp(self.derive_kappa),
                             KAPPA_VIGUEUR_MIN, KAPPA_VIGUEUR_MAX))

    def vigueur(self) -> float:
        """LE SEUIL NON LINÉAIRE — `énergie ** κ`, borné par le bas.

        Ce n'est PAS un seuil : aucun `if énergie < X` n'existe nulle part. C'est une
        puissance, donc une dégradation continue mais ACCÉLÉRANTE (κ=2 : énergie 0.5 →
        vigueur 0.25). Tous les consommateurs — C1, C2, le déficit, la plasticité — lisent
        cette seule grandeur, plutôt que d'être couplés un par un à l'énergie.

        Le plancher est indispensable : sans lui, vigueur→0 annulerait C1 ET C2, donc
        produirait des logits tous nuls, donc une action ALÉATOIRE. Un agent mourant doit
        rester cohérent — diminué, jamais aléatoire."""
        return float(np.clip(self.energie ** self.kappa_effectif(),
                             VIGUEUR_PLANCHER, 1.0))

    def reserve_mobilisable(self) -> float:
        """Ce que le stock peut encore rendre en énergie. C'est la CONDITION DE
        SOLVABILITÉ qui porte la règle « se reposer sans manger = mourir » : se reposer
        abaisse la dépense, mais ne crée aucune matière. Satiété vide ⇒ réserve nulle ⇒
        l'énergie descend quoi que fasse l'agent. Aucun `if` n'exprime cette règle : elle
        est arithmétique."""
        return self.satiete * RENDEMENT_CONVERSION * math.exp(self.derive_metabolique)

    def reinitialiser_episode(self):
        """Les jauges ne se réinitialisent PAS à chaque épisode (contrairement aux
        détecteurs de position) : la faim/soif de l'agent est un état continu qui
        traverse les épisodes au sein d'une même journée, cohérent avec un métabolisme
        réel plutôt qu'un compteur remis à zéro à chaque reset MiniGrid.

        v41.26 — EXCEPTION : la `brulure` accumulée, elle, repart à zéro. Ce n'est pas une
        jauge métabolique mais une LÉSION LOCALE, et au `reset()` l'agent est téléporté sur
        une carte régénérée : conserver la brûlure du dernier tick de l'épisode précédent
        ferait payer un corps qui n'existe plus. Même raison que `_odeurs_precedentes`
        (v32.0) et `_chaleur_precedente` (v41.11), remis à `None` pour ce motif exact.

        ⚠️ `chaleur_habituee` SURVIT, elle : c'est un apprentissage sur la vie de l'agent,
        pas un état corporel — au même titre que `reference_choc_dopamine`, qui traverse
        les épisodes ET les journées."""
        self.brulure = 0.0
        # v41.27 — la douleur et son exposition sont des états du CORPS : au `reset()`
        # l'agent est téléporté, le corps blessé n'existe plus.
        self.douleur = 0.0
        self.exposition = 0.0

    def encaisser_douleur(self, pic: float, demi_vie_type: float):
        """v41.27 — LE POINT D'ENTRÉE UNIQUE DE TOUTE DOULEUR.

        `pic`            : l'intensité de l'événement, dans [0,1]. Chaleur ressentie pour
                           une brûlure, vitesse d'impact pour un choc — c'est à l'organe
                           sensoriel de le fournir, pas au cœur de le deviner.
        `demi_vie_type`  : en ticks, la vitesse de récupération PROPRE AU TYPE. Courte pour
                           un choc (ça passe), longue pour une brûlure (ça s'installe).
                           C'est le seul endroit où « le type » existe — et c'est un
                           NOMBRE, jamais un nom : `noyau.py` ne sait pas ce qu'est la lave.

        --- L'indexation exponentielle, dans les deux sens (formulation utilisateur) ---

        (1) **Le pic SATURE.** `douleur += pic × (1 − douleur)` : plus on a déjà mal, moins
            un surcroît ajoute. Un corps déjà au maximum ne peut pas avoir « deux fois plus
            mal ». Borné dans [0,1] par construction, sans aucun `clip`.

        (2) **La récupération RALENTIT avec l'exposition ET avec l'intensité.** C'est la
            correction utilisateur du 19/08 : *« ce n'est pas que la douleur prolongée fait
            plus mal, c'est que le temps de récupération est plus long à redescendre »*.

                dégradation = (1/demi_vie) × exp(−(exposition + douleur))

            Un choc bref sur un corps reposé s'efface en quelques ticks ; la même douleur
            sur un corps déjà éprouvé traîne des dizaines de ticks.

        ⚠️ CE QUI EST INTERDIT ICI : que l'exposition alimente le PIC. C'est le défaut
        v41.26 — la brûlure accumulée saturait à `pic/dissipation` (×6,67) et amplifiait un
        état permanent au lieu de mémoriser un événement. Mesuré : douleur réelle 0,2365
        contre 0,087 attendu. L'exposition ne doit toucher QUE la vitesse de descente.
        """
        pic = max(0.0, min(1.0, float(pic)))
        # (1) Saturation du pic — l'exponentielle « vers le haut ».
        self.douleur += pic * (1.0 - self.douleur)
        # L'exposition monte quand ça fait mal, redescend quand ça ne fait plus mal. Même
        # échelle temporelle que la douleur elle-même, donc rien de nouveau à calibrer.
        self.exposition += (pic - self.exposition) * TAUX_EXPOSITION_DOULEUR
        # (2) Récupération — l'exponentielle « vers le bas ». Un corps éprouvé récupère
        # lentement ; un corps neuf récupère vite.
        demi_vie = max(1.0, float(demi_vie_type))
        degradation = (1.0 / demi_vie) * math.exp(-(self.exposition + self.douleur))
        self.douleur = max(0.0, self.douleur - self.douleur * degradation)

    def douleur_corporelle(self) -> float:
        """v41.27 — l'état douloureux du corps, dans [0,1]. Lecture pure, aucun effet de
        bord (même discipline que `chaleur_seule` : une grandeur consultée plusieurs fois
        par tick ne doit jamais faire avancer un état — c'est le bug v41.25-fix1)."""
        return float(self.douleur)

    def douleur_thermique(self) -> float:
        """v41.26 — LA DOULEUR GRADUÉE, dérivée du vécu de l'agent.

        Retourne la charge nociceptive dans [0,1], somme de deux termes :
          • l'INSTANT  : l'excès thermique au-dessus de ce à quoi l'agent est habitué,
                         élevé au cube — quasi nul tant qu'on n'est pas près, explosif
                         au contact ;
          • la BRÛLURE : ce même instant ACCUMULÉ tant qu'on reste, dissipé quand on part.

        Les quatre paliers ÉMERGENT de cette forme, aucun n'est codé (mesuré à λ=0,782,
        habituation 0,20) :

            distance 3+ « ça va »          → 0,0000   ← un vrai ZÉRO, pas un epsilon
            distance 2  « gênant »         → 0,0000
            distance 1  « douloureux »     → 0,033 au 1er tick, 0,162 après 8
            distance 0  « intense »        → 1,0000 immédiatement

        ⚠️ LE ZÉRO EST DÉRIVÉ, JAMAIS POSÉ. `chaleur_habituee` est un niveau vécu, pas un
        seuil : deux agents d'histoires différentes n'ont pas le même palier 1. C'est le
        même mécanisme que `reference_choc_dopamine`, dont le projet a déjà démontré qu'il
        rend le même événement « 100 % remarquable pour un débutant, 11,4 % pour un
        expert ». Ici : la même chaleur est atroce pour qui n'a jamais brûlé, supportable
        pour qui vit près du feu.
        """
        return float(min(1.0, self._douleur_instantanee() + self.brulure))

    def _douleur_instantanee(self) -> float:
        """v41.26 — la charge du tick courant, AVANT accumulation. Lecture pure.

        Le PALIER 1 (« ça va, c'est chaud ») est produit par un seuil de perception
        nociceptive : sous une intensité minimale, le nocicepteur **ne décharge pas du
        tout**, et la douleur vaut ZÉRO EXACT — pas un epsilon. C'est ce qui rend un lieu
        de repos possible, et c'est précisément ce qui manquait en v41.25 (mesuré : **0 %**
        des cases libres étaient indolores, donc l'agent souffrait partout et fuyait sans
        pouvoir s'arrêter).

        ⚠️ Ce seuil n'est PAS une constante posée sur la chaleur : il est RELATIF à
        l'habituation de l'agent, donc dérivé de son vécu. Deux agents d'histoires
        différentes n'ont pas le même palier 1. Un agent neuf (habituation 0) a un seuil
        plancher minimal, ce qui est correct : un nouveau-né sent tout.
        """
        seuil = max(FRACTION_SEUIL_NOCICEPTION * self.chaleur_habituee,
                    SEUIL_NOCICEPTION_PLANCHER)
        if self.chaleur <= seuil:
            return 0.0
        marge = 1.0 - seuil
        if marge <= 1e-9:
            return 0.0
        exces = (self.chaleur - seuil) / marge
        return exces ** EXPOSANT_GRADATION_DOULEUR

    def encaisser_chaleur(self, chaleur: float):
        """v41.26 — met à jour la brûlure accumulée et l'habituation. UNE fois par tick.

        Séparée de `douleur_thermique` (lecture pure) pour la même raison que
        `chaleur_seule` l'est de `lire_thermoception` : une fonction consultée plusieurs
        fois dans un tick ne doit JAMAIS faire avancer un état. C'est le défaut qui a
        produit le bug v41.25-fix1 (la douleur annulée par sa propre soustraction).
        """
        self.chaleur = float(chaleur)
        # Une SEULE définition de la douleur instantanée, partagée avec la lecture pure :
        # dupliquer le calcul serait la porte ouverte à ce que les deux divergent au
        # premier correctif (même discipline que `_champ_thermique` en v41.25).
        instant = self._douleur_instantanee()
        # La brûlure s'accumule tant qu'on reste, se dissipe quand on part.
        self.brulure = float(min(1.0, self.brulure * (1.0 - DISSIPATION_BRULURE) + instant))
        # Habituation : cliquet LENT dans les deux sens.
        #
        # 🔴 CORRECTIF (banc du 18/08, défaut n°1). Une montée IMMÉDIATE — le cliquet de
        # `reference_choc_dopamine` — est ici un contresens : l'habituation rattrapait la
        # chaleur en UN tick, l'excès tombait à zéro, et la brûlure DÉCROISSAIT pendant que
        # l'agent restait dans le feu (mesuré : 0,0956 → 0,0307 en 8 ticks, l'inverse exact
        # du palier 3). Une brûlure ne s'apaise pas parce qu'on reste dedans.
        #
        # L'habituation est une adaptation de LONG TERME (des centaines de ticks), pas une
        # réaction du tick. Montée ~10× plus rapide que la descente : on s'habitue plus vite
        # qu'on ne se déshabitue, ce qui reste la forme d'un cliquet.
        _vitesse = (VITESSE_HABITUATION_MONTEE if self.chaleur > self.chaleur_habituee
                    else 1.0 - INERTIE_OUBLI_HABITUATION)
        self.chaleur_habituee += (self.chaleur - self.chaleur_habituee) * _vitesse

    def calculer_deficit(self) -> float:
        """v41.2 — l'énergie entre dans le déficit comme ÉTAT (le carré de son manque),
        au même titre que les autres jauges, et JAMAIS comme flux.

        ⚠️ Le double comptage était le risque n°3 du chantier (et le §7.2 de
        CONCEPTION_v34) : l'effort est déjà facturé en dépense d'énergie. Il l'est donc
        UNE SEULE FOIS — dépenser fait baisser `energie`, ce qui creuse le déficit, ce qui
        rend `r_bio` négatif. L'effort n'est pas soustrait une seconde fois ailleurs.

        v41.25 — LA DOULEUR EST UN DÉFICIT, pas une pénalité. `+ chaleur**2` ferme la
        boucle nociceptive : la chaleur n'entre PAS comme un malus conditionnel
        (`si mort: -X`, ce que l'invariant v41.11 interdit explicitement), mais comme un
        quatrième manque, au même titre et à la même échelle que la faim ou la soif.

        L'échelle n'est posée par personne. Les trois jauges donnent `(1-x)**2` dans
        [0,1] ; la chaleur donne `T**2` dans [0,1] par construction du champ de
        rayonnement. Aucun coefficient multiplicateur n'est introduit — c'est la
        géométrie de la carte (le `lambda_diffusion_carte` de l'odorat, dérivé de ses
        dimensions) qui règle seule la pente du gradient.

        Ce qui en découle MÉCANIQUEMENT, sans qu'aucune règle ne le décrive : `r_bio` est
        la DÉRIVÉE du déficit (`D(t-1) - D(t)`), donc avancer vers la chaleur produit un
        r_bio négatif proportionnel au rapprochement, et marcher DANS la source (T=1)
        produit un effondrement de ~-1.0 — cinq à dix fois le choc d'un mur. La valence
        de la trace mnésique s'inverse par la seule moyenne des chocs vécus, et C2, qui
        reçoit le corps dans son rollout depuis la v41.13, projette cet effondrement
        avant de s'y jeter.

        ⚠️ PAS de drain de jauge au contact (arbitrage utilisateur explicite) : ce serait
        facturer deux fois le même événement, exactement le risque n°3 écarté plus haut.
        À T=1 le déficit est déjà maximal — la thermodynamique se suffit.
        """
        return ((1.0 - self.satiete) ** 2 + (1.0 - self.hydratation) ** 2
                + (1.0 - self.stimulation) ** 2 + (1.0 - self.energie) ** 2
                + (self.douleur_corporelle() if DOULEUR_THERMIQUE_ACTIVE else 0.0))

    def masse_totale(self, dim_bus: int, porte_objet: bool = False) -> float:
        """v41.20 — LA MASSE ÉMERGENTE. Aucune des trois composantes n'est posée.

        `M_base` dérive de `dim_bus` : un cerveau qui grandit par neurogenèse pèse plus
        lourd et coûte plus cher à déplacer. C'est le compromis évolutif de l'intelligence
        — décision utilisateur explicite, et c'est ce qui évite de poser `M_base = 1.0`,
        qui aurait été la même faute que la table qu'on remplace, mieux déguisée.

        `BUS_REFERENCE_INITIAL` n'est pas un réglage : c'est la taille réelle du bus à la
        naissance, donc l'unité naturelle. Un agent qui n'a jamais fait de neurogenèse a
        `M_base = 1.0` par construction, pas par décret.
        """
        # v41.21 — LE CORPS DÉCOULE DU CERVEAU (loi des 2 % / 98 %).
        #
        # `m_cerveau` est la masse encéphalique, dérivée de `dim_bus`. Le corps qui la
        # porte n'est plus absent du modèle : chez le vivant, le cerveau ne représente que
        # 2 % de la masse totale — les 98 % restants sont le corps qui le transporte.
        # La masse totale est donc `m_cerveau / FRACTION_MASSE_CERVEAU`, ce qui garde la
        # proportion cérébrale rigoureusement constante quelle que soit la neurogenèse.
        #
        # ⚠️ Cette masse totale n'est PAS utilisée telle quelle dans le travail mécanique :
        # elle est rapportée à la masse de naissance (voir `calculer_effort_metabolique`).
        # Ce qui compte pour l'effort est le RATIO de masse, jamais sa valeur absolue —
        # sans quoi le choix de l'unité (le kilo, le gramme) changerait la physique.
        m_cerveau = float(dim_bus) / float(BUS_REFERENCE_INITIAL)
        m_charge = 1.0 if porte_objet else 0.0
        return m_cerveau / self.FRACTION_MASSE_CERVEAU + self.reserve + m_charge

    def calculer_effort_metabolique(self, action_item: int, force_planification: float,
                                     horizons_planification=(1, 3, 7),
                                     dim_bus: int = None, deplacement: bool = None,
                                     rotation: bool = False, porte_objet: bool = False,
                                     erreur_jepa: float = 0.0) -> float:
        """v41.20 — L'EFFORT EST UN TRAVAIL PHYSIQUE, plus une table de sept valeurs.

        Remplace `COUT_CORPOREL_PAR_ACTION` (violation n°1 de la revue du dogme). Le coût
        ne dépend plus de l'INDEX de l'action mais de ce que l'action A RÉELLEMENT FAIT —
        mesuré autour du `env.step` par la sonde v41.19.

        🔴 CE QUE ÇA CORRIGE, mesuré sur 6 graines × 400 jours (2400 nuits) :
        l'ancienne table facturait **0,5016/tick** dont **0,3957 pour des gestes qui ne
        changeaient rien au monde** — une sur-facturation de **×4,73**. `poser` et
        `activer` étaient stériles à **100 %** (28,7 % des ticks) et payés 0,8 et 0,6.
        C'est la cause mécanique de l'hypoglycémie permanente (énergie ~0,04).

        --- La physique, sans une seule constante posée ---

        MASSE      M = dim_bus/BUS_REFERENCE_INITIAL + réserve + charge   (voir masse_totale)
        RAYON      r = ½ case — l'agent occupe EXACTEMENT une case de la grille, quelle
                   que soit sa masse. Le rayon vient de la GÉOMÉTRIE DU MONDE, pas du
                   corps : un organisme plus lourd est plus dense, pas plus large.
        TRAVAIL    translation : W = M × 1.0        (une case = l'unité de la grille)
                   rotation    : W = ½ M r² = M/8   (moment d'inertie d'un disque)
                   stérile     : W = 0.0            (aucun travail : rien n'a bougé)

        ⚠️ DEUX ERREURS ÉCARTÉES ICI, toutes deux mesurées avant correction.

        (1) **La longueur d'arc `(π/2)·r` est fausse.** Avec elle, un agent de masse 7
        paierait **2,3× plus cher pour tourner que pour avancer** — l'inverse exact de
        l'intention. Une rotation sur place ne déplace pas le centre de gravité : son
        travail de translation est NUL, seule l'inertie compte.

        (2) **`r = √(M/π)` (surface = masse) rend la rotation QUADRATIQUE** : `½Mr²`
        devient `M²/2π`, donc un corps 2× plus lourd serait 4× plus dur à tourner. Mesuré :
        ×49 à masse 7. Avec le rayon géométrique, le rapport rotation/translation vaut
        **0,125 quelle que soit la masse** — constant, et dérivé de la grille.

        BASAL      Le coût d'EXISTER n'est PAS facturé ici. `taux_satiete` et
        `taux_hydratation` le prélèvent déjà à chaque tick : l'ajouter serait le double
        comptage que `calculer_deficit` interdit explicitement (risque n°3 du chantier
        v34). Mesuré avant correction : l'effort moyen montait à **2,269** contre 0,639 au
        témoin — un geste stérile coûtait 3,4× l'ancien tarif *parce qu'il portait le
        basal*. L'effort d'ACTION ne porte que le TRAVAIL.

        NORMALISATION  Le travail est rapporté à celui d'un agent NAISSANT qui se déplace
        d'une case (M=1, W=1). Référence interne au modèle, pas un chiffre posé — même
        statut que `ENERGIE_MAX = 1.0`. Elle garde l'échelle historique (~0,5/tick) sur
        laquelle les jauges sont calibrées.

        Rétrocompatibilité : sans `dim_bus` ni `deplacement` (appel à l'ancienne), on
        retombe sur la table historique — c'est le chemin qu'emprunte le drapeau
        d'ablation `--cout-moteur-table`.
        """
        if not COUT_MOTEUR_PHYSIQUE or dim_bus is None or deplacement is None:
            cout_corps = self.COUT_CORPOREL_PAR_ACTION.get(action_item, 0.5)
            cout_cerveau = min(1.0, force_planification * (sum(horizons_planification) / 10.0))
            return self.POIDS_CORPS * cout_corps + self.POIDS_CERVEAU * cout_cerveau

        m_base = float(dim_bus) / float(BUS_REFERENCE_INITIAL)
        # Le TRAVAIL est un RATIO de masse, jamais une masse absolue : l'unité choisie
        # (le « kilo » de ce monde) ne doit pas changer la physique. On rapporte donc la
        # masse courante à celle d'un nouveau-né à vide.
        masse = self.masse_totale(dim_bus, porte_objet) / self.masse_totale(
            BUS_REFERENCE_INITIAL, porte_objet=False)

        # LE RAYON EST DÉRIVÉ DE LA GRILLE, PAS POSÉ. L'agent occupe exactement une case
        # (invariant MiniGrid), donc son rayon est une demi-case : `PAS_GRILLE / 2`. Le
        # `0.5` qui figurait ici en dur n'était que cette division, non écrite.
        rayon = PAS_GRILLE / 2.0

        # --- v41.28 : LE TRAVAIL TENTÉ, PAS LE TRAVAIL RÉUSSI ---
        #
        # 🔴 CE QUE ÇA CORRIGE (mesuré le 20/08 sur 10 runs × 300 jours). L'ancienne
        # version facturait `travail = 0.0` dès que le monde n'avait pas bougé, si bien
        # qu'un geste stérile ne coûtait plus que le basal cérébral : **1,09**, soit le
        # geste LE MOINS CHER du barème, contre **4,00** pour avancer. Le seul geste qui
        # rapproche du but coûtait donc **3,7× plus cher que ne rien faire**, alors que la
        # récompense du but est rare et lointaine et que la punition de l'effort tombe à
        # chaque tick. Résultat : **57,2 % des ticks** partis en gestes stériles, dont
        # `poser`/`activer`/`parler` stériles à **100 %**. L'agent n'était pas irrationnel
        # — il jouait optimalement sous cette fonction de coût.
        #
        # LA PHYSIQUE JUSTE : un geste stérile n'est pas un geste NON FAIT. L'agent a
        # bien contracté ses muscles ; c'est le MONDE qui n'a pas bougé. **Pousser un mur
        # coûte autant que pousser une porte qui s'ouvre.** Le rendement d'un geste change
        # son RÉSULTAT, jamais sa DÉPENSE.
        #
        # ⚠️ RIEN N'EST POSÉ. La nature du geste est lue sur l'API MiniGrid
        # (`unwrapped.actions`, l'énumération du monde lui-même) via les index déjà
        # utilisés partout dans le fichier — pas une table de coûts réintroduite par la
        # bande. Deux familles suffisent, et chacune réutilise un travail DÉJÀ dérivé :
        #   • locomotion tentée (`forward`)      → le travail d'une translation
        #   • manipulation tentée (pickup/drop/  → le travail d'une rotation : tendre le
        #     toggle/done)                          bras déplace une masse sur un rayon
        if deplacement:
            travail = masse * PAS_GRILLE               # translation d'une case
        elif rotation:
            # Moment d'inertie d'un disque homogène : I = ½ M r². Le facteur ½ et le
            # rayon viennent de la géométrie du disque et de la grille — rien n'est réglé.
            travail = 0.5 * masse * rayon * rayon
        elif not TRAVAIL_TENTE_ACTIF:
            travail = 0.0                              # témoin v41.27 : geste stérile gratuit
        elif action_item == ACTION_AVANCER:
            # `forward` qui n'a rien déplacé : l'agent a poussé, le mur n'a pas cédé.
            # Même travail musculaire qu'un pas réussi.
            travail = masse * PAS_GRILLE
        else:
            # Manipulation tentée (ramasser/poser/activer/`done`) : le bras se tend, qu'il
            # attrape quelque chose ou non. Même ordre qu'une rotation, pour la même
            # raison géométrique — une masse déplacée sur un rayon.
            travail = 0.5 * masse * rayon * rayon

        # Le corps ne paie QUE le travail (le basal est déjà prélevé par les jauges).
        e_corps = travail
        # Le cerveau, lui, paie bien un basal : maintenir le réseau en éveil a un coût
        # même sans agir, et il croît avec la taille du cerveau. C'est le vrai prix de la
        # neurogenèse — et il n'est prélevé nulle part ailleurs.
        e_cerveau = m_base * (1.0 + force_planification + erreur_jepa)
        effort = self.POIDS_CORPS * e_corps + self.POIDS_CERVEAU * e_cerveau

        # Référence : le même calcul pour un nouveau-né qui AVANCE d'une case (M=1, W=1,
        # jepa=0). Dérivée des poids du modèle, jamais posée.
        reference = (self.POIDS_CORPS * 1.0
                     + self.POIDS_CERVEAU * (1.0 + force_planification))
        return effort / max(reference, 1e-9)

    def step_metabolisme(self, cout_action: float, erreur_jepa: float, nouvelle_case_visitee: bool,
                         chaleur_apres: float = None):
        """Retourne (r_bio, quete_active_ou_None, effort). `cout_action` est ici l'effort
        métabolique déjà fusionné 20/80 (voir calculer_effort_metabolique), pas une
        constante fixe comme en v18.0.

        v41.25-fix1 — `chaleur_apres` : la chaleur de la case ATTEINTE, appliquée ENTRE
        les deux mesures de déficit.

        🔴 CE QUE ÇA CORRIGE, et c'est une annulation arithmétique pure. `r_bio` est la
        DIFFÉRENCE `deficit_avant − deficit_apres`, et `deficit_avant` est calculé ICI,
        en interne. La v41.25 écrivait `self.chaleur` AVANT d'appeler cette méthode :
        les deux déficits contenaient donc la MÊME valeur de `T²`, qui disparaissait de
        la soustraction. Mesuré : `r_bio` en entrant dans la lave = **−0,000238**, contre
        **−0,000238** sans aucune chaleur — un écart de **0,000000**. La douleur était
        exactement annulée, et 5 paires de graines ont donné des valences identiques à
        la 6ᵉ décimale (y compris sur `FOOD` et `sol`, sans rapport avec la lave — le
        signe qui aurait dû alerter immédiatement).

        ⚠️ Le `r_bio = −1,000` publié en v41.25 était mesuré À LA MAIN, hors du tick réel
        (deux appels à `calculer_deficit` encadrant une affectation). Il n'a jamais été
        produit par le moteur. C'est l'erreur de mesure que le §3 de la règle de mesure
        décrit : un chiffre trop propre, jamais confronté au chemin réel.

        `None` ⇒ comportement inchangé (la chaleur courante vaut pour les deux mesures),
        ce qui garde la compatibilité de tout appelant qui ne la fournit pas."""
        deficit_avant = self.calculer_deficit()
        if chaleur_apres is not None:
            # La chaleur change ENTRE les deux mesures : `deficit_avant` porte celle de
            # la case quittée, `deficit_apres` celle de la case atteinte. C'est cette
            # transition — et elle seule — qui produit la douleur dans `r_bio`.
            # v41.26 — passe par `encaisser_chaleur` : l'habituation avance d'un tick ICI,
            # et nulle part ailleurs.
            self.encaisser_chaleur(chaleur_apres)
            # v41.27 — la chaleur alimente LA douleur unique, avec sa signature de type
            # (pic = excès thermique au-dessus du seuil de perception, récupération LENTE).
            # Le pic passe par `_douleur_instantanee` : le palier 1 (« ça va, c'est chaud »)
            # reste un ZÉRO EXACT, donc une case tiède n'alimente rien du tout.
            # v41.27-fix1 — LA CHALEUR EST UN ÉTAT MAINTENU PAR LA SOURCE, pas un pic
            # que le corps s'infligerait à chaque tick (correction utilisateur du 19/08 :
            # *« selon la distance, la chauffe est un état maintenu, lié au feu ou à la
            # lave, pas qu'au cerveau »*).
            #
            # 🔴 CE QUE ÇA CORRIGE. Traiter la chaleur comme un pic répété faisait monter
            # la douleur à **0,898** en régime permanent (400 ticks à distance 1) — pire
            # que la v41.26 (0,432). Le pic arrivait à chaque tick pendant que la
            # récupération ralentissait : les deux effets se cumulaient au lieu de
            # s'équilibrer. C'est le même piège que la brûlure v41.26, sous une autre forme.
            #
            # LA PHYSIQUE. Un corps ÉVACUE la chaleur ; il ne se lèse que si l'apport
            # DÉPASSE sa capacité d'évacuation. Percevoir et évacuer sont deux capacités
            # distinctes : on sent la chaleur bien avant de brûler.
            #
            #     apport net = max(0, chaleur − CAPACITE_EVACUATION_THERMIQUE)
            #
            # La distance module alors le PALIER D'ÉQUILIBRE, pas seulement la vitesse d'y
            # arriver (mesuré à 400 ticks) : d≥2 → 0,000 · d=1 → 0,166 · d=0 → 0,800.
            # L'agent peut LONGER la lave sans se consumer, mais y entrer brûle à fond.
            _apport = max(0.0, self.chaleur - CAPACITE_EVACUATION_THERMIQUE)
            self.encaisser_douleur(_apport * PENETRATION_THERMIQUE, DEMI_VIE_BRULURE)

        # v41.2 — LA SATIÉTÉ NE SE VIDE PLUS TOUTE SEULE. Dans un modèle à deux étages, le
        # STOCK ne baisse que parce qu'il est DIGÉRÉ (voir plus bas) : lui appliquer en
        # plus une décroissance propre le ferait disparaître deux fois, et un repas ne
        # financerait alors que 59 ticks là où il doit en couvrir 133 (mesuré). C'est le
        # même double comptage que celui écarté dans `calculer_deficit`, côté stock.
        # L'hydratation, elle, se perd bien en continu (transpiration, respiration) : elle
        # n'est pas un carburant mais un COFACTEUR de la conversion.
        # v41.32 — ablation piste C : `SOIF_FIGEE` gèle l'axe hydrique à son maximum.
        # Un seul point d'application, comme le drain lui-même.
        if SOIF_FIGEE:
            self.hydratation = 1.0
        else:
            self.hydratation -= self.taux_hydratation

        bonus_nouveaute = (0.05 if nouvelle_case_visitee else 0.0) + erreur_jepa * 2.0
        self.stimulation += bonus_nouveaute - self.taux_stimulation

        # --- v41.2 : LE SECOND ÉTAGE ---
        # La dépense a une part BASALE incompressible (~65 % dans le vivant) et une part
        # d'effort. Avant v41.2 le basal ne pesait que 12 %, ce qui punissait massivement
        # le mouvement — cohérent avec les 5,5 % de `forward` mesurés. Le coût pénalise
        # donc désormais l'effort SUPPLÉMENTAIRE, sur un fond incompressible : c'est la
        # ligne de flottaison de la v41, posée dans le CORPS au lieu d'être dérivée après.
        # --- v41.16 : L'ÉCONOMIE D'ACTION — le corps ralentit quand l'énergie manque ---
        #
        # 🔴 CE QUE ÇA CORRIGE. La dépense ne consultait JAMAIS l'énergie : un agent à 4 %
        # payait un pas exactement au même prix qu'un agent repu. La loi B du vivant
        # (formulation utilisateur, 17/08) — *« quand l'énergie baisse, l'organisme ne
        # s'agite pas davantage : il ralentit, limite les déplacements inutiles, passe en
        # économie drastique »* — n'existait nulle part dans le code.
        #
        # C'est le pendant indispensable du brain-sparing appliqué juste au-dessus : en
        # retirant `vigueur` des logits, on a rendu sa lucidité à l'agent affamé. Sans ce
        # correctif-ci, `vigueur` ne modulerait plus RIEN d'autre que de la télémétrie —
        # on aurait supprimé la contrainte au lieu de la déplacer, et le corps ne
        # paierait plus jamais son épuisement.
        #
        # LA FORME est dérivée, pas posée : la part d'EFFORT est modulée par la vigueur,
        # le BASAL ne l'est pas. Un organisme épuisé ne peut pas réduire son métabolisme
        # de base (c'est ce qui le tue), mais il peut cesser de courir. À vigueur 0,15, un
        # geste coûteux revient donc presque au prix d'un geste immobile — l'agitation
        # stérile cesse d'être payante sans qu'aucune règle ne l'interdise.
        #
        # ⚠️ Aucune constante nouvelle : `vigueur` et `METABOLISME_BASAL_PART` existent
        # déjà, on les compose. Aucun seuil, aucune branche — un facteur continu de plus.
        _mod_effort = self.vigueur() if ECONOMIE_ACTION_ACTIVE else 1.0
        depense = self.depense_energie * (METABOLISME_BASAL_PART
                                          + (1.0 - METABOLISME_BASAL_PART)
                                            * cout_action * _mod_effort)
        # La conversion est bornée par le DÉBIT DIGESTIF : on ne transforme pas un estomac
        # plein en énergie instantanément. C'est ce qui crée le « coup de barre » (estomac
        # plein, énergie basse) sans qu'aucune règle ne le décrive.
        conversion = min(self.debit_digestif, self.reserve_mobilisable())
        # La digestion consomme le stock qu'elle convertit — sinon l'énergie serait
        # gratuite et la satiété purement décorative.
        self.satiete -= conversion / max(RENDEMENT_CONVERSION, 1e-6)
        # L'hydratation est un COFACTEUR : déshydraté, on convertit mal. C'est le « lien
        # direct entre nourriture, eau et sommeil » demandé — la soif tue plus vite que la
        # faim non pas en vidant l'énergie, mais en empêchant de la FABRIQUER.
        #
        # ⚠️ Le cofacteur est BORNÉ PAR LE BAS, et ce n'est pas un détail : en version
        # linéaire pure (`× hydratation`), le bilan énergétique devenait négatif dès que
        # l'hydratation passait sous 0,50 — quelle que soit la nourriture ingérée. Mesuré
        # sur un run réel de 10 jours : l'énergie s'effondrait à 0,005 au 3ᵉ jour et n'en
        # remontait jamais, alors que l'agent mangeait. Une soif modérée doit RALENTIR la
        # digestion, pas l'ANNULER — sinon la mort par déshydratation devient inévitable
        # bien avant que la jauge d'eau n'atteigne zéro, et aucun apprentissage ne peut la
        # prévenir. Même raisonnement que VIGUEUR_PLANCHER : un organisme diminué reste
        # fonctionnel, il n'est pas éteint.
        cofacteur_hydrique = COFACTEUR_HYDRIQUE_MIN + (1.0 - COFACTEUR_HYDRIQUE_MIN) * self.hydratation
        self.energie += conversion * cofacteur_hydrique - depense

        # --- v41.2-fix8 : LA RÉSERVE (décision utilisateur) ---
        # « Le déficit rassasié est transformé en graisse pour éventuellement le
        # retransformer en énergie en cas de manque. »
        #
        # Sans réserve, tout surplus était PERDU au clip à 1.0 : manger rassasié ne
        # rapportait rien (mesuré : −0,0227), donc l'agent n'avait aucune raison de se
        # constituer une avance, et un jour faste ne préparait pas un jour maigre. C'est ce
        # qui rendait le métabolisme purement « au jour le jour ».
        #
        # Deux flux, tous deux DÉRIVÉS de l'écart à l'énergie nominale — aucun seuil :
        #   - au-dessus de 1.0, le trop-plein part en réserve (avec perte de stockage) ;
        #   - en dessous, la réserve remonte à hauteur du manque (avec perte de mobilisation).
        # Les pertes sont ce qui rend la graisse INTÉRESSANTE MAIS COÛTEUSE : mieux vaut
        # manger à sa faim que faire des réserves, sans que jeûner devienne fatal.
        surplus = max(0.0, self.energie - ENERGIE_MAX)
        manque = max(0.0, ENERGIE_MIN + self.seuil_critique - self.energie)
        if surplus > 0.0:
            self.reserve = min(RESERVE_MAX, self.reserve + surplus * RENDEMENT_STOCKAGE)
        elif manque > 0.0:
            # La mobilisation est bornée par le débit : on ne brûle pas sa graisse d'un
            # coup, sinon la réserve serait un simple prolongement de la jauge d'énergie.
            mobilise = min(self.reserve, manque, self.debit_reserve)
            self.reserve -= mobilise
            self.energie += mobilise * RENDEMENT_MOBILISATION

        self.satiete = float(np.clip(self.satiete, 0.0, 1.0))
        self.hydratation = float(np.clip(self.hydratation, 0.0, 1.0))
        self.stimulation = float(np.clip(self.stimulation, 0.0, 1.0))
        self.energie = float(np.clip(self.energie, ENERGIE_MIN, ENERGIE_MAX))

        deficit_apres = self.calculer_deficit()
        r_bio = deficit_avant - deficit_apres

        return r_bio, self.evaluer_quetes_biologiques()

    def est_mort(self) -> bool:
        """v41.2 — la mort par INSOLVABILITÉ, jamais par test de seuil arbitraire.

        L'agent meurt quand son énergie est épuisée ET que son stock ne peut plus rien
        rendre. Se reposer abaisse la dépense mais ne crée pas de matière : un agent qui
        se repose sans manger arrive donc ici mécaniquement. C'est la règle utilisateur
        « se reposer sans manger = mourir » exprimée sans aucune branche conditionnelle
        dédiée — ce test ne fait que CONSTATER l'insolvabilité, il ne la provoque pas."""
        if self.energie > ENERGIE_MIN or self.reserve_mobilisable() > 0.0:
            return False
        self.cause_mort = ("deshydratation" if self.hydratation <= 0.0
                           else "famine" if self.satiete <= 0.0 else "epuisement")
        return True

    def reviser_derive_metabolique(self, pression: float):
        """v41.2 — LES BORNES NE SONT PAS DES LIMITES (formulation utilisateur).

        Un métabolisme peut s'optimiser et déplacer sa propre norme, mais s'en écarter
        coûte EXPONENTIELLEMENT cher :

            Δdérive = pression × plasticité − raideur × dérive × exp(|dérive| / élasticité)

        Près de la norme le rappel est négligeable (adaptation facile) ; loin, il explose
        en `exp` et fait mur. La borne est une PENTE QUI DEVIENT VERTICALE, pas une
        barrière. Appelée une fois par NUIT, jamais par tick.

        `pression` > 0 = le monde a été dur (l'agent a manqué) ⇒ le métabolisme apprend à
        tirer davantage de son stock."""
        for attribut in ("derive_metabolique", "derive_kappa"):
            derive = getattr(self, attribut)
            rappel = (RAIDEUR_RAPPEL_DERIVE * derive
                      * math.exp(abs(derive) / ELASTICITE_DERIVE))
            # κ dérive en sens INVERSE de la pression : un monde dur pousse vers une
            # dégradation plus douce (κ↓), pour que l'agent reste fonctionnel plus bas.
            signe = 1.0 if attribut == "derive_metabolique" else -1.0
            derive += signe * pression * PLASTICITE_DERIVE_METABOLIQUE - rappel
            setattr(self, attribut, float(np.clip(derive, -DERIVE_MAX_ABSOLUE,
                                                  DERIVE_MAX_ABSOLUE)))

    def valeur_nutritive(self) -> float:
        """v41.2 — la valeur d'UNE ressource ALIMENTAIRE, DÉRIVÉE du besoin réel.

        Avant v41.2 c'était `0.4` en dur, calibré pour un métabolisme qui n'existe plus.
        Mesuré : le stock se vidait de ~1,1 réserve par journée, donc trois repas à 0,4
        ne pouvaient structurellement pas suivre — l'agent mourait *le ventre à moitié
        plein*, avec une satiété bloquée à 0,392 pendant que l'énergie s'effondrait.

        La valeur est donc ce qu'il faut manger pour couvrir une journée en
        REPAS_PAR_JOURNEE prises, pertes de conversion comprises. Si la dépense change,
        la nutrition suit — aucun des deux nombres ne peut plus dériver seul."""
        # 🔴 v41.30-fix2 — LA PORTION EST UNE PROPRIÉTÉ DE LA RESSOURCE, PAS DU RYTHME.
        #
        # Décision utilisateur (20/08) : *« Une pomme ne quadruple pas de volume ni de valeur
        # nutritive sous prétexte que l'animal qui la regarde a décidé de marcher plus
        # lentement aujourd'hui. »*
        #
        # La v41.30 faisait dériver la portion du rythme vécu. Mesuré au banc, l'effet est
        # une TAXE SUR LE VIDE — l'estomac étant plafonné à 1,0 et le coût de digestion
        # facturé sur la portion ENTIÈRE :
        #
        #   rythme  portion   gain satiété   GASPILLÉ   coût digestion
        #     1,00    3,175      1,000        2,175       0,476   ← ×4 le coût
        #     4,00    0,794      0,794        0,000       0,119
        #
        # L'agent payait l'impôt digestif maximal sur des calories qu'il ne pouvait même pas
        # faire entrer dans son estomac : 68 % de chaque repas jeté. C'est le défaut corrigé
        # en v41.2-fix pour l'eau (0,889 sur une jauge à 1,0), reproduit à plus grande échelle.
        #
        # La portion est donc dérivée de la CONTENANCE DE L'ESTOMAC, une propriété du corps
        # invariante au vécu — pas d'un agenda journalier. Le rythme vécu continue de régler
        # la PHYSIOLOGIE (vitesse de vidange, seuil de faim), jamais la taille des objets.
        #
        # ⚠️ Ne jamais réindexer cette valeur sur `besoin_par_axe` : ce serait rendre le monde
        # dépendant de la patience de l'agent, exactement ce que le fix1 vient de découpler.
        return PART_ESTOMAC_PAR_PRISE * CONTENANCE_JAUGE

    def valeur_hydrique(self) -> float:
        """v41.2-fix — la portion d'UNE ressource HYDRIQUE, dérivée de la perte d'eau
        réelle et non de la valeur alimentaire.

        ⚠️ Ce découplage corrige un défaut mesuré : partager la même portion entre les
        deux axes donnait une eau à 0,889 sur une jauge plafonnée à 1,0. L'agent qui boit
        tôt **gaspillait** (2,0 unités perdues par débordement sur une journée mesurée), et
        celui qui boit tard avait déjà subi le bridage de conversion — la fenêtre utile
        était trop étroite pour être trouvée par apprentissage. Résultat sur 57 jours :
        hydratation à 0,00 la plupart des jours, énergie effondrée à 0,072 et **zéro
        victoire**, alors que l'agent buvait pourtant le nombre théorique de fois (0,97/j
        pour un besoin de 0,94).

        Les deux axes ont des besoins journaliers différents (la soif se renouvelle plus
        vite que la faim, cf. RATIO_SOIF_SUR_FAIM) : leurs portions doivent donc être
        dérivées séparément, chacune de SA propre perte."""
        # v41.30-fix2 — même correction que `valeur_nutritive` : une gorgée d'eau est une
        # propriété du monde. La jauge d'hydratation partage la même échelle [0,1] que la
        # satiété, donc la même fraction de contenance.
        return PART_ESTOMAC_PAR_PRISE * CONTENANCE_JAUGE

    def consommer_ressource(self, type_ressource: str, quantite: float = None):
        """v41.2 — consommation sur PROFIL À TROIS AXES plutôt que « un type remplit sa
        jauge ». Chaque ressource porte son niveau d'hydratation, son remplissage de
        satiété, sa valeur énergétique, et le COÛT DE SA PROPRE DIGESTION.

        C'est ce qui permet à l'eau d'hydrater à 100 % sans apporter la moindre calorie,
        et à un aliment de coûter en énergie une fraction de ce qu'il rapporte — un
        aliment dont `digestion` approcherait 1,0 serait net-nul, entièrement consommé par
        l'effort de le digérer.

        ⚠️ Le coût de digestion est prélevé sur l'énergie DISPONIBLE, immédiatement : il
        faut de l'énergie pour en fabriquer. Un agent totalement épuisé paie donc ce coût
        sur une réserve qu'il n'a pas — d'où le `max(0.0, ...)`, qui l'empêche de devenir
        négatif tout en le laissant à zéro. Manger n'est jamais un piège mortel, mais ce
        n'est pas gratuit non plus.

        `quantite` reste surchargeable (tests, calibrage) : elle multiplie alors le profil
        au lieu de le remplacer, pour que les proportions du profil soient préservées."""
        profil = PROFILS_NUTRITIONNELS.get(type_ressource)
        if profil is None:
            return
        # v41.2-fix — CHAQUE AXE A SA PROPRE PORTION, dérivée de SA propre perte
        # journalière. Une portion unique partagée entre les deux donnait une eau à 0,889
        # sur une jauge plafonnée à 1,0 : boire tôt gaspillait, boire tard laissait la
        # conversion déjà bridée (voir `valeur_hydrique`). `quantite` reste surchargeable
        # et s'applique alors aux deux axes, pour les tests et le calibrage.
        portion_alim = self.valeur_nutritive() if quantite is None else quantite
        portion_hydr = self.valeur_hydrique() if quantite is None else quantite

        self.satiete = float(np.clip(
            self.satiete + profil["satiete"] * portion_alim, 0.0, 1.0))
        self.hydratation = float(np.clip(
            self.hydratation + profil["hydrique"] * portion_hydr, 0.0, 1.0))
        portion = portion_alim
        self.stimulation = float(np.clip(
            self.stimulation + profil.get("stimulation", 0.0) * portion, 0.0, 1.0))

        # Le coût de digérer, prélevé tout de suite sur l'énergie disponible. Exprimé en
        # fraction de l'apport énergétique de CETTE ressource : digérer une pomme coûte
        # une part de la pomme, jamais une constante détachée de ce qu'on avale.
        cout_digestion = profil["digestion"] * profil["energie"] * portion
        self.energie = float(np.clip(self.energie - cout_digestion,
                                     ENERGIE_MIN, ENERGIE_MAX))

    def faim(self) -> float:
        """v41.2-fix2 — LA FAIM EST INDEXÉE SUR L'ÉNERGIE **ET** LA SATIÉTÉ.

        Décision utilisateur (15/08) : *« pour qu'il fasse le choix de boire ou de manger
        il faut qu'il ait soif ou faim ; la faim est indexée sur l'énergie et la satiété,
        alors que la soif n'est indexée que sur l'hydratation »*.

        C'est la correction d'un défaut de conception introduit avec le second étage : la
        faim ne regardait QUE la satiété, donc un agent à l'énergie effondrée mais au
        ventre encore à moitié plein ne se déclarait **pas** affamé — il ne cherchait donc
        pas à manger alors qu'il était en train de mourir. Mesuré : `Satiété 0.70 |
        Hydratation 0.00 | énergie 0.015`, l'agent en quête d'eau pendant que son énergie
        gisait au plancher.

        Les deux termes se **multiplient** plutôt que de se moyenner : avoir du stock
        *et* de l'énergie est nécessaire pour ne pas avoir faim. Un seul des deux à zéro
        suffit à déclencher la faim — c'est ce que « indexée sur les deux » veut dire."""
        return 1.0 - (self.satiete * self.energie)

    def soif(self) -> float:
        """v41.2-fix2 — LA SOIF N'EST INDEXÉE QUE SUR L'HYDRATATION (décision
        utilisateur). L'eau n'apporte aucune calorie : sa carence ne se lit nulle part
        ailleurs que dans sa propre jauge."""
        return 1.0 - self.hydratation

    def evaluer_quetes_biologiques(self):
        """Génère la quête la plus urgente. v41.2-fix2 : l'urgence est COMPARÉE, plus
        arbitrée par un ordre figé.

        ⚠️ L'ancienne version était une cascade `if satiété < seuil / elif hydratation <
        seuil` : la faim l'emportait TOUJOURS sur la soif dès qu'elle était déclenchée,
        quelle que soit l'intensité respective des deux. Un agent mourant de soif restait
        en quête de nourriture tant que sa satiété était basse — et l'ordre `Nourriture >
        Eau > Stimulation` était un « rien en dur » violé au cœur du chemin motivationnel.

        Désormais les trois besoins déclarent leur urgence sur la même échelle et le plus
        pressant l'emporte. Le seuil ne sert plus qu'à décider s'il y a lieu d'avoir une
        quête, pas laquelle — c'est `max()` qui tranche, donc l'ordre n'est plus décrété.
        """
        besoins = (
            ("SURVIVAL_FOOD", self.faim(), [1.0, 0.0, 0.0]),
            ("SURVIVAL_WATER", self.soif(), [0.0, 1.0, 0.0]),
            ("EXPLORATION_STIM", 1.0 - self.stimulation, [0.0, 0.0, 1.0]),
        )
        type_besoin, urgence, cible = max(besoins, key=lambda b: b[1])
        # Le seuil décide s'il y a QUÊTE, jamais LAQUELLE : `1 - seuil_critique` est le
        # niveau d'urgence à partir duquel un besoin mérite de mobiliser l'agent.
        if urgence <= 1.0 - self.seuil_critique:
            self.quete_active = None
        else:
            self.quete_active = {"type": type_besoin, "priorite": urgence,
                                 "vecteur_cible": cible}
        return self.quete_active

    def obtenir_vecteur_bio(self, rappel_spatial=None, cible_vocale=None,
                             signaux_sensoriels=None, rappel_marquant=None,
                             presence_auditive=None, portage=None):
        """Retourne le vecteur de `DIM_VECTEUR_BIO` dims — la constante fait foi, ce
        commentaire ne la répète PAS (v39-fix R2 : la valeur « 34 » écrite ici en dur
        était périmée depuis deux versions, et c'est ce genre d'écart qui a produit le
        défaut R1 du banc d'ablation).

        Composition, dans l'ordre de concaténation (contrat append-only) : 3 jauges +
        3 quête + 2 rappel spatial + 8 quête vocale + 4 toucher + 4 chimie + 8 Exo-Sens +
        2 clinotaxie + 2 rappel marquant + 1 présence auditive. Consommé par
        AGI_Naulthene.integrer_bio — jamais recalculé côté réseau, toujours dérivé de
        l'état réel du moteur biologique, de la mémoire épisodique et des sens.

        `rappel_spatial` (v20.0) : tuple (distance_normalisee, fraicheur) renvoyé par
        MemoireEpisodiqueSpatiale.recuperer_contexte(), ou None si aucun souvenir
        pertinent n'a encore été formé — dans ce cas le rappel est neutre (0.0, 0.0),
        l'agent n'a simplement encore rien à se rappeler.

        `cible_vocale` (v22.1) : les 8 formants cibles normalisés [0,1]^8 de la leçon
        vocale en cours (voir hemisphere_audio.SynthetiseurFormants), ou None hors
        leçon — dans ce cas la quête vocale est neutre ([0.0]*8), exactement le même
        pattern que rappel_spatial. C'est ce bloc qui remplace l'embedding sémantique
        qui court-circuitait l'oreille en v22.0 (voir CONCEPTION_v22_audio.md, défaut 2
        du correctif v22.1) : l'agent reçoit ICI la cible ("voici ce qu'il faut
        produire"), jamais mélangée au son perçu par porte_auditive.

        `signaux_sensoriels` (v29.0, étendu v30.0 et v32.0) : les DIM_TOUCHER + DIM_CHIMIE
        + DIM_EXO + DIM_ODORAT_DELTA = 18 dims renvoyées par
        `bus_sensoriel.BusSensoriel.interpreter()` — le toucher (contact frontal, objet en
        main, orientation cos/sin), la chimie (odorat nourriture/eau, goût nourriture/eau),
        l'Exo-Sens (8 dims perçues via PortC3, nulles si aucun plug branché), puis la
        clinotaxie (2 dims de variation olfactive, v32.0). None hors MiniGrid (ex. leçon
        vocale isolée, rêve) : les 18 dims sont alors neutres, même pattern que
        `rappel_spatial`/`cible_vocale` — à ceci près que le neutre de la clinotaxie est
        0.5 et non 0.0 (voir le corps de la méthode).

        Ces 8 dims sont ajoutées EN QUEUE, jamais insérées au milieu : c'est ce qui permet
        à `persistance._greffer_vecteur_bio_etendu` de recopier les 16 premières colonnes
        d'un `.brain` pré-v29.0 sans décaler aucun acquis existant."""
        vecteur_quete = self.quete_active["vecteur_cible"] if self.quete_active else [0.0, 0.0, 0.0]
        vecteur_rappel = list(rappel_spatial) if rappel_spatial is not None else [0.0, 0.0]
        vecteur_quete_vocale = list(cible_vocale) if cible_vocale is not None else [0.0] * 8
        # v32.0 — le neutre des 2 dims de clinotaxie est 0.5 (« ni rapprochement ni
        # éloignement »), PAS 0.0 qui signifierait un éloignement maximal. Hors MiniGrid
        # (leçon vocale isolée, rêve), l'agent ne se déplace pas : lui injecter une fuite
        # olfactive permanente biaiserait `integrateur_bio` vers un signal qui n'existe pas.
        # v41.11 — le neutre thermique est ASYMÉTRIQUE, et c'est voulu : la chaleur vaut
        # 0.0 (hors MiniGrid il n'y a aucun danger — c'est une absence, pas une inconnue),
        # mais sa VARIATION vaut 0.5 comme toute clinotaxie (0.0 signifierait un
        # refroidissement maximal, donc une fuite permanente devant un feu inexistant).
        vecteur_sensoriel = (list(signaux_sensoriels) if signaux_sensoriels is not None
                             else [0.0] * (DIM_TOUCHER + DIM_CHIMIE + DIM_EXO)
                                  + [0.5] * DIM_ODORAT_DELTA
                                  + [0.0, 0.5]     # thermoception (v41.11)
                                  + [0.0, 0.5])    # pression (v41.12) : hors monde,
                                  # aucun obstacle autour, et aucune asymétrie
        # v36.0 — LE RAPPEL MARQUANT, en QUEUE (contrat append-only). `rappel_marquant`
        # est le couple (valence ∈ [−1,1], confiance ∈ [0,1]) renvoyé par
        # `MemoireEpisodiqueSpatiale.rappel_le_plus_marquant`, ou None hors MiniGrid.
        #
        # La valence est remappée de [−1,1] vers [0,1] par `(v+1)/2` — même discipline que
        # la clinotaxie v32.0 : toutes les dims du vecteur bio sont bornées dans [0,1], et
        # une dim signée pèserait deux fois plus lourd à l'entrée d'`integrateur_bio` par
        # simple effet d'échelle. Le neutre est donc **0.5**, jamais 0.0 — 0.0 signifierait
        # « le pire souvenir possible », ce qui rendrait l'agent craintif partout où il n'a
        # simplement rien vécu.
        if rappel_marquant is not None:
            valence, confiance = rappel_marquant
            vecteur_marquant = [float(np.clip((valence + 1.0) / 2.0, 0.0, 1.0)),
                                float(np.clip(confiance, 0.0, 1.0))]
        else:
            vecteur_marquant = [0.5, 0.0]

        # v39.2 — LA PRÉSENCE AUDITIVE, en QUEUE (contrat append-only). C'est le canal qui
        # distingue « j'écoute et c'est calme » de « je n'ai pas d'oreilles » — deux états
        # jusqu'ici rigoureusement indiscernables pour le cerveau (voir DIM_PRESENCE_AUDITIVE).
        #
        # Le neutre est 0.0, et ici c'est JUSTE (contrairement à la clinotaxie ou au rappel
        # marquant, dont le 0.0 signifierait « pire cas ») : 0.0 veut dire « aucun canal
        # auditif ce tick », ce qui est exactement l'information à porter. Il n'y a pas de
        # « mauvais silence » — il y a un silence, et une absence.
        vecteur_presence = [float(np.clip(presence_auditive, 0.0, 1.0))
                            if presence_auditive is not None else 0.0]

        # v41.33 — LA CHARGE PORTÉE, en QUEUE (contrat append-only). Voir DIM_PORTAGE.
        # `portage=None` (aucun corps ce tick : rêve, leçon vocale hors MiniGrid) donne
        # 0.0, la même valeur que « mains vides » — et c'est correct : dans les deux cas
        # l'agent ne porte effectivement rien. Il n'y a pas de « portage inconnu ».
        vecteur_portage = [float(np.clip(portage, 0.0, 1.0))
                           if portage is not None else 0.0]

        return ([self.satiete, self.hydratation, self.stimulation] + vecteur_quete
                + vecteur_rappel + vecteur_quete_vocale + vecteur_sensoriel
                + vecteur_marquant + vecteur_presence + vecteur_portage)


class DetecteurRessourcesBiologiques:
    """
    Génération procédurale de sources de Nourriture/Eau sur la grille (v18.0), générique
    comme les autres détecteurs de la section 3b — aucun palier ni carte codé en dur.
    MiniGrid n'a pas d'objets Nourriture/Eau natifs : ce détecteur réutilise `Ball` avec
    une couleur dédiée par ressource (rouge = Nourriture, bleu = Eau) plutôt que de
    sous-classer WorldObj, pour ne pas ajouter de complexité de rendu/encodage
    OBJECT_TO_IDX à un projet qui carbure déjà sur les objets standards.

    Fait apparaître un nombre limité de sources par épisode sur des cases vides
    aléatoires ; les retire de la grille (grid.set(x, y, None)) au moment où l'agent
    marche dessus, pour que la ressource ne soit consommée qu'une seule fois.

    Respawn 80/20 (v19.0, étendu Eau v21.0) : contrairement à la v18.0 où une ressource
    consommée disparaissait définitivement, Nourriture ET Eau réapparaissent
    immédiatement après consommation, selon une distribution 80% Foyer / 20% Dispersion :

    - 80% : à proximité (±1 case) d'un "Nid" — la première case vide trouvée à
      l'initialisation de l'épisode, PAS une coordonnée fixe codée en dur (contrairement
      au pseudo-code initial `primary_nest_pos=(2,2)`) puisque ce détecteur doit rester
      agnostique de la carte comme les autres détecteurs génériques du projet ;
      fonctionne donc identiquement sur les 5 niveaux du PROGRAMME.
    - 20% : n'importe où ailleurs sur la grille (dispersion totale).

    Historique : jusqu'en v20.0, l'Eau ne respawnait pas (seule la Nourriture suivait ce
    cycle de forage, le pseudo-code v19.0 ne concernant que "FoodSpawner"). Observé en
    v21.0 sur un run réel (481 jours, cursus DoorKey bloqué au dernier palier) : sans
    respawn, les `nb_sources_water` sources d'un épisode s'épuisent définitivement dès
    qu'elles sont bues, l'hydratation ne pouvant plus remonter avant le `reset()` suivant
    — combiné à une patience d'épisode parfois longue (Sursaut de Volonté), ça pousse la
    jauge à 0.0 de façon quasi permanente, plombant `r_bio` (donc la motivation nette) en
    continu. L'Eau suit donc désormais le même cycle de forage que la Nourriture.
    """
    # v41.44 — P8 de l'audit du génome : LE CŒUR NE NOMME PLUS LES COULEURS DU MONDE.
    # Ces deux constantes étaient une DUPLICATION de `bus_sensoriel.COULEUR_NOURRITURE` /
    # `COULEUR_EAU`, déjà importées en tête de ce fichier. Elles sont désormais un simple
    # alias de la source unique : la traduction « ce qui est rouge est de la nourriture »
    # appartient à l'organe sensoriel — la frontière corps/monde, où `lava` a déjà droit
    # de cité — pas au cœur cognitif.
    # ⚠️ Le cœur reste néanmoins DÉPENDANT de cette convention pour SEMER les ressources
    # (il est le jardinier du monde, pas seulement son habitant) : le nom a disparu du
    # cœur, la dépendance non. C'est ce que P8 corrige, et ce qu'il ne corrige pas.
    COULEUR_FOOD = COULEUR_NOURRITURE
    COULEUR_WATER = COULEUR_EAU
    PROBABILITE_RESPAWN_AU_NID = 0.80

    def __init__(self, nb_sources_food=2, nb_sources_water=2):
        self.nb_sources_food = nb_sources_food
        self.nb_sources_water = nb_sources_water
        self.actif = _MINIGRID_INTERNALS_OK
        self._avertissement_donne = False
        self.reinitialiser_episode(None)

    def _avertir(self, exception):
        if not self._avertissement_donne:
            print(f"⚠️  Détecteur de ressources biologiques désactivé (API minigrid incompatible : {exception})")
            self._avertissement_donne = True
        self.actif = False

    def reinitialiser_episode(self, env):
        self.positions_food = set()
        self.positions_water = set()
        self.nid_position = None
        self.env_courant = env
        if env is None or not self.actif:
            return
        try:
            grille = env.unwrapped.grid
            cases_vides = []
            for x in range(1, grille.width - 1):
                for y in range(1, grille.height - 1):
                    if grille.get(x, y) is None and (x, y) != tuple(env.unwrapped.agent_pos):
                        cases_vides.append((x, y))

            if cases_vides:
                self.nid_position = cases_vides[0]  # nid dérivé de la carte, jamais fixe

            np.random.shuffle(cases_vides)
            # v41.2-fix3 — LA DENSITÉ EST RELATIVE À LA CARTE, jamais absolue.
            #
            # `nb_sources_*` sont des SOUHAITS dérivés du besoin métabolique ; la carte a
            # le dernier mot. Sans ce plafond, `Empty-5x5` (8 cases libres) recevait les 13
            # sources demandées : 7 étaient placées et il ne restait **1 case libre**.
            # L'agent était quasi emmuré dans un garde-manger, et sa récolte plafonnait à
            # ~3,5/jour quelle que soit la densité demandée — d'où trois calibrages
            # successifs restés sans le moindre effet (3,72 / 3,52 / 3,47).
            #
            # Le plafond préserve la proportion food/eau voulue plutôt que de tronquer la
            # liste, ce qui aurait supprimé l'eau en premier (elle est placée en second).
            budget = max(2, int(len(cases_vides) * FRACTION_CASES_RESSOURCES_MAX))
            total_souhaite = self.nb_sources_food + self.nb_sources_water
            total_sources = min(total_souhaite, budget)
            part_food = self.nb_sources_food / max(total_souhaite, 1)
            n_food = max(1, int(round(total_sources * part_food))) if total_sources else 0
            for i, (x, y) in enumerate(cases_vides[:total_sources]):
                if i < n_food:
                    grille.set(x, y, Ball(color=self.COULEUR_FOOD))
                    self.positions_food.add((x, y))
                else:
                    grille.set(x, y, Ball(color=self.COULEUR_WATER))
                    self.positions_water.add((x, y))
        except Exception as e:
            self._avertir(e)

    def evaluer_tick(self, env, action_item=None):
        """Retourne (mange_food: bool, mange_water: bool). Retire la ressource
        consommée de la grille, puis fait repousser la Nourriture ailleurs (80/20).

        v41.2-fix5 — **MANGER EST UN ACTE, PLUS UN EFFET DE BORD DU DÉPLACEMENT.**

        Avant ce correctif, marcher sur une case chargée consommait la ressource
        automatiquement : un agent rassasié qui traversait une pomme l'avalait quand même
        et la gaspillait, et un agent affamé « se nourrissait » sans jamais avoir eu à le
        vouloir. La « récolte » mesurée n'était donc pas un comportement de recherche mais
        une conséquence mécanique des déplacements — ce qui invalidait la lecture des
        chiffres de fourrage de tout ce chantier.

        La consommation est désormais conditionnée à `ACTION_CONSOMMER` (le `pickup` de
        MiniGrid), l'action la plus coûteuse du barème corporel (0,8 contre 0,2 pour
        tourner). Manger a donc un prix, et l'agent doit **choisir** de le payer.

        ⚠️ Aucun `if faim then manger` nulle part : le geste reste une sortie de la tête
        motrice, apprise par le gradient. Le corps signale la faim dans le vecteur bio
        (jauges + quête + vigueur), la décision reste au réseau. `action_item=None`
        conserve l'ancien comportement automatique pour les appelants non migrés."""
        if not self.actif:
            return False, False
        if action_item is not None and action_item != ACTION_CONSOMMER:
            return False, False
        try:
            # v41.2-fix6 — LA CASE VISÉE EST CELLE QUE `pickup` ATTEINT : celle DEVANT
            # l'agent, jamais celle sous ses pieds.
            #
            # Défaut mesuré : le geste était joué 70 fois par jour pour une efficacité de
            # **2,9 %**. `pickup` agit sur la case frontale (`agent_pos + dir_vec`) alors
            # que le détecteur testait `agent_pos` — les deux ne coïncident jamais, donc
            # l'agent « mangeait » systématiquement dans le vide. Pire : MiniGrid retirait
            # bien la Ball de la grille pour la mettre en `carrying`, donc la ressource
            # disparaissait sans nourrir personne et sans repousser.
            #
            # L'agent est donc rendu au geste naturel : se tourner vers ce qu'on veut
            # manger. `carrying` est vidé juste après, sinon la main reste pleine et tout
            # `pickup` suivant échoue — un agent qui aurait mangé une fois ne pourrait plus
            # jamais se nourrir.
            agent_pos = tuple(env.unwrapped.agent_pos)
            if action_item is not None:
                agent_pos = tuple(np.array(env.unwrapped.agent_pos)
                                  + env.unwrapped.dir_vec)
            mange_food, mange_water = False, False

            if agent_pos in self.positions_food:
                env.unwrapped.grid.set(agent_pos[0], agent_pos[1], None)
                self.positions_food.discard(agent_pos)
                mange_food = True
                self._faire_repousser_ressource(env, self.COULEUR_FOOD, self.positions_food)
            elif agent_pos in self.positions_water:
                env.unwrapped.grid.set(agent_pos[0], agent_pos[1], None)
                self.positions_water.discard(agent_pos)
                mange_water = True
                self._faire_repousser_ressource(env, self.COULEUR_WATER, self.positions_water)

            # v41.2-fix6 — la main est vidée après ingestion. MiniGrid vient de placer la
            # Ball dans `carrying` en exécutant `pickup` ; sans ce nettoyage, la main reste
            # pleine et TOUT `pickup` suivant échoue silencieusement — un agent qui aurait
            # mangé une seule fois ne pourrait plus jamais se nourrir de sa vie.
            if mange_food or mange_water:
                env.unwrapped.carrying = None

            return mange_food, mange_water
        except Exception as e:
            self._avertir(e)
            return False, False

    def _positions_occupees(self, env):
        occupees = set(self.positions_food) | set(self.positions_water)
        occupees.add(tuple(env.unwrapped.agent_pos))
        return occupees

    def _case_libre_pres_du_nid(self, grille, occupees):
        nx, ny = self.nid_position
        for _ in range(10):
            x = int(np.clip(nx + np.random.randint(-1, 2), 1, grille.width - 2))
            y = int(np.clip(ny + np.random.randint(-1, 2), 1, grille.height - 2))
            if (x, y) not in occupees and grille.get(x, y) is None:
                return (x, y)
        return None

    def _case_libre_aleatoire(self, grille, occupees):
        for _ in range(50):
            x = int(np.random.randint(1, grille.width - 1))
            y = int(np.random.randint(1, grille.height - 1))
            if (x, y) not in occupees and grille.get(x, y) is None:
                return (x, y)
        return None

    def _faire_repousser_ressource(self, env, couleur, positions_cible):
        """Respawn 80/20 (v19.0 Nourriture, étendu Eau en v21.0) : 80% de chances près
        du nid (±1 case), 20% n'importe où sur la grille. Si la case tirée est occupée,
        retente jusqu'à épuisement des tentatives plutôt que de forcer un écrasement —
        une carte pleine reste jouable sans ressource supplémentaire ce tick-là."""
        if self.nid_position is None:
            return
        try:
            grille = env.unwrapped.grid
            occupees = self._positions_occupees(env)

            if np.random.random() < self.PROBABILITE_RESPAWN_AU_NID:
                position = self._case_libre_pres_du_nid(grille, occupees)
            else:
                position = self._case_libre_aleatoire(grille, occupees)

            if position is None:
                position = self._case_libre_aleatoire(grille, occupees)
            if position is None:
                return

            grille.set(position[0], position[1], Ball(color=couleur))
            positions_cible.add(position)
        except Exception as e:
            self._avertir(e)


# --- 3f. MÉMOIRE ÉPISODIQUE SPATIO-TEMPORELLE (v20.0, générique, actif partout) ---
class MemoireEpisodiqueSpatiale:
    """
    Mémoire épisodique au sens propre (v20.0) : stocke le souvenir d'un événement avec
    son contexte spatio-temporel (où, quand, quoi) — distincte de `vecteurs_episodiques`
    (déjà existant dans AGI_Naulthene, une moyenne glissante d'états latents récents,
    plus proche d'une mémoire de travail que d'un vrai souvenir daté et localisé).

    Enregistre les événements de ressources biologiques (voir DetecteurRessourcesBiologiques,
    v18.0/v19.0) : position, type ("FOOD"/"WATER"), tick d'enregistrement. Ne stocke
    JAMAIS d'encodage visuel appris (contrairement au pseudo-code initial qui gardait un
    tenseur par souvenir) — uniquement des scalaires (position, type, tick), pour rester
    une mémoire épisodique légère consommée par le vecteur bio existant plutôt qu'un
    second canal de features concurrent de `porte_visuelle`.

    Persistance (v20.0) : contrairement aux détecteurs spatiaux locaux à l'épisode
    (thermostat_cinetique, detecteur_portes...), les souvenirs PERSISTENT à travers les
    resets MiniGrid d'une même journée — un vrai souvenir épisodique survit à un simple
    reset d'environnement. Ils ne sont vidés qu'au changement de NIVEAU (nouvelle carte
    du PROGRAMME), car les coordonnées d'un niveau précédent n'ont alors plus aucun sens.
    """
    # --- v31.0 : CAPACITÉ ADAPTATIVE (fin du plafond arbitraire de 200) ---
    #
    # Jusqu'en v30.1, `capacite_max = 200` était une constante arbitraire, jamais
    # justifiée ni calibrée. La télémétrie v30.1 a confirmé le symptôme : un cerveau
    # mature affiche 200/200 en permanence, donc une FIFO qui jette en continu — la
    # profondeur temporelle accessible ne dépend plus que du débit d'événements.
    #
    # Le principe fondateur du projet interdit les chiffres arbitraires (voir le rêve
    # adaptatif : `pourcentage_reve` émerge de la plasticité × richesse). La capacité
    # mnésique doit donc ÉMERGER, elle aussi — de deux facteurs biologiquement
    # défendables :
    #
    #   capacite = dim_bus × SOUVENIRS_PAR_DIM × (1 + deficit_bio)
    #              └───┬───┘   └──────┬──────┘   └───────┬───────┘
    #        substrat neural    densité fixe        le BESOIN
    #
    # 1. `dim_bus` — un cerveau qui a grandi par neurogenèse peut retenir davantage.
    #    C'est le même rapport que `empreinte_enfance` (BUS_REFERENCE/dim_bus) utilise
    #    déjà en sens inverse pour pondérer l'importance des souvenirs.
    # 2. `deficit_bio` — un agent affamé/assoiffé a un besoin réel de se rappeler où
    #    sont les ressources ; un agent repu n'en a pas l'usage. C'est le facteur
    #    « besoins » demandé, et il réutilise `BiologicalHomeostasisEngine.calculer_deficit`
    #    qui existe déjà — aucune notion nouvelle inventée.
    #
    # SOUVENIRS_PAR_DIM = 12 est calibré pour que la naissance (dim_bus=16, agent repu)
    # donne 192 ≈ les 200 historiques : pas de rupture de comportement au démarrage, la
    # capacité ne fait que cesser d'être un plafond dur quand le cerveau grandit.
    #
    #   dim_bus=16 repu → 192   |  dim_bus=48 → 576   |  dim_bus=96 → 1152
    #
    # Coût : `recuperer_contexte` parcourt la liste en O(n) à chaque tick avec une quête
    # active. À dim_bus=96 (1152 souvenirs), cela reste une boucle Python sur des dicts
    # de 3 scalaires — négligeable devant un forward PyTorch. Surveillé par la télémétrie
    # `Memoire_Capacite_Courante`.
    SOUVENIRS_PAR_DIM = 12

    # --- v31.1 : CAP DE DENSITÉ SPATIALE ---
    #
    # La capacité proportionnelle (v31.0) supprime bien la saturation, mais elle ignore
    # une contrainte évidente : la taille du MONDE. Mesuré sur un run réel de 700 jours,
    # à dim_bus=48 (capacité 576) :
    #
    #     DoorKey-6x6 : 576 slots pour 16 cases intérieures = 36 souvenirs par case
    #     Empty-8x8   : 576 slots pour 36 cases             = 16 souvenirs par case
    #     MultiRoom   : 576 slots pour 169 cases            =  3.4 souvenirs par case
    #
    # Retenir 36 repères pour une seule case n'a aucun sens — un lieu n'a besoin que
    # d'être connu, pas d'être mémorisé 36 fois. La capacité est donc désormais bornée
    # par ce que le monde peut réellement contenir :
    #
    #     capacite = min( dim_bus × 12 × (1+déficit),  cases_grille × DENSITE_MAX )
    #
    # DENSITE_MAX = 3 laisse la place aux quelques types d'événements distincts
    # (FOOD/WATER, extensibles) sur une même case, sans permettre l'accumulation de
    # doublons — que la déduplication d'`enregistrer_evenement` empêche déjà par ailleurs.
    # Les deux mécaniques sont complémentaires : la déduplication traite la CAUSE
    # (empilement de repères identiques), le cap traite le DIMENSIONNEMENT (une mémoire
    # ne doit pas être absurdement plus grande que son monde).
    #
    # Le plancher (200) reste prioritaire sur le cap : sur une carte minuscule, l'agent
    # garde de quoi mémoriser son historique récent même si la grille est petite.
    DENSITE_MAX_PAR_CASE = 3

    def __init__(self, capacite_max=200, fenetre_fraicheur=1000):
        # `capacite_max` reste le PLANCHER (et la valeur utilisée tant qu'aucune capacité
        # adaptative n'a été calculée) — un cerveau qui n'appelle jamais
        # `ajuster_capacite` se comporte donc exactement comme en v30.1.
        self.capacite_max = capacite_max
        self.capacite_plancher = capacite_max
        self.fenetre_fraicheur = fenetre_fraicheur
        self.souvenirs = []  # liste de {'pos': (x,y), 'type': str, 'tick': int}

        # --- v41.10 : LES CARTES SONT DES LIEUX, PAS DES INSTANTS ---
        #
        # `souvenirs` est la vue de la carte COURANTE. Les autres cartes ne sont pas
        # oubliées : elles dorment ici, indexées par leur identifiant de carte.
        #
        # 🔴 CE QUE ÇA CORRIGE (mesuré, campagne 20 graines du 16/08) :
        #
        #     🗺️ 5/200 souvenir(s) spatial(aux) — 51 715 doublon(s) évité(s)
        #
        # La mémoire tournait à **1 % de sa capacité** pendant que 51 715 expériences
        # étaient jetées. Cause : P17 (v41.6) change de carte ~1,5 fois par jour, et
        # chaque bascule appelait `reinitialiser_niveau()` — soit ~3750 effacements
        # complets par run de 2500 jours.
        #
        # L'erreur de raisonnement était de confondre deux choses :
        #
        #     changer de carte      -> les coordonnées courantes ne s'appliquent plus
        #     ne plus jamais y aller -> les coordonnées ne valent plus rien
        #
        # Le premier cas n'implique pas le second. Sous P17, l'agent REVIENT sans cesse
        # sur les mêmes cartes (révision, incursion, défi) : effacer à chaque bascule lui
        # faisait redécouvrir de zéro un monde qu'il connaissait déjà. C'est le mécanisme
        # d'abstraction par récurrence (v36.0) tournant sur une ardoise essuyée deux fois
        # par jour — `confirmations` ne pouvait structurellement jamais monter.
        #
        # ⚠️ L'INVARIANT v39.0 EST INTACT, et même renforcé : une position (1,2) n'est
        # JAMAIS lue sur une autre carte que celle où elle a été vécue. On ne mélange
        # rien ; on cesse simplement de détruire ce qu'on quitte. Le OÙ reste local à sa
        # carte, le QUOI (`empreinte_types`) reste transversal comme en v39.0.
        #
        # ⚠️ Rien n'est nommé : la clé d'archive est l'identifiant de carte que
        # l'appelant fournit, une étiquette opaque de plus. Cette classe ne sait toujours
        # pas ce qu'est un niveau, une porte ou une grille.
        #
        # {cle_carte: [souvenirs]} — la carte courante n'y figure pas (elle est `souvenirs`)
        self.archives_cartes = {}
        self.carte_courante = None
        # Télémétrie : combien de bascules ont RETROUVÉ une carte déjà connue, contre
        # combien ont découvert une carte inédite. Un ratio élevé de retrouvailles est la
        # preuve directe que l'effacement d'avant détruisait du vécu réutilisable.
        self.cartes_retrouvees = 0
        self.cartes_decouvertes = 0
        # v31.1 — télémétrie : combien de fois un repère existant a été rafraîchi plutôt
        # que dupliqué. Un compteur élevé prouve que la déduplication travaille.
        self.doublons_evites = 0
        self.cap_densite_actif = False  # True si le cap spatial a bridé la capacité

        # --- v39.0 : L'EMPREINTE DE TYPE — le QUOI qui survit au OÙ ---
        #
        # 🔴 CE QUE ÇA CORRIGE (mesuré, run instrumenté du 13/08, graine 22) :
        #
        #     [ECRIT goal] tick=22091 pos=(1,2) int=1.0035
        #     [ECRIT goal] tick=22142 pos=(1,3) int=1.0119
        #     🎓 [PROMOTION] L'Agent passe en DoorKey 6x6 !
        #     -> .brain sauvegardé juste après : ZÉRO repère `goal`
        #
        # Sur 300 jours : 4 repères `goal` écrits, 3 promotions, **0 survivant, 0 jamais
        # confirmé une seule fois**. Sur les 12 cerveaux de la campagne 2a, onze ont
        # exactement 0 repère `goal` ; le seul qui en garde (21) est celui qui avait
        # atteint le DERNIER palier, donc que plus aucune promotion n'effaçait.
        #
        # La cause est `reinitialiser_niveau()`, qui vide la mémoire entière à chaque
        # palier. Son intention est juste — une position (1,2) n'a plus le même sens sur
        # une autre carte — mais elle jetait AUSSI ce qui n'a rien de spatial.
        #
        # LA DISTINCTION (formulée par l'utilisateur) :
        #
        #     le OÙ   : les coordonnées (x,y)      -> périmées au changement de carte
        #     le QUOI : la valence apprise du TYPE -> vraie partout, indépendante du lieu
        #
        # « L'abstraction doit s'émanciper de l'espace. » Un agent qui a appris
        # qu'atteindre un `goal` est ce qui lui arrive de mieux (valence ~1,00 contre
        # ~0,07 pour `sol`) redécouvrait cette leçon DE ZÉRO à chaque palier — et la
        # perdait à l'instant précis où il venait de prouver qu'il l'avait acquise.
        #
        # ⚠️ RIEN N'EST EXPLIQUÉ EN DUR. `empreinte_types` n'est pas une table
        # `goal = bien` : c'est la moyenne glissante des chocs réellement vécus sur
        # chaque étiquette, exactement comme `valence` l'est par lieu. Le cerveau ne sait
        # toujours pas ce qu'est un but — il sait seulement que « ce genre d'endroit » lui
        # a valu telle intensité, en moyenne, sur toute sa vie. C'est le mécanisme v36.0
        # (l'abstraction par récurrence) qu'on laisse enfin vivre au lieu de le remettre
        # à zéro.
        #
        # {type: {'valence': float, 'confirmations': int}}
        self.empreinte_types = {}

    def ajuster_capacite(self, dim_bus: int, deficit_bio: float = 0.0,
                          cases_grille: int | None = None) -> int:
        """Recalcule la capacité en fonction du substrat neural et du besoin courant.

        Appelée une fois par nuit (voir `executer_nuit`) plutôt qu'à chaque tick : une
        capacité qui fluctuerait en permanence rendrait la FIFO illisible et le
        diagnostic impossible. La nuit est le moment naturel — c'est déjà là que le
        cerveau grandit (`declencher_neurogenese`) et que la plasticité est recalculée.

        `deficit_bio` est la somme des écarts au carré des trois jauges vitales (voir
        `BiologicalHomeostasisEngine.calculer_deficit`), donc dans [0, 3] en pratique.
        Il est borné à 1.0 ici : un agent totalement épuisé double sa capacité, jamais
        plus — sans ce clamp, un déficit extrême ferait exploser la mémoire au pire
        moment (quand l'agent est déjà en difficulté).

        La capacité ne descend JAMAIS sous `capacite_plancher` : la neurogenèse ne
        recule pas, et un agent momentanément repu ne doit pas perdre ses souvenirs.
        Rétrécir la capacité tronque la FIFO — voir le `pop(0)` ci-dessous.
        """
        besoin = 1.0 + min(1.0, max(0.0, float(deficit_bio)))
        nouvelle = int(round(dim_bus * self.SOUVENIRS_PAR_DIM * besoin))

        # v31.1 — cap de densité : une mémoire ne doit pas être absurdement plus grande
        # que le monde qu'elle décrit (voir DENSITE_MAX_PAR_CASE). `cases_grille=None`
        # (appelant qui ne connaît pas la carte, ex. mode vocal isolé) désactive le cap —
        # le comportement se réduit alors exactement à celui de la v31.0.
        self.cap_densite_actif = False
        if cases_grille:
            plafond_spatial = int(cases_grille) * self.DENSITE_MAX_PAR_CASE
            if plafond_spatial < nouvelle:
                nouvelle = plafond_spatial
                self.cap_densite_actif = True

        # Le plancher reste prioritaire sur le cap : sur une carte minuscule, l'agent
        # garde de quoi mémoriser son historique récent.
        self.capacite_max = max(self.capacite_plancher, nouvelle)
        # Si la capacité a rétréci (agent redevenu repu), on tronque par l'AVANT — les
        # souvenirs les plus anciens partent en premier, exactement comme la FIFO
        # d'`enregistrer_evenement`. Jamais de troncature par la fin : ce serait jeter
        # les souvenirs les plus frais, les plus utiles au rappel.
        while len(self.souvenirs) > self.capacite_max:
            self.souvenirs.pop(0)
        return self.capacite_max

    def dedupliquer(self) -> int:
        """Compacte une mémoire déjà peuplée de doublons (v31.1) — retourne le nombre de
        souvenirs supprimés.

        La déduplication d'`enregistrer_evenement` ne vaut que pour les NOUVEAUX
        souvenirs : un `.brain` antérieur porte encore tous ses doublons historiques.
        Mesuré sur un cerveau réel (`naulthene_parole`, 480 000 ticks) : **200 souvenirs
        pour seulement 18 repères distincts**, soit 182 doublons (91 %). La « saturation »
        observée n'était donc pas un manque de place, mais une redondance massive.

        Appelée une fois au chargement d'un `.brain` (voir `persistance.py`). Conserve
        systématiquement le tick le PLUS RÉCENT de chaque repère et préserve l'ordre
        d'ancienneté de dernière visite — la FIFO d'éviction garde donc le même sens
        après compactage qu'avant.

        v41.10 — compacte AUSSI les cartes archivées : elles portent exactement les mêmes
        doublons historiques que la carte courante, et les ignorer laisserait la
        redondance dormir dans l'archive jusqu'au premier retour sur cette carte.
        """
        def _compacter(liste):
            if not liste:
                return liste, 0
            plus_recent = {}
            for souvenir in liste:  # ordre chronologique : le dernier écrase
                plus_recent[(souvenir['pos'], souvenir['type'])] = souvenir
            # Retrié par tick pour que la FIFO continue d'évincer les repères les plus
            # anciennement confirmés en premier.
            compacte = sorted(plus_recent.values(), key=lambda s: s['tick'])
            return compacte, len(liste) - len(compacte)

        self.souvenirs, supprimes = _compacter(self.souvenirs)
        for cle, liste in list(self.archives_cartes.items()):
            self.archives_cartes[cle], n = _compacter(liste)
            supprimes += n
        return supprimes

    def _nourrir_empreinte(self, type_evenement: str, intensite: float) -> None:
        """v39.0 — accumule la statistique par TYPE, indépendamment du lieu.

        Moyenne glissante exacte (pas exponentielle) : chaque expérience d'un type pèse
        autant que les autres, comme pour `valence` au niveau du repère. Un type vécu
        mille fois a donc une empreinte très stable, un type vu deux fois reste
        volatil — ce qui est le comportement voulu : l'abstraction se mérite par la
        répétition.

        ⚠️ Aucune étiquette n'est interprétée ici. La fonction ne sait pas si
        `type_evenement` vaut 'goal', 'lava' ou 'sol' — elle accumule ce qu'on lui donne.
        """
        e = self.empreinte_types.get(type_evenement)
        if e is None:
            self.empreinte_types[type_evenement] = {'valence': float(intensite),
                                                     'confirmations': 1}
            return
        n = e['confirmations'] + 1
        e['valence'] = (e['valence'] * (n - 1) + float(intensite)) / n
        e['confirmations'] = n

    def valence_de_type(self, type_evenement: str, defaut: float = 0.0) -> float:
        """La valeur apprise d'un TYPE, survivant aux changements de carte (v39.0)."""
        e = self.empreinte_types.get(type_evenement)
        return float(e['valence']) if e else float(defaut)

    def reinitialiser_niveau(self):
        """Au changement de niveau (PROGRAMME) : on oublie le OÙ, on garde le QUOI.

        v39.0 — LA CORRECTION. Jusqu'ici cette méthode faisait `self.souvenirs = []`,
        c'est-à-dire qu'elle effaçait **tout**. Mesuré sur un run instrumenté de
        300 jours (graine 22) : 4 repères `goal` écrits, 3 promotions, **0 survivant et
        0 jamais confirmé une seule fois**. Sur les 12 cerveaux de la campagne 2a, onze
        ont exactement 0 repère `goal` — le seul qui en garde est celui qu'aucune
        promotion n'effaçait plus (dernier palier atteint).

        Les COORDONNÉES doivent effectivement partir : `(1,2)` ne désigne pas le même
        endroit sur la carte suivante, et garder ces positions produirait des rappels
        franchement trompeurs. C'est le comportement historique, et il est conservé.

        Mais l'EMPREINTE DE TYPE n'est pas spatiale. « Ce genre d'endroit m'a valu ça en
        moyenne » reste vrai quelle que soit la carte — c'est même la définition d'une
        abstraction. La v36.0 avait construit le mécanisme qui la produit
        (`confirmations` + `valence`) ; cette méthode le remettait à zéro à chaque palier,
        donc juste après chaque victoire, puisque le repère du but naît au tick même de
        la victoire qui déclenche la promotion.

        ⚠️ Rien n'est expliqué en dur : `empreinte_types` ne contient aucune table
        `objet → valeur`, seulement la moyenne des chocs réellement vécus sur chaque
        étiquette opaque. Le cerveau ne sait toujours pas ce qu'est un but.
        """
        self.souvenirs = []          # le OÙ : périmé, il part
        # le QUOI : `empreinte_types` survit intentionnellement.

    def basculer_carte(self, cle_carte) -> bool:
        """v41.10 — change de carte SANS rien détruire. Retourne True si carte déjà connue.

        Remplace `reinitialiser_niveau()` sur le chemin des bascules fréquentes (P17).
        Les souvenirs de la carte quittée sont ARCHIVÉS, ceux de la carte rejointe sont
        restaurés si elle a déjà été visitée.

        La distinction avec `reinitialiser_niveau` est celle entre **quitter un lieu** et
        **le perdre**. L'agent qui rentre chez lui ne redécouvre pas sa cuisine ; celui
        qui déménage, si. P17 fait revenir l'agent sur les mêmes cartes en permanence :
        c'est un va-et-vient, pas un déménagement.

        ⚠️ Aucun souvenir n'est jamais LU hors de sa carte d'origine — l'invariant v39.0
        (une coordonnée n'a de sens que sur sa grille) est strictement préservé, puisque
        seule la liste de la carte courante est exposée sous `self.souvenirs`.

        ⚠️ `cle_carte` est opaque : cette classe ne l'interprète jamais.
        """
        if cle_carte == self.carte_courante:
            return True
        # On quitte : la carte courante est mise de côté, pas jetée.
        if self.carte_courante is not None:
            self.archives_cartes[self.carte_courante] = self.souvenirs
        connue = cle_carte in self.archives_cartes
        # `pop` et non `get` : la carte rejointe sort de l'archive pour devenir la vue
        # courante — sans quoi la même liste existerait à deux endroits et l'archive
        # dériverait silencieusement de la réalité.
        self.souvenirs = self.archives_cartes.pop(cle_carte, [])
        self.carte_courante = cle_carte
        if connue:
            self.cartes_retrouvees += 1
        else:
            self.cartes_decouvertes += 1
        return connue

    def total_souvenirs(self) -> int:
        """Le vécu spatial COMPLET, toutes cartes confondues (v41.10).

        `len(self.souvenirs)` ne compte plus que la carte courante : la télémétrie
        historique sous-estimerait donc massivement la mémoire réelle sous P17.
        """
        return len(self.souvenirs) + sum(len(v) for v in self.archives_cartes.values())

    # --- v36.0 : LE FLUX ENRICHI & L'ABSTRACTION PAR RÉCURRENCE ---
    #
    # 🔴 CE QUE ÇA CORRIGE (mesuré sur un run de 600 jours, `58ssyw19`) :
    #
    #   - la mémoire spatiale ne recevait que DEUX types d'événements (FOOD, WATER) :
    #     deux sites d'appel dans tout le code. Ne pouvaient JAMAIS y entrer la clé
    #     ramassée, la porte ouverte, le but atteint, la lave, un mur percuté ;
    #   - sur ce flux déjà appauvri, **98,6 %** était rejeté (869 doublons pour 12
    #     souvenirs conservés).
    #
    # Ce n'était pas un mauvais filtre : c'était un filtre privé de matière. Une mémoire
    # ne peut pas trier ce qu'on ne lui donne jamais.
    #
    # LE MODÈLE (décision utilisateur, formulée ainsi) :
    #
    #   1. « Il devrait absolument TOUT mémoriser, mais avec des filtres de pondération
    #      selon : nouveau, récurrent, etc. » ⇒ le flux est enrichi, pas centralisé. Il
    #      n'y a PAS de routeur unique en amont (ce serait un goulot et un point de
    #      défaillance) : chaque mémoire reste son propre filtre, on cesse simplement de
    #      l'affamer.
    #   2. « La récurrence devient des abstractions dans le cerveau. » ⇒ un doublon n'est
    #      plus jeté : il RENFORCE le repère. La répétition est la matière première de
    #      l'abstraction, pas du bruit à supprimer.
    #   3. « L'oubli est un moyen de dire : l'abstraction est faite, on met en archive
    #      dégradable avec le temps. » ⇒ la `confiance` d'un repère se dégrade avec le
    #      temps et se renforce à chaque confirmation.
    #
    # ⚠️ INVARIANT ABSOLU (décision utilisateur) : **rien n'est expliqué en dur.** Le
    # cerveau ne sait pas ce qu'est une pomme ni une clé — ces mots ne sont que des
    # ÉTIQUETTES OPAQUES servant à regrouper des expériences semblables. Aucune table du
    # type « lave = danger » ou « clé = utile » n'existe ni ne doit exister : la valence
    # d'un type est APPRISE, portée par `valence` (la moyenne des chocs vécus à cet
    # endroit), jamais déclarée. C'est ce qui distingue ce mécanisme d'un système expert.

    def enregistrer_evenement(self, position, type_evenement: str, tick_absolu: int,
                              intensite: float = 0.0):
        """v36.0 — ABSTRACTION PAR RÉCURRENCE (remplace la déduplication v31.1).

        `intensite` (v36.0) : la charge de l'expérience à cet endroit, SIGNÉE — positive
        pour un choc favorable, négative pour un choc défavorable. Elle n'est jamais
        interprétée : elle est moyennée dans `valence`, que l'agent apprend à lire via
        `integrateur_bio`. Le code ne sait pas si −0.9 veut dire « lave » ou « mur » — il
        sait seulement que cet endroit a mal réussi.

        v31.1 — DÉDUPLICATION à l'écriture (conservée, mais retournée) :

        Jusqu'ici, chaque événement empilait un souvenir de plus, même si l'agent
        remangeait au MÊME endroit. Sur une petite carte, la mémoire se remplissait donc
        de doublons : mesuré à 36 souvenirs par case sur `DoorKey-6x6` (16 cases
        intérieures) une fois la capacité proportionnelle en place (v31.0). Un souvenir
        n'est pas un journal d'événements — c'est un REPÈRE : « il y a de la nourriture
        ici ». Deux repères identiques n'apportent rien, ils diluent seulement.

        Effet de bord corrigé au passage : `recuperer_contexte` sélectionne par
        `min(distance)`, la fraîcheur n'étant lue qu'APRÈS. Avec des doublons, un
        souvenir périmé pouvait donc être retenu à la place d'un souvenir récent situé à
        la même distance — le rappel devenait moins fiable à mesure que la mémoire
        grossissait. En rafraîchissant le tick d'un repère existant au lieu d'empiler,
        un lieu connu reste toujours à sa fraîcheur la plus récente.

        Le repère rafraîchi est **remis en fin de liste** : la FIFO d'éviction jette
        toujours les plus anciennement CONFIRMÉS, jamais un lieu encore régulièrement
        visité — c'est ce qui rend l'oubli sélectif plutôt qu'arbitraire.
        """
        for i, souvenir in enumerate(self.souvenirs):
            if souvenir['pos'] == position and souvenir['type'] == type_evenement:
                souvenir['tick'] = tick_absolu
                # v36.0 — LA RÉCURRENCE DEVIENT UNE ABSTRACTION. Le doublon n'est plus
                # jeté : il CONFIRME le repère. `confirmations` compte combien de fois
                # l'expérience s'est répétée ici — c'est ce compteur qui transforme un
                # fait isolé (« j'ai mangé là une fois ») en régularité du monde (« il y
                # a toujours à manger là »).
                souvenir['confirmations'] = souvenir.get('confirmations', 1) + 1
                # La valence est la MOYENNE GLISSANTE des chocs vécus ici. Aucune table,
                # aucun mot-clé : un endroit devient « bon » ou « mauvais » par accumulation
                # d'expérience, exactement comme un conditionnement.
                n = souvenir['confirmations']
                souvenir['valence'] = (souvenir.get('valence', 0.0) * (n - 1) + intensite) / n
                # v39.0 — la confirmation nourrit AUSSI l'empreinte de type. Sans cela,
                # `empreinte_types` n'enregistrerait que les premières impressions et
                # ignorerait toute la répétition — or c'est précisément la récurrence qui
                # produit l'abstraction (v36.0).
                self._nourrir_empreinte(type_evenement, intensite)
                self.souvenirs.append(self.souvenirs.pop(i))
                self.doublons_evites += 1
                return
        # --- v39.1 : LE PRIOR D'EMPREINTE — « je ne suis jamais venu ici, mais je sais
        #             ce que vaut CE GENRE d'endroit » ---
        #
        # Un repère naissait avec la valence du SEUL choc de l'instant. Il naît désormais
        # d'un mélange entre ce choc et ce que l'agent a appris du TYPE, sur toute sa vie.
        # C'est le transfert du tout-petit : il n'a jamais vu CE chien, mais il sait déjà
        # que les chiens mordent.
        #
        # ⚠️ Sans ce branchement, `empreinte_types` (v39.0) était écrite, sérialisée,
        # télémétrée — et JAMAIS LUE. Un agent v39.0 se comportait exactement comme un
        # v38 : le QUOI survivait aux promotions, enfermé dans une boîte que le cerveau
        # n'ouvrait pas. Mesurer la v39.0 aurait produit un « effet nul » parfaitement
        # crédible et parfaitement faux — le symétrique de l'ablation d'un organe vide.
        #
        # LE POIDS DU PRIOR EST DÉRIVÉ, JAMAIS POSÉ. Il vaut la solidité de l'empreinte
        # du type : `n / (n + SOUVENIRS_CONFIRMATIONS_REFERENCE)`, exactement la même
        # saturation douce que `rappel_le_plus_marquant` applique déjà aux repères. Un
        # type vu deux fois n'impose presque rien ; un type vécu cent fois pèse. Le
        # préjugé se mérite par l'expérience, et il ne peut jamais écraser complètement
        # le vécu de l'instant (le poids tend vers 1 sans l'atteindre).
        #
        # ⚠️ Rien n'est expliqué en dur : aucune table, aucun seuil, aucun type nommé.
        # Le prior est une moyenne d'expériences réellement vécues par CET agent.
        e = self.empreinte_types.get(type_evenement)
        if e is not None:
            n = e['confirmations']
            poids = n / (n + SOUVENIRS_CONFIRMATIONS_REFERENCE)
            valence_initiale = (1.0 - poids) * float(intensite) + poids * e['valence']
        else:
            valence_initiale = float(intensite)   # type inédit : rien à transférer

        self.souvenirs.append({'pos': position, 'type': type_evenement, 'tick': tick_absolu,
                               'confirmations': 1, 'valence': valence_initiale})
        self._nourrir_empreinte(type_evenement, intensite)
        if len(self.souvenirs) > self.capacite_max:
            # v36.0 — l'éviction ne jette plus aveuglément le plus ancien : elle jette le
            # MOINS ABSTRAIT. Un repère confirmé cent fois est une régularité du monde ;
            # un repère vu une seule fois est peut-être un accident. À confirmations
            # égales, le plus ancien part (FIFO), ce qui préserve la règle v31.0.
            #
            # C'est « l'oubli comme archivage » : ce qui a produit une abstraction solide
            # survit, le détail non consolidé se dégrade.
            idx_faible = min(range(len(self.souvenirs)),
                             key=lambda k: (self.souvenirs[k].get('confirmations', 1),
                                            self.souvenirs[k]['tick']))
            self.souvenirs.pop(idx_faible)

    def recuperer_contexte(self, position_actuelle, type_recherche: str, tick_absolu: int):
        """Retrouve le souvenir le plus pertinent pour le TYPE de besoin courant (ex:
        SURVIVAL_FOOD -> cherche un souvenir 'FOOD'), en combinant proximité spatiale et
        fraîcheur temporelle. Retourne (distance_normalisee, fraicheur) dans [0, 1], ou
        None si aucun souvenir pertinent n'existe encore."""
        souvenirs_utiles = [s for s in self.souvenirs if s['type'] == type_recherche]
        if not souvenirs_utiles:
            return None

        def distance_manhattan(s):
            return abs(s['pos'][0] - position_actuelle[0]) + abs(s['pos'][1] - position_actuelle[1])

        meilleur = min(souvenirs_utiles, key=distance_manhattan)
        distance = distance_manhattan(meilleur)
        distance_normalisee = 1.0 / (1.0 + distance)  # proche de 1 si tout proche, vers 0 si loin

        age = max(0, tick_absolu - meilleur['tick'])
        fraicheur = max(0.0, 1.0 - (age / self.fenetre_fraicheur))

        return distance_normalisee, fraicheur

    def rappel_le_plus_marquant(self, position_actuelle, tick_absolu):
        """v36.0 — LE RAPPEL AGNOSTIQUE : « qu'est-ce qui compte, près d'ici ? »

        Contrairement à `recuperer_contexte`, cette lecture ne demande **aucun type** :
        elle balaie TOUS les repères, quelle que soit leur étiquette. C'est ce qui la rend
        conforme à l'invariant « rien n'est expliqué en dur » — le cerveau ne cherche pas
        « de la nourriture » ou « une clé », il cherche ce qui est **proche, confirmé et
        chargé**, sans savoir de quoi il s'agit.

        Retourne `(valence, confiance)` dans [−1, 1] × [0, 1], ou None si la mémoire est
        vide :
          - `valence`  : l'expérience moyenne vécue là — apprise, jamais déclarée. C'est
                         le seul canal par lequel un danger peut devenir « évitable » sans
                         qu'aucune ligne de code ne mentionne le mot « lave ».
          - `confiance`: à quel point ce repère est une ABSTRACTION solide plutôt qu'un
                         accident — combine la répétition (`confirmations`) et la
                         fraîcheur. C'est « l'archive dégradable » : un repère ancien et
                         peu confirmé s'efface, un repère souvent confirmé résiste.

        Le repère retenu est celui qui pèse le plus, pondéré par la proximité : un souvenir
        très marquant mais à l'autre bout de la carte ne doit pas masquer un souvenir tiède
        juste devant.
        """
        if not self.souvenirs:
            return None

        def evaluer(s):
            d = abs(s['pos'][0] - position_actuelle[0]) + abs(s['pos'][1] - position_actuelle[1])
            proximite = 1.0 / (1.0 + d)
            n = s.get('confirmations', 1)
            # Saturation douce : la 1re confirmation apporte beaucoup, la 50e presque rien.
            # Une régularité n'a pas besoin d'être vue mille fois pour être une régularité.
            solidite = n / (n + SOUVENIRS_CONFIRMATIONS_REFERENCE)
            age = max(0, tick_absolu - s['tick'])
            fraicheur = max(0.0, 1.0 - (age / self.fenetre_fraicheur))
            return proximite * abs(s.get('valence', 0.0)), solidite, fraicheur, proximite

        meilleur = max(self.souvenirs, key=lambda s: evaluer(s)[0])
        _, solidite, fraicheur, proximite = evaluer(meilleur)
        valence = float(np.clip(meilleur.get('valence', 0.0), -1.0, 1.0))
        # La confiance combine les trois : une abstraction solide (souvent confirmée),
        # encore fraîche, et proche d'ici. Le produit est volontaire — il suffit qu'un
        # seul facteur s'effondre pour que le rappel cesse de peser.
        confiance = float(np.clip(solidite * fraicheur * proximite, 0.0, 1.0))
        return valence, confiance


# --- 3g. LECTURE SYNESTHÉSIQUE DE LA CASE FRONTALE (v27.0, générique) ---
# Distinct de 3b : les détecteurs 3b renvoient tous un couple (micro_recompense,
# poids_choc) et alimentent directement la récompense. LecteurCaseFrontale ne renvoie
# AUCUNE récompense — il renvoie un MOT. Il respecte la même règle d'agnosticité que 3b
# (CLAUDE.md : aucune position, aucun identifiant de niveau, aucun palier écrit en dur),
# mais le mettre dans 3b brouillerait le contrat de cette section (couple récompense).
MOT_PAR_OBJET_MINIGRID = {
    "wall": "mur", "door": "porte", "key": "clé", "goal": "but",
    "ball": "balle", "box": "boîte", "lava": "lave", None: "vide",
}
MOT_PAR_COULEUR_MINIGRID = {
    "red": "rouge", "green": "vert", "blue": "bleu",
    "purple": "violet", "yellow": "jaune", "grey": "gris",
}


# v27.4 (correctif utilisateur, "l'agent a l'air de progresser trop vite") : en phases
# 1-2 du Cursus de la Parole (synesthésie active), LecteurCaseFrontale.lire/
# lire_syntagme renvoient un mot différent à CHAQUE tick où l'agent tourne la tête ou
# avance — sans lissage, la cible vocale changeait donc jusqu'à 10×/seconde dans
# l'Arène (FPS_ARENE), bien plus vite que le temps nécessaire pour qu'un mot
# "s'imprime". LecteurCaseFrontale.lire_stable (ci-dessous) n'accepte une nouvelle
# cible qu'après SEUIL_STABILITE_SYNESTHESIE ticks CONSÉCUTIFS passés devant le même
# objet — 20 ticks est un ordre de grandeur cohérent avec PERIODE_LECTURE_VOCALE
# (Arène) et laisse largement le temps à un agent qui explore normalement de
# "s'arrêter" mentalement sur un objet avant qu'il compte comme la cible à apprendre,
# sans pour autant exiger une immobilité totale prolongée.
SEUIL_STABILITE_SYNESTHESIE = 20


class LecteurCaseFrontale:
    """v27.0 — "Synesthésie réelle" (décision utilisateur) : le mot que l'agent doit
    nommer n'est plus tiré d'un curriculum abstrait déroulé en parallèle de la vision,
    il est LU dans la case juste devant lui. Ce qu'il voit devient ce qu'il dit — c'est
    ce qui transforme la fusion audio+vision du tronc cérébral (somme dans le bus
    latent, _tronc_cerebral) en association sémantique réelle plutôt qu'en simple
    co-occurrence de deux signaux sans rapport.

    Générique au sens de la section 3b (CLAUDE.md) : aucune position, aucun identifiant
    de niveau, aucun palier écrit en dur — le mot se déduit du TYPE de l'objet MiniGrid
    rencontré, quel que soit le niveau. Sur un niveau sans porte ni clé, il renvoie
    simplement "mur" et "vide", qui sont eux-mêmes des mots valides du curriculum.

    Dégradation identique aux détecteurs 3b : _MINIGRID_INTERNALS_OK à False, ou toute
    exception d'API, désactive le lecteur définitivement (self.actif = False) après UN
    avertissement — jamais de crash de l'entraînement.

    Sans état inter-tick pour `lire`/`lire_syntagme` (contrairement aux détecteurs 3b) :
    pas de reinitialiser_episode, volontairement — la case frontale ne dépend que de la
    position/orientation courantes de l'agent, jamais de l'historique de l'épisode.
    `lire_stable` (v27.4) fait exception : elle porte un état de stabilisation minimal
    (mot brut vu + compteur de répétitions), voir sa docstring."""

    def __init__(self):
        self.actif = _MINIGRID_INTERNALS_OK
        self._avertissement_donne = False
        self.dernier_mot = None
        self.dernier_objet = None
        # v27.4 (correctif utilisateur, "l'agent a l'air de progresser trop vite") :
        # état de stabilisation pour lire_stable — voir sa docstring.
        self._mot_brut_courant = None
        self._ticks_stables = 0
        self._cible_stabilisee = None

    def _avertir(self, exception):
        if not self._avertissement_donne:
            print(f"⚠️  Lecteur de case frontale désactivé (API minigrid incompatible : {exception})")
            self._avertissement_donne = True
        self.actif = False

    def lire(self, env) -> tuple:
        """Retourne (mot: str, type_objet: str|None, couleur: str|None).

        Utilise env.unwrapped.front_pos (propriété MiniGrid native = agent_pos +
        dir_vec) plutôt qu'un recalcul manuel de la direction. BORNE explicitement les
        coordonnées avant grid.get() : Grid.get lève un AssertionError sur un index hors
        grille — les détecteurs 3b n'ont pas ce problème car ils itèrent sur
        range(width/height), celui-ci lit une position dérivée de l'orientation de
        l'agent, qui peut en théorie pointer hors grille. Hors grille → "mur" (ce qui
        est sémantiquement exact : le bord d'un niveau MiniGrid est toujours un mur).

        Retourne ("vide", None, None) si le lecteur est inactif — l'appelant traite ce
        cas comme "pas de cible synesthésique ce tick"."""
        if not self.actif:
            return "vide", None, None
        try:
            noyau_env = env.unwrapped
            fx, fy = (int(v) for v in noyau_env.front_pos)
            grille = noyau_env.grid
            if not (0 <= fx < grille.width and 0 <= fy < grille.height):
                self.dernier_mot, self.dernier_objet = "mur", "wall"
                return "mur", "wall", None
            objet = grille.get(fx, fy)
            type_objet = objet.type if objet is not None else None
            couleur = getattr(objet, "color", None) if objet is not None else None
            mot = MOT_PAR_OBJET_MINIGRID.get(type_objet, "vide")
            self.dernier_mot, self.dernier_objet = mot, type_objet
            return mot, type_objet, couleur
        except Exception as e:
            self._avertir(e)
            return "vide", None, None

    def lire_syntagme(self, env) -> tuple:
        """Comme `lire`, mais renvoie le syntagme "<objet> <couleur>" (ex. "porte
        jaune", ordre nom-adjectif du français, cohérent avec le palier 19 du
        curriculum vocal) quand une couleur existe. Réservé à la phase d'émancipation
        du Cursus de la Parole (cursus_parole.py) : deux mots demandent une cible F1/F2
        unique (celle de la première voyelle du syntagme), raccourci du même ordre que
        les paliers 13-14 existants ("ouvre porte")."""
        mot, type_objet, couleur = self.lire(env)
        if couleur is None or type_objet is None:
            return mot, type_objet, couleur
        mot_couleur = MOT_PAR_COULEUR_MINIGRID.get(couleur)
        if mot_couleur is None:
            return mot, type_objet, couleur
        return f"{mot} {mot_couleur}", type_objet, couleur

    def lire_stable(self, env, seuil_stabilite: int = SEUIL_STABILITE_SYNESTHESIE,
                     syntagme: bool = False) -> tuple:
        """v27.4 (correctif utilisateur) : comme `lire`/`lire_syntagme`, mais la cible
        publiée ne change que si l'agent a regardé LE MÊME mot pendant au moins
        `seuil_stabilite` ticks CONSÉCUTIFS. Retourne (mot, type_objet, couleur, stable)
        — `stable` indique si CE tick vient de déclencher une nouvelle stabilisation
        (utile pour ne recalculer une nouvelle référence audio qu'à ce moment-là).

        Motivation : sans lissage, `lire`/`lire_syntagme` renvoient un mot différent à
        CHAQUE tick où l'agent tourne la tête ou avance — la cible vocale changeait donc
        aussi vite que le regard de l'agent (jusqu'à 10×/seconde dans l'Arène), sans
        jamais laisser à `porte_auditive`/`tete_vocale` le temps de vraiment "digérer"
        un mot avant qu'il soit remplacé. Un enfant qu'on nomme "porte" doit rester
        devant la porte un moment, pas juste la croiser du regard en passant.

        Mécanique : un compteur `_ticks_stables` s'incrémente tant que le mot BRUT lu ce
        tick est identique au précédent, et se remet à zéro dès qu'il change (aucune
        tolérance — un aller-retour du regard annule la progression, cohérent avec
        "rester devant l'objet"). La cible PUBLIÉE (`_cible_stabilisee`) ne se met à jour
        que lorsque `_ticks_stables` atteint le seuil ; avant cela, la précédente cible
        stabilisée reste active (ou None si aucune ne l'a jamais été). C'est la variante
        recommandée face à un simple verrou temporel fixe : elle exige explicitement
        que l'exposition soit CONTINUE devant l'objet, pas seulement qu'il ait été vu une
        fois puis oublié en attendant l'expiration d'un minuteur."""
        mot_brut, type_objet, couleur = (
            self.lire_syntagme(env) if syntagme else self.lire(env)
        )

        if mot_brut == self._mot_brut_courant:
            self._ticks_stables += 1
        else:
            self._mot_brut_courant = mot_brut
            self._ticks_stables = 1

        stable_ce_tick = False
        if self._ticks_stables >= seuil_stabilite and self._cible_stabilisee != mot_brut:
            self._cible_stabilisee = mot_brut
            stable_ce_tick = True

        return self._cible_stabilisee, type_objet, couleur, stable_ce_tick


def etat_mental_dopamine(teneur, dmin, dneutre, dmax):
    pct = 100.0 * (teneur - dmin) / (dmax - dmin)
    if pct < 5:
        label = "💤 Aphasique"
    elif pct < 35:
        label = "😐 Sous-motivé"
    elif pct < 65:
        label = "⚖️ Neutre"
    elif pct < 90:
        label = "⚡ Motivé"
    else:
        label = "🔥 Hyper-Motivé"
    return label, pct


def etat_empreinte(empreinte):
    if empreinte >= 0.75:
        return "🧠 Empreinte Enfance Forte"
    elif empreinte >= 0.4:
        return "🧠 Empreinte en Transition"
    else:
        return "🧠 Raisonnement Froid (Système 2 dominant)"


# --- 3h. CHRONOMÈTRE DE JALONS DOORKEY (v33.0-etape0, télémétrie PURE) ---
class ChronometreJalonsDoorKey:
    """
    Étape 0 de la v33.0 : MESURER avant de refondre (méthode posée en v30.1).

    Le diagnostic « l'agent bloque au Palier 7 parce que le segment porte→but est un
    désert de signal » est aujourd'hui une DÉDUCTION DE LECTURE DE CODE, jamais une
    mesure. Ce chronomètre découpe l'épisode en trois deltas pour trancher :

        Δt1 : reset → prise de la clé
        Δt2 : prise de la clé → déverrouillage de la porte
        Δt3 : déverrouillage → sortie (le « désert » présumé)

    Ce que la mesure doit départager (l'enjeu est le PLAN de la v33, pas un détail) :
    - Δt3 domine        → le désert de récompense est bien le goulot, la conception du
                          document CONCEPTION_v33 s'applique telle quelle ;
    - Δt2 domine        → le vrai goulot est le TRANSPORT de la clé (l'agent erre en
                          cherchant à manger), et c'est le conflit viscéral qu'il faut
                          traiter d'abord — la priorité de la v33 change ;
    - Δt1 domine        → le problème est en amont, bien avant le Palier 7.

    Mesure complémentaire — le CONFLIT VISCÉRAL : `ressources_post_cle` compte les
    consommations FOOD/WATER survenues clé en main. Si « l'agent erre avec la clé en
    cherchant à manger » est vrai, ce compteur le prouve directement.

    Contrat de cette classe (non négociable tant qu'elle reste une étape 0) :
    - elle ne retourne AUCUNE récompense et AUCUN poids de choc — contrairement à tous
      les détecteurs de 3a/3b, elle n'entre ni dans `recompense_interne`, ni dans
      `poids_evenement`, ni dans le gradient. Elle observe, point. L'empreinte MD5 des
      400 actions à graine fixée doit rester identique après son ajout ;
    - un jalon n'est chronométré qu'une fois par épisode (`is None`), sinon un
      aller-retour devant la porte réécrirait la mesure ;
    - les épisodes incomplets ne sont PAS comptés dans les moyennes : un Δt3 n'existe
      que si l'agent a réellement déverrouillé ET franchi. C'est ce qui distingue « le
      segment est lent » de « le segment n'est jamais atteint » — deux diagnostics
      opposés que confondrait une moyenne sur zéro.

    Comme `DetecteurJalonsDoorKey` (3a) et contrairement aux détecteurs génériques de
    3b, cette classe est SPÉCIFIQUE à la mécanique clé/porte/but de DoorKey : elle n'a
    aucun sens sur `Empty` ou `MultiRoom`, et reste inerte s'il n'y a pas de porte.
    """
    def __init__(self):
        self.actif = _MINIGRID_INTERNALS_OK
        self._avertissement_donne = False
        self.reinitialiser_episode(None)

    def _avertir(self, exception):
        if not self._avertissement_donne:
            print(f"⚠️  Chronomètre de jalons DoorKey désactivé (API minigrid incompatible : {exception})")
            self._avertissement_donne = True
        self.actif = False

    def reinitialiser_episode(self, env):
        self.tick_prise_cle = None
        self.tick_deverrouillage = None
        self.tick_sortie = None
        self.porte_etait_verrouillee = None
        self.carrying_precedent = None
        self.ressources_post_cle = 0
        self.pos_porte = None
        if env is None or not self.actif:
            return
        try:
            grille = env.unwrapped.grid
            for x in range(grille.width):
                for y in range(grille.height):
                    if isinstance(grille.get(x, y), Door):
                        self.pos_porte = (x, y)
                        break
                if self.pos_porte is not None:
                    break
        except Exception as e:
            self._avertir(e)

    def signaler_consommation_post_cle(self):
        """Appelée depuis traiter_tick au moment exact d'une consommation FOOD/WATER.
        Ne compte que si la clé est déjà en main : c'est la mesure du conflit viscéral
        PENDANT le transport, pas de l'appétit général de l'agent."""
        if self.tick_prise_cle is not None and self.tick_sortie is None:
            self.ressources_post_cle += 1

    def evaluer_tick(self, env, tick_episode: int, recompense_env: float):
        """Purement observationnel : ne retourne rien, n'influence rien."""
        if not self.actif:
            return
        try:
            carrying = env.unwrapped.carrying

            if self.tick_prise_cle is None and isinstance(carrying, Key) \
                    and self.carrying_precedent is None:
                self.tick_prise_cle = tick_episode
            self.carrying_precedent = carrying

            if self.pos_porte is not None and self.tick_deverrouillage is None:
                porte = env.unwrapped.grid.get(*self.pos_porte)
                if isinstance(porte, Door):
                    # Le déverrouillage se lit sur la TRANSITION verrouillée → ouverte,
                    # jamais sur l'état courant seul : une porte déjà ouverte au reset
                    # (cartes sans serrure) ne doit pas être datée au tick 0.
                    if self.porte_etait_verrouillee and not porte.is_locked:
                        self.tick_deverrouillage = tick_episode
                    self.porte_etait_verrouillee = porte.is_locked

            if self.tick_sortie is None and recompense_env > 0:
                self.tick_sortie = tick_episode
        except Exception as e:
            self._avertir(e)

    def extraire_deltas(self):
        """Retourne les trois deltas de l'épisode écoulé, `None` pour tout segment
        non parcouru. Un `None` n'est PAS un zéro : il signifie « l'agent n'a jamais
        atteint ce jalon », information que la moyenne doit exclure et non diluer."""
        delta1 = self.tick_prise_cle
        delta2 = (self.tick_deverrouillage - self.tick_prise_cle
                  if self.tick_deverrouillage is not None and self.tick_prise_cle is not None
                  else None)
        delta3 = (self.tick_sortie - self.tick_deverrouillage
                  if self.tick_sortie is not None and self.tick_deverrouillage is not None
                  else None)
        return delta1, delta2, delta3


# --- 4. EXÉCUTION & CURSUS ---
DIM_VISUELLE = 147

BUS_REFERENCE_INITIAL = 16  # taille du bus à la naissance ; sert de référence pour
                             # l'Empreinte de l'Enfance même après résurrection (v21.0)
                             # et pour la masse cérébrale (v41.20) — doit rester défini
                             # AVANT `_plafond_bus_machine()`, qui le lit.

# v41.22 — LES DEUX BORNES DU BUDGET DE CROISSANCE. Ce sont des BORNES au sens du dogme
# (elles disent « pas au-delà »), pas des seuils de décision : rien ne les lit dans le
# chemin cognitif, elles ne servent qu'à convertir une capacité machine en dimension.
FRACTION_RAM_PAR_CERVEAU = 0.02   # part de la RAM d'un cœur qu'un cerveau peut prendre.
                                  # Volontairement basse : le modèle n'est pas le seul
                                  # consommateur d'un run (env, buffers, rêve).
FACTEUR_TEMPS_MATURITE = 100.0    # un cerveau adulte peut coûter jusqu'à 100× un
                                  # nouveau-né par tick. Mesuré : le coût est en O(d²),
                                  # donc cela autorise 10× la dimension de naissance.
                                  # À 160 dims un run de 600 jours prend ~0,05 h — le
                                  # banc de mesure du projet reste praticable.


def _plafond_bus_machine() -> int:
    """v41.22 — LE PLAFOND DU BUS EST UNE PROPRIÉTÉ DE LA MACHINE, PLUS UN CHIFFRE POSÉ.

    🔴 POURQUOI CE CHANGEMENT (mesuré le 17/08, campagne v41.21).
    Tant que le thermostat était cassé, `DIM_BUS_MAX = 96` n'était atteint que par
    **1 cerveau sur 40** : le plafond ne limitait rien. Une fois le thermostat rendu
    relatif (v41.21), **10 cerveaux sur 10 le touchent**. Le plafond est donc devenu le
    facteur qui arrête la croissance — et c'est exactement ce qu'un chiffre posé ne doit
    jamais faire.

    ⚠️ CE QUE LA MESURE DIT, ET QU'IL FAUT ASSUMER : ni la RAM ni le temps ne sont
    réellement contraignants sur cette machine. Mesuré : un cerveau à `dim_bus=512` pèse
    **144 Mo** optimiseur compris (0,4 % des 38,7 Go) et un run de 600 jours à
    `dim_bus=384` prend **0,12 h**. Dériver le plafond de la RAM seule donnerait 544 à
    **1 % du budget**, et 2800 à 25 % — c'est-à-dire un plafond qui ne veut plus rien dire.

    Le plafond retenu est donc celui d'un **budget de calcul explicite** : un run doit
    rester praticable en parallèle sur cette machine. On borne la part du temps qu'un
    tick a le droit de coûter par rapport à la naissance, et on convertit ce budget en
    dimension. Le coût par tick croît en O(d²) (mesuré : 0,30 ms à d=16, 1,73 ms à d=384,
    soit 5,8×), donc `d_max = d_naissance × √(budget_temps)`.

    Le budget est lui-même dérivé du parallélisme réel : la machine fait tourner
    `os.cpu_count()` runs de front, et un cerveau ne doit pas monopoliser plus que sa
    part. C'est la seule grandeur qui change vraiment d'une machine à l'autre.

    Le résultat est **borné par le bas à l'ancienne valeur** : jamais moins que 96, pour
    qu'une petite machine ne rétrograde pas silencieusement des `.brain` existants (le
    même piège que le remappage de `niveau_actuel` en v35.0).

    ⚠️ UNE PREMIÈRE VERSION DE CETTE FONCTION ÉTAIT INOPÉRANTE, et c'est consigné parce
    que c'est exactement la faute que la revue du dogme dénonce. J'avais posé
    `budget = √(cpu_count)`, ce qui donne `16 × √12 = 55`, arrondi à 48 — **moins que
    l'ancien plafond de 96**, donc entièrement absorbé par le plancher. Une borne
    inventée qui ne mord jamais n'est pas une dérivation : c'est un chiffre posé avec un
    habillage. La formule ci-dessous part des DEUX mesures réelles.
    """
    import os as _os
    coeurs = max(1, _os.cpu_count() or 1)
    try:
        ram = _os.sysconf("SC_PAGE_SIZE") * _os.sysconf("SC_PHYS_PAGES")
    except (ValueError, AttributeError, OSError):
        ram = 4e9      # machine qui ne sait pas se décrire : hypothèse basse

    # --- Borne 1 : LA MÉMOIRE ---------------------------------------------------------
    # La machine fait tourner `coeurs` runs de front ; un cerveau ne doit pas monopoliser
    # plus que sa part. `FRACTION_RAM_PAR_CERVEAU` est volontairement basse : le modèle
    # n'est pas le seul consommateur d'un run (environnement, buffers, rêve).
    # Coût mesuré : ~8,5·d² paramètres, ×4 octets, ×3 (poids + moments Adam).
    budget_octets = (ram / coeurs) * FRACTION_RAM_PAR_CERVEAU
    d_ram = math.sqrt(budget_octets / (8.5 * 4 * 3))

    # --- Borne 2 : LE TEMPS -----------------------------------------------------------
    # Le coût par tick croît en O(d²) — mesuré : 0,30 ms à d=16, 1,73 ms à d=384 (5,8×,
    # soit exactement (384/16)^2 amorti par les frais fixes). Un cerveau mature a le droit
    # de coûter `FACTEUR_TEMPS_MATURITE` fois un nouveau-né : au-delà, un run long cesse
    # d'être praticable et le banc de mesure du projet s'effondre.
    d_temps = BUS_REFERENCE_INITIAL * math.sqrt(FACTEUR_TEMPS_MATURITE)

    # La plus CONTRAIGNANTE des deux gouverne — c'est la définition d'un plafond.
    d_max = int(min(d_ram, d_temps))
    # Arrondi au pas de neurogenèse, et jamais sous le plafond historique : une machine
    # modeste ne doit pas rétrograder silencieusement des `.brain` déjà à 96.
    return max(96, (d_max // 16) * 16)


DIM_BUS_MAX = _plafond_bus_machine()
# v41.23 — surcharge du plafond pour les BANCS DE MESURE uniquement. Le seul moyen de
# savoir si la croissance s'arrête d'elle-même est de relever le plafond hors de portée
# et de regarder où elle se pose : tant que `dim_bus` finit exactement AU plafond, on
# mesure le plafond, jamais le frein. N'est jamais lue par la décision.
_PLAFOND_TEST = os.environ.get("NAULTHENE_PLAFOND_BUS", "").strip()
if _PLAFOND_TEST.isdigit() and int(_PLAFOND_TEST) >= 96:
    DIM_BUS_MAX = (int(_PLAFOND_TEST) // 16) * 16
    print(f"🔬 [BANC] plafond de bus forcé à {DIM_BUS_MAX} (NAULTHENE_PLAFOND_BUS)")
# v41.21 — LE PAS DE LA GRILLE. MiniGrid est discret : une case est l'unité de distance
# du monde, et l'agent en occupe exactement une. Ce n'est pas un réglage mais une
# propriété de l'environnement — c'est d'elle que dérivent le rayon du corps
# (`PAS_GRILLE / 2`) et l'unité de translation, qui étaient écrits en dur en v41.20.
PAS_GRILLE = 1.0
JOURS_ENTRE_MUTATIONS = 5

jours_totaux = 500  # run long en local (Mac) — 400 dans agi_google_colab.py
ticks_par_jour = 400
CAPACITE_MEMOIRE = 20

# --- RÉSERVOIR DOPAMINERGIQUE ---
# TENEUR_DOPAMINE n'est plus une globale mutable (v21.0) : c'est désormais
# etat.teneur_dopamine, initialisée à DOPAMINE_NEUTRE dans EtatCognitif.__init__ —
# une seule source de vérité, sérialisable telle quelle par PersistanceAnatomique.
DOPAMINE_NEUTRE = 5.0
DOPAMINE_MIN = 0.001
DOPAMINE_MAX = 10.0

TAUX_FRICTION = 0.01
TAUX_CHOC_BASE = 0.9
TAUX_RESSORT = 0.4

PLAFOND_ERREUR_DOPAMINE = 2.0
BOOST_ANCRAGE_MAX = 20.0
SEUIL_APHASIE_NEUROGENESE = 0.05

# v41.24 — LE BUDGET DE CROISSANCE (voir le thermostat dans `executer_nuit`).
AJOUT_DIM_BASE = 16          # BORNE : la mutation d'un organisme à plein rendement.
                             # C'est un MAXIMUM, jamais une quantité garantie — l'ajout
                             # réel vaut `round(AJOUT_DIM_BASE × vitalité)` et tombe à 0
                             # de lui-même quand le rendement s'effondre.
INERTIE_OUBLI_RENDEMENT = 50.0  # le cliquet du rendement de référence : montée immédiate,
                                # descente ~50× plus lente. Même discipline que
                                # `INERTIE_OUBLI_REFERENCE_CHOC` (v37.1-fix1) — une
                                # référence qui suit la décroissance ne borne plus rien.
# v41.43 — `MALUS_DOULEUR = -0.01` SUPPRIMÉ (P7 de l'audit du génome).
# Retiré du CHEMIN de récompense en v41.27 (la douleur passe par `calculer_deficit`,
# donc par `r_bio`), la DÉFINITION subsistait ici, morte — lue par aucun code du noyau.
# ⚠️ Une constante morte n'est pas inerte : `sonde_recompense` l'a RESSUSCITÉE pendant
# trois versions, facturant un coût disparu sur 57,8 % des ticks et retournant le signe
# de sa conclusion (mesuré le 30/08 : solde affiché −4,1621 contre +0,4579 réel).
# C'était l'une des quatre récompenses posées de l'audit du dogme, et celle qui rendait
# `mourir` (0.0) MOINS CHER que `se cogner` (−0.01).
# ⚠️ `colab.py` (script de référence) la conserve et l'utilise : la suppression ne vaut
# que pour `noyau.py`, conformément à la séparation essai/référence du projet.

# --- CRISTALLISATION SOUPLE (v26.0-experimental, §A.5 AMELIORATION_V1.md, correctif
# "Falaise" sigmoïde) ---
# myeline_cumul accumule la myéline consolidée nuit après nuit (relaxation exponentielle,
# voir NaultheneLinearSynaptique.cycle_sommeil) ; au-delà de SEUIL_CRISTAL, la synapse
# devient cristallisee (cliquet à sens unique) et son érosion nocturne est plancher-protégée
# par p_protection = sigmoid(K_RAIDEUR_CRISTAL * (myeline_cumul - SEUIL_CRISTAL)) — une
# falaise continue plutôt qu'un plancher rigide en tout ou rien : les synapses jamais
# consolidées s'érodent au taux plein (zéro synapse fantôme qui traînerait des centaines de
# nuits), les synapses cristallisées voient leur érosion tendre vers 0 (ancrage quasi
# indestructible). Le gradient diurne (annexe_weight) reste totalement inchangé, cristallisée
# ou non.
ALPHA_CRISTAL = 0.95
# v41.44 — LE SEUIL DE CRISTALLISATION EST RELATIF À LA COUCHE (P6 de l'audit du génome).
#
# 🔴 CE QUE LA MESURE DIT (30/08/2026, 10 cerveaux de la cohorte AB3) :
#
#     0 synapse cristallisée sur 1 906 360        (0,0000 %)
#     myeline_cumul maximum observé : 0,01193434
#     SEUIL_CRISTAL posé            : 0,80        -> 67× trop loin
#
# La Cristallisation Souple v26.0 ne s'est enclenchée sur AUCUN cerveau du dépôt, jamais.
# Ce n'était pas une protection dormante « au cas où » : c'était du code mort exécuté à
# chaque nuit, sur chaque synapse, pour un résultat toujours nul.
#
# C'EST EXACTEMENT LE DÉFAUT QUE LA v37.0 A CORRIGÉ AILLEURS. `q_ref = 1.0` supposait une
# myéline d'ordre 1 alors qu'elle vaut ~0,002 — échelle 500× trop grande, `myeline_norm`
# collée à 0. Le correctif fut `echelle_myeline`, un QUANTILE de la couche. `SEUIL_CRISTAL`
# est le même bug, au même endroit, resté en place quatre versions de plus : une échelle
# absolue posée a priori, jamais confrontée à une mesure.
#
# LA CORRECTION suit le patron déjà validé : le seuil devient une FRACTION de l'échelle
# que la couche a elle-même atteinte (`echelle_myeline`, monotone croissante, quantile 0,75
# de `myeline_M`). Une synapse cristallise quand son `myeline_cumul` dépasse nettement ce
# que sa propre couche a connu — jamais quand il dépasse un chiffre venu d'ailleurs.
#
# ⚠️ CE QUI RESTE UNE BORNE, ASSUMÉE : `FRACTION_SEUIL_CRISTAL` dit « nettement au-dessus
# de l'ordinaire de cette couche », pas une valeur de myéline. Elle est > 1 par
# construction : cristalliser DOIT rester exceptionnel, sinon le cliquet fige tout le
# réseau et l'érosion nocturne — donc l'oubli — cesse d'exister.
#
# ⚠️ NON MESURÉ EN COMPORTEMENT. Ce correctif REND POSSIBLE une mécanique qui n'a jamais
# tourné ; il ne démontre pas qu'elle aide. Elle peut très bien nuire — figer des synapses
# est irréversible (cliquet à sens unique). D'où le drapeau `--sans-cristallisation`, et
# d'où le choix d'un seuil volontairement haut.
FRACTION_SEUIL_CRISTAL = 3.0   # borne : « 3× l'ordinaire de la couche ». Au-dessus de
                               # l'échelle (quantile 0,75), donc réservé aux synapses
                               # nettement plus myélinisées que leurs voisines.
SEUIL_CRISTAL_FOSSILE = 0.80   # la valeur absolue d'avant la v41.44 — conservée comme
                               # TÉMOIN, et comme trace du chiffre jamais franchi.
CRISTALLISATION_RELATIVE_ACTIVE = True   # --cristallisation-fossile pour le témoin
CRISTALLISATION_ACTIVE = True            # --sans-cristallisation coupe la mécanique
K_RAIDEUR_CRISTAL = 10.0

# --- v34.0-fix1 : LE PLANCHER VITAL (correctif de l'EXTINCTION SYNAPTIQUE) ---
#
# 🔴 BUG MESURÉ (2026-08-06, cerveau 060820260038_V34_1500_RMD) : 8 couches sur 11
# entièrement à ZÉRO après 1500 nuits — porte_visuelle, porte_auditive, hippocampe,
# fusion_memoire, analyseur, generateur_attente(_audio), tete_requete. Le cerveau était
# devenu littéralement aveugle et sourd : bus_latent nul ⇒ JEPA nul ⇒ C2 nul ⇒ politique
# réduite au hasard uniforme (entropie 1.94587 pour un maximum ln(7)=1.94591).
#
# MÉCANIQUE DE L'EXTINCTION, en trois maillons :
#   1. `myeline_M = max(myeline_M, |annexe_weight|)` — la myéline ne peut venir QUE du
#      gradient. Un agent sans récompense a des gradients infimes, donc myéline ≈ 0.
#   2. L'érosion vaut alors `base *= (1 - lambda)` à taux PLEIN, chaque nuit. Avec
#      lambda=0.05, un poids de 0.05 tombe sous le seuil de pruning (1e-4) en 121 nuits.
#   3. L'Étape 4 met à 0.0 tout ce qui passe sous 1e-4 — définitivement.
#
# POURQUOI LA PROTECTION EXISTANTE N'A JAMAIS FONCTIONNÉ : `SEUIL_CRISTAL = 0.80` alors
# que la myéline maximale MESURÉE sur les cerveaux du dépôt est de **0.0038** — soit un
# seuil 210× trop haut. Le compteur `cristallisee` vaut 0 sur 11 760 synapses pour TOUS
# les cerveaux examinés : la Cristallisation Souple de la v26.0 n'a jamais pu s'enclencher
# une seule fois. Ce n'est pas un réglage à ajuster, c'est une échelle qui ne correspond
# à rien de réel.
#
# LE CORRECTIF : un plancher d'érosion qui ne dépend d'AUCUN seuil absolu. Quelle que soit
# la myéline, une couche ne peut pas perdre plus qu'une fraction de sa norme par nuit —
# l'oubli reste possible (c'est le rôle du sommeil), l'EXTINCTION ne l'est plus.
#
# Ce n'est pas une constante de fonctionnement mais une BORNE (doctrine : les constantes
# sont des bornes, les valeurs sont dérivées). La quantité réellement érodée reste
# émergente ; seul son plafond est fixé.
#
# Le précédent était connu : `ATTENUATION_EROSION_AUDIO_DEBUT` (v24.0-fix1) corrigeait
# déjà « zéro exact après 1000 nuits d'érosion non amortie » — mais UNIQUEMENT sur les 3
# couches audio, et par un facteur daté au palier vocal. Le présent correctif est général
# et ne dépend d'aucun calendrier.
FRACTION_NORME_MIN_COUCHE = 0.10   # une couche conserve ≥ 10 % de la norme qu'elle avait
                                    # à l'entrée de la nuit — borne, jamais une cible
PLANCHER_POIDS_VITAL = 1e-3        # sous ce seuil, une synapse non nulle n'est plus
                                    # érodée du tout : elle peut stagner, jamais mourir
QUANTILE_ECHELLE_MYELINE = 0.75    # v37.0-fix — quantile de `myeline_M` qui sert d'échelle
                                    # de référence à la couche. Normaliser par le MAXIMUM
                                    # strict ferait porter l'échelle par une seule synapse
                                    # extrême (mesuré sur tete_motrice : p50=0,027 mais
                                    # p99=1,000), écrasant la protection moyenne à 12,7 %
                                    # face à une érosion de 5 % — insuffisant, la couche
                                    # restait figée au millième près. Au 3e quartile, une
                                    # synapse du peloton de tête de sa couche est protégée,
                                    # et non la seule championne.
PLANCHER_ECHELLE_MYELINE = 1e-6    # v37.0-fix — borne basse de `echelle_myeline`, l'échelle
                                    # de référence PROPRE À CHAQUE COUCHE qui remplace
                                    # l'ancien `q_ref=1.0` absolu. Sert uniquement à éviter
                                    # une division par zéro à la toute première nuit d'une
                                    # couche qui n'a encore rien myélinisé ; au-delà, la
                                    # valeur est mesurée (max historique de `myeline_M`),
                                    # jamais déclarée.

# --- MODE LIBRE (DoorKey uniquement) ---
# Décrochage précoce (v17.0) : la béquille de guidage artificiel (RECOMPENSE_APPROCHE_BUT)
# se lève dès le Palier 5 (Viser la Porte) au lieu d'attendre le Palier 7 — l'agent est
# confronté à l'inconnu plus tôt, pendant qu'il travaille encore les paliers 5/6/7,
# plutôt que d'attendre une maîtrise complète avant tout lâcher-prise.
SEUIL_PALIER_MODE_LIBRE = 5
COEFF_ENTROPIE_GUIDE = 0.02
COEFF_ENTROPIE_LIBRE = 0.06

# --- v40.0 : LA PLANIFICATION ÉMERGENTE (force_planification n'est plus une constante) ---
#
# Formulation utilisateur : « C1 a toujours raison, SAUF si C2 estime que le bénéfice
# dépasse le risque au vu des expériences passées. L'enfant est entièrement piloté par C1 ;
# chaque fois qu'il gagne = OKAY, chaque fois qu'il perd = DANGER ; C2 mesure si le pari en
# vaut la peine. »
#
# Ce qui DISPARAÎT : FORCE_PLANIFICATION_GUIDE (0.5), FORCE_PLANIFICATION_LIBRE (0.85) et
# RATIO_C1C2_VISE (2.0). Ces trois nombres fixaient un rapport de force posé a priori, jamais
# confronté à une mesure — et l'ablation du 14/08 a montré qu'aucune valeur unique ne peut
# être juste : couper C2 MULTIPLIE le succès par 4,5 sur DoorKey-5x5 mais l'ANNULE sur 8x8.
# Une constante qui devrait dépendre du contexte était figée pour tous les contextes.
#
# Ce qui REMPLACE : deux compteurs de vécu, et rien d'autre.
#
#                            OKAY
#     f_planif  =  ────────────────────────────
#                   OKAY  +  DANGER  +  PRUDENCE_NAISSANCE
#
# OKAY et DANGER sont les sommes pondérées des chocs dopaminergiques réellement vécus
# (positifs / négatifs) — exactement la matière que `chocs_dopamine_journee` collecte déjà.
# Rien n'est déclaré : l'agent ne sait pas ce qu'est une victoire, il sait qu'il a ressenti
# n fois un choc positif et m fois un choc négatif.
#
# PRUDENCE_NAISSANCE = 1.0 n'est PAS un rapport de force : c'est un a priori de Laplace,
# l'équivalent d'UNE observation fictive de prudence. Il ne sert qu'à donner un sens à la
# fraction quand l'agent n'a encore rien vécu (0/0 est indéfini). À la naissance f = 0/1 = 0
# — C1 SEUL, littéralement l'enfant de la formulation. Au premier succès f = 1/2, après neuf
# succès et un échec f = 9/11 ≈ 0,82. La force de planification GRANDIT avec l'expérience,
# elle n'est jamais accordée.
PRUDENCE_NAISSANCE = 1.0

# Le CLIQUET, repris à l'identique de `reference_choc_dopamine` (v37.1-fix1) : le DANGER
# s'inscrit vite, il s'efface lentement. Sans lui, un agent traversant une mauvaise passe
# verrait f s'effondrer et perdrait sa planification PRÉCISÉMENT quand il en a le plus
# besoin — la boucle qui s'auto-verrouille. La décroissance reste NON NULLE (un monde
# durablement plus dur doit pouvoir recalibrer), mais sur des centaines de nuits.
#
# v41.0 — LES DEMI-VIES SONT RECALIBRÉES SUR UNE MESURE, plus posées à vue.
#
# Mesure du benchmark « C1 pur » (3 graines × 2000 jours, 14/08/2026) : le réservoir
# DANGER croît de façon LINÉAIRE sur toute la durée du run — 0 → 186 pour g11, avec une
# pente encore à +0,096/jour sur les 200 DERNIERS jours. Aucun aplatissement.
#
# La cause est arithmétique : OUBLI_DANGER = 0,99990 a une demi-vie de **6931 jours**.
# Sur un run de 2000 jours, l'oubli n'existe tout simplement pas — le réservoir ACCUMULE.
# Le cliquet n'était pas asymétrique, il était **inopérant des deux côtés** (OKAY :
# 1386 jours, soit encore 70 % de la durée totale d'un run).
#
# Une constante d'oubli ne se lit pas en « pour mille par jour » — elle se lit en DEMI-VIE,
# et c'est la demi-vie qui doit être comparable à l'échelle de temps du vécu. Un agent qui
# vit 2000 jours doit pouvoir oublier une mauvaise saison en quelques centaines de nuits,
# pas en trois fois sa propre vie.
#
# L'asymétrie du cliquet est PRÉSERVÉE et devient enfin visible : le danger s'efface
# ~1,7× plus lentement que le succès. C'est le rapport, pas la valeur absolue, qui porte
# le principe « ce qui a fait mal s'oublie plus lentement que ce qui a marché ».
DEMI_VIE_OKAY = 300.0              # jours — ce qui a marché s'oublie lentement...
DEMI_VIE_DANGER = 500.0            # ...et ce qui a fait mal ~1,7× plus lentement encore.
                                    # L'asymétrie est le cliquet : elle interdit à une
                                    # bonne série d'effacer la mémoire d'un danger réel.
OUBLI_OKAY = 0.5 ** (1.0 / DEMI_VIE_OKAY)        # ≈ 0,997692
OUBLI_DANGER = 0.5 ** (1.0 / DEMI_VIE_DANGER)    # ≈ 0,998615

# --- v41.0 : LA LIGNE DE FLOTTAISON MÉTABOLIQUE ---
#
# Formulation utilisateur : « Le zéro n'est pas 0.0, c'est la ligne de flottaison
# métabolique. Le métabolisme de base est le coût incompressible d'un organisme vivant. Un
# pas qui consomme −0,02 de satiété est un pas NEUTRE (0 danger, 0 succès). »
#
# POURQUOI ELLE EST INDISPENSABLE (et pas un raffinement). Mesuré avant implémentation, sur
# la journée type de g11 : sommer les saillances SANS zéro de référence est arithmétiquement
# PIRE que moyenner. La somme brute compte les 400 micro-négatifs du coût métabolique
# (2,28 cumulé) comme s'ils étaient des événements — `danger` sature à 1,0 et `okay` monte
# à 0,25 UN JOUR SANS AUCUNE VICTOIRE. C'est le défaut exactement symétrique de la moyenne :
# au lieu de noyer la victoire sous le coût, on noie tout dans le bruit.
#
#   opérateur              okay (avec victoire)   danger   okay (sans victoire)
#   moyenne  (v40)              0,0000            0,0146         0,0000
#   somme nue                   1,0000            1,0000         0,2503   ← inutilisable
#   somme au-dessus flottaison  1,0000            ~1,0           0,0209   ← v41.0
#
# D'OÙ VIENT LE ZÉRO — IL EST DÉRIVÉ, JAMAIS POSÉ. La flottaison d'une journée est la
# MÉDIANE des |r| de ses ticks : par construction, c'est le tick ordinaire de cette
# journée-là, donc le coût d'exister tel que l'agent vient de le vivre. Mesuré sur 200
# journées simulées : 0,00574 ± 0,00026 (amplitude 23 %). Écrire `cout_neutre = 0.0057`
# aurait donné le même chiffre — et aurait été une constante en dur, invalide dès que le
# métabolisme, la carte ou l'âge de l'agent changent.
#
# ⚠️ POURQUOI LA MÉDIANE ET NON LA MOYENNE : la moyenne des |r| est tirée par la victoire
# elle-même (+1,0 sur un tick pèse autant que 176 ticks ordinaires). La médiane est
# insensible à cette queue — c'est précisément la propriété recherchée, la même raison qui
# avait fait choisir le 3ᵉ quartile plutôt que le max pour `echelle_myeline` (v37.0).
#
# LE CLIQUET DE FLOTTAISON (demande utilisateur explicite). Même principe que
# `reference_choc_dopamine` (v37.1-fix1) : montée rapide, descente ~50× plus lente. Sans
# lui, un agent traversant une famine prolongée verrait sa ligne de flottaison DESCENDRE
# vers la famine — normalisant l'agonie comme état ordinaire, donc cessant de la compter
# comme un danger. C'est le défaut de `norme_naissance` à l'identique : une référence qui
# suit la décroissance ne borne plus rien. La descente reste NON NULLE (un monde
# durablement plus pauvre doit pouvoir recalibrer l'agent), mais sur des centaines de nuits.
INERTIE_FLOTTAISON = 0.98          # montée : 2 % d'écart absorbé par nuit
FREIN_DESCENTE_FLOTTAISON = 50.0   # descente 50× plus lente que la montée

# --- v40.1 : L'ENVIE DE VIVRE (le couplage C1 ↔ C2) ---
#
# Formulation utilisateur : « L'envie de vivre pousse au maximum la pondération à essayer
# quand même. Cependant quand C2 sera assez fort et l'expérience de C1 assez construite, il
# y a un risque non négligeable que l'envie de vivre diminue au risque de tuer l'agent.
# C'est le jeu de la vie. » Et : « C1 est lui-même lié à cet élément comme une force qui est
# comme de l'ACCEPTATION et devient EXPONENTIELLE liée à la compréhension de C2. »
#
# CE QUE CE N'EST PAS : un troisième module posé à côté de C1 et C2. L'envie de vivre est
# le COUPLAGE entre les deux — ce qui fait que C1 accepte d'autant plus que C2 comprend.
#
# CE QUE ÇA RÉPOND (et que la v40 ne répondait pas) :
#   v40   : « est-ce que je planifie ? »  → f_planif, une balance okay/danger
#   v40.1 : « est-ce que je TENTE ? »     → l'envie, une dynamique multiplicative
# Un agent peut très bien savoir délibérer (f élevé) et refuser d'agir. Rien dans le cerveau
# ne portait cette question : l'envie d'essayer était implicite et constante.
#
# POURQUOI MULTIPLICATIF, JAMAIS UNE MOYENNE. Trois propriétés demandées, qu'une moyenne
# glissante détruirait toutes les trois :
#   1. EFFET BOULE DE NEIGE — le positif appelle le positif. Une suite de facteurs > 1
#      s'emballe ; une moyenne, elle, lisse et ramène au centre.
#   2. INVERSION POSSIBLE — « certains éléments peuvent littéralement changer le sens ». Un
#      seul facteur très bas casse la série ; une moyenne diluerait cet événement.
#   3. LES DEUX COEXISTENT — « l'un n'empêche pas l'autre ». Ce n'est pas un solde net où le
#      positif annule le négatif : `vecu_okay` et `vecu_danger` vivent en parallèle.
# La croissance exponentielle ÉMERGE de la composition, elle n'est jamais déclarée. Il n'y a
# donc aucun `exp()` dans ce code : seulement des produits successifs.
#
# ⚠️ AUCUN PLANCHER (décision utilisateur explicite). L'envie peut atteindre zéro et l'agent
# s'y figer définitivement. C'est un RÉSULTAT du modèle, pas un bug : une variable qui ne
# peut pas atteindre zéro ne mesure pas la perte de foi. Certains runs mourront — c'est le
# jeu de la vie, et c'est mesurable (métrique `Envie_Vivre`).
ENVIE_NAISSANCE = 1.0              # le nourrisson tente TOUT : il n'a rien à perdre et
                                    # aucun modèle du monde pour évaluer un risque. Ce n'est
                                    # pas un réglage, c'est le maximum de l'échelle [0, 1].
ENVIE_PLAFOND = 1.0                # borne haute : l'envie ne s'emballe pas au-delà du
                                    # maximum. Une BORNE, pas un rapport de force.

# La LUCIDITÉ — ce qui érode l'envie. C'est la phrase « quand C2 sera assez fort ET
# l'expérience de C1 assez construite » : le produit de ce que C2 comprend du monde (le
# modèle JEPA, mesuré par son erreur) et de ce que C1 a construit (sa vigueur réelle).
#
# Rien n'est posé ici : la lucidité est le produit de deux grandeurs déjà mesurées à chaque
# tick. Un agent qui prédit mal le monde n'a aucune raison d'avoir peur — il ne VOIT pas le
# risque. Un agent qui prédit bien le voit, et c'est ce savoir qui le paralyse.
#
# C'est le mécanisme contre-intuitif que la formulation demande : LA COMPÉTENCE PRODUIT SA
# PROPRE PARALYSIE. L'envie de vivre est ce qui l'en empêche.
POIDS_LUCIDITE = 0.02              # DYNAMIQUE, pas seuil : à quelle vitesse (par nuit) la
                                    # lucidité peut éroder l'envie. À 0.02, une lucidité
                                    # pleine coûte 2 % d'envie par nuit — donc des dizaines
                                    # de nuits pour se figer, jamais un basculement.
POIDS_FOI = 0.03                   # ...et à quelle vitesse la foi la restaure. Légèrement
                                    # SUPÉRIEUR à la lucidité : un agent qui réussit doit
                                    # pouvoir remonter plus vite qu'il ne s'éteint, sinon
                                    # la mort est le seul état absorbant et la mécanique ne
                                    # dit plus rien. Aucun des deux n'est un seuil : ce sont
                                    # les deux pentes d'une composition multiplicative.

# --- v37.0 : L'ÉQUILIBRE C1 / C2 ---
#
# Diagnostic complet dans `docs/ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md`. En trois lignes : sur le
# cerveau V36 (600 jours), C1 et C2 n'étaient d'accord sur AUCUN tick (accord 0 %, sur les
# niveaux maîtrisés comme sur le niveau bloquant), chacun votant une action constante. Le
# ratio d'amplitude C2/C1 allait de 9,9× à 22,1× — non par supériorité de C2, mais parce
# que C2 était le seul des deux à sortir avec une échelle garantie (normalisation z-score).
#
# Les trois constantes ci-dessous sont des BORNES (doctrine du projet : les constantes
# bornent, les valeurs sont dérivées). Aucune ne fixe un rapport de force : la confiance de
# C2 et la vigueur de C1 restent mesurées à chaque tick.

# Mesure 1 (« l'échelle de C2 porte sa confiance ») : ESSAYÉE PUIS RETIRÉE. Ses deux
# constantes (PLAFOND_CONFIANCE_C2, INERTIE_ECHELLE_C2) ont donc disparu. Le détail des
# deux implémentations et des deux mesures qui les ont écartées est conservé dans
# `simuler_futur_et_planifier`, à l'endroit exact où le code aurait vécu.

# Mesure 2 — l'amplitude sous laquelle la voix de C1 est réputée ÉTOUFFÉE PAR L'ÉROSION
# plutôt que par l'indécision. Mesuré sur le cerveau V36 : amplitude C1 de 0,095 à 0,217,
# avec `tete_motrice` collée à 10,00 % de sa norme de naissance.
#
# Cette valeur n'est PAS posée à la main : elle est DÉRIVÉE de l'échelle de C2, seule
# grandeur de référence disponible. C2 sort d'une normalisation z-score, donc son écart-type
# vaut 1 par construction ; sur 7 actions, l'amplitude (max − min) d'une telle distribution
# vaut ~2,1 — vérifié empiriquement sur trois environnements (2,105 / 2,096 / 2,103).
# Pondérée par force_planification, la voix de C2 pèse donc ~2,1 × force.
#
# RATIO_C1C2_VISE fixe le rapport de force cible entre les deux voix. À 2,0, C2 reste le
# plus fort — c'est voulu : C2 doit continuer de faire émerger l'intelligence, pas être mis
# à égalité avec le réflexe. Mais il ne l'écrase plus d'un facteur 8 à 22, où C1 n'avait
# structurellement aucune chance d'être entendu, quelle que soit la qualité de son avis.
AMPLITUDE_C2_NORMALISEE = 2.1      # amplitude d'un z-score sur 7 actions (mesurée, borne)

# v40.0 — `RATIO_C1C2_VISE = 2.0` A DISPARU, et avec lui le dernier rapport de force posé.
#
# Il disait « C2 doit peser 2× C1 ». D'où venait ce 2 ? D'aucune mesure. Désormais la cible
# de vigueur de C1 est simplement l'amplitude que C2 pèse RÉELLEMENT ce tick-ci :
#
#     VIGUEUR_MIN_C1(f)  =  AMPLITUDE_C2_NORMALISEE × f_planif
#
# C'est la PARITÉ, et elle est le seul point de référence non arbitraire : « C1 doit être
# audible à la hauteur de ce que C2 pèse aujourd'hui ». Le rapport de force n'est plus
# décrété, il devient une CONSÉQUENCE de l'expérience — f petit (agent inexpérimenté) ⇒ C2
# pèse peu ⇒ C1 domine naturellement. C'est la formulation « C1 a toujours raison, sauf
# si… » exprimée en une ligne, sans aucun seuil.
def vigueur_min_c1(force_planification):
    """La cible vers laquelle l'amplitude de C1 est ramenée, dans les DEUX sens.

    On règle sa VOIX, jamais son OPINION : le gain reste un facteur purement scalaire,
    les rapports entre les 7 logits de C1 sont rigoureusement préservés (invariant v37.0).
    """
    return AMPLITUDE_C2_NORMALISEE * float(force_planification)
GAIN_C1_MIN = 0.25                 # bornes du gain. Sans la borne HAUTE, un C1 érodé à
GAIN_C1_MAX = 4.0                  # l'extrême serait amplifié sans limite et son bruit
                                    # deviendrait du signal ; sans la borne BASSE, un C1
                                    # devenu très fort (ce qui arrive dès que la distillation
                                    # le débloque — mesuré : ratio inversé à 0,21× en 30
                                    # jours) serait réduit au silence. Aucune des deux ne
                                    # fixe un rapport de force : elles empêchent seulement
                                    # l'un des deux modules de disparaître de l'arbitrage.

# v37.1 — LA DISTILLATION SÉLECTIVE (crédit rétrograde).
#
# La v37.0 distillait à l'aveugle : C1 imitait C2 à chaque tick, au même poids, que C2 ait
# eu raison ou tort — donc C1 apprenait aussi les erreurs de C2. On n'automatise pas tous
# ses gestes, on automatise ceux qui ont marché.
#
# Les trois constantes ci-dessous sont des DYNAMIQUES (à quelle vitesse un crédit s'efface,
# à quelle vitesse une référence monte, à quelle vitesse elle redescend), jamais des seuils
# de décision. Le niveau qui décide si un choc est « marquant » n'est écrit nulle part :
# c'est `reference_choc_dopamine`, dérivée de ce que l'agent a lui-même vécu, et qui évolue
# avec son âge et ses habitudes — même principe que la faim ou la soif.
DECROISSANCE_CREDIT_DISTILLATION = 0.92
                                    # décroissance du crédit à rebours du temps : le geste
                                    # juste avant la récompense compte plus que celui d'il y
                                    # a trente ticks. Même patron que `trace_activation`
                                    # (LTP v20.0). À 0.92, un tick garde ~44 % de crédit
                                    # 10 ticks avant le choc, ~8 % après 30 ticks.
INERTIE_REFERENCE_CHOC = 0.99      # inertie de `reference_choc_dopamine` À LA MONTÉE —
                                    # l'échelle à laquelle CET agent juge un choc fort ou
                                    # faible. Lente à dessein : elle suit la maturation (des
                                    # dizaines de jours), jamais l'humeur d'une journée.
                                    # C'est ce qui fait qu'un agent habitué aux victoires
                                    # cesse de trouver un micro-progrès marquant, alors
                                    # qu'un agent qui n'a rien connu de mieux le grave.
INERTIE_OUBLI_REFERENCE_CHOC = 0.9998
# --- v41.26 : THERMOHOMÉOSTASIE ---
# L'exposant de la gradation. 3 = la douleur croît comme le CUBE de l'excès thermique :
# le palier 2 reste quasi nul, le palier 4 domine tout. Ce n'est pas un réglage libre —
# c'est le plus petit entier qui produit les 4 paliers décrits, vérifié numériquement
# (n=2 laisse le palier 2 à 3,3 % d'un manque vital, n=4 écrase le palier 3).
EXPOSANT_GRADATION_DOULEUR = 3
# Dissipation de la brûlure accumulée, PAR TICK. La brûlure perd 15 % de sa charge à
# chaque tick passé hors du danger : un contact bref se dissipe en ~15 ticks, un séjour
# prolongé sature. C'est la seule constante de temps du mécanisme, du même ordre que les
# demi-vies déjà présentes (DEMI_VIE_OKAY, DEMI_VIE_DANGER).
DISSIPATION_BRULURE = 0.15
# Habituation thermique : même cliquet que la référence de choc (montée immédiate,
# descente ~50× plus lente). Un agent qui vit près du feu s'y habitue ; s'il s'en éloigne
# durablement, sa sensibilité revient — mais lentement, jamais en une journée.
INERTIE_OUBLI_HABITUATION = 0.998
# Montée de l'habituation, par tick. ~10× la descente : on s'habitue plus vite qu'on ne
# se déshabitue (forme de cliquet), mais sur des CENTAINES de ticks — jamais en un seul,
# sinon la brûlure s'éteindrait pendant que l'agent est encore dans le feu.
VITESSE_HABITUATION_MONTEE = 0.02
# Seuil de PERCEPTION nociceptive, en fraction de l'habituation courante. C'est le palier 1
# — « ça va, c'est chaud » — et c'est la seule façon d'obtenir un ZÉRO EXACT plutôt qu'un
# epsilon : sous ce niveau, le nocicepteur ne décharge pas du tout. Chez le vivant ce
# seuil existe littéralement (les nocicepteurs ont une intensité minimale d'activation) ;
# ici il est RELATIF au vécu de l'agent, donc jamais le même d'un agent à l'autre.
# v41.27 — vitesse à laquelle l'exposition suit la douleur vécue. Même ordre que les
# autres inerties du projet ; c'est la mémoire « ça fait mal depuis un moment ».
TAUX_EXPOSITION_DOULEUR = 0.05
# v41.27-fix1 — CAPACITÉ D'ÉVACUATION THERMIQUE du corps. En dessous, la chaleur est
# ressentie (les 2 dims de thermoception la rapportent toujours) mais **évacuée sans
# lésion** : c'est la différence entre « il fait chaud » et « je brûle ». Au-dessus, le
# surplus pénètre et lèse.
# ⚠️ Distincte du seuil de PERCEPTION (`SEUIL_NOCICEPTION_PLANCHER`, 0.12) : un corps
# perçoit la chaleur bien avant d'en souffrir. Les confondre revenait à faire brûler
# l'agent partout où il sentait quelque chose — le défaut de fond des v41.25 et v41.26.
CAPACITE_EVACUATION_THERMIQUE = 0.40
# Vitesse à laquelle le surplus thermique pénètre les tissus. Une brûlure ne s'installe
# pas en un tick : c'est ce qui laisse à l'agent le temps de FUIR avant la lésion.
PENETRATION_THERMIQUE = 0.05
FRACTION_SEUIL_NOCICEPTION = 0.25
# Plancher du seuil de perception, pour un agent qui n'a jamais rien senti (habituation 0).
# Correspond à la chaleur ressentie à ~3 cases d'une source sur une petite carte : au-delà,
# l'agent perçoit toujours la chaleur par ses 2 dims sensorielles, mais elle ne lui fait
# plus MAL. C'est la frontière entre percevoir et souffrir.
SEUIL_NOCICEPTION_PLANCHER = 0.12
                                    # v37.1-fix — inertie À LA DESCENTE, ~50× plus lente que
                                    # la montée. C'est un CLIQUET, et il n'est pas
                                    # décoratif : avec une inertie symétrique (le bug v37.1),
                                    # la référence suivait les micro-chocs vers le bas dès
                                    # que l'agent cessait de gagner — mesuré sur 600 jours,
                                    # 0,2149 → 0,0932 (−57 %) pendant que le crédit passait
                                    # de 10 % à 69 % (×7). L'agent devenait de plus en plus
                                    # FACILE à impressionner et C1 distillait 70 % de bruit.
                                    # Même défaut, même remède que `norme_naissance` en
                                    # v34.0-fix2 : une référence qui suit la décroissance ne
                                    # borne plus rien. La descente reste NON NULLE — un monde
                                    # durablement plus pauvre doit pouvoir recalibrer — mais
                                    # sur des centaines de nuits, pas sur une saison creuse.

TAUX_DISTILLATION_C1 = 0.05        # Mesure 3 — poids de l'auto-distillation C2 → C1 dans
                                    # la perte. C'est le SEUL canal par lequel la tête
                                    # motrice reçoit du gradient quand l'agent ne gagne
                                    # jamais (myéline mesurée : 0.000000 EXACT sur
                                    # tete_motrice et cortex_prefrontal du cerveau V36).
                                    # Mettre à 0.0 désactive entièrement la mesure 3 et
                                    # restaure le comportement v36 sur ce point.

# --- ÉTAPE 0.5 (v33.0) : TEST D'ABLATION INVERSÉE — quête auto en Mode Libre ---
# `DetecteurProgresPersonnel` (3b) est historiquement INACTIF sur DoorKey, pour une
# raison explicite : ces niveaux ont déjà leur guidage vers le But
# (`DetecteurJalonsDoorKey.RECOMPENSE_APPROCHE_BUT`), et faire tourner les deux
# créerait « un guidage qui ne s'éteint jamais complètement ».
#
# Or cette exclusion est devenue CADUQUE en Mode Libre : `recompense_continue` n'est
# ajoutée à `recompense_interne` QUE si `not etat.mode_libre` (voir traiter_tick). Dès
# le Palier 5, la béquille DoorKey est donc déjà coupée — il n'y a plus aucun double
# guidage à craindre, seulement un segment porte→but totalement dépourvu de signal.
#
# CE QUE LE RUN DE 700 JOURS A MESURÉ (run 50ac6kz0, cerveau neuf, v32) :
#   - arrivée au Palier 7 au jour 94, puis 607 jours à 0 % de réussite ;
#   - la SEULE victoire est le jour 94 lui-même, c.-à-d. le dernier jour où l'agent
#     travaillait encore sous guidage — après le décrochage, plus jamais ;
#   - 51,4 % de portage (l'agent PREND la clé) et 42 franchissements de porte sur 607
#     jours, pour ZÉRO sortie : Δt1 et Δt2 fonctionnent, Δt3 est un mur absolu ;
#   - 1,4 ressource consommée par jour seulement → l'hypothèse « il erre en cherchant à
#     manger » est INFIRMÉE par la mesure.
#
# Ce drapeau est donc un INSTRUMENT DE DIAGNOSTIC, pas une mécanique cognitive : il
# rétablit le gradient manquant sur le dernier segment pour établir la causalité. S'il
# débloque le Palier 7, la nature exacte du blocage est prouvée (rareté du signal) —
# et il doit ensuite être REMIS À False pour garder le défi intact, la vraie solution
# devant émerger de la mémoire (v33 : valence + replay orienté), jamais d'une béquille
# permanente. Voir docs/ameliorations/CONCEPTION_v33_memoire_emotionnelle.md §5.1.
#
# False = comportement strictement identique à la v32.0 (invariant de non-régression).
QUETE_AUTO_EN_MODE_LIBRE = False

# --- HORIZONS DE PLANIFICATION MULTI-ÉCHELLE (v15.0) ---
# Sauts exponentiels (t+1, t+3, t+7) plutôt qu'une chaîne pas-à-pas t+1→t+2→t+3 : le
# Système 2 évalue l'impact immédiat ET la tendance à moyen horizon, utile pour les
# couloirs longs de MultiRoom (Doctorat) où l'objectif n'est jamais visible à un seul
# pas de distance, sans calculer chaque micro-état intermédiaire un par un.
HORIZONS_PLANIFICATION = (1, 3, 7)
GAMMA_PLANIFICATION = 0.9

# --- PRESSION CINÉTIQUE MULTIMODALE (thermostat de stagnation, v16.0) ---
# La pénalité brute reste identique à la v15.0, mais elle est désormais ATTÉNUÉE selon
# le contexte multimodal du tick (voir ThermostatCinetiqueMultimodal) plutôt
# qu'appliquée uniformément partout.
# v41.43 — L'ÉCHELLE DE LA DOULEUR DE STAGNATION EST DÉRIVÉE DU MONDE (P3 de l'audit
# du génome, reformulé après mesure).
#
# 🔴 CE QUE LA MESURE A DIT, ET QUI A CORRIGÉ LA PROPOSITION INITIALE (30/08/2026).
# P3 supposait un DOUBLON avec le métabolisme basal (« l'inaction est facturée deux
# fois »). **C'est FAUX, et mesuré** : le basal facture le TEMPS (0,003250/tick, quoi
# qu'il arrive), la stagnation facture la REDONDANCE SPATIALE (revenir sur ses pas,
# en `1.5 ** occurrences`). Un agent qui avance en ligne droite paie le basal et
# **rien** en stagnation. Ce ne sont pas les mêmes grandeurs — supprimer la seconde
# aurait retiré le seul signal anti-piétinement du barème.
#
# 🔴 LE VRAI DÉFAUT EST L'ÉCHELLE, et il est sévère. `0.015` n'était relié à RIEN —
# ni à ce que vaut une victoire, ni au vécu de l'agent. Mesuré sur 40 cerveaux
# (800 ticks) : la stagnation cumulée vaut **14,44**, soit l'équivalent de
# **14,4 VICTOIRES effacées**, quand l'agent en obtient au mieux 2 ou 3. Neuf ticks
# de piétinement annulent une victoire entière.
#
# LA DÉRIVATION. Une victoire MiniGrid rapporte `1 − 0.9 × (pas/max_steps)`, donc au
# PIRE `0.1` (victoire à l'ultime tick). Le budget de douleur d'un épisode entièrement
# piétiné ne doit pas dépasser ce pire gain : sinon l'échec rapide devient préférable à
# l'exploration, et l'agent a RAISON de renoncer.
#
#     pénalité_unitaire = GAIN_MINIMAL_VICTOIRE / max_steps
#
# `max_steps` est une propriété DU MONDE, déjà lue par `_budget_natif_carte` (v41.30,
# même précédent que la patience) — ce n'est pas un réglage. L'écart avec la constante
# posée grandit avec la carte, ce qui explique que les grands niveaux soient invivables :
#
#     max_steps=100 -> 0,001000 (posé 15,0x trop cher)
#     max_steps=324 -> 0,000309 (posé 48,6x trop cher)
#     max_steps=640 -> 0,000156 (posé 96,0x trop cher)
#
# ⚠️ CE QUI RESTE UNE BORNE, ASSUMÉE : `GAIN_MINIMAL_VICTOIRE = 0.1` n'est pas posé —
# c'est la valeur plancher que MiniGrid lui-même attribue à une victoire (`1 − 0.9`).
# Le choix conservateur est de prendre ce PIRE cas plutôt que la victoire moyenne :
# une pénalité trop faible laisse l'agent piétiner, une pénalité trop forte le fait
# renoncer — et c'est le second défaut qui a été mesuré.
#
# ⚠️ NON MESURÉ EN COMPORTEMENT. Cette correction aligne le code sur le dogme et sur
# une échelle vérifiable ; elle n'est PAS une hypothèse sur le plafond, et rien ne dit
# qu'elle changera le niveau atteint. Dix-sept réfutations invitent à ne rien promettre.
# Le drapeau `--stagnation-fossile` conserve l'ancien comportement pour le témoin.
GAIN_MINIMAL_VICTOIRE = 0.1   # borne : ce que MiniGrid paie une victoire in extremis
                              # (`1 − 0.9`), lu dans la formule de l'environnement.
PENALITE_STAGNATION_FOSSILE = 0.015   # la valeur posée d'avant la v41.43 — conservée
                                      # comme TÉMOIN d'ablation, jamais sur le chemin.
STAGNATION_DERIVEE_ACTIVE = True      # --stagnation-fossile pour le bras témoin


def _penalite_stagnation_du_monde(env, defaut: float = PENALITE_STAGNATION_FOSSILE) -> float:
    """v41.43 — L'échelle de la pénalité, dérivée du budget que le MONDE accorde.

    Le coût d'un épisode entièrement piétiné est borné par ce qu'une victoire
    rapporte au pire. Hors MiniGrid (vocal isolé, rêve), on retombe sur la valeur
    historique : même lecture défensive que `_budget_natif_carte`.
    """
    if not STAGNATION_DERIVEE_ACTIVE:
        return defaut
    budget = _budget_natif_carte(env, defaut=0)
    if budget <= 0:
        return defaut
    return GAIN_MINIMAL_VICTOIRE / float(budget)


FACTEUR_ATTENUATION_MANIPULATION = 0.30  # objet en main (carrying) : arrêts légitimes
FACTEUR_ATTENUATION_INTERACTION = 0.05   # face à un objet clé + action de ciblage
FACTEUR_ATTENUATION_LIBRE = 1.00         # déplacement libre : pénalité pleine

# --- POTENTIOMÈTRE D'ACCEPTATION PAR ABNÉGATION (patience évolutive, v16.0) ---
# Remplace le plafond de ticks par épisode implicite (borné seulement par la fin de
# journée) par un seuil de troncature volontaire recalculé chaque jour à partir de
# l'historique de succès/vitesse, puis ÉTIRÉ par le facteur de complexité du sous-seuil
# courant — voir ModuleAcceptationAbnegation et GestionnaireCursusAbnegation.
# v41.30 — DEUX INTERRUPTEURS SÉPARÉS, un par constante supprimée.
#
# ⚠️ Ils DOIVENT rester distincts : patience et rythme métabolique sont COUPLÉS
# (`épisodes/jour` est l'entrée du besoin). Les couper ensemble produirait une ablation
# CONFONDUE — impossible de savoir laquelle des deux a agi. C'est la règle de mesure §4.
# v41.31 — TROIS INTERRUPTEURS, un par axe. ⚠️ Ils DOIVENT rester séparés : le gradient
# causal, le tube digestif et l'unification du détecteur sont trois mécaniques distinctes ;
# les couper ensemble produirait une ablation CONFONDUE (règle de mesure §4).
GRADIENT_CAUSAL_ACTIF = True        # False = `.mean()` d'avant v41.31 (`--gradient-non-filtre`)

# --- v41.48 : LE RENDEMENT MÉCANIQUE ASYMÉTRIQUE (brique C) ---------------------------
#
# 🔴 CE QUE ÇA CORRIGE (Étape 0 du 01/09/2026, `A_g66`, 40 ép., 10 851 ticks, instrument
# corrigé). Le masque binaire de la v41.31 laisse passer **44,5 %** de gestes stériles,
# parce que `transition_tick` compte la ROTATION comme une transition — à juste titre,
# c'est une acquisition d'information. Mais il ne distingue pas un pas qui déplace d'un
# `forward` qui s'écrase sur un mur : mesuré, **53,6 % des `AVANCER` se cognent** (2 184
# sur 4 078), et seuls **17,5 % des ticks** produisent un déplacement réel. Sur 324 ticks
# de budget, l'agent obtient ~57 ticks de mouvement pour un objectif à 12 cases.
#
# LE MÉCANISME. Le gradient de l'acteur est pondéré par le RENDEMENT du geste :
#
#     rendement = travail_utile / travail_engagé   ∈ [0, 1]
#
# où le numérateur est le travail qui a **effectivement déplacé quelque chose** et le
# dénominateur le travail **musculaire engagé**, tous deux déjà dérivés par
# `calculer_effort_metabolique` (v41.28) — aucune table, aucun coefficient posé. Un geste
# qui brasse du vent a un rendement nul ; pousser une porte qui s'ouvre, un rendement de 1.
#
# ⚠️ L'ASYMÉTRIE EST LE CŒUR DU MÉCANISME, et elle est une DÉCISION UTILISATEUR explicite
# (01/09/2026) :
#
#     ∇θ ← ∇θ × rendement   si A_t > 0      (un succès stérile n'ancre RIEN)
#     ∇θ ← ∇θ                si A_t ≤ 0      (un échec stérile reste PUNI)
#
# Sans l'asymétrie, un geste stérile aurait un gradient nul dans les DEUX sens : il
# deviendrait INVISIBLE à l'apprentissage au lieu d'être appris comme mauvais. C'est
# exactement le piège que `travail = 0.0` avait tendu en v41.27 côté COÛT — le geste
# inutile était devenu le moins cher du barème. Ici la faute symétrique serait de le
# rendre le moins instructif. **Le rendement module le BÉNÉFICE, jamais la PUNITION.**
#
# C'est le levier que `CLAUDE.md` désignait depuis la v41.28 : « si le gaspillage persiste
# après ce correctif, le levier suivant est le BÉNÉFICE (un geste qui ne change rien
# devrait n'apprendre rien), PAS un durcissement du coût. » Le gaspillage a persisté
# (57,2 % → 44,5 %), la condition est remplie.
#
# ⚠️ NE PAS CONFONDRE AVEC LE MASQUE v41.31. Le masque REJETTE un tick (0 ou 1) ; le
# rendement le PONDÈRE (continu dans [0,1]). Les deux sont composables et restent deux
# interrupteurs SÉPARÉS — les couper ensemble donnerait une ablation confondue.
RENDEMENT_MECANIQUE_ACTIF = True    # False = pas de pondération (`--sans-rendement`)
RENDEMENT_SYMETRIQUE_TEMOIN = False  # True = pondère AUSSI les avantages négatifs, donc
                                     # rend le geste stérile INVISIBLE au lieu de puni.
                                     # Témoin de falsification de l'asymétrie
                                     # (`--rendement-symetrique`).

# v41.32 — ABLATION « COLLISION C1/C2 » : le critique sabote-t-il l'intégrateur bio ?
#
# Mesuré le 25/08 (chemins de gradient, 3 pertes injectées séparément) : `integrateur_bio`
# est la SEULE couche où C1 (6,127) et C2 (4,907) rétropropagent tous les deux. Le tronc
# perceptif, lui, est coupé des deux têtes par le `.detach()` de la l. 1149 — la collision
# ne peut donc avoir lieu QUE là.
#
# Ce drapeau neutralise le gradient de C2 en gardant son FORWARD intact : `valeurs_tensor`
# est détaché avant la perte critique, donc `cortex_prefrontal` et `integrateur_bio` ne
# reçoivent plus rien de ce canal. C2 continue de produire ses valeurs, de peser dans
# l'arbitrage et de fournir les avantages — seule sa rétropropagation cesse.
#
# ⚠️ NEUTRALISER N'EST PAS DÉBRANCHER : le comportement du tick reste identique, seule
# l'ardoise du gradient change. C'est ce qui isole la COLLISION de l'UTILITÉ de C2 (dont
# l'ablation comportementale est déjà mesurée à 0,0 pt sur 6 niveaux, v41.29).
#
# ⚠️ Sans gradient, le critique cesse d'apprendre : ses estimations dérivent, donc les
# AVANTAGES qu'il fournit à l'acteur se dégradent. Ce bras mesure l'ALIGNEMENT du
# gradient, JAMAIS la performance — un score qui baisse ici ne prouve rien.
GRADIENT_C2_ACTIF = True

# v41.32 — LE `.detach()` ASYMÉTRIQUE : C2 LIT LE CORPS, IL NE LE SCULPTE PLUS.
#
# Mesuré le 26/08 : couper entièrement le gradient de C2 fait passer l'alignement de
# `tete_motrice` de 0,3428 à 0,6751 (+97 %) et son gradient de 0,1998 à 0,4739 (×2,4).
# La collision C1/C2 dans `integrateur_bio` — la SEULE couche partagée — était donc bien
# la source du thrashing.
#
# Mais couper le gradient de C2 empêche le critique d'apprendre : c'est un scalpel de
# diagnostic, pas un correctif. Le `.detach()` asymétrique est la forme soignée :
#
#   - C2 LIT `pensee_bio` pour évaluer et planifier — sa fonction est intacte ;
#   - mais il ne rétropropage plus DANS `integrateur_bio` ;
#   - `cortex_prefrontal` continue, lui, d'apprendre normalement.
#
# Seul C1 sculpte donc la représentation viscérale. C'est exactement la symétrie du
# `.detach()` déjà présent l. 1149, qui protège le tronc perceptif des deux têtes : ici on
# protège la représentation du corps de la seule tête qui n'a pas à la façonner.
#
# ⚠️ CE N'EST PAS ÉQUIVALENT À `--sans-gradient-c2` : là, C2 n'apprenait plus du tout et
# ses estimations dérivaient. Ici, il apprend toujours — il cesse seulement de déformer
# le sol de C1. Les deux bras doivent être mesurés séparément.
DETACH_C2_ASYMETRIQUE = False
# v41.31-controle — bras de falsification : gradient acteur ×N SANS filtrage. 1.0 = inactif.
# Le 2.6 n'est pas posé : c'est `T / Σm` mesuré (61,7 % de ticks stériles → 1/0,383 ≈ 2,6).
GAIN_ACTEUR_CONTROLE = 1.0
DEBIT_DIGESTIF_VECU_ACTIF = True    # False = débit figé à 3,0/jour (`--debit-fossile`)
UNIFIER_DETECTEUR_STERILITE = True  # False = `mur_touche` sur l'observation (`--detecteur-observation`)

ENDURANCE_DERIVEE_ACTIVE = True   # False = patience fossile (+10 plafonné, `--patience-fossile`)
RYTHME_VECU_ACTIF = True          # False = besoin figé à 4 épisodes/jour (`--rythme-fossile`)

# Le régime fossile exact d'avant v41.30, conservé pour que le témoin soit FIDÈLE et non
# approximatif : mêmes chiffres, même plafond, même gain constant.
PATIENCE_MAX_FOSSILE = 350
BOOST_PATIENCE_FOSSILE = 10
EPISODES_PAR_JOURNEE_FOSSILE = 4.0

PATIENCE_MIN = 50
# v41.30 — `PATIENCE_MAX = 350` SUPPRIMÉE. C'était une CONSTANTE FOSSILE : un chiffre posé
# qui décrivait l'agent d'août 2026, pas une propriété de l'espèce.
#
# 🔴 LA MESURE (campagne v41.29, 10 graines × 1500 jours) : **9 graines sur 10 finissent
# à `patience_min = 350` — le plafond EXACT** (la 10ᵉ à 330). Le mécanisme accordait un
# gain CONSTANT (+10 par victoire-sursaut) jusqu'au mur, puis RIEN : 30 victoires
# suffisaient à saturer, et 1200 jours de plus ne changeaient plus rien. C'est l'inverse
# d'une difficulté croissante.
#
# ⚠️ Le plafond n'a pas été remplacé par un autre chiffre : il est **dérivé du MONDE**.
# `_budget_natif_carte` lit `max_steps`, que MiniGrid impose de toute façon — au-delà,
# toute patience est inopérante puisque l'épisode est coupé. Les patiences relevées dans
# la campagne (100 · 144 · 256 · 324) sont exactement les `max_steps` des cartes jouées :
# le vrai plafond était déjà là, mesuré, et `PATIENCE_MAX` ne faisait que le doubler d'une
# borne arbitraire. `PLAFOND_PATIENCE_HORS_MONDE` ne sert plus qu'aux contextes SANS carte
# (vocal isolé, rêve), où `max_steps` n'existe pas.
# La journée elle-même est le seul plafond qui ait un sens hors carte : au-delà,
# l'épisode ne peut de toute façon pas continuer.
PLAFOND_PATIENCE_HORS_MONDE = ticks_par_jour
FENETRE_HISTORIQUE_PATIENCE = 20

# --- v41.8 : LA PATIENCE SE DÉRIVE DU BUDGET DE LA CARTE, ET SE MUSCLE PAR L'ÉCHEC ---
#
# Décision utilisateur : *« La patience n'est toujours pas une dérivée calculée comme le
# reste ! Il faut donc la travailler et la muscler dès le plus jeune âge pour qu'elle
# permette en avançant de réussir. »*
#
# 🔴 DEUX DÉFAUTS MESURÉS.
#
# (1) `PATIENCE_MIN/MAX` sont posés en dur et **sans rapport avec la carte**. MiniGrid
#     accorde un budget natif par environnement (`max_steps`) que le projet n'a **jamais
#     lu** — 0 occurrence de `max_steps` dans tout le code avant cette version :
#
#         Empty-5x5 : 100 ticks   ← le palier où 4 graines sur 6 sont bloquées
#         Empty-Random-6x6 : 144  ·  Empty-8x8 : 256  ·  SimpleCrossing : 324
#
#     La patience calculée valait 119 à 329 ticks : **toujours au-dessus du plafond de
#     `Empty-5x5`**. Elle n'avait donc aucun effet à ce niveau — c'est `max_steps` qui
#     coupait l'épisode. Les « 273 ticks, 0 abandon lucide » observés signifiaient « il
#     n'atteint jamais SA patience », et non « il a le temps qu'il faut ».
#
# (2) Elle était **à l'envers** : `potentiometre = 0.7 × taux_succes` faisait CROÎTRE la
#     patience avec la réussite. Un débutant qui échoue recevait 119 ticks, un expert qui
#     n'en a plus besoin 329. L'inverse exact de « muscler dès le plus jeune âge ».
#
# LA FORME. La patience est désormais une FRACTION du budget réel de la carte, et cette
# fraction décroît avec la maîtrise :
#
#     patience = max_steps × (PATIENCE_PLANCHER_BUDGET + marge × (1 − maîtrise))
#
#   maîtrise 0 %   → tout le budget : le débutant a droit à l'épisode entier
#   maîtrise 100 % → une fraction : l'expert n'a plus besoin d'errer, il tranche vite
#
# Le sevrage temporel suit ainsi la même doctrine que le sevrage de l'aide (v41.3) : on
# retire ce dont l'agent n'a plus besoin, à mesure qu'il n'en a plus besoin.
PATIENCE_PLANCHER_BUDGET = 0.45   # borne basse : un expert garde toujours ~45 % du budget
PATIENCE_MARGE_BUDGET = 0.55      # ce que l'échec restitue — plancher + marge = 1.0 budget
TAUX_FRICTION_DOUCE_ABANDON = 0.05  # friction dopaminergique appliquée sur abandon lucide,
                                     # plus douce qu'un choc négatif : l'agent accepte
                                     # l'échec, il ne le subit pas comme un traumatisme

# --- CURSUS À DEUX SOUS-SEUILS (Abnégation, v16.0, DoorKey uniquement) ---
# Remplace la validation de palier par taux de réussite journalier (SEUIL_MAITRISE_PALIER)
# par un compteur cumulatif de 4 succès (2 sous-seuils x 2), indépendant des frontières
# de journée — voir GestionnaireCursusAbnegation.
SUCCES_PAR_SOUS_SEUIL = 2
COEFF_ABNEGATION_SOUS_SEUIL_2 = 1.6

# --- VOLONTÉ ÉMERGENTE : CURIOSITÉ JEPA & SURSAUT (v17.0, Mode Libre uniquement) ---
FENETRE_HISTORIQUE_CURIOSITE = 50
FACTEUR_SEUIL_SURPRISE = 1.5     # erreur JEPA du tick devant dépasser 1.5x la moyenne récente
MICRO_RECOMPENSE_CURIOSITE = 0.04
POIDS_CHOC_CURIOSITE = 0.15

SEUIL_DECLENCHEMENT_SURSAUT = 0.95  # % de la patience du jour consommée avant sursaut
BOOST_SECOND_SOUFFLE = 0.5          # décharge dopaminergique ponctuelle liée à l'effort
EXTENSION_PATIENCE_SURSAUT = 50     # ticks supplémentaires accordés, plafonnés au budget
                                    # natif de la carte (`max_steps`), v41.30
# v41.30 — `BOOST_PATIENCE_MIN_PAR_RECURRENCE = 10` SUPPRIMÉE. Le gain de patience était un
# compteur d'événements (+10 par victoire-sursaut, quelle que soit sa difficulté) ; il est
# désormais DÉRIVÉ de l'écart mesuré entre la durée des réussites et celle des abandons,
# avec un rendement décroissant — voir `augmenter_patience_de_base_definitivement`.
#
# L'INERTIE DU TRAIT D'ENDURANCE. Décision utilisateur du 20/08/2026 : le lissage porte sur
# la VIE ENTIÈRE de l'agent, sans réinitialisation au changement de carte — c'est ce qui
# garantit la continuité ontogénétique (promu, l'agent garde son endurance acquise au lieu
# de s'effondrer). Une inertie proche de 1 fait glisser la référence lentement vers le
# récent : ni amnésie à chaque promotion, ni écrasement par les jours de la naissance.
#
# ⚠️ C'est une BORNE sur une VITESSE d'oubli, jamais une valeur de patience : elle survit à
# tout changement de carte, de durée de journée ou de barème. Même nature que
# `INERTIE_OUBLI_REFERENCE_CHOC` (v37.1-fix1).
INERTIE_TRAIT_ENDURANCE = 0.02   # borne : part du récent dans l'EMA (≈50 épisodes de mémoire)

# --- MOTEUR HOMÉOSTATIQUE BIOLOGIQUE (v18.0, générique, actif partout) ---
# v41.2 — L'ÉCHELLE TEMPORELLE. Les taux ci-dessous étaient calibrés sur une journée de
# 400 ticks, alors que le code lui-même définit ailleurs une journée comme
# TICKS_PAR_JOUR_BEBE = 3600 (« cycle nycthéméral complet »). Mesuré sur la campagne des
# 10 graines : l'agent passait 400 ticks sur 400 en zone critique, satiété et hydratation
# à 0.00, TOUS les jours. Ce n'était pas une difficulté mais une erreur d'échelle d'un
# facteur ~35 (il aurait fallu manger 104 fois par journée de 3600 ticks).
#
# Les taux sont désormais exprimés PAR JOURNÉE, pas par tick, et divisés par la longueur
# réelle de la journée. L'invariant préservé est le VÉCU BIOLOGIQUE (« 3 repas par
# journée »), jamais le nombre de ticks : un run de réglage à 400 ticks et un run cible à
# 3600 ticks doivent produire le même profil de jauges en POURCENTAGE de journée.
# C'est le test de non-régression à conserver.
TICKS_JOUR_REFERENCE = 3600.0   # borne : la journée nycthémérale de référence

# Proportions ancrées sur le vivant, pas choisies (voir CHANTIER_v41.2 §6) :
#   - 3 repas par journée  ⇒ un repas doit couvrir ~1/3 de journée
#   - l'eau tue ~10× plus vite que la faim (3 jours contre 30)
#   - le métabolisme BASAL représente ~60-70 % de la dépense totale
# v41.2-fix5 — LE RYTHME EST DÉRIVÉ DE LA CARTE LA PLUS PAUVRE, plus posé à la main.
#
# `REPAS_PAR_JOURNEE = 2.5` et `PRISES_HYDRIQUES = 4.0` étaient deux chiffres choisis puis
# recalibrés trois fois à la main — exactement ce que la règle « rien en dur » interdit.
#
# ⚠️ Le sens de la dérivation compte. Faire dépendre le besoin de la carte COURANTE serait
# un corps qui change de nature en changeant de pièce : sur `Empty-8x8` le calcul donnerait
# un besoin de 24 repas/jour. Le métabolisme est une propriété de l'ESPÈCE, pas du décor.
#
# C'est donc la carte la plus PAUVRE du cursus qui fixe le rythme — un organisme viable
# doit pouvoir subsister là où son monde offre le moins :
#
#   opportunités_min = budget(carte la plus pauvre) × épisodes_par_journée
#   besoin total     = opportunités_min / MARGE_SUBSISTANCE
#
# La marge sépare une pression d'une condamnation : mesurée à ×1,05, l'agent devait saisir
# CHAQUE occasion sans jamais en rater une. C'est une borne sur un RAPPORT, pas sur une
# quantité — elle survit donc à tout changement de carte, de densité ou de durée de journée.
MARGE_SUBSISTANCE = 2.0                  # borne : le monde doit offrir 2× le besoin
# v41.30 — `EPISODES_PAR_JOURNEE_REFERENCE = 4.0` SUPPRIMÉE : le rythme est désormais LU
# sur ce que l'agent a réellement vécu (`etat.episodes_jour`), lissé sur sa vie.
#
# 🔴 CE QUE VALAIT CE CHIFFRE. `4.0` = `400 ticks / patience ~95` — la patience d'un agent
# NEUF, quand `patience_min` valait encore 50. Il était juste **le jour où il a été écrit**
# (commit 0609beb, v41.2, 15/08/2026). Ce chantier-là a dérivé QUATRE grandeurs sur cinq,
# et la formule a hérité d'un chiffre posé au milieu : c'était le résidu du chantier.
#
# 🔴 LA MESURE (campagne v41.29, 10 graines × 1500 jours) :
#
#     patience réelle    168 → 258 ticks   (t = +9,55, SIG)
#     épisodes/jour     2,39 → 1,55        (−35 %)
#     écart au 4.0      ×1,68 → ×2,58      ← l'écart SE CREUSE
#
# La patience monte par cliquet, donc les épisodes/jour ne peuvent que DIMINUER : le besoin
# restait calibré pour 4 épisodes pendant que l'agent n'en jouait plus que 1,55. Corrélation
# qui relie le tout : `maîtrise ~ énergie moyenne`, r = +0,710 (t = +2,85, SIG).
#
# ⚠️ Ce n'est pas une constante fausse : c'est une constante qui mesure la JEUNESSE d'un
# agent et qu'on appliquait à sa VIEILLESSE.
#
# La valeur de naissance est PRUDENTE, jamais optimiste : un agent au jour 1 n'a rien vécu,
# on suppose donc le cas le moins favorable (un seul épisode par journée, soit le maximum de
# besoin par occasion). Même discipline que le plancher vital : on protège le cas défavorable
# plutôt que de parier sur le confortable.
EPISODES_PAR_JOURNEE_NAISSANCE = 1.0
RATIO_SOIF_SUR_FAIM = 10.0 / 30.0        # borne : 3 jours sans eau contre 30 sans
                                         # nourriture — l'eau se vide 10x plus vite
# Densité maximale de ressources, en fraction des cases libres. Définie ici parce que le
# rythme métabolique en dérive (voir _BUDGET_CARTE_MINIMALE plus bas) ; son rôle de garde-
# fou du monde est documenté au point d'usage, dans le détecteur de ressources.
FRACTION_CASES_RESSOURCES_MAX = 0.35     # borne : au-delà, la carte devient un garde-manger
                                         # infranchissable et l'agent n'a plus d'espace pour
                                         # apprendre à se déplacer. La densité est RELATIVE
                                         # à la carte, jamais absolue — même discipline que
                                         # DENSITE_MAX_PAR_CASE (v31.0) pour la mémoire.
CASES_LIBRES_CARTE_MINIMALE = 8.0        # borne : `Empty-5x5`, la plus petite du cursus.
                                         # Mesurée, pas supposée (voir §8 du chantier).
_BUDGET_CARTE_MINIMALE = max(2.0, CASES_LIBRES_CARTE_MINIMALE * FRACTION_CASES_RESSOURCES_MAX)


def besoin_par_axe(episodes_par_journee: float) -> float:
    """v41.30 — LE BESOIN MÉTABOLIQUE SUIT LE RYTHME RÉELLEMENT VÉCU.

    Le calcul est celui de la v41.2, à ceci près que le nombre d'épisodes n'est plus posé :

        opportunités_min = budget(carte la plus pauvre) × épisodes_par_journée
        besoin/axe       = (opportunités_min / 2) / MARGE_SUBSISTANCE

    ⚠️ Le SENS de la dérivation est inchangé et reste essentiel : c'est la carte la plus
    PAUVRE du cursus qui fixe le rythme, jamais la carte courante — un métabolisme qui
    changerait de nature en changeant de pièce ne serait pas une propriété de l'espèce
    (sur `Empty-8x8` le calcul donnerait 24 repas/jour).

    ⚠️ La marge doit tenir sur CHAQUE axe, pas sur leur somme : répartir le besoin total
    selon `RATIO_SOIF_SUR_FAIM` donnait une marge food ×2,86 et une marge eau ×0,95 —
    le défaut §8.6 reproduit par une FORMULE au lieu d'un chiffre. Chaque axe reçoit donc
    la moitié des opportunités, divisée par la marge.
    """
    if not RYTHME_VECU_ACTIF:
        # Témoin `--rythme-fossile` : le besoin figé de la v41.2, quel que soit le vécu.
        episodes = EPISODES_PAR_JOURNEE_FOSSILE
    else:
        episodes = max(EPISODES_PAR_JOURNEE_NAISSANCE, float(episodes_par_journee))
    return (_BUDGET_CARTE_MINIMALE * episodes / 2.0) / MARGE_SUBSISTANCE


_OPPORTUNITES_MIN_JOUR = _BUDGET_CARTE_MINIMALE * EPISODES_PAR_JOURNEE_NAISSANCE
_BESOIN_TOTAL_JOUR = _OPPORTUNITES_MIN_JOUR / MARGE_SUBSISTANCE

# ⚠️ La marge doit tenir sur CHAQUE axe, pas sur leur somme. La carte offre autant d'eau
# que de nourriture (la densité suit la même fraction de cases) : répartir le besoin total
# selon un ratio biologique donnerait un axe confortable et l'autre en dessous de la marge.
# Mesuré sur une première tentative répartissant par RATIO_SOIF_SUR_FAIM : marge food ×2,86
# mais marge eau ×0,95 — soit exactement le défaut du §8.6 reproduit par une formule au lieu
# d'un chiffre posé. Une dérivation n'est pas une garantie de justesse.
#
# Chaque axe reçoit donc la moitié des opportunités minimales, divisée par la marge. On boit
# toujours plus souvent qu'on ne mange (la valeur hydrique d'une prise est plus petite, voir
# `valeur_hydrique`), mais le NOMBRE de prises reste soutenable des deux côtés.
# ⚠️ Ces trois noms sont désormais des VALEURS DE NAISSANCE, plus des constantes de régime :
# ils décrivent l'agent au jour 1, qui n'a encore rien vécu. Le rythme réel est recalculé
# chaque nuit par `besoin_par_axe(rythme vécu)` — voir `_rafraichir_rythme_metabolique`.
_BESOIN_PAR_AXE = besoin_par_axe(EPISODES_PAR_JOURNEE_NAISSANCE)
PRISES_HYDRIQUES_PAR_JOURNEE = _BESOIN_PAR_AXE
REPAS_PAR_JOURNEE = _BESOIN_PAR_AXE

# Historique de ces deux nombres, conservé parce qu'il porte la leçon du chantier :
# `REPAS = 2.5` et `PRISES = 4.0` ont été posés puis recalibrés à la main TROIS fois
# (§7.3, §7.5, §8.6), chaque fois sans confronter le barème à ce que la carte peut
# physiquement offrir. À `PRISES = 4.0`, `Empty-5x5` n'offrait que 4,2 prises/jour : une
# marge de ×1,05, où l'agent devait saisir CHAQUE occasion sans jamais en rater une.
# Un besoin que le monde ne satisfait que dans le cas parfait n'est pas une pression,
# c'est une condamnation — et c'est ce que la marge dérivée empêche désormais.

FRACTION_JOURNEE_PAR_REPAS = 1.0 / REPAS_PAR_JOURNEE   # autonomie d'un estomac plein

# Taux exprimés PAR JOURNÉE (divisés par ticks_par_jour au moment de l'usage).
TAUX_SATIETE_JOUR = 1.0 / FRACTION_JOURNEE_PAR_REPAS   # 1 estomac plein = 1/3 de journée
TAUX_HYDRATATION_JOUR = TAUX_SATIETE_JOUR * RATIO_SOIF_SUR_FAIM
TAUX_STIMULATION_JOUR = 4.0    # la stimulation se vide vite, mais se recharge par la nouveauté

# ⚠️ Conservés pour compatibilité de signature/résurrection : les anciens taux PAR TICK.
# Ils ne sont plus la source de vérité dès que `ticks_par_jour` est connu.
TAUX_SATIETE = 0.008
TAUX_HYDRATATION = 0.005
TAUX_STIMULATION = 0.012
SEUIL_CRITIQUE_BIO = 0.35

# --- v41.2 — LE MÉTABOLISME À DEUX ÉTAGES & L'ÉNERGIE MODULATRICE ---
# La satiété est un STOCK (le réservoir digestif), l'énergie est le FLUX réellement
# dépensé pour agir. Se reposer réduit la dépense mais NE CRÉE PAS DE MATIÈRE : si la
# satiété est vide, la réserve mobilisable est nulle, l'énergie continue de descendre et
# l'agent meurt. C'est une condition de SOLVABILITÉ, pas un `if` — il n'existe nulle part
# de règle « si repos et faim alors mourir ».
METABOLISME_BASAL_PART = 0.65   # borne : part incompressible de la dépense (~65 % dans le
                                 # vivant). Avant v41.2 le basal valait 12 % (`done`=0.1
                                 # contre `pickup`=0.8), ce qui punissait massivement le
                                 # mouvement — cohérent avec les 5,5 % de `forward` mesurés.
DEPENSE_ENERGIE_JOUR = 2.0       # borne : une journée pleine d'activité consomme 2 réserves.
                                 # CALIBRÉ PAR MESURE, pas choisi (méthode v30.1) : balayage
                                 # 1.0→3.0 à 3 repas/jour. À 1.0 l'énergie sature à 1.000
                                 # (écart-type 0.000 : variable morte, fil n°2 du projet) ;
                                 # à 3.0 l'agent est en zone critique 37 % du temps même en
                                 # mangeant correctement. À 2.0 : jamais critique avec
                                 # 3 repas (E_min 0.458, écart-type 0.163 — donc la vigueur
                                 # module réellement), 11 % de critique à 2 repas, et la
                                 # MORT PAR FAMINE au tick 367 si l'agent ne mange pas.
                                 # Le régime récompense l'alimentation et punit la
                                 # négligence, sans jamais rendre la mort inévitable.
MARGE_DIGESTIVE = 1.5            # borne : le débit digestif dépasse la dépense de 50 %.
                                 # DÉRIVÉ de la dépense, jamais posé indépendamment — si
                                 # le débit était fixé à part, il pourrait passer sous la
                                 # dépense et rendre la mort certaine par construction,
                                 # auquel cas la mécanique ne mesurerait plus rien.
DEBIT_DIGESTIF_JOUR = DEPENSE_ENERGIE_JOUR * MARGE_DIGESTIVE
RENDEMENT_CONVERSION = 0.9       # borne : satiété → énergie (jamais 100 %)
# --- v41.2 : LE PROFIL NUTRITIONNEL À TROIS AXES ---
# Une ressource n'est plus un type opaque qui remplit « sa » jauge : c'est un profil de
# TROIS grandeurs indépendantes, plus le coût de sa propre digestion. C'est ce qui rend
# possible un aliment qui hydrate un peu mais coûte presque autant à digérer qu'il ne
# rapporte, et une eau qui hydrate à 100 % sans apporter la moindre calorie.
#
#   satiete   : ce que ça remplit dans l'estomac (le STOCK)
#   hydrique  : ce que ça apporte en eau
#   energie   : la valeur énergétique BRUTE du stock apporté
#   digestion : ce que digérer cette ressource COÛTE, en fraction de son propre apport
#               énergétique. Une valeur proche de 1,0 = aliment quasi nul en net.
#
# ⚠️ Rien ici n'est « expliqué » au cerveau : il n'existe aucune table `pomme = bon`.
# L'agent ne perçoit que les conséquences sur ses jauges, et la valence de chaque type est
# APPRISE par `empreinte_types` (v39.0). Ce tableau décrit le MONDE, pas la connaissance
# qu'en a l'agent — même discipline que `DetecteurRessourcesBiologiques`.
# v41.30-fix2 — LA CONTENANCE ET LA PART D'UNE PRISE.
#
# `CONTENANCE_JAUGE` n'est pas un réglage : c'est l'amplitude que le code borne déjà partout
# (`np.clip(..., 0.0, 1.0)` sur satiété, hydratation et stimulation). Elle est écrite ici pour
# que la portion s'y réfère explicitement au lieu de la supposer.
CONTENANCE_JAUGE = 1.0
# La part d'estomac que remplit UNE prise. Borne, jamais valeur de régime : elle dit qu'un
# repas doit remplir l'essentiel d'un estomac vide SANS déborder — au-delà de 1,0 l'excédent
# est perdu tandis que la digestion reste facturée en entier (la « taxe sur le vide », mesurée
# à ×4 le coût pour 68 % du repas jeté). En-deçà, l'agent ne pourrait jamais se rassasier en
# une prise. Le nombre de prises nécessaires, lui, reste dérivé du besoin métabolique.
PART_ESTOMAC_PAR_PRISE = 0.80

PROFILS_NUTRITIONNELS = {
    # L'eau : hydrate totalement, zéro calorie, digestion gratuite.
    "WATER": {"satiete": 0.0, "hydrique": 1.0, "energie": 0.0, "digestion": 0.0},
    # Un fruit : peu d'eau, un apport énergétique réel mais coûteux à digérer.
    "FOOD":  {"satiete": 1.0, "hydrique": 0.03, "energie": 1.0, "digestion": 0.15},
    "STIM":  {"satiete": 0.0, "hydrique": 0.0, "energie": 0.0, "digestion": 0.0},
}

COFACTEUR_HYDRIQUE_MIN = 0.6     # borne : une soif TOTALE laisse encore 60 % du débit
                                 # digestif. Sans ce plancher, le bilan énergétique passe
                                 # négatif sous 50 % d'hydratation quoi que l'agent mange
                                 # (mesuré : énergie effondrée à 0,005 au 3ᵉ jour d'un run
                                 # réel). La soif doit RALENTIR la digestion, jamais
                                 # l'annuler — sinon la mort devient inévitable avant même
                                 # que la jauge d'eau n'atteigne zéro.
RECUPERATION_SOMMEIL = 0.5       # borne : fraction d'énergie rendue par une nuit complète

ENERGIE_MIN, ENERGIE_MAX = 0.0, 1.0

# --- v41.2-fix8 : LA RÉSERVE (la graisse) ---
# Le surplus d'énergie n'est plus perdu au plafond : il est stocké, et remobilisé quand
# l'énergie manque. C'est ce qui permet à un jour faste de préparer un jour maigre, et qui
# fait qu'on ne réagit pas tous pareil au même monde — deux agents qui mangent autant mais
# à des rythmes différents n'ont pas la même réserve.
#
# Les DEUX rendements sont < 1 : stocker coûte, déstocker coûte. C'est ce qui rend la
# réserve utile sans la rendre gratuite — mieux vaut manger à sa faim que faire des
# réserves, mais jeûner un jour ne tue plus.
RESERVE_MAX = 3.0                 # borne : ~3 journées de dépense (DEPENSE_ENERGIE_JOUR),
                                  # ordre de grandeur du jeûne court chez le vivant
RENDEMENT_STOCKAGE = 0.8          # borne : constituer une réserve perd 20 %
RENDEMENT_MOBILISATION = 0.9      # borne : la brûler perd 10 % — déstocker est moins
                                  # coûteux que stocker, comme dans le vivant
FRACTION_RESERVE_MOBILISABLE_JOUR = 0.5  # borne : on ne brûle pas sa graisse d'un coup ;
                                         # au plus la moitié de la réserve par journée

# LE SEUIL NON LINÉAIRE (décision utilisateur du 15/08) : l'énergie module TOUT — C1, C2,
# le déficit, la plasticité — via une seule grandeur dérivée, `vigueur = énergie ** κ`.
# Ce n'est PAS un seuil : il n'existe aucun `if énergie < X`. C'est une puissance, donc
# une chute continue mais ACCÉLÉRANTE. À κ=2 : énergie 0.5 → vigueur 0.25.
# Conséquence voulue : C2 (qui subit la vigueur en plus de sa force) s'éteint AVANT C1 —
# un organisme épuisé cesse de simuler l'avenir bien avant de cesser de marcher.
KAPPA_VIGUEUR = 2.0              # norme d'espèce ; dérivable (voir DERIVE_* ci-dessous)
KAPPA_VIGUEUR_MIN, KAPPA_VIGUEUR_MAX = 1.0, 4.0
VIGUEUR_PLANCHER = 0.15          # ⚠️ INDISPENSABLE : sans lui, vigueur→0 annule C1 ET C2,
                                 # donc logits tous nuls, donc action ALÉATOIRE. Un agent
                                 # mourant doit rester COHÉRENT, jamais aléatoire. Même
                                 # raisonnement que PLANCHER_POIDS_VITAL (v34.0-fix1).

# LES BORNES NE SONT PAS DES LIMITES (formulation utilisateur) : un métabolisme peut
# s'optimiser et déplacer sa propre norme, mais s'en écarter coûte EXPONENTIELLEMENT cher.
#   paramètre_effectif = norme * exp(dérive)
#   Δdérive = pression * plasticité − raideur * dérive * exp(|dérive| / élasticité)
# Près de la norme le rappel est négligeable (adaptation facile) ; loin, il explose en
# exp (mur asymptotique). La borne est une PENTE QUI DEVIENT VERTICALE, pas une barrière.
PLASTICITE_DERIVE_METABOLIQUE = 0.02   # borne : vitesse d'adaptation par nuit
RAIDEUR_RAPPEL_DERIVE = 0.05           # borne : force du rappel élastique vers la norme
ELASTICITE_DERIVE = 0.35               # borne : échelle au-delà de laquelle le mur monte
DERIVE_MAX_ABSOLUE = 1.0               # borne dure de sécurité (exp(1) ≈ 2,7× la norme)
# v41.2 — LA DENSITÉ DE RESSOURCES EST DÉRIVÉE DU BESOIN, plus posée à 2.
#
# Mesuré sur 71 jours d'un cerveau neuf : l'agent trouvait 1,92 nourriture/jour pour un
# besoin de 2,5, et ce taux n'augmentait PAS avec l'apprentissage — l'énergie descendait
# (0,172 → 0,079). Avec seulement 2 sources par carte, il aurait fallu qu'il les trouve
# TOUTES, à CHAQUE épisode, sans jamais échouer. Le déficit était structurel, pas
# comportemental : aucune politique n'aurait pu le combler.
#
# ⚠️ Le correctif porte sur le MONDE (la trouvabilité), jamais sur le barème métabolique.
# Baisser `REPAS_PAR_JOURNEE` jusqu'à ce que l'agent s'en sorte aurait rendu la mécanique
# « verte » en supprimant la pression même qui doit le pousser à chercher sa nourriture —
# on aurait mesuré un agent confortable qui n'a rien appris. C'est le seul levier qui ait
# jamais fonctionné sur ce projet (fil n°1 : « ce qui rend possible fait progresser »).
#
# La marge couvre l'échec de recherche : trouver la moitié des sources d'une carte doit
# suffire à survivre, tout en laissant l'agent qui cherche mieux vivre mieux.
MARGE_TROUVABILITE = 2.0

# 🔴 v41.30-fix1 — LA DENSITÉ EST UNE PROPRIÉTÉ DU BIOTOPE, PAS DU MÉTABOLISME.
#
# Jusqu'ici `NB_SOURCES_* = besoin × marge`, donc la richesse du monde suivait l'appétit de
# l'agent. Tant que le besoin était une constante (2,80), le couplage était invisible. La
# v41.30 l'a rendu vivant — et destructeur : le besoin de naissance tombant à 0,70, la carte
# ne recevait plus que **2 sources au lieu de 6** dès l'import.
#
# Mesuré (3 graines × 10 jours) : énergie **0,1968 contre 0,2651** au témoin fossile.
# La cause est la FALAISE DE RENCONTRE — en début de vie la politique est quasi aléatoire,
# donc la survie dépend de la densité spatiale (N_sources / surface), pas de la valeur
# nutritive. Quadrupler la valeur d'une ressource (0,794 → 3,175) ne compense rien si l'agent
# a mathématiquement moins de chances de poser le pied dessus.
#
# La densité est donc dérivée de la SURFACE de la carte la plus pauvre du cursus — la même
# grandeur qui plafonne déjà le placement dans le détecteur (`FRACTION_CASES_RESSOURCES_MAX`).
# Le monde est ainsi cohérent avec lui-même : ce qu'il SOUHAITE placer est exactement ce
# qu'il PEUT placer, réparti entre les deux axes.
#
# ⚠️ Ne JAMAIS réindexer ces deux nombres sur `besoin_par_axe` : le monde n'a pas à faire
# disparaître des ressources de la grille sous prétexte que l'agent prend son temps pour
# réfléchir. Le rythme vécu ne règle que la PHYSIOLOGIE (`valeur_alimentaire`,
# `valeur_hydrique`), jamais l'ÉCOSYSTÈME.
# Le souhait est SATURANT : le détecteur plafonne déjà le placement à
# `cases_libres × FRACTION_CASES_RESSOURCES_MAX` (v41.2-fix3), donc demander au moins ce
# plafond fait que **la SURFACE seule** fixe la densité, sur chaque carte du cursus. Mesuré :
# Empty-5x5 → 2 · Empty-Random-6x6 → 4 · Empty-8x8 → 11 · SimpleCrossingS9N1 → 14, soit une
# densité par case constante (~0,29) d'un palier à l'autre. La carte la plus RICHE du cursus
# borne le souhait — au-delà, le chiffre serait inopérant sur toutes les cartes.
_CASES_LIBRES_CARTE_MAXIMALE = 41.0       # borne : `SimpleCrossingS9N1`, la plus vaste
                                          # du cursus atteint à ce jour. Mesurée, pas supposée.
_SOURCES_BIOTOPE = max(4, int(round(_CASES_LIBRES_CARTE_MAXIMALE * FRACTION_CASES_RESSOURCES_MAX)))
# Répartition à parts égales : la carte offre autant d'eau que de nourriture (la densité suit
# la même fraction de cases), et la marge doit tenir sur CHAQUE axe — répartir selon un ratio
# biologique donnerait un axe confortable et l'autre sous la marge (défaut §8.6, v41.2).
NB_SOURCES_FOOD = max(2, _SOURCES_BIOTOPE - _SOURCES_BIOTOPE // 2)
NB_SOURCES_WATER = max(2, _SOURCES_BIOTOPE // 2)

# ⚠️ v41.2-fix3 — CES NOMBRES SONT DES SOUHAITS, PAS DES GARANTIES : ils sont plafonnés
# par la place réellement disponible sur la carte (voir `_budget_ressources`). Mesuré sur
# `Empty-5x5` : l'intérieur ne compte que **8 cases libres**, alors que 5 food + 8 eau = 13
# étaient demandées. Le monde en plaçait 7 et il ne restait **1 case libre** — l'agent était
# quasi emmuré, et la récolte plafonnait à ~3,5/jour QUELLE QUE SOIT la densité demandée
# (mesuré identique sur 3 runs : 3,72 / 3,52 / 3,47). C'est ce qui rendait inopérants les
# trois calibrages successifs : ils réglaient un paramètre déjà saturé.
POIDS_CHOC_RESSOURCE_BIO = 0.25  # ancrage mémoriel à la consommation d'une ressource
# COUT_ACTION_METABOLIQUE (constante fixe v18.0) supprimé en v19.0 : le coût énergétique
# est désormais calculé dynamiquement par moteur_bio.calculer_effort_metabolique() à
# partir du ratio 20% Cerveau / 80% Corps — voir BiologicalHomeostasisEngine.

MICRO_RECOMPENSE_VOCALE = 0.05  # v22.0 — même ordre de grandeur que MICRO_RECOMPENSE_CURIOSITE,
                                  # récompense continue par tick quand une leçon vocale est active
                                  # (voir hemisphere_audio.recompense_formants)
COEFF_PERTE_VOCALE = 1.0  # v22.1 — poids de la perte MSE vocale supervisée dans perte_totale
                            # (apprendre_journee). Même ordre de grandeur que les pertes JEPA/
                            # acteur/critique existantes (non additionnées avec un facteur
                            # d'échelle disproportionné) — à recalibrer empiriquement sur les
                            # premières leçons si la bouche apprend trop vite/trop lentement.

# --- DOPAMINE UNIFIÉE MULTIMODALE (v27.0) --- voir traiter_tick pour la formule et sa
# justification complète (agrégation probabiliste "OU doux" entre canaux visuels et
# canal vocal, remplaçant le max() pré-v27.0).
POIDS_DOPAMINE_VISUEL = 1.0   # la vue garde son plein poids historique — c'est la
                               # modalité mature (500+ jours de physique MiniGrid déjà
                               # appris), la toucher rejouerait le risque
                               # "empoisonnement du JEPA" traité en v22.1 sur un autre canal.
POIDS_DOPAMINE_VOCAL = 0.7    # l'ouïe/la parole contribue fortement mais pas à parité :
                               # le score vocal est CONTINU et non nul presque à chaque
                               # tick d'une leçon (recompense_formants renvoie ~0.1-0.4 en
                               # régime normal), là où les canaux visuels sont ÉVÉNEMENTIELS
                               # (une porte franchie, une ressource mangée). À poids égal,
                               # le canal vocal saturerait le réservoir en permanence par
                               # simple fréquence d'occurrence, écrasant la valeur
                               # informative des événements visuels rares — l'inverse exact
                               # de l'unification recherchée. 0.7 est un point de départ à
                               # recalibrer en observant Dopamine_Poids_Visuel_Moyen /
                               # Dopamine_Poids_Vocal_Moyen sur W&B (voir executer_nuit).

# v27.5 (correctif utilisateur, "boucle infinie de promotion vocale") : voir
# facteur_nouveaute_vocale — décroissance linéaire du poids dopaminergique/LTP/
# micro-récompense vocale avec la progression dans le curriculum (paliers 1→19), pour
# qu'un mot déjà maîtrisé cesse de shooter la dopamine au même niveau qu'un mot neuf.
FACTEUR_NOUVEAUTE_VOCALE_MIN = 0.1  # au dernier palier : 10% de l'effet dopaminergique/LTP
                                     # d'origine — jamais 0.0, un agent au sommet du
                                     # curriculum vocal continue de mériter UN minimum de
                                     # reconnaissance pour une bonne prononciation
                                     # (cohérent avec TAUX_FRICTION > 0 partout ailleurs :
                                     # rien dans ce moteur ne tombe jamais à un plancher
                                     # dur exactement nul).

# ⚠️⚠️ C3 EST MORT AU RUNTIME (constat du 20/08/2026, décision utilisateur) ⚠️⚠️
#
# Vérifié par la mesure, pas par lecture : **aucun plug n'est jamais enregistré** sur
# `port_c3` dans tout le noyau, donc `ACTION_DEMANDER` est masquée à `-inf` EN PERMANENCE
# (voir `penser()`), et l'action 7 n'apparaît dans AUCUN log de run — 0 occurrence sur les
# campagnes de 20 graines. `COUT_REQUETE_C3` n'est donc jamais prélevé, et l'Exo-Sens
# renvoie un vecteur nul à chaque tick.
#
# 🔴 POURQUOI CE CODE N'EST PAS SUPPRIMÉ NI COMMENTÉ. `DIM_EXO = 8` entre dans
# `DIM_VECTEUR_BIO` (= 41), donc dans la FORME des poids de `integrateur_bio`, et
# `num_actions = 8` dans celle de `tete_motrice`. Les retirer changerait la géométrie du
# réseau et **rendrait illisible tout `.brain` existant** — exactement ce que la règle
# « greffe par recopie, jamais par exclusion » interdit (bug v24.0-fix4).
#
# Le coût réel est donc : 8 dimensions d'entrée nulles et une colonne de sortie dormante.
# Aucun cycle CPU sur le chemin de décision, aucun effet sur le comportement.
#
# ➡️ À traiter dans un chantier dédié (retrait propre + greffe de rétrocompatibilité), pas
#    au détour d'un correctif. Tant que ce n'est pas fait, ne PAS s'appuyer sur C3 et ne
#    pas le compter comme une fonctionnalité du système.
#
# --- PORT EXOCORTEX C3 (v28.0, expérimental) --- voir naulthene.exocortex.port_c3 et
# la section 2 (AGI_Naulthene) pour la cascade complète. Aucune de ces constantes n'a
# d'effet tant qu'aucun plug n'est enregistré sur port_c3 (comportement identique à la
# v27.6 par défaut).
ACTION_ENV_NEUTRE_C3 = 6      # action MiniGrid "done" (Actions.done) — substituée à
                               # env.step() quand ACTION_DEMANDER est jouée : la seule
                               # action réellement neutre du jeu (agent immobile, déjà
                               # documentée comme telle dans docs/fonctionnement/CHANGELOG.md v27.4),
                               # jamais une action inventée.
COUT_REQUETE_C3 = 0.01        # pénalité en recompense_interne à chaque ACTION_DEMANDER —
                               # même ordre de grandeur que PENALITE_STAGNATION_FOSSILE.
                               # Sans coût, REINFORCE apprendrait à spammer le bus
                               # (l'action ne coûterait jamais rien à essayer) ; ce coût
                               # est ce qui rend "demander" un choix réellement économique,
                               # donc appris plutôt que gratuit.
POIDS_DOPAMINE_C3 = 0.5       # 3ème canal du "OU doux" (voir traiter_tick) — plus faible
                               # que POIDS_DOPAMINE_VOCAL (0.7) : un conseil C3 accepté est
                               # rare par construction (coût + masquage), mais un canal
                               # externe ne doit jamais peser plus que les modalités
                               # propres à l'agent (vue, ouïe) déjà éprouvées sur des
                               # centaines de jours.
SEUIL_OVERRIDE_C3 = 0.85      # confiance à partir de laquelle une ReponseC3 IMPOSE
                               # l'action plutôt que de biaiser les logits (voir
                               # traiter_tick, reponse_c3_en_attente) — volontairement
                               # élevé : l'override rend le gradient REINFORCE off-policy
                               # sur ce tick, à réserver aux avis les plus fiables.
FORCE_C3 = 0.5                # poids du biais logits += FORCE_C3 * preferences quand
                               # confiance < SEUIL_OVERRIDE_C3 — même ordre de grandeur
                               # que FORCE_PLANIFICATION_GUIDE (0.5), le poids du Système 2
                               # en mode guidé.

# --- L'EXO-SENS (v30.0) — le 6ème sens, perception continue du monde numérique ---
# Période de rafraîchissement de la perception exogène, en ticks. Un plug HTTP coûte de
# 100 ms à 30 s par appel (voir professeur_gemma, qui n'a ni health-check ni cache et
# fait payer son timeout complet à chaque appel) : l'interroger à CHAQUE tick rendrait
# impraticable un run de 400 ticks/jour × 300 jours. Entre deux rafraîchissements, la
# dernière perception reçue est réutilisée telle quelle (cache dans
# etat.perception_exogene_cache).
#
# 20 ticks est du même ordre que PERIODE_EVAL_SPECTRALE (10) pour le canal spectral
# vocal, qui résout exactement le même problème (un canal coûteux échantillonné moins
# souvent que le tick). Biologiquement cohérent : un sens a sa propre fréquence
# d'échantillonnage, il ne rafraîchit pas à l'infini.
PERIODE_PERCEPTION_EXO = 20

# v22.1 (correctif défaut 3, "empoisonnement du JEPA") : coeff_jepa_audio monte
# progressivement de 0.0 à COEFF_JEPA_AUDIO_MAX sur RAMPE_JEPA_AUDIO ticks audio reçus
# (etat.ticks_audio_recus) — protège les 481 jours de physique MiniGrid déjà appris
# en ne laissant jamais le signal audio, bruyant au démarrage, perturber le JEPA
# visuel dès le premier tick d'une leçon.
COEFF_JEPA_AUDIO_MAX = 0.3   # plafond, volontairement < 1.0 (poids de la perte vision) —
                              # l'audio reste toujours secondaire au JEPA visuel
RAMPE_JEPA_AUDIO = 2000       # ticks audio cumulés avant d'atteindre le plafond (~2 leçons
                              # de 1000 ticks, ordre de grandeur d'un run de test raisonnable)

# --- MÉMOIRE ÉPISODIQUE SPATIO-TEMPORELLE (v20.0, générique, actif partout) ---
CAPACITE_MEMOIRE_EPISODIQUE = 200
FENETRE_FRAICHEUR_SOUVENIR = 2000  # ticks absolus après lesquels un souvenir est jugé "périmé"

# --- RÊVE À POURCENTAGE ADAPTATIF (remplace le batch_size=64 fixe) ---
# Principe : pas de vrai plafond dur imposé de l'extérieur. Le plafond ÉMERGE de la
# composition de deux facteurs eux-mêmes bornés : la plasticité du moment (déjà
# comprise entre 0 et 1) et la "richesse" de la journée (combien d'évènements
# importants s'y sont produits, elle aussi normalisée). Une nuit "aphasique" après une
# journée creuse replaiera ~0.01% de la journée ; une nuit très plastique après une
# journée pleine de réussites peut monter jusqu'à PLAGE_REVE_MAX — mais jamais au-delà,
# et jamais par une simple clause "if > X: X" arbitraire.
POURCENTAGE_REVE_MIN = 0.0001       # 0.01 %
PLAGE_REVE_MAX = 0.60                # 60 % : atteint seulement si plasticité ET richesse
                                      # de la journée sont TOUTES DEUX maximales
IMPORTANCE_REFERENCE_REVE = 0.5      # échelle de calibration : à ajuster en observant
                                      # la distribution réelle de 'importance' sur tes runs
TAILLE_MIN_REVE = 8                  # sous ce nombre de souvenirs, le lot est jugé trop
                                      # petit pour un gradient stable : pas de rêve cette nuit

# --- LE CURSUS PROGRESSIF (v35.0, expérimental) ---
#
# 🔴 POURQUOI CE CHANGEMENT — le cursus à 5 niveaux bloquait l'agent (mesuré) :
#   2000 jours au Collège sans en sortir, palier 7 atteint dès le jour 701 puis plus rien,
#   22 victoires avec une tendance à 1,08 (stationnaire = hasard, pas apprentissage),
#   « Δt1 atteindre la clé : JAMAIS ATTEINT », 82 % des ticks au contact d'un mur.
#
# TROIS DÉFAUTS DIAGNOSTIQUÉS :
#
#  1. Le saut Primaire → Collège demandait CINQ compétences d'un coup. `Empty-8x8` a
#     1 objet (le but) ; `DoorKey-6x6` en a 3 et exige repérer + ramasser + porter +
#     viser + ouvrir. Deux victoires sur une salle vide suffisaient pour y accéder.
#
#  2. L'exigence d'EFFICACITÉ faisait un bond de ×10 sans étape intermédiaire. Mesuré par
#     BFS sur (x, y, direction) — coût réel en ACTIONS, rotations et `toggle` compris,
#     30 graines par niveau :
#
#         DoorKey-6x6        : 9.7 actions optimales pour 360 dispo  → marge 37.0x
#         Empty-8x8          : 11.0                     256          → marge 23.3x
#         MultiRoom-N2-S4    : 7.3                       40          → marge  5.5x
#         MultiRoom-N4-S5    : 33.7 (max 43)            120          → marge  3.6x
#
#     ⚠️ Le Doctorat n'est PAS infaisable (première lecture erronée, corrigée) : la marge
#     reste positive. Mais l'agent passe d'un droit à l'erreur de ×37 à ×3.6 en un seul
#     saut. `MultiRoom-N2-S4` (×5.5) est l'étape manquante.
#
#  3. Aucun palier ne consolidait : chaque niveau changeait DE TÂCHE, jamais d'échelle.
#
# LE PRINCIPE DE CE PROGRAMME : entre deux paliers voisins, **une seule chose change**.
# `DoorKey-5x5` → `6x6` → `8x8` est la MÊME tâche à trois échelles — l'agent consolide au
# lieu de tout réapprendre. Même logique pour `MultiRoom-N2` → `N4`.
#
# MiniGrid expose 58 environnements ; le projet n'en utilisait que 5.
#
# Rétrocompatibilité : `niveau_actuel` est un INDEX. Un `.brain` sauvegardé au niveau 4
# (ex-Doctorat) se retrouverait à l'index 4 du nouveau programme (`LavaGapS5`) — voir
# `persistance._remapper_niveau_cursus`, qui traduit l'ancien index vers le nouveau.
# v41.25 — BANC DE MESURE (`--env-force`). Quand il est non-nul, le PROGRAMME entier est
# remplacé par ce seul niveau, répété : l'agent naît dedans et n'en sort jamais.
#
# 🔴 POURQUOI. La lave n'apparaît qu'au niveau 5 (`LavaGapS5`) et l'agent est bloqué au
# niveau 4 depuis toutes les campagnes mesurées. Un A/B de la douleur thermique lancé sur
# le cursus normal comparerait donc deux bras dont le terme mesuré vaut zéro dans 99,7 %
# des ticks — une ablation VIDE, pas négative (§4 de la règle de mesure). Le banc n'est
# pas un raccourci : c'est la seule façon d'exposer réellement le mécanisme testé.
ENV_FORCE = None

# v41.32 — ABLATION « PISTE C » : le thrashing vient-il du CONFLIT DES ORGANES ?
#
# Mesuré le 25/08 : le gradient reçu par `integrateur_bio` (0,914) vaut **78×** celui de
# `porte_visuelle` (0,012) — le corps dicte l'essentiel de la mise à jour des poids. Or les
# besoins corporels ALTERNENT par construction : affamé un jour, assoiffé le lendemain. Si
# la politique ne conditionne pas sur l'état externe (mesuré : distance mur/ressource au
# niveau du bruit), elle subit cette alternance comme un pendule et le gradient s'annule.
#
# ⚠️ CE DRAPEAU NE SUPPRIME PAS LA SOIF, il en GÈLE la dynamique : `hydratation` reste à
# 1.0, donc le terme `(1 − hydratation)²` du déficit vaut 0 en permanence. L'agent garde
# ses cinq sens, sa mémoire, sa vue — SEUL l'axe hydrique cesse de tirer la politique.
# C'est la discipline du témoin `--sans-douleur` : garder le SENS, ne couper que la
# MÉCANIQUE, pour isoler la boucle testée du capteur lui-même.
#
# ⚠️ Un agent qui n'a jamais soif ne cherche plus d'eau : la récolte hydrique tombera, et
# c'est ATTENDU. Ce drapeau ne mesure PAS la performance — uniquement l'alignement du
# gradient. Ne jamais en tirer une conclusion de niveau atteint.
SOIF_FIGEE = False

PROGRAMME = [
    # — Socle moteur : se déplacer, sans aucun objet à manipuler —
    ("MiniGrid-Empty-5x5-v0",         "Nourrisson (Premiers pas)"),
    ("MiniGrid-Empty-Random-6x6-v0",  "Éveil (Départ aléatoire)"),
    ("MiniGrid-Empty-8x8-v0",         "Maternelle (Longue distance)"),
    # — Socle spatial : le monde n'est plus vide —
    ("MiniGrid-SimpleCrossingS9N1-v0", "Primaire 1 (Contourner)"),
    ("MiniGrid-LavaGapS5-v0",          "Primaire 2 (Éviter le danger)"),
    ("MiniGrid-Fetch-5x5-N2-v0",       "Primaire 3 (Ramasser)"),
    # — Logique clé/porte, introduite en trois temps —
    ("MiniGrid-GoToDoor-6x6-v0",      "Collège 1 (Viser une porte)"),
    ("MiniGrid-DoorKey-5x5-v0",       "Collège 2 (Clé & porte, minimal)"),
    ("MiniGrid-DoorKey-6x6-v0",       "Collège 3 (Clé & porte)"),
    ("MiniGrid-DoorKey-8x8-v0",       "Lycée 1 (Clé & porte, distance)"),
    ("MiniGrid-Unlock-v0",            "Lycée 2 (Déverrouiller)"),
    ("MiniGrid-UnlockPickup-v0",      "Lycée 3 (Déverrouiller & prendre)"),
    # — Mémoire, puis planification longue —
    ("MiniGrid-MemoryS7-v0",          "Université (Mémoire Épisodique)"),
    ("MiniGrid-MultiRoom-N2-S4-v0",   "Doctorat 1 (Deux pièces)"),
    ("MiniGrid-MultiRoom-N4-S5-v0",   "Doctorat 2 (Planification Longue)"),
]

# --- PROMOTION PAR TAUX DE MAÎTRISE (v35.0) ---
#
# `VICTOIRES_REQUISES = 2` consécutives était à la fois FRAGILE et FAIBLE : une seule
# défaite remettait le compteur à zéro (donc un agent à 80 % de réussite pouvait rester
# bloqué), et deux réussites d'affilée peuvent n'être que de la chance sur un niveau facile.
#
# Le taux glissant mesure une compétence INSTALLÉE : il faut réussir `TAUX_PROMOTION` des
# `FENETRE_PROMOTION` derniers épisodes. Une défaite ne détruit plus rien, elle pèse son
# poids réel dans la moyenne.
#
# ⚠️ Les deux critères coexistent (OU logique) : `VICTOIRES_REQUISES` reste actif comme
# voie rapide pour un agent qui enchaîne. C'est ce qui garantit qu'aucun cerveau existant
# ne régresse en vitesse de promotion — le taux ne fait qu'AJOUTER une seconde porte.
VICTOIRES_REQUISES = 2
FENETRE_PROMOTION = 20      # nombre d'épisodes observés (borne, pas une cible)
TAUX_PROMOTION = 0.60       # 60 % de réussite sur la fenêtre ⇒ compétence installée
MIN_EPISODES_PROMOTION = 10  # sous ce nombre, le taux n'est pas encore significatif

# --- v40.2 : LA MATURITÉ — la promotion cesse d'être scolaire ---
#
# Formulation utilisateur : « L'idée de promotion devrait être différente, car c'est une
# méthode très scolaire qui ne qualifie pas directement les capacités d'un élève/agent. »
#
# CE QUI CLOCHAIT. Deux portes en OU, toutes deux binaires : 2 victoires CONSÉCUTIVES, ou
# 60 % sur 20 épisodes. La première est un examen qu'on passe par chance — et la campagne
# P17 l'a mesuré noir sur blanc : un agent monté au palier 5/6 avec **4 victoires au
# total**, dont plus aucune depuis 1368 jours, contre un agent resté à 1/6 avec **205
# victoires**. Le niveau enregistrait le plus haut palier jamais EFFLEURÉ, pas ce que
# l'agent savait faire.
#
# CE QUI LA REMPLACE. Une grandeur continue dans [0, 1] — la MATURITÉ — produit de trois
# facteurs qui doivent TOUS être présents. Un produit, jamais une somme : une somme
# laisserait un facteur fort compenser un facteur nul, et c'est exactement ce que faisait
# le OU logique.
#
#   maturité = régularité × consolidation × autonomie
#
#   RÉGULARITÉ    le taux de réussite observé. « Sait-il faire ? »
#   CONSOLIDATION combien de fois il l'a montré, rapporté à la fenêtre. « Est-ce installé
#                 ou est-ce un coup de chance ? » — c'est ce facteur qui tue l'examen : un
#                 agent à 2 victoires sur 2 a une régularité de 1,0 mais une consolidation
#                 de 0,1, donc une maturité de 0,1. Il ne passe pas.
#   AUTONOMIE     1 − guidage. « Y arrive-t-il SANS béquille ? » Un agent qui ne réussit
#                 que sous perfusion de récompense continue n'a rien démontré ; le sevrage
#                 (v35.1) fait déjà décroître ce guidage avec la maîtrise, donc l'autonomie
#                 monte toute seule quand la compétence s'installe. Aucun terme nouveau.
#
# LA PROMOTION RESTE UN ÉVÉNEMENT DISCRET — on change de carte ou non, il n'existe pas de
# demi-promotion — mais elle est désormais déclenchée par le franchissement d'une grandeur
# CONTINUE que l'agent construit, au lieu d'un compteur d'examens réussis.
# Le SEUIL_MATURITE est DÉRIVÉ des constantes de sevrage, définies plus bas dans ce
# fichier (§ guidage dégressif) — voir `SEUIL_MATURITE` juste après elles.

# --- LE GUIDAGE DÉGRESSIF (v35.1) : « plus il comprend, moins on l'aide » ---
#
# Décision utilisateur, formulée ainsi : *« à chaque victoire, jusqu'à 85-100 % de réussite,
# on fait de façon à moins répéter — comme un enfant : plus il comprend, moins on l'aide,
# jusqu'à lui laisser assez d'autonomie pour qu'il comprenne. »*
#
# 🔴 CE QUE ÇA REMPLACE. Le guidage était coupé d'un SEUL COUP au palier 5 (Mode Libre),
# c'est-à-dire au moment précis où la tâche devient la plus dure. Mesuré sur 2000 jours :
# **0,00 record de proximité par jour** — l'agent perdait tout signal de progression
# spatiale du jour au lendemain. Une falaise, là où il fallait une pente.
#
# LA FORME. Le facteur suit la maîtrise mesurée, pas un numéro de palier ni un compteur de
# jours : c'est la même doctrine que le rêve adaptatif (le pourcentage rejoué émerge de la
# plasticité × richesse, jamais d'une constante).
#
#     maîtrise = 0                            →  guidage PLEIN   (facteur 1.0)
#     maîtrise >= SEUIL_FIN_SEVRAGE   (90 %)  →  guidage NUL     (facteur 0.0)
#     entre les deux                          →  décroissance linéaire
#
# Pourquoi 90 % et pas 100 % : à 100 %, le guidage ne s'éteindrait jamais tout à fait — or
# le but est bien l'autonomie complète. C'est une BORNE ; le facteur réel est dérivé.
#
# ⚠️ v41.3 — LE SEVRAGE COMMENCE AU PREMIER POINT DE MAÎTRISE. Il démarrait auparavant à
# `SEUIL_DEBUT_SEVRAGE = 0.60`, choisi parce que c'était `TAUX_PROMOTION`. L'intention
# était juste — « le sevrage commence quand l'agent devient promouvable » — mais l'effet
# était l'inverse : à 60 % l'autonomie valait encore exactement 0, donc la maturité
# (un PRODUIT) aussi, donc **la promotion était mathématiquement impossible**. Mesuré sur
# 300 jours : aide pleine 300 jours sur 300, maîtrise à 60 % deux fois, zéro promotion.
#
# ⚠️ INVARIANT : quand la maîtrise n'est pas encore mesurable (< MIN_EPISODES_PROMOTION),
# le guidage reste PLEIN. Un agent qui débarque sur un niveau neuf est un débutant, pas un
# expert — lui couper l'aide faute de données serait exactement l'erreur du Mode Libre.
SEUIL_FIN_SEVRAGE = 0.90     # borne haute : au-dessus, plus aucune aide

# --- v41.4 : LA MAÎTRISE GÉNÉRALE ET L'HÉRITAGE D'AUTONOMIE ---
#
# Décision utilisateur : *« tu as une maîtrise générale des cartes et une maîtrise carte
# par carte »*, et *« reporter une proportion du niveau précédent de maîtrise sur le
# suivant »*.
#
# 🔴 CE QUE ÇA CORRIGE. Mesuré sur le run v41.3 de 300 jours : à chaque promotion,
# `historique_episodes_niveau` est vidé (invariant non négociable), donc la maturité
# retombe à **0,000 exactement** et le guidage à **1,0 — l'aide maximale**. L'agent
# redevient un nouveau-né sur chaque carte. Après deux promotions (j74, ~j180), la
# maîtrise s'est effondrée à 2 % et l'autonomie à 3 % sur les 185 derniers jours.
#
# Or un agent qui vient de tenir 60 % sur trois cartes n'est pas un débutant absolu : il
# sait terminer un épisode. Ce qui est périmé, c'est le PLAN de la carte — pas la
# compétence motrice.
#
# LA FORME. Deux grandeurs distinctes, comme demandé :
#   • maîtrise PAR CARTE  (`historique_episodes_niveau`)  → pilote la PROMOTION
#   • maîtrise GÉNÉRALE   (`historique_episodes_general`) → pilote le SEVRAGE, en attendant
#
# L'héritage est reporté **à proportion de la parenté mesurée** entre l'ancienne carte et
# la nouvelle (`_parente_cartes`), jamais d'un pourcentage posé : la parenté entre voisins
# du PROGRAMME varie de 0,85 à 0,00 selon la paire. Il s'efface ensuite à mesure que les
# données réelles de la nouvelle carte arrivent (pondération par le remplissage de la
# fenêtre) — sans quoi une baisse de compréhension ne pourrait plus faire remonter l'aide,
# ce que l'utilisateur exige explicitement : *« une baisse de compréhension augmente aussi
# l'aide proportionnellement »*.
#
# ⚠️ TROIS INVARIANTS.
#   1. L'héritage ne touche QUE le sevrage. `_maturite_niveau` continue de lire la seule
#      maîtrise par carte : la promotion exige une preuve fraîche, sinon un agent
#      enchaînerait les paliers sans rien montrer (mesuré en P17 : palier 5/6 avec
#      4 victoires au total).
#   2. Il s'EFFACE quand la fenêtre se remplit. À fenêtre pleine, le sevrage ne dépend
#      plus que du niveau courant — exactement comme en v41.3.
#   3. La parenté est LUE sur la grille, jamais tabulée. Aucune table
#      `niveau → difficulté` : ce serait renommer une constante en dur.
FENETRE_MAITRISE_GENERALE = 100   # borne : ~5 fenêtres de niveau, assez long pour
                                   # traverser plusieurs cartes, assez court pour qu'un
                                   # décrochage durable finisse par s'y voir

# Interrupteur d'ABLATION (drapeau de campagne, pas un réglage cognitif) : coupé, le
# sevrage retombe exactement sur v41.3. Il n'existe que pour disposer d'un témoin à
# graine identique — voir `--sans-heritage`.
HERITAGE_SEVRAGE_ACTIF = True

# v41.28 — interrupteur du TRAVAIL TENTÉ (`--travail-reussi` = témoin v41.27).
# True  : un geste stérile coûte le travail qu'il a TENTÉ (pousser un mur = prix d'un pas).
# False : `travail = 0.0` dès que le monde n'a pas bougé — l'ancien barème, où le geste
#         inutile était le MOINS CHER (1,09 contre 4,00 pour avancer).
TRAVAIL_TENTE_ACTIF = True


# v41.27 — interrupteur de l'option (b) : mourir coûte le reste de la journée.
# True  : la journée s'arrête à la mort (décision utilisateur du 19/08).
# False : l'agent repart au tick suivant — le comportement de toutes les versions
#         antérieures, et le TÉMOIN qui isole le coût de l'option (b) de celui de la
#         douleur elle-même. Sans ce témoin, deux changements simultanés seraient
#         confondus et le résultat ininterprétable (règle « rien sans témoin »).
MORT_COUTE_LA_JOURNEE = True

# v41.25 — interrupteur d'ablation de la NOCICEPTION THERMIQUE (`--sans-douleur`).
# True  : la chaleur entre dans le déficit (`+ chaleur**2`) — elle FAIT MAL.
# False : la chaleur reste perçue par les 2 dims de thermoception, mais ne coûte rien —
#         c'est exactement l'état v41.11 à v41.24, le TÉMOIN de la campagne.
# Le témoin n'est donc pas « sans thermoception » : le sens est identique des deux côtés,
# seule la douleur diffère. C'est ce qui isole la boucle nociceptive du sens lui-même.
DOULEUR_THERMIQUE_ACTIVE = True

# v41.10 — interrupteur d'ablation de la mémoire par carte (`--sans-memoire-cartes`).
# False = la bascule EFFACE, comportement v41.9 exact. Un seul point de lecture
# (`_appliquer_niveau_episode`), jamais un branchement dispersé dans le chemin cognitif.
MEMOIRE_PAR_CARTE_ACTIVE = True

# v41.13 — interrupteur d'ablation du CORPS DANS LE ROLLOUT (`--sans-corps-rollout`).
# False = C2 simule sans reprojeter le vecteur bio, comportement v41.12 bit-identique.
CORPS_DANS_ROLLOUT_ACTIF = True

# v41.16 — interrupteur d'ablation du BRAIN-SPARING (`--vigueur-sur-logits`).
# False = la vigueur multiplie de nouveau les logits (comportement v41.15 exact).
BRAIN_SPARING_ACTIF = True

# v41.17 — ABLATION CROISÉE. La v41.16 a livré DEUX mécaniques dans le même commit, et sa
# campagne (8 victoires sur 10 duels, intervalles disjoints au niveau 4) ne peut donc pas
# dire laquelle produit l'effet. Ce second drapeau les sépare :
#
#   BRAIN_SPARING_ACTIF   : la vigueur cesse d'écraser les LOGITS   (loi A — l'esprit)
#   ECONOMIE_ACTION_ACTIVE: la vigueur module le COÛT D'ACTION      (loi B — le corps)
#
# Les quatre cellules du plan factoriel :
#   (OFF, OFF) = v41.15 exact | (ON, OFF) = esprit seul
#   (OFF, ON)  = corps seul   | (ON, ON)  = v41.16 complet
ECONOMIE_ACTION_ACTIVE = True

# v41.20 — LE COÛT MOTEUR PHYSIQUE (`--cout-moteur-table` pour revenir à l'ancien).
#
# True  : l'effort est un TRAVAIL (masse × déplacement réel), voir
#         `calculer_effort_metabolique`. La table des 7 valeurs n'est plus lue.
# False : témoin — retour à `COUT_CORPOREL_PAR_ACTION`, la violation n°1 de la revue
#         du dogme, conservée UNIQUEMENT comme bras de comparaison A/B.
#
# La table n'est pas supprimée du fichier : elle reste le témoin d'ablation, exactement
# comme `reinitialiser_niveau` a été conservée en v41.10.
COUT_MOTEUR_PHYSIQUE = True

# v41.18 — TEST DE FALSIFICATION DU VERROU P17 (`--defi-force`, hors par défaut).
#
# La mesure du 17/08 montre qu'au niveau 4 l'agent ne joue son propre palier que 34 % du
# temps, et que la part de défi ne monte qu'AVEC la maîtrise (33 % à maîtrise 0,20, 65 %
# à 0,60). D'où l'hypothèse d'un verrou : pour maîtriser il faut s'entraîner, pour
# s'entraîner il faut déjà maîtriser.
#
# ⚠️ Cette hypothèse repose sur une CORRÉLATION, et le sens de la boucle est ambigu :
# « peu de défi ⇒ peu de maîtrise » et « peu de maîtrise ⇒ peu de défi » expliquent tous
# deux les mêmes chiffres. Ce drapeau force l'exposition à 100 % du palier de référence,
# ce qui tranche : si la maîtrise décolle, le défi était bien le facteur limitant ; si
# elle stagne, le palier est simplement trop dur et la formule P17 est innocentée.
#
# C'est un INSTRUMENT DE MESURE, pas une mécanique candidate : il court-circuite tout le
# principe de P17 (le cursus comme distribution) et ne doit jamais être activé par défaut.
DEFI_FORCE = False

# --- v40.2 : LE SEUIL DE MATURITÉ, DÉRIVÉ (voir `_maturite_niveau`) ---
#
# Il n'est PAS posé. Il vaut la maturité d'un agent qui réussit `TAUX_PROMOTION` du temps
# ET qui, à ce niveau de compétence, a déjà été sevré à proportion — et continue de
# réussir sans l'aide retirée.
#
# v41.3 — il dérive désormais de `TAUX_PROMOTION` directement, ce que l'ancienne courbe
# interdisait : à 0,60 le sevrage n'avait pas commencé, l'autonomie y était nulle par
# construction, et le seuil devait donc être calculé à mi-rampe (0,375) — un point sans
# signification propre. Avec un sevrage proportionnel dès le premier point, le taux de
# promotion redevient calculable, et les deux constantes cessent de se neutraliser.
_AUTONOMIE_A_PROMOTION = min(1.0, TAUX_PROMOTION / SEUIL_FIN_SEVRAGE)
SEUIL_MATURITE = TAUX_PROMOTION * _AUTONOMIE_A_PROMOTION
                            # ≈ 0,400 — BORNE, jamais une cible. Elle ne fixe aucun
                            # comportement : elle dit « à ce point, rester est du
                            # surplace ». Les grandeurs dont elle dérive préexistent
                            # toutes.

# --- LE FILET DE SÉCURITÉ (v35.1) : « quand il bloque, on l'aide un peu » ---
#
# Décision utilisateur, en réponse à la question de la redescente de palier :
# *« non, il ne peut pas aller faire un palier impossible — et quand il bloque, on l'aide
# un peu. »*
#
# La redescente est donc ÉCARTÉE (elle contredirait « ce qui ne régresse jamais », §11 du
# guide des parcours). À la place : un agent qui stagne longtemps reçoit un SURPLUS d'aide,
# au-delà même du guidage nominal.
#
# Mesuré, le cas à traiter : sur `SimpleCrossingS9N1`, un cerveau neuf a calé à **0 % de
# maîtrise pendant 79 jours** après avoir franchi 3 niveaux en 21 jours. Sans filet, il y
# serait resté indéfiniment — exactement le scénario des 2000 jours au Collège.
#
# La forme : au-delà de `JOURS_AVANT_RENFORT` jours consécutifs sans la moindre victoire
# sur le niveau courant, l'aide est multipliée, jusqu'à `RENFORT_AIDE_MAX`. La montée est
# progressive (un jour de plus = un peu plus d'aide), jamais un palier brutal — même
# principe que le sevrage, en miroir.
#
# ⚠️ Le renfort se remet à zéro dès la PREMIÈRE victoire : c'est une bouée, pas une rente.
# Et il ne s'applique qu'au guidage (récompenses d'approche), jamais à la récompense
# terminale — on aide l'agent à trouver le chemin, on ne lui offre jamais la victoire.
# --- v36.0 : L'ABSTRACTION PAR RÉCURRENCE ---
# Nombre de confirmations à partir duquel un repère est « à moitié abstrait »
# (`solidite = n / (n + REF)` vaut 0.5 pour n = REF). Saturation douce : la 1re
# confirmation apporte beaucoup, la 50e presque rien — une régularité n'a pas besoin
# d'être vue mille fois pour être une régularité. BORNE d'échelle, pas une cible : la
# solidité réelle reste dérivée du vécu.
SOUVENIRS_CONFIRMATIONS_REFERENCE = 5

# Plancher d'ENREGISTREMENT (pas un seuil de décision — il ne pilote aucune action) : en
# deçà, un tick est du bruit de fond et ne mérite pas de laisser de trace. Calibré sur
# l'ordre de grandeur des micro-récompenses existantes (MICRO_RECOMPENSE_CURIOSITE = 0.04,
# MALUS_DOULEUR = -0.01) : un simple choc contre un mur ne crée pas de repère, un jalon
# franchi ou une mort en crée un. À mesurer sur run long via `Memoire_Ecritures_Jour`.
SEUIL_SAILLANCE_MEMOIRE = 0.05

JOURS_AVANT_RENFORT = 30     # borne : en deçà, un échec est normal, pas un blocage
RENFORT_AIDE_MAX = 3.0       # borne haute du multiplicateur d'aide
PENTE_RENFORT = 60           # jours supplémentaires pour atteindre le renfort maximal


def facteur_guidage(etat) -> float:
    """Retourne le multiplicateur d'aide du jour, dans [0.0, RENFORT_AIDE_MAX] (v35.1).

    Appliqué à TOUTES les récompenses de guidage — `RECOMPENSE_APPROCHE_BUT` (DoorKey) et
    les records de proximité (`DetecteurProgresPersonnel`) — pour qu'un seul curseur pilote
    l'assistance, au lieu de deux mécaniques qui s'éteignent selon des règles différentes.

    Deux forces opposées, dans cet ordre :
      1. le SEVRAGE — plus l'agent maîtrise, moins on l'aide (jusqu'à 0.0) ;
      2. le FILET — plus il stagne, plus on l'aide (jusqu'à RENFORT_AIDE_MAX).

    Elles ne peuvent pas se contredire : un agent qui stagne a par définition une maîtrise
    basse, donc un sevrage à 1.0 que le renfort vient amplifier. Un agent qui maîtrise n'a
    aucun jour de stagnation, donc aucun renfort. Le produit reste toujours cohérent.

    Lecture seule : ne modifie rien, peut être appelée autant de fois que voulu.
    """
    # v40.1-fix4 — LE SEVRAGE ÉCRIT COMME UNE RAMPE, plus comme un escalier à 3 marches.
    # Les trois branches (`<= DEBUT`, `>= FIN`, sinon interpolation) sont exactement les
    # deux saturations d'une rampe linéaire : un `clip` les absorbe toutes. Le `None`
    # (« pas encore mesurable ») reste une garde technique, pas un régime cognitif — il
    # distingue « aucune donnée » de « mesuré à zéro », ce qu'aucune formule ne peut faire.
    # v41.3 — LE SEVRAGE COMMENCE AU PREMIER POINT DE MAÎTRISE, plus à 60 %.
    #
    # Défaut mesuré sur un run de 300 jours : la promotion était MATHÉMATIQUEMENT
    # IMPOSSIBLE. `maturite = régularité × consolidation × autonomie` est un produit, et
    # `autonomie = 1 − guidage` valait **0 sur les 300 jours** — donc le produit aussi.
    # Cause : `SEUIL_DEBUT_SEVRAGE = 0.60` était le point où le sevrage *commençait*, et
    # `TAUX_PROMOTION = 0.60` celui où la promotion était *exigée*. À 60 % de maîtrise,
    # l'autonomie valait donc encore exactement zéro ; il fallait ~75 % pour qu'elle
    # décolle, et l'aide est restée « pleine » 300 jours sur 300. L'agent a touché 60 %
    # deux fois sans jamais pouvoir être promu.
    #
    # Le sevrage est désormais **inversement proportionnel à la maîtrise** (formulation
    # utilisateur) : chaque point gagné retire immédiatement de l'aide, au lieu d'attendre
    # un palier. `SEUIL_FIN_SEVRAGE` reste la borne où l'aide s'annule.
    #
    # ⚠️ Le sens de l'inversion compte. C'est le GUIDAGE qui est inverse de la maîtrise,
    # donc l'AUTONOMIE qui lui est proportionnelle — l'inverse rendrait l'agent d'autant
    # plus « autonome » qu'il échoue, et promouvrait les cerveaux les moins compétents.
    #
    # Effet sur la maturité (à consolidation pleine) : 0,044 à 20 % de maîtrise, 0,178 à
    # 40 %, **0,400 à 60 %** — soit le franchissement du seuil de promotion (0,38) à
    # exactement 60 % de maîtrise, la valeur historique de `TAUX_PROMOTION`. Les deux
    # constantes redeviennent cohérentes au lieu de se neutraliser.
    taux = _taux_maitrise_niveau(etat)
    taux_effectif = 0.0 if taux is None else taux

    # --- v41.4 : L'HÉRITAGE — ce qu'il sait déjà compte, à proportion de la parenté ---
    #
    # Le taux qui pilote le sevrage est un mélange entre ce que l'agent démontre ICI et
    # ce qu'il a démontré AILLEURS, pondéré par deux facteurs mesurés :
    #
    #   • le REMPLISSAGE de la fenêtre du niveau — plus il a joué ici, moins le passé
    #     compte. À fenêtre pleine l'héritage vaut 0 : on retombe exactement sur v41.3.
    #   • la PARENTÉ entre la carte quittée et la carte courante — un saut de vocabulaire
    #     ne se transfère pas.
    #
    # Le produit des deux est la seule chose qui décide : rien n'est posé.
    h_niveau = etat.historique_episodes_niveau
    fraicheur = min(1.0, len(h_niveau) / FENETRE_PROMOTION)   # 0 = rien joué ici
    taux_general = _taux_maitrise_generale(etat)
    parente = max(0.0, min(1.0, getattr(etat, "parente_niveau_precedent", 0.0)))

    if taux_general is None or not HERITAGE_SEVRAGE_ACTIF:
        # Aucun vécu transversal significatif (ou ablation de campagne) : le débutant
        # reste un débutant, et le sevrage retombe exactement sur v41.3.
        taux_pour_sevrage = taux_effectif
    else:
        poids_heritage = (1.0 - fraicheur) * parente
        taux_pour_sevrage = (taux_effectif * (1.0 - poids_heritage)
                             + taux_general * poids_heritage)

    # Télémétrie (bilan de nuit + W&B). ⚠️ v41.5 — cette fonction est désormais appelée
    # DEUX FOIS par journée : au matin par `demarrer_journee` (c'est cette valeur-là qui
    # est APPLIQUÉE à la journée) et au soir par `_maturite_niveau` (lecture synchrone du
    # critère). La télémétrie porte donc la valeur du SOIR, celle qui a décidé de la
    # promotion — c'est l'information utile pour comprendre un franchissement, et elle est
    # cohérente avec l'autonomie affichée juste à côté dans le bilan.
    etat.taux_sevrage_jour = taux_pour_sevrage
    # v41.4-fix1 — mémoriser AUSSI le taux du niveau tel qu'il était À CET INSTANT.
    # Le guidage est calculé en début de journée (`demarrer_journee`) et le bilan
    # s'affiche en fin de journée : entre les deux, la fenêtre glissante a bougé de
    # plusieurs épisodes. Comparer `taux_sevrage_jour` au taux de FIN de journée mesurait
    # ce décalage temporel et l'étiquetait « héritage » — jusqu'à −33 pt affichés sur un
    # run où l'héritage était pourtant coupé. L'écart n'est un héritage que si les deux
    # termes sont lus au même instant.
    etat.taux_niveau_au_sevrage = taux_effectif
    base = 1.0 - max(0.0, min(1.0, taux_pour_sevrage / SEUIL_FIN_SEVRAGE))

    # --- Le filet : renfort progressif après une longue stagnation ---
    # `jours_stagnation_niveau` compte les jours consécutifs SANS victoire sur le niveau
    # courant ; il est remis à zéro à la première victoire et à chaque promotion.
    #
    # Le `if jours_bloque <= JOURS_AVANT_RENFORT: return base` était la borne basse de la
    # même rampe : `max(0, ...)` la porte, et `progression = 0` rend le facteur 1.0 donc
    # `base` inchangée. Une seule expression pour les deux cas.
    jours_bloque = getattr(etat, "jours_stagnation_niveau", 0)
    progression = max(0.0, min(1.0, (jours_bloque - JOURS_AVANT_RENFORT) / PENTE_RENFORT))
    return base * (1.0 + (RENFORT_AIDE_MAX - 1.0) * progression)


# --- Le Cursus Développemental par Ères (v23.0, expérimental) ---
# Programme de 1000 jours subjectifs qui alterne MiniGrid (matin) et apprentissage
# vocal (après-midi), avec une difficulté qui monte par ères — voir
# cursus_developpemental.py pour la boucle qui pilote ces constantes. Ce curriculum est
# une couche AJOUTÉE au-dessus de PROGRAMME (décision utilisateur) : les deux
# progressent en parallèle, indépendamment l'un de l'autre.
DUREE_ERE = 1000                 # jours subjectifs visés pour un cycle complet du cursus
TICKS_MATIN = 200                # ticks [0, TICKS_MATIN) : focus moteur/visuel (MiniGrid)
                                  # ticks [TICKS_MATIN, ticks_par_jour) : focus vocal/auditif
BORNES_ERES = (400, 600)         # jour < 400 : Alternance ; 400-599 : Synesthésie ; ≥600 : Intégration

# École de Rattrapage Vocal (v24.0-fix1) : le seuil de promotion vocale n'est plus une
# constante fixe mais PROGRESSE par palier atteint. Diagnostic sur un vrai run de 1000
# jours : avec un seuil fixe à 0.5 (v23.0 initial), gestionnaire_cursus_vocal_succes_courant
# est resté à 0 du jour 1 au jour 1000 (aucune promotion), et porte_auditive.base_weight
# a fini à NORME EXACTEMENT ZÉRO — l'oreille n'a strictement rien appris. Cause racine :
# `cycle_sommeil` (ligne 87) érode `base_weight` d'autant plus fort que `myeline_M` est
# faible ; sans un premier succès pour amorcer la myélinisation, le peu de gradient
# accumulé dans la journée se fait entièrement raser chaque nuit — un cercle vicieux
# qui ne se débloque jamais tout seul. L'École de Rattrapage démarre donc TRÈS
# permissive (0.15, cohérent avec les scores réellement observés sur cerveau neuf,
# voir plan v22.1) pour garantir un premier succès rapide et amorcer la myélinisation,
# puis DURCIT à mesure que le palier vocal progresse (paliers plus difficiles =
# exigence plus grande), jusqu'à 0.45 sur les derniers paliers — jamais 0.5, pour ne
# jamais retomber dans le blocage diagnostiqué. Voir aussi ATTENUATION_EROSION_AUDIO_DEBUT
# ci-dessous pour le second volet du correctif (protéger le tout premier apprentissage).
SEUIL_VOCAL_PALIER_DEBUTANT = 0.15  # paliers 1-3 (vocaliser, voyelles a/e)
SEUIL_VOCAL_PALIER_AVANCE = 0.45     # dernier palier (combinatoire) — jamais 0.5
# v25.0 (Paradigme Bébé, expérimental) : 11 -> 14, suite à l'ajout des paliers
# "porte" (12) et combinatoire "ouvre porte"/"prends clé" (13-14) dans
# professeur_gemma.CURRICULUM_VOCAL — DOIT rester synchronisé avec len(CURRICULUM_VOCAL)
# sous peine de fausser l'interpolation de seuil_jour_vocal_reussi ci-dessous.
# v27.0 (École de la Parole & Synesthésie, expérimental) : 14 -> 19, suite à l'ajout
# des paliers 15-19 (mur/clé/but/vide/"porte jaune", voir professeur_gemma.py) — ce
# fichier étant gitignoré, AUCUN diff de PR n'attrape un oubli de cette synchronisation :
# vérifier à la main après toute modification de CURRICULUM_VOCAL. Effet secondaire :
# abaisse le seuil de chaque palier intermédiaire déjà atteint (interpolation sur une
# plage plus longue) — assouplissement, pas de risque de blocage.
NB_PALIERS_VOCAUX = 19                # cohérent avec professeur_gemma.CURRICULUM_VOCAL


def seuil_jour_vocal_reussi(palier_vocal: int) -> float:
    """École de Rattrapage Vocal : interpolation linéaire de SEUIL_VOCAL_PALIER_DEBUTANT
    (palier 1) à SEUIL_VOCAL_PALIER_AVANCE (palier NB_PALIERS_VOCAUX). Un `palier_vocal`
    hors bornes est simplement clampé (robuste à un curriculum vocal qui changerait de
    longueur)."""
    p = max(1, min(NB_PALIERS_VOCAUX, palier_vocal))
    progression = (p - 1) / (NB_PALIERS_VOCAUX - 1)  # 0.0 au palier 1, 1.0 au dernier
    return SEUIL_VOCAL_PALIER_DEBUTANT + progression * (SEUIL_VOCAL_PALIER_AVANCE - SEUIL_VOCAL_PALIER_DEBUTANT)


# École de Rattrapage Vocal, second volet : tant que le palier vocal est encore bas
# (paliers 1-3, la phase la plus fragile où porte_auditive/tete_vocale n'ont accumulé
# AUCUNE myéline), l'érosion nocturne standard de ces 2 couches est atténuée d'un
# facteur — laisse au gradient de la journée une chance de survivre à plusieurs nuits
# consécutives plutôt que d'être rasé avant d'avoir pu s'accumuler. Voir
# executer_nuit/cycle_sommeil_global pour l'application ; AGI_Naulthene.cycle_sommeil_global
# reste par ailleurs totalement inchangé pour les 9 autres couches (aucune régression
# sur l'érosion visuelle/motrice déjà mature).
PALIER_VOCAL_FIN_PROTECTION = 3
ATTENUATION_EROSION_AUDIO_DEBUT = 0.1  # 10% de l'érosion normale tant que palier_vocal <= 3


def ere_courante(jour: int) -> str:
    """Retourne l'ère du cursus développemental correspondant au jour subjectif donné,
    selon BORNES_ERES : "alternance" (jour < bornes[0]), "synesthesie"
    (bornes[0] <= jour < bornes[1]), "integration" (jour >= bornes[1])."""
    seuil_synesthesie, seuil_integration = BORNES_ERES
    if jour < seuil_synesthesie:
        return "alternance"
    elif jour < seuil_integration:
        return "synesthesie"
    else:
        return "integration"


# --- Paradigme Développemental Bébé (v25.0, expérimental, naulthene_bb.brain) ---
# Second curriculum développemental, distinct du Cursus par Ères (v23.0) ci-dessus et
# qui vit dans son propre fichier .brain (voir cursus_bebe.py) — décision utilisateur,
# les deux paradigmes ne se mélangent jamais. Vision Piaget/Dehaene plutôt que RL
# classique : au lieu d'un cursus mesuré en réussites de tâche, le bébé traverse 4 ans
# (1440 jours subjectifs, 3600 ticks/jour) découpés en 5 phases d'âge, avec un signal de
# récompense externe VERROUILLÉ à zéro pendant les 8 premiers mois (JOUR_FIN_MASQUAGE_EXTERNE)
# — l'agent n'a "aucune idée s'il fait bien ou mal", seuls le JEPA, l'homéostasie et la
# curiosité pilotent l'apprentissage — puis un module "Parent" qui réintroduit
# progressivement un feedback social vocal ("Oui !"/"Non !").
#
# Toutes les constantes et helpers ci-dessous sont des AJOUTS PURS : ils ne sont
# consommés que par cursus_bebe.py et par les nouveaux paramètres optionnels de
# traiter_tick/executer_nuit (masquer_recompense_externe, parent_actif, plafond_reve),
# tous par défaut inertes (False/None) — aucune régression sur le Cursus par Ères ou le
# mode standalone classique.
TICKS_PAR_JOUR_BEBE = 3600         # 1 jour = 3600 ticks (cycle nycthéméral complet) —
                                    # DÉLIBÉRÉMENT distinct du `ticks_par_jour` module
                                    # global (400, Cursus par Ères/standalone) : le
                                    # Cerveau Bébé (cursus_bebe.py) itère sur
                                    # TICKS_PAR_JOUR_BEBE, jamais sur `ticks_par_jour`.
JOURS_TOTAUX_BEBE = 1440           # 4 ans = 48 mois = 1440 jours (~5,18M ticks)
TICKS_MATIN_BEBE = TICKS_PAR_JOUR_BEBE // 2  # même ratio 50/50 matin/après-midi que
                                              # TICKS_MATIN (200/400) du Cursus par Ères,
                                              # rapporté à TICKS_PAR_JOUR_BEBE

# 5 phases d'âge (voir readme.md pour le tableau narratif complet) : bornes hautes
# EXCLUSIVES, dernière phase = tout jour >= dernière borne. Phase 0 : Éveil des Sens
# (0-3 mois) ; Phase 1 : Exploration Motrice (3-6 mois) ; Phase 2 : Locomotion &
# Concepts (6-12 mois) ; Phase 3 : Association Forte (12-24 mois) ; Phase 4 : Jeune
# Enfant (24-48 mois).
BORNES_PHASES_BEBE = (90, 180, 360, 720)

# École de Rattrapage : avant ce jour, la récompense externe (recompense_env) est
# gelée à 0.0 dans traiter_tick — voir masquer_recompense_externe. 240 jours = 8 mois,
# repère biologique du concept ("l'absence de notation 0-8 mois est la véritable clé").
JOUR_FIN_MASQUAGE_EXTERNE = 240

# Plafond du pourcentage de rêve nocturne (voir executer_nuit/pourcentage_reve) par
# phase d'âge — PAS une taille de batch fixe, seulement un PLAFOND : le pourcentage
# réellement rejoué reste émergent (plasticité_base × richesse de la journée), comme
# partout ailleurs dans le moteur de rêve adaptatif. Correspond au "% Dodo" du concept
# (70% -> 35% à mesure que le bébé grandit et dort moins).
PLAFOND_REVE_PAR_PHASE = (0.70, 0.60, 0.50, 0.40, 0.35)

# Module "Parent" (jour >= JOUR_FIN_MASQUAGE_EXTERNE) : feedback social vocal
# déterministe, sans appel Gemma par tick — un score de formants net au-dessus du
# seuil déclenche un "Oui !" (renforce le choc dopaminergique déjà existant sur
# poids_vocal) ; nettement en dessous, un "Non !" pousse activement la dopamine vers
# DOPAMINE_MIN (nouveau canal "cortisol", distinct de la simple friction quotidienne).
SEUIL_PARENT_OUI = 0.45
SEUIL_PARENT_NON = 0.15
TAUX_CORTISOL_PARENT = 0.5


def phase_bebe(jour: int) -> int:
    """Retourne l'indice de phase (0 à 4) du paradigme Bébé pour le jour subjectif
    donné, selon BORNES_PHASES_BEBE. Un jour au-delà de la dernière borne reste en
    phase 4 (Jeune Enfant) — pas d'erreur au-delà de JOURS_TOTAUX_BEBE."""
    for indice, borne in enumerate(BORNES_PHASES_BEBE):
        if jour < borne:
            return indice
    return len(BORNES_PHASES_BEBE)


def plafond_reve_bebe(jour: int) -> float:
    """Plafond de pourcentage_reve (executer_nuit) correspondant à la phase d'âge du
    jour donné — voir PLAFOND_REVE_PAR_PHASE."""
    return PLAFOND_REVE_PAR_PHASE[phase_bebe(jour)]


# --- Cursus de la Parole (v27.0, "École de la Parole & Synesthésie", expérimental,
# naulthene_parole.brain) ---
# Troisième écosystème développemental, distinct du Cursus par Ères (v23.0) et du
# Cerveau Bébé (v25.0) — vit dans son propre fichier .brain (voir cursus_parole.py),
# les trois paradigmes ne partagent jamais le même cerveau. 3 phases pédagogiques
# (imprégnation totale / autonomie guidée / émancipation), voir cursus_parole.py pour
# le détail complet de ce qui change à chaque phase.
TICKS_PAR_JOUR_PAROLE = 800   # > 400 OBLIGATOIRE : apprendre_journee ne se déclenche
                               # QU'APRÈS ticks_par_jour ticks accumulés (docs/fonctionnement/LANCEMENT.md,
                               # piège historique n°5 — moins de 400 ticks = aucun
                               # apprentissage). 800 laisse 400 ticks à CHACUNE des deux
                               # moitiés de la journée, garantissant que même une phase à
                               # guidage nul produit un vrai apprentissage.
TICKS_MATIN_PAROLE = TICKS_PAR_JOUR_PAROLE // 2
JOURS_TOTAUX_PAROLE = 900
BORNES_PHASES_PAROLE = (300, 600)   # bornes HAUTES exclusives, même convention que
                                     # BORNES_PHASES_BEBE/BORNES_ERES
TAUX_GUIDAGE_INITIAL = 1.0   # phase 0 (Imprégnation) : le professeur donne la cible à 100% des ticks
TAUX_GUIDAGE_FINAL = 0.1     # fin de phase 2 (Émancipation) : l'agent est quasi seul


def phase_parole(jour: int) -> int:
    """Indice de phase (0/1/2) du Cursus de la Parole pour le jour subjectif donné,
    selon BORNES_PHASES_PAROLE — même convention que phase_bebe."""
    for indice, borne in enumerate(BORNES_PHASES_PAROLE):
        if jour < borne:
            return indice
    return len(BORNES_PHASES_PAROLE)


def taux_guidage_parole(jour: int) -> float:
    """Fraction des ticks où le professeur fournit une cible vocale (`formants_cibles`),
    décroissante de TAUX_GUIDAGE_INITIAL à TAUX_GUIDAGE_FINAL sur JOURS_TOTAUX_PAROLE.

    Plateau puis décroissance linéaire, PAS une exponentielle : pendant toute la phase
    d'Imprégnation (jour < BORNES_PHASES_PAROLE[0]) le taux reste EXACTEMENT 1.0 —
    l'agent doit d'abord entendre le mot associé à la chose des milliers de fois avant
    qu'on commence à le lâcher. Une exponentielle décroissante dès le jour 1 retirerait
    le guidage pendant la fenêtre la plus fragile (celle où porte_auditive n'a encore
    accumulé aucune myéline, voir le diagnostic v24.0-fix1) et rejouerait le blocage
    "aucune promotion en 1000 jours". La décroissance ne commence qu'à la phase 1.

    Retourne toujours une valeur dans [TAUX_GUIDAGE_FINAL, TAUX_GUIDAGE_INITIAL], un
    jour au-delà de JOURS_TOTAUX_PAROLE restant clampé à TAUX_GUIDAGE_FINAL."""
    debut = BORNES_PHASES_PAROLE[0]
    if jour < debut:
        return TAUX_GUIDAGE_INITIAL
    progression = min(1.0, (jour - debut) / max(1, JOURS_TOTAUX_PAROLE - debut))
    return TAUX_GUIDAGE_INITIAL + progression * (TAUX_GUIDAGE_FINAL - TAUX_GUIDAGE_INITIAL)


def promouvoir_palier_vocal_si_merite(etat):
    """Décide, en fin de journée, si le score de formants moyen du jour justifie une
    promotion du palier vocal — identique dans cursus_developpemental.py, cursus_bebe.py
    et cursus_parole.py (même mécanisme GestionnaireCursusAbnegation via l'instance
    séparée etat.gestionnaire_cursus_vocal, même seuil progressif
    seuil_jour_vocal_reussi). Factorisée ici (v27.0) plutôt que triplée."""
    import naulthene.audio.professeur_gemma as pg

    ticks_vocaux = getattr(etat, "ticks_vocaux_jour", 0)
    if ticks_vocaux == 0:
        return

    # v27.5 (correctif utilisateur, "boucle infinie de promotion vocale") : une fois le
    # dernier palier du curriculum atteint, il n'y a plus rien à promouvoir — court-
    # circuiter AVANT d'appeler enregistrer_resultat_episode, qui continuerait sinon à
    # cumuler des succès et à émettre un message "🎓 [PROMOTION...]" à chaque évaluation
    # réussie (tous les ~2 jours dans les faits), même si etat.palier_vocal n'était
    # jamais réellement incrémenté (la garde plus bas empêchait déjà le dépassement du
    # dernier palier, mais pas le message trompeur ni l'accumulation de succès fantômes
    # dans le gestionnaire). Aucun impact sur score_vocal_jour/la dopamine (déjà réglés
    # séparément par facteur_nouveaute_vocale) — ce court-circuit ne fait que taire un
    # mécanisme de promotion devenu sans objet.
    if etat.palier_vocal >= len(pg.CURRICULUM_VOCAL):
        return

    seuil_du_jour = seuil_jour_vocal_reussi(etat.palier_vocal)
    score_moyen_jour = getattr(etat, "score_vocal_jour", 0.0) / ticks_vocaux
    jour_reussi = score_moyen_jour >= seuil_du_jour

    promu, message = etat.gestionnaire_cursus_vocal.enregistrer_resultat_episode(jour_reussi)
    if message:
        print(f"   🗣️ {message} (score vocal moyen du jour: {score_moyen_jour:.3f}, "
              f"seuil École de Rattrapage: {seuil_du_jour:.3f})")
    if promu and etat.palier_vocal < len(pg.CURRICULUM_VOCAL):
        etat.palier_vocal += 1
        nom_palier = pg.CURRICULUM_VOCAL[etat.palier_vocal - 1]["nom"]
        print(f"   🎓 [PROMOTION VOCALE] Palier {etat.palier_vocal} visé : {nom_palier}")
        if etat.palier_vocal >= len(pg.CURRICULUM_VOCAL):
            print(f"   🏆 [MAÎTRISE VOCALE] L'agent a atteint le dernier palier du "
                  f"curriculum vocal ({len(pg.CURRICULUM_VOCAL)}/{len(pg.CURRICULUM_VOCAL)}) "
                  f"— plus aucune promotion vocale possible, l'effet dopaminergique du "
                  f"canal vocal continue de s'atténuer avec facteur_nouveaute_vocale.")


# --- 4b. HELPERS RÉUTILISABLES (v21.0) ---
# Extraction de la boucle principale en fonctions partagées, consommées à l'identique
# par le mode standalone (voir __main__ en bas de fichier) ET par la Cuve du daemon
# persistant (daemon_cerveau.py, voir CuveDeMaintien._vivre_connexion/_nuit). Aucun
# changement de comportement : mêmes calculs, même ordre d'opérations que la boucle
# d'origine — un refactor pur, validé par comparaison de logs avant/après (voir
# CHANGELOG.md v21.0).
class EtatCognitif:
    """Conteneur de tout l'état mutable qui vivait auparavant au niveau module. Les
    CONSTANTES (DOPAMINE_*, HORIZONS_PLANIFICATION, TAUX_*, seuils…) restent des
    globales de module — elles ne changent jamais et n'ont pas besoin d'être
    encapsulées ; seul l'état qui évolue au fil des jours/ticks est regroupé ici,
    pour pouvoir être sauvegardé/restauré tel quel par PersistanceAnatomique (v21.0)."""

    def __init__(self, agent, env, env_id, nom_classe):
        # --- Cerveau & moteurs ---
        self.agent = agent
        self.moteur_bio = BiologicalHomeostasisEngine(
            taux_satiete=TAUX_SATIETE, taux_hydratation=TAUX_HYDRATATION,
            taux_stimulation=TAUX_STIMULATION, seuil_critique=SEUIL_CRITIQUE_BIO,
            # v41.2 — passe la longueur RÉELLE de la journée : les taux sont exprimés par
            # journée puis divisés ici, pour que le vécu (≈3 repas/journée) soit invariant
            # entre un run de réglage à 400 ticks et un run cible à 3600.
            ticks_par_jour=ticks_par_jour,
        )  # générique, actif partout — jauges persistantes entre épisodes
        self.memoire_episodique_spatiale = MemoireEpisodiqueSpatiale(
            capacite_max=CAPACITE_MEMOIRE_EPISODIQUE, fenetre_fraicheur=FENETRE_FRAICHEUR_SOUVENIR,
        )  # générique, actif partout — persiste entre épisodes, vidée au changement de niveau

        # --- Détecteurs ---
        self.detecteur = None            # spécifique DoorKey, créé à la volée
        self.palier_cible = 1
        self.detecteur_portes = DetecteurFranchissementPortes()   # générique, actif partout
        self.detecteur_progres = DetecteurProgresPersonnel()       # générique, inactif sur DoorKey
        self.thermostat_cinetique = ThermostatCinetiqueMultimodal(
            # v41.43 — valeur de CONSTRUCTION seulement : elle sert de repli hors
            # MiniGrid. Sur une carte, `reinitialiser_episode` la remplace par
            # l'échelle dérivée du budget du monde.
            penalite_base=PENALITE_STAGNATION_FOSSILE,
            facteur_manipulation=FACTEUR_ATTENUATION_MANIPULATION,
            facteur_interaction=FACTEUR_ATTENUATION_INTERACTION,
            facteur_libre=FACTEUR_ATTENUATION_LIBRE,
        )  # générique, actif partout
        self.module_acceptation = ModuleAcceptationAbnegation(
            patience_min=PATIENCE_MIN,
            plafond_hors_monde=PLAFOND_PATIENCE_HORS_MONDE,
            fenetre_historique=FENETRE_HISTORIQUE_PATIENCE,
        )
        self.gestionnaire_cursus = GestionnaireCursusAbnegation(
            succes_par_sous_seuil=SUCCES_PAR_SOUS_SEUIL,
            coeff_abnegation_sous_seuil_2=COEFF_ABNEGATION_SOUS_SEUIL_2,
        )  # spécifique DoorKey (cursus à 7 paliers), inerte sur les autres niveaux

        # --- Cursus Développemental par Ères (v23.0) ---
        # palier_vocal : index dans professeur_gemma.CURRICULUM_VOCAL (1 = "Vocaliser").
        # gestionnaire_cursus_vocal : instance SÉPARÉE de gestionnaire_cursus ci-dessus
        # — même classe (GestionnaireCursusAbnegation, mécanisme 2+2 succès), mais
        # compteur totalement indépendant : la progression vocale ne doit jamais
        # interférer avec la progression des 7 paliers DoorKey.
        self.palier_vocal = 1
        self.gestionnaire_cursus_vocal = GestionnaireCursusAbnegation(
            succes_par_sous_seuil=SUCCES_PAR_SOUS_SEUIL,
            coeff_abnegation_sous_seuil_2=COEFF_ABNEGATION_SOUS_SEUIL_2,
        )

        self.detecteur_curiosite = DetecteurCuriositeJEPA(
            fenetre_historique=FENETRE_HISTORIQUE_CURIOSITE,
            facteur_seuil_surprise=FACTEUR_SEUIL_SURPRISE,
            micro_recompense=MICRO_RECOMPENSE_CURIOSITE,
            poids_choc=POIDS_CHOC_CURIOSITE,
        )  # générique, actif uniquement en Mode Libre
        self.sursaut_volonte = ModuleSursautVolonte(
            seuil_declenchement=SEUIL_DECLENCHEMENT_SURSAUT,
            boost_second_souffle=BOOST_SECOND_SOUFFLE,
            extension_patience=EXTENSION_PATIENCE_SURSAUT,
        )  # générique, actif uniquement en Mode Libre
        self.detecteur_ressources_bio = DetecteurRessourcesBiologiques(
            nb_sources_food=NB_SOURCES_FOOD, nb_sources_water=NB_SOURCES_WATER,
        )  # générique, actif partout
        self.lecteur_case_frontale = LecteurCaseFrontale()  # v27.0, générique, actif partout —
                                                             # sans état inter-tick, jamais réinitialisé
        # v33.0-etape0 — chronomètre de jalons (télémétrie PURE, aucun effet sur la
        # décision ni le gradient). Spécifique DoorKey comme `self.detecteur`, inerte
        # ailleurs. Voir ChronometreJalonsDoorKey pour l'enjeu de la mesure.
        self.chronometre_jalons = ChronometreJalonsDoorKey()
        # v29.0 — L'Interpréteur des 5 Sens. Générique (aucune carte ni palier codé en
        # dur), actif partout. Porte le seul état inter-tick des sens faibles : la trace
        # de goût, remise à zéro à chaque épisode (voir reinitialiser_episode).
        self.bus_sensoriel = BusSensoriel()

        # --- Dopamine ---
        self.teneur_dopamine = DOPAMINE_NEUTRE
        self.plasticite_base = 1.0

        # --- Curriculum & environnement ---
        self.env = env
        self.env_id = env_id
        # v41.10 — la mémoire spatiale doit savoir SUR QUELLE carte elle écrit dès le
        # premier tick. Sans cet amorçage, `carte_courante` resterait None et la première
        # bascule archiverait les repères de naissance sous la clé None — ils seraient
        # alors inaccessibles au retour sur la carte de départ.
        self.memoire_episodique_spatiale.carte_courante = env_id
        self.nom_classe = nom_classe
        self.niveau_actuel = 0
        self.victoires_consecutives = 0
        # v35.0 — historique glissant des épisodes du NIVEAU COURANT (1.0 = réussi).
        # Vidé à chaque promotion : un taux calculé sur des épisodes d'un niveau plus
        # facile promouvrait l'agent sans qu'il ait rien montré sur le niveau courant.
        self.historique_episodes_niveau = []
        # v41.6 (P17) — niveau réellement joué par l'épisode courant. Distinct de
        # `niveau_actuel`, qui reste le niveau de RÉFÉRENCE (celui que la promotion
        # déplace). À la naissance les deux coïncident : aucun tirage n'a encore eu lieu.
        self.niveau_episode = 0
        # v41.9 — compteur d'épisodes DEPUIS LA NAISSANCE, persisté. Il sert à dériver la
        # graine de chaque carte (voir `_graine_episode`) : c'est lui qui garantit qu'un
        # run rejoué voit la MÊME suite de mondes, tout en en voyant une NOUVELLE à
        # chaque épisode. Doit être monotone et jamais remis à zéro — un reset ferait
        # revoir les mêmes cartes qu'à la naissance.
        self.episodes_vecus = 0
        self.p17_episodes_hors_reference_jour = 0
        self.p17_victoires_hors_reference_jour = 0
        self.p17_revisions_jour = 0
        self.p17_incursions_jour = 0
        # v41.4 — historique TRANSVERSAL, jamais vidé à la promotion : c'est la « maîtrise
        # générale des cartes ». Il ne pilote que le sevrage, jamais la promotion.
        self.historique_episodes_general = []
        # v41.4 — parenté mesurée entre la carte quittée et la carte courante, calculée
        # UNE FOIS au moment de la promotion (voir `_parente_cartes`). 0.0 à la naissance :
        # il n'y a aucune carte précédente dont hériter.
        self.parente_niveau_precedent = 0.0
        # v41.4 — télémétrie : le taux effectivement utilisé pour le sevrage (mélange du
        # niveau courant et de l'héritage). Égal au taux du niveau quand l'héritage est nul.
        self.taux_sevrage_jour = 0.0
        # v35.1 — curseur d'aide, recalculé chaque `demarrer_journee`. 1.0 par défaut :
        # un cerveau qui n'a pas encore ouvert sa première journée est un débutant.
        self.facteur_guidage_jour = 1.0
        # v35.1 — jours CONSÉCUTIFS sans victoire sur le niveau courant. Remis à zéro à la
        # première victoire et à chaque promotion : c'est une bouée, jamais une rente.
        self.jours_stagnation_niveau = 0
        self.doorkey_actif = False
        self.mode_libre = False
        # v40.0 — à la naissance l'agent n'a rien vécu : f = 0, C1 SEUL. La valeur réelle
        # est relue au début de chaque journée depuis le vécu de l'agent.
        self.force_planification_jour = 0.0
        self.coeff_entropie_jour = COEFF_ENTROPIE_GUIDE

        # --- Thermostat de neurogenèse ---
        self.seuil_base, self.seuil_actuel, self.delta_max = 0.0005, 0.0005, 0.50
        # v41.24 — mémoire du RENDEMENT structurel : ce que les mutations passées ont
        # rapporté (baisse d'erreur JEPA) rapporté à ce qu'elles ont coûté (effort
        # métabolique permanent). `None` = aucune mutation encore jugée.
        self.erreur_avant_mutation = None
        self.effort_avant_mutation = None
        self.rendement_moyen = None
        self.rendement_ref = None
        self.vitalite_jour = 1.0
        self.cooldown_jours = 0
        self.jours_depuis_mutation = JOURS_ENTRE_MUTATIONS
        self.historique_erreurs = []

        # --- Compteurs de temps ---
        self.tick_absolu = 0  # au-delà de ticks_par_jour, pour la fraîcheur des souvenirs
        self.jour = 0
        self.ticks_audio_recus = 0  # v22.1 : compteur cumulatif de ticks où un son a été
                                     # réellement injecté (obs_auditive non-None) — pilote
                                     # la rampe progressive coeff_jepa_audio (voir perte_jepa,
                                     # correctif défaut 3), pour ne jamais perturber le JEPA
                                     # visuel dès le premier tick audio reçu.

        # --- v33.0-etape0.6 : CHRONOLOGIE DES VICTOIRES (télémétrie PURE) ---
        # La question que la v33 doit trancher AVANT d'écrire une ligne de Replay
        # Orienté : les victoires arrivent-elles au HASARD (processus stationnaire) ou
        # l'agent réussit-il DE MIEUX EN MIEUX (intervalles qui se resserrent) ?
        #
        # L'analyse a posteriori des logs du run 700 jours donnait des écarts de
        # 60, 38, 90, 17, 109, 217 jours — apparemment stationnaires, mais lus À LA MAIN
        # sur 7 points seulement, sans jamais survivre à une reprise de run.
        #
        # Ces champs ne sont VOLONTAIREMENT PAS dans `_reinitialiser_buffers_journee` :
        # ce sont des compteurs de VIE, pas de journée. Les y mettre les remettrait à
        # zéro chaque matin et détruirait la mesure — piège inverse de celui de
        # `score_vocal_jour` (v27.0), où un compteur journalier cumulait depuis la
        # naissance. Ici, c'est bien le cumul depuis la naissance qui est voulu.
        self.jour_derniere_victoire = None   # None = aucune victoire de toute la vie
        self.jours_depuis_victoire = 0       # 0 le jour même d'une victoire
        self.intervalles_victoires = []      # écarts successifs, en jours — voir ⚠️ ci-dessous
        self.victoires_totales = 0
        # ⚠️ v33.0-etape0.6-fix1 — LE CONTEXTE DE COMPARAISON.
        #
        # Bug diagnostiqué sur le run 78859bgs (700 jours) : la ligne affichait
        # « tendance 34.89 ↗️ s'espacent » alors que l'agent s'AMÉLIORAIT en fin de run.
        # Cause : les 5 premières victoires (jours 49-67) étaient des victoires FACILES
        # en Primaire, obtenues avant même que le Palier 7 existe. Le ratio comparait
        # donc « Primaire » à « Palier 7 » — deux tâches sans commune mesure.
        #
        # Un intervalle n'a de sens qu'entre deux victoires de MÊME DIFFICULTÉ. Le
        # contexte est donc (niveau, palier) : dès qu'il change, la série repart à zéro,
        # exactement comme `memoire_episodique_spatiale.reinitialiser_niveau()` efface
        # des coordonnées qui n'ont plus de sens sur une autre carte.
        #
        # `victoires_totales` et `jour_derniere_victoire`, eux, ne sont JAMAIS remis à
        # zéro : ils comptent une vie entière. Seule la série d'intervalles — le support
        # du ratio de tendance — est contextuelle.
        self.contexte_victoires = None       # (niveau_actuel, palier_cible) de la série courante
        self.intervalles_contexte_prec = []  # série archivée du contexte précédent (télémétrie)

        # --- État inter-tick (vivant pendant l'épisode courant) ---
        self.etat_courant = None
        self.memoire_tampon = None
        self.vecteurs_episodiques = []
        self.ticks_episode_courant = 0
        self.positions_visitees_episode = set()
        self.fin_episode = False

        # --- Port Exocortex C3 (v28.0, expérimental) --- reponse_c3_en_attente : la
        # dernière ReponseC3 reçue, pas encore appliquée au choix d'action (le bus
        # répond après coup — voir traiter_tick, appliquée au tick SUIVANT celui où
        # ACTION_DEMANDER a été jouée). None = comportement par défaut (aucune requête
        # en cours), cohérent avec l'invariance biologique pure sans plug branché.
        self.reponse_c3_en_attente = None
        # derniere_erreur_jepa : miroir de valeur_erreur du tick précédent, transmis en
        # contexte neutre dans RequeteC3 (voir port_c3.RequeteC3.erreur_jepa) — un plug
        # sait ainsi "à quel point le monde surprend l'agent" sans jamais recevoir de
        # gradient ni d'objet PyTorch.
        self.derniere_erreur_jepa = 0.0

        # --- Buffers de gradient / accumulateurs de la journée subjective ---
        self._reinitialiser_buffers_journee()

    def _reinitialiser_buffers_calibrage(self):
        """v41.2-fix — les compteurs de calibrage v34, remis à zéro CHAQUE NUIT.

        ⚠️ Bug corrigé ici : ces champs portaient le suffixe `_jour` et leur commentaire
        d'origine invoquait explicitement « le piège du bug `score_vocal_jour` v27.0 » —
        mais ils n'étaient initialisés qu'une fois, dans `__init__`, et jamais réarmés.
        `jauge_min_satiete_jour` était donc le minimum **depuis la naissance**, et
        `ticks_deficit_critique_jour` un cumul monotone : d'où les « 400/400 ticks en zone
        critique » lus sur les runs, qui surestimaient la détresse réelle du jour.
        Le commentaire décrivait le piège, le code le contenait — troisième occurrence du
        fil n°3 de l'INDEX (« un invariant en commentaire finit par être violé »).
        """
        # 1. Distribution de l'effort réel par tick — l'échelle du futur taux de fatigue.
        self.effort_min_jour = None
        self.effort_max_jour = 0.0
        self.effort_par_action_jour = {a: [0, 0.0] for a in range(7)}  # [n_ticks, somme]
        # 2. Déficit homéostatique : combien de temps l'agent passe en zone critique.
        self.deficit_cumul_jour = 0.0
        self.deficit_max_jour = 0.0
        self.ticks_deficit_critique_jour = 0
        # 3. Autonomie des jauges — LE critère de sevrage du soin parental (§3.3) :
        #    un agent qui maintient ses jauges seul n'a plus besoin qu'on le nourrisse.
        self.ticks_jauges_saines_jour = 0
        self.jauge_min_satiete_jour = 1.0
        self.jauge_min_hydratation_jour = 1.0
        self.jauge_min_stimulation_jour = 1.0
        # v41.2 — télémétrie du second étage. Une mécanique non instrumentée est
        # indémontrable sur un run long (leçon v29.1) : l'énergie module désormais TOUTE
        # la décision, elle doit donc être lisible nuit par nuit.
        self.energie_cumul_jour = 0.0
        self.energie_min_jour = 1.0
        self.vigueur_cumul_jour = 0.0
        self.vigueur_min_jour = 1.0
        self.ticks_energie_basse_jour = 0
        # v41.2-fix7 — le soulagement réellement obtenu en mangeant, crédité au geste.
        # C'est la mesure de la boucle corporelle : si ce total reste proche de zéro alors
        # que l'agent mange, c'est qu'il mange sans en avoir besoin.
        self.soulagement_repas_jour = 0.0
        # 4. Ressources réellement disponibles — §7.4, BLOQUANT pour l'Étape 3 : rendre
        #    l'agent mortel sur une carte sans nourriture serait le condamner d'office.
        self.ressources_vues_jour = 0
        self.ticks_avec_odeur_jour = 0

    def _reinitialiser_buffers_journee(self):
        self._reinitialiser_buffers_calibrage()
        # v41.6 (P17) — compteurs de distribution du cursus. Réarmés ici comme tout buffer
        # journalier : sans cela ils cumuleraient depuis la naissance et la « part de
        # révision du jour » serait en réalité la part depuis toujours (piège du bug
        # `score_vocal_jour` v27.0, et de `jauge_min_satiete_jour` v41.2).
        self.p17_revisions_jour = 0
        self.p17_incursions_jour = 0
        self.p17_episodes_hors_reference_jour = 0
        self.p17_victoires_hors_reference_jour = 0
        self.memoire_moyen_terme = []
        self.jepa_losses, self.log_probs_journee, self.entropies_journee = [], [], []
        # v41.31 — vidé ICI avec les autres buffers journaliers. S'il ne l'était pas, il
        # grossirait d'un jour à l'autre et désalignerait le masque de `log_probs`
        # (piège du compteur non réinitialisé, v27.0 et v37.1).
        self.transitions_journee = []
        # v41.48 — buffer du rendement mécanique, STRICTEMENT aligné sur
        # `transitions_journee` et `log_probs_journee` (un élément par tick joué).
        self.rendements_journee = []
        self.valeurs_journee, self.recompenses_journee, self.dones_journee = [], [], []
        # v37.1 — chocs dopaminergiques tick par tick, pour le crédit rétrograde de la
        # distillation sélective. Remis à zéro ici comme tout buffer journalier (piège du
        # compteur cumulé depuis la naissance, bug `score_vocal_jour` v27.0).
        self.chocs_dopamine_journee = []
        # v22.1 (correctif défaut 1, CRITIQUE) : buffer de la perte MSE supervisée qui
        # donne enfin un vrai gradient à tete_vocale — voir traiter_tick et
        # apprendre_journee. Avant ce fix, parametres_vocaux était détaché avant tout
        # calcul de score, donc la bouche ne recevait jamais d'erreur dirigée vers la
        # cible (uniquement LTP hebbien + rêve, jamais un gradient de régression).
        self.pertes_vocales = []

        self.erreur_journee = 0.0
        self.victoire_aujourdhui = False
        self.episodes_jour = 0
        self.succes_palier_cible_jour = 0
        self.guidage_but_journee = 0.0
        self.portes_franchies_jour = 0
        self.progres_personnel_jour = 0
        self.penalite_stagnation_jour = 0.0
        self.sous_objectifs_curiosite_jour = 0
        self.r_bio_jour = 0.0
        self.effort_metabolique_jour = 0.0

        # --- v41.32-etape1 : LA SONDE DE MIXAGE (télémétrie PURE, aucun effet) ---
        # Le point d'assemblage de la récompense est UNIQUE dans tout le fichier : les
        # onze termes y sont sommés à poids 1 (voir `recompense_interne`). C'est le
        # dernier gros coefficient posé du projet — mais avant de le remplacer par quoi
        # que ce soit, il faut savoir ce que chaque terme PÈSE et surtout ce qu'il
        # VARIE. Un terme constant, si gros soit-il, n'apprend rien au gradient : c'est
        # la dispersion qui porte le signal, pas la moyenne.
        #
        # ⚠️ Cinq des onze termes avaient déjà un cumul (`r_bio_jour`,
        # `penalite_stagnation_jour`, `guidage_but_journee`…), mais TROIS autres
        # comptaient des ÉVÉNEMENTS et non des AMPLITUDES : `portes_franchies_jour`,
        # `progres_personnel_jour` et `sous_objectifs_curiosite_jour` répondent à
        # « combien de fois ? », jamais à « combien de récompense ? ». Un terme fréquent
        # à trois fois rien et un terme rare mais massif avaient donc le même compteur.
        #
        # Méthode : trois scalaires par terme (n, Σx, Σx²), moyenne ET écart-type
        # reconstruits la nuit. Surtout PAS de liste tick par tick — 1500 jours × 400
        # ticks × 11 termes = 6,6 M de flottants Python pour un résultat obtenable en
        # O(1) mémoire. Coût mesuré par tick : 11 additions + 11 multiplications, contre
        # un forward réseau + un rollout C2 sur 7 actions (< 0,01 % du tick).
        #
        # Remis à zéro ICI comme tout buffer journalier — piège `score_vocal_jour` v27.0,
        # rappelé en tête de cette méthode : un compteur créé à la volée par getattr()
        # sans réarmement cumulerait depuis la NAISSANCE du cerveau, et la « moyenne du
        # jour » serait en réalité la moyenne de toute la vie.
        self.mix_n = 0
        self.mix_somme = {}
        self.mix_somme_carres = {}

        # --- v41.32-etape2 : LA SONDE DE FOURRAGE (télémétrie PURE) ---
        # Mesure la CONJONCTION « être en face d'une ressource » ET « jouer le geste ».
        # Voir `_sonder_fourrage` pour le détail de ce que chaque compteur distingue.
        # Réarmés ici comme tout buffer journalier (piège `score_vocal_jour` v27.0).
        # --- v41.32-etape4 : LA SONDE DE DISCRIMINATION (télémétrie PURE) ---
        # Distribution des 7 actions quand `contact_frontal = 1`, séparément selon que la
        # case frontale porte un MUR ou une RESSOURCE. Voir `_sonder_discrimination`.
        self.discrim_actions_mur = {}
        self.discrim_actions_ressource = {}

        self.fourrage_occasions_jour = 0
        self.fourrage_saisies_jour = 0
        self.fourrage_tentatives_jour = 0
        self.fourrage_faim_aux_occasions = 0.0
        self.food_consommes_jour = 0
        self.water_consommes_jour = 0

        # --- v37.0 : TÉLÉMÉTRIE DE L'ÉQUILIBRE C1/C2 ---
        # Sans ces compteurs, l'équilibrage serait invisible sur un run long et son
        # utilité indémontrable (leçon v29.1 : les 5 sens livrés sans aucune télémétrie).
        # Accumulés dans traiter_tick, agrégés dans executer_nuit.
        self.amplitude_c1_jour = 0.0     # vigueur brute du réflexe, AVANT réamplification
        self.amplitude_c2_jour = 0.0     # vigueur de la délibération, après confiance
        self.accord_c1c2_jour = 0        # ticks où les deux voix désignent la même action
        # v41.14 — QUI vote QUOI. Sans cet histogramme, `accord_c1c2_jour` est
        # ininterprétable : deux voix figées sur la même action donnent 100 % d'accord
        # sans qu'aucune délibération n'ait lieu (mesuré le 17/08).
        self.votes_c1_jour = {}
        self.votes_c2_jour = {}
        # v41.19 — sonde du coût moteur réel (étape 1). Réarmée ici comme tout buffer
        # journalier : sans cela la « distribution du jour » serait la distribution depuis
        # la naissance (piège `score_vocal_jour` v27.0, rappelé en tête de cette méthode).
        self.cout_moteur_reel_jour = {}
        self.gain_c1_jour = 0.0          # facteur de réamplification appliqué (1.0 = intact)
        self.ticks_arbitrage_jour = 0    # dénominateur commun des quatre lignes ci-dessus

        # --- v34.0-etape0 (TÉLÉMÉTRIE PURE, aucun effet sur la décision) ---
        # Mesures préalables au chantier Fatigue/Mortalité/Soin parental. Aucune de ces
        # valeurs n'est lue par penser(), par le gradient ou par la dopamine : elles ne
        # font que compter ce qui se passe déjà, pour CALIBRER avant d'écrire la moindre
        # mécanique (doctrine v30.1, et leçon v33 : une prémisse non mesurée coûte un
        # cycle entier). Voir docs/ameliorations/CONCEPTION_v34_fatigue_mortalite.md §5, Étape 0.
        #
        # ⚠️ Tous ces compteurs DOIVENT rester ici : un compteur journalier créé par
        # getattr(etat, "...", 0) sans remise à zéro cumulerait depuis la naissance
        # (piège du bug `score_vocal_jour` v27.0).
        #
        self._reinitialiser_buffers_calibrage()

        # --- v36.0 : flux enrichi & abstraction par récurrence ---
        # `ecritures` compte les repères créés OU confirmés — c'est la mesure du flux
        # réellement reçu par la mémoire (2 types seulement avant cette version).
        # `rappels_marquants` compte les ticks où un repère chargé a effectivement pesé
        # dans le vecteur bio : si ce compteur reste à 0, le canal ne sert à rien.
        self.memoire_ecritures_jour = 0
        self.memoire_rappels_marquants_jour = 0
        self.memoire_valence_cumul_jour = 0.0
        self.abandons_patience_jour = 0
        self.sursauts_jour = 0
        self.a_utilise_sursaut_episode = False
        # v25.0 (Paradigme Bébé, expérimental) : compteur net du Module "Parent" —
        # incrémenté par "Oui !", décrémenté par "Non !" (voir
        # _appliquer_feedback_parent_vocal), neutre (0) tant que parent_actif=False.
        self.feedback_parent_jour = 0

        # v27.0 (correctif) : score_vocal_jour/ticks_vocaux_jour étaient créés à la volée
        # par getattr(etat, "...", 0) dans les deux chemins de tick mais JAMAIS remis à
        # zéro — la "moyenne du jour" lue par _promouvoir_palier_vocal_si_merite était en
        # réalité la moyenne cumulée depuis la naissance du cerveau. Effet observé :
        # inertie du dénominateur qui croît sans fin → plus aucune promotion vocale
        # possible passé quelques centaines de jours, quel que soit le progrès réel de la
        # journée. NE PAS vider ces deux champs dans executer_nuit : la promotion les lit
        # APRÈS executer_nuit (voir cursus_bebe.py/cursus_developpemental.py/
        # cursus_parole.py, appelés dans cet ordre : executer_nuit puis
        # _promouvoir_palier_vocal_si_merite) — _reinitialiser_buffers_journee (appelée
        # par demarrer_journee, donc au DÉBUT du jour suivant) est le seul emplacement
        # correct.
        self.score_vocal_jour = 0.0
        self.ticks_vocaux_jour = 0
        # v27.0 — télémétrie du score mixte formants+spectral et de la dopamine unifiée
        # (voir _evaluer_production_vocale et le bloc DOPAMINE UNIFIÉE de traiter_tick),
        # loggées dans executer_nuit pour permettre le recalibrage empirique de
        # POIDS_DOPAMINE_VOCAL/POIDS_RECOMPENSE_SPECTRALE.
        # v28.0 (expérimental) — télémétrie du Port Exocortex C3, neutre (0) sur tout
        # run n'ayant enregistré aucun plug sur port_c3.
        self.dopamine_poids_c3_jour = 0.0
        self.requetes_c3_jour = 0
        self.reponses_c3_jour = 0
        # v29.1 (expérimental) — TÉLÉMÉTRIE DES 5 SENS (voir bus_sensoriel.py).
        # Purement observationnelle : ces compteurs ne sont JAMAIS relus par la décision,
        # le gradient ou la dopamine — uniquement agrégés dans executer_nuit. Sans eux,
        # un run de 300 jours ne permettrait pas de répondre à "l'odorat a-t-il jamais
        # servi ?" ni de détecter une désactivation silencieuse du bus (dégradation
        # gracieuse : un seul avertissement console, vite noyé dans les logs).
        # Les deux sens gourmands (vue, ouïe) sont déjà suivis indirectement par
        # Erreur_JEPA et les scores vocaux — ce bloc couvre les 3 sens ajoutés en v29.0.
        self.ticks_sensoriels_jour = 0        # dénominateur des ratios ci-dessous
        self.toucher_contact_jour = 0         # ticks avec un obstacle devant l'agent
        self.toucher_portage_jour = 0         # ticks avec un objet en main (la clé...)
        self.odorat_cumul_jour = 0.0          # somme des intensités (food + eau)
        self.odorat_max_jour = 0.0            # pic d'intensité de la journée
        self.odorat_ticks_actifs_jour = 0     # ticks où au moins une odeur > 0
        self.gout_ticks_actifs_jour = 0       # ticks où une trace gustative persiste
        # v32.0 (expérimental) — TÉLÉMÉTRIE DE L'ODORAT TOPOLOGIQUE & DE LA CLINOTAXIE.
        # `odorat_ticks_approche_jour` est LA métrique décisive de cette version, dans le
        # même esprit que `Sursaut_Taux_Victoire` en v30.1 : le projet saura enfin si
        # l'agent SUIT réellement le gradient olfactif, et pas seulement s'il le perçoit.
        # Un taux durablement voisin de 50 % signifierait que la clinotaxie n'oriente
        # rien (l'agent monte et descend le gradient au hasard) — auquel cas ces 2 dims
        # seraient à remettre en cause, exactement comme les 182 doublons de la v31.1.
        self.odorat_delta_cumul_jour = 0.0    # somme des |ΔS| (amplitude des variations)
        self.odorat_ticks_approche_jour = 0   # ticks où ΔS > 0 sur au moins un type
        self.odorat_ticks_variation_jour = 0  # dénominateur : ticks avec ΔS non nul
        # v41.11 — THERMOCEPTION. Réarmés ici comme tout compteur journalier : les laisser
        # cumuler depuis la naissance ferait passer « la chaleur moyenne du jour » pour la
        # chaleur moyenne d'une vie (piège `score_vocal_jour` v27.0).
        # v41.25 — compteurs de survie. Remis à zéro ICI, jamais seulement par getattr :
        # c'est le piège `score_vocal_jour` (v27.0), où « la moyenne du jour » cumulait
        # en réalité depuis la naissance.
        self.morts_jour = 0
        self.episodes_gagnes_jour = 0
        self.episodes_epuises_jour = 0
        self.chaleur_a_la_mort_jour = 0.0
        # v41.26 — la douleur EFFECTIVEMENT ressentie (après gradation), distincte de la
        # chaleur brute : c'est elle qui entre dans le déficit. Sans ce compteur, on ne
        # saurait pas si le palier 1 produit bien un vrai zéro.
        self.douleur_cumul_jour = 0.0
        self.douleur_max_jour = 0.0
        self.douleur_ticks_actifs_jour = 0
        # v41.27 — la douleur UNIQUE (thermique + mécanique) et ses causes.
        self.douleur_corp_cumul_jour = 0.0
        self.douleur_corp_max_jour = 0.0
        self.chocs_muraux_jour = 0
        self.ticks_perdus_mort_jour = 0
        self.mort_du_jour = False
        self.chaleur_cumul_jour = 0.0         # somme des intensités thermiques du jour
        self.chaleur_max_jour = 0.0           # pic de chaleur ressenti
        self.chaleur_ticks_actifs_jour = 0    # ticks où un danger est perceptible
        self.chaleur_ticks_approche_jour = 0  # ticks où la chaleur MONTE (l'agent approche)
        self.chaleur_ticks_variation_jour = 0 # dénominateur : ticks avec Δ non nul
        # v41.12 — TOUCHER À DISTANCE (pression + asymétrie). Actifs sur toute carte.
        # v41.13 — ventilation JEPA (étape 1 de la confrontation multimodale).
        self.jepa_concentration_cumul_jour = 0.0
        self.jepa_amplitude_cumul_jour = 0.0
        self.jepa_err_max_dim_jour = 0.0
        self.pression_cumul_jour = 0.0        # encombrement moyen vécu dans la journée
        self.pression_max_jour = 0.0          # pic (cul-de-sac)
        self.asymetrie_ecart_cumul_jour = 0.0 # |asym - 0.5| : le signal latéral porte-t-il ?
        self.odorat_sources_inodores_jour = 0 # ticks où une source existe mais est
                                              # inatteignable (BFS) : mesure ce que la
                                              # topologie v32.0 a cessé de faire traverser
        # v30.0 — L'EXO-SENS (6ème sens). Même discipline que ci-dessus : purement
        # observationnel, jamais relu par la décision. `perceptions_exo_jour` compte les
        # RAFRAÎCHISSEMENTS réels du bus (un tick sur PERIODE_PERCEPTION_EXO), pas les
        # ticks où le vecteur est utilisé — c'est la mesure du coût externe réellement payé.
        self.perceptions_exo_jour = 0
        self.exo_ticks_actifs_jour = 0        # ticks où Z_exogène n'est pas nul
        self.exo_cumul_jour = 0.0             # somme des normes L1 moyennes du vecteur
        self.exo_max_jour = 0.0               # pic d'intensité perçue

        # --- v30.1 : INSTRUMENTATION AVANT CALIBRAGE (mémoire épisodique & sursaut) ---
        # Ces compteurs ne changent AUCUN comportement : ils mesurent deux mécaniques
        # actuellement pilotées par des constantes arbitraires (`capacite_max=200`,
        # `EXTENSION_PATIENCE_SURSAUT=50`) que l'on veut rendre adaptatives. Les mesurer
        # d'abord évite de remplacer un chiffre arbitraire par une FORMULE arbitraire —
        # c'est la leçon de la v29.1 (5 sens livrés sans télémétrie, écart corrigé après
        # coup). Objectif : disposer de courbes réelles pour calibrer, puis DÉMONTRER que
        # l'adaptatif fait mieux que le fixe.
        #
        # Mémoire épisodique — la question posée : la saturation à 200 coûte-t-elle
        # quelque chose ? Un rappel qui reste bon à saturation prouverait que la capacité
        # n'est pas le facteur limitant.
        self.memoire_rappels_tentes_jour = 0   # appels à recuperer_contexte avec une quête active
        self.memoire_rappels_reussis_jour = 0  # ... ayant trouvé un souvenir du bon type
        self.memoire_distance_cumul_jour = 0.0 # somme des distances normalisées (1.0 = sur place)
        self.memoire_fraicheur_cumul_jour = 0.0
        # Sursaut de volonté — la question posée : dans quel sens doit varier l'extension ?
        # Un sursaut qui débouche souvent sur une victoire mérite d'être renforcé
        # (« muscle »), un sursaut stérile mérite de s'atténuer (« habituation »). Sans
        # ce taux, impossible de trancher autrement qu'à l'intuition.
        self.sursauts_suivis_victoire_jour = 0
        self.sursauts_suivis_echec_jour = 0
        # v33.0-etape0 — CHRONOMÉTRIE DES JALONS DOORKEY (voir ChronometreJalonsDoorKey).
        # Purement observationnelle : jamais relue par la décision, le gradient ou la
        # dopamine. Chaque delta a son propre dénominateur, car un épisode peut fournir
        # Δt1 sans jamais fournir Δt3 — moyenner sur un dénominateur commun mélangerait
        # « le segment est lent » et « le segment n'est jamais atteint », les deux
        # diagnostics que cette mesure doit justement séparer.
        self.jalon_delta1_cumul_jour = 0    # reset → prise de la clé
        self.jalon_delta1_n_jour = 0
        self.jalon_delta2_cumul_jour = 0    # clé → déverrouillage
        self.jalon_delta2_n_jour = 0
        self.jalon_delta3_cumul_jour = 0    # déverrouillage → sortie (le « désert » présumé)
        self.jalon_delta3_n_jour = 0
        self.jalon_ressources_post_cle_jour = 0  # conflit viscéral : manger clé en main
        self.jalon_episodes_doorkey_jour = 0     # dénominateur des taux d'atteinte
        self.score_formants_jour = 0.0
        self.score_spectral_jour = 0.0
        self.dopamine_poids_visuel_jour = 0.0
        self.dopamine_poids_vocal_jour = 0.0
        # v27.0 — cache du canal spectral (voir _evaluer_production_vocale et
        # PERIODE_EVAL_SPECTRALE) : force une évaluation dès le 1er tick vocal du jour.
        self._tick_dernier_spectral = -10_000_000
        self._dernier_score_spectral_mfcc = None


def initialiser_etat_cognitif():
    """Naissance d'un nouveau cerveau (bus=16) et de tout son écosystème de détecteurs.
    Utilisée par le mode standalone ET par PersistanceAnatomique.charger_ou_naitre()
    quand aucun fichier .brain n'existe encore (v21.0)."""
    agent = AGI_Naulthene(dim_visuelle=DIM_VISUELLE, dim_bus=BUS_REFERENCE_INITIAL).to(DEVICE)
    env_id, nom_classe = ((ENV_FORCE, "Banc de mesure (env forcé)")
                          if ENV_FORCE else PROGRAMME[0])
    env = creer_env(env_id, DIM_VISUELLE)
    print(f"\n🎒 Rentrée des classes : L'Agent démarre en {nom_classe}...")
    return EtatCognitif(agent, env, env_id, nom_classe)


def _memoriser_si_saillant(etat, intensite: float) -> bool:
    """v36.0 — LE FLUX ENRICHI : tout événement marquant devient un repère spatial.

    Remplace les deux seuls points d'entrée historiques (FOOD, WATER) par un canal
    générique : n'importe quel tick dont la charge dépasse le bruit de fond laisse une
    trace à l'endroit où il s'est produit.

    ⚠️ AUCUN TYPE N'EST NOMMÉ. L'étiquette est dérivée de ce que l'agent a **sous les
    pieds**, via l'API MiniGrid (`objet.type`), et reste une chaîne OPAQUE : le code ne
    contient nulle part « lave = danger » ou « clé = utile ». Deux expériences au même
    endroit sur le même type se confirment mutuellement, et c'est tout — la valeur de ce
    type est apprise par accumulation dans `valence`, jamais déclarée.

    Le seuil de saillance n'est pas un « seuil de décision » au sens que `CLAUDE.md`
    interdit (il ne pilote aucun choix d'action) : c'est un plancher d'ENREGISTREMENT,
    l'équivalent du bruit de fond en deçà duquel une expérience ne mérite pas d'être
    retenue. Sans lui, les 400 ticks de chaque journée entreraient tous, et la mémoire ne
    contiendrait plus que du bruit.

    Retourne True si un repère a été écrit ou confirmé.
    """
    if not _MINIGRID_INTERNALS_OK or abs(intensite) < SEUIL_SAILLANCE_MEMOIRE:
        return False
    try:
        noyau_env = etat.env.unwrapped
        position = tuple(int(v) for v in noyau_env.agent_pos)
        # L'étiquette vient de la case OCCUPÉE (le but, la lave…) ou, à défaut, de ce que
        # l'agent tient. Sur une case vide sans rien en main, l'événement est rattaché au
        # sol : l'endroit lui-même devient le repère (« ici il se passe quelque chose »).
        objet = noyau_env.grid.get(*position)
        if objet is not None:
            etiquette = getattr(objet, "type", "sol")
        elif getattr(noyau_env, "carrying", None) is not None:
            etiquette = f"porte_{getattr(noyau_env.carrying, 'type', 'objet')}"
        else:
            etiquette = "sol"
        etat.memoire_episodique_spatiale.enregistrer_evenement(
            position, etiquette, etat.tick_absolu, intensite=intensite
        )
        etat.memoire_ecritures_jour += 1
        return True
    except Exception:
        return False


# --- v41.6 : P17 — LE CURSUS COMME DISTRIBUTION, PLUS COMME POINTEUR ---
#
# Décision utilisateur (P17, formulée le 14/08) : *« Tu fais 3×3 vingt fois, puis 4×4 cinq
# fois, puis 3×3 deux fois, comme ça aléatoirement — mais tant que le 3×3 n'est pas réussi,
# tu ne vas pas au-delà du 5×5, sauf exceptionnellement. Tu peux le présenter sous forme de
# gaussienne : chaque étape à valider est en haut de la courbe. »*
#
# 🔴 CE QUE ÇA REMPLACE. `niveau_actuel` était un POINTEUR : on jouait ce niveau et rien
# d'autre. Mesuré sur les runs de 2000 jours : g44 promu au niveau 3 (`Empty-8x8`) s'y
# effondre à **2 % de maîtrise** et y reste **1500 jours**, sans jamais rejouer les deux
# niveaux qu'il maîtrisait. Un pointeur qui ne recule jamais transforme le moindre mur en
# cul-de-sac définitif.
#
# LA FORME. Le niveau joué est TIRÉ AU SORT à chaque épisode, autour du niveau de
# référence. Trois propriétés tombent alors sans un seul `if` :
#   • les retours en arrière — la queue gauche de la distribution
#   • « pas au-delà tant que ce n'est pas acquis » — le sommet ne bouge qu'avec la maîtrise
#   • « sauf exceptionnellement » — la queue droite est fine, jamais nulle
#
# ⚠️ LES PROPORTIONS SONT DÉRIVÉES, JAMAIS POSÉES. La formulation initiale proposait
# 65 % / 15 % / 20 % (défi / révision / incursion). Trois constantes en dur auraient
# remplacé un pointeur rigide par trois chiffres arbitraires — exactement ce que le projet
# refuse (« remplacer un chiffre arbitraire par une formule arbitraire ne vaut pas mieux »,
# méthode v30.1). Ces trois valeurs sont donc devenues le **point de passage** de la courbe
# à `TAUX_PROMOTION`, et non son socle :
#
#   maîtrise 0 %   → l'agent ne sait rien : il révise beaucoup, n'explore rien
#   maîtrise 60 %  → 65 / 15 / 20, le point demandé
#   maîtrise 90 %  → il s'ennuie ici : l'incursion domine
#
# La largeur de la distribution suit `1 − maîtrise` : un agent qui maîtrise reste concentré,
# un agent qui échoue s'étale vers ce qu'il sait faire. C'est la même doctrine que le rêve
# adaptatif (le pourcentage rejoué émerge de la plasticité × richesse).
#
# INVARIANT DE MESURE : seuls les épisodes joués SUR LE NIVEAU DE RÉFÉRENCE alimentent
# `historique_episodes_niveau`. Créditer une révision réussie sur `Empty-5x5` au compte du
# niveau 3 gonflerait la maîtrise et promouvrait un agent qui n'a rien montré là où il
# fallait — c'est le défaut que l'invariant « vider la fenêtre à la promotion » existe pour
# empêcher, et P17 le réintroduirait par une autre porte.
POIDS_REVISION_REFERENCE = 0.15    # point de passage à TAUX_PROMOTION (formulation P17)
POIDS_INCURSION_REFERENCE = 0.20   # idem — le défi occupe le reste
ETALEMENT_MAX_CURSUS = 2.5         # borne : au pire, la révision porte ~2-3 paliers en arrière


# --- v41.9 : LE BANC D'ESSAI DEVIENT REPRODUCTIBLE ---
#
# 🔴 LE DÉFAUT. `env.reset()` était appelé **sans graine** aux trois points du fichier
# (0 occurrence de `reset(seed=` avant cette version). Or MiniGrid possède son PROPRE
# générateur, initialisé sur l'entropie système : `torch.manual_seed`, `np.random.seed` et
# `random.seed` n'ont **aucun effet** dessus.
#
# Mesuré, même processus, les trois générateurs Python semés à 11 avant chaque essai :
#
#     reset()          → agent en (1,2), puis (2,4), puis (2,2)   ← 3 mondes différents
#     reset(seed=11)   → agent en (4,2), (4,2), (4,2)             ← identique
#
# Conséquence : **deux runs de même `--graine` voyaient des cartes différentes**, et
# divergeaient dès le jour 1 (maîtrise 45 % contre 50 % sur un run de 3 jours). Toute
# comparaison « même graine, seul le correctif change » était donc caduque — les deux
# branches différaient aussi par le monde. Le « bruit natal » attribué aux graines depuis
# des semaines était, au moins en partie, un bruit de BANC D'ESSAI.
#
# ⚠️ CE QUE CE CORRECTIF CHANGE POUR LE PROJET. Les cartes tirées ne sont plus les mêmes
# qu'avant la v41.9 : **les chiffres antérieurs ne sont pas comparables aux suivants**.
# C'est un coût accepté une fois, en échange de la seule chose qui manquait — la capacité
# de savoir si une modification a un effet.
#
# LA FORME. La graine de chaque carte est dérivée de deux grandeurs déjà existantes :
# la graine du run et le numéro d'épisode depuis la naissance. Elle est donc REPRODUCTIBLE
# (même run → même suite de mondes) et VARIÉE (chaque épisode → un monde neuf).
#
# Le multiplicateur écarte les suites de deux graines voisines : sans lui, la graine 11 à
# l'épisode 1 et la graine 12 à l'épisode 0 tireraient la même carte, et deux « individus »
# de la population partageraient une partie de leur vécu.
GRAINE_ECART_ENTRE_RUNS = 1_000_003   # premier : évite tout recouvrement entre graines


def _graine_episode(etat) -> int:
    """v41.9 — Graine de la carte du prochain épisode. Reproductible et variée.

    Bornée à 2**31-1 : gymnasium refuse les graines plus grandes.
    """
    base = getattr(etat, "graine_run", 0) * GRAINE_ECART_ENTRE_RUNS
    return int((base + getattr(etat, "episodes_vecus", 0)) % (2**31 - 1))


def _reset_seede(etat):
    """v41.9 — `env.reset()` avec la graine dérivée, et incrément du compteur.

    UNIQUE point de reset d'épisode du fichier : centraliser évite qu'un futur appel
    oublie la graine et rétablisse silencieusement le défaut corrigé ici.
    """
    graine = _graine_episode(etat)
    etat.episodes_vecus = getattr(etat, "episodes_vecus", 0) + 1
    return etat.env.reset(seed=graine)


def _budget_natif_carte(env, defaut: int = PLAFOND_PATIENCE_HORS_MONDE) -> int:
    """v41.8 — Le nombre de pas que l'ENVIRONNEMENT accorde réellement à un épisode.

    MiniGrid termine l'épisode à `max_steps` quoi qu'il arrive : toute patience
    au-dessus de cette valeur est inopérante. Le projet ne lisait pas cette grandeur —
    d'où une patience de 119 à 329 ticks sur une carte qui en accorde 100.

    Lecture défensive : un monde non-MiniGrid (vocal isolé, rêve) n'expose pas
    `max_steps`, on retombe alors sur la borne historique.
    """
    try:
        budget = int(getattr(env.unwrapped, "max_steps", 0) or 0)
        return budget if budget > 0 else defaut
    except Exception:
        return defaut


def _patience_budget(etat, patience_courante: int) -> int:
    """v41.8 — Ramène la patience dans le budget réel de la carte, part d'autant plus
    grande que l'agent maîtrise MOINS (« muscler dès le plus jeune âge »).

    ⚠️ L'inversion est le point essentiel. L'ancienne formule
    (`potentiometre = 0.7 × taux_succes`) donnait 119 ticks au débutant et 329 à
    l'expert : elle retirait du temps précisément à qui en avait besoin. Ici, un agent
    sans maîtrise reçoit **l'épisode entier**, et ne s'en voit retirer qu'à mesure qu'il
    démontre ne plus en avoir besoin — même doctrine que le sevrage de l'aide (v41.3).
    """
    budget = _budget_natif_carte(etat.env)
    taux = _taux_maitrise_niveau(etat)
    # « Pas encore mesurable » ⇒ régime débutant : le bénéfice du doute va au temps.
    maitrise = 0.0 if taux is None else max(0.0, min(1.0, taux))

    part = PATIENCE_PLANCHER_BUDGET + PATIENCE_MARGE_BUDGET * (1.0 - maitrise)
    cible = int(round(budget * part))

    # v41.8-fix1 — la cible est un PLANCHER, pas une substitution.
    #
    # En remplaçant la valeur, on effaçait la modulation par l'envie et par le thermostat.
    # En la bornant par le bas, on garantit ce qui compte — « le débutant a droit à
    # l'épisode entier » — tout en laissant les autres mécaniques accorder DAVANTAGE si
    # elles le jugent utile. Le plafond reste le budget natif : au-delà, toute patience
    # est inopérante puisque `max_steps` coupe l'épisode.
    return max(PATIENCE_MIN, min(budget, max(cible, int(patience_courante))))


def _distribution_cursus(etat):
    """v41.6 (P17) — Poids de tirage de chaque niveau, dérivés de la maîtrise mesurée.

    Retourne `(niveaux, poids)` normalisés, bornés à `[0, len(PROGRAMME) - 1]`.

    Rien n'est posé : les trois masses (révision / défi / incursion) sont calculées à
    partir du seul taux de maîtrise du niveau de référence, et coïncident avec la
    formulation P17 (15 / 65 / 20) quand ce taux vaut `TAUX_PROMOTION`.
    """
    ref = etat.niveau_actuel
    dernier = len(PROGRAMME) - 1

    taux = _taux_maitrise_niveau(etat)
    # « Pas encore mesurable » ⇒ traité comme un débutant : c'est le régime prudent, il
    # révise et n'explore pas. Même garde que `facteur_guidage`.
    maitrise = 0.0 if taux is None else max(0.0, min(1.0, taux))

    # Progression vers la promotion, dans [0, 1] : 1.0 = l'agent est promouvable ici.
    avancement = min(1.0, maitrise / TAUX_PROMOTION) if TAUX_PROMOTION > 0 else 1.0

    # RÉVISION — maximale quand l'agent échoue, elle s'efface quand il maîtrise.
    # À l'avancement de référence (1.0), elle vaut exactement POIDS_REVISION_REFERENCE.
    poids_revision = POIDS_REVISION_REFERENCE + (1.0 - avancement) * (1.0 - POIDS_REVISION_REFERENCE)
    # INCURSION — faible chez le débutant (rien à explorer si les bases ne tiennent pas),
    # elle croît avec la maîtrise et dépasse la référence quand l'agent s'ennuie ici.
    # Elle n'est JAMAIS nulle : c'est le « sauf exceptionnellement » de P17, et c'est aussi
    # ce qui permet à un agent bloqué de découvrir que le palier suivant lui conviendrait
    # mieux (mesuré : `Empty-Random-6x6` est parfois plus facile que `Empty-5x5`).
    # Le facteur vaut exactement 1 à l'avancement de référence (`avancement = 1`,
    # `maitrise = TAUX_PROMOTION`), de sorte que l'incursion y vaille précisément
    # `POIDS_INCURSION_REFERENCE` — le 20 % demandé par P17. En deçà elle se réduit sans
    # jamais s'annuler, au-delà elle croît avec l'ennui.
    _croissance = (0.15 + 0.85 * avancement) * (1.0 + maitrise) / (1.0 + TAUX_PROMOTION)
    poids_incursion = POIDS_INCURSION_REFERENCE * _croissance

    # ⚠️ LE DÉFI NE DESCEND JAMAIS SOUS SA MOITIÉ DE RÉFÉRENCE. Sans ce plancher, un agent
    # à 0 % de maîtrise voyait son propre palier tomber à **2 %** des tirages : il ne
    # pouvait alors plus jamais y progresser, et P17 l'aurait enfermé dans la révision au
    # lieu de l'en sortir. Le plancher est DÉRIVÉ du point de passage P17, pas posé.
    defi_reference = 1.0 - POIDS_REVISION_REFERENCE - POIDS_INCURSION_REFERENCE   # 0,65
    poids_defi = max(defi_reference * 0.5, 1.0 - poids_revision - poids_incursion)

    # Renormalisation : le plancher du défi peut faire dépasser 1, la révision doit alors
    # céder la place (jamais l'incursion, qui est déjà la plus fine des trois).
    total_masses = poids_revision + poids_defi + poids_incursion
    if total_masses > 1.0:
        exces = total_masses - 1.0
        poids_revision = max(0.0, poids_revision - exces)

    # L'ÉTALEMENT suit l'échec : un agent qui maîtrise reste concentré sur son palier,
    # un agent qui bloque s'étale vers ce qu'il sait faire.
    etalement = max(0.5, ETALEMENT_MAX_CURSUS * (1.0 - maitrise))

    # ⚠️ Les trois masses sont réparties SÉPARÉMENT puis normalisées à leur cible.
    #
    # Une première version laissait la gaussienne porter directement `poids_revision` par
    # palier : la masse totale d'un côté dépendait alors du NOMBRE de paliers disponibles
    # et de l'étalement, pas de l'intention. Mesuré, deux effets absurdes : à 0 % de
    # maîtrise le défi tombait à **2 %** (l'agent ne jouait plus son propre palier, donc
    # ne pouvait plus jamais y progresser), et à 80 % l'incursion tombait à **0 %** —
    # l'inverse exact de l'intention, l'étalement s'annulant avec la maîtrise.
    #
    # Ici, chaque côté est d'abord distribué en forme (gaussienne), puis remis à l'échelle
    # de la masse voulue. La forme décide de la RÉPARTITION, les poids décident du VOLUME.
    def _former(ecarts, sigma):
        formes = [math.exp(-(e ** 2) / (2.0 * sigma ** 2)) for e in ecarts]
        s = sum(formes)
        return [f / s for f in formes] if s > 0 else []

    gauche = list(range(0, ref))            # révision — peut être vide (niveau 0)
    droite = list(range(ref + 1, dernier + 1))  # incursion — peut être vide (dernier palier)

    masses = {ref: poids_defi}
    if gauche:
        for niveau, part in zip(gauche, _former([n_ - ref for n_ in gauche], etalement)):
            masses[niveau] = poids_revision * part
    if droite:
        # Queue droite plus resserrée : on explore le palier suivant, pas le doctorat.
        # `max(…, 0.4)` empêche l'incursion de s'éteindre quand l'étalement tend vers 0 —
        # c'est le « sauf exceptionnellement » de P17, qui doit rester **jamais nul**.
        sigma_d = max(0.4, etalement * 0.6)
        for niveau, part in zip(droite, _former([n_ - ref for n_ in droite], sigma_d)):
            masses[niveau] = poids_incursion * part

    niveaux = sorted(k for k, v in masses.items() if v > 1e-9)
    poids = [masses[k] for k in niveaux]

    total = sum(poids)
    if total <= 0.0:            # garde-fou : ne jamais rendre une distribution vide
        return [ref], [1.0]
    return niveaux, [p / total for p in poids]


def _tirer_niveau_episode(etat) -> int:
    """v41.6 (P17) — Tire le niveau du prochain épisode, borné à `[0, len(PROGRAMME)-1]`.

    Le tirage porte sur la distribution de `_distribution_cursus`. Le résultat est un
    INDEX valide du `PROGRAMME` par construction (la distribution n'énumère que des
    index existants), ce que l'assertion vérifie explicitement.
    """
    if DEFI_FORCE:
        # Falsification : 100 % du palier de référence, aucune révision, aucune incursion.
        return int(etat.niveau_actuel)
    niveaux, poids = _distribution_cursus(etat)
    # `np.random` et non `random` : c'est le générateur que tout le module utilise déjà
    # (placement des ressources, rêve, shuffle), et le seul que `--graine` réamorce — un
    # second générateur rendrait les runs non reproductibles à graine fixée.
    tire = int(np.random.choice(niveaux, p=poids))
    assert 0 <= tire < len(PROGRAMME), f"niveau tiré hors cursus : {tire}"
    return tire


def _appliquer_niveau_episode(etat, niveau: int) -> None:
    """v41.6 (P17) — Bascule l'environnement sur le niveau tiré, si besoin.

    Ne touche NI `niveau_actuel` (le niveau de référence, que seule la promotion déplace)
    NI `historique_episodes_niveau` : une révision n'est pas une preuve de maîtrise du
    palier courant. Voir l'invariant de mesure en tête de section.
    """
    etat.niveau_episode = niveau
    # Télémétrie P17, comptée AU TIRAGE (pas au résultat) : c'est la distribution qu'on
    # veut observer, indépendamment de ce que l'agent en fait.
    if niveau < etat.niveau_actuel:
        etat.p17_revisions_jour = getattr(etat, "p17_revisions_jour", 0) + 1
    elif niveau > etat.niveau_actuel:
        etat.p17_incursions_jour = getattr(etat, "p17_incursions_jour", 0) + 1

    env_id_voulu = ENV_FORCE if ENV_FORCE else PROGRAMME[niveau][0]
    if env_id_voulu == etat.env_id:
        return
    etat.env.close()
    etat.env_id = env_id_voulu
    etat.env = creer_env(env_id_voulu, DIM_VISUELLE)
    # v41.10 — la mémoire spatiale BASCULE au lieu d'être effacée. Les coordonnées n'ont
    # toujours aucun sens d'une carte à l'autre (invariant v39.0, intact : chaque carte
    # garde ses propres repères et n'en lit jamais d'autres), mais sous P17 l'agent
    # REVIENT sans cesse sur les mêmes cartes — effacer ici lui faisait redécouvrir de
    # zéro un monde déjà connu, ~1,5 fois par jour. Mesuré : 5/200 souvenirs utilisés
    # pour 51 715 doublons jetés.
    if MEMOIRE_PAR_CARTE_ACTIVE:
        etat.memoire_episodique_spatiale.basculer_carte(env_id_voulu)
    else:
        # Témoin v41.9 : la bascule efface. Conservé UNIQUEMENT pour l'ablation — c'est
        # le comportement dont on veut mesurer le coût, jamais un mode d'usage.
        etat.memoire_episodique_spatiale.carte_courante = env_id_voulu
        etat.memoire_episodique_spatiale.reinitialiser_niveau()

    # ⚠️ `doorkey_actif` était jusqu'ici fixé UNE FOIS par journée (`demarrer_journee`) —
    # ce qui était juste tant qu'une journée ne voyait qu'une seule carte. P17 change de
    # carte EN COURS DE JOURNÉE : sans cette réévaluation, les détecteurs de jalons
    # DoorKey tourneraient sur une carte qui n'en est pas une (ou l'inverse), et
    # `etat.detecteur` serait interrogé sur une grille sans clé ni porte.
    etat.doorkey_actif = est_doorkey(env_id_voulu)
    if etat.doorkey_actif and etat.detecteur is None:
        etat.detecteur = DetecteurJalonsDoorKey()
        etat.palier_cible = 1
        etat.gestionnaire_cursus.reinitialiser_palier()
    etat.mode_libre = etat.doorkey_actif and (etat.palier_cible >= SEUIL_PALIER_MODE_LIBRE)


def _enregistrer_episode_niveau(etat, reussi: bool) -> None:
    """v35.0 — alimente l'historique glissant qui sert à la promotion par taux de maîtrise.

    Fenêtre bornée à `FENETRE_PROMOTION` : au-delà, les plus anciens sortent (`pop(0)`),
    jamais les plus récents — même discipline que `MemoireEpisodiqueSpatiale`. Un agent
    qui progresse doit voir ses vieux échecs sortir de la moyenne, sinon il resterait
    puni indéfiniment pour ses débuts.
    """
    # v41.6 (P17) — SEULS les épisodes joués sur le NIVEAU DE RÉFÉRENCE comptent pour la
    # promotion. Une révision réussie sur un palier plus facile n'est pas une preuve de
    # maîtrise du palier courant : la créditer promouvrait un agent qui n'a rien montré là
    # où il fallait — exactement ce que l'invariant « vider la fenêtre à la promotion »
    # existe pour empêcher (P17 le réintroduirait par une autre porte).
    #
    # Les statistiques de révision/incursion sont comptées séparément (télémétrie), et la
    # maîtrise GÉNÉRALE (v41.4), elle, prend tout : c'est son rôle de traverser les cartes.
    sur_reference = getattr(etat, "niveau_episode", etat.niveau_actuel) == etat.niveau_actuel
    if sur_reference:
        etat.historique_episodes_niveau.append(1.0 if reussi else 0.0)
        if len(etat.historique_episodes_niveau) > FENETRE_PROMOTION:
            etat.historique_episodes_niveau.pop(0)
    else:
        # Télémétrie P17 : ce que l'agent fait hors de son palier de référence.
        etat.p17_episodes_hors_reference_jour = getattr(
            etat, "p17_episodes_hors_reference_jour", 0) + 1
        if reussi:
            etat.p17_victoires_hors_reference_jour = getattr(
                etat, "p17_victoires_hors_reference_jour", 0) + 1

    # v41.4 — LA MAÎTRISE GÉNÉRALE, transversale aux cartes (décision utilisateur :
    # « tu as une maîtrise générale des cartes et une maîtrise carte par carte »).
    #
    # Elle n'est PAS vidée à la promotion : c'est tout son intérêt. Un agent qui a
    # réussi 60 % sur trois cartes d'affilée n'est pas un débutant absolu sur la
    # quatrième — il sait tenir un but, éviter un mur, terminer un épisode. Cette
    # grandeur porte ce qui TRAVERSE les cartes, là où `historique_episodes_niveau`
    # porte ce qui appartient à la carte courante.
    #
    # ⚠️ Elle ne touche JAMAIS à la promotion (voir `_maturite_niveau`) — uniquement au
    # sevrage. L'invariant du projet est explicite : un taux hérité d'un niveau plus
    # facile promouvrait en chaîne. Il reste entier ici : la promotion continue d'exiger
    # une preuve fraîche sur la carte courante ; seule l'AIDE tient compte du passé.
    etat.historique_episodes_general.append(1.0 if reussi else 0.0)
    if len(etat.historique_episodes_general) > FENETRE_MAITRISE_GENERALE:
        etat.historique_episodes_general.pop(0)


def _taux_maitrise_generale(etat):
    """v41.4 — Taux de réussite sur les `FENETRE_MAITRISE_GENERALE` derniers épisodes,
    TOUTES CARTES CONFONDUES, ou None s'il n'est pas encore significatif.

    C'est la « maîtrise générale des cartes » : ce que l'agent sait faire en général,
    indépendamment du décor. Même garde `None` que le taux par niveau — « pas encore
    mesurable » n'est pas « mesuré à zéro »."""
    h = getattr(etat, "historique_episodes_general", [])
    if len(h) < MIN_EPISODES_PROMOTION:
        return None
    return sum(h) / len(h)


def _profil_carte(env):
    """v41.4 — Signature structurelle de la carte courante, LUE sur la grille.

    Rien n'est déclaré : le cerveau ne sait pas ce qu'est une clé ni une porte. On ne
    lit que des grandeurs de forme (taille, espace libre, densité d'obstacles) et
    l'ENSEMBLE OPAQUE des étiquettes d'objets présents — jamais leur signification.
    C'est la même discipline que l'empreinte de type (v39.0) : les étiquettes servent
    à comparer, jamais à interpréter.
    """
    g = env.unwrapped.grid
    surface = float(g.width * g.height)
    libres = 0.0
    murs = 0.0
    types = set()
    for y in range(g.height):
        for x in range(g.width):
            c = g.get(x, y)
            if c is None:
                libres += 1.0
            else:
                t = c.type
                if t == "wall":
                    murs += 1.0
                else:
                    types.add(t)
    return {"surface": surface, "libres": libres,
            "densite": murs / max(surface, 1.0), "types": types}


def _parente_cartes(profil_a, profil_b):
    """v41.4 — Similarité dans [0, 1] entre deux cartes, DÉRIVÉE de leurs profils.

    Le report de maîtrise d'un niveau au suivant (décision utilisateur : « reporter une
    proportion du niveau précédent de maîtrise sur le suivant ») ne peut pas être un
    pourcentage posé : les paliers ne se ressemblent pas tous. Mesuré sur les 15 niveaux
    du PROGRAMME (40 resets chacun, `docs/recherche/`), la parenté entre voisins va de
    **0,85** (`Empty-8x8` → `SimpleCrossing`, même tâche à une autre échelle) à
    **0,00** (`MemoryS7` → `MultiRoom`, vocabulaire entièrement neuf). Reporter le même
    pourcentage dans les deux cas serait faux dans au moins un des deux.

    Deux termes MULTIPLIÉS, jamais sommés — pour la même raison que la maturité est un
    produit : une carte de forme identique mais au vocabulaire inconnu n'est PAS un
    niveau parent, et une somme laisserait la forme compenser la nouveauté.

      1. la FORME  — surface, espace libre, densité d'obstacles (écarts relatifs)
      2. le VOCABULAIRE — la part des étiquettes de b déjà rencontrées dans a

    ⚠️ Le vocabulaire est comparé comme un ENSEMBLE OPAQUE. Aucune table
    `objet → difficulté` : « lava est dangereux » n'est écrit nulle part, seulement
    « lava est un symbole que cette carte-ci n'avait pas ».
    """
    ecarts = []
    for axe in ("surface", "libres", "densite"):
        va, vb = profil_a[axe], profil_b[axe]
        denom = max(abs(va), abs(vb), 1e-9)
        ecarts.append(min(1.0, abs(va - vb) / denom))
    forme = 1.0 - (sum(ecarts) / len(ecarts))

    types_b = profil_b["types"]
    if not types_b:
        vocabulaire = 1.0        # rien de neuf à apprendre : la forme décide seule
    else:
        connus = len(types_b & profil_a["types"])
        vocabulaire = connus / len(types_b)

    return max(0.0, min(1.0, forme * vocabulaire))


def _taux_maitrise_niveau(etat):
    """Taux de réussite sur la fenêtre glissante, ou None s'il n'est pas encore
    significatif (moins de `MIN_EPISODES_PROMOTION` épisodes observés).

    Retourner None plutôt que 0.0 est délibéré : « pas encore mesurable » et « mesuré à
    zéro » sont deux états différents, et les confondre promouvrait ou bloquerait sur du
    vide (même raison que le `None` des jalons DoorKey, v33.0-etape0)."""
    h = etat.historique_episodes_niveau
    if len(h) < MIN_EPISODES_PROMOTION:
        return None
    return sum(h) / len(h)


def _maturite_niveau(etat):
    """v40.2 — LA MATURITÉ sur le niveau courant, dans [0, 1]. Continue, jamais binaire.

    Remplace les deux portes scolaires (2 victoires consécutives OU 60 % sur 20 épisodes)
    par le produit de trois facteurs qui doivent TOUS être présents :

        maturité = régularité × consolidation × autonomie

    Le PRODUIT est le point essentiel. Une somme laisserait un facteur fort compenser un
    facteur nul — c'est précisément ce que faisait le `OU` logique, et ce qui a permis à un
    agent de monter au palier 5/6 avec 4 victoires au total (campagne P17). Ici, un seul
    facteur à zéro annule tout : savoir faire ne suffit pas s'il ne l'a montré qu'une fois,
    et l'avoir montré souvent ne suffit pas s'il était guidé.

    Aucune donnée nouvelle n'est collectée : les trois facteurs sortent de grandeurs déjà
    mesurées (`historique_episodes_niveau`, `facteur_guidage_jour`).
    """
    h = etat.historique_episodes_niveau
    # « Pas encore mesurable » reste distinct de « mesuré à zéro » (même invariant que
    # `_taux_maitrise_niveau`) : sans historique, aucune maturité ne peut être affirmée.
    if not h:
        return 0.0

    # 1. RÉGULARITÉ — sait-il faire ?
    regularite = sum(h) / len(h)

    # 2. CONSOLIDATION — l'a-t-il montré assez souvent pour que ce ne soit pas la chance ?
    #    Rapportée à la fenêtre : il faut avoir REMPLI la fenêtre d'observations pour
    #    qu'une réussite pèse son poids plein. C'est ce facteur qui tue l'examen.
    consolidation = min(1.0, len(h) / FENETRE_PROMOTION)

    # 3. AUTONOMIE — y arrive-t-il sans béquille ? Le guidage décroît déjà avec la maîtrise
    #    (sevrage v35.1), donc l'autonomie monte d'elle-même quand la compétence s'installe.
    #    `min(guidage, 1)` neutralise le filet (> 1), qui n'est pas une aide « en plus »
    #    mais une compensation de stagnation : la compter comme telle punirait deux fois.
    #
    # ⚠️ v41.5 — L'AUTONOMIE EST LUE AU MÊME INSTANT QUE LA RÉGULARITÉ.
    #
    # `facteur_guidage_jour` est calculé dans `demarrer_journee`, donc sur la fenêtre de la
    # VEILLE ; cette fonction est évaluée dans `executer_nuit`, avec la maîtrise DU JOUR.
    # Le produit mélangeait deux instants et sous-estimait la maturité **exactement pendant
    # les phases de progression** — c'est-à-dire au moment où la promotion se joue.
    #
    # Mesuré sur 28 runs (8 × 2000 j + 20 × 300 j) : **7 promotions refusées** à des agents
    # qui remplissaient la condition, contre **5 accordées**. Le critère refusait plus qu'il
    # n'accordait. Cas d'école : g11 refusé QUATRE FOIS à 65 % de maîtrise (maturité 0,397)
    # quand g44 était promu à 60 % (0,400 pile) — le moins compétent promu, le plus
    # compétent refusé, sur un décalage d'index.
    #
    # La marge est nulle par construction : `SEUIL_MATURITE` dérive de `TAUX_PROMOTION` par
    # la MÊME formule que l'autonomie, donc le seuil est franchi à l'égalité stricte à
    # `TAUX_PROMOTION`. Un décalage d'un jour suffit à passer dessous.
    #
    # Le guidage est RECALCULÉ ici plutôt que relu : `facteur_guidage` porte déjà tout le
    # sevrage (v41.3) et l'héritage (v41.4), et le dupliquer les ferait diverger au premier
    # changement. L'appel est pur — il ne fait qu'écrire de la télémétrie sur `etat`.
    #
    # ⚠️ Ce qui est appliqué dans la JOURNÉE reste le guidage du matin : on ne réécrit pas
    # le passé. Seule la LECTURE du critère est réalignée sur l'instant qu'elle prétend
    # mesurer.
    autonomie = 1.0 - max(0.0, min(1.0, facteur_guidage(etat)))
    # Mémorisée pour que le bilan de nuit affiche l'autonomie qui a RÉELLEMENT décidé de la
    # promotion, et non celle du matin — sans quoi la ligne « maturité = a × b × c »
    # afficherait un produit qui ne tombe pas juste.
    etat.autonomie_au_critere = autonomie

    return regularite * consolidation * autonomie


def _compter_ressources_grille(etat) -> int:
    """v34.0-etape0 — TÉLÉMÉTRIE PURE : combien de sources Nourriture/Eau existent
    réellement sur la carte de l'épisode qui commence.

    C'est la mesure BLOQUANTE du chantier v34 (voir
    docs/ameliorations/CONCEPTION_v34_fatigue_mortalite.md §7.4) : les cartes MultiRoom du Doctorat
    n'ont ni nourriture ni eau (odorat mesuré à 0,0 % des ticks, r_bio à 0,000). Rendre
    l'agent MORTEL sur une carte sans ressource, ce serait le condamner d'office, quelle
    que soit sa compétence — donc il faut connaître ce chiffre AVANT d'écrire la mort.

    Appelée une fois par épisode (jamais par tick) : la grille ne change qu'au reset, et
    un balayage complet à chaque tick coûterait cher pour une valeur constante.

    Lecture seule absolue : ne modifie ni la grille, ni l'état, ni la décision.
    """
    if not _MINIGRID_INTERNALS_OK:
        return 0
    try:
        grille = etat.env.unwrapped.grid
        total = 0
        for x in range(grille.width):
            for y in range(grille.height):
                objet = grille.get(x, y)
                if objet is not None and getattr(objet, "type", None) == TYPE_RESSOURCE \
                   and getattr(objet, "color", None) in (COULEUR_NOURRITURE, COULEUR_EAU):
                    total += 1
        return total
    except Exception:
        return 0


def _sonder_mixage(etat, **termes) -> None:
    """v41.32-etape1 — LA SONDE DE MIXAGE. Télémétrie PURE, aucun effet sur la décision.

    Accumule, pour chaque terme de la récompense, les trois scalaires qui suffisent à
    reconstruire moyenne et écart-type la nuit venue : n, Σx, Σx². Rien n'est stocké
    tick par tick.

    POURQUOI L'ÉCART-TYPE ET PAS SEULEMENT LA MOYENNE
    -------------------------------------------------
    Le gradient n'apprend pas d'une constante. Un terme qui vaut toujours −0,015 est un
    décalage d'origine : il déplace la valeur de tous les états sans jamais distinguer
    une action d'une autre. Un terme rare mais massif, lui, porte tout le signal. Les
    deux peuvent avoir la MÊME moyenne. C'est donc la dispersion qui départage, et c'est
    elle qu'il faut mesurer avant de toucher à la moindre pondération.

    POURQUOI PAS DE LISTE
    ---------------------
    1500 jours × 400 ticks × 12 termes = 7,2 M de flottants Python, pour un résultat
    obtenable en O(1) mémoire. Ici : 3 scalaires par terme, constants, aucune croissance.
    Coût par tick : une addition et une multiplication par terme — contre un forward
    réseau et un rollout C2 sur 7 actions. Mesuré négligeable (< 0,01 % du tick).

    ⚠️ La variance est calculée par Σx²/n − (Σx/n)², sensible à l'annulation
    catastrophique quand la moyenne est grande devant l'écart-type. Ce n'est PAS le cas
    ici : les termes de récompense sont tous d'ordre 1e-3 à 1e0, et la variance est
    clampée à 0 avant la racine (voir `executer_nuit`). Si un jour un terme sortait de
    cette plage, passer à l'algorithme de Welford en ligne (moyenne courante + M2).

    ⚠️ Les trois dictionnaires sont réarmés dans `_reinitialiser_buffers_journee`, comme
    TOUT buffer journalier. Ne jamais les créer à la volée par getattr() sans les y
    ajouter : c'est le bug `score_vocal_jour` v27.0, où la « moyenne du jour » cumulait
    depuis la naissance du cerveau.
    """
    etat.mix_n += 1
    somme = etat.mix_somme
    carres = etat.mix_somme_carres
    for nom, valeur in termes.items():
        v = float(valeur)
        somme[nom] = somme.get(nom, 0.0) + v
        carres[nom] = carres.get(nom, 0.0) + v * v


def _sonder_fourrage(etat, action_item) -> None:
    """v41.32-etape2 — LA SONDE DE FOURRAGE. Télémétrie PURE, aucun effet sur la décision.

    Question mesurée : **pourquoi un agent entraîné récolte-t-il 1,68 FOOD/jour quand un
    marcheur aléatoire en récolte 3,33 ?** (mesuré le 23/08, 3 graines, même distribution
    d'actions). L'agent fait donc MOINS BIEN que l'absence de politique.

    Manger exige une CONJONCTION depuis la v41.2-fix5/fix6 :
      (1) l'agent doit FAIRE FACE à la ressource (case frontale `agent_pos + dir_vec`),
      (2) et jouer `ACTION_CONSOMMER` (le `pickup` de MiniGrid).

    Une conjonction se casse de deux façons, et il faut savoir LAQUELLE :
      - l'agent ne se met jamais en position (défaut de NAVIGATION) ;
      - il s'y met mais ne tente pas le geste (défaut de DÉCISION).

    Les compteurs distinguent exactement ces deux cas :
      `occasions`        — ticks où une ressource est dans la case frontale
      `saisies`          — occasions où `ACTION_CONSOMMER` a effectivement été joué
      `tentatives`       — `ACTION_CONSOMMER` joué, avec ou sans ressource en face
      `tentatives_vides` — geste joué dans le vide (dérivé : tentatives − saisies)

    Le rapport `saisies / occasions` est le **taux de saisie** : sachant que l'agent est
    en position, tente-t-il de manger ? C'est LA grandeur qui manque au diagnostic.

    ⚠️ Lue AVANT `env.step` du tick suivant, donc la case frontale est bien celle que
    l'agent voyait quand il a décidé. Lire après périmerait la mesure — même défaut que
    la chaleur en v41.25-fix1, où une grandeur lue en tête et consommée en queue
    traversait un `env.step` qui l'avait invalidée.

    ⚠️ Compteurs réarmés dans `_reinitialiser_buffers_journee` comme TOUT buffer
    journalier (piège `score_vocal_jour` v27.0).
    """
    det = getattr(etat, "detecteur_ressources_bio", None)
    if det is None or not getattr(det, "actif", False):
        return
    try:
        env = etat.env
        devant = tuple(np.array(env.unwrapped.agent_pos) + env.unwrapped.dir_vec)
        sur_food = devant in det.positions_food
        sur_water = devant in det.positions_water
        tente = (action_item == ACTION_CONSOMMER)

        if tente:
            etat.fourrage_tentatives_jour += 1
        if sur_food or sur_water:
            etat.fourrage_occasions_jour += 1
            if tente:
                etat.fourrage_saisies_jour += 1
            # La faim au moment de l'occasion : un agent repu qui passe son tour a
            # raison, un agent affamé qui passe son tour est le défaut cherché.
            etat.fourrage_faim_aux_occasions += float(etat.moteur_bio.faim())
    except Exception:
        return    # une sonde ne doit JAMAIS interrompre un tick


def _sonder_discrimination(etat, action_item) -> None:
    """v41.32-etape4 — LA SONDE DE DISCRIMINATION. Télémétrie PURE.

    Question mesurée : **l'agent distingue-t-il une ressource d'un mur ?**

    `contact_frontal` (bus_sensoriel, DIM_TOUCHER) est UN SEUL BIT, dérivé de
    `can_overlap()`. Or `Ball.can_overlap() == False` comme `Wall.can_overlap() == False` :
    le même bit vaut 1.0 pour un mur ET pour une ressource. Mesuré sur `Empty-5x5`
    (3000 ticks) : quand le bit vaut 1, c'est un mur dans **81,5 %** des cas.

    Un réflexe appris sur ce seul bit apprendrait donc majoritairement à SE DÉTOURNER —
    et se détourner devant une ressource est exactement l'anti-corrélation mesurée à
    l'étape 2 (ratio observé/attendu = 0,67, 49 nuits sur 60 sous le hasard).

    ⚠️ MAIS L'INFORMATION EXISTE AILLEURS : la vue voit la couleur et le type, l'odorat
    donne un gradient topologique. Le bit ambigu n'est donc une cause que si l'agent
    s'appuie dessus PLUTÔT QUE sur ces canaux. C'est ce que cette sonde tranche.

    Le test : comparer la distribution des 7 actions quand `contact_frontal = 1`,
    séparément selon ce que porte la case frontale.
      - distributions IDENTIQUES  -> l'agent ne discrimine pas : le bit aveugle
      - distributions DIFFÉRENTES -> il discrimine par un autre canal : hypothèse tombée

    La distance entre les deux distributions est mesurée par la **distance de variation
    totale** (½·Σ|p−q|, dans [0,1]) : 0 = indiscernables, 1 = disjointes. Aucune
    hypothèse de forme, aucun seuil posé — c'est une lecture, pas un test.

    ⚠️ Compteurs réarmés dans `_reinitialiser_buffers_journee` (piège `score_vocal_jour`
    v27.0). Aucune écriture hors de `discrim_*`.
    """
    det = getattr(etat, "detecteur_ressources_bio", None)
    if det is None or not getattr(det, "actif", False):
        return
    if not (isinstance(action_item, (int, np.integer)) and 0 <= int(action_item) < 7):
        return
    try:
        env = etat.env
        e = env.unwrapped
        fx, fy = (int(v) for v in e.front_pos)
        grille = e.grid
        # ⚠️ v41.32-etape4-fix1 — L'APPARTENANCE AUX ENSEMBLES DU DÉTECTEUR EST TESTÉE
        # EN PREMIER, jamais `can_overlap()` sur la grille.
        #
        # Défaut mesuré : `env.step` s'exécute ~370 lignes plus haut, donc quand la sonde
        # regarde, MiniGrid a DÉJÀ exécuté `pickup` — la Ball est dans `carrying` et la
        # case est VIDE. `grille.get(fx,fy)` retournait None, `bloquant` valait False, et
        # la sonde sortait sans rien compter. Résultat : « consommer sur ressource » à
        # **0,0 % sur 60/60 nuits**, alors que le même run enregistrait **295 saisies**
        # réelles. Les deux étaient incompatibles — c'était l'artefact, pas une découverte.
        #
        # `positions_food`/`positions_water` sont maintenus par le détecteur lui-même et
        # ne sont vidés qu'à `evaluer_tick`, APRÈS cette sonde : ils restent donc valides.
        # C'est exactement la raison pour laquelle la sonde de fourrage, qui les utilise
        # déjà, n'a jamais eu ce biais.
        est_ressource = (fx, fy) in det.positions_food or (fx, fy) in det.positions_water
        if not est_ressource:
            if not (0 <= fx < grille.width and 0 <= fy < grille.height):
                bloquant = True                   # bord de grille = mur
            else:
                objet = grille.get(fx, fy)
                bloquant = objet is not None and not objet.can_overlap()
            if not bloquant:
                return                             # contact_frontal = 0, hors sujet
        a = int(action_item)
        if est_ressource:
            etat.discrim_actions_ressource[a] = etat.discrim_actions_ressource.get(a, 0) + 1
        else:
            etat.discrim_actions_mur[a] = etat.discrim_actions_mur.get(a, 0) + 1
    except Exception:
        return    # une sonde ne doit JAMAIS interrompre un tick


def _resumer_discrimination(etat) -> tuple:
    """v41.32-etape4 — distance de variation totale entre les deux distributions.

    Retourne (distance, n_mur, n_ressource, p_mur, p_ressource) ou None si l'un des deux
    échantillons est vide — auquel cas il n'y a rien à comparer, et publier un zéro ferait
    passer une sonde INACTIVE pour une mesure NULLE (règle de mesure §4).
    """
    mur = getattr(etat, "discrim_actions_mur", {}) or {}
    res = getattr(etat, "discrim_actions_ressource", {}) or {}
    n_mur, n_res = sum(mur.values()), sum(res.values())
    if n_mur == 0 or n_res == 0:
        return None
    p_mur = [mur.get(a, 0) / n_mur for a in range(7)]
    p_res = [res.get(a, 0) / n_res for a in range(7)]
    distance = 0.5 * sum(abs(p_mur[a] - p_res[a]) for a in range(7))
    return distance, n_mur, n_res, p_mur, p_res


def _resumer_mixage(etat) -> dict:
    """v41.32-etape1 — reconstruit (moyenne, écart-type) par terme depuis les 3 scalaires.

    Appelée UNE FOIS PAR NUIT, jamais par tick : le coût est de ~2 divisions et 1 racine
    par terme, soit une douzaine d'opérations pour toute la journée.

    ⚠️ `max(0.0, var)` avant la racine : Σx²/n − moy² peut sortir très légèrement négatif
    par arrondi flottant quand un terme est rigoureusement constant (typiquement un terme
    jamais déclenché de la journée, donc à 0.0 partout). Sans ce clamp, `sqrt` lèverait
    une `ValueError` en pleine nuit — et une exception ici ferait perdre la journée
    entière, alors que la sonde est censée n'avoir AUCUN effet.

    Retourne {nom: (moyenne, ecart_type)}. Un terme absent du dictionnaire est un terme
    qui n'a jamais été sondé — pas un terme à zéro.
    """
    n = max(1, getattr(etat, "mix_n", 0))
    carres = getattr(etat, "mix_somme_carres", {}) or {}
    resultats = {}
    for nom, somme in (getattr(etat, "mix_somme", {}) or {}).items():
        moyenne = somme / n
        variance = carres.get(nom, 0.0) / n - moyenne * moyenne
        resultats[nom] = (moyenne, math.sqrt(max(0.0, variance)))
    return resultats


def _quete_auto_active(etat) -> bool:
    """v33.0-etape0.5 — SEULE définition de « la quête auto tourne-t-elle ce tick ? ».

    Cinq sites lisaient auparavant `not etat.doorkey_actif` en parallèle (init d'épisode
    ×2, évaluation du tick, bilan de nuit). Les laisser diverger produirait le pire des
    bugs possibles ici : un détecteur qui ÉVALUE sans avoir été réinitialisé compare la
    distance courante au record d'un épisode précédent — donc sur une carte régénérée,
    avec un But ailleurs. Une seule fonction, cinq appels.

    Deux cas où la quête auto est active :
      - hors DoorKey : comportement historique, ces niveaux n'ont aucun autre guidage ;
      - sur DoorKey EN MODE LIBRE, si `QUETE_AUTO_EN_MODE_LIBRE` — l'exclusion visait à
        éviter un double guidage avec `RECOMPENSE_APPROCHE_BUT`, or celle-ci est déjà
        coupée en Mode Libre (voir la constante pour la mesure qui le justifie).

    ⚠️ Jamais en Mode Guidé sur DoorKey : là, les deux guidages coexisteraient
    réellement, ce que l'exclusion d'origine interdit à juste titre.
    """
    if not etat.doorkey_actif:
        return True
    return QUETE_AUTO_EN_MODE_LIBRE and etat.mode_libre


def demarrer_journee(etat):
    """Ouvre une nouvelle journée subjective : active le détecteur DoorKey si besoin,
    calcule les paramètres du jour (Empreinte de l'Enfance, Mode Libre, planification,
    entropie, patience), reset l'environnement et les buffers. Équivalent au début de
    la boucle `for jour in range(...)` d'origine (jusqu'à `agent.train()`)."""
    etat.jour += 1
    etat.doorkey_actif = est_doorkey(etat.env_id)
    if etat.doorkey_actif and etat.detecteur is None:
        etat.detecteur = DetecteurJalonsDoorKey()
        etat.palier_cible = 1
        etat.gestionnaire_cursus.reinitialiser_palier()
        print(f"   📘 Détecteur de jalons DoorKey activé (Palier visé : {etat.palier_cible} - "
              f"{DetecteurJalonsDoorKey.NOMS[0]})")

    etat.empreinte_enfance = BUS_REFERENCE_INITIAL / etat.agent.dim_bus

    etat.mode_libre = etat.doorkey_actif and (etat.palier_cible >= SEUIL_PALIER_MODE_LIBRE)
    # v35.1 — le curseur d'aide du jour, calculé UNE FOIS par journée (jamais par tick :
    # une aide qui fluctuerait d'un tick à l'autre serait un signal non stationnaire, donc
    # impossible à apprendre). Voir `facteur_guidage` pour la courbe et ses deux bornes.
    etat.facteur_guidage_jour = facteur_guidage(etat)
    # v40.0 — la force de planification n'est plus choisie par un seuil de palier, elle est
    # LUE sur le vécu de l'agent (voir `force_planification_vecue`). La bascule
    # Guidé/Libre (0.5 → 0.85) a disparu : elle décrétait un rapport de force que rien
    # n'avait mesuré, et l'ablation du 14/08 a montré qu'aucune valeur unique ne peut être
    # juste sur tous les niveaux. Calculée UNE FOIS par journée, comme le guidage : une
    # force qui fluctuerait d'un tick à l'autre serait un signal non stationnaire.
    #
    # --- v40.1 : L'ENVIE DE VIVRE MODULE TOUTES LES DÉCISIONS ---
    #
    # Décision utilisateur : « Sur toutes les décisions ! C1 est lui-même lié à cet élément
    # comme une force qui est comme de l'acceptation. » L'envie n'est donc pas un curseur
    # posé à côté des deux modules — elle traverse les trois leviers du chemin de décision :
    # ce que l'agent OSE (entropie), combien il INSISTE (patience), et à quel point il
    # DÉLIBÈRE (poids de C2).
    #
    # Toutes trois passent par `acceptation()` = envie × confiance. Un agent qui a perdu la
    # foi n'explore plus, n'insiste plus et ne planifie plus — il répète le connu jusqu'à
    # s'éteindre. C'est le « risque de tuer l'agent » assumé, et il est observable.
    envie = etat.agent.envie_de_vivre
    acceptation = etat.agent.acceptation()

    # La confiance vécue (v40) est PONDÉRÉE par l'envie : savoir délibérer ne sert à rien
    # si l'on n'ose plus rien tenter.
    etat.force_planification_jour = acceptation

    # L'exploration suit l'envie au lieu de basculer sur un seuil de palier. Les deux
    # constantes COEFF_ENTROPIE_GUIDE/LIBRE (0.02 / 0.06) deviennent les BORNES d'un
    # continuum, plus un interrupteur : à envie pleine l'agent explore comme en Mode Libre,
    # à envie nulle il se replie sur le réflexe pur.
    etat.coeff_entropie_jour = (COEFF_ENTROPIE_GUIDE
                                + (COEFF_ENTROPIE_LIBRE - COEFF_ENTROPIE_GUIDE) * envie)

    etat.facteur_complexite_jour = etat.gestionnaire_cursus.obtenir_facteur_complexite() if etat.doorkey_actif else 1.0
    etat.patience_jour = etat.module_acceptation.obtenir_seuil_patience(etat.facteur_complexite_jour)
    # La persistance suit l'envie : « pousse au maximum à essayer quand même ». L'agent qui
    # y croit s'acharne, celui qui n'y croit plus abandonne tôt. La patience reste par
    # ailleurs adaptative (taux de succès récent) — l'envie la module, ne la remplace pas.
    # Bornée par PATIENCE_MIN pour rester un épisode jouable, jamais un abandon immédiat.
    # v41.8 — LA PATIENCE EST BORNÉE PAR LE BUDGET RÉEL DE LA CARTE, et le débutant en
    # reçoit la totalité. Voir le bloc de constantes `PATIENCE_PLANCHER_BUDGET`.
    etat.patience_jour = max(PATIENCE_MIN,
                             int(round(etat.patience_jour * (0.5 + 0.5 * envie))))

    # v41.8-fix1 — LE BUDGET S'APPLIQUE EN DERNIER, APRÈS la modulation par l'envie.
    #
    # Défaut mesuré sur la campagne de nuit : appliqué AVANT, le budget était ensuite
    # multiplié par `(0.5 + 0.5 × envie)`, soit jusqu'à ÷2. Un débutant censé recevoir
    # l'épisode entier (100 ticks sur `Empty-5x5`) n'en recevait que 50 à 70 — patience
    # moyenne mesurée à **70 ticks contre 117** pour la version sans correctif, et
    # **161 abandons lucides contre 107**. La v41.8 retirait donc du temps là où elle
    # devait en donner, exactement le défaut qu'elle prétendait corriger.
    #
    # L'envie continue de moduler (un agent qui n'y croit plus abandonne tôt), mais elle
    # module DANS le budget au lieu de mordre dessous.
    etat.patience_jour = _patience_budget(etat, etat.patience_jour)
    etat.patience_base_jour = etat.patience_jour  # capturée avant tout étirement par Sursaut (v17.0), pour le log
    etat.ticks_episode_courant = 0
    etat.a_utilise_sursaut_episode = False

    obs, info = _reset_seede(etat)
    etat.etat_courant = encoder(obs)
    etat.memoire_tampon = torch.zeros(1, etat.agent.dim_bus, device=DEVICE)
    etat.vecteurs_episodiques = []
    if etat.doorkey_actif:
        etat.detecteur.reinitialiser_episode(etat.env)
        etat.chronometre_jalons.reinitialiser_episode(etat.env)  # v33.0-etape0
    etat.detecteur_portes.reinitialiser_episode(etat.env)
    if _quete_auto_active(etat):  # v33.0-etape0.5 (lu APRÈS le calcul de mode_libre)
        etat.detecteur_progres.reinitialiser_episode(etat.env)
    etat.thermostat_cinetique.reinitialiser_episode(etat.env)
    etat.sursaut_volonte.reinitialiser_episode()
    etat.detecteur_ressources_bio.reinitialiser_episode(etat.env)
    etat.bus_sensoriel.reinitialiser_episode(etat.env)  # v29.0 — efface la trace de goût
    etat.moteur_bio.reinitialiser_episode()  # v41.26 — la brûlure est une lésion locale
    etat.positions_visitees_episode = set()

    etat._reinitialiser_buffers_journee()
    # v34.0-etape0 (télémétrie) : APRÈS la remise à zéro des buffers, sinon le comptage
    # du premier épisode serait effacé aussitôt.
    etat.ressources_vues_jour += _compter_ressources_grille(etat)
    etat.jours_depuis_mutation += 1
    etat.fin_episode = False

    etat.agent.train()


# --- Helper de l'Exo-Sens (v30.0) ---

def _rafraichir_perception_exogene(etat):
    """Retourne la `ReponseC3` perceptive courante (ou None si aucun plug n'est branché).

    v30.0 — cœur du pivot de C3 en 6ème sens. Contrairement à la v28.0 où le noyau
    n'émettait sur le bus QUE lorsque l'agent jouait `ACTION_DEMANDER`, la perception
    exogène est ici **continue** : elle n'est conditionnée par aucune décision de l'agent,
    aucun seuil d'incertitude, aucun `if` cognitif. C'est ce qui la rend cohérente avec
    les deux refus déjà posés par le projet (v28 : pas de seuil pour appeler C3 ; v29 :
    pas de court-circuit C1→C2 sur confiance).

    Deux garde-fous pratiques, tous deux invisibles pour la cognition :

    1. **Cache et période de rafraîchissement** (`PERIODE_PERCEPTION_EXO`) — le bus n'est
       réellement interrogé qu'un tick sur 20 ; entre deux appels, la dernière perception
       est réutilisée. Sans ça, un plug HTTP à 100 ms rendrait un run de 120 000 ticks
       impraticable. C'est une contrainte d'échantillonnage du capteur, pas une règle de
       décision — le cerveau, lui, perçoit bien quelque chose à chaque tick.
    2. **Isolation totale** — `PortC3.canal_emission` capture déjà toute exception d'un
       plug ; on ne rajoute donc pas de `try` ici, mais on ne suppose jamais qu'une
       réponse existe (bus vide, tous les plugs en cooldown ⇒ None, vecteur nul).

    Sans aucun plug enregistré, cette fonction retourne None sans jamais toucher au bus —
    le comportement est bit-identique à la v29.1.
    """
    plugs = etat.agent.port_c3.plugs_disponibles(tick_absolu=etat.tick_absolu)
    if not plugs:
        etat.perception_exogene_cache = None
        return None

    dernier = getattr(etat, "tick_derniere_perception_exo", None)
    if dernier is not None and (etat.tick_absolu - dernier) < PERIODE_PERCEPTION_EXO:
        return etat.perception_exogene_cache  # cache encore frais

    requete = RequeteC3(
        latent=etat.memoire_tampon.detach().cpu().numpy().flatten(),
        num_actions=etat.agent.num_actions,
        indecision_c2=float(getattr(etat, "derniere_indecision_c2", 0.0)),
        erreur_jepa=float(getattr(etat, "derniere_erreur_jepa", 0.0)),
        palier_vocal=int(getattr(etat, "palier_vocal", 0)),
        mot_frontal=getattr(getattr(etat, "lecteur_case_frontale", None),
                            "_mot_brut_courant", None),
    )
    # mode="1_X" (diffusion à tous les plugs disponibles) plutôt que le routage "1_1" de
    # la v28.0 : un SENS n'est pas adressé à un interlocuteur choisi, il capte tout ce qui
    # est perceptible. La tête de routage `tete_requete` n'a donc plus de rôle ici — elle
    # reste dans le réseau (jamais amputée, comme ACTION_DEMANDER) mais n'est plus
    # consommée par le chemin perceptif.
    reponses = etat.agent.port_c3.canal_emission(
        requete, mode="1_X", tick_absolu=etat.tick_absolu
    )
    perception = etat.agent.port_c3.agreger(reponses)

    etat.tick_derniere_perception_exo = etat.tick_absolu
    etat.perception_exogene_cache = perception
    if perception is not None and perception.perception is not None:
        etat.perceptions_exo_jour = getattr(etat, "perceptions_exo_jour", 0) + 1
    return perception


# --- Helpers vocaux partagés (v27.0) ---
# Jusqu'ici, la quête vocale (L2247-2266 historique) et le bloc "score + perte
# supervisée" (L2411-2452 historique) étaient dupliqués À L'IDENTIQUE entre traiter_tick
# et _traiter_tick_vocal_isole, et avaient déjà divergé (seul traiter_tick calculait
# micro_recompense_vocale). La v27.0 triple la taille de ce bloc (score mixte
# formants+spectral, cache du canal spectral) — sans factorisation, toute la mécanique
# se serait écrite deux fois avec un risque de divergence garanti.
def facteur_nouveaute_vocale(etat) -> float:
    """v27.5 (correctif utilisateur, "boucle infinie de promotion vocale" / dopamine
    verrouillée au maximum) : facteur dans [FACTEUR_NOUVEAUTE_VOCALE_MIN, 1.0] qui
    décroît LINÉAIREMENT avec `etat.palier_vocal` — 1.0 au palier 1 (plein effet), vers
    FACTEUR_NOUVEAUTE_VOCALE_MIN au dernier palier (NB_PALIERS_VOCAUX).

    Constat : `poids_vocal` (score de prononciation du tick) alimentait la dopamine
    (`POIDS_DOPAMINE_VOCAL * poids_vocal`), le LTP (`fortifier_synapses`), la
    micro-récompense RL et le "Oui !" du Module Parent SANS AUCUNE décroissance liée à
    la maîtrise déjà acquise — un agent au dernier palier, qui prononce parfaitement un
    mot qu'il maîtrise depuis longtemps, recevait le même choc dopaminergique qu'un
    débutant qui vient tout juste de réussir sa première voyelle. Sur un cerveau resté
    bloqué sur un curriculum vocal déjà épuisé (score moyen > seuil de promotion en
    continu), ce choc quotidien maintenait `etat.teneur_dopamine` artificiellement haute
    (`plasticite_base` à 1.0 en permanence), sans qu'aucune tension motivationnelle ne
    pousse l'agent vers le reste du cursus (MiniGrid). "Moins il sait, plus l'effet est
    fort ; plus il sait, moins les effets sont forts" (décision utilisateur).

    NE s'applique JAMAIS à : la perte MSE supervisée (`perte_vocale_tick` — l'agent doit
    continuer à s'entraîner à plein régime sur F1/F2 quel que soit le palier, sinon il
    désapprendrait) ni `score_vocal_jour`/la logique de promotion de palier (sinon le
    mécanisme de promotion lui-même s'auto-invaliderait). S'applique uniquement au choc
    dopaminergique, au LTP hebbien et à la micro-récompense RL — voir les appelants."""
    p = max(1, min(NB_PALIERS_VOCAUX, etat.palier_vocal))
    progression = (p - 1) / (NB_PALIERS_VOCAUX - 1)  # 0.0 au palier 1, 1.0 au dernier
    return 1.0 + progression * (FACTEUR_NOUVEAUTE_VOCALE_MIN - 1.0)


def _construire_cible_vocale(formants_cibles: dict | None) -> list | None:
    """Vecteur [0,1]^8 de la quête vocale, ou None hors leçon. Extrait à l'identique
    des deux chemins de tick (v22.1, correctif défaut 2 : le concept-cible entre par le
    vecteur bio, jamais par l'oreille).

    v27.6 (décision utilisateur, "le cerveau doit intégrer le son peu importe la forme,
    rien en dur, dynamique") : jusqu'ici seuls les index 1 (F1) et 2 (F2) étaient
    renseignés, les 6 autres dimensions (f0, F3, F1_bw, F2_bw, durée, amplitude)
    restant TOUJOURS à 0.5 (neutre), quelle que soit la richesse de `formants_cibles` —
    ce qui plafonnait `tete_vocale` à n'apprendre que 2 des 8 paramètres du son qu'elle
    produit, même après des centaines de jours d'entraînement (diagnostiqué par
    l'utilisateur : f0/F3/durée/amplitude inchangés au dixième près sur un cerveau de
    300 jours). Chaque dimension EFFECTIVEMENT présente dans `formants_cibles` (voir
    lecons_vocales.CacheReferencesVocales, qui les dérive dynamiquement de l'audio réel
    — banque personnelle ou repli `say`, jamais une table écrite en dur) est désormais
    normalisée et intégrée ; toute dimension ABSENTE reste au neutre 0.5 — rétrocompatible
    avec les appelants qui ne fournissent encore que F1/F2 (ex. client_professeur.py, qui
    construit sa propre cible depuis VOYELLES_CIBLES sans passer par CacheReferencesVocales)."""
    if formants_cibles is None:
        return None

    def _normaliser(v, bornes):
        lo, hi = bornes
        return float(np.clip((v - lo) / (hi - lo), 0.0, 1.0))

    # index -> (clé du dict, bornes) — même ordre que SynthetiseurFormants.parametres_depuis_vecteur
    dimensions = {
        0: ("f0", BORNES_F0), 1: ("F1", BORNES_F1), 2: ("F2", BORNES_F2), 3: ("F3", BORNES_F3),
        4: ("F1_bw", BORNES_BW), 5: ("F2_bw", BORNES_BW),
        6: ("duree", BORNES_DUREE), 7: ("amplitude", BORNES_AMPLITUDE),
    }
    cible_vocale = [0.5] * 8
    for index, (cle, bornes) in dimensions.items():
        valeur = formants_cibles.get(cle)
        if valeur is not None:
            cible_vocale[index] = _normaliser(valeur, bornes)
    return cible_vocale


def _evaluer_production_vocale(etat, parametres_vocaux, formants_cibles, cible_vocale,
                                mfcc_references=None, avec_micro_recompense: bool = True) -> tuple:
    """Bloc commun « score vocal (mixte formants+spectral, v27.0) + perte MSE
    supervisée », extrait des deux chemins de tick. Retourne (poids_vocal,
    micro_recompense_vocale, score_formants, score_spectral) — les deux derniers pour
    la télémétrie uniquement.

    `avec_micro_recompense=False` (chemin vocal_isolé) : micro_recompense_vocale vaut
    TOUJOURS 0.0 — CONTRAINTE ABSOLUE, ce chemin ne touche à AUCUN des 5 buffers
    acteur-critique (log_probs/entropies/valeurs/recompenses/dones), donc une
    micro-récompense y serait calculée puis jetée, ou pire poussée dans un buffer
    désynchronisé (voir le docstring de _traiter_tick_vocal_isole).

    `mfcc_references` (v27.0) : liste de MFCC de référence (prises de la banque
    vocale) pour le canal spectral — voir hemisphere_audio.recompense_vocale_mixte.
    None/vide (repli `say`, aucune prise enregistrée) → score EXACTEMENT identique à
    recompense_formants seule, rétrocompatibilité stricte avec tous les runs
    pré-v27.0. Le coût du canal spectral (synthèse + MFCC de la production de l'agent)
    est amorti par PERIODE_EVAL_SPECTRALE (cache etat._dernier_score_spectral) — voir
    l'appelant.

    Effets de bord (identiques dans les deux chemins) : incrémente
    etat.score_vocal_jour / etat.ticks_vocaux_jour et empile etat.pertes_vocales."""
    if formants_cibles is None:
        return 0.0, 0.0, 0.0, 0.0

    formants_produits = SynthetiseurFormants().parametres_depuis_vecteur(
        parametres_vocaux.detach().cpu().numpy()
    )

    # Canal spectral (v27.0) : coûteux (synthèse + MFCC de la production de l'agent),
    # rafraîchi seulement tous les PERIODE_EVAL_SPECTRALE ticks — les paramètres vocaux
    # varient peu d'un tick au suivant sur une même leçon, voir hemisphere_audio.py.
    from naulthene.audio.hemisphere_audio import (
        extraire_mfcc, PERIODE_EVAL_SPECTRALE,
    )
    mfcc_produit = None
    if mfcc_references:
        tick_dernier = getattr(etat, "_tick_dernier_spectral", -PERIODE_EVAL_SPECTRALE)
        if etat.tick_absolu - tick_dernier >= PERIODE_EVAL_SPECTRALE:
            onde_produite = SynthetiseurFormants().synthetiser(
                parametres_vocaux.detach().cpu().numpy()
            )
            mfcc_produit = extraire_mfcc(onde_produite, sample_rate=16000)
            etat._tick_dernier_spectral = etat.tick_absolu
            etat._dernier_score_spectral_mfcc = mfcc_produit
        else:
            mfcc_produit = getattr(etat, "_dernier_score_spectral_mfcc", None)

    score_vocal, score_formants, score_spectral = recompense_vocale_mixte(
        formants_cibles, formants_produits,
        mfcc_references=mfcc_references, mfcc_produit=mfcc_produit,
    )
    poids_vocal = score_vocal
    micro_recompense_vocale = score_vocal * MICRO_RECOMPENSE_VOCALE if avec_micro_recompense else 0.0

    etat.score_vocal_jour = getattr(etat, "score_vocal_jour", 0.0) + score_vocal
    etat.ticks_vocaux_jour = getattr(etat, "ticks_vocaux_jour", 0) + 1

    # Le vrai gradient : MSE entre les formants PRODUITS (tenseur vivant, graphe
    # intact) et les formants CIBLES — sur TOUTES les dimensions EFFECTIVEMENT
    # renseignées dans `formants_cibles` (v27.6, décision utilisateur : "rien en dur,
    # dynamique"). Avant v27.6, seuls F1/F2 (index [1, 2]) recevaient jamais de
    # gradient dirigé, quelle que soit la richesse de la cible — les 6 autres
    # dimensions restaient à 0.5 dans cible_vocale et n'apprenaient donc jamais rien
    # (diagnostiqué par l'utilisateur : f0/F3/durée/amplitude inchangés au dixième
    # près après 300 jours). Les indices contraints se calculent maintenant à partir
    # des clés RÉELLEMENT présentes dans formants_cibles — un appelant qui ne fournit
    # encore que {"F1","F2"} (ex. client_professeur.py) continue de contraindre
    # exactement [1, 2], rétrocompatibilité stricte ; un appelant qui fournit les 8
    # clés (CacheReferencesVocales, dérivées dynamiquement de l'audio réel) contraint
    # les 8 dimensions.
    _cles_par_index = {
        0: "f0", 1: "F1", 2: "F2", 3: "F3", 4: "F1_bw", 5: "F2_bw",
        6: "duree", 7: "amplitude",
    }
    indices_presents = [i for i, cle in _cles_par_index.items() if formants_cibles.get(cle) is not None]
    indices_contraints = torch.tensor(indices_presents, device=DEVICE)
    cible_vocale_tensor = torch.tensor(cible_vocale, dtype=torch.float32, device=DEVICE)
    perte_vocale_tick = F.mse_loss(
        parametres_vocaux.squeeze(0).index_select(0, indices_contraints),
        cible_vocale_tensor.index_select(0, indices_contraints),
    )
    etat.pertes_vocales.append(perte_vocale_tick)

    return poids_vocal, micro_recompense_vocale, score_formants, score_spectral


def _appliquer_feedback_parent_vocal(etat, score_vocal: float) -> None:
    """Module "Parent" (v25.0, Paradigme Bébé, expérimental) : feedback social vocal
    déterministe, appelé UNIQUEMENT quand `parent_actif=True` (jour >=
    JOUR_FIN_MASQUAGE_EXTERNE) et qu'une cible vocale était bien présente ce tick.
    "Oui !" (score_vocal >= SEUIL_PARENT_OUI) renforce le choc dopaminergique déjà
    déclenché par poids_vocal>0 dans l'appelant (rien à faire de plus ici que de
    tracer l'événement) ; "Non !" (score_vocal < SEUIL_PARENT_NON) pousse activement
    la dopamine vers DOPAMINE_MIN via un nouveau canal ("cortisol"), distinct de la
    simple friction quotidienne — seul point du moteur qui punit activement plutôt que
    de laisser décroître par défaut. Le clip [DOPAMINE_MIN, DOPAMINE_MAX] est
    systématiquement réappliqué (garde-fou CLAUDE.md, réservoir dopaminergique)."""
    etat.feedback_parent_jour = getattr(etat, "feedback_parent_jour", 0)
    if score_vocal >= SEUIL_PARENT_OUI:
        etat.feedback_parent_jour += 1  # "Oui !" — le choc positif existant sur poids_vocal suffit
    elif score_vocal < SEUIL_PARENT_NON:
        etat.feedback_parent_jour -= 1  # "Non !" — décompte pour distinguer des "Oui !" dans les logs
        etat.teneur_dopamine += (DOPAMINE_MIN - etat.teneur_dopamine) * TAUX_CORTISOL_PARENT
        etat.teneur_dopamine = float(np.clip(etat.teneur_dopamine, DOPAMINE_MIN, DOPAMINE_MAX))


def _traiter_tick_vocal_isole(etat, obs_auditive, formants_cibles, parent_actif=False,
                               mfcc_references=None):
    """Le chemin réduit de l'après-midi vocal (v23.0, Cursus Développemental par Ères) :
    l'agent est "au calme, écran noir" — AUCUN `env.step` n'est appelé (l'environnement
    MiniGrid est en pause, pas juste ignoré) et la vision est un tenseur de zéros. Seuls
    s'exécutent : la pensée multimodale (vision nulle + audio réel), le JEPA (vision
    nulle + audio), la perte vocale supervisée, la dopamine sur le score de formants.

    Volontairement PAS de sursaut/abandon/détecteurs MiniGrid (jalons, portes, progrès,
    biologie spatiale, ressources) — tous dépendent d'`etat.env` qu'on ne fait pas
    avancer ce tick, les invoquer produirait un signal trompeur (ex: "nouvelle case
    visitée" alors que l'agent n'a pas bougé). Volontairement PAS d'échantillonnage
    d'action motrice (`dist.sample()`) ni d'ajout à `log_probs_journee`/
    `entropies_journee`/`valeurs_journee`/`recompenses_journee`/`dones_journee` : ces 5
    buffers doivent rester mutuellement synchronisés (voir `apprendre_journee`, la
    boucle `zip(reversed(rewards), reversed(dones))` suppose une correspondance stricte
    de longueur) — le rejouer avec des paires factices (action neutre, récompense 0)
    pollueraient l'estimation d'avantage du Système 1/2 avec du bruit sans rapport avec
    une vraie décision motrice. La perte acteur-critique de la journée ne porte donc
    que sur les ticks du matin (MiniGrid réel), exactement comme avant v23.0.

    `parent_actif` (v25.0, Paradigme Bébé, expérimental) : défaut False = comportement
    identique à avant v25.0. À True (jour >= JOUR_FIN_MASQUAGE_EXTERNE dans
    cursus_bebe.py), applique le feedback social déterministe "Oui !"/"Non !" en plus
    du choc dopaminergique existant sur poids_vocal — voir _appliquer_feedback_parent_vocal.

    `mfcc_references` (v27.0) : liste de MFCC de la banque vocale pour le mot en cours,
    transmise à _evaluer_production_vocale pour le score spectral — voir
    hemisphere_audio.recompense_vocale_mixte. None = comportement pré-v27.0 (formants
    seuls)."""
    etat.tick_absolu += 1

    vision_nulle = torch.zeros(1, etat.agent.dim_visuelle, device=DEVICE)
    memoire_avant = etat.memoire_tampon
    if etat.vecteurs_episodiques:
        contexte = torch.stack(etat.vecteurs_episodiques).mean(dim=0)
    else:
        contexte = etat.agent.contexte_vide()

    cible_vocale = _construire_cible_vocale(formants_cibles)

    # Pas de rappel spatial (l'agent ne bouge pas ce tick, aucun souvenir de position
    # n'est pertinent à consulter) — vecteur bio construit sans lui, comme si l'agent
    # n'avait pas de quête de survie active en cours (neutre par défaut).
    # v39.2 — en leçon vocale, le canal auditif existe par construction : la présence porte
    # l'amplitude réellement entendue. C'est le cas où la distinction compte le plus, le
    # professeur alternant parole et silence.
    _presence_aud = (float(torch.clamp(obs_auditive.detach().abs().mean(), 0.0, 1.0))
                     if obs_auditive is not None else 0.0)
    vecteur_bio_tensor = torch.tensor(
        [etat.moteur_bio.obtenir_vecteur_bio(None, cible_vocale,
                                              presence_auditive=_presence_aud)],
        dtype=torch.float32, device=DEVICE
    )

    (_logits_action, _valeur_estimee, parametres_vocaux, pensee_enrichie,
     etat.memoire_tampon, bus_latent, _logits_routage,
     _indecision_c2) = etat.agent.penser(
        vision_nulle, memoire_avant, contexte, vecteur_bio_tensor,
        force_planification=etat.force_planification_jour,
        horizons_planification=HORIZONS_PLANIFICATION,
        gamma_planif=GAMMA_PLANIFICATION,
        obs_auditive=obs_auditive,
        # Mode vocal isolé (pas d'env MiniGrid, aucun mouvement possible ce tick) :
        # aucune raison d'exposer l'action ACTION_DEMANDER ici, on ne transmet donc
        # jamais de plugs disponibles — comportement identique à "aucun plug branché".
    )

    etat.vecteurs_episodiques.append(bus_latent.detach())
    if len(etat.vecteurs_episodiques) > CAPACITE_MEMOIRE:
        etat.vecteurs_episodiques.pop(0)

    # JEPA (vision nulle prédite — coût quasi nul et stable puisque la cible est
    # elle-même toujours nulle ; audio réel via la tête dédiée, même rampe progressive
    # coeff_jepa_audio que le mode minigrid).
    action_neutre = 0  # n'est JAMAIS appliqué à un env — sert seulement au one-hot JEPA
    attente = etat.agent.generer_attente_reelle(pensee_enrichie, action_neutre)
    attente_audio = None
    coeff_jepa_audio = 0.0
    if obs_auditive is not None:
        etat.ticks_audio_recus += 1
        coeff_jepa_audio = COEFF_JEPA_AUDIO_MAX * min(1.0, etat.ticks_audio_recus / RAMPE_JEPA_AUDIO)
        attente_audio = etat.agent.generer_attente_audio_reelle(pensee_enrichie, action_neutre)
    perte_tick = etat.agent.perte_jepa(
        attente, vision_nulle, attente_audio=attente_audio,
        obs_auditive_suivante=obs_auditive, coeff_jepa_audio=coeff_jepa_audio,
    )
    etat.jepa_losses.append(perte_tick)
    valeur_erreur = float(perte_tick.item())
    etat.erreur_journee += valeur_erreur
    # v41.13 — ventilation JEPA (télémétrie pure, voir perte_jepa). `getattr` car un
    # cerveau n'ayant encore jamais calculé de perte n'a pas ces attributs.
    _ag = etat.agent
    etat.jepa_concentration_cumul_jour = (getattr(etat, "jepa_concentration_cumul_jour", 0.0)
                                          + getattr(_ag, "jepa_diag_concentration", 0.0))
    etat.jepa_amplitude_cumul_jour = (getattr(etat, "jepa_amplitude_cumul_jour", 0.0)
                                      + getattr(_ag, "jepa_diag_amplitude_cible", 0.0))
    etat.jepa_err_max_dim_jour = max(getattr(etat, "jepa_err_max_dim_jour", 0.0),
                                     getattr(_ag, "jepa_diag_erreur_max_dim", 0.0))

    # Perte vocale supervisée + dopamine (même mécanique que traiter_tick, voir le
    # correctif v22.1 défaut 1 : c'est cette perte MSE, pas le score, qui donne le vrai
    # gradient d'apprentissage à tete_vocale). avec_micro_recompense=False : ce chemin
    # ne touche à AUCUN des 5 buffers acteur-critique (contrainte absolue, voir
    # docstring ci-dessus).
    poids_vocal, _micro_recompense_ignoree, _sf, _ss = _evaluer_production_vocale(
        etat, parametres_vocaux, formants_cibles, cible_vocale,
        mfcc_references=mfcc_references, avec_micro_recompense=False,
    )

    # --- DOPAMINE UNIFIÉE MULTIMODALE (v27.0) : ici, visuel = 0 (l'env est en pause,
    # aucun canal visuel n'existe ce tick) — la formule générale de traiter_tick
    # (1 - (1 - w_v*visuel)*(1 - w_a*vocal)) s'y réduit exactement à w_a*vocal. Voir
    # traiter_tick pour la justification complète de l'agrégation probabiliste.
    #
    # v27.5 (correctif utilisateur) : poids_vocal est pondéré par facteur_nouveaute_vocale
    # AVANT d'entrer dans la dopamine/le LTP — jamais avant la perte MSE (déjà calculée
    # ci-dessus dans _evaluer_production_vocale, sur poids_vocal brut) ni score_vocal_jour
    # (déjà accumulé aussi, sert la promotion de palier). Un mot déjà maîtrisé (palier
    # avancé) continue d'entraîner tete_vocale à plein régime, mais ne shoote plus la
    # dopamine au même niveau qu'un mot neuf.
    poids_vocal_dopamine = poids_vocal * facteur_nouveaute_vocale(etat)
    poids_evenement = POIDS_DOPAMINE_VOCAL * poids_vocal_dopamine
    if poids_evenement > 0:
        etat.teneur_dopamine += (DOPAMINE_MAX - etat.teneur_dopamine) * TAUX_CHOC_BASE * poids_evenement
        etat.agent.fortifier_synapses(poids_evenement)
    else:
        etat.teneur_dopamine += (DOPAMINE_MIN - etat.teneur_dopamine) * TAUX_FRICTION
    etat.teneur_dopamine = float(np.clip(etat.teneur_dopamine, DOPAMINE_MIN, DOPAMINE_MAX))

    if parent_actif and formants_cibles is not None:
        _appliquer_feedback_parent_vocal(etat, poids_vocal)

    return {
        'action': None,  # aucune action motrice appliquée ce tick (env en pause)
        'infos_internes': {
            'dopamine': etat.teneur_dopamine,
            'faim': 1.0 - etat.moteur_bio.satiete,
            'parametres_vocaux': parametres_vocaux.detach().cpu().numpy().flatten().tolist(),
        },
    }


def traiter_tick(etat, obs_auditive=None, formants_cibles=None, mode_perception="minigrid",
                  masquer_recompense_externe=False, parent_actif=False, mfcc_references=None):
    """Un seul tick complet de conscience active : perception → pensée → action →
    apprentissage (LTP + accumulation des buffers pour apprendre_journee/rever).
    Équivalent au corps de `for tick in range(ticks_par_jour):` d'origine. Appelée à
    la fois par le mode standalone (une fois par itération) et par la Cuve du daemon
    (une fois par paquet réseau reçu, voir CuveDeMaintien._vivre_connexion).

    Ouverture du verrou v22.0 (voir plan v22.0, Étape 5 et Question ouverte A) : le
    daemon ignorait jusqu'ici tout le contenu du paquet reçu du client (seul `env.step`
    côté serveur faisait foi). `obs_auditive` (tenseur DIM_AUDIO_ENTREE, ou None =
    silence) est le premier canal de perception réellement transmis par le tuteur —
    c'est ce qui permet à un `client_professeur.py` d'injecter un son dans le cerveau.
    `formants_cibles` (dict F1/F2 ou None) déclenche la récompense de formants par tick
    quand une leçon vocale est active ; sans leçon, l'agent vocalise quand même (voir
    penser()) mais sans pilotage de récompense dédié — juste le JEPA audio en fond.

    `mode_perception` (v23.0, Cursus Développemental par Ères) : "minigrid" (défaut,
    comportement strictement identique à avant v23.0 — non-régression validée) ou
    "vocal_isole". En "vocal_isole", l'après-midi vocal du cursus met l'agent "au calme,
    écran noir" (décision utilisateur) : AUCUN `env.step` n'est appelé (l'environnement
    MiniGrid est en pause, pas juste ignoré) et la vision est un tenseur de zéros —
    seuls la pensée multimodale, le JEPA (audio + vision nulle), la perte vocale
    supervisée et la dopamine sur le score de formants s'exécutent. Voir
    _traiter_tick_vocal_isole ci-dessous pour le détail de ce chemin réduit.

    `masquer_recompense_externe` (v25.0, Paradigme Bébé, expérimental) : défaut False =
    comportement identique à avant v25.0. À True (cursus_bebe.py, jour <
    JOUR_FIN_MASQUAGE_EXTERNE), `recompense_env` est gelée à 0.0 juste après `env.step`
    — neutralise à la fois sa contribution à `recompense_interne` (Système 1/2) ET à
    `poids_evenement` (donc plus de choc dopaminergique "victoire" ni de
    `victoire_aujourdhui`, donc plus de promotion de niveau MiniGrid tant que le
    masquage est actif). JEPA, curiosité, homéostasie (r_bio) et vocal restent
    intacts — seul le signal RL externe est verrouillé, conformément au principe
    "l'agent n'a aucune idée s'il fait bien ou mal" des 8 premiers mois.

    `parent_actif` (v25.0, Paradigme Bébé, expérimental) : défaut False = comportement
    identique à avant v25.0. Transmis tel quel à `_traiter_tick_vocal_isole` en mode
    "vocal_isole" ; en mode "minigrid", déclenche le feedback social déterministe
    "Oui !"/"Non !" (voir _appliquer_feedback_parent_vocal) sur le score de formants du
    tick, en plus du choc dopaminergique existant sur poids_vocal.

    `mfcc_references` (v27.0) : liste de MFCC de la banque vocale pour le mot de la
    leçon en cours (voir lecons_vocales.CacheReferencesVocales.obtenir_mfcc_prises) —
    active le canal spectral de la récompense mixte. None (défaut) = comportement
    pré-v27.0, formants seuls."""
    if mode_perception == "vocal_isole":
        return _traiter_tick_vocal_isole(etat, obs_auditive, formants_cibles,
                                          parent_actif=parent_actif,
                                          mfcc_references=mfcc_references)

    memoire_avant = etat.memoire_tampon
    etat.ticks_episode_courant += 1
    etat.tick_absolu += 1

    if etat.vecteurs_episodiques:
        contexte = torch.stack(etat.vecteurs_episodiques).mean(dim=0)
    else:
        contexte = etat.agent.contexte_vide()

    # --- Rappel de mémoire épisodique spatiale (v20.0, générique) : si l'agent a
    # une quête de survie active, on cherche si un souvenir pertinent (ex: dernier
    # emplacement de Nourriture vu) existe déjà, pour orienter la décision ---
    rappel_spatial = None
    if _MINIGRID_INTERNALS_OK and etat.moteur_bio.quete_active is not None:
        type_recherche = etat.moteur_bio.quete_active["type"].replace("SURVIVAL_", "")
        position_courante = tuple(etat.env.unwrapped.agent_pos)
        rappel_spatial = etat.memoire_episodique_spatiale.recuperer_contexte(
            position_courante, type_recherche, etat.tick_absolu
        )
        # v30.1 (télémétrie, aucun effet sur la décision) : mesure la QUALITÉ du rappel,
        # pas seulement la taille de la mémoire. C'est ce qui permettra de dire si la
        # saturation à `capacite_max=200` coûte réellement quelque chose — un rappel qui
        # reste proche et frais à saturation prouverait que la capacité n'est pas le
        # facteur limitant, et qu'une capacité adaptative serait une fausse bonne idée.
        etat.memoire_rappels_tentes_jour += 1
        if rappel_spatial is not None:
            etat.memoire_rappels_reussis_jour += 1
            etat.memoire_distance_cumul_jour += rappel_spatial[0]
            etat.memoire_fraicheur_cumul_jour += rappel_spatial[1]

    # --- Quête vocale (v22.1, défaut 2 du correctif) : le concept-cible d'une leçon
    # vocale n'entre plus dans l'oreille (porte_auditive) mais dans le vecteur bio,
    # comme une quête au même titre que SURVIVAL_FOOD/SURVIVAL_WATER — "voici ce qu'il
    # faut produire", jamais mélangé au son réellement perçu.
    cible_vocale = _construire_cible_vocale(formants_cibles)

    # --- Les 3 sens faibles à moyens (v29.0, Bus Sensoriel) : toucher (contact frontal,
    # objet en main, orientation) + chimie (odorat des ressources à portée, goût rémanent
    # de la dernière consommation). Lus AVANT penser(), comme la vue et l'ouïe, et
    # transmis par la queue du vecteur bio — jamais par le bus latent, donc jamais dans
    # la cible JEPA. `interpreter()` fait aussi décroître la trace de goût de ce tick.
    # --- L'EXO-SENS (v30.0, le 6ème sens) : perception CONTINUE du monde numérique.
    # Aucun `if` de déclenchement, aucun seuil — l'agent « sent » C3 comme il sent le
    # toucher, et c'est integrateur_bio qui apprend seul (par myélinisation) quelle
    # attention accorder à ces 8 dimensions. Sans plug branché, reponse_c3_perception
    # reste None et les 8 dims sont nulles : comportement strictement identique à v29.1.
    #
    # Latence : un plug HTTP peut coûter de 100 ms à 30 s par appel (voir
    # professeur_gemma). L'interroger à CHAQUE tick rendrait un run de 400 ticks/jour
    # impraticable — la perception est donc rafraîchie tous les PERIODE_PERCEPTION_EXO
    # ticks et mise en cache entre deux appels. C'est cohérent avec la biologie : un sens
    # a une fréquence d'échantillonnage propre, il ne rafraîchit pas à l'infini.
    reponse_c3_perception = _rafraichir_perception_exogene(etat)
    signaux_sensoriels = etat.bus_sensoriel.interpreter(
        etat.env, reponse_c3=reponse_c3_perception
    )

    # Télémétrie des 3 sens ajoutés en v29.0 (v29.1) — purement observationnelle, jamais
    # relue par la décision. Indices figés par le contrat de BusSensoriel.interpreter :
    # [0]=contact, [1]=objet en main, [2:4]=orientation, [4:6]=odorat, [6:8]=goût.
    etat.ticks_sensoriels_jour += 1
    etat.toucher_contact_jour += int(signaux_sensoriels[0] > 0.5)
    etat.toucher_portage_jour += int(signaux_sensoriels[1] > 0.5)
    odorat_tick = signaux_sensoriels[4] + signaux_sensoriels[5]
    etat.odorat_cumul_jour += odorat_tick
    etat.odorat_max_jour = max(etat.odorat_max_jour, odorat_tick)
    etat.odorat_ticks_actifs_jour += int(odorat_tick > 0.0)
    etat.gout_ticks_actifs_jour += int((signaux_sensoriels[6] + signaux_sensoriels[7]) > 0.0)
    # v32.0 — CLINOTAXIE : dims [16:18], les 2 DERNIÈRES du vecteur (contrat append-only).
    # Neutre = 0.5 ; > 0.5 ⇒ l'odeur monte, l'agent se rapproche d'une ressource.
    # ⚠️ Borne HAUTE explicite depuis la v41.11 : la thermoception est ajoutée en queue
    # APRÈS la clinotaxie, et sans cette borne ses 2 dims seraient comptées comme de la
    # variation olfactive — exactement le défaut dont la v32.0 avertit trois lignes plus
    # bas pour l'Exo-Sens. Une tranche ouverte n'est jamais sûre sur un contrat append-only.
    _debut_deltas = DIM_TOUCHER + DIM_CHIMIE + DIM_EXO
    deltas_odorat = signaux_sensoriels[_debut_deltas:_debut_deltas + DIM_ODORAT_DELTA]
    ecarts = [d - 0.5 for d in deltas_odorat]
    if any(abs(e) > 1e-6 for e in ecarts):
        etat.odorat_ticks_variation_jour += 1
        etat.odorat_delta_cumul_jour += sum(abs(e) for e in ecarts)
        etat.odorat_ticks_approche_jour += int(any(e > 1e-6 for e in ecarts))
    # Une source présente sur la grille mais d'odeur nulle est, depuis la v32.0, une
    # source que le BFS a jugée INATTEIGNABLE (murs) — en v31.x elle aurait embaumé à
    # travers la cloison. Mesure directement ce que la topologie a cessé de laisser fuir.
    if odorat_tick == 0.0 and getattr(etat, "detecteur_ressources_bio", None) is not None:
        etat.odorat_sources_inodores_jour += 1
    # v30.0 — Exo-Sens : dims [8:16] du vecteur sensoriel (voir le contrat d'ordre de
    # BusSensoriel.interpreter). Intensité = moyenne des 8 dims, 0.0 sans plug branché.
    # Borne HAUTE explicite depuis la v32.0 : sans elle, les 2 dims de clinotaxie
    # ajoutées en queue seraient comptées comme de l'Exo-Sens et fausseraient `Sens_Exo_*`.
    vecteur_exo = signaux_sensoriels[DIM_TOUCHER + DIM_CHIMIE:
                                     DIM_TOUCHER + DIM_CHIMIE + DIM_EXO]
    intensite_exo = sum(vecteur_exo) / max(1, len(vecteur_exo))
    etat.exo_cumul_jour += intensite_exo
    etat.exo_max_jour = max(etat.exo_max_jour, intensite_exo)
    etat.exo_ticks_actifs_jour += int(intensite_exo > 0.0)

    # --- v41.11 : THERMOCEPTION — les 2 DERNIÈRES dims du vecteur sensoriel ---
    # Instrumentée dans le même commit que la mécanique (règle v29.1). Sans ces compteurs,
    # impossible de répondre à la seule question qui vaille : le champ de chaleur monte-t-il
    # réellement quand l'agent approche du danger, et l'agent finit-il par l'éviter ?
    # Clés CONDITIONNELLES à la nuit : sur une carte sans source brûlante, le signal est
    # nul partout et logger des zéros ferait croire à un capteur mort.
    # ⚠️ Bornée en HAUT depuis la v41.12, pour la même raison qu'au-dessus : la pression a
    # été ajoutée en queue et une tranche ouverte l'aurait comptée comme de la chaleur.
    # Le défaut se reproduit à CHAQUE ajout — c'est le prix du contrat append-only.
    _debut_thermo = _debut_deltas + DIM_ODORAT_DELTA
    _thermo = signaux_sensoriels[_debut_thermo:_debut_thermo + DIM_THERMOCEPTION]
    if _thermo:
        _chaleur, _delta_chaleur = float(_thermo[0]), float(_thermo[1])
        # v41.25 — LA BOUCLE SE FERME ICI. La chaleur perçue devient la chaleur SUBIE :
        # le moteur homéostatique la lira dans `calculer_deficit` (terme `+ chaleur**2`).
        # ⚠️ L'écriture doit avoir lieu AVANT le `calculer_deficit` du tick (plus bas,
        # `deficit_tick`), sinon la douleur serait facturée avec un tick de retard et
        # `r_bio` créditerait le déplacement suivant — une superstition, au sens exact
        # de l'invariant v37.1 sur les frontières d'épisode.
        etat.moteur_bio.chaleur = _chaleur
        etat.chaleur_cumul_jour = getattr(etat, "chaleur_cumul_jour", 0.0) + _chaleur
        # v41.26 — la douleur GRADUÉE réellement facturée (lecture pure, sans effet de bord)
        _dlr = etat.moteur_bio.douleur_thermique()
        etat.douleur_cumul_jour = getattr(etat, "douleur_cumul_jour", 0.0) + _dlr
        etat.douleur_max_jour = max(getattr(etat, "douleur_max_jour", 0.0), _dlr)
        etat.douleur_ticks_actifs_jour = (
            getattr(etat, "douleur_ticks_actifs_jour", 0) + int(_dlr > 1e-6))
        etat.chaleur_max_jour = max(getattr(etat, "chaleur_max_jour", 0.0), _chaleur)
        etat.chaleur_ticks_actifs_jour = (
            getattr(etat, "chaleur_ticks_actifs_jour", 0) + int(_chaleur > 0.0))
        # Approche = la chaleur monte (> 0.5). C'est la mesure qui dira si l'agent
        # apprend à FUIR : ce taux doit baisser avec l'âge sur les cartes à danger.
        if abs(_delta_chaleur - 0.5) > 1e-6:
            etat.chaleur_ticks_variation_jour = (
                getattr(etat, "chaleur_ticks_variation_jour", 0) + 1)
            etat.chaleur_ticks_approche_jour = (
                getattr(etat, "chaleur_ticks_approche_jour", 0)
                + int(_delta_chaleur > 0.5))

    # v41.27 — la douleur UNIQUE, hors du bloc thermique : elle existe même sans danger
    # thermique (un choc mural suffit), donc son compteur est inconditionnel.
    _dc = etat.moteur_bio.douleur_corporelle()
    etat.douleur_corp_cumul_jour = getattr(etat, "douleur_corp_cumul_jour", 0.0) + _dc
    etat.douleur_corp_max_jour = max(getattr(etat, "douleur_corp_max_jour", 0.0), _dc)

    # --- v41.12 : LE TOUCHER À DISTANCE — les 2 DERNIÈRES dims du vecteur sensoriel ---
    # Contrairement à la thermoception, ce sens est actif sur TOUTE carte (il y a toujours
    # des murs) : les clés sont donc inconditionnelles. `Pression_Moyenne` mesure
    # l'encombrement vécu, `Asymetrie_Ecart` mesure si le signal latéral porte vraiment de
    # l'information — plat à 0.5, il ne servirait à rien.
    _pression = signaux_sensoriels[_debut_thermo + DIM_THERMOCEPTION:]
    if _pression:
        _p, _asym = float(_pression[0]), float(_pression[1])
        etat.pression_cumul_jour = getattr(etat, "pression_cumul_jour", 0.0) + _p
        etat.pression_max_jour = max(getattr(etat, "pression_max_jour", 0.0), _p)
        etat.asymetrie_ecart_cumul_jour = (
            getattr(etat, "asymetrie_ecart_cumul_jour", 0.0) + abs(_asym - 0.5))

    # --- v36.0 : LE RAPPEL MARQUANT (lecture agnostique) ---
    # Contrairement à `rappel_spatial` plus haut, qui exige une quête active ET un type
    # recherché, ce rappel-ci ne demande RIEN : il balaie tous les repères et rend le plus
    # pesant. C'est ce qui le rend conforme à « rien n'est expliqué en dur » — l'agent ne
    # cherche pas « de la nourriture », il perçoit « ici, il s'est passé quelque chose ».
    rappel_marquant = None
    if _MINIGRID_INTERNALS_OK:
        try:
            rappel_marquant = etat.memoire_episodique_spatiale.rappel_le_plus_marquant(
                tuple(int(v) for v in etat.env.unwrapped.agent_pos), etat.tick_absolu
            )
        except Exception:
            rappel_marquant = None
    if rappel_marquant is not None and rappel_marquant[1] > 0.0:
        etat.memoire_rappels_marquants_jour += 1
        etat.memoire_valence_cumul_jour += abs(rappel_marquant[0])

    # v39.2 — la présence auditive : l'amplitude moyenne réellement perçue ce tick, ou 0.0
    # si aucun canal n'existe. C'est la seule information qui distingue « j'écoute et c'est
    # calme » de « je n'ai pas d'oreilles » — deux états jusqu'ici identiques pour le
    # cerveau (`relu(porte_auditive(zeros)) == 0` exactement, la couche étant sans biais).
    # `obs_auditive` est un TENSEUR (DIM_AUDIO_ENTREE) — pas un tableau numpy.
    _presence_aud = (float(torch.clamp(obs_auditive.detach().abs().mean(), 0.0, 1.0))
                     if obs_auditive is not None else 0.0)

    # v41.33 — LA CHARGE PORTÉE. Lue sur `carrying`, l'API MiniGrid, exactement comme
    # `transition_tick` lit `agent_pos`/`agent_dir` (v41.31) : aucun TYPE d'objet n'est
    # nommé, seule la PRÉSENCE d'une charge est perçue. Un agent qui porte une clé et un
    # agent qui porte une balle envoient le même 1.0 — c'est au réseau de découvrir la
    # différence par ce qui lui arrive ensuite, jamais à une table de le lui dire.
    # Lecture défensive : hors MiniGrid (rêve, cuve, arène), `portage=None` → 0.0.
    try:
        _portage = 1.0 if etat.env.unwrapped.carrying is not None else 0.0
    except Exception:
        _portage = None
    if not PORTAGE_PERCU_ACTIF:
        _portage = 0.0   # témoin : la dimension reste, l'information est coupée

    vecteur_bio_tensor = torch.tensor(
        [etat.moteur_bio.obtenir_vecteur_bio(rappel_spatial, cible_vocale,
                                              signaux_sensoriels=signaux_sensoriels,
                                              rappel_marquant=rappel_marquant,
                                              presence_auditive=_presence_aud,
                                              portage=_portage)],
        dtype=torch.float32, device=DEVICE
    )

    # Port Exocortex C3 (v28.0) : la disponibilité est interrogée UNE FOIS par tick,
    # avant penser() — c'est ce qui détermine si l'action ACTION_DEMANDER existe ou
    # non dans les logits (voir masquage dans penser()). tick_absolu sert d'horloge
    # de cooldown pour PortC3 (voir port_c3.COOLDOWN_PLUG_ECHEC).
    plugs_c3_disponibles = etat.agent.port_c3.plugs_disponibles(tick_absolu=etat.tick_absolu)

    (logits_action, valeur_estimee, parametres_vocaux, pensee_enrichie,
     etat.memoire_tampon, bus_latent, logits_routage,
     indecision_c2) = etat.agent.penser(
        etat.etat_courant, memoire_avant, contexte, vecteur_bio_tensor,
        force_planification=etat.force_planification_jour,
        horizons_planification=HORIZONS_PLANIFICATION,
        gamma_planif=GAMMA_PLANIFICATION,
        obs_auditive=obs_auditive,
        plugs_c3_disponibles=plugs_c3_disponibles,
        # v41.2 — l'état du CORPS module la décision : `vigueur = énergie ** κ`, lue au
        # tick courant. C'est le point où le métabolisme entre dans le chemin cognitif.
        vigueur=etat.moteur_bio.vigueur(),
    )

    # --- v37.0 : accumulation de la télémétrie d'arbitrage ---
    # Uniquement sur ce point d'appel : c'est la décision MOTRICE réelle. Le tick vocal
    # isolé (plus haut) appelle aussi penser() mais sur une vision nulle, sans
    # environnement — l'y inclure polluerait la mesure du rapport de force C1/C2.
    mesure = getattr(etat.agent, "mesure_arbitrage", None)
    if mesure is not None:
        etat.amplitude_c1_jour += mesure["amplitude_c1"]
        etat.amplitude_c2_jour += mesure["amplitude_c2"]
        etat.gain_c1_jour += mesure["gain_c1"]
        etat.accord_c1c2_jour += mesure["accord"]
        # v41.14 — histogramme des votes de chaque voix (télémétrie pure).
        if "vote_c1" in mesure:
            etat.votes_c1_jour[mesure["vote_c1"]] = etat.votes_c1_jour.get(mesure["vote_c1"], 0) + 1
            etat.votes_c2_jour[mesure["vote_c2"]] = etat.votes_c2_jour.get(mesure["vote_c2"], 0) + 1
        etat.ticks_arbitrage_jour += 1

    etat.vecteurs_episodiques.append(bus_latent.detach())
    if len(etat.vecteurs_episodiques) > CAPACITE_MEMOIRE:
        etat.vecteurs_episodiques.pop(0)

    # --- Chantier 4 (v28.0) : application d'une réponse C3 EN ATTENTE, reçue lors
    # d'un tick précédent où ACTION_DEMANDER a été jouée (le bus répond après coup,
    # jamais dans le même pas que l'émission — voir plus bas où reponse_c3_en_attente
    # est peuplée). `confiance < SEUIL_OVERRIDE_C3` biaise les logits (même forme que
    # l'arbitrage C2, logits += force * préférence) ; `confiance >= SEUIL_OVERRIDE_C3`
    # impose l'action — le log_prob poussé plus bas reste alors celui de l'action
    # RÉELLEMENT jouée sous la distribution courante (dist.log_prob), jamais celui
    # d'un échantillon fictif, pour ne pas invalider le gradient REINFORCE.
    reponse_c3_en_attente = getattr(etat, "reponse_c3_en_attente", None)
    action_imposee_c3 = None
    if reponse_c3_en_attente is not None:
        etat.reponse_c3_en_attente = None
        preferences_c3 = torch.as_tensor(
            reponse_c3_en_attente.preferences, dtype=torch.float32, device=DEVICE
        ).view(1, -1)
        if reponse_c3_en_attente.confiance >= SEUIL_OVERRIDE_C3:
            action_imposee_c3 = int(torch.argmax(preferences_c3, dim=-1).item())
        else:
            logits_action = logits_action + FORCE_C3 * preferences_c3

    dist = torch.distributions.Categorical(logits=logits_action)
    if action_imposee_c3 is not None:
        action_item = action_imposee_c3
        log_prob_tick = dist.log_prob(torch.tensor(action_item, device=DEVICE))
    else:
        action = dist.sample()
        action_item = int(action.item())
        log_prob_tick = dist.log_prob(action)

    etat.log_probs_journee.append(log_prob_tick)
    etat.entropies_journee.append(dist.entropy())
    etat.valeurs_journee.append(valeur_estimee)

    # --- Cascade C1 → C2 → C3 (v28.0, Chantier 2a) : la 8ème action, "tendre la main"
    # vers l'Exocortex. Un choix APPRIS (REINFORCE), jamais un déclenchement sur seuil
    # (décision utilisateur explicite) — plugs_c3_disponibles n'a fait que déterminer
    # SI ce choix existait dans les logits, jamais QUAND le jouer.
    #
    # L'action réellement transmise à env.step() est TOUJOURS une des 7 actions
    # MiniGrid : quand ACTION_DEMANDER est choisie, on substitue l'action "done" (6),
    # seule action réellement neutre du jeu MiniGrid (déjà documentée comme telle dans
    # docs/fonctionnement/CHANGELOG.md v27.4 — agent immobile, aucun effet sur l'environnement) —
    # préserve les invariants d'env.step (agent_pos, murs, etc.) sans jamais inventer
    # un pas d'environnement fictif.
    #
    # La réponse (si obtenue) N'EST PAS appliquée à l'action de CE tick — elle est
    # mise en attente pour biaiser/imposer le PROCHAIN tick (voir reponse_c3_en_attente
    # ci-dessus) : le bus répond à une pensée déjà écoulée, jamais à celle qui vient de
    # se jouer, exactement comme un conseil qu'on ne peut suivre qu'à l'action d'après.
    reponse_c3 = None
    cout_requete_c3 = 0.0
    if action_item == ACTION_DEMANDER:
        requete = RequeteC3(
            latent=pensee_enrichie.detach().cpu().numpy().flatten(),
            num_actions=etat.agent.num_actions,
            indecision_c2=indecision_c2,
            erreur_jepa=float(getattr(etat, "derniere_erreur_jepa", 0.0)),
            palier_vocal=int(getattr(etat, "palier_vocal", 0)),
            mot_frontal=getattr(getattr(etat, "lecteur_case_frontale", None), "_mot_brut_courant", None),
        )
        if plugs_c3_disponibles:
            logits_routage_np = logits_routage.detach().cpu().numpy().flatten()
            # Canal de diffusion "1_X" = dernier index de DIM_ROUTAGE_C3 ; sinon on
            # route vers le plug dont le rang (ordre de plugs_c3_disponibles) a reçu
            # le plus grand logit parmi les indices adressables.
            idx_diffusion = DIM_ROUTAGE_C3 - 1
            rangs_plugs = list(range(min(len(plugs_c3_disponibles), DIM_ROUTAGE_C3 - 1)))
            meilleur_idx = max(rangs_plugs + [idx_diffusion], key=lambda i: logits_routage_np[i])
            if meilleur_idx == idx_diffusion:
                mode_emission, cible_emission = "1_X", None
            else:
                mode_emission = "1_1"
                cible_emission = plugs_c3_disponibles[meilleur_idx]
            reponses = etat.agent.port_c3.canal_emission(
                requete, mode=mode_emission, cible=cible_emission, tick_absolu=etat.tick_absolu
            )
            reponse_c3 = etat.agent.port_c3.agreger(reponses)
            # Mise en attente pour le PROCHAIN tick (voir reponse_c3_en_attente en
            # tête de fonction) — jamais appliquée au tick courant, déjà décidé.
            etat.reponse_c3_en_attente = reponse_c3
        cout_requete_c3 = COUT_REQUETE_C3
        action_effective_env = ACTION_ENV_NEUTRE_C3
    else:
        action_effective_env = action_item

    # --- v41.19 : SONDE DU COÛT MOTEUR RÉEL (télémétrie PURE, étape 1 du chantier) ---
    #
    # Objet : mesurer ce que chaque action FAIT réellement, pour pouvoir un jour DÉRIVER
    # son coût au lieu de le déclarer. `COUT_CORPOREL_PAR_ACTION` pose 7 valeurs a priori
    # (0.2 tourner, 0.5 avancer, 0.8 manipuler…) jamais confrontées à une mesure, alors
    # qu'elles pèsent 80 % de l'effort à chaque tick (violation n°1 de la revue du dogme,
    # `docs/recherche/REVUE_DOGME_17082026_rien_en_dur.md`).
    #
    # ⚠️ Cette sonde ne MODIFIE RIEN : elle lit la position et l'orientation avant/après le
    # `step` et accumule. `calculer_effort_metabolique` continue d'utiliser la table en
    # dur — c'est l'étape 2 qui la remplacera, une fois la distribution connue. Le run
    # reste bit-identique (aucune lecture de ces compteurs par la décision, le gradient
    # ou la dopamine).
    #
    # Trois grandeurs par action, parce que le coût physique d'un geste ne se lit pas sur
    # son index mais sur son EFFET :
    #   - deplacement : l'agent a-t-il changé de case ? (0 ou 1)
    #   - rotation    : a-t-il changé d'orientation ? (0 ou 1)
    #   - succes      : le monde a-t-il changé d'une façon ou d'une autre ? Un `forward`
    #                   contre un mur ne déplace rien : il coûte aujourd'hui 0,5 comme un
    #                   `forward` qui avance, alors qu'il ne produit aucun travail.
    _u = etat.env.unwrapped
    _pos_avant = tuple(_u.agent_pos)
    _dir_avant = int(_u.agent_dir)
    _porte_avant = _u.carrying is not None

    obs_suivante, recompense_env, termine, tronque, _ = etat.env.step(action_effective_env)

    # La lecture encadre le `step` lui-même : elle est donc valide à chaque tick, y
    # compris au premier de l'épisode (aucun `reset` ne s'intercale entre les deux).
    _stats = etat.cout_moteur_reel_jour.setdefault(
        int(action_effective_env),
        {"n": 0, "deplacement": 0, "rotation": 0, "portage_change": 0, "sterile": 0})
    _stats["n"] += 1
    # --- v41.27 : LA VITESSE D'IMPACT (formulation utilisateur : « compte le temps entre
    # deux cases et crée une formule de vitesse »). MiniGrid n'a pas de vitesse continue :
    # l'agent change de case ou non. La vitesse est donc l'INVERSE du nombre de ticks
    # écoulés depuis le dernier déplacement réussi — avancer à chaque tick donne 1,0,
    # piétiner donne une valeur qui s'effondre. Se cogner en pleine course pique ; se
    # cogner à l'arrêt, presque pas.
    _a_bouge = tuple(_u.agent_pos) != _pos_avant
    _a_tourne = int(_u.agent_dir) != _dir_avant
    _a_manipule = (_u.carrying is not None) != _porte_avant
    _stats["deplacement"] += int(_a_bouge)
    _stats["rotation"] += int(_a_tourne)
    _stats["portage_change"] += int(_a_manipule)
    # STÉRILE : rien n'a changé dans le monde. C'est la mesure qui manquait — elle dit
    # quelle fraction du barème actuel est facturée pour du travail qui n'existe pas.
    # v41.31 — L'INVARIANT PHYSIQUE UNIQUE DE NON-TRANSITION.
    #
    #   transition = (pos changée) OU (dir changée) OU (portage changé)
    #
    # ⚠️ LA ROTATION EST UNE TRANSITION. Tourner ne déplace pas l'agent mais PIVOTE SON
    # CHAMP DE VISION : c'est une acquisition d'information, la brique de base de
    # l'exploration. L'exclure reviendrait à punir le fait de regarder.
    #
    # ⚠️ LE VECTEUR BIO EST EXCLU. Faim, soif, douleur et thermoception dérivent à CHAQUE
    # tick par le seul métabolisme : un critère qui les inclurait ne détecterait JAMAIS de
    # non-transition, la condition serait mathématiquement toujours fausse.
    #
    # C'est le détecteur de référence : `mur_touche` s'y aligne plus bas (v41.31), pour que
    # la douleur et le gradient ne punissent plus deux ensembles différents (mesuré avant
    # unification : 61,7 % contre 29,9 %, soit un facteur 2).
    etat.transition_tick = bool(_a_bouge or _a_tourne or _a_manipule)
    _stats["sterile"] += int(not etat.transition_tick)
    # v41.31 — LE BUFFER DU MASQUE, aligné tick à tick sur `log_probs_journee`.
    #
    # ⚠️ L'ORDRE DES OPÉRATIONS IMPOSE UN BUFFER. `log_prob` est empilé AVANT `env.step`
    # (l'agent doit choisir avant d'agir) ; la transition n'est connue qu'APRÈS. On ne
    # peut donc pas masquer à l'empilement — seulement au calcul de la perte, où les deux
    # séries se rejoignent. L'alignement est vérifié là-bas par une égalité de longueur :
    # au moindre décalage, le masque est ignoré plutôt qu'appliqué de travers.
    etat.transitions_journee.append(etat.transition_tick)

    # v41.48 — LE RENDEMENT MÉCANIQUE DU TICK, aligné sur le même buffer.
    #
    #     rendement = travail_utile / travail_engagé   ∈ [0, 1]
    #
    # Le dénominateur est le travail que `calculer_effort_metabolique` facture (v41.28 :
    # le travail TENTÉ, jamais le travail réussi — pousser un mur coûte autant que pousser
    # une porte qui cède). Le numérateur est la part de ce travail qui a effectivement
    # déplacé quelque chose dans le monde.
    #
    # ⚠️ AUCUN COEFFICIENT N'EST POSÉ. Le rendement est un rapport de deux travaux déjà
    # dérivés de la géométrie (translation d'une case, moment d'inertie d'un disque) : il
    # vaut exactement 1 quand le geste aboutit et 0 quand il brasse du vent. Les deux
    # bornes sortent de la physique, pas d'un réglage.
    #
    # ⚠️ LA ROTATION A UN RENDEMENT DE 1. Tourner PIVOTE le champ de vision : c'est une
    # acquisition d'information, la brique de base de l'exploration (même raison qu'en
    # v41.31, où la rotation est une transition à part entière). La punir reviendrait à
    # punir le fait de regarder.
    # 🔴 CE QUI LE DISTINGUE DU MASQUE v41.31 — sans quoi il n'ajouterait RIEN.
    #
    # Le masque rejette un tick sans transition (0 ou 1) et ANNULE déjà tout ce qui n'a
    # rien changé. Un rendement calqué sur `transition_tick` serait donc un DOUBLON exact,
    # et les deux bras d'une campagne sortiraient identiques — vérifié le 01/09 sur 3 jours
    # appariés, c'est exactement ce qui s'est produit à la première écriture de ce bloc.
    #
    # Le rendement mesure autre chose : le TRAVAIL MÉCANIQUE LIVRÉ rapporté au TRAVAIL
    # ENGAGÉ. Il départage ce que le masque confond — une ROTATION est une transition
    # pleine (le masque la garde à 1) mais elle ne déplace RIEN dans l'espace ; un PAS
    # déplace une masse d'une case entière. Les deux travaux sont déjà dérivés par
    # `calculer_effort_metabolique` (v41.28), de la géométrie seule :
    #
    #     translation d'une case : W = M · PAS_GRILLE
    #     rotation du disque     : W = ½ M r²,  r = PAS_GRILLE / 2
    #
    # ⚠️ AUCUN COEFFICIENT POSÉ : le rapport des deux (8×) sort du disque et de la grille,
    # c'est l'invariant géométrique déjà inscrit dans les invariants v41.28 (« le ratio
    # locomotion/manipulation est GÉOMÉTRIQUE, pas un réglage »). On réutilise les mêmes
    # quantités plutôt que d'en dériver de nouvelles.
    # La masse se SIMPLIFIE dans le rapport : elle figure aux deux numérateur et
    # dénominateur, donc le rendement ne dépend que de la géométrie. C'est ce qui le rend
    # invariant à la croissance du corps (la masse évolue avec la neurogenèse).
    _w_pas = PAS_GRILLE                            # M · PAS_GRILLE,  M simplifié
    _w_rot = 0.5 * (PAS_GRILLE / 2.0) ** 2         # ½ M r²,          M simplifié
    if action_item == ACTION_DEMANDER:
        # Seule action sans travail musculaire (elle n'atteint pas le monde physique) :
        # rendement neutre, sinon interroger C3 serait puni comme un geste raté.
        _rendement_tick = 1.0
    elif _a_bouge:
        _rendement_tick = 1.0                      # une masse a franchi une case
    elif _a_tourne or _a_manipule:
        # Le champ de vision a pivoté, ou l'inventaire a changé : travail réel, mais
        # d'un ordre géométrique inférieur. La rotation N'EST PAS punie (elle reste la
        # brique de base de l'exploration, invariant v41.31) — elle est simplement
        # créditée à la hauteur de ce qu'elle déplace.
        _rendement_tick = _w_rot / _w_pas
    else:
        _rendement_tick = 0.0                      # le muscle s'est contracté, rien n'a bougé
    etat.rendements_journee.append(_rendement_tick)

    # v41.20 — L'EFFET DU TICK COURANT, retenu pour la facturation plus bas. La sonde
    # v41.19 n'agrégeait que des compteurs journaliers ; ici on conserve le tick lui-même,
    # parce que `calculer_effort_metabolique` doit facturer CE geste, pas une moyenne.
    etat.effet_moteur_tick = {"deplacement": bool(_a_bouge), "rotation": bool(_a_tourne),
                              "porte_objet": _u.carrying is not None}

    # v41.27 — horloge de déplacement, base de la vitesse d'impact.
    if _a_bouge:
        etat.vitesse_agent = 1.0 / max(1, getattr(etat, "ticks_depuis_deplacement", 1))
        etat.ticks_depuis_deplacement = 1
    else:
        etat.ticks_depuis_deplacement = getattr(etat, "ticks_depuis_deplacement", 1) + 1

    # --- v41.25 : LA DOULEUR SE FACTURE LÀ OÙ LE CORPS EST ARRIVÉ ---
    #
    # 🔴 LE PIÈGE, et il est subtil. La thermoception est lue en tête de tick (avec tout
    # le vecteur sensoriel), donc AVANT ce `step` : c'est la chaleur de la case QUITTÉE.
    # `step_metabolisme` s'exécute lui APRÈS. Sans cette relecture, l'agent qui marche
    # dans la lave paierait la température de la case d'où il vient — soit ~0.45 au lieu
    # de 1.0 — et, l'épisode se terminant aussitôt, il ne ressentirait JAMAIS T=1. Le
    # signal le plus important du mécanisme serait précisément celui qui n'arrive pas.
    #
    # C'est le même défaut de décalage temporel que la v41.5 avait corrigé sur la
    # maturité, et il se reproduit ici pour la même raison : une grandeur lue en tête de
    # tick et consommée en queue traverse un `env.step` qui l'a périmée.
    #
    # ⚠️ La perception (`signaux_sensoriels`, ce que le CERVEAU voit) n'est pas touchée :
    # elle reste celle du début de tick, cohérente avec la décision qui vient d'être
    # prise. Seule la facturation homéostatique est réalignée sur la position réelle.
    if _thermo:
        try:
            # v41.25-fix1 — on STOCKE, on n'applique pas. Écrire `moteur_bio.chaleur` ici
            # ferait porter la MÊME chaleur aux deux mesures de déficit de
            # `step_metabolisme`, et la soustraction l'annulerait intégralement (mesuré :
            # écart de 0,000000). La valeur est passée en argument plus bas, pour être
            # appliquée ENTRE `deficit_avant` et `deficit_apres`.
            etat.chaleur_apres_step = etat.bus_sensoriel.chaleur_seule(etat.env)
        except Exception:
            etat.chaleur_apres_step = None   # capteur en échec : pas de transition

    if masquer_recompense_externe:
        # École de Rattrapage Vocal / Paradigme Bébé (v25.0, expérimental) : l'agent
        # "n'a aucune idée s'il fait bien ou mal" avant JOUR_FIN_MASQUAGE_EXTERNE — ce
        # gel neutralise à la fois recompense_interne (plus bas) ET poids_evenement
        # (plus de choc dopaminergique "victoire", plus de victoire_aujourdhui, donc
        # plus de promotion de niveau MiniGrid tant que le masquage est actif). termine
        # / tronque restent inchangés (la fin d'épisode MiniGrid reste réelle) — seul le
        # SIGNAL de récompense est verrouillé, pas la mécanique de l'environnement.
        recompense_env = 0.0
    etat_suivant = encoder(obs_suivante)
    etat.fin_episode = bool(termine or tronque)

    # --- v41.25 : LE COMPTAGE DES MORTS (instrumentation du même commit) ---
    # `termine` sans récompense = l'épisode s'est arrêté sans victoire. Sur un banc à
    # lave c'est une mort par le danger ; MiniGrid la punit par exactement 0.0, ce qui
    # est précisément le trou que la nociception vient combler. C'est la mesure de
    # SURVIE de la campagne : elle doit baisser dans le bras qui a mal.
    # ⚠️ `termine` seul ne suffit pas à juger d'un succès (invariant v35.0) — c'est la
    # même raison qui le rend, ici, exactement le bon signal pour compter les échecs.
    if termine:
        # --- v41.27 : MOURIR COÛTE LA JOURNÉE (option (b), décision utilisateur 19/08) ---
        #
        # `termine` sans récompense = l'agent est mort. Jusqu'ici il repartait au tick
        # suivant, si bien que mourir ne coûtait RIEN : mesuré, 7 800 à 18 500 morts par
        # run de 300 jours. Désormais la journée s'arrête là — l'agent perd ses ticks
        # restants, la nuit tombe, il repart le lendemain.
        #
        # ⚠️ L'utilisateur assume que c'est une convention (« même si c'est tricher ») :
        # une vraie mort terminerait le run, mais aucun cerveau ne dépasserait le jour 2
        # (206 morts sur 300 épisodes mesurées), donc plus rien ne serait apprenable. Le
        # coût est réel sans être terminal — l'agent a le temps d'apprendre à l'éviter.
        if recompense_env <= 0 and MORT_COUTE_LA_JOURNEE:
            etat.mort_du_jour = True
        if recompense_env > 0:
            etat.episodes_gagnes_jour = getattr(etat, "episodes_gagnes_jour", 0) + 1
        else:
            etat.morts_jour = getattr(etat, "morts_jour", 0) + 1
            # La chaleur au moment de la fin : ~1.0 si l'agent est DANS la source.
            etat.chaleur_a_la_mort_jour = (
                getattr(etat, "chaleur_a_la_mort_jour", 0.0)
                + float(getattr(etat.moteur_bio, "chaleur", 0.0)))
    elif tronque:
        etat.episodes_epuises_jour = getattr(etat, "episodes_epuises_jour", 0) + 1
    # v28.0 : l'action "done" substituée pour ACTION_DEMANDER laisse l'observation
    # inchangée PAR CONSTRUCTION (agent immobile) — ce n'est jamais un mur touché,
    # juste l'agent qui a choisi de tendre la main plutôt que de bouger.
    # v41.31 — `mur_touche` S'ALIGNE SUR L'INVARIANT PHYSIQUE, plus sur l'observation.
    #
    # 🔴 CE QUE ÇA CORRIGE. `torch.equal(etat_courant, etat_suivant)` ne lit que le champ
    # visuel partiel encodé : il peut rester identique alors que le monde a changé (le
    # changement est hors champ), ou différer alors que rien n'a bougé. Mesuré : ce
    # détecteur voyait 29,9 % des ticks quand l'invariant physique en voit 61,7 % — un
    # FACTEUR 2. Or `mur_touche` alimente la douleur (v41.27) et l'invariant alimente
    # désormais le gradient (v41.31) : laisser les deux diverger ferait punir DEUX
    # ENSEMBLES DIFFÉRENTS par deux mécaniques croyant parler du même geste.
    #
    # ⚠️ L'exclusion d'ACTION_DEMANDER reste : le `done` substitué laisse l'agent immobile
    # PAR CONSTRUCTION (v28.0), ce n'est jamais un mur touché.
    if UNIFIER_DETECTEUR_STERILITE:
        mur_touche = (action_item != ACTION_DEMANDER) and not getattr(etat, "transition_tick", True)
    else:
        mur_touche = (action_item != ACTION_DEMANDER) and torch.equal(etat.etat_courant, etat_suivant)
    # v41.27 — LE CHOC EST UNE DOULEUR, pas un malus. Pic ∝ vitesse d'impact (v41.27),
    # récupération RAPIDE (DEMI_VIE_CHOC ≈ 12× plus courte que la brûlure) : ça pique fort
    # et ça passe. Encaissé AVANT `step_metabolisme`, donc le déficit du tick le voit.
    if mur_touche:
        # La vitesse retenue est celle du DERNIER déplacement réussi : l'agent qui avançait
        # vite et percute paie cher, celui qui piétinait déjà ne se fait presque rien.
        etat.moteur_bio.encaisser_douleur(
            float(getattr(etat, "vitesse_agent", 0.0)), DEMI_VIE_CHOC)
        etat.chocs_muraux_jour = getattr(etat, "chocs_muraux_jour", 0) + 1

    # --- Muscle de la Volonté : Sursaut avant l'abandon (v17.0 ; continu v40.1-fix4) ---
    #
    # L'ancien `if etat.mode_libre` réservait le second souffle au-delà du palier 5 — un
    # interrupteur cognitif. Le DÉCLENCHEMENT reste un événement discret (95 % du budget,
    # une fois par épisode : c'est une action, pas un régime), mais son AMPLEUR suit
    # désormais l'envie de vivre : à envie pleine, extension et boost identiques à l'ancien
    # Mode Libre ; à envie nulle, un sursaut qui ne porte rien — l'agent n'a plus la force
    # de son second souffle. « L'envie de vivre pousse au maximum à essayer quand même » :
    # le sursaut est littéralement cette phrase, son intensité ne pouvait pas être binaire.
    _envie = etat.agent.envie_de_vivre
    # v41.30 — le sursaut est plafonné par le budget RÉEL de la carte (`max_steps`), plus
    # par la constante fossile `PATIENCE_MAX`. Étirer la patience au-delà de ce que
    # l'environnement accorde n'a jamais eu d'effet : MiniGrid coupe l'épisode de toute façon.
    sursaut_declenche, etat.patience_jour = etat.sursaut_volonte.evaluer_tick(
        etat.ticks_episode_courant, etat.patience_jour,
        _budget_natif_carte(etat.env), etat.fin_episode,
        facteur=_envie
    )
    if sursaut_declenche:
        etat.teneur_dopamine += BOOST_SECOND_SOUFFLE * _envie
        etat.teneur_dopamine = float(np.clip(etat.teneur_dopamine, DOPAMINE_MIN, DOPAMINE_MAX))
        etat.sursauts_jour += 1
        etat.a_utilise_sursaut_episode = True
        print(f"   🔥 Sursaut de Volonté ! Patience étirée à {etat.patience_jour} ticks.")

    # --- Potentiomètre d'acceptation : abandon lucide si la patience du jour est dépassée ---
    abandon_par_patience = False
    if not etat.fin_episode and etat.ticks_episode_courant >= etat.patience_jour:
        etat.fin_episode = True
        tronque = True
        abandon_par_patience = True
        etat.abandons_patience_jour += 1

    # --- Pression cinétique multimodale (générique, tous niveaux, v16.0) ---
    penalite_stagnation = etat.thermostat_cinetique.evaluer_tick(etat.env, action_item)
    etat.penalite_stagnation_jour += penalite_stagnation

    # --- Jalons DoorKey (spécifique) ---
    palier_ce_tick, micro_recompense, poids_palier, recompense_continue = 0, 0.0, 0.0, 0.0
    if etat.doorkey_actif:
        palier_ce_tick, micro_recompense, poids_palier, recompense_continue = etat.detecteur.evaluer_tick(
            etat.env, action_item, recompense_env
        )
        # v35.1 — accumulé APRÈS l'atténuation (voir plus bas) : cette métrique doit
        # refléter l'aide RÉELLEMENT versée, c'est elle qui rendra le sevrage visible.
        # v33.0-etape0 — chronométrage des jalons, APRÈS le détecteur de paliers pour
        # observer le même tick, mais sans rien lui retourner : cet appel ne produit ni
        # récompense ni poids de choc (voir ChronometreJalonsDoorKey).
        etat.chronometre_jalons.evaluer_tick(
            etat.env, etat.ticks_episode_courant, recompense_env
        )

    # --- Franchissement de portes (générique, tous niveaux) ---
    nb_portes, micro_recompense_porte, poids_porte = etat.detecteur_portes.evaluer_tick(etat.env)
    etat.portes_franchies_jour += nb_portes

    # --- Progrès personnel (générique, hors DoorKey — v33.0-etape0.5 : et sur DoorKey
    # en Mode Libre si QUETE_AUTO_EN_MODE_LIBRE, voir _quete_auto_active) ---
    micro_recompense_progres, poids_progres = 0.0, 0.0
    if _quete_auto_active(etat):
        micro_recompense_progres, poids_progres = etat.detecteur_progres.evaluer_tick(etat.env)
        if micro_recompense_progres > 0:
            etat.progres_personnel_jour += 1

    # --- v35.1 : LE GUIDAGE DÉGRESSIF, appliqué en UN SEUL POINT ---
    #
    # Les deux sources d'aide — `recompense_continue` (DoorKey) et
    # `micro_recompense_progres` (records de proximité, générique) — passent par le même
    # curseur `etat.facteur_guidage_jour`, calculé une fois par jour dans
    # `demarrer_journee`. Un seul point d'application : deux atténuations séparées
    # finiraient par diverger, et c'est exactement le défaut du Mode Libre qu'on corrige.
    #
    # ⚠️ Le COMPTEUR (`progres_personnel_jour`) est incrémenté AVANT l'atténuation : il
    # mesure « l'agent a-t-il battu son record ? », un fait, pas la récompense qu'on lui
    # verse pour ça. Les atténuer ensemble rendrait la télémétrie illisible au moment
    # précis où on veut observer le sevrage.
    # v40.1-fix4 — `min(_g, 1.0)` au lieu de `if _g < 1.0` : strictement équivalent (le
    # filet > 1 ne doit pas amplifier ces récompenses, seul le sevrage < 1 les atténue),
    # mais écrit comme la saturation qu'il est, pas comme une branche.
    _g = min(etat.facteur_guidage_jour, 1.0)
    recompense_continue *= _g
    micro_recompense_progres *= _g
    poids_progres *= _g
    etat.guidage_but_journee += recompense_continue

    attente = etat.agent.generer_attente_reelle(pensee_enrichie, action_item)
    # Cortex auditif prédictif (v22.0, décision utilisateur : JEPA audio dès le
    # départ ; têtes séparées depuis v22.1, correctif défaut 3) : la cible auditive du
    # tick est le son que le tuteur vient d'injecter à CE tick (le protocole étant
    # stateless par paquet, on n'a pas de "son suivant" séparé à ce stade — l'agent
    # apprend donc à prédire, à partir de son état d'avant action, le son qu'il est en
    # train d'entendre/produire maintenant). Silence (obs_auditive=None) → comportement
    # strictement identique à avant v22.0 (coeff_jepa_audio reste sans effet).
    attente_audio = None
    coeff_jepa_audio = 0.0
    if obs_auditive is not None:
        etat.ticks_audio_recus += 1
        coeff_jepa_audio = COEFF_JEPA_AUDIO_MAX * min(1.0, etat.ticks_audio_recus / RAMPE_JEPA_AUDIO)
        attente_audio = etat.agent.generer_attente_audio_reelle(pensee_enrichie, action_item)
    perte_tick = etat.agent.perte_jepa(
        attente, etat_suivant, attente_audio=attente_audio,
        obs_auditive_suivante=obs_auditive, coeff_jepa_audio=coeff_jepa_audio,
    )
    etat.jepa_losses.append(perte_tick)
    valeur_erreur = float(perte_tick.item())
    etat.erreur_journee += valeur_erreur
    # v41.13 — ventilation JEPA (télémétrie pure, voir perte_jepa). `getattr` car un
    # cerveau n'ayant encore jamais calculé de perte n'a pas ces attributs.
    _ag = etat.agent
    etat.jepa_concentration_cumul_jour = (getattr(etat, "jepa_concentration_cumul_jour", 0.0)
                                          + getattr(_ag, "jepa_diag_concentration", 0.0))
    etat.jepa_amplitude_cumul_jour = (getattr(etat, "jepa_amplitude_cumul_jour", 0.0)
                                      + getattr(_ag, "jepa_diag_amplitude_cible", 0.0))
    etat.jepa_err_max_dim_jour = max(getattr(etat, "jepa_err_max_dim_jour", 0.0),
                                     getattr(_ag, "jepa_diag_erreur_max_dim", 0.0))
    etat.derniere_erreur_jepa = valeur_erreur  # v28.0 : contexte neutre pour la prochaine RequeteC3

    # --- Sous-quête intrinsèque par curiosité JEPA (générique, v17.0 ; continue v40.1-fix4) ---
    #
    # L'ancien `if etat.mode_libre` était un interrupteur cognitif : la curiosité passait
    # de 0 à 100 % au franchissement du palier 5. Elle est désormais TOUJOURS évaluée et
    # pondérée par l'ACCEPTATION (envie × confiance, v40.1) — le même continuum qui pilote
    # déjà le poids de C2. Le profil reproduit l'intention d'origine sans le seuil : un
    # débutant (f≈0) a une curiosité quasi nulle exactement comme l'ancien mode guidé, un
    # agent mûr la déploie comme l'ancien mode libre, et un agent qui a perdu l'envie
    # cesse d'être curieux — ce que l'interrupteur était incapable d'exprimer.
    sous_objectif_intrinseque, poids_curiosite = etat.detecteur_curiosite.evaluer_tick(valeur_erreur)
    _acc = etat.agent.acceptation()
    sous_objectif_intrinseque *= _acc
    poids_curiosite *= _acc
    if sous_objectif_intrinseque > 0:
        etat.sous_objectifs_curiosite_jour += 1

    # --- Moteur homéostatique biologique (générique, tous niveaux, v18.0) ---
    agent_pos_bio = tuple(etat.env.unwrapped.agent_pos) if _MINIGRID_INTERNALS_OK else None
    nouvelle_case_visitee = agent_pos_bio is not None and agent_pos_bio not in etat.positions_visitees_episode
    if agent_pos_bio is not None:
        etat.positions_visitees_episode.add(agent_pos_bio)

    # v41.20 — l'effort est facturé sur l'EFFET RÉEL du geste (mesuré autour du `step`
    # 170 lignes plus haut), plus sur l'index de l'action. `valeur_erreur` est l'erreur
    # JEPA du tick : elle porte l'éveil (une surprise mobilise l'attention, donc coûte).
    _eff = getattr(etat, "effet_moteur_tick", None) or {}
    effort_metabolique = etat.moteur_bio.calculer_effort_metabolique(
        action_item, etat.force_planification_jour, HORIZONS_PLANIFICATION,
        dim_bus=etat.agent.dim_bus,
        deplacement=_eff.get("deplacement"),
        rotation=_eff.get("rotation", False),
        porte_objet=_eff.get("porte_objet", False),
        erreur_jepa=float(valeur_erreur),
    )
    r_bio, _quete_bio = etat.moteur_bio.step_metabolisme(
        cout_action=effort_metabolique, erreur_jepa=valeur_erreur,
        nouvelle_case_visitee=nouvelle_case_visitee,
        # v41.25-fix1 — la chaleur de la case ATTEINTE, appliquée entre les deux mesures
        # de déficit. C'est la TRANSITION thermique qui fait mal, jamais le niveau seul.
        chaleur_apres=getattr(etat, "chaleur_apres_step", None),
    )
    etat.r_bio_jour += r_bio
    etat.effort_metabolique_jour += effort_metabolique

    # --- v34.0-etape0 : TÉLÉMÉTRIE PURE (lecture seule, aucun effet sur la décision) ---
    # Tout ce bloc ne fait que LIRE des valeurs déjà calculées ci-dessus. Il n'écrit dans
    # aucune variable consommée par penser(), le gradient ou la dopamine — c'est ce qui
    # garantit l'invariance d'empreinte à graine fixée.
    etat.effort_max_jour = max(etat.effort_max_jour, effort_metabolique)
    etat.effort_min_jour = (effort_metabolique if etat.effort_min_jour is None
                            else min(etat.effort_min_jour, effort_metabolique))
    if 0 <= action_item < 7:
        etat.effort_par_action_jour[action_item][0] += 1
        etat.effort_par_action_jour[action_item][1] += effort_metabolique

    # Le déficit est la distance à l'équilibre idéal (voir calculer_deficit) : c'est lui
    # qui portera le futur seuil de mort, donc il faut connaître sa plage réelle AVANT.
    deficit_tick = etat.moteur_bio.calculer_deficit()
    etat.deficit_cumul_jour += deficit_tick
    etat.deficit_max_jour = max(etat.deficit_max_jour, deficit_tick)

    seuil = etat.moteur_bio.seuil_critique
    jauges = (etat.moteur_bio.satiete, etat.moteur_bio.hydratation,
              etat.moteur_bio.stimulation)
    if min(jauges) < seuil:
        etat.ticks_deficit_critique_jour += 1
    else:
        # « Saines » = les 3 jauges au-dessus du seuil critique SANS intervention
        # extérieure. C'est la définition opérationnelle de l'autonomie (§3.3).
        etat.ticks_jauges_saines_jour += 1
    etat.jauge_min_satiete_jour = min(etat.jauge_min_satiete_jour, jauges[0])
    etat.jauge_min_hydratation_jour = min(etat.jauge_min_hydratation_jour, jauges[1])
    etat.jauge_min_stimulation_jour = min(etat.jauge_min_stimulation_jour, jauges[2])
    # v41.2 — le second étage : l'énergie réellement disponible et la vigueur qu'elle
    # produit (`énergie ** κ`), qui module C1, C2, le déficit et la plasticité.
    _energie = etat.moteur_bio.energie
    _vigueur = etat.moteur_bio.vigueur()
    etat.energie_cumul_jour += _energie
    etat.energie_min_jour = min(etat.energie_min_jour, _energie)
    etat.vigueur_cumul_jour += _vigueur
    etat.vigueur_min_jour = min(etat.vigueur_min_jour, _vigueur)
    if _energie < SEUIL_CRITIQUE_BIO:
        etat.ticks_energie_basse_jour += 1

    # v41.2-fix5 — l'action du tick est transmise : manger n'est plus un effet de bord du
    # déplacement mais un geste volontaire (voir DetecteurRessourcesBiologiques.evaluer_tick).
    # v41.32-etape2 — sonde de fourrage, AVANT `evaluer_tick` : celui-ci retire la
    # ressource de la grille en cas de succès, donc mesurer après ferait disparaître
    # l'occasion qu'on veut compter.
    _sonder_fourrage(etat, action_item)
    # v41.32-etape4 — même position que la sonde de fourrage, et pour la même raison :
    # `evaluer_tick` retire la ressource de la grille en cas de succès.
    _sonder_discrimination(etat, action_item)
    mange_food, mange_water = etat.detecteur_ressources_bio.evaluer_tick(etat.env, action_item)
    # v41.2-fix7 — LE SOULAGEMENT EST CRÉDITÉ AU GESTE QUI L'A PRODUIT.
    #
    # `r_bio` a été calculé plus haut (avant la consommation) et sera additionné à
    # `recompense_interne` plus bas. Sans le rattrapage qui suit, le soulagement d'avoir
    # mangé tombait donc au tick SUIVANT, sur une action sans rapport — et l'agent ne
    # pouvait pas apprendre l'association « ce geste-ci m'a soulagé ».
    #
    # C'est la boucle corporelle de base : le nourrisson porte tout à la bouche, la plupart
    # du temps sans effet ; quand il a faim, le geste soulage. Le corps renforce alors le
    # geste — et quand il n'a plus faim, manger ne soulage plus rien, donc ne renforce plus.
    # Aucune règle n'interdit de manger repu : mesuré, manger rassasié rapporte **−0,0227**
    # (le gain est nul et le geste coûte 0,8 d'effort), contre **+0,7945** affamé, soit un
    # contraste de 15×. L'association « manger = besoin » est donc apprenable par le seul
    # gradient, sans qu'aucun `if` ne la déclare.
    deficit_avant_repas = etat.moteur_bio.calculer_deficit()
    poids_ressource_bio = 0.0
    if mange_food:
        etat.moteur_bio.consommer_ressource("FOOD")
        # v29.0 — le GOÛT : une bouchée laisse une trace rémanente dans le vecteur bio,
        # décroissante sur ~10 ticks (voir BusSensoriel.DECROISSANCE_GOUT). Signalé ici,
        # au moment exact de la consommation, pour rester synchronisé avec les jauges.
        etat.bus_sensoriel.signaler_consommation("FOOD")
        etat.food_consommes_jour += 1
        etat.chronometre_jalons.signaler_consommation_post_cle()  # v33.0-etape0, conflit viscéral
        poids_ressource_bio = POIDS_CHOC_RESSOURCE_BIO
        # v41.7 — l'écriture mémoire a été DÉPLACÉE plus bas, après le calcul du
        # soulagement : elle avait lieu ici avec une intensité nulle par défaut.
    if mange_water:
        etat.moteur_bio.consommer_ressource("WATER")
        etat.bus_sensoriel.signaler_consommation("WATER")  # v29.0, voir FOOD ci-dessus
        etat.water_consommes_jour += 1
        etat.chronometre_jalons.signaler_consommation_post_cle()  # v33.0-etape0, conflit viscéral
        poids_ressource_bio = POIDS_CHOC_RESSOURCE_BIO
        # v41.7 — idem : écriture déplacée après le calcul du soulagement.

    # v41.2-fix7 — le soulagement réel, mesuré sur le déficit AVANT/APRÈS l'ingestion, et
    # ajouté au `r_bio` de CE tick — donc crédité à l'action qui l'a produit. Même unité et
    # même échelle que le `r_bio` ordinaire (une différence de déficit), donc rien de
    # nouveau n'entre dans la récompense : c'est le même signal, rendu à son auteur.
    if mange_food or mange_water:
        soulagement = deficit_avant_repas - etat.moteur_bio.calculer_deficit()
        r_bio += soulagement
        etat.soulagement_repas_jour += soulagement

        # ⚠️ v41.7 — LE SOULAGEMENT EST AUSSI ÉCRIT DANS LA MÉMOIRE.
        #
        # Défaut mesuré sur 6 runs × 1000 jours : `enregistrer_evenement` était appelé
        # pour "FOOD"/"WATER" **sans `intensite`**, donc avec sa valeur par défaut de
        # **0.0** — alors que le seul autre appelant (`_memoriser_si_saillant`, l. 5550)
        # transmet bien la sienne.
        #
        # Conséquence, lue dans le bilan de nuit après 1000 jours :
        #
        #     ↑ 'goal' +0.515 (×1037)      ← appris, valence positive
        #     ↓ 'FOOD' +0.000 (×4004)      ← QUATRE MILLE repas, valence RIGOUREUSEMENT NULLE
        #
        # L'agent apprenait la valeur du but et **jamais** celle de la nourriture. Le
        # mécanisme d'abstraction par récurrence (v36.0) et l'empreinte de type (v39.0)
        # tournaient à vide sur les ressources : ils moyennaient des zéros. C'est
        # cohérent avec la mesure du §Q2 — après 1000 jours, l'agent mange **comme un
        # marcheur aléatoire** (4,0 contre 4,4 unités/jour).
        #
        # Le soulagement réel est déjà calculé ici, dans la même unité que toute autre
        # intensité (une différence de déficit) : rien de nouveau n'entre dans le
        # système, on cesse seulement de jeter une information qui existait déjà.
        #
        # ⚠️ Rien n'est déclaré pour autant : `intensite` est **mesurée**, jamais posée.
        # Manger rassasié écrit une intensité quasi nulle, manger affamé une intensité
        # forte — l'agent apprend la valeur de la nourriture *par ce qu'elle lui fait*,
        # jamais par une table `FOOD = bon`. L'invariant v36.0 (« rien n'est expliqué au
        # cerveau ») est respecté.
        pos_repas = tuple(etat.env.unwrapped.agent_pos)
        if mange_food:
            etat.memoire_episodique_spatiale.enregistrer_evenement(
                pos_repas, "FOOD", etat.tick_absolu, intensite=soulagement)
        if mange_water:
            etat.memoire_episodique_spatiale.enregistrer_evenement(
                pos_repas, "WATER", etat.tick_absolu, intensite=soulagement)

    # --- Récompense de formants ET perte vocale supervisée (v22.0, corrigé v22.1,
    # score mixte formants+spectral en v27.0) : uniquement quand une leçon vocale est
    # active côté tuteur (formants_cibles fourni). Voir _evaluer_production_vocale pour
    # le détail (score détaché pour la récompense/dopamine, perte MSE NON détachée pour
    # le vrai gradient d'apprentissage — v22.1, correctif du "membre fantôme").
    poids_vocal, micro_recompense_vocale, _score_formants, _score_spectral = _evaluer_production_vocale(
        etat, parametres_vocaux, formants_cibles, cible_vocale,
        mfcc_references=mfcc_references, avec_micro_recompense=True,
    )
    etat.score_formants_jour = getattr(etat, "score_formants_jour", 0.0) + _score_formants
    etat.score_spectral_jour = getattr(etat, "score_spectral_jour", 0.0) + _score_spectral

    # v27.5 (correctif utilisateur, "boucle infinie de promotion vocale") : version
    # pondérée par la maîtrise déjà acquise (voir facteur_nouveaute_vocale), UNIQUEMENT
    # pour la dopamine et le bonus RL — poids_vocal brut reste utilisé au-dessus pour la
    # perte MSE (déjà calculée dans _evaluer_production_vocale) et pour score_vocal_jour/
    # la promotion de palier, qui ne doivent jamais s'auto-invalider.
    _facteur_nouveaute = facteur_nouveaute_vocale(etat)
    poids_vocal_dopamine = poids_vocal * _facteur_nouveaute
    micro_recompense_vocale *= _facteur_nouveaute

    # --- DOPAMINE UNIFIÉE MULTIMODALE (v27.0) ---
    # Jusqu'en v26.0 : poids_evenement = max(canaux visuels…, canal vocal) — un seul
    # canal "gagnait" le tick, l'autre était intégralement ignoré. Un agent qui franchit
    # une porte ET prononce son nom au même tick recevait la même dopamine que s'il
    # n'avait fait que l'un des deux : le contraire exact de ce qu'on veut d'un cerveau
    # synesthésique (décision utilisateur v27.0 : "la dopamine est la même pour la vue
    # que pour l'ouïe, il faudrait recalculer avec pondération").
    #
    # Agrégation PROBABILISTE ("OU doux") entre deux agrégats modaux :
    #     visuel = max(recompense_env, poids_palier, poids_porte, poids_progres,
    #                  poids_curiosite, poids_ressource_bio)        # max interne inchangé
    #     poids_evenement = 1 - (1 - w_v*visuel) * (1 - w_a*vocal)
    #
    # Trois propriétés, et pas une simple somme pondérée :
    #  1. BORNÉE PAR CONSTRUCTION dans [0,1] — invariant NON NÉGOCIABLE : poids_evenement
    #     est facteur du choc (DOPAMINE_MAX - d)*TAUX_CHOC_BASE*poids et de
    #     micro_boost_ancrage. Une somme pondérée exigerait un clip explicite : un
    #     pansement, pas une borne.
    #  2. RÉTROCOMPATIBLE À L'IDENTIQUE sans audio : poids_vocal = 0 et
    #     POIDS_DOPAMINE_VISUEL = 1.0 donnent 1 - (1 - visuel)*(1 - 0) = visuel =
    #     exactement le max() d'avant v27.0. Tous les runs MiniGrid purs conservent leur
    #     dynamique au bit près.
    #  3. MONOTONE ET SANS ÉCRASEMENT : chaque canal augmente strictement le résultat, et
    #     un canal saturé n'annule pas l'autre — contrairement au max (canal faible
    #     perdu) et à une moyenne (un canal nul DILUERAIT un canal excellent : régression).
    poids_visuel = max(1.0 if recompense_env > 0 else 0.0, poids_palier, poids_porte,
                       poids_progres, poids_curiosite, poids_ressource_bio)

    # --- Chantier 4 (v28.0) : Registre d'Assimilation — 3ème canal du "OU doux" ---
    # Un conseil C3 alimente la dopamine SEULEMENT s'il a été SUIVI D'UN SUCCÈS ce
    # même tick (recompense_env > 0 ou un canal visuel déjà positif) — un conseil reçu
    # sans rien accomplir ne doit pas graver quoi que ce soit (voir Chantier 3, la
    # trappe de secours : un appel "à vide" ne doit coûter que cout_requete_c3, jamais
    # être récompensé). La formule s'étend au même OU probabiliste plutôt qu'une
    # simple somme, pour les mêmes 3 raisons que le canal vocal v27.0 (bornée dans
    # [0,1] par construction, rétrocompatible à l'identique si wc3=0, monotone sans
    # écrasement d'un canal par un autre).
    poids_c3 = reponse_c3.confiance if (reponse_c3 is not None and poids_visuel > 0) else 0.0
    poids_evenement = 1.0 - (1.0 - POIDS_DOPAMINE_VISUEL * poids_visuel) \
                          * (1.0 - POIDS_DOPAMINE_VOCAL * poids_vocal_dopamine) \
                          * (1.0 - POIDS_DOPAMINE_C3 * poids_c3)
    poids_evenement = float(np.clip(poids_evenement, 0.0, 1.0))  # ceinture+bretelles :
        # la formule est bornée par construction, ce clip ne protège que d'un futur
        # POIDS_DOPAMINE_* > 1.0 réglé par erreur.
    etat.dopamine_poids_visuel_jour = getattr(etat, "dopamine_poids_visuel_jour", 0.0) + poids_visuel
    etat.dopamine_poids_vocal_jour = getattr(etat, "dopamine_poids_vocal_jour", 0.0) + poids_vocal_dopamine
    etat.dopamine_poids_c3_jour = getattr(etat, "dopamine_poids_c3_jour", 0.0) + poids_c3
    if action_item == ACTION_DEMANDER:
        etat.requetes_c3_jour = getattr(etat, "requetes_c3_jour", 0) + 1
        if reponse_c3 is not None:
            etat.reponses_c3_jour = getattr(etat, "reponses_c3_jour", 0) + 1

    dopamine_normalisee = (etat.teneur_dopamine - DOPAMINE_MIN) / (DOPAMINE_MAX - DOPAMINE_MIN)
    dopamine_curiosite = dopamine_normalisee * min(valeur_erreur, PLAFOND_ERREUR_DOPAMINE)

    recompense_interne = (float(recompense_env) + dopamine_curiosite + micro_recompense
                         + micro_recompense_porte + micro_recompense_progres
                         + penalite_stagnation + sous_objectif_intrinseque + r_bio
                         + micro_recompense_vocale - cout_requete_c3)
    # v40.1-fix4 — LA FALAISE DU GUIDAGE DISPARAÎT. L'ancien `if not mode_libre` coupait
    # l'aide continue D'UN COUP au palier 5 — précisément le défaut que le diagnostic
    # v35.1 documentait (« 0,00 record de proximité par jour pendant 2000 jours. Une
    # falaise, là où il fallait une pente »). `recompense_continue` est déjà multipliée
    # par min(facteur_guidage, 1), qui tend continûment vers 0 avec la maîtrise mesurée
    # (sevrage v35.1) : le retrait de l'aide ÉMERGE de la compétence, il n'est plus
    # décrété par un seuil de palier. ⚠️ Changement de comportement réel : un agent
    # au-delà du palier 5 qui NE maîtrise PAS garde son aide — c'est le but.
    recompense_interne += recompense_continue

    # --- v41.32-etape1 : SONDE DE MIXAGE (lecture seule, aucun effet sur la décision) ---
    # Placée ICI, juste après l'assemblage, pour trois raisons :
    #   - c'est le SEUL point du fichier où les onze termes coexistent ;
    #   - c'est APRÈS le guidage dégressif `_g` (l. ~8760), donc on mesure l'aide
    #     RÉELLEMENT versée et non l'aide brute — même précaution que le noyau prend
    #     déjà explicitement pour `guidage_but_journee` ;
    #   - c'est APRÈS l'atténuation par `acceptation()` sur la curiosité.
    # Mesurer avant l'un ou l'autre donnerait des chiffres qui ne sont pas ceux que le
    # gradient reçoit — donc inutilisables pour arbitrer une pondération.
    _sonder_mixage(
        etat,
        Env=recompense_env,
        Curiosite=dopamine_curiosite,
        Jalons=micro_recompense,
        Portes=micro_recompense_porte,
        Progres=micro_recompense_progres,
        Stagnation=penalite_stagnation,
        SousObjectif=sous_objectif_intrinseque,
        Bio=r_bio,
        Vocal=micro_recompense_vocale,
        CoutC3=-cout_requete_c3,
        Guidage=recompense_continue,
        Total=recompense_interne,
    )

    # v41.27 — `MALUS_DOULEUR` SUPPRIMÉ. Le choc mural n'est plus une pénalité posée dans
    # la récompense (−0,01, l'une des 4 récompenses en dur que l'audit du dogme signalait,
    # et celle-là même qui produisait l'inversion « mourir coûte moins cher que se
    # cogner ») : c'est désormais LA douleur, au même titre que la brûlure, avec sa
    # signature propre — pic ∝ vitesse d'impact, récupération RAPIDE.
    # Le coût atteint `r_bio` par le déficit, comme toute douleur. Rien n'est ajouté à la
    # récompense : `r_bio` en dérive déjà.

    if poids_evenement > 0:
        etat.teneur_dopamine += (DOPAMINE_MAX - etat.teneur_dopamine) * TAUX_CHOC_BASE * poids_evenement
        micro_boost_ancrage = 1.0 + (BOOST_ANCRAGE_MAX - 1.0) * poids_evenement
        # LTP par pic de dopamine (v20.0)
        etat.agent.fortifier_synapses(poids_evenement)
        if recompense_env > 0:
            etat.victoire_aujourdhui = True
    elif abandon_par_patience:
        etat.teneur_dopamine += (DOPAMINE_MIN - etat.teneur_dopamine) * TAUX_FRICTION_DOUCE_ABANDON
        micro_boost_ancrage = 1.0
    else:
        etat.teneur_dopamine += (DOPAMINE_MIN - etat.teneur_dopamine) * TAUX_FRICTION
        micro_boost_ancrage = 1.0
    etat.teneur_dopamine = float(np.clip(etat.teneur_dopamine, DOPAMINE_MIN, DOPAMINE_MAX))

    # Module "Parent" (v25.0, Paradigme Bébé, expérimental) : feedback social
    # déterministe, actif uniquement si parent_actif=True (jour >=
    # JOUR_FIN_MASQUAGE_EXTERNE dans cursus_bebe.py). Deux canaux — décision
    # utilisateur : (1) le score de formants du tick (voir
    # _appliquer_feedback_parent_vocal, "Oui !"/"Non !" par seuil) ; (2) un "Oui !"
    # supplémentaire quand une ressource bio est atteinte PENDANT une quête de survie
    # active (poids_ressource_bio > 0 implique déjà qu'une jauge était sous
    # SEUIL_CRITIQUE_BIO, donc qu'une quête était bien active — voir
    # evaluer_quetes_biologiques) ; ce second canal ne fait QUE tracer/renforcer, le
    # choc dopaminergique correspondant est déjà appliqué ci-dessus via poids_evenement.
    if parent_actif:
        if formants_cibles is not None:
            _appliquer_feedback_parent_vocal(etat, poids_vocal)
        if poids_ressource_bio > 0:
            etat.feedback_parent_jour = getattr(etat, "feedback_parent_jour", 0) + 1

    # --- v36.0 : LE FLUX ENRICHI ---
    #
    # Placé ICI, après que `recompense_interne` est complète : c'est le seul point du tick
    # où la charge réelle de l'expérience est connue (récompense terminale, jalons, chocs,
    # malus de douleur, métabolisme — tout est déjà agrégé).
    #
    # La mémoire spatiale recevait jusqu'ici DEUX types d'événements (FOOD, WATER) et
    # rejetait 98,6 % de ce qu'elle voyait. Elle reçoit désormais tout ce qui dépasse le
    # bruit de fond, sans qu'aucun type ne soit nommé dans le code.
    #
    # ⚠️ Écriture SEULE : cet appel ne lit ni ne modifie la décision du tick (déjà prise
    # plus haut), le gradient ou la dopamine. La mémoire ainsi enrichie n'influencera
    # l'agent qu'au tick SUIVANT, via `rappel_le_plus_marquant` dans le vecteur bio.
    _memoriser_si_saillant(etat, float(recompense_interne))

    etat.recompenses_journee.append(recompense_interne)
    etat.dones_journee.append(etat.fin_episode)
    # v37.1 — trace du choc dopaminergique de ce tick, consommée par le crédit rétrograde
    # de la distillation sélective (voir `_ponderer_distillation`). `poids_evenement` est
    # déjà l'intensité réelle de l'événement vécu — on ne la recalcule pas, on l'enregistre.
    etat.chocs_dopamine_journee.append(float(poids_evenement))

    etat.memoire_moyen_terme.append({
        'obs_courante': etat.etat_courant.detach(),
        'memoire_prec': memoire_avant.detach(),
        'contexte': contexte.detach(),
        'action': action_item,
        'obs_suivante': etat_suivant.detach(),
        # v27.0 : trace de l'audio entendu ce tick (None = silence, comportement
        # inchangé) — voir AGI_Naulthene.rever pour la consolidation nocturne qui
        # l'exploite. Sans cette trace, tout ce que l'agent apprend en vocal le jour
        # (multimodal, mode "minigrid" avec obs_auditive) n'était jamais rejoué la nuit,
        # pendant que l'érosion nocturne grignotait porte_auditive.
        'obs_auditive': obs_auditive.detach() if obs_auditive is not None else None,
        'importance': (abs(recompense_interne) + (valeur_erreur * 2.0) + 1e-5)
                      * micro_boost_ancrage * etat.empreinte_enfance
    })

    if etat.fin_episode:
        etat.episodes_jour += 1
        reussi_palier_episode = etat.doorkey_actif and etat.detecteur.meilleur_palier_episode >= etat.palier_cible
        if reussi_palier_episode:
            etat.succes_palier_cible_jour += 1
        etat.module_acceptation.enregistrer_episode(reussi=bool(termine), nombre_ticks=etat.ticks_episode_courant)
        # v35.0 — la RÉUSSITE se juge sur la récompense terminale, jamais sur `termine`
        # seul : `termine` vaut aussi True quand l'agent marche dans la lave (LavaGap) ou
        # épuise le budget de l'environnement. Compter ça comme un succès promouvrait un
        # agent qui se suicide vite.
        _enregistrer_episode_niveau(etat, bool(termine) and float(recompense_env) > 0.0)
        if etat.doorkey_actif and etat.palier_cible < 7:
            promu, msg_progression = etat.gestionnaire_cursus.enregistrer_resultat_episode(reussi_palier_episode)
            if msg_progression:
                print(f"   {msg_progression}")
            if promu:
                etat.palier_cible += 1
                print(f"   🎓 Palier {etat.palier_cible} visé : {DetecteurJalonsDoorKey.NOMS[etat.palier_cible - 1]}")

        # --- Apprentissage de la récurrence (Phase C, v17.0) ---
        if recompense_env > 0 and etat.a_utilise_sursaut_episode:
            etat.module_acceptation.augmenter_patience_de_base_definitivement()
            print("   💪 [RÉCURRENCE] Victoire après Sursaut de Volonté — patience de base augmentée durablement.")
        # v30.1 (télémétrie, aucun effet sur la décision) : issue du sursaut. Le projet
        # comptait déjà COMBIEN de sursauts (`sursauts_jour`) mais jamais s'ils SERVAIENT
        # à quelque chose. Ce taux est ce qui permettra de trancher le sens de variation
        # d'une extension adaptative : « muscle » (un sursaut qui gagne souvent se
        # renforce) ou « habituation » (un sursaut stérile s'atténue). Les deux lectures
        # sont défendables biologiquement — seules les données peuvent départager.
        if etat.a_utilise_sursaut_episode:
            if recompense_env > 0:
                etat.sursauts_suivis_victoire_jour += 1
            else:
                etat.sursauts_suivis_echec_jour += 1
        etat.a_utilise_sursaut_episode = False

        # v33.0-etape0 (télémétrie, aucun effet sur la décision) : récolte des trois
        # deltas AVANT le reset() qui efface l'état du chronomètre. Chaque delta n'est
        # accumulé que s'il existe réellement — un segment jamais atteint ne compte ni
        # au numérateur ni au dénominateur, sans quoi « lent » et « jamais atteint »
        # deviendraient indiscernables (voir ChronometreJalonsDoorKey.extraire_deltas).
        if etat.doorkey_actif:
            _d1, _d2, _d3 = etat.chronometre_jalons.extraire_deltas()
            etat.jalon_episodes_doorkey_jour += 1
            if _d1 is not None:
                etat.jalon_delta1_cumul_jour += _d1
                etat.jalon_delta1_n_jour += 1
            if _d2 is not None:
                etat.jalon_delta2_cumul_jour += _d2
                etat.jalon_delta2_n_jour += 1
            if _d3 is not None:
                etat.jalon_delta3_cumul_jour += _d3
                etat.jalon_delta3_n_jour += 1
            etat.jalon_ressources_post_cle_jour += etat.chronometre_jalons.ressources_post_cle

        # v41.6 (P17) — le niveau du prochain épisode est TIRÉ, pas imposé. Le tirage doit
        # précéder le `reset()` : c'est lui qui décide de quelle carte on parle.
        _appliquer_niveau_episode(etat, _tirer_niveau_episode(etat))
        obs, info = _reset_seede(etat)
        etat.etat_courant = encoder(obs)
        etat.memoire_tampon = torch.zeros(1, etat.agent.dim_bus, device=DEVICE)
        etat.vecteurs_episodiques.clear()
        etat.ticks_episode_courant = 0
        if etat.doorkey_actif:
            etat.detecteur.reinitialiser_episode(etat.env)
            etat.chronometre_jalons.reinitialiser_episode(etat.env)  # v33.0-etape0
        etat.detecteur_portes.reinitialiser_episode(etat.env)
        if _quete_auto_active(etat):  # v33.0-etape0.5
            etat.detecteur_progres.reinitialiser_episode(etat.env)
        etat.thermostat_cinetique.reinitialiser_episode(etat.env)
        etat.sursaut_volonte.reinitialiser_episode()
        etat.detecteur_ressources_bio.reinitialiser_episode(etat.env)
        etat.bus_sensoriel.reinitialiser_episode(etat.env)  # v29.0 — efface la trace de goût
        etat.moteur_bio.reinitialiser_episode()  # v41.26 — la brûlure est une lésion locale
        etat.positions_visitees_episode = set()
        # v34.0-etape0 (télémétrie) : chaque nouvelle carte de la journée est comptée.
        etat.ressources_vues_jour += _compter_ressources_grille(etat)
    else:
        etat.etat_courant = etat_suivant

    return {
        'action': action_item,
        'infos_internes': {
            'dopamine': etat.teneur_dopamine,
            'faim': 1.0 - etat.moteur_bio.satiete,
            # v22.0 : la BOUCHE — remonté à CHAQUE tick (l'agent vocalise en continu,
            # voir penser()), pour que le tuteur puisse synthétiser et jouer le son en
            # temps réel (exigence explicite utilisateur), leçon active ou non.
            'parametres_vocaux': parametres_vocaux.detach().cpu().numpy().flatten().tolist(),
        },
    }


def _rafraichir_rythme_metabolique(etat):
    """v41.30 — Lisse le nombre d'épisodes RÉELLEMENT joués et en dérive la densité de
    ressources du monde. Remplace `EPISODES_PAR_JOURNEE_REFERENCE = 4.0`.

    ⚠️ **La grandeur était déjà mesurée** : `etat.episodes_jour` existe, est réarmé chaque
    nuit par `_reinitialiser_buffers_journee` et logué en W&B sous `Episodes_Jour`. Il n'y
    avait rien à instrumenter — seulement à le LIRE.

    ⚠️ **L'inertie est celle du trait d'endurance**, et pour la même raison : promu, l'agent
    ne doit pas voir son métabolisme se réinitialiser. Une carte neuve où les épisodes
    s'allongent fait glisser le rythme vers le bas SANS RUPTURE, au lieu d'un saut.

    ⚠️ **Boucle de rétroaction à surveiller** : moins d'épisodes → moins de sources → plus
    de faim → patience modifiée → moins d'épisodes. C'est l'inertie qui l'amortit (~50
    journées de mémoire), et c'est exactement ce que la campagne d'ablation doit mesurer.
    """
    moteur = getattr(etat, "moteur_bio", None)
    if moteur is None:
        return

    vecu = float(max(0, getattr(etat, "episodes_jour", 0)))
    if vecu <= 0.0:
        # Journée sans aucun épisode clos : rien de mesuré, donc rien à apprendre. On ne
        # tire PAS la référence vers zéro sur une absence de donnée (même discipline que
        # « une journée stérile ne distille rien », v37.1).
        return

    ancien = getattr(moteur, "rythme_episodes", EPISODES_PAR_JOURNEE_NAISSANCE)
    moteur.rythme_episodes = max(
        EPISODES_PAR_JOURNEE_NAISSANCE,
        ancien + (vecu - ancien) * INERTIE_TRAIT_ENDURANCE,
    )

    # v41.30-fix2 — CE QUE LE RYTHME RÈGLE DÉSORMAIS : LA VITESSE DE VIDANGE.
    #
    # Plus la portion (fix2 : propriété du monde), plus la densité du monde (fix1 : propriété
    # de la surface). Le rythme vécu ne touche plus qu'à la PHYSIOLOGIE — l'allure à laquelle
    # les jauges se vident, donc le nombre de prises qu'une journée exige.
    #
    # Le sens est celui du bon sens biologique : un agent qui ne joue qu'un épisode par jour
    # n'a qu'UNE poignée d'occasions de manger, donc son corps doit tenir plus longtemps sur
    # un estomac plein. Un agent qui enchaîne les épisodes en croise davantage et peut
    # consommer plus vite. `besoin_par_axe` est exactement ce nombre de prises par journée.
    if moteur.ticks_par_jour:
        besoin = besoin_par_axe(moteur.rythme_episodes)
        taux_satiete_jour = besoin * PART_ESTOMAC_PAR_PRISE * CONTENANCE_JAUGE
        moteur.taux_satiete = taux_satiete_jour / float(moteur.ticks_par_jour)
        moteur.taux_hydratation = (taux_satiete_jour * RATIO_SOIF_SUR_FAIM
                                   / float(moteur.ticks_par_jour))

        # 🔴 v41.31 — LE TUBE DIGESTIF SUIT CE QUE L'AGENT MANGE RÉELLEMENT.
        #
        # `taux_satiete` ci-dessus est une VARIABLE MORTE : rien ne la soustrait depuis
        # que la v41.2 a remplacé le prélèvement direct par la digestion (vérifié — un
        # agent qui jeûne perd 0,083333 de satiété en 10 ticks, soit exactement
        # `debit_digestif / RENDEMENT_CONVERSION`). Elle est conservée pour la
        # rétrocompatibilité, mais elle ne pilote rien.
        #
        # LE VRAI RÉGULATEUR est `debit_digestif`, jusqu'ici figé à
        # `DEPENSE_ENERGIE_JOUR × MARGE_DIGESTIVE = 3,0`, soit une vidange de
        # **3,333 estomacs/jour IDENTIQUE dans les deux bras** de la campagne v41.30 —
        # quel que soit le besoin. C'est l'explication complète de l'invariance
        # énergétique mesurée (`t = +1,04`, NS, n=20) : aucun réglage en amont sur le
        # besoin ne pouvait atteindre les jauges tant que la vanne restait verrouillée
        # en aval. L'agent mangeait 5,4 fois par jour et restait à 0,22 d'énergie.
        #
        # ⚠️ `MARGE_DIGESTIVE` RESTE — c'est une borne sur un RAPPORT, pas une valeur :
        # elle garantit que le débit DÉPASSE la dépense. Si le débit passait sous la
        # dépense, la mort deviendrait certaine PAR CONSTRUCTION et la mécanique ne
        # mesurerait plus rien.
        #
        # ⚠️ Le débit est donc dérivé de ce que le corps peut réellement absorber dans la
        # journée — `besoin × portion` — et non d'une dépense posée. Un organisme qui
        # mange peu n'a pas le tube digestif d'un organisme qui mange beaucoup.
        # 🔴 v41.31-fix2 — L'AXE 2 EST RETIRÉ. La prémisse était fausse.
        #
        # L'idée : « un organisme qui mange peu n'a pas le tube digestif d'un organisme qui
        # mange beaucoup », donc indexer `debit_digestif` sur le besoin vécu. Mesuré au banc,
        # DEUX FOIS : −0,18 puis −0,17 d'énergie, sur 3/3 graines à chaque essai.
        #
        # LA RAISON EST STRUCTURELLE. `debit_digestif` a deux rôles opposés :
        #
        #   satiete -= conversion / RENDEMENT   ← il VIDE l'estomac      (suit l'ingestion)
        #   energie += conversion × cofacteur   ← il FABRIQUE l'énergie  (doit suivre la DÉPENSE)
        #
        # Le premier jet l'a indexé sur l'INGESTION. Le second a ajouté un plancher au coût
        # d'exister — mais ce plancher ne garantit que la survie À L'ARRÊT :
        #
        #   conversion plancher  0,003611/tick
        #   dépense basale       0,003250     → +0,000361 ✅ (agent immobile)
        #   dépense max          0,005000     → −0,001389 ❌ (agent qui agit)
        #
        # Or `MARGE_DIGESTIVE` s'applique, dans le régime historique, à la DÉPENSE — pas à
        # l'ingestion. Borner sur la dépense max ramènerait exactement au fossile, rendant
        # l'axe inopérant par construction.
        #
        # ⚠️ CE QUI RESTE VRAI : `DEPENSE_ENERGIE_JOUR = 2.0` EST un fossile (son propre
        # commentaire dit « calibré à 3 repas/jour »), et `taux_satiete` EST une variable
        # morte. Mais les corriger exige de dériver LA DÉPENSE — l'effort mécanique et
        # cognitif réellement produit — pas le débit. C'est un chantier à part, à mener
        # isolément de toute modification de l'apprentissage moteur.
        #
        # `DEBIT_DIGESTIF_VECU_ACTIF` et `--debit-fossile` sont conservés comme témoins
        # inertes : le drapeau ne pilote plus rien, mais le retirer casserait les scripts
        # de campagne existants.

    # 🔴 v41.30-fix1 — LE MONDE N'EST PAS INDEXÉ SUR LE MÉTABOLISME DE L'AGENT.
    #
    # La v41.30 recalculait ici `nb_sources_food/water` à partir du rythme vécu. C'était une
    # CONFUSION ENTRE L'ESTOMAC ET L'ÉCOSYSTÈME, et le banc l'a payée : −0,068 d'énergie
    # (0,1968 dérivé contre 0,2651 fossile, 3 graines × 10 jours), tout l'écart imputé au
    # rythme, la patience n'y étant pour rien (runs bit-identiques avec `--rythme-fossile`).
    #
    # Le mécanisme de l'échec — LA FALAISE DE RENCONTRE :
    #
    #   persévérance ↑ → épisodes réels ↓ → besoin ↓ → sources ↓ (6 → 4)
    #                                                → DENSITÉ SPATIALE ↓ (−33 %)
    #                                                → famine par NON-RENCONTRE
    #
    # En début de vie la politique motrice est quasi aléatoire : la survie dépend presque
    # uniquement de la densité spatiale (N_sources / surface). Quadrupler la valeur d'une
    # ressource (0,794 → 3,175) ne compense RIEN si l'agent a mathématiquement moins de
    # chances de poser le pied dessus. Le monde n'a pas à faire disparaître des pommes de la
    # grille sous prétexte que l'agent prend son temps pour réfléchir.
    #
    # La séparation posée par cette correction, et qu'il ne faut plus jamais franchir :
    #
    #   • la DENSITÉ du monde est une propriété du BIOTOPE — dérivée de la SURFACE de la
    #     carte (`FRACTION_CASES_RESSOURCES_MAX`), invariante au vécu de l'agent ;
    #   • la QUANTITÉ requise pour vivre est une propriété du MÉTABOLISME — dérivée du
    #     rythme vécu, et elle seule (`besoin_par_axe`, lue par `valeur_alimentaire` et
    #     `valeur_hydrique`).
    #
    # Le rythme vécu ne touche donc PLUS au détecteur de ressources : il ne règle que la
    # physiologie. Ne pas rebrancher `nb_sources_*` ici sans relire ce bloc.


def executer_nuit(etat, plafond_reve=None):
    """Clôture la journée subjective en cours : bilan d'épisode incomplet, promotion de
    niveau, apprentissage (apprendre_journee), rêve adaptatif, ressort dopaminergique,
    thermostat de neurogenèse, cycle_sommeil_global. Équivalent à la fin de la boucle
    `for jour in range(...)` d'origine (à partir de `if not fin_episode:`). Retourne le
    dict à logger sur W&B (l'appelant décide s'il logge ou non — voir CuveDeMaintien).

    `plafond_reve` (v25.0, Paradigme Bébé, expérimental) : défaut None = comportement
    identique à avant v25.0 (le plafond reste PLAGE_REVE_MAX, 0.60). Si fourni
    (cursus_bebe.py passe plafond_reve_bebe(etat.jour), qui suit le "% Dodo" de la
    phase d'âge : 70%→60%→50%→40%→35%), REMPLACE PLAGE_REVE_MAX dans le calcul de
    pourcentage_reve ci-dessous — le pourcentage réellement rejoué reste toujours
    émergent (plasticite_base × facteur_richesse), seul son PLAFOND varie ; on ne
    réintroduit jamais une taille de batch fixe (garde-fou CLAUDE.md, rêve adaptatif)."""
    if not etat.fin_episode:
        etat.episodes_jour += 1
        reussi_palier_episode = etat.doorkey_actif and etat.detecteur.meilleur_palier_episode >= etat.palier_cible
        if reussi_palier_episode:
            etat.succes_palier_cible_jour += 1
        etat.module_acceptation.enregistrer_episode(reussi=False, nombre_ticks=etat.ticks_episode_courant)
        _enregistrer_episode_niveau(etat, False)  # v35.0 — épisode coupé par la nuit = échec
        if etat.doorkey_actif and etat.palier_cible < 7:
            promu, msg_progression = etat.gestionnaire_cursus.enregistrer_resultat_episode(reussi_palier_episode)
            if msg_progression:
                print(f"   {msg_progression}")
            if promu:
                etat.palier_cible += 1
                print(f"   🎓 Palier {etat.palier_cible} visé : {DetecteurJalonsDoorKey.NOMS[etat.palier_cible - 1]}")

    # v41.30 — LE RYTHME MÉTABOLIQUE SUIT LA VIE, plus une constante posée.
    #
    # Placé ICI, après la clôture de l'épisode incomplet : `episodes_jour` est alors
    # définitif pour la journée. Une fois par NUIT, jamais par tick — un besoin qui
    # fluctuerait en cours de journée rendrait la faim illisible (même discipline que
    # `MemoireEpisodiqueSpatiale.ajuster_capacite`, v31.0).
    _rafraichir_rythme_metabolique(etat)

    taux_maitrise = None
    if etat.doorkey_actif and etat.detecteur.actif and etat.episodes_jour > 0:
        taux_maitrise = etat.succes_palier_cible_jour / etat.episodes_jour

    if etat.victoire_aujourdhui:
        etat.victoires_consecutives += 1
        # v35.1 — la première victoire suffit à replier le filet : l'agent a prouvé que le
        # niveau n'est pas hors de portée, il n'a plus besoin d'un surplus d'aide.
        etat.jours_stagnation_niveau = 0
    else:
        etat.victoires_consecutives = 0
        etat.jours_stagnation_niveau += 1

    # --- v33.0-etape0.6 : chronologie des victoires (télémétrie PURE) ---
    # Placée APRÈS `victoires_consecutives` (qui répond à « suis-je promu ? ») et
    # avant tout usage : elle répond à une question différente et non posée jusqu'ici —
    # « l'agent réussit-il DE MIEUX EN MIEUX, ou au hasard ? ». Aucune décision, aucun
    # gradient, aucune dopamine ne la lit.
    # v33.0-etape0.6-fix1 — la série d'intervalles est SEGMENTÉE PAR CONTEXTE.
    # Lu à chaque nuit (pas seulement les jours de victoire) pour que la remise à zéro
    # survienne au moment exact du changement, jamais rétroactivement à la victoire
    # suivante. Le palier est lu avant la promotion de niveau (plus bas) : au tour
    # suivant, `niveau_actuel` aura changé et déclenchera lui-même la coupure.
    contexte_courant = (etat.niveau_actuel, etat.palier_cible if etat.doorkey_actif else None)
    if etat.contexte_victoires is None:
        etat.contexte_victoires = contexte_courant
    elif contexte_courant != etat.contexte_victoires:
        # Changement de difficulté : les intervalles d'avant ne sont plus comparables à
        # ceux d'après. On archive la série (elle reste lisible en télémétrie) et on
        # repart à zéro, plutôt que de laisser le ratio mélanger deux tâches.
        if etat.intervalles_victoires:
            etat.intervalles_contexte_prec = etat.intervalles_victoires
        etat.intervalles_victoires = []
        etat.contexte_victoires = contexte_courant
        # `jour_derniere_victoire` est CONSERVÉ : le premier intervalle du nouveau
        # contexte se mesure depuis la dernière victoire réelle, ce qui est bien le
        # temps qu'il a fallu pour regagner à la nouvelle difficulté.

    if etat.victoire_aujourdhui:
        if etat.jour_derniere_victoire is not None:
            # L'écart n'est enregistré qu'à partir de la DEUXIÈME victoire : la première
            # n'a pas de précédente à laquelle se comparer, et compter « jour 93 » comme
            # un intervalle de 93 jours mélangerait le temps d'apprentissage initial
            # avec les intervalles inter-victoires, qui sont la vraie mesure.
            etat.intervalles_victoires.append(etat.jour - etat.jour_derniere_victoire)
        etat.jour_derniere_victoire = etat.jour
        etat.jours_depuis_victoire = 0
        etat.victoires_totales += 1
    elif etat.jour_derniere_victoire is not None:
        etat.jours_depuis_victoire = etat.jour - etat.jour_derniere_victoire
    else:
        # Jamais gagné de toute sa vie : le compteur mesure alors l'âge de l'agent,
        # ce qui est exactement l'information voulue (« toujours rien après N jours »).
        etat.jours_depuis_victoire = etat.jour

    # --- v35.0 : DEUX VOIES DE PROMOTION (OU logique) ---
    #
    # (a) la voie historique — N victoires CONSÉCUTIVES : rapide, mais fragile (une seule
    #     défaite remet à zéro) ;
    # (b) la voie du TAUX DE MAÎTRISE — réussir `TAUX_PROMOTION` de la fenêtre glissante :
    #     lente à établir mais robuste, elle mesure une compétence installée plutôt qu'une
    #     série chanceuse. Un agent à 80 % de réussite qui perd un épisode sur cinq était
    #     auparavant bloqué à vie ; il passe désormais.
    #
    # Les deux coexistent pour qu'aucun cerveau existant ne régresse en vitesse de
    # promotion : le taux ne fait qu'AJOUTER une seconde porte, jamais fermer la première.
    # v40.2 — LA MATURITÉ REMPLACE LES DEUX PORTES SCOLAIRES.
    #
    # `promu_par_serie` (2 victoires consécutives) et `promu_par_taux` (60 % sur 20) ont
    # disparu : c'étaient deux examens, et un examen se passe par chance. Mesuré en P17 :
    # palier 5/6 atteint avec 4 victoires au total. La promotion suit désormais une
    # grandeur CONTINUE que l'agent construit — voir `_maturite_niveau`.
    #
    # L'ÉVÉNEMENT reste discret (on change de carte ou non), mais son déclencheur ne l'est
    # plus : c'est le franchissement d'un continuum, pas la réussite d'un test.
    taux_niveau = _taux_maitrise_niveau(etat)
    maturite = _maturite_niveau(etat)
    etat.maturite_niveau_jour = maturite   # télémétrie (voir bilan de nuit et W&B)

    if maturite >= SEUIL_MATURITE:
        if etat.niveau_actuel < len(PROGRAMME) - 1:
            # Motif calculé AVANT de vider l'historique, sinon il afficherait 0 épisode.
            motif = (f"maturité {maturite:.0%} "
                     f"(régularité {(sum(etat.historique_episodes_niveau) / max(len(etat.historique_episodes_niveau), 1)):.0%}"
                     f" × {len(etat.historique_episodes_niveau)} épisodes"
                     f" × autonomie {getattr(etat, 'autonomie_au_critere', 1.0 - min(1.0, getattr(etat, 'facteur_guidage_jour', 1.0))):.0%})")
            etat.niveau_actuel += 1
            etat.victoires_consecutives = 0
            # Vider l'historique est OBLIGATOIRE : un taux hérité d'un niveau plus facile
            # promouvrait en chaîne sans que l'agent ait rien montré sur le nouveau.
            etat.historique_episodes_niveau = []
            # v35.1 — idem pour le filet : la stagnation se compte PAR NIVEAU, sinon un
            # agent promu arriverait sur son nouveau palier avec un renfort maximal déjà
            # armé, et le sevrage ne pourrait jamais démarrer.
            etat.jours_stagnation_niveau = 0
            # v41.4 — profil de la carte QUITTÉE, lu avant de la fermer : il servira à
            # mesurer combien la nouvelle lui ressemble, donc combien de sevrage se
            # reporte. Lu sur la grille, jamais tabulé (voir `_profil_carte`).
            try:
                profil_ancien = _profil_carte(etat.env)
            except Exception:
                profil_ancien = None   # un monde non-MiniGrid n'a pas de grille : pas
                                        # d'héritage, l'agent repart en débutant complet
            etat.env_id, etat.nom_classe = ((ENV_FORCE, "Banc de mesure (env forcé)")
                                            if ENV_FORCE else PROGRAMME[etat.niveau_actuel])
            etat.env.close()
            etat.env = creer_env(etat.env_id, DIM_VISUELLE)
            # La parenté exige une carte instanciée : le reset a lieu au prochain épisode,
            # mais la grille existe déjà après `creer_env` sur MiniGrid.
            try:
                # v41.9 — seedé comme tout reset, mais SANS incrémenter `episodes_vecus` :
                # ce reset ne joue aucun épisode, il n'existe que pour lire la forme de la
                # nouvelle carte. L'incrémenter décalerait la suite des mondes à chaque
                # promotion et casserait la reproductibilité.
                etat.env.reset(seed=_graine_episode(etat))
                parente = (_parente_cartes(profil_ancien, _profil_carte(etat.env))
                           if profil_ancien is not None else 0.0)
            except Exception:
                parente = 0.0
            etat.parente_niveau_precedent = parente
            # v41.6 (P17) — le niveau de l'épisode suit la promotion : sans cela, le
            # prochain épisode serait compté « hors référence » alors qu'il est joué sur
            # la nouvelle carte, et n'alimenterait pas la fenêtre de promotion.
            etat.niveau_episode = etat.niveau_actuel
            # v41.10 — bascule, pas effacement : une promotion n'est plus un adieu depuis
            # P17 (l'agent révise ses anciens paliers en permanence). Le repère du `goal`
            # naît au tick même de la victoire qui déclenche cette promotion — l'effacer
            # ici revenait à faire oublier à l'agent ce qu'il venait juste de démontrer.
            etat.memoire_episodique_spatiale.basculer_carte(etat.env_id)
            print(f"\n🎓 [PROMOTION] L'Agent passe en {etat.nom_classe} ! 🚀  ({motif})")
            print(f"   🧬 parenté avec la carte quittée : {parente:.0%} "
                  f"→ sevrage hérité à proportion (v41.4)")
        else:
            print(f"🏆 [MAÎTRISE] L'Agent a vaincu le dernier niveau ({etat.nom_classe}) !")

    # v25.0 (Paradigme Bébé, expérimental) : normalisation par le nombre RÉEL de ticks
    # de la journée (len(etat.jepa_losses), un ajout par tick que ce soit via
    # traiter_tick ou _traiter_tick_vocal_isole), plutôt que par la constante globale
    # `ticks_par_jour` (400) — cursus_bebe.py tourne sur TICKS_PAR_JOUR_BEBE (3600),
    # diviser par 400 aurait faussé erreur_moyenne d'un facteur ~9 et donc le
    # thermostat de neurogenèse qui la compare à seuil_base. Comportement inchangé pour
    # le Cursus par Ères / mode standalone (len(etat.jepa_losses) == ticks_par_jour
    # dans ce cas, résultat identique).
    ticks_du_jour = len(etat.jepa_losses) or ticks_par_jour
    erreur_moyenne = etat.erreur_journee / ticks_du_jour

    # --- Plasticité calculée AVANT le rêve et AVANT le ressort nocturne ---
    #
    # v40.1-style — écrit comme un CLIP, plus comme un `if`. L'ancienne forme
    # (`if teneur >= NEUTRE: 1.0 else: rampe`) donnait exactement le même résultat —
    # vérifié : écart maximal 0.000000000000 sur 10 001 points couvrant tout le domaine
    # [DOPAMINE_MIN, DOPAMINE_MAX]. Ce n'était donc pas une décision, seulement une
    # saturation déguisée en branche, et le `if` laissait croire à deux régimes
    # cognitifs là où il n'y a qu'une rampe bornée.
    etat.plasticite_base = max(0.0, min(1.0, (etat.teneur_dopamine - DOPAMINE_MIN)
                                             / (DOPAMINE_NEUTRE - DOPAMINE_MIN)))

    perte_jour = etat.agent.apprendre_journee(
        etat.jepa_losses, etat.log_probs_journee, etat.entropies_journee,
        etat.valeurs_journee, etat.recompenses_journee, etat.dones_journee,
        coeff_entropie=etat.coeff_entropie_jour,
        pertes_vocales=etat.pertes_vocales,
        # v37.1 — le crédit rétrograde de la distillation sélective a besoin de savoir
        # QUAND l'agent a réellement vécu quelque chose. `getattr` pour rester tolérant
        # aux cursus qui n'auraient pas encore ce buffer (cuve, arène).
        chocs_dopamine=getattr(etat, "chocs_dopamine_journee", None),
        # v41.31 — le masque du gradient causal. Même tolérance : un cursus qui n'aurait
        # pas ce buffer (cuve, arène) retombe sur le `.mean()` d'avant v41.31.
        transitions=getattr(etat, "transitions_journee", None),
        rendements=getattr(etat, "rendements_journee", None),
    )

    # --- v40.0 : LE VÉCU NOURRIT LA FORCE DE PLANIFICATION (une fois par nuit) ---
    # Placé APRÈS `apprendre_journee` (le buffer est alors complet) et AVANT le bilan
    # console, qui affiche la valeur mise à jour. La force elle-même n'est relue qu'au
    # début de la journée suivante — jamais en cours de journée, pour rester stationnaire.
    #
    # ⚠️ La source est `recompenses_journee`, la grandeur SIGNÉE — pas
    # `chocs_dopamine_journee`, qui est une intensité toujours positive (voir la docstring
    # de `nourrir_vecu`). Sans le signe, DANGER ne se remplit jamais.
    #
    # v40.0-fix1 — UNE journée = au plus UN point de vécu (`nourrir_vecu_journee`). La
    # version par tick faisait passer f de 0,000 à 0,906 en une seule nuit (400 ticks
    # contre un a priori de 1,0) : l'agent naissait prudent et délibérait largement dès le
    # lendemain, au lieu de gagner sa confiance sur des dizaines de journées.
    etat.agent.nourrir_vecu_journee(getattr(etat, "recompenses_journee", None))

    # --- v40.1 : LA COMPOSITION DE L'ENVIE DE VIVRE (une fois par nuit) ---
    # Placée APRÈS `nourrir_vecu_journee` : la foi du jour doit être à jour avant d'entrer
    # dans le produit. `erreur_moyenne` (calculée plus haut) est ce que C2 comprend du
    # monde — la moitié « lucidité » du couplage. L'ordre compte : lucidité puis foi, sur
    # l'état de la nuit précédente, jamais sur une moyenne.
    etat.agent.reviser_envie_de_vivre(erreur_moyenne)

    # --- v31.0 : capacité mnésique adaptative (une fois par nuit) ---
    # Placée AVANT le calcul du rêve : la nuit est le moment où le cerveau grandit
    # (declencher_neurogenese plus bas) et où la plasticité est réévaluée — c'est donc
    # le point naturel pour réajuster ce que l'organisme peut retenir. Une capacité
    # recalculée à chaque tick fluctuerait sans cesse et rendrait la FIFO illisible.
    # v31.1 — la taille de la grille borne la capacité (cap de densité). Lecture
    # défensive : un env absent ou une API MiniGrid différente donne None, ce qui
    # désactive simplement le cap au lieu de faire échouer la nuit — même discipline de
    # dégradation gracieuse que les détecteurs génériques (§3b).
    cases_grille = None
    try:
        grille = etat.env.unwrapped.grid
        cases_grille = int(grille.width) * int(grille.height)
    except Exception:
        pass
    capacite_memoire = etat.memoire_episodique_spatiale.ajuster_capacite(
        dim_bus=etat.agent.dim_bus,
        deficit_bio=etat.moteur_bio.calculer_deficit(),
        cases_grille=cases_grille,
    )

    # --- Calcul du pourcentage de rêve adaptatif ---
    if etat.memoire_moyen_terme:
        importance_moyenne_jour = float(np.mean([s['importance'] for s in etat.memoire_moyen_terme]))
    else:
        importance_moyenne_jour = 0.0
    # v31.0 — CORRECTIF de l'effondrement du rêve sur un cerveau mature.
    #
    # `importance` est multipliée par `empreinte_enfance = BUS_REFERENCE_INITIAL/dim_bus`
    # (voir traiter_tick) : à dim_bus=96, tout souvenir vaut 6× moins qu'à la naissance.
    # Comme `facteur_richesse` comparait cette importance à une référence CONSTANTE, le
    # pourcentage de rêve s'effondrait mécaniquement à mesure que le cerveau grandissait —
    # mesuré : 60 % à dim_bus=16, 15 % à dim_bus=96, et ~2 % sur un cerveau réel mature.
    # Un cerveau plus grand rêvait donc de MOINS EN MOINS, exactement l'inverse de ce que
    # la consolidation nocturne devrait faire.
    #
    # Correctif : la référence suit la même échelle que ce qu'elle mesure. Le rapport
    # importance/référence redevient invariant à la taille du cerveau, et `%_reve`
    # continue d'émerger de la plasticité × richesse RÉELLE de la journée — le principe
    # fondateur est préservé, on retire seulement un biais d'échelle parasite.
    reference_richesse = IMPORTANCE_REFERENCE_REVE * max(1e-6, etat.empreinte_enfance)
    facteur_richesse = min(1.0, importance_moyenne_jour / reference_richesse)
    plage_reve_max_effective = PLAGE_REVE_MAX if plafond_reve is None else plafond_reve
    pourcentage_reve = POURCENTAGE_REVE_MIN + (plage_reve_max_effective - POURCENTAGE_REVE_MIN) * etat.plasticite_base * facteur_richesse
    taille_lot_reve = int(round(pourcentage_reve * len(etat.memoire_moyen_terme)))
    taille_lot_reve = max(0, min(taille_lot_reve, len(etat.memoire_moyen_terme)))

    if taille_lot_reve < TAILLE_MIN_REVE:
        perte_reves, nb_reves = 0.0, 0
    else:
        # v27.0 — même rampe progressive que traiter_tick (coeff_jepa_audio), pour que
        # le rêve ne consolide l'audio qu'avec la même prudence que l'apprentissage
        # diurne (voir AGI_Naulthene.rever).
        coeff_jepa_audio_nuit = COEFF_JEPA_AUDIO_MAX * min(1.0, etat.ticks_audio_recus / RAMPE_JEPA_AUDIO)
        perte_reves, nb_reves = etat.agent.rever(
            etat.memoire_moyen_terme, batch_size=taille_lot_reve,
            coeff_jepa_audio=coeff_jepa_audio_nuit,
        )
    etat.memoire_moyen_terme.clear()
    # Bug v21.0 (découvert lors des premières nuits in-session du daemon, plusieurs
    # nuits pouvant s'enchaîner dans une même connexion longue) : seul jepa_losses
    # était vidé ici — log_probs_journee/entropies_journee/valeurs_journee/
    # recompenses_journee/dones_journee ne l'étaient jamais après apprendre_journee().
    # Les tenseurs de la nuit précédente (déjà consommés par .backward(), donc à
    # graphe libéré) se recollaient alors via torch.cat aux tenseurs du jour suivant,
    # provoquant "Trying to backward through the graph a second time" dès la 2e nuit
    # — en mode standalone comme dans la Cuve. Note : on ne peut PAS appeler
    # _reinitialiser_buffers_journee() ici, elle remet aussi à zéro des compteurs
    # scalaires (episodes_jour, erreur_journee...) encore lus plus bas dans cette
    # même fonction pour le log/dict W&B de fin de nuit.
    etat.jepa_losses.clear()
    etat.log_probs_journee.clear()
    etat.entropies_journee.clear()
    etat.valeurs_journee.clear()
    etat.recompenses_journee.clear()
    etat.dones_journee.clear()
    etat.pertes_vocales.clear()  # v22.1 — 6e buffer, même raison que les 5 ci-dessus
    # v41.31 — 7e buffer. S'il n'était pas vidé ICI (et pas seulement dans
    # `_reinitialiser_buffers_journee`), il grossirait d'une nuit à l'autre dans la Cuve
    # où plusieurs nuits s'enchaînent sans réinitialisation complète : le masque serait
    # alors plus long que `log_probs` et l'égalité de longueur le ferait ignorer en
    # silence — le gradient causal se désactiverait sans le moindre message.
    if hasattr(etat, "transitions_journee"):
        # La télémétrie est lue PLUS BAS, après ce vidage : on fige donc le compte ici,
        # sinon la ligne du bilan afficherait un buffer vide (défaut attrapé au premier
        # run de validation v41.31).
        etat.gradient_ticks_credites = sum(1 for x in etat.transitions_journee if x)
        etat.gradient_ticks_total = len(etat.transitions_journee)
        etat.transitions_journee.clear()
    # v41.48 — le buffer du rendement est vidé DANS TOUS LES CAS, comme celui des
    # transitions : un compteur journalier jamais remis à zéro cumulerait depuis la
    # naissance (piège du bug `score_vocal_jour` v27.0).
    if hasattr(etat, "rendements_journee"):
        _r = etat.rendements_journee
        etat.rendement_moyen_journee = (sum(_r) / len(_r)) if _r else None
        etat.rendement_ticks_nuls = sum(1 for x in _r if x <= 0.0)
        etat.rendements_journee.clear()

    etat.teneur_dopamine += (DOPAMINE_NEUTRE - etat.teneur_dopamine) * TAUX_RESSORT
    etat.teneur_dopamine = float(np.clip(etat.teneur_dopamine, DOPAMINE_MIN, DOPAMINE_MAX))

    # --- v41.21 : LE THERMOSTAT CRISTALLISE COMME UN RÉSEAU DE NAULTHÈNES ---
    #
    # Source : travaux de cosmologie Naulthène, modèle v5.0/v5.1 (documents personnels,
    # hors dépôt). Le potentiel de Landau
    # `V(Q,K) = C(c)Q²/2 + K²ln(N)/2 − Q·K + Q⁴/4` fait émerger la CRISTALLISATION d'une
    # seule condition, la condition de survie :
    #
    #       C(c) > ln(N)        (cohésion interne  >  friction d'expansion)
    #
    # Rien n'y est posé : le seuil `c_min = 5` ÉMERGE du calcul (c=3 → 28,07 et c=4 →
    # 120,69 échouent contre ln(10¹²²) ≈ 280,9 ; c=5 → 448,58 survit). Les deux termes
    # vivent sur la MÊME échelle, ce qui rend la comparaison adimensionnelle.
    #
    # 🔴 CE QUE ÇA CORRIGE (violation n°2 de la revue du dogme, mesurée le 17/08).
    # L'ancienne condition `variance_erreur < 0.005` comparait une variance ABSOLUE à un
    # nombre posé. Erreur JEPA réelle mesurée : 0,0111 à 0,0173, donc variance ~4e-6 —
    # **mille fois sous le seuil**. La condition était donc TOUJOURS vraie : elle ne
    # discriminait rien. C'est le défaut exact de `SEUIL_CRISTAL = 0.80` (myéline réelle
    # 0,0038) et de `q_ref = 1.0` (500× trop grand), tous deux corrigés en v37.0 — une
    # échelle absolue posée a priori, jamais confrontée à une mesure.
    #
    # LA TRANSPOSITION, terme à terme :
    #   C(c)  → cohésion   = 1/CV²  où CV = écart-type/moyenne de l'erreur JEPA.
    #                        Un modèle du monde dont l'erreur est STABLE est cohérent ;
    #                        le coefficient de variation est sans dimension, donc valable
    #                        quelle que soit l'échelle de l'erreur — c'est tout l'intérêt.
    #   ln(N) → friction   = ln(nb de paramètres du cerveau). Plus le réseau est grand,
    #                        plus il est difficile d'y maintenir une cohérence globale.
    #                        C'est littéralement l'horizon holographique du modèle : la
    #                        friction croît avec la taille de l'espace à couvrir.
    #
    # La fenêtre d'observation n'est plus « 3 » posé : elle suit la période de mutation
    # (`JOURS_ENTRE_MUTATIONS`), seule échelle de temps que la neurogenèse connaisse.
    # v41.24 — `pas` est lu plus bas par le lissage du rendement structurel, or il n'est
    # calculé que lorsque la fenêtre d'observation est PLEINE. Sans cette valeur par
    # défaut, la première mutation d'un cerveau neuf lèverait un NameError.
    pas = 1.0 / float(JOURS_ENTRE_MUTATIONS)
    etat.historique_erreurs.append(erreur_moyenne)
    if len(etat.historique_erreurs) > JOURS_ENTRE_MUTATIONS:
        etat.historique_erreurs.pop(0)
    if len(etat.historique_erreurs) == JOURS_ENTRE_MUTATIONS:
        moyenne_glissante = float(np.mean(etat.historique_erreurs))
        ecart_type = float(np.std(etat.historique_erreurs))
        # CV adimensionnel : la stabilité RELATIVE du modèle du monde.
        cv = ecart_type / max(moyenne_glissante, 1e-9)
        cohesion = 1.0 / max(cv * cv, 1e-9)
        friction = math.log(max(sum(p.numel() for p in etat.agent.parameters()), math.e))
        # --- v41.23 : DEUX RAISONS DE SE RECALIBRER, ET ELLES SONT CONTINUES ----------
        #
        # 🔴 CE QUE ÇA CORRIGE — une régression que j'ai moi-même introduite en v41.21.
        # J'avais remplacé la condition historique par la seule cristallisation
        # cosmologique. Mesuré : les cerveaux V30 se stabilisaient d'eux-mêmes à
        # **dim_bus 48** (plafond 96, jamais atteint) ; après v41.21, **20/20 collent au
        # plafond**, quel qu'il soit (96, puis 160). J'avais retiré le frein.
        #
        # La cause : la condition historique `variance < 0.005 AND moyenne > seuil*1.5`
        # avait un membre mort (la variance, toujours vraie) et un membre VIVANT
        # (`moyenne > seuil*1.5`) qui faisait MONTER `seuil_base` vers l'erreur réelle.
        # Ce rattrapage est ce qui éteignait la neurogenèse. J'ai jugé la ligne sur son
        # membre mort et jeté le vivant avec.
        #
        # LES DEUX FORCES, en OU — un organisme cesse de croître pour deux raisons :
        #
        #   (1) LIMITE STRUCTURELLE — `cohésion / friction` (Landau, v41.21). Le réseau
        #       a atteint une densité où l'expansion coûterait plus de friction qu'elle
        #       n'apporte de cohésion. La structure dit stop.
        #   (2) LIMITE D'HABITUATION — `moyenne / (seuil_base × exigence)`. L'agent se
        #       trompe beaucoup mais son erreur STAGNE : il accepte ce niveau comme sa
        #       nouvelle normalité, la référence remonte, et le signal de détresse qui
        #       déclenchait la neurogenèse s'éteint de lui-même.
        #
        # ⚠️ AUCUNE DES DEUX N'EST UN `if`. Chacune produit une PRESSION dans [0,1] par
        # une saturation `x/(1+x)` — la forme continue d'un rapport, sans seuil ni pente
        # réglable. Le pas de recalibrage est le MAXIMUM des deux (le « OU » logique
        # devient un max continu), multiplié par le pas d'observation. Une force faible
        # recalibre un peu, une force forte recalibre beaucoup : il n'existe plus de
        # point où le comportement bascule.
        #
        # L'EXIGENCE N'EST PLUS `1.5` POSÉ : elle vaut `1 + 1/fenêtre`. Un agent qui
        # observe sur 5 nuits tolère 20 % d'écart avant de se recalibrer ; s'il observait
        # sur 20 nuits il n'en tolérerait que 5 %. L'exigence dérive de la durée
        # d'observation — c'est la même échelle de temps qui gouverne tout le bloc.
        exigence = 1.0 + 1.0 / float(JOURS_ENTRE_MUTATIONS)
        pression_structure = (cohesion / friction) / (1.0 + cohesion / friction)
        _ecart = moyenne_glissante / max(etat.seuil_base * exigence, 1e-9)
        pression_habituation = _ecart / (1.0 + _ecart)
        #
        # ⚠️ LE PAS EST LA PRESSION ELLE-MÊME, PAS `pression / fenêtre`. Une première
        # version divisait encore par la fenêtre : la fenêtre gouverne l'EXIGENCE (à quel
        # écart on se recalibre), jamais la VITESSE (de combien). La diviser deux fois
        # écrasait le recalibrage et reproduisait exactement le défaut de la v41.21.
        pas = max(pression_structure, pression_habituation)
        etat.seuil_base = (1.0 - pas) * etat.seuil_base + pas * moyenne_glissante
        etat.cohesion_jour, etat.friction_jour = cohesion, friction
        etat.pression_expansion_jour = max(pression_structure, pression_habituation)

    etat_thermostat = "Stable"
    mutation_possible = (etat.jours_depuis_mutation >= JOURS_ENTRE_MUTATIONS
                         and etat.agent.dim_bus + 16 <= DIM_BUS_MAX
                         and etat.plasticite_base > SEUIL_APHASIE_NEUROGENESE)

    if etat.cooldown_jours > 0:
        etat.cooldown_jours -= 1
        etat_thermostat = f"Conv ({etat.cooldown_jours}j)"
        if erreur_moyenne < etat.seuil_base * 2:
            etat.cooldown_jours = 0
            etat_thermostat = "Guérison"
    elif erreur_moyenne > etat.seuil_actuel and etat.jour > 1:
        if mutation_possible:
            # --- v41.24 : LA CROISSANCE N'EST PLUS UN DROIT, C'EST UN BUDGET ---
            #
            # 🔴 CE QUE ÇA CORRIGE — l'hypertrophie mesurée le 18/08. Avec un plafond
            # relevé à 512, `dim_bus` finissait à **512/512 sur 3 graines (31 mutations)**
            # pour un niveau atteint IDENTIQUE (4/3/4), une énergie divisée par 11
            # (0,19 → 0,017) et un effort triplé. Et 60 % des synapses du gros cerveau
            # n'étaient JAMAIS myélinisées : on ajoutait du tissu, pas de la capacité.
            #
            # LE PIÈGE D'AUTO-JUSTIFICATION : un gros réseau prédit marginalement mieux
            # (erreur 0,0013 contre 0,0047), donc `seuil_base` relaxe vers cette erreur
            # ultra-basse, donc l'agent se crée un standard d'exigence infini — chaque
            # agrandissement justifie le suivant. Le frein v41.23 stabilise le RAPPORT
            # erreur/seuil, jamais la TAILLE.
            #
            # LE PRINCIPE (décision utilisateur) : un organisme n'investit dans du tissu
            # neural que si les calories dépensées rapportent un bénéfice de survie.
            #
            #     rendement = Δ(erreur JEPA gagnée) / Δ(effort métabolique payé)
            #     vitalité  = rendement courant / rendement de référence
            #     ajout     = round(AJOUT_DIM_BASE × vitalité)
            #
            # ⚠️ IL N'Y A AUCUN `if rendement < X`. L'arrêt est ARITHMÉTIQUE :
            # `round(16 × 0.03) == 0`. L'agent déclenche sa mutation, la biologie ne lui
            # accorde aucun neurone. Mesuré sur les gains réels de `t512_g7` : l'ajout
            # tombe à 16 → 11 → 7 → 5 → 3 → 2 → 1 → 0 au fil des mutations.
            #
            # ⚠️ `rendement_ref` EST UN CLIQUET, jamais une valeur figée au premier
            # rendement. Testé : si la première mutation tombe sur un rendement
            # anormalement bas (l'erreur baissait déjà toute seule), une référence figée
            # fait exploser la vitalité — mesuré **ajout = 1020 dimensions**. Montée
            # immédiate, descente ~50× plus lente : c'est exactement la discipline de
            # `reference_choc_dopamine` (v37.1-fix1) et de `norme_naissance` (v34.0-fix2).
            # Le `min(…, 1.0)` borne l'ajout à sa valeur de base : on ne finance jamais
            # plus qu'un organisme sain.
            _effort_moyen = etat.effort_metabolique_jour / max(1, ticks_du_jour)

            if etat.erreur_avant_mutation is not None:
                # Gain cognitif — nul si la mutation a DÉGRADÉ la prédiction (14 des 30
                # mutations mesurées sur t512_g7 n'amélioraient rien).
                _gain = max(0.0, etat.erreur_avant_mutation - erreur_moyenne)
                # Surcoût métabolique permanent : le prix à payer, chaque tick, à vie.
                _surcout = max(1e-4, _effort_moyen - etat.effort_avant_mutation)
                _rendement = _gain / _surcout
                if etat.rendement_moyen is None:
                    etat.rendement_moyen = _rendement
                    etat.rendement_ref = max(_rendement, 1e-9)
                else:
                    # Lissé au MÊME pas que le thermostat : tout le système respire
                    # sur la même horloge.
                    etat.rendement_moyen = ((1.0 - pas) * etat.rendement_moyen
                                            + pas * _rendement)
                    if etat.rendement_moyen > etat.rendement_ref:
                        etat.rendement_ref = etat.rendement_moyen        # montée immédiate
                    else:
                        etat.rendement_ref += ((etat.rendement_moyen - etat.rendement_ref)
                                               / INERTIE_OUBLI_RENDEMENT)  # descente lente

            if etat.rendement_moyen is None:
                _ajout = AJOUT_DIM_BASE      # force vitale de naissance : rien à comparer
                etat.vitalite_jour = 1.0
            else:
                etat.vitalite_jour = min(etat.rendement_moyen
                                         / max(etat.rendement_ref, 1e-9), 1.0)
                _ajout = int(round(AJOUT_DIM_BASE * etat.vitalite_jour))

            # Le plafond reste une borne matérielle, jamais le régulateur.
            _ajout = min(_ajout, DIM_BUS_MAX - etat.agent.dim_bus)

            if _ajout > 0:
                etat.agent.declencher_neurogenese(ajout_dim=_ajout)
                etat.jours_depuis_mutation = 0
                ratio_gravite = erreur_moyenne / max(etat.seuil_base, 1e-9)
                etat.cooldown_jours = min(5, max(1, int(ratio_gravite * 0.1)))
                etat.seuil_actuel = min(etat.seuil_actuel + (erreur_moyenne * 1.5),
                                        etat.seuil_base + etat.delta_max)
                # Base de comparaison pour juger CETTE mutation la prochaine fois.
                etat.erreur_avant_mutation = erreur_moyenne
                etat.effort_avant_mutation = _effort_moyen
                etat_thermostat = f"MUTATION +{_ajout} !"
            else:
                # Fonds insuffisants : l'agent voulait grandir, son métabolisme refuse.
                etat.cooldown_jours = 1
                etat_thermostat = "Rendement nul (croissance refusée)"
        elif etat.plasticite_base <= SEUIL_APHASIE_NEUROGENESE:
            etat_thermostat = "Aphasique (neurogenèse suspendue)"
        else:
            etat_thermostat = "Saturé" if etat.agent.dim_bus + 16 > DIM_BUS_MAX else "Réfractaire"

    if etat.seuil_actuel > etat.seuil_base:
        etat.seuil_actuel = max(etat.seuil_base, etat.seuil_actuel * 0.8)

    # École de Rattrapage Vocal, second volet (v24.0-fix1) : tant que le palier vocal
    # est encore bas (voir PALIER_VOCAL_FIN_PROTECTION), l'érosion nocturne des couches
    # audio est fortement atténuée — laisse au gradient accumulé pendant la journée le
    # temps de survivre à plusieurs nuits et d'amorcer sa propre myélinisation, plutôt
    # que d'être rasé avant d'avoir pu s'accumuler (diagnostiqué sur un run réel de
    # 1000 jours : porte_auditive restée à norme exactement zéro, jamais protégée).
    attenuation_audio = (ATTENUATION_EROSION_AUDIO_DEBUT
                          if etat.palier_vocal <= PALIER_VOCAL_FIN_PROTECTION else 1.0)
    synapses_mortes = etat.agent.cycle_sommeil_global(
        plasticite=etat.plasticite_base, attenuation_erosion_audio=attenuation_audio,
    )
    rec_moy = sum(etat.recompenses_journee) / ticks_du_jour if etat.recompenses_journee else 0.0

    etat_mental, pct_dopamine = etat_mental_dopamine(etat.teneur_dopamine, DOPAMINE_MIN, DOPAMINE_NEUTRE, DOPAMINE_MAX)
    etat_plasticite = etat_empreinte(etat.empreinte_enfance)

    print(f"\n🌙 Jour {etat.jour:03d} [{etat.nom_classe}]")
    print(f"  ├─ État Mental    : {etat_mental} (Dopamine: {etat.teneur_dopamine:.3f}/10.0 [{pct_dopamine:.0f}%])")
    print(f"  ├─ Plasticité     : {etat_plasticite} (Bus: {etat.agent.dim_bus} dims, "
          f"Empreinte: {etat.empreinte_enfance:.2f}, Plasticité base: {etat.plasticite_base:.2f})")
    if etat.doorkey_actif and etat.detecteur.actif:
        nom_palier = DetecteurJalonsDoorKey.NOMS[etat.palier_cible - 1]
        maitrise_txt = f"{taux_maitrise * 100:.0f}%" if taux_maitrise is not None else "N/A"
        sous_seuil_txt = "Amorçage" if etat.gestionnaire_cursus.sous_seuil_actuel == 1 else "Abnégation"
        print(f"  ├─ Progrès Jalon  : 🎯 Palier {etat.palier_cible} ({nom_palier}) — "
              f"{etat.succes_palier_cible_jour}/{etat.episodes_jour} épisodes réussis (taux: {maitrise_txt})")
        print(f"  ├─ Abnégation     : 📿 Sous-Seuil {etat.gestionnaire_cursus.sous_seuil_actuel} ({sous_seuil_txt}) — "
              f"{etat.gestionnaire_cursus.succes_sous_seuil_courant}/{SUCCES_PAR_SOUS_SEUIL} succès "
              f"(complexité: x{etat.facteur_complexite_jour:.1f})")
        mode_txt = "🕊️ Libre (aucune récompense de guidage)" if etat.mode_libre else "🧭 Guidé (béquille active)"
        print(f"  ├─ Mode Décision  : {mode_txt} — Planification: {etat.force_planification_jour:.2f}, "
              f"Entropie: {etat.coeff_entropie_jour:.2f}")
    # v40.0 — la confiance en la planification, affichée sur TOUS les niveaux (la mécanique
    # est globale, contrairement au bloc DoorKey ci-dessus). Se lit comme une balance : la
    # part de vécu que l'agent a trouvée bénéfique.
    _f = etat.agent.force_planification_vecue()
    _okay, _danger = etat.agent.vecu_okay, etat.agent.vecu_danger
    if _f < 0.15:
        _profil = "🐣 réflexe pur (n'ose pas encore planifier)"
    elif _f < 0.50:
        _profil = "🌱 planification naissante"
    elif _f < 0.80:
        _profil = "🧭 planifie volontiers"
    else:
        _profil = "🦉 délibère largement"
    print(f"  ├─ Planif. v40    : {_profil} — force {_f:.3f} "
          f"(okay {_okay:.2f} / danger {_danger:.2f})")
    # v40.1 — l'envie de vivre et ses deux forces opposées. Sans cette ligne, la mécanique
    # serait latente et indémontrable sur un run long (leçon v29.1).
    _me = getattr(etat.agent, "mesure_envie", None) or {}
    if _me:
        _envie = _me.get("envie", 1.0)
        if _envie < 0.05:
            _etat_vie = "💀 éteint (ne tente plus rien)"
        elif _envie < 0.35:
            _etat_vie = "🥀 la foi vacille"
        elif _envie < 0.75:
            _etat_vie = "🚶 avance prudemment"
        else:
            _etat_vie = "🔥 tente quand même"
        print(f"  ├─ Envie v40.1    : {_etat_vie} — envie {_envie:.4f} "
              f"| lucidité {_me.get('lucidite', 0.0):.3f} ↓ "
              f"foi {_me.get('foi', 0.0):.3f} ↑ | acceptation {_me.get('acceptation', 0.0):.4f}")
    if etat.detecteur_portes.actif and etat.portes_franchies_jour > 0:
        print(f"  ├─ Portes         : 🚪 {etat.portes_franchies_jour} porte(s) franchie(s) aujourd'hui")
    if _quete_auto_active(etat) and etat.detecteur_progres.actif and etat.progres_personnel_jour > 0:
        # v33.0-etape0.5 : le suffixe signale que la quête auto tourne sur DoorKey, cas
        # qui n'existait pas avant — sans lui, cette ligne serait indiscernable d'un run
        # normal sur Empty/MultiRoom au moment de relire les logs du test d'ablation.
        suffixe_ablation = " [ABLATION INVERSÉE — Mode Libre DoorKey]" if etat.doorkey_actif else ""
        print(f"  ├─ Quête Auto     : 🧭 {etat.progres_personnel_jour} nouveaux records "
              f"de proximité au But{suffixe_ablation}")
    print(f"  ├─ Consolidations : 💤 {nb_reves} souvenirs rejoués ({pourcentage_reve*100:.3f}% de la journée, "
          f"perte rêves: {perte_reves:.4f})")
    # v30.1 — l'ISSUE du sursaut, pas seulement son nombre : c'est ce taux qui dira si
    # une extension adaptative doit renforcer (« muscle ») ou atténuer (« habituation »).
    victoires_sursaut = getattr(etat, "sursauts_suivis_victoire_jour", 0)
    echecs_sursaut = getattr(etat, "sursauts_suivis_echec_jour", 0)
    if victoires_sursaut + echecs_sursaut > 0:
        taux_sursaut = 100.0 * victoires_sursaut / (victoires_sursaut + echecs_sursaut)
        issue_txt = f", {etat.sursauts_jour} Sursaut(s) → {taux_sursaut:.0f}% de victoires"
    else:
        issue_txt = f", {etat.sursauts_jour} Sursaut(s) de Volonté"
    print(f"  ├─ Potentiomètre  : ⏳ Patience de base du jour: {etat.patience_base_jour} ticks/épisode "
          f"({etat.abandons_patience_jour} abandon(s) lucide(s){issue_txt}, "
          f"patience_min actuelle: {etat.module_acceptation.patience_min})")
    # v41.30 — TÉLÉMÉTRIE DES TROIS CONSTANTES SUPPRIMÉES. Sans elle, la mécanique serait
    # invisible sur un run long et son utilité indémontrable (leçon de la v29.1).
    _ma = etat.module_acceptation
    _reussite = _ma.duree_reussite_vie
    _echec = _ma.duree_echec_vie
    _txt_ecart = ("jamais mesuré" if (_reussite is None or _echec is None)
                  else f"réussite {_reussite:.0f}t vs abandon {_echec:.0f}t")
    print(f"  │                   🧬 Endurance de vie : patience dérivée "
          f"{_ma.patience_de_vie():.0f} ticks (capital {_ma.capital_endurance:.3f}) — {_txt_ecart}")
    _rythme = getattr(etat.moteur_bio, "rythme_episodes", EPISODES_PAR_JOURNEE_NAISSANCE)
    print(f"  │                   🍽️ Rythme métabolique : {_rythme:.2f} épisode(s)/jour vécu(s) "
          f"({etat.episodes_jour} aujourd'hui) → besoin {besoin_par_axe(_rythme):.2f}/axe, "
          f"biotope {NB_SOURCES_FOOD}+{NB_SOURCES_WATER} source(s) [densité de la SURFACE, "
          f"découplée du besoin — v41.30-fix1])")
    if etat.mode_libre and etat.sous_objectifs_curiosite_jour > 0:
        print(f"  ├─ Curiosité JEPA : ✨ {etat.sous_objectifs_curiosite_jour} sous-quête(s) intrinsèque(s) générée(s)")
    # v33.0-etape0 — CHRONOMÉTRIE DES JALONS (conditionnelle : rien à dire si aucun
    # épisode DoorKey ce jour-là). Chaque delta affiche sa moyenne ET son effectif :
    # « Δt3 12 ticks (n=1) » et « Δt3 12 ticks (n=200) » ne se lisent pas pareil, et
    # un « n=0 » sur Δt3 est en soi LE résultat (le segment n'est jamais atteint).
    # v33.0-etape0.6 — chronologie des victoires. Affichée dès qu'une victoire a eu lieu
    # dans la vie de l'agent (sinon la ligne dirait « jamais » pendant des centaines de
    # jours sans rien apprendre à personne).
    if etat.victoires_totales > 0:
        _tendance = ""
        if len(etat.intervalles_victoires) >= 4:
            _m = len(etat.intervalles_victoires) // 2
            _d = etat.intervalles_victoires[:_m]
            _f = etat.intervalles_victoires[_m:]
            _md = sum(_d) / len(_d)
            if _md > 0:
                _r = (sum(_f) / len(_f)) / _md
                _verdict = ("↘️ se rapprochent" if _r < 0.8
                            else "↗️ s'espacent" if _r > 1.25 else "➡️ stationnaire")
                _tendance = f" — tendance {_r:.2f} {_verdict}"
        _moy = (f"{sum(etat.intervalles_victoires) / len(etat.intervalles_victoires):.0f}"
                if etat.intervalles_victoires else "—")
        # v33.0-etape0.6-fix1 : le contexte est affiché AVEC le chiffre. Sans lui, un
        # « intervalle moyen 81 j » ne dit pas s'il parle de Primaire ou du Palier 7 —
        # c'est exactement l'ambiguïté qui a produit le faux « ↗️ s'espacent » du run
        # 78859bgs. Le compte de la série en cours (n=…) rappelle en outre combien de
        # victoires soutiennent réellement la tendance affichée.
        _ctx = etat.contexte_victoires
        _ctx_txt = (f"P{_ctx[1]}" if _ctx and _ctx[1] is not None
                    else f"niv.{_ctx[0]}" if _ctx else "—")
        print(f"  ├─ Chrono Victoire: 🏆 {etat.victoires_totales} victoire(s) en {etat.jour} jour(s)"
              f" | dernière il y a {etat.jours_depuis_victoire} j"
              f" | [{_ctx_txt}] intervalle moyen {_moy} j (n={len(etat.intervalles_victoires)})"
              f"{_tendance}")

    if getattr(etat, "jalon_episodes_doorkey_jour", 0) > 0:
        def _fmt_delta(cumul, n):
            return f"{cumul / n:.1f} ticks (n={n})" if n > 0 else "JAMAIS ATTEINT (n=0)"
        print(f"  ├─ Jalons DoorKey : ⏱️  Δt1 clé {_fmt_delta(etat.jalon_delta1_cumul_jour, etat.jalon_delta1_n_jour)}"
              f" | Δt2 porte {_fmt_delta(etat.jalon_delta2_cumul_jour, etat.jalon_delta2_n_jour)}"
              f" | Δt3 sortie {_fmt_delta(etat.jalon_delta3_cumul_jour, etat.jalon_delta3_n_jour)}"
              f" | 🍎 {etat.jalon_ressources_post_cle_jour} ressource(s) mangée(s) clé en main")
    quete_bio_txt = etat.moteur_bio.quete_active["type"] if etat.moteur_bio.quete_active else "Aucune"
    print(f"  ├─ État Viscéral  : 🍎 Satiété {etat.moteur_bio.satiete:.2f} | 💧 Hydratation {etat.moteur_bio.hydratation:.2f} | "
          f"✨ Stimulation {etat.moteur_bio.stimulation:.2f} (Quête: {quete_bio_txt})")
    # --- Les 5 Sens (v29.1, télémétrie) : la ligne n'est affichée que si des ticks
    # sensoriels ont réellement été vécus ce jour-là (0 en mode "vocal_isole" pur, où
    # aucun env MiniGrid n'est lu — même logique conditionnelle que la Curiosité JEPA
    # ou les Portes ci-dessus, plutôt qu'une ligne vide et trompeuse). ---
    ticks_sens = getattr(etat, "ticks_sensoriels_jour", 0)
    if ticks_sens > 0:
        bus_actif = getattr(etat, "bus_sensoriel", None) is not None and etat.bus_sensoriel.actif
        etat_bus = "" if bus_actif else "  ⚠️ BUS DÉSACTIVÉ"
        pct_contact = 100.0 * etat.toucher_contact_jour / ticks_sens
        pct_portage = 100.0 * etat.toucher_portage_jour / ticks_sens
        pct_odorat = 100.0 * etat.odorat_ticks_actifs_jour / ticks_sens
        print(f"  ├─ Les 5 Sens     : ✋ Contact {pct_contact:.1f}% | 🔑 Portage {pct_portage:.1f}% | "
              f"👃 Odorat {pct_odorat:.1f}% des ticks (max {etat.odorat_max_jour:.2f}) | "
              f"👅 Goût {etat.gout_ticks_actifs_jour} tick(s){etat_bus}")
        # v32.0 — la clinotaxie. Affichée seulement si l'odeur a réellement VARIÉ dans la
        # journée : sur un run où aucune source n'est jamais approchée, la ligne serait
        # un « 0 % » trompeur plutôt qu'une absence de mesure.
        ticks_variation = getattr(etat, "odorat_ticks_variation_jour", 0)
        if ticks_variation > 0:
            pct_approche = 100.0 * etat.odorat_ticks_approche_jour / ticks_variation
            delta_moyen = etat.odorat_delta_cumul_jour / ticks_variation
            print(f"  ├─ Clinotaxie     : 🧭 Approche {pct_approche:.1f}% des ticks de variation "
                  f"(|ΔS| moyen {delta_moyen:.3f} sur {ticks_variation} tick(s))")
        # v30.0 — le 6ème sens. Ligne affichée UNIQUEMENT si un plug a réellement été
        # perçu ce jour-là : sur un run sans greffon (le cas par défaut), rien ne
        # s'affiche et le bilan reste exactement celui de la v29.1.
        if getattr(etat, "exo_ticks_actifs_jour", 0) > 0:
            pct_exo = 100.0 * etat.exo_ticks_actifs_jour / ticks_sens
            intensite_moy = etat.exo_cumul_jour / ticks_sens
            print(f"  ├─ Exo-Sens (C3)  : 🔌 Perçu {pct_exo:.1f}% des ticks "
                  f"(intensité moy {intensite_moy:.3f}, max {etat.exo_max_jour:.3f}) — "
                  f"{etat.perceptions_exo_jour} rafraîchissement(s) du bus")

    effort_moyen_jour = etat.effort_metabolique_jour / ticks_du_jour
    print(f"  ├─ Métabolisme    : r_bio cumulé {etat.r_bio_jour:+.3f} — {etat.food_consommes_jour} Nourriture(s), "
          f"{etat.water_consommes_jour} Eau(x) consommée(s) — effort moyen (20% cerveau/80% corps): {effort_moyen_jour:.3f}")

    # --- v41.32-etape4 : LA DISCRIMINATION — mur ou ressource ? ---
    # Distance de variation totale entre les deux distributions d'actions, à
    # `contact_frontal = 1`. Proche de 0 : l'agent réagit IDENTIQUEMENT à un mur et à une
    # pomme, donc il ne discrimine pas. Ligne conditionnelle (règle v29.1).
    _disc = _resumer_discrimination(etat)
    if _disc is not None:
        _d, _nm, _nr, _pm, _pr = _disc
        print(f"  ├─ Discrim v41.32 : 🧱 {_nm} tick(s) face à un MUR | "
              f"🍎 {_nr} face à une RESSOURCE | distance des politiques {_d:.4f} "
              f"(0 = indiscernables)")
        _noms = {0: "gauche", 1: "droite", 2: "avancer", 3: "consommer",
                 4: "poser", 5: "activer", 6: "parler"}
        _det = " ".join(f"{_noms[a][:4]} {100*_pm[a]:.0f}/{100*_pr[a]:.0f}" for a in range(7))
        print(f"  │                   ↳ % mur/ressource — {_det}")

    # --- v41.32-etape2 : LE FOURRAGE — la conjonction, décomposée ---
    # Manger exige DEUX conditions simultanées (v41.2-fix5/fix6) : faire FACE à la
    # ressource, et jouer le geste. Cette ligne dit laquelle des deux manque.
    #   - `occasions` bas  -> défaut de NAVIGATION (l'agent ne se met pas en position)
    #   - `saisie` bas     -> défaut de DÉCISION (il y est, mais ne tente pas)
    # ⚠️ Ligne CONDITIONNELLE (règle v29.1) : sans détecteur actif, ne rien afficher
    # plutôt que des zéros qui feraient passer une sonde inactive pour une mesure nulle.
    _occ = getattr(etat, "fourrage_occasions_jour", 0)
    _tent = getattr(etat, "fourrage_tentatives_jour", 0)
    if _occ > 0 or _tent > 0:
        _sais = getattr(etat, "fourrage_saisies_jour", 0)
        _taux = 100.0 * _sais / _occ if _occ else 0.0
        _faim = (getattr(etat, "fourrage_faim_aux_occasions", 0.0) / _occ) if _occ else 0.0
        _vides = _tent - _sais
        print(f"  ├─ Fourrage v41.32: 🍽️  {_occ} occasion(s) (face à une ressource) | "
              f"{_sais} saisie(s) → taux {_taux:.1f}% | faim moyenne aux occasions {_faim:.3f}")
        print(f"  │                   ↳ {_tent} geste(s) `consommer` joué(s), dont "
              f"{_vides} dans le vide")

    # --- v41.32-etape1 : LA TABLE DE MIXAGE, mesurée ---
    # Ce que chaque terme de la récompense PÈSE (moyenne) et ce qu'il VARIE (écart-type).
    # Les termes sont triés par écart-type DÉCROISSANT, pas par moyenne : c'est la
    # dispersion qui porte le signal d'apprentissage, une constante ne distingue aucune
    # action d'une autre. Un terme en tête de liste est un terme que le gradient entend ;
    # un terme en queue est un décalage d'origine, si gros soit-il.
    #
    # ⚠️ Ligne CONDITIONNELLE (règle v29.1) : sur un jour sans aucun tick — vocal isolé,
    # journée avortée — ne rien afficher plutôt que des zéros trompeurs, qui feraient
    # passer une sonde INACTIVE pour une mesure NULLE (distinction ablation vide /
    # ablation négative de la règle de mesure).
    _mix_n = getattr(etat, "mix_n", 0)
    if _mix_n > 0:
        _stats_mix = _resumer_mixage(etat)
        # `Total` est la récompense assemblée : c'est le dénominateur de lecture, pas un
        # terme. Affiché à part pour qu'on puisse rapporter chaque part au tout.
        _tot = _stats_mix.pop("Total", None)
        _classe = sorted(_stats_mix.items(), key=lambda kv: -kv[1][1])
        _tete = " | ".join(f"{nom} {moy:+.4f}±{ec:.4f}" for nom, (moy, ec) in _classe[:4])
        print(f"  ├─ Mixage v41.32  : 🎚️  {_mix_n} tick(s) | par σ décroissant → {_tete}")
        _queue = " | ".join(f"{nom} {moy:+.4f}±{ec:.4f}" for nom, (moy, ec) in _classe[4:])
        if _queue:
            print(f"  │                   ↳ {_queue}")
        if _tot is not None:
            print(f"  │                   ↳ TOTAL assemblé {_tot[0]:+.4f}±{_tot[1]:.4f} "
                  f"(les 11 termes sont sommés à poids 1)")

    # --- v34.0-etape0 : les mesures préalables au chantier Fatigue/Mortalité/Soin ---
    # Ligne unique et dense : c'est un cadran de calibrage, pas une métrique de suivi.
    # Elle disparaîtra quand les constantes de la v34 auront été calibrées.
    # v35.0 — où en est l'agent dans le cursus, et à quelle distance de la promotion.
    _t = _taux_maitrise_niveau(etat)
    _n = len(etat.historique_episodes_niveau)
    _txt = (f"{_t:.0%} (n={_n})" if _t is not None
            else f"— (n={_n}/{MIN_EPISODES_PROMOTION} requis)")
    # v35.1 — l'état de l'aide, lisible d'un coup d'œil : sevrage en cours, filet déployé,
    # ou régime nominal.
    _g = etat.facteur_guidage_jour
    if _g > 1.0:
        _aide = f"🛟 filet ×{_g:.1f} ({etat.jours_stagnation_niveau} j sans victoire)"
    elif _g <= 0.0:
        _aide = "🕊️ autonome (aide nulle)"
    elif _g < 1.0:
        _aide = f"📉 sevrage {_g:.0%}"
    else:
        _aide = "🤝 aide pleine"
    # v40.2 — la MATURITÉ remplace « série x/2 » : on ne compte plus des examens réussis,
    # on affiche les trois facteurs dont le produit décide de la promotion.
    _h = etat.historique_episodes_niveau
    _mat = getattr(etat, "maturite_niveau_jour", 0.0)
    _reg = sum(_h) / max(len(_h), 1)
    _cons = min(1.0, len(_h) / FENETRE_PROMOTION)
    # v41.5 — l'autonomie du CRITÈRE (lue le soir, synchrone avec la régularité), pas celle
    # du matin : c'est elle qui a décidé de la promotion, et c'est elle qui rend le produit
    # affiché cohérent avec la maturité affichée.
    _auto = getattr(etat, "autonomie_au_critere",
                    1.0 - max(0.0, min(1.0, etat.facteur_guidage_jour)))
    print(f"  ├─ Cursus         : 🎓 Niveau {etat.niveau_actuel + 1}/{len(PROGRAMME)} — "
          f"maîtrise {_txt} | {_aide}")
    print(f"  ├─ Maturité v40.2 : 🌡️ {_mat:.3f} / {SEUIL_MATURITE:.2f} — "
          f"régularité {_reg:.0%} × consolidation {_cons:.0%} × autonomie {_auto:.0%}")
    # v41.4 — la maîtrise générale et l'héritage. L'écart entre le taux de sevrage et le
    # taux du niveau EST l'héritage : à fenêtre pleine il se referme, par construction.
    _tg = _taux_maitrise_generale(etat)
    _tg_txt = (f"{_tg:.0%}" if _tg is not None
               else f"— (n={len(getattr(etat, 'historique_episodes_general', []))}"
                    f"/{MIN_EPISODES_PROMOTION})")
    _tsev = getattr(etat, "taux_sevrage_jour", 0.0)
    _par = getattr(etat, "parente_niveau_precedent", 0.0)
    # v41.4-fix1 — les deux termes sont lus AU MÊME INSTANT (début de journée), sinon
    # l'écart mesure la dérive de la fenêtre glissante et non l'héritage.
    _herit = _tsev - getattr(etat, "taux_niveau_au_sevrage", _tsev)
    # v41.6 (P17) — la distribution réellement tirée dans la journée. Si `révisions` reste
    # à 0 sur un agent qui échoue, la mécanique ne mord pas ; si `incursions` reste à 0 sur
    # un agent qui maîtrise, la queue droite est trop fine.
    _rev = getattr(etat, "p17_revisions_jour", 0)
    _inc = getattr(etat, "p17_incursions_jour", 0)
    _hors = getattr(etat, "p17_episodes_hors_reference_jour", 0)
    _vhors = getattr(etat, "p17_victoires_hors_reference_jour", 0)
    _tot_ep = len(_h) + _hors
    if _tot_ep > 0:
        _nv, _pd = _distribution_cursus(etat)
        _p_ref = next((p for n_, p in zip(_nv, _pd) if n_ == etat.niveau_actuel), 0.0)
        print(f"  ├─ Cursus P17     : 🎲 {_rev} révision(s) · {_inc} incursion(s) — "
              f"défi visé {_p_ref:.0%} | hors palier {_vhors}/{_hors} réussis")
    print(f"  ├─ Maîtrise v41.4 : 🌍 générale {_tg_txt} | sevrage sur {_tsev:.0%} "
          f"(héritage {_herit:+.0%}, parenté carte {_par:.0%})")

    # v36.0 — ce que la mémoire reçoit, ce qu'elle abstrait, ce qu'elle rend.
    _sv = etat.memoire_episodique_spatiale.souvenirs
    _conf = sum(s.get('confirmations', 1) for s in _sv) / max(1, len(_sv))
    _typ = len({s['type'] for s in _sv})
    print(f"  ├─ Mémoire v36    : 📥 {etat.memoire_ecritures_jour} écriture(s) | "
          f"🔁 {_conf:.1f} confirmation(s)/repère | 🏷️ {_typ} type(s) distinct(s) | "
          f"💭 rappel marquant {100.0 * etat.memoire_rappels_marquants_jour / ticks_du_jour:.1f}% des ticks")

    # v41.11 — THERMOCEPTION. Ligne CONDITIONNELLE : sur une carte sans source brûlante le
    # capteur est silencieux par construction (0.0 partout, vérifié sur Empty-5x5,
    # DoorKey-6x6 et Empty-8x8), et afficher des zéros ferait croire à un sens mort.
    # `Approche` est LA mesure qui compte : si l'agent apprend le danger, ce taux doit
    # BAISSER avec l'âge — c'est ce qui distinguera un sens utile d'un sens décoratif.
    _ticks_chaud = getattr(etat, "chaleur_ticks_actifs_jour", 0)
    if _ticks_chaud:
        _var_chaud = getattr(etat, "chaleur_ticks_variation_jour", 0)
        _appr_chaud = getattr(etat, "chaleur_ticks_approche_jour", 0)
        print(f"  ├─ Thermocep.v41.11: 🔥 {_ticks_chaud}/{ticks_du_jour} tick(s) au contact d'un danger | "
              f"chaleur moy {getattr(etat, 'chaleur_cumul_jour', 0.0) / ticks_du_jour:.3f} "
              f"(max {getattr(etat, 'chaleur_max_jour', 0.0):.3f}) | "
              f"🧭 approche {100.0 * _appr_chaud / max(1, _var_chaud):.1f}% des ticks de variation")
        # v41.25 — la SURVIE, la mesure qui juge la nociception. Conditionnelle comme
        # le reste du bloc : sur une carte sans danger, ces chiffres n'ont pas de sens.
        _morts = getattr(etat, "morts_jour", 0)
        _gagnes = getattr(etat, "episodes_gagnes_jour", 0)
        _fins = _morts + _gagnes
        _dm = getattr(etat, "douleur_cumul_jour", 0.0) / max(ticks_du_jour, 1)
        print(f"  ├─ Douleur v41.26: 🩹 moy {_dm:.4f} (max "
              f"{getattr(etat, 'douleur_max_jour', 0.0):.3f}) | "
              f"{getattr(etat, 'douleur_ticks_actifs_jour', 0)}/{ticks_du_jour} tick(s) douloureux | "
              f"habituation {etat.moteur_bio.chaleur_habituee:.3f}"
              f"{'' if DOULEUR_THERMIQUE_ACTIVE else ' [CALCULÉE, NON FACTURÉE — témoin]'}")
        print(f"  ├─ Douleur v41.27: 🤕 corps moy "
              f"{getattr(etat, 'douleur_corp_cumul_jour', 0.0) / max(ticks_du_jour, 1):.4f} "
              f"(max {getattr(etat, 'douleur_corp_max_jour', 0.0):.3f}) | "
              f"💥 {getattr(etat, 'chocs_muraux_jour', 0)} choc(s) mural(aux) | "
              f"⏳ {getattr(etat, 'ticks_perdus_mort_jour', 0)} tick(s) perdus (mort)")
        print(f"  ├─ Survie v41.25 : {'💀' if _morts else '🛡️'} {_morts} mort(s) / "
              f"{_gagnes} victoire(s) — survie {100.0 * _gagnes / max(_fins, 1):.0f}% | "
              f"douleur {'ON' if DOULEUR_THERMIQUE_ACTIVE else 'OFF (témoin)'} | "
              f"chaleur moy. à la mort "
              f"{getattr(etat, 'chaleur_a_la_mort_jour', 0.0) / max(_morts, 1):.3f}")

    _amp = getattr(etat, "jepa_amplitude_cumul_jour", 0.0) / ticks_du_jour
    _conc = getattr(etat, "jepa_concentration_cumul_jour", 0.0) / ticks_du_jour
    print(f"  ├─ JEPA v41.13    : 🎯 amplitude cible {_amp:.4f} | "
          f"📍 concentration {_conc:.3f} (0.25 = étalé, 1.0 = un seul coin) | "
          f"pire dim {getattr(etat, 'jepa_err_max_dim_jour', 0.0):.5f}")
    print(f"  ├─ Toucher v41.12 : 🖐️ pression moy {getattr(etat, 'pression_cumul_jour', 0.0) / ticks_du_jour:.3f} "
          f"(max {getattr(etat, 'pression_max_jour', 0.0):.3f}) | "
          f"↔️ asymétrie moy {getattr(etat, 'asymetrie_ecart_cumul_jour', 0.0) / ticks_du_jour:.3f} "
          f"(0 = aucun signal latéral)")

    # v41.19 — LE COÛT MOTEUR RÉEL, action par action. Compare ce que la table en dur
    # FACTURE à ce que l'action FAIT. Une action stérile est un geste payé plein tarif
    # pour un travail qui n'a pas eu lieu. Ligne conditionnelle (rien à dire si la sonde
    # n'a rien vu), comme les blocs `Sens_*` et C3.
    _cm = getattr(etat, "cout_moteur_reel_jour", {}) or {}
    if _cm:
        _tot = sum(s["n"] for s in _cm.values()) or 1
        _st = sum(s["sterile"] for s in _cm.values())
        _detail = " ".join(
            f"a{a}:{s['n']*100//_tot}%/{s['sterile']*100//max(1,s['n'])}st"
            for a, s in sorted(_cm.items()))
        print(f"  ├─ Coût moteur v41.19: ⚙️ {_st*100//_tot}% de gestes STÉRILES "
              f"({_st}/{_tot}) | par action (part/stérile) — {_detail}")
        # v41.31 — CE QUE LE GRADIENT CAUSAL A RÉELLEMENT MASQUÉ. Sans cette ligne, la
        # mécanique serait invisible sur un run long et son utilité indémontrable
        # (leçon v29.1). Conditionnelle : rien à afficher si la branche est inactive.
        _gt = getattr(etat, "gradient_ticks_total", 0)
        if GRADIENT_CAUSAL_ACTIF and _gt:
            _ret = getattr(etat, "gradient_ticks_credites", 0)
            print(f"  │                   🎯 Gradient causal v41.31 : {_ret}/{_gt} tick(s) "
                  f"crédité(s) ({100*_ret//max(1,_gt)}%) — dénominateur de l'acteur, "
                  f"jamais {_gt}")
        # v41.48 — le rendement mécanique de la journée (même discipline v29.1 :
        # conditionnelle, pour ne pas logger un zéro trompeur quand la branche dort).
        _rm = getattr(etat, "rendement_moyen_journee", None)
        if RENDEMENT_MECANIQUE_ACTIF and _rm is not None:
            _rn = getattr(etat, "rendement_ticks_nuls", 0)
            print(f"  │                   ⚙️  Rendement mécanique v41.48 : {_rm:.3f} moyen "
                  f"— {_rn} geste(s) à rendement NUL "
                  f"({'symétrique' if RENDEMENT_SYMETRIQUE_TEMOIN else 'asymétrique'})")
        _dd = getattr(etat.moteur_bio, "debit_digestif", None)
        if _dd is not None:
            print(f"  │                   🫀 Tube digestif v41.31 : {_dd*ticks_par_jour:.2f} "
                  f"estomac(s)/jour (fossile 3,00) — vidange réelle "
                  f"{_dd*ticks_par_jour/max(RENDEMENT_CONVERSION,1e-6):.2f}/jour")

    # v41.10 — LES CARTES CONNUES. `len(souvenirs)` ne compte que la carte du moment :
    # sans cette ligne, la télémétrie sous-estimerait massivement le vécu spatial réel
    # sous P17 et donnerait exactement la fausse alerte « mémoire à 1 % » qui a motivé le
    # correctif. `retrouvée(s)` est la mesure directe de ce que l'effacement détruisait :
    # chaque retrouvaille est une carte que l'agent aurait redécouverte de zéro.
    _mem = etat.memoire_episodique_spatiale
    _total_souv = _mem.total_souvenirs()
    _nb_cartes = len(_mem.archives_cartes) + 1
    print(f"  ├─ Cartes v41.10  : 🗺️ {_nb_cartes} carte(s) en mémoire | "
          f"📍 {_total_souv} repère(s) au total ({len(_mem.souvenirs)} sur la carte courante) | "
          f"🔙 {_mem.cartes_retrouvees} retrouvée(s) / {_mem.cartes_decouvertes} découverte(s)")

    # v39.0 — L'EMPREINTE DE TYPE : ce que l'agent sait du QUOI, indépendamment du OÙ.
    # Instrumentée dans le même commit que la mécanique (règle v29.1) : sans cette ligne,
    # impossible de vérifier sur un run long que l'abstraction survit bien aux promotions
    # — ce qui est exactement l'objet du correctif.
    _emp = getattr(etat.memoire_episodique_spatiale, 'empreinte_types', {}) or {}
    if _emp:
        _meilleur = max(_emp.items(), key=lambda kv: kv[1]['valence'])
        _pire = min(_emp.items(), key=lambda kv: kv[1]['valence'])
        _vecu = sum(e['confirmations'] for e in _emp.values())
        print(f"  ├─ Empreinte v39  : 🧬 {len(_emp)} type(s) appris sur {_vecu} expérience(s) | "
              f"↑ '{_meilleur[0]}' {_meilleur[1]['valence']:+.3f} "
              f"(×{_meilleur[1]['confirmations']}) | "
              f"↓ '{_pire[0]}' {_pire[1]['valence']:+.3f} (×{_pire[1]['confirmations']})")

    pct_autonomie = 100.0 * etat.ticks_jauges_saines_jour / ticks_du_jour
    deficit_moyen = etat.deficit_cumul_jour / ticks_du_jour
    print(f"  ├─ Calibrage v34  : ⚡ Effort [{(etat.effort_min_jour or 0.0):.2f}–{etat.effort_max_jour:.2f}] | "
          f"💀 Déficit moy {deficit_moyen:.3f} (max {etat.deficit_max_jour:.3f}) | "
          f"🍼 Autonomie {pct_autonomie:.1f}% des ticks | "
          f"🍎 {etat.ressources_vues_jour} ressource(s) sur les cartes du jour")
    print(f"  │                   Jauges min : satiété {etat.jauge_min_satiete_jour:.2f} | "
          f"hydratation {etat.jauge_min_hydratation_jour:.2f} | "
          f"stimulation {etat.jauge_min_stimulation_jour:.2f} | "
          f"ticks en zone critique : {etat.ticks_deficit_critique_jour}/{ticks_du_jour}")
    # v41.2 — le second étage. `vigueur` est la grandeur qui module TOUTE la décision :
    # si elle reste plate à 1.000, le couplage est décoratif et la mécanique ne sert à rien.
    print(f"  ├─ Énergie v41.2  : ⚡ moy {etat.energie_cumul_jour / ticks_du_jour:.3f} "
          f"(min {etat.energie_min_jour:.3f}) | 💪 vigueur moy "
          f"{etat.vigueur_cumul_jour / ticks_du_jour:.3f} (min {etat.vigueur_min_jour:.3f}) | "
          f"🪫 {etat.ticks_energie_basse_jour}/{ticks_du_jour} ticks en basse énergie")
    # v41.2-fix5 — le geste de manger. `part` dit s'il le joue, `efficacité` s'il le joue
    # au bon endroit : un geste fréquent mais inefficace est une politique qui dépense sans
    # se nourrir, indistinguable d'un geste rare si l'on ne regarde que la récolte.
    _n_conso = etat.effort_par_action_jour[ACTION_CONSOMMER][0]
    print(f"  ├─ Geste manger   : 🍽️ {_n_conso}/{ticks_du_jour} ticks "
          f"({_n_conso / ticks_du_jour:.1%}) | efficacité "
          f"{(etat.food_consommes_jour + etat.water_consommes_jour) / max(1, _n_conso):.1%} "
          f"| récolté {etat.food_consommes_jour + etat.water_consommes_jour} "
          f"| soulagement {etat.soulagement_repas_jour:+.2f} "
          f"| 🧈 réserve {etat.moteur_bio.reserve:.2f}")
    # v30.1 — la taille seule ne disait pas si la mémoire SERT : on affiche désormais le
    # taux de saturation (200/200 = plafond `capacite_max` atteint) et la qualité du
    # rappel, pour pouvoir juger si une capacité adaptative apporterait quelque chose.
    nb_souvenirs = len(etat.memoire_episodique_spatiale.souvenirs)
    capacite_mem = etat.memoire_episodique_spatiale.capacite_max
    saturation_txt = " ⚠️ SATURÉE" if nb_souvenirs >= capacite_mem else ""
    rappels_tentes = getattr(etat, "memoire_rappels_tentes_jour", 0)
    if rappels_tentes > 0:
        reussis = etat.memoire_rappels_reussis_jour
        taux = 100.0 * reussis / rappels_tentes
        prox_moy = (etat.memoire_distance_cumul_jour / reussis) if reussis else 0.0
        qualite_txt = (f" — rappel {taux:.0f}% des tentatives "
                       f"(proximité moy {prox_moy:.2f})")
    else:
        qualite_txt = " — aucun rappel tenté (pas de quête de survie active)"
    # v31.0 — la capacité est désormais adaptative : on affiche son origine (dim_bus ×
    # besoin) pour qu'un « N/576 » soit lisible sans aller relire le code.
    if etat.memoire_episodique_spatiale.cap_densite_actif:
        # v31.1 — le cap spatial a bridé la capacité : c'est la taille du MONDE qui
        # limite, pas le cerveau. L'afficher évite de croire à une sous-capacité.
        origine_cap = (f" [cap. bornée par la carte : ×"
                       f"{MemoireEpisodiqueSpatiale.DENSITE_MAX_PAR_CASE}/case]")
    else:
        origine_cap = f" [cap. {etat.agent.dim_bus}×{MemoireEpisodiqueSpatiale.SOUVENIRS_PAR_DIM} adaptée]"
    doublons = etat.memoire_episodique_spatiale.doublons_evites
    if doublons:
        origine_cap += f" — {doublons} doublon(s) évité(s)"
    print(f"  ├─ Mémoire Épiso. : 🗺️ {nb_souvenirs}/{capacite_mem} souvenir(s) spatial(aux){saturation_txt}"
          f"{qualite_txt}{origine_cap}")
    # --- v37.0 : bilan de l'équilibre C1/C2 ---
    # Ligne CONDITIONNELLE (v29.1) : affichée seulement si l'arbitrage a réellement tourné
    # ce jour-là — un jour purement vocal n'a aucun tick moteur, y logger des zéros serait
    # trompeur.
    n_arb = etat.ticks_arbitrage_jour
    if n_arb > 0:
        amp_c1 = etat.amplitude_c1_jour / n_arb
        amp_c2 = etat.amplitude_c2_jour / n_arb
        ratio_c2c1 = amp_c2 / max(1e-9, amp_c1)
        accord_pct = 100.0 * etat.accord_c1c2_jour / n_arb
        # v41.14 — entropie normalisée des votes, dans [0,1]. 0 = la voix répète TOUJOURS
        # la même action (elle est figée, pas décidée) ; 1 = elle répartit ses votes sur
        # toutes les actions. C'est ce qui rend `accord` interprétable.
        def _entropie_votes(hist):
            total = sum(hist.values())
            if total <= 0 or len(hist) <= 1:
                return 0.0
            import math as _m
            h = -sum((n / total) * _m.log(n / total) for n in hist.values() if n > 0)
            return h / _m.log(NUM_ACTIONS_BASE)   # 7 actions réelles (la 8e est masquée)
        entropie_c1 = _entropie_votes(etat.votes_c1_jour)
        entropie_c2 = _entropie_votes(etat.votes_c2_jour)
        gain_moy = etat.gain_c1_jour / n_arb
        sante = "✅" if ratio_c2c1 <= 3.0 else "⚠️"
        print(f"  ├─ Arbitrage C1/C2: {sante} C1={amp_c1:.3f} C2={amp_c2:.3f} "
              f"(ratio {ratio_c2c1:.2f}x) | accord {accord_pct:.1f}% | gain C1 ×{gain_moy:.2f}"
              + (f" | distill. {etat.agent.derniere_perte_distillation:.4f}"
                 f" (crédit {getattr(etat.agent, 'dernier_credit_distillation', 0.0):.1%}"
                 f", réf. choc {(etat.agent.reference_choc_dopamine or 0.0):.3f})"
                 if getattr(etat.agent, "derniere_perte_distillation", 0.0) else ""))
        # v41.14 — le témoin qui rend la ligne ci-dessus interprétable. Un accord de
        # 100 % avec une entropie C2 à 0.000 ne dit PAS que les deux voix délibèrent et
        # convergent : il dit que C2 répète toujours la même action.
        print(f"  │                   🗳️ entropie des votes — C1 {entropie_c1:.3f} | "
              f"C2 {entropie_c2:.3f} (0 = voix FIGÉE) | "
              f"actions distinctes : C1 {len(etat.votes_c1_jour)}, C2 {len(etat.votes_c2_jour)}")

    print(f"  └─ Erreur JEPA moy: {erreur_moyenne:.4f} | Réc. moyenne: {rec_moy:.3f} | "
          f"Thermostat: {etat_thermostat}")

    # v41.2 — LA DÉRIVE MÉTABOLIQUE, une fois par NUIT (jamais par tick : une norme qui
    # bougerait à chaque pas serait illisible et rendrait le diagnostic impossible, même
    # discipline que `MemoireEpisodiqueSpatiale.ajuster_capacite` en v31.0).
    #
    # La pression est ce que le monde a réellement imposé : la fraction de la journée
    # passée en basse énergie. Elle est DÉRIVÉE du vécu, jamais posée — un monde clément
    # ne fait dériver personne, un monde dur pousse le métabolisme à s'optimiser, et le
    # rappel élastique en exp() rend cette optimisation exponentiellement plus coûteuse à
    # mesure qu'elle s'éloigne de la norme d'espèce.
    etat.moteur_bio.reviser_derive_metabolique(
        etat.ticks_energie_basse_jour / max(ticks_du_jour, 1)
    )

    log_wandb = {
        "Jour": etat.jour,
        "Niveau": etat.niveau_actuel,
        "Erreur_JEPA": erreur_moyenne,
        "Perte_Consolidation": perte_jour,
        "Perte_Reves": perte_reves,
        "Nb_Reves": nb_reves,
        # ⚠️ v39.0 — PIÈGE DE LECTURE, conservé tel quel pour la continuité historique.
        # `Pourcentage_Reve` est une FRACTION (0,15 = 15 %), malgré son nom. Cette
        # ambiguïté a produit une vraie erreur de diagnostic, propagée dans deux
        # documents : la valeur 0,001 avait été lue « 0,1 % » et le rêve déclaré éteint,
        # alors qu'il rejouait 15-18 % de la journée et fonctionnait.
        #
        # La clé n'est PAS renommée : 190 runs historiques l'utilisent, et casser leur
        # comparabilité coûterait plus que l'ambiguïté. On ajoute la version explicite
        # à côté, et c'est elle qu'il faut lire désormais.
        "Pourcentage_Reve": pourcentage_reve,          # fraction [0,1] — nom trompeur
        "Reve_Fraction": pourcentage_reve,             # idem, nom honnête
        "Reve_Pourcentage_Reel": pourcentage_reve * 100.0,   # en %, lisible directement
        "Recompense_Moyenne": rec_moy,
        "Victoire": int(etat.victoire_aujourdhui),
        "Teneur_Dopamine": etat.teneur_dopamine,
        "Plasticite_Base": etat.plasticite_base,
        "Empreinte_Enfance": etat.empreinte_enfance,
        "Synapses_Mortes": synapses_mortes,
        "Taille_Thalamus": etat.agent.dim_bus,
        "Episodes_Jour": etat.episodes_jour,
        "Portes_Franchies_Jour": etat.portes_franchies_jour,
        "Progres_Personnel_Jour": etat.progres_personnel_jour,
        "Patience_Max_Episode": etat.patience_base_jour,
        "Abandons_Patience_Jour": etat.abandons_patience_jour,
        "Penalite_Stagnation": etat.penalite_stagnation_jour,
        # --- v34.0-etape0 : calibrage Fatigue/Mortalité/Soin (télémétrie pure) ---
        # Ces clés sont INCONDITIONNELLES : elles mesurent des grandeurs qui existent à
        # chaque tick de chaque niveau (effort, déficit, jauges). Contrairement aux blocs
        # Sens_*/C3, un zéro y est une information — « aucune ressource sur la carte » est
        # précisément le fait bloquant que l'Étape 0 doit établir (§7.4 du cadrage).
        "Calibrage_Effort_Min": etat.effort_min_jour or 0.0,
        "Calibrage_Effort_Max": etat.effort_max_jour,
        "Calibrage_Effort_Moyen": etat.effort_metabolique_jour / ticks_du_jour,
        "Calibrage_Deficit_Moyen": etat.deficit_cumul_jour / ticks_du_jour,
        "Calibrage_Deficit_Max": etat.deficit_max_jour,
        "Calibrage_Ticks_Critiques_Ratio": etat.ticks_deficit_critique_jour / ticks_du_jour,
        # LE critère de sevrage du futur soin parental (§3.3) : fraction de ticks où
        # l'agent tient ses 3 jauges au-dessus du seuil critique SANS aide extérieure.
        "Calibrage_Autonomie_Jauges": etat.ticks_jauges_saines_jour / ticks_du_jour,
        "Calibrage_Jauge_Min_Satiete": etat.jauge_min_satiete_jour,
        "Calibrage_Jauge_Min_Hydratation": etat.jauge_min_hydratation_jour,
        "Calibrage_Jauge_Min_Stimulation": etat.jauge_min_stimulation_jour,
        # Mesure BLOQUANTE (§7.4) : rendre l'agent mortel sur une carte sans ressource
        # serait le condamner d'office. Zéro ici ⇒ l'Étape 3 est interdite sur ce niveau.
        "Calibrage_Ressources_Cartes_Jour": etat.ressources_vues_jour,
        # v41.2 — le métabolisme à deux étages
        "Meta_Energie_Moy": etat.energie_cumul_jour / ticks_du_jour,
        "Meta_Energie_Min": etat.energie_min_jour,
        "Meta_Vigueur_Moy": etat.vigueur_cumul_jour / ticks_du_jour,
        "Meta_Vigueur_Min": etat.vigueur_min_jour,
        "Meta_Ticks_Energie_Basse_Ratio": etat.ticks_energie_basse_jour / ticks_du_jour,
        "Meta_Derive_Metabolique": etat.moteur_bio.derive_metabolique,
        "Meta_Derive_Kappa": etat.moteur_bio.derive_kappa,
        "Meta_Kappa_Effectif": etat.moteur_bio.kappa_effectif(),
        "Meta_Reserve": etat.moteur_bio.reserve,
        "Meta_Soulagement_Repas": etat.soulagement_repas_jour,
        # --- v35.0 : la promotion par taux de maîtrise ---
        # `Cursus_Taux_Maitrise_Niveau` est la métrique qui dira si la seconde voie de
        # promotion sert réellement, ou si tout passe encore par la série de victoires.
        # Publiée à -1.0 tant que la fenêtre n'est pas significative (< MIN_EPISODES) :
        # un 0.0 laisserait croire à un échec mesuré là où il n'y a pas encore de mesure.
        "Cursus_Niveau_Index": etat.niveau_actuel,
        "Cursus_Niveau_Total": len(PROGRAMME),
        "Cursus_Episodes_Fenetre": len(etat.historique_episodes_niveau),
        "Cursus_Taux_Maitrise_Niveau": (_taux_maitrise_niveau(etat)
                                         if _taux_maitrise_niveau(etat) is not None else -1.0),
        # v35.1 — le sevrage et le filet. `Cursus_Facteur_Guidage` est LA métrique qui
        # dira si l'aide s'estompe réellement quand l'agent progresse (< 1.0) et si le
        # filet se déclenche quand il bloque (> 1.0). Un 1.0 constant signifierait que ni
        # l'un ni l'autre ne mord — donc que la mécanique ne sert à rien.
        "Cursus_Facteur_Guidage": etat.facteur_guidage_jour,
        "Cursus_Jours_Stagnation": etat.jours_stagnation_niveau,
        # --- v41.4 : la maîtrise générale et l'héritage de sevrage ---
        # `Maitrise_Generale` est ce que l'agent sait faire TOUTES CARTES CONFONDUES ;
        # `Taux_Sevrage` est le mélange réellement utilisé pour doser l'aide. L'écart
        # entre `Taux_Sevrage` et `Cursus_Taux_Maitrise_Niveau` EST l'héritage : s'il
        # reste nul en permanence, la mécanique ne mord pas. `Parente_Niveau` dit
        # combien la dernière promotion a transféré (0 = rupture de vocabulaire).
        "Cursus_Maitrise_Generale": (_taux_maitrise_generale(etat)
                                      if _taux_maitrise_generale(etat) is not None
                                      else -1.0),
        "Cursus_Taux_Sevrage": getattr(etat, "taux_sevrage_jour", 0.0),
        "Cursus_Parente_Niveau": getattr(etat, "parente_niveau_precedent", 0.0),
        "Cursus_Episodes_General": len(getattr(etat, "historique_episodes_general", [])),
        # --- v41.6 (P17) : le cursus comme distribution ---
        # `Revisions` et `Incursions` disent si la queue gauche et la queue droite mordent
        # réellement. Deux zéros permanents signifieraient un pointeur déguisé.
        # `Poids_Defi` est la masse théorique du palier de référence : elle doit MONTER
        # quand la maîtrise monte (moins de révision), et c'est ce couplage qui distingue
        # une distribution dérivée de trois constantes en dur.
        "P17_Revisions": getattr(etat, "p17_revisions_jour", 0),
        "P17_Incursions": getattr(etat, "p17_incursions_jour", 0),
        "P17_Episodes_Hors_Reference": getattr(etat, "p17_episodes_hors_reference_jour", 0),
        "P17_Victoires_Hors_Reference": getattr(etat, "p17_victoires_hors_reference_jour", 0),
        "P17_Poids_Defi": next(
            (p for n_, p in zip(*_distribution_cursus(etat)) if n_ == etat.niveau_actuel),
            0.0),
        "P17_Niveau_Episode": getattr(etat, "niveau_episode", etat.niveau_actuel),
        # --- v36.0 : le flux enrichi & l'abstraction par récurrence ---
        # `Ecritures` mesure ce que la mémoire REÇOIT (2 types seulement avant v36.0).
        # `Rappels_Ratio` mesure ce qu'elle REND : si ce ratio reste à 0, le canal ne sert
        # à rien et les 2 dims ajoutées au vecteur bio sont mortes.
        # `Confirmations_Moy` est LA métrique de l'abstraction : > 1 signifie que la
        # récurrence se convertit en repères solides au lieu d'être jetée.
        "Memoire_Ecritures_Jour": etat.memoire_ecritures_jour,
        "Memoire_Rappels_Ratio": etat.memoire_rappels_marquants_jour / max(1, ticks_du_jour),
        "Memoire_Valence_Moyenne": (etat.memoire_valence_cumul_jour
                                     / max(1, etat.memoire_rappels_marquants_jour)),
        "Memoire_Confirmations_Moy": (
            sum(s.get('confirmations', 1) for s in etat.memoire_episodique_spatiale.souvenirs)
            / max(1, len(etat.memoire_episodique_spatiale.souvenirs))),
        "Memoire_Types_Distincts": len({s['type'] for s in
                                        etat.memoire_episodique_spatiale.souvenirs}),
        # Effort MOYEN de l'action `forward` vs celui des rotations. C'est la mesure du
        # RISQUE CRITIQUE identifié au §4 du cadrage : COUT_CORPOREL_PAR_ACTION facture
        # déjà `forward` (0.5) plus cher que tourner (0.2). Si la future fatigue se
        # branche naïvement dessus, elle RENFORCERA le biais anti-mouvement déjà mesuré
        # (forward joué 5,5 % du temps). Ce ratio doit être connu AVANT d'écrire l'Étape 1.
        "Calibrage_Effort_Avancer": (
            etat.effort_par_action_jour[2][1] / etat.effort_par_action_jour[2][0]
            if etat.effort_par_action_jour[2][0] else 0.0),
        "Calibrage_Effort_Tourner": (
            (etat.effort_par_action_jour[0][1] + etat.effort_par_action_jour[1][1])
            / max(1, etat.effort_par_action_jour[0][0] + etat.effort_par_action_jour[1][0])),
        "Calibrage_Part_Avancer": (
            etat.effort_par_action_jour[2][0] / ticks_du_jour),
        # v41.2-fix5 — LE GESTE DE MANGER, mesuré. Depuis que la consommation est un acte
        # volontaire, « l'agent apprend-il à manger ? » se décompose en deux questions que
        # seul ce couple de métriques sépare : joue-t-il le geste (`Part_Consommer`), et le
        # joue-t-il AU BON ENDROIT (`Efficacite_Consommer`) ? Un geste fréquent mais
        # inefficace signale une politique qui dépense sans se nourrir — indistinguable
        # d'un geste rare si l'on ne regarde que la récolte.
        "Calibrage_Part_Consommer": (
            etat.effort_par_action_jour[ACTION_CONSOMMER][0] / ticks_du_jour),
        "Calibrage_Efficacite_Consommer": (
            (etat.food_consommes_jour + etat.water_consommes_jour)
            / max(1, etat.effort_par_action_jour[ACTION_CONSOMMER][0])),
        "Sursauts_Volonte_Jour": etat.sursauts_jour,
        "Patience_Min_Actuelle": etat.module_acceptation.patience_min,
        # v41.30 — les grandeurs qui remplacent les trois constantes fossiles.
        "Endurance_Patience_De_Vie": etat.module_acceptation.patience_de_vie(),
        "Endurance_Capital": etat.module_acceptation.capital_endurance,
        "Endurance_Duree_Reussite": (etat.module_acceptation.duree_reussite_vie
                                     if etat.module_acceptation.duree_reussite_vie is not None else 0.0),
        "Endurance_Duree_Echec": (etat.module_acceptation.duree_echec_vie
                                  if etat.module_acceptation.duree_echec_vie is not None else 0.0),
        "Rythme_Episodes_Vecu": getattr(etat.moteur_bio, "rythme_episodes",
                                        EPISODES_PAR_JOURNEE_NAISSANCE),
        # v41.31 — les deux grandeurs des axes 1 et 2.
        "Gradient_Ticks_Credites": getattr(etat, "gradient_ticks_credites", 0),
        "Gradient_Ticks_Total": getattr(etat, "gradient_ticks_total", 0),
        # v41.48 — brique C. Clés CONDITIONNELLES : absentes si la mécanique dort,
        # plutôt que des zéros qui se liraient comme « mesuré à zéro » (règle v29.1).
        **({"Rendement_Mecanique_Moyen": getattr(etat, "rendement_moyen_journee", 0.0),
            "Rendement_Ticks_Nuls": getattr(etat, "rendement_ticks_nuls", 0)}
           if (RENDEMENT_MECANIQUE_ACTIF
               and getattr(etat, "rendement_moyen_journee", None) is not None) else {}),
        "Debit_Digestif_Jour": getattr(etat.moteur_bio, "debit_digestif", 0.0) * ticks_par_jour,
        "Rythme_Besoin_Par_Axe": besoin_par_axe(
            getattr(etat.moteur_bio, "rythme_episodes", EPISODES_PAR_JOURNEE_NAISSANCE)),
        "Bio_Satiete": etat.moteur_bio.satiete,
        "Bio_Hydratation": etat.moteur_bio.hydratation,
        "Bio_Stimulation": etat.moteur_bio.stimulation,
        "Bio_Deficit": etat.moteur_bio.calculer_deficit(),
        "Bio_R_Bio_Jour": etat.r_bio_jour,
        # v41.32-etape1 — la sonde de mixage n'entre PAS ici : ses clés sont ajoutées
        # plus bas de façon CONDITIONNELLE (une par terme réellement observé), pour ne
        # pas publier des zéros sur un jour sans tick. Voir le bloc `Mix_*`.
        "Bio_Food_Consommes_Jour": etat.food_consommes_jour,
        "Bio_Water_Consommes_Jour": etat.water_consommes_jour,
        "Bio_Quete_Active": etat.moteur_bio.quete_active["type"] if etat.moteur_bio.quete_active else "Aucune",
        "Bio_Effort_Metabolique_Moyen": effort_moyen_jour,
        "Memoire_Episodique_Taille": len(etat.memoire_episodique_spatiale.souvenirs),
        # v25.0 (Paradigme Bébé, expérimental) — neutres (plafond=PLAGE_REVE_MAX,
        # feedback=0) sur tout run n'utilisant pas cursus_bebe.py.
        "Plafond_Reve_Effectif": plage_reve_max_effective,
        "Feedback_Parent_Jour": getattr(etat, "feedback_parent_jour", 0),
    }
    # v27.0 — télémétrie vocale/dopamine unifiée, neutre (0) sur tout run 100% muet
    # (aucune leçon vocale active un seul tick de la journée).
    ticks_vocaux_jour = getattr(etat, "ticks_vocaux_jour", 0)
    if ticks_vocaux_jour > 0:
        log_wandb["Score_Vocal_Moyen_Jour"] = getattr(etat, "score_vocal_jour", 0.0) / ticks_vocaux_jour
        log_wandb["Score_Formants_Moyen_Jour"] = getattr(etat, "score_formants_jour", 0.0) / ticks_vocaux_jour
        log_wandb["Score_Spectral_Moyen_Jour"] = getattr(etat, "score_spectral_jour", 0.0) / ticks_vocaux_jour
        log_wandb["Palier_Vocal"] = etat.palier_vocal
    if ticks_du_jour > 0:
        log_wandb["Dopamine_Poids_Visuel_Moyen"] = getattr(etat, "dopamine_poids_visuel_jour", 0.0) / ticks_du_jour
        log_wandb["Dopamine_Poids_Vocal_Moyen"] = getattr(etat, "dopamine_poids_vocal_jour", 0.0) / ticks_du_jour
        log_wandb["Dopamine_Poids_C3_Moyen"] = getattr(etat, "dopamine_poids_c3_jour", 0.0) / ticks_du_jour
    # v28.0 (expérimental) — neutre (absent du log) tant qu'aucune ACTION_DEMANDER n'a
    # jamais été jouée ce jour (comportement par défaut sans plug branché).
    requetes_c3_jour = getattr(etat, "requetes_c3_jour", 0)
    if requetes_c3_jour > 0:
        log_wandb["Requetes_C3_Jour"] = requetes_c3_jour
        log_wandb["Reponses_C3_Jour"] = getattr(etat, "reponses_c3_jour", 0)
        log_wandb["Taux_Reponse_C3"] = getattr(etat, "reponses_c3_jour", 0) / requetes_c3_jour
    # v29.1 (expérimental) — LES 5 SENS. Absent du log si aucun tick sensoriel n'a été
    # vécu (mode "vocal_isole" pur, sans environnement MiniGrid), même logique que le
    # bloc C3 ci-dessus. `Sens_Bus_Actif` est la métrique de SANTÉ : elle passe à 0 si le
    # bus s'est désactivé en vol (API minigrid incompatible) — sans elle, la dégradation
    # gracieuse ne laisse qu'un unique avertissement console, invisible sur un run long.
    ticks_sensoriels_jour = getattr(etat, "ticks_sensoriels_jour", 0)
    if ticks_sensoriels_jour > 0:
        log_wandb["Sens_Bus_Actif"] = int(etat.bus_sensoriel.actif)
        log_wandb["Sens_Toucher_Contact_Ratio"] = etat.toucher_contact_jour / ticks_sensoriels_jour
        log_wandb["Sens_Toucher_Portage_Ratio"] = etat.toucher_portage_jour / ticks_sensoriels_jour
        log_wandb["Sens_Odorat_Moyen"] = etat.odorat_cumul_jour / ticks_sensoriels_jour
        log_wandb["Sens_Odorat_Max"] = etat.odorat_max_jour
        log_wandb["Sens_Odorat_Ticks_Actifs_Ratio"] = etat.odorat_ticks_actifs_jour / ticks_sensoriels_jour
        log_wandb["Sens_Gout_Ticks_Actifs"] = etat.gout_ticks_actifs_jour
        # v32.0 — CLINOTAXIE. `Sens_Odorat_Taux_Approche` est la métrique décisive : elle
        # ne dit pas si l'agent PERÇOIT le gradient (Sens_Odorat_Moyen le fait déjà) mais
        # s'il le SUIT. Lecture : ~50 % = l'agent monte et descend le gradient au hasard,
        # les 2 dims n'orientent rien et sont à remettre en cause ; nettement > 50 % =
        # la clinotaxie fait son travail. À lire sur plusieurs centaines de jours, une
        # fois integrateur_bio myélinisé — c'est un apprentissage, pas un câblage.
        ticks_variation = getattr(etat, "odorat_ticks_variation_jour", 0)
        if ticks_variation > 0:
            log_wandb["Sens_Odorat_Taux_Approche"] = etat.odorat_ticks_approche_jour / ticks_variation
            log_wandb["Sens_Odorat_Delta_Moyen"] = etat.odorat_delta_cumul_jour / ticks_variation
            log_wandb["Sens_Odorat_Ticks_Variation_Ratio"] = ticks_variation / ticks_sensoriels_jour
        # Ticks où une source existait sans être sentie : ce que la topologie v32.0 a
        # cessé de laisser traverser les murs. Une valeur qui s'effondre au fil d'un
        # épisode = l'agent a ouvert la porte et « débouché » l'odeur.
        log_wandb["Sens_Odorat_Ticks_Inodores_Ratio"] = (
            getattr(etat, "odorat_sources_inodores_jour", 0) / ticks_sensoriels_jour)
        # v30.0 — Exo-Sens : absent du log tant qu'aucun plug n'a été perçu (cas par
        # défaut), même logique conditionnelle que les blocs C3/Sens ci-dessus.
        if getattr(etat, "exo_ticks_actifs_jour", 0) > 0:
            log_wandb["Sens_Exo_Ticks_Actifs_Ratio"] = etat.exo_ticks_actifs_jour / ticks_sensoriels_jour
            log_wandb["Sens_Exo_Intensite_Moyenne"] = etat.exo_cumul_jour / ticks_sensoriels_jour
            log_wandb["Sens_Exo_Intensite_Max"] = etat.exo_max_jour
            log_wandb["Sens_Exo_Rafraichissements"] = etat.perceptions_exo_jour

    # --- v33.0-etape0.6 : CHRONOLOGIE DES VICTOIRES (hasard ou apprentissage ?) ---
    # Purement observationnel. Ces courbes doivent répondre à UNE question, celle qui
    # décide si la v33 attaque le bon problème : les victoires sont-elles un processus
    # STATIONNAIRE (l'agent gagne au hasard, à taux constant → il ne retient rien, le
    # Replay Orienté est justifié) ou CONVERGENT (les intervalles se resserrent → il
    # apprend déjà lentement, et c'est la vitesse qu'il faut traiter, pas la mémoire) ?
    log_wandb["Victoire_Jours_Depuis_Derniere"] = etat.jours_depuis_victoire
    log_wandb["Victoire_Total_Vie"] = etat.victoires_totales
    if etat.jour > 0:
        # Taux moyen sur toute la vie : le dénominateur d'une éventuelle accélération.
        log_wandb["Victoire_Taux_Vie"] = etat.victoires_totales / etat.jour
    # v33.0-etape0.6-fix1 : taille de la série COURANTE (remise à zéro au changement de
    # contexte). Sans elle, un `Victoire_Tendance_Ratio` isolé sur une courbe W&B ne dit
    # pas sur combien de points il repose ni s'il vient de repartir de zéro.
    log_wandb["Victoire_Serie_Contexte_N"] = len(etat.intervalles_victoires)
    if etat.intervalles_victoires:
        log_wandb["Victoire_Intervalle_Dernier"] = etat.intervalles_victoires[-1]
        log_wandb["Victoire_Intervalle_Moyen"] = (
            sum(etat.intervalles_victoires) / len(etat.intervalles_victoires))
        # LA MÉTRIQUE DÉCISIVE : moyenne de la seconde moitié des intervalles rapportée
        # à celle de la première. < 1.0 = les victoires se rapprochent (apprentissage) ;
        # ≈ 1.0 = stationnaire (hasard) ; > 1.0 = elles s'espacent (régression).
        # Exigée à partir de 4 intervalles : en dessous, une seule victoire chanceuse
        # ferait basculer le ratio du simple au double et le chiffre ne voudrait rien
        # dire — mieux vaut une clé absente qu'un ratio trompeur (règle v29.1).
        if len(etat.intervalles_victoires) >= 4:
            milieu = len(etat.intervalles_victoires) // 2
            debut = etat.intervalles_victoires[:milieu]
            fin = etat.intervalles_victoires[milieu:]
            moy_debut = sum(debut) / len(debut)
            if moy_debut > 0:
                log_wandb["Victoire_Tendance_Ratio"] = (sum(fin) / len(fin)) / moy_debut

    # --- v33.0-etape0 : CHRONOMÉTRIE DES JALONS DOORKEY ---
    # Purement observationnel. Ces courbes doivent trancher, AVANT d'écrire la moindre
    # ligne de la Mémoire Émotionnelle, où se situe réellement le goulot du Palier 7 :
    # le désert de récompense du dernier segment (Δt3), ou le conflit viscéral pendant
    # le transport de la clé (Δt2). Le diagnostic actuel est une déduction de lecture de
    # code, jamais une mesure — et la v31.1 a déjà montré qu'une intuition forte peut
    # être infirmée. Clés conditionnelles (absentes hors DoorKey) plutôt que des zéros
    # trompeurs, conformément à la règle posée en v29.1.
    episodes_doorkey = getattr(etat, "jalon_episodes_doorkey_jour", 0)
    if episodes_doorkey > 0:
        log_wandb["Jalon_Episodes_DoorKey"] = episodes_doorkey
        # v33.0-etape0.5 : sans cette clé, deux runs aux courbes opposées seraient
        # impossibles à distinguer a posteriori — c'est la variable indépendante de
        # l'expérience d'ablation, elle doit voyager avec ses résultats.
        log_wandb["Jalon_Quete_Auto_Ablation"] = int(_quete_auto_active(etat))
        # Les TAUX D'ATTEINTE sont aussi importants que les durées : un Δt3 rapide sur
        # n=1 épisode et un Δt3 rapide sur n=200 racontent l'inverse l'un de l'autre.
        log_wandb["Jalon_Taux_Atteinte_Cle"] = etat.jalon_delta1_n_jour / episodes_doorkey
        log_wandb["Jalon_Taux_Atteinte_Porte"] = etat.jalon_delta2_n_jour / episodes_doorkey
        log_wandb["Jalon_Taux_Atteinte_Sortie"] = etat.jalon_delta3_n_jour / episodes_doorkey
        if etat.jalon_delta1_n_jour > 0:
            log_wandb["Jalon_Delta1_Vers_Cle"] = etat.jalon_delta1_cumul_jour / etat.jalon_delta1_n_jour
        if etat.jalon_delta2_n_jour > 0:
            log_wandb["Jalon_Delta2_Cle_Vers_Porte"] = etat.jalon_delta2_cumul_jour / etat.jalon_delta2_n_jour
        if etat.jalon_delta3_n_jour > 0:
            log_wandb["Jalon_Delta3_Porte_Vers_Sortie"] = etat.jalon_delta3_cumul_jour / etat.jalon_delta3_n_jour
        # Le conflit viscéral, mesuré : combien de fois l'agent s'est arrêté manger
        # alors qu'il portait déjà la clé. Rapporté au nombre d'épisodes ayant atteint
        # la clé (jamais au total), sinon la métrique se diluerait dans les épisodes où
        # la question ne se pose pas.
        if etat.jalon_delta1_n_jour > 0:
            log_wandb["Jalon_Ressources_Post_Cle_Par_Episode"] = (
                etat.jalon_ressources_post_cle_jour / etat.jalon_delta1_n_jour)

    # --- v30.1 : mesures préalables au calibrage adaptatif (mémoire & sursaut) ---
    # Purement observationnel. Ces courbes doivent répondre à deux questions AVANT
    # d'écrire la moindre formule adaptative : (a) la saturation mémoire dégrade-t-elle
    # le rappel ? (b) le sursaut débouche-t-il assez souvent sur une victoire pour
    # mériter d'être renforcé plutôt qu'atténué ?
    nb_souv = len(etat.memoire_episodique_spatiale.souvenirs)
    cap_mem = etat.memoire_episodique_spatiale.capacite_max
    log_wandb["Memoire_Taux_Saturation"] = nb_souv / cap_mem if cap_mem else 0.0
    # v31.0 — la capacité n'est plus une constante : la logger permet de vérifier
    # qu'elle suit bien dim_bus et le déficit, et de relire a posteriori un taux de
    # saturation (dont le dénominateur bouge désormais d'une nuit à l'autre).
    log_wandb["Memoire_Capacite_Courante"] = cap_mem
    # v41.10 — LE VÉCU SPATIAL COMPLET. `Memoire_Taux_Saturation` ci-dessus ne porte que
    # sur la carte COURANTE : sous P17 il sous-estime le vécu d'un facteur égal au nombre
    # de cartes fréquentées. Ces trois clés sont ce qui permet de vérifier que le
    # correctif fait ce qu'on attend :
    #   - `Cartes_Souvenirs_Total` doit CROÎTRE bien au-delà de la capacité d'une carte ;
    #   - `Cartes_Connues` doit se stabiliser sur le nombre de niveaux fréquentés ;
    #   - `Cartes_Retrouvees` doit exploser (chaque unité = une redécouverte évitée).
    log_wandb["Cartes_Connues"] = len(etat.memoire_episodique_spatiale.archives_cartes) + 1
    log_wandb["Cartes_Souvenirs_Total"] = etat.memoire_episodique_spatiale.total_souvenirs()
    log_wandb["Cartes_Retrouvees"] = etat.memoire_episodique_spatiale.cartes_retrouvees
    # v41.11 — THERMOCEPTION. Clés CONDITIONNELLES (règle v29.1) : rien à logger sur une
    # carte sans danger. `Thermo_Taux_Approche` est la courbe à surveiller — elle doit
    # DÉCROÎTRE si l'agent apprend à fuir ; stable, le sens est perçu mais inexploité.
    if getattr(etat, "chaleur_ticks_actifs_jour", 0):
        log_wandb["Thermo_Ticks_Actifs"] = etat.chaleur_ticks_actifs_jour
        log_wandb["Thermo_Chaleur_Moyenne"] = etat.chaleur_cumul_jour / ticks_du_jour
        log_wandb["Thermo_Chaleur_Max"] = etat.chaleur_max_jour
        # v41.25 — la boucle nociceptive. `Thermo_Morts` est la métrique de survie de la
        # campagne ; `Thermo_Douleur_Active` distingue les deux bras dans W&B.
        _m = getattr(etat, "morts_jour", 0)
        _g = getattr(etat, "episodes_gagnes_jour", 0)
        log_wandb["Thermo_Morts"] = _m
        log_wandb["Thermo_Victoires"] = _g
        log_wandb["Thermo_Taux_Survie"] = _g / max(_m + _g, 1)
        log_wandb["Thermo_Chaleur_A_La_Mort"] = (
            getattr(etat, "chaleur_a_la_mort_jour", 0.0) / max(_m, 1))
        log_wandb["Thermo_Douleur_Active"] = int(DOULEUR_THERMIQUE_ACTIVE)
        # v41.26 — la gradation : douleur effective vs chaleur brute, et l'habituation.
        log_wandb["Thermo_Douleur_Moyenne"] = (
            getattr(etat, "douleur_cumul_jour", 0.0) / max(ticks_du_jour, 1))
        log_wandb["Thermo_Douleur_Max"] = getattr(etat, "douleur_max_jour", 0.0)
        log_wandb["Thermo_Ticks_Douloureux"] = getattr(etat, "douleur_ticks_actifs_jour", 0)
        log_wandb["Thermo_Habituation"] = etat.moteur_bio.chaleur_habituee
        log_wandb["Douleur_Corps_Moyenne"] = (
            getattr(etat, "douleur_corp_cumul_jour", 0.0) / max(ticks_du_jour, 1))
        log_wandb["Douleur_Corps_Max"] = getattr(etat, "douleur_corp_max_jour", 0.0)
        log_wandb["Douleur_Chocs_Muraux"] = getattr(etat, "chocs_muraux_jour", 0)
        log_wandb["Douleur_Ticks_Perdus_Mort"] = getattr(etat, "ticks_perdus_mort_jour", 0)
        _var = getattr(etat, "chaleur_ticks_variation_jour", 0)
        if _var:
            log_wandb["Thermo_Taux_Approche"] = etat.chaleur_ticks_approche_jour / _var
    # v41.12 — TOUCHER À DISTANCE. Inconditionnel : il y a toujours des murs.
    # `Toucher_Asymetrie_Ecart` est la clé de diagnostic — plate à 0, le capteur latéral
    # ne porte aucune information et le sens serait décoratif.
    # v41.13 — VENTILATION JEPA. Répond à « reste-t-il quelque chose à prédire ? » AVANT
    # d'ajouter des têtes par sens. `Amplitude_Cible` est le témoin décisif : une erreur
    # faible sur une cible plate ne prouve pas un bon modèle, elle prouve un monde
    # trivial (distinction ablation négative / ablation vide, règle de mesure §4).
    log_wandb["JEPA_Concentration"] = getattr(etat, "jepa_concentration_cumul_jour", 0.0) / ticks_du_jour
    log_wandb["JEPA_Amplitude_Cible"] = getattr(etat, "jepa_amplitude_cumul_jour", 0.0) / ticks_du_jour
    log_wandb["JEPA_Erreur_Max_Dim"] = getattr(etat, "jepa_err_max_dim_jour", 0.0)
    log_wandb["Toucher_Pression_Moyenne"] = getattr(etat, "pression_cumul_jour", 0.0) / ticks_du_jour
    log_wandb["Toucher_Pression_Max"] = getattr(etat, "pression_max_jour", 0.0)
    log_wandb["Toucher_Asymetrie_Ecart"] = getattr(etat, "asymetrie_ecart_cumul_jour", 0.0) / ticks_du_jour

    # v41.19 — sonde du coût moteur réel. Clés CONDITIONNELLES (rien de loggé si la sonde
    # n'a rien vu), et une clé par action plutôt qu'une moyenne : c'est précisément la
    # DISTRIBUTION par action qu'il faut pour dériver la formule de l'étape 2.
    _cm_w = getattr(etat, "cout_moteur_reel_jour", {}) or {}
    if _cm_w:
        _tot_w = sum(s["n"] for s in _cm_w.values()) or 1
        log_wandb["CoutMoteur_Sterile_Global"] = sum(s["sterile"] for s in _cm_w.values()) / _tot_w
        for _a, _s in _cm_w.items():
            _n = max(1, _s["n"])
            log_wandb[f"CoutMoteur_a{_a}_Part"] = _s["n"] / _tot_w
            log_wandb[f"CoutMoteur_a{_a}_Sterile"] = _s["sterile"] / _n
            log_wandb[f"CoutMoteur_a{_a}_Deplacement"] = _s["deplacement"] / _n
            log_wandb[f"CoutMoteur_a{_a}_Rotation"] = _s["rotation"] / _n
            log_wandb[f"CoutMoteur_a{_a}_Portage"] = _s["portage_change"] / _n
    # v39.0 — L'EMPREINTE DE TYPE. Clés CONDITIONNELLES (règle v29.1) : tant qu'aucune
    # expérience n'a été vécue, ne rien logger plutôt que des zéros trompeurs.
    #
    # Ce que ces courbes doivent montrer si le correctif fait ce qu'on attend :
    #   - `Empreinte_Types_Connus` CROÎT et ne retombe JAMAIS à 0 après une promotion
    #     (avant la v39, la mémoire entière était vidée à chaque palier) ;
    #   - `Empreinte_Valence_Max` se sépare de `Empreinte_Valence_Min` : l'agent
    #     distingue de mieux en mieux ce qui lui réussit de ce qui lui coûte, et cette
    #     distinction survit au changement de carte.
    _emp_w = getattr(etat.memoire_episodique_spatiale, 'empreinte_types', {}) or {}
    if _emp_w:
        _vals = [e['valence'] for e in _emp_w.values()]
        log_wandb["Empreinte_Types_Connus"] = len(_emp_w)
        log_wandb["Empreinte_Experiences_Cumul"] = sum(e['confirmations']
                                                        for e in _emp_w.values())
        log_wandb["Empreinte_Valence_Max"] = max(_vals)
        log_wandb["Empreinte_Valence_Min"] = min(_vals)
        log_wandb["Empreinte_Valence_Etendue"] = max(_vals) - min(_vals)

    # --- v41.32-etape4 : LA DISCRIMINATION en W&B ---
    # `Discrim_Distance` est la courbe décisive. Si elle reste plate près de 0 au fil des
    # jours, l'agent n'apprend jamais à distinguer une ressource d'un obstacle.
    _disc_w = _resumer_discrimination(etat)
    if _disc_w is not None:
        _dw, _nmw, _nrw, _pmw, _prw = _disc_w
        log_wandb["Discrim_Distance"] = _dw
        log_wandb["Discrim_Ticks_Mur"] = _nmw
        log_wandb["Discrim_Ticks_Ressource"] = _nrw
        log_wandb["Discrim_Consommer_Sur_Mur"] = _pmw[ACTION_CONSOMMER]
        log_wandb["Discrim_Consommer_Sur_Ressource"] = _prw[ACTION_CONSOMMER]

    # --- v41.32-etape2 : LE FOURRAGE en W&B ---
    # `Fourrage_Taux_Saisie` est la courbe décisive : sachant que l'agent est EN FACE
    # d'une ressource, tente-t-il de la prendre ? Si elle DÉCROÎT au fil des jours, le
    # gradient réprime activement le geste — c'est l'hypothèse à falsifier.
    # Clés conditionnelles (règle v29.1) : un détecteur inactif ne doit rien publier.
    _occ_w = getattr(etat, "fourrage_occasions_jour", 0)
    _tent_w = getattr(etat, "fourrage_tentatives_jour", 0)
    if _occ_w > 0 or _tent_w > 0:
        _sais_w = getattr(etat, "fourrage_saisies_jour", 0)
        log_wandb["Fourrage_Occasions"] = _occ_w
        log_wandb["Fourrage_Saisies"] = _sais_w
        log_wandb["Fourrage_Tentatives"] = _tent_w
        log_wandb["Fourrage_Tentatives_Vides"] = _tent_w - _sais_w
        if _occ_w > 0:
            log_wandb["Fourrage_Taux_Saisie"] = _sais_w / _occ_w
            log_wandb["Fourrage_Faim_Aux_Occasions"] = (
                getattr(etat, "fourrage_faim_aux_occasions", 0.0) / _occ_w)
        if _tent_w > 0:
            log_wandb["Fourrage_Efficacite_Geste"] = _sais_w / _tent_w

    # --- v41.32-etape1 : LA TABLE DE MIXAGE en W&B ---
    # Deux courbes par terme : `Mix_Moy_*` (ce qu'il pèse) et `Mix_Ecart_*` (ce qu'il
    # varie). C'est la SECONDE qui décide : un terme constant ne distingue aucune action
    # d'une autre, quelle que soit son amplitude.
    #
    # ⚠️ Clés CONDITIONNELLES (règle v29.1, blocs `Sens_*` et C3) : un terme jamais sondé
    # doit être ABSENT des courbes, pas à zéro. Publier un zéro ferait passer un canal
    # débranché pour un canal mesuré nul — exactement la confusion « ablation vide /
    # ablation négative » que la règle de mesure interdit, et le piège dans lequel le
    # projet est déjà tombé deux fois (v41.4, v41.7).
    #
    # Ce que ces courbes doivent montrer :
    #   - quel terme domine RÉELLEMENT la récompense, par sa dispersion ;
    #   - si `Mix_Ecart_Bio` est du même ordre que `Mix_Ecart_Env` — auquel cas la
    #     survie et le but parlent au gradient à voix comparable ;
    #   - si un terme a un écart-type quasi nul : il ne sert alors à rien, quelle que
    #     soit sa moyenne, et c'est un candidat au retrait plutôt qu'à la pondération.
    if getattr(etat, "mix_n", 0) > 0:
        log_wandb["Mix_Ticks"] = etat.mix_n
        _stats_w = _resumer_mixage(etat)
        for _nom, (_moy, _ec) in _stats_w.items():
            log_wandb[f"Mix_Moy_{_nom}"] = _moy
            log_wandb[f"Mix_Ecart_{_nom}"] = _ec
        # Part de dispersion : quelle fraction du signal total chaque terme porte.
        # C'est la lecture DIRECTE de la table de mixage — la seule qui réponde à
        # « le soulagement de l'eau est-il noyé sous le bruit de fond ? ».
        _somme_ec = sum(_ec for _nom, (_moy, _ec) in _stats_w.items() if _nom != "Total")
        if _somme_ec > 0:
            for _nom, (_moy, _ec) in _stats_w.items():
                if _nom != "Total":
                    log_wandb[f"Mix_PartSignal_{_nom}"] = _ec / _somme_ec
    log_wandb["Reve_Facteur_Richesse"] = facteur_richesse
    log_wandb["Reve_Empreinte_Enfance"] = etat.empreinte_enfance
    # v31.1 — santé de la mémoire spatiale : la déduplication travaille-t-elle, et la
    # capacité est-elle bridée par la taille du monde plutôt que par le cerveau ?
    log_wandb["Memoire_Doublons_Evites"] = etat.memoire_episodique_spatiale.doublons_evites
    log_wandb["Memoire_Cap_Densite_Actif"] = int(etat.memoire_episodique_spatiale.cap_densite_actif)
    if cases_grille:
        # Densité réellement occupée : nb de repères distincts rapporté aux cases de la
        # grille. Proche de 0 = mémoire éparse (normal) ; > 1 = plusieurs types
        # d'événements par case, ce qui reste sain tant que le cap n'est pas atteint.
        log_wandb["Memoire_Densite_Par_Case"] = nb_souv / cases_grille
    if etat.memoire_episodique_spatiale.souvenirs:
        # Âge (en ticks) du plus VIEUX souvenir encore conservé : sur une mémoire saturée,
        # c'est la profondeur temporelle réellement accessible à l'agent. S'il s'effondre
        # alors que la mémoire est pleine, la FIFO jette des souvenirs encore utiles.
        plus_vieux = min(s['tick'] for s in etat.memoire_episodique_spatiale.souvenirs)
        log_wandb["Memoire_Age_Plus_Vieux_Souvenir"] = etat.tick_absolu - plus_vieux
    rappels_tentes_jour = getattr(etat, "memoire_rappels_tentes_jour", 0)
    if rappels_tentes_jour > 0:
        reussis_jour = etat.memoire_rappels_reussis_jour
        log_wandb["Memoire_Taux_Rappel_Reussi"] = reussis_jour / rappels_tentes_jour
        if reussis_jour > 0:
            log_wandb["Memoire_Proximite_Moyenne"] = etat.memoire_distance_cumul_jour / reussis_jour
            log_wandb["Memoire_Fraicheur_Moyenne"] = etat.memoire_fraicheur_cumul_jour / reussis_jour
    total_sursauts_juges = (getattr(etat, "sursauts_suivis_victoire_jour", 0)
                            + getattr(etat, "sursauts_suivis_echec_jour", 0))
    if total_sursauts_juges > 0:
        log_wandb["Sursaut_Taux_Victoire"] = etat.sursauts_suivis_victoire_jour / total_sursauts_juges
        log_wandb["Sursaut_Victoires_Jour"] = etat.sursauts_suivis_victoire_jour
        log_wandb["Sursaut_Echecs_Jour"] = etat.sursauts_suivis_echec_jour

    # --- v37.0 : L'ÉQUILIBRE C1/C2 ---
    # Conditionnelles : un jour sans tick moteur (vocal pur) ne doit pas logger de zéros.
    # `Arbitrage_Ratio_C2C1` et `Arbitrage_Accord` sont les deux courbes qui valident (ou
    # invalident) le chantier — voir docs/ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md §6.
    if n_arb > 0:
        log_wandb["Arbitrage_Amplitude_C1"] = amp_c1
        log_wandb["Arbitrage_Amplitude_C2"] = amp_c2
        log_wandb["Arbitrage_Ratio_C2C1"] = ratio_c2c1
        log_wandb["Arbitrage_Accord"] = etat.accord_c1c2_jour / n_arb
        # v41.14 — SANS ces deux clés, `Arbitrage_Accord` est ininterprétable : un accord
        # de 100 % peut signifier « les deux voix délibèrent et convergent » OU « les deux
        # voix sont figées ». Une entropie C2 proche de 0 invalide toute lecture de
        # l'accord — c'est le témoin qui distingue une mesure d'un artefact.
        log_wandb["Arbitrage_Entropie_C1"] = entropie_c1
        log_wandb["Arbitrage_Entropie_C2"] = entropie_c2
        log_wandb["Arbitrage_Gain_C1"] = gain_moy
        log_wandb["Arbitrage_Ticks"] = n_arb
    if getattr(etat.agent, "derniere_perte_distillation", 0.0):
        log_wandb["Distillation_C2_vers_C1"] = etat.agent.derniere_perte_distillation
        # v37.1 — les deux courbes qui disent si la sélectivité fonctionne.
        # `Credit_Moyen` : quelle part de la journée a mérité d'être automatisée (une
        # journée stérile doit tendre vers 0). `Reference_Choc` : le niveau, propre à cet
        # agent, au-dessus duquel un événement lui paraît marquant — il doit MONTER avec
        # la maturation, ce qui rend l'agent progressivement plus difficile à impressionner.
        log_wandb["Distillation_Credit_Moyen"] = getattr(
            etat.agent, "dernier_credit_distillation", 0.0)
        if etat.agent.reference_choc_dopamine:
            log_wandb["Distillation_Reference_Choc"] = etat.agent.reference_choc_dopamine

    # v40.1-fix4 — la curiosité est désormais continue (pondérée par l'acceptation), donc
    # toujours active : sa clé est loggée sans condition, un 0 y est une vraie mesure.
    log_wandb["Sous_Objectifs_Curiosite_Jour"] = etat.sous_objectifs_curiosite_jour
    # v40.0 — la planification émergente est GLOBALE : ses trois métriques sortent du bloc
    # DoorKey. `Force_Planification` y était enfermée du temps où elle valait 0.5 ou 0.85
    # selon le palier ; elle dépend maintenant du vécu, donc elle vit sur tous les niveaux.
    # Les deux réservoirs sont loggés séparément : c'est leur RAPPORT qui pilote, mais leur
    # évolution respective est ce qui dira si le cliquet fait son travail.
    log_wandb["Force_Planification"] = etat.force_planification_jour
    log_wandb["Planif_Vecu_Okay"] = etat.agent.vecu_okay
    log_wandb["Planif_Vecu_Danger"] = etat.agent.vecu_danger
    # v40.1 — les six courbes de l'envie de vivre. `Envie_Vivre` est celle qui dit si un
    # run est mort ; `Envie_Lucidite` et `Envie_Foi` disent laquelle des deux forces l'a
    # emporté, et leurs deux facteurs séparément (a-t-il compris ? a-t-il construit ?).
    _me = getattr(etat.agent, "mesure_envie", None) or {}
    if _me:
        log_wandb["Envie_Vivre"] = _me.get("envie")
        log_wandb["Envie_Lucidite"] = _me.get("lucidite")
        log_wandb["Envie_Foi"] = _me.get("foi")
        log_wandb["Envie_Comprehension_C2"] = _me.get("comprehension_c2")
        log_wandb["Envie_Experience_C1"] = _me.get("experience_c1")
        log_wandb["Envie_Acceptation"] = _me.get("acceptation")
    if etat.doorkey_actif and etat.detecteur.actif:
        log_wandb["Palier_Cible"] = etat.palier_cible
        log_wandb["Guidage_But"] = etat.guidage_but_journee
        log_wandb["Mode_Libre"] = int(etat.mode_libre)
        log_wandb["Coeff_Entropie"] = etat.coeff_entropie_jour
        log_wandb["Sous_Seuil_Abnegation"] = etat.gestionnaire_cursus.sous_seuil_actuel
        log_wandb["Succes_Sous_Seuil_Courant"] = etat.gestionnaire_cursus.succes_sous_seuil_courant
        log_wandb["Facteur_Complexite"] = etat.facteur_complexite_jour
        if taux_maitrise is not None:
            log_wandb["Taux_Maitrise_Palier"] = taux_maitrise

    return log_wandb


if __name__ == "__main__":
    # v40.2 — CLI minimal. Jusqu'ici le mode standalone n'acceptait AUCUN argument : les
    # flags passés en ligne de commande (`--jours`, `--brain`, `--graine`) étaient ignorés
    # SILENCIEUSEMENT, et la graine était figée à 42 en tête de fichier. Conséquence
    # mesurée le 14/08 : trois runs lancés avec trois graines différentes étaient en
    # réalité STRICTEMENT IDENTIQUES, et tournaient tous vers `jours_totaux` (500) quel que
    # soit le `--jours` demandé. Toute campagne multi-graines lancée ainsi était nulle.
    import argparse
    import os
    import random as _random
    from naulthene.cerveau.persistance import PersistanceAnatomique

    _p = argparse.ArgumentParser(description="Naulthène — terrain d'essai local")
    _p.add_argument("--jours", type=int, default=jours_totaux,
                    help=f"nombre de journées à simuler (défaut : {jours_totaux})")
    _p.add_argument("--graine", type=int, default=42,
                    help="graine aléatoire — DOIT différer entre runs d'une même campagne")
    _p.add_argument("--brain", type=str, default=None,
                    help="chemin du .brain (repris s'il existe, créé sinon)")
    _p.add_argument("--no-wandb", action="store_true", help="désactive Weights & Biases")
    # v41.4 — interrupteur d'ABLATION du seul héritage de sevrage. Il existe pour que la
    # campagne dispose d'un témoin à graine IDENTIQUE : comparer 10 graines v41.4 à 10
    # graines d'un run antérieur ne prouverait rien, les trajectoires natales différant
    # (leçon de la loterie natale g22, campagne v41). Avec ce flag, `facteur_guidage`
    # retombe exactement sur le comportement v41.3.
    _p.add_argument("--sans-heritage", action="store_true",
                    help="ABLATION : coupe l'héritage de sevrage v41.4 (témoin v41.3)")
    # v41.10 — ABLATION de la mémoire par carte. Avec ce flag, la bascule redevient un
    # EFFACEMENT (comportement v41.9) : c'est le témoin exact du correctif, sur les mêmes
    # graines et donc les mêmes mondes (v41.9).
    _p.add_argument("--sans-memoire-cartes", action="store_true",
                    help="ABLATION : la bascule de carte efface la mémoire (témoin v41.9)")
    # v41.13 — ABLATION du corps dans le rollout de C2. C'est LE témoin de l'hypothèse
    # « C2 est inerte parce qu'il simule un monde sans corps ».
    _p.add_argument("--sans-corps-rollout", action="store_true",
                    help="ABLATION : C2 simule sans reprojeter le vecteur bio (témoin v41.12)")
    # v41.16 — ABLATION du brain-sparing : la vigueur réécrase les logits (témoin v41.15).
    _p.add_argument("--vigueur-sur-logits", action="store_true",
                    help="ABLATION : la vigueur multiplie les logits (témoin v41.15)")
    # v41.17 — second axe du plan factoriel (voir ECONOMIE_ACTION_ACTIVE).
    _p.add_argument("--sans-economie-action", action="store_true",
                    help="ABLATION : le coût d'action ne suit plus la vigueur (témoin v41.15)")
    # v41.18 — instrument de falsification du verrou P17 (voir DEFI_FORCE).
    _p.add_argument("--defi-force", action="store_true",
                    help="MESURE : 100 %% du palier de référence, court-circuite P17")
    # v41.20 — témoin du coût moteur physique (voir COUT_MOTEUR_PHYSIQUE).
    _p.add_argument("--cout-moteur-table", action="store_true",
                    help="ABLATION : revient à COUT_CORPOREL_PAR_ACTION, les 7 valeurs en dur")
    # v41.22 — témoin du plafond de bus indexé machine (voir _plafond_bus_machine).
    _p.add_argument("--plafond-bus-fixe", action="store_true",
                    help="ABLATION : fige DIM_BUS_MAX à 96, l'ancienne valeur posée")
    # v41.25 — témoin de la nociception thermique (voir DOULEUR_THERMIQUE_ACTIVE).
    # v41.28 — témoin du travail tenté, voir TRAVAIL_TENTE_ACTIF.
    # v41.31 — témoins des trois axes, séparés.
    _p.add_argument("--gain-acteur", type=float, default=1.0,
                    help="bras de contrôle v41.31 : multiplie le gradient de l'acteur "
                         "SANS filtrer (2.6 = l'effet du dénominateur réduit)")
    # v41.48 — brique C. DEUX drapeaux SÉPARÉS : le premier coupe la pondération, le
    # second casse son ASYMÉTRIE. Les couper ensemble donnerait une ablation confondue.
    _p.add_argument("--sans-rendement", action="store_true",
                    help="v41.48 : coupe la pondération du gradient par le rendement "
                         "mécanique (témoin — restitue le comportement v41.47)")
    _p.add_argument("--rendement-symetrique", action="store_true",
                    help="v41.48 : pondère AUSSI les avantages négatifs — le geste "
                         "stérile devient invisible au lieu d'être puni (témoin de "
                         "falsification de l'asymétrie)")
    _p.add_argument("--gradient-non-filtre", action="store_true",
                    help="témoin v41.30 : l'acteur apprend aussi sur les gestes stériles")
    _p.add_argument("--debit-fossile", action="store_true",
                    help="témoin v41.2 : débit digestif figé à 3,0 estomacs/jour")
    _p.add_argument("--detecteur-observation", action="store_true",
                    help="témoin pré-v41.31 : `mur_touche` lit l'observation, pas la physique")
    # v41.30 — témoins des deux constantes supprimées, séparés.
    _p.add_argument("--patience-fossile", action="store_true",
                    help="témoin v41.29 : patience à gain constant (+10) plafonnée à 350")
    _p.add_argument("--rythme-fossile", action="store_true",
                    help="témoin v41.29 : besoin métabolique figé à 4,0 épisodes/jour")
    _p.add_argument("--travail-reussi", action="store_true",
                    help="ABLATION : un geste stérile ne coûte rien (barème v41.27)")
    # v41.43 — témoin de l'échelle de stagnation dérivée (P3 de l'audit du génome).
    _p.add_argument("--stagnation-fossile", action="store_true",
                    help="témoin v41.42 : pénalité de stagnation figée à 0,015 (posée)")
    # v41.44 — témoins de la cristallisation, voir P6 de l'audit du génome.
    _p.add_argument("--cristallisation-fossile", action="store_true",
                    help="témoin v26.0 : SEUIL_CRISTAL absolu à 0,80 (jamais franchi)")
    _p.add_argument("--sans-cristallisation", action="store_true",
                    help="ABLATION : aucune synapse ne cristallise jamais")
    # v41.27 — témoin de l'option (b), voir MORT_COUTE_LA_JOURNEE.
    _p.add_argument("--mort-sans-cout", action="store_true",
                    help="ABLATION : mourir ne coûte plus la journée (comportement < v41.27)")
    _p.add_argument("--detach-c2", action="store_true",
                    help="C2 lit le corps sans le sculpter : il apprend toujours, mais ne "
                         "rétropropage plus dans integrateur_bio (correctif candidat de la "
                         "collision C1/C2)")
    _p.add_argument("--sans-gradient-c2", action="store_true",
                    help="ABLATION : C2 garde son forward mais ne rétropropage plus "
                         "(teste la collision C1/C2 dans integrateur_bio). Mesure "
                         "l'ALIGNEMENT du gradient, jamais la performance.")
    _p.add_argument("--soif-figee", action="store_true",
                    help="ABLATION piste C : l'hydratation reste à 1.0 (le corps ne tire "
                         "plus que sur UN axe). Mesure l'alignement du gradient, JAMAIS "
                         "la performance.")
    _p.add_argument("--sans-douleur", action="store_true",
                    help="ABLATION : la chaleur reste perçue mais ne coûte rien (témoin v41.24)")
    _p.add_argument("--tronc-connecte", action="store_true",
                    help="ABLATION v41.34 : retire le .detach() du tronc perceptif — "
                         "l'acteur et le critique rétropropagent jusqu'à porte_visuelle")
    _p.add_argument("--sans-portage", action="store_true",
                    help="ABLATION v41.33 : le bit de portage reste dans le vecteur bio "
                         "mais toujours à 0.0 (témoin — la DIMENSION est conservée, seule "
                         "l'INFORMATION est coupée, ce qui isole le signal de la largeur)")
    # v41.25 — banc de mesure. Le cursus est bloqué au niveau 4, or les niveaux 1-4 ne
    # contiennent AUCUNE lave : mesurer la douleur thermique sur le cursus normal
    # reviendrait à mesurer un terme nul dans 99,7 % des ticks (mesuré : chaleur moyenne
    # 0,001, 1 tick sur 400). Ce flag force l'environnement où le signal existe.
    _p.add_argument("--env-force", type=str, default=None,
                    help="MESURE : force un env_id MiniGrid unique (ex. MiniGrid-LavaGapS6-v0)")
    _args = _p.parse_args()

    # Drapeau global lu par `facteur_guidage` — un seul point de lecture, pas de
    # branchement dispersé dans le chemin cognitif.
    #
    # ⚠️ v41.4-fix1 — ÉCRIRE DANS LE MODULE NOMMÉ, JAMAIS DANS `globals()`.
    # `python -m naulthene.cerveau.noyau` charge ce fichier DEUX FOIS, sous deux noms :
    # `__main__` (ce bloc) et `naulthene.cerveau.noyau` (celui que voient les fonctions
    # définies plus haut, et que les autres modules importent). `globals()` ici désigne
    # `__main__` — donc l'affectation n'était **jamais vue par `facteur_guidage`**, et
    # l'ablation ne coupait rien.
    #
    # Mesuré : sur 135 jours, le témoin et la variante ont produit des logs
    # **rigoureusement identiques** (maturité 0,361 des deux côtés, héritage +5 pt affiché
    # alors même que le message « ABLATION » était imprimé). C'est la deuxième occurrence
    # du défaut que ce bloc dénonce quelques lignes plus haut : des runs qu'on croit
    # différents et qui sont le même run. Un témoin qui ne diffère pas ne mesure rien.
    import sys as _sys
    _module_reel = _sys.modules.get("naulthene.cerveau.noyau")
    _actif = not _args.sans_heritage
    globals()["HERITAGE_SEVRAGE_ACTIF"] = _actif
    if _module_reel is not None:
        _module_reel.HERITAGE_SEVRAGE_ACTIF = _actif
    if not _actif:
        print("🔬 [ABLATION] héritage de sevrage v41.4 COUPÉ — témoin v41.3")
        # Vérification à l'exécution : sans elle, une ablation muette produirait une
        # campagne entière de résultats faux (c'est ce qui vient d'arriver).
        from naulthene.cerveau.noyau import HERITAGE_SEVRAGE_ACTIF as _verif
        assert _verif is False, ("l'ablation n'a pas atteint le module lu par "
                                 "facteur_guidage — campagne invalide")

    # v41.10 — même discipline exactement : écriture dans le module NOMMÉ + assertion.
    _mem_actif = not _args.sans_memoire_cartes
    globals()["MEMOIRE_PAR_CARTE_ACTIVE"] = _mem_actif
    if _module_reel is not None:
        _module_reel.MEMOIRE_PAR_CARTE_ACTIVE = _mem_actif
    if not _mem_actif:
        print("🔬 [ABLATION] mémoire par carte v41.10 COUPÉE — la bascule efface (témoin v41.9)")
        from naulthene.cerveau.noyau import MEMOIRE_PAR_CARTE_ACTIVE as _verif_mem
        assert _verif_mem is False, ("l'ablation n'a pas atteint le module — campagne invalide")

    if _args.env_force:
        globals()["ENV_FORCE"] = _args.env_force
        if _module_reel is not None:
            _module_reel.ENV_FORCE = _args.env_force
        print(f"🔬 [BANC] environnement forcé sur {_args.env_force} — cursus court-circuité")
        from naulthene.cerveau.noyau import ENV_FORCE as _verif_env
        assert _verif_env == _args.env_force, "le forçage n'a pas atteint le module"

    # v41.48 — même discipline : écriture dans le module NOMMÉ + assertion runtime.
    _rend = not _args.sans_rendement
    globals()["RENDEMENT_MECANIQUE_ACTIF"] = _rend
    if _module_reel is not None:
        _module_reel.RENDEMENT_MECANIQUE_ACTIF = _rend
    if not _rend:
        print("🔬 [ABLATION] rendement mécanique v41.48 COUPÉ — gradient non pondéré")
        from naulthene.cerveau.noyau import RENDEMENT_MECANIQUE_ACTIF as _v_rend
        assert _v_rend is False, ("l'ablation n'a pas atteint le module — campagne invalide")

    _rsym = bool(_args.rendement_symetrique)
    globals()["RENDEMENT_SYMETRIQUE_TEMOIN"] = _rsym
    if _module_reel is not None:
        _module_reel.RENDEMENT_SYMETRIQUE_TEMOIN = _rsym
    if _rsym:
        print("🔬 [TÉMOIN] rendement SYMÉTRIQUE — le geste stérile devient invisible")
        from naulthene.cerveau.noyau import RENDEMENT_SYMETRIQUE_TEMOIN as _v_sym
        assert _v_sym is True, ("le témoin n'a pas atteint le module — campagne invalide")

    # v41.28 — même discipline : écriture dans le module NOMMÉ + assertion runtime.
    _trav = not _args.travail_reussi
    globals()["TRAVAIL_TENTE_ACTIF"] = _trav
    if _module_reel is not None:
        _module_reel.TRAVAIL_TENTE_ACTIF = _trav
    if not _trav:
        print("🔬 [ABLATION] travail tenté v41.28 COUPÉ — geste stérile gratuit (v41.27)")
        from naulthene.cerveau.noyau import TRAVAIL_TENTE_ACTIF as _vt
        assert _vt is False, "l'ablation n'a pas atteint le module — campagne invalide"

    # v41.43 — témoin de l'échelle de stagnation dérivée. Même discipline : écriture
    # dans le module NOMMÉ puis assertion runtime, faute de quoi les deux bras seraient
    # identiques sans que rien ne le signale (bug v41.4, trois bras confondus).
    _stag = not _args.stagnation_fossile
    globals()["STAGNATION_DERIVEE_ACTIVE"] = _stag
    if _module_reel is not None:
        _module_reel.STAGNATION_DERIVEE_ACTIVE = _stag
    if not _stag:
        print("🔬 [TÉMOIN] stagnation FOSSILE — pénalité figée à "
              f"{PENALITE_STAGNATION_FOSSILE} (posée, d'avant la v41.43)")
        from naulthene.cerveau.noyau import STAGNATION_DERIVEE_ACTIVE as _vs
        assert _vs is False, "le témoin n'a pas atteint le module — campagne invalide"

    # v41.44 — mêmes deux disciplines : module NOMMÉ + assertion runtime.
    _cris_rel = not _args.cristallisation_fossile
    globals()["CRISTALLISATION_RELATIVE_ACTIVE"] = _cris_rel
    if _module_reel is not None:
        _module_reel.CRISTALLISATION_RELATIVE_ACTIVE = _cris_rel
    if not _cris_rel:
        print(f"🔬 [TÉMOIN] cristallisation FOSSILE — seuil absolu {SEUIL_CRISTAL_FOSSILE} "
              "(mesuré : 0 synapse sur 1 906 360 le franchit)")
        from naulthene.cerveau.noyau import CRISTALLISATION_RELATIVE_ACTIVE as _vcr
        assert _vcr is False, "le témoin n'a pas atteint le module — campagne invalide"

    _cris = not _args.sans_cristallisation
    globals()["CRISTALLISATION_ACTIVE"] = _cris
    if _module_reel is not None:
        _module_reel.CRISTALLISATION_ACTIVE = _cris
    if not _cris:
        print("🔬 [ABLATION] cristallisation COUPÉE — aucune synapse ne se fige")
        from naulthene.cerveau.noyau import CRISTALLISATION_ACTIVE as _vc
        assert _vc is False, "l'ablation n'a pas atteint le module — campagne invalide"

    if _args.gain_acteur != 1.0:
        globals()["GAIN_ACTEUR_CONTROLE"] = float(_args.gain_acteur)
        if _module_reel is not None:
            _module_reel.GAIN_ACTEUR_CONTROLE = float(_args.gain_acteur)
        print(f"🔬 [CONTRÔLE] gradient acteur ×{_args.gain_acteur} SANS filtrage")
        import naulthene.cerveau.noyau as _mg
        assert _mg.GAIN_ACTEUR_CONTROLE == float(_args.gain_acteur), \
            "le contrôle n'a pas atteint le module — campagne invalide"

    # v41.31 — un drapeau PAR axe, même discipline : module NOMMÉ + assertion runtime.
    for _flag, _arg, _msg in (
        ("GRADIENT_CAUSAL_ACTIF", _args.gradient_non_filtre,
         "gradient causal COUPÉ — l'acteur réapprend sur les gestes stériles"),
        ("DEBIT_DIGESTIF_VECU_ACTIF", _args.debit_fossile,
         "débit digestif FIGÉ à 3,0/jour (régime v41.2)"),
        ("UNIFIER_DETECTEUR_STERILITE", _args.detecteur_observation,
         "détecteur de stérilité sur l'OBSERVATION (régime pré-v41.31)"),
    ):
        _val = not _arg
        globals()[_flag] = _val
        if _module_reel is not None:
            setattr(_module_reel, _flag, _val)
        if not _val:
            print(f"🔬 [ABLATION] {_msg}")
            import naulthene.cerveau.noyau as _m
            assert getattr(_m, _flag) is False, (
                f"l'ablation {_flag} n'a pas atteint le module — campagne invalide")

    # v41.30 — un drapeau PAR constante (jamais groupés : ablation confondue sinon).
    _endur = not _args.patience_fossile
    globals()["ENDURANCE_DERIVEE_ACTIVE"] = _endur
    if _module_reel is not None:
        _module_reel.ENDURANCE_DERIVEE_ACTIVE = _endur
    if not _endur:
        print("🔬 [ABLATION] endurance dérivée COUPÉE — patience fossile (+10, plafond 350)")
        from naulthene.cerveau.noyau import ENDURANCE_DERIVEE_ACTIVE as _ve
        assert _ve is False, "l'ablation n'a pas atteint le module — campagne invalide"

    _rythme_actif = not _args.rythme_fossile
    globals()["RYTHME_VECU_ACTIF"] = _rythme_actif
    if _module_reel is not None:
        _module_reel.RYTHME_VECU_ACTIF = _rythme_actif
    if not _rythme_actif:
        print("🔬 [ABLATION] rythme vécu COUPÉ — besoin figé à 4,0 épisodes/jour")
        from naulthene.cerveau.noyau import RYTHME_VECU_ACTIF as _vr
        assert _vr is False, "l'ablation n'a pas atteint le module — campagne invalide"

    # v41.27 — même discipline : écriture dans le module NOMMÉ + assertion runtime.
    _mort_cout = not _args.mort_sans_cout
    globals()["MORT_COUTE_LA_JOURNEE"] = _mort_cout
    if _module_reel is not None:
        _module_reel.MORT_COUTE_LA_JOURNEE = _mort_cout
    if not _mort_cout:
        print("🔬 [ABLATION] option (b) COUPÉE — mourir ne coûte plus la journée")
        from naulthene.cerveau.noyau import MORT_COUTE_LA_JOURNEE as _v
        assert _v is False, "l'ablation n'a pas atteint le module — campagne invalide"

    # v41.32 — detach asymétrique. MÊME DISCIPLINE : module NOMMÉ + assertion runtime.
    _det_c2 = bool(_args.detach_c2)
    globals()["DETACH_C2_ASYMETRIQUE"] = _det_c2
    if _module_reel is not None:
        _module_reel.DETACH_C2_ASYMETRIQUE = _det_c2
    if _det_c2:
        print("🔬 [VARIANTE] detach asymétrique — C2 lit le corps sans le sculpter")
        from naulthene.cerveau.noyau import DETACH_C2_ASYMETRIQUE as _verif_det
        assert _verif_det is True, ("le drapeau n'a pas atteint le module — campagne invalide")

    # v41.32 — collision C1/C2. MÊME DISCIPLINE : module NOMMÉ + assertion runtime.
    _grad_c2 = not _args.sans_gradient_c2
    globals()["GRADIENT_C2_ACTIF"] = _grad_c2
    if _module_reel is not None:
        _module_reel.GRADIENT_C2_ACTIF = _grad_c2
    if not _grad_c2:
        print("🔬 [ABLATION] gradient de C2 COUPÉ — forward intact, plus de "
              "rétropropagation vers integrateur_bio")
        from naulthene.cerveau.noyau import GRADIENT_C2_ACTIF as _verif_c2
        assert _verif_c2 is False, ("l'ablation n'a pas atteint le module — campagne invalide")

    # v41.32 — piste C. MÊME DISCIPLINE : écriture dans le module NOMMÉ + assertion
    # runtime. C'est le correctif du bug v41.4, où le drapeau n'atteignait pas le module
    # et où les trois bras de la campagne étaient en réalité identiques — un résultat
    # « trop propre » qui a coûté un cycle entier.
    _soif_figee = bool(_args.soif_figee)
    globals()["SOIF_FIGEE"] = _soif_figee
    if _module_reel is not None:
        _module_reel.SOIF_FIGEE = _soif_figee
    if _soif_figee:
        print("🔬 [ABLATION] axe hydrique GELÉ (piste C) — hydratation forcée à 1.0, "
              "le corps ne tire plus que sur la faim")
        from naulthene.cerveau.noyau import SOIF_FIGEE as _verif_soif
        assert _verif_soif is True, ("l'ablation n'a pas atteint le module — campagne invalide")

    # v41.25 — même discipline : écriture dans le module NOMMÉ + assertion runtime.
    _douleur_active = not _args.sans_douleur
    globals()["DOULEUR_THERMIQUE_ACTIVE"] = _douleur_active
    if _module_reel is not None:
        _module_reel.DOULEUR_THERMIQUE_ACTIVE = _douleur_active
    if not _douleur_active:
        print("🔬 [ABLATION] nociception thermique v41.25 COUPÉE — chaleur perçue mais indolore")
        from naulthene.cerveau.noyau import DOULEUR_THERMIQUE_ACTIVE as _verif_dlr
        assert _verif_dlr is False, ("l'ablation n'a pas atteint le module — campagne invalide")

    # v41.33 — même discipline : écriture dans le module NOMMÉ + assertion runtime.
    #
    # ⚠️ LE TÉMOIN GARDE LA DIMENSION ET NE COUPE QUE L'INFORMATION (règle de mesure §6.3).
    # Retirer la 42ᵉ colonne changerait la LARGEUR d'`integrateur_bio` : on mesurerait
    # « un réseau plus large contre un réseau plus étroit », pas « avec ou sans
    # proprioception ». Ici les deux bras ont exactement la même architecture.
    _portage_actif = not _args.sans_portage
    globals()["PORTAGE_PERCU_ACTIF"] = _portage_actif
    if _module_reel is not None:
        _module_reel.PORTAGE_PERCU_ACTIF = _portage_actif
    if not _portage_actif:
        print("🔬 [ABLATION] bit de portage v41.33 COUPÉ — la dim reste, l'info est à 0.0")
        from naulthene.cerveau.noyau import PORTAGE_PERCU_ACTIF as _verif_port
        assert _verif_port is False, ("l'ablation n'a pas atteint le module — campagne invalide")

    # v41.34 — même discipline : écriture dans le module NOMMÉ + assertion runtime.
    _tronc_detache = not _args.tronc_connecte
    globals()["TRONC_PERCEPTIF_DETACHE"] = _tronc_detache
    if _module_reel is not None:
        _module_reel.TRONC_PERCEPTIF_DETACHE = _tronc_detache
    if not _tronc_detache:
        print("🔬 [VARIANTE] tronc perceptif CONNECTÉ — l'acteur et le critique "
              "sculptent la vue")
        from naulthene.cerveau.noyau import TRONC_PERCEPTIF_DETACHE as _verif_tronc
        assert _verif_tronc is False, ("la variante n'a pas atteint le module — campagne invalide")

    # v41.13 — même discipline : écriture dans le module NOMMÉ + assertion runtime.
    _corps_actif = not _args.sans_corps_rollout
    globals()["CORPS_DANS_ROLLOUT_ACTIF"] = _corps_actif
    if _module_reel is not None:
        _module_reel.CORPS_DANS_ROLLOUT_ACTIF = _corps_actif
    if not _corps_actif:
        print("🔬 [ABLATION] corps dans le rollout v41.13 COUPÉ — C2 simule sans corps (témoin v41.12)")
        from naulthene.cerveau.noyau import CORPS_DANS_ROLLOUT_ACTIF as _verif_corps
        assert _verif_corps is False, ("l'ablation n'a pas atteint le module — campagne invalide")

    # v41.16 — même discipline : module NOMMÉ + assertion runtime.
    _bs = not _args.vigueur_sur_logits
    globals()["BRAIN_SPARING_ACTIF"] = _bs
    if _module_reel is not None:
        _module_reel.BRAIN_SPARING_ACTIF = _bs
    if not _bs:
        print("🔬 [ABLATION] brain-sparing v41.16 COUPÉ — la vigueur écrase les logits (témoin v41.15)")
        from naulthene.cerveau.noyau import BRAIN_SPARING_ACTIF as _vbs
        assert _vbs is False, "l'ablation n'a pas atteint le module — campagne invalide"

    # v41.20 — même discipline : module NOMMÉ + assertion runtime.
    _cmp = not _args.cout_moteur_table
    globals()["COUT_MOTEUR_PHYSIQUE"] = _cmp
    if _module_reel is not None:
        _module_reel.COUT_MOTEUR_PHYSIQUE = _cmp
    if not _cmp:
        print("🔬 [ABLATION] coût moteur v41.20 COUPÉ — retour à la table des 7 valeurs en dur")
        from naulthene.cerveau.noyau import COUT_MOTEUR_PHYSIQUE as _vcm
        assert _vcm is False, "l'ablation n'a pas atteint le module — campagne invalide"

    # v41.22 — même discipline : module NOMMÉ + assertion runtime.
    if _args.plafond_bus_fixe:
        globals()["DIM_BUS_MAX"] = 96
        if _module_reel is not None:
            _module_reel.DIM_BUS_MAX = 96
        print("🔬 [ABLATION] plafond de bus v41.22 COUPÉ — DIM_BUS_MAX figé à 96")
        from naulthene.cerveau.noyau import DIM_BUS_MAX as _vpb
        assert _vpb == 96, "l'ablation n'a pas atteint le module — campagne invalide"

    # v41.17 — second axe, même discipline : module NOMMÉ + assertion runtime.
    _ea = not _args.sans_economie_action
    globals()["ECONOMIE_ACTION_ACTIVE"] = _ea
    if _module_reel is not None:
        _module_reel.ECONOMIE_ACTION_ACTIVE = _ea
    if not _ea:
        print("🔬 [ABLATION] économie d'action v41.16 COUPÉE — le coût ignore la vigueur")
        from naulthene.cerveau.noyau import ECONOMIE_ACTION_ACTIVE as _vea
        assert _vea is False, "l'ablation n'a pas atteint le module — campagne invalide"

    # v41.18 — même discipline : module NOMMÉ + assertion runtime.
    globals()["DEFI_FORCE"] = bool(_args.defi_force)
    if _module_reel is not None:
        _module_reel.DEFI_FORCE = bool(_args.defi_force)
    if _args.defi_force:
        print("🔬 [FALSIFICATION] défi forcé à 100 % — P17 court-circuité")
        from naulthene.cerveau.noyau import DEFI_FORCE as _vdf
        assert _vdf is True, "le drapeau n'a pas atteint le module — mesure invalide"

    # La graine est réappliquée ICI, après les `manual_seed(42)` du haut de fichier : ce
    # sont eux qui rendaient les runs indiscernables.
    torch.manual_seed(_args.graine)
    np.random.seed(_args.graine)
    _random.seed(_args.graine)

    if _args.no_wandb:
        os.environ["WANDB_MODE"] = "disabled"
    wandb.init(project="Naulthene-AGI",
               name=f"v40_g{_args.graine}_{_args.jours}j",
               mode="disabled" if _args.no_wandb else None)

    if _args.brain:
        _persist = PersistanceAnatomique(_args.brain)
        etat = _persist.charger_ou_naitre()
    else:
        _persist, etat = None, initialiser_etat_cognitif()

    # v41.9 — la graine du run est portée par l'état : c'est elle qui dérive la graine de
    # chaque carte (voir `_graine_episode`). Posée APRÈS le chargement pour qu'un `.brain`
    # repris continue avec la graine du lancement courant, et non celle de sa naissance —
    # sans quoi deux reprises d'un même cerveau seraient indiscernables.
    etat.graine_run = int(_args.graine)

    for _ in range(1, _args.jours + 1):
        demarrer_journee(etat)
        etat.mort_du_jour = False
        for _tick in range(ticks_par_jour):
            traiter_tick(etat)
            # v41.27 (option b) — la mort coûte le reste de la journée. `executer_nuit`
            # s'exécute normalement juste après : l'agent dort, rêve et consolide ce qu'il
            # a vécu, exactement comme une journée complète — il en a simplement vécu
            # moins. C'est le coût.
            if getattr(etat, "mort_du_jour", False):
                etat.ticks_perdus_mort_jour = ticks_par_jour - _tick - 1
                break
        log = executer_nuit(etat)
        wandb.log(log)
        if _persist is not None:
            _persist.sauvegarder(etat)

    etat.env.close()
