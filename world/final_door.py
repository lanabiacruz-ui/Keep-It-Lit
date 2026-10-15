"""PUERTA FINAL (la de las 2 gemas)

Puerta VERTICAL en el pasillo horizontal que sale de la sala superior
derecha (la sala de los dos altares de piedra, detras de la puerta
violeta). Ninguna luz la rompe: se abre poniendo las DOS gemas, cada una
en SU altar y apretando F cerca del altar:

    - altar de ARRIBA: gema verde CLARA   (la normal, icon_gema.png)
    - altar de ABAJO:  gema verde OSCURO  (la del Guardian, icon_gema_verde)

Las gemas quedan flotando sobre su altar. Con las dos puestas:

    1. CARGA    rayos de cada gema hacia la puerta, la puerta tiembla y
                se llena de grietas de luz
    2. EXPLOSION flash blanco, ondas expansivas, la puerta estalla
    3. PORTAL   un haz de luz corre por el pasillo

La puerta SOLO se rompe. Despues, si seguis derecho por el pasillo hasta
el final (arriba), pasas a mapa2 con un fundido. En mapa2 hay una salida
al final de su pasillo que te devuelve a la sala de los altares.

Textura (opcional): assets/maps/puertas/puerta_final.png (24 x 65 px).

Es una subclase de Door: bloquea el paso, los golpes la hacen "resistir"
y se guarda como rota en broken_doors.
"""

import math
import random
from pathlib import Path

import pygame

from core.audio_manager import audio
from world.doors import Door, DOORS_DIR
from world.items import get_gem_icon, get_green_gem_icon


# ---------------------------------------------------------------
# DONDE ESTA Y CUANTO MIDE (unidades del mundo = pixeles de mapa.png)
# ---------------------------------------------------------------
FINAL_DOOR_ID = "puerta_final"

# Centro de la puerta. Pasillo horizontal (piso y 106..166) que sale de
# la sala de los pedestales, en un tramo recto con pared arriba y abajo.
FINAL_DOOR_POS = (1585, 136)

# Alto = piso del pasillo (61) + 2 px de borde por lado = 65.
# Ancho (grosor) = 24 (las otras puertas tienen 16: esta es mas imponente).
FINAL_DOOR_SIZE = (24, 65)

# A que distancia del altar (en unidades del mundo) se puede poner la gema
INTERACT_DIST = 44

# Base de cada altar (para medir la distancia) y donde flota su gema.
# Medido sobre mapa.png: altares de piedra en x ~1484, y 66..106 y 170..210
ALTAR_BASE = {
    "clara": (1484, 90),
    "oscura": (1485, 192),
}

SLOT_POS = {
    "clara": (1484, 62),
    "oscura": (1485, 165),
}

# Obstaculos solidos de los altares (para que no se camine encima)
ALTAR_OBSTACLES = [
    pygame.Rect(1465, 70, 40, 36),
    pygame.Rect(1466, 174, 40, 36),
]

# Que contador del juego gasta cada gema
SLOT_GEM_ATTR = {
    "clara": "gems",
    "oscura": "gems_green",
}

SLOT_NAMES = {
    "clara": "gema verde clara",
    "oscura": "gema verde oscura",
}

SLOT_COLORS = {
    "clara": (150, 235, 130),
    "oscura": (40, 200, 120),
}

# Duraciones de la secuencia (segundos)
CHARGE_TIME = 1.8
BURST_TIME = 0.25
PORTAL_TIME = 2.4
FADE_OUT = 0.55            # fundido a negro al cambiar de mapa
FADE_IN = 0.55             # y de vuelta a la imagen

# Zonas de salida: al pisarlas se cambia de mapa.
# mapa1: final del pasillo (arriba), solo si la puerta ya esta rota.
EXIT_ZONE_MAP1 = pygame.Rect(1644, 0, 60, 14)
# mapa2: final del pasillo de entrada (abajo), vuelve a mapa1.
EXIT_ZONE_MAP2 = pygame.Rect(92, 1586, 68, 14)

# Donde apareces al volver a mapa1 (justo debajo de la salida)
MAP1_RETURN = (1673, 40)

