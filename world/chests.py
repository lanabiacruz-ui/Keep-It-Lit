import json
import math
import random
from pathlib import Path

import pygame

from world.items import WorldItem


BASE_DIR = Path(__file__).resolve().parent.parent

CHEST_DIR = BASE_DIR / "assets" / "maps" / "cofre"
DATA_FILE = BASE_DIR / "data" / "chests.json"

# El PNG de 128x128 se dibuja a 20x20 unidades (80 px en pantalla)
CHEST_SIZE = 20

# Parte del cofre que bloquea el paso (los pies del cofre)
BLOCK_W = 18
BLOCK_H = 12

# Relojito que aparece mientras el cofre esta en espera
CLOCK_SIZE = 10

FLASH_TIME = 0.12
SHAKE_TIME = 0.18

# Los items caen a esta distancia del cofre (unidades del mundo)
DROP_MIN_DIST = 16
DROP_MAX_DIST = 40

# Cada item sale un poquito despues del anterior
DROP_DELAY = 0.07

DEFAULTS = {
    "espera_segundos": 180,
    "items_por_cofre": [10, 15],
    "pesos": {"moneda": 1},
    "cofres": [],
}


def load_config():

    config = dict(DEFAULTS)

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            config.update(data)

    except (OSError, ValueError) as error:

        print(f"[cofres] No se pudo leer data/chests.json: {error}")

    return config


def format_time(seconds):
    """150.2 -> '2:31'"""

    total = max(0, int(math.ceil(seconds)))

    return f"{total // 60}:{total % 60:02d}"


_image_cache = {}


def _load(name):

    if name not in _image_cache:

        _image_cache[name] = pygame.image.load(
            str(CHEST_DIR / name)
        ).convert_alpha()

    return _image_cache[name]


class Chest:
    """Un cofre del mapa. Es un objetivo mas de los golpes del fosforo
    (tiene .rect y .take_damage)."""

    def __init__(self, chest_id, x, y, cooldown=0.0):

        self.id = chest_id

        self.rect = pygame.Rect(0, 0, CHEST_SIZE, CHEST_SIZE)
        self.rect.center = (x, y)

        # Lo que bloquea el paso del jugador
        self.block = pygame.Rect(0, 0, BLOCK_W, BLOCK_H)
        self.block.center = (x, y + 4)

        # Segundos que faltan para poder abrirlo de nuevo (0 = listo)
        self.cooldown = float(cooldown)

        # True mientras el minijuego de este cofre esta abierto
        self.busy = False

        self.flash = 0.0
        self.shake = 0.0

        self._zoom = None
        self._closed = None
        self._open = None
        self._flash_closed = None
        self._clock = None

    @property
    def ready(self):

        return self.cooldown <= 0 and not self.busy

    # ---------- golpes ----------

    def take_damage(self, amount):
        """El golpe no lo rompe: solo lo hace brillar y temblar. Quien
        decide que pasa (abrir el minijuego, avisar que esta vacio) es
        el juego."""

        self.flash = FLASH_TIME
        self.shake = SHAKE_TIME

        return 0.0

    def start_cooldown(self, seconds):

        self.cooldown = float(seconds)

    def update(self, dt):

        if self.cooldown > 0:
            self.cooldown = max(0.0, self.cooldown - dt)

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt)

    # ---------- dibujo ----------

    def _prepare(self, zoom):

        if self._zoom == zoom:
            return

        size = (int(CHEST_SIZE * zoom), int(CHEST_SIZE * zoom))

        self._closed = pygame.transform.smoothscale(
            _load("cofre_cerrado.png"), size
        )

        self._open = pygame.transform.smoothscale(
            _load("cofre_abierto.png"), size
        )

        self._flash_closed = self._closed.copy()
        self._flash_closed.fill(
            (110, 110, 110, 0),
            special_flags=pygame.BLEND_RGB_ADD
        )

        clock = int(CLOCK_SIZE * zoom)

        self._clock = pygame.transform.smoothscale(
            _load("cofre_reloj.png"), (clock, clock)
        )

        self._zoom = zoom

    def draw(self, screen, camera, font):

        self._prepare(camera.zoom)

        dest = camera.apply(self.rect)

        if self.cooldown > 0:
            sprite = self._open
        elif self.flash > 0:
            sprite = self._flash_closed
        else:
            sprite = self._closed

        # Temblor corto al recibir un golpe
        dx = 0

        if self.shake > 0:

            dx = int(
                math.sin(self.shake * 70) * 3 * (self.shake / SHAKE_TIME)
            )

        screen.blit(sprite, (dest.x + dx, dest.y))

        # Reloj y cuenta regresiva mientras esta en espera
        if self.cooldown > 0:

            clock_rect = self._clock.get_rect(
                midbottom=(dest.centerx - 14, dest.top + 6)
            )

            screen.blit(self._clock, clock_rect)

            txt = format_time(self.cooldown)

            shadow = font.render(txt, True, (0, 0, 0))
            label = font.render(txt, True, (255, 235, 170))

            pos = label.get_rect(
                midleft=(clock_rect.right + 4, clock_rect.centery)
            )

            screen.blit(shadow, pos.move(1, 1))
            screen.blit(label, pos)


