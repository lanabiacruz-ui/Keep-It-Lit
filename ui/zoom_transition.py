import math

import pygame

from states.main_menu import MONITOR_BOX, MONITOR_REF


ZOOM_DELAY = 0.15
ZOOM_DURATION = 1.0
REVEAL_DURATION = 0.5

ZOOM_FILL = 0.90

FLASH_COLOR = (215, 232, 255)
FLASH_MAX = 210
FLASH_START = 0.70

VIGNETTE_ALPHA = 130


def _clamp01(k):

    return max(0.0, min(1.0, k))


def _ease_in_out(k):

    k = _clamp01(k)

    if k < 0.5:
        return 4 * k * k * k

    return 1 - ((-2 * k + 2) ** 3) / 2


def _make_vignette(w, h):

    sw, sh = 64, 36

    small = pygame.Surface((sw, sh), pygame.SRCALPHA)

    for y in range(sh):

        for x in range(sw):

            dx = (x + 0.5) / sw - 0.5
            dy = (y + 0.5) / sh - 0.5

            dist = math.sqrt(dx * dx + dy * dy) / 0.707

            alpha = int(255 * _clamp01((dist - 0.35) / 0.65) ** 1.6)

            small.set_at((x, y), (0, 0, 0, alpha))

    return pygame.transform.smoothscale(small, (w, h))


class ZoomTransition:

    def __init__(self, old_frame, delay=ZOOM_DELAY, duration=ZOOM_DURATION,
                 reveal=REVEAL_DURATION):

        self.old = old_frame
        self.w, self.h = old_frame.get_size()

        self.delay = delay
        self.duration = duration
        self.reveal = reveal

        self.t = 0.0

        kx = self.w / MONITOR_REF[0]
        ky = self.h / MONITOR_REF[1]

        x0, y0, x1, y1 = MONITOR_BOX

        mon = pygame.Rect(
            round(x0 * kx),
            round(y0 * ky),
            round((x1 - x0) * kx),
            round((y1 - y0) * ky),
        )

        end_h = mon.height * ZOOM_FILL

        self.end_scale = self.h / end_h

        self.start_center = (self.w / 2, self.h / 2)
        self.end_center = mon.center

        self._canvas = pygame.Surface((self.w, self.h))

        self._flash = pygame.Surface((self.w, self.h))
        self._flash.fill(FLASH_COLOR)

        self._vignette = _make_vignette(self.w, self.h)


    @property
    def active(self):

        return self.t < self.delay + self.duration + self.reveal

    def update(self, dt):

        self.t += dt

        if not self.active:
            return "done"

        return None

    def zoom_progress(self):

        return _ease_in_out((self.t - self.delay) / max(0.001, self.duration))

    def reveal_progress(self):

        return _clamp01(
            (self.t - self.delay - self.duration) / max(0.001, self.reveal)
        )


    def _render_view(self, e):

        w, h = self.w, self.h

        scale = math.exp(e * math.log(self.end_scale))

        cx = self.start_center[0] + (self.end_center[0] - self.start_center[0]) * e
        cy = self.start_center[1] + (self.end_center[1] - self.start_center[1]) * e

        vw = w / scale
        vh = h / scale

        vx = max(0.0, min(cx - vw / 2, w - vw))
        vy = max(0.0, min(cy - vh / 2, h - vh))

        ix = int(math.floor(vx))
        iy = int(math.floor(vy))

        iw = min(w - ix, int(math.ceil(vx + vw)) - ix)
        ih = min(h - iy, int(math.ceil(vy + vh)) - iy)

        piece = self.old.subsurface(pygame.Rect(ix, iy, iw, ih))

        size = (max(1, round(iw * scale)), max(1, round(ih * scale)))

        if size == (w, h):
            scaled = piece
        else:
            scaled = pygame.transform.smoothscale(piece, size)

        self._canvas.fill((0, 0, 0))

        self._canvas.blit(
            scaled,
            (round((ix - vx) * scale), round((iy - vy) * scale))
        )

    def draw(self, screen):

        if not self.active:
            return

        e = self.zoom_progress()
        r = self.reveal_progress()

        self._render_view(e)

        if VIGNETTE_ALPHA > 0:

            self._vignette.set_alpha(int(VIGNETTE_ALPHA * e))
            self._canvas.blit(self._vignette, (0, 0))

        flash = _clamp01((e - FLASH_START) / (1 - FLASH_START)) ** 2

        if flash > 0:

            self._flash.set_alpha(int(FLASH_MAX * flash))
            self._canvas.blit(self._flash, (0, 0))

        self._canvas.set_alpha(int(255 * (1 - r)))

        screen.blit(self._canvas, (0, 0))
