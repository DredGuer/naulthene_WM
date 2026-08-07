"""
Persistance Anatomique (V21.0, expérimental) — Cristallisation du cerveau Naulthène.

Ce module ne vit que dans l'écosystème local de test (`agi_local_test.py` +
`daemon_cerveau.py` + `client_corps.py`), pas encore porté sur `agi_google_colab.py`.
Voir CLAUDE.md (section "Variante Locale de Test") et readme.md (section "Nouveautés
v21.0 — Le Cerveau Persistant en Cuve") pour le contexte narratif complet.

Contrairement au pseudo-code initial (qui ne sauvait que dopamine/satiété/hydratation/
stimulation/souvenirs), le VRAI cerveau porte plus d'état qu'un simple pseudo-code
minimal ne le laissait supposer :

  - la dimension du bus (`dim_bus`), qui grandit par neurogenèse et doit être connue
    AVANT de reconstruire l'agent et charger ses poids ;
  - l'optimiseur Adam, recréé par `declencher_neurogenese()` — ses moments doivent
    être sauvés APRÈS la nuit, pas avant, sinon on perd la dynamique d'apprentissage ;
  - le curriculum (niveau, palier visé, victoires consécutives) et le thermostat de
    neurogenèse (seuils, cooldown) — sans eux, la résurrection redémarrerait un cursus
    déjà entamé depuis zéro ;
  - la mémoire épisodique spatiale et le compteur `tick_absolu` dont dépend la
    fraîcheur des souvenirs.

Une seule fonction d'entrée côté appelant : `charger_ou_naitre()`, qui retourne un
`EtatCognitif` prêt à l'emploi que ce soit une naissance ou une résurrection.
"""

import os
import torch

from naulthene.cerveau.noyau import (
    AGI_Naulthene, EtatCognitif, DIM_VISUELLE, BUS_REFERENCE_INITIAL,
    PROGRAMME, DEVICE, creer_env, DetecteurJalonsDoorKey, GestionnaireCursusAbnegation,
    NUM_ACTIONS_BASE, NUM_ACTIONS_AVEC_C3, DIM_VECTEUR_BIO,
    DIM_TOUCHER, DIM_CHIMIE, DIM_EXO,
)


# v28.0 (expérimental) — Port Exocortex C3 : couches dont la FORME change avec le
# passage de num_actions=7 à 8. Pour chaque couche, préciser si la dimension
# supplémentaire touche les LIGNES (sortie, ex: tete_motrice) ou les COLONNES (entrée,
# ex: generateur_attente — actions_onehot est concaténé en tête, voir _predire_bus).
# `offset_colonne` : position du bloc "actions_onehot" dans la concaténation d'entrée
# (0 pour generateur_attente/generateur_attente_audio, qui concatènent
# [actions_onehot, pensee] — voir _predire_bus/_predire_bus_audio).
_COUCHES_ACTION_SUPPLEMENTAIRE = {
    'tete_motrice': {'axe': 'sortie'},
    'generateur_attente': {'axe': 'entree', 'offset_colonne': 0},
    'generateur_attente_audio': {'axe': 'entree', 'offset_colonne': 0},
}
_BUFFERS_NAULTHENE_LINEAR = (
    'base_weight', 'myeline_M', 'trace_activation', 'myeline_cumul', 'cristallisee', 'annexe_weight',
)


