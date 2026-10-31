import math
import time
from pathlib import Path

import pygame


class PauseMenu:

    IMG_W = 1637
    IMG_H = 961

    BUTTONS = {
        "settings": (569, 402, 1063, 480),
        "enemies": (569, 514, 1063, 592),
        "back": (569, 627, 1063, 705),
    }

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
            / "pantallaesc.png"
        )

        self.background = pygame.image.load(image_path).convert_alpha()

        self.resize()

    def resize(self):
        self.width, self.height = self.screen.get_size()

        self.background_scaled = pygame.transform.smoothscale(
            self.background,
            (self.width, self.height),
        )

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

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

        if self.pending_enemies > 0:
            self._draw_pending_badge()

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