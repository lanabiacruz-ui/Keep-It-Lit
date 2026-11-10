"""Sonidos de interfaz compartidos (menus del juego y menus de pausa)."""

import pygame

from core.audio_manager import audio

ARROWS = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
WASD = (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d)


def nav_key(key, letters=True):
    """True si la tecla mueve la seleccion de un menu."""

    return key in ARROWS or key == pygame.K_TAB or (letters and key in WASD)


def ui_sound(event, letters=True):
    """Click / Enter confirman, Esc vuelve, flechas (y WASD) mueven.

    letters=False en pantallas donde se escribe texto (nombre, clave)."""

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        audio.play("ui_confirm")

    elif event.type == pygame.KEYDOWN:

        if event.key == pygame.K_ESCAPE:
            audio.play("ui_back")

        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            audio.play("ui_confirm")

        elif nav_key(event.key, letters):
            audio.play("ui_move")