"""Cabaña a oscuras: cuando el gato ya se fue (core/story.py) toda la
cabaña queda a oscuras y solo la PC ilumina al jugador.

Lo usan el menu principal y las pantallas que dibujan la cabaña de fondo
(ajustes, logros, skins, partidas, nombre, modo, carga). Cada pantalla
dibuja su fondo con blit_background(): si el gato ya se fue, se usa una
copia oscurecida (se calcula una sola vez y queda guardada).

Solo se oscurecen los fondos de la cabaña (CABIN_BACKGROUNDS): la tablet
del juego (pausa) no se toca.
"""

import math
from pathlib import Path

import pygame

from core import story


# Imagenes de fondo que muestran la cabaña
CABIN_BACKGROUNDS = {
    "menu.png",
    "mapaajustes.png",
    "mapalogros.png",
    "mapamodo.png",
    "mapapartidas.png",
    "mapacarga.png",
    "mapaloading.png",
    "mapacontrasena.png",
}

# Geometria de la escena (px de la imagen de referencia de 1669x942)
BG_W = 745
BG_H = 421

WINDOWS = [
    (257, 1, 99, 55),
    (380, 1, 110, 55),
]

MONITOR_BOX = (456, 201, 1235, 534)
MONITOR_REF = (1669, 942)

# Luz de la noche en toda la cabaña: se multiplica contra la escena.
# Mas alto = se ve mas; mas bajo = mas a oscuras.
AMBIENT = (44, 50, 84)

# Reflejo azul que se suma en las sombras (las desatura, como de noche)
LIFT = (12, 16, 30)

MON_LIGHT = (205, 225, 255)
MOON_LIGHT = (105, 124, 176)

# Alcance de la luz de la PC sobre las paredes
MON_REACH = 190

# Charco de luz sobre el escritorio y el jugador: (x, y, radio x, radio y)
POOL = (845, 650, 440, 210)

# Contraste de la caida de luz (mas alto = sombras mas profundas)
FALLOFF_POWER = 1.2

# Oscurecimiento de las esquinas (0 = nada)
VIGNETTE = 0.30

# Parpadeo muy leve de la pantalla en el menu principal (0 = sin parpadeo)
FLICKER = 0.0


_maps = {}
_dark_copies = {}


def is_dark():
    """True cuando el gato ya se fue."""

    return story.cat_gone()


def is_cabin(name):
    """True si la imagen de fondo (nombre o ruta) es una de la cabaña."""

    return Path(str(name)).name in CABIN_BACKGROUNDS


def monitor_rect(size):

    kx = size[0] / MONITOR_REF[0]
    ky = size[1] / MONITOR_REF[1]

    x0, y0, x1, y1 = MONITOR_BOX

    return pygame.Rect(
        round(x0 * kx),
        round(y0 * ky),
        round((x1 - x0) * kx),
        round((y1 - y0) * ky),
    ).clip(pygame.Rect(0, 0, size[0], size[1]))


