"""Mapa que se ve mientras se mantiene el click derecho.

Imagenes (assets/maps/region_01/), hechas con tools/make_mapa_contorno.py:
  mapa_contorno.png    1567x1049   forma del mapa 1 (recortada al borde)
  mapa2_contorno.png   1984x1592   forma del mapa 2
Fondo (assets/maps/hud/): fondo_mapa.png (el papel).
"""

import math
from pathlib import Path

import pygame

from world.zones import ZONES


OUTLINE_COLOR = (226, 201, 150)
SHADOW_COLOR = (14, 10, 6)

DIM_ALPHA = 165

FILL_RATIO = 0.50

FADE_IN_SPEED = 7.0
FADE_OUT_SPEED = 12.0

MAP_IMAGES = {
    "mapa1": "mapa_contorno.png",
    "mapa2": "mapa2_contorno.png",
}

# Zona del mundo (x, y, ancho, alto) que cubre cada imagen de arriba. Las
# imagenes estan recortadas justo al borde de la forma (tools/make_mapa_
# contorno.py), asi la forma queda centrada en el papel. Si regeneras las
# imagenes, actualiza estos numeros con lo que imprime el script.
MAP_BOUNDS = {
    "mapa1": (139, 0, 1567, 1049),
    "mapa2": (8, 8, 1984, 1592),
}

# Texto neutro (sin voseo)
PLAYER_TEXT = "Tú"

BG_NAMES = (
    "fondo_mapa.png",
    "mapa_fondo.png",
    "mapafondo.png",
    "fondomapa.png",
)

BG_DIRS = (
    Path(__file__).resolve().parent.parent / "assets" / "maps" / "hud",
    Path(__file__).resolve().parent.parent / "assets" / "maps" / "ui",
    Path(__file__).resolve().parent.parent / "assets" / "maps" / "region_01",
)

BG_RATIO = 0.62

# Que tanto del papel (fondo_mapa.png) puede ocupar el dibujo del mapa.
# Antes el contorno se calculaba contra la pantalla y se salia del papel.
INNER_RATIO = 0.74

MAP_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "region_01"
)


# Solo el nombre de la zona, todas las letras del mismo color.
LABEL_COLOR = (240, 225, 190)

ZONE_LABELS = {
    "inicio": ("Cabaña", None, LABEL_COLOR),
    "central": ("Centro", None, LABEL_COLOR),
    "tienda": ("Tienda", None, LABEL_COLOR),
    "cofres": ("Sala de cofres", None, LABEL_COLOR),
    "combate": ("ORKUN", None, LABEL_COLOR),
    "combate_izq": ("STONUN", None, LABEL_COLOR),
}

LABEL_OUTLINE = (0, 0, 0)

# Salas chicas: el nombre no entra adentro (y taparia los cofres), asi que
# va ARRIBA de la sala, centrado sobre ella. Las salas grandes lo llevan
# adentro, en el medio.
LABEL_ABOVE = {"cofres", "tienda"}

PLAYER_COLOR = (255, 215, 110)
CHEST_READY = (120, 225, 120)
CHEST_WAIT = (140, 132, 122)


def _erode(mask, size, t):

    eroded = mask.copy()

    for dx, dy in (
        (t, 0), (-t, 0), (0, t), (0, -t),
        (t, t), (t, -t), (-t, t), (-t, -t),
    ):

        shifted = pygame.mask.Mask(size)
        shifted.draw(mask, (dx, dy))

        eroded = eroded.overlap_mask(shifted, (0, 0))

    return eroded


def _fit(walkable, screen_size, box=None):

    rects = [pygame.Rect(r) for r in walkable if r.width > 0 and r.height > 0]

    if not rects:
        return None

    sw, sh = screen_size

    bounds = rects[0].unionall(rects[1:])

    # box = (ancho, alto) maximo que puede ocupar el dibujo; sin caja se
    # usa la pantalla (como antes).
    if box is None:
        box = (sw * FILL_RATIO, sh * FILL_RATIO)

    scale = min(
        box[0] / bounds.width,
        box[1] / bounds.height,
    )

    thickness = max(2, int(min(sw, sh) / 240))

    pad = thickness + 4

    return rects, bounds, scale, thickness, pad


