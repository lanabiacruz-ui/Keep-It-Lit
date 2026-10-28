import math
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy import ndimage as ndi

import make_skin_sheets as M


def mix(a, b, k):

    return tuple(int(round(a[i] * (1 - k) + b[i] * k)) for i in range(3))


def star_pts(cx, cy, r_out, r_in, n=5, rot=-90):

    pts = []

    for i in range(n * 2):

        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180.0 / n)

        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    return pts


def scale_pts(pts, c, k):

    return [(c[0] + (x - c[0]) * k, c[1] + (y - c[1]) * k) for x, y in pts]


def shape_parts(name, cx, cy, s):

    if name == "star":
        return [("poly", star_pts(cx, cy, s, s * 0.45), 0)]

    if name == "burst":
        return [("poly", star_pts(cx, cy, s * 1.1, s * 0.5, 8), 0)]

    if name == "diamond":
        return [
            ("poly", [(cx, cy - s), (cx + 0.75 * s, cy), (cx, cy + s), (cx - 0.75 * s, cy)], 0),
            ("poly", [(cx, cy - 0.5 * s), (cx + 0.35 * s, cy), (cx, cy + 0.5 * s), (cx - 0.35 * s, cy)], 1),
        ]

    if name == "drop":
        return [
            ("poly", [(cx, cy - s), (cx - 0.66 * s, cy + 0.15 * s), (cx + 0.66 * s, cy + 0.15 * s)], 0),
            ("disc", (cx, cy + 0.3 * s), 0.72 * s, 0),
            ("disc", (cx - 0.25 * s, cy + 0.38 * s), 0.17 * s, 1),
        ]

    if name == "flame":
        return [
            ("poly", [
                (cx, cy - s), (cx + 0.55 * s, cy - 0.2 * s), (cx + 0.78 * s, cy + 0.35 * s),
                (cx + 0.4 * s, cy + 0.95 * s), (cx - 0.4 * s, cy + 0.95 * s),
                (cx - 0.78 * s, cy + 0.35 * s), (cx - 0.45 * s, cy - 0.15 * s),
                (cx - 0.2 * s, cy - 0.5 * s)], 0),
            ("poly", [
                (cx, cy - 0.1 * s), (cx + 0.38 * s, cy + 0.4 * s), (cx + 0.22 * s, cy + 0.8 * s),
                (cx - 0.22 * s, cy + 0.8 * s), (cx - 0.38 * s, cy + 0.4 * s)], 1),
        ]

    if name == "coin":
        return [
            ("disc", (cx, cy), s, 0),
            ("disc", (cx, cy), 0.66 * s, 1),
            ("disc", (cx, cy), 0.46 * s, 0),
        ]

    if name == "clock":
        return [
            ("disc", (cx, cy), s, 0),
            ("disc", (cx, cy), 0.76 * s, 1),
            ("line", [(cx, cy), (cx, cy - 0.58 * s)], 1.4, 0),
            ("line", [(cx, cy), (cx + 0.42 * s, cy + 0.2 * s)], 1.4, 0),
        ]

    if name == "door":
        return [
            ("poly", [(cx - 0.6 * s, cy - s), (cx + 0.6 * s, cy - s), (cx + 0.6 * s, cy + s), (cx - 0.6 * s, cy + s)], 0),
            ("poly", [(cx - 0.36 * s, cy - 0.7 * s), (cx + 0.36 * s, cy - 0.7 * s), (cx + 0.36 * s, cy + 0.7 * s), (cx - 0.36 * s, cy + 0.7 * s)], 1),
            ("disc", (cx + 0.2 * s, cy + 0.05 * s), 0.14 * s, 0),
        ]

    if name == "bolt":
        return [
            ("poly", [
                (cx + 0.2 * s, cy - s), (cx - 0.62 * s, cy + 0.12 * s), (cx - 0.05 * s, cy + 0.12 * s),
                (cx - 0.28 * s, cy + s), (cx + 0.66 * s, cy - 0.22 * s), (cx + 0.06 * s, cy - 0.22 * s)], 0),
        ]

    if name == "paw":
        return [
            ("disc", (cx, cy + 0.34 * s), 0.58 * s, 0),
            ("disc", (cx - 0.78 * s, cy - 0.2 * s), 0.27 * s, 0),
            ("disc", (cx - 0.28 * s, cy - 0.7 * s), 0.27 * s, 0),
            ("disc", (cx + 0.28 * s, cy - 0.7 * s), 0.27 * s, 0),
            ("disc", (cx + 0.78 * s, cy - 0.2 * s), 0.27 * s, 0),
        ]

    if name == "leaf":
        return [
            ("poly", [
                (cx - s, cy + 0.7 * s), (cx - 0.4 * s, cy - 0.4 * s), (cx + 0.2 * s, cy - 0.9 * s),
                (cx + 0.9 * s, cy - 0.8 * s), (cx + 0.7 * s, cy - 0.1 * s), (cx + 0.1 * s, cy + 0.6 * s)], 0),
            ("line", [(cx - 0.85 * s, cy + 0.7 * s), (cx + 0.6 * s, cy - 0.6 * s)], 1.2, 1),
        ]

    if name == "cross":
        return [
            ("line", [(cx - 0.8 * s, cy - 0.8 * s), (cx + 0.8 * s, cy + 0.8 * s)], 0.55 * s, 0),
            ("line", [(cx + 0.8 * s, cy - 0.8 * s), (cx - 0.8 * s, cy + 0.8 * s)], 0.55 * s, 0),
        ]

    if name == "heart":
        return [
            ("disc", (cx - 0.42 * s, cy - 0.3 * s), 0.55 * s, 0),
            ("disc", (cx + 0.42 * s, cy - 0.3 * s), 0.55 * s, 0),
            ("poly", [(cx - 0.94 * s, cy - 0.08 * s), (cx + 0.94 * s, cy - 0.08 * s), (cx, cy + s)], 0),
        ]

    return []


