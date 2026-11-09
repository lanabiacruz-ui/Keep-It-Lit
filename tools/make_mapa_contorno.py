"""Genera las imagenes con la FORMA del mapa (la que se ve al mantener
click derecho). Salen recortadas justo al borde de la forma, asi quedan
bien centradas en el papel.

  assets/maps/region_01/mapa_contorno.png    1570x1049  (mapa 1)
  assets/maps/region_01/mapa2_contorno.png   1984x1592  (mapa 2)

Las coordenadas del mundo que cubre cada imagen estan en
world/dungeon_map.py (MAP_BOUNDS). Si cambias mapa_colision.png o el
tamaño de mapa2, volve a correr esto y actualiza MAP_BOUNDS.

Uso (desde la raiz del proyecto):  python tools/make_mapa_contorno.py
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

BASE = Path(__file__).resolve().parent.parent
DIR = BASE / "assets" / "maps" / "region_01"

LINE = (226, 201, 150)
SHADOW = (14, 10, 6)
FILL = (58, 46, 26)

LINE_W = 6      # grosor del trazo claro (hacia adentro)
SHADOW_W = 3    # trazo oscuro pegado por dentro


def erode(mask, n):
    """Achica una mascara booleana n px (cruz)."""
    img = Image.fromarray((mask * 255).astype("uint8"))
    return np.array(img.filter(ImageFilter.MinFilter(2 * n + 1))) > 127


def clean(mask):
    """Saca las pelusas del borde de la mascara y suaviza el contorno."""
    img = Image.fromarray((mask * 255).astype("uint8"))
    img = img.filter(ImageFilter.GaussianBlur(3.5))
    m = np.array(img) > 128
    try:
        from scipy import ndimage
        lab, n = ndimage.label(m)
        if n:
            sizes = ndimage.sum(m, lab, range(1, n + 1))
            keep = [i + 1 for i, v in enumerate(sizes) if v > 2000]
            m = np.isin(lab, keep)
    except ImportError:
        pass
    return m


def render(mask):
    h, w = mask.shape
    inner1 = erode(mask, LINE_W)
    inner2 = erode(mask, LINE_W + SHADOW_W)

    out = np.zeros((h, w, 4), dtype="uint8")
    out[mask] = FILL + (70,)
    out[mask & ~inner1] = LINE + (255,)
    out[inner1 & ~inner2] = SHADOW + (200,)

    return Image.fromarray(out, "RGBA")


def main():
    # ---- mapa 1: sale de la mascara de piso
    floor = np.array(Image.open(DIR / "mapa_colision.png").convert("RGBA"))
    mask = clean(floor[..., 3] > 128)
    ys, xs = np.where(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    img = render(mask[y0:y1, x0:x1])
    img.save(DIR / "mapa_contorno.png")
    print("mapa 1:", img.size, "MAP_BOUNDS =", (int(x0), int(y0), int(x1 - x0), int(y1 - y0)))

    # ---- mapa 2: un rectangulo (MAP2_WALKABLE = 8, 8, 1984, 1592)
    w, h = 1984, 1592
    m2 = np.ones((h, w), dtype=bool)
    img2 = render(m2)
    img2.save(DIR / "mapa2_contorno.png")
    print("mapa 2:", img2.size)


if __name__ == "__main__":
    main()