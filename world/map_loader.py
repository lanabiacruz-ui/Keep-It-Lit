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

        # Se agranda solo el pedazo visible del mapa (no el mapa entero).
        # El rectangulo de origen se recorta al tamano de la imagen: con el
        # sacudon de camara, camera.x/y pueden quedar negativos o pasarse
        # del borde, y subsurface() falla si el Rect sale de la superficie.
        zoom = max(1, int(camera.zoom))

        screen_w = screen.get_width()
        screen_h = screen.get_height()

        # Region visible en pixeles del mapa original (redondeada hacia
        # afuera para cubrir toda la pantalla).
        x0 = camera.x // zoom
        y0 = camera.y // zoom
        x1 = -(-(camera.x + screen_w) // zoom)
        y1 = -(-(camera.y + screen_h) // zoom)

        src = pygame.Rect(x0, y0, x1 - x0, y1 - y0).clip(self.rect)

        if src.width <= 0 or src.height <= 0:
            screen.fill((0, 0, 0))
            return

        piece = pygame.transform.scale(
            self.image.subsurface(src),
            (src.width * zoom, src.height * zoom)
        )

        dest = (
            src.x * zoom - camera.x,
            src.y * zoom - camera.y
        )

        # Si el mapa no cubre toda la pantalla (borde + sacudon), se
        # limpia el fondo para no dejar restos del cuadro anterior.
        covered = pygame.Rect(dest, piece.get_size())

        if not covered.contains(screen.get_rect()):
            screen.fill((0, 0, 0))

        screen.blit(piece, dest)