def paint_parts(rgb, shape, parts, cx, cy, mask, col, col2, ocol):

    for part in parts:

        kind = part[0]

        if kind == "poly":
            alpha = M._poly(shape, scale_pts(part[1], (cx, cy), 1.28), mask)
        elif kind == "disc":
            alpha = M._disc(shape, part[1], part[2] * 1.25 + 1.0, mask)
        else:
            alpha = M._line(shape, part[1], part[2] + 2.6, mask)

        M._paint(rgb, alpha, ocol)

    for part in parts:

        kind = part[0]
        color = col if part[-1] == 0 else col2

        if kind == "poly":
            alpha = M._poly(shape, part[1], mask)
        elif kind == "disc":
            alpha = M._disc(shape, part[1], part[2], mask)
        else:
            alpha = M._line(shape, part[1], part[2], mask)

        M._paint(rgb, alpha, color)


def head_box(hm):

    ys, xs = np.where(hm)

    return xs.min(), xs.max(), ys.min(), ys.max()


def head_band(rgb, shape, hm, y0f, y1f, color, ocol):

    x0, x1, y0, y1 = head_box(hm)

    hh = y1 - y0

    yy = np.arange(shape[0])[:, None]

    a = ((yy >= y0 + y0f * hh) & (yy <= y0 + y1f * hh)) & hm

    alpha = ndi.gaussian_filter(a.astype(np.float32), 0.6) * hm

    M._paint(rgb, np.clip(alpha * 1.25, 0, 1), color)

    edge = mix(color, ocol, 0.6)

    for yf in (y0f, y1f):

        yv = y0 + yf * hh

        M._paint(rgb, M._line(shape, [(x0, yv), (x1, yv)], 1.2, hm), edge)


