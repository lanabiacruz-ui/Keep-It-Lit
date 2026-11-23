"""Genera las imagenes del Farolero a partir de los dibujos originales.

Entradas (poner en tools/farolero_src/):
    farolero_base.png     el Farolero parado, fondo NEGRO puro
    farolero_ritual.png   hoja 4x4 del ritual (parado -> sentado -> llama ->
                          de nuevo parado), fondo negro

Salidas en assets/maps/combate/:
    salvador.png            el Farolero parado con transparencia (retrato del
                            dialogo y sprite quieto)
    farolero_caminar.png    tira horizontal de 4 cuadros de caminata
                            (hecha a partir del dibujo parado)
    farolero_ritual.png     la hoja del ritual con TRANSPARENCIA (sin fondo negro):
                            cuerpo opaco, llama y resplandor con alfa suave
    farolero_anim.json      medidas que lee ui/map2_rescue.py

Para usar una caminata dibujada a mano: reemplazar farolero_caminar.png por
una tira con el mismo formato y ajustar "frames" y "cell" en el json.

Uso:  python tools/make_farolero_assets.py
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi


BASE = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent / "farolero_src"
OUT = BASE / "assets" / "maps" / "combate"

BG_MAX = 2            # lo que sea <= a esto (en el canal mas alto) es fondo
WALK_FRAMES = 4
WALK_LIFT = 14        # cuanto levanta cada pierna (px del dibujo)
WALK_PAD = 10

RITUAL_COLS = 4
RITUAL_ROWS = 4
FADE_SIDE = 40        # difuminado de los bordes (px del cuadro)
FADE_TOP = 20
FADE_BOTTOM = 10
FADE_ELLIPSE = (0.50, 0.62)   # elipse (fraccion del ancho y del alto) fuera de la cual la luz se apaga


def smooth(t):

    t = np.clip(t, 0.0, 1.0)

    return t * t * (3.0 - 2.0 * t)


# ------------------------------------------------------------- parado

def build_standing():

    rgb = np.array(Image.open(SRC / "farolero_base.png").convert("RGB"))

    bg = rgb.max(axis=2) <= BG_MAX

    lab, _ = ndi.label(bg)

    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    border.discard(0)

    outside = np.isin(lab, list(border))

    alpha = np.where(outside, 0, 255).astype(np.uint8)

    rgba = np.dstack([rgb, alpha])

    ys, xs = np.where(alpha > 0)

    rgba = rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    img = Image.fromarray(rgba, "RGBA")

    img.save(OUT / "salvador.png")

    return img


# ------------------------------------------------------------- caminata

def build_walk(stand):
    """Caminata simple a partir del dibujo parado: las piernas se levantan de
    a una, el cuerpo se balancea y sube un poco en cada paso."""

    w, h = stand.size

    cw = w + WALK_PAD * 2
    ch = h + WALK_PAD

    hip = int(h * 0.68)

    upper = stand.crop((0, 0, w, hip))

    legs = stand.crop((0, hip, w, h))

    # las piernas se separan por la mitad de las columnas ocupadas abajo
    alpha = np.array(legs)[..., 3]
    cols = np.where(alpha.max(axis=0) > 0)[0]

    gap_lo, gap_hi = int(w * 0.40), int(w * 0.60)
    profile = alpha[int(legs.height * 0.55):].max(axis=0)

    split = int(np.argmin(profile[gap_lo:gap_hi])) + gap_lo

    if cols.size == 0:
        split = w // 2

    left = legs.crop((0, 0, split, legs.height))
    right = legs.crop((split, 0, w, legs.height))

    # (levanta_izq, levanta_der, desplazamiento_x_cuerpo, sube_cuerpo)
    poses = [
        (0, 0, 0, 0),
        (WALK_LIFT, 0, 2, 3),
        (0, 0, 0, 0),
        (0, WALK_LIFT, -2, 3),
    ]

    strip = Image.new("RGBA", (cw * WALK_FRAMES, ch), (0, 0, 0, 0))

    for n, (ll, lr, sway, rise) in enumerate(poses):

        cell = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

        ox = WALK_PAD
        floor = ch

        cell.alpha_composite(
            left, (ox, floor - legs.height - ll - rise)
        )
        cell.alpha_composite(
            right, (ox + split, floor - legs.height - lr - rise)
        )
        cell.alpha_composite(
            upper, (ox + sway, floor - legs.height - hip - rise)
        )

        strip.alpha_composite(cell, (n * cw, 0))

    strip.save(OUT / "farolero_caminar.png")

    return {"file": "farolero_caminar.png", "frames": WALK_FRAMES,
            "cell": [cw, ch], "stand_h": h}


# ------------------------------------------------------------- ritual

LIT_FRAMES = (5, 6, 7, 8, 9, 10, 11)   # cuadros con llama: el fondo tiene brillo
REF_FRAME = 10                          # cuadro limpio para sacar la silueta sentado
SEARCH = 26                             # cuanto se busca desplazar la silueta (px)
GLOW_FLOOR = 22                         # por debajo de esto el fondo es ruido


def _clean(mask, min_size=250, close=3):

    lab, n = ndi.label(mask)

    if n == 0:
        return mask

    sizes = ndi.sum(mask, lab, range(1, n + 1))

    keep = [i + 1 for i, v in enumerate(sizes) if v >= min_size]

    mask = np.isin(lab, keep)
    mask = ndi.binary_closing(mask, iterations=close)

    return ndi.binary_fill_holes(mask)


def _frame_border_off(mask):

    mask = mask.copy()
    mask[:5] = mask[-5:] = False
    mask[:, :5] = mask[:, -5:] = False

    return mask


def _dark_mask(cell, close=7):
    """Cuadros apagados: el cuerpo es gris y el fondo casi negro."""

    sm = np.stack([ndi.gaussian_filter(cell[..., i], 1.0) for i in range(3)], -1)

    lum = sm.max(axis=2)

    # el contorno es mas oscuro que el cuerpo: se recupera cerrando huecos
    # (el cuello y los bordes) y rellenando
    mask = _frame_border_off((lum > 23) & (sm[..., 2] > 0.55 * sm[..., 0]))

    mask = ndi.binary_opening(mask, iterations=1)

    return _clean(mask, 250, close)


def _chroma_core(cell):
    """Parte del cuerpo con luz de fuego: tiene mas azul que el resplandor."""

    sm = np.stack([ndi.gaussian_filter(cell[..., i], 0.8) for i in range(3)], -1)

    core = _frame_border_off((sm[..., 0] > 30) & (sm[..., 2] > 0.40 * sm[..., 0]))

    return ndi.binary_opening(core, iterations=1)


def _best_shift(ref, core):

    best, best_score = (0, 0), -1

    for dy in range(-SEARCH, SEARCH + 1, 2):
        for dx in range(-SEARCH, SEARCH + 1, 2):

            moved = np.roll(np.roll(ref, dy, axis=0), dx, axis=1)

            score = int((moved & core).sum()) - 0.35 * int((moved & ~core).sum())

            if score > best_score:
                best, best_score = (dy, dx), score

    return best


def build_ritual():
    """Hoja del ritual con TRANSPARENCIA: el cuerpo opaco y la llama / el
    resplandor con alfa suave (sin el fondo negro)."""

    sheet = np.array(Image.open(SRC / "farolero_ritual.png").convert("RGB"))

    H, W = sheet.shape[:2]

    cw = W // RITUAL_COLS
    ch = H // RITUAL_ROWS

    cells = []

    for n in range(RITUAL_COLS * RITUAL_ROWS):
        r, c = divmod(n, RITUAL_COLS)
        cells.append(
            sheet[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw].astype(np.float32)
        )

    # silueta de la pose sentado, sacada de un cuadro limpio
    ref = _clean(_chroma_core(cells[REF_FRAME]), 400, 4)
    ref = ndi.binary_opening(ref, iterations=2)

    yy, xx = np.mgrid[0:ch, 0:cw]

    rx = cw * FADE_ELLIPSE[0]
    ry = ch * FADE_ELLIPSE[1]

    radial = np.sqrt(((xx - cw / 2.0) / rx) ** 2 + ((yy - ch / 2.0) / ry) ** 2)

    fade = (
        smooth(xx / FADE_SIDE) * smooth((cw - 1 - xx) / FADE_SIDE)
        * smooth(yy / FADE_TOP) * smooth((ch - 1 - yy) / FADE_BOTTOM)
        * smooth((1.0 - radial) / 0.30)
    )

    out = np.zeros((H, W, 4), np.uint8)

    for n, cell in enumerate(cells):

        if n in LIT_FRAMES:

            dy, dx = _best_shift(ref, _chroma_core(cell))

            body = np.roll(np.roll(ref, dy, axis=0), dx, axis=1)

        else:
            body = _dark_mask(cell, 13 if n in (3, 4) else 7)

        body = ndi.binary_dilation(body, iterations=1 if n in LIT_FRAMES else 2)

        # alfa de la llama y el resplandor: sale del brillo
        lum = cell.max(axis=2)

        glow_a = np.clip((lum - GLOW_FLOOR) / (255.0 - GLOW_FLOOR), 0.0, 1.0)

        # el cuerpo: opaco, con borde suave de 1 px
        soft = ndi.gaussian_filter(body.astype(np.float32), 0.7)

        alpha = np.maximum(soft, glow_a * (1.0 - soft))

        alpha = alpha * fade

        # color sin multiplicar por el alfa (el brillo se queda en el color)
        safe = np.maximum(alpha, 1e-3)[..., None]

        color = np.where(
            soft[..., None] > 0.5,
            cell,
            np.clip(cell / np.maximum(glow_a, 1e-3)[..., None], 0, 255),
        )

        color = np.clip(color, 0, 255)

        r, c = divmod(n, RITUAL_COLS)

        out[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw, :3] = color.astype(np.uint8)
        out[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw, 3] = (
            np.clip(alpha, 0, 1) * 255
        ).astype(np.uint8)

    Image.fromarray(out, "RGBA").save(OUT / "farolero_ritual.png")

    # medidas del personaje parado (cuadro 0) para igualarlo al dibujo base
    m0 = _dark_mask(cells[0])

    ys, xs = np.where(m0)

    top, bottom = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())

    return {
        "file": "farolero_ritual.png",
        "cols": RITUAL_COLS,
        "rows": RITUAL_ROWS,
        "cell": [cw, ch],
        "stand_h": bottom - top + 1,
        "foot": [(left + right) // 2, bottom + 1],
    }


def main():

    OUT.mkdir(parents=True, exist_ok=True)

    stand = build_standing()

    meta = {
        "stand": {"file": "salvador.png", "size": list(stand.size)},
        "walk": build_walk(stand),
        "ritual": build_ritual(),
    }

    with open(OUT / "farolero_anim.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()