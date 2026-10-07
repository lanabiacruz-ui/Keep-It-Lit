import random

import pygame


# ---------------------------------------------------------------
# Tipos de puerta
#   hits:  golpes para romperla (None = no se rompe a golpes)
#   cost:  cuanta vida de la luz (0.0 a 1.0) gasta CADA golpe.
#          El fosforo dura 30 s, asi que 0.05 = 1.5 s de luz.
#   Que luz puede romper cada tipo se define en world/lights.py
#   ("rompe"): la gris solo la rompe la vela.
# ---------------------------------------------------------------
DOOR_TYPES = {
    "comun": {"hits": 2, "cost": 0.05},
    "verde": {"hits": 6, "cost": 0.05},
    # Solo se rompe con la vela
    "gris": {"hits": 4, "cost": 0.05},
    # Se abre con otro objeto (todavia no existe)
    "azul": {"hits": None, "cost": 0.0},
}

# ---------------------------------------------------------------
# Donde esta cada puerta (centro, en unidades del mundo = pixeles
# del mapa).
#   "v" = tapa un pasillo horizontal (la puerta es alta y angosta)
#   "h" = tapa un pasillo vertical    (la puerta es ancha y baja)
#   largo = lo que mide la puerta a lo largo del hueco. Esta
#           medido sobre mapa.png: piso del pasillo + 2 px de borde
#           por lado, asi la puerta llena el hueco de pared a pared
#           sin montarse sobre la piedra.
#
# Cada puerta esta en un tramo RECTO del pasillo (con pared de los
# dos lados), nunca en la boca donde se abre a la sala.
# ---------------------------------------------------------------
DOOR_LAYOUT = [
    # id,                     tipo,    orient, x,    y,   largo
    ("sup_izq_central",       "comun", "v",    838,  138, 40),
    ("sup_izq_sala",          "verde", "v",    614,  137, 39),
    ("sup_der_sala",          "azul",  "v",    1222, 136, 36),
    ("sup_central_abajo",     "verde", "h",    943,  197, 41),
    ("hub_arriba",            "comun", "h",    942,  370, 35),
    ("hub_izquierda",         "comun", "v",    806,  518, 46),
    ("hub_derecha",           "comun", "v",    1090, 520, 44),
    ("hub_abajo",             "comun", "h",    943,  642, 44),
    ("cabana",                "comun", "h",    941,  877, 36),
    ("sala_izq",              "gris",  "v",    682,  518, 45),
    ("sala_der",              "gris",  "v",    1214, 519, 45),
]

# Grosor de toda puerta (sentido del pasillo)
THICKNESS = 16

# Tiempo del destello blanco cuando recibe un golpe
FLASH_TIME = 0.12

# ---------------------------------------------------------------
# Aspecto
# ---------------------------------------------------------------
OUTLINE = (20, 17, 15)

PALETTES = {
    "comun": {
        "base": (118, 80, 50),
        "light": (150, 106, 66),
        "dark": (82, 54, 33),
        "band": (68, 64, 62),
        "band_light": (116, 112, 108),
        "knob": (236, 172, 52),
    },
    "verde": {
        "base": (62, 92, 62),
        "light": (92, 130, 88),
        "dark": (40, 62, 44),
        "band": (42, 44, 42),
        "band_light": (86, 90, 84),
        "knob": (196, 230, 120),
    },
    "gris": {
        "base": (128, 126, 120),
        "light": (168, 166, 160),
        "dark": (84, 82, 80),
        "band": (56, 56, 60),
        "band_light": (106, 106, 112),
        "knob": (66, 66, 70),
    },
    "azul": {
        "base": (50, 76, 132),
        "light": (92, 128, 202),
        "dark": (30, 46, 88),
        "band": (30, 32, 52),
        "band_light": (72, 78, 112),
        "knob": (170, 225, 255),
    },
}

_image_cache = {}


