# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — le RAPPORTEUR : lire un cerveau VIVANT par `register_forward_hook`, sans le toucher.

C'est le SEUL module du chantier qui connaît un cerveau (`AGI_Naulthene`) : il pose un hook de
sortie sur les 12 couches `NaultheneLinearSynaptique`, met en forme les trois trames de
`telemetrie.py`, et publie. Le serveur, la page et la source factice, eux, ne savent rien de
`torch` — c'est ce qui fait tenir la promesse de l'étape 0.

⚠️ LECTURE SEULE STRICTE : aucun `backward()`, aucun pas d'optimiseur, aucun fichier écrit, et
**un hook ne remplace JAMAIS la sortie d'une couche** (il retourne `None`). Discipline MES-02 :
le rapporteur OBSERVE le passage avant réel de `penser()`, il ne recalcule RIEN. La neutralité
est prouvée par `torch.equal` sur `_tronc_cerebral` avec et sans hooks
(`tests/test_cerveau_3d.py::TestRapporteur::test_les_hooks_ne_changent_pas_la_sortie_observee`).

⚠️ Le module est inerte sur le cerveau, mais l'APPELANT doit avoir mis l'agent en `eval()` :
en mode `train`, `NaultheneLinearSynaptique.forward` met à jour `myeline_M`/`trace_activation` —
c'est le cerveau qui apprend, pas le rapporteur, mais le résultat n'est plus « sans effet ».


═══ 🔴 LA CONTRAINTE CENTRALE DE CETTE TÂCHE : QUELLE ÉCRITURE RETENIR ? ═══

Le plan supposait qu'un hook « dernière écriture gagne » suffisait. **C'est faux, et c'est
mesurable dans `noyau.py`** : plusieurs couches sont appelées PLUSIEURS FOIS par tick, parce que
`simuler_futur_et_planifier` (le rollout mental, `noyau.py` l.1146-1308) les rappelle dans des
boucles sur 8 branches × plusieurs horizons. Capturer la dernière écriture afficherait donc une
**hypothèse contrefactuelle** (le dernier futur simulé) au lieu du tick réellement vécu.

