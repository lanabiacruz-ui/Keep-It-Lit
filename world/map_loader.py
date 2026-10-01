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

        # Antes se agrandaba el mapa entero una vez (1920x1080 x4 =
        # 7680x4320, unos 130 MB y un tirón al arrancar). Ahora se
        # agranda solo el pedazo que se ve, con el mismo resultado.
        zoom = camera.zoom

        sx = camera.x // zoom
        sy = camera.y // zoom

        off_x = camera.x - sx * zoom
        off_y = camera.y - sy * zoom

        w = min(
            self.width - sx,
            -(-(screen.get_width() + off_x) // zoom) + 1
        )

        h = min(
            self.height - sy,
            -(-(screen.get_height() + off_y) // zoom) + 1
        )

        if w <= 0 or h <= 0:
            return

        piece = self.image.subsurface(
            pygame.Rect(sx, sy, w, h)
        )

        piece = pygame.transform.scale(
            piece,
            (w * zoom, h * zoom)
        )

        screen.blit(piece, (-off_x, -off_y))