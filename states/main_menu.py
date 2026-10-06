import math
import random
from pathlib import Path

import pygame


# El fondo original mide 745x421; todas las coordenadas de abajo estan
# en ese tamano y se escalan solas al tamano de la ventana.
BG_W = 745
BG_H = 421

# Zona del gato dormido: (x, y, ancho, alto)
CAT_RECT = (552, 262, 126, 76)

# Ventanas por donde pasan las hojas: (x, y, ancho, alto)
WINDOWS = [
    (257, 1, 99, 55),
    (380, 1, 110, 55),
]

# Respiracion del gato
BREATH_PERIOD = 3.8      # segundos por respiracion
BREATH_Y = 0.022         # cuanto se estira hacia arriba (2.2%)
BREATH_X = 0.010         # cuanto se ensancha (1%)

# Hojas
LEAF_MAX = 5             # maximo de hojas a la vez
LEAF_SPAWN = (2.5, 5.5)  # segundos entre una hoja y la siguiente
LEAF_COLORS = [
    (28, 84, 44),     # verde oscuro
    (46, 112, 56),    # verde bosque
    (72, 140, 66),    # verde medio
    (104, 168, 78),   # verde hoja
    (146, 200, 104),  # verde clarito
    (184, 226, 140),  # verde muy claro
]


def build_cat_mask(px, w, h):
    """px[y][x] = (r, g, b). Devuelve una matriz de bool donde True es
    un pixel del gato. El gato es gris (r, g y b casi iguales), el
    escritorio y la pared son marrones, asi que se separan por color."""

    base = [[False] * w for _ in range(h)]

    for y in range(h):
        for x in range(w):

            r, g, b = px[y][x]

            spread = max(r, g, b) - min(r, g, b)
            avg = (r + g + b) / 3

            gray = spread <= 12 and 45 <= avg <= 200
            blue_z = b - r > 40   # las "z" azules del sueno

            base[y][x] = gray or blue_z

    # Un pixel de borde oscuro alrededor (el contorno negro del gato)
    mask = [row[:] for row in base]

    for y in range(h):
        for x in range(w):

            if not base[y][x]:
                continue

            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):

                    nx, ny = x + dx, y + dy

                    if 0 <= nx < w and 0 <= ny < h:

                        r, g, b = px[ny][nx]

                        if (r + g + b) / 3 < 90:
                            mask[ny][nx] = True

    # Rellenar huecos de adentro (ojos, bigotes, boca)
    outside = [[False] * w for _ in range(h)]

    stack = []

    for x in range(w):
        stack += [(x, 0), (x, h - 1)]

    for y in range(h):
        stack += [(0, y), (w - 1, y)]

    while stack:

        x, y = stack.pop()

        if not (0 <= x < w and 0 <= y < h):
            continue

        if outside[y][x] or mask[y][x]:
            continue

        outside[y][x] = True

        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    for y in range(h):
        for x in range(w):

            if not outside[y][x]:
                mask[y][x] = True

    return mask


class Leaf:

    def __init__(self, rng, surfaces):

        self.surface = rng.choice(surfaces)

        # Entra por la derecha y cruza hacia la izquierda, bajando
        # de a poco y balanceandose (coordenadas del fondo original).
        self.x = rng.uniform(495, 515)
        self.y = rng.uniform(0, 26)

        self.vx = -rng.uniform(16, 28)
        self.vy = rng.uniform(1.0, 3.2)

        self.angle = rng.uniform(0, 360)
        self.spin = rng.uniform(-70, 70)

        self.sway_amp = rng.uniform(5, 11)
        self.sway_speed = rng.uniform(1.2, 2.4)
        self.phase = rng.uniform(0, math.tau)
        self.t = 0.0

    def update(self, dt):

        self.t += dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.angle += self.spin * dt

    @property
    def draw_y(self):

        return self.y + math.sin(
            self.t * self.sway_speed + self.phase
        ) * self.sway_amp * 0.35

    def is_dead(self):

        return self.x < 245 or self.y > 70


