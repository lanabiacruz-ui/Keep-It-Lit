"""Bolas de fuego de la antorcha (se activan con la tecla G).

Todo en unidades del mundo, igual que el resto de coordenadas. Para
balancear se cambian los numeros de aca abajo (el dano y lo que gasta
de luz estan en states/new_game.py: FIRE_DAMAGE, FIRE_COST...).

Imagen (opcional: si falta se dibuja una bolita naranja):

  assets/maps/hud/bola_fuego.png   32x32  (mira hacia la derecha)
"""

import math
from pathlib import Path

import pygame


HUD_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
)

# Que tan rapido vuela (unidades del mundo por segundo) y hasta donde
# llega antes de apagarse.
FIRE_SPEED = 240.0
FIRE_RANGE = 150.0

# Radio con el que toca a los enemigos / puertas / cofres.
FIRE_HIT_RADIUS = 3.0

# Tamano dibujado (unidades del mundo) y cuanta luz tira alrededor
# (radio en pixeles de pantalla).
FIRE_SIZE = 7.0
FIRE_LIGHT_RADIUS = 80

# Cada cuanto se revisan choques mientras vuela (para no atravesar
# enemigos finitos cuando el frame tarda).
STEP = 3.0

# Cuanto dura el estallido al chocar.
BURST_TIME = 0.22

_base_sprite = None
_sprite_cache = {}


def _load_base():
    """Imagen original de la bola (se carga una sola vez)."""

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


def _get_sprite(zoom, angle):
    """Sprite ya escalado al zoom y girado hacia donde vuela."""

    deg = round(-math.degrees(angle) / 10) * 10

    key = (zoom, deg)

    if key not in _sprite_cache:

        base = _load_base()

        size = max(4, int(FIRE_SIZE * zoom))

        sprite = pygame.transform.smoothscale(base, (size, size))

        _sprite_cache[key] = pygame.transform.rotate(sprite, deg)

    return _sprite_cache[key]


class Fireball:

    def __init__(self, x, y, angle, damage):

        self.x = float(x)
        self.y = float(y)

        self.angle = angle
        self.damage = damage

        self.vx = math.cos(angle) * FIRE_SPEED
        self.vy = math.sin(angle) * FIRE_SPEED

        self.left = FIRE_RANGE
        self.dead = False

    def update(self, dt, targets, walkable):
        """Avanza. Devuelve el objetivo que toco (o None).

        targets  -> cosas con .rect en coordenadas del mundo
        walkable -> funcion (x, y) -> True si ahi no hay pared
        """

        if self.dead:
            return None

        dist = math.hypot(self.vx, self.vy) * dt

        steps = max(1, math.ceil(dist / STEP))

        step = dist / steps

        dx = math.cos(self.angle) * step
        dy = math.sin(self.angle) * step

        grow = int(FIRE_HIT_RADIUS * 2)

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
        """(x, y, radio) para el sistema de luces."""

        return (self.x, self.y, FIRE_LIGHT_RADIUS)

    def draw(self, screen, camera):

        sprite = _get_sprite(camera.zoom, self.angle)

        sx = self.x * camera.zoom - camera.x
        sy = self.y * camera.zoom - camera.y

        screen.blit(sprite, sprite.get_rect(center=(int(sx), int(sy))))


class FireBurst:
    """Estallido corto donde la bola choco."""

    def __init__(self, x, y):

        self.x = float(x)
        self.y = float(y)

        self.t = 0.0

    @property
    def done(self):

        return self.t >= BURST_TIME

    def update(self, dt):

        self.t += dt

    def draw(self, screen, camera):

        k = min(1.0, self.t / BURST_TIME)

        radius = int((3 + 9 * k) * camera.zoom)

        size = radius * 2 + 4

        layer = pygame.Surface((size, size), pygame.SRCALPHA)

        alpha = int(220 * (1.0 - k))

        pygame.draw.circle(
            layer,
            (255, 150, 50, alpha),
            (size // 2, size // 2),
            radius,
            max(2, int(radius * 0.35))
        )

        pygame.draw.circle(
            layer,
            (255, 230, 150, int(alpha * 0.8)),
            (size // 2, size // 2),
            max(1, int(radius * 0.45))
        )

        sx = self.x * camera.zoom - camera.x
        sy = self.y * camera.zoom - camera.y

        screen.blit(layer, layer.get_rect(center=(int(sx), int(sy))))