def _greffer_action_supplementaire(state_dict, agent):
    """Recopie chaque tenseur affecté par NUM_ACTIONS_BASE=7 → NUM_ACTIONS_AVEC_C3=8
    dans un tenseur de la forme attendue par `agent` (déjà instancié à 8 actions),
    plutôt que de laisser `load_state_dict(strict=False)` échouer sur un mismatch de
    forme (il ne gère que les clés ABSENTES, jamais un mismatch sur une clé présente
    des deux côtés — voir le filtre integrateur_bio ci-dessus pour le même problème
    déjà rencontré une fois). Un .brain qui a déjà 8 actions (sauvegardé depuis v28.0)
    traverse cette fonction sans aucune modification (les formes correspondent déjà)."""
    resultat = dict(state_dict)
    for nom_couche, regle in _COUCHES_ACTION_SUPPLEMENTAIRE.items():
        prefixe = f"{nom_couche}."
        cle_base = f"{prefixe}base_weight"
        ancien_base = state_dict.get(cle_base)
        if ancien_base is None:
            continue  # couche absente du checkpoint (greffe déjà gérée par strict=False)
        couche_agent = getattr(agent, nom_couche)
        forme_attendue = couche_agent.base_weight.shape
        if tuple(ancien_base.shape) == tuple(forme_attendue):
            continue  # déjà à la bonne taille (checkpoint post-v28.0), rien à faire

        axe = regle['axe']
        for nom_buffer in _BUFFERS_NAULTHENE_LINEAR:
            cle = f"{prefixe}{nom_buffer}"
            ancien = state_dict.get(cle)
            if ancien is None:
                continue
            nouveau = getattr(couche_agent, nom_buffer).detach().clone()
            if nom_buffer == 'annexe_weight':
                # Repart de zéro (comme cycle_sommeil le fait déjà chaque nuit) plutôt
                # que de recopier un annexe_weight de la veille — l'ancien annexe_weight
                # a la mauvaise forme et n'a de toute façon de sens que pour la journée
                # en cours, jamais rechargé tel quel entre deux sessions.
                nouveau.zero_()
            elif axe == 'sortie':
                nouveau[:ancien.shape[0], :] = ancien
            else:  # axe == 'entree' : le bloc actions_onehot est en tête de la concaténation
                # La concaténation est [actions_onehot(A), pensee(dim_bus)] (voir
                # _predire_bus/_predire_bus_audio) : seule la largeur du bloc
                # actions_onehot change (7→8), le bloc pensee est recopié tel quel
                # juste après, à son nouvel offset.
                largeur_actions_ancienne = NUM_ACTIONS_BASE
                nouveau[:, :largeur_actions_ancienne] = ancien[:, :largeur_actions_ancienne]
                nouveau[:, NUM_ACTIONS_AVEC_C3:] = ancien[:, largeur_actions_ancienne:]
            resultat[cle] = nouveau
        print(f"   🖐️  {nom_couche} greffé(e) de {NUM_ACTIONS_BASE} à {NUM_ACTIONS_AVEC_C3} actions "
              f"(ACTION_DEMANDER/Port Exocortex C3, v28.0) — acquis existants préservés.")

    # actions_eye est une simple matrice identité (register_buffer, jamais un poids
    # appris) — pas de recopie partielle à faire, juste la remplacer par l'identité de
    # la bonne taille si le checkpoint est encore à l'ancienne forme. La retirer du
    # state_dict la laisse à sa valeur d'__init__ (déjà torch.eye(NUM_ACTIONS_AVEC_C3)),
    # ce qui est exactement ce qu'on veut.
    ancien_actions_eye = resultat.get('actions_eye')
    if ancien_actions_eye is not None and tuple(ancien_actions_eye.shape) != tuple(agent.actions_eye.shape):
        del resultat['actions_eye']

    return resultat


