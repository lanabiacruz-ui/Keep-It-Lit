"""Genera el arte de la hotbar (assets/maps/hud/).

    hud_pociones.png   panel violeta de los 2 marcos de pociones (236x120)

Uso:  python tools/make_hud_art.py      (necesita Pillow)

Todo se dibuja con contorno "a mano" (con un poquito de temblor) para que
combine con el resto del arte del juego.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HUD = Path(__file__).resolve().parent.parent / "assets" / "maps" / "hud"

SS = 4   # supersampling


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------

def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def wobbly_rrect(x0, y0, x1, y1, radius, amp, seed, step=3.0):
    """Puntos de un rectangulo redondeado con un temblor suave en el borde."""

    rnd = random.Random(seed)

    r = radius
    pts = []

    # esquinas: (centro, angulo inicial)
    corners = [
        (x1 - r, y0 + r, -90),
        (x1 - r, y1 - r, 0),
        (x0 + r, y1 - r, 90),
        (x0 + r, y0 + r, 180),
    ]

    for cx, cy, a0 in corners:

        n = max(6, int(r * math.pi / 2 / step))

        for k in range(n + 1):

            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    # remuestrear para que el temblor sea parejo
    dense = []

    for i, p in enumerate(pts):

        q = pts[(i + 1) % len(pts)]
        d = math.hypot(q[0] - p[0], q[1] - p[1])
        n = max(1, int(d / step))

        for k in range(n):

            t = k / n
            dense.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))

    count = len(dense)

    ph = [rnd.uniform(0, math.tau) for _ in range(3)]
    fr = [rnd.uniform(2.0, 3.5), rnd.uniform(5.0, 8.0), rnd.uniform(11, 16)]
    am = [amp, amp * 0.55, amp * 0.3]

    out = []

    for i, p in enumerate(dense):

        a = dense[(i - 1) % count]
        b = dense[(i + 1) % count]

        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0

        nx, ny = ty / ln, -tx / ln

        t = i / count * math.tau

        off = sum(am[k] * math.sin(fr[k] * t + ph[k]) for k in range(3))

        out.append((p[0] + nx * off, p[1] + ny * off))

    return out


def gradient(size, top, bottom):

    w, h = size
    img = Image.new("RGBA", size)
    px = img.load()

    for y in range(h):

        c = lerp(top, bottom, y / max(1, h - 1))

        for x in range(w):
            px[x, y] = rgba(c)

    return img


def poly_mask(size, pts):

    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)

    return m


def stroke(img, pts, color, width):

    d = ImageDraw.Draw(img)
    closed = list(pts) + [pts[0], pts[1]]

    d.line(closed, fill=color, width=int(width), joint="curve")

    # puntas redondeadas
    r = width / 2

    for x, y in pts[::2]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)


def plate(size, box, radius, top, bottom, outline, hi, lo, seed, amp=1.0,
          outline_w=3.0):
    """Placa con contorno, relleno degradado y bisel (luz arriba, sombra abajo).

    size / box en pixeles finales; se dibuja a SS veces y se baja al final.
    """

    W, H = size[0] * SS, size[1] * SS
    x0, y0, x1, y1 = [v * SS for v in box]

    outer = wobbly_rrect(x0, y0, x1, y1, radius * SS, amp * SS, seed)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    fill = gradient((W, H), top, bottom)
    layer.paste(fill, (0, 0), poly_mask((W, H), outer))

    # bisel: borde interior claro arriba / oscuro abajo
    inset = 3.2 * SS
    inner = wobbly_rrect(
        x0 + inset, y0 + inset, x1 - inset, y1 - inset,
        max(2, radius * SS - inset), amp * SS * 0.5, seed + 7
    )

    hi_l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    stroke(hi_l, inner, rgba(hi, 200), 1.6 * SS)

    lo_l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    stroke(lo_l, inner, rgba(lo, 190), 1.6 * SS)

    mid = (y0 + y1) / 2

    # mascara con transicion suave (sin escalon en el medio)
    top_m = Image.new("L", (W, H), 0)
    tp = top_m.load()
    span = (y1 - y0) * 0.35

    for yy in range(H):

        v = max(0.0, min(1.0, 0.5 + (mid - yy) / span))
        row = int(255 * v)

        for xx in range(W):
            tp[xx, yy] = row

    bot_m = ImageChops.invert(top_m)

    layer.paste(hi_l, (0, 0), ImageChops.multiply(top_m, hi_l.getchannel("A")))
    layer.paste(lo_l, (0, 0), ImageChops.multiply(bot_m, lo_l.getchannel("A")))

    stroke(layer, outer, rgba(outline), outline_w * SS)

    return layer, outer


def finish(layer, size):

    return layer.resize(size, Image.LANCZOS)


def glow(size, pts, color, blur, alpha):
    """Resplandor suave alrededor de una forma (a escala SS)."""

    W, H = size[0] * SS, size[1] * SS

    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    stroke(g, pts, rgba(color, alpha), 6 * SS)

    return g.filter(ImageFilter.GaussianBlur(blur * SS))


def stud(layer, cx, cy, r, base, light, dark):
    """Remache (tachuela) chiquito."""

    d = ImageDraw.Draw(layer)
    cx, cy, r = cx * SS, cy * SS, r * SS

    d.ellipse([cx - r, cy - r, cx + r, cy + r],
              fill=rgba(dark))
    d.ellipse([cx - r * 0.85, cy - r * 0.85, cx + r * 0.85, cy + r * 0.85],
              fill=rgba(base))
    d.ellipse([cx - r * 0.5, cy - r * 0.6, cx + r * 0.05, cy - r * 0.1],
              fill=rgba(light))


def gem(layer, cx, cy, w, h, base, light, dark, outline):
    """Gemita en forma de rombo."""

    d = ImageDraw.Draw(layer)

    cx, cy, w, h = cx * SS, cy * SS, w * SS, h * SS

    pts = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2),
           (cx - w / 2, cy)]

    d.polygon(pts, fill=rgba(base), outline=rgba(outline), width=SS)
    d.polygon([pts[0], pts[1], (cx, cy)], fill=rgba(light))
    d.polygon([pts[3], pts[2], (cx, cy)], fill=rgba(dark))
    d.line(pts + [pts[0]], fill=rgba(outline), width=int(1.4 * SS))


# ---------------------------------------------------------------------------
# paleta
# ---------------------------------------------------------------------------

SLATE_TOP = (74, 84, 100)
SLATE_BOT = (44, 51, 64)
SLATE_OUT = (18, 22, 30)
SLATE_HI = (150, 164, 184)
SLATE_LO = (22, 27, 36)

AMBER = (255, 196, 84)
AMBER_DK = (176, 112, 36)
AMBER_LT = (255, 232, 160)

VIO_TOP = (92, 66, 140)
VIO_BOT = (52, 34, 86)
VIO_OUT = (26, 14, 46)
VIO_HI = (190, 160, 245)
VIO_LO = (30, 16, 56)

VIO_GLOW = (200, 150, 255)


# ---------------------------------------------------------------------------
# piezas
# ---------------------------------------------------------------------------

def make_bar():
    """450x120 -> se muestra a 270x72, justo el ancho de 4 casilleros."""

    size = (450, 120)

    layer, outer = plate(
        size, (3, 4, 447, 116), 20, SLATE_TOP, SLATE_BOT,
        SLATE_OUT, SLATE_HI, SLATE_LO, seed=11, amp=0.9, outline_w=3.2
    )

    # filete dorado fino, pegado al borde (enmarca los casilleros)
    trim = wobbly_rrect(
        8 * SS, 9 * SS, 442 * SS, 111 * SS, 15 * SS, 0.5 * SS, 23
    )
    stroke(layer, trim, rgba(AMBER_DK, 235), 1.7 * SS)
    stroke(layer, trim, rgba(AMBER, 170), 0.8 * SS)

    # remaches en las cuatro esquinas
    for cx, cy in ((17, 18), (433, 18), (17, 102), (433, 102)):
        stud(layer, cx, cy, 3.6, (200, 140, 60), AMBER_LT, (70, 40, 14))

    # gemas de brasa entre casilleros (arriba y abajo, en el centro)
    for cy in (9, 111):
        gem(layer, 225, cy, 14, 11, AMBER, AMBER_LT, AMBER_DK, (60, 34, 10))

    # brillo suave arriba
    shine = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(shine).rounded_rectangle(
        [30 * SS, 14 * SS, 420 * SS, 20 * SS], radius=3 * SS,
        fill=(255, 255, 255, 36)
    )
    layer = Image.alpha_composite(layer, shine.filter(
        ImageFilter.GaussianBlur(1.5 * SS)))

    return finish(layer, size)


def flask_mark(layer, color, alpha):
    """Marca de agua de un frasco en el casillero de pocion vacio."""

    d = ImageDraw.Draw(layer)
    c = rgba(color, alpha)

    def S(v):
        return int(round(v * SS))

    w = int(round(2.2 * SS))

    d.ellipse([S(34), S(46), S(66), S(78)], outline=c, width=w)
    d.rectangle([S(46), S(30), S(54), S(50)], outline=c, width=w)
    d.rectangle([S(43), S(26), S(57), S(32)], outline=c, width=w)
    d.arc([S(39), S(61), S(61), S(75)], 20, 160, fill=c, width=w)


def make_slot(violet=False, selected=False):
    """Casillero hundido 100x100 (se muestra a 60x60)."""

    size = (100, 100)

    if violet:
        top, bot, out, hi, lo = VIO_BOT, VIO_TOP, VIO_OUT, VIO_HI, VIO_LO
        gl, edge = VIO_GLOW, (222, 190, 255)
    else:
        top, bot, out, hi, lo = (34, 40, 52), (66, 76, 92), SLATE_OUT, \
            (120, 134, 156), (14, 18, 26)
        gl, edge = AMBER, AMBER_LT

    # el casillero se ve "hundido": oscuro arriba, mas claro abajo
    layer, outer = plate(
        size, (7, 7, 93, 93), 15, top, bot, out, lo, hi,
        seed=(5 if violet else 3), amp=0.8, outline_w=3.6
    )

    # sombra interior
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [12 * SS, 12 * SS, 88 * SS, 30 * SS], radius=8 * SS,
        fill=(0, 0, 0, 70)
    )
    layer = Image.alpha_composite(layer, sh.filter(
        ImageFilter.GaussianBlur(3 * SS)))

    if violet:
        flask_mark(layer, (210, 170, 255), 70)

    if selected:

        g = glow(size, outer, gl, 3.2, 230)
        base = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        base = Image.alpha_composite(base, g)
        layer = Image.alpha_composite(base, layer)

        ring = wobbly_rrect(
            5.2 * SS, 5.2 * SS, 94.8 * SS, 94.8 * SS, 17 * SS, 0.8 * SS, 41
        )
        stroke(layer, ring, rgba(gl), 3.4 * SS)
        stroke(layer, ring, rgba(edge, 200), 1.2 * SS)

        # relleno apenas mas claro
        warm = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(warm).rounded_rectangle(
            [13 * SS, 13 * SS, 87 * SS, 87 * SS], radius=11 * SS,
            fill=rgba(gl, 20)
        )
        layer = Image.alpha_composite(layer, warm)

    return finish(layer, size)


def make_potion_panel():
    """Panel violeta que va detras de los 2 marcos de pociones."""

    size = (236, 120)

    layer, outer = plate(
        size, (3, 4, 233, 116), 20, VIO_TOP, VIO_BOT,
        VIO_OUT, VIO_HI, VIO_LO, seed=29, amp=0.9, outline_w=3.2
    )

    trim = wobbly_rrect(
        8 * SS, 9 * SS, 228 * SS, 111 * SS, 15 * SS, 0.5 * SS, 31
    )
    stroke(layer, trim, rgba((120, 80, 190), 235), 1.7 * SS)
    stroke(layer, trim, rgba((214, 170, 255), 180), 0.8 * SS)

    for cx, cy in ((17, 18), (219, 18), (17, 102), (219, 102)):
        stud(layer, cx, cy, 3.4, (150, 110, 215), (235, 215, 255),
             (40, 22, 70))

    for cy in (9, 111):
        gem(layer, 118, cy, 14, 11, (190, 140, 255), (236, 214, 255),
            (112, 70, 190), (36, 18, 64))

    shine = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(shine).rounded_rectangle(
        [30 * SS, 14 * SS, 206 * SS, 20 * SS], radius=3 * SS,
        fill=(255, 255, 255, 40)
    )
    layer = Image.alpha_composite(layer, shine.filter(
        ImageFilter.GaussianBlur(1.5 * SS)))

    return finish(layer, size)


def main():

    HUD.mkdir(parents=True, exist_ok=True)

    img = make_potion_panel()
    img.save(HUD / "hud_pociones.png")

    print("ok hud_pociones.png", img.size)


if __name__ == "__main__":
    main()