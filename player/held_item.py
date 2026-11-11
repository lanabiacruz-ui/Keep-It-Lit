"""El objeto elegido en la hotbar se ve en la mano del jugador.

El fosforo / vela / antorcha ya los lleva en una mano (la del dibujo del
personaje), asi que el objeto va en la OTRA mano.

Uso desde el juego:

    held = HeldItemRenderer()
    held.update(dt)                       # cada cuadro
    held.kick()                           # al usar el objeto (sube un poco)
    held.draw(screen, camera, player, item_id, behind=True)   # si mira arriba
    held.draw(screen, camera, player, item_id, behind=False)  # el resto
"""

import math

import pygame

from world.items import load_icon

# OJO: el sprite del jugador se dibuja con su alto "crudo" (74 px en
# pantalla) y NO se multiplica por el zoom de la camara; solo la posicion
# usa el zoom. Por eso todo lo de abajo esta en pixeles de PANTALLA.
ICON_SIZE = 26

# posicion de la mano libre dentro del dibujo del personaje, como fraccion
# del ancho / alto del sprite: (x, y, inclinacion en grados)
HAND = {
    "down": (0.84, 0.68, -14),
    "up": (0.16, 0.70, 14),
    "left": (0.80, 0.70, 10),
    "right": (0.20, 0.70, -10),
}

# ancho / alto del cuadro del personaje (Player.CELL_WIDTH / CELL_HEIGHT)
SPRITE_W_RATIO = 176 / 226

KICK_TIME = 0.28

# transparencia minima del objeto en la mano cuando el jugador es invisible
MIN_GHOST_ALPHA = 170


class HeldItemRenderer:

    def __init__(self):

        self._cache = {}
        self._kick = 0.0
        self._clock = 0.0

    # ------------------------------------------------------------------
    def kick(self):
        """Pequeno tiron hacia arriba al usar el objeto."""

        self._kick = KICK_TIME

    def update(self, dt):

        self._clock += dt

        if self._kick > 0.0:
            self._kick = max(0.0, self._kick - dt)

    # ------------------------------------------------------------------
    def _sprite(self, item_id, px, angle):

        key = (item_id, px, int(angle))

        spr = self._cache.get(key)

        if spr is None:

            icon = load_icon(item_id)

            if icon is None:
                return None

            if len(self._cache) > 80:
                self._cache.clear()

            spr = pygame.transform.smoothscale(icon, (px, px))

            if angle:
                spr = pygame.transform.rotate(spr, angle)

            self._cache[key] = spr

        return spr

    @staticmethod
    def _visible(player):
        """No se muestra en emotes, agarrado o muerto. Invisible SI se ve."""

        if getattr(player, "emote", None) is not None:
            return False

        if getattr(player, "grabbed", False):
            return False

        if getattr(player, "death_black", 0.0) > 0.0:
            return False

        if getattr(player, "death_sink", 0.0) > 0.0:
            return False

        return True

    # ------------------------------------------------------------------
    def draw(self, screen, camera, player, item_id, behind=False):
        """behind=True dibuja solo cuando mira hacia arriba (la mano queda
        detras del cuerpo); behind=False dibuja en los demas casos."""

        if item_id is None or not self._visible(player):
            return

        direction = getattr(player, "direction", "down")

        if (direction == "up") != behind:
            return

        hand = HAND.get(direction)

        if hand is None:
            return

        z = camera.zoom

        px = ICON_SIZE

        # pequeno balanceo mientras camina y "respiracion" cuando esta quieto
        if getattr(player, "moving", False):
            phase = getattr(player, "walk_phase", 0.0)
            bob = math.sin(phase * math.tau * 2.0) * 1.6
            tilt = math.sin(phase * math.tau * 2.0) * 6.0
        else:
            bob = math.sin(self._clock * 2.4) * 0.9
            tilt = math.sin(self._clock * 1.6) * 3.0

        # al usarlo: sube rapido y vuelve
        kick_lift = 0.0
        kick_spin = 0.0

        if self._kick > 0.0:
            k = 1.0 - self._kick / KICK_TIME
            kick_lift = math.sin(k * math.pi) * 14.0
            kick_spin = math.sin(k * math.pi) * 40.0

        spr = self._sprite(item_id, px, hand[2] + tilt + kick_spin)

        if spr is None:
            return

        # misma referencia que usa Player.draw: la base del rect, ya con zoom
        anchor = camera.apply(player.image_rect).midbottom

        height = player.image_rect.height      # sin zoom, como el sprite
        width = height * SPRITE_W_RATIO

        hx = anchor[0] + (hand[0] - 0.5) * width
        hy = anchor[1] - height + hand[1] * height

        # el salto si se multiplica por zoom (igual que en Player.draw)
        lift = getattr(player, "jump_height", 0.0) * z + kick_lift - bob

        # con la pocion de invisibilidad el personaje se ve translucido, pero
        # el objeto sigue legible (nunca baja de MIN_GHOST_ALPHA)
        ghost = getattr(player, "ghost_alpha", 255)

        spr.set_alpha(max(MIN_GHOST_ALPHA, int(ghost)) if ghost < 255 else 255)

        screen.blit(spr, spr.get_rect(center=(int(hx), int(hy - lift))))