import math

import pygame
from pathlib import Path


class WorldMap:

    def __init__(self):

        base = Path(__file__).resolve().parent.parent

        map_path = (
            base
            / "assets"
            / "maps"
            / "region_01"
            / "mapa.png"
        )

        self.image = pygame.image.load(
            str(map_path)
        ).convert()

        self.width = self.image.get_width()
        self.height = self.image.get_height()

        self.rect = self.image.get_rect(
            topleft=(0, 0)
        )

    def draw(self, screen, camera):

        zoom = max(1, camera.zoom)

        screen_w = screen.get_width()
        screen_h = screen.get_height()

        x0 = int(camera.x // zoom)
        y0 = int(camera.y // zoom)
        x1 = int(math.ceil((camera.x + screen_w) / zoom))
        y1 = int(math.ceil((camera.y + screen_h) / zoom))

        src = pygame.Rect(x0, y0, x1 - x0, y1 - y0).clip(self.rect)

        if src.width <= 0 or src.height <= 0:
            screen.fill((0, 0, 0))
            return

        piece = pygame.transform.scale(
            self.image.subsurface(src),
            (
                int(math.ceil(src.width * zoom)),
                int(math.ceil(src.height * zoom)),
            )
        )

        dest = (
            int(round(src.x * zoom - camera.x)),
            int(round(src.y * zoom - camera.y))
        )

        covered = pygame.Rect(dest, piece.get_size())

        if not covered.contains(screen.get_rect()):
            screen.fill((0, 0, 0))

        screen.blit(piece, dest)