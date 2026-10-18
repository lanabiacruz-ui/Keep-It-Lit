import pygame


SLIDE_DURATION = 1.0
SLIDE_DELAY = 0.15
SLIDE_DIRECTION = "left"

EDGE_COLOR = (255, 215, 140)
EDGE_WIDTH = 4
SHADOW_SIZE = 90
SHADOW_ALPHA = 150
DIM_ALPHA = 120


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


    @property
    def active(self):

        return self.t < self.delay + self.duration

    def update(self, dt):

        self.t += dt

        if not self.active:
            return "done"

        return None

    def progress(self):

        return _ease_in_out((self.t - self.delay) / max(0.001, self.duration))


    def _make_shadow(self):

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

        k = self.progress()

        dim = int(DIM_ALPHA * (1 - k) ** 1.2)

        if dim > 0:
            self._dim.set_alpha(dim)
            screen.blit(self._dim, (0, 0))

        if k >= 1.0:
            return

        w, h = self.w, self.h

        if self.direction == "left":

            x, y = -int(w * k), 0

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

        else:

            x, y = 0, int(h * k)

            screen.blit(pygame.transform.flip(self._shadow, False, True),
                        (0, y - SHADOW_SIZE))
            screen.blit(self.old, (x, y))
            pygame.draw.rect(screen, EDGE_COLOR, (0, y, w, EDGE_WIDTH))