def build_outline(walkable, screen_size, box=None):

    fit = _fit(walkable, screen_size, box)

    if fit is None:
        return None, None

    rects, bounds, scale, thickness, pad = fit

    size = (
        int(math.ceil(bounds.width * scale)) + pad * 2,
        int(math.ceil(bounds.height * scale)) + pad * 2,
    )

    shape = pygame.Surface(size, pygame.SRCALPHA)

    for r in rects:

        x0 = int(math.floor((r.left - bounds.left) * scale)) + pad
        y0 = int(math.floor((r.top - bounds.top) * scale)) + pad
        x1 = int(math.ceil((r.right - bounds.left) * scale)) + pad
        y1 = int(math.ceil((r.bottom - bounds.top) * scale)) + pad

        pygame.draw.rect(
            shape,
            (255, 255, 255, 255),
            (x0, y0, max(1, x1 - x0), max(1, y1 - y0)),
        )

    mask = pygame.mask.from_surface(shape)

    outline = mask.copy()
    outline.erase(_erode(mask, size, thickness), (0, 0))

    line = outline.to_surface(
        setcolor=OUTLINE_COLOR + (255,),
        unsetcolor=(0, 0, 0, 0),
    )

    shadow = outline.to_surface(
        setcolor=SHADOW_COLOR + (210,),
        unsetcolor=(0, 0, 0, 0),
    )

    return line, shadow


