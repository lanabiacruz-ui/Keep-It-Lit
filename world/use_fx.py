"""Un efecto visual propio para cada objeto que se usa.

Cada efecto es una funcion  fx(s, c, t, k, sd, col)  que dibuja sobre una
superficie transparente `s` centrada en el cuerpo del jugador:

    s    superficie (SRCALPHA)
    c    (x, y) del centro del cuerpo dentro de `s`
    t    segundos desde que arranco
    k    progreso 0..1 (t / duracion)
    sd   semilla (cada uso se ve un poco distinto, pero sin parpadeos)
    col  color dominante del icono (solo lo usa el efecto generico)

Todo esta en pixeles de PANTALLA: el personaje mide 74 px (cabeza a -37,
pies a +37 respecto de `c`).

Para agregar un objeto: escribi su funcion, sumala a EFFECTS y poné su
duracion en DURATIONS.
"""

import math
import random

import pygame

TAU = math.tau

# ----------------------------------------------------------------------
# utilidades
# ----------------------------------------------------------------------


def _rgba(c, a):
    return (int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, a))))


def _eo(x):
    """ease-out cuadratico, x en 0..1"""

    x = max(0.0, min(1.0, x))

    return 1.0 - (1.0 - x) ** 2


_GLOW = {}


def _glow(s, x, y, r, col, a):
    """Resplandor suave (gradiente radial cacheado)."""

    r = int(r) // 4 * 4

    if r < 4 or a <= 2:
        return

    key = (r, col[0] // 8, col[1] // 8, col[2] // 8)

    g = _GLOW.get(key)

    if g is None:

        if len(_GLOW) > 60:
            _GLOW.clear()

        g = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)

        steps = max(4, r // 3)

        for i in range(steps):

            rad = int(r * (1.0 - i / steps))
            al = int(210 * ((i + 1) / steps) ** 2)

            pygame.draw.circle(
                g, (int(col[0]), int(col[1]), int(col[2]), al), (r, r), rad
            )

        _GLOW[key] = g

    g.set_alpha(int(min(255, a)))

    s.blit(g, (int(x) - r, int(y) - r))


def _ring(s, x, y, r, col, a, w=2):

    r = int(r)

    if r < 2 or a <= 2:
        return

    pygame.draw.circle(
        s, _rgba(col, a), (int(x), int(y)), r, max(1, min(int(w), r))
    )


def _ellipse_ring(s, x, y, rx, ry, col, a, w=2):

    rx, ry = int(rx), int(ry)

    if rx < 3 or ry < 2 or a <= 2:
        return

    pygame.draw.ellipse(
        s, _rgba(col, a),
        pygame.Rect(int(x) - rx, int(y) - ry, rx * 2, ry * 2),
        max(1, min(int(w), ry)),
    )


def _star(s, col, x, y, r, a, rot=0.0):

    if r < 1 or a <= 2:
        return

    pts = []

    for i in range(8):

        rad = r if i % 2 == 0 else r * 0.28
        ang = rot + i * math.pi / 4 - math.pi / 2

        pts.append((x + math.cos(ang) * rad, y + math.sin(ang) * rad))

    pygame.draw.polygon(s, _rgba(col, a), pts)


def _heart(s, col, x, y, r, a):

    if r < 1:
        return

    c = _rgba(col, a)

    rr = max(1, int(r * 0.6))

    pygame.draw.circle(s, c, (int(x - r * 0.5), int(y - r * 0.3)), rr)
    pygame.draw.circle(s, c, (int(x + r * 0.5), int(y - r * 0.3)), rr)
    pygame.draw.polygon(
        s, c,
        [(x - r * 1.05, y - r * 0.05), (x + r * 1.05, y - r * 0.05),
         (x, y + r * 1.15)]
    )


def _drop(s, col, x, y, r, a):

    if r < 1:
        return

    c = _rgba(col, a)

    pygame.draw.polygon(
        s, c,
        [(x, y - r * 2.1), (x + r * 0.85, y - r * 0.2),
         (x - r * 0.85, y - r * 0.2)]
    )
    pygame.draw.circle(s, c, (int(x), int(y)), max(1, int(r)))

    pygame.draw.circle(
        s, (255, 255, 255, int(a * 0.7)),
        (int(x - r * 0.3), int(y - r * 0.2)), max(1, int(r * 0.3))
    )


def _flame(s, col, x, y, r, a, flick=0.0):
    """Llama: cuerpo del color dado y centro amarillo."""

    if r < 1 or a <= 2:
        return

    w = r * (1.0 + 0.15 * math.sin(flick))
    h = r * (2.8 + 0.5 * math.sin(flick * 1.7))

    pygame.draw.polygon(
        s, _rgba(col, a),
        [(x, y - h), (x + w, y - h * 0.25), (x + w * 0.7, y + r * 0.6),
         (x - w * 0.7, y + r * 0.6), (x - w, y - h * 0.25)]
    )
    pygame.draw.circle(
        s, _rgba(col, a), (int(x), int(y + r * 0.1)), max(1, int(w * 0.8))
    )

    pygame.draw.polygon(
        s, (255, 232, 130, int(a * 0.9)),
        [(x, y - h * 0.55), (x + w * 0.5, y - h * 0.1),
         (x + w * 0.35, y + r * 0.4), (x - w * 0.35, y + r * 0.4),
         (x - w * 0.5, y - h * 0.1)]
    )


def _plus(s, col, x, y, r, a):

    c = _rgba(col, a)

    t = max(1, int(r * 0.45))

    pygame.draw.rect(
        s, c, pygame.Rect(int(x - r), int(y - t // 2), int(r * 2), t)
    )
    pygame.draw.rect(
        s, c, pygame.Rect(int(x - t // 2), int(y - r), t, int(r * 2))
    )


def _poly_rot(s, col, x, y, pts, rot, a, width=0):

    cr, sr = math.cos(rot), math.sin(rot)

    out = [
        (x + px * cr - py * sr, y + px * sr + py * cr) for px, py in pts
    ]

    pygame.draw.polygon(s, _rgba(col, a), out, width)


def _hex(s, col, x, y, r, a, rot=0.0, w=1):

    if r < 2:
        return

    pts = [
        (x + math.cos(rot + i * TAU / 6) * r,
         y + math.sin(rot + i * TAU / 6) * r)
        for i in range(6)
    ]

    pygame.draw.polygon(s, _rgba(col, a), pts, w)


def _shape(s, shape, col, x, y, r, a, rot, ang):

    if a <= 2:
        return

    if shape == "dot":

        pygame.draw.circle(s, _rgba(col, a), (int(x), int(y)), max(1, int(r)))

    elif shape == "glowdot":

        _glow(s, x, y, r * 3.2, col, a * 0.55)

        pygame.draw.circle(
            s, (255, 255, 255, int(a)), (int(x), int(y)),
            max(1, int(r * 0.55))
        )

    elif shape == "star":

        _star(s, col, x, y, r * 1.7, a, rot)

    elif shape == "drop":

        _drop(s, col, x, y, r, a)

    elif shape == "bubble":

        pygame.draw.circle(
            s, _rgba(col, a * 0.8), (int(x), int(y)), max(2, int(r)), 1
        )
        pygame.draw.circle(
            s, (255, 255, 255, int(a * 0.8)),
            (int(x - r * 0.35), int(y - r * 0.35)), max(1, int(r * 0.22))
        )

    elif shape == "smoke":

        pygame.draw.circle(
            s, _rgba(col, a * 0.45), (int(x), int(y)), max(2, int(r))
        )

    elif shape == "spark":

        dx, dy = math.cos(ang), math.sin(ang)

        pygame.draw.line(
            s, _rgba(col, a), (x, y),
            (x - dx * r * 4.0, y - dy * r * 4.0), 2
        )
        pygame.draw.circle(
            s, (255, 255, 230, int(a)), (int(x), int(y)), max(1, int(r * 0.5))
        )

    elif shape == "streak":

        dx, dy = math.cos(ang), math.sin(ang)

        pygame.draw.line(
            s, _rgba(col, a), (x, y),
            (x - dx * r * 9.0, y - dy * r * 9.0), max(1, int(r * 0.6))
        )

    elif shape == "heart":

        _heart(s, col, x, y, r, a)

    elif shape == "flame":

        _flame(s, col, x, y, r, a, flick=rot * 3.0)

    elif shape == "plus":

        _plus(s, col, x, y, r, a)

    elif shape == "hex":

        _hex(s, col, x, y, r * 1.5, a, rot, 1)

    elif shape == "chip":

        _poly_rot(
            s, col, x, y,
            [(-r, -r * 0.5), (r, -r * 0.5), (r, r * 0.5), (-r, r * 0.5)],
            rot, a
        )
        _poly_rot(
            s, (60, 36, 18), x, y,
            [(-r, -r * 0.5), (r, -r * 0.5), (r, r * 0.5), (-r, r * 0.5)],
            rot, a, 1
        )


def emit(s, sd, t, n, ox, oy, color, shape="dot", ang=(0.0, TAU),
         speed=(40, 90), life=(0.4, 0.8), size=(2.5, 4.5), grav=0.0,
         delay=(0.0, 0.0), jitter=(0, 0), drag=0.0, grow=0.0,
         spin=(0.0, 0.0), alpha=255, colors=None):
    """Emisor de particulas determinista (mismo `sd` => mismo resultado)."""

    rng = random.Random(sd)

    for _ in range(n):

        a = rng.uniform(*ang)
        sp = rng.uniform(*speed)
        lf = rng.uniform(*life)
        sz = rng.uniform(*size)
        d = rng.uniform(*delay)
        jx = rng.uniform(-jitter[0], jitter[0])
        jy = rng.uniform(-jitter[1], jitter[1])
        rot0 = rng.uniform(0.0, TAU)
        sw = rng.uniform(*spin)
        col = color if colors is None else colors[rng.randrange(len(colors))]

        tt = t - d

        if tt < 0 or tt >= lf:
            continue

        f = tt / lf

        m = (1.0 - math.exp(-drag * tt)) / drag if drag > 0 else tt

        x = ox + jx + math.cos(a) * sp * m
        y = oy + jy + math.sin(a) * sp * m + grav * tt * tt * 0.5

        al = alpha * min(1.0, (1.0 - f) * 2.2)

        _shape(s, shape, col, x, y, sz * (1.0 + grow * f), al,
               rot0 + sw * tt, a)


# ----------------------------------------------------------------------
# efectos por objeto
# ----------------------------------------------------------------------


def fx_madera(s, c, t, k, sd, col):
    """Se parte la madera: astillas, brasas y un calorcito que cura."""

    cx, cy = c

    _glow(s, cx, cy, 40 + 22 * _eo(k), (255, 160, 70), 160 * (1 - k) ** 1.5)

    emit(s, sd + 1, t, 8, cx, cy + 4, (168, 110, 60), "chip",
         ang=(-2.9, -0.25), speed=(80, 160), life=(0.5, 0.85),
         size=(3.5, 6.0), grav=560, spin=(-10, 10))

    emit(s, sd + 2, t, 5, cx, cy + 4, (104, 66, 36), "chip",
         ang=(-2.8, -0.35), speed=(60, 120), life=(0.5, 0.85),
         size=(3.0, 5.0), grav=560, spin=(-12, 12))

    emit(s, sd + 3, t, 12, cx, cy + 10, (255, 150, 50), "glowdot",
         ang=(-2.4, -0.7), speed=(18, 55), life=(0.55, 1.0),
         size=(1.6, 3.0), grav=-70, jitter=(16, 6),
         colors=[(255, 150, 50), (255, 205, 90), (255, 110, 40)])

    emit(s, sd + 4, t, 4, cx, cy - 6, (130, 255, 150), "plus",
         ang=(-1.9, -1.2), speed=(26, 40), life=(0.7, 0.95),
         size=(3.0, 4.5), jitter=(20, 8), delay=(0.15, 0.35))


def fx_aceite(s, c, t, k, sd, col):
    """Aceite que chorrea dorado + ondas en el piso + rafagas de velocidad."""

    cx, cy = c
    feet = cy + 37

    emit(s, sd + 1, t, 14, cx, cy - 62, (255, 196, 64), "drop",
         ang=(math.pi / 2, math.pi / 2), speed=(40, 90), life=(0.4, 0.6),
         size=(2.2, 3.6), grav=620, jitter=(24, 4), delay=(0.0, 0.3),
         colors=[(255, 196, 64), (255, 224, 120), (230, 160, 40)])

    for i in range(3):

        tt = t - 0.22 - i * 0.14

        if tt > 0:

            f = tt / 0.6

            _ellipse_ring(
                s, cx, feet - 2, 12 + 44 * _eo(f), 4 + 12 * _eo(f),
                (255, 205, 80), 230 * (1 - f), 2
            )

    emit(s, sd + 2, t, 7, cx + 34, cy, (255, 235, 150), "streak",
         ang=(math.pi, math.pi), speed=(150, 230), life=(0.25, 0.45),
         size=(1.4, 2.2), jitter=(8, 30), delay=(0.35, 0.6))

    _glow(s, cx, cy, 44, (255, 190, 60), 90 * math.sin(min(1.0, k) * math.pi))


def fx_cera(s, c, t, k, sd, col):
    """Cera tibia: gotas lentas y un reloj que se llena (dura mas)."""

    cx, cy = c

    _glow(s, cx, cy, 46, (255, 236, 170), 110 * math.sin(min(1.0, k) * math.pi))

    emit(s, sd + 1, t, 8, cx, cy - 50, (255, 244, 200), "drop",
         ang=(math.pi / 2, math.pi / 2), speed=(8, 30), life=(0.6, 0.95),
         size=(2.4, 3.6), grav=140, jitter=(22, 6), delay=(0.0, 0.3))

    sweep = _eo(min(1.0, k * 1.5))
    fade = 255 if k < 0.65 else 255 * (1 - (k - 0.65) / 0.35)

    r = 44

    for i in range(12):

        a0 = -math.pi / 2 + i * TAU / 12

        if i / 12 > sweep:
            break

        x1, y1 = cx + math.cos(a0) * (r - 5), cy + math.sin(a0) * (r - 5)
        x2, y2 = cx + math.cos(a0) * (r + 2), cy + math.sin(a0) * (r + 2)

        pygame.draw.line(s, _rgba((255, 236, 170), fade), (x1, y1), (x2, y2), 3)

    steps = int(60 * sweep)

    if steps > 1:

        pts = [
            (cx + math.cos(-math.pi / 2 + TAU * j / 60) * (r - 9),
             cy + math.sin(-math.pi / 2 + TAU * j / 60) * (r - 9))
            for j in range(steps + 1)
        ]

        pygame.draw.lines(s, _rgba((255, 250, 220), fade * 0.8), False, pts, 2)


def fx_ganzua(s, c, t, k, sd, col):
    """Clic metalico: dos ganzuas girando y destellos plateados."""

    cx, cy = c

    px, py = cx + 20, cy + 4

    wob = math.sin(t * 38) * 0.35 * (1 - k)

    _poly_rot(s, (205, 210, 220), px, py,
              [(-12, -1.2), (12, -1.2), (12, 1.2), (-12, 1.2)],
              -0.7 + wob, 255 * (1 - k ** 3))

    _poly_rot(s, (160, 165, 178), px, py,
              [(-10, -1.2), (10, -1.2), (10, 1.2), (-10, 1.2)],
              0.5 - wob, 255 * (1 - k ** 3))

    for i, t0 in enumerate((0.08, 0.24, 0.40)):

        tt = t - t0

        if 0 <= tt < 0.2:

            f = tt / 0.2

            _star(s, (255, 255, 255), px + 8 * (i - 1), py - 4,
                  8 * (1 - f) + 2, 255 * (1 - f), f * 2)

            _ring(s, px, py, 4 + 14 * f, (225, 232, 245), 220 * (1 - f), 1)

    emit(s, sd + 1, t, 8, px, py, (225, 232, 245), "spark",
         ang=(-2.6, -0.5), speed=(60, 120), life=(0.25, 0.45),
         size=(1.2, 2.0), grav=320, delay=(0.05, 0.4))


def fx_polvora(s, c, t, k, sd, col):
    """Chispazo de polvora: destello, humo gris y chispas naranjas."""

    cx, cy = c

    if t < 0.18:
        _glow(s, cx, cy, 52, (255, 230, 150), 255 * (1 - t / 0.18))

    emit(s, sd + 1, t, 9, cx, cy + 6, (90, 88, 96), "smoke",
         ang=(-2.5, -0.65), speed=(25, 60), life=(0.5, 0.9),
         size=(5, 8), grow=1.1, drag=2.0, delay=(0.0, 0.2),
         jitter=(14, 6))

    emit(s, sd + 2, t, 16, cx, cy, (255, 160, 50), "spark",
         ang=(0, TAU), speed=(90, 190), life=(0.3, 0.6),
         size=(1.2, 2.2), grav=260, drag=1.5,
         colors=[(255, 160, 50), (255, 220, 110), (255, 100, 40)])


def fx_resina(s, c, t, k, sd, col):
    """Resina densa: burbujas ambar y un pulso lento (cura gradual)."""

    cx, cy = c

    pulse = 0.5 + 0.5 * math.sin(t * 9)

    _glow(s, cx, cy, 40 + 8 * pulse, (255, 176, 40),
          (70 + 70 * pulse) * (1 - k ** 2))

    emit(s, sd + 1, t, 10, cx, cy + 20, (255, 190, 70), "bubble",
         ang=(-1.9, -1.2), speed=(18, 42), life=(0.7, 1.1),
         size=(3.0, 6.0), jitter=(20, 8), delay=(0.0, 0.45),
         grow=0.3)

    emit(s, sd + 2, t, 6, cx, cy - 44, (210, 130, 30), "drop",
         ang=(math.pi / 2, math.pi / 2), speed=(6, 20), life=(0.8, 1.1),
         size=(2.2, 3.4), grav=90, jitter=(18, 4), delay=(0.1, 0.5))

    for i in range(2):

        tt = t - i * 0.4

        if 0 < tt < 0.55:

            f = tt / 0.55

            _ring(s, cx, cy, 18 + 34 * _eo(f), (255, 190, 70),
                  200 * (1 - f), 3)


def fx_hongo_azul(s, c, t, k, sd, col):
    """Esporas azules y una burbuja-escudo que se forma alrededor."""

    cx, cy = c

    emit(s, sd + 1, t, 16, cx, cy + 24, (150, 200, 255), "glowdot",
         ang=(-2.2, -0.9), speed=(14, 40), life=(0.7, 1.1),
         size=(1.6, 3.2), jitter=(24, 10), delay=(0.0, 0.4),
         colors=[(120, 180, 255), (200, 230, 255), (90, 140, 255)])

    grow = _eo(min(1.0, k * 2.2))
    fade = 255 if k < 0.6 else 255 * (1 - (k - 0.6) / 0.4)

    r = 46 * grow

    if r > 3:

        _glow(s, cx, cy, r + 8, (90, 150, 255), 70 * fade / 255)

        _ring(s, cx, cy, r, (140, 200, 255), fade, 3)

        for i in range(3 if r > 14 else 0):

            a0 = t * 3 + i * TAU / 3

            pygame.draw.arc(
                s, (255, 255, 255, int(fade * 0.8)),
                pygame.Rect(int(cx - r + 5), int(cy - r + 5),
                            int(2 * r - 10), int(2 * r - 10)),
                a0, a0 + 0.5, 2
            )


def fx_hongo_amarillo(s, c, t, k, sd, col):
    """Rayos dorados giratorios y un escudo de oro."""

    cx, cy = c

    grow = _eo(min(1.0, k * 2.0))
    fade = 255 if k < 0.6 else 255 * (1 - (k - 0.6) / 0.4)

    _glow(s, cx, cy, 60 * grow, (255, 215, 80), 120 * fade / 255)

    for i in range(10):

        a0 = t * 2.2 + i * TAU / 10

        r0 = 30 * grow + 4
        r1 = (30 + 30 * (0.6 + 0.4 * math.sin(t * 8 + i))) * grow + 6

        pygame.draw.polygon(
            s, _rgba((255, 224, 100), fade * 0.9),
            [(cx + math.cos(a0 - 0.1) * r0, cy + math.sin(a0 - 0.1) * r0),
             (cx + math.cos(a0) * r1, cy + math.sin(a0) * r1),
             (cx + math.cos(a0 + 0.1) * r0, cy + math.sin(a0 + 0.1) * r0)]
        )

    _ring(s, cx, cy, 36 * grow, (255, 236, 150), fade, 3)

    emit(s, sd + 1, t, 8, cx, cy, (255, 240, 170), "star",
         ang=(0, TAU), speed=(20, 60), life=(0.5, 0.9),
         size=(2.0, 3.6), spin=(-4, 4), delay=(0.1, 0.4),
         jitter=(30, 34))


def fx_repelente(s, c, t, k, sd, col):
    """Nube de repelente que se expande y mosquitos que huyen."""

    cx, cy = c

    emit(s, sd + 1, t, 14, cx, cy, (190, 240, 170), "smoke",
         ang=(0, TAU), speed=(50, 100), life=(0.6, 1.0),
         size=(6, 10), grow=1.2, drag=2.4, jitter=(8, 8))

    rng = random.Random(sd + 2)

    for i in range(7):

        a0 = rng.uniform(0, TAU)
        sp = rng.uniform(100, 150)
        t0 = rng.uniform(0.1, 0.35)
        ph = rng.uniform(0, TAU)

        tt = t - t0

        if tt < 0 or tt > 0.7:
            continue

        f = tt / 0.7

        d = 22 + sp * tt

        x = cx + math.cos(a0) * d + math.sin(tt * 34 + ph) * 3
        y = cy + math.sin(a0) * d + math.cos(tt * 29 + ph) * 3

        al = 255 * (1 - f)

        pygame.draw.circle(s, (30, 30, 34, int(al)), (int(x), int(y)), 2)

        pygame.draw.line(
            s, (200, 220, 230, int(al * 0.8)),
            (x - 3, y - 3 + math.sin(tt * 90) * 2),
            (x + 3, y - 3 - math.sin(tt * 90) * 2), 1
        )


def fx_iman(s, c, t, k, sd, col):
    """Campo magnetico: rojo y azul se pliegan hacia el centro."""

    cx, cy = c

    rng = random.Random(sd + 1)

    for i in range(16):

        a0 = rng.uniform(0, TAU)
        r0 = rng.uniform(70, 100)
        t0 = rng.uniform(0.0, 0.3)
        sp = rng.uniform(0.5, 0.7)

        f = (t - t0) / sp

        if f < 0 or f >= 1:
            continue

        r = r0 * (1 - _eo(f) ** 1.6)

        x, y = cx + math.cos(a0) * r, cy + math.sin(a0) * r

        c1 = (240, 70, 70) if i % 2 == 0 else (80, 120, 255)

        al = 255 * min(1.0, (1 - f) * 2)

        pygame.draw.line(
            s, _rgba(c1, al * 0.7), (x, y),
            (x + math.cos(a0) * 14, y + math.sin(a0) * 14), 2
        )
        pygame.draw.circle(s, _rgba(c1, al), (int(x), int(y)), 3)

    for i in range(2):

        tt = t - i * 0.18

        if 0 < tt < 0.55:

            f = tt / 0.55

            _ring(s, cx, cy, 80 * (1 - _eo(f)), (200, 210, 255),
                  230 * f ** 0.5 * (1 - f * 0.6), 2)

    if 0.5 < t < 0.8:

        f = (t - 0.5) / 0.3

        _glow(s, cx, cy, 36, (255, 255, 255), 220 * (1 - f))


def fx_esfera(s, c, t, k, sd, col):
    """Esfera de vidrio: destello, rayos giratorios y onda de luz grande."""

    cx, cy = c

    if t < 0.25:
        _glow(s, cx, cy, 60, (210, 245, 255), 255 * (1 - t / 0.25))

    fade = 255 * (1 - k ** 1.5)

    for i in range(12):

        a0 = t * 1.6 + i * TAU / 12

        r1 = 20 + 70 * _eo(k * 1.2) * (0.55 + 0.45 * (i % 2))

        pygame.draw.polygon(
            s, _rgba((200, 240, 255), fade * 0.7),
            [(cx + math.cos(a0 - 0.05) * 16, cy + math.sin(a0 - 0.05) * 16),
             (cx + math.cos(a0) * r1, cy + math.sin(a0) * r1),
             (cx + math.cos(a0 + 0.05) * 16, cy + math.sin(a0 + 0.05) * 16)]
        )

    _ring(s, cx, cy, 16 + 80 * _eo(k), (180, 235, 255), fade, 3)
    _ring(s, cx, cy, 10 + 56 * _eo(k), (255, 255, 255), fade * 0.7, 1)

    emit(s, sd + 1, t, 8, cx, cy, (255, 255, 255), "star",
         ang=(0, TAU), speed=(10, 30), life=(0.5, 0.9),
         size=(2.0, 3.6), spin=(-4, 4), delay=(0.05, 0.4), jitter=(46, 46))


def fx_gelea(s, c, t, k, sd, col):
    """Gelatina saltarina con corazoncitos."""

    cx, cy = c
    feet = cy + 37

    rng = random.Random(sd + 1)

    cols = [(255, 110, 170), (255, 150, 200), (230, 80, 150)]

    for i in range(6):

        x0 = cx + rng.uniform(-30, 30)
        t0 = rng.uniform(0.0, 0.25)
        amp = rng.uniform(28, 52)
        r = rng.uniform(5, 8)

        tt = t - t0

        if tt < 0 or tt > 0.75:
            continue

        f = tt / 0.75

        h = abs(math.sin(tt * 9.0)) * amp * (1 - f)

        squash = 1.0 - 0.35 * max(0.0, 1.0 - h / 6.0)

        rx = int(r / squash)
        ry = int(r * squash)

        al = 255 * min(1.0, (1 - f) * 2.2)

        body = pygame.Rect(int(x0 - rx), int(feet - h - ry * 2), rx * 2, ry * 2)

        pygame.draw.ellipse(s, _rgba(cols[i % 3], al), body)

        pygame.draw.circle(
            s, (255, 255, 255, int(al * 0.8)),
            (int(x0 - rx * 0.35), int(feet - h - ry * 1.4)),
            max(1, int(r * 0.25))
        )

    emit(s, sd + 2, t, 7, cx, cy - 6, (255, 120, 180), "heart",
         ang=(-1.9, -1.2), speed=(30, 60), life=(0.7, 1.0),
         size=(3.0, 5.0), jitter=(20, 8), delay=(0.1, 0.5))

    for i in range(2):

        tt = t - 0.15 - i * 0.2

        if 0 < tt < 0.5:

            f = tt / 0.5

            _ellipse_ring(s, cx, feet - 2, 10 + 36 * _eo(f), 3 + 10 * _eo(f),
                          (255, 140, 190), 220 * (1 - f), 2)


def fx_pocion_ascua(s, c, t, k, sd, col):
    """Llamas en espiral subiendo por el cuerpo."""

    cx, cy = c
    feet = cy + 37

    if t < 0.2:
        _glow(s, cx, cy, 56, (255, 120, 40), 230 * (1 - t / 0.2))

    for i in range(9):

        f = max(0.0, min(1.0, (t - i * 0.04) / 0.8))

        if f <= 0 or f >= 1:
            continue

        a0 = i * TAU / 9 + t * 7

        r = 26 * (1 - 0.3 * f)

        x = cx + math.cos(a0) * r
        y = feet - 6 - 96 * f

        cc = [(255, 90, 30), (255, 140, 40), (230, 50, 30)][i % 3]

        _flame(s, cc, x, y, 5 * (1 - 0.35 * f), 255 * (1 - f ** 2),
               flick=t * 14 + i)

    emit(s, sd + 1, t, 16, cx, feet - 10, (255, 170, 60), "glowdot",
         ang=(-2.4, -0.7), speed=(30, 90), life=(0.5, 1.0),
         size=(1.4, 2.8), grav=-90, jitter=(22, 6), delay=(0.0, 0.5),
         colors=[(255, 170, 60), (255, 110, 40), (255, 220, 120)])

    _ellipse_ring(s, cx, feet - 2, 16 + 40 * _eo(k), 5 + 12 * _eo(k),
                  (255, 120, 40), 220 * (1 - k), 2)


def fx_pocion_invisibilidad(s, c, t, k, sd, col):
    """El cuerpo se deshace en destellos violetas y blancos."""

    cx, cy = c

    _glow(s, cx, cy, 44, (170, 120, 255), 100 * math.sin(min(1.0, k) * math.pi))

    emit(s, sd + 1, t, 26, cx, cy, (200, 170, 255), "dot",
         ang=(-2.4, -0.7), speed=(16, 48), life=(0.5, 1.0),
         size=(1.4, 3.0), jitter=(20, 34), delay=(0.0, 0.5), drag=0.8,
         colors=[(200, 170, 255), (255, 255, 255), (150, 110, 255)])

    f = min(1.0, k * 1.6)

    if f < 1.0:

        x = cx - 30 + 60 * f

        pygame.draw.line(
            s, (255, 255, 255, int(230 * (1 - f ** 2))),
            (x, cy - 38), (x, cy + 38), 2
        )
        pygame.draw.line(
            s, (190, 150, 255, int(120 * (1 - f ** 2))),
            (x - 4, cy - 38), (x - 4, cy + 38), 5
        )

    emit(s, sd + 2, t, 6, cx, cy, (255, 255, 255), "star",
         ang=(0, TAU), speed=(10, 26), life=(0.5, 0.9),
         size=(2.0, 3.0), spin=(-5, 5), delay=(0.1, 0.5),
         jitter=(26, 32))


def fx_pocion_velocidad(s, c, t, k, sd, col):
    """Rafagas de velocidad, rayitos electricos y polvo en los pies."""

    cx, cy = c
    feet = cy + 37

    _glow(s, cx, cy, 44, (90, 220, 255), 100 * math.sin(min(1.0, k) * math.pi))

    emit(s, sd + 1, t, 14, cx + 46, cy, (170, 240, 255), "streak",
         ang=(math.pi, math.pi), speed=(260, 420), life=(0.25, 0.5),
         size=(1.5, 2.6), jitter=(10, 38), delay=(0.0, 0.5),
         colors=[(170, 240, 255), (255, 255, 255), (90, 210, 255)])

    rng = random.Random(sd + 2)

    for i in range(4):

        t0 = rng.uniform(0.0, 0.4)
        bx = cx + rng.uniform(-22, 22)
        by = cy + rng.uniform(-20, 20)

        tt = t - t0

        if tt < 0 or tt > 0.18:
            continue

        pts = [(bx, by)]

        for j in range(1, 5):

            pts.append((
                bx + rng.uniform(-9, 9),
                by + j * 7
            ))

        pygame.draw.lines(
            s, (255, 255, 200, int(255 * (1 - tt / 0.18))), False, pts, 2
        )

    emit(s, sd + 3, t, 8, cx, feet - 2, (170, 160, 150), "smoke",
         ang=(math.pi * 0.85, math.pi * 1.15), speed=(30, 70),
         life=(0.4, 0.7), size=(3, 6), grow=1.0, drag=2.0,
         jitter=(10, 2), delay=(0.0, 0.4))


def fx_pocion_ira(s, c, t, k, sd, col):
    """Aura furiosa: onda dentada roja, llamas oscuras y marca de enojo."""

    cx, cy = c
    feet = cy + 37

    if t < 0.2:
        _glow(s, cx, cy, 60, (255, 40, 40), 255 * (1 - t / 0.2))

    f = _eo(min(1.0, k * 1.6))

    if f < 1.0:

        pts = []

        n = 28

        for i in range(n):

            a0 = i * TAU / n

            rr = (20 + 70 * f) * (1.0 + (0.16 if i % 2 == 0 else -0.04))

            pts.append((cx + math.cos(a0) * rr, cy + math.sin(a0) * rr))

        pygame.draw.polygon(s, _rgba((255, 60, 50), 230 * (1 - f)), pts, 3)

    for i in range(7):

        ff = max(0.0, min(1.0, (t - i * 0.05) / 0.7))

        if ff <= 0 or ff >= 1:
            continue

        x = cx + (i - 3) * 9

        _flame(s, [(190, 20, 20), (255, 70, 40)][i % 2], x,
               feet - 4 - 40 * ff, 5.5, 255 * (1 - ff ** 2),
               flick=t * 16 + i * 2)

    # marca de enojo (las cuatro esquinas) latiendo sobre la cabeza
    pulse = 1.0 + 0.25 * math.sin(t * 22)

    ax, ay = cx + 24, cy - 46

    al = 255 if k < 0.6 else 255 * (1 - (k - 0.6) / 0.4)

    for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):

        x0, y0 = ax + dx * 3 * pulse, ay + dy * 3 * pulse

        pygame.draw.line(s, _rgba((255, 50, 50), al),
                         (x0, y0), (x0 + dx * 6 * pulse, y0), 3)
        pygame.draw.line(s, _rgba((255, 50, 50), al),
                         (x0, y0), (x0, y0 + dy * 6 * pulse), 3)

    emit(s, sd + 1, t, 14, cx, cy, (255, 90, 50), "spark",
         ang=(0, TAU), speed=(70, 150), life=(0.3, 0.6),
         size=(1.2, 2.2), grav=100, drag=1.4)


def fx_generico(s, c, t, k, sd, col):
    """Para objetos sin efecto propio: chispas y anillo del color del icono."""

    cx, cy = c

    _glow(s, cx, cy, 40 + 20 * _eo(k), col, 140 * (1 - k) ** 1.5)

    _ring(s, cx, cy, 14 + 46 * _eo(k), col, 200 * (1 - k), 3)

    emit(s, sd + 1, t, 12, cx, cy - 4, col, "star",
         ang=(0, TAU), speed=(40, 95), life=(0.45, 0.8),
         size=(1.6, 3.0), grav=60, spin=(-5, 5), drag=0.6)


EFFECTS = {
    "madera": fx_madera,
    "aceite": fx_aceite,
    "cera": fx_cera,
    "ganzua": fx_ganzua,
    "polvora": fx_polvora,
    "resina": fx_resina,
    "hongo_azul": fx_hongo_azul,
    "hongo_amarillo": fx_hongo_amarillo,
    "repelente": fx_repelente,
    "iman": fx_iman,
    "esfera": fx_esfera,
    "gelea": fx_gelea,
    "pocion_ascua": fx_pocion_ascua,
    "pocion_invisibilidad": fx_pocion_invisibilidad,
    "pocion_velocidad": fx_pocion_velocidad,
    "pocion_ira": fx_pocion_ira,
}

DURATIONS = {
    "madera": 0.95,
    "aceite": 1.0,
    "cera": 1.1,
    "ganzua": 0.7,
    "polvora": 0.9,
    "resina": 1.2,
    "hongo_azul": 1.1,
    "hongo_amarillo": 1.1,
    "repelente": 1.0,
    "iman": 0.95,
    "esfera": 1.0,
    "gelea": 1.0,
    "pocion_ascua": 1.1,
    "pocion_invisibilidad": 1.1,
    "pocion_velocidad": 0.95,
    "pocion_ira": 1.1,
}

DEFAULT_DURATION = 0.85