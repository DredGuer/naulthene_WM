"""Plug Mémoire Augmentée (v30.0, expérimental) — le premier plug PERCEPTIF.

C'est le plug de démonstration de l'Exo-Sens (le 6ème sens). Contrairement aux plugs
v28.0 (`PlugSimule`, `PlugHTTP`) qui rendaient un avis sur les ACTIONS, celui-ci rend un
vecteur de PERCEPTION (`ReponseC3.perception`, DIM_EXO=8 dims dans [0, 1]) — l'agent ne
l'interroge pas, il le « sent » en continu.

**100 % local, déterministe, aucune dépendance externe** (ni réseau, ni Ollama, ni base
vectorielle). C'est délibéré : il sert à valider que C1/C2 digèrent correctement un signal
exogène AVANT d'introduire la latence et le non-déterminisme d'un vrai service. On ne
débogue jamais deux inconnues à la fois.

Ce qu'il perçoit : un résumé de la **mémoire épisodique spatiale** que l'agent possède
déjà (`noyau.MemoireEpisodiqueSpatiale`). C'est donc une « prothèse mnésique » — l'agent
perçoit une synthèse de ses propres souvenirs, que son cerveau ne sait pas produire seul
à chaque tick. Un cas d'usage exogène honnête, sans tricher en injectant une information
que l'agent n'aurait aucun moyen de connaître.

Discipline d'isolation (identique aux autres plugs) : ce module n'importe JAMAIS
`naulthene.cerveau.noyau` — il ne connaît que le contrat `port_c3` et une **source de
données injectée** (un callable fourni à la construction). C'est ce qui garde le
sous-package `exocortex` indépendant du cerveau, et permet de brancher n'importe quelle
autre source (RAG, base vectorielle, API) sur exactement le même patron.
"""

import numpy as np

from naulthene.exocortex.port_c3 import PlugC3, RequeteC3, ReponseC3

# Doit rester synchronisé avec `bus_sensoriel.DIM_EXO`. Redéclaré ici plutôt qu'importé
# pour ne pas créer de dépendance de `exocortex/` vers `cerveau/` — le contrat est la
# taille du vecteur, pas le module qui le consomme.
DIM_PERCEPTION = 8


class PlugMemoireAugmentee(PlugC3):
    """Traduit un résumé de mémoire spatiale en vecteur perceptif de 8 dims.

    `source` est un callable sans argument qui retourne un dict (ou None). Les clés
    attendues, toutes optionnelles et toutes dans [0, 1] :

        distance_food, fraicheur_food      — souvenir de nourriture le plus pertinent
        distance_water, fraicheur_water    — idem pour l'eau
        distance_porte, fraicheur_porte    — idem pour une porte/objet remarquable
        densite_souvenirs                  — combien de souvenirs actifs (normalisé)
        couverture_carte                   — part de la carte déjà explorée

    ⚠️ `distance_porte`/`fraicheur_porte` restent à 0.0 avec la source fournie ci-dessous :
    à ce jour, `MemoireEpisodiqueSpatiale` n'enregistre que des souvenirs de type "FOOD" et
    "WATER" (voir les deux appels à `enregistrer_evenement` dans `noyau.traiter_tick`).
    Ces deux dimensions sont donc réservées — dimensionnées dès maintenant pour que le
    contrat de 8 dims reste stable si un souvenir de porte est ajouté plus tard, plutôt que
    de devoir réordonner le vecteur (ce qui invaliderait les poids déjà appris par
    `integrateur_bio`). Un vecteur à deux dimensions constamment nulles est sans danger :
    le réseau apprendra simplement à les ignorer.

    Une clé absente vaut 0.0 (perception neutre sur cette dimension), une source qui
    retourne None vaut vecteur nul. Aucune exception n'est laissée remonter au-delà de
    `PortC3.canal_emission`, mais on préfère renvoyer un vecteur neutre plutôt que lever
    pour une source simplement vide — un plug perceptif « qui n'a rien à dire » n'est pas
    un plug en panne.
    """

    nom = "plug_memoire_augmentee"

    # Ordre FIGÉ des dimensions — c'est le contrat de lecture du vecteur, il doit rester
    # stable pour que les poids appris par `integrateur_bio` gardent leur sens d'un run à
    # l'autre. Ne jamais réordonner ni insérer au milieu : ajouter en queue si besoin
    # (même règle que le vecteur bio côté noyau).
    CLES = (
        "distance_food", "fraicheur_food",
        "distance_water", "fraicheur_water",
        "distance_porte", "fraicheur_porte",
        "densite_souvenirs", "couverture_carte",
    )

    def __init__(self, source=None, confiance: float = 0.6):
        self.source = source
        self.confiance = float(np.clip(confiance, 0.0, 1.0))
        self.panne = False  # même flag de crash-test que PlugSimule

    def est_disponible(self) -> bool:
        """Toujours disponible : aucune ressource externe à joindre. Doit répondre vite
        (contrat `PlugC3`) — c'est le cas, c'est une constante."""
        return not self.panne

    def interroger(self, requete: RequeteC3) -> ReponseC3 | None:
        if self.panne:
            raise RuntimeError("PlugMemoireAugmentee en panne simulée (crash-test)")

        donnees = self.source() if callable(self.source) else None
        vecteur = np.zeros(DIM_PERCEPTION, dtype=np.float32)
        if isinstance(donnees, dict):
            for i, cle in enumerate(self.CLES):
                valeur = donnees.get(cle, 0.0)
                try:
                    vecteur[i] = float(valeur)
                except (TypeError, ValueError):
                    vecteur[i] = 0.0  # valeur illisible → dimension neutre, jamais un crash

        # Clip défensif : le noyau reclippe de toute façon (voir
        # BusSensoriel.percevoir_exogene), mais un plug qui respecte son propre contrat
        # rend le diagnostic bien plus simple quand plusieurs plugs sont branchés.
        vecteur = np.clip(np.nan_to_num(vecteur, nan=0.0, posinf=1.0, neginf=0.0), 0.0, 1.0)

        return ReponseC3(
            perception=vecteur,
            confiance=self.confiance,
            origine=self.nom,
        )


