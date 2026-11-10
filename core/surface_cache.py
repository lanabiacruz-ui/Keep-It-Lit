"""Cachés chicas para no recalcular cada frame lo que no cambia.

- scaled(): escala una imagen y recuerda el resultado.
- render_text(): renderiza texto y recuerda el resultado.

Las superficies devueltas son compartidas: NO hay que modificarlas
(nada de fill/set_alpha sobre ellas); si hace falta, usar .copy().
Cada caché tiene un límite (LRU) para que la memoria no crezca.
"""
from collections import OrderedDict

import pygame

_MAX_SCALED = 512
_MAX_TEXT = 1024

_scaled_cache = OrderedDict()
_text_cache = OrderedDict()


def scaled(surface, size, smooth=True):
    """Igual que pygame.transform.(smooth)scale pero con caché.

    La clave usa id(surface); se guarda también la superficie original
    para que ese id no pueda reutilizarse mientras la entrada exista.
    """
    w = max(1, int(size[0]))
    h = max(1, int(size[1]))

    if surface.get_size() == (w, h):
        return surface

    key = (id(surface), w, h, bool(smooth))
    entry = _scaled_cache.get(key)

    if entry is not None and entry[0] is surface:
        _scaled_cache.move_to_end(key)
        return entry[1]

    fn = pygame.transform.smoothscale if smooth else pygame.transform.scale
    result = fn(surface, (w, h))

    _scaled_cache[key] = (surface, result)

    if len(_scaled_cache) > _MAX_SCALED:
        _scaled_cache.popitem(last=False)

    return result


def render_text(font, text, color):
    """Igual que font.render(text, True, color) pero con caché."""
    key = (id(font), text, tuple(color))
    entry = _text_cache.get(key)

    if entry is not None and entry[0] is font:
        _text_cache.move_to_end(key)
        return entry[1]

    result = font.render(text, True, color)

    _text_cache[key] = (font, result)

    if len(_text_cache) > _MAX_TEXT:
        _text_cache.popitem(last=False)

    return result


def clear():
    _scaled_cache.clear()
    _text_cache.clear()