# Donde aparece el jugador en mapa2 (entrada del pasillo, abajo a la
# izquierda de mapa2.png) y por donde puede caminar. Es PROVISORIO:
# cuando dibujes mapa2 completo, cambia estos rects.
MAP2_NAME = "mapa2.png"
MAP2_SPAWN = (126, 1550)
# Todo el mapa es caminable (por ahora esta en blanco) menos las 2 paredes
# del pasillo de entrada, que estan dibujadas en mapa2.png.
MAP2_WALKABLE = [pygame.Rect(8, 8, 1984, 1592)]
MAP2_OBSTACLES = [
    # pared izquierda del pasillo (se corre un poco hacia abajo)
    pygame.Rect(68, 1388, 24, 100),
    pygame.Rect(68, 1488, 14, 112),
    # pared derecha del pasillo
    pygame.Rect(161, 1388, 14, 212),
]

GLOW_WHITE = (225, 255, 225)

_glow_cache = {}
_pillar_cache = {}
_font_cache = {}
_fade_cache = {}


# ---------------------------------------------------------------
# Utilidades de dibujo
# ---------------------------------------------------------------

def _clamp01(k):

    return max(0.0, min(1.0, k))


def _glow(radius, color):
    """Disco de luz suave (se suma sobre la pantalla con BLEND_RGB_ADD)."""

    radius = max(2, int(radius) // 2 * 2)
    key = (radius, color)

    if key not in _glow_cache:

        size = radius * 2
        surf = pygame.Surface((size, size))
        surf.fill((0, 0, 0))

        steps = max(6, radius // 2)

        for i in range(steps, 0, -1):

            k = i / steps
            level = (1.0 - k) ** 1.6

            c = (
                int(color[0] * level),
                int(color[1] * level),
                int(color[2] * level),
            )

            pygame.draw.circle(surf, c, (radius, radius), int(radius * k))

        _glow_cache[key] = surf.convert()

        # No dejar crecer la cache sin limite
        if len(_glow_cache) > 160:
            _glow_cache.pop(next(iter(_glow_cache)))

    return _glow_cache[key]


def _pillar(width, height, level):
    """Pilar de luz vertical: brillante abajo y en el centro."""

    width = max(8, int(width) // 8 * 8)
    height = max(16, int(height) // 8 * 8)
    level = max(1, min(8, int(level)))

    key = (width, height, level)

    if key not in _pillar_cache:

        small = pygame.Surface((16, 32))

        for y in range(32):

            vy = (1.0 - y / 31.0) ** 0.8

            for x in range(16):

                vx = 1.0 - abs((x - 7.5) / 8.0)
                vx = max(0.0, vx) ** 1.4

                v = vx * vy * (level / 8.0)

                small.set_at(
                    (x, y),
                    (
                        int(150 * v + 90 * v * v),
                        int(255 * v),
                        int(170 * v + 70 * v * v),
                    ),
                )

        _pillar_cache[key] = pygame.transform.smoothscale(
            small, (width, height)
        ).convert()

        if len(_pillar_cache) > 40:
            _pillar_cache.pop(next(iter(_pillar_cache)))

    return _pillar_cache[key]


def _font(size):

    if size not in _font_cache:
        _font_cache[size] = pygame.font.Font(None, size)

    return _font_cache[size]


def _fade_surface(size):

    if size not in _fade_cache:
        _fade_cache[size] = pygame.Surface(size).convert()

    return _fade_cache[size]


# ---------------------------------------------------------------
# Textura de la puerta (por codigo, o el PNG si lo dibujaste vos)
# ---------------------------------------------------------------

def _build_sprite():
    """Se dibuja acostada (65 x 24) y al final se gira a vertical."""

    W, H = FINAL_DOOR_SIZE          # 24 x 65 (vertical)
    w, h = H, W                     # 65 x 24 (acostada, para dibujar)

    path = DOORS_DIR / "puerta_final.png"

    if path.exists():

        img = pygame.image.load(str(path)).convert_alpha()

        if img.get_size() != (W, H):
            img = pygame.transform.scale(img, (W, H))

        return img

    outline = (14, 12, 20)
    base = (58, 54, 78)
    light = (96, 90, 128)
    dark = (36, 33, 52)
    metal = (30, 30, 40)
    metal_l = (92, 92, 112)

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    pygame.draw.rect(surf, outline, (0, 0, w, h), border_radius=4)
    pygame.draw.rect(surf, base, (1, 1, w - 2, h - 2), border_radius=3)

    # bisel
    pygame.draw.line(surf, light, (3, 2), (w - 4, 2))
    pygame.draw.line(surf, dark, (3, h - 3), (w - 4, h - 3))
    pygame.draw.line(surf, light, (2, 3), (2, h - 4))
    pygame.draw.line(surf, dark, (w - 3, 3), (w - 3, h - 4))

    # bloques de piedra
    rng = random.Random("puerta-final")

    for y in (h // 2 - 1,):
        pygame.draw.line(surf, dark, (3, y), (w - 4, y))
        pygame.draw.line(surf, light, (3, y + 1), (w - 4, y + 1))

    for x in range(10, w - 6, 14):
        pygame.draw.line(surf, dark, (x, 3), (x, h // 2 - 2))

    for x in range(17, w - 6, 14):
        pygame.draw.line(surf, dark, (x, h // 2 + 1), (x, h - 4))

    for _ in range(14):
        x = rng.randint(4, w - 8)
        y = rng.randint(4, h - 5)
        pygame.draw.line(surf, dark, (x, y), (x + rng.randint(1, 3), y))

    # fajas de hierro a los costados
    for x in (4, w - 7):
        pygame.draw.rect(surf, metal, (x, 2, 3, h - 4))
        pygame.draw.line(surf, metal_l, (x, 2), (x, h - 4))

    # runa del medio (entre los dos huecos)
    cx, cy = w // 2, h // 2
    pygame.draw.line(surf, (120, 200, 150), (cx, cy - 4), (cx, cy + 4))
    pygame.draw.line(surf, (120, 200, 150), (cx - 2, cy - 2), (cx + 2, cy - 2))
    pygame.draw.line(surf, (120, 200, 150), (cx - 2, cy + 2), (cx + 2, cy + 2))

    # -90: lo de la izquierda queda ARRIBA
    return pygame.transform.rotate(surf, -90)


_sprite_cache = {}


def _get_sprite():

    if "base" not in _sprite_cache:
        _sprite_cache["base"] = _build_sprite()

    return _sprite_cache["base"]


# ---------------------------------------------------------------
# La puerta
# ---------------------------------------------------------------

class FinalDoor(Door):

    is_final = True

    def __init__(self, game=None, slots=None):

        # No se llama a Door.__init__: esta puerta no esta en DOOR_TYPES
        self.id = FINAL_DOOR_ID
        self.kind = "final"
        self.orient = "v"
        self.length = FINAL_DOOR_SIZE[1]

        # Ninguna luz la rompe (max_hits None = no se rompe a golpes)
        self.max_hits = None
        self.hits_left = None
        self.hit_cost = 0.0

        w, h = FINAL_DOOR_SIZE

        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = FINAL_DOOR_POS

        self.broken = False
        self.flash = 0.0

        self.game = game

        self.sprite = _get_sprite()
        self._scaled = None
        self._scaled_zoom = None

        slots = slots or {}
        self.slots = {k: bool(slots.get(k, False)) for k in SLOT_POS}

        # locked | charge | burst | portal | fade | done
        self.state = "locked"
        self.t = 0.0
        self.clock = 0.0

        self.particles = []
        self.shards = []
        self.rings = []
        self.sock_pulse = {k: 0.0 for k in SLOT_POS}
        self.flying = []          # gemas que vuelan hacia su hueco
        self.cracks = self._make_cracks()
        self._shake_off = (0, 0)
        self._hint_alpha = 0.0
        self._near = False
        self._near_key = None
        self._entered = False

        # Si la partida se guardo con las dos gemas ya puestas pero sin
        # haber terminado, la secuencia arranca de nuevo.
        if all(self.slots.values()):
            self._start_charge(silent=True)

    # ---------- estado ----------

    @property
    def breakable(self):

        return False

    @property
    def sequence_active(self):
        """True mientras dura la secuencia: el juego se congela."""

        return self.state in ("charge", "burst")

    def slots_for_save(self):

        return dict(self.slots)

    def _set_state(self, state):

        self.state = state
        self.t = 0.0

    def center(self):

        return FINAL_DOOR_POS

    def slot_pos(self, key):

        return SLOT_POS[key]

    def _make_cracks(self):
        """Grietas de luz (puntos relativos al centro de la puerta)."""

        rng = random.Random("grietas-final")
        w, h = FINAL_DOOR_SIZE
        out = []

        for _ in range(9):

            x = rng.uniform(-w * 0.45, w * 0.45)
            y = rng.uniform(-h * 0.3, h * 0.3)

            pts = [(x, y)]

            for _ in range(rng.randint(3, 5)):
                x = max(-w * 0.48, min(w * 0.48, x + rng.uniform(-9, 9)))
                y = max(-h * 0.45, min(h * 0.45, y + rng.uniform(-6, 6)))
                pts.append((x, y))

            out.append(pts)

        return out

    # ---------- interaccion ----------

    def nearest_altar(self, player_rect):
        """Altar vacio que tenes al lado (o None)."""

        px, py = player_rect.center
        best, best_d = None, INTERACT_DIST

        for key, (ax, ay) in ALTAR_BASE.items():

            if self.slots[key]:
                continue

            d = math.hypot(px - ax, py - ay)

            if d <= best_d:
                best, best_d = key, d

        return best

    def player_near(self, player_rect):

        self._near_key = self.nearest_altar(player_rect)

        return self._near_key is not None and self.state == "locked"

    def try_interact(self, game):
        """Se llama al apretar F. Devuelve True si la tecla se uso aca
        (asi no se abre la tienda ni se agarra otra cosa)."""

        if self.state != "locked":
            return False

        key = self.nearest_altar(game.player.rect)

        if key is None:
            return False

        attr = SLOT_GEM_ATTR[key]

        if int(getattr(game, attr, 0)) <= 0:

            game.show_message(
                f"Este altar pide la {SLOT_NAMES[key]}"
            )

            audio.play("door_resist")

            return True

        setattr(game, attr, int(getattr(game, attr)) - 1)

        self._place(key)

        left = [k for k in SLOT_POS if not self.slots[k]]

        if left:
            game.show_message(f"Falta la {SLOT_NAMES[left[0]]}")

        return True

    def resist(self):
        """Un golpe de luz: solo destella."""

        self.flash = 0.12

    def _place(self, key):

        self.slots[key] = True
        self.sock_pulse[key] = 1.0

        x, y = self.slot_pos(key)

        audio.play("gem")

        color = SLOT_COLORS[key]

        for _ in range(26):
            self._spark(x, y, color, 20, 70, 0.35, 0.8, 1.6)

        self.rings.append([x, y, 2.0, 22.0, 0.0, 0.5, color, 3])

        if self.game is not None:
            self.game.fx.shake(2.5, 0.25)

        if all(self.slots.values()):
            self._start_charge()

    # ---------- secuencia ----------

    def _start_charge(self, silent=False):

        self._set_state("charge")

        if not silent:
            audio.play("alert")

    def _start_burst(self):

        self._set_state("burst")

        cx, cy = self.center()
        game = self.game

        audio.play("door_break")
        audio.play("explosion")

        if game is not None:
            game.fx.flash(0.8, (235, 255, 235), 1.0)
            game.fx.shake(18.0, 1.0)

        # Pedazos de la puerta
        w, h = FINAL_DOOR_SIZE
        cell = 8

        for gy in range(0, h, cell):
            for gx in range(0, w, cell):

                piece = self.sprite.subsurface(
                    pygame.Rect(gx, gy, min(cell, w - gx), min(cell, h - gy))
                ).copy()

                px = self.rect.left + gx + piece.get_width() / 2
                py = self.rect.top + gy + piece.get_height() / 2

                ang = math.atan2(py - cy, px - cx) + random.uniform(-0.5, 0.5)
                spd = random.uniform(40, 130)

                self.shards.append({
                    "img": piece,
                    "x": px, "y": py,
                    "vx": math.cos(ang) * spd,
                    "vy": math.sin(ang) * spd - random.uniform(0, 30),
                    "rot": random.uniform(0, 360),
                    "vr": random.uniform(-420, 420),
                    "life": random.uniform(1.2, 2.0),
                    "max": 2.0,
                })

        # Ondas expansivas
        for i, color in enumerate((GLOW_WHITE, SLOT_COLORS["clara"], SLOT_COLORS["oscura"])):
            self.rings.append([cx, cy, 4.0, 150.0 + 30 * i, -0.08 * i, 0.9 + 0.1 * i, color, 8 - 2 * i])

        # La puerta ya no bloquea el paso (se mueve su rect afuera del mapa)
        self.rect = pygame.Rect(-500, -500, 1, 1)

        # Chispas de las dos gemas
        for i in range(120):

            color = SLOT_COLORS["clara"] if i % 2 else SLOT_COLORS["oscura"]

            self._spark(
                cx + random.uniform(-w / 2, w / 2),
                cy + random.uniform(-h / 2, h / 2),
                color, 40, 220, 0.7, 1.6, 2.4,
            )

    def _start_portal(self):

        self._set_state("portal")

        if self.game is not None:
            self.game.show_message("La puerta se rompio")

        audio.play("flashbang", 0.5)

    def _finish(self):

        self._set_state("done")
        self.broken = True

        self.particles = []
        self.shards = []
        self.rings = []

    # ---------- particulas ----------

    def _spark(self, x, y, color, smin, smax, lmin, lmax, size, angle=None):

        ang = random.uniform(0, math.tau) if angle is None else angle
        spd = random.uniform(smin, smax)

        self.particles.append({
            "x": x, "y": y,
            "vx": math.cos(ang) * spd,
            "vy": math.sin(ang) * spd,
            "life": random.uniform(lmin, lmax),
            "max": lmax,
            "color": color,
            "size": size * random.uniform(0.6, 1.2),
            "drag": 2.2,
            "ay": 0.0,
        })

    def _rise(self, x, y, color):
        """Particula que sube (portal)."""

        self.particles.append({
            "x": x, "y": y,
            "vx": random.uniform(40, 90),
            "vy": random.uniform(-6, 6),
            "life": random.uniform(0.9, 1.7),
            "max": 1.7,
            "color": color,
            "size": random.uniform(1.0, 2.2),
            "drag": 0.2,
            "ay": 0.0,
        })

    # ---------- update ----------

    def update(self, dt):

        self.clock += dt
        self.t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        for k in self.sock_pulse:
            if self.sock_pulse[k] > 0:
                self.sock_pulse[k] = max(0.0, self.sock_pulse[k] - dt * 1.6)

        self._update_fx_lists(dt)

        # cartelito "E"
        want = 1.0 if self._near and self.state == "locked" else 0.0
        self._hint_alpha += (want - self._hint_alpha) * min(1.0, dt * 10)

        cx, cy = self.center()

        if self.state == "locked":

            # Los huecos llenos largan chispitas
            for key, filled in self.slots.items():
                if filled and random.random() < dt * 5:
                    x, y = self.slot_pos(key)
                    self._spark(x, y - 2, SLOT_COLORS[key], 6, 22, 0.5, 0.9, 1.2,
                                angle=-math.pi / 2 + random.uniform(-0.6, 0.6))

        elif self.state == "charge":

            k = _clamp01(self.t / CHARGE_TIME)

            # Temblor cada vez mas fuerte
            amp = 0.6 + 1.6 * k
            self._shake_off = (
                random.uniform(-amp, amp),
                random.uniform(-amp * 0.5, amp * 0.5),
            )

            if self.game is not None:
                self.game.fx.shake(1.0 + 7.0 * k, 0.12)

            # Particulas que se meten hacia el centro
            for _ in range(int(2 + 8 * k)):

                key = random.choice(list(SLOT_POS))
                sx, sy = self.slot_pos(key)

                ang = random.uniform(0, math.tau)
                dist = random.uniform(10, 34)

                px = cx + math.cos(ang) * dist
                py = cy + math.sin(ang) * dist

                speed = 90 + 90 * k
                a = math.atan2(cy - py, cx - px)

                self.particles.append({
                    "x": px, "y": py,
                    "vx": math.cos(a) * speed,
                    "vy": math.sin(a) * speed,
                    "life": dist / speed,
                    "max": dist / speed,
                    "color": SLOT_COLORS[key],
                    "size": 1.4,
                    "drag": 0.0,
                    "ay": 0.0,
                })

            if self.t >= CHARGE_TIME:
                self._shake_off = (0, 0)
                self._start_burst()

        elif self.state == "burst":

            if self.t >= BURST_TIME:
                self._start_portal()

        elif self.state == "portal":

            # El haz de luz corre por el pasillo (ya podes moverte)
            if self.t < PORTAL_TIME - 1.7:

                for _ in range(3):
                    y = cy + random.uniform(-FINAL_DOOR_SIZE[1] * 0.4, FINAL_DOOR_SIZE[1] * 0.4)
                    color = random.choice((SLOT_COLORS["clara"], SLOT_COLORS["oscura"], GLOW_WHITE))
                    self._rise(cx + random.uniform(-4, 4), y, color)

            if self.game is not None and self.t < 0.8:
                self.game.fx.shake(4.0 * (1.0 - self.t / 0.8), 0.1)

            if self.t >= PORTAL_TIME:
                self._finish()

    def _update_fx_lists(self, dt):

        alive = []

        for p in self.particles:

            p["life"] -= dt

            if p["life"] <= 0:
                continue

            drag = max(0.0, 1.0 - p["drag"] * dt)

            p["vx"] *= drag
            p["vy"] = p["vy"] * drag + p["ay"] * dt

            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt

            alive.append(p)

        self.particles = alive

        alive = []

        for s in self.shards:

            s["life"] -= dt

            if s["life"] <= 0:
                continue

            drag = max(0.0, 1.0 - 1.6 * dt)

            s["vx"] *= drag
            s["vy"] *= drag
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["rot"] += s["vr"] * dt

            alive.append(s)

        self.shards = alive

        alive = []

        for r in self.rings:

            r[4] += dt

            if r[4] < r[5]:
                alive.append(r)

        self.rings = alive

    def set_player_near(self, near):

        self._near = bool(near)

    # ---------- dibujo ----------

    def _w2s(self, camera, x, y):

        return (
            x * camera.zoom - camera.x,
            y * camera.zoom - camera.y,
        )

    def _get_scaled(self, zoom):

        if self._scaled_zoom != zoom:

            w, h = self.sprite.get_size()

            self._scaled = pygame.transform.scale(
                self.sprite, (w * zoom, h * zoom)
            )

            self._scaled_zoom = zoom

        return self._scaled

    def _add_glow(self, screen, camera, wx, wy, radius_world, color):

        sx, sy = self._w2s(camera, wx, wy)
        r = int(radius_world * camera.zoom)

        if r < 4:
            return

        g = _glow(r, color)

        screen.blit(g, (sx - r, sy - r), special_flags=pygame.BLEND_RGB_ADD)

    def draw(self, screen, camera):
        """Dibuja la puerta y todos sus efectos (en el mundo)."""

        zoom = camera.zoom
        cx, cy = self.center()

        # --- puerta entera (hasta que explota) ---
        if self.state in ("locked", "charge"):

            scaled = self._get_scaled(zoom)

            dest = camera.apply(self.rect).copy()
            dest.x += int(self._shake_off[0] * zoom)
            dest.y += int(self._shake_off[1] * zoom)

            if self.flash > 0:

                tmp = scaled.copy()
                tmp.fill((110, 110, 110, 0), special_flags=pygame.BLEND_RGB_ADD)
                screen.blit(tmp, dest.topleft)

            else:
                screen.blit(scaled, dest.topleft)

            self._draw_slots(screen, camera, dest)

    def draw_fx(self, screen, camera):
        """Efectos de luz: se dibujan ENCIMA de la oscuridad."""

        zoom = camera.zoom

        if self.state in ("locked", "charge"):
            self._draw_slot_glows(screen, camera)

        if self.state == "charge":
            self._draw_charge(screen, camera)

        # --- pilar de luz ---
        if self.state in ("burst", "portal"):
            self._draw_portal(screen, camera)

        # --- pedazos ---
        for s in self.shards:

            img = pygame.transform.rotozoom(s["img"], s["rot"], zoom)

            sx, sy = self._w2s(camera, s["x"], s["y"])

            if s["life"] < 0.5:
                img.set_alpha(int(255 * s["life"] / 0.5))

            screen.blit(img, img.get_rect(center=(int(sx), int(sy))))

        # --- ondas ---
        for x, y, r0, r1, t, dur, color, width in self.rings:

            if t < 0:
                continue

            k = _clamp01(t / dur)
            r = r0 + (r1 - r0) * (1 - (1 - k) ** 2)

            sx, sy = self._w2s(camera, x, y)

            w = max(1, int(width * (1 - k)))

            fade = 1.0 - k * 0.7

            c = (int(color[0] * fade), int(color[1] * fade), int(color[2] * fade))

            pygame.draw.circle(
                screen, c, (int(sx), int(sy)), max(1, int(r * zoom)), w
            )

        # --- particulas (sumando luz) ---
        for p in self.particles:

            k = _clamp01(p["life"] / p["max"])

            sx, sy = self._w2s(camera, p["x"], p["y"])

            r = max(2, int(p["size"] * zoom * (0.5 + 0.5 * k)))

            c = (
                int(p["color"][0] * k),
                int(p["color"][1] * k),
                int(p["color"][2] * k),
            )

            if k > 0.4:
                screen.blit(
                    _glow(r * 2, p["color"]),
                    (sx - r * 2, sy - r * 2),
                    special_flags=pygame.BLEND_RGB_ADD,
                )
            else:
                pygame.draw.circle(
                    screen, c, (int(sx), int(sy)), max(1, r // 2)
                )

    def _slot_float(self, key):
        """Posicion de la gema flotando (sube y baja)."""

        x, y = SLOT_POS[key]

        bob = math.sin(self.clock * 2.6 + (0 if key == "clara" else 2.1)) * 2.2

        return x, y + bob

    def _draw_slots(self, screen, camera, dest=None):
        """Gemas flotando sobre los altares (debajo de la oscuridad)."""

        zoom = camera.zoom

        for key in SLOT_POS:

            x, y = self._slot_float(key)
            sx, sy = self._w2s(camera, x, y)

            if self.slots[key]:

                icon = get_gem_icon() if key == "clara" else get_green_gem_icon()
                size = int(14 * zoom)
                icon = pygame.transform.scale(icon, (size, size))

                screen.blit(icon, icon.get_rect(center=(int(sx), int(sy))))

            else:

                # Altar vacio: aro que late suave, para marcar donde va
                beat = 0.5 + 0.5 * math.sin(self.clock * 2.4 + (0 if key == "clara" else 1.7))
                rc = tuple(int(c * (0.25 + 0.5 * beat)) for c in SLOT_COLORS[key])

                pygame.draw.circle(
                    screen, rc, (int(sx), int(sy)), int(7 * zoom), max(1, zoom // 2)
                )

    def _draw_slot_glows(self, screen, camera):
        """Resplandor de las gemas puestas (encima de la oscuridad)."""

        for key in SLOT_POS:

            if not self.slots[key]:
                continue

            x, y = self._slot_float(key)

            radius = 15 + 14 * self.sock_pulse[key]

            if self.state == "charge":
                radius += 12 * _clamp01(self.t / CHARGE_TIME)

            self._add_glow(screen, camera, x, y, radius, SLOT_COLORS[key])

    def _draw_charge(self, screen, camera):

        zoom = camera.zoom
        k = _clamp01(self.t / CHARGE_TIME)
        cx, cy = self.center()

        cx += self._shake_off[0]
        cy += self._shake_off[1]

        # rayos de cada gema al centro
        for key in SLOT_POS:

            x, y = self.slot_pos(key)

            x, y = self._slot_float(key)

            a = self._w2s(camera, x, y)
            b = self._w2s(camera, cx, cy)

            color = SLOT_COLORS[key]

            width = max(1, int((1 + 3 * k) * zoom / 2))

            pygame.draw.line(screen, color, a, b, width)
            pygame.draw.line(screen, (255, 255, 255), a, b, max(1, width // 3))

        # luz del centro creciendo
        self._add_glow(screen, camera, cx, cy, 10 + 40 * k, GLOW_WHITE)

        # grietas de luz que se van abriendo
        total = len(self.cracks)
        shown = int(total * _clamp01((k - 0.15) / 0.8)) + (1 if k > 0.15 else 0)

        for i in range(min(total, shown)):

            pts = [
                self._w2s(camera, cx + px, cy + py)
                for px, py in self.cracks[i]
            ]

            pygame.draw.lines(screen, (210, 255, 215), False, pts, max(1, zoom // 2))

    def _draw_portal(self, screen, camera):

        zoom = camera.zoom
        cx, cy = self.center()

        if self.state == "burst":
            k = _clamp01(self.t / BURST_TIME) * 0.5
        else:
            out = _clamp01((PORTAL_TIME - self.t) / 0.9)
            k = (0.5 + 0.5 * _clamp01(self.t / 0.8)) * out

        # destello grande en el hueco
        self._add_glow(screen, camera, cx, cy, 30 + 30 * k, GLOW_WHITE)

        # pilar que sube por el pasillo (parpadea un poco)
        flick = 1.0 + 0.12 * math.sin(self.clock * 18)

        level = int(8 * k * flick)

        # el haz de luz corre por el pasillo, hacia la derecha
        thick = FINAL_DOOR_SIZE[1] * zoom * (0.6 + 0.5 * k)
        length = 220 * zoom * k + 40

        pil = _pillar(thick, length, level)
        pil = pygame.transform.rotate(pil, -90)

        sx, sy = self._w2s(camera, cx, cy)

        screen.blit(
            pil,
            (sx - 12 * zoom, sy - pil.get_height() / 2),
            special_flags=pygame.BLEND_RGB_ADD,
        )

        # aro que gira alrededor de la boca del portal
        ring_n = 16

        for i in range(ring_n):

            ang = self.clock * 2.4 + i * math.tau / ring_n

            x = cx + math.sin(ang) * 7
            y = cy + math.cos(ang) * FINAL_DOOR_SIZE[1] * 0.42

            color = SLOT_COLORS["clara"] if i % 2 else SLOT_COLORS["oscura"]

            self._add_glow(screen, camera, x, y, 5, color)

    def draw_overlay(self, screen):
        """Cosas de pantalla: cartelito E y el fundido final."""

        sw, sh = screen.get_size()

        # cartelito "E: poner gema"
        if self._hint_alpha > 0.05 and self.state == "locked":

            key = self._near_key

            if key is not None:

                font = _font(26)
                text = font.render(
                    f"F  poner {SLOT_NAMES[key]}", True, (235, 255, 235)
                )

                pad = 8
                box = pygame.Surface(
                    (text.get_width() + pad * 2, text.get_height() + pad), pygame.SRCALPHA
                )

                a = int(190 * self._hint_alpha)
                pygame.draw.rect(box, (10, 14, 12, a), box.get_rect(), border_radius=6)

                text.set_alpha(int(255 * self._hint_alpha))
                box.blit(text, (pad, pad // 2))

                screen.blit(box, (sw // 2 - box.get_width() // 2, int(sh * 0.12)))


# ---------------------------------------------------------------
# Cambio de mapa (ida y vuelta)
# ---------------------------------------------------------------

def _capture(game):
    """Foto del mapa en el que estas (para poder volver)."""

    wm = game.world_map
    col = game.collision_map

    return {
        "image": wm.image,
        "walkable": col.walkable,
        "obstacles": col.obstacles,
        "doors": game.doors.doors,
        "items": getattr(game, "world_items", []),
        "drops": getattr(game, "light_drops", []),
    }


def _apply(game, st):

    wm = game.world_map
    img = st["image"]

    wm.image = img
    wm.width = img.get_width()
    wm.height = img.get_height()
    wm.rect = img.get_rect(topleft=(0, 0))

    col = game.collision_map
    col.world_width = wm.width
    col.world_height = wm.height
    col.walkable = st["walkable"]
    col.obstacles = st["obstacles"]

    game.doors.doors = st["doors"]
    game.world_items = st["items"]
    game.light_drops = st["drops"]

    cam = game.camera
    cam.world_width = wm.width
    cam.world_height = wm.height
    cam.scaled_width = int(wm.width * cam.zoom)
    cam.scaled_height = int(wm.height * cam.zoom)


def enter_map(game, target, pos=None):
    """Pasa a 'mapa1' o 'mapa2' (guarda el que dejas, carga el otro)."""

    cur = getattr(game, "current_map", "mapa1")

    if not hasattr(game, "_map_states"):
        game._map_states = {}

    if cur == target:
        return

    game._map_states[cur] = _capture(game)

    st = game._map_states.get(target)

    if st is None:

        # Primera vez en mapa2
        base = Path(__file__).resolve().parent.parent
        img = pygame.image.load(
            str(base / "assets" / "maps" / "region_01" / MAP2_NAME)
        ).convert()

        st = {
            "image": img,
            "walkable": [r.copy() for r in MAP2_WALKABLE],
            "obstacles": [r.copy() for r in MAP2_OBSTACLES],
            "doors": [],
            "items": [],
            "drops": [],
        }

    _apply(game, st)

    game.current_map = target

    if pos is None:
        pos = MAP2_SPAWN if target == "mapa2" else MAP1_RETURN

    game.player.rect.center = pos

    game.player.image_rect.midbottom = (
        game.player.rect.centerx,
        game.player.rect.bottom + 3,
    )

    # la camara salta directo (sin deslizarse desde el otro mapa)
    game.camera.update(game.player)


def enter_map2(game, pos=None):

    enter_map(game, "mapa2", pos)


class MapSwitcher:
    """Detecta las zonas de salida y hace el fundido entre mapas."""

    def __init__(self):

        self.target = None
        self.phase = None     # None | "out" | "in"
        self.t = 0.0

    @property
    def active(self):

        return self.phase is not None

    def check(self, game):
        """Llamar cada cuadro (cuando el juego corre normal)."""

        if self.active:
            return

        pos = game.player.rect.center
        cur = getattr(game, "current_map", "mapa1")

        if cur == "mapa1":

            door_gone = FINAL_DOOR_ID in game.doors.broken_ids

            if door_gone and EXIT_ZONE_MAP1.collidepoint(pos):
                self._start("mapa2")

        elif EXIT_ZONE_MAP2.collidepoint(pos):

            self._start("mapa1")

    def _start(self, target):

        self.target = target
        self.phase = "out"
        self.t = 0.0

        audio.play("pickup", 0.6)

    def update(self, dt, game):

        if not self.active:
            return

        self.t += dt

        if self.phase == "out" and self.t >= FADE_OUT:

            enter_map(game, self.target)

            self.phase = "in"
            self.t = 0.0

        elif self.phase == "in" and self.t >= FADE_IN:

            self.phase = None
            self.t = 0.0

    def draw(self, screen):

        if not self.active:
            return

        if self.phase == "out":
            a = _clamp01(self.t / FADE_OUT)
        else:
            a = 1.0 - _clamp01(self.t / FADE_IN)

        surf = _fade_surface(screen.get_size())
        surf.fill((0, 0, 0))
        surf.set_alpha(int(255 * a))
        screen.blit(surf, (0, 0))