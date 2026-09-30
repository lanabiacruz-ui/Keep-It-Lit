import pygame


class PlayerLight:

    def __init__(self, screen_size, darkness_alpha=245):
        self.screen_size = tuple(screen_size)
        self.darkness_alpha = int(darkness_alpha)

        self._darkness = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )


        self._cache = {}

    def _get_light(self, radius):

        if radius not in self._cache:
            self._cache[radius] = self._create_light_surface(radius)

        return self._cache[radius]

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

    def draw(self, screen, camera, sources):


        self._darkness.fill(
            (0, 0, 0, self.darkness_alpha)
        )

        for wx, wy, radius in sources:

            light = self._get_light(int(radius))

            sx = int(wx * camera.zoom - camera.x)
            sy = int(wy * camera.zoom - camera.y)

            self._darkness.blit(
                light,
                light.get_rect(center=(sx, sy)),
                special_flags=pygame.BLEND_RGBA_SUB
            )

        screen.blit(
            self._darkness,
            (0, 0)
        )