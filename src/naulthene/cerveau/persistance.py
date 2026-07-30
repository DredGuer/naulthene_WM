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
    NUM_ACTIONS_BASE, NUM_ACTIONS_AVEC_C3,
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
            'victoires_consecutives': etat.victoires_consecutives,
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
        forme_integrateur_checkpoint = checkpoint['state_dict'].get('integrateur_bio.base_weight')
        forme_integrateur_attendue = agent.integrateur_bio.base_weight.shape
        integrateur_bio_incompatible = (
            forme_integrateur_checkpoint is not None
            and forme_integrateur_checkpoint.shape != forme_integrateur_attendue
        )
        if integrateur_bio_incompatible:
            cles_a_exclure = {k for k in checkpoint['state_dict'] if k.startswith('integrateur_bio.')}
            state_dict_filtre = {k: v for k, v in checkpoint['state_dict'].items() if k not in cles_a_exclure}
            print(f"   🔄 integrateur_bio exclu du chargement (forme {tuple(forme_integrateur_checkpoint.shape)} "
                  f"incompatible avec {tuple(forme_integrateur_attendue)} attendu) — cette couche renaît à neuf.")
        else:
            state_dict_filtre = checkpoint['state_dict']

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
        greffe_detectee = bool(resultat_chargement.missing_keys)
        if greffe_detectee:
            print(f"   🌱 Hémisphères nouvellement greffés sur ce cerveau (initialisés à neuf) : "
                  f"{sorted({cle.split('.')[0] for cle in resultat_chargement.missing_keys})}")
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
            print("   🔄 Optimiseur réinitialisé (incompatible avec les nouvelles couches greffées) — "
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

        # --- Curriculum & progression ---
        etat.niveau_actuel = checkpoint['niveau_actuel']
        etat.victoires_consecutives = checkpoint['victoires_consecutives']
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
