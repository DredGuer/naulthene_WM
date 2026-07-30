"""Plug HTTP (v28.0, expérimental) — backend générique JSON/HTTP, sans logique propre
à un fournisseur.

Sérialise `RequeteC3` en JSON (`latent` en liste de floats) vers `url_endpoint`, attend
`{"preferences": [...], "confiance": <float>}` en retour. C'est le socle sur lequel se
brancheront plus tard des services concrets (Ollama, une base vectorielle, une
recherche web) sans jamais toucher au noyau cognitif — seule l'URL/le format du service
distant change, pas le contrat.

Reprend la LEÇON de `naulthene.audio.professeur_gemma` (aucun health-check, aucun cache
d'indisponibilité, jusqu'à 60s de timeout payés À CHAQUE appel) sans en répéter le
défaut : `est_disponible()` met en cache le résultat de son dernier ping
(`INTERVALLE_PING`) au lieu d'en émettre un par tick, et `TIMEOUT_C3` reste court —
un service absent ne doit jamais coûter cher dans une boucle 800 ticks × 900 jours.
"""

import time

import numpy as np
import requests

from naulthene.exocortex.port_c3 import PlugC3, RequeteC3, ReponseC3

TIMEOUT_C3 = 2.0            # secondes — volontairement court, voir docstring
INTERVALLE_PING = 5.0       # secondes entre deux vérifications de disponibilité


class PlugHTTP(PlugC3):
    def __init__(self, url_endpoint: str, nom: str = "plug_http", timeout: float = TIMEOUT_C3):
        self.nom = nom
        self.url_endpoint = url_endpoint.rstrip("/")
        self.timeout = timeout
        self._dernier_ping = 0.0
        self._disponible_cache = False

    def est_disponible(self) -> bool:
        maintenant = time.monotonic()
        if maintenant - self._dernier_ping < INTERVALLE_PING:
            return self._disponible_cache
        self._dernier_ping = maintenant
        try:
            reponse = requests.get(f"{self.url_endpoint}/sante", timeout=self.timeout)
            self._disponible_cache = reponse.ok
        except requests.RequestException:
            self._disponible_cache = False
        return self._disponible_cache

    def interroger(self, requete: RequeteC3) -> ReponseC3 | None:
        charge_utile = {
            "latent": requete.latent.astype(np.float32).tolist(),
            "num_actions": requete.num_actions,
            "indecision_c2": requete.indecision_c2,
            "erreur_jepa": requete.erreur_jepa,
            "palier_vocal": requete.palier_vocal,
            "mot_frontal": requete.mot_frontal,
        }
        reponse = requests.post(f"{self.url_endpoint}/interroger", json=charge_utile,
                                 timeout=self.timeout)
        reponse.raise_for_status()
        donnees = reponse.json()
        preferences = np.asarray(donnees["preferences"], dtype=np.float32)
        if preferences.shape[0] != requete.num_actions:
            # Contrat violé côté service distant — on ne fait jamais confiance à une
            # forme inattendue plutôt que de risquer un crash plus loin dans le rollout.
            return None
        confiance = float(np.clip(donnees.get("confiance", 0.0), 0.0, 1.0))
        return ReponseC3(preferences=preferences, confiance=confiance, origine=self.nom)
