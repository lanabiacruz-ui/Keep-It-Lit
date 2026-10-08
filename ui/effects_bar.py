"""Efectos activos como cubitos arriba al centro de la pantalla.

Cada efecto (aceite, cera, polvora, resina, furia de la vela) aparece
como un cubito. El contenido del cubito se va vaciando de arriba hacia
abajo mientras pasa el tiempo; cuando se acaba, el cubito se desvanece.
Los ultimos segundos parpadea para avisar.

Imagenes (todas opcionales: si falta alguna se dibuja un reemplazo).
TODAS comparten el mismo lienzo de 96x96 px:

  assets/maps/hud/efecto_cubo.png              96x96  (el marco; adentro TRANSPARENTE)
  assets/maps/hud/efecto_relleno_aceite.png    96x96  (lo que se vacia)
  assets/maps/hud/efecto_relleno_cera.png      96x96
  assets/maps/hud/efecto_relleno_polvora.png   96x96
  assets/maps/hud/efecto_relleno_resina.png    96x96
  assets/maps/hud/efecto_relleno_furia.png     96x96
  assets/maps/hud/efecto_relleno_repelente.png 96x96
  assets/maps/hud/efecto_relleno_iman.png      96x96
  assets/maps/hud/efecto_relleno_esfera.png    96x96

El relleno se dibuja DEBAJO del marco y se recorta desde arriba, asi
que tiene que llenar todo el interior del marco (el codigo muestra
solo la parte de abajo que todavia "queda").

La alerta del mosquito tambien va en esta fila: usa la imagen que ya
existe (assets/maps/combate/mosquito_advertencia.png, 96x96), parpadea
mientras haya un mosquito cerca y no se vacia ni lleva marco.
"""

import math
import time
from pathlib import Path

import pygame


HUD_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
)

CANVAS = 96            # lado de los PNG (px)

# Orden en el que se asignan lugares (el primero en aparecer va a la izquierda)
EFFECTS = {
    "aceite":  {"label": "Aceite",  "color": (235, 190, 60)},
    "cera":    {"label": "Cera",    "color": (255, 225, 140)},
    "polvora": {"label": "Polvora", "color": (255, 130, 60)},
    "resina":  {"label": "Resina",  "color": (200, 140, 80)},
    "furia":   {"label": "Furia",   "color": (255, 80, 50)},
    "repelente": {"label": "Repelente", "color": (80, 190, 96)},
    "iman":      {"label": "Iman",      "color": (226, 76, 88)},
    "esfera":    {"label": "Esfera",    "color": (96, 190, 240)},
    # Alerta (no es un efecto con tiempo: parpadea mientras dure el peligro)
    "mosquito": {"label": "Mosquito cerca!", "color": (255, 120, 110),
                 "alert": True},
}

FADE_TIME = 0.35       # cuanto tarda en desvanecerse al terminar
POP_TIME = 0.18        # cuanto tarda en aparecer
SLIDE_SPEED = 12.0     # que tan rapido se acomodan los cubitos
BLINK_BELOW = 0.25     # parpadea cuando queda menos de este % del tiempo
BLINK_RATE = 14.0


def _load(name):

    path = HUD_DIR / name

    if not path.exists():
        return None

    try:
        return pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        return None


def _placeholder_frame():

    surf = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)

    rect = pygame.Rect(4, 4, CANVAS - 8, CANVAS - 8)

    pygame.draw.rect(surf, (45, 30, 22), rect, 6, border_radius=16)
    pygame.draw.rect(surf, (150, 115, 80), rect.inflate(-8, -8), 2, border_radius=12)

    return surf


def _placeholder_fill(color, label):

    surf = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)

    rect = pygame.Rect(8, 8, CANVAS - 16, CANVAS - 16)

    pygame.draw.rect(surf, color, rect, border_radius=12)

    light = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(
        surf, light, (rect.x + 6, rect.y + 6, rect.width - 12, 10),
        border_radius=5
    )

    try:

        font = pygame.font.Font(None, 22)
        text = font.render(label, True, (40, 25, 15))
        surf.blit(text, text.get_rect(center=rect.center))

    except pygame.error:
        pass

    return surf


