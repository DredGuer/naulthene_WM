# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — LE SPECTATEUR-PILOTE : faire vivre un VRAI `.brain` et l'afficher (étape 1).

    PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d \\
        --source cerveau --brain brains/<campagne>/<cerveau>.brain

`jouer_cerveau` charge un `.brain` EXISTANT (`PersistanceAnatomique.charger_ou_naitre`), ouvre la
journée (`demarrer_journee`), attache le `Rapporteur` (tâche 7), publie la structure une fois puis
une trame d'activité par période de `hz`, et rend la main en renvoyant l'EMPREINTE du fichier
avant/après. C'est le pattern de `lancer_arene.py` (observer un cerveau qui vit), transposé sur la
télémétrie 3D au lieu de pygame.

⚠️ CE MODULE EST LE SEUL DU CHANTIER QUI *PILOTE* UN CERVEAU (le rapporteur, lui, ne fait que
regarder des `forward`). Sa garantie n'est donc pas une propriété du code qu'il lit, c'est une
propriété de ce qu'il APPELLE — et elle est énoncée ci-dessous dans les termes exacts, parce
qu'une garantie approximative est une garantie fausse.

═══ LA GARANTIE EXACTE — ET CE QU'IL NE FAUT PAS ÉCRIRE ═══

**Le FICHIER `.brain` n'est jamais touché.** Ce module n'appelle jamais `executer_nuit` (la nuit :
`apprendre_journee`, `rever`, `cycle_sommeil`, la neurogenèse) ni `PersistanceAnatomique.
sauvegarder` : rien n'ouvre le `.brain` en écriture, donc l'octet sur le disque ne peut pas
changer. C'est vérifiable et vérifié — SHA-256 avant/après **et** liste du dossier (un `.tmp` de
`sauvegarder`, qui en crée un avant son `os.replace`, serait vu) :
`tests/test_cerveau_3d.py::TestSpectateurLectureSeule`.

⚠️ **Ne jamais écrire « aucun poids n'est modifié » ici.** C'est faux, mesuré, et le dépôt a déjà
corrigé cette formulation dans deux docstrings (`lancer_arene.py` et `irm_cerveau.py`, registre
DOC-02, 10/09/2026). `traiter_tick` déclenche la LTP par pic de dopamine :
`etat.agent.fortifier_synapses` écrit **EN PLACE, sous `no_grad`, dans `base_weight` ET
`myeline_M`**, sans `backward()` — et `eval()` ne l'arrête pas. Cette écriture est
**numériquement nulle** pour un `.brain` sauvegardé après une nuit (la trace d'éligibilité gravée
est remise à zéro par `cycle_sommeil`), mais **PAS** pour un `.brain` sauvegardé en pleine journée
(micro-sieste de la Cuve). Elle reste **en mémoire** : aucune sauvegarde n'étant appelée, elle ne
repart jamais sur le disque. C'est précisément ce que l'empreinte renvoyée atteste.

⚠️ `etat.agent.eval()` est appelé — mais APRÈS `demarrer_journee`, jamais avant : `demarrer_journee`
se termine par `etat.agent.train()` (`noyau.py` l.8951). L'ordre inverse laisserait le cerveau en
mode entraînement, où `NaultheneLinearSynaptique.forward` remet à jour `myeline_M` et
`trace_activation` à chaque passage (`lancer_arene.py` porte le même commentaire).

═══ LA SECONDE PREUVE §10 : « LE CERVEAU OBSERVÉ NE DÉRIVE PAS » ═══

L'empreinte SHA-256 prouve le **FICHIER** ; elle ne dit **rien** de la mémoire, où `traiter_tick`
grave la LTP. La spec §10 exige donc une seconde preuve, et ce module la REND : les normes L2 de
`base_weight` et de `myeline_M`, relevées avant la première trame et après le dernier tick
(clés `*_norme_avant` / `*_norme_apres` du dictionnaire de retour).