class ChestManager:

    def __init__(self, saved_cooldowns=None):

        config = load_config()

        self.wait = float(config["espera_segundos"])

        low, high = config["items_por_cofre"]
        self.min_items = int(low)
        self.max_items = int(high)

        self.weights = dict(config["pesos"])

        saved = saved_cooldowns if isinstance(saved_cooldowns, dict) else {}

        self.chests = []

        for entry in config["cofres"]:

            try:
                x, y = entry["pos"]
                chest_id = entry["id"]
            except (KeyError, TypeError, ValueError):
                continue

            self.chests.append(
                Chest(chest_id, x, y, float(saved.get(chest_id, 0.0)))
            )

        self.font = pygame.font.Font(None, 24)

        print(f"[cofres] {len(self.chests)} cofres en el mapa")

    @property
    def blocking_rects(self):
        """Rects que bloquean el paso (para la colision)."""

        return [c.block for c in self.chests]

    def update(self, dt):

        for chest in self.chests:
            chest.update(dt)

    def draw(self, screen, camera):

        for chest in self.chests:
            chest.draw(screen, camera, self.font)

    def save_data(self):
        """{id: segundos que faltan} solo de los que estan en espera."""

        return {
            c.id: round(c.cooldown, 1)
            for c in self.chests
            if c.cooldown > 0
        }

    def nearest_ready(self, pos, max_dist):
        """El cofre listo mas cercano a `pos` (None si no hay ninguno
        a menos de `max_dist`)."""

        best = None
        best_dist = max_dist

        for chest in self.chests:

            if not chest.ready:
                continue

            dist = pygame.Vector2(chest.rect.center).distance_to(pos)

            if dist <= best_dist:
                best = chest
                best_dist = dist

        return best

    # ---------- drops ----------

    def roll_ids(self):
        """Que sale en esta apertura: de 10 a 15 al azar, segun los
        pesos de data/chests.json."""

        count = random.randint(self.min_items, self.max_items)

        ids = list(self.weights)
        weights = [self.weights[i] for i in ids]

        if not ids:
            return []

        return random.choices(ids, weights=weights, k=count)

    def _drop_target(self, chest, collision_map):

        cx, cy = chest.rect.center

        for _ in range(30):

            angle = random.uniform(0, math.tau)
            dist = random.uniform(DROP_MIN_DIST, DROP_MAX_DIST)

            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist

            if not collision_map.point_is_walkable(x, y):
                continue

            # No caer encima de un cofre
            if any(
                c.block.inflate(6, 6).collidepoint(x, y)
                for c in self.chests
            ):
                continue

            return (x, y)

        # Sin lugar libre: queda justo abajo del cofre
        return (cx, cy + DROP_MIN_DIST)

    def spawn_drops(self, chest, collision_map, item_defs):
        """Crea los items que salen disparados del cofre. Devuelve la
        lista de WorldItem para agregar al mundo."""

        drops = []

        origin = chest.rect.center

        for n, item_id in enumerate(self.roll_ids()):

            if item_id != "moneda" and item_id not in item_defs:

                print(f"[cofres] '{item_id}' no esta en data/items.json")

                continue

            target = self._drop_target(chest, collision_map)

            item = WorldItem(item_id, origin[0], origin[1])

            item.start_fly(origin, target, delay=n * DROP_DELAY)

            drops.append(item)

        return drops