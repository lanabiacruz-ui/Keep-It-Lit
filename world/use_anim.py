"""Animaciones que aparecen sobre el jugador al usar un objeto.

Cada objeto tiene su propio efecto, dibujado por codigo en world/use_fx.py
(madera se astilla, el aceite chorrea, la pocion de ira echa llamas, etc.).

Opcional: si preferis dibujar la animacion a mano, hacelo asi y tiene
prioridad sobre el efecto por codigo:

    1. Una tira horizontal de cuadros (todos cuadrados y del mismo tamano,
       MINIMO 2 cuadros; una imagen suelta se ignora)
    2. Guardala como  assets/maps/usar/uso_<id_del_objeto>.png
    3. Cantidad de cuadros = ancho / alto. Se detecta sola.

Ajustes opcionales por objeto: tabla USE_ANIM_CFG de abajo.

OJO con las medidas: el personaje se dibuja con 74 px de alto en PANTALLA
(sin multiplicar por el zoom de la camara; el zoom solo afecta posiciones).
Por eso todos los tamanos de aca estan en pixeles de pantalla.
"""

import math
import random
from pathlib import Path

import pygame

from world.items import load_icon
from world import use_fx

USE_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "usar"
)

# fps: velocidad | size: ancho del cuadro en pixeles de pantalla |
# dy: desplazamiento vertical (negativo = mas arriba) |
# hold: segundos que se queda el ultimo cuadro
DEFAULT_CFG = {"fps": 14, "size": 96, "dy": -4, "hold": 0.0}

USE_ANIM_CFG = {
    # "aceite": {"fps": 10, "size": 110},
}

MAX_ACTIVE = 4

# mitad del alto del sprite del jugador (74 px)
BODY_HALF = 37

# lado de la superficie donde se dibujan los efectos
OVERLAY = 300


def _item_color(item_id):
    """Color dominante (y vivo) del icono del objeto."""

    icon = load_icon(item_id)

    if icon is None:
        return (255, 214, 120)

    small = pygame.transform.smoothscale(icon, (8, 8))

    r = g = b = w = 0.0

    for x in range(8):
        for y in range(8):

            cr, cg, cb, ca = small.get_at((x, y))

            if ca < 40:
                continue

            r += cr * ca
            g += cg * ca
            b += cb * ca
            w += ca

    if w <= 0:
        return (255, 214, 120)

    r, g, b = r / w, g / w, b / w

    top = max(r, g, b, 1.0)
    k = min(2.2, 200.0 / top)

    return (
        int(min(255, r * k)),
        int(min(255, g * k)),
        int(min(255, b * k)),
    )


