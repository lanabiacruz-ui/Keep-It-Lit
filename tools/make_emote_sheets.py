"""Genera las imagenes de la rueda de emotes (assets/maps/hud/).

Uso (desde la carpeta del proyecto):

    python tools/make_emote_wheel.py

Crea:
    emotes_panel.png        panel completo con las 3 tarjetas (normal)
    emotes_card_hover.png   tarjeta resaltada (el juego la pega encima al pasar el mouse)

Los poses salen de los cuadros del skin "clasico". Si queres cambiar el
dibujo, edita este script o reemplaza los png con los tuyos manteniendo
las medidas (el juego lee las posiciones de las tarjetas de CARDS).
Requiere Pillow.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
HUD = ROOT / "assets" / "maps" / "hud"
PLAYER = ROOT / "assets" / "maps" / "player"

# --- colores sacados del menu de pausa y del hud ------------------------------
PANEL = (99, 108, 121)
PANEL_DARK = (78, 86, 99)
OUTLINE = (52, 58, 70)
BUTTON = (141, 148, 158)
BUTTON_LIGHT = (160, 167, 177)
WHITE = (250, 250, 252)
FLAME = (255, 168, 54)
FLAME_HOT = (255, 214, 110)
INK = (44, 50, 62)

W, H = 1000, 560
SS = 3  # supersampling

# tarjetas: (x, y, ancho, alto) en pixeles de la imagen final
CARD_W, CARD_H = 252, 330
CARD_Y = 138
CARD_GAP = 38
_total = CARD_W * 3 + CARD_GAP * 2
CARD_X0 = (W - _total) // 2
CARDS = [
    (CARD_X0 + i * (CARD_W + CARD_GAP), CARD_Y, CARD_W, CARD_H)
    for i in range(3)
]

EMOTES = [
    ("Six Seven", "emote_six_seven.png", 10),
    ("Dab", "emote_dab.png", 8),
    ("Saludo", "emote_saludo.png", 10),
]


def font(size, bold=True):
    name = "Poppins-Bold.ttf" if bold else "Poppins-Medium.ttf"
    for base in (
        "/usr/share/fonts/truetype/google-fonts/",
        "/usr/share/fonts/truetype/dejavu/",
    ):
        try:
            return ImageFont.truetype(base + name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wobble_rect(box, radius, seed, amp=2.2):
    """Poligono de rectangulo redondeado con borde 'dibujado a mano'."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    pts = []
    corners = [
        (x1 - radius, y0 + radius, -90),
        (x1 - radius, y1 - radius, 0),
        (x0 + radius, y1 - radius, 90),
        (x0 + radius, y0 + radius, 180),
    ]
    for cx, cy, start in corners:
        for k in range(11):
            a = math.radians(start + 90 * k / 10)
            r = radius + rnd.uniform(-amp, amp) * 0.5
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    # mini ondulacion en los lados
    out = []
    n = len(pts)
    for i, (px, py) in enumerate(pts):
        out.append((px + rnd.uniform(-amp, amp) * 0.4,
                    py + rnd.uniform(-amp, amp) * 0.4))
    return out


def draw_blob(img, box, fill, outline, width, radius, seed):
    s = SS
    x0, y0, x1, y1 = box
    pad = 8
    lw, lh = int(x1 - x0) + pad * 2, int(y1 - y0) + pad * 2
    layer = Image.new("RGBA", (lw * s, lh * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    local = (pad * s, pad * s, (pad + x1 - x0) * s, (pad + y1 - y0) * s)
    pts = wobble_rect(local, radius * s, seed, amp=2.4 * s)
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=outline, width=int(width * s), joint="curve")
    layer = layer.resize((lw, lh), Image.LANCZOS)
    img.alpha_composite(layer, (int(x0) - pad, int(y0) - pad))


def shadow(img, box, radius, blur=14, alpha=110, offset=(0, 8)):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(
        (x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]),
        radius, fill=(10, 12, 18, alpha),
    )
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)


def text_center(img, text, cx, cy, fnt, fill, stroke=None, stroke_w=0):
    d = ImageDraw.Draw(img)
    d.text((cx, cy), text, font=fnt, fill=fill, anchor="mm",
           stroke_width=stroke_w, stroke_fill=stroke)


