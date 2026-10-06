import pygame


class PlayerLight:

    def __init__(self, screen_size, darkness_alpha=200):
        self.screen_size = tuple(screen_size)
        self.darkness_alpha = int(darkness_alpha)

        self._darkness = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )


        self._cache = {}
        self._soft_cache = {}

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

    def _soft_rect(self, w, h, feather, strength):
        """Cuadrado iluminado con el borde difuminado (se arma una vez y
        queda guardado). Lo que se resta de la oscuridad es el alfa."""

        strength = max(0.0, min(1.0, strength))

        key = (w, h, feather, int(round(strength * 10)))

        if key not in self._soft_cache:

            peak = int(self.darkness_alpha * round(strength * 10) / 10)

            surf = pygame.Surface(
                (w + feather * 2, h + feather * 2),
                pygame.SRCALPHA
            )

            surf.fill((0, 0, 0, peak), pygame.Rect(feather, feather, w, h))

            for i in range(feather):

                t = i / feather
                t = t * t * (3 - 2 * t)

                ring = pygame.Rect(
                    i, i,
                    w + (feather - i) * 2,
                    h + (feather - i) * 2
                )

                pygame.draw.rect(
                    surf, (0, 0, 0, int(peak * t)), ring, width=1
                )

            self._soft_cache[key] = surf

        return self._soft_cache[key]

    def draw(self, screen, camera, sources, lit_rects=()):
        """lit_rects: [(Rect del mundo, fuerza 0.0 a 1.0, borde)].
        Adentro del rect no hay oscuridad (1.0 = todo iluminado) y el
        borde (en unidades del mundo) se difumina hacia la oscuridad."""

        self._darkness.fill(
            (0, 0, 0, self.darkness_alpha)
        )

        for world_rect, strength, feather in lit_rects:

            f = max(1, int(feather * camera.zoom))

            w = int(world_rect.width * camera.zoom)
            h = int(world_rect.height * camera.zoom)

            surf = self._soft_rect(w, h, f, strength)

            self._darkness.blit(
                surf,
                (
                    int(world_rect.x * camera.zoom - camera.x) - f,
                    int(world_rect.y * camera.zoom - camera.y) - f
                ),
                special_flags=pygame.BLEND_RGBA_SUB
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