class _Strip:

    def __init__(self, image):

        h = image.get_height()

        self.frame_w = h
        self.count = max(1, image.get_width() // h)
        self.frames = [
            image.subsurface((i * h, 0, h, h)).copy()
            for i in range(self.count)
        ]
        self.scaled = {}

    def frame(self, idx, px):

        key = (idx, px)
        spr = self.scaled.get(key)

        if spr is None:

            if len(self.scaled) > 120:
                self.scaled.clear()

            spr = pygame.transform.scale(self.frames[idx], (px, px))
            self.scaled[key] = spr

        return spr


class UseAnimManager:

    def __init__(self):

        self._strips = {}
        self._active = []
        self._overlay = None

    # ------------------------------------------------------------------
    def _strip_for(self, item_id):
        """Tira dibujada a mano (solo si tiene 2 cuadros o mas)."""

        if item_id in self._strips:
            return self._strips[item_id]

        strip = None

        for name in (f"uso_{item_id}.png", "uso_default.png"):

            path = USE_DIR / name

            if not path.exists():
                continue

            try:
                cand = _Strip(pygame.image.load(str(path)).convert_alpha())
            except pygame.error:
                continue

            # una imagen suelta no es una animacion: se ignora
            if cand.count < 2:
                continue

            strip = cand
            break

        self._strips[item_id] = strip
        return strip

    def play(self, item_id):
        """Arranca la animacion de ese objeto. Devuelve True si hubo una."""

        strip = self._strip_for(item_id)

        if strip is not None:

            cfg = dict(DEFAULT_CFG)
            cfg.update(USE_ANIM_CFG.get(item_id, {}))

            self._push({
                "strip": strip,
                "cfg": cfg,
                "t": 0.0,
                "dur": strip.count / cfg["fps"] + cfg["hold"],
            })

            return True

        fx = use_fx.EFFECTS.get(item_id)

        if fx is None and load_icon(item_id) is None:
            return False

        self._push({
            "proc": True,
            "item": item_id,
            "fx": fx or use_fx.fx_generico,
            "color": _item_color(item_id),
            "seed": random.randrange(1 << 30),
            "t": 0.0,
            "dur": use_fx.DURATIONS.get(item_id, use_fx.DEFAULT_DURATION),
        })

        return True

    def _push(self, anim):

        self._active.append(anim)

        if len(self._active) > MAX_ACTIVE:
            self._active.pop(0)

    def update(self, dt):

        for a in self._active:
            a["t"] += dt

        self._active = [a for a in self._active if a["t"] < a["dur"]]

    # ------------------------------------------------------------------
    @staticmethod
    def _body_center(camera, anchor):
        """Centro del cuerpo en pantalla. `anchor` es el centro del rect del
        jugador en el mundo; el sprite apoya los pies en la base del rect
        (ya con zoom) y mide BODY_HALF*2 px hacia arriba."""

        cz = camera.zoom

        return (
            int(anchor[0] * cz - camera.x),
            int((anchor[1] + BODY_HALF) * cz - camera.y - BODY_HALF),
        )

    def _draw_icon(self, screen, sx, sy, a):
        """El icono del objeto aparece sobre la cabeza con un rebote."""

        icon = load_icon(a["item"])

        if icon is None:
            return

        k = a["t"] / a["dur"]

        pop = min(1.0, k / 0.18)

        scale = 0.4 + 0.6 * (1.0 - (1.0 - pop) ** 3) + 0.18 * math.sin(pop * math.pi)

        size = max(6, int(30 * scale))

        rise = 58 + 22 * (1.0 - (1.0 - min(1.0, k * 1.3)) ** 2)

        fade = 1.0 if k < 0.6 else max(0.0, 1.0 - (k - 0.6) / 0.4)

        pos = (sx, int(sy - rise))

        use_fx._glow(screen, pos[0], pos[1], 24, a["color"], 120 * fade)

        spr = pygame.transform.smoothscale(icon, (size, size))

        wob = 10.0 * math.sin(k * 14.0) * (1.0 - k)

        if abs(wob) > 0.5:
            spr = pygame.transform.rotate(spr, wob)

        spr.set_alpha(int(255 * fade))

        screen.blit(spr, spr.get_rect(center=pos))

    def _draw_proc(self, screen, camera, anchor, a):

        sx, sy = self._body_center(camera, anchor)

        if self._overlay is None:
            self._overlay = pygame.Surface((OVERLAY, OVERLAY), pygame.SRCALPHA)

        ov = self._overlay
        ov.fill((0, 0, 0, 0))

        mid = OVERLAY // 2

        a["fx"](ov, (mid, mid), a["t"], a["t"] / a["dur"], a["seed"], a["color"])

        screen.blit(ov, (sx - mid, sy - mid))

        self._draw_icon(screen, sx, sy, a)

    def draw(self, screen, camera, anchor):
        """anchor = (x, y) en coordenadas del mundo (centro del jugador)."""

        for a in self._active:

            if a.get("proc"):
                self._draw_proc(screen, camera, anchor, a)
                continue

            strip = a["strip"]
            cfg = a["cfg"]

            idx = min(strip.count - 1, int(a["t"] * cfg["fps"]))
            px = max(4, int(cfg["size"]))

            spr = strip.frame(idx, px)

            sx, sy = self._body_center(camera, anchor)

            screen.blit(spr, (sx - px // 2, sy + cfg["dy"] - px // 2))