import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent if Path(__file__).parent.name == "tools" else Path(__file__).resolve().parent
SRC = ROOT / "assets" / "maps" / "hud" / "slime.png"
OUT = ROOT / "assets" / "maps" / "combate"

S = 4
F = 64
EYE = (119, 95, 75)
CLOSED = (92, 70, 54)
GLINT = (240, 224, 206)
HIT_EYE = (52, 40, 32)
GROUND_OUT = 60.5


def load_base():

    im = np.array(Image.open(SRC).convert("RGBA"))

    dark = (im[..., 3] > 200) & (im[..., 0] < 135)
    labels, n = ndimage.label(dark)

    eyes = []
    mask = np.zeros(dark.shape, np.uint8)

    for i in range(1, n + 1):

        comp = labels == i
        area = int(comp.sum())

        if area > 150:
            continue

        ys, xs = np.where(comp)

        eyes.append({
            "cx": (xs.min() + xs.max() + 1) / 2,
            "cy": (ys.min() + ys.max() + 1) / 2,
            "w": xs.max() - xs.min() + 1,
            "h": ys.max() - ys.min() + 1,
        })

        mask |= comp.astype(np.uint8)

    eyes.sort(key=lambda e: e["cx"])

    mask = cv2.dilate(mask * 255, np.ones((3, 3), np.uint8), iterations=1)

    rgb = cv2.inpaint(im[..., :3], mask, 3, cv2.INPAINT_TELEA)

    clean = im.copy()
    clean[..., :3] = rgb

    alpha = im[..., 3] > 20
    ys, xs = np.where(alpha)

    return clean, eyes, (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1)


def upscale(rgba):

    img = Image.fromarray(rgba, "RGBA").resize((F * S, F * S), Image.LANCZOS)

    arr = np.array(img).astype(np.float32)
    arr[..., :3] *= arr[..., 3:4] / 255.0

    return arr


