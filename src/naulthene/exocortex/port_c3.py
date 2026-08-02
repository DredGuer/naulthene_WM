"""
Le Port C3 (v28.0, expérimental) — bus multiplexeur et contrat neutre de l'Exocortex.

Ce module ne connaît QUE des vecteurs numpy et des scalaires — jamais un tenseur
PyTorch, jamais `AGI_Naulthene`. C'est le "contrat d'interface neutre" du Chantier 1 :
le noyau construit une `RequeteC3`, l'envoie sur `PortC3.canal_emission`, reçoit une
liste de `ReponseC3` (éventuellement vide) et ne sait jamais ce qu'il y a de l'autre
côté du câble (un LLM local, une base vectorielle, un autre cerveau Naulthène...).

Isolation totale : `canal_emission` capture TOUTE exception levée par un plug — aucune
panne externe (réseau, timeout, format invalide) ne doit jamais remonter jusqu'au
noyau cognitif. Un plug qui échoue est mis en cooldown (voir `COOLDOWN_PLUG_ECHEC`)
plutôt que réinterrogé à chaque tick — la leçon retenue de `professeur_gemma.py`
(aucun health-check, aucun cache d'indisponibilité) est qu'un service éteint fait payer
son timeout complet À CHAQUE appel ; inacceptable dans une boucle 800 ticks × 900 jours.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# Ticks de mise en quarantaine d'un plug après une exception ou une indisponibilité —
# évite de repayer le coût d'un appel (souvent le pire cas : un timeout complet) à
# chaque tick tant que le service reste éteint. Volontairement modeste (~20s à 10
# ticks/s) : assez long pour ne pas spammer un service mort, assez court pour qu'un
# redémarrage du service soit détecté dans le même épisode.
COOLDOWN_PLUG_ECHEC = 200


@dataclass
class RequeteC3:
    """Ce que C2 émet sur le bus. `latent` est la pensée courante (pensee_bio, dim_bus)
    — jamais l'observation brute. Les métadonnées sont volontairement NEUTRES (aucune
    ne code un identifiant de niveau ou une position en dur, même esprit que les
    détecteurs génériques de noyau.py) : elles décrivent l'état interne de l'agent, pas
    la carte."""
    latent: np.ndarray                    # pensee_bio, shape (dim_bus,)
    num_actions: int                      # taille attendue de ReponseC3.preferences
    indecision_c2: float = 0.0            # std() du rollout mental avant normalisation — voir noyau.simuler_futur_et_planifier
    erreur_jepa: float = 0.0              # perte JEPA du tick courant
    palier_vocal: int = 0                 # 0 si aucun cursus vocal actif
    mot_frontal: Optional[str] = None     # mot lu par LecteurCaseFrontale, si actif
    contexte_libre: dict = field(default_factory=dict)  # extension future, jamais lu par le noyau lui-même


@dataclass
class ReponseC3:
    """Ce qu'un plug renvoie.

    v30.0 — **le pivot de C3 en 6ème sens**. Jusqu'en v29.x, un plug rendait un avis sur
    les actions (`preferences`) : C3 était un canal de DÉCISION, consulté via une 8ème
    action apprise. Depuis la v30.0, C3 est un canal de PERCEPTION — le plug rend un
    vecteur perceptif `perception` (DIM_EXO=8 dims normalisées) que l'agent « sent » en
    continu, au même titre que le toucher ou l'odorat, sans jamais avoir à le demander.

    Les deux champs coexistent et sont tous deux optionnels :

    - `perception` : le vecteur exogène Z_exogène, shape (8,), valeurs attendues dans
      [0, 1] (le noyau clippe de toute façon — voir `BusSensoriel.percevoir_exogene`).
      C'est le canal de la v30.0.
    - `preferences` : l'avis sur les actions, shape (num_actions,). **Conservé pour la
      rétrocompatibilité** des plugs écrits en v28.0 (`PlugSimule`, `PlugHTTP`) et parce
      que `ACTION_DEMANDER` reste présente dans le réseau (masquée en permanence, jamais
      amputée des `.brain` existants). Un plug purement perceptif laisse ce champ à None.

    Un plug peut donc être perceptif (v30), décisionnel (v28, historique), ou les deux —
    le port ne juge pas, il transporte."""
    confiance: float                      # dans [0, 1]
    origine: str                          # nom du plug ayant répondu
    perception: Optional[np.ndarray] = None   # v30.0 — Z_exogène, shape (DIM_EXO,)
    preferences: Optional[np.ndarray] = None  # v28.0 — avis sur les actions, shape (num_actions,)
    latence_ms: float = 0.0


class PlugC3(ABC):
    """Contrat minimal qu'un greffon doit respecter pour s'enregistrer sur le port.
    Toute nouvelle implémentation (Plug_Ollama, Plug_VectorDB, Plug_Web,
    Plug_BrainToBrain...) hérite de cette classe — le port ne connaît jamais rien
    d'autre que ces trois méthodes."""

    nom: str = "plug_anonyme"

    @abstractmethod
    def est_disponible(self) -> bool:
        """Doit répondre vite (pas d'appel réseau bloquant ici — un plug HTTP doit
        mettre en cache le résultat de son dernier ping, pas en refaire un par tick)."""
        raise NotImplementedError

    @abstractmethod
    def interroger(self, requete: RequeteC3) -> Optional[ReponseC3]:
        """Peut lever n'importe quelle exception — c'est `PortC3.canal_emission` qui
        est responsable de l'isolation, pas le plug lui-même. Peut aussi renvoyer None
        pour signaler "je n'ai rien à dire" sans que ce soit une erreur."""
        raise NotImplementedError


