from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent if HERE.name == "tools" else HERE
DIR = ROOT / "assets" / "maps" / "combate"

F = 56
TORSO_END = 48
TORSO_BOTTOM = TORSO_END - 1
ROW_A = 20
ROW_B = 43
FEET_SPLIT_X = 26


def load_frames(name):

    sheet = Image.open(DIR / name).convert("RGBA")

    return [
        np.array(sheet.crop((i * F, 0, (i + 1) * F, F)))
        for i in range(sheet.width // F)
    ]


def glow_mask(img):

    r = img[..., 0].astype(int)
    b = img[..., 2].astype(int)

    return (img[..., 3] > 200) & (r > 140) & (r - b > 70)


def blend(a, b, f):

    near = a if f < 0.5 else b

    out = near.copy()

    mask = (glow_mask(a) | glow_mask(b)) & (a[..., 3] > 200) & (b[..., 3] > 200)

    mixed = a[..., :3].astype(np.float32) * (1 - f) + b[..., :3].astype(np.float32) * f

    out[..., :3][mask] = (mixed[mask] + 0.5).astype(np.uint8)

    return out


def shift_row(row, dx):

    if dx == 0:
        return row

    out = np.zeros_like(row)

    if dx > 0:
        out[dx:] = row[:-dx]
    else:
        out[:dx] = row[-dx:]

    return out


def torso_rows(stretch, use_b):

    rows = list(range(TORSO_END))

    slots = [ROW_A, ROW_B, ROW_A, ROW_B] if use_b else [ROW_A, ROW_A, ROW_A, ROW_A]

    for k in range(abs(stretch)):

        target = slots[k]

        if stretch > 0:
            rows.insert(rows.index(target), target)
        else:
            rows.remove(target if use_b or k == 0 else ROW_A - k)

    return rows


def rig(img, stretch=0, lean=0, dx=0, foot_l=(0, 0), foot_r=(0, 0), use_b=True):

    out = np.zeros_like(img)

    feet = img[TORSO_END:].copy()

    for (fx, fy), cols in (
        (foot_l, slice(0, FEET_SPLIT_X)),
        (foot_r, slice(FEET_SPLIT_X, F)),
    ):

        part = np.zeros_like(feet)
        part[:, cols] = feet[:, cols]

        for r in range(part.shape[0]):

            y = TORSO_END + r + fy

            if 0 <= y < F:

                row = shift_row(part[r], fx)

                mask = row[:, 3] > 0
                out[y][mask] = row[mask]

    rows = torso_rows(stretch, use_b)

    top = TORSO_BOTTOM - (len(rows) - 1)

    for i, src in enumerate(rows):

        y = top + i

        if y < 0:
            continue

        t = max(0.0, (TORSO_BOTTOM - y) / TORSO_BOTTOM)

        shift = dx + int(round(lean * (t ** 1.5)))

        row = shift_row(img[src], shift)

        mask = row[:, 3] > 0
        out[y][mask] = row[mask]

    return out


def sheet(frames, path):

    img = Image.new("RGBA", (F * len(frames), F), (0, 0, 0, 0))

    for i, arr in enumerate(frames):
        img.paste(Image.fromarray(arr, "RGBA"), (i * F, 0))

    img.save(path)


def main():

    idle = load_frames("tronco.png")[0]
    charge = load_frames("tronco_carga.png")
    shoot = load_frames("tronco_disparo.png")

    idle_cfg = [
        (0, 0), (0, 0), (1, 1), (1, 1), (1, 0), (0, 0), (-1, -1), (-1, -1),
    ]

    sheet(
        [rig(idle, stretch=s, lean=l) for s, l in idle_cfg],
        DIR / "tronco_idle.png"
    )

    walk_cfg = [
        dict(stretch=-1, lean=0, dx=0, foot_l=(0, 0), foot_r=(0, 0)),
        dict(stretch=0, lean=1, dx=1, foot_l=(0, -1), foot_r=(0, 0)),
        dict(stretch=1, lean=1, dx=1, foot_l=(1, -3), foot_r=(0, 0)),
        dict(stretch=0, lean=0, dx=1, foot_l=(1, -2), foot_r=(0, 0)),
        dict(stretch=-1, lean=0, dx=0, foot_l=(0, 0), foot_r=(0, 0)),
        dict(stretch=0, lean=-1, dx=-1, foot_l=(0, 0), foot_r=(0, -1)),
        dict(stretch=1, lean=-1, dx=-1, foot_l=(0, 0), foot_r=(-1, -3)),
        dict(stretch=0, lean=0, dx=-1, foot_l=(0, 0), foot_r=(-1, -2)),
    ]

    sheet([rig(idle, **cfg) for cfg in walk_cfg], DIR / "tronco_anim.png")

    charge_cfg = [
        (0.0, 0, 0), (0.5, 0, 0), (1.0, 1, 0), (1.5, 1, 1), (2.0, 1, -1),
        (2.5, 1, 1), (3.0, 0, -1), (3.0, -1, 1),
    ]

    frames = []

    for q, s, l in charge_cfg:

        lo = int(q)
        hi = min(3, lo + 1)

        src = blend(charge[lo], charge[hi], q - lo) if hi != lo else charge[lo]

        frames.append(rig(src, stretch=s, lean=l))

    frames.append(rig(shoot[0], stretch=0, lean=-1))
    frames.append(rig(shoot[0], stretch=-1, lean=1))

    sheet(frames, DIR / "tronco_carga_anim.png")

    shoot_cfg = [
        (1, 0, 0), (1, -1, 0), (2, 0, -1), (2, -1, 1), (2, 0, -1),
        (3, 0, 0), (3, 1, 0), (3, 0, 0),
    ]

    frames = [
        rig(shoot[i], stretch=s, lean=l, use_b=False) for i, s, l in shoot_cfg
    ]

    frames.append(rig(idle, stretch=0, lean=0))
    frames.append(rig(idle, stretch=0, lean=0))

    sheet(frames, DIR / "tronco_disparo_anim.png")


if __name__ == "__main__":
    main()