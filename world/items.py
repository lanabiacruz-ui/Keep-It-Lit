import json
import random

import pygame
from pathlib import Path

HUD_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
)


class MatchItem:

    WORLD_SIZE = 14           
    INTERACT_DISTANCE = 45    

    def __init__(self, x, y):

        self.original = pygame.image.load(
            str(HUD_DIR / "item_fosforo.png")
        ).convert_alpha()

        self.e_icon = pygame.image.load(
            str(HUD_DIR / "E.png")
        ).convert_alpha()

        self.rect = pygame.Rect(0, 0, self.WORLD_SIZE, self.WORLD_SIZE)
        self.rect.center = (x, y)

        self._scaled = None
        self._scaled_zoom = None

    def is_near(self, player):

        return (
            pygame.Vector2(player.rect.center).distance_to(
                self.rect.center
            ) <= self.INTERACT_DISTANCE
        )

    def _get_sprite(self, zoom):

        if self._scaled_zoom != zoom:

            size = int(self.WORLD_SIZE * zoom)

            self._scaled = pygame.transform.smoothscale(
                self.original,
                (size, size)
            )

            self._scaled_zoom = zoom

        return self._scaled

    def draw(self, screen, camera):

        sprite = self._get_sprite(camera.zoom)

        dest = camera.apply(self.rect)

        screen.blit(sprite, sprite.get_rect(center=dest.center))

    def draw_prompt(self, screen, camera):

        dest = camera.apply(self.rect)

        screen.blit(
            self.e_icon,
            self.e_icon.get_rect(midbottom=(dest.centerx, dest.top - 6))
        )


# ---------------------------------------------------------------
# Objetos recolectables (madera, aceite, cera, ...)
# ---------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_icon_cache = {}


def load_icon(item_id):
    """Icono de un item: assets/maps/hud/icon_<id>.png (None si falta)."""

    if item_id not in _icon_cache:

        path = HUD_DIR / f"icon_{item_id}.png"

        _icon_cache[item_id] = (
            pygame.image.load(str(path)).convert_alpha()
            if path.exists()
            else None
        )

    return _icon_cache[item_id]


def _load_json(name):

    try:
        with open(DATA_DIR / name, "r", encoding="utf-8") as f:
            return json.load(f)

    except (OSError, ValueError) as error:

        print(f"[items] No se pudo leer data/{name}: {error}")

        return {}


def load_item_defs():
    """Definiciones de data/items.json: {id: {nombre, descripcion, ...}}"""

    data = _load_json("items.json")

    return data if isinstance(data, dict) else {}


def load_spawn_zones():
    """Zonas de data/item_spawns.json: [{id, item, zona, cantidad}]"""

    data = _load_json("item_spawns.json")

    zones = data.get("zonas", []) if isinstance(data, dict) else []

    return zones if isinstance(zones, list) else []


class WorldItem(MatchItem):
    """Item tirado en el mapa. NO ilumina (a diferencia del fosforo)."""

    WORLD_SIZE = 16

    def __init__(self, item_id, x, y, spawn_id=None):

        super().__init__(x, y)

        self.item_id = item_id

        # None = lo soltaste vos; si no, "<zona>#<n>" para no repetirlo
        self.spawn_id = spawn_id

        icon = load_icon(item_id)

        if icon is not None:
            self.original = icon


def make_spawn_items(zones, defs, collision_map, seed, collected):
    """Crea los items de cada zona en un punto caminable al azar.

    La posicion depende solo de `seed` (se guarda en la partida), asi
    que al volver a cargar quedan en el mismo lugar. Los ya agarrados
    (`collected`) no se vuelven a crear.
    """

    rng = random.Random(seed)

    items = []

    for zone in zones:

        item_id = zone.get("item")

        if item_id not in defs:

            print(
                f"[items] La zona '{zone.get('id')}' usa '{item_id}', "
                "que no esta en data/items.json"
            )

            continue

        # Posicion fija: {"id": ..., "item": ..., "pos": [x, y]}
        if "pos" in zone:

            spawn_id = f"{zone.get('id', item_id)}#0"

            if spawn_id not in collected:

                px, py = zone["pos"]

                items.append(WorldItem(item_id, px, py, spawn_id))

            continue

        # Zona al azar: {"id": ..., "item": ..., "zona": [x, y, w, h]}
        try:
            x, y, w, h = zone["zona"]
        except (KeyError, TypeError, ValueError):
            continue

        for n in range(int(zone.get("cantidad", 1))):

            spawn_id = f"{zone.get('id', item_id)}#{n}"

            pos = None

            for _ in range(40):

                px = rng.randint(int(x), int(x + w))
                py = rng.randint(int(y), int(y + h))

                if collision_map.point_is_walkable(px, py):
                    pos = (px, py)
                    break

            if pos is None or spawn_id in collected:
                continue

            items.append(WorldItem(item_id, pos[0], pos[1], spawn_id))

    return items