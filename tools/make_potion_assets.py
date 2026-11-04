"""Genera las imagenes de las pociones (assets/maps/hud/).

    icon_pocion_ascua.png / _invisibilidad / _velocidad / _ira   (96x96)
    hud_pocion_slot.png / hud_pocion_slot_select.png             (marcos, violeta)
    efecto_relleno_pocion_<nombre>.png                           (barra de efectos)

Uso:  python tools/make_potion_assets.py
"""

import colorsys
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HUD = Path(__file__).resolve().parent.parent / "assets" / "maps" / "hud"

SS = 4                 # supersampling para que quede suave
SIZE = 96

OUTLINE = (58, 38, 34, 255)

POTIONS = {
    "ascua": {
        "liquid": (222, 58, 48),
        "light": (255, 128, 96),
        "dark": (150, 28, 34),
        "hue": 0.0,
        "mark": "flame",
    },
    "invisibilidad": {
        "liquid": (150, 96, 224),
        "light": (206, 170, 255),
        "dark": (92, 52, 160),
        "hue": 0.75,
        "mark": "dots",
    },
    "velocidad": {
        "liquid": (72, 196, 240),
        "light": (160, 232, 255),
        "dark": (30, 120, 190),
        "hue": 0.54,
        "mark": "bolt",
    },
    "ira": {
        "liquid": (255, 140, 40),
        "light": (255, 200, 110),
        "dark": (200, 84, 18),
        "hue": 0.07,
        "mark": "brows",
    },
}


def _s(v):
    return int(round(v * SS))


def _mark(d, kind, cx, cy, light):

    white = (255, 250, 235, 255)

    if kind == "flame":

        pts = [
            (cx, cy - _s(15)), (cx + _s(9), cy - _s(3)),
            (cx + _s(7), cy + _s(8)), (cx, cy + _s(13)),
            (cx - _s(7), cy + _s(8)), (cx - _s(9), cy - _s(3)),
            (cx - _s(3), cy - _s(7)),
        ]
        d.polygon(pts, fill=(255, 214, 90, 255))
        d.polygon(
            [(cx, cy - _s(4)), (cx + _s(4), cy + _s(5)),
             (cx, cy + _s(9)), (cx - _s(4), cy + _s(5))],
            fill=white,
        )

    elif kind == "dots":

        for dx, dy, r in ((-10, -4, 5), (6, -10, 4), (8, 6, 6), (-6, 9, 3)):
            d.ellipse(
                (cx + _s(dx - r), cy + _s(dy - r),
                 cx + _s(dx + r), cy + _s(dy + r)),
                fill=(*light, 255),
            )

    elif kind == "bolt":

        pts = [
            (cx + _s(4), cy - _s(16)), (cx - _s(9), cy + _s(2)),
            (cx - _s(1), cy + _s(2)), (cx - _s(5), cy + _s(16)),
            (cx + _s(10), cy - _s(3)), (cx + _s(2), cy - _s(3)),
        ]
        d.polygon(pts, fill=white)

    elif kind == "brows":

        w = _s(5)
        d.line([(cx - _s(14), cy - _s(10)), (cx - _s(3), cy - _s(3))],
               fill=(120, 40, 10, 255), width=w)
        d.line([(cx + _s(14), cy - _s(10)), (cx + _s(3), cy - _s(3))],
               fill=(120, 40, 10, 255), width=w)
        d.ellipse((cx - _s(2), cy + _s(6), cx + _s(2), cy + _s(10)),
                  fill=(120, 40, 10, 255))
        d.rectangle((cx - _s(2), cy + _s(1), cx + _s(2), cy + _s(6)),
                    fill=(120, 40, 10, 255))


