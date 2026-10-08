import json
import random

import pygame
from pathlib import Path

from world.lights import light_stats

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


def _gem_placeholder():
    """Gema dibujada por codigo, por si falta icon_gema.png."""

    surf = pygame.Surface((64, 64), pygame.SRCALPHA)

    top = [(32, 6), (56, 24), (32, 58), (8, 24)]

    pygame.draw.polygon(surf, (90, 200, 255), top)
    pygame.draw.polygon(surf, (190, 240, 255), [(32, 6), (56, 24), (32, 24)])
    pygame.draw.polygon(surf, (50, 140, 220), [(8, 24), (32, 24), (32, 58)])
    pygame.draw.polygon(surf, (235, 250, 255), top, 3)

    return surf


_gem_cache = None


def get_gem_icon():
    """Icono de la gema: assets/maps/hud/icon_gema.png (64x64). Si no
    existe, una gema dibujada por codigo."""

    global _gem_cache

    if _gem_cache is None:

        icon = load_icon("gema")

        _gem_cache = icon if icon is not None else _gem_placeholder()

    return _gem_cache


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

        elif item_id == "gema":
            self.original = get_gem_icon()

        # Las monedas y la gema se juntan solas al pasar cerca (sin
        # apretar E)
        self.auto = item_id in (
            "moneda", "moneda_5", "moneda_10", "gema"
        )

        # Animacion de "salir del cofre" (None = quieto en el piso)
        self.fly = None
        self._lift = 0.0

    def start_fly(self, src, dst, delay=0.0, height=14.0, duration=0.45):
        """Sale disparado de `src` y cae en `dst` (como un dispenser)."""

        self.fly = {
            "src": src,
            "dst": dst,
            "delay": delay,
            "t": 0.0,
            "dur": duration,
            "h": height,
        }

        self.rect.center = (round(src[0]), round(src[1]))

    def update_fly(self, dt):

        f = self.fly

        if f is None:
            return

        if f["delay"] > 0:
            f["delay"] -= dt
            return

        f["t"] += dt / f["dur"]

        if f["t"] >= 1.0:

            self.rect.center = (round(f["dst"][0]), round(f["dst"][1]))
            self.fly = None
            self._lift = 0.0

            return

        t = f["t"]

        x = f["src"][0] + (f["dst"][0] - f["src"][0]) * t
        y = f["src"][1] + (f["dst"][1] - f["src"][1]) * t

        self.rect.center = (round(x), round(y))

        # Arco: sube y baja (0 al principio y al final)
        self._lift = f["h"] * 4 * t * (1 - t)

    def is_near(self, player):

        # En el aire no se puede agarrar
        if self.fly is not None:
            return False

        return super().is_near(player)

    def draw(self, screen, camera):

        f = self.fly

        # Todavia "dentro" del cofre
        if f is not None and f["delay"] > 0:
            return

        sprite = self._get_sprite(camera.zoom)

        dest = camera.apply(self.rect)

        lift = int(self._lift * camera.zoom)

        screen.blit(
            sprite,
            sprite.get_rect(center=(dest.centerx, dest.centery - lift))
        )


class LightItem(MatchItem):
    """Luz tirada en el piso (fosforo o vela). Ilumina un poco y se
    recuerda cuanta vida le quedaba, asi al agarrarla sigue igual."""

    def __init__(self, kind, x, y, life=1.0):

        # La vela es un poco mas grande que el fosforo
        if kind == "vela":
            self.WORLD_SIZE = 16

        super().__init__(x, y)

        self.kind = kind
        self.life = float(life)

        # El fosforo usa el sprite de MatchItem; las demas luces usan su
        # icono (assets/maps/hud/icon_<luz>.png)
        if kind != "fosforo":

            icon = load_icon(kind)

            if icon is not None:
                self.original = icon

    @property
    def light_radius(self):

        return light_stats(self.kind)["radio_suelo"]


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