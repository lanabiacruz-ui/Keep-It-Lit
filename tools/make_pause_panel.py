"""Genera assets/maps/hud/pantallaesc_skins.png a partir de pantallaesc.png.

Agrega una fila nueva con dos botones angostos (Skins | Logros) entre
"Enemigos" y "Regresar", reusando el arte de los botones originales.
Los textos de los dos botones nuevos NO van en la imagen: los dibuja
states/pause_menu.py.  Si algun dia dibujan el panel a mano con los 5
botones, alcanza con reemplazar el png y ajustar PauseMenu.BUTTONS.

Uso:  python tools/make_pause_panel.py   (requiere Pillow y numpy)
"""
from pathlib import Path

import numpy as np
from PIL import Image

HUD = Path(__file__).resolve().parent.parent / "assets" / "maps" / "hud"

src = np.array(Image.open(HUD / "pantallaesc.png").convert("RGBA"))

H, W = src.shape[:2]

BTN_FILL = (141, 148, 158, 255)
PANEL_FILL = (99, 108, 121, 255)

PANEL_TOP, PANEL_BOTTOM = 185, 777     # filas del panel original
ROW_TOP, ROW_BOTTOM = 513, 605         # boton "Enemigos" (arte completo)
GAP_BOTTOM = 624                       # empieza el boton "Regresar"
ART_X1, ART_X2 = 549, 1081             # extremos horizontales del boton
CAP = 70                               # ancho de cada extremo redondeado
SPLIT_GAP = 14                         # separacion entre los dos botones

# 1) boton "Enemigos" sin texto
blank = src[ROW_TOP:ROW_BOTTOM].copy()
blank[12:80, 575 - 0:1055] = BTN_FILL

# 2) fila nueva: lados del panel originales, centro liso, 2 botones angostos
row = src[ROW_TOP:ROW_BOTTOM].copy()
row[:, ART_X1:ART_X2] = PANEL_FILL

half_w = (ART_X2 - ART_X1 - SPLIT_GAP) // 2


def half_button():
    out = np.zeros((blank.shape[0], half_w, 4), dtype=np.uint8)
    left = blank[:, ART_X1:ART_X1 + CAP]
    right = blank[:, ART_X2 - CAP:ART_X2]
    mid_col = blank[:, 800:801]
    out[:, :CAP] = left
    out[:, CAP:half_w - CAP] = np.repeat(mid_col, half_w - 2 * CAP, axis=1)
    out[:, half_w - CAP:] = right
    return out


hb = half_button()
row[:, ART_X1:ART_X1 + half_w] = hb
row[:, ART_X2 - half_w:ART_X2] = hb

gap = src[ROW_BOTTOM:GAP_BOTTOM]

parts = [
    src[PANEL_TOP:ROW_BOTTOM],
    gap,
    row,
    gap,
    src[GAP_BOTTOM:PANEL_BOTTOM + 1],
]

panel = np.concatenate(parts, axis=0)

out = np.zeros((H, W, 4), dtype=np.uint8)
top = (H - panel.shape[0]) // 2
out[top:top + panel.shape[0]] = panel

Image.fromarray(out).save(HUD / "pantallaesc_skins.png")

print("listo:", HUD / "pantallaesc_skins.png", "| panel top:", top)