class DungeonMapView:

    def __init__(self):

        self._key = None
        self._line = None
        self._shadow = None

        self._dim = None
        self._dim_size = None

        self._alpha = 0.0
        self._last_ms = None

        self._images = {}
        self._bg = None
        self._bg_loaded = False
        self._bg_scaled = None
        self._bg_key = None
        self._scaled_key = None
        self._scaled = None
        self._frame = None

        self._fonts = {}
        self._label_cache = {}

    def _ensure_bg(self, screen_size):

        if not self._bg_loaded:

            self._bg_loaded = True

            for folder in BG_DIRS:

                for name in BG_NAMES:

                    path = folder / name

                    if not path.exists():
                        continue

                    try:
                        self._bg = pygame.image.load(
                            str(path)
                        ).convert_alpha()
                    except pygame.error:
                        self._bg = None

                    if self._bg is not None:
                        break

                if self._bg is not None:
                    break

        if self._bg is None:
            return None

        key = tuple(screen_size)

        if key == self._bg_key:
            return self._bg_scaled

        sw, sh = screen_size

        scale = min(
            sw * BG_RATIO / self._bg.get_width(),
            sh * BG_RATIO / self._bg.get_height(),
        )

        size = (
            max(1, int(self._bg.get_width() * scale)),
            max(1, int(self._bg.get_height() * scale)),
        )

        self._bg_scaled = pygame.transform.smoothscale(self._bg, size)
        self._bg_key = key

        return self._bg_scaled

    def _load_image(self, map_name):

        if map_name in self._images:
            return self._images[map_name]

        image = None

        file_name = MAP_IMAGES.get(map_name)

        if file_name:

            try:
                image = pygame.image.load(
                    str(MAP_DIR / file_name)
                ).convert_alpha()
            except (pygame.error, FileNotFoundError):
                image = None

        self._images[map_name] = image

        return image

    def _ensure_image(self, map_name, screen_size):

        image = self._load_image(map_name)

        if image is None:
            return None

        bg = self._ensure_bg(screen_size)

        key = (map_name, tuple(screen_size), bg is not None)

        if key == self._scaled_key:
            return self._scaled

        sw, sh = screen_size

        if bg is not None:
            box_w = bg.get_width() * INNER_RATIO
            box_h = bg.get_height() * INNER_RATIO
        else:
            box_w = sw * FILL_RATIO
            box_h = sh * FILL_RATIO

        scale = min(
            box_w / image.get_width(),
            box_h / image.get_height(),
        )

        size = (
            max(1, int(image.get_width() * scale)),
            max(1, int(image.get_height() * scale)),
        )

        self._scaled = pygame.transform.smoothscale(image, size)
        self._scaled_key = key

        return self._scaled

    def _ensure(self, walkable, screen_size, box=None):

        key = (
            tuple((r.x, r.y, r.w, r.h) for r in walkable),
            tuple(screen_size),
            None if box is None else (round(box[0]), round(box[1])),
        )

        if key != self._key:

            self._line, self._shadow = build_outline(
                walkable, screen_size, box
            )
            self._key = key

        if self._dim is None or self._dim_size != tuple(screen_size):

            self._dim = pygame.Surface(screen_size, pygame.SRCALPHA)
            self._dim.fill((0, 0, 0, DIM_ALPHA))
            self._dim_size = tuple(screen_size)

    def _font(self, size):

        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)

        return self._fonts[size]

    def _label(self, text, size, color):

        key = (text, size, color)

        if key not in self._label_cache:

            font = self._font(size)

            body = font.render(text, True, color)
            edge = font.render(text, True, LABEL_OUTLINE)

            w, h = body.get_size()

            surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)

            for dx, dy in (
                (0, 2), (4, 2), (2, 0), (2, 4),
                (0, 0), (4, 4), (0, 4), (4, 0),
            ):
                surf.blit(edge, (dx, dy))

            surf.blit(body, (2, 2))

            self._label_cache[key] = surf

        return self._label_cache[key]

    def _draw_zone_labels(self, screen, to_screen, alpha, screen_h, subs=None):

        base = max(14, int(screen_h / 40))

        for zone in ZONES:

            info = ZONE_LABELS.get(zone.id)

            if info is None:
                continue

            title, sub, color = info

            if subs and zone.id in subs:
                sub = subs[zone.id]

            cx, cy = to_screen(*zone.rect.center)

            main = self._label(title, base, color)

            main.set_alpha(alpha)

            small = None

            if sub is not None:

                small = self._label(sub, max(12, base - 4), color)

                small.set_alpha(alpha)

            if zone.id in LABEL_ABOVE:

                # bloque (nombre + estado) apoyado sobre el borde de arriba
                _, ty = to_screen(zone.rect.centerx, zone.rect.top)

                block = main.get_height()

                if small is not None:
                    block += small.get_height() - 2

                cy = ty - 6 - block / 2

            if small is None:

                screen.blit(main, main.get_rect(center=(int(cx), int(cy))))

                continue

            total = main.get_height() + small.get_height() - 2

            top = int(cy - total // 2)

            screen.blit(main, main.get_rect(midtop=(cx, top)))

            screen.blit(
                small,
                small.get_rect(midtop=(cx, top + main.get_height() - 2))
            )

    def _draw_extras(self, screen, to_screen, alpha, screen_h, map_name,
                     info, bottom):
        """Nombres de zona (con su estado), cofres, tu posicion y leyenda."""

        info = info or {}

        if map_name == "mapa1":
            self._draw_zone_labels(
                screen, to_screen, alpha, screen_h, info.get("subs")
            )

        player = info.get("player")
        chests = info.get("chests") or []

        if player is None and not chests:
            return

        base = max(6, int(screen_h / 110))
        now = pygame.time.get_ticks() / 1000.0

        layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

        for x, y, ready in chests:

            sx, sy = to_screen(x, y)

            box = pygame.Rect(0, 0, base * 2, base * 2)
            box.center = (int(sx), int(sy))

            color = CHEST_READY if ready else CHEST_WAIT

            pygame.draw.rect(layer, color + (255,), box, border_radius=2)
            pygame.draw.rect(
                layer, SHADOW_COLOR + (255,), box, 2, border_radius=2
            )

        if player is not None:

            sx, sy = to_screen(*player)

            pulse = 0.5 + 0.5 * math.sin(now * 5)

            pygame.draw.circle(
                layer, PLAYER_COLOR + (int(150 * (1 - pulse)),),
                (int(sx), int(sy)), int(base + 3 + 6 * pulse), 2
            )
            pygame.draw.circle(
                layer, SHADOW_COLOR + (255,), (int(sx), int(sy)), base + 2
            )
            pygame.draw.circle(
                layer, PLAYER_COLOR + (255,), (int(sx), int(sy)), base
            )

        layer.set_alpha(alpha)
        screen.blit(layer, (0, 0))

        if player is not None:

            sx, sy = to_screen(*player)

            tag = self._label(PLAYER_TEXT, max(15, int(screen_h / 40)), PLAYER_COLOR)
            tag.set_alpha(alpha)

            screen.blit(
                tag, tag.get_rect(midbottom=(int(sx), int(sy - base - 8)))
            )

        # leyenda abajo del papel
        items = []

        if player is not None:
            items.append(("player", PLAYER_TEXT))

        if chests:
            items.append(("ready", "Cofre listo"))
            items.append(("wait", "Cofre en espera"))

        size = max(14, int(screen_h / 46))

        labels = [
            (kind, self._label(text, size, LABEL_COLOR))
            for kind, text in items
        ]

        gap = 22
        icon_w = base * 2 + 8

        total = sum(icon_w + lab.get_width() for _, lab in labels)
        total += gap * (len(labels) - 1)

        x = (screen.get_width() - total) // 2
        y = min(screen_h - 26, int(bottom) + 10)

        for kind, lab in labels:

            lab.set_alpha(alpha)

            cx, cy = x + base, y + lab.get_height() // 2

            dot = pygame.Surface((base * 2 + 6, base * 2 + 6), pygame.SRCALPHA)
            c = (dot.get_width() // 2, dot.get_height() // 2)

            if kind == "player":
                pygame.draw.circle(dot, SHADOW_COLOR + (255,), c, base + 2)
                pygame.draw.circle(dot, PLAYER_COLOR + (255,), c, base)
            else:
                color = CHEST_READY if kind == "ready" else CHEST_WAIT
                box = pygame.Rect(0, 0, base * 2, base * 2)
                box.center = c
                pygame.draw.rect(dot, color + (255,), box, border_radius=2)
                pygame.draw.rect(
                    dot, SHADOW_COLOR + (255,), box, 2, border_radius=2
                )

            dot.set_alpha(alpha)

            screen.blit(dot, dot.get_rect(center=(cx, cy)))
            screen.blit(lab, (x + icon_w, y))

            x += icon_w + lab.get_width() + gap

    def draw(self, screen, walkable, held, label_font=None, map_name="mapa1",
             info=None):

        now = pygame.time.get_ticks()

        dt = 0.0 if self._last_ms is None else (now - self._last_ms) / 1000.0

        self._last_ms = now

        dt = min(dt, 0.1)

        if held:
            self._alpha = min(1.0, self._alpha + dt * FADE_IN_SPEED)
        else:
            self._alpha = max(0.0, self._alpha - dt * FADE_OUT_SPEED)

        if self._alpha <= 0.0:
            return

        sw, sh = screen.get_size()

        bg = self._ensure_bg((sw, sh))

        # el contorno tiene que entrar dentro del papel, no de la pantalla
        box = (
            None if bg is None
            else (bg.get_width() * INNER_RATIO, bg.get_height() * INNER_RATIO)
        )

        self._ensure(walkable, (sw, sh), box)

        a = int(255 * self._alpha)

        self._dim.set_alpha(a)
        screen.blit(self._dim, (0, 0))

        bg_top = None
        bg_bottom = None

        if bg is not None:

            # el PNG tiene margen transparente desigual: se centra la parte
            # visible del papel, no la imagen entera
            vis = bg.get_bounding_rect()

            bg_rect = bg.get_rect(center=(
                sw // 2 - (vis.centerx - bg.get_width() // 2),
                sh // 2 - (vis.centery - bg.get_height() // 2),
            ))

            bg.set_alpha(a)

            screen.blit(bg, bg_rect)

            bg_top = bg_rect.top + vis.top
            bg_bottom = bg_rect.top + vis.bottom

        image = self._ensure_image(map_name, (sw, sh))

        if image is not None:

            rect = image.get_rect(center=(sw // 2, sh // 2))

            image.set_alpha(a)

            screen.blit(image, rect)

            top = rect.top

            fit = _fit(walkable, (sw, sh), box)

            if map_name in MAP_BOUNDS:
                bounds = pygame.Rect(MAP_BOUNDS[map_name])
            else:
                bounds = None if fit is None else fit[1]

            if bounds is not None:

                def to_screen(x, y, rect=rect, bounds=bounds):
                    return (
                        rect.left + (x - bounds.left) / bounds.width * rect.width,
                        rect.top + (y - bounds.top) / bounds.height * rect.height,
                    )

                self._draw_extras(
                    screen, to_screen, a, sh, map_name, info,
                    rect.bottom if bg is None else bg_bottom
                )

        else:

            if self._line is None:
                return

            pos = (
                (sw - self._line.get_width()) // 2,
                (sh - self._line.get_height()) // 2,
            )

            self._shadow.set_alpha(a)
            self._line.set_alpha(a)

            screen.blit(self._shadow, (pos[0] + 2, pos[1] + 2))
            screen.blit(self._line, pos)

            top = pos[1]

            fit = _fit(walkable, (sw, sh), box)

            if fit is not None:

                _, bounds, scale, _, pad = fit

                def to_screen(x, y, pos=pos, bounds=bounds,
                              scale=scale, pad=pad):
                    return (
                        pos[0] + pad + (x - bounds.left) * scale,
                        pos[1] + pad + (y - bounds.top) * scale,
                    )

                self._draw_extras(
                    screen, to_screen, a, sh, map_name, info,
                    pos[1] + self._line.get_height()
                    if bg is None else bg_bottom
                )

        if bg_top is not None:
            top = bg_top

        if label_font is not None:

            text = label_font.render("MAPA", True, OUTLINE_COLOR)
            text.set_alpha(a)

            screen.blit(
                text,
                text.get_rect(midtop=(sw // 2, max(8, top // 2 - 10))),
            )