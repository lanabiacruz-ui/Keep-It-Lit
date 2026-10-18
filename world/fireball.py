import math
from pathlib import Path

import pygame


HUD_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
)

FIRE_SPEED = 240.0
FIRE_RANGE = 150.0

FIRE_HIT_RADIUS = 3.0

FIRE_SIZE = 7.0
FIRE_LIGHT_RADIUS = 80

STEP = 3.0

BURST_TIME = 0.22

HEAVY_SIZE_MULT = 1.7

HEAVY_DARK = (30, 70, 255)
HEAVY_LIGHT = (225, 245, 255)
HEAVY_AURA = (70, 150, 255)
HEAVY_AURA_CORE = (200, 235, 255)
HEAVY_BURST = (80, 160, 255)
HEAVY_BURST_CORE = (210, 240, 255)
HEAVY_LIGHT_RADIUS = 130
HEAVY_HIT_RADIUS = 5.0

_base_sprite = None
_heavy_base = None
_sprite_cache = {}


def _load_base():

    global _base_sprite

    if _base_sprite is None:

        try:

            _base_sprite = pygame.image.load(
                str(HUD_DIR / "bola_fuego.png")
            ).convert_alpha()

        except (pygame.error, FileNotFoundError):

            _base_sprite = pygame.Surface((32, 32), pygame.SRCALPHA)

            pygame.draw.circle(_base_sprite, (230, 90, 30), (22, 16), 9)
            pygame.draw.circle(_base_sprite, (255, 190, 70), (22, 16), 6)
            pygame.draw.circle(_base_sprite, (255, 245, 200), (22, 16), 3)

    return _base_sprite


def _load_heavy_base():

    global _heavy_base

    if _heavy_base is None:

        base = _load_base()

        tinted = base.copy()

        for x in range(tinted.get_width()):
            for y in range(tinted.get_height()):

                r, g, b, a = tinted.get_at((x, y))

                if a == 0:
                    continue

                k = min(1.0, (0.3 * r + 0.59 * g + 0.11 * b) / 200)

                tinted.set_at((x, y), (
                    round(HEAVY_DARK[0] + (HEAVY_LIGHT[0] - HEAVY_DARK[0]) * k),
                    round(HEAVY_DARK[1] + (HEAVY_LIGHT[1] - HEAVY_DARK[1]) * k),
                    round(HEAVY_DARK[2] + (HEAVY_LIGHT[2] - HEAVY_DARK[2]) * k),
                    a
                ))

        _heavy_base = tinted

    return _heavy_base


def _get_sprite(zoom, angle, heavy=False):

    deg = round(-math.degrees(angle) / 10) * 10

    key = (zoom, deg, heavy)

    if key not in _sprite_cache:

        base = _load_heavy_base() if heavy else _load_base()

        mult = HEAVY_SIZE_MULT if heavy else 1.0

        size = max(4, int(FIRE_SIZE * mult * zoom))

        sprite = pygame.transform.smoothscale(base, (size, size))

        _sprite_cache[key] = pygame.transform.rotate(sprite, deg)

    return _sprite_cache[key]


class Fireball:

    def __init__(self, x, y, angle, damage, heavy=False):

        self.x = float(x)
        self.y = float(y)

        self.angle = angle
        self.damage = damage

        self.heavy = heavy

        self.vx = math.cos(angle) * FIRE_SPEED
        self.vy = math.sin(angle) * FIRE_SPEED

        self.left = FIRE_RANGE
        self.dead = False

    def update(self, dt, targets, walkable):

        if self.dead:
            return None

        dist = math.hypot(self.vx, self.vy) * dt

        steps = max(1, math.ceil(dist / STEP))

        step = dist / steps

        dx = math.cos(self.angle) * step
        dy = math.sin(self.angle) * step

        hit_radius = HEAVY_HIT_RADIUS if self.heavy else FIRE_HIT_RADIUS

        grow = int(hit_radius * 2)

        for _ in range(steps):

            self.x += dx
            self.y += dy

            self.left -= step

            for target in targets:

                if target.rect.inflate(grow, grow).collidepoint(
                    self.x,
                    self.y
                ):

                    self.dead = True

                    return target

            if not walkable(self.x, self.y) or self.left <= 0:

                self.dead = True

                return None

        return None

    def light_source(self):

        radius = HEAVY_LIGHT_RADIUS if self.heavy else FIRE_LIGHT_RADIUS

        return (self.x, self.y, radius)

    def draw(self, screen, camera):

        sprite = _get_sprite(camera.zoom, self.angle, self.heavy)

        sx = self.x * camera.zoom - camera.x
        sy = self.y * camera.zoom - camera.y

        if self.heavy:

            r = int(FIRE_SIZE * HEAVY_SIZE_MULT * camera.zoom * 0.9)

            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)

            pygame.draw.circle(halo, (*HEAVY_AURA, 100), (r, r), r)
            pygame.draw.circle(halo, (*HEAVY_AURA_CORE, 110), (r, r), r // 2)

            screen.blit(halo, halo.get_rect(center=(int(sx), int(sy))))

        screen.blit(sprite, sprite.get_rect(center=(int(sx), int(sy))))


class FireBurst:

    def __init__(self, x, y, heavy=False):

        self.x = float(x)
        self.y = float(y)

        self.heavy = heavy

        self.t = 0.0

    @property
    def done(self):

        return self.t >= BURST_TIME

    def update(self, dt):

        self.t += dt

    def draw(self, screen, camera):

        k = min(1.0, self.t / BURST_TIME)

        scale = 1.8 if self.heavy else 1.0

        radius = int((3 + 9 * k) * scale * camera.zoom)

        size = radius * 2 + 4

        layer = pygame.Surface((size, size), pygame.SRCALPHA)

        alpha = int(220 * (1.0 - k))

        ring = HEAVY_BURST if self.heavy else (255, 150, 50)
        core = HEAVY_BURST_CORE if self.heavy else (255, 230, 150)

        pygame.draw.circle(
            layer,
            (*ring, alpha),
            (size // 2, size // 2),
            radius,
            max(2, int(radius * 0.35))
        )

        pygame.draw.circle(
            layer,
            (*core, int(alpha * 0.8)),
            (size // 2, size // 2),
            max(1, int(radius * 0.45))
        )

        sx = self.x * camera.zoom - camera.x
        sy = self.y * camera.zoom - camera.y

        screen.blit(layer, layer.get_rect(center=(int(sx), int(sy))))
