from pathlib import Path

import pygame


class PauseMenu:
    """Menu de pausa mostrado encima de la partida."""

    IMG_W = 1637
    IMG_H = 961

    # Coordenadas de los botones sobre pantallaesc.png
    BUTTONS = {
        "settings": (569, 402, 1063, 480),
        "enemies": (569, 514, 1063, 592),
        "back": (569, 627, 1063, 705),
    }

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()

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

        # ESC dentro del menú = volver a jugar
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "resume"

        # Click en los botones
        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                for name, rect in self.button_rects.items():

                    if rect.collidepoint(event.pos):
                        return name

        return None

    def update(self, dt):
        # No actualizamos la partida mientras este menú está abierto.
        return None

    def draw(self):
        self.screen.blit(
            self.background_scaled,
            (0, 0)
        )