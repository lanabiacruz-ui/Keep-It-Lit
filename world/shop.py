import json
import math
import random
from pathlib import Path

import pygame

from world.items import WorldItem, HUD_DIR


DATA_FILE = (
    Path(__file__).resolve().parent.parent / "data" / "shop.json"
)

MOUTH_IMAGE = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "tienda"
    / "vendedor_boca.png"
)

# Catalogo por si falta data/shop.json
DEFAULT_CATALOG = [
    {
        "nombre": "Luces",
        "items": [
            {"id": "fosforo", "precio": 40},
            {"id": "vela", "precio": 90},
        ],
    },
    {
        "nombre": "Objetos",
        "items": [
            {"id": "madera", "precio": 5},
            {"id": "cera", "precio": 8},
            {"id": "aceite", "precio": 12},
            {"id": "resina", "precio": 15},
            {"id": "polvora", "precio": 20},
            {"id": "ganzua", "precio": 30},
        ],
    },
]


def load_catalog():
    """Secciones de data/shop.json: [{nombre, items: [{id, precio}]}]"""

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        sections = data.get("secciones", [])

    except (OSError, ValueError, AttributeError) as error:

        print(f"[tienda] No se pudo leer data/shop.json: {error}")

        return DEFAULT_CATALOG

    catalog = []

    for sec in sections:

        items = []

        for it in sec.get("items", []):

            try:
                items.append(
                    {"id": str(it["id"]), "precio": int(it["precio"])}
                )
            except (KeyError, TypeError, ValueError):
                continue

        if items:
            catalog.append(
                {"nombre": str(sec.get("nombre", "")), "items": items}
            )

    return catalog or DEFAULT_CATALOG


def price_table(catalog):

    return {
        it["id"]: it["precio"]
        for sec in catalog
        for it in sec["items"]
    }


class Shopkeeper:
    """El vendedor rojo de la sala superior central.

    Esta dibujado en el mapa (mapa.png); aca solo vive su zona de
    interaccion, el cartelito de [E] y la animacion de escupir lo
    que compraste.
    """

    # Boca del vendedor (coordenadas del mundo = pixeles de mapa.png)
    MOUTH = (948, 75)

    # Arriba de la cabeza, para el cartel de [E]
    HEAD_TOP = 62

    # Desde donde se le puede hablar: alrededor de la mesa (el
    # jugador no puede pasar al otro lado)
    TALK_RECT = pygame.Rect(902, 100, 92, 40).inflate(44, 60)

    # El cuadrado de la tienda (la salita de arriba). Adentro todo esta
    # iluminado y la luz del jugador no se gasta.
    ZONE = pygame.Rect(840, 30, 215, 140)

    # Que tanto se difumina el borde de la luz de la tienda (mundo)
    ZONE_FEATHER = 22

    def zone_inset(self, player):
        """Cuanto adentro del cuadrado esta el jugador (0 = en el borde
        o afuera). Sirve para apagar su luz de a poco al entrar."""

        x, y = player.rect.center
        z = self.ZONE

        if not z.collidepoint(x, y):
            return 0.0

        return float(min(x - z.left, z.right - x, y - z.top, z.bottom - y))

    # Donde caen los items escupidos: el piso al frente de la mesa
    LAND_RECT = pygame.Rect(878, 146, 140, 30)

    # Tiempos de la escupida (segundos)
    FIRST_DELAY = 0.25
    ITEM_DELAY = 0.14
    MAX_SPIT_TIME = 4.0
    FLY_TIME = 0.6
    FLY_HEIGHT = 26

    def __init__(self):

        self.e_icon = pygame.image.load(
            str(HUD_DIR / "E.png")
        ).convert_alpha()

        # Boca abierta (vendedor_boca.png); None si falta el archivo
        try:
            self.mouth_img = pygame.image.load(
                str(MOUTH_IMAGE)
            ).convert_alpha()
        except (pygame.error, FileNotFoundError):
            self.mouth_img = None

        self._mouth_cache = {}

        # Segundos que le quedan escupiendo (0 = quieto)
        self.spit_time = 0.0

        self._clock = 0.0

    # ---------- interaccion ----------

    @property
    def busy(self):

        return self.spit_time > 0

    def in_zone(self, player):
        """True si el jugador esta adentro del cuadrado de la tienda."""

        return self.ZONE.collidepoint(player.rect.center)

    def can_talk(self, player):

        return (not self.busy) and player.rect.colliderect(self.TALK_RECT)

    # ---------- escupir ----------

    def _landing_point(self, collision_map):

        for _ in range(30):

            x = random.randint(self.LAND_RECT.left, self.LAND_RECT.right)
            y = random.randint(self.LAND_RECT.top, self.LAND_RECT.bottom)

            if collision_map.point_is_walkable(x, y):
                return (x, y)

        return self.LAND_RECT.center

    def spit(self, item_ids, collision_map):
        """Escupe un item por cada id de la lista, uno atras del otro.
        Devuelve los WorldItem para agregar al mundo."""

        count = len(item_ids)

        if count == 0:
            return []

        # Con muchos items salen mas rapido para que no dure una eternidad
        gap = min(self.ITEM_DELAY, self.MAX_SPIT_TIME / count)

        items = []

        for n, item_id in enumerate(item_ids):

            item = WorldItem(item_id, *self.MOUTH)

            item.start_fly(
                self.MOUTH,
                self._landing_point(collision_map),
                delay=self.FIRST_DELAY + n * gap,
                height=self.FLY_HEIGHT,
                duration=self.FLY_TIME
            )

            items.append(item)

        # Tiene la boca abierta hasta que sale el ultimo
        self.spit_time = self.FIRST_DELAY + count * gap + 0.2

        return items

    # ---------- update / dibujo ----------

    def update(self, dt):

        self._clock += dt

        if self.spit_time > 0:
            self.spit_time = max(0.0, self.spit_time - dt)

    def draw(self, screen, camera):
        """Boca abierta mientras escupe (el resto esta en el mapa)."""

        if self.spit_time <= 0:
            return

        mx, my = self.MOUTH

        center = camera.apply(pygame.Rect(mx - 1, my - 1, 2, 2)).center

        # La boca se abre y se cierra con cada item
        wave = abs(math.sin(self._clock * 16))

        rx = int((2.4 + 1.4 * wave) * camera.zoom)
        ry = int((2.8 + 1.8 * wave) * camera.zoom)

        mouth = pygame.Rect(0, 0, rx, ry)
        mouth.center = center

        if self.mouth_img is not None:

            size = (max(1, rx), max(1, ry))

            if size not in self._mouth_cache:

                self._mouth_cache[size] = pygame.transform.smoothscale(
                    self.mouth_img, size
                )

            screen.blit(self._mouth_cache[size], mouth.topleft)

            return

        pygame.draw.ellipse(screen, (46, 12, 12), mouth)

        pygame.draw.ellipse(
            screen, (14, 8, 6), mouth, max(2, camera.zoom // 2)
        )

    def draw_prompt(self, screen, camera):
        """Cartelito de [E] arriba de la cabeza."""

        mx = self.MOUTH[0]

        dest = camera.apply(pygame.Rect(mx - 1, self.HEAD_TOP, 2, 2))

        screen.blit(
            self.e_icon,
            self.e_icon.get_rect(midbottom=(dest.centerx, dest.top - 6))
        )