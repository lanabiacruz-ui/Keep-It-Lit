"""Animaciones que aparecen sobre el jugador al usar un objeto.

Como agregar una animacion nueva (sin tocar codigo):

    1. Dibuja una tira horizontal de cuadros (todos del mismo tamano, cuadrados)
    2. Guardala como  assets/maps/usar/uso_<id_del_objeto>.png
       (el id es el de data/items.json: aceite, gelea, pocion_ira, etc.)
    3. Listo. Se detecta sola: cantidad de cuadros = ancho / alto.

Si no existe el archivo del objeto, se usa assets/maps/usar/uso_default.png
(si tampoco existe, simplemente no se muestra nada).

Ajustes opcionales por objeto: tabla USE_ANIM_CFG de abajo.
"""

from pathlib import Path

import pygame

USE_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "usar"
)

# fps: velocidad | size: ancho del cuadro en pixeles del MUNDO (el jugador mide
# 54x74) | dy: desplazamiento vertical (negativo = mas arriba) |
# hold: segundos que se queda el ultimo cuadro
DEFAULT_CFG = {"fps": 14, "size": 72, "dy": -6, "hold": 0.0}

USE_ANIM_CFG = {
    # "aceite": {"fps": 10, "size": 80},
    # "pocion_ira": {"dy": -10, "hold": 0.2},
}

MAX_ACTIVE = 4


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

    def _strip_for(self, item_id):

        if item_id in self._strips:
            return self._strips[item_id]

        strip = None

        for name in (f"uso_{item_id}.png", "uso_default.png"):

            path = USE_DIR / name

            if not path.exists():
                continue

            try:
                strip = _Strip(pygame.image.load(str(path)).convert_alpha())
                break
            except pygame.error:
                strip = None

        self._strips[item_id] = strip
        return strip

    def play(self, item_id):
        """Arranca la animacion de ese objeto. Devuelve True si existe."""

        strip = self._strip_for(item_id)

        if strip is None:
            return False

        cfg = dict(DEFAULT_CFG)
        cfg.update(USE_ANIM_CFG.get(item_id, {}))

        self._active.append({
            "strip": strip,
            "cfg": cfg,
            "t": 0.0,
            "dur": strip.count / cfg["fps"] + cfg["hold"],
        })

        if len(self._active) > MAX_ACTIVE:
            self._active.pop(0)

        return True

    def update(self, dt):

        for a in self._active:
            a["t"] += dt

        self._active = [a for a in self._active if a["t"] < a["dur"]]

    def draw(self, screen, camera, anchor):
        """anchor = (x, y) en coordenadas del mundo (centro del jugador)."""

        z = camera.zoom

        for a in self._active:

            strip = a["strip"]
            cfg = a["cfg"]

            idx = min(strip.count - 1, int(a["t"] * cfg["fps"]))
            px = max(4, int(cfg["size"] * z))

            spr = strip.frame(idx, px)

            sx = int(anchor[0] * z - camera.x)
            sy = int((anchor[1] + cfg["dy"]) * z - camera.y)

            screen.blit(spr, (sx - px // 2, sy - px // 2))
