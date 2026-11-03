"""Genera la mascara de colision del mapa 1 a partir del dibujo del mapa.

Problema que resuelve: los rectangulos de `walkable` en world/collision.py
quedaron entre 8 y 14 px mas chicos que el piso real, asi que en el borde de
cada sala y a los costados de los pasillos habia "paredes invisibles".

Que hace: parte de esos rectangulos y los hace crecer (hasta MAX_GROW px)
por todo lo que sea piso en el dibujo, frenando en el contorno negro de las
paredes, en la piedra de las paredes y en el exterior oscuro. Despues deja
un margen de seguridad (SAFETY px) para que el jugador no se meta dentro del
borde dibujado.

Uso (desde la raiz del proyecto):

    python tools/make_collision_mask.py

Escribe assets/maps/region_01/mapa_colision.png (alpha 255 = caminable).
Si cambias el dibujo de mapa.png o los rects de collision.py, volve a
correrlo. Solo hace falta para desarrollo: el juego solo lee el PNG.
"""

import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent.parent
MAP_PNG = BASE / "assets" / "maps" / "region_01" / "mapa.png"
OUT_PNG = BASE / "assets" / "maps" / "region_01" / "mapa_colision.png"
COLLISION_PY = BASE / "world" / "collision.py"

MAX_GROW = 16   # cuanto puede crecer un rect hacia el piso real
SAFETY = 1      # margen (px) respecto del contorno de la pared


def read_walkable_rects():
    src = COLLISION_PY.read_text(encoding="utf-8")
    block = re.search(
        r"self\.walkable = \[(.*?)\n        \]", src, re.S
    ).group(1)
    return [
        tuple(int(v) for v in m)
        for m in re.findall(r"Rect\((\d+), (\d+), (\d+), (\d+)\)", block)
    ]


def barrier_mask(rgb):
    r = rgb[..., 0].astype(int)
    g = rgb[..., 1].astype(int)
    b = rgb[..., 2].astype(int)

    outline = (r < 36) & (g < 36) & (b < 36)

    # Piedra de pared: gris-marron parejo. El camino de adoquines de la
    # tienda es mas anaranjado (r - b >= 35), asi que NO cuenta como pared.
    stone = (
        (r >= 90) & (r >= g) & (g >= b)
        & (abs(r - g) < 30) & (b >= 55) & (r - b <= 30)
    )

    outside = (r <= 42) & (g <= 52) & (b <= 42) & ~outline

    return outline | stone | outside


def shift_or(mask):
    out = mask.copy()
    out[1:, :] |= mask[:-1, :]
    out[:-1, :] |= mask[1:, :]
    out[:, 1:] |= mask[:, :-1]
    out[:, :-1] |= mask[:, 1:]
    return out


def shift_and(mask):
    out = mask.copy()
    out[1:, :] &= mask[:-1, :]
    out[:-1, :] &= mask[1:, :]
    out[:, 1:] &= mask[:, :-1]
    out[:, :-1] &= mask[:, 1:]
    # los bordes de la imagen cuentan como pared
    out[0, :] = False
    out[-1, :] = False
    out[:, 0] = False
    out[:, -1] = False
    return out


def build(rgb, rects):
    h, w = rgb.shape[:2]

    original = np.zeros((h, w), bool)
    for x, y, rw, rh in rects:
        original[y:y + rh, x:x + rw] = True

    passable = ~barrier_mask(rgb)

    grown = original.copy()
    for _ in range(MAX_GROW):
        grown = (grown | shift_or(grown)) & (passable | original)

    safe = grown
    for _ in range(SAFETY):
        safe = shift_and(safe)

    return original | safe, original


def main():
    rgb = np.array(Image.open(MAP_PNG).convert("RGB"))
    rects = read_walkable_rects()

    final, original = build(rgb, rects)

    alpha = np.where(final, 255, 0).astype(np.uint8)
    out = np.zeros(final.shape + (4,), np.uint8)
    out[..., 0:3] = 255
    out[..., 3] = alpha

    Image.fromarray(out, "RGBA").save(OUT_PNG)

    print(f"rects: {len(rects)}")
    print(f"px caminables antes: {int(original.sum())}")
    print(f"px caminables ahora: {int(final.sum())}")
    print(f"escrito: {OUT_PNG}")


if __name__ == "__main__":
    sys.exit(main())