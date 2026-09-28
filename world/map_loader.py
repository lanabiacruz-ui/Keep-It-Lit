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

       
        self._scaled = None
        self._scaled_size = None

    def draw(self, screen, camera):

        size = (
            camera.scaled_width,
            camera.scaled_height
        )

        if self._scaled_size != size:

            self._scaled = pygame.transform.scale(
                self.image,
                size
            )

            self._scaled_size = size

        screen.blit(
            self._scaled,
            (-camera.x, -camera.y)
        )