def my_detail(sub, lab, n, kinds, head, torso, row, col, spec, ocol):

    rgb = sub[..., :3]
    shape = lab.shape
    d = spec["detail"]
    oc = tuple(float(v) for v in ocol)

    hm = lab == (head + 1)
    tm = (lab == (torso + 1)) if torso is not None else None

    for i in range(n):

        if i == head or i == torso or kinds[i + 1] == "limb":
            M._shade(rgb, lab == (i + 1), strength=0.26, ao=0.16)

    hx0, hx1, hy0, hy1 = head_box(hm)
    hw, hh = hx1 - hx0, hy1 - hy0
    hcx = (hx0 + hx1) / 2.0

    if d.get("gloss", True) and hh > 20:

        gx = hx0 + hw * (0.34 if row == 2 else 0.70)
        gy = hy0 + hh * 0.13

        img = M.Image.new("L", (shape[1], shape[0]), 0)
        M.ImageDraw.Draw(img).ellipse([gx - 14, gy - 5, gx + 14, gy + 5], fill=255)

        gm = (np.array(img) > 0) & hm

        rgb[gm] = np.array(mix(spec["head"], (255, 255, 255), 0.55), np.float32)

    if d.get("cheeks") and row == 1:

        for sgn in (-1, 1):

            m = M._disc(shape, (hcx + sgn * hw * 0.36, hy0 + hh * 0.72), 5.5, hm)

            M._paint(rgb, m * 0.8, d["cheeks"])

    if d.get("headband"):

        head_band(rgb, shape, hm, 0.16, 0.27, d["headband"], oc)

    if d.get("crown"):

        col = d["crown"]

        head_band(rgb, shape, hm, 0.22, 0.32, col, oc)

        for fx in (-0.26, 0.0, 0.26):

            bx = hcx + fx * hw

            tri = [(bx - 6, hy0 + hh * 0.23), (bx + 6, hy0 + hh * 0.23), (bx, hy0 + hh * 0.07)]

            M._paint(rgb, M._poly(shape, scale_pts(tri, (bx, hy0 + hh * 0.2), 1.25), hm), mix(col, oc, 0.6))
            M._paint(rgb, M._poly(shape, tri, hm), col)

    if d.get("plaster"):

        px = hx0 + hw * (0.28 if row == 3 else 0.72)
        py = hy0 + hh * 0.30

        a = math.radians(-28)

        c, s = math.cos(a), math.sin(a)

        pts = [(-11, -4.5), (11, -4.5), (11, 4.5), (-11, 4.5)]
        pts = [(px + x * c - y * s, py + x * s + y * c) for x, y in pts]

        M._paint(rgb, M._poly(shape, scale_pts(pts, (px, py), 1.18), hm), mix(d["plaster"], oc, 0.6))
        M._paint(rgb, M._poly(shape, pts, hm), d["plaster"])

        for off in (-3.5, 3.5):

            dx = px + off * c
            dy = py + off * s

            M._paint(rgb, M._disc(shape, (dx, dy), 1.0, hm), mix(d["plaster"], oc, 0.4))

    if d.get("sparkles"):

        if row == 2:
            spots = ((0.80, 0.34, 6.5), (0.64, 0.20, 4.0))
        elif row == 3:
            spots = ((0.20, 0.34, 6.5), (0.36, 0.20, 4.0))
        else:
            spots = ((0.78, 0.34, 6.5), (0.24, 0.24, 4.0))

        for fx, fy, r in spots:

            sx, sy = hx0 + hw * fx, hy0 + hh * fy

            M._paint(rgb, M._poly(shape, star_pts(sx, sy, r, r * 0.28, 4), hm), d["sparkles"])

    if tm is None:
        return

    ys, xs = np.where(tm)

    if len(ys) < 50:
        return

    x_min, x_max, y_min, y_max = xs.min(), xs.max(), ys.min(), ys.max()

    bw, bh = x_max - x_min, y_max - y_min
    cx = (x_min + x_max) / 2.0

    if d.get("stripes"):

        for f in (0.30, 0.52):

            M._paint(rgb, M._line(shape, [(x_min - 3, y_min + bh * f), (x_max + 3, y_min + bh * f)], 3.6, tm), d["stripes"])

    if d.get("bubbles"):

        for fx, fy, r in ((0.30, 0.40, 3.6), (0.66, 0.58, 2.8), (0.46, 0.78, 2.2), (0.74, 0.30, 1.8)):

            bx, by = x_min + bw * fx, y_min + bh * fy

            M._paint(rgb, M._disc(shape, (bx, by), r, tm), d["bubbles"])
            M._paint(rgb, M._disc(shape, (bx - r * 0.3, by - r * 0.3), r * 0.35, tm), (255, 255, 255))

    if d.get("cracks"):

        pts = [(cx - 12, y_min + bh * 0.1), (cx - 5, y_min + bh * 0.34), (cx - 11, y_min + bh * 0.5), (cx - 2, y_min + bh * 0.8)]

        M._paint(rgb, M._line(shape, pts, 1.3, tm), d["cracks"])

        pts2 = [(cx + 13, y_min + bh * 0.3), (cx + 7, y_min + bh * 0.52), (cx + 12, y_min + bh * 0.72)]

        M._paint(rgb, M._line(shape, pts2, 1.1, tm), d["cracks"])

    if d.get("scarf"):

        col = d["scarf"]

        edge = mix(col, oc, 0.55)

        top = M._poly(shape, [(x_min - 4, y_min - 2), (x_max + 4, y_min - 2), (x_max + 4, y_min + 9), (x_min - 4, y_min + 9)], tm)

        M._paint(rgb, top, col)
        M._paint(rgb, M._line(shape, [(x_min - 2, y_min + 9), (x_max + 2, y_min + 9)], 1.2, tm), edge)

        if row == 1:

            tail = [(cx + 6, y_min + 6), (cx + 20, y_min + 6), (cx + 18, y_min + bh * 0.66), (cx + 8, y_min + bh * 0.58)]

            M._paint(rgb, M._poly(shape, scale_pts(tail, (cx + 13, y_min + 20), 1.18), tm), edge)
            M._paint(rgb, M._poly(shape, tail, tm), col)
            M._paint(rgb, M._line(shape, [(cx + 9, y_min + bh * 0.5), (cx + 18, y_min + bh * 0.56)], 1.4, tm), edge)

    if d.get("belt"):

        col, buckle = d["belt"]

        y0, y1 = y_min + bh * 0.68, y_min + bh * 0.82

        band = M._poly(shape, [(x_min - 4, y0), (x_max + 4, y0), (x_max + 4, y1), (x_min - 4, y1)], tm)

        M._paint(rgb, band, col)

        edge = mix(col, oc, 0.6)

        M._paint(rgb, M._line(shape, [(x_min - 2, y0), (x_max + 2, y0)], 1.0, tm), edge)
        M._paint(rgb, M._line(shape, [(x_min - 2, y1), (x_max + 2, y1)], 1.0, tm), edge)

        if row == 1:

            by = (y0 + y1) / 2.0

            M._paint(rgb, M._poly(shape, [(cx - 6, by - 6), (cx + 6, by - 6), (cx + 6, by + 6), (cx - 6, by + 6)], tm), mix(buckle, oc, 0.6))
            M._paint(rgb, M._poly(shape, [(cx - 4.6, by - 4.6), (cx + 4.6, by - 4.6), (cx + 4.6, by + 4.6), (cx - 4.6, by + 4.6)], tm), buckle)
            M._paint(rgb, M._poly(shape, [(cx - 2, by - 2), (cx + 2, by - 2), (cx + 2, by + 2), (cx - 2, by + 2)], tm), mix(buckle, oc, 0.5))

    emb = d.get("emblem")

    if emb and row == 1:

        name, col, col2 = emb

        s = min(bw, bh) * 0.26

        cy = y_min + bh * (0.40 if d.get("belt") or d.get("scarf") else 0.46)

        paint_parts(rgb, shape, shape_parts(name, cx, cy, s), cx, cy, tm, col, col2, oc)

    legs, arms = [], []

    for i in range(n):

        if kinds[i + 1] != "limb":
            continue

        m = lab == (i + 1)

        yy, xx = np.where(m)

        if len(yy) < 30:
            continue

        (legs if yy.mean() > y_max - 0.15 * bh else arms).append((m, yy, xx))

    if d.get("boots"):

        for m, yy, xx in legs:

            low = m & (np.arange(shape[0])[:, None] > yy.min() + 0.5 * (yy.max() - yy.min()))

            alpha = ndi.gaussian_filter(low.astype(np.float32), 0.7) * m

            M._paint(rgb, np.clip(alpha * 1.2, 0, 1), d["boots"])

    if d.get("cuffs"):

        tcy = (y_min + y_max) / 2.0

        dist = np.hypot(np.arange(shape[0])[:, None] - tcy, np.arange(shape[1])[None, :] - cx)

        for m, yy, xx in arms:

            far = np.where(m, dist, -1).max()

            band = (m & (dist > far - 9.0)).astype(np.float32)

            band = ndi.gaussian_filter(band, 0.6) * m

            M._paint(rgb, np.clip(band * 1.25, 0, 1), d["cuffs"])


