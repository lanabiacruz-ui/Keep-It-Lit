import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
HUD_DIR = ROOT / "assets" / "maps" / "hud"
UI_DIR = ROOT / "assets" / "maps" / "ui"

DARK = (30, 32, 38, 255)
GOLD = (214, 170, 72, 255)
GOLD_DARK = (122, 84, 24, 255)
GOLD_LIGHT = (255, 232, 150, 255)
RED = (200, 54, 54, 255)
RED_DARK = (140, 30, 34, 255)
BLACK = (34, 36, 42, 255)
GREEN = (50, 160, 84, 255)
FELT = (40, 104, 66, 255)
FELT_DARK = (28, 76, 48, 255)

WHEEL = "RNRNV" * 4
PAINT = {"R": RED, "N": BLACK, "V": GREEN}


def wedge(d, cx, cy, r_out, r_in, a_start, a_end, fill, outline=None):

    pts = []

    steps = 6

    for j in range(steps + 1):
        a = math.radians(a_start + (a_end - a_start) * j / steps)
        pts.append((cx + math.cos(a) * r_out, cy + math.sin(a) * r_out))

    for j in range(steps, -1, -1):
        a = math.radians(a_start + (a_end - a_start) * j / steps)
        pts.append((cx + math.cos(a) * r_in, cy + math.sin(a) * r_in))

    d.polygon(pts, fill=fill)

    if outline is not None:
        d.polygon(pts, outline=outline)


def add_outline(img, px, color):

    alpha = img.getchannel("A")
    grown = alpha.filter(ImageFilter.MaxFilter(px * 2 + 1))

    base = Image.new("RGBA", img.size, color)
    base.putalpha(grown)

    return Image.alpha_composite(base, img)


def make_icon():

    s = 8
    size = 64 * s

    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def p(v):
        return int(round(v * s))

    d.rounded_rectangle(
        (p(5), p(34), p(59), p(57)), radius=p(5), fill=FELT_DARK
    )
    d.rounded_rectangle(
        (p(5), p(30), p(59), p(52)), radius=p(5), fill=FELT
    )
    d.rounded_rectangle(
        (p(8), p(33), p(56), p(49)), radius=p(3), outline=GOLD, width=p(1)
    )

    cx, cy = p(32), p(28)

    d.ellipse((cx - p(23), cy - p(23), cx + p(23), cy + p(23)), fill=DARK)
    d.ellipse((cx - p(21.5), cy - p(21.5), cx + p(21.5), cy + p(21.5)), fill=GOLD)
    d.ellipse((cx - p(19.5), cy - p(19.5), cx + p(19.5), cy + p(19.5)), fill=GOLD_DARK)
    d.ellipse((cx - p(18.5), cy - p(18.5), cx + p(18.5), cy + p(18.5)), fill=DARK)

    step = 360.0 / len(WHEEL)

    for i, letter in enumerate(WHEEL):

        a0 = -90 + i * step - step / 2
        a1 = -90 + i * step + step / 2

        wedge(d, cx, cy, p(17.5), p(8.5), a0, a1, PAINT[letter], GOLD_DARK)

    d.ellipse((cx - p(8.5), cy - p(8.5), cx + p(8.5), cy + p(8.5)), fill=(58, 62, 70, 255))
    d.ellipse((cx - p(8.5), cy - p(8.5), cx + p(8.5), cy + p(8.5)), outline=GOLD, width=p(0.9))

    for k in range(4):
        a = math.radians(k * 90 + 45)
        d.line(
            (cx, cy, cx + math.cos(a) * p(7), cy + math.sin(a) * p(7)),
            fill=GOLD, width=p(1.1),
        )

    d.ellipse((cx - p(3), cy - p(3), cx + p(3), cy + p(3)), fill=GOLD, outline=GOLD_DARK, width=p(0.8))
    d.ellipse((cx - p(1.6), cy - p(1.9), cx - p(0.2), cy - p(0.5)), fill=GOLD_LIGHT)

    bx, by = p(41.5), p(17)

    d.ellipse((bx - p(2.4) + p(.5), by - p(2.4) + p(.8), bx + p(2.4) + p(.5), by + p(2.4) + p(.8)), fill=(16, 16, 18, 200))
    d.ellipse((bx - p(2.4), by - p(2.4), bx + p(2.4), by + p(2.4)), fill=(236, 190, 62, 255), outline=GOLD_DARK, width=p(0.7))
    d.ellipse((bx - p(1.4), by - p(1.5), bx - p(0.2), by - p(0.3)), fill=(255, 246, 190, 255))

    for x, y, col, dark in ((p(47), p(46), RED, RED_DARK), (p(51.5), p(48.5), (60, 110, 200, 255), (34, 66, 130, 255))):
        d.ellipse((x - p(4.2), y - p(2.1) + p(1.2), x + p(4.2), y + p(2.1) + p(1.2)), fill=dark)
        d.ellipse((x - p(4.2), y - p(2.1), x + p(4.2), y + p(2.1)), fill=col, outline=DARK, width=p(0.7))
        d.ellipse((x - p(2.4), y - p(1.0), x + p(2.4), y + p(1.0)), outline=(240, 240, 244, 255), width=p(0.5))

    small = im.resize((64, 64), Image.LANCZOS)

    return add_outline(small, 1, DARK)