def _greffer_vecteur_bio_etendu(state_dict, agent):
    """v29.0 (expérimental) — Greffe des 3 sens faibles à moyens (toucher, odorat, goût)
    sur `integrateur_bio`, par RECOPIE PARTIELLE plutôt que par exclusion.

    `DIM_VECTEUR_BIO` passe de 16 à 24 dims (voir noyau.py) : l'entrée de `integrateur_bio`
    passe donc de `dim_bus + 16` à `dim_bus + 24` colonnes. Le filtre historique de
    `charger_ou_naitre` traitait ce cas en EXCLUANT la couche — elle renaissait à neuf,
    perdant tout l'apprentissage de l'intégration viscérale et vocale accumulé (le même
    symptôme exact que le bug v24.0-fix4 documenté plus bas : bouche silencieuse dans
    l'Arène). Inacceptable ici, où un `.brain` peut porter 1000 jours de vécu.

    La concaténation d'entrée est `[pensee(dim_bus), vecteur_bio(DIM_VECTEUR_BIO)]` (voir
    `AGI_Naulthene.integrer_bio`), et les 8 nouvelles dims sont ajoutées EN QUEUE du
    vecteur bio (contrat posé par `BiologicalHomeostasisEngine.obtenir_vecteur_bio` et
    `bus_sensoriel.BusSensoriel.interpreter`). La recopie est donc directe : les
    `dim_bus + 16` premières colonnes gardent leurs poids appris, les 8 dernières
    conservent leur initialisation Xavier atténuée — exactement la sémantique de
    `NaultheneLinearSynaptique.agrandir()`. L'agent se réveille avec tous ses acquis et
    découvre simplement qu'il a désormais un toucher, un odorat et un goût, encore muets.

    Un `.brain` déjà à 24 dims (sauvegardé depuis la v29.0) traverse cette fonction sans
    aucune modification. Un `.brain` dont la largeur est INFÉRIEURE à celle attendue mais
    incohérente avec `dim_bus + 16` (cas jamais produit par une version réelle du projet)
    est laissé tel quel, pour retomber sur le filtre d'exclusion existant plutôt que de
    recopier des poids à un offset faux."""
    prefixe = "integrateur_bio."
    ancien_base = state_dict.get(f"{prefixe}base_weight")
    if ancien_base is None:
        return state_dict, False

    forme_attendue = agent.integrateur_bio.base_weight.shape
    if tuple(ancien_base.shape) == tuple(forme_attendue):
        return state_dict, False  # déjà à la bonne taille, rien à faire

    # Largeur d'entrée réellement portée par le checkpoint, et celle attendue. On ne
    # greffe QUE le cas "même dim_bus, vecteur bio plus court" — tout autre écart
    # (dim_bus différent, largeur incohérente) reste géré par le filtre d'exclusion.
    largeur_checkpoint = int(ancien_base.shape[1])
    largeur_attendue = int(forme_attendue[1])
    dim_bus_attendue = largeur_attendue - DIM_VECTEUR_BIO
    if ancien_base.shape[0] != forme_attendue[0] or largeur_checkpoint >= largeur_attendue:
        return state_dict, False
    if largeur_checkpoint <= dim_bus_attendue:
        return state_dict, False  # pas de segment bio identifiable, on ne devine pas

    resultat = dict(state_dict)
    couche_agent = agent.integrateur_bio
    for nom_buffer in _BUFFERS_NAULTHENE_LINEAR:
        cle = f"{prefixe}{nom_buffer}"
        ancien = state_dict.get(cle)
        if ancien is None:
            continue
        nouveau = getattr(couche_agent, nom_buffer).detach().clone()
        if nom_buffer == 'annexe_weight':
            # Même raison que dans _greffer_action_supplementaire : l'annexe n'a de sens
            # que pour la journée en cours, cycle_sommeil la remet à zéro chaque nuit.
            nouveau.zero_()
        else:
            nouveau[:, :largeur_checkpoint] = ancien
        resultat[cle] = nouveau

    nb_nouvelles = largeur_attendue - largeur_checkpoint
    # Libellé déduit de la LARGEUR BIO réellement portée par le checkpoint, et non du
    # nombre de dimensions ajoutées : DIM_TOUCHER+DIM_CHIMIE et DIM_EXO valent tous deux
    # 8, donc `nb_nouvelles == 8` est ambigu (un .brain pré-v29 comme un .brain v29
    # gagnent 8 dims, mais pas les mêmes). La largeur d'origine, elle, est sans ambiguïté.
    # v32.0 — la déduction se fait sur la largeur bio d'ORIGINE (16 pré-v29, 24 en v29.x,
    # 32 en v30/v31), chaque palier disant sans ambiguïté ce qui manque au checkpoint.
    # Les libellés se cumulent : un .brain pré-v29 chargé par un binaire v32 gagne d'un
    # coup les trois blocs, et doit le dire — c'est la seule trace console qu'aura
    # l'utilisateur de ce qui vient d'être greffé sur un cerveau de plusieurs centaines
    # de jours.
    largeur_bio_checkpoint = largeur_checkpoint - dim_bus_attendue
    acquis = []
    if largeur_bio_checkpoint <= 16:
        acquis.append("toucher/odorat/goût (v29.0)")
    if largeur_bio_checkpoint <= 16 + DIM_TOUCHER + DIM_CHIMIE:
        acquis.append("Exo-Sens (v30.0)")
    if largeur_bio_checkpoint <= 16 + DIM_TOUCHER + DIM_CHIMIE + DIM_EXO:
        acquis.append("clinotaxie olfactive (v32.0)")
    libelle = " + ".join(acquis) if acquis else "extension du vecteur bio"
    print(f"   👃 integrateur_bio greffé de {largeur_checkpoint} à {largeur_attendue} dims d'entrée "
          f"(+{nb_nouvelles} : {libelle}) — acquis existants préservés.")
    return resultat, True


