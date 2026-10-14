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

# La bola fuerte (la 3ra del combo): cuantas veces mas grande es, cuanta
# mas luz tira y con que radio toca. El dano x2 esta en states/new_game.py
# (FIRE_HEAVY_MULT).
HEAVY_SIZE_MULT = 1.7

# Colores de la bola fuerte (azul-blanco, como fuego muy caliente).
# La imagen de la bola se repinta: lo oscuro queda en HEAVY_DARK y lo
# mas claro (el centro) se acerca a HEAVY_LIGHT. Cambialos a gusto.
HEAVY_DARK = (30, 70, 255)
HEAVY_LIGHT = (225, 245, 255)
HEAVY_AURA = (70, 150, 255)       # aura de afuera
HEAVY_AURA_CORE = (200, 235, 255) # aura de adentro
HEAVY_BURST = (80, 160, 255)      # anillo del estallido
HEAVY_BURST_CORE = (210, 240, 255)
HEAVY_LIGHT_RADIUS = 130
HEAVY_HIT_RADIUS = 5.0

_base_sprite = None
_heavy_base = None
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


def _load_heavy_base():
    """La imagen de la bola repintada de azul para la bola fuerte.

    Se calcula una sola vez: usa el brillo de cada pixel para mezclar
    entre HEAVY_DARK y HEAVY_LIGHT, asi conserva la forma de tu dibujo.
    """

    global _heavy_base

    if _heavy_base is None:

        base = _load_base()

        tinted = base.copy()

        for x in range(tinted.get_width()):
            for y in range(tinted.get_height()):

                r, g, b, a = tinted.get_at((x, y))

                if a == 0:
                    continue

                # Brillo del pixel (0 a 1), un poco realzado
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
    """Sprite ya escalado al zoom y girado hacia donde vuela."""

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

        # La bola fuerte del combo: mas grande, mas luz, mas dano
        self.heavy = heavy

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
        """(x, y, radio) para el sistema de luces."""

        radius = HEAVY_LIGHT_RADIUS if self.heavy else FIRE_LIGHT_RADIUS

        return (self.x, self.y, radius)

    def draw(self, screen, camera):

        sprite = _get_sprite(camera.zoom, self.angle, self.heavy)

        sx = self.x * camera.zoom - camera.x
        sy = self.y * camera.zoom - camera.y

        if self.heavy:

            # Aura para que se note que es la fuerte
            r = int(FIRE_SIZE * HEAVY_SIZE_MULT * camera.zoom * 0.9)

            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)

            pygame.draw.circle(halo, (*HEAVY_AURA, 100), (r, r), r)
            pygame.draw.circle(halo, (*HEAVY_AURA_CORE, 110), (r, r), r // 2)

            screen.blit(halo, halo.get_rect(center=(int(sx), int(sy))))

        screen.blit(sprite, sprite.get_rect(center=(int(sx), int(sy))))


class FireBurst:
    """Estallido corto donde la bola choco."""

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