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

# --- reaccion al clic (cuando usas la antorcha PNG) ---
# "calor" 0..1: sube rapido al clickear/mantener y se apaga de a poco al soltar
HEAT_RISE = 16.0       # velocidad de subida (por segundo)
HEAT_FALL = 3.2        # velocidad de bajada al soltar (mas bajo = dura mas)
CLICK_FLARE = 0.85     # calor minimo instantaneo en el momento del clic
FLAME_BOTTOM = 0.46    # fraccion de la altura de la imagen donde termina la llama
GLOW_RADIUS = 46


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


def _make_bright_flame(image):
    """Copia de la imagen con SOLO la llama aclarada (amarillo/blanco calido).

    Se dibuja encima de la antorcha normal con alpha = calor, asi la llama
    "se prende mas" sin tocar el mango ni la cabeza de tela.
    """
    w, h = image.get_size()
    bright = pygame.Surface((w, h), pygame.SRCALPHA)
    limit = int(h * FLAME_BOTTOM)

    for y in range(min(limit, h)):
        for x in range(w):
            r, g, b, a = image.get_at((x, y))
            if a == 0 or r < 150:
                continue
            t = 0.62
            bright.set_at((x, y), (
                int(r + (255 - r) * t),
                int(g + (238 - g) * t),
                int(b + (165 - b) * t),
                a,
            ))

    return bright


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

        # pixeles que habia debajo de la antorcha antes de dibujarla, para
        # poder sacar capturas de pantalla SIN la antorcha (transiciones)
        self._under = None
        self._under_pos = (0, 0)
        self._pad = GLOW_RADIUS * 2 + 24
        if self.image is not None:
            self._pad += max(self.image.get_size())
        else:
            self._pad += FLAME_LEN + HANDLE_LEN

        # reaccion al clic
        self.heat = 0.0
        self._was_pressed = False
        self._bright = None
        self._heat_glow = _make_glow(GLOW_RADIUS)

        if self.image is not None:
            self._bright = _make_bright_flame(self.image)

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
    def _draw_image(self, surface, mx, my, dt):
        """Antorcha PNG; la llama se aviva al clickear o mantener presionado."""
        pressed = pygame.mouse.get_pressed()[0]

        # calor: salto instantaneo al clic, sube mientras mantenes, baja suave
        if pressed:
            if not self._was_pressed:
                self.heat = max(self.heat, CLICK_FLARE)
            self.heat = min(1.0, self.heat + HEAT_RISE * dt)
        else:
            self.heat = max(0.0, self.heat - HEAT_FALL * dt)
        self._was_pressed = pressed

        heat = self.heat
        t = self.time
        flick = math.sin(t * 17) * 0.5 + math.sin(t * 9.1 + 1.3) * 0.5

        w, h = self.image.get_size()
        ox, oy = mx - self._hotspot[0], my - self._hotspot[1]

        # resplandor naranja detras (solo cuando hay calor)
        if heat > 0.01:
            glow_alpha = int(255 * heat * (0.8 + 0.2 * flick))
            self._heat_glow.set_alpha(max(0, min(255, glow_alpha)))
            surface.blit(
                self._heat_glow,
                (
                    int(ox + w * 0.5 - GLOW_RADIUS),
                    int(oy + h * 0.2 - GLOW_RADIUS),
                ),
            )

        # antorcha normal
        surface.blit(self.image, (ox, oy))

        # llama aclarada encima, con parpadeo
        if heat > 0.01 and self._bright is not None:
            a = int(255 * heat * (0.85 + 0.15 * flick))
            self._bright.set_alpha(max(0, min(255, a)))
            surface.blit(self._bright, (ox, oy))

        # chispas: aparecen con el calor
        if heat > 0.05:
            self._update_embers(dt, (mx, my), 1 + 4 * heat)
            for x, y, _, _, life in self.embers:
                k = max(0.0, min(1.0, life / 0.7))
                c = (255, int(150 + 90 * k), int(40 + 60 * k))
                pygame.draw.circle(surface, c, (int(x), int(y)), 1)
        elif self.embers:
            self._update_embers(dt, (mx, my), 0)

    # ------------------------------------------------------------------
    def _backup_under(self, surface, mx, my):
        """Guarda los pixeles de la zona donde se va a dibujar la antorcha
        (cursor, resplandor y chispas)."""
        pad = self._pad
        area = pygame.Rect(mx - pad, my - pad, pad * 2, pad * 2)

        # las chispas pueden haberse quedado atras si movieron el mouse rapido
        for e in self.embers:
            area.union_ip(pygame.Rect(int(e[0]) - 8, int(e[1]) - 8, 16, 16))

        area = area.clip(surface.get_rect())

        if area.w <= 0 or area.h <= 0:
            self._under = None
            return

        self._under = surface.subsurface(area).copy()
        self._under_pos = area.topleft

    def clean_copy(self, surface):
        """Copia de la pantalla SIN la antorcha dibujada encima.

        Usar esto (en vez de screen.copy()) para las capturas que se
        congelan en una transicion; si no, la antorcha queda pegada en la
        captura y se ve duplicada junto a la real.
        """
        frame = surface.copy()

        if self._under is not None:
            frame.blit(self._under, self._under_pos)

        return frame

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not pygame.mouse.get_focused():
            self._under = None
            return

        mx, my = pygame.mouse.get_pos()
        self._backup_under(surface, mx, my)
        dt = self._dt()
        self.time += dt

        if self.image is not None:
            self._draw_image(surface, mx, my, dt)
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