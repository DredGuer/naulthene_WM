#Version actuelle 14.

import torch
import torch.nn as nn
import torch.nn.functional as F
import gymnasium as gym
import minigrid
import wandb
import numpy as np

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(42)
np.random.seed(42)

# Accès aux internes de MiniGrid pour la détection de jalons. Se désactive proprement
# si l'API a changé d'une version de minigrid à l'autre, au lieu de faire planter
# l'entraînement.
try:
    from minigrid.core.world_object import Key, Door, Goal
    from minigrid.core.actions import Actions
    _MINIGRID_INTERNALS_OK = True
except Exception:
    _MINIGRID_INTERNALS_OK = False


# --- 1. LE SCALPEL (Plasticité Structurelle) ---
class NaultheneLinearSynaptique(nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features

        self.register_buffer('base_weight', torch.empty(out_features, in_features))
        nn.init.xavier_uniform_(self.base_weight)
        self.annexe_weight = nn.Parameter(torch.zeros(out_features, in_features))
        self.register_buffer('myeline_M', torch.zeros(out_features, in_features))

    def forward(self, x):
        weight_total = self.base_weight + self.annexe_weight
        if self.training:
            with torch.no_grad():
                self.myeline_M = torch.max(self.myeline_M, torch.abs(self.annexe_weight.detach()))
        return F.linear(x, weight_total)

    def cycle_sommeil(self, lambda_erosion=0.05, q_ref=1.0):
        with torch.no_grad():
            self.base_weight += self.annexe_weight
            myeline_norm = torch.clamp(self.myeline_M / q_ref, 0.0, 1.0)
            self.base_weight *= (1.0 - (lambda_erosion * (1.0 - myeline_norm)))

            masque_mort = torch.abs(self.base_weight) < 1e-4
            self.base_weight[masque_mort] = 0.0
            self.myeline_M[masque_mort] = 0.0
            self.annexe_weight.zero_()
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

        src = 0
        dst = 0
        for taille, ajout in segments_in:
            new_base[:self.out_features, dst:dst + taille] = self.base_weight[:, src:src + taille]
            new_myeline[:self.out_features, dst:dst + taille] = self.myeline_M[:, src:src + taille]
            src += taille
            dst += taille + ajout

        self.base_weight = new_base
        self.myeline_M = new_myeline
        self.annexe_weight = nn.Parameter(new_annexe)
        self.in_features, self.out_features = new_in, new_out


# --- 2. LE CERVEAU SYSTÈME 1 & 2 ---
class AGI_Naulthene(nn.Module):
    def __init__(self, dim_visuelle=147, dim_bus=16, num_actions=7, lr=1e-3):
        super().__init__()
        self.dim_visuelle = dim_visuelle
        self.dim_bus = dim_bus
        self.num_actions = num_actions
        self.lr = lr

        self.porte_visuelle = NaultheneLinearSynaptique(dim_visuelle, dim_bus)
        self.hippocampe = NaultheneLinearSynaptique(dim_bus * 2, dim_bus)
        self.fusion_memoire = NaultheneLinearSynaptique(dim_bus * 2, dim_bus)
        self.analyseur = NaultheneLinearSynaptique(dim_bus, dim_bus)
        self.tete_motrice = NaultheneLinearSynaptique(dim_bus, num_actions)
        self.cortex_prefrontal = NaultheneLinearSynaptique(dim_bus, 1)
        self.generateur_attente = NaultheneLinearSynaptique(num_actions + dim_bus, dim_bus)

        self.register_buffer('actions_eye', torch.eye(num_actions))
        self._reset_optimizer()

    def _reset_optimizer(self):
        params = [p for p in self.parameters() if p.requires_grad]
        self.optimizer = torch.optim.Adam(params, lr=self.lr)

    def contexte_vide(self, batch=1):
        return torch.zeros(batch, self.dim_bus, device=self.actions_eye.device)

    def _tronc_cerebral(self, obs, memoire_precedente):
        bus_latent = F.relu(self.porte_visuelle(obs))
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

    @torch.no_grad()
    def simuler_futur_et_planifier(self, pensee, memoire_actuelle, horizon=1, gamma_planif=0.9):
        """Rollout imaginé sur `horizon` pas virtuels (1 à 3, cf. demande utilisateur).

        Le PREMIER pas branche sur les 7 actions réelles (c'est la décision qu'on évalue
        maintenant). Les pas SUIVANTS suivent le réflexe du réseau (argmax de la tête
        motrice) plutôt que de re-brancher sur 7 nouvelles actions à chaque niveau :
        sans cette restriction, le nombre de branches exploserait en 7^horizon au lieu
        de rester à 7 quel que soit l'horizon. La valeur finale est une somme actualisée
        (comme un retour à N pas classique en RL) des valeurs imaginées à chaque étape,
        pas seulement la valeur du dernier pas — un chemin qui traverse un bon état
        intermédiaire compte, même si l'état final est incertain."""
        A = self.num_actions
        pensee_branche = pensee.expand(A, -1)
        mem_branche = memoire_actuelle.expand(A, -1)

        valeur_cumulee = torch.zeros(1, A, device=pensee.device)
        remise = 1.0

        for pas in range(horizon):
            if pas == 0:
                actions_pas = self.actions_eye  # les 7 choix réels, un par branche
            else:
                choix = torch.argmax(self.tete_motrice(pensee_branche), dim=-1)
                actions_pas = self.actions_eye[choix]  # continuation gourmande, 1 par branche

            futur_bus = F.relu(self._predire_bus(pensee_branche, actions_pas))
            futur_mem = F.relu(self.hippocampe(torch.cat([futur_bus, mem_branche], dim=-1)))
            futur_pensee = F.relu(self.analyseur(futur_mem))
            valeur_pas = self.cortex_prefrontal(futur_pensee).view(1, A)

            valeur_cumulee = valeur_cumulee + remise * valeur_pas
            remise *= gamma_planif
            pensee_branche, mem_branche = futur_pensee, futur_mem

        if valeur_cumulee.std() > 1e-6:
            valeur_cumulee = (valeur_cumulee - valeur_cumulee.mean()) / (valeur_cumulee.std() + 1e-8)
        return valeur_cumulee

    def penser(self, obs_visuelle, memoire_precedente, contexte_episodique,
              force_planification=0.5, horizon_planification=1, gamma_planif=0.9):
        bus_latent, memoire_actuelle, pensee = self._tronc_cerebral(
            obs_visuelle, memoire_precedente.detach()
        )
        pensee_enrichie = self.lecture_episodique(pensee, contexte_episodique)

        pensee_detachee = pensee_enrichie.detach()
        logits_instinct = self.tete_motrice(pensee_detachee)
        valeurs_simulees = self.simuler_futur_et_planifier(
            pensee_detachee, memoire_actuelle.detach(),
            horizon=horizon_planification, gamma_planif=gamma_planif
        )

        logits_finaux = logits_instinct + (valeurs_simulees * force_planification)
        valeur_etat_courant = self.cortex_prefrontal(pensee_detachee)

        return logits_finaux, valeur_etat_courant, pensee_enrichie, memoire_actuelle, bus_latent

    def generer_attente_reelle(self, pensee_enrichie, actions_idx):
        onehot = self.actions_eye[actions_idx]
        if onehot.dim() == 1:
            onehot = onehot.unsqueeze(0)
        return self._predire_bus(pensee_enrichie, onehot)

    def perte_jepa(self, attente, obs_suivante):
        with torch.no_grad():
            bus_reel = F.relu(self.porte_visuelle(obs_suivante))
        return F.mse_loss(attente, bus_reel)

    def apprendre_journee(self, jepa_losses, log_probs, entropies, valeurs, rewards, dones,
                          gamma=0.95, coeff_entropie=0.02):
        self.optimizer.zero_grad(set_to_none=True)
        perte_totale = torch.zeros((), device=DEVICE)

        if jepa_losses:
            perte_totale = perte_totale + torch.stack(jepa_losses).mean()

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

            perte_acteur = -(log_probs_tensor * avantages).mean()
            perte_critique = F.mse_loss(valeurs_tensor, returns)
            perte_entropie = -coeff_entropie * entropies_tensor.mean()

            perte_totale = perte_totale + perte_acteur + perte_critique + perte_entropie

        if not perte_totale.requires_grad:
            return 0.0

        perte_totale.backward()
        torch.nn.utils.clip_grad_norm_([p for p in self.parameters() if p.requires_grad], 1.0)
        self.optimizer.step()
        return float(perte_totale.item())

    def rever(self, memoire_moyen_terme, batch_size=32):
        """batch_size est désormais calculé par l'appelant comme un POURCENTAGE adaptatif
        de la journée (voir la boucle principale) plutôt qu'une constante fixe."""
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

        self.optimizer.zero_grad(set_to_none=True)
        _, _, pensee = self._tronc_cerebral(obs_courante, memoire_prec)
        pensee_enrichie = self.lecture_episodique(pensee, contexte)
        attente = self.generer_attente_reelle(pensee_enrichie, actions)
        perte_reves = self.perte_jepa(attente, obs_suivante)

        perte_reves.backward()
        torch.nn.utils.clip_grad_norm_([p for p in self.parameters() if p.requires_grad], 1.0)
        self.optimizer.step()
        return float(perte_reves.item()), batch_size

    def cycle_sommeil_global(self, plasticite=1.0):
        lam = 0.05 * plasticite
        return sum([
            self.porte_visuelle.cycle_sommeil(lambda_erosion=lam),
            self.hippocampe.cycle_sommeil(lambda_erosion=lam),
            self.fusion_memoire.cycle_sommeil(lambda_erosion=lam),
            self.analyseur.cycle_sommeil(lambda_erosion=lam),
            self.tete_motrice.cycle_sommeil(lambda_erosion=lam),
            self.cortex_prefrontal.cycle_sommeil(lambda_erosion=lam),
            self.generateur_attente.cycle_sommeil(lambda_erosion=lam),
        ])

    def declencher_neurogenese(self, ajout_dim=16):
        d = self.dim_bus
        a = ajout_dim
        A = self.num_actions

        self.porte_visuelle.agrandir([(self.dim_visuelle, 0)], a)
        self.hippocampe.agrandir([(d, a), (d, a)], a)
        self.fusion_memoire.agrandir([(d, a), (d, a)], a)
        self.analyseur.agrandir([(d, a)], a)
        self.tete_motrice.agrandir([(d, a)], 0)
        self.cortex_prefrontal.agrandir([(d, a)], 0)
        self.generateur_attente.agrandir([(A, 0), (d, a)], a)

        self.dim_bus += a
        self.to(DEVICE)
        self._reset_optimizer()


def encoder(obs):
    return torch.as_tensor(obs['image'].flatten(), dtype=torch.float32, device=DEVICE).unsqueeze(0) / 10.0


def creer_env(env_id, dim_attendue):
    e = gym.make(env_id)
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


# --- 4. EXÉCUTION & CURSUS ---
wandb.init(project="Naulthene-AGI", name="Run_14_Reves_Adaptatifs_Planification_Etendue")

DIM_VISUELLE = 147
DIM_BUS_MAX = 96
JOURS_ENTRE_MUTATIONS = 5

agent = AGI_Naulthene(dim_visuelle=DIM_VISUELLE, dim_bus=16).to(DEVICE)
BUS_REFERENCE = agent.dim_bus

jours_totaux = 400
ticks_par_jour = 400
CAPACITE_MEMOIRE = 20

# --- RÉSERVOIR DOPAMINERGIQUE ---
DOPAMINE_NEUTRE = 5.0
DOPAMINE_MIN = 0.001
DOPAMINE_MAX = 10.0
TENEUR_DOPAMINE = DOPAMINE_NEUTRE

TAUX_FRICTION = 0.01
TAUX_CHOC_BASE = 0.9
TAUX_RESSORT = 0.4

PLAFOND_ERREUR_DOPAMINE = 2.0
BOOST_ANCRAGE_MAX = 20.0
SEUIL_APHASIE_NEUROGENESE = 0.05
MALUS_DOULEUR = -0.01
SEUIL_MAITRISE_PALIER = 0.80

# --- MODE LIBRE (DoorKey uniquement, inchangé) ---
FORCE_PLANIFICATION_GUIDE = 0.5
FORCE_PLANIFICATION_LIBRE = 0.85
COEFF_ENTROPIE_GUIDE = 0.02
COEFF_ENTROPIE_LIBRE = 0.06

# --- HORIZON DE PLANIFICATION (nouveau) ---
# 1 pas = ancien comportement. 3 pas = ce qui est demandé : le Système 2 imagine une
# petite séquence, pas juste le prochain instant — utile pour les couloirs longs de
# MultiRoom (Doctorat) où l'objectif n'est jamais visible à un seul pas de distance.
HORIZON_PLANIFICATION = 3
GAMMA_PLANIFICATION = 0.9

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

PROGRAMME = [
    ("MiniGrid-Empty-8x8-v0", "Primaire (Mouvement basique)"),
    ("MiniGrid-DoorKey-6x6-v0", "Collège (Logique Simple)"),
    ("MiniGrid-Unlock-v0", "Lycée (Manipulation Avancée)"),
    ("MiniGrid-MemoryS7-v0", "Université (Mémoire Épisodique)"),
    ("MiniGrid-MultiRoom-N4-S5-v0", "Doctorat (Planification Longue)")
]
niveau_actuel = 0
victoires_consecutives = 0
VICTOIRES_REQUISES = 2

env_id, nom_classe = PROGRAMME[niveau_actuel]
env = creer_env(env_id, DIM_VISUELLE)
print(f"\n🎒 Rentrée des classes : L'Agent démarre en {nom_classe}...")

seuil_base, seuil_actuel, delta_max = 0.0005, 0.0005, 0.50
cooldown_jours = 0
jours_depuis_mutation = JOURS_ENTRE_MUTATIONS
historique_erreurs = []

detecteur = None            # spécifique DoorKey, créé à la volée
palier_cible = 1
detecteur_portes = DetecteurFranchissementPortes()   # générique, actif partout
detecteur_progres = DetecteurProgresPersonnel()       # générique, inactif sur DoorKey

for jour in range(1, jours_totaux + 1):
    doorkey_actif = est_doorkey(env_id)
    if doorkey_actif and detecteur is None:
        detecteur = DetecteurJalonsDoorKey()
        palier_cible = 1
        print(f"   📘 Détecteur de jalons DoorKey activé (Palier visé : {palier_cible} - "
              f"{DetecteurJalonsDoorKey.NOMS[0]})")

    EMPREINTE_ENFANCE = BUS_REFERENCE / agent.dim_bus

    mode_libre = doorkey_actif and (palier_cible >= 7)
    force_planification_jour = FORCE_PLANIFICATION_LIBRE if mode_libre else FORCE_PLANIFICATION_GUIDE
    coeff_entropie_jour = COEFF_ENTROPIE_LIBRE if mode_libre else COEFF_ENTROPIE_GUIDE

    obs, info = env.reset()
    etat_courant = encoder(obs)
    memoire_tampon = torch.zeros(1, agent.dim_bus, device=DEVICE)
    vecteurs_episodiques = []
    if doorkey_actif:
        detecteur.reinitialiser_episode(env)
    detecteur_portes.reinitialiser_episode(env)
    if not doorkey_actif:
        detecteur_progres.reinitialiser_episode(env)

    memoire_moyen_terme = []
    jepa_losses, log_probs_journee, entropies_journee = [], [], []
    valeurs_journee, recompenses_journee, dones_journee = [], [], []

    erreur_journee = 0.0
    victoire_aujourdhui = False
    episodes_jour = 0
    succes_palier_cible_jour = 0
    guidage_but_journee = 0.0
    portes_franchies_jour = 0
    progres_personnel_jour = 0
    jours_depuis_mutation += 1
    fin_episode = False

    agent.train()

    for tick in range(ticks_par_jour):
        memoire_avant = memoire_tampon

        if vecteurs_episodiques:
            contexte = torch.stack(vecteurs_episodiques).mean(dim=0)
        else:
            contexte = agent.contexte_vide()

        logits_action, valeur_estimee, pensee_enrichie, memoire_tampon, bus_latent = agent.penser(
            etat_courant, memoire_avant, contexte,
            force_planification=force_planification_jour,
            horizon_planification=HORIZON_PLANIFICATION,
            gamma_planif=GAMMA_PLANIFICATION,
        )

        vecteurs_episodiques.append(bus_latent.detach())
        if len(vecteurs_episodiques) > CAPACITE_MEMOIRE:
            vecteurs_episodiques.pop(0)

        dist = torch.distributions.Categorical(logits=logits_action)
        action = dist.sample()
        action_item = int(action.item())

        log_probs_journee.append(dist.log_prob(action))
        entropies_journee.append(dist.entropy())
        valeurs_journee.append(valeur_estimee)

        obs_suivante, recompense_env, termine, tronque, _ = env.step(action_item)
        etat_suivant = encoder(obs_suivante)
        fin_episode = bool(termine or tronque)
        mur_touche = torch.equal(etat_courant, etat_suivant)

        # --- Jalons DoorKey (spécifique) ---
        palier_ce_tick, micro_recompense, poids_palier, recompense_continue = 0, 0.0, 0.0, 0.0
        if doorkey_actif:
            palier_ce_tick, micro_recompense, poids_palier, recompense_continue = detecteur.evaluer_tick(
                env, action_item, recompense_env
            )
            guidage_but_journee += recompense_continue

        # --- Franchissement de portes (générique, tous niveaux) ---
        nb_portes, micro_recompense_porte, poids_porte = detecteur_portes.evaluer_tick(env)
        portes_franchies_jour += nb_portes

        # --- Progrès personnel (générique, hors DoorKey) ---
        micro_recompense_progres, poids_progres = 0.0, 0.0
        if not doorkey_actif:
            micro_recompense_progres, poids_progres = detecteur_progres.evaluer_tick(env)
            if micro_recompense_progres > 0:
                progres_personnel_jour += 1

        attente = agent.generer_attente_reelle(pensee_enrichie, action_item)
        perte_tick = agent.perte_jepa(attente, etat_suivant)
        jepa_losses.append(perte_tick)
        valeur_erreur = float(perte_tick.item())
        erreur_journee += valeur_erreur

        poids_evenement = 1.0 if recompense_env > 0 else 0.0
        poids_evenement = max(poids_evenement, poids_palier, poids_porte, poids_progres)

        dopamine_normalisee = (TENEUR_DOPAMINE - DOPAMINE_MIN) / (DOPAMINE_MAX - DOPAMINE_MIN)
        dopamine_curiosite = dopamine_normalisee * min(valeur_erreur, PLAFOND_ERREUR_DOPAMINE)

        recompense_interne = (float(recompense_env) + dopamine_curiosite + micro_recompense
                             + micro_recompense_porte + micro_recompense_progres)
        if not mode_libre:
            recompense_interne += recompense_continue
        if mur_touche:
            recompense_interne += MALUS_DOULEUR

        if poids_evenement > 0:
            TENEUR_DOPAMINE += (DOPAMINE_MAX - TENEUR_DOPAMINE) * TAUX_CHOC_BASE * poids_evenement
            micro_boost_ancrage = 1.0 + (BOOST_ANCRAGE_MAX - 1.0) * poids_evenement
            if recompense_env > 0:
                victoire_aujourdhui = True
        else:
            TENEUR_DOPAMINE += (DOPAMINE_MIN - TENEUR_DOPAMINE) * TAUX_FRICTION
            micro_boost_ancrage = 1.0
        TENEUR_DOPAMINE = float(np.clip(TENEUR_DOPAMINE, DOPAMINE_MIN, DOPAMINE_MAX))

        recompenses_journee.append(recompense_interne)
        dones_journee.append(fin_episode)

        memoire_moyen_terme.append({
            'obs_courante': etat_courant.detach(),
            'memoire_prec': memoire_avant.detach(),
            'contexte': contexte.detach(),
            'action': action_item,
            'obs_suivante': etat_suivant.detach(),
            'importance': (abs(recompense_interne) + (valeur_erreur * 2.0) + 1e-5)
                          * micro_boost_ancrage * EMPREINTE_ENFANCE
        })

        if fin_episode:
            episodes_jour += 1
            if doorkey_actif and detecteur.meilleur_palier_episode >= palier_cible:
                succes_palier_cible_jour += 1

            obs, info = env.reset()
            etat_courant = encoder(obs)
            memoire_tampon = torch.zeros(1, agent.dim_bus, device=DEVICE)
            vecteurs_episodiques.clear()
            if doorkey_actif:
                detecteur.reinitialiser_episode(env)
            detecteur_portes.reinitialiser_episode(env)
            if not doorkey_actif:
                detecteur_progres.reinitialiser_episode(env)
        else:
            etat_courant = etat_suivant

    if not fin_episode:
        episodes_jour += 1
        if doorkey_actif and detecteur.meilleur_palier_episode >= palier_cible:
            succes_palier_cible_jour += 1

    taux_maitrise = None
    if doorkey_actif and detecteur.actif and episodes_jour > 0:
        taux_maitrise = succes_palier_cible_jour / episodes_jour
        if taux_maitrise >= SEUIL_MAITRISE_PALIER and palier_cible < 7:
            palier_cible += 1
            print(f"   🎯 [PROGRESSION DE PALIER] Palier {palier_cible} visé : "
                  f"{DetecteurJalonsDoorKey.NOMS[palier_cible - 1]}")

    if victoire_aujourdhui:
        victoires_consecutives += 1
    else:
        victoires_consecutives = 0

    if victoires_consecutives >= VICTOIRES_REQUISES:
        if niveau_actuel < len(PROGRAMME) - 1:
            niveau_actuel += 1
            victoires_consecutives = 0
            env_id, nom_classe = PROGRAMME[niveau_actuel]
            env.close()
            env = creer_env(env_id, DIM_VISUELLE)
            print(f"\n🎓 [PROMOTION] L'Agent passe en {nom_classe} ! 🚀")
        else:
            print("🏆 [MAÎTRISE] L'Agent a vaincu le Doctorat (MultiRoom) !")

    erreur_moyenne = erreur_journee / ticks_par_jour

    # --- Plasticité calculée AVANT le rêve (elle pilote la taille du lot de rêve) et
    # AVANT le ressort nocturne (elle reflète l'état réel vécu pendant la journée) ---
    if TENEUR_DOPAMINE >= DOPAMINE_NEUTRE:
        PLASTICITE_BASE = 1.0
    else:
        PLASTICITE_BASE = max(0.0, (TENEUR_DOPAMINE - DOPAMINE_MIN) / (DOPAMINE_NEUTRE - DOPAMINE_MIN))

    perte_jour = agent.apprendre_journee(jepa_losses, log_probs_journee, entropies_journee,
                                         valeurs_journee, recompenses_journee, dones_journee,
                                         coeff_entropie=coeff_entropie_jour)

    # --- Calcul du pourcentage de rêve adaptatif ---
    if memoire_moyen_terme:
        importance_moyenne_jour = float(np.mean([s['importance'] for s in memoire_moyen_terme]))
    else:
        importance_moyenne_jour = 0.0
    facteur_richesse = min(1.0, importance_moyenne_jour / IMPORTANCE_REFERENCE_REVE)
    pourcentage_reve = POURCENTAGE_REVE_MIN + (PLAGE_REVE_MAX - POURCENTAGE_REVE_MIN) * PLASTICITE_BASE * facteur_richesse
    taille_lot_reve = int(round(pourcentage_reve * len(memoire_moyen_terme)))
    taille_lot_reve = max(0, min(taille_lot_reve, len(memoire_moyen_terme)))

    if taille_lot_reve < TAILLE_MIN_REVE:
        perte_reves, nb_reves = 0.0, 0
    else:
        perte_reves, nb_reves = agent.rever(memoire_moyen_terme, batch_size=taille_lot_reve)
    memoire_moyen_terme.clear()
    jepa_losses.clear()

    TENEUR_DOPAMINE += (DOPAMINE_NEUTRE - TENEUR_DOPAMINE) * TAUX_RESSORT
    TENEUR_DOPAMINE = float(np.clip(TENEUR_DOPAMINE, DOPAMINE_MIN, DOPAMINE_MAX))

    historique_erreurs.append(erreur_moyenne)
    if len(historique_erreurs) > 3:
        historique_erreurs.pop(0)
    if len(historique_erreurs) == 3:
        variance_erreur = float(np.var(historique_erreurs))
        moyenne_glissante = float(np.mean(historique_erreurs))
        if variance_erreur < 0.005 and moyenne_glissante > seuil_base * 1.5:
            seuil_base = (0.7 * seuil_base) + (0.3 * moyenne_glissante)

    etat_thermostat = "Stable"
    mutation_possible = (jours_depuis_mutation >= JOURS_ENTRE_MUTATIONS
                         and agent.dim_bus + 16 <= DIM_BUS_MAX
                         and PLASTICITE_BASE > SEUIL_APHASIE_NEUROGENESE)

    if cooldown_jours > 0:
        cooldown_jours -= 1
        etat_thermostat = f"Conv ({cooldown_jours}j)"
        if erreur_moyenne < seuil_base * 2:
            cooldown_jours = 0
            etat_thermostat = "Guérison"
    elif erreur_moyenne > seuil_actuel and jour > 1:
        if mutation_possible:
            agent.declencher_neurogenese(ajout_dim=16)
            jours_depuis_mutation = 0
            ratio_gravite = erreur_moyenne / max(seuil_base, 1e-9)
            cooldown_jours = min(5, max(1, int(ratio_gravite * 0.1)))
            seuil_actuel = min(seuil_actuel + (erreur_moyenne * 1.5), seuil_base + delta_max)
            etat_thermostat = "MUTATION !"
        elif PLASTICITE_BASE <= SEUIL_APHASIE_NEUROGENESE:
            etat_thermostat = "Aphasique (neurogenèse suspendue)"
        else:
            etat_thermostat = "Saturé" if agent.dim_bus + 16 > DIM_BUS_MAX else "Réfractaire"

    if seuil_actuel > seuil_base:
        seuil_actuel = max(seuil_base, seuil_actuel * 0.8)

    synapses_mortes = agent.cycle_sommeil_global(plasticite=PLASTICITE_BASE)
    rec_moy = sum(recompenses_journee) / ticks_par_jour

    etat_mental, pct_dopamine = etat_mental_dopamine(TENEUR_DOPAMINE, DOPAMINE_MIN, DOPAMINE_NEUTRE, DOPAMINE_MAX)
    etat_plasticite = etat_empreinte(EMPREINTE_ENFANCE)

    print(f"\n🌙 Jour {jour:03d} [{nom_classe}]")
    print(f"  ├─ État Mental    : {etat_mental} (Dopamine: {TENEUR_DOPAMINE:.3f}/10.0 [{pct_dopamine:.0f}%])")
    print(f"  ├─ Plasticité     : {etat_plasticite} (Bus: {agent.dim_bus} dims, "
          f"Empreinte: {EMPREINTE_ENFANCE:.2f}, Plasticité base: {PLASTICITE_BASE:.2f})")
    if doorkey_actif and detecteur.actif:
        nom_palier = DetecteurJalonsDoorKey.NOMS[palier_cible - 1]
        maitrise_txt = f"{taux_maitrise * 100:.0f}%" if taux_maitrise is not None else "N/A"
        print(f"  ├─ Progrès Jalon  : 🎯 Palier {palier_cible} ({nom_palier}) — "
              f"{succes_palier_cible_jour}/{episodes_jour} épisodes réussis "
              f"(maîtrise: {maitrise_txt}, seuil promotion: {SEUIL_MAITRISE_PALIER*100:.0f}%)")
        mode_txt = "🕊️ Libre (aucune récompense de guidage)" if mode_libre else "🧭 Guidé (béquille active)"
        print(f"  ├─ Mode Décision  : {mode_txt} — Planification: {force_planification_jour:.2f}, "
              f"Entropie: {coeff_entropie_jour:.2f}")
    if detecteur_portes.actif and portes_franchies_jour > 0:
        print(f"  ├─ Portes         : 🚪 {portes_franchies_jour} porte(s) franchie(s) aujourd'hui")
    if not doorkey_actif and detecteur_progres.actif and progres_personnel_jour > 0:
        print(f"  ├─ Quête Auto     : 🧭 {progres_personnel_jour} nouveaux records de proximité au But")
    print(f"  ├─ Consolidations : 💤 {nb_reves} souvenirs rejoués ({pourcentage_reve*100:.3f}% de la journée, "
          f"perte rêves: {perte_reves:.4f})")
    print(f"  └─ Erreur JEPA moy: {erreur_moyenne:.4f} | Réc. moyenne: {rec_moy:.3f} | "
          f"Thermostat: {etat_thermostat}")

    log_wandb = {
        "Jour": jour,
        "Niveau": niveau_actuel,
        "Erreur_JEPA": erreur_moyenne,
        "Perte_Consolidation": perte_jour,
        "Perte_Reves": perte_reves,
        "Nb_Reves": nb_reves,
        "Pourcentage_Reve": pourcentage_reve,
        "Recompense_Moyenne": rec_moy,
        "Victoire": int(victoire_aujourdhui),
        "Teneur_Dopamine": TENEUR_DOPAMINE,
        "Plasticite_Base": PLASTICITE_BASE,
        "Empreinte_Enfance": EMPREINTE_ENFANCE,
        "Synapses_Mortes": synapses_mortes,
        "Taille_Thalamus": agent.dim_bus,
        "Episodes_Jour": episodes_jour,
        "Portes_Franchies_Jour": portes_franchies_jour,
        "Progres_Personnel_Jour": progres_personnel_jour,
    }
    if doorkey_actif and detecteur.actif:
        log_wandb["Palier_Cible"] = palier_cible
        log_wandb["Guidage_But"] = guidage_but_journee
        log_wandb["Mode_Libre"] = int(mode_libre)
        log_wandb["Force_Planification"] = force_planification_jour
        log_wandb["Coeff_Entropie"] = coeff_entropie_jour
        if taux_maitrise is not None:
            log_wandb["Taux_Maitrise_Palier"] = taux_maitrise
    wandb.log(log_wandb)

env.close()
wandb.finish()