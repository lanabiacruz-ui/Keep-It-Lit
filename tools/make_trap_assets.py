"""Dibuja las imagenes de las trampas de la Zona 2 (Stonun).

Genera en assets/maps/combate/:
    trampa.png          trampa armada (mandibulas abiertas, placa roja)
    trampa_activa.png   trampa cerrada sobre el jugador
    trampa_usada.png    trampa gastada (oxidada, rota)

Cada imagen es de 96x64 px y en el juego se dibuja a 24x16 px del mundo
(zoom x4), igual que el resto de los sprites.

Uso (desde la raiz del proyecto):  python tools/make_trap_assets.py
Solo hace falta para desarrollo: el juego lee los PNG.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets" / "maps" / "combate"

S = 4                       # supersampling
W, H = 96, 64
CX, CY = 48 * S, 36 * S
OUTLINE = (20, 17, 15, 255)


def ell(d, cx, cy, rx, ry, fill, width=0, outline=OUTLINE):
    d.ellipse(
        (cx - rx, cy - ry, cx + rx, cy + ry),
        fill=fill, outline=outline if width else None, width=width,
    )


def tooth(d, cx, cy, rx, ry, ang, size, fill, point_in=True):
    """Diente triangular sobre el borde de una elipse, apuntando al centro."""

    px = cx + math.cos(ang) * rx
    py = cy + math.sin(ang) * ry

    nx = -math.cos(ang) * (1 if point_in else -1)
    ny = -math.sin(ang) * (1 if point_in else -1)

    # tangente
    tx, ty = -math.sin(ang), math.cos(ang)

    half = size * 0.55

    tip = (px + nx * size, py + ny * size * 0.75)
    a = (px + tx * half, py + ty * half * 0.8)
    b = (px - tx * half, py - ty * half * 0.8)

    d.polygon([a, tip, b], fill=fill, outline=OUTLINE, width=S * 1)


def base(d, metal, rim, shadow_alpha=95):

    # sombra
    sh = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    ell(sd, CX, CY + 16 * S // 4, 41 * S, 20 * S, (0, 0, 0, shadow_alpha))
    d._image.alpha_composite(sh)

    # grosor (borde de abajo)
    ell(d, CX, CY + 5 * S, 40 * S, 19 * S, rim, width=3 * S)
    # chapa
    ell(d, CX, CY, 40 * S, 19 * S, metal, width=3 * S)


def make_armed():

    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d._image = img

    base(d, (88, 91, 99, 255), (46, 47, 53, 255))

    # aro interior
    ell(d, CX, CY, 33 * S, 14 * S, (58, 60, 66, 255), width=2 * S)

    # dientes de las mandibulas (apuntan al centro)
    n = 16
    for i in range(n):
        ang = 2 * math.pi * i / n + math.pi / n
        tooth(d, CX, CY, 31 * S, 12.5 * S, ang, 9 * S, (214, 214, 206, 255))

    # placa de presion
    ell(d, CX, CY + 1 * S, 15 * S, 6.5 * S, (150, 48, 30, 255), width=2 * S)
    ell(d, CX - 2 * S, CY - 0.5 * S, 10 * S, 3.6 * S, (226, 98, 58, 255))
    ell(d, CX - 5 * S, CY - 1.5 * S, 3.5 * S, 1.3 * S, (255, 170, 120, 255))

    # remaches
    for sx in (-35, 35):
        ell(d, CX + sx * S, CY + 2 * S, 2.2 * S, 1.8 * S,
            (160, 164, 172, 255), width=S)

    # brillo del borde
    d.arc((CX - 37 * S, CY - 17 * S, CX + 37 * S, CY + 17 * S),
          200, 250, fill=(176, 180, 190, 255), width=2 * S)

    return img


def make_active():

    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d._image = img

    # resplandor rojo: esta mordiendo
    glow = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    ell(gd, CX, CY, 46 * S, 24 * S, (255, 60, 30, 70))
    ell(gd, CX, CY, 42 * S, 21 * S, (255, 90, 40, 70))
    img.alpha_composite(glow)

    base(d, (88, 91, 99, 255), (46, 47, 53, 255), shadow_alpha=70)

    ell(d, CX, CY, 33 * S, 14 * S, (58, 60, 66, 255), width=2 * S)

    # mandibula de arriba y de abajo, cerradas
    top = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    td = ImageDraw.Draw(top)
    td._image = top
    ell(td, CX, CY, 33 * S, 14 * S, (112, 116, 124, 255), width=2 * S)
    # cortar la mitad de abajo
    mask = Image.new("L", (W * S, H * S), 0)
    ImageDraw.Draw(mask).rectangle((0, 0, W * S, CY), fill=255)
    top_half = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    top_half.paste(top, (0, 0), mask)
    img.alpha_composite(top_half)

    bot = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bot)
    bd._image = bot
    ell(bd, CX, CY, 33 * S, 14 * S, (96, 100, 108, 255), width=2 * S)
    mask2 = Image.new("L", (W * S, H * S), 0)
    ImageDraw.Draw(mask2).rectangle((0, CY, W * S, H * S), fill=255)
    bot_half = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    bot_half.paste(bot, (0, 0), mask2)
    img.alpha_composite(bot_half)

    # dientes entrelazados sobre la costura
    d = ImageDraw.Draw(img)
    d._image = img
    d.line((CX - 32 * S, CY, CX + 32 * S, CY), fill=OUTLINE, width=2 * S)

    k = 9
    for i in range(k):
        x = CX + (-28 + i * 7) * S
        up = i % 2 == 0
        h = 8 * S
        if up:
            pts = [(x - 3.3 * S, CY), (x, CY - h), (x + 3.3 * S, CY)]
        else:
            pts = [(x - 3.3 * S, CY), (x, CY + h * 0.8), (x + 3.3 * S, CY)]
        d.polygon(pts, fill=(222, 222, 214, 255), outline=OUTLINE, width=S)

    d.arc((CX - 31 * S, CY - 13 * S, CX + 31 * S, CY + 13 * S),
          200, 250, fill=(190, 194, 204, 255), width=2 * S)

    return img


def make_used():

    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d._image = img

    base(d, (78, 66, 60, 255), (44, 38, 36, 255), shadow_alpha=60)

    ell(d, CX, CY, 33 * S, 14 * S, (54, 46, 43, 255), width=2 * S)

    # dientes rotos / mas cortos y oxidados
    n = 16
    for i in range(n):
        if i % 3 == 1:
            continue
        ang = 2 * math.pi * i / n + math.pi / n
        tooth(d, CX, CY, 31 * S, 12.5 * S, ang, 5 * S, (132, 112, 98, 255))

    # placa hundida y apagada
    ell(d, CX, CY + 1 * S, 15 * S, 6.5 * S, (62, 40, 36, 255), width=2 * S)
    ell(d, CX - 1 * S, CY, 10 * S, 3.6 * S, (88, 58, 50, 255))

    # grieta
    d.line([(CX - 9 * S, CY - 3 * S), (CX - 3 * S, CY + 1 * S),
            (CX - 1 * S, CY - 2 * S), (CX + 6 * S, CY + 3 * S)],
           fill=OUTLINE, width=int(1.3 * S))

    for sx in (-35, 35):
        ell(d, CX + sx * S, CY + 2 * S, 2.2 * S, 1.8 * S,
            (110, 92, 82, 255), width=S)

    # se ve gastada
    alpha = img.getchannel("A").point(lambda a: int(a * 0.82))
    img.putalpha(alpha)

    return img


def save(img, name):

    out = img.resize((W, H), Image.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    out.save(OUT / name)
    print("escrito", OUT / name)


def main():

    save(make_armed(), "trampa.png")
    save(make_active(), "trampa_activa.png")
    save(make_used(), "trampa_usada.png")


if __name__ == "__main__":
    main()