import pygame


class PlayerLight:

    def __init__(self, screen_size, darkness_alpha=225):
        self.screen_size = tuple(screen_size)
        self.darkness_alpha = int(darkness_alpha)

        self._darkness = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )


        self._cache = {}
        self._soft_cache = {}
        self._glow_cache = {}
        self._base = None

    LIGHT_STEP = 4
    BASE_RADIUS = 256
    MAX_CACHE = 120

    def _get_light(self, radius):

        radius = max(
            self.LIGHT_STEP,
            int(round(radius / self.LIGHT_STEP)) * self.LIGHT_STEP
        )

        light = self._cache.get(radius)

        if light is None:

            if len(self._cache) >= self.MAX_CACHE:
                self._cache.clear()

            light = self._create_light_surface(radius)
            self._cache[radius] = light

        return light

    def _create_light_surface(self, radius):

        if self._base is None:
            self._base = self._draw_light(self.BASE_RADIUS)

        if radius == self.BASE_RADIUS:
            return self._base

        size = radius * 2 + 2

        return pygame.transform.smoothscale(self._base, (size, size))

    def _draw_light(self, radius):
        size = radius * 2 + 2

        light = pygame.Surface(
            (size, size),
            pygame.SRCALPHA
        )

        center = radius + 1

        for r in range(radius, -1, -1):

            t = r / radius
            x = max(0.0, min(1.0, (t - 0.15) / 0.85))
            strength = 1.0 - x * x * (3 - 2 * x)

            alpha = max(0, min(255, int(255 * strength)))

            pygame.draw.circle(
                light,
                (0, 0, 0, alpha),
                (center, center),
                r
            )

        return light

    def add_glow(self, screen, camera, wx, wy, radius, color, intensity):

        radius = int(radius)

        if radius < 8 or intensity <= 0.01:
            return

        step = max(8, int(round(radius / 8)) * 8)
        level = max(1, int(round(min(1.0, intensity) * 12)))

        key = (step, color, level)

        spr = self._glow_cache.get(key)

        if spr is None:

            if len(self._glow_cache) > 160:
                self._glow_cache.clear()

            size = step * 2
            spr = pygame.Surface((size, size))
            spr.fill((0, 0, 0))

            k = level / 12.0

            for r in range(step, 0, -2):

                t = 1.0 - r / step
                f = t * t * k * 0.55

                pygame.draw.circle(
                    spr,
                    (int(color[0] * f), int(color[1] * f), int(color[2] * f)),
                    (step, step), r
                )

            self._glow_cache[key] = spr

        sx = int(wx * camera.zoom - camera.x)
        sy = int(wy * camera.zoom - camera.y)

        screen.blit(
            spr, spr.get_rect(center=(sx, sy)),
            special_flags=pygame.BLEND_RGB_ADD
        )

    def _soft_rect(self, w, h, feather, strength):
        """Rectangulo iluminado con degradado suave y esquinas redondeadas.

        La zona central resta toda la oscuridad; el borde hace una transicion
        gradual hacia la oscuridad exterior, tambien en las cuatro esquinas.
        """
        w = max(1, int(w))
        h = max(1, int(h))
        feather = max(1, int(feather))
        strength = max(0.0, min(1.0, float(strength)))

        peak = int(self.darkness_alpha * strength)
        key = (w, h, feather, peak)

        cached = self._soft_cache.get(key)
        if cached is not None:
            return cached

        surf = pygame.Surface(
            (w + feather * 2, h + feather * 2),
            pygame.SRCALPHA
        )

        # Se dibuja desde el borde exterior hacia el interior. Cada capa
        # aumenta suavemente la opacidad que se resta de la oscuridad.
        for i in range(feather, -1, -1):
            t = 1.0 - (i / float(feather))
            smooth = t * t * (3.0 - 2.0 * t)
            alpha = max(0, min(255, int(peak * smooth)))

            rect = pygame.Rect(
                feather - i,
                feather - i,
                w + i * 2,
                h + i * 2
            )
            radius = min(max(1, feather // 2), rect.width // 2, rect.height // 2)

            pygame.draw.rect(
                surf,
                (0, 0, 0, alpha),
                rect,
                border_radius=radius
            )

        if len(self._soft_cache) > 180:
            self._soft_cache.clear()

        self._soft_cache[key] = surf
        return surf

    def draw(self, screen, camera, sources, lit_rects=()):

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

        screen_w, screen_h = self.screen_size

        for wx, wy, radius in sources:

            light = self._get_light(int(radius))

            sx = int(wx * camera.zoom - camera.x)
            sy = int(wy * camera.zoom - camera.y)

            half = light.get_width() // 2

            if (
                sx + half < 0 or sx - half > screen_w
                or sy + half < 0 or sy - half > screen_h
            ):
                continue

            self._darkness.blit(
                light,
                light.get_rect(center=(sx, sy)),
                special_flags=pygame.BLEND_RGBA_SUB
            )

        screen.blit(
            self._darkness,
            (0, 0)
        )