class Rig:

    def __init__(self):

        self.clean, self.eyes, box = load_base()

        self.big = upscale(self.clean)

        self.cx_src = (box[0] + box[1]) / 2
        self.top_src = box[2]
        self.ground_src = float(box[3])
        self.body_h = self.ground_src - self.top_src

        self.pose = None

    def _sx(self, t, p):

        t = min(1.0, max(0.0, t))

        return p["sxb"] + (p["sxt"] - p["sxb"]) * t

    def _lean(self, t, p):

        t = min(1.0, max(0.0, t))

        return p.get("lean", 0.0) * (t ** 1.6)

    def forward(self, x, y, p):

        h = self.ground_src - y
        t = h / self.body_h

        xo = F / 2 + (x - self.cx_src) * self._sx(t, p) + self._lean(t, p)
        yo = GROUND_OUT - p.get("lift", 0.0) - h * p["sy"]

        return xo, yo, self._sx(t, p)

    def render_body(self, p, white=0.0):

        n = F * S

        u = (np.arange(n, dtype=np.float32) + 0.5) / S
        xo, yo = np.meshgrid(u, u)

        h_src = (GROUND_OUT - p.get("lift", 0.0) - yo) / p["sy"]
        t = np.clip(h_src / self.body_h, 0.0, 1.0)

        sx = p["sxb"] + (p["sxt"] - p["sxb"]) * t
        lean = p.get("lean", 0.0) * (t ** 1.6)

        ys = self.ground_src - h_src
        xs = self.cx_src + (xo - F / 2 - lean) / sx

        map_x = (xs * S - 0.5).astype(np.float32)
        map_y = (ys * S - 0.5).astype(np.float32)

        out = cv2.remap(
            self.big, map_x, map_y, cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)
        )

        a = out[..., 3:4]

        rgb = np.where(a > 0, out[..., :3] / np.maximum(a, 1e-3) * 255.0, 0)

        if white > 0:
            rgb = rgb * (1 - white) + np.array([246, 241, 236]) * white

        res = np.concatenate([np.clip(rgb, 0, 255), a], axis=2)

        return Image.fromarray(res.astype(np.uint8), "RGBA")

    def draw_face(self, img, p, face):

        d = ImageDraw.Draw(img)

        kind = face.get("eyes", "open")
        dx, dy = face.get("look", (0.0, 0.0))
        mw = face.get("w", 1.0)
        mh = face.get("h", 1.0)

        for i, e in enumerate(self.eyes):

            ex = e["cx"] + dx
            ey = e["cy"] + dy

            cx, cy, sx = self.forward(ex, ey, p)

            w = e["w"] * sx * mw
            h = e["h"] * p["sy"] * mh

            cx *= S
            cy *= S
            w *= S
            h *= S

            if kind in ("open", "wide"):

                d.ellipse(
                    (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
                    fill=EYE + (255,)
                )

                if face.get("glint"):

                    gr = max(1.2, w * 0.17)
                    gx = cx - w * 0.14
                    gy = cy - h * 0.20

                    d.ellipse(
                        (gx - gr, gy - gr, gx + gr, gy + gr),
                        fill=GLINT + (255,)
                    )

            elif kind == "closed":

                aw = e["w"] * sx * 1.35 * S
                curve = aw * 0.22
                thick = int(2.1 * S)

                pts = []

                for k in range(13):

                    u = k / 12
                    px = cx - aw / 2 + aw * u
                    py = cy + curve * (1 - (2 * u - 1) ** 2) * 0.5 - curve * 0.1

                    pts.append((px, py))

                d.line(pts, fill=CLOSED + (255,), width=thick, joint="curve")

                r = thick / 2

                for px, py in (pts[0], pts[-1]):
                    d.ellipse((px - r, py - r, px + r, py + r), fill=CLOSED + (255,))

            elif kind == "hit":

                aw = e["w"] * sx * 0.62 * S
                ah = e["h"] * p["sy"] * 0.36 * S
                thick = max(2, int(1.6 * S))

                sign = 1 if i == 0 else -1

                pts = [
                    (cx - sign * aw, cy - ah),
                    (cx + sign * aw, cy),
                    (cx - sign * aw, cy + ah),
                ]

                d.line(pts, fill=HIT_EYE + (255,), width=thick, joint="curve")

        if face.get("mouth"):

            mx = (self.eyes[0]["cx"] + self.eyes[-1]["cx"]) / 2
            my = self.eyes[0]["cy"] + self.eyes[0]["h"] * 0.5 + 9.0

            cx, cy, sx = self.forward(mx, my, p)

            w = 4.2 * sx * face["mouth"] * S
            h = 5.0 * p["sy"] * face["mouth"] * S

            cx *= S
            cy *= S

            d.ellipse(
                (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
                fill=EYE + (255,)
            )

    def frame(self, p, face, white=0.0):

        img = self.render_body(p, white)

        self.draw_face(img, p, face)

        return img.resize((F, F), Image.LANCZOS)


def pose(sxb, sxt, sy, lift=0.0, lean=0.0):

    return {"sxb": sxb, "sxt": sxt, "sy": sy, "lift": lift, "lean": lean}


IDLE = [
    (pose(1.000, 1.000, 1.000, 0, 0.0), {"eyes": "open"}),
    (pose(0.996, 0.990, 1.030, 0, 0.4), {"eyes": "open", "look": (-0.4, 0)}),
    (pose(0.988, 0.975, 1.058, 0, 0.9), {"eyes": "open", "look": (-0.9, -0.3)}),
    (pose(0.996, 0.990, 1.028, 0, 0.3), {"eyes": "open", "look": (-0.3, 0)}),
    (pose(1.004, 1.000, 1.000, 0, 0.0), {"eyes": "closed"}),
    (pose(1.016, 1.004, 0.974, 0, -0.6), {"eyes": "open", "look": (0.9, 0.2)}),
]

WALK = [
    (pose(1.000, 1.000, 1.000, 0, 0.0), {"eyes": "open"}),
    (pose(1.050, 0.990, 0.900, 0, -0.5), {"eyes": "open", "h": 0.80}),
    (pose(1.087, 0.965, 0.760, 0, -1.1), {"eyes": "open", "h": 0.68, "look": (0, 0.6)}),
    (pose(0.940, 0.900, 1.070, 3.0, 1.0), {"eyes": "open", "h": 1.10, "w": 1.0, "look": (0, -0.5)}),
    (pose(0.910, 0.870, 1.100, 6.0, 1.7), {"eyes": "open", "h": 1.18, "w": 1.0, "look": (0, -0.8)}),
    (pose(0.950, 0.910, 1.060, 3.5, 0.8), {"eyes": "open", "h": 1.08, "look": (0, -0.3)}),
    (pose(1.087, 0.960, 0.740, 0, -0.9), {"eyes": "closed"}),
    (pose(0.990, 0.980, 1.060, 0, 0.6), {"eyes": "open", "look": (0, -0.2)}),
]

RUN = [
    (pose(1.000, 1.000, 1.000, 0, 0.0), {"eyes": "wide", "h": 1.18, "w": 1.0}),
    (pose(1.087, 0.970, 0.740, 0, -1.3), {"eyes": "wide", "h": 0.95, "w": 1.05, "look": (0, 0.5)}),
    (pose(0.900, 0.860, 1.090, 3.0, 1.5), {"eyes": "wide", "h": 1.30, "w": 1.02, "look": (0, -0.6)}),
    (pose(0.860, 0.820, 1.120, 5.5, 2.1), {"eyes": "wide", "h": 1.38, "w": 1.05, "look": (0, -0.9)}),
    (pose(0.900, 0.860, 1.090, 3.0, 1.2), {"eyes": "wide", "h": 1.30, "w": 1.02, "look": (0, -0.5)}),
    (pose(1.087, 0.955, 0.720, 0, -1.1), {"eyes": "closed"}),
]

HIT = (pose(1.070, 0.985, 0.900, 0, 2.6), {"eyes": "hit"})


def strip(rig, frames):

    sheet = Image.new("RGBA", (F * len(frames), F), (0, 0, 0, 0))

    for i, (p, face) in enumerate(frames):
        sheet.paste(rig.frame(p, face), (i * F, 0))

    return sheet


def main():

    rig = Rig()

    OUT.mkdir(parents=True, exist_ok=True)

    strip(rig, IDLE).save(OUT / "slime_idle.png")
    strip(rig, WALK).save(OUT / "slime_anim.png")
    strip(rig, RUN).save(OUT / "slime_correr.png")

    rig.frame(HIT[0], HIT[1], white=0.82).save(OUT / "slime_golpe.png")


if __name__ == "__main__":
    main()