def _draw_planks(surf, pal, rng, avoid):
    """Tablones: costuras, brillo y vetas de madera."""

    w, h = surf.get_size()

    n = max(2, round(h / 10))

    seams = []

    for i in range(1, n):

        y = int(h * i / n)

        if any(abs(y - a) < 4 for a in avoid):
            continue

        seams.append(y)

        pygame.draw.line(surf, pal["dark"], (2, y), (w - 3, y))
        pygame.draw.line(surf, pal["light"], (3, y + 1), (w - 4, y + 1))

    # vetas
    for _ in range(h // 5):

        x = rng.randint(3, w - 7)
        y = rng.randint(3, h - 4)

        if any(abs(y - s) < 2 for s in seams):
            continue

        if any(abs(y - a) < 3 for a in avoid):
            continue

        pygame.draw.line(
            surf, pal["dark"], (x, y), (x + rng.randint(2, 4), y)
        )

    return seams


def _draw_slab(surf, pal, rng, avoid):
    """Losa de piedra (puerta gris): grietas talladas."""

    w, h = surf.get_size()

    for _ in range(h // 7):

        x = rng.randint(3, w - 6)
        y = rng.randint(4, h - 5)

        if any(abs(y - a) < 3 for a in avoid):
            continue

        pygame.draw.line(
            surf, pal["dark"], (x, y), (x + rng.randint(2, 4), y + rng.choice((-1, 0, 1)))
        )

    # juntas de la losa
    for y in (h // 3, 2 * h // 3):

        if any(abs(y - a) < 4 for a in avoid):
            continue

        pygame.draw.line(surf, pal["dark"], (2, y), (w - 3, y))
        pygame.draw.line(surf, pal["light"], (3, y + 1), (w - 4, y + 1))


def _draw_band(surf, pal, y):
    """Faja de hierro con remaches."""

    w = surf.get_width()

    pygame.draw.rect(surf, pal["band"], (1, y, w - 2, 3))
    pygame.draw.line(surf, pal["band_light"], (1, y), (w - 2, y))

    surf.set_at((3, y + 1), pal["band_light"])
    surf.set_at((w - 4, y + 1), pal["band_light"])


def _draw_handle(surf, pal):
    """Placa y pomo dorado."""

    w, h = surf.get_size()
    cy = h // 2

    pygame.draw.rect(surf, OUTLINE, (w - 8, cy - 3, 6, 7))
    pygame.draw.rect(surf, pal["band"], (w - 7, cy - 2, 4, 5))
    pygame.draw.rect(surf, pal["knob"], (w - 7, cy - 1, 3, 3))
    surf.set_at((w - 7, cy - 1), (255, 238, 170))


def _draw_lock(surf, pal):
    """Candado brillante de la puerta azul."""

    w, h = surf.get_size()
    cx, cy = w // 2, h // 2

    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*pal["knob"], 55), (cx, cy), 8)
    pygame.draw.circle(glow, (*pal["knob"], 40), (cx, cy), 6)
    surf.blit(glow, (0, 0))

    # arco del candado
    pygame.draw.rect(surf, OUTLINE, (cx - 3, cy - 6, 7, 7))
    pygame.draw.rect(surf, pal["band"], (cx - 2, cy - 5, 5, 6))

    # cuerpo
    pygame.draw.rect(surf, OUTLINE, (cx - 4, cy - 2, 9, 8))
    pygame.draw.rect(surf, pal["knob"], (cx - 3, cy - 1, 7, 6))

    # ojo de la cerradura
    pygame.draw.rect(surf, OUTLINE, (cx, cy + 1, 1, 2))


def _draw_cracks(surf, level, seed):
    """Grietas que aparecen a medida que la puerta recibe golpes."""

    w, h = surf.get_size()
    rng = random.Random(seed)

    for _ in range(level * 2):

        x = rng.randint(4, w - 5)
        y = rng.randint(5, h - 6)

        points = [(x, y)]

        for _ in range(rng.randint(3, 5)):

            x = max(2, min(w - 3, x + rng.randint(-3, 3)))
            y = max(2, min(h - 3, y + rng.randint(2, 5) * rng.choice((1, -1))))

            points.append((x, y))

        pygame.draw.lines(surf, OUTLINE, False, points)


def _build_vertical(kind, length, cracks):
    """Dibuja la puerta 'v' (16 de ancho x largo de alto)."""

    pal = PALETTES[kind]

    w, h = THICKNESS, length

    rng = random.Random(f"{kind}-{length}")

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # contorno + cuerpo
    pygame.draw.rect(surf, OUTLINE, (0, 0, w, h), border_radius=4)
    pygame.draw.rect(
        surf, pal["base"], (1, 1, w - 2, h - 2), border_radius=3
    )

    bands = [4, h - 7]

    if kind == "gris":
        _draw_slab(surf, pal, rng, bands)
    else:
        _draw_planks(surf, pal, rng, bands + [h // 2])

    # bisel (luz a la izquierda, sombra a la derecha)
    pygame.draw.line(surf, pal["light"], (2, 4), (2, h - 5))
    pygame.draw.line(surf, pal["dark"], (w - 3, 4), (w - 3, h - 5))

    for y in bands:
        _draw_band(surf, pal, y)

    if kind == "azul":
        _draw_lock(surf, pal)
    else:
        _draw_handle(surf, pal)

    if cracks > 0:
        _draw_cracks(surf, cracks, f"{kind}-{length}-crack")

    return surf


def _get_door_image(kind, orient, length, cracks):

    key = (kind, orient, length, cracks)

    if key not in _image_cache:

        image = _build_vertical(kind, length, cracks)

        if orient == "h":
            image = pygame.transform.rotate(image, 90)

        _image_cache[key] = image

    return _image_cache[key]


class Door:

    # Le dice a Melee que pruebe el borde real de la puerta
    precise_hit = True

    def __init__(self, door_id, kind, orient, x, y, length=56):

        self.id = door_id
        self.kind = kind
        self.orient = orient
        self.length = length

        data = DOOR_TYPES[kind]

        self.max_hits = data["hits"]
        self.hits_left = data["hits"]
        self.hit_cost = data["cost"]

        self.original = _get_door_image(kind, orient, length, 0)

        w, h = self.original.get_size()

        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (x, y)

        self.broken = False
        self.flash = 0.0

        self._scaled = None
        self._flash_scaled = None
        self._sprite_key = None

    @property
    def breakable(self):

        return self.max_hits is not None

    @property
    def crack_level(self):
        """0 = intacta, 3 = a punto de romperse."""

        if not self.breakable or self.hits_left >= self.max_hits:
            return 0

        dmg = self.max_hits - self.hits_left

        return max(1, min(3, int(3 * dmg / self.max_hits)))

    def resist(self):
        """La luz no puede con esta puerta: solo destella, sin dano."""

        self.flash = FLASH_TIME

    def take_damage(self, amount):
        """Devuelve cuanta vida de la luz cuesta este golpe."""

        self.flash = FLASH_TIME

        if not self.breakable:
            return 0.0

        self.hits_left -= 1

        if self.hits_left <= 0:
            self.broken = True

        return self.hit_cost

    def update(self, dt):

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

    def _get_sprites(self, zoom):

        key = (zoom, self.crack_level)

        if self._sprite_key != key:

            base = _get_door_image(
                self.kind, self.orient, self.length, self.crack_level
            )

            size = (base.get_width() * zoom, base.get_height() * zoom)

            # scale (no smoothscale) para que el pixel art no se borre
            self._scaled = pygame.transform.scale(base, size)

            self._flash_scaled = self._scaled.copy()
            self._flash_scaled.fill(
                (110, 110, 110, 0),
                special_flags=pygame.BLEND_RGB_ADD
            )

            self._sprite_key = key

        return self._scaled, self._flash_scaled

    def draw(self, screen, camera):

        normal, flash = self._get_sprites(camera.zoom)

        dest = camera.apply(self.rect)

        screen.blit(flash if self.flash > 0 else normal, dest.topleft)


class DoorManager:

    def __init__(self, broken_ids=None):

        broken_ids = set(broken_ids or [])

        self.doors = [
            Door(*entry)
            for entry in DOOR_LAYOUT
            if entry[0] not in broken_ids
        ]

        self.broken_ids = broken_ids

    @property
    def blocking_rects(self):
        """Rects que bloquean el paso (para la colision)."""

        return [d.rect for d in self.doors]

    def update(self, dt):

        for door in self.doors:
            door.update(dt)

        for door in self.doors:
            if door.broken:
                self.broken_ids.add(door.id)

        # Las rotas desaparecen
        self.doors = [d for d in self.doors if not d.broken]

    def draw(self, screen, camera):

        for door in self.doors:
            door.draw(screen, camera)