L'ordre des appels d'un tick complet (`traiter_tick` → `penser`), relevé sur les sites d'appel :

    C1  `_tronc_cerebral`  porte_visuelle → porte_auditive → hippocampe → analyseur
        `lecture_episodique`  fusion_memoire  (DEUX fois : la 2ᵉ est la valeur retournée)
        `integrer_bio`        integrateur_bio
        `tete_motrice`        (les logits qui SERVENT à décider)
    C2  `simuler_futur_et_planifier`  — TOUTES ses écritures sont par LOT de 8 branches :
        generateur_attente (l.1197), hippocampe (l.1198), analyseur (l.1199),
        integrateur_bio (l.1239), tete_motrice (l.1194), cortex_prefrontal (l.1245)
    fin `penser`   cortex_prefrontal (valeur de l'état RÉEL, l.1614) → tete_vocale → tete_requete
    `traiter_tick` generateur_attente par `generer_attente_reelle` (l.10104, l'action réellement
                   jouée) puis generateur_attente_audio (l.10117) ;
                   `perte_jepa` rappelle porte_visuelle (l.1712) et porte_auditive (l.1752)
                   sur l'observation SUIVANTE, sous `torch.no_grad()`.

**Règle 1 — le LOT.** Seules les écritures d'un lot à UNE ligne sont candidates. Un tick décide
pour UN état : les branchements simulés sont TOUS par lot (`pensee.expand(num_actions, -1)`), donc
écartés **structurellement**, sans avoir à deviner l'ordre des appels. C'est ce qui rend la règle
robuste à un horizon changé, ajouté ou retiré.

**Règle 2 — la POLITIQUE PAR COUCHE**, déclarée dans `POLITIQUE_PAR_COUCHE` (une ligne par couche,
justifiée ci-dessous) :

| Couche | Écriture retenue | Pourquoi |
|---|---|---|
| `porte_visuelle` | **première** | la 1ʳᵉ est l'observation COURANTE (l.1084) ; la 2ᵉ est `perte_jepa` sur `obs_suivante` (l.1712) — le monde d'APRÈS, que la décision n'a pas vu |
| `porte_auditive` | **première** | idem : le son courant (l.1086, ou le silence zéro l.1124) ; la 2ᵉ (l.1752) est le son suivant |
| `hippocampe` | **première** | la mémoire de travail du tick (l.1126) ; le rollout la rappelle 8×horizons fois (l.1198) |
| `analyseur` | **première** | la pensée du tick (l.1127) ; rappelée par le rollout (l.1199) |
| `fusion_memoire` | **dernière** | `lecture_episodique` l'appelle DEUX fois (l.1133) : seule la 2ᵉ est retournée, la 1ʳᵉ n'alimente personne |
| `integrateur_bio` | **première** | le corps entre dans la décision (l.1318) ; rappelé par le rollout (l.1239) |
| `tete_motrice` | **première** | `logits_instinct` (l.1353) est la sortie qui a servi à décider ; le rollout la rappelle pour son argmax (l.1194) |
| `cortex_prefrontal` | **dernière** | la valeur de l'état RÉEL (l.1614) vient APRÈS les valeurs imaginaires du rollout (l.1245) |
| `tete_vocale` | **dernière** | un seul appel par tick (l.1621) |
| `tete_requete` | **dernière** | un seul appel par tick (l.1628) |
| `generateur_attente` | **dernière** | ⚠️ AUCUN appel sur le chemin de décision (voir ci-dessous) |
| `generateur_attente_audio` | **dernière** | ⚠️ AUCUN appel dans un tick muet (voir ci-dessous) |

⚠️ **Les deux têtes JEPA n'ont aucun appel sur le chemin de décision — et c'est DIT, pas tu.**
Le cerveau ne s'en sert pas pour décider : elles prédisent le bus. Dans `penser`, les seules
écritures de `generateur_attente` sont celles du rollout (contrefactuelles, par lot : écartées) ;
la seule écriture réelle du tick est `generer_attente_reelle`, APRÈS le pas d'environnement —
la prédiction de l'action réellement jouée. Si le tick ne l'atteint pas (appel de `penser` seul,
`rever()`, rejeu nocturne), la couche n'a **aucune** écriture de tick : le rapporteur publie alors
des ZÉROS et l'inscrit dans `compteurs()["couches_non_ecrites"]`. Un zéro affiché est un silence
DOCUMENTÉ, jamais une branche simulée prise pour le présent. `generateur_attente_audio` est dans
le même cas dès qu'aucun son n'est perçu (le cerveau ne calcule pas de prédiction auditive sans
audio).

**Fenêtre de capture.** `nouveau_tick()` remet la capture à zéro et DOIT être appelé avant chaque
tick observé : sans lui, les écritures d'une nuit (`rever()`, rejeu nocturne, qui appellent les
mêmes couches) seraient prises pour celles du dernier tick. `publier_activite` publie la capture
du DERNIER tick capté, au plus une fois par période — un cerveau qui vit à 400 ticks/s et un
écran à 15 Hz ne sont pas la même horloge.

