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

# Cuanto se ve el cofre abierto despues de cada apertura (cuando todavia
# le quedan usos y no entra en espera)
OPEN_SHOW_TIME = 0.7

# Los items caen a esta distancia del cofre (unidades del mundo)
DROP_MIN_DIST = 16
DROP_MAX_DIST = 40

# Cada item sale un poquito despues del anterior
DROP_DELAY = 0.07

DEFAULTS = {
    "espera_segundos": 180,
    # Cuantas veces se puede abrir un cofre antes de quedar en espera
    "aperturas_por_cofre": [10, 15],
    # Probabilidad (peso) de que una apertura suelte N objetos
    "items_por_apertura": {"4": 35, "5": 40, "6": 25},
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

    def __init__(self, chest_id, x, y, cooldown=0.0, uses_left=None):

        self.id = chest_id

        self.rect = pygame.Rect(0, 0, CHEST_SIZE, CHEST_SIZE)
        self.rect.center = (x, y)

        # Lo que bloquea el paso del jugador
        self.block = pygame.Rect(0, 0, BLOCK_W, BLOCK_H)
        self.block.center = (x, y + 4)

        # Segundos que faltan para poder abrirlo de nuevo (0 = listo)
        self.cooldown = float(cooldown)

        # Aperturas que le quedan antes de quedar en espera
        # (None = todavia no se sorteo, se sortea en la primera apertura)
        self.uses_left = uses_left

        # True mientras el minijuego de este cofre esta abierto
        self.busy = False

        self.flash = 0.0
        self.shake = 0.0

        # Segundos que se muestra abierto tras una apertura
        self.open_time = 0.0

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

        if self.open_time > 0:
            self.open_time = max(0.0, self.open_time - dt)

    def show_open(self, seconds=OPEN_SHOW_TIME):
        """Lo muestra abierto un ratito (cofre_abierto.png)."""

        self.open_time = float(seconds)

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

        if self.cooldown > 0 or self.open_time > 0:
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

        low, high = config["aperturas_por_cofre"]
        self.min_uses = max(1, int(low))
        self.max_uses = max(self.min_uses, int(high))

        # {cantidad de objetos: peso}
        self.count_weights = {}

        for key, weight in dict(config["items_por_apertura"]).items():

            try:
                self.count_weights[int(key)] = float(weight)
            except (TypeError, ValueError):
                continue

        if not self.count_weights:
            self.count_weights = {4: 35.0, 5: 40.0, 6: 25.0}

        self.weights = dict(config["pesos"])

        saved = saved_cooldowns if isinstance(saved_cooldowns, dict) else {}

        self.chests = []

        for entry in config["cofres"]:

            try:
                x, y = entry["pos"]
                chest_id = entry["id"]
            except (KeyError, TypeError, ValueError):
                continue

            cooldown, uses_left = self._read_saved(saved.get(chest_id))

            self.chests.append(
                Chest(chest_id, x, y, cooldown, uses_left)
            )

        self.font = pygame.font.Font(None, 24)

        print(f"[cofres] {len(self.chests)} cofres en el mapa")

    @staticmethod
    def _read_saved(value):
        """Lee lo guardado de un cofre. Acepta el formato viejo (solo los
        segundos de espera) y el nuevo ({"espera": s, "usos": n})."""

        if isinstance(value, dict):

            try:
                cooldown = float(value.get("espera", 0.0))
            except (TypeError, ValueError):
                cooldown = 0.0

            uses = value.get("usos")

            if not isinstance(uses, int) or uses <= 0:
                uses = None

            return cooldown, uses

        try:
            return float(value or 0.0), None
        except (TypeError, ValueError):
            return 0.0, None

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
        """{id: {"espera": segundos que faltan, "usos": aperturas que le
        quedan}} solo de los cofres en espera o ya empezados."""

        data = {}

        for c in self.chests:

            if c.cooldown <= 0 and c.uses_left is None:
                continue

            entry = {}

            if c.cooldown > 0:
                entry["espera"] = round(c.cooldown, 1)

            if c.uses_left is not None:
                entry["usos"] = c.uses_left

            data[c.id] = entry

        return data

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

    def roll_count(self):
        """Cuantos objetos salen en esta apertura (4 a 6), segun las
        probabilidades de data/chests.json."""

        counts = list(self.count_weights)
        weights = [self.count_weights[n] for n in counts]

        return random.choices(counts, weights=weights, k=1)[0]

    def consume_use(self, chest):
        """Gasta una apertura del cofre. La primera vez sortea cuantas
        aperturas tiene (10 a 15). Cuando se acaban queda en espera.
        Devuelve True si el cofre se quedo sin aperturas."""

        if chest.uses_left is None:

            chest.uses_left = random.randint(self.min_uses, self.max_uses)

        chest.uses_left -= 1

        if chest.uses_left <= 0:

            chest.uses_left = None
            chest.start_cooldown(self.wait)

            return True

        return False

    def roll_ids(self):
        """Que sale en esta apertura: 4 a 6 objetos al azar, segun los
        pesos de data/chests.json."""

        count = self.roll_count()

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