import math

import pygame


class Camera:
  

    def __init__(
        self,
        screen_width,
        screen_height,
        world_width,
        world_height,
        zoom=4,
        smoothing=8
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.world_width = world_width
        self.world_height = world_height

        self.zoom = zoom

        
        self.smoothing = smoothing

        self.scaled_width = int(world_width * zoom)
        self.scaled_height = int(world_height * zoom)

       
        self.x = 0
        self.y = 0

        
        self._fx = 0.0
        self._fy = 0.0

    def update(self, player, dt=None):
    

       
        target_x = player.rect.centerx * self.zoom - self.screen_width / 2
        target_y = player.rect.centery * self.zoom - self.screen_height / 2

        
        max_x = max(0, self.scaled_width - self.screen_width)
        max_y = max(0, self.scaled_height - self.screen_height)

        target_x = max(0, min(target_x, max_x))
        target_y = max(0, min(target_y, max_y))

        if dt is None:

            self._fx = target_x
            self._fy = target_y

        else:

            t = 1 - math.exp(-self.smoothing * dt)

            self._fx += (target_x - self._fx) * t
            self._fy += (target_y - self._fy) * t

        self.x = int(round(self._fx))
        self.y = int(round(self._fy))

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(
            int(rect.x * self.zoom - self.x),
            int(rect.y * self.zoom - self.y),
            int(rect.width * self.zoom),
            int(rect.height * self.zoom)
        )
