import pygame
from pathlib import Path


class WorldMap:
    def __init__(self):
        base = Path(__file__).resolve().parent.parent

        # Cargar mapa
        map_path = base / "mapabeta.png"

        self.image = pygame.image.load(
            str(map_path)
        ).convert()

        # Tamaño mapa
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # Rect del mapa
        self.rect = self.image.get_rect(
            topleft=(0, 0)
        )

    def draw(self, screen, camera):
        # Dibuja mapa
        screen.blit(
            self.image,
            (
                -camera.x,
                -camera.y
            )
        )