def source_depuis_memoire_spatiale(etat, capacite_reference: int = 200,
                                    distance_reference: float = 20.0):
    """Fabrique un `source` branché sur la mémoire épisodique spatiale d'un `EtatCognitif`.

    Vit ICI plutôt que dans `noyau.py` pour garder le sens de la dépendance : c'est
    l'appelant (un cursus, un script de test) qui connaît à la fois le cerveau et le plug,
    jamais `exocortex/` qui irait chercher `cerveau/`. La fonction retournée est un
    closure sans argument, exactement ce qu'attend `PlugMemoireAugmentee(source=...)`.

    Toutes les valeurs produites sont normalisées dans [0, 1] :
    - `distance_*` : 1.0 = le souvenir est ici même, 0.0 = très loin (ou aucun souvenir) ;
    - `fraicheur_*` : 1.0 = souvenir tout récent, 0.0 = ancien (ou aucun) ;
    - `densite_souvenirs` : nombre de souvenirs rapporté à `capacite_reference` ;
    - `couverture_carte` : part des cases distinctes visitées, si l'information existe.

    Robuste par construction : toute absence d'attribut ou exception retombe sur 0.0 pour
    la dimension concernée — un plug perceptif ne doit jamais faire tomber un run.
    """
    def _lire():
        try:
            memoire = getattr(etat, "memoire_episodique_spatiale", None)
            if memoire is None:
                return None
            souvenirs = getattr(memoire, "souvenirs", None) or []
            tick = int(getattr(etat, "tick_absolu", 0))
            fenetre = float(getattr(memoire, "fenetre_fraicheur", 1000)) or 1000.0

            position = None
            env = getattr(etat, "env", None)
            if env is not None:
                try:
                    position = tuple(int(v) for v in env.unwrapped.agent_pos)
                except Exception:
                    position = None

            resultat = {
                "densite_souvenirs": min(1.0, len(souvenirs) / float(capacite_reference)),
                "couverture_carte": min(
                    1.0, len(getattr(etat, "positions_visitees_episode", ()) or ()) / 50.0
                ),
            }

            for cle_type, prefixe in (("FOOD", "food"), ("WATER", "water"), ("PORTE", "porte")):
                meilleur_d, meilleure_f = 0.0, 0.0
                for souvenir in souvenirs:
                    if not isinstance(souvenir, dict):
                        continue
                    if souvenir.get("type") != cle_type:
                        continue
                    # Clé 'pos' — c'est le format réel écrit par
                    # MemoireEpisodiqueSpatiale.enregistrer_evenement :
                    # {'pos': position, 'type': type_evenement, 'tick': tick_absolu}
                    pos = souvenir.get("pos")
                    age = tick - int(souvenir.get("tick", tick))
                    fraicheur = max(0.0, 1.0 - (age / fenetre))
                    if position is not None and pos is not None:
                        d = abs(pos[0] - position[0]) + abs(pos[1] - position[1])
                        proximite = max(0.0, 1.0 - (d / distance_reference))
                    else:
                        proximite = 0.0
                    if proximite >= meilleur_d:
                        meilleur_d, meilleure_f = proximite, fraicheur
                resultat[f"distance_{prefixe}"] = meilleur_d
                resultat[f"fraicheur_{prefixe}"] = meilleure_f

            return resultat
        except Exception:
            return None  # jamais d'exception vers le plug : perception neutre

    return _lire