def make_icon(name, cfg):

    big = SIZE * SS
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))

    cx = big // 2
    body_cy = _s(60)
    rx, ry = _s(27), _s(25)

    def body_box(grow=0):
        return (cx - rx - grow, body_cy - ry - grow,
                cx + rx + grow, body_cy + ry + grow)

    neck = (cx - _s(9), _s(22), cx + _s(9), _s(42))
    lip = (cx - _s(13), _s(18), cx + _s(13), _s(26))
    cork = [
        (cx - _s(9), _s(8)), (cx + _s(9), _s(8)),
        (cx + _s(11), _s(19)), (cx - _s(11), _s(19)),
    ]

    # ---- contorno (todo un poco mas grande, en marron oscuro) ----
    o = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    od = ImageDraw.Draw(o)
    g = _s(3.2)
    od.ellipse(body_box(g), fill=OUTLINE)
    od.rectangle((neck[0] - g, neck[1] - g, neck[2] + g, neck[3] + g),
                 fill=OUTLINE)
    od.rectangle((lip[0] - g, lip[1] - g, lip[2] + g, lip[3] + g),
                 fill=OUTLINE)
    od.polygon([(x + (-g if x < cx else g), y - (g if y < _s(10) else 0))
                for x, y in cork], fill=OUTLINE)
    img.alpha_composite(o)

    d = ImageDraw.Draw(img)

    # ---- vidrio (clarito) ----
    glass = (226, 238, 244, 255)
    d.ellipse(body_box(), fill=glass)
    d.rectangle(neck, fill=glass)
    d.rectangle(lip, fill=(205, 222, 232, 255))

    # ---- liquido ----
    liquid = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ld = ImageDraw.Draw(liquid)
    level = body_cy - _s(10)
    ld.rectangle((0, level, big, big), fill=(*cfg["liquid"], 255))
    # ola en la superficie
    for k in range(-3, 4):
        ld.ellipse(
            (cx + k * _s(10) - _s(7), level - _s(3),
             cx + k * _s(10) + _s(7), level + _s(3)),
            fill=(*cfg["liquid"], 255),
        )
    # sombra abajo
    ld.ellipse((cx - rx, body_cy + _s(6), cx + rx, body_cy + ry + _s(8)),
               fill=(*cfg["dark"], 255))
    ld.ellipse((cx - rx + _s(5), body_cy + _s(2), cx + rx - _s(5),
                body_cy + ry), fill=(*cfg["liquid"], 255))
    # brillo del liquido
    ld.ellipse((cx - _s(18), level + _s(3), cx - _s(8), level + _s(9)),
               fill=(*cfg["light"], 255))

    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse(body_box(), fill=255)
    clipped = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    clipped.paste(liquid, (0, 0), mask)
    img.alpha_composite(clipped)

    d = ImageDraw.Draw(img)

    _mark(d, cfg["mark"], cx + _s(2), body_cy + _s(4), cfg["light"])

    # ---- corcho ----
    d.polygon(cork, fill=(196, 140, 84, 255))
    d.line([(cx - _s(6), _s(11)), (cx + _s(5), _s(11))],
           fill=(226, 178, 120, 255), width=_s(2))
    d.line([(cx - _s(7), _s(16)), (cx + _s(7), _s(16))],
           fill=(150, 100, 58, 255), width=_s(2))

    # ---- brillo del vidrio ----
    d.arc((cx - rx + _s(5), body_cy - ry + _s(5), cx + rx - _s(5),
           body_cy + ry - _s(5)), 200, 255, fill=(255, 255, 255, 230),
          width=_s(3))
    d.line([(cx - _s(5), _s(28)), (cx - _s(5), _s(38))],
           fill=(255, 255, 255, 210), width=_s(2))

    # inclinada como el resto de frascos del juego
    img = img.rotate(-16, resample=Image.BICUBIC, center=(cx, big // 2))
    img = img.resize((SIZE, SIZE), Image.LANCZOS)

    img.save(HUD / f"icon_pocion_{name}.png")


def _tint_slot(src, dst, select):

    im = Image.open(HUD / src).convert("RGBA")
    px = im.load()

    for y in range(im.height):
        for x in range(im.width):

            r, g, b, a = px[x, y]

            if a == 0:
                continue

            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

            if select:
                if s > 0.15:
                    h = 0.76
                    s = min(1.0, s * 1.05)
                else:
                    h, s = 0.76, 0.18
            else:
                h = 0.76
                s = min(1.0, s + 0.28)
                v = min(1.0, v * 0.96)

            r, g, b = colorsys.hsv_to_rgb(h, s, v)

            px[x, y] = (int(r * 255), int(g * 255), int(b * 255), a)

    im.save(HUD / dst)


def make_effect_fill(name, cfg):

    src = Image.open(HUD / "efecto_relleno_aceite.png").convert("RGBA")
    px = src.load()

    for y in range(src.height):
        for x in range(src.width):

            r, g, b, a = px[x, y]

            if a == 0:
                continue

            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

            if s > 0.25:
                h = cfg["hue"]

            r, g, b = colorsys.hsv_to_rgb(h, s, v)

            px[x, y] = (int(r * 255), int(g * 255), int(b * 255), a)

    src.save(HUD / f"efecto_relleno_pocion_{name}.png")


def main():

    for name, cfg in POTIONS.items():
        make_icon(name, cfg)
        make_effect_fill(name, cfg)

    _tint_slot("hud_slot.png", "hud_pocion_slot.png", False)
    _tint_slot("hud_slot_select.png", "hud_pocion_slot_select.png", True)

    print("listo:", HUD)


if __name__ == "__main__":
    main()