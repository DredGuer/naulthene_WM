"""
L'Arène Visuelle (V24.0, expérimental) — le rendu de la Démo Live.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir le plan
v24.0 et `readme.md` (section "L'Arène & Démo Live") pour le contexte narratif complet.

Pur module de RENDU (pygame) — aucune dépendance au réseau de neurones ni au moteur
MiniGrid. Il reçoit une image déjà rendue (`etat.env.render()`, `render_mode="rgb_array"`)
et un dictionnaire de télémétrie déjà calculé, et se contente de les dessiner dans une
fenêtre composite unique : l'image MiniGrid à gauche, un panneau de jauges/texte à
droite (dopamine, jauges biologiques, curriculum MiniGrid, curriculum vocal, mot visé
vs score de formants). C'est `lancer_arene.py` (l'orchestrateur) qui lit `EtatCognitif`
et construit ce dictionnaire — cette séparation garde le rendu testable en isolation,
sans avoir à faire tourner un vrai agent pour vérifier que les jauges se dessinent bien.
"""

import pygame
import pygame.freetype

LARGEUR_IMAGE = 512   # image MiniGrid agrandie depuis les 256×256 natifs (render_mode="rgb_array")
LARGEUR_PANNEAU = 380  # panneau de télémétrie à droite
HAUTEUR_FENETRE = 512
LARGEUR_FENETRE = LARGEUR_IMAGE + LARGEUR_PANNEAU

FPS_ARENE = 10  # aligné sur metadata["render_fps"] natif de MiniGrid (minigrid_env.py)

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
        surface = pygame.transform.scale(surface, (LARGEUR_IMAGE, HAUTEUR_FENETRE))
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

    def _dessiner_panneau_telemetrie(self, telemetrie: dict):
        """`telemetrie` attend les clés : dopamine, satiete, hydratation, stimulation
        (floats [0,1]), niveau_minigrid (str), palier_doorkey (int ou None), ere (str),
        palier_vocal_nom (str), score_vocal (float [0,1] ou None), jour (int),
        tick_absolu (int). Toutes optionnelles — une clé absente affiche simplement
        "—" plutôt que de faire planter le rendu (une démo ne doit jamais crasher sur
        un tick où une info manque)."""
        x0 = LARGEUR_IMAGE + 16
        largeur_jauge = LARGEUR_PANNEAU - 32
        y = 16

        pygame.draw.rect(self.ecran, (24, 24, 30), (LARGEUR_IMAGE, 0, LARGEUR_PANNEAU, HAUTEUR_FENETRE))

        self.police_titre.render_to(self.ecran, (x0, y), "État Interne", COULEUR_TEXTE)
        y += 34

        self._dessiner_jauge(x0, y, largeur_jauge, "🧠 Dopamine",
                              telemetrie.get("dopamine", 0.0) / 10.0, COULEURS_JAUGES["dopamine"])
        y += 40
        self._dessiner_jauge(x0, y, largeur_jauge, "🍎 Satiété",
                              telemetrie.get("satiete", 0.0), COULEURS_JAUGES["satiete"])
        y += 40
        self._dessiner_jauge(x0, y, largeur_jauge, "💧 Hydratation",
                              telemetrie.get("hydratation", 0.0), COULEURS_JAUGES["hydratation"])
        y += 40
        self._dessiner_jauge(x0, y, largeur_jauge, "✨ Stimulation",
                              telemetrie.get("stimulation", 0.0), COULEURS_JAUGES["stimulation"])
        y += 48

        pygame.draw.line(self.ecran, COULEUR_SEPARATEUR, (x0, y), (x0 + largeur_jauge, y))
        y += 16

        self.police_titre.render_to(self.ecran, (x0, y), "Curriculum", COULEUR_TEXTE)
        y += 30
        self.police_texte.render_to(
            self.ecran, (x0, y),
            f"MiniGrid : {telemetrie.get('niveau_minigrid', '—')}", COULEUR_TEXTE)
        y += 22
        palier_dk = telemetrie.get("palier_doorkey")
        if palier_dk is not None:
            self.police_texte.render_to(self.ecran, (x0, y), f"Palier DoorKey : {palier_dk}/7", COULEUR_TEXTE)
            y += 22
        self.police_texte.render_to(
            self.ecran, (x0, y),
            f"Ère : {telemetrie.get('ere', '—')}", COULEUR_TEXTE)
        y += 22
        self.police_texte.render_to(
            self.ecran, (x0, y),
            f"Palier vocal : {telemetrie.get('palier_vocal_nom', '—')}", COULEUR_TEXTE)
        y += 36

        pygame.draw.line(self.ecran, COULEUR_SEPARATEUR, (x0, y), (x0 + largeur_jauge, y))
        y += 16

        self.police_titre.render_to(self.ecran, (x0, y), "Voix", COULEUR_TEXTE)
        y += 30
        score_vocal = telemetrie.get("score_vocal")
        if score_vocal is not None:
            self._dessiner_jauge(x0, y, largeur_jauge, "Score formants (produit vs visé)",
                                  score_vocal, COULEURS_JAUGES["score_vocal"])
            y += 40
        else:
            self.police_texte.render_to(self.ecran, (x0, y), "(silence)", COULEUR_TEXTE_ATTENUE)
            y += 24

        y = HAUTEUR_FENETRE - 40
        self.police_petite.render_to(
            self.ecran, (x0, y),
            f"Jour {telemetrie.get('jour', '—')} · tick {telemetrie.get('tick_absolu', '—')}",
            COULEUR_TEXTE_ATTENUE)

    def dessiner_frame(self, image_minigrid, telemetrie: dict):
        """Point d'entrée principal, appelé une fois par tick par l'orchestrateur.
        Cadence l'affichage à FPS_ARENE (indépendant de la vitesse réelle des ticks
        traiter_tick, qui n'ont aucune contrainte physique et défileraient sinon trop
        vite pour être lisibles à l'œil — voir plan v24.0, Question ouverte A)."""
        self.ecran.fill(COULEUR_FOND)
        self._dessiner_image_minigrid(image_minigrid)
        self._dessiner_panneau_telemetrie(telemetrie)
        pygame.display.flip()
        self.horloge.tick(FPS_ARENE)

    def fermer(self):
        pygame.quit()
