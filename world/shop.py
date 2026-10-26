import json
import math
import random
from pathlib import Path

import pygame

from world.items import WorldItem, LightItem, HUD_DIR
from world.lights import LIGHTS


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

TIENDA_DIR = MOUTH_IMAGE.parent

BODY_IMAGE = TIENDA_DIR / "vendedor_cuerpo.png"
BG_IMAGE = TIENDA_DIR / "vendedor_fondo.png"

# Oleada que hay que alcanzar (en cualquiera de las 2 salas de combate)
# para poder comprar cada objeto en la tienda. Para cambiarlo, editá acá.
SHOP_UNLOCK_WAVES = {
    "hongo_azul": 5,
    "antorcha": 6,
    "repelente": 8,
    "iman": 8,
    "esfera": 8,
}

DEFAULT_CATALOG = [
    {
        "nombre": "Luces",
        "items": [
            {"id": "fosforo", "precio": 40},
            {"id": "vela", "precio": 90},
            {"id": "antorcha", "precio": 180},
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

    MOUTH = (951, 87)

    HEAD_TOP = 76

    TALK_RECT = pygame.Rect(902, 100, 92, 40).inflate(44, 60)

    ZONE = pygame.Rect(840, 30, 215, 140)

    ZONE_FEATHER = 22

    def zone_inset(self, player):

        x, y = player.rect.center
        z = self.ZONE

        if not z.collidepoint(x, y):
            return 0.0

        return float(min(x - z.left, z.right - x, y - z.top, z.bottom - y))

    LAND_RECT = pygame.Rect(878, 146, 140, 30)

    FIRST_DELAY = 0.25
    ITEM_DELAY = 0.14
    MAX_SPIT_TIME = 4.0
    FLY_TIME = 0.6
    FLY_HEIGHT = 26

    # --- animacion del vendedor -------------------------------------------
    # El vendedor esta pintado en el mapa. Para animarlo se recorto (ver
    # tools/make_vendor_assets.py) y se tapa el original con el fondo limpio.

    BOX = (932, 76)          # esquina de arriba a la izquierda del recorte
    ANCHOR = (951, 99)       # abajo al medio: la linea del mostrador
    EYES = ((13, 7), (22, 7))  # (x, y) de cada ojo dentro del recorte, 2 px de ancho
    SKIN = (105, 47, 47)

    WINDUP = 0.16            # cuanto antes de cada disparo infla los cachetes
    RECOIL = 0.36            # cuanto dura el retroceso despues de disparar

    def __init__(self):

        self.f_icon = self._load_f_icon()

        try:
            self.mouth_img = pygame.image.load(
                str(MOUTH_IMAGE)
            ).convert_alpha()
        except (pygame.error, FileNotFoundError):
            self.mouth_img = None

        self._mouth_cache = {}

        self.spit_time = 0.0

        self._clock = 0.0

        # imagenes del vendedor animado (si faltan, queda el dibujo del mapa)
        self.body_open = None
        self.body_blink = None
        self.bg_img = None

        try:
            body = pygame.image.load(str(BODY_IMAGE)).convert_alpha()
            bg = pygame.image.load(str(BG_IMAGE)).convert()

            self.body_open = body

            blink = body.copy()

            for ex, ey in self.EYES:
                blink.fill(self.SKIN + (255,), pygame.Rect(ex, ey, 2, 1))

            self.body_blink = blink
            self.bg_img = bg

        except (pygame.error, FileNotFoundError):
            pass

        self._scaled_cache = {}
        self._bg_cache = {}

        # disparos pendientes: {"t": momento en self._clock, "dir": angulo, "fired": bool}
        self._shots = []

        self.sparks = []
        self.rings = []

        self._happy = 0.0
        self._blink_in = random.uniform(1.5, 3.5)
        self._blink_left = 0.0

        self.kick = 0.0          # >0 infla, <0 retrocede
        self.open_mouth = 0.0    # 0..1

        self._pose = (1.0, 1.0, 0.0)   # sx, sy, dy (en pixeles del mundo)

    @staticmethod
    def _load_f_icon():

        path = HUD_DIR / "F.png"

        try:
            return pygame.image.load(str(path)).convert_alpha()
        except (pygame.error, FileNotFoundError):
            pass

        surf = pygame.Surface((32, 32), pygame.SRCALPHA)

        pygame.draw.rect(
            surf, (30, 30, 38, 235), surf.get_rect(), border_radius=6
        )
        pygame.draw.rect(
            surf, (230, 230, 240), surf.get_rect(), 2, border_radius=6
        )

        font = pygame.font.Font(None, 30)
        letter = font.render("F", True, (255, 255, 255))

        surf.blit(letter, letter.get_rect(center=(16, 16)))

        return surf


    @property
    def busy(self):

        return self.spit_time > 0

    def in_zone(self, player):

        return self.ZONE.collidepoint(player.rect.center)

    def can_talk(self, player):

        return (not self.busy) and player.rect.colliderect(self.TALK_RECT)


    def _landing_point(self, collision_map):

        for _ in range(30):

            x = random.randint(self.LAND_RECT.left, self.LAND_RECT.right)
            y = random.randint(self.LAND_RECT.top, self.LAND_RECT.bottom)

            if collision_map.point_is_walkable(x, y):
                return (x, y)

        return self.LAND_RECT.center

    def add_shot(self, dst, delay=0.0):
        """Anota un escupitajo: el vendedor se prepara, dispara y retrocede.

        dst = hacia donde sale el objeto (solo se usa para la direccion de las chispas).
        """

        dx = dst[0] - self.MOUTH[0]
        dy = dst[1] - self.MOUTH[1]

        self._shots.append({
            "t": self._clock + delay,
            "dir": math.atan2(dy, dx),
            "fired": False,
        })

    def spit(self, item_ids, collision_map):

        count = len(item_ids)

        if count == 0:
            return []

        gap = min(self.ITEM_DELAY, self.MAX_SPIT_TIME / count)

        items = []

        for n, item_id in enumerate(item_ids):

            if item_id in LIGHTS:
                item = LightItem(item_id, *self.MOUTH)
            else:
                item = WorldItem(item_id, *self.MOUTH)

            landing = self._landing_point(collision_map)

            delay = self.FIRST_DELAY + n * gap

            item.start_fly(
                self.MOUTH,
                landing,
                delay=delay,
                height=self.FLY_HEIGHT,
                duration=self.FLY_TIME,
                fancy=True
            )

            self.add_shot(landing, delay)

            items.append(item)

        self.spit_time = self.FIRST_DELAY + count * gap + 0.2

        return items

    # ------------------------------------------------------------------

    def _kick_value(self):
        """Resorte del vendedor: positivo = inflado, negativo = retroceso."""

        k = 0.0

        upcoming = None

        for shot in self._shots:

            u = self._clock - shot["t"]

            if u < 0:

                if -u <= self.WINDUP:
                    k += 1.0 - (-u / self.WINDUP)

                if upcoming is None or shot["t"] < upcoming:
                    upcoming = shot["t"]

            elif u < self.RECOIL:

                k -= math.exp(-u * 11.0) * math.cos(u * 17.0) * 1.15

        # antes del primero toma aire de a poco
        if (
            upcoming is not None
            and self._clock < upcoming
            and not any(
                0 <= self._clock - sh["t"] < self.RECOIL for sh in self._shots
            )
        ):
            gulp = min(1.0, max(0.0, 1.0 - (upcoming - self._clock) / 0.5))

            k += 0.55 * gulp

        return max(-1.5, min(1.3, k))

    def _fire(self, shot):

        mx, my = self.MOUTH

        base = shot["dir"]

        palette = (
            (255, 226, 140),
            (255, 178, 90),
            (255, 250, 220),
        )

        for _ in range(7):

            ang = base + random.uniform(-0.7, 0.7)
            speed = random.uniform(35, 95)

            self.sparks.append({
                "x": mx + random.uniform(-1, 1),
                "y": my + random.uniform(-1, 1),
                "vx": math.cos(ang) * speed,
                "vy": math.sin(ang) * speed - random.uniform(5, 20),
                "t": 0.0,
                "life": random.uniform(0.28, 0.5),
                "size": random.uniform(0.9, 1.7),
                "color": random.choice(palette),
                "smoke": False,
            })

        for _ in range(3):

            ang = base + random.uniform(-0.5, 0.5)
            speed = random.uniform(10, 28)

            self.sparks.append({
                "x": mx, "y": my,
                "vx": math.cos(ang) * speed,
                "vy": math.sin(ang) * speed - random.uniform(6, 14),
                "t": 0.0,
                "life": random.uniform(0.45, 0.7),
                "size": random.uniform(1.6, 2.6),
                "color": (206, 196, 176),
                "smoke": True,
            })

        self.rings.append({"t": 0.0, "dur": 0.26})

        if len(self.sparks) > 160:
            del self.sparks[:40]

    def update(self, dt, player=None):

        self._clock += dt

        if self.spit_time > 0:
            self.spit_time = max(0.0, self.spit_time - dt)

        # --- disparos ---
        for shot in self._shots:

            if not shot["fired"] and self._clock >= shot["t"]:
                shot["fired"] = True
                self._fire(shot)

        self._shots = [
            sh for sh in self._shots
            if self._clock - sh["t"] < self.RECOIL + 0.1
        ]

        self.kick = self._kick_value()

        self.open_mouth = max(
            0.0, min(1.0, max(0.0, -self.kick) * 0.9 + max(0.0, self.kick) * 0.35)
        )

        # --- chispas y anillos ---
        for p in self.sparks:
            p["t"] += dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            drag = max(0.0, 1.0 - (3.0 if p["smoke"] else 2.2) * dt)
            p["vx"] *= drag
            p["vy"] = p["vy"] * drag + (0.0 if p["smoke"] else 90.0) * dt

        self.sparks = [p for p in self.sparks if p["t"] < p["life"]]

        for r in self.rings:
            r["t"] += dt

        self.rings = [r for r in self.rings if r["t"] < r["dur"]]

        # --- se alegra cuando te acercas ---
        near = False

        if player is not None:
            try:
                near = bool(self.can_talk(player)) or bool(
                    player.rect.colliderect(self.TALK_RECT)
                )
            except Exception:
                near = False

        self._happy += ((1.0 if near else 0.0) - self._happy) * (
            1.0 - math.exp(-6.0 * dt)
        )

        # --- parpadeo ---
        if self._blink_left > 0:
            self._blink_left -= dt
        else:
            self._blink_in -= dt

            if self._blink_in <= 0:
                self._blink_left = 0.13
                self._blink_in = random.uniform(
                    1.2 if self._happy > 0.5 else 2.4,
                    3.0 if self._happy > 0.5 else 5.2
                )

        # --- pose ---
        breath = math.sin(self._clock * math.tau / 2.4)

        sx = 1.0 - 0.020 * breath
        sy = 1.0 + 0.045 * breath

        # el cuerpo queda siempre pegado al mostrador (dy = 0): el recorte del
        # vendedor termina en el mostrador, si se levantara se veria cortado
        dy = 0.0

        # disparo: solo se infla / se achica un poco, sin despegarse del mostrador
        k = self.kick

        sx += 0.11 * k
        sy -= 0.09 * k

        self._pose = (sx, sy, dy)

    # ------------------------------------------------------------------

    def _scaled_body(self, zoom, sx, sy, blinking):

        base = self.body_blink if blinking else self.body_open

        w0, h0 = base.get_size()

        size = (
            max(1, int(round(w0 * zoom * sx))),
            max(1, int(round(h0 * zoom * sy))),
        )

        key = (blinking, size)

        img = self._scaled_cache.get(key)

        if img is None:

            if len(self._scaled_cache) > 160:
                self._scaled_cache.clear()

            img = pygame.transform.scale(base, size)

            self._scaled_cache[key] = img

        return img

    def mouth_world(self):
        """Donde esta la boca ahora (coordenadas del mundo), siguiendo el cuerpo."""

        sx, sy, dy = self._pose

        ax, ay = self.ANCHOR
        mx, my = self.MOUTH

        return (
            ax + (mx - ax) * sx,
            ay + (my - ay) * sy + dy,
        )

    def draw_body(self, screen, camera):
        """El vendedor animado. Va justo despues del mapa, antes de los objetos,
        asi lo que escupe pasa por delante de el."""

        if self.body_open is None:
            return

        zoom = int(camera.zoom)

        sx, sy, dy = self._pose

        # 1) el fondo limpio tapa al vendedor dibujado en el mapa
        bx, by = self.BOX

        bw, bh = self.bg_img.get_size()

        bg = self._bg_cache.get(zoom)

        if bg is None:
            bg = pygame.transform.scale(self.bg_img, (bw * zoom, bh * zoom))
            self._bg_cache = {zoom: bg}

        top_left = camera.apply(pygame.Rect(bx, by, bw, bh)).topleft

        if (
            top_left[0] > screen.get_width()
            or top_left[1] > screen.get_height()
            or top_left[0] + bw * zoom < 0
            or top_left[1] + bh * zoom < 0
        ):
            return

        screen.blit(bg, top_left)

        # 2) el cuerpo, anclado al mostrador
        blinking = self._blink_left > 0 and self.spit_time <= 0

        body = self._scaled_body(zoom, sx, sy, blinking)

        anchor = camera.apply(
            pygame.Rect(self.ANCHOR[0], self.ANCHOR[1], 0, 0)
        ).topleft

        dest = body.get_rect(
            midbottom=(anchor[0], anchor[1] + int(round(dy * zoom)))
        )

        old_clip = screen.get_clip()

        # nada se dibuja por debajo del borde del mostrador
        screen.set_clip(
            pygame.Rect(
                anchor[0] - 400, anchor[1] - 400, 800, 400
            ).clip(old_clip)
        )

        screen.blit(body, dest)

        screen.set_clip(old_clip)

    def _draw_effects(self, screen, camera):

        zoom = camera.zoom

        mx, my = self.mouth_world()

        # anillo que se abre al disparar
        for r in self.rings:

            k = r["t"] / r["dur"]

            radius = int((2.0 + 8.0 * k) * zoom)

            alpha = int(170 * (1.0 - k))

            if alpha <= 0:
                continue

            size = radius * 2 + 6

            ring = pygame.Surface((size, size), pygame.SRCALPHA)

            pygame.draw.circle(
                ring,
                (255, 232, 170, alpha),
                (size // 2, size // 2),
                radius,
                max(1, int(2 * (1.0 - k) * zoom / 2))
            )

            center = camera.apply(pygame.Rect(int(mx), int(my), 0, 0)).topleft

            screen.blit(ring, ring.get_rect(center=center))

        for p in self.sparks:

            k = p["t"] / p["life"]

            r = max(1, int(p["size"] * (1.0 + (1.2 if p["smoke"] else -0.4) * k) * zoom / 2))

            alpha = int((90 if p["smoke"] else 230) * (1.0 - k))

            if alpha <= 0:
                continue

            spr = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)

            pygame.draw.circle(
                spr, p["color"] + (alpha,), (r + 1, r + 1), r
            )

            pos = camera.apply(
                pygame.Rect(int(p["x"]), int(p["y"]), 0, 0)
            ).topleft

            screen.blit(spr, spr.get_rect(center=pos))

    def draw(self, screen, camera):

        self._draw_effects(screen, camera)

        # la boca solo se ve mientras escupe
        if self.spit_time <= 0 and self.open_mouth < 0.05:
            return

        mx, my = self.mouth_world()

        center = camera.apply(pygame.Rect(int(round(mx)) - 1, int(round(my)) - 1, 2, 2)).center

        wave = abs(math.sin(self._clock * 16))

        grow = 1.0 + 0.9 * self.open_mouth

        rx = int((2.2 + 1.2 * wave) * grow * camera.zoom)
        ry = int((2.2 + 1.6 * wave) * grow * camera.zoom)

        mouth = pygame.Rect(0, 0, rx, ry)
        mouth.center = center

        if self.mouth_img is not None:

            size = (max(1, rx), max(1, ry))

            if size not in self._mouth_cache:

                if len(self._mouth_cache) > 120:
                    self._mouth_cache.clear()

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

        mx = self.MOUTH[0]

        dest = camera.apply(pygame.Rect(mx - 1, self.HEAD_TOP, 2, 2))

        screen.blit(
            self.f_icon,
            self.f_icon.get_rect(midbottom=(dest.centerx, dest.top - 6))
        )