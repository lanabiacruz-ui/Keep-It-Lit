import pygame
from pathlib import Path

HUD_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
)


class MatchItem:

    WORLD_SIZE = 14           
    INTERACT_DISTANCE = 45    

    def __init__(self, x, y):

        self.original = pygame.image.load(
            str(HUD_DIR / "item_fosforo.png")
        ).convert_alpha()

        self.e_icon = pygame.image.load(
            str(HUD_DIR / "E.png")
        ).convert_alpha()

        self.rect = pygame.Rect(0, 0, self.WORLD_SIZE, self.WORLD_SIZE)
        self.rect.center = (x, y)

        self._scaled = None
        self._scaled_zoom = None

    def is_near(self, player):

        return (
            pygame.Vector2(player.rect.center).distance_to(
                self.rect.center
            ) <= self.INTERACT_DISTANCE
        )

    def _get_sprite(self, zoom):

        if self._scaled_zoom != zoom:

            size = int(self.WORLD_SIZE * zoom)

            self._scaled = pygame.transform.smoothscale(
                self.original,
                (size, size)
            )

            self._scaled_zoom = zoom

        return self._scaled

    def draw(self, screen, camera):

        sprite = self._get_sprite(camera.zoom)

        dest = camera.apply(self.rect)

        screen.blit(sprite, sprite.get_rect(center=dest.center))

    def draw_prompt(self, screen, camera):

        dest = camera.apply(self.rect)

        screen.blit(
            self.e_icon,
            self.e_icon.get_rect(midbottom=(dest.centerx, dest.top - 6))
        )