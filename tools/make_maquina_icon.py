"""Genera assets/maps/hud/icon_maquina.png (mini maquina industrial, 64x64).

Es la maquina que convierte geleas en monedas de gelea. Se dibuja en una
grilla de 32x32 y se escala x2 sin suavizar, igual que icon_tacho.png.
Uso: python tools/make_maquina_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT = (
    Path(__file__).resolve().parent.parent
    / "assets" / "maps" / "hud" / "icon_maquina.png"
)

OUTLINE = (38, 42, 50, 255)
BODY = (122, 130, 140, 255)
BODY_LIGHT = (168, 176, 186, 255)
BODY_DARK = (88, 95, 106, 255)
PANEL = (60, 66, 74, 255)
PANEL_LIGHT = (84, 91, 100, 255)
METAL = (196, 203, 212, 255)
HOLE = (30, 33, 39, 255)
GEL = (196, 160, 118, 255)
GEL_LIGHT = (226, 196, 158, 255)
GEL_DARK = (140, 108, 74, 255)


def box(d, x0, y0, x1, y1, fill, light=None, dark=None):
    """Rectangulo con contorno oscuro y luz arriba/izquierda."""

    d.rectangle([x0, y0, x1, y1], fill=OUTLINE)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=fill)

    if light:
        d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=light)
        d.line([(x0 + 1, y0 + 1), (x0 + 1, y1 - 1)], fill=light)

    if dark:
        d.line([(x0 + 1, y1 - 1), (x1 - 1, y1 - 1)], fill=dark)
        d.line([(x1 - 1, y0 + 1), (x1 - 1, y1 - 1)], fill=dark)


def build():

    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # chimenea (atras a la derecha)
    box(d, 21, 2, 25, 11, BODY_DARK, BODY)
    box(d, 20, 1, 26, 3, BODY, BODY_LIGHT, BODY_DARK)
    d.rectangle([21, 2, 25, 2], fill=HOLE)

    # tolva (embudo) donde entra la gelea
    d.polygon([(4, 4), (17, 4), (14, 12), (7, 12)], fill=OUTLINE)
    d.polygon([(5, 5), (16, 5), (13, 11), (8, 11)], fill=BODY)
    d.line([(5, 5), (16, 5)], fill=BODY_LIGHT)
    d.line([(5, 6), (7, 10)], fill=BODY_LIGHT)
    d.line([(16, 6), (13, 10)], fill=BODY_DARK)

    # gelea asomando en la tolva
    d.ellipse([7, 3, 13, 7], fill=GEL_DARK)
    d.ellipse([8, 3, 12, 6], fill=GEL)
    d.point([(9, 4), (10, 4)], fill=GEL_LIGHT)

    # cuerpo principal
    box(d, 3, 12, 28, 25, BODY, BODY_LIGHT, BODY_DARK)

    # remaches
    for x, y in ((5, 14), (26, 14), (5, 23), (26, 23)):
        d.point((x, y), fill=BODY_DARK)

    # panel oscuro con medidor
    box(d, 6, 15, 15, 22, PANEL, PANEL_LIGHT)
    d.line([(8, 20), (13, 20)], fill=BODY_DARK)
    d.arc([8, 16, 13, 21], 180, 360, fill=METAL)
    d.line([(10, 19), (12, 17)], fill=METAL)

    # engranaje (derecha del panel)
    d.ellipse([18, 15, 25, 22], fill=OUTLINE)
    d.ellipse([19, 16, 24, 21], fill=METAL)
    d.ellipse([21, 18, 22, 19], fill=HOLE)
    for x, y in ((21, 14), (21, 23), (17, 18), (26, 18)):
        d.point((x, y), fill=OUTLINE)

    # patas
    d.rectangle([5, 26, 8, 28], fill=OUTLINE)
    d.rectangle([23, 26, 26, 28], fill=OUTLINE)
    d.rectangle([6, 26, 7, 27], fill=BODY_DARK)
    d.rectangle([24, 26, 25, 27], fill=BODY_DARK)

    # bandeja de salida con una moneda de gelea
    box(d, 10, 25, 21, 29, BODY_DARK, BODY)
    d.rectangle([11, 26, 20, 27], fill=HOLE)
    d.ellipse([13, 25, 18, 29], fill=GEL_DARK)
    d.ellipse([14, 25, 17, 28], fill=GEL)
    d.point((15, 26), fill=GEL_LIGHT)

    return im.resize((64, 64), Image.NEAREST)


if __name__ == "__main__":

    build().save(OUT)
    print("guardado", OUT)