M.detail = my_detail


SKINS = {
    "derribapuertas": dict(
        outline=(52, 32, 22), head=(228, 186, 140), torso=(176, 112, 62), limb=(124, 80, 46),
        detail=dict(headband=(196, 66, 46), belt=((92, 96, 106), (238, 196, 72)),
                    emblem=("door", (236, 190, 120), (120, 74, 40)), boots=(70, 48, 34), cuffs=(98, 102, 112)),
    ),
    "saqueador": dict(
        outline=(60, 38, 14), head=(242, 212, 156), torso=(216, 160, 54), limb=(142, 94, 38),
        detail=dict(headband=(150, 44, 44), belt=((96, 60, 30), (250, 218, 90)),
                    emblem=("coin", (252, 222, 100), (168, 112, 30)), boots=(84, 54, 28), sparkles=(255, 246, 200)),
    ),
    "gelatinero": dict(
        outline=(22, 78, 50), head=(164, 234, 154), torso=(92, 202, 114), limb=(62, 164, 94),
        detail=dict(bubbles=(190, 250, 190), emblem=("drop", (214, 255, 206), (120, 214, 132)),
                    sparkles=(240, 255, 236)),
    ),
    "pirotecnico": dict(
        outline=(78, 24, 14), head=(255, 206, 150), torso=(228, 78, 40), limb=(255, 150, 44),
        detail=dict(headband=(255, 216, 70), emblem=("flame", (255, 222, 90), (255, 140, 40)),
                    belt=((122, 40, 22), (255, 216, 70)), boots=(110, 34, 20), cuffs=(255, 216, 70)),
    ),
    "dragon_monedas": dict(
        outline=(64, 14, 24), head=(238, 128, 112), torso=(180, 38, 54), limb=(124, 26, 42),
        detail=dict(crown=(252, 214, 84), emblem=("coin", (252, 218, 90), (150, 96, 20)),
                    belt=((250, 206, 70), (255, 240, 150)), boots=(250, 206, 70), sparkles=(255, 240, 180)),
    ),
    "zona_1": dict(
        outline=(112, 38, 74), head=(255, 218, 230), torso=(242, 132, 180), limb=(206, 92, 146),
        detail=dict(cheeks=(255, 140, 166), emblem=("star", (255, 246, 214), (255, 200, 120)),
                    stripes=(255, 190, 214), sparkles=(255, 255, 255), cuffs=(255, 220, 232)),
    ),
    "coctel": dict(
        outline=(18, 60, 46), head=(194, 238, 216), torso=(52, 152, 110), limb=(34, 110, 82),
        detail=dict(headband=(240, 230, 196), emblem=("flame", (255, 214, 90), (255, 130, 40)),
                    stripes=(120, 214, 170), boots=(240, 230, 196)),
    ),
    "region_1": dict(
        outline=(14, 64, 72), head=(180, 238, 232), torso=(40, 168, 160), limb=(28, 122, 126),
        detail=dict(scarf=(238, 180, 66), emblem=("diamond", (255, 244, 200), (240, 190, 80)),
                    belt=((22, 86, 96), (240, 190, 80)), boots=(22, 86, 96)),
    ),
    "abrazo_golem": dict(
        outline=(42, 30, 72), head=(216, 204, 240), torso=(124, 100, 186), limb=(88, 72, 144),
        detail=dict(emblem=("paw", (230, 218, 255), (170, 150, 220)), stripes=(150, 126, 210),
                    cuffs=(60, 48, 104), boots=(60, 48, 104)),
    ),
    "ojos_ciegos": dict(
        outline=(100, 88, 40), head=(255, 253, 230), torso=(255, 238, 134), limb=(242, 210, 92),
        detail=dict(emblem=("burst", (255, 255, 255), (255, 230, 120)), sparkles=(255, 255, 255),
                    headband=(255, 214, 90), cuffs=(255, 255, 240)),
    ),
    "desactivado": dict(
        outline=(20, 22, 28), head=(176, 184, 196), torso=(68, 74, 86), limb=(44, 48, 58),
        detail=dict(headband=(78, 206, 118), emblem=("clock", (226, 62, 52), (36, 38, 46)),
                    belt=((236, 192, 44), (60, 62, 70)), boots=(236, 192, 44)),
    ),
    "slime_brillante": dict(
        outline=(96, 64, 12), head=(255, 242, 176), torso=(252, 208, 72), limb=(234, 172, 42),
        detail=dict(bubbles=(255, 244, 190), emblem=("drop", (255, 252, 220), (255, 214, 90)),
                    sparkles=(255, 255, 255), cuffs=(255, 248, 200)),
    ),
    "zona_2": dict(
        outline=(46, 42, 38), head=(216, 206, 190), torso=(138, 128, 114), limb=(98, 90, 80),
        detail=dict(cracks=(66, 60, 54), belt=((72, 64, 56), (176, 168, 154)),
                    emblem=("diamond", (200, 190, 174), (110, 102, 92)), boots=(66, 60, 52)),
    ),
    "exterminador": dict(
        outline=(42, 10, 12), head=(236, 208, 200), torso=(192, 46, 46), limb=(66, 26, 30),
        detail=dict(headband=(36, 24, 28), emblem=("cross", (255, 240, 232), (255, 240, 232)),
                    belt=((40, 26, 30), (214, 70, 60)), boots=(40, 26, 30), cuffs=(214, 70, 60)),
    ),
    "entomologo": dict(
        outline=(46, 54, 24), head=(234, 226, 180), torso=(120, 142, 74), limb=(86, 102, 54),
        detail=dict(headband=(196, 170, 104), emblem=("leaf", (190, 230, 120), (70, 100, 44)),
                    belt=((112, 80, 46), (214, 190, 120)), boots=(112, 80, 46)),
    ),
    "ultimo_segundo": dict(
        outline=(16, 16, 42), head=(210, 210, 238), torso=(64, 68, 116), limb=(40, 44, 88),
        detail=dict(emblem=("clock", (250, 214, 100), (30, 32, 70)), sparkles=(255, 244, 200),
                    stripes=(92, 98, 160), cuffs=(250, 214, 100)),
    ),
    "intocable": dict(
        outline=(72, 86, 120), head=(242, 248, 255), torso=(208, 224, 252), limb=(166, 188, 228),
        detail=dict(headband=(150, 220, 250), emblem=("diamond", (130, 214, 250), (236, 248, 255)),
                    sparkles=(255, 255, 255), cuffs=(236, 248, 255), boots=(236, 248, 255)),
    ),
    "perder_50": dict(
        outline=(34, 42, 62), head=(194, 206, 222), torso=(86, 104, 132), limb=(62, 76, 100),
        detail=dict(plaster=(238, 216, 178), stripes=(112, 130, 158), cuffs=(238, 216, 178),
                    boots=(44, 54, 76)),
    ),
    "sin_red": dict(
        outline=(10, 8, 12), head=(124, 120, 132), torso=(40, 36, 46), limb=(26, 24, 32),
        detail=dict(headband=(228, 42, 62), emblem=("bolt", (255, 70, 84), (120, 20, 30)),
                    stripes=(228, 42, 62), cuffs=(228, 42, 62), boots=(228, 42, 62)),
    ),
}


def build(args):

    sid, out_dir = args

    spec = SKINS[sid]

    folder = os.path.join(out_dir, sid)

    os.makedirs(folder, exist_ok=True)

    for sheet in M.SHEETS:

        img = M.process_sheet(M.BASE + sheet, spec)
        img.save(os.path.join(folder, sheet), optimize=True)

    return sid


if __name__ == "__main__":

    out_dir = sys.argv[1] if len(sys.argv) > 1 else M.OUT

    ids = sys.argv[2:] or list(SKINS)

    jobs = [(sid, out_dir) for sid in ids]

    with Pool() as pool:

        for sid in pool.imap_unordered(build, jobs):
            print("ok", sid, flush=True)