class EffectsBar:

    def __init__(self, screen_size, scale=0.7, gap=10, top=14):

        w, _ = screen_size

        self.center_x = w // 2
        self.top = top
        self.gap = gap
        self.size = max(8, int(CANVAS * scale))

        def fit(img):

            if img.get_size() == (self.size, self.size):
                return img

            return pygame.transform.smoothscale(img, (self.size, self.size))

        self.frame = fit(_load("efecto_cubo.png") or _placeholder_frame())

        self.fills = {}

        for key, info in EFFECTS.items():

            if info.get("alert"):
                continue

            img = _load(f"efecto_relleno_{key}.png")

            if img is None:
                img = _placeholder_fill(info["color"], info["label"])

            self.fills[key] = fit(img)

        # Fondo oscuro translucido: lo que se ve en la parte ya vaciada
        self.back = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

        pygame.draw.rect(
            self.back, (0, 0, 0, 120),
            self.back.get_rect().inflate(-6, -6),
            border_radius=max(4, self.size // 6)
        )

        # Imagen de la alerta del mosquito (la pasa el juego con
        # set_alert_image; si no se pasa, se dibuja un triangulo)
        self.alert_img = self._fit_alert(None)
        self.alert_font = None

        self._cubes = {}     # key -> estado de cada cubito
        self._order = []     # orden de aparicion
        self._last = None

    # ---------- alerta del mosquito ----------

    def _fit_alert(self, img):

        if img is None:

            img = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)

            pygame.draw.polygon(
                img, (255, 65, 65),
                [(CANVAS // 2, 6), (CANVAS - 6, CANVAS - 10), (6, CANVAS - 10)]
            )

        return pygame.transform.smoothscale(img, (self.size, self.size))

    def set_alert_image(self, img):
        """Imagen de la alerta del mosquito (la misma de siempre)."""

        self.alert_img = self._fit_alert(img)

    # ---------- dibujo ----------

    def draw(self, screen, active):
        """active: {clave: fraccion que queda (0.0 a 1.0)} de los efectos
        que estan corriendo ahora. Los que ya no estan se desvanecen."""

        now = time.monotonic()

        dt = 0.0 if self._last is None else min(0.1, now - self._last)

        self._last = now

        # --- altas y bajas ---
        for key in EFFECTS:

            if key in active:

                cube = self._cubes.get(key)

                if cube is None:

                    cube = {"x": None, "age": 0.0, "gone": 0.0, "frac": 1.0}
                    self._cubes[key] = cube
                    self._order.append(key)

                cube["gone"] = 0.0
                cube["frac"] = max(0.0, min(1.0, active[key]))

            elif key in self._cubes:

                cube = self._cubes[key]
                cube["gone"] += dt
                cube["frac"] = 0.0

                if cube["gone"] >= FADE_TIME:

                    del self._cubes[key]
                    self._order.remove(key)

        if not self._order:
            return

        # --- posiciones: centrados, de a uno al lado del otro ---
        count = len(self._order)
        total = count * self.size + (count - 1) * self.gap
        left = self.center_x - total // 2

        for i, key in enumerate(self._order):

            cube = self._cubes[key]
            cube["age"] += dt

            target = left + i * (self.size + self.gap)

            if cube["x"] is None:
                cube["x"] = float(target)
            else:
                cube["x"] += (target - cube["x"]) * min(1.0, dt * SLIDE_SPEED)

            self._draw_cube(screen, key, cube, now)

    def _draw_alert(self, screen, cube, now):
        """La alerta del mosquito: imagen que late + el texto abajo."""

        pulse = 0.5 + 0.5 * math.sin(now * 8)

        alpha = (0.6 + 0.4 * pulse) * min(1.0, cube["age"] / POP_TIME)

        if cube["gone"] > 0:
            alpha *= max(0.0, 1.0 - cube["gone"] / FADE_TIME)

        img = self.alert_img.copy()
        img.set_alpha(int(255 * alpha))

        x = int(cube["x"])
        y = self.top + int((1.0 - min(1.0, cube["age"] / POP_TIME)) * -10)

        screen.blit(img, (x, y))

        if self.alert_font is None:
            self.alert_font = pygame.font.Font(None, 24)

        text = EFFECTS["mosquito"]["label"]
        color = EFFECTS["mosquito"]["color"]

        shadow = self.alert_font.render(text, True, (0, 0, 0))
        label = self.alert_font.render(text, True, color)

        shadow.set_alpha(int(255 * alpha))
        label.set_alpha(int(255 * alpha))

        pos = label.get_rect(midtop=(x + self.size // 2, y + self.size + 2))

        screen.blit(shadow, pos.move(2, 2))
        screen.blit(label, pos)

    def _draw_cube(self, screen, key, cube, now):

        if key == "mosquito":

            self._draw_alert(screen, cube, now)

            return

        size = self.size
        frac = cube["frac"]

        surf = pygame.Surface((size, size), pygame.SRCALPHA)

        surf.blit(self.back, (0, 0))

        # El relleno se recorta desde arriba: queda solo la parte de abajo
        visible = int(round(frac * size))

        if visible > 0:

            area = pygame.Rect(0, size - visible, size, visible)
            surf.blit(self.fills[key], (0, size - visible), area)

        surf.blit(self.frame, (0, 0))

        # Transparencia: aparece, parpadea al final y se desvanece
        alpha = 1.0

        if cube["gone"] > 0:

            alpha = max(0.0, 1.0 - cube["gone"] / FADE_TIME)

        elif frac < BLINK_BELOW:

            alpha = 0.5 + 0.5 * (0.5 + 0.5 * math.sin(now * BLINK_RATE))

        pop = min(1.0, cube["age"] / POP_TIME)

        alpha *= pop

        surf.set_alpha(int(255 * alpha))

        y = self.top + int((1.0 - pop) * -10)

        screen.blit(surf, (int(cube["x"]), y))