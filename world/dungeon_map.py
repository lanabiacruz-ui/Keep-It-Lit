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
INNER_RATIO = 0.82

MAP_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "region_01"
)


ZONE_LABELS = {
    "inicio": ("Cabaña", None, (240, 225, 190)),
    "central": ("Centro", None, (240, 225, 190)),
    "tienda": ("Tienda", None, (240, 225, 190)),
    "cofres": ("Sala de cofres", None, (240, 225, 190)),
    "combate": ("ORKUN", "Zona 1 - empezá acá", (150, 235, 150)),
    "combate_izq": ("STONUN", "Zona 2 - difícil", (255, 120, 100)),
}

LABEL_OUTLINE = (0, 0, 0)


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


def _fit(walkable, screen_size):

    rects = [pygame.Rect(r) for r in walkable if r.width > 0 and r.height > 0]

    if not rects:
        return None

    sw, sh = screen_size

    bounds = rects[0].unionall(rects[1:])

    scale = min(
        sw * FILL_RATIO / bounds.width,
        sh * FILL_RATIO / bounds.height,
    )

    thickness = max(2, int(min(sw, sh) / 240))

    pad = thickness + 4

    return rects, bounds, scale, thickness, pad


def build_outline(walkable, screen_size):

    fit = _fit(walkable, screen_size)

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

    def _ensure(self, walkable, screen_size):

        key = (
            tuple((r.x, r.y, r.w, r.h) for r in walkable),
            tuple(screen_size),
        )

        if key != self._key:

            self._line, self._shadow = build_outline(walkable, screen_size)
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

    def _draw_zone_labels(self, screen, to_screen, alpha, screen_h):

        base = max(15, int(screen_h / 34))

        for zone in ZONES:

            info = ZONE_LABELS.get(zone.id)

            if info is None:
                continue

            title, sub, color = info

            cx, cy = to_screen(*zone.rect.center)

            main = self._label(title, base, color)

            main.set_alpha(alpha)

            if sub is None:

                screen.blit(main, main.get_rect(center=(cx, cy)))

                continue

            small = self._label(sub, max(13, base - 5), color)

            small.set_alpha(alpha)

            total = main.get_height() + small.get_height() - 2

            top = cy - total // 2

            screen.blit(main, main.get_rect(midtop=(cx, top)))

            screen.blit(
                small,
                small.get_rect(midtop=(cx, top + main.get_height() - 2))
            )

    def draw(self, screen, walkable, held, label_font=None, map_name="mapa1"):

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

        self._ensure(walkable, (sw, sh))

        a = int(255 * self._alpha)

        self._dim.set_alpha(a)
        screen.blit(self._dim, (0, 0))

        bg = self._ensure_bg((sw, sh))

        bg_top = None

        if bg is not None:

            bg_rect = bg.get_rect(center=(sw // 2, sh // 2))

            bg.set_alpha(a)

            screen.blit(bg, bg_rect)

            bg_top = bg_rect.top

        image = self._ensure_image(map_name, (sw, sh))

        if image is not None:

            rect = image.get_rect(center=(sw // 2, sh // 2))

            image.set_alpha(a)

            screen.blit(image, rect)

            top = rect.top

            fit = _fit(walkable, (sw, sh))

            if map_name == "mapa1" and fit is not None:

                bounds = fit[1]

                def to_screen(x, y, rect=rect, bounds=bounds):
                    return (
                        rect.left + (x - bounds.left) / bounds.width * rect.width,
                        rect.top + (y - bounds.top) / bounds.height * rect.height,
                    )

                self._draw_zone_labels(screen, to_screen, a, sh)

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

            fit = _fit(walkable, (sw, sh))

            if map_name == "mapa1" and fit is not None:

                _, bounds, scale, _, pad = fit

                def to_screen(x, y, pos=pos, bounds=bounds,
                              scale=scale, pad=pad):
                    return (
                        pos[0] + pad + (x - bounds.left) * scale,
                        pos[1] + pad + (y - bounds.top) * scale,
                    )

                self._draw_zone_labels(screen, to_screen, a, sh)

        if bg_top is not None:
            top = bg_top

        if label_font is not None:

            text = label_font.render("MAPA", True, OUTLINE_COLOR)
            text.set_alpha(a)

            screen.blit(
                text,
                text.get_rect(midtop=(sw // 2, max(8, top // 2 - 10))),
            )