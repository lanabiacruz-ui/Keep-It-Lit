import sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
BASE = str(ROOT / "assets" / "maps" / "player") + "/"
OUT = str(ROOT / "assets" / "maps" / "skins") + "/"
SHEETS = ["player.png", "player_phosphor.png", "player_vela.png", "player_antorcha.png"]
CW, CH = 190, 214

SKINS = {
    "pago_1": dict(outline=(41, 68, 67), head=(102, 154, 151), torso=(102, 154, 151),
                   limb=(102, 154, 151), detail="sash"),
    "pago_2": dict(outline=(26, 26, 26), head=(212, 181, 160), torso=(62, 120, 200),
                   limb=(30, 30, 30), detail="gloss"),
    "pago_3": dict(outline=(30, 34, 34), head=(114, 121, 121), torso=(52, 56, 56),
                   limb=(62, 64, 64), detail="suit"),
}

def classify(rgb, alpha, F, O):
    """Devuelve (t, resid): posicion del pixel entre contorno (0) y relleno (1)."""
    d = (F - O).astype(np.float32)
    dd = float((d * d).sum())
    v = rgb.astype(np.float32) - O.astype(np.float32)
    t = (v @ d) / dd
    proj = O.astype(np.float32) + t[..., None] * d
    resid = np.sqrt(((rgb - proj) ** 2).sum(-1))
    return t, resid

def process_sheet(path, spec):
    im = np.array(Image.open(path).convert("RGBA"))
    H, W = im.shape[:2]
    rgb = im[..., :3].astype(np.float32)
    a = im[..., 3]

    # colores base: relleno = mediana de pixeles claros del cuerpo; contorno = oscuros neutros
    spread = rgb.max(-1) - rgb.min(-1)
    cand = (a > 250) & (rgb.max(-1) > 140) & (rgb.max(-1) < 215) & (spread < 45) & (spread > 8)
    F = np.median(rgb[cand], axis=0)
    dark = (a > 250) & (rgb.max(-1) < 60) & (spread < 25)
    O = np.median(rgb[dark], axis=0)

    t, resid = classify(rgb, a, F, O)
    belongs = (a > 0) & (resid < np.where(t < 0.6, 16, 34)) & (t > -0.15) & (t < 1.2)

    out = im.astype(np.float32).copy()
    ocol = np.array(spec["outline"], np.float32)

    for r in range(4):
        for c in range(5):
            y0, x0 = r * CH, c * CW
            sl = (slice(y0, y0 + CH), slice(x0, x0 + CW))
            cb = belongs[sl]
            ct = np.clip(t[sl], 0, 1)
            ca = a[sl]

            fill = cb & (t[sl] > 0.8) & (ca > 250)
            lab, n = ndi.label(fill)
            if n == 0:
                continue
            areas = ndi.sum(fill, lab, range(1, n + 1))
            cents = ndi.center_of_mass(fill, lab, range(1, n + 1))
            order = np.argsort(-areas)
            head = order[0]
            region_of = {}
            region_of[head] = "head"
            torso = None
            for i in order[1:]:
                if areas[i] > 1500 and cents[i][0] > cents[head][0]:
                    torso = i
                    break
            if torso is not None:
                region_of[torso] = "torso"
            # mapa componente -> color
            colors = np.zeros((n + 1, 3), np.float32)
            kinds = ["limb"] * (n + 1)
            for i in range(n):
                kind = region_of.get(i, "limb")
                kinds[i + 1] = kind
                colors[i + 1] = spec[kind]
            # propagar etiquetas a los pixeles de borde (antialias)
            dist, (iy, ix) = ndi.distance_transform_edt(lab == 0, return_indices=True)
            nearest = lab[iy, ix]
            near_ok = dist <= 4
            Fcol = colors[nearest]

            tt = ct[..., None]
            newc = ocol * (1 - tt) + Fcol * tt
            apply = cb & near_ok & (nearest > 0)
            # contorno/ojos/boca (oscuros sin componente cercano)
            dark_px = cb & (t[sl] < 0.5)
            apply = apply | (dark_px & ~near_ok) | (dark_px & near_ok)
            # donde no hay componente cercano, el color es el contorno puro
            newc = np.where((nearest[..., None] > 0) & near_ok[..., None], newc, ocol[None, None, :])
            sub = out[sl]
            sub[..., :3] = np.where(apply[..., None], newc, sub[..., :3])

            # sombreado suave: conserva un poco de la textura original en el relleno
            tex = (rgb[sl].mean(-1) - F.mean())
            sub[..., :3] += np.where((fill)[..., None], tex[..., None] * 0.5, 0)

            detail(sub, lab, n, kinds, head, torso, r, c, spec, ocol)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")

