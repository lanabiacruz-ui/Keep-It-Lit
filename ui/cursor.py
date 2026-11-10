"""Cursor del juego: una antorcha con llama animada.

Se dibuja con codigo (no hace falta ninguna imagen). El punto de clic
(hotspot) es la PUNTA DE LA LLAMA.

Uso en main.py:
    pygame.mouse.set_visible(False)
    torch_cursor = TorchCursor()
    ...
    torch_cursor.draw(screen)      # justo antes de pygame.display.flip()

Si preferis tu propio dibujo: guardalo como assets/cursor_antorcha.png y
ajusta IMAGE_HOTSPOT (el pixel de la imagen donde "hace clic").
"""
import math
import random
from pathlib import Path

import pygame

IMAGE_FILE = "cursor_antorcha.png"
# punto de clic en la imagen ORIGINAL (la punta de la llama)
IMAGE_HOTSPOT = (6, 0)
# tamano en pantalla: 1.0 = tal cual la imagen, 0.5 = la mitad, etc.
CURSOR_SCALE = 0.5

_IMAGE_PATH = Path(__file__).resolve().parent.parent / "assets" / IMAGE_FILE

# Inclinacion de la antorcha (radianes): el mango baja hacia la derecha,
# como una flecha de mouse normal.
TILT = 0.38
_DX, _DY = math.sin(TILT), math.cos(TILT)      # eje punta -> mango
_NX, _NY = math.cos(TILT), -math.sin(TILT)     # perpendicular

FLAME_LEN = 24
HANDLE_LEN = 34


def _pt(origin, t, w):
    """Punto a distancia t sobre el eje y w al costado."""
    return (
        origin[0] + _DX * t + _NX * w,
        origin[1] + _DY * t + _NY * w,
    )


def _make_glow(radius):
    size = radius * 2
    glow = pygame.Surface((size, size), pygame.SRCALPHA)

    for r in range(radius, 0, -2):
        a = int(48 * (1 - r / radius) ** 2)
        pygame.draw.circle(glow, (255, 150, 40, a), (radius, radius), r)

    return glow


class TorchCursor:

    def __init__(self):
        self.time = 0.0
        self.embers = []
        self.image = None
        self._hotspot = IMAGE_HOTSPOT

        if _IMAGE_PATH.exists():
            try:
                self.image = pygame.image.load(str(_IMAGE_PATH)).convert_alpha()

                if CURSOR_SCALE != 1:
                    w, h = self.image.get_size()
                    size = (
                        max(1, round(w * CURSOR_SCALE)),
                        max(1, round(h * CURSOR_SCALE)),
                    )
                    self.image = pygame.transform.smoothscale(self.image, size)
                    self._hotspot = (
                        round(IMAGE_HOTSPOT[0] * CURSOR_SCALE),
                        round(IMAGE_HOTSPOT[1] * CURSOR_SCALE),
                    )
            except pygame.error:
                self.image = None

        self._glow = _make_glow(40)
        self._last_ticks = pygame.time.get_ticks()

    # ------------------------------------------------------------------
    def _dt(self):
        now = pygame.time.get_ticks()
        dt = min((now - self._last_ticks) / 1000, 0.05)
        self._last_ticks = now
        return dt

    def _update_embers(self, dt, tip, strength):
        if random.random() < 6 * dt * strength:
            self.embers.append([
                tip[0] + random.uniform(-3, 3),
                tip[1] + random.uniform(0, 6),
                random.uniform(-14, 14),
                random.uniform(-46, -22),
                random.uniform(0.35, 0.7),
            ])

        for e in self.embers:
            e[0] += e[2] * dt
            e[1] += e[3] * dt
            e[4] -= dt

        self.embers = [e for e in self.embers if e[4] > 0]

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not pygame.mouse.get_focused():
            return

        mx, my = pygame.mouse.get_pos()
        dt = self._dt()
        self.time += dt

        if self.image is not None:
            surface.blit(
                self.image, (mx - self._hotspot[0], my - self._hotspot[1])
            )
            return

        pressed = pygame.mouse.get_pressed()[0]
        strength = 1.3 if pressed else 1.0

        # la punta de la llama es el punto de clic
        tip = (mx, my)
        t = self.time

        flick = math.sin(t * 13) * 0.6 + math.sin(t * 7.3 + 1.3) * 0.4
        sway = flick * 2.2
        length = FLAME_LEN * strength * (1 + 0.08 * flick)

        # base de la llama = cabeza del mango
        base = _pt(tip, length, 0)

        # --- resplandor ---
        glow_center = _pt(tip, length * 0.65, 0)
        surface.blit(
            self._glow,
            (int(glow_center[0] - 40), int(glow_center[1] - 40)),
        )

        # --- mango ---
        h0 = _pt(base, 2, 0)
        h1 = _pt(base, HANDLE_LEN, 0)
        pygame.draw.polygon(surface, (96, 58, 28), [
            _pt(h0, 0, -4), _pt(h0, 0, 4), _pt(h1, 0, 3), _pt(h1, 0, -3),
        ])
        pygame.draw.polygon(surface, (140, 90, 44), [
            _pt(h0, 0, -4), _pt(h0, 0, -1), _pt(h1, 0, -1), _pt(h1, 0, -3),
        ])
        # tira de tela
        for k in (7, 13):
            c = _pt(base, k, 0)
            pygame.draw.line(
                surface, (60, 34, 16), _pt(c, 0, -4), _pt(c, 0, 4), 2
            )
        pygame.draw.polygon(surface, (50, 30, 18), [
            _pt(h1, 0, -3), _pt(h1, 0, 3), _pt(h1, 3, 2), _pt(h1, 3, -2),
        ])

        # --- cabeza de tela quemada ---
        pygame.draw.polygon(surface, (38, 24, 18), [
            _pt(base, -3, -6), _pt(base, -3, 6),
            _pt(base, 6, 5), _pt(base, 6, -5),
        ])
        pygame.draw.polygon(surface, (70, 42, 24), [
            _pt(base, -3, -6), _pt(base, -3, -1),
            _pt(base, 6, -1), _pt(base, 6, -5),
        ])

        # --- llama (tres capas) ---
        layers = (
            ((255, 110, 20), 1.0, 8.5),
            ((255, 185, 40), 0.78, 6.0),
            ((255, 242, 170), 0.5, 3.2),
        )

        for color, scale, width in layers:
            L = length * scale
            w = width * (0.9 + 0.1 * strength)
            top = _pt(tip, length - L, 0)
            top = (top[0] + sway * (0.6 + scale * 0.4), top[1])

            pts = [
                top,
                _pt(base, -L * 0.62, -w * 0.55),
                _pt(base, -L * 0.28, -w),
                _pt(base, 1, -w * 0.62),
                _pt(base, 3, 0),
                _pt(base, 1, w * 0.62),
                _pt(base, -L * 0.28, w),
                _pt(base, -L * 0.62, w * 0.55),
            ]
            pygame.draw.polygon(surface, color, pts)

        # --- chispas ---
        self._update_embers(dt, tip, strength)

        for x, y, _, _, life in self.embers:
            a = max(0.0, min(1.0, life / 0.7))
            c = (255, int(150 + 90 * a), int(40 + 60 * a))
            pygame.draw.circle(surface, c, (int(x), int(y)), 1)