def flame(img, cx, cy, h, glow=True):
    """Llamita (la luz del juego) dibujada con poligonos suaves."""
    if glow:
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        r = h * 0.9
        gd.ellipse((cx - r, cy - r * 0.8, cx + r, cy + r * 1.0),
                   fill=(255, 150, 40, 120))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(h * 0.5)))

    s = 4
    w = int(h * 0.8)
    tile = Image.new("RGBA", (w * s, h * 2 * s // 1), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    tw, th = tile.size

    def drop(scale, color):
        pts = []
        for i in range(0, 101):
            t = i / 100
            a = t * 2 * math.pi
            x = math.sin(a) * (1 - math.cos(a) * 0.0)
            # forma de gota con punta arriba
            y = -math.cos(a)
            wx = math.sin(a) * (0.5 - 0.5 * y) ** 0.9
            pts.append((wx, y))
        out = []
        for wx, y in pts:
            px = tw / 2 + wx * tw * 0.46 * scale
            py = th * 0.55 - y * th * 0.42 * scale + (th * 0.05 * scale)
            out.append((px, py))
        d.polygon(out, fill=color)

    drop(1.0, OUTLINE + (255,))
    drop(0.86, FLAME + (255,))
    drop(0.52, FLAME_HOT + (255,))
    tile = tile.resize((tw // s, th // s), Image.LANCZOS)
    img.alpha_composite(tile, (int(cx - tile.width / 2), int(cy - tile.height / 2)))


def sparkle(img, cx, cy, r, color):
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.32
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=color)


def frame(path, idx):
    im = Image.open(PLAYER / path).convert("RGBA")
    c, r = idx % 8, idx // 8
    cell = im.crop((c * 266, r * 266, c * 266 + 266, r * 266 + 266))
    bbox = cell.getbbox()
    return cell.crop(bbox)


def draw_card(card_img, hover):
    """Dibuja una tarjeta (sin personaje ni texto) en un lienzo del tamaño de la tarjeta."""
    pad = 24
    w, h = CARD_W, CARD_H
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))

    if hover:
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.rounded_rectangle((pad - 6, pad - 6, pad + w + 6, pad + h + 6), 40,
                             fill=(255, 168, 54, 190))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))

    shadow(img, (pad, pad, pad + w, pad + h), 34, blur=8, alpha=90, offset=(0, 6))

    body = BUTTON_LIGHT if hover else BUTTON
    draw_blob(img, (pad, pad, pad + w, pad + h), body, OUTLINE, 5, 32, 11)

    # ventana del personaje
    win = (pad + 22, pad + 22, pad + w - 22, pad + 22 + 196)
    win_fill = (118, 126, 140) if not hover else (255, 226, 160)
    draw_blob(img, win, win_fill, OUTLINE, 4, 24, 5)

    # etiqueta inferior
    lab = (pad + 22, pad + h - 84, pad + w - 22, pad + h - 22)
    lab_fill = PANEL if not hover else FLAME
    draw_blob(img, lab, lab_fill, OUTLINE, 4, 22, 23)
    return img.resize(img.size, Image.LANCZOS), pad


def build_card(index, hover):
    name, sheet, idx = EMOTES[index]
    # el lienzo se dibuja directo a resolucion final con supersampling propio
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    del big  # (no hace falta, solo documentacion)

    card, pad = draw_card(None, hover)

    pose = frame(sheet, idx)
    target_h = 168
    sc = target_h / pose.height
    pose = pose.resize((max(1, int(pose.width * sc)), target_h), Image.LANCZOS)

    # sombra del suelo bajo el personaje
    wy1 = pad + 22 + 196
    cx = card.width // 2
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - 52, wy1 - 20, cx + 52, wy1 - 6),
                               fill=(20, 24, 32, 90))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
    card.alpha_composite(pose, (cx - pose.width // 2, wy1 - 10 - pose.height))

    # adornos en la ventana
    sparkle(card, pad + 48, pad + 52, 11, FLAME_HOT if hover else WHITE)
    sparkle(card, pad + CARD_W - 50, pad + 70, 8, FLAME_HOT if hover else WHITE)

    # nombre
    lab_cy = pad + CARD_H - 53
    text_center(card, name, cx, lab_cy, font(30), WHITE, INK, 3)
    return card, pad


def build_panel():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # panel principal
    shadow(img, (40, 70, W - 40, H - 30), 50, blur=18, alpha=140, offset=(0, 12))
    draw_blob(img, (40, 70, W - 40, H - 30), PANEL, OUTLINE, 6, 46, 3)

    # franja interior mas oscura (efecto de profundidad)
    inner = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(inner).rounded_rectangle(
        (62, 92, W - 62, H - 52), 34, outline=PANEL_DARK + (255,), width=3)
    img.alpha_composite(inner)

    # tab del titulo
    tab = (W // 2 - 190, 24, W // 2 + 190, 112)
    shadow(img, tab, 36, blur=8, alpha=110, offset=(0, 6))
    draw_blob(img, tab, PANEL_DARK, OUTLINE, 6, 34, 41)
    text_center(img, "EMOTES", W // 2, 70, font(52), WHITE, INK, 4)

    # tarjetas
    for i, (x, y, w, h) in enumerate(CARDS):
        card, pad = build_card(i, False)
        img.alpha_composite(card, (x - pad, y - pad))

    # pie
    text_center(img, "Click para hacer el emote", W // 2, H - 46,
                font(20, False), (226, 231, 238), INK, 2)
    return img


def main():
    HUD.mkdir(parents=True, exist_ok=True)

    panel = build_panel()
    panel.save(HUD / "emotes_panel.png")

    # tarjetas resaltadas, una por emote (el pose cambia)
    for i, (name, sheet, idx) in enumerate(EMOTES):
        card, pad = build_card(i, True)
        card.save(HUD / f"emotes_card_hover_{i}.png")

    print("listo:", HUD / "emotes_panel.png")
    print("tarjetas:", CARDS, "margen de las tarjetas hover:", 24)


if __name__ == "__main__":
    main()