class PersistanceAnatomique:
    """Cristallise et ressuscite l'état complet d'un `EtatCognitif` dans un fichier
    binaire `.brain` (torch.save/torch.load). Un seul fichier par cerveau — le port
    d'écoute de la Cuve n'a pas besoin d'être encodé dedans, c'est un détail du
    daemon, pas de l'anatomie de l'agent."""

    def __init__(self, fichier="brains/naulthene_v21.brain"):
        self.fichier = fichier

    def sauvegarder(self, etat):
        """Cristallise l'âme et le corps de l'agent sur le disque dur. Peut être
        appelée aussi bien après une nuit complète (cerveau reposé, optimiseur à jour)
        qu'après une micro-sieste (simple photographie de l'état courant, voir
        CuveDeMaintien) — dans les deux cas, l'état sauvé est cohérent et rechargeable
        tel quel."""
        checkpoint = {
            # --- 1. Structure (pour reconstruire la bonne taille de cerveau AVANT
            # load_state_dict — la neurogenèse fait grandir dim_bus au fil des jours) ---
            'dim_bus': etat.agent.dim_bus,

            # --- 2. Poids, traces de myéline/éligibilité et optimiseur ---
            'state_dict': etat.agent.state_dict(),
            'optimizer_state_dict': etat.agent.optimizer.state_dict(),

            # --- 3. Chimie viscérale (réservoir dopaminergique + moteur homéostatique) ---
            'teneur_dopamine': etat.teneur_dopamine,
            'plasticite_base': etat.plasticite_base,
            'satiete': etat.moteur_bio.satiete,
            'hydratation': etat.moteur_bio.hydratation,
            'stimulation': etat.moteur_bio.stimulation,
            'quete_active': etat.moteur_bio.quete_active,

            # --- 4. Souvenirs persistants (mémoire épisodique spatiale, v20.0) ---
            'souvenirs_spatiaux': etat.memoire_episodique_spatiale.souvenirs,

            # --- 5. Curriculum & progression ---
            'niveau_actuel': etat.niveau_actuel,
            # v35.0 — fenêtre glissante de promotion (voir _taux_maitrise_niveau).
            'historique_episodes_niveau': list(etat.historique_episodes_niveau),
            # v35.1 — filet de sécurité : jours consécutifs sans victoire sur le niveau.
            'jours_stagnation_niveau': etat.jours_stagnation_niveau,
            'victoires_consecutives': etat.victoires_consecutives,
            # v33.0-etape0.6 — chronologie des victoires. DOIT être persistée : c'est une
            # mesure de VIE (intervalles entre victoires sur des centaines de jours), pas
            # de journée. Sans ça, toute reprise de run remettrait les intervalles à zéro
            # et la question « hasard ou apprentissage ? » resterait sans réponse sur les
            # cerveaux qui ont justement le plus de vécu.
            'jour_derniere_victoire': etat.jour_derniere_victoire,
            'jours_depuis_victoire': etat.jours_depuis_victoire,
            'intervalles_victoires': etat.intervalles_victoires,
            'victoires_totales': etat.victoires_totales,
            # v33.0-etape0.6-fix1 : le contexte (niveau, palier) de la série courante.
            # Sans lui, une reprise de run reprendrait les intervalles d'un contexte
            # sans savoir duquel — et la première nuit les jetterait de toute façon,
            # `contexte_victoires=None` étant réinitialisé au contexte du moment.
            'contexte_victoires': etat.contexte_victoires,
            'intervalles_contexte_prec': etat.intervalles_contexte_prec,
            'env_id': etat.env_id,
            'nom_classe': etat.nom_classe,
            'palier_cible': etat.palier_cible,
            'doorkey_actif_a_la_sauvegarde': etat.doorkey_actif,
            'gestionnaire_cursus_sous_seuil': etat.gestionnaire_cursus.sous_seuil_actuel,
            'gestionnaire_cursus_succes_courant': etat.gestionnaire_cursus.succes_sous_seuil_courant,
            # v24.0 — Cursus Développemental par Ères : palier vocal + état du
            # gestionnaire dédié (instance SÉPARÉE de gestionnaire_cursus ci-dessus,
            # voir agi_local_test.py EtatCognitif.__init__), même pattern que les 2
            # champs DoorKey juste au-dessus. Sans ça, reprendre un .brain issu du
            # cursus repartait de la voyelle "a" à chaque résurrection.
            'palier_vocal': etat.palier_vocal,
            'gestionnaire_cursus_vocal_sous_seuil': etat.gestionnaire_cursus_vocal.sous_seuil_actuel,
            'gestionnaire_cursus_vocal_succes_courant': etat.gestionnaire_cursus_vocal.succes_sous_seuil_courant,
            'module_acceptation_patience_min': etat.module_acceptation.patience_min,
            'module_acceptation_historique_succes': etat.module_acceptation.historique_succes,
            'module_acceptation_historique_vitesses': etat.module_acceptation.historique_vitesses,

            # --- 6. Thermostat de neurogenèse ---
            'seuil_base': etat.seuil_base,
            'seuil_actuel': etat.seuil_actuel,
            'cooldown_jours': etat.cooldown_jours,
            'jours_depuis_mutation': etat.jours_depuis_mutation,
            'historique_erreurs': etat.historique_erreurs,

            # --- 7. Compteurs de temps ---
            'tick_absolu': etat.tick_absolu,
            'jour': etat.jour,
        }
        # v30.0 — crée le dossier parent s'il n'existe pas. Depuis l'ajout du flag
        # `--brain` aux cursus (convention de nommage horodatée, voir CLAUDE.md), le
        # chemin peut pointer vers un sous-dossier absent (ex. brains/old_V30/...) :
        # sans ce mkdir, torch.save échouerait par FileNotFoundError APRÈS une journée
        # entière de calcul — le pire moment possible pour découvrir le problème.
        dossier = os.path.dirname(self.fichier)
        if dossier:
            os.makedirs(dossier, exist_ok=True)

        # Écriture atomique : on écrit dans un fichier temporaire puis on renomme,
        # pour ne jamais laisser un .brain à moitié écrit si le process est tué en
        # plein torch.save (ex: kill -9 pendant une sauvegarde d'urgence).
        fichier_temp = self.fichier + ".tmp"
        torch.save(checkpoint, fichier_temp)
        os.replace(fichier_temp, self.fichier)
        print(f"💾 Cerveau cristallisé avec succès ({self.fichier}).")

    def charger_ou_naitre(self, device=DEVICE):
        """Réveille l'agent dans l'état exact où il s'est endormi, ou fait naître un
        nouveau cerveau (bus=16) si aucun fichier `.brain` n'existe encore. Retourne
        toujours un `EtatCognitif` prêt à vivre une connexion."""
        if not os.path.exists(self.fichier):
            print(f"🐣 Naissance d'un nouveau cerveau (Bus={BUS_REFERENCE_INITIAL}) — "
                  f"aucun fichier {self.fichier} trouvé.")
            agent = AGI_Naulthene(dim_visuelle=DIM_VISUELLE, dim_bus=BUS_REFERENCE_INITIAL).to(device)
            env_id, nom_classe = PROGRAMME[0]
            env = creer_env(env_id, DIM_VISUELLE)
            print(f"   🎒 L'Agent démarre en {nom_classe}...")
            return EtatCognitif(agent, env, env_id, nom_classe)

        print(f"🧬 Résurrection du cerveau existant ({self.fichier})...")
        # weights_only=False : le checkpoint contient de l'état non-tensoriel (dicts,
        # listes, scalaires numpy — historique de ModuleAcceptationAbnegation, quête
        # active...) en plus des poids. Sûr ici car le fichier est cristallisé par
        # notre propre PersistanceAnatomique.sauvegarder(), jamais une source externe.
        checkpoint = torch.load(self.fichier, map_location=device, weights_only=False)

        # On doit créer l'agent avec la dimension évoluée AVANT de charger les poids —
        # sinon load_state_dict échoue sur un mismatch de shape.
        agent = AGI_Naulthene(dim_visuelle=DIM_VISUELLE, dim_bus=checkpoint['dim_bus']).to(device)

        # strict=False (v22.0) : greffe rétrocompatible de l'Hémisphère Auditif & Vocal.
        # Un vieux .brain (pré-v22.0) n'a pas porte_auditive/tete_vocale dans son
        # state_dict — un chargement strict planterait sur ces clés manquantes. Avec
        # strict=False, l'agent hérite de tous ses acquis existants (vision, MiniGrid,
        # curriculum) et les couches audio, absentes du checkpoint, restent à leur
        # initialisation aléatoire — l'agent se réveille avec ses souvenirs intacts mais
        # "sourd/muet de naissance qui vient d'être opéré" : il devra apprendre à
        # entendre/parler par babillage. Une fois ce .brain re-sauvegardé, il contiendra
        # les couches audio et ce chemin ne sera plus emprunté pour lui.
        #
        # v22.1 : DIM_VECTEUR_BIO est passé de 8 à 16 (ajout de la quête vocale, voir
        # correctif défaut 2) — integrateur_bio (entrée dim_bus+DIM_VECTEUR_BIO) change
        # donc de FORME, pas seulement de clés manquantes, pour un VIEUX .brain
        # (pré-v22.1). strict=False ne gère que les clés absentes/en trop, PAS un
        # mismatch de shape sur une clé présente des deux côtés : sans un filtre,
        # load_state_dict lève une RuntimeError ("size mismatch for integrateur_bio...")
        # sur ces vieux fichiers, confirmée par test sur le vrai .brain d'alors.
        #
        # Bug corrigé (v24.0-fix4, signalé par l'utilisateur) : l'exclusion était
        # INCONDITIONNELLE — elle testait seulement `startswith('integrateur_bio.')`,
        # sans jamais vérifier si le checkpoint avait DÉJÀ la bonne forme (16 dims).
        # Conséquence concrète : tout .brain sauvegardé depuis la v22.1 (donc avec
        # integrateur_bio correctement appris à la bonne taille, ex. naulthene_cursus.brain
        # produit par cursus_developpemental.py) se faisait quand même amputer de cette
        # couche à CHAQUE rechargement — l'agent "oubliait" son intégration bio/vocale à
        # chaque relance (Cursus, Arène...), remplacée par des poids aléatoires. Comme
        # integrateur_bio est justement la couche qui réinjecte la quête vocale vers
        # tete_vocale, une réinitialisation systématique produisait une bouche
        # silencieuse dans l'Arène (amplitude sous le seuil d'audibilité en mode eval()).
        #
        # Correctif : ne filtrer QUE si la forme réelle du checkpoint diffère de la
        # forme attendue par l'agent fraîchement recréé (dim_bus+DIM_VECTEUR_BIO en
        # entrée) — un .brain déjà à la bonne taille charge intégralement, sans perte.
        #
        # v29.0 (expérimental) — DIM_VECTEUR_BIO passe de 16 à 24 (ajout du toucher, de
        # l'odorat et du goût, voir bus_sensoriel.py). Ce cas est désormais traité EN
        # AMONT du filtre d'exclusion ci-dessous, par recopie partielle
        # (_greffer_vecteur_bio_etendu) : un .brain pré-v29.0 conserve intégralement son
        # intégration viscérale/vocale apprise, au lieu de la perdre comme le ferait
        # l'exclusion. Le filtre reste en place derrière, comme trappe de secours pour
        # tout autre mismatch de forme (ex. dim_bus incohérent) qu'on ne sait pas greffer.
        state_dict_prepare, bio_greffe = _greffer_vecteur_bio_etendu(checkpoint['state_dict'], agent)

        forme_integrateur_checkpoint = state_dict_prepare.get('integrateur_bio.base_weight')
        forme_integrateur_attendue = agent.integrateur_bio.base_weight.shape
        integrateur_bio_incompatible = (
            forme_integrateur_checkpoint is not None
            and forme_integrateur_checkpoint.shape != forme_integrateur_attendue
        )
        if integrateur_bio_incompatible:
            cles_a_exclure = {k for k in state_dict_prepare if k.startswith('integrateur_bio.')}
            state_dict_filtre = {k: v for k, v in state_dict_prepare.items() if k not in cles_a_exclure}
            print(f"   🔄 integrateur_bio exclu du chargement (forme {tuple(forme_integrateur_checkpoint.shape)} "
                  f"incompatible avec {tuple(forme_integrateur_attendue)} attendu) — cette couche renaît à neuf.")
        else:
            state_dict_filtre = state_dict_prepare

        # v28.0 (expérimental) — Greffe de la 8ème action (ACTION_DEMANDER, Port
        # Exocortex C3) par RECOPIE PARTIELLE, PAS par exclusion. Contrairement au
        # filtre integrateur_bio ci-dessus (qui laisse la couche renaître à neuf sur
        # mismatch), num_actions passe de 7 à 8 : jeter tete_motrice/
        # generateur_attente/generateur_attente_audio sur un .brain existant
        # amputerait l'agent de 300+ jours de tête motrice et de modèle du monde
        # appris — inacceptable (voir CLAUDE.md, "Toute nouvelle couche
        # NaultheneLinearSynaptique... "). _greffer_action_supplementaire recopie
        # chaque bloc [:7] existant dans le nouveau tenseur [:8] et laisse la 8ème
        # ligne/colonne à son initialisation Xavier atténuée (même sémantique que
        # NaultheneLinearSynaptique.agrandir(), voir noyau.py) — un .brain sauvegardé
        # sans la 8ème action reprend l'intégralité de ses acquis existants, et
        # découvre juste une nouvelle action possible, jamais entraînée.
        state_dict_filtre = _greffer_action_supplementaire(state_dict_filtre, agent)

        resultat_chargement = agent.load_state_dict(state_dict_filtre, strict=False)
        # v32.0 — `missing_keys` ne suffit PAS à décider du sort de l'optimiseur : il ne
        # signale que les couches entièrement ABSENTES du checkpoint. Une greffe par
        # RECOPIE (la règle du projet : `_greffer_vecteur_bio_etendu`,
        # `_greffer_action_supplementaire`) ne produit aucune clé manquante — la couche
        # existe et a déjà été réécrite à la BONNE forme, seule sa largeur d'origine a
        # changé. Les moments Adam restaient donc chargés à l'ancienne largeur, et la
        # première NUIT du cerveau greffé plantait sur « The size of tensor a (80) must
        # match the size of tensor b (82) » — jamais au chargement ni pendant la journée,
        # ce qui rendait le bug invisible à toute vérification courte. Cas réel rencontré
        # en greffant un `.brain` v31 (80 dims) sur cette version (82).
        #
        # On se fie donc au drapeau retourné par la greffe elle-même, seul témoin fiable
        # qu'une largeur a bougé une fois le state_dict réaligné.
        #
        # v34.0-fix1 — `norme_naissance` est un BUFFER DE DIAGNOSTIC ajouté à chaque
        # NaultheneLinearSynaptique (référence du plancher vital anti-extinction). Il est
        # forcément absent de tout `.brain` antérieur, sur les 12 couches à la fois — ce
        # qui faisait croire à une greffe massive et réinitialisait Adam sans raison, à
        # chaque chargement de chaque ancien cerveau.
        #
        # Il ne participe à aucun calcul de forme et sa valeur par défaut (la norme du
        # tenseur fraîchement initialisé) est la bonne pour un cerveau déjà entraîné : le
        # plancher se cale alors sur l'échelle d'origine de la couche, exactement comme
        # pour un cerveau neuf. Il est donc exclu de la détection de greffe.
        cles_manquantes_reelles = [c for c in resultat_chargement.missing_keys
                                    if not c.endswith("norme_naissance")]
        greffe_detectee = bool(cles_manquantes_reelles) or bio_greffe
        if greffe_detectee:
            print(f"   🌱 Hémisphères nouvellement greffés sur ce cerveau (initialisés à neuf) : "
                  f"{sorted({cle.split('.')[0] for cle in cles_manquantes_reelles})}")
        if resultat_chargement.unexpected_keys:
            print(f"   ⚠️  Clés du checkpoint ignorées (absentes de l'architecture actuelle) : "
                  f"{sorted({cle.split('.')[0] for cle in resultat_chargement.unexpected_keys})}")

        if greffe_detectee:
            # L'ancien optimizer ne connaît pas les paramètres des nouvelles couches
            # greffées (nombre de groupes différent) — le charger tel quel lève un
            # ValueError PyTorch ("parameter group that doesn't match the size").
            # On repart donc sur un optimiseur frais (déjà créé par AGI_Naulthene.
            # __init__ / _reset_optimizer ci-dessus) plutôt que de tenter un chargement
            # partiel de la dynamique Adam, de toute façon incohérent avec les nouvelles
            # synapses. Seule la dynamique d'apprentissage (moments Adam) est perdue —
            # tous les poids/acquis du state_dict, eux, sont bien préservés au-dessus.
            motif = ("nouvelles couches greffées" if cles_manquantes_reelles
                     else "largeur du vecteur bio étendue par greffe")
            print(f"   🔄 Optimiseur réinitialisé ({motif}) — "
                  "les poids/acquis existants sont intacts, seule la dynamique Adam repart à neuf.")
        else:
            agent.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

        env_id = checkpoint['env_id']
        nom_classe = checkpoint['nom_classe']
        env = creer_env(env_id, DIM_VISUELLE)

        etat = EtatCognitif(agent, env, env_id, nom_classe)

        # --- Chimie viscérale ---
        etat.teneur_dopamine = checkpoint['teneur_dopamine']
        etat.plasticite_base = checkpoint['plasticite_base']
        etat.moteur_bio.satiete = checkpoint['satiete']
        etat.moteur_bio.hydratation = checkpoint['hydratation']
        etat.moteur_bio.stimulation = checkpoint['stimulation']
        etat.moteur_bio.quete_active = checkpoint['quete_active']

        # --- Souvenirs ---
        etat.memoire_episodique_spatiale.souvenirs = checkpoint['souvenirs_spatiaux']
        # v31.1 — compactage des doublons historiques. La déduplication d'
        # `enregistrer_evenement` ne vaut que pour les nouveaux souvenirs ; un `.brain`
        # antérieur porte encore tous les siens. Mesuré sur naulthene_parole (480 000
        # ticks) : 200 souvenirs pour 18 repères distincts, soit 91 % de redondance — la
        # « saturation » observée n'était pas un manque de place. Le tick le plus récent
        # de chaque repère est conservé, donc aucune information n'est perdue : seules
        # les répétitions disparaissent.
        supprimes = etat.memoire_episodique_spatiale.dedupliquer()
        if supprimes:
            restants = len(etat.memoire_episodique_spatiale.souvenirs)
            print(f"   🧹 Mémoire spatiale compactée : {supprimes} doublon(s) fusionné(s) "
                  f"→ {restants} repère(s) distinct(s) (v31.1, aucune information perdue).")

        # --- Curriculum & progression ---
        #
        # v35.0 — REMAPPAGE DU NIVEAU. `niveau_actuel` est un INDEX dans `PROGRAMME`, or
        # le programme est passé de 5 à 15 entrées. Un `.brain` sauvegardé au niveau 4
        # (ex-Doctorat, `MultiRoom-N4-S5`) se retrouverait sinon à l'index 4 du nouveau
        # programme (`LavaGapS5`) — c'est-à-dire RÉTROGRADÉ de dix crans sans le savoir,
        # et son `env_id` sauvegardé ne correspondrait plus à son index.
        #
        # On se fie donc à `env_id`, qui est la seule donnée non ambiguë : on cherche
        # l'index réel de cet environnement dans le programme courant. Même règle que la
        # greffe par recopie — on traduit, on ne jette jamais.
        etat.niveau_actuel = checkpoint['niveau_actuel']
        index_reel = next((i for i, (e, _) in enumerate(PROGRAMME) if e == env_id), None)
        if index_reel is None:
            # L'environnement du checkpoint ne fait plus partie du programme : on garde
            # l'index tel quel s'il est valide, sinon on borne. L'agent reprendra sur son
            # env_id d'origine (déjà créé ci-dessus) et sera réaligné à la 1re promotion.
            etat.niveau_actuel = min(etat.niveau_actuel, len(PROGRAMME) - 1)
            print(f"   ⚠️  '{env_id}' ne figure plus dans le PROGRAMME — niveau borné à "
                  f"{etat.niveau_actuel}. L'agent continue sur cet environnement.")
        elif index_reel != etat.niveau_actuel:
            print(f"   🔀 Niveau remappé : index {etat.niveau_actuel} → {index_reel} "
                  f"({nom_classe}) — le PROGRAMME a changé de taille (v35.0), "
                  f"aucune progression n'est perdue.")
            etat.niveau_actuel = index_reel
        etat.victoires_consecutives = checkpoint['victoires_consecutives']
        # v35.0 — historique glissant de promotion. Absent des `.brain` antérieurs : on
        # repart d'une fenêtre vide, donc `_taux_maitrise_niveau` renvoie None tant que
        # MIN_EPISODES_PROMOTION épisodes n'ont pas été rejoués. La voie « série de
        # victoires » reste disponible entre-temps : aucun cerveau ne perd de vitesse.
        etat.historique_episodes_niveau = checkpoint.get('historique_episodes_niveau', [])
        # v35.1 — un `.brain` antérieur repart à 0 : le filet se réarmera naturellement si
        # l'agent stagne réellement, plutôt que d'hériter d'un renfort qu'il n'a pas mérité.
        etat.jours_stagnation_niveau = checkpoint.get('jours_stagnation_niveau', 0)
        # v33.0-etape0.6 — lecture DÉFENSIVE (`.get`) : les `.brain` antérieurs à cette
        # version n'ont aucune de ces clés. Un cerveau ancien repart donc d'une
        # chronologie vierge (aucune victoire connue) plutôt que de faire planter le
        # chargement — même principe que les autres champs ajoutés après coup, et
        # cohérent avec la règle « greffe par recopie, jamais par exclusion » : on
        # n'ampute rien, on complète ce qui manque.
        etat.jour_derniere_victoire = checkpoint.get('jour_derniere_victoire')
        etat.jours_depuis_victoire = checkpoint.get('jours_depuis_victoire', 0)
        etat.intervalles_victoires = checkpoint.get('intervalles_victoires', [])
        etat.victoires_totales = checkpoint.get('victoires_totales', 0)
        etat.contexte_victoires = checkpoint.get('contexte_victoires')
        etat.intervalles_contexte_prec = checkpoint.get('intervalles_contexte_prec', [])
        etat.palier_cible = checkpoint['palier_cible']
        if checkpoint.get('doorkey_actif_a_la_sauvegarde'):
            # Recrée le détecteur DoorKey s'il était actif à la sauvegarde, pour que
            # demarrer_journee() n'ait pas besoin de le redétecter à froid — il sera
            # de toute façon réinitialisé sur le nouvel env au premier appel.
            etat.detecteur = DetecteurJalonsDoorKey()
        etat.gestionnaire_cursus.sous_seuil_actuel = checkpoint['gestionnaire_cursus_sous_seuil']
        etat.gestionnaire_cursus.succes_sous_seuil_courant = checkpoint['gestionnaire_cursus_succes_courant']
        # v24.0 : .get(..., défaut) — un .brain antérieur à la v24.0 (ex. issu de la
        # Cuve avant l'ajout du Cursus par Ères) n'a pas ces clés ; l'agent reprend
        # alors simplement au palier vocal 1 (comme un cerveau neuf), sans planter.
        etat.palier_vocal = checkpoint.get('palier_vocal', 1)
        etat.gestionnaire_cursus_vocal.sous_seuil_actuel = checkpoint.get(
            'gestionnaire_cursus_vocal_sous_seuil', 1)
        etat.gestionnaire_cursus_vocal.succes_sous_seuil_courant = checkpoint.get(
            'gestionnaire_cursus_vocal_succes_courant', 0)
        etat.module_acceptation.patience_min = checkpoint['module_acceptation_patience_min']
        etat.module_acceptation.historique_succes = checkpoint['module_acceptation_historique_succes']
        etat.module_acceptation.historique_vitesses = checkpoint['module_acceptation_historique_vitesses']

        # --- Thermostat de neurogenèse ---
        etat.seuil_base = checkpoint['seuil_base']
        etat.seuil_actuel = checkpoint['seuil_actuel']
        etat.cooldown_jours = checkpoint['cooldown_jours']
        etat.jours_depuis_mutation = checkpoint['jours_depuis_mutation']
        etat.historique_erreurs = checkpoint['historique_erreurs']

        # --- Compteurs de temps ---
        etat.tick_absolu = checkpoint['tick_absolu']
        etat.jour = checkpoint['jour']

        print(f"   🧠 Bus: {agent.dim_bus} dims | Dopamine: {etat.teneur_dopamine:.3f}/10.0 | "
              f"Niveau: {nom_classe} | Tick absolu: {etat.tick_absolu} | "
              f"Souvenirs: {len(etat.memoire_episodique_spatiale.souvenirs)}")
        return etat