**Pourquoi les deux sont EXACTEMENT égales sur un `.brain` sauvegardé après une nuit** — et non
« à peu près » : la LTP par pic vaut

    myeline_M += trace_activation × pic          (Étape 1 de `fortification_dopaminergique`)
    base_weight += annexe_weight × clamp(trace_activation × pic, 0, 1)

et `cycle_sommeil` remet à zéro **les deux** facteurs, `annexe_weight.zero_()` **et**
`trace_activation.zero_()` (`noyau.py` l.365-366, en fin de nuit, après consolidation). Un produit
dont un facteur est nul vaut zéro **au bit** : `myeline_M += 0` et `base_weight += 0` sont des
non-opérations exactes, pas des non-opérations approchées. **Mesuré** sur
`brains/08092026_sci01_balayage_K/K4_NU/K4_NU_g11.brain` (bus 145, jour 1500) : `base_weight`
16,750667240914318 et `myeline_M` 1,6425963671801869 — **identiques au bit** avant/après 300 ticks,
pour une `trace_activation` mesurée à `0,0` exactement.

⚠️ **Ce ne serait PAS nul sur un `.brain` sauvegardé en pleine journée** (micro-sieste de la
Cuve) : `trace_activation` y est non nulle et `annexe_weight` porte le gradient du jour — la même
boucle de ticks graverait alors une dérive RÉELLE. Elle resterait **en mémoire** (aucune sauvegarde
n'étant appelée : c'est ce que l'empreinte atteste), mais l'égalité exacte des normes, elle,
tomberait. Une dérive affichée par ce module n'est donc pas un défaut du spectateur : elle dit
l'état du `.brain` qu'on lui a donné à observer. C'est pour cette raison que la CLI **affiche** les
normes sans en faire un critère de sortie — un `.brain` de pleine journée doit pouvoir être observé
sans être déclaré en échec.

═══ POURQUOI `demarrer_journee` EST RAPPELÉ TOUS LES `ticks_par_jour` TICKS ═══

Mesuré, deux fois 2400 ticks sur un cerveau neuf (`bus = 16`, `NAULTHENE_DEVICE=cpu`), pic RSS
relevé tous les 400 ticks :

| Ticks | sans ménage | avec ménage |
|---|---|---|
| (départ) | 323 Mo | 322 Mo |
| 400  | 361 Mo | 361 Mo |
| 800  | 396 Mo | 361 Mo |
| 1200 | 430 Mo | 361 Mo |
| 1600 | 464 Mo | 361 Mo |
| 2000 | 498 Mo | 361 Mo |
| 2400 | 531 Mo | 361 Mo |

Sans ménage : **≈ 88 Ko par tick** (`memoire_moyen_terme`, `jepa_losses`, `recompenses_journee`
gagnent une entrée par tick — 2400 entrées à 2400 ticks). À la cadence réelle mesurée du `.brain`
de campagne observé (~440 ticks/s), **cinq minutes d'observation exigeraient ~11 Go** : le
spectateur mourrait avant l'auteur. `demarrer_journee` vide ces buffers de journée — c'est le
« ménage mémoire » de `lancer_arene.py`, exactement la même boucle et la même raison. Le
`eval()` qui suit est obligatoire (voir ci-dessus) : `demarrer_journee` vient de rappeler
`train()`.

⚠️ Ce ménage incrémente `etat.jour` : sur un cerveau observé, le « jour » affiché avance au
rythme des ticks (une journée subjective toutes les `ticks_par_jour` ticks), il ne mesure plus des
nuits. Aucune nuit n'est jouée — c'est la contrepartie assumée et affichée.

═══ LA CADENCE : LE TICK N'EST JAMAIS RALENTI PAR L'AFFICHAGE ═══

La boucle ne dort JAMAIS. Elle enchaîne `traiter_tick` aussi vite que le cerveau le peut ; c'est le
`Rapporteur` qui throttle la PUBLICATION (`publier_activite` renvoie `None` tant que la période
`1/hz` n'est pas écoulée). Un cerveau qui vit à 400 ticks/s et un écran à 15 Hz ne sont pas la
même horloge, et l'observation ne doit pas ralentir le cerveau observé.

═══ CE QUI EST PUBLIÉ, ET CE QUI NE L'EST PAS ═══

- `structure` : une fois, avant la première trame d'activité (la page doit connaître la scène) ;
- `activite` : la capture du dernier tick, au plus `hz` fois par seconde ;
- `evenement` : **AUCUN**. Le canal d'actualité de la page reste donc sur « flux connecté ». Les
  chocs dopaminergiques (`poids_evenement`) et la promotion de niveau sont le sujet de la tâche 9
  (le drapeau `--telemetrie-3d` du noyau, à côté de `fortifier_synapses`) : les émettre ici
  demanderait de dériver un fait daté du noyau depuis l'extérieur du tick, ce qui n'a pas été
  spécifié ni mesuré. Écarté, et DIT plutôt que bricolé.

⚠️ Le spectateur n'ENSEIGNE rien : `traiter_tick` est appelé sans `obs_auditive` ni
`formants_cibles` (l'Arène, elle, injecte la leçon vocale courante). L'oreille du cerveau observé
est donc au silence et sa bouche sans consigne — `porte_auditive` s'affiche à zéro exact et le
rapporteur déclare `generateur_attente_audio` non écrite. Un spectateur regarde, il ne fait pas
classe.

Voir `docs/ameliorations/PLAN_VIS-01_cerveau_3d.md` (tâche 8) et
`docs/ameliorations/CHANTIER_VIS-01_cerveau_3d_irm_vivante.md` §4 (les trois trames).
"""
from __future__ import annotations

import hashlib
import math
import os
import time

from naulthene.cerveau import noyau
from naulthene.cerveau.persistance import PersistanceAnatomique
from naulthene.instruments.cerveau_3d.rapporteur import Rapporteur

# Une journée subjective du cerveau observé (`ticks_par_jour`, `noyau.py`). Lue sur le noyau, jamais
# recopiée : c'est la même constante que celle du cursus, donc le même « ménage ».
TICKS_PAR_JOURNEE = int(noyau.ticks_par_jour)


def _sha256(chemin) -> str:
    """L'empreinte du fichier, relue sur le disque — jamais une valeur mémorisée."""
    empreinte = hashlib.sha256()
    with open(chemin, "rb") as fichier:
        for bloc in iter(lambda: fichier.read(1024 * 1024), b""):
            empreinte.update(bloc)
    return empreinte.hexdigest()


def _normes_poids(agent) -> dict:
    """Les normes L2 de `base_weight` et de `myeline_M` de TOUTES les couches plastiques.

    C'est la preuve §10 « le cerveau observé ne dérive pas », en MÉMOIRE — l'empreinte SHA-256,
    elle, ne parle que du FICHIER. Les deux sont nécessaires et aucune ne remplace l'autre :
    `traiter_tick` → `fortifier_synapses` écrit **en place** (`noyau.py`, section 1) sans jamais
    toucher le disque, donc un spectateur qui dériverait passerait le test d'empreinte les doigts
    dans le nez. Voir la docstring du module pour la raison EXACTE pour laquelle ces normes sont
    égales **au bit** sur un `.brain` sauvegardé après une nuit, et ne le seraient pas sur un
    `.brain` sauvegardé en pleine journée.

    UNE norme par grandeur, sur l'ENSEMBLE des couches (racine de la somme des carrés) : douze
    valeurs séparées seraient douze assertions à maintenir, et un maximum élément par élément
    devrait être comparé à une tolérance — or c'est précisément la tolérance qu'on ne veut pas ici.

    Lecture seule, sous `detach()`, sans aucun `forward` : mesurer ne modifie rien.

    Sélection des couches : celles qui portent `base_weight` ET `myeline_M` (les
    `NaultheneLinearSynaptique`), comme `rapporteur.py` l.174 sélectionne les couches
    instrumentées. Un module qui ne porterait qu'un des deux est ignoré — mesurer la moitié d'un
    couple ne prouve rien sur le couple.
    """
    carres = {"base_weight": 0.0, "myeline_M": 0.0}
    for _, module in agent.named_modules():
        base = getattr(module, "base_weight", None)
        myeline = getattr(module, "myeline_M", None)
        if base is None or myeline is None:
            continue
        carres["base_weight"] += float(base.detach().float().pow(2).sum())
        carres["myeline_M"] += float(myeline.detach().float().pow(2).sum())
    return {nom: math.sqrt(total) for nom, total in carres.items()}


def _meta_etat(etat) -> dict:
    """Les métadonnées d'état des deux trames — miroir de `_meta_telemetrie` du plan (tâche 9).

    `niveau` porte TOUJOURS son `env_id` (règle du 07/09 : un niveau sans son `env_id` est
    ambigu — `niveau_actuel` est un INDEX du `PROGRAMME`, et deux `.brain` peuvent le partager
    avec des cartes différentes). `affiche` est la forme que la page sait rendre
    (`trame.niveau.affiche`, spec §4 : `4/15`), calculée comme le bilan console du noyau
    (`niveau_actuel + 1` sur `len(PROGRAMME)`) — jamais un `15` écrit en dur.
    """
    index = int(getattr(etat, "niveau_actuel", 0))
    return {"jour": int(etat.jour),
            "tick": int(etat.tick_absolu),
            "tick_absolu": int(etat.tick_absolu),
            "dim_bus": int(etat.agent.dim_bus),
            "niveau": {"index": index,
                       "affiche": f"{index + 1}/{len(noyau.PROGRAMME)}",
                       "env_id": getattr(etat, "env_id", "?")}}


def _meta_activite(etat, infos) -> dict:
    """Les métadonnées de la trame d'activité : l'état, plus ce que SEUL le tick connaît.

    ⚠️ `dopamine`, `faim` et l'action jouée ne sont PAS lisibles sur l'agent (ils vivent dans
    `etat`, et l'action n'existe que le temps du tick) : s'ils ne passent pas par `meta`, la clé
    est ABSENTE de la trame et la page retombe sur son défaut d'affichage — « dopamine 0,000 » sur
    un cerveau qui en a 7. C'est le ruling de la tâche : le rapporteur ne peut pas les inventer,
    donc c'est le spectateur qui les lui donne.

    Les valeurs sont prises dans le RETOUR de `traiter_tick` (`infos_internes`) et non relues sur
    `etat` : ce dictionnaire est l'état tel que le tick l'a laissé, et le noyau le remplit
    lui-même (`noyau.py`, fin de `traiter_tick`). Le repli `.get(clé, …)` sur `etat` n'invente
    rien — il lit la même source — il n'existe que pour un noyau qui n'aurait pas encore ces clés.
    L'ACTION, elle, n'a pas de repli : `etat` ne la porte pas, donc une action absente reste
    ABSENTE (la page affiche « — », `app.js`) au lieu d'un zéro qui serait une action inventée
    (`0` = `Actions.left`, une action bien réelle).

    ⚠️ `force_planification` n'est PAS passée, et ce n'est pas un oubli : le repli du rapporteur
    sur `agent.acceptation()` est ici **exact**, mesuré. `acceptation() = envie_de_vivre ×
    force_planification_vecue()`, et `envie_de_vivre` n'est révisée que par
    `reviser_envie_de_vivre`, appelée UNIQUEMENT dans `executer_nuit` (`noyau.py` l.10965, sous
    l'en-tête « une fois par nuit ») — une fonction que ce module n'appelle jamais. L'acceptation
    est donc FIGÉE pendant toute l'observation, à la valeur que `demarrer_journee` vient de poser
    dans `force_planification_jour`. Protocole : 1000 ticks sur deux cerveaux (neuf `bus = 16`, et
    `K4_NU_g11.brain` `bus = 145`, jour 1500), `|force_planification_jour − acceptation()|` relevé
    tous les 200 ticks ⇒ **écart maximal 0,000000** (0,576986 = 0,576986 sur le cerveau de
    campagne). Passer la valeur en plus serait donc un doublon qui ne change rien à l'écran —
    écarté, avec la mesure, plutôt que par confiance dans un commentaire.
    """
    internes = (infos or {}).get("infos_internes") or {}
    meta = _meta_etat(etat)
    meta["dopamine"] = float(internes.get("dopamine", etat.teneur_dopamine))
    meta["faim"] = float(internes.get("faim", 1.0 - etat.moteur_bio.satiete))
    action = (infos or {}).get("action")
    if action is not None:            # `0` (Actions.left) est une action, pas une absence
        meta["action"] = int(action)
    return meta


def jouer_cerveau(bus, fichier_brain, arret=None, duree=None, hz=15.0) -> dict:
    """Fait vivre le `.brain` `fichier_brain` et publie ses trames dans `bus`. BLOQUANT.

    - `bus` : un `BusTrames` (`telemetrie`) — ou `None` pour produire les trames sans les publier
      (contrat accepté par le rapporteur) ;
    - `arret` : objet à `is_set()` (`threading.Event`), testé EN TÊTE de tour ; `None` = s'arrête
      uniquement sur `duree` ;
    - `duree` : durée d'OBSERVATION en secondes (`None` = jusqu'à `arret`) ;
    - `hz` : cadence de PUBLICATION (le tick, lui, n'est jamais ralenti — voir la docstring du
      module).

    Renvoie un dictionnaire qui porte les DEUX preuves de lecture seule de la spec §10 :

    - le FICHIER — contrat minimal `{"tick_absolu", "jour", "brain_sha256_avant",
      "brain_sha256_apres"}`, plus `ticks_observes` (les ticks joués par CETTE session) et
      `menages` (les ménages de journée effectués — ce que le test de fuite mémoire observe) ;
    - la MÉMOIRE — `base_weight_norme_avant/apres` et `myeline_M_norme_avant/apres` : les normes L2
      relevées au DÉBUT de l'observation (cerveau chargé, `demarrer_journee` appelé et `eval()`
      posé — l'instant exact où la session prend la main) et à la FIN du dernier tick observé.
      « Le cerveau observé ne dérive pas » se lit LÀ, jamais dans l'empreinte : `fortifier_synapses`
      écrit en mémoire sans salir le disque.

    ⚠️ Ces normes sont égales **au bit** sur un `.brain` sauvegardé après une nuit (mesuré :
    16,750667240914318 et 1,6425963671801869 sur `K4_NU_g11.brain`, inchangées sur 300 ticks) et
    peuvent ne PAS l'être sur un `.brain` sauvegardé en pleine journée — la docstring du module en
    donne la raison exacte. Un écart n'est donc pas un défaut du spectateur : il dit l'état du
    `.brain` qu'on lui a donné à observer.

    ⚠️ `tick_absolu` est le compteur de vie du CERVEAU (restauré du `.brain`, il survit aux
    résurrections : 537 329 au chargement de `K4_NU_g11.brain`) ; `ticks_observes` est celui de la
    SESSION. Les deux ne coïncident que sur un cerveau né à l'instant, et les confondre fait
    annoncer « 538 834 ticks observés » après quatre secondes d'observation — mesuré, c'est ce que
    le premier verdict imprimé disait.

    ⚠️ Un `.brain` ABSENT est REFUSÉ (`FileNotFoundError`), jamais créé :
    `PersistanceAnatomique.charger_ou_naitre()` sait faire naître un agent neuf quand le fichier
    manque. Pour un spectateur, ce serait une création silencieuse — le viewer afficherait un
    cerveau de démonstration en le présentant comme celui qu'on lui a demandé d'observer. Un
    spectateur ne crée jamais de fichier.
    """
    chemin = os.fspath(fichier_brain)
    if not os.path.isfile(chemin):
        raise FileNotFoundError(
            f"aucun `.brain` à observer : {chemin} est introuvable. Un spectateur ne fait JAMAIS "
            f"naître de cerveau (la persistance en créerait un en silence, et vous regarderiez un "
            f"cerveau neuf en croyant regarder le vôtre) : lancez d'abord un run qui le fait "
            f"vivre, puis observez le fichier qu'il a écrit.")

    sha_avant = _sha256(chemin)
    etat = PersistanceAnatomique(chemin).charger_ou_naitre()
    noyau.demarrer_journee(etat)          # ⚠️ AVANT `eval()` : il finit par `agent.train()`
    etat.agent.eval()
    # Le point de DÉPART de la preuve §10 : l'état exact où l'observation commence. Relevé ici, et
    # pas juste après le chargement, parce que c'est ici que la session prend la main — mesurer plus
    # tôt attribuerait à l'observation ce que la mise en route aurait fait.
    normes_avant = _normes_poids(etat.agent)

    rapporteur = Rapporteur(bus, hz=hz)
    rapporteur.attacher(etat.agent)
    ticks, menages, observes = 0, 0, 0
    try:
        # La scène d'abord : la page doit connaître les 12 plaques avant la première image.
        rapporteur.publier_structure(etat.agent, _meta_etat(etat))
        debut = time.monotonic()
        while True:
            if arret is not None and arret.is_set():
                break
            if duree is not None and time.monotonic() - debut >= float(duree):
                break
            # ⚠️ OBLIGATOIRE avant chaque tick : `nouveau_tick()` ouvre la fenêtre de capture.
            # Sans lui, les passages hors tick (rejeu nocturne, tick précédent) seraient pris pour
            # le tick courant — la page afficherait un état qui n'a pas été vécu.
            rapporteur.nouveau_tick()
            infos = noyau.traiter_tick(etat)
            # Le throttle est DANS le rapporteur : à 400 ticks/s et 15 Hz, une trame sur ~27.
            rapporteur.publier_activite(etat.agent, _meta_activite(etat, infos))
            ticks += 1
            observes += 1
            if ticks >= TICKS_PAR_JOURNEE:
                # Ménage mesuré (tableau de la docstring du module) : sans lui, ~88 Ko par tick.
                noyau.demarrer_journee(etat)
                etat.agent.eval()          # `demarrer_journee` vient de rappeler `train()`
                ticks, menages = 0, menages + 1
        # Le point d'ARRIVÉE, relevé AVANT le démontage : `detacher()` et `env.close()` ne touchent
        # aucun poids, mais la mesure doit porter sur le dernier tick OBSERVÉ, pas sur une sortie.
        normes_apres = _normes_poids(etat.agent)
    finally:
        rapporteur.detacher()
        etat.env.close()

    return {"tick_absolu": int(etat.tick_absolu),
            "ticks_observes": observes,
            "jour": int(etat.jour),
            "brain_sha256_avant": sha_avant,
            "brain_sha256_apres": _sha256(chemin),
            "menages": menages,
            # §10 — « le cerveau observé ne dérive pas » : mêmes bornes temporelles que l'empreinte.
            "base_weight_norme_avant": normes_avant["base_weight"],
            "base_weight_norme_apres": normes_apres["base_weight"],
            "myeline_M_norme_avant": normes_avant["myeline_M"],
            "myeline_M_norme_apres": normes_apres["myeline_M"]}
