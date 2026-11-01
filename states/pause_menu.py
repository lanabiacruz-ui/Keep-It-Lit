import math
import time
from pathlib import Path

import pygame


class PauseMenu:

    IMG_W = 1637
    IMG_H = 961

    # Coordenadas sobre pantallaesc_skins.png (se genera con
    # tools/make_pause_panel.py a partir de pantallaesc.png)
    BUTTONS = {
        "settings": (569, 345, 1063, 423),
        "enemies": (569, 457, 1063, 535),
        "skins": (569, 568, 802, 646),
        "achievements": (828, 568, 1063, 646),
        "back": (569, 681, 1063, 759),
    }

    # Botones cuyo texto NO esta en la imagen (se dibuja por codigo).
    # Vacio porque "Skins" y "Logros" ya van escritos en el png.
    # Si hiciera falta de nuevo: {"skins": "Skins", "achievements": "Logros"}
    LABELS = {}

    LABEL_COLOR = (74, 79, 90)

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()

        # cantidad de recompensas de la enciclopedia sin cobrar
        self.pending_enemies = 0

        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "hud"
            / "pantallaesc_skins.png"
        )

        self.background = pygame.image.load(image_path).convert_alpha()

        self.resize()

    def _make_label_font(self):
        font = pygame.font.Font(None, max(20, round(52 * self.sy)))
        font.set_italic(True)
        return font

    def resize(self):
        self.width, self.height = self.screen.get_size()

        self.background_scaled = pygame.transform.smoothscale(
            self.background,
            (self.width, self.height),
        )

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        self.label_font = self._make_label_font()

        self.button_rects = {}

        for key, (x1, y1, x2, y2) in self.BUTTONS.items():

            self.button_rects[key] = pygame.Rect(
                round(x1 * self.sx),
                round(y1 * self.sy),
                round((x2 - x1) * self.sx),
                round((y2 - y1) * self.sy),
            )

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "resume"

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                for name, rect in self.button_rects.items():

                    if rect.collidepoint(event.pos):
                        return name

        return None

    def update(self, dt):
        return None

    def draw(self):
        self.screen.blit(
            self.background_scaled,
            (0, 0)
        )

        self._draw_labels()

        if self.pending_enemies > 0:
            self._draw_pending_badge()

    def _draw_labels(self):
        for key, text in self.LABELS.items():
            rect = self.button_rects[key]

            surf = self.label_font.render(text, True, self.LABEL_COLOR)

            self.screen.blit(surf, surf.get_rect(center=rect.center))

    def _draw_pending_badge(self):
        rect = self.button_rects["enemies"]

        beat = 0.5 + 0.5 * math.sin(time.monotonic() * 6.0)

        radius = max(8, round((13 + 2 * beat) * self.sy))

        center = (rect.right - round(26 * self.sx), rect.top + round(4 * self.sy))

        pygame.draw.circle(self.screen, (60, 40, 8), center, radius + 3)
        pygame.draw.circle(self.screen, (255, 205, 70), center, radius)

        font = pygame.font.Font(None, max(16, round(radius * 1.6)))
        text = font.render(str(min(99, self.pending_enemies)), True, (60, 34, 4))

        self.screen.blit(text, text.get_rect(center=center))