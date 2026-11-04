"""Genera assets/maps/hud/icon_tacho.png (tacho de basura, pixel art 64x64).

Se dibuja en una grilla de 32x32 y se escala x2 sin suavizar, igual que el
resto de los iconos del HUD. Uso: python tools/make_tacho_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT = (
    Path(__file__).resolve().parent.parent
    / "assets" / "maps" / "hud" / "icon_tacho.png"
)

OUTLINE = (38, 42, 50, 255)
BODY = (122, 130, 140, 255)
BODY_LIGHT = (168, 176, 186, 255)
BODY_DARK = (88, 95, 106, 255)
RIDGE = (98, 105, 116, 255)
LID = (150, 158, 168, 255)
LID_LIGHT = (196, 203, 212, 255)
LID_DARK = (104, 111, 122, 255)
HOLE = (46, 50, 58, 255)


def build():

    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # cuerpo (trapecio) con contorno
    body = [(7, 11), (24, 11), (22, 29), (9, 29)]
    d.polygon(body, fill=OUTLINE)
    inner = [(8, 11), (23, 11), (21, 28), (10, 28)]
    d.polygon(inner, fill=BODY)

    # luz a la izquierda, sombra a la derecha
    d.polygon([(8, 12), (11, 12), (12, 27), (10, 27)], fill=BODY_LIGHT)
    d.polygon([(20, 12), (23, 12), (21, 27), (18, 27)], fill=BODY_DARK)

    # nervaduras verticales
    for x0, x1 in ((14, 14), (16, 16), (18, 18)):
        d.line([(x0, 14), (x1, 26)], fill=RIDGE)

    # aro inferior
    d.line([(10, 26), (21, 26)], fill=BODY_DARK)

    # tapa
    d.rectangle([4, 7, 27, 11], fill=OUTLINE)
    d.rectangle([5, 8, 26, 10], fill=LID)
    d.line([(5, 8), (26, 8)], fill=LID_LIGHT)
    d.line([(5, 10), (26, 10)], fill=LID_DARK)

    # manija
    d.rectangle([12, 3, 19, 7], fill=OUTLINE)
    d.rectangle([13, 4, 18, 6], fill=HOLE)
    d.line([(13, 4), (18, 4)], fill=LID_DARK)

    return im.resize((64, 64), Image.NEAREST)


if __name__ == "__main__":

    build().save(OUT)
    print("guardado", OUT)