class MainMenu:

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()


        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
            / "menu.png"
        )

        original = pygame.image.load(image_path).convert()

        self.background = pygame.transform.scale(
            original,
            (self.width, self.height)
        )

        self.sx = self.width / BG_W
        self.sy = self.height / BG_H

        self._setup_cat(original)
        self._setup_leaves()

        self._last_ticks = pygame.time.get_ticks() / 1000


        self.options = [
            ("Nueva partida", "new_game"),
            ("Continuar partida", "continue_game"),
            ("Configuraciones", "settings"),
            ("Logros", "achievements"),
            ("Salir", "quit")
        ]

        self.selected = 0

        self.menu_x = 376
        self.menu_y = 245
        self.option_height = 33

        self.font = pygame.font.Font(None,42)
        self.small_font = pygame.font.Font(None,24)

    # ---------- animaciones de fondo ----------

    def _setup_cat(self, original):
        """Recorta el gato del fondo para poder hacerlo respirar."""

        x0, y0, w, h = CAT_RECT

        px = [
            [tuple(original.get_at((x0 + x, y0 + y))[:3]) for x in range(w)]
            for y in range(h)
        ]

        mask = build_cat_mask(px, w, h)

        sprite = pygame.Surface((w, h), pygame.SRCALPHA)

        for y in range(h):
            for x in range(w):

                if mask[y][x]:
                    sprite.set_at((x, y), (*px[y][x], 255))

        # Mismo escalado "a pixel" que el fondo
        size = (
            max(1, round(w * self.sx)),
            max(1, round(h * self.sy))
        )

        self.cat_sprite = pygame.transform.scale(sprite, size)

        self.cat_pos = (round(x0 * self.sx), round(y0 * self.sy))

        # Punto fijo de la respiracion: abajo al medio del gato
        self.cat_anchor = (size[0] / 2, size[1] * 0.93)

    def _setup_leaves(self):

        self.rng = random.Random()

        # Hojas chiquitas, un par de tamanos, ya a escala de pantalla
        self.leaf_surfaces = []

        for color in LEAF_COLORS:

            for length, thick in ((4.5, 2.4), (3.4, 1.9)):

                lw = max(3, round(length * self.sx))
                lh = max(2, round(thick * self.sy))

                surf = pygame.Surface((lw + 2, lh + 2), pygame.SRCALPHA)

                pygame.draw.ellipse(
                    surf,
                    (*color, 225),
                    pygame.Rect(1, 1, lw, lh)
                )

                self.leaf_surfaces.append(surf)

        self.leaves = []
        self.leaf_timer = self.rng.uniform(0.5, 2.0)

        self.window_rects = [
            pygame.Rect(
                round(x * self.sx),
                round(y * self.sy),
                round(w * self.sx),
                round(h * self.sy)
            )
            for x, y, w, h in WINDOWS
        ]

    def _update_animation(self, dt):

        self.leaf_timer -= dt

        if self.leaf_timer <= 0:

            if len(self.leaves) < LEAF_MAX:
                self.leaves.append(Leaf(self.rng, self.leaf_surfaces))

            self.leaf_timer = self.rng.uniform(*LEAF_SPAWN)

        for leaf in self.leaves:
            leaf.update(dt)

        self.leaves = [leaf for leaf in self.leaves if not leaf.is_dead()]

    def _draw_cat(self, now):

        # 0 -> 1 -> 0 suave. Nunca achica el gato: asi la copia siempre
        # tapa al gato original que esta pintado en el fondo.
        breath = 0.5 * (1 - math.cos(now * math.tau / BREATH_PERIOD))

        fx = 1 + BREATH_X * breath
        fy = 1 + BREATH_Y * breath

        bw, bh = self.cat_sprite.get_size()

        new_size = (round(bw * fx), round(bh * fy))

        sprite = pygame.transform.smoothscale(self.cat_sprite, new_size)

        ax, ay = self.cat_anchor

        pos = (
            self.cat_pos[0] + ax - ax * (new_size[0] / bw),
            self.cat_pos[1] + ay - ay * (new_size[1] / bh)
        )

        self.screen.blit(sprite, (round(pos[0]), round(pos[1])))

    def _draw_leaves(self):

        for window in self.window_rects:

            previous_clip = self.screen.get_clip()

            self.screen.set_clip(window)

            for leaf in self.leaves:

                sprite = pygame.transform.rotate(leaf.surface, leaf.angle)

                rect = sprite.get_rect(
                    center=(
                        round(leaf.x * self.sx),
                        round(leaf.draw_y * self.sy)
                    )
                )

                self.screen.blit(sprite, rect)

            self.screen.set_clip(previous_clip)

    def get_option_rect(self, index):

        y = 227.25 + index * 33

        return pygame.Rect(
            376,
            y,
            290,
            38
        )

    def draw(self):

        now = pygame.time.get_ticks() / 1000

        # Si el menu estuvo un rato sin dibujarse, no dar un salto
        dt = min(max(now - self._last_ticks, 0.0), 0.05)

        self._last_ticks = now

        self._update_animation(dt)

        self.screen.blit(
            self.background,
            (0, 0)
        )

        self._draw_cat(now)
        self._draw_leaves()

        for i in range(len(self.options)):

            self.draw_option(i)


        controls = self.small_font.render(
            "W/S o ↑/↓  •  ENTER seleccionar  •  ESC salir",
            True,
            (235, 242, 255)
        )

        controls_rect = controls.get_rect(
            bottomright=(
                self.width - 18,
                self.height - 15
            )
        )

        self.screen.blit(
            controls,
            controls_rect
        )

    def draw_option(self, index):

        if index == self.selected:

            rect = self.get_option_rect(index)

            pygame.draw.rect(
                self.screen,
                (240, 248, 255),
                rect,
                width=2,
                border_radius=3
            )

            arrow = self.font.render(
                "▶",
                True,
                (255, 255, 255)
            )

            arrow_rect = arrow.get_rect(
                midleft=(
                    rect.left + 10,
                    rect.centery
                )
            )

            self.screen.blit(
                arrow,
                arrow_rect
            )

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key in (
                pygame.K_UP,
                pygame.K_w
            ):

                self.selected = (
                    self.selected - 1
                ) % len(self.options)

            elif event.key in (
                pygame.K_DOWN,
                pygame.K_s
            ):

                self.selected = (
                    self.selected + 1
                ) % len(self.options)

            elif event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE
            ):

                return self.options[self.selected][1]

            elif event.key == pygame.K_ESCAPE:

                return "quit"


        elif event.type == pygame.MOUSEMOTION:

            for i in range(
                len(self.options)
            ):

                rect = self.get_option_rect(i)

                if rect.collidepoint(
                    event.pos
                ):

                    self.selected = i

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                for i, option in enumerate(
                    self.options
                ):

                    rect = self.get_option_rect(i)

                    if rect.collidepoint(event.pos):

                        self.selected = i

                        return option[1]

        return None