"""Fuente del juego: un solo lugar para cambiarla.

Para usar otra fuente: copiar el .ttf a assets/fonts/ y cambiar FONT_FILE.
Si el archivo no existe, se usa la fuente por defecto de Pygame para que
el juego no se rompa.
"""
from pathlib import Path

import pygame

FONT_FILE = "YoungSerif-Regular.ttf"

_FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / FONT_FILE

# Font(None, n) de Pygame achica internamente el tamano (x0.6875); con un
# .ttf propio el tamano se usa tal cual. Este factor mantiene el tamano
# visual de todo el juego (y compensa que Young Serif es un poco mas ancha).
SIZE_SCALE = 0.66

_cache = {}


def load_font(size):
    """Devuelve la fuente del juego para el tamano que usaba Font(None, size)."""
    size = int(size)
    font = _cache.get(size)

    if font is None:
        if _FONT_PATH.exists():
            font = pygame.font.Font(str(_FONT_PATH), max(8, round(size * SIZE_SCALE)))
        else:
            font = pygame.font.Font(None, size)

        _cache[size] = font

    return font