def _build(size):

    sw, sh = size
    rw, rh = MONITOR_REF

    step = 6
    lw = max(2, sw // step)
    lh = max(2, sh // step)

    amb = AMBIENT
    lit = MON_LIGHT
    moon = MOON_LIGHT

    mx0, my0, mx1, my1 = MONITOR_BOX
    px, py, prx, pry = POOL

    windows = [
        (
            x / BG_W * rw, y / BG_H * rh,
            (x + w) / BG_W * rw, (y + h) / BG_H * rh,
        )
        for x, y, w, h in WINDOWS
    ]

    low = pygame.Surface((lw, lh), 0, 32)
    low_lift = pygame.Surface((lw, lh), 0, 32)

    for j in range(lh):

        y = (j + 0.5) / lh * rh

        for i in range(lw):

            x = (i + 0.5) / lw * rw

            # luz de la pantalla: cae como una luz real (con cola larga)
            d = math.hypot(
                max(mx0 - x, 0, x - mx1),
                max(my0 - y, 0, y - my1),
            )

            k = 1.0 / (1.0 + (d / MON_REACH) ** 2) ** 1.2

            # charco sobre el escritorio y el jugador
            pool = math.exp(
                -(((x - px) / prx) ** 2 + ((y - py) / pry) ** 2)
            )

            k = min(1.0, k * 0.9 + pool * 0.8) ** FALLOFF_POWER

            color = [amb[c] + (lit[c] - amb[c]) * k for c in range(3)]

            moon_k = 0.0

            # luz de luna: en la ventana y un poquito debajo
            for x0, y0, x1, y1 in windows:

                if y < y0:
                    continue

                gx = max(x0 - x, 0, x - x1)
                gy = max(0, y - y1)

                if x0 <= x <= x1 and y <= y1:
                    glow = 1.0
                else:
                    glow = math.exp(-((gx / 70) ** 2 + (gy / 90) ** 2)) * 0.22

                color = [
                    max(color[c], amb[c] + (moon[c] - amb[c]) * glow)
                    for c in range(3)
                ]

                moon_k = max(moon_k, glow)

            # viñeta: las esquinas quedan mas negras
            vx = (x / rw - 0.5) * 2
            vy = (y / rh - 0.5) * 2

            vig = 1.0 - VIGNETTE * min(1.0, 0.55 * vx * vx + 0.55 * vy * vy)

            low.set_at((i, j), tuple(int(v * vig) for v in color))

            # reflejo azul de las sombras: donde hay luz no se suma
            shade = (1.0 - k) * (1.0 - moon_k * 0.6)

            low_lift.set_at((i, j), tuple(int(v * shade) for v in LIFT))

    full = pygame.transform.smoothscale(low, (sw, sh))
    lift = pygame.transform.smoothscale(low_lift, (sw, sh))

    # la pantalla de la PC emite luz: se ve sin oscurecer
    box = monitor_rect(size)

    full.fill((255, 255, 255), box)
    lift.fill((0, 0, 0), box)

    ambient = pygame.Surface((sw, sh))
    ambient.fill(amb)

    flat_lift = pygame.Surface((sw, sh))
    flat_lift.fill(LIFT)

    return full, ambient, lift, flat_lift


def _get(size):

    size = (int(size[0]), int(size[1]))

    if size not in _maps:
        _maps[size] = _build(size)

    return _maps[size]


def lit_map(size):
    """Mapa de luz con la PC encendida."""

    return _get(size)[0]


def _mix(on, off, level):

    if level >= 1.0:
        return on

    if level <= 0.0:
        return off

    mixed = off.copy()

    on.set_alpha(int(255 * level))
    mixed.blit(on, (0, 0))
    on.set_alpha(255)

    return mixed


def light_surface(size, level=1.0):
    """Mapa de luz para multiplicar contra la escena.
    level: 0 = PC apagada (todo a oscuras), 1 = PC encendida."""

    lit, ambient, _, _ = _get(size)

    return _mix(lit, ambient, level)


def lift_surface(size, level=1.0):
    """Reflejo azul de las sombras, para sumar a la escena."""

    _, _, lift, flat_lift = _get(size)

    return _mix(lift, flat_lift, level)


def apply_light(surface, level=1.0, offset=(0, 0)):
    """Oscurece `surface` con la luz de la cabaña: multiplica por la luz
    y suma el reflejo azul de las sombras. `offset`: donde esta la
    superficie dentro de la pantalla (para sprites sueltos)."""

    screen = pygame.display.get_surface()

    size = screen.get_size() if screen is not None else surface.get_size()

    surface.blit(
        light_surface(size, level),
        offset,
        special_flags=pygame.BLEND_RGB_MULT,
    )

    surface.blit(
        lift_surface(size, level),
        offset,
        special_flags=pygame.BLEND_RGB_ADD,
    )


def darkened(background):
    """Copia oscurecida de un fondo de la cabaña (se calcula una vez)."""

    key = id(background)

    cached = _dark_copies.get(key)

    if cached is not None and cached[0] is background:
        return cached[1]

    copy = background.copy()

    size = background.get_size()

    copy.blit(
        light_surface(size), (0, 0), special_flags=pygame.BLEND_RGB_MULT
    )
    copy.blit(
        lift_surface(size), (0, 0), special_flags=pygame.BLEND_RGB_ADD
    )

    _dark_copies[key] = (background, copy)

    return copy


def blit_background(screen, background, enabled=True, dest=(0, 0)):
    """Dibuja el fondo. Si es la cabaña (enabled) y el gato ya se fue,
    la dibuja a oscuras."""

    if enabled and is_dark():
        background = darkened(background)

    screen.blit(background, dest)


def darken_sprite(sprite, pos):
    """Copia de un sprite dibujado en `pos` de la pantalla, oscurecido con
    la luz que le toca en ese lugar."""

    out = sprite.copy()

    apply_light(out, 1.0, (-pos[0], -pos[1]))

    return out


def sample(point, size=None):
    """Color de la luz en un punto de la pantalla (r, g, b)."""

    if size is None:
        size = pygame.display.get_surface().get_size()

    lit = lit_map(size)

    x = max(0, min(lit.get_width() - 1, int(point[0])))
    y = max(0, min(lit.get_height() - 1, int(point[1])))

    r, g, b = lit.get_at((x, y))[:3]

    return r, g, b