def make_panel():

    w, h = 640, 440
    s = 2
    size = (w * s, h * s)

    radius = 34 * s
    border = 9 * s

    outer = Image.new("L", size, 0)
    ImageDraw.Draw(outer).rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255
    )

    inner = Image.new("L", size, 0)
    ImageDraw.Draw(inner).rounded_rectangle(
        (border, border, size[0] - 1 - border, size[1] - 1 - border),
        radius=radius - border // 2, fill=255,
    )

    base = np.zeros((size[1], size[0], 3), dtype=np.float32)
    base[:, :] = (78, 84, 96)

    yy, xx = np.mgrid[0:size[1], 0:size[0]]

    cell = 16 * s
    fx = (xx % cell) / cell
    fy = (yy % cell) / cell
    diamond = (np.abs(fx - 0.5) + np.abs(fy - 0.5)) < 0.30
    diamond2 = (np.abs(((xx + cell // 2) % cell) / cell - 0.5)
                + np.abs(((yy + cell // 2) % cell) / cell - 0.5)) < 0.30

    base[diamond] += 7
    base[diamond2] -= 5

    cx = size[0] / 2
    cy = size[1] / 2
    dist = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    vignette = 1.0 - 0.20 * np.clip(dist - 0.35, 0, 1)

    base *= vignette[..., None]

    top_band = np.clip(1.0 - yy / (60.0 * s), 0, 1) * 10
    base += top_band[..., None]

    body = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    panel = Image.new("RGBA", size, (0, 0, 0, 0))
    panel.paste(Image.new("RGBA", size, DARK), (0, 0), outer)
    panel.paste(body, (0, 0), inner)

    d = ImageDraw.Draw(panel)

    gap = 8 * s
    line = Image.new("RGBA", size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)

    ld.rounded_rectangle(
        (border + gap, border + gap, size[0] - 1 - border - gap, size[1] - 1 - border - gap),
        radius=radius - border // 2 - gap // 2, outline=GOLD, width=2 * s,
    )

    ld.rounded_rectangle(
        (border + gap + 4 * s, border + gap + 4 * s,
         size[0] - 1 - border - gap - 4 * s, size[1] - 1 - border - gap - 4 * s),
        radius=radius - border // 2 - gap // 2 - 4 * s,
        outline=(GOLD_DARK[0], GOLD_DARK[1], GOLD_DARK[2], 150), width=1 * s,
    )

    panel = Image.alpha_composite(panel, line)
    d = ImageDraw.Draw(panel)

    def diamond_shape(x, y, r):
        pts = [(x, y - r), (x + r * 0.75, y), (x, y + r), (x - r * 0.75, y)]
        d.polygon(pts, fill=GOLD, outline=GOLD_DARK)

    off = border + gap
    for x, y in (
        (off + 2 * s, off + 2 * s),
        (size[0] - off - 2 * s, off + 2 * s),
        (off + 2 * s, size[1] - off - 2 * s),
        (size[0] - off - 2 * s, size[1] - off - 2 * s),
    ):
        diamond_shape(x, y, 7 * s)

    diamond_shape(size[0] // 2, off + 2 * s, 6 * s)
    diamond_shape(size[0] // 2, size[1] - off - 2 * s, 6 * s)

    return panel.resize((w, h), Image.LANCZOS)


def main():

    icon = make_icon()
    panel = make_panel()

    HUD_DIR.mkdir(parents=True, exist_ok=True)
    UI_DIR.mkdir(parents=True, exist_ok=True)

    icon.save(HUD_DIR / "icon_ruleta.png")
    panel.save(UI_DIR / "ruleta_panel.png")

    print("icon_ruleta.png", icon.size)
    print("ruleta_panel.png", panel.size)


if __name__ == "__main__":
    main()