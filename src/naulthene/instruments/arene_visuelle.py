# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
L'Arène Visuelle (V24.0, expérimental) — le rendu de la Démo Live.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir le plan
v24.0 et `readme_fr.md` (section "L'Arène & Démo Live") pour le contexte narratif complet.

Pur module de RENDU (pygame) — aucune dépendance au réseau de neurones ni au moteur
MiniGrid. Il reçoit une image déjà rendue (`etat.env.render()`, `render_mode="rgb_array"`)
et un dictionnaire de télémétrie déjà calculé, et se contente de les dessiner dans une
fenêtre composite unique : l'image MiniGrid à gauche, un panneau de jauges/texte à
droite (dopamine, jauges biologiques, curriculum MiniGrid, curriculum vocal, mot visé
vs score de formants). C'est `lancer_arene.py` (l'orchestrateur) qui lit `EtatCognitif`
et construit ce dictionnaire — cette séparation garde le rendu testable en isolation,
sans avoir à faire tourner un vrai agent pour vérifier que les jauges se dessinent bien.

Mini-IRM en pygame pur (v26.0-experimental) : une bande sous l'image MiniGrid affiche les
activations du bus latent à 3 étapes du tronc cérébral (`bus_latent`/`memoire_actuelle`/
`pensee`), le pendant temps-réel du panneau 1 de `irm_cerveau.py` — mais en pygame plutôt
qu'en matplotlib, pour rester dans le MÊME framework graphique et alimenter la visualisation
depuis le MÊME cerveau que celui qui joue dans MiniGrid (pas un second `charger_ou_naitre()`
qui divergerait). Mélanger pygame (SDL) et matplotlib (Tk/Qt/macosx) dans un seul thread est
fragile sur macOS — les deux se disputent la boucle d'événements native Cocoa — d'où ce choix
de tout garder en primitives `pygame.draw` plutôt que d'ouvrir une seconde fenêtre matplotlib
depuis ce process.
"""

import pygame
import pygame.freetype

LARGEUR_IMAGE = 512   # image MiniGrid agrandie depuis les 256×256 natifs (render_mode="rgb_array")
LARGEUR_PANNEAU = 520  # panneau de télémétrie à droite — élargi (v26.0-experimental) pour
                        # afficher la parité complète avec le bilan de nuit console (§ci-dessous)
HAUTEUR_IMAGE = 512
HAUTEUR_PANNEAU_BUS = 140  # bande mini-IRM sous l'image MiniGrid (v26.0-experimental)
HAUTEUR_FENETRE = HAUTEUR_IMAGE + HAUTEUR_PANNEAU_BUS
LARGEUR_FENETRE = LARGEUR_IMAGE + LARGEUR_PANNEAU

FPS_ARENE = 10  # aligné sur metadata["render_fps"] natif de MiniGrid (minigrid_env.py)

# Couleurs des 3 séries d'activation du mini-IRM — reprises telles quelles de
# irm_cerveau.py (panneau 1) pour la cohérence visuelle entre les deux outils.
COULEUR_BUS_LATENT = (76, 114, 176)      # #4C72B0
COULEUR_MEMOIRE_ACTUELLE = (221, 132, 82)  # #DD8452
COULEUR_PENSEE = (85, 168, 104)           # #55A868

COULEUR_FOND = (18, 18, 24)
COULEUR_TEXTE = (230, 230, 235)
COULEUR_TEXTE_ATTENUE = (150, 150, 160)
COULEUR_SEPARATEUR = (60, 60, 70)

# Couleurs de jauge par nom — cohérent avec les emojis déjà utilisés dans les logs
# console d'agi_local_test.py (🍎 satiété, 💧 hydratation, ✨ stimulation, 🧠 dopamine)
COULEURS_JAUGES = {
    "dopamine": (255, 200, 60),
    "satiete": (220, 90, 90),
    "hydratation": (90, 160, 230),
    "stimulation": (190, 120, 230),
    "score_vocal": (110, 220, 140),
}


class FenetreArene:
    """Fenêtre pygame unique composant le rendu MiniGrid et le panneau de télémétrie.
    Aucun état cognitif ici — uniquement des primitives de dessin, appelées à chaque
    tick par l'orchestrateur (`lancer_arene.py`) avec des données déjà prêtes."""

    def __init__(self, titre="Naulthène AGI — Arène & Démo Live"):
        pygame.init()
        pygame.freetype.init()
        self.ecran = pygame.display.set_mode((LARGEUR_FENETRE, HAUTEUR_FENETRE))
        pygame.display.set_caption(titre)
        self.police_titre = pygame.freetype.SysFont("Arial", 18, bold=True)
        self.police_texte = pygame.freetype.SysFont("Arial", 15)
        self.police_petite = pygame.freetype.SysFont("Arial", 12)
        self.horloge = pygame.time.Clock()

    def evenements_fermeture_demandee(self) -> bool:
        """Consomme la file d'événements pygame et retourne True si l'utilisateur a
        cliqué sur la croix de la fenêtre (pygame.QUIT) — à appeler à chaque tick pour
        permettre une fermeture intuitive en plus du Ctrl+C terminal (voir plan v24.0,
        Question ouverte C)."""
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                return True
        return False

    def _dessiner_image_minigrid(self, image_rgb):
        """`image_rgb` : tableau numpy (H, W, 3) issu de `env.render()` en
        render_mode="rgb_array". pygame attend (largeur, hauteur, 3) — transposition
        des deux premiers axes, cohérent avec la convention numpy (lignes, colonnes)
        vs pygame (x, y)."""
        surface = pygame.surfarray.make_surface(image_rgb.swapaxes(0, 1))
        surface = pygame.transform.scale(surface, (LARGEUR_IMAGE, HAUTEUR_IMAGE))
        self.ecran.blit(surface, (0, 0))

    def _dessiner_jauge(self, x, y, largeur, label, valeur_01, couleur):
        """Une barre de jauge [0,1] avec son label — pattern répété pour dopamine/
        satiété/hydratation/stimulation/score vocal."""
        self.police_petite.render_to(self.ecran, (x, y), label, COULEUR_TEXTE_ATTENUE)
        y_barre = y + 16
        hauteur_barre = 10
        pygame.draw.rect(self.ecran, (40, 40, 48), (x, y_barre, largeur, hauteur_barre))
        largeur_remplie = int(largeur * max(0.0, min(1.0, valeur_01)))
        if largeur_remplie > 0:
            pygame.draw.rect(self.ecran, couleur, (x, y_barre, largeur_remplie, hauteur_barre))
        pygame.draw.rect(self.ecran, COULEUR_SEPARATEUR, (x, y_barre, largeur, hauteur_barre), width=1)

    def _ligne(self, x, y, texte, couleur=None):
        """Une ligne de texte compacte (police_petite) — le pattern répété pour toutes
        les lignes de type "bilan de nuit" du panneau (v26.0-experimental)."""
        self.police_petite.render_to(self.ecran, (x, y), texte, couleur or COULEUR_TEXTE)
        return y + 18

    def _titre_section(self, x, y, texte):
        self.police_texte.render_to(self.ecran, (x, y), texte, COULEUR_TEXTE)
        return y + 22

    def _separateur(self, x, y, largeur):
        pygame.draw.line(self.ecran, COULEUR_SEPARATEUR, (x, y), (x + largeur, y))
        return y + 10

    def _dessiner_panneau_telemetrie(self, telemetrie: dict):
        """Panneau de télémétrie complet (v26.0-experimental) — parité avec le bilan de
        nuit console (`noyau.py`, `executer_nuit`, bloc `🌙 Jour N [...]`) : mêmes 13
        lignes d'information, recalculées EN CONTINU tick par tick plutôt qu'une fois
        par nuit (l'Arène n'appelle jamais `executer_nuit`, garantie de non-altération).

        Deux catégories de valeurs :
        - la plupart des attributs sont déjà accumulés en continu sur `EtatCognitif`
          pendant la journée (dopamine, jalons, portes, potentiomètre, viscéral,
          métabolisme, mémoire épisodique) — affichées telles quelles, identiques au
          bilan de nuit au même instant.
        - trois valeurs n'existent QUE après un vrai `executer_nuit` (`plasticite_base`,
          le pourcentage de rêve/souvenirs rejoués, le thermostat de neurogenèse) — ce
          panneau affiche à la place un PROXY recalculé avec la même formule mais sans
          attendre la nuit, marqué "(estimé)" pour ne jamais laisser croire à une valeur
          aussi précise qu'un vrai bilan nocturne (voir `_construire_telemetrie` dans
          `lancer_arene.py` pour le calcul exact de ces proxys).

        Toutes les clés sont lues via `.get(..., défaut)` — une clé absente affiche
        simplement "—" plutôt que de faire planter le rendu (une démo ne doit jamais
        crasher sur un tick où une info manque)."""
        x0 = LARGEUR_IMAGE + 16
        largeur_jauge = LARGEUR_PANNEAU - 32
        y = 12

        pygame.draw.rect(self.ecran, (24, 24, 30), (LARGEUR_IMAGE, 0, LARGEUR_PANNEAU, HAUTEUR_IMAGE))

        self.police_titre.render_to(
            self.ecran, (x0, y),
            f"🌙 Jour {telemetrie.get('jour', '—')} [{telemetrie.get('niveau_minigrid', '—')}]",
            COULEUR_TEXTE)
        y += 28

        # --- État Mental / Dopamine ---
        y = self._ligne(x0, y, f"État Mental : {telemetrie.get('etat_mental', '—')} "
                                f"(Dopamine {telemetrie.get('dopamine', 0.0):.2f}/10.0 "
                                f"[{telemetrie.get('pct_dopamine', 0.0):.0f}%])")
        self._dessiner_jauge(x0, y, largeur_jauge, "", telemetrie.get("dopamine", 0.0) / 10.0,
                              COULEURS_JAUGES["dopamine"])
        y += 20

        # --- Plasticité (plasticite_base estimée, proxy hors-nuit) ---
        y = self._ligne(x0, y,
            f"Plasticité : {telemetrie.get('etat_plasticite', '—')} "
            f"(Bus {telemetrie.get('dim_bus', '—')} dims, "
            f"Empreinte {telemetrie.get('empreinte_enfance', 0.0):.2f}, "
            f"Plasticité base ≈{telemetrie.get('plasticite_base_estimee', 0.0):.2f} estimé)")

        # --- Progrès Jalon (DoorKey uniquement) ---
        if telemetrie.get("palier_doorkey") is not None:
            y = self._ligne(x0, y,
                f"Progrès Jalon : 🎯 Palier {telemetrie['palier_doorkey']} "
                f"({telemetrie.get('nom_palier_doorkey', '—')}) — "
                f"{telemetrie.get('succes_palier_jour', 0)}/{telemetrie.get('episodes_jour', 0)} "
                f"épisodes réussis (taux: {telemetrie.get('taux_maitrise_txt', 'N/A')})")
            y = self._ligne(x0, y,
                f"Abnégation : 📿 Sous-Seuil {telemetrie.get('sous_seuil_actuel', '—')} "
                f"({telemetrie.get('sous_seuil_nom', '—')}) — "
                f"{telemetrie.get('succes_sous_seuil', 0)}/{telemetrie.get('succes_par_sous_seuil', 2)} succès "
                f"(complexité x{telemetrie.get('facteur_complexite_jour', 1.0):.1f})")
            y = self._ligne(x0, y,
                f"Mode Décision : {telemetrie.get('mode_decision_txt', '—')} — "
                f"Planif. {telemetrie.get('force_planification', 0.0):.2f}, "
                f"Entropie {telemetrie.get('coeff_entropie', 0.0):.2f}")

        # --- Portes / Quête auto ---
        if telemetrie.get("portes_franchies_jour", 0) > 0:
            y = self._ligne(x0, y, f"Portes : 🚪 {telemetrie['portes_franchies_jour']} franchie(s) aujourd'hui")
        if telemetrie.get("progres_personnel_jour", 0) > 0:
            y = self._ligne(x0, y, f"Quête Auto : 🧭 {telemetrie['progres_personnel_jour']} nouveaux records de proximité")

        # --- Consolidations (proxy, pas de vraie nuit en Arène) ---
        y = self._ligne(x0, y,
            f"Rêve (nuit non dispo.) : 💤 {telemetrie.get('souvenirs_en_attente', 0)} souvenir(s) "
            f"accumulé(s) ce jour, en attente d'une vraie nuit", COULEUR_TEXTE_ATTENUE)

        # --- Potentiomètre ---
        y = self._ligne(x0, y,
            f"Potentiomètre : ⏳ Patience {telemetrie.get('patience_base_jour', '—')} ticks/épisode "
            f"({telemetrie.get('abandons_patience_jour', 0)} abandon(s), "
            f"{telemetrie.get('sursauts_jour', 0)} Sursaut(s), "
            f"min={telemetrie.get('patience_min', '—')})")

        # --- Curiosité JEPA ---
        if telemetrie.get("sous_objectifs_curiosite_jour", 0) > 0:
            y = self._ligne(x0, y, f"Curiosité JEPA : ✨ {telemetrie['sous_objectifs_curiosite_jour']} sous-quête(s) générée(s)")

        y += 4
        y = self._separateur(x0, y, largeur_jauge)

        # --- État Viscéral ---
        y = self._ligne(x0, y,
            f"🍎 Satiété {telemetrie.get('satiete', 0.0):.2f} · "
            f"💧 Hydratation {telemetrie.get('hydratation', 0.0):.2f} · "
            f"✨ Stimulation {telemetrie.get('stimulation', 0.0):.2f} "
            f"(Quête: {telemetrie.get('quete_bio', 'Aucune')})")

        # --- Métabolisme ---
        y = self._ligne(x0, y,
            f"Métabolisme : r_bio {telemetrie.get('r_bio_jour', 0.0):+.3f} — "
            f"{telemetrie.get('food_consommes_jour', 0)} Nourriture(s), "
            f"{telemetrie.get('water_consommes_jour', 0)} Eau(x) — "
            f"effort moyen {telemetrie.get('effort_moyen_jour', 0.0):.3f}")

        # --- Mémoire Épisodique ---
        y = self._ligne(x0, y,
            f"Mémoire Épiso. : 🗺️ {telemetrie.get('souvenirs_spatiaux', 0)} souvenir(s) spatial(aux) actif(s)")

        # --- Erreur JEPA / Récompense / Thermostat (proxy) ---
        y = self._ligne(x0, y,
            f"Erreur JEPA ≈{telemetrie.get('erreur_jepa_proxy', 0.0):.4f} | "
            f"Réc. ≈{telemetrie.get('recompense_proxy', 0.0):.3f} | "
            f"Thermostat (estimé): {telemetrie.get('thermostat_estime', '—')}", COULEUR_TEXTE_ATTENUE)

        y += 4
        y = self._separateur(x0, y, largeur_jauge)

        # --- Curriculum vocal + score ---
        y = self._titre_section(x0, y, "Voix")
        y = self._ligne(x0, y, f"Ère : {telemetrie.get('ere', '—')} · Palier vocal : {telemetrie.get('palier_vocal_nom', '—')}")
        score_vocal = telemetrie.get("score_vocal")
        if score_vocal is not None:
            self._dessiner_jauge(x0, y, largeur_jauge, "Score formants (produit vs visé)",
                                  score_vocal, COULEURS_JAUGES["score_vocal"])
            y += 32
        else:
            y = self._ligne(x0, y, "(silence)", COULEUR_TEXTE_ATTENUE)

        y_pied = HAUTEUR_IMAGE - 20
        self.police_petite.render_to(
            self.ecran, (x0, y_pied),
            f"tick {telemetrie.get('tick_absolu', '—')}",
            COULEUR_TEXTE_ATTENUE)

    def _dessiner_panneau_bus(self, activations: dict):
        """Mini-IRM (v26.0-experimental) : barres verticales des 3 activations du tronc
        cérébral (`bus_latent`, `memoire_actuelle`, `pensee`), une bande sous l'image
        MiniGrid — le pendant pygame du panneau 1 de `irm_cerveau.py`, mais dessiné avec
        des primitives `pygame.draw` plutôt qu'avec matplotlib (voir docstring de module).

        `activations` attend les clés bus_latent/memoire_actuelle/pensee (ndarrays numpy
        1D, même longueur = dim_bus courant) — absentes ou vides, la bande reste vide
        plutôt que de faire planter le rendu, même principe que le panneau télémétrie."""
        y0 = HAUTEUR_IMAGE
        pygame.draw.rect(self.ecran, (24, 24, 30), (0, y0, LARGEUR_FENETRE, HAUTEUR_PANNEAU_BUS))

        bus_latent = activations.get("bus_latent")
        memoire_actuelle = activations.get("memoire_actuelle")
        pensee = activations.get("pensee")
        if bus_latent is None or len(bus_latent) == 0:
            self.police_texte.render_to(
                self.ecran, (16, y0 + 16), "(mini-IRM indisponible)", COULEUR_TEXTE_ATTENUE)
            return

        dim_bus = len(bus_latent)
        marge = 16
        largeur_utile = LARGEUR_FENETRE - 2 * marge
        largeur_groupe = largeur_utile / dim_bus
        largeur_barre = max(1, int(largeur_groupe / 3) - 1)

        pic = max(float(bus_latent.max(initial=0.0)),
                  float(memoire_actuelle.max(initial=0.0)) if memoire_actuelle is not None else 0.0,
                  float(pensee.max(initial=0.0)) if pensee is not None else 0.0,
                  1e-6)
        hauteur_max = HAUTEUR_PANNEAU_BUS - 40  # sous le titre, au-dessus du bord bas

        self.police_petite.render_to(
            self.ecran, (marge, y0 + 4),
            f"🧲 Mini-IRM — bus latent ({dim_bus} dims) · bleu=vision, orange=mémoire, vert=pensée",
            COULEUR_TEXTE_ATTENUE)

        y_base = y0 + HAUTEUR_PANNEAU_BUS - 8
        for i in range(dim_bus):
            x_groupe = marge + i * largeur_groupe
            series = [(bus_latent, COULEUR_BUS_LATENT, 0),
                      (memoire_actuelle, COULEUR_MEMOIRE_ACTUELLE, 1),
                      (pensee, COULEUR_PENSEE, 2)]
            for donnees, couleur, offset in series:
                if donnees is None or i >= len(donnees):
                    continue
                hauteur = int(hauteur_max * max(0.0, min(1.0, float(donnees[i]) / pic)))
                if hauteur <= 0:
                    continue
                x = int(x_groupe + offset * largeur_barre)
                pygame.draw.rect(self.ecran, couleur, (x, y_base - hauteur, largeur_barre, hauteur))

    def _dessiner_bandeau_evenement(self, texte: str):
        """Bandeau d'événement temporaire (v26.0-experimental) — affiché par-dessus le
        haut de l'image MiniGrid quand `lancer_arene.py` détecte un changement ponctuel
        observable en direct (ex: promotion de palier DoorKey, même formulation que les
        prints console de `noyau.py`, lignes 2525/1042/1045). C'est l'appelant qui décide
        combien de ticks ce bandeau reste affiché (compteur décrémenté côté
        `lancer_arene.py`) — cette méthode se contente de le dessiner tant qu'on le lui
        demande, une fois par frame.

        Ne concerne QUE des événements qui peuvent réellement se produire dans l'Arène
        (changement de palier DoorKey) — la promotion de NIVEAU MiniGrid ne peut
        structurellement jamais survenir ici (décidée uniquement par `executer_nuit`,
        jamais appelée dans cette boucle) et n'a donc pas de bandeau correspondant."""
        surface_bandeau = pygame.Surface((LARGEUR_IMAGE, 44), pygame.SRCALPHA)
        surface_bandeau.fill((255, 200, 60, 210))
        self.ecran.blit(surface_bandeau, (0, 0))
        self.police_texte.render_to(self.ecran, (16, 14), texte, (24, 24, 30))

    def dessiner_frame(self, image_minigrid, telemetrie: dict, activations: dict = None,
                        evenement: str = None):
        """Point d'entrée principal, appelé une fois par tick par l'orchestrateur.
        Cadence l'affichage à FPS_ARENE (indépendant de la vitesse réelle des ticks
        traiter_tick, qui n'ont aucune contrainte physique et défileraient sinon trop
        vite pour être lisibles à l'œil — voir plan v24.0, Question ouverte A).

        `activations` (v26.0-experimental, optionnel) : dict bus_latent/memoire_actuelle/
        pensee pour le mini-IRM sous l'image MiniGrid — None = bande vide, ne casse rien
        pour un appelant qui ne le fournit pas encore.

        `evenement` (v26.0-experimental, optionnel) : texte à afficher en bandeau
        temporaire sur l'image MiniGrid (changement de palier DoorKey) — None = pas de
        bandeau ce tick."""
        self.ecran.fill(COULEUR_FOND)
        self._dessiner_image_minigrid(image_minigrid)
        self._dessiner_panneau_telemetrie(telemetrie)
        self._dessiner_panneau_bus(activations or {})
        if evenement:
            self._dessiner_bandeau_evenement(evenement)
        pygame.display.flip()
        self.horloge.tick(FPS_ARENE)

    def fermer(self):
        pygame.quit()
