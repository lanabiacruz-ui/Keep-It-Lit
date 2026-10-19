import math

import pygame


OUTLINE_COLOR = (226, 201, 150)
SHADOW_COLOR = (14, 10, 6)

DIM_ALPHA = 165

FILL_RATIO = 0.80

FADE_IN_SPEED = 7.0
FADE_OUT_SPEED = 12.0


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


def build_outline(walkable, screen_size):

    rects = [pygame.Rect(r) for r in walkable if r.width > 0 and r.height > 0]

    if not rects:
        return None, None

    sw, sh = screen_size

    bounds = rects[0].unionall(rects[1:])

    scale = min(
        sw * FILL_RATIO / bounds.width,
        sh * FILL_RATIO / bounds.height,
    )

    thickness = max(2, int(min(sw, sh) / 240))

    pad = thickness + 4

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

    def draw(self, screen, walkable, held, label_font=None):

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

        self._ensure(walkable, screen.get_size())

        if self._line is None:
            return

        a = int(255 * self._alpha)

        self._dim.set_alpha(a)
        screen.blit(self._dim, (0, 0))

        sw, sh = screen.get_size()

        pos = (
            (sw - self._line.get_width()) // 2,
            (sh - self._line.get_height()) // 2,
        )

        self._shadow.set_alpha(a)
        self._line.set_alpha(a)

        screen.blit(self._shadow, (pos[0] + 2, pos[1] + 2))
        screen.blit(self._line, pos)

        if label_font is not None:

            text = label_font.render("MAPA", True, OUTLINE_COLOR)
            text.set_alpha(a)

            screen.blit(
                text,
                text.get_rect(midtop=(sw // 2, max(8, pos[1] // 2 - 10))),
            )
