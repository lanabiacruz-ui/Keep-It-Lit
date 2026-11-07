"""Genera los 6 iconos de las mejoras del yunque (pixel art 64x64).

Salen en assets/maps/hud/ como yunque_<mejora>.png: resistencia, brasas,
repelente, llama_amplia, llama_larga, manos.
Mismo estilo que el HUD: fondo gris oscuro con el dibujo en grises claros.
Uso: python tools/make_yunque_icons.py
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets" / "maps" / "hud"

S = 64
EDGE = (30, 34, 40, 255)
TILE = (60, 66, 74, 255)
TILE_HI = (84, 91, 100, 255)
DARK = (75, 81, 88, 255)
MID = (143, 155, 161, 255)
LIGHT = (200, 207, 212, 255)
WHITE = (240, 242, 244, 255)


def new():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 62, 62], radius=9, fill=TILE, outline=EDGE, width=2)
    d.line([(6, 3), (57, 3)], fill=TILE_HI, width=1)
    return im, d


def outline(im, color=EDGE, box=(6, 6, 58, 58)):
    """Contorno oscuro alrededor de los pixeles claros del dibujo."""
    px = im.load()
    x0, y0, x1, y1 = box
    marks = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if px[x, y][:3] in (MID[:3], LIGHT[:3], WHITE[:3], DARK[:3]):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if px[nx, ny][:3] in (TILE[:3], TILE_HI[:3]):
                        marks.append((nx, ny))
    for m in marks:
        px[m] = color


def flame(d, cx, top, bottom, w, big=True):
    h = bottom - top
    pts = [
        (cx, top), (cx + w * .30, top + h * .30), (cx + w * .55, top + h * .55),
        (cx + w * .50, top + h * .80), (cx + w * .22, bottom),
        (cx - w * .22, bottom), (cx - w * .50, top + h * .80),
        (cx - w * .55, top + h * .55), (cx - w * .28, top + h * .34),
        (cx - w * .10, top + h * .20),
    ]
    d.polygon(pts, fill=LIGHT)
    inner = [
        (cx, top + h * .38), (cx + w * .28, top + h * .66),
        (cx + w * .16, bottom - 3), (cx - w * .16, bottom - 3),
        (cx - w * .28, top + h * .66),
    ]
    d.polygon(inner, fill=WHITE)


# ---- 1. resistencia: escudo ----
def resistencia():
    im, d = new()
    d.polygon([(32, 8), (52, 14), (52, 32), (44, 46), (32, 56),
               (20, 46), (12, 32), (12, 14)], fill=MID)
    d.polygon([(32, 8), (52, 14), (52, 32), (44, 46), (32, 56)], fill=LIGHT)
    d.polygon([(32, 14), (46, 18), (46, 31), (40, 42), (32, 49),
               (24, 42), (18, 31), (18, 18)], fill=DARK)
    d.rectangle([30, 20, 34, 44], fill=WHITE)
    d.rectangle([23, 27, 41, 31], fill=WHITE)
    outline(im)
    return im


# ---- 2. brasas: llama chica con chispas ----
def brasas():
    im, d = new()
    flame(d, 32, 14, 52, 26)
    for x, y in ((14, 18), (50, 22), (46, 10), (18, 40)):
        d.rectangle([x, y, x + 2, y + 2], fill=WHITE)
    d.rectangle([20, 50, 44, 53], fill=DARK)
    outline(im)
    return im


# ---- 3. repelente: golpe que empuja (flechas hacia afuera) ----
def repelente():
    im, d = new()
    d.rectangle([8, 22, 18, 42], fill=MID)          # el puño
    d.rectangle([8, 22, 12, 42], fill=LIGHT)
    for x in (24, 36, 48):                          # ondas de empuje
        d.polygon([(x, 16), (x + 8, 32), (x, 48), (x + 5, 48),
                   (x + 13, 32), (x + 5, 16)], fill=WHITE if x == 24 else LIGHT if x == 36 else MID)
    outline(im)
    return im


# ---- 4. llama amplia: llama con anillos de luz ----
def llama_amplia():
    im, d = new()
    d.ellipse([6, 6, 57, 57], outline=DARK, width=3)
    d.ellipse([14, 14, 49, 49], outline=MID, width=3)
    flame(d, 32, 20, 44, 16)
    outline(im, box=(14, 14, 50, 50))
    return im


# ---- 5. llama larga: llama alta + barra de duracion ----
def llama_larga():
    im, d = new()
    flame(d, 32, 7, 42, 20)
    d.rectangle([10, 48, 53, 54], fill=DARK)
    d.rectangle([10, 48, 44, 54], fill=LIGHT)
    for x in (18, 26, 34, 42, 50):
        d.line([(x, 47), (x, 49)], fill=WHITE)
    outline(im)
    return im


# ---- 6. manos agiles: mano con chispas ----
def manos():
    im, d = new()
    d.rectangle([19, 46, 45, 55], fill=DARK)
    d.rectangle([19, 28, 45, 48], fill=LIGHT)
    for i, x in enumerate((19, 26, 33, 40)):
        top = 11 + (0 if i in (1, 2) else 5)
        d.rectangle([x, top, x + 4, 32], fill=LIGHT)
        d.rectangle([x + 3, top, x + 4, 32], fill=MID)
    d.polygon([(19, 38), (9, 30), (7, 36), (19, 46)], fill=LIGHT)
    d.rectangle([39, 32, 45, 48], fill=MID)
    for x, y in ((54, 14), (8, 14), (55, 30)):
        d.rectangle([x, y - 2, x + 1, y + 3], fill=WHITE)
        d.rectangle([x - 2, y, x + 3, y + 1], fill=WHITE)
    outline(im)
    d.line([(19, 48), (45, 48)], fill=EDGE)
    return im


ICONS = {
    "resistencia": resistencia, "brasas": brasas, "repelente": repelente,
    "llama_amplia": llama_amplia, "llama_larga": llama_larga, "manos": manos,
}

if __name__ == "__main__":
    out = OUT if OUT.exists() else Path(".")
    for name, fn in ICONS.items():
        fn().save(out / f"yunque_{name}.png")
        print("guardado", out / f"yunque_{name}.png")