⚠️ Ce module est un MIROIR des activations déclarées par `ACTIVATION_PAR_COUCHE` (le hook capture
la sortie LINÉAIRE ; le ReLU/la sigmoïde sont appliqués après, par `penser`) : si cette table
s'avère fausse, elle se signale ici — `TestRapporteur::test_l_activation_declaree_par_la_table_
est_appliquee` compare la table à ce que `noyau.py` fait vraiment. On ne la corrige pas dans ce
module (hors périmètre), on le rapporte.

Voir `docs/ameliorations/CHANTIER_VIS-01_cerveau_3d_irm_vivante.md` §4 (les trois trames) et
`PLAN_VIS-01_cerveau_3d.md` (tâche 7).
"""
from __future__ import annotations

import time

import numpy as np

from naulthene.cerveau.telemetrie import (
    ACTIVATION_PAR_COUCHE,
    RANGS,
    disposition,
    encoder_octets,
    quantifier_matrice,
    trame_activite,
    trame_evenement,
    trame_structure,
)

# --- 1. La politique de capture, une ligne par couche --------------------------------
#
# « premiere » = seule la 1ʳᵉ écriture à UNE ligne du tick est retenue ;
# « derniere » = la dernière écriture à UNE ligne du tick est retenue.
# La justification de chaque ligne est dans la docstring du module (tableau) — elle est le
# résultat de la lecture des sites d'appel de `noyau.py`, pas d'un choix esthétique.
POLITIQUE_PAR_COUCHE = {
    "porte_visuelle": "premiere",          # obs COURANTE (l.1084), pas `obs_suivante` (l.1712)
    "porte_auditive": "premiere",          # son courant ou silence (l.1086/1124), pas le suivant
    "hippocampe": "premiere",              # mémoire de travail (l.1126), pas le rollout (l.1198)
    "analyseur": "premiere",               # pensée (l.1127), pas le rollout (l.1199)
    "fusion_memoire": "derniere",          # 2ᵉ des 2 itérations de `lecture_episodique` (l.1133)
    "integrateur_bio": "premiere",         # corps dans la décision (l.1318), pas le rollout (l.1239)
    "tete_motrice": "premiere",            # `logits_instinct` (l.1353) : ce qui a décidé
    "cortex_prefrontal": "derniere",       # valeur de l'état RÉEL (l.1614) après les imaginaires
    "tete_vocale": "derniere",             # un seul appel par tick (l.1621)
    "tete_requete": "derniere",            # un seul appel par tick (l.1628)
    "generateur_attente": "derniere",      # prédiction de l'action JOUÉE (l.10104), sinon rien
    "generateur_attente_audio": "derniere",  # idem, et seulement si un son est perçu (l.10117)
}

# Les scalaires d'affichage que le RAPPORTEUR ne peut pas connaître : ils vivent dans `etat`
# (dopamine, faim, action échantillonnée), pas dans l'agent. C'est `meta` qui les porte — le
# rapporteur ne les invente jamais, et une clé absente reste absente (la page a son propre
# défaut d'affichage, ce module n'écrit pas un chiffre qu'il n'a pas lu).
SCALAIRES_DU_CALLER = ("dopamine", "faim", "action", "force_planification")

# Le témoin du dernier arbitrage déposé par `penser()` sur le module (`mesure_arbitrage`),
# purement observationnel côté cerveau. Clés conditionnelles : un cerveau qui n'a pas encore
# pensé n'en a pas.
SCALAIRES_DU_CERVEAU = ("amplitude_c1", "amplitude_c2", "gain_c1", "accord",
                        "vote_c1", "vote_c2")


def couches_du_cerveau(agent) -> list[dict]:
    """Les 12 couches, **lues sur l'agent** — jamais une table supposée.

    `definir_couches` est une FIXTURE (sa docstring le dit) : la seule chose qui l'empêche de
    dériver est `test_forme_factice_egale_forme_reelle`. Ici, `entree`/`sortie` sont prises sur
    les modules eux-mêmes (`in_features`/`out_features`), ce qui rend le rapporteur insensible à
    une erreur de la table ; seul le `rang` (convention d'AFFICHAGE, spec §5) vient de `RANGS`.

    ⚠️ GARDE-FOU QUI CRIE : si le cerveau n'a pas EXACTEMENT les 12 couches attendues (une
    couche nouvelle, ou une couche disparue après une greffe), on lève — afficher 11 plaques en
    silence ferait passer une architecture changée pour un cerveau normal.
    """
    vues = {nom: module for nom, module in agent.named_modules()
            if hasattr(module, "base_weight") and hasattr(module, "annexe_weight")}
    manquantes = [nom for nom in RANGS if nom not in vues]
    inconnues = sorted(nom for nom in vues if nom not in RANGS)
    if manquantes or inconnues:
        raise ValueError(
            f"cerveau inattendu pour la lecture 3D : {len(vues)} couches lues, "
            f"12 attendues — manquantes={manquantes} inconnues={inconnues}")
    return [{"nom": nom, "rang": RANGS[nom],
             "entree": int(vues[nom].in_features), "sortie": int(vues[nom].out_features)}
            for nom in RANGS]


def bornes_du_cerveau(agent) -> list[dict]:
    """Les bornes sensorielles et les têtes à entrée mixte, LITes sur l'agent (spec §5).

    Miroir exact de `factice.bornes_factices`, qui ne peut pas, lui, interroger l'agent. Les
    dimensions sont DÉRIVÉES des formes réelles : `vecteur_bio = integrateur_bio.in_features -
    dim_bus` (le `cat([pensee, vecteur_bio])` de `integrer_bio`), jamais la constante 44 posée
    à côté — une greffe du vecteur bio (v41.x) ferait mentir la constante, pas cette soustraction.
    L'ORDRE des `rang_entree` est celui du `cat()` de `noyau.py` : les actions AVANT le bus
    (`153 = 145 + 8`), le vecteur bio APRÈS (`189 = 145 + 44`).
    """
    db = int(agent.dim_bus)
    vision = int(agent.porte_visuelle.in_features)
    audio = int(agent.porte_auditive.in_features)
    bio = int(agent.integrateur_bio.in_features) - db
    actions = int(agent.num_actions)
    return [
        {"nom": "vision", "dim": vision, "couche": "porte_visuelle",
         "rang_entree": [0, vision]},
        {"nom": "audio", "dim": audio, "couche": "porte_auditive",
         "rang_entree": [0, audio]},
        {"nom": "vecteur_bio", "dim": bio, "couche": "integrateur_bio",
         "rang_entree": [db, db + bio]},
        {"nom": "actions", "dim": actions, "couche": "generateur_attente",
         "rang_entree": [0, actions]},
        {"nom": "actions", "dim": actions, "couche": "generateur_attente_audio",
         "rang_entree": [0, actions]},
    ]


def appliquer_activation(nom: str, valeurs: np.ndarray) -> np.ndarray:
    """Applique l'activation que `penser()` applique après cette couche (`ACTIVATION_PAR_COUCHE`).

    Le hook capture la sortie LINÉAIRE : ceci est un MIROIR, pas une réinterprétation. La
    sigmoïde passe par `0,5·(1 + tanh(x/2))` — identité exacte avec `1/(1 + e^-x)`, mais sans
    `overflow` sur un logit extrême (un cerveau dans un état inattendu doit s'afficher, pas
    remplir la console d'avertissements numpy).
    """
    mode = ACTIVATION_PAR_COUCHE.get(nom, "aucune")
    if mode == "relu":
        return np.maximum(valeurs, 0.0)
    if mode == "sigmoide":
        x = np.asarray(valeurs, dtype=np.float64)
        return (0.5 * (1.0 + np.tanh(0.5 * x))).astype(np.asarray(valeurs).dtype)
    return valeurs


# --- 2. Le rapporteur ----------------------------------------------------------------

class Rapporteur:
    """Lit un cerveau VIVANT sans le modifier, et publie ses trames.

    Cycle d'usage (le seul ordre correct) ::

        rapporteur.attacher(agent)                       # une fois
        rapporteur.publier_structure(agent, meta)        # à la connexion, après chaque neurogenèse
        for tick in ...:
            rapporteur.nouveau_tick()                    # AVANT le tick : ouvre la fenêtre
            traiter_tick(etat)                           # le cerveau vit (et décide)
            trame = rapporteur.publier_activite(agent, meta)   # None si la période n'est pas écoulée
        rapporteur.detacher()

    `bus=None` est permis (ruling du plan) : les trames sont alors PRODUITES et renvoyées, sans
    être publiées — c'est le cas du drapeau `--telemetrie-3d` du noyau, qui relaie lui-même.
    """

    def __init__(self, bus, hz: float = 15.0):
        if float(hz) <= 0.0:
            raise ValueError(f"cadence invalide : hz={hz!r} (attendu > 0)")
        self.bus = bus
        self.periode = 1.0 / float(hz)
        self._formes = {}          # nom -> nombre de neurones de sortie (lu à l'attachement)
        self._sorties = {}         # nom -> np.ndarray : LA capture du tick courant
        self._ecritures = {}       # nom -> écritures candidates vues depuis `nouveau_tick()`
        self._hooks = []
        # ⚠️ `None` (et non `0.0`) : « jamais publié ». Avec 0.0, une machine fraîchement
        # démarrée (`time.monotonic()` < période) resterait muette pendant la première seconde —
        # un rapporteur qui n'émet pas au premier tick est un défaut, pas un throttle.
        self._derniere_publication = None
        self._par_lot = 0          # écritures écartées (lot > 1 ligne) depuis `nouveau_tick()`
        self._par_lot_total = 0
        self._publications = 0
        self._structures = 0
        self._chocs = 0
        self._non_ecrites = []     # couches sans écriture de tick, à la dernière trame publiée

    # --- attachement ---

    def attacher(self, agent) -> None:
        """Pose un hook de sortie sur les 12 couches, dans l'ordre de `RANGS` (celui de
        `definir_couches` — l'ordre du FLUX de données, jamais une anatomie).

        `attacher` est IDEMPOTENT : un second appel détache le premier (sinon chaque couche
        serait écrite 2×, 3×… et une politique de capture deviendrait un compteur de hooks).
        Les formes sont lues ICI, sur l'agent (`couches_du_cerveau`) : c'est ce qui permet à
        `publier_activite(None, meta)` — le cas du throttle — de connaître les 12 longueurs.
        """
        self.detacher()
        couches = couches_du_cerveau(agent)
        self._formes = {couche["nom"]: int(couche["sortie"]) for couche in couches}
        for couche in couches:
            module = getattr(agent, couche["nom"])
            self._hooks.append(module.register_forward_hook(self._fabriquer_hook(couche["nom"])))

    def _fabriquer_hook(self, nom):
        """Le hook d'une couche : il CAPTURE et retourne `None` (jamais la sortie).

        ⚠️ `return None` est impératif : un hook qui retourne une valeur REMPLACE la sortie du
        module, donc modifie le cerveau observé. C'est la neutralité prouvée par `torch.equal`.
        """
        politique = POLITIQUE_PAR_COUCHE[nom]

        def hook(_module, _entree, sortie):
            # Règle 1 — le LOT. Un tick décide pour UN état ; les branchements du rollout mental
            # sont tous par lot de `num_actions`, donc écartés ici sans lire l'ordre des appels.
            lignes = int(sortie.shape[0]) if getattr(sortie, "ndim", 0) >= 1 else 1
            if lignes != 1:
                self._par_lot += 1
                self._par_lot_total += 1
                return None
            self._ecritures[nom] = self._ecritures.get(nom, 0) + 1
            # Règle 2 — la politique par couche (cf. `POLITIQUE_PAR_COUCHE`).
            if politique == "premiere" and nom in self._sorties:
                return None
            # `.copy()` : `numpy()` partage la mémoire du tenseur, et une écriture en place en
            # aval (`logits_finaux[..., 7] = -inf` se fait sur un clone, mais rien ne le garantit)
            # salirait la capture rétroactivement. La copie est de taille d'un neurone × 12.
            self._sorties[nom] = sortie.detach().reshape(-1).to("cpu").numpy().copy()
            return None

        return hook

    def detacher(self) -> None:
        """Retire les hooks. Idempotent : le cerveau redevient exactement ce qu'il était."""
        for hook in self._hooks:
            hook.remove()
        self._hooks = []

    def nouveau_tick(self) -> None:
        """Ouvre la fenêtre de capture d'un tick — À APPELER AVANT CHAQUE TICK OBSERVÉ.

        Sans cet appel, la capture retiendrait aussi les passages hors tick (`rever()`, rejeu
        nocturne de `_epoques_supplementaires`), c'est-à-dire une autre horloge que celle qu'on
        croit regarder.
        """
        self._sorties = {}
        self._ecritures = {}
        self._par_lot = 0

    # --- publication ---

    def publier_structure(self, agent, meta=None) -> None:
        """Lit formes, poids et bornes SUR L'AGENT, calcule la géométrie (`disposition`) et publie.

        ⚠️ Les positions partent DANS la trame (`positions`) : c'est le serveur qui sait où sont
        les neurones, jamais le navigateur — la disposition est définie une seule fois, en Python,
        et identique pour tous les cerveaux (spec §5).

        `dim_bus` est ÉCRIT par le rapporteur depuis l'agent (la valeur lue prime sur une valeur
        passée par l'appelant : une trame qui annonce un bus faux ferait mentir toute la page).
        """
        couches = couches_du_cerveau(agent)
        geometrie = disposition(couches)
        encodees = []
        for couche in couches:
            module = getattr(agent, couche["nom"])
            poids = (module.base_weight + module.annexe_weight).detach().to("cpu").numpy()
            octets, echelle = quantifier_matrice(poids)
            points = geometrie[couche["nom"]].astype(np.float16).tobytes()
            encodees.append({**couche, "echelle": echelle,
                             "poids_i8": encoder_octets(octets),
                             "positions": encoder_octets(points)})
        meta_complet = {**(meta or {}), "dim_bus": int(agent.dim_bus)}
        self._structures += 1
        if self.bus is None:
            return
        self.bus.publier_structure(
            trame_structure(encodees, bornes_du_cerveau(agent), meta_complet))

    def publier_activite(self, agent=None, meta=None):
        """Publie l'activité capturée du dernier tick — au plus une fois par période.

        Renvoie la trame publiée, ou `None` si la période n'est pas écoulée (c'est ce retour que
        relaie le drapeau `--telemetrie-3d` du noyau, tâche 9). `agent=None` est accepté : le
        throttle et la forme des 12 couches viennent de l'attachement, pas de cet appel.

        Les couches sans écriture de tick (cf. docstring du module) partent à ZÉRO et sont
        listées dans `compteurs()["couches_non_ecrites"]` — un silence déclaré.
        """
        maintenant = time.monotonic()
        if (self._derniere_publication is not None
                and maintenant - self._derniere_publication < self.periode):
            return None
        self._derniere_publication = maintenant
        if not self._formes and agent is not None:
            self._formes = {couche["nom"]: int(couche["sortie"])
                            for couche in couches_du_cerveau(agent)}
        neurones = {}
        self._non_ecrites = []
        for nom, taille in self._formes.items():
            valeurs = self._sorties.get(nom)
            if valeurs is None:
                self._non_ecrites.append(nom)
                valeurs = np.zeros(int(taille), dtype=np.float32)
            elif valeurs.size != int(taille):
                # Garde-fou de forme qui CRIE : une trame de la mauvaise longueur ferait
                # désaligner la page en silence (elle découpe par `couche.sortie`).
                raise ValueError(f"capture de {nom!r} : {valeurs.size} valeurs, "
                                 f"{taille} attendues")
            neurones[nom] = encoder_octets(
                appliquer_activation(nom, valeurs).astype(np.float16).tobytes())
        trame = trame_activite(neurones, self._scalaires(agent, meta), dict(meta or {}))
        self._publications += 1
        if self.bus is not None:
            self.bus.publier_activite(trame)
        return trame

    def signal_choc(self, intensite, meta=None):
        """Publie un choc dopaminergique (fait daté du canal `evenement`) et renvoie sa trame.

        Le rapporteur ne DOSE pas un choc : il relaie une intensité qu'on lui donne (le noyau la
        connaît, lui). Le retour existe pour que le mode sans bus (tâche 9) puisse le relayer.
        """
        trame = trame_evenement("choc_dopamine", dict(meta or {}), intensite=float(intensite))
        self._chocs += 1
        if self.bus is not None:
            self.bus.publier_evenement(trame)
        return trame

    # --- lecture de l'agent ---

    def _scalaires(self, agent, meta) -> dict:
        """Les scalaires de la trame : ce que l'appelant SAIT, puis ce que l'agent TÉMOIGNE.

        `dopamine`, `faim` et `action` vivent dans `etat` (le noyau), pas dans l'agent : ils
        arrivent par `meta` et ne sont JAMAIS inventés ici. `force_planification` est en revanche
        lisible sur l'agent — `acceptation() = envie × confiance vécue` est exactement la valeur
        que `traiter_tick` passe à `penser` (elle ne bouge qu'à la nuit) ; elle sert de repli
        quand `meta` ne la porte pas.
        """
        meta = meta or {}
        scalaires = {cle: meta[cle] for cle in SCALAIRES_DU_CALLER if cle in meta}
        if agent is None:
            return scalaires
        if "force_planification" not in scalaires:
            scalaires["force_planification"] = float(agent.acceptation())
        mesure = getattr(agent, "mesure_arbitrage", None)
        if isinstance(mesure, dict):
            for cle in SCALAIRES_DU_CERVEAU:
                if cle in mesure:
                    scalaires[cle] = mesure[cle]
        return scalaires

    def compteurs(self) -> dict:
        """Ce que le rapporteur a fait — et surtout ce qu'il n'a PAS pu capturer.

        `ecritures_par_couche` est la table de vérité de la règle de capture : elle permet à un
        appelant de voir qu'une couche a bien été écrite (ou pas) sur le dernier tick, au lieu de
        le déduire d'une couleur à l'écran. `ecritures_par_lot` compte les écritures écartées
        parce que par LOT (rollout mental, rejeu nocturne) — depuis `nouveau_tick()`, et en cumul.
        """
        return {
            "publications": self._publications,
            "structures": self._structures,
            "chocs": self._chocs,
            "couches": len(self._formes),
            "ecritures_par_couche": dict(self._ecritures),
            "couches_non_ecrites": list(self._non_ecrites),
            "ecritures_par_lot": self._par_lot,
            "ecritures_par_lot_total": self._par_lot_total,
            "periode": self.periode,
        }
