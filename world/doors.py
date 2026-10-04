from pathlib import Path

import pygame


DOORS_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "puertas"
)

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
# del mapa). "v" = 16x56 (tapa un pasillo horizontal),
# "h" = 56x16 (tapa un pasillo vertical).
# ---------------------------------------------------------------
DOOR_LAYOUT = [
    # id,                     tipo,    orient, x,    y
    ("sup_izq_central",       "comun", "v",    839,  137),
    ("sup_izq_sala",          "verde", "v",    606,  137),
    ("sup_der_sala",          "azul",  "v",    1231, 135),
    ("sup_central_abajo",     "verde", "h",    942,  185),
    ("hub_arriba",            "comun", "h",    947,  389),
    ("hub_izquierda",         "comun", "v",    817,  520),
    ("hub_derecha",           "comun", "v",    1077, 520),
    ("hub_abajo",             "comun", "h",    942,  638),
    ("cabana",                "comun", "h",    943,  879),
    ("sala_izq",              "gris",  "v",    672,  518),
    ("sala_der",              "gris",  "v",    1226, 518),
]

# Tiempo del destello blanco cuando recibe un golpe
FLASH_TIME = 0.12

_image_cache = {}


def _load_image(kind, orient):

    key = (kind, orient)

    if key not in _image_cache:

        path = DOORS_DIR / f"puerta_{kind}_{orient}.png"

        if not path.exists():
            # Si falta la version horizontal (o vertical), se rota la otra
            other = "v" if orient == "h" else "h"
            alt = DOORS_DIR / f"puerta_{kind}_{other}.png"

            image = pygame.image.load(str(alt)).convert_alpha()
            image = pygame.transform.rotate(image, 90)

        else:
            image = pygame.image.load(str(path)).convert_alpha()

        _image_cache[key] = image

    return _image_cache[key]


class Door:

    # Le dice a Melee que pruebe el borde real de la puerta
    precise_hit = True

    def __init__(self, door_id, kind, orient, x, y):

        self.id = door_id
        self.kind = kind
        self.orient = orient

        data = DOOR_TYPES[kind]

        self.max_hits = data["hits"]
        self.hits_left = data["hits"]
        self.hit_cost = data["cost"]

        self.original = _load_image(kind, orient)

        w, h = self.original.get_size()

        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (x, y)

        self.broken = False
        self.flash = 0.0

        self._scaled = None
        self._scaled_zoom = None
        self._flash_scaled = None

    @property
    def breakable(self):

        return self.max_hits is not None

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

        if self._scaled_zoom != zoom:

            size = (
                self.original.get_width() * zoom,
                self.original.get_height() * zoom
            )

            # scale (no smoothscale) para que el pixel art no se borre
            self._scaled = pygame.transform.scale(self.original, size)

            self._flash_scaled = self._scaled.copy()
            self._flash_scaled.fill(
                (110, 110, 110, 0),
                special_flags=pygame.BLEND_RGB_ADD
            )

            self._scaled_zoom = zoom

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