def detail(sub, lab, n, kinds, head, torso, row, col, spec, ocol):
    d = spec["detail"]
    h, w = lab.shape
    if torso is not None:
        tm = lab == (torso + 1)
        ys, xs = np.where(tm)
        if len(ys) == 0:
            return
        y_min, y_max, x_min, x_max = ys.min(), ys.max(), xs.min(), xs.max()
    if d == "sash" and torso is not None:
        img = Image.new("L", (w, h), 0)
        dr = ImageDraw.Draw(img)
        bw = x_max - x_min
        bh = y_max - y_min
        flip = (row == 3)
        for off in (0.10, 0.38):
            if not flip:
                p0 = (x_min - 4, y_min + bh * off)
                p1 = (x_max + 4, y_min + bh * (off + 0.42))
            else:
                p0 = (x_max + 4, y_min + bh * off)
                p1 = (x_min - 4, y_min + bh * (off + 0.42))
            dr.line([p0, p1], fill=255, width=4)
        m = (np.array(img) > 0) & tm
        sub[..., :3][m] = ocol
    elif d == "gloss" and head is not None and row in (1, 2, 3):
        hm = lab == (head + 1)
        ys, xs = np.where(hm)
        if len(ys):
            cx = xs.min() + (xs.max() - xs.min()) * (0.72 if row != 2 else 0.35)
            cy = ys.min() + (ys.max() - ys.min()) * 0.17
            img = Image.new("L", (w, h), 0)
            ImageDraw.Draw(img).ellipse([cx - 14, cy - 5, cx + 14, cy + 5], fill=255)
            m = (np.array(img) > 0) & hm
            sub[..., :3][m] = np.array([236, 208, 190], np.float32)
    elif d == "suit" and torso is not None:
        suit_detail(sub, lab, n, kinds, head, torso, row, tm, x_min, x_max, y_min, y_max)

SS = 4

def _soft(shape, draw_fn, mask):
    """Dibuja a 4x y reduce: bordes suaves. Devuelve alfa float (0..1) limitado a `mask`."""
    img = Image.new("L", (shape[1] * SS, shape[0] * SS), 0)
    draw_fn(ImageDraw.Draw(img), lambda p: (p[0] * SS, p[1] * SS))
    small = img.resize((shape[1], shape[0]), Image.LANCZOS)
    return (np.array(small).astype(np.float32) / 255.0) * mask.astype(np.float32)

def _poly(shape, pts, mask):
    return _soft(shape, lambda d, S: d.polygon([S(p) for p in pts], fill=255), mask)

def _line(shape, pts, width, mask):
    return _soft(shape, lambda d, S: d.line([S(p) for p in pts], fill=255, width=int(width * SS)), mask)

def _disc(shape, c, r, mask):
    return _soft(shape, lambda d, S: d.ellipse([S((c[0] - r, c[1] - r)), S((c[0] + r, c[1] + r))], fill=255), mask)

def _paint(rgb, alpha, color):
    rgb[...] = rgb * (1 - alpha[..., None]) + np.array(color, np.float32) * alpha[..., None]

def _shade(rgb, comp_mask, strength=0.20, ao=0.14):
    """Luz desde arriba a la izquierda + oclusion suave en los bordes."""
    ys, xs = np.where(comp_mask)
    if len(ys) < 20:
        return
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    X = (np.arange(comp_mask.shape[1])[None, :] - x0) / max(1, x1 - x0)
    Y = (np.arange(comp_mask.shape[0])[:, None] - y0) / max(1, y1 - y0)
    grad = 1.0 + strength * (0.5 - (X * 0.5 + Y * 0.5)) * 1.0
    dist = ndi.distance_transform_edt(comp_mask)
    edge = (1.0 - ao) + ao * np.clip(dist / 5.0, 0, 1)
    f = (grad * edge)[..., None]
    rgb[comp_mask] = np.clip(rgb[comp_mask] * f[comp_mask], 0, 255)

