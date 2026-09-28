import pygame
from pathlib import Path


class WorldMap:

    def __init__(self):

        base = Path(__file__).resolve().parent.parent


       
        map_path = base / "mapabeta.png"

        map_path = (
            base
            / "assets"
            / "maps"
            / "region_01"
            / "mapabeta.png"
        )


        self.image = pygame.image.load(
            str(map_path)
        ).convert()


     
        self.width = self.image.get_width()
        self.height = self.image.get_height()

      

        self.width = self.image.get_width()
        self.height = self.image.get_height()


        self.rect = self.image.get_rect(
            topleft=(0, 0)
        )

    def draw(self, screen, camera):

       
        scaled_map = pygame.transform.scale(
            self.image,
                (camera.scaled_width, camera.scaled_height)
        )

        screen.blit(
            scaled_map,
                (-int(camera.x), -int(camera.y))
        )

