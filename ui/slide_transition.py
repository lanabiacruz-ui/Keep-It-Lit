"""Transicion de entrada al juego: la pantalla anterior (el ultimo cuadro del
comic, de la carga o de "Perdiste") se desliza y deja ver el juego que esta
abajo.

Se usa desde main.py cuando empieza una partida nueva (despues del comic),
cuando se continua una partida guardada y cuando volves a jugar despues de
perder.

Mientras dura, main.py NO le pasa eventos ni tiempo al juego. Asi el
tutorial (que se abre apenas se crea la partida nueva) y los enemigos
esperan a que termine la transicion, y los clicks no se cuelan.
"""

import pygame


# ---------- AJUSTES ----------

SLIDE_DURATION = 1.0        # cuanto tarda en deslizarse (segundos)
SLIDE_DELAY = 0.15          # pausita antes de empezar a moverse
SLIDE_DIRECTION = "left"    # "left", "right", "up" o "down"

EDGE_COLOR = (255, 215, 140)   # lineita de luz en el borde de la pantalla
EDGE_WIDTH = 4
SHADOW_SIZE = 90            # ancho de la sombra que tira la pantalla
SHADOW_ALPHA = 150          # que tan oscura es esa sombra (0 a 255)
DIM_ALPHA = 120             # el juego arranca un poco oscuro y se aclara


def _ease_in_out(k):

    k = max(0.0, min(1.0, k))

    if k < 0.5:
        return 4 * k * k * k

    return 1 - ((-2 * k + 2) ** 3) / 2


class SlideTransition:

    def __init__(self, old_frame, duration=SLIDE_DURATION,
                 delay=SLIDE_DELAY, direction=SLIDE_DIRECTION):

        self.old = old_frame
        self.w, self.h = old_frame.get_size()

        self.duration = duration
        self.delay = delay
        self.direction = direction

        self.t = 0.0

        self._shadow = self._make_shadow()
        self._dim = pygame.Surface((self.w, self.h))
        self._dim.fill((0, 0, 0))

    # ----- estado -----

    @property
    def active(self):

        return self.t < self.delay + self.duration

    def update(self, dt):

        self.t += dt

        if not self.active:
            return "done"

        return None

    def progress(self):
        """0 = pantalla anterior completa, 1 = ya se fue."""

        return _ease_in_out((self.t - self.delay) / max(0.001, self.duration))

    # ----- dibujo -----

    def _make_shadow(self):
        """Degradado oscuro que cae sobre el juego, pegado a la pantalla
        que se va (se dibuja del lado del borde)."""

        horizontal = self.direction in ("left", "right")

        size = SHADOW_SIZE

        surf = pygame.Surface(
            (size, self.h) if horizontal else (self.w, size),
            pygame.SRCALPHA
        )

        for i in range(size):

            a = int(SHADOW_ALPHA * (1 - i / size) ** 2)

            if horizontal:
                pygame.draw.line(surf, (0, 0, 0, a), (i, 0), (i, self.h))
            else:
                pygame.draw.line(surf, (0, 0, 0, a), (0, i), (self.w, i))

        return surf

    def draw(self, screen):
        """Se llama DESPUES de dibujar el juego."""

        k = self.progress()

        # El juego que esta abajo se va aclarando
        dim = int(DIM_ALPHA * (1 - k) ** 1.2)

        if dim > 0:
            self._dim.set_alpha(dim)
            screen.blit(self._dim, (0, 0))

        if k >= 1.0:
            return

        w, h = self.w, self.h

        if self.direction == "left":

            x, y = -int(w * k), 0

            # Sombra a la derecha del borde, con el borde de luz
            screen.blit(self._shadow, (x + w, 0))
            screen.blit(self.old, (x, y))
            pygame.draw.rect(screen, EDGE_COLOR, (x + w - EDGE_WIDTH, 0, EDGE_WIDTH, h))

        elif self.direction == "right":

            x, y = int(w * k), 0

            screen.blit(pygame.transform.flip(self._shadow, True, False),
                        (x - SHADOW_SIZE, 0))
            screen.blit(self.old, (x, y))
            pygame.draw.rect(screen, EDGE_COLOR, (x, 0, EDGE_WIDTH, h))

        elif self.direction == "up":

            x, y = 0, -int(h * k)

            screen.blit(self._shadow, (0, y + h))
            screen.blit(self.old, (x, y))
            pygame.draw.rect(screen, EDGE_COLOR, (0, y + h - EDGE_WIDTH, w, EDGE_WIDTH))

        else:  # "down"

            x, y = 0, int(h * k)

            screen.blit(pygame.transform.flip(self._shadow, False, True),
                        (0, y - SHADOW_SIZE))
            screen.blit(self.old, (x, y))
            pygame.draw.rect(screen, EDGE_COLOR, (0, y, w, EDGE_WIDTH))