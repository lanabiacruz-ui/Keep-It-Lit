import pygame
from pathlib import Path


class WorldMap:
    def __init__(self):
        base = Path(__file__).resolve().parent.parent

        # Cargar el mapa
        map_path = base / "assets" / "maps" / "region_01" / "mapabeta.png"

        self.image = pygame.image.load(
            str(map_path)
        ).convert()

        # Tamaño del mapa
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # Rectángulo del mapa
        self.rect = self.image.get_rect(
            topleft=(0, 0)
        )

    def draw(self, screen, camera):
        # Dibujar el mapa teniendo en cuenta la cámara
        screen.blit(
            self.image,
            (
                -camera.x,
                -camera.y
            )
        )
        )
