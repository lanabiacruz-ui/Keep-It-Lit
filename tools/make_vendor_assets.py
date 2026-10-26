"""Recorta al vendedor del mapa y genera dos imagenes para animarlo:

    assets/maps/tienda/vendedor_cuerpo.png  -> el vendedor solo, con fondo transparente
    assets/maps/tienda/vendedor_fondo.png   -> el mismo recuadro del mapa, pero sin el vendedor
                                               (el pasto tapa el hueco que deja al moverse)

Se corre una sola vez:  python tools/make_vendor_assets.py
Necesita: pip install pillow numpy
"""

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent.parent
MAP = BASE / "assets" / "maps" / "region_01" / "mapa.png"
OUT = BASE / "assets" / "maps" / "tienda"

# Recuadro del mapa (en pixeles del mapa) que contiene al vendedor.
# La ultima fila (y = 98) es la ultima antes del borde negro del mostrador.
BOX = (932, 76, 38, 23)

# Color del pasto, para tapar el hueco que deja el vendedor.
GRASS = (62, 78, 59)


def is_grass(px):
    r, g, b = int(px[0]), int(px[1]), int(px[2])
    return g > r + 10 and g >= b - 2 and r + g + b > 150


def main():
    mapa = Image.open(MAP).convert("RGBA")
    x0, y0, w, h = BOX
    box = mapa.crop((x0, y0, x0 + w, y0 + h))
    arr = np.array(box)

    # 1) Todo el pasto que se pueda alcanzar desde el borde del recuadro
    #    (arriba, izquierda y derecha) es fondo. Lo que no, es el vendedor.
    grass = np.zeros((h, w), bool)
    for y in range(h):
        for x in range(w):
            grass[y, x] = is_grass(arr[y, x])

    reach = np.zeros((h, w), bool)
    q = deque()

    for x in range(w):
        if grass[0, x]:
            q.append((0, x))
    for y in range(h):
        for x in (0, w - 1):
            if grass[y, x]:
                q.append((y, x))

    while q:
        y, x = q.popleft()
        if reach[y, x]:
            continue
        reach[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and grass[ny, nx] and not reach[ny, nx]:
                q.append((ny, nx))

    vendor = ~reach

    # Los bordes suavizados ya cuentan como vendedor (no son pasto), asi que no hace falta agrandar.
    grown = vendor

    cuerpo = arr.copy()
    cuerpo[..., 3] = np.where(grown, 255, 0)

    fondo = arr.copy()
    fondo[grown, 0:3] = GRASS
    fondo[..., 3] = 255

    OUT.mkdir(parents=True, exist_ok=True)

    ys, xs = np.where(grown)
    print("vendedor ocupa x", xs.min(), "-", xs.max(), " y", ys.min(), "-", ys.max(),
          "(dentro del recuadro", BOX, ")")

    Image.fromarray(cuerpo).save(OUT / "vendedor_cuerpo.png")
    Image.fromarray(fondo).save(OUT / "vendedor_fondo.png")
    print("listo ->", OUT)


if __name__ == "__main__":
    main()