import math

import pygame


# Rueda de emotes: 3 casilleros fijos, sin seleccion.
# Click en uno para hacerlo.

EMOTES = [
    {"id": "six_seven", "label": "Six Seven",  "short": "67", "color": (255, 214, 90)},
    {"id": "dab",       "label": "Dab",        "short": "D",  "color": (255, 120, 180)},
    {"id": "saludo",    "label": "Saludo",     "short": "S",  "color": (120, 200, 255)},
]

SLOTS = len(EMOTES)

OUTER_R = 250
INNER_R = 95
GAP_DEG = 2.2

COL_DIM = (0, 0, 0, 150)
COL_SEG = (28, 26, 30, 235)
COL_SEG_HOVER = (70, 62, 52, 245)
COL_EDGE = (150, 140, 125)
COL_EDGE_HOVER = (255, 205, 120)
COL_TEXT = (235, 230, 220)
COL_MUTED = (140, 135, 128)


def _segment_points(cx, cy, r_in, r_out, a0, a1, steps=14):

    points = []

    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        points.append((cx + math.cos(a) * r_out, cy + math.sin(a) * r_out))

    for i in range(steps, -1, -1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        points.append((cx + math.cos(a) * r_in, cy + math.sin(a) * r_in))

    return points


class EmoteWheel:

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()
        self.cx = self.width // 2
        self.cy = self.height // 2

        self.active = False
        self.hover = None

        self.selected = None
        self._fonts = {}

    def _font(self, size):

        font = self._fonts.get(size)

        if font is None:
            font = pygame.font.Font(None, size)
            self._fonts[size] = font

        return font

    # ------------------------------------------------------------ estado

    def open(self):

        self.active = True
        self.hover = None
        self.selected = None

    def close(self):

        self.active = False
        self.hover = None

    def toggle(self):

        if self.active:
            self.close()
        else:
            self.open()

    def pop_selected(self):
        """Devuelve el id del emote elegido (una sola vez) o None."""

        chosen = self.selected
        self.selected = None

        return chosen

    # ---------------------------------------------------------- geometria

    def _slot_at(self, pos):

        dx = pos[0] - self.cx
        dy = pos[1] - self.cy

        dist = math.hypot(dx, dy)

        if dist < INNER_R or dist > OUTER_R:
            return None

        angle = math.degrees(math.atan2(dy, dx)) + 90 + 180 / SLOTS

        return int((angle % 360) // (360 / SLOTS))

    def _slot_center(self, i):

        r = (INNER_R + OUTER_R) / 2

        a = math.radians(-90 + i * (360 / SLOTS))

        return (
            self.cx + math.cos(a) * r,
            self.cy + math.sin(a) * r,
        )

    # ------------------------------------------------------------ eventos

    def handle_event(self, event):

        """Devuelve True si el evento fue consumido por la rueda."""

        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.close()
                return True

            return False

        if event.type == pygame.MOUSEMOTION:

            self.hover = self._slot_at(event.pos)

            return False

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                slot = self._slot_at(event.pos)

                if slot is not None:
                    self.selected = EMOTES[slot]["id"]

                self.close()

            return True

        if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
            return True

        return False

    # ------------------------------------------------------------- dibujo

    def _draw_icon(self, surface, emote, center, size):

        pygame.draw.circle(surface, emote["color"], center, size)
        pygame.draw.circle(surface, (255, 255, 255), center, size, 2)

        text = self._font(int(size * (1.1 if len(emote["short"]) > 1 else 1.4)))
        letter = text.render(emote["short"], True, (30, 24, 20))

        surface.blit(letter, letter.get_rect(center=center))

    def draw(self, surface=None):

        if not self.active:
            return

        surface = surface or self.screen

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill(COL_DIM)
        surface.blit(dim, (0, 0))

        layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        step = 360 / SLOTS

        for i in range(SLOTS):

            a0 = -90 - step / 2 + i * step + GAP_DEG / 2
            a1 = a0 + step - GAP_DEG

            hovered = i == self.hover

            points = _segment_points(
                self.cx, self.cy, INNER_R, OUTER_R, a0, a1
            )

            pygame.draw.polygon(
                layer,
                COL_SEG_HOVER if hovered else COL_SEG,
                points
            )

            pygame.draw.polygon(
                layer,
                COL_EDGE_HOVER if hovered else COL_EDGE,
                points,
                3 if hovered else 2
            )

        surface.blit(layer, (0, 0))

        for i, emote in enumerate(EMOTES):

            center = self._slot_center(i)
            center = (int(center[0]), int(center[1]))

            self._draw_icon(surface, emote, center, 38)

            label = self._font(26).render(emote["label"], True, COL_TEXT)
            surface.blit(
                label,
                label.get_rect(midtop=(center[0], center[1] + 46))
            )

        pygame.draw.circle(
            surface, (20, 18, 22), (self.cx, self.cy), INNER_R - 12
        )
        pygame.draw.circle(
            surface, COL_EDGE, (self.cx, self.cy), INNER_R - 12, 3
        )

        title = self._font(34).render("EMOTES", True, COL_TEXT)
        surface.blit(title, title.get_rect(center=(self.cx, self.cy)))

        foot = "Click: hacer emote   |   H / Esc: cerrar"
        foot_img = self._font(24).render(foot, True, COL_MUTED)
        surface.blit(
            foot_img,
            foot_img.get_rect(midtop=(self.cx, self.cy + OUTER_R + 24))
        )