class PortC3:
    """Le multiplexeur. Un seul port par `AGI_Naulthene`, zéro ou plusieurs plugs
    enregistrés dessus. Absent d'un run (aucun `enregistrer` appelé) : `plugs_disponibles()`
    est toujours vide, exactement comme si le port n'existait pas — c'est ce qui
    garantit l'invariance biologique pure (voir noyau._masque_action_c3)."""

    def __init__(self):
        self._plugs: dict[str, PlugC3] = {}
        self._cooldown_jusqua: dict[str, int] = {}  # nom -> tick_absolu de fin de cooldown

    def enregistrer(self, plug: PlugC3) -> None:
        self._plugs[plug.nom] = plug

    def retirer(self, nom: str) -> None:
        self._plugs.pop(nom, None)
        self._cooldown_jusqua.pop(nom, None)

    def plugs_disponibles(self, tick_absolu: int = 0) -> list[str]:
        """Un plug en cooldown n'est PAS disponible, même s'il répondrait `est_disponible()
        -> True` — c'est la mémoire de panne qui protège le budget de latence."""
        disponibles = []
        for nom, plug in self._plugs.items():
            if tick_absolu < self._cooldown_jusqua.get(nom, 0):
                continue
            try:
                if plug.est_disponible():
                    disponibles.append(nom)
            except Exception:
                self._mettre_en_cooldown(nom, tick_absolu)
        return disponibles

    def _mettre_en_cooldown(self, nom: str, tick_absolu: int) -> None:
        self._cooldown_jusqua[nom] = tick_absolu + COOLDOWN_PLUG_ECHEC

    def canal_emission(self, requete: RequeteC3, mode: str = "1_1",
                        cible: Optional[str] = None,
                        tick_absolu: int = 0) -> list[ReponseC3]:
        """mode="1_1" : interroge uniquement `cible` (désigné par la tête de routage
        `tete_requete` côté noyau). mode="1_X" : diffuse à tous les plugs disponibles.
        Ne lève JAMAIS — toute exception d'un plug est capturée, le plug part en
        cooldown, et l'appel continue avec les plugs restants."""
        noms_disponibles = self.plugs_disponibles(tick_absolu)
        if mode == "1_1":
            noms_a_interroger = [cible] if cible in noms_disponibles else []
        else:
            noms_a_interroger = noms_disponibles

        reponses = []
        for nom in noms_a_interroger:
            plug = self._plugs[nom]
            debut = time.monotonic()
            try:
                reponse = plug.interroger(requete)
            except Exception:
                self._mettre_en_cooldown(nom, tick_absolu)
                continue
            if reponse is not None:
                reponse.latence_ms = (time.monotonic() - debut) * 1000.0
                reponses.append(reponse)
        return reponses

    @staticmethod
    def _moyenne_ponderee(vecteurs: list, poids: list) -> Optional[np.ndarray]:
        """Moyenne pondérée d'une liste de vecteurs, en ignorant les None. Retourne None
        si aucun vecteur exploitable — jamais une valeur inventée. Un poids total nul
        (toutes les confiances à 0) retombe sur une moyenne simple plutôt qu'une
        division par zéro."""
        paires = [(v, p) for v, p in zip(vecteurs, poids) if v is not None]
        if not paires:
            return None
        total = sum(p for _, p in paires)
        if total <= 0.0:
            return np.mean([v for v, _ in paires], axis=0)
        return sum(v * p for v, p in paires) / total

    @staticmethod
    def agreger(reponses: list[ReponseC3]) -> Optional[ReponseC3]:
        """Fusionne les réponses de plusieurs plugs en une seule, pondérée par la
        confiance de chacun — repli None si aucune réponse (bus vide ou tous les plugs
        en échec), jamais une valeur inventée (même philosophie que
        `professeur_gemma.juger_qualitatif`).

        v30.0 : agrège les DEUX canaux indépendamment — `perception` (le 6ème sens) et
        `preferences` (l'avis historique sur les actions). Chacun ignore les plugs qui ne
        le fournissent pas, si bien qu'un bus mélangeant un plug perceptif (v30) et un
        plug décisionnel (v28) produit une réponse cohérente sur les deux canaux, sans
        qu'aucun des deux ne plante sur le `None` de l'autre."""
        if not reponses:
            return None
        poids = [r.confiance for r in reponses]
        poids_total = sum(poids)
        confiance = 0.0 if poids_total <= 0.0 else poids_total / len(reponses)
        return ReponseC3(
            perception=PortC3._moyenne_ponderee([r.perception for r in reponses], poids),
            preferences=PortC3._moyenne_ponderee([r.preferences for r in reponses], poids),
            confiance=float(np.clip(confiance, 0.0, 1.0)),
            origine="+".join(r.origine for r in reponses),
            latence_ms=max((r.latence_ms for r in reponses), default=0.0),
        )