def suit_detail(sub, lab, n, kinds, head, torso, row, tm, x_min, x_max, y_min, y_max):
    shape = lab.shape
    rgb = sub[..., :3]
    bh = y_max - y_min
    cx = (x_min + x_max) / 2.0
    WHITE = (222, 224, 224)
    WHITE_SH = (170, 174, 174)
    LAPEL = (84, 89, 89)
    LAPEL_DK = (36, 40, 40)
    TIE = (20, 22, 24)
    TIE_HI = (62, 66, 72)
    BUTTON = (128, 132, 132)
    PANTS = (66, 68, 68)
    SHOE = (30, 32, 32)
    CUFF = (214, 217, 217)
    JACKET_TOP = (78, 82, 82)

    # --- colores base de piernas y brazos ---
    tcy = (y_min + y_max) / 2.0
    legs, arms = [], []
    for i in range(n):
        if kinds[i + 1] != "limb":
            continue
        m = lab == (i + 1)
        ys, xs = np.where(m)
        if len(ys) < 30:
            continue
        (legs if ys.mean() > y_max - 0.15 * bh else arms).append((m, ys, xs))

    for m, ys, xs in legs:
        rgb[m] = PANTS
        low = m & (np.arange(shape[0])[:, None] > ys.min() + 0.55 * (ys.max() - ys.min()))
        rgb[low] = SHOE

    # --- sombreado de todas las piezas ---
    for i in range(n):
        if kinds[i + 1] == "limb" or i in (head, torso):
            _shade(rgb, lab == (i + 1), strength=0.22 if i == head else 0.30)

    # --- zapatos: brillo ---
    for m, ys, xs in legs:
        yy = ys.min() + 0.78 * (ys.max() - ys.min())
        sh = _line(shape, [(xs.min() + 3, yy), (xs.min() + (xs.max() - xs.min()) * 0.55, yy)], 1.1, m)
        _paint(rgb, sh * 0.35, (96, 100, 100))

    # --- puños blancos con gemelo ---
    d_all = np.hypot(np.arange(shape[0])[:, None] - tcy, np.arange(shape[1])[None, :] - cx)
    for m, ys, xs in arms:
        far = np.where(m, d_all, -1).max()
        band = (m & (d_all > far - 10.5) & (d_all <= far - 6.5)).astype(np.float32)
        band = ndi.gaussian_filter(band, 0.6) * m
        _paint(rgb, np.clip(band * 1.3, 0, 1), CUFF)
        shadow = (m & (d_all > far - 12) & (d_all <= far - 10.5)).astype(np.float32)
        _paint(rgb, ndi.gaussian_filter(shadow, 0.6) * m * 0.5, LAPEL_DK)

    top = y_min + 1.0

    if row == 1:   # ---------- FRENTE ----------
        # solapas como paneles (un tono mas claro que el saco)
        for sgn in (-1, 1):
            panel = _poly(shape, [
                (cx + sgn * 20, top - 1), (cx + sgn * 7, top - 1),
                (cx + sgn * 1, y_min + bh * 0.52), (cx + sgn * 11, y_min + bh * 0.58),
                (cx + sgn * 21, y_min + bh * 0.34)], tm)
            _paint(rgb, panel * 0.85, JACKET_TOP)
            _paint(rgb, _line(shape, [(cx + sgn * 20, top), (cx + sgn * 22, y_min + bh * 0.34),
                                      (cx + sgn * 11, y_min + bh * 0.58), (cx + sgn * 1, y_min + bh * 0.52)], 1.2, tm), LAPEL_DK)
        # camisa
        shirt = _poly(shape, [(cx - 13, top - 1), (cx + 13, top - 1), (cx, y_min + bh * 0.66)], tm)
        _paint(rgb, shirt, WHITE)
        _paint(rgb, _line(shape, [(cx - 13, top), (cx, y_min + bh * 0.64)], 1.0, tm), WHITE_SH)
        # cuello de camisa (dos puntas)
        for sgn in (-1, 1):
            _paint(rgb, _poly(shape, [(cx + sgn * 3, top - 1), (cx + sgn * 15, top - 1),
                                      (cx + sgn * 11, top + 9)], tm), WHITE)
            _paint(rgb, _line(shape, [(cx + sgn * 15, top), (cx + sgn * 11, top + 9), (cx + sgn * 3, top + 2)], 0.9, tm), WHITE_SH)
        # corbata
        knot = _poly(shape, [(cx - 4.5, top), (cx + 4.5, top), (cx + 3.2, top + 8), (cx - 3.2, top + 8)], tm)
        _paint(rgb, knot, TIE)
        tie = _poly(shape, [(cx - 3.2, top + 7), (cx + 3.2, top + 7), (cx + 6.2, y_min + bh * 0.72),
                            (cx, y_min + bh * 0.84), (cx - 6.2, y_min + bh * 0.72)], tm)
        _paint(rgb, tie, TIE)
        _paint(rgb, _line(shape, [(cx - 1.2, top + 8), (cx - 2.4, y_min + bh * 0.62)], 1.0, tm), TIE_HI)
        # botones + costura
        for k in (0.86, 0.96):
            c = (cx + 3, y_min + bh * k)
            _paint(rgb, _disc(shape, c, 1.9, tm), BUTTON)
            _paint(rgb, _disc(shape, (c[0] - 0.5, c[1] - 0.6), 0.7, tm), (190, 194, 194))
        _paint(rgb, _line(shape, [(cx + 1, y_min + bh * 0.72), (cx + 1, y_max)], 0.9, tm), LAPEL_DK)
    elif row == 0:  # ---------- ESPALDA ----------
        _paint(rgb, _line(shape, [(cx, top), (cx, y_max)], 1.6, tm), LAPEL_DK)
        _paint(rgb, _line(shape, [(cx + 1.4, top), (cx + 1.4, y_max)], 0.9, tm), LAPEL)
        # cuello de camisa apenas visible
        _paint(rgb, _poly(shape, [(cx - 11, top - 1), (cx + 11, top - 1), (cx + 8, top + 3), (cx - 8, top + 3)], tm), WHITE_SH)
        # abertura trasera del saco
        _paint(rgb, _line(shape, [(cx, y_min + bh * 0.62), (cx, y_max)], 2.0, tm), LAPEL_DK)
        _paint(rgb, _line(shape, [(cx - 15, y_min + bh * 0.2), (cx - 13, y_min + bh * 0.62)], 0.9, tm), LAPEL)
        _paint(rgb, _line(shape, [(cx + 15, y_min + bh * 0.2), (cx + 13, y_min + bh * 0.62)], 0.9, tm), LAPEL)
    else:           # ---------- PERFILES ----------
        sgn = -1 if row == 2 else 1
        fx = (x_min if row == 2 else x_max)
        panel = _poly(shape, [(fx - sgn * 0, top - 1), (fx - sgn * 9, top - 1),
                              (fx - sgn * 12, y_min + bh * 0.55), (fx - sgn * 1, y_min + bh * 0.45)], tm)
        _paint(rgb, panel * 0.85, JACKET_TOP)
        _paint(rgb, _line(shape, [(fx - sgn * 9, top), (fx - sgn * 12, y_min + bh * 0.55)], 1.1, tm), LAPEL_DK)
        _paint(rgb, _poly(shape, [(fx - sgn * 1, top - 1), (fx - sgn * 6, top - 1), (fx - sgn * 4, top + 6)], tm), WHITE)
        for k in (0.66, 0.84):
            c = (fx - sgn * 7, y_min + bh * k)
            _paint(rgb, _disc(shape, c, 1.8, tm), BUTTON)
            _paint(rgb, _disc(shape, (c[0] - 0.5, c[1] - 0.6), 0.6, tm), (190, 194, 194))

if __name__ == "__main__":
    for sid, spec in SKINS.items():
        os.makedirs(OUT + sid, exist_ok=True)
        for s in SHEETS:
            img = process_sheet(BASE + s, spec)
            img.save(OUT + sid + "/" + s, optimize=True)
        print("ok", sid)