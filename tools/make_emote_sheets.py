"""Genera las hojas de los emotes (baile) de cada skin.

Uso (desde la carpeta del proyecto):

    python tools/make_emote_sheets.py            # todas las skins
    python tools/make_emote_sheets.py pago_2     # solo una

Por cada skin crea 3 hojas con los cuadros del baile ya dibujados:

    emote_six_seven.png   emote_dab.png   emote_saludo.png

Van en assets/maps/skins/<skin>/ (la skin "clasico" en assets/maps/player/).
El juego solo las reproduce: no dibuja nada en tiempo real.

PARA DIBUJARLAS A MANO: cada hoja es una grilla de 8 columnas de cuadros de
266x266 px, a 20 cuadros por segundo, empezando arriba a la izquierda y
leyendo de izquierda a derecha. Los pies del personaje van abajo al medio
del cuadro (6 px de margen abajo), igual que en esta version. Si reemplazas
una hoja por una tuya con el mismo nombre y medidas, el juego la usa sola.

Cantidad de cuadros: seis_siete 48, dab 24, saludo 28.
"""

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PLAYER_DIR = ROOT / "assets" / "maps" / "player"
SKINS_DIR = ROOT / "assets" / "maps" / "skins"

# --- formato de las hojas (tiene que coincidir con player/player.py) ----------
FPS = 20
COLS = 8
CELL = (266, 266)
EMOTE_TIME = {"six_seven": 2.4, "dab": 1.2, "saludo": 1.4}

SHEET_CELL = (190, 214)      # celdas de las hojas de caminata
BODY_POS = (38, 46)          # donde cae el cuadro de 190x214 dentro del cuadro de 266x266
FEET = (BODY_POS[0] + 95, BODY_POS[1] + 214)    # abajo al medio del personaje

# --- brazos -------------------------------------------------------------------
ARM_R = 12
ARM_OUTLINE = 6
SS = 4                        # supersampling del trazo

ARMS_REST = (
    ((50, 134), (36, 148), (30, 162)),
    ((144, 134), (158, 148), (164, 162)),
)

JUMP_CELL_PX = 27             # alto del saltito del saludo, en px de cuadro
JUMP_TIME = 0.36


def smooth(k):
    return k * k * (3.0 - 2.0 * k)


def blend(t, total):
    k = max(0.0, min(1.0, t / 0.18, (total - t) / 0.20))
    return smooth(k)


def lerp_arms(a, b, k):
    return tuple(
        tuple(
            tuple(a[i][j][c] + (b[i][j][c] - a[i][j][c]) * k for c in range(2))
            for j in range(3)
        )
        for i in range(2)
    )


def arms_target(emote, t):
    rest_l, rest_r = ARMS_REST

    if emote == "six_seven":
        s = math.sin(t * math.tau * 2.6)
        return (
            ((50, 134), (40, 148), (64, 143 + 15 * s)),
            ((144, 134), (154, 148), (130, 143 - 15 * s)),
        )

    if emote == "dab":
        return (
            ((50, 134), (53, 115), (82, 103)),
            ((144, 134), (158, 118), (172, 98)),
        )

    w = math.sin(t * math.tau * 3.2)
    return (rest_l, ((144, 134), (158 + 3 * w, 120), (164 + 8 * w, 96)))


# --- lectura del personaje de frente -------------------------------------------

def front_frame(skin_id):
    """Cuadro de frente y quieto (190x214) de la skin, y su hoja de origen."""

    path = SKINS_DIR / skin_id / "player.png"

    if not path.exists():
        path = PLAYER_DIR / "player.png"

    sheet = Image.open(path).convert("RGBA")
    w, h = SHEET_CELL

    return sheet.crop((4 * w, 1 * h, 5 * w, 2 * h))


def sample_colors(frame):
    px = np.array(frame)

    ys = range(134, 160, 2)
    xs = range(26, 47, 2)

    pts = [tuple(px[y, x][:3]) for y in ys for x in xs if px[y, x][3] > 200]
    bright = [p for p in pts if sum(int(v) for v in p) > 150]

    pool = bright or pts

    if pool:
        pool.sort(key=lambda c: sum(int(v) for v in c))
        fill = pool[len(pool) // 2]
    else:
        fill = (172, 191, 200)

    # trazo: el pixel mas oscuro del borde de la cabeza
    row = [tuple(px[70, x][:3]) for x in range(18, 40) if px[70, x][3] > 200]

    outline = min(row, key=lambda c: sum(int(v) for v in c)) if row else (20, 18, 18)

    return tuple(int(v) for v in fill), tuple(int(v) for v in outline)


def armless(frame):
    """El cuadro sin los brazos pegados al cuerpo."""

    body = frame.copy()
    clear = Image.new("RGBA", (200, 44), (0, 0, 0, 0))

    body.paste(clear, (-149, 126))       # costado izquierdo (x < 51)
    body.paste(clear, (147, 126))        # costado derecho  (x >= 147)

    return body


# --- trazo de los brazos (con un poco de pulso, como dibujado a mano) ----------

def _centerline(points, step):
    out = []

    for a, b in zip(points, points[1:]):
        dist = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(dist / step))

        for i in range(n):
            u = i / n
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))

    out.append(points[-1])

    return out


def draw_arm(draw, pts, fill, outline, seed):
    rnd = random.Random(seed)
    ph1, ph2, ph3 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)

    line = _centerline(pts, 1.0 / SS)
    total = len(line)

    for stage in (0, 1):

        for i, (x, y) in enumerate(line):
            u = i / max(1, total - 1)

            width = ARM_R * (0.92 + 0.12 * u) * (1.0 + 0.05 * math.sin(u * 9 + ph1))

            if stage == 0:
                r = width + ARM_OUTLINE * (1.0 + 0.18 * math.sin(u * 13 + ph2))
                color = outline
            else:
                r = width
                color = fill

            r *= SS
            cx, cy = x * SS, y * SS

            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,))

        # mano: una manopla un poco mas grande, con un bultito de pulgar
        hx, hy = pts[-1]
        hand = ARM_R * 1.18

        shapes = [(hx, hy, hand), (hx + 4, hy - 6, hand * 0.38)]

        for sx, sy, sr in shapes:
            r = (sr + (ARM_OUTLINE if stage == 0 else 0)) * SS
            color = outline if stage == 0 else fill
            draw.ellipse(
                [sx * SS - r, sy * SS - r, sx * SS + r, sy * SS + r],
                fill=color + (255,)
            )


def render_frame(body, fill, outline, emote, t, skin_seed):
    total = EMOTE_TIME[emote]
    k = blend(t, total)

    arms = lerp_arms(ARMS_REST, arms_target(emote, t), k)

    w, h = CELL
    layer = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    for side, (s_pt, e_pt, h_pt) in enumerate(arms):
        pts = [
            ((p[0] + BODY_POS[0]), (p[1] + BODY_POS[1])) for p in (s_pt, e_pt, h_pt)
        ]
        draw_arm(draw, pts, fill, outline, skin_seed + side)

    layer = layer.resize((w, h), Image.LANCZOS)

    canvas = Image.new("RGBA", CELL, (0, 0, 0, 0))
    canvas.alpha_composite(body, BODY_POS)
    canvas.alpha_composite(layer)

    # inclinacion del cuerpo (alrededor de los pies)
    angle = 0.0

    if emote == "dab":
        angle = 10.0 * k
    elif emote == "six_seven":
        angle = 3.0 * math.sin(t * math.tau * 1.3) * k

    if abs(angle) > 0.05:
        canvas = canvas.rotate(angle, resample=Image.BICUBIC, center=FEET)

    # saltitos
    lift = 0

    if emote == "six_seven":
        lift = abs(math.sin(t * math.tau * 2.6)) * 10.5 * k

    elif emote == "saludo":
        p = (t % JUMP_TIME) / JUMP_TIME if t < JUMP_TIME * 2 else 0.0
        lift = JUMP_CELL_PX * 4.0 * p * (1.0 - p) if t < JUMP_TIME * 2 else 0.0

    if lift > 0.4:
        moved = Image.new("RGBA", CELL, (0, 0, 0, 0))
        moved.alpha_composite(canvas, (0, -int(round(lift))))
        canvas = moved

    return canvas


def quantize(sheet):
    """Paleta de 256 colores con transparencia: PNG mucho mas chico."""

    return sheet.quantize(colors=255, method=Image.FASTOCTREE, dither=Image.NONE)


def build_sheet(body, fill, outline, emote, seed):
    count = round(EMOTE_TIME[emote] * FPS)
    rows = math.ceil(count / COLS)

    sheet = Image.new("RGBA", (COLS * CELL[0], rows * CELL[1]), (0, 0, 0, 0))

    for i in range(count):
        frame = render_frame(body, fill, outline, emote, i / FPS, seed)
        sheet.paste(frame, ((i % COLS) * CELL[0], (i // COLS) * CELL[1]))

    return sheet


def skin_ids():
    ids = ["clasico"]
    ids += sorted(p.name for p in SKINS_DIR.iterdir() if p.is_dir())

    return ids


def main(only=None):
    for skin_id in skin_ids():

        if only and skin_id not in only:
            continue

        out_dir = PLAYER_DIR if skin_id == "clasico" else SKINS_DIR / skin_id

        frame = front_frame(skin_id)
        fill, outline = sample_colors(frame)
        body = armless(frame)
        seed = sum(ord(c) for c in skin_id)

        for emote in EMOTE_TIME:
            sheet = build_sheet(body, fill, outline, emote, seed)
            path = out_dir / f"emote_{emote}.png"

            quantize(sheet).save(path, optimize=True)

            print(f"{skin_id:16s} {path.name:22s} {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
