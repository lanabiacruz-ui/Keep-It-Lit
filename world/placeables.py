import math
from pathlib import Path

import pygame

from core.audio_manager import audio
from world import items as _items
from world.items import HUD_DIR, load_icon


REACH = 64

DRAG_RANGE = 56

# si te alejas mas que esto del objeto arrastrado, se suelta
DRAG_RELEASE = 120

DRAG_SPEED = 22.0

# maximo de px por paso al mover (evita atravesar paredes finas)
DRAG_STEP = 2.0

# margen extra para agarrar el objeto con el mouse (mas comodo)
GRAB_PAD = 10

# el objeto "se levanta" un poco mientras lo arrastras
DRAG_LIFT = 4.0

BAG_SLOTS = 4
CHEST_SLOTS = 8

CONTAINER_STACK = 15

PLACE_RANGE = 72

FARO_MAX = 90.0
FARO_START = 30.0
FARO_PER_CERA = 25.0
FARO_RADIUS = 140
FOGATA_HEAL = 0.06
FARO_HEAL = 0.015

FOGATA_MAX = 900.0
FOGATA_START = 300.0
FOGATA_PER_MADERA = 60.0
FOGATA_RADIUS = 440

LOW_FUEL = 0.15

ANIM_ENABLED = True

FARO_WICK = (0.51, 0.70)

FARO_GLOW_SIZE = 0.55
FARO_GLOW_COLOR = (150, 100, 30)
FARO_CORE_COLOR = (170, 105, 18)
FARO_EMBERS = 2

FOGATA_GLOW_SIZE = 1.10
FOGATA_GLOW_COLOR = (200, 110, 30)
FOGATA_EMBERS = 7

FEED_HINT_ENABLED = True
FEED_HINT_LINE2 = "En la hotbar elegí {item} y apretá F o click derecho"

FARO_LIGHT_FLICKER = 0.02
FOGATA_LIGHT_FLICKER = 0.035

HEAL_RATE = {
    "faro": FARO_HEAL,
    "fogata": FOGATA_HEAL,
}

FUEL_ITEM = {
    "faro": "cera",
    "fogata": "madera",
}

FUEL_PER_ITEM = {
    "faro": FARO_PER_CERA,
    "fogata": FOGATA_PER_MADERA,
}

PLACE_ITEMS = ("cofre", "faro", "fogata")

WORLD_SIZE = {
    "bolsa": (16, 16),
    "cofre": (22, 18),
    "faro": (14, 16),
    "fogata": (20, 18),
}

ICON_IDS = ("bolsa", "cofre", "faro", "fogata")


UI_DIR = HUD_DIR.parent / "ui"

PANEL_FILES = {
    "bolsa": "panel_bolsa.png",
    "cofre": "panel_cofre.png",
}
SLOT_FILE = "slot_contenedor.png"
SLOT_HOVER_FILE = "slot_contenedor_hover.png"

SLOT_PX = 56
SLOT_GAP = 8
PANEL_COLS = 4
PANEL_MARGIN_X = 24
PANEL_TOP = 56
PANEL_BOTTOM = 32


def _sprite_path(kind, suffix=""):
    return HUD_DIR / f"icon_{kind}{suffix}.png"


_GLOW_CACHE = {}


def _glow_surface(radius, level, color):

    radius = max(4, int(radius) // 4 * 4)
    lv = max(1, min(8, int(round(level * 8))))

    key = (radius, lv, color)

    surf = _GLOW_CACHE.get(key)

    if surf is None:

        if len(_GLOW_CACHE) > 120:
            _GLOW_CACHE.clear()

        surf = pygame.Surface((radius * 2, radius * 2))
        surf.fill((0, 0, 0))

        steps = max(6, min(24, radius // 3))

        for i in range(steps, 0, -1):

            t = i / steps
            k = ((1.0 - t) ** 1.4) * lv / 8.0

            pygame.draw.circle(
                surf, tuple(int(c * k) for c in color),
                (radius, radius), max(1, int(radius * t))
            )

        _GLOW_CACHE[key] = surf

    return surf


def _add_glow(screen, cx, cy, radius, level, color):

    if level <= 0.05 or radius < 4:
        return

    surf = _glow_surface(radius, level, color)

    screen.blit(
        surf,
        (int(cx) - surf.get_width() // 2, int(cy) - surf.get_height() // 2),
        special_flags=pygame.BLEND_RGB_ADD
    )


def _draw_embers(screen, ox, oy, rise, spread, size, clock, phase,
                 count, level):

    if level <= 0.05:
        return

    for i in range(count):

        seed = i * 1.618 + phase

        life = (
            clock * (0.35 + 0.07 * (i % 4)) + i / count + phase * 0.1
        ) % 1.0

        x = ox + math.sin(seed * 5.3 + life * 5.0) * spread * (0.3 + life)
        y = oy - life * rise

        fade = ((1.0 - life) ** 0.8) * level

        if fade <= 0.05:
            continue

        color = (
            int(255 * fade),
            int((200 - 130 * life) * fade),
            int((90 - 80 * life) * fade),
        )

        sz = max(1, int(size * (1.0 - life * 0.5)))

        screen.fill(
            color, pygame.Rect(int(x), int(y), sz, sz),
            special_flags=pygame.BLEND_RGB_ADD
        )


def _draw_bolsa(W, H):

    s = pygame.Surface((W, H), pygame.SRCALPHA)

    body = pygame.Rect(int(W * .12), int(H * .30), int(W * .76), int(H * .65))

    neck = [
        (W * .34, H * .34), (W * .66, H * .34),
        (W * .58, H * .10), (W * .42, H * .10),
    ]

    pygame.draw.polygon(s, (140, 95, 50), neck)
    pygame.draw.ellipse(s, (140, 95, 50), body)
    shine = body.inflate(-int(body.w * .5), -int(body.h * .55))
    shine.move_ip(-int(body.w * .08), -int(body.h * .12))

    pygame.draw.ellipse(s, (176, 126, 70), shine)
    pygame.draw.ellipse(s, (80, 50, 25), body, max(1, W // 24))
    pygame.draw.polygon(s, (80, 50, 25), neck, max(1, W // 32))
    pygame.draw.line(s, (232, 204, 120),
                     (W * .34, H * .34), (W * .66, H * .34),
                     max(2, W // 14))

    return s


def _draw_cofre(W, H):

    s = pygame.Surface((W, H), pygame.SRCALPHA)

    lw = max(1, W // 24)

    body = pygame.Rect(int(W * .05), int(H * .38), int(W * .90), int(H * .57))
    lid = pygame.Rect(int(W * .05), int(H * .10), int(W * .90), int(H * .32))

    pygame.draw.rect(s, (118, 76, 38), body, border_radius=max(2, W // 14))
    pygame.draw.rect(s, (150, 100, 52), lid, border_radius=max(3, W // 8))
    pygame.draw.rect(s, (70, 44, 22), body, lw, border_radius=max(2, W // 14))
    pygame.draw.rect(s, (70, 44, 22), lid, lw, border_radius=max(3, W // 8))

    band = max(2, W // 9)

    pygame.draw.rect(s, (205, 172, 62),
                     (W // 2 - band // 2, int(H * .10), band, int(H * .85)))

    lock = pygame.Rect(0, 0, max(3, W // 6), max(3, W // 6))
    lock.center = (W // 2, int(H * .42))

    pygame.draw.rect(s, (238, 208, 90), lock, border_radius=2)
    pygame.draw.rect(s, (90, 64, 20), lock, 1, border_radius=2)

    return s


def _draw_faro(W, H, lit=True):

    s = pygame.Surface((W, H), pygame.SRCALPHA)

    lw = max(1, W // 20)
    dark = (70, 52, 38)

    pygame.draw.ellipse(s, dark, (int(W * .36), 0, int(W * .28), int(H * .22)), lw)

    pygame.draw.polygon(s, (120, 96, 70), [
        (W * .20, H * .30), (W * .80, H * .30), (W * .66, H * .14),
        (W * .34, H * .14),
    ])
    pygame.draw.rect(s, (120, 96, 70),
                     (int(W * .18), int(H * .86), int(W * .64), int(H * .10)))

    glass = pygame.Rect(int(W * .24), int(H * .30), int(W * .52), int(H * .56))

    pygame.draw.rect(s, (255, 226, 120) if lit else (150, 146, 140), glass)
    pygame.draw.rect(s, dark, glass, lw)

    if lit:
        pygame.draw.polygon(s, (255, 150, 40), [
            (W * .40, H * .80), (W * .50, H * .46), (W * .60, H * .80),
        ])

    return s


def _draw_fogata(W, H, flame=False):

    s = pygame.Surface((W, H), pygame.SRCALPHA)

    t = max(3, int(W * .11))

    for i in range(6):

        a = math.pi * (0.1 + 0.8 * i / 5)
        cx = W * .5 + math.cos(a) * W * .40
        cy = H * .78 + math.sin(a) * H * .16

        r = pygame.Rect(0, 0, max(3, W // 6), max(3, W // 7))
        r.center = (int(cx), int(cy))

        pygame.draw.ellipse(s, (130, 130, 138), r)
        pygame.draw.ellipse(s, (70, 70, 78), r, 1)

    pygame.draw.line(s, (112, 70, 34),
                     (W * .20, H * .90), (W * .80, H * .62), t)
    pygame.draw.line(s, (96, 58, 28),
                     (W * .20, H * .62), (W * .80, H * .90), t)

    if flame:

        pygame.draw.polygon(s, (255, 150, 40), [
            (W * .30, H * .70), (W * .50, H * .06), (W * .70, H * .70),
        ])
        pygame.draw.polygon(s, (255, 226, 110), [
            (W * .40, H * .70), (W * .50, H * .32), (W * .60, H * .70),
        ])

    return s


_DRAWERS = {
    "bolsa": _draw_bolsa,
    "cofre": _draw_cofre,
    "faro": lambda W, H: _draw_faro(W, H, lit=True),
    "fogata": lambda W, H: _draw_fogata(W, H, flame=True),
}


def install_placeholder_icons():

    for item_id in ICON_IDS:

        if _sprite_path(item_id).exists():
            continue

        if _items._icon_cache.get(item_id) is None:
            _items._icon_cache[item_id] = _DRAWERS[item_id](64, 64)


class Container:

    def __init__(self, slots, capacity=None):

        self.slots = [None] * slots
        self.capacity = capacity

    def total(self):

        return sum(s[1] for s in self.slots if s)

    def add(self, item_id, stack_limit):

        for s in self.slots:

            if s and s[0] == item_id and s[1] < stack_limit:

                s[1] += 1

                return True

        for i, s in enumerate(self.slots):

            if s is None:

                self.slots[i] = [item_id, 1]

                return True

        return False

    def take(self, index, amount=None):

        s = self.slots[index]

        if not s:
            return 0

        n = s[1] if amount is None else min(amount, s[1])

        s[1] -= n

        if s[1] <= 0:
            self.slots[index] = None

        return n

    def save(self):

        return [list(s) if s else None for s in self.slots]

    def load(self, data):

        for i in range(len(self.slots)):

            entry = data[i] if i < len(data) else None

            if (
                isinstance(entry, (list, tuple))
                and len(entry) == 2
                and entry[1] > 0
            ):
                self.slots[i] = [str(entry[0]), int(entry[1])]


class Placeable:

    kind = "?"
    draggable = False
    container_slots = 0
    container_capacity = None
    fuel_max = 0.0
    light_radius_px = 0
    light_flicker = 0.0

    def __init__(self, x, y, fuel=None):

        w, h = WORLD_SIZE[self.kind]

        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(x), int(y))

        self.container = (
            Container(self.container_slots, self.container_capacity)
            if self.container_slots else None
        )

        self.fuel = float(fuel) if fuel is not None else 0.0

        self.near = False
        self._phase = (x * 0.37 + y * 0.11) % 6.28

        self._scaled = {}

        self._real = _sprite_path(self.kind).exists()

        self.fly = None
        self._lift = 0.0

        self._world_h = h

        self.grab_dx = 0.0
        self.grab_dy = 0.0

    def start_fly(self, src, dst, delay=0.0, height=14.0, duration=0.45):

        self.fly = {
            "src": src, "dst": dst, "delay": delay,
            "t": 0.0, "dur": duration, "h": height,
        }

        self.rect.center = (round(src[0]), round(src[1]))

    update_fly = _items.WorldItem.update_fly

    @property
    def uses_fuel(self):
        return self.fuel_max > 0

    @property
    def lit(self):
        return self.uses_fuel and self.fuel > 0

    @property
    def fuel_fraction(self):

        if not self.uses_fuel:
            return 0.0

        return max(0.0, min(1.0, self.fuel / self.fuel_max))

    def add_fuel(self, amount):

        self.fuel = min(self.fuel_max, self.fuel + amount)

    def burn(self, dt):

        if self.lit:
            self.fuel = max(0.0, self.fuel - dt)

    def _flicker(self, clock):

        if self.fuel_fraction < LOW_FUEL:
            return 0.45 + 0.55 * abs(math.sin(clock * 14 + self._phase))

        return 1.0

    def _size_k(self):

        return 0.55 + 0.45 * min(1.0, self.fuel_fraction * 3)


    def light_radius(self, clock):

        if not self.lit:
            return 0

        frac = self.fuel_fraction

        radius = self.light_radius_px * (0.55 + 0.45 * min(1.0, frac * 3))

        if ANIM_ENABLED and self.light_flicker:

            ph = self._phase

            radius *= 1.0 + self.light_flicker * (
                0.6 * math.sin(clock * 9 + ph)
                + 0.4 * math.sin(clock * 23 + ph * 2.3)
            )

        if frac < LOW_FUEL:

            radius *= 0.6 + 0.4 * abs(math.sin(clock * 14 + self._phase))

        return radius

    def heal_range(self, zoom):

        if not self.lit:
            return 0.0

        return (
            self.light_radius_px
            * (0.55 + 0.45 * min(1.0, self.fuel_fraction * 3))
            / max(1, zoom)
        )


    def _base_sprite(self):

        path = _sprite_path(self.kind)

        if self.uses_fuel and not self.lit:

            off = _sprite_path(self.kind, "_apagado")

            if off.exists():
                path = off

        if path.exists():
            return pygame.image.load(str(path)).convert_alpha()

        w, h = WORLD_SIZE[self.kind]

        if self.kind == "fogata":
            return _draw_fogata(w * 8, h * 8, flame=False)

        return _DRAWERS[self.kind](w * 8, h * 8)

    def _sprite(self, zoom):

        key = (round(zoom, 3), self.uses_fuel and not self.lit)

        sprite = self._scaled.get(key)

        if sprite is None:

            base = self._base_sprite()

            w = max(2, int(self.rect.w * zoom))
            h = max(2, int(w * base.get_height() / base.get_width()))

            sprite = pygame.transform.smoothscale(base, (w, h))

            self._scaled[key] = sprite

            # alto real del dibujo en el mundo (para agarrarlo mejor)
            self._world_h = max(self.rect.h, h / max(zoom, 0.01))

        return sprite

    def hit(self, wx, wy):

        # el dibujo es mas alto que la caja: se puede agarrar por
        # cualquier parte visible, con un poco de margen
        area = self.rect.inflate(GRAB_PAD, GRAB_PAD)

        extra = int(self._world_h - self.rect.h)

        if extra > 0:
            area.y -= extra
            area.h += extra

        return area.collidepoint(wx, wy)

    def draw(self, screen, camera, clock):

        f = self.fly

        if f is not None and f["delay"] > 0:
            return

        sprite = self._sprite(camera.zoom)

        dest = camera.apply(self.rect)

        lift = int(self._lift * camera.zoom)

        r = sprite.get_rect(
            midbottom=(dest.centerx, dest.bottom - lift)
        )

        screen.blit(sprite, r)

        self.draw_extras(screen, r, clock)

        if self.near and self.uses_fuel:
            self._draw_fuel_bar(screen, r)

    def draw_extras(self, screen, r, clock):
        pass

    def _draw_fuel_bar(self, screen, r):

        w = max(16, r.w)
        bar = pygame.Rect(0, 0, w, 5)
        bar.midbottom = (r.centerx, r.top - 3)

        pygame.draw.rect(screen, (20, 20, 24), bar.inflate(2, 2))

        frac = self.fuel_fraction

        color = (255, 190, 70) if frac > LOW_FUEL else (230, 70, 50)

        fill = bar.copy()
        fill.w = int(bar.w * frac)

        pygame.draw.rect(screen, color, fill)


    def save(self):

        x, y = self.rect.center

        if self.fly is not None:
            x, y = self.fly["dst"]

        data = {
            "t": self.kind,
            "x": int(x),
            "y": int(y),
        }

        if self.uses_fuel:
            data["fuel"] = round(self.fuel, 2)

        if self.container is not None:
            data["slots"] = self.container.save()

        return data


class Bag(Placeable):

    kind = "bolsa"
    draggable = True
    container_slots = BAG_SLOTS


class Chest(Placeable):

    # una vez puesto, el cofre queda fijo para siempre
    kind = "cofre"
    draggable = False
    container_slots = CHEST_SLOTS


class Lighthouse(Placeable):

    kind = "faro"
    draggable = True
    fuel_max = FARO_MAX
    light_radius_px = FARO_RADIUS
    light_flicker = FARO_LIGHT_FLICKER

    def draw_extras(self, screen, r, clock):

        if not self.lit:
            return

        if not self._real:

            pulse = 0.75 + 0.25 * math.sin(clock * 6 + self._phase)

            glow = pygame.Surface((r.w, r.w), pygame.SRCALPHA)

            pygame.draw.circle(
                glow, (255, 230, 120, int(110 * pulse)),
                (r.w // 2, r.w // 2), r.w // 2
            )

            screen.blit(
                glow,
                glow.get_rect(center=(r.centerx, r.top + int(r.h * .26)))
            )

            return

        if not ANIM_ENABLED:
            return

        ph = self._phase
        k = self._flicker(clock)

        breath = (
            0.80
            + 0.12 * math.sin(clock * 2.1 + ph)
            + 0.08 * math.sin(clock * 7.3 + ph * 1.7)
        )

        cx = r.left + int(r.w * FARO_WICK[0]) + int(
            math.sin(clock * 1.3 + ph) * r.w * 0.015
        )
        cy = r.top + int(r.h * FARO_WICK[1])

        _add_glow(
            screen, cx, cy, r.w * FARO_GLOW_SIZE,
            breath * k, FARO_GLOW_COLOR
        )

        _add_glow(
            screen, cx, cy, r.w * 0.20,
            (0.70 + 0.30 * breath) * k, FARO_CORE_COLOR
        )

        _draw_embers(
            screen, r.centerx, r.top + r.h * 0.06, r.h * 0.30, r.w * 0.10,
            max(1, r.w // 30), clock, ph, FARO_EMBERS, 0.6 * k
        )


class Campfire(Placeable):

    kind = "fogata"
    fuel_max = FOGATA_MAX
    light_radius_px = FOGATA_RADIUS
    light_flicker = FOGATA_LIGHT_FLICKER

    def draw_extras(self, screen, r, clock):

        if not self.lit:
            return

        if not self._real:

            s = 0.85 + 0.15 * math.sin(clock * 11 + self._phase)
            s2 = 0.85 + 0.15 * math.sin(clock * 17 + self._phase * 2)

            base_y = r.top + int(r.h * .72)
            fh = int(r.h * .85 * s)
            fw = int(r.w * .46)

            outer = [
                (r.centerx - fw // 2, base_y),
                (r.centerx + int(2 * math.sin(clock * 9)), base_y - fh),
                (r.centerx + fw // 2, base_y),
            ]

            pygame.draw.polygon(screen, (255, 150, 40), outer)

            ih = int(fh * .6 * s2)
            iw = int(fw * .5)

            pygame.draw.polygon(screen, (255, 226, 110), [
                (r.centerx - iw // 2, base_y),
                (r.centerx, base_y - ih),
                (r.centerx + iw // 2, base_y),
            ])

            return

        if not ANIM_ENABLED:
            return

        ph = self._phase
        k = self._flicker(clock)
        size_k = self._size_k()

        f1 = math.sin(clock * 11 + ph)
        f2 = math.sin(clock * 17 + ph * 2)
        f3 = math.sin(clock * 5.3 + ph * 0.7)

        flare = 0.85 + 0.09 * f1 + 0.06 * f2

        cx = r.centerx

        _add_glow(
            screen, cx, r.top + int(r.h * 0.62),
            r.w * FOGATA_GLOW_SIZE * size_k * (1.0 + 0.05 * f1),
            flare * k, FOGATA_GLOW_COLOR
        )

        layer = pygame.Surface((r.w, r.h))
        layer.fill((0, 0, 0))

        base = r.h * 0.70
        fw = r.w * 0.30 * size_k
        fh = r.h * 0.60 * size_k * (0.90 + 0.12 * f1 + 0.08 * f2)
        sway = r.w * 0.035 * f3

        def tongue(x0, width, height, tilt, color):

            pygame.draw.polygon(layer, tuple(int(c * k) for c in color), [
                (x0 - width / 2, base),
                (x0 - width * 0.20 + tilt * 0.5, base - height * 0.55),
                (x0 + tilt, base - height),
                (x0 + width * 0.20 + tilt * 0.5, base - height * 0.55),
                (x0 + width / 2, base),
            ])

        mid = r.w / 2

        for side, off in ((-1, 1.7), (1, 4.1)):

            wob = math.sin(clock * 13 + off + ph)

            tongue(
                mid + side * fw * 0.38,
                fw * 0.55,
                fh * (0.50 + 0.14 * wob),
                side * r.w * 0.02 + sway * 0.8,
                (70, 32, 5)
            )

        tongue(mid, fw, fh, sway, (95, 45, 8))
        tongue(mid, fw * 0.55, fh * 0.65, sway * 0.7, (80, 72, 24))

        screen.blit(layer, r.topleft, special_flags=pygame.BLEND_RGB_ADD)

        _draw_embers(
            screen, cx, r.top + r.h * 0.30, r.h * 0.60, r.w * 0.20,
            max(1, r.w // 26), clock, ph,
            max(2, int(FOGATA_EMBERS * size_k)), k
        )


KINDS = {
    "bolsa": Bag,
    "cofre": Chest,
    "faro": Lighthouse,
    "fogata": Campfire,
}


class PlaceableManager:

    def __init__(self, saved=None):

        install_placeholder_icons()

        self.objects = []

        self.clock = 0.0

        self.dragging = None

        self.open_obj = None

        self._fonts = {}
        self._icons = {}
        self._ui = {}
        self._ghosts = {}

        for entry in saved or []:

            cls = KINDS.get(entry.get("t")) if isinstance(entry, dict) else None

            if cls is None:
                continue

            obj = cls(entry.get("x", 0), entry.get("y", 0), entry.get("fuel"))

            if obj.container is not None:
                obj.container.load(entry.get("slots", []))

            self.objects.append(obj)


    def _font(self, size):

        font = self._fonts.get(size)

        if font is None:
            font = pygame.font.Font(None, size)
            self._fonts[size] = font

        return font

    def _icon(self, item_id, size):

        key = (item_id, size)

        if key not in self._icons:

            icon = load_icon(item_id)

            if icon is not None:
                icon = pygame.transform.smoothscale(icon, (size, size))

            self._icons[key] = icon

        return self._icons[key]

    @staticmethod
    def _mouse_world(game):

        mx, my = pygame.mouse.get_pos()

        return (
            (game.camera.x + mx) / game.camera.zoom,
            (game.camera.y + my) / game.camera.zoom,
        )

    @staticmethod
    def _dist(game, obj):

        return math.hypot(
            obj.rect.centerx - game.player.rect.centerx,
            obj.rect.centery - game.player.rect.centery,
        )

    def _under_mouse(self, game):

        wx, wy = self._mouse_world(game)

        best = None

        for obj in self.objects:

            if obj.fly is not None:
                continue

            if obj.hit(wx, wy) and self._dist(game, obj) <= REACH:

                if best is None or obj.rect.centery > best.rect.centery:
                    best = obj

        return best

    def _nearest_feedable(self, game, item_id):

        best = None
        best_d = None

        for obj in self.objects:

            if (
                obj.uses_fuel
                and FUEL_ITEM.get(obj.kind) == item_id
                and obj.fuel < obj.fuel_max - 0.01
            ):
                d = self._dist(game, obj)

                if d <= REACH and (best is None or d < best_d):
                    best, best_d = obj, d

        return best


    def spawn(self, kind, x, y, src=None, delay=0.0):

        # objetos que salen de la tienda (bolsa, candil): no pasan por
        # el inventario, aparecen en el piso y se arrastran
        obj = KINDS[kind](x, y)

        if obj.uses_fuel:
            obj.fuel = FARO_START if kind == "faro" else FOGATA_START

        if src is not None:
            obj.start_fly(src, (x, y), delay=delay)

        self.objects.append(obj)

        return obj

    def spawn_bag(self, x, y, src=None, delay=0.0, collision_map=None):

        return self.spawn("bolsa", x, y, src=src, delay=delay)

    def _spot_free(self, game, rect):

        pts = [
            rect.center, rect.topleft, rect.topright,
            (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1),
        ]

        for p in pts:

            if not game.collision_map.point_is_walkable(*p):
                return False

        for obj in self.objects:

            if obj.rect.colliderect(rect):
                return False

        return True


    def _held(self, game):

        slot = game.selected_slot

        if not isinstance(slot, int) or slot >= game.hud.SLOTS:
            return None

        item_id = game.hud.items[slot]

        if item_id in PLACE_ITEMS:
            return slot, item_id

        return None

    @staticmethod
    def _over_hud(game, pos):

        if game.hud.slot_at(pos) is not None:
            return True

        for name in ("equipped_rect", "menu_button_rect", "attack_panel_rect"):

            r = getattr(game.hud, name, None)

            if r is not None and r.collidepoint(pos):
                return True

        return False

    def _can_place(self, game, kind, wx, wy):

        w, h = WORLD_SIZE[kind]

        r = pygame.Rect(0, 0, w, h)
        r.center = (int(wx), int(wy))

        px, py = game.player.rect.center

        if math.hypot(wx - px, wy - py) > PLACE_RANGE:
            return False, r

        return self._spot_free(game, r), r

    def _place(self, game, slot, item_id, wx, wy):

        ok, r = self._can_place(game, item_id, wx, wy)

        if not ok:

            game.show_message("No se puede poner ahí")

            return False

        obj = KINDS[item_id](r.centerx, r.centery)

        if obj.uses_fuel:
            obj.fuel = FARO_START if item_id == "faro" else FOGATA_START

        self.objects.append(obj)

        game._take_one(slot)

        audio.play("pickup")

        game.show_message(
            f"Pusiste {game._item_name(item_id)}"
            + (" (queda fijo)" if not obj.draggable else "")
        )

        return True


    def try_use(self, game, slot):

        item_id = game.hud.items[slot]

        if item_id is None:
            return False

        if item_id in PLACE_ITEMS:

            mouse = pygame.mouse.get_pos()

            if self._over_hud(game, mouse):

                game.show_message(
                    "Elegilo y hacé click en el mapa donde lo querés poner"
                )

                return True

            wx, wy = self._mouse_world(game)

            self._place(game, slot, item_id, wx, wy)

            return True

        return False

    def feed_target(self, game, item_id):

        return self._nearest_feedable(game, item_id)

    def feed(self, game, obj, item_id):

        obj.add_fuel(FUEL_PER_ITEM[obj.kind])

        audio.play("pickup")

        return obj


    def handle_event(self, game, event):

        if game.state != "playing":
            return False

        if (
            self.open_obj is not None
            and event.type == pygame.KEYDOWN
            and event.key == pygame.K_ESCAPE
        ):
            self.open_obj = None

            return True

        if event.type != pygame.MOUSEBUTTONDOWN:
            return False

        if self.open_obj is not None:

            consumed = self._panel_click(game, event)

            if consumed:
                return True

        if event.button == 1:

            if self._over_hud(game, event.pos):
                return False

            obj = self._under_mouse(game)

            if obj is not None and obj.draggable:

                wx, wy = self._mouse_world(game)

                # se agarra desde donde hiciste click: no pega un salto
                obj.grab_dx = obj.rect.centerx - wx
                obj.grab_dy = obj.rect.centery - wy

                self._unstick(game, obj)

                self.dragging = obj

                return True

            held = self._held(game)

            if held is not None and self.open_obj is None:

                wx, wy = self._mouse_world(game)

                self._place(game, held[0], held[1], wx, wy)

                return True

            return False

        if event.button == 3:

            obj = self._under_mouse(game)

            if obj is None:
                return False

            if obj.container is not None:

                self.open_obj = obj

                return True

            if obj.uses_fuel:

                game.show_message(
                    f"{game._item_name(obj.kind)}: "
                    f"{int(obj.fuel)} s de luz"
                )

                return True

        return False

    def _draw_feed_hints(self, game, screen):

        if not FEED_HINT_ENABLED:
            return

        if (
            game.state != "playing"
            or self.open_obj is not None
            or getattr(game, "shop", None) is not None
            or getattr(game, "pause_view", None) is not None
            or getattr(game, "tutorial", None) is not None
        ):
            return

        sw = screen.get_width()

        held = None

        if pygame.mouse.get_pressed()[0]:

            held = self.dragging or self._under_mouse(game)

            if held is not None and not held.uses_fuel:
                held = None

        for obj in self.objects:

            if not obj.uses_fuel or obj.fly is not None:
                continue

            if obj is not held:
                continue

            is_held = True
            fade = 1.0

            item = game._item_name(FUEL_ITEM[obj.kind])
            name = game._item_name(obj.kind)

            if obj.fuel >= obj.fuel_max - 0.01:
                lines = [f"{name}: está llena"]
            else:
                lines = [
                    f"Alimentala con {item.upper()}",
                    FEED_HINT_LINE2.format(item=item.upper()),
                ]

            if is_held:
                lines.insert(
                    0, f"{name}: {int(obj.fuel)} / {int(obj.fuel_max)} s de luz"
                )

            sprite = obj._sprite(game.camera.zoom)
            dest = game.camera.apply(obj.rect)
            lift = int(obj._lift * game.camera.zoom)

            r = sprite.get_rect(
                midbottom=(dest.centerx, dest.bottom - lift)
            )

            for size in (22, 20, 18, 16, 14):

                font = self._font(size)

                if max(font.size(ln)[0] for ln in lines) <= sw - 40:
                    break

            line_h = font.get_linesize()

            w = max(font.size(ln)[0] for ln in lines) + 16
            h = line_h * len(lines) + 8

            box = pygame.Rect(0, 0, w, h)
            box.midbottom = (r.centerx, r.top - 12)
            box.clamp_ip(screen.get_rect())

            card = pygame.Surface(box.size, pygame.SRCALPHA)

            pygame.draw.rect(
                card, (16, 14, 12, 190), card.get_rect(), border_radius=8
            )

            y = 4

            for n, ln in enumerate(lines):

                color = (255, 224, 150) if n == 0 else (225, 225, 230)

                img = font.render(ln, True, color)

                card.blit(img, img.get_rect(midtop=(box.w // 2, y)))

                y += line_h

            card.set_alpha(int(255 * fade))

            screen.blit(card, box)

    def draw_ghost(self, game, screen):

        self._draw_feed_hints(game, screen)

        if game.state != "playing" or self.open_obj is not None:
            return

        if (
            getattr(game, "shop", None) is not None
            or getattr(game, "pause_view", None) is not None
            or getattr(game, "tutorial", None) is not None
        ):
            return

        held = self._held(game)

        if held is None:
            return

        mouse = pygame.mouse.get_pos()

        if self._over_hud(game, mouse):
            return

        kind = held[1]

        wx, wy = self._mouse_world(game)

        ok, r = self._can_place(game, kind, wx, wy)

        ghost = self._ghosts.get(kind)

        if ghost is None:

            ghost = KINDS[kind](0, 0)

            if ghost.uses_fuel:
                ghost.fuel = ghost.fuel_max

            self._ghosts[kind] = ghost

        ghost.rect.center = r.center

        sprite = ghost._sprite(game.camera.zoom).copy()

        sprite.set_alpha(150)

        dest = game.camera.apply(ghost.rect)

        screen.blit(sprite, sprite.get_rect(midbottom=dest.midbottom))

        color = (90, 230, 120) if ok else (240, 80, 70)

        pygame.draw.rect(screen, color, dest, 2)


    def _panel_size(self, obj):

        n = len(obj.container.slots)

        rows = math.ceil(n / PANEL_COLS)

        w = (
            PANEL_MARGIN_X * 2
            + PANEL_COLS * SLOT_PX
            + (PANEL_COLS - 1) * SLOT_GAP
        )

        h = (
            PANEL_TOP
            + rows * SLOT_PX
            + (rows - 1) * SLOT_GAP
            + PANEL_BOTTOM
        )

        return w, h

    def _panel_layout(self, game):

        obj = self.open_obj

        w, h = self._panel_size(obj)

        sw, sh = game.screen.get_size()

        panel = pygame.Rect(0, 0, w, h)
        panel.center = (sw // 2, int(sh * 0.40))

        slots = []

        for i in range(len(obj.container.slots)):

            c, r = i % PANEL_COLS, i // PANEL_COLS

            slots.append(
                pygame.Rect(
                    panel.x + PANEL_MARGIN_X + c * (SLOT_PX + SLOT_GAP),
                    panel.y + PANEL_TOP + r * (SLOT_PX + SLOT_GAP),
                    SLOT_PX, SLOT_PX
                )
            )

        return panel, slots

    def _ui_image(self, name, size=None):

        key = (name, size)

        if key not in self._ui:

            path = UI_DIR / name

            img = None

            if path.exists():

                img = pygame.image.load(str(path)).convert_alpha()

                if size is not None and img.get_size() != tuple(size):
                    img = pygame.transform.smoothscale(img, size)

            self._ui[key] = img

        return self._ui[key]

    def _panel_click(self, game, event):

        panel, slots = self._panel_layout(game)

        obj = self.open_obj

        one = event.button == 3

        for i, r in enumerate(slots):

            if r.collidepoint(event.pos):

                self._to_inventory(game, obj, i, one)

                return True

        hotbar = game.hud.slot_at(event.pos)

        if hotbar is not None:

            self._to_container(game, obj, hotbar, one)

            return True

        if panel.collidepoint(event.pos):
            return True

        return False

    def _to_inventory(self, game, obj, index, one):

        s = obj.container.slots[index]

        if not s:
            return

        item_id = s[0]

        moved = 0

        want = 1 if one else s[1]

        for _ in range(want):

            slot = game._free_slot_for(item_id)

            if slot is None:

                game.show_message("Inventario lleno")

                break

            if game.hud.items[slot] is None:

                game.hud.items[slot] = item_id
                game.hud.counts[slot] = 1

            else:

                game.hud.counts[slot] += 1

            obj.container.take(index, 1)

            moved += 1

        if moved:
            audio.play("pickup")

    def _to_container(self, game, obj, slot, one):

        item_id = game.hud.items[slot]

        if item_id is None:
            return

        want = 1 if one else game.hud.counts[slot]

        limit = CONTAINER_STACK

        moved = 0

        for _ in range(want):

            if not obj.container.add(item_id, limit):

                game.show_message(
                    "La bolsa está llena"
                    if obj.kind == "bolsa" else "El cofre está lleno"
                )

                break

            game._take_one(slot)

            moved += 1

        if moved:
            audio.play("pickup")

    def _draw_hint(self, screen, panel, text, color=(170, 176, 192)):

        parts = [p.strip() for p in text.split("\u00b7")]

        max_w = panel.w - 16
        avail = PANEL_BOTTOM - 4

        for size in (20, 18, 16, 14, 12):

            font = self._font(size)

            lines = []
            cur = ""

            for part in parts:

                test = f"{cur}  \u00b7  {part}" if cur else part

                if cur and font.size(test)[0] > max_w:
                    lines.append(cur)
                    cur = part
                else:
                    cur = test

            if cur:
                lines.append(cur)

            line_h = font.get_linesize()

            if (
                all(font.size(ln)[0] <= max_w for ln in lines)
                and line_h * len(lines) <= avail
            ):
                break

        y = panel.bottom - 6

        for ln in reversed(lines):

            img = font.render(ln, True, color)

            screen.blit(img, img.get_rect(midbottom=(panel.centerx, y)))

            y -= line_h

    def draw_panel(self, game, screen):

        obj = self.open_obj

        if obj is None:
            return

        panel, slots = self._panel_layout(game)

        mouse = pygame.mouse.get_pos()

        bg = self._ui_image(PANEL_FILES[obj.kind], panel.size)

        if bg is not None:

            screen.blit(bg, panel)

        else:

            shade = pygame.Surface(panel.size, pygame.SRCALPHA)

            pygame.draw.rect(
                shade, (22, 24, 30, 240), shade.get_rect(), border_radius=12
            )

            screen.blit(shade, panel)

            pygame.draw.rect(
                screen, (214, 168, 84), panel, 2, border_radius=12
            )

        title = "Bolsa" if obj.kind == "bolsa" else "Cofre"

        text = self._font(30).render(title, True, (244, 236, 214))

        screen.blit(text, (panel.x + PANEL_MARGIN_X, panel.y + 16))

        slot_img = self._ui_image(SLOT_FILE, (SLOT_PX, SLOT_PX))
        slot_hover = self._ui_image(SLOT_HOVER_FILE, (SLOT_PX, SLOT_PX))

        hover_name = None

        for i, r in enumerate(slots):

            hover = r.collidepoint(mouse)

            if slot_img is not None:

                screen.blit(
                    slot_hover if (hover and slot_hover is not None)
                    else slot_img,
                    r
                )

            else:

                pygame.draw.rect(
                    screen, (62, 66, 80) if hover else (44, 47, 58), r,
                    border_radius=6
                )
                pygame.draw.rect(
                    screen, (120, 126, 146), r, 1, border_radius=6
                )

            s = obj.container.slots[i]

            if not s:
                continue

            icon = self._icon(s[0], 40)

            if icon is not None:
                screen.blit(icon, icon.get_rect(center=r.center))

            if s[1] > 1:

                n = self._font(22).render(str(s[1]), True, (255, 255, 255))

                screen.blit(
                    n, n.get_rect(bottomright=(r.right - 4, r.bottom - 2))
                )

            if hover:
                hover_name = game._item_name(s[0])

        self._draw_hint(
            screen, panel,
            "Click: pasar todo  \u00b7  Click derecho: de a 1  \u00b7  Esc: cerrar"
        )

        if hover_name:

            tip = self._font(24).render(hover_name, True, (255, 232, 170))

            screen.blit(
                tip, tip.get_rect(midbottom=(panel.centerx, panel.y - 6))
            )


    def update(self, game, dt):

        self.clock += dt

        for obj in self.objects:

            if obj.fly is not None:

                obj.update_fly(dt)

                continue

            obj.burn(dt)

            obj.near = self._dist(game, obj) <= REACH + 24

        if game.has_match and game.vida < 1.0:

            heal = 0.0

            for obj in self.objects:

                rate = HEAL_RATE.get(obj.kind, 0.0)

                if (
                    rate > heal
                    and obj.fly is None
                    and self._dist(game, obj) <= obj.heal_range(game.camera.zoom)
                ):
                    heal = rate

            if heal > 0.0:
                game.vida = min(1.0, game.vida + heal * dt)

        if self.open_obj is not None:

            if (
                self.open_obj not in self.objects
                or self._dist(game, self.open_obj) > REACH + 30
            ):
                self.open_obj = None

        for obj in self.objects:

            if obj.fly is not None:
                continue

            # se levanta suave al agarrarlo y baja suave al soltarlo
            want = DRAG_LIFT if obj is self.dragging else 0.0

            obj._lift += (want - obj._lift) * min(1.0, 14.0 * dt)

            if abs(obj._lift - want) < 0.05:
                obj._lift = want

        if self.dragging is not None:

            obj = self.dragging

            if (
                not pygame.mouse.get_pressed()[0]
                or obj not in self.objects
                or self._dist(game, obj) > DRAG_RELEASE
            ):

                self._drop(game, obj)

                self.dragging = None

                return

            self._drag(game, obj, dt)

    # ---------- movimiento y colisiones de lo arrastrable ----------

    def _footprint_ok(self, game, rect):

        # 8 puntos del borde: no se cuela por paredes finas ni esquinas
        cmap = game.collision_map

        l, t = rect.left, rect.top
        r, b = rect.right - 1, rect.bottom - 1
        cx, cy = rect.centerx, rect.centery

        for p in (
            (cx, cy), (l, t), (cx, t), (r, t),
            (l, cy), (r, cy), (l, b), (cx, b), (r, b),
        ):
            if not cmap.point_is_walkable(*p):
                return False

        return True

    def _blocked_by_objects(self, obj, rect):

        # caja un poco mas chica: roza a los vecinos sin trabarse
        hit = rect.inflate(-2, -2)

        for other in self.objects:

            if other is obj or other.fly is not None:
                continue

            if other.rect.colliderect(hit):
                return other

        return None

    def _spot_ok(self, game, obj, x, y):

        r = pygame.Rect(0, 0, *obj.rect.size)
        r.center = (int(round(x)), int(round(y)))

        return (
            self._footprint_ok(game, r)
            and self._blocked_by_objects(obj, r) is None
        )

    def _unstick(self, game, obj):

        # si quedo trabado (pared u otro objeto) lo saca al lugar libre
        # mas cercano, asi nunca queda "pegado"
        cx, cy = obj.rect.center

        if self._spot_ok(game, obj, cx, cy):
            return

        for radius in range(2, 26, 2):

            for i in range(16):

                a = math.tau * i / 16

                x = cx + math.cos(a) * radius
                y = cy + math.sin(a) * radius

                if self._spot_ok(game, obj, x, y):

                    obj.rect.center = (int(round(x)), int(round(y)))

                    return

    def _drop(self, game, obj):

        self._unstick(game, obj)

    def _drag(self, game, obj, dt):

        mx, my = self._mouse_world(game)

        mx += obj.grab_dx
        my += obj.grab_dy

        px, py = game.player.rect.center

        dx, dy = mx - px, my - py

        d = math.hypot(dx, dy)

        # el objeto solo se puede llevar hasta DRAG_RANGE del jugador
        if d > DRAG_RANGE:

            mx = px + dx / d * DRAG_RANGE
            my = py + dy / d * DRAG_RANGE

        cx, cy = obj.rect.center

        k = min(1.0, DRAG_SPEED * dt)

        mvx = (mx - cx) * k
        mvy = (my - cy) * k

        dist = math.hypot(mvx, mvy)

        if dist < 0.01:
            return

        # avanza de a pocos pixeles y desliza por los costados:
        # en paredes y esquinas sigue por el eje que si esta libre
        steps = max(1, int(math.ceil(dist / DRAG_STEP)))

        sx, sy = mvx / steps, mvy / steps

        fx, fy = float(cx), float(cy)

        for _ in range(steps):

            if self._spot_ok(game, obj, fx + sx, fy + sy):

                fx += sx
                fy += sy

            elif sx and self._spot_ok(game, obj, fx + sx, fy):

                fx += sx

            elif sy and self._spot_ok(game, obj, fx, fy + sy):

                fy += sy

            else:
                break

        obj.rect.center = (int(round(fx)), int(round(fy)))


    def draw(self, screen, camera):

        for obj in sorted(self.objects, key=lambda o: o.rect.bottom):
            obj.draw(screen, camera, self.clock)

    def light_sources(self):

        out = []

        for obj in self.objects:

            if obj.fly is not None and obj.fly["delay"] > 0:
                continue

            radius = obj.light_radius(self.clock)

            if radius >= 2:

                out.append((
                    obj.rect.centerx,
                    obj.rect.centery - (3 if obj.kind == "faro" else 0),
                    radius
                ))

        return out


    def save_data(self):

        return [obj.save() for obj in self.objects]