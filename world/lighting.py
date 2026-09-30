import pygame


class PlayerLight:

    def __init__(self, screen_size, radius=220, darkness_alpha=245):
        self.screen_size = tuple(screen_size)
        self.radius = int(radius)
        self.darkness_alpha = int(darkness_alpha)
      
        self._darkness = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )

       
        self._light = self._create_light_surface(self.radius)

    def _create_light_surface(self, radius):
        size = radius * 2 + 2

        light = pygame.Surface(
            (size, size),
            pygame.SRCALPHA
        )

        center = radius + 1

       
        for r in range(radius, -1, -2):

            strength = 1.0 - (r / radius)

            alpha = max(
                0,
                min(255, int(255 * strength))
            )

            pygame.draw.circle(
                light,
                (0, 0, 0, alpha),
                (center, center),
                r
            )

        return light

    def draw(self, screen, player, camera):

        
        self._darkness.fill(
            (0, 0, 0, self.darkness_alpha)
        )

       
        player_screen = camera.apply(player.rect)

        light_center = player_screen.center

       
        light_rect = self._light.get_rect(
            center=light_center
        )

        
        self._darkness.blit(
            self._light,
            light_rect,
            special_flags=pygame.BLEND_RGBA_SUB
        )

        screen.blit(
            self._darkness,
            (0, 0)
        )

        pygame.draw.circle(
            screen,
            (255, 225, 130),
            light_center,
            3
        )