import math
import random
from pathlib import Path

import pygame

from core.audio_manager import audio


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


# ---------- Efectos del menu ----------

# "Prendido de pantalla" (estilo tele vieja): una linea de luz se abre a
# lo ancho y despues hacia arriba y abajo mostrando el menu.
INTRO_LINE = 0.22         # tramo 1: la linea se abre a lo ancho
INTRO_OPEN = 0.62         # tramo 2: la linea se abre hacia arriba/abajo
FULL_END = 1.05           # fin del efecto de pantalla completa
INTRO_FLASH = 170         # brillo blanco inicial (0 a 255)
INTRO_SCANLINES = 85      # intensidad inicial de las lineas de tele

# Encendido del monitor de la computadora (la que mira el personaje).
# Arranca apagado y se prende un poquito despues del prendido general.
# El area de la pantalla esta en pixeles de menu.png (1669x942).
MONITOR_BOX = (456, 201, 1235, 534)     # x0, y0, x1, y1
MONITOR_REF = (1669, 942)

MON_DELAY = 0.85          # cuando empieza a prenderse (desde el inicio)
MON_LINE = 0.20           # la linea de luz se abre a lo ancho del monitor
MON_OPEN = 0.40           # se abre hacia arriba/abajo mostrando el menu
MON_GLOW = 0.45           # el brillo y el resplandor se apagan de a poco
MON_FLASH = 200           # brillo blanco del monitor al prenderse (0-255)
MON_SCANLINES = 70        # lineas de tele del monitor (0-255)
MON_SPILL = 1.0           # resplandor sobre la pared y el escritorio (0 = sin)

MON_ON_AT = MON_DELAY + MON_LINE + MON_OPEN   # el menu ya se ve completo
INTRO_DURATION = MON_ON_AT + MON_GLOW         # fin de todo el efecto
INTRO_INPUT_AT = MON_ON_AT  # recien ahi el menu acepta clicks y teclas

# Al elegir una opcion
PRESS_DURATION = 0.32     # tiempo entre el clic y el cambio de pantalla
PRESS_PARTICLES = 30      # chispitas que salen de la opcion
SPARK_COLORS = [
    (255, 215, 140),
    (255, 240, 190),
    (255, 255, 255),
    (255, 190, 100),
]

HIGHLIGHT_SPEED = 18      # que tan rapido se desliza el marco entre opciones


def _clamp01(k):

    return max(0.0, min(1.0, k))


def _ease_out(k):

    k = _clamp01(k)

    return 1 - (1 - k) ** 3


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

        self._setup_effects()

    # ---------- animaciones de fondo ----------

    def _setup_cat(self, original):
        """Recorta el gato del fondo para poder hacerlo respirar."""

        # CAT_RECT esta en coordenadas "logicas" (745x421). El fondo real
        # puede tener otra resolucion, asi que se convierte a pixeles de
        # la imagen original antes de recortar.
        kx = original.get_width() / BG_W
        ky = original.get_height() / BG_H

        lx, ly, lw, lh = CAT_RECT

        x0 = round(lx * kx)
        y0 = round(ly * ky)
        w = round(lw * kx)
        h = round(lh * ky)

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

        # Tamano en pantalla: lo que ocupa esa zona en la ventana
        size = (
            max(1, round(lw * self.sx)),
            max(1, round(lh * self.sy))
        )

        self.cat_sprite = pygame.transform.smoothscale(sprite, size)

        self.cat_pos = (round(lx * self.sx), round(ly * self.sy))

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

        self._update_sparks(dt)

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
        self._update_highlight(dt)

        self.screen.blit(
            self.background,
            (0, 0)
        )

        self._draw_cat(now)
        self._draw_leaves()

        self._draw_monitor(now)

        # El marco de seleccion aparece cuando el monitor ya prendio
        if self._monitor_ui_visible(now):

            for i in range(len(self.options)):

                self.draw_option(i)

            self._draw_press(now)

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

        self._draw_intro(now)

    def draw_option(self, index):

        if index != self.selected:
            return

        now = pygame.time.get_ticks() / 1000

        rect = self.get_option_rect(index)

        # El marco se desliza suave hasta la opcion elegida
        if self._hl_y is not None:
            rect.y = round(self._hl_y)

        # Brillo suave que "respira" detras del marco
        pulse = 0.5 + 0.5 * math.sin(now * 5)

        glow = pygame.Surface(rect.size, pygame.SRCALPHA)

        pygame.draw.rect(
            glow,
            (255, 240, 200, int(26 + 30 * pulse)),
            glow.get_rect(),
            border_radius=3
        )

        self.screen.blit(glow, rect.topleft)

        pygame.draw.rect(
            self.screen,
            (240, 248, 255),
            rect,
            width=2,
            border_radius=3
        )

        # La flechita se mece de a poquito
        bob = math.sin(now * 7) * 2.5

        arrow = self.font.render(
            "▶",
            True,
            (255, 255, 255)
        )

        arrow_rect = arrow.get_rect(
            midleft=(
                rect.left + 10 + bob,
                rect.centery
            )
        )

        self.screen.blit(
            arrow,
            arrow_rect
        )

    # ---------- efectos ----------

    def _setup_effects(self):

        self._hl_y = None

        # Prendido de pantalla (None = no se esta reproduciendo)
        self.intro_t0 = None

        # Opcion elegida: se espera PRESS_DURATION y recien ahi se avisa
        self.pending = None
        self.press_index = 0
        self.press_t0 = 0.0
        self.sparks = []

        self._setup_monitor()

        self._fade = pygame.Surface((self.width, self.height))

        self._white = pygame.Surface((self.width, self.height))
        self._white.fill((255, 255, 255))

        # Lineas horizontales como las de una tele
        self._scanlines = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )

        for y in range(0, self.height, 3):

            pygame.draw.line(
                self._scanlines,
                (0, 0, 0, 255),
                (0, y),
                (self.width, y)
            )

    def _setup_monitor(self):
        """Prepara las piezas del encendido del monitor."""

        kx = self.width / MONITOR_REF[0]
        ky = self.height / MONITOR_REF[1]

        x0, y0, x1, y1 = MONITOR_BOX

        rect = pygame.Rect(
            round(x0 * kx),
            round(y0 * ky),
            round((x1 - x0) * kx),
            round((y1 - y0) * ky),
        ).clip(self.screen.get_rect())

        self.monitor_rect = rect

        w, h = rect.size

        # Lo que muestra el monitor prendido: el pedazo del fondo
        self._mon_on = self.background.subsurface(rect).copy()

        # Monitor apagado: vidrio oscuro con un par de reflejos
        off = pygame.Surface((w, h))
        off.fill((8, 12, 24))

        shine = pygame.Surface((w, h), pygame.SRCALPHA)

        for x_a, x_b, alpha in ((0.08, 0.16, 16), (0.42, 0.46, 11)):

            pygame.draw.polygon(
                shine,
                (170, 200, 255, alpha),
                [
                    (w * x_a, h),
                    (w * (x_a + 0.22), 0),
                    (w * (x_a + 0.22 + (x_b - x_a)), 0),
                    (w * x_b, h),
                ]
            )

        off.blit(shine, (0, 0))

        pygame.draw.rect(off, (16, 24, 44), off.get_rect(), width=2)

        self._mon_off = off

        self._mon_white = pygame.Surface((w, h))
        self._mon_white.fill((215, 232, 255))

        self._mon_scan = pygame.Surface((w, h), pygame.SRCALPHA)

        for y in range(0, h, 3):

            pygame.draw.line(
                self._mon_scan, (0, 0, 0, 255), (0, y), (w, y)
            )

        # Resplandor azul que el monitor tira sobre la pared y el escritorio
        self._mon_spill = []

        for grow, alpha in ((72, 9), (46, 13), (26, 17), (10, 22)):

            ring = pygame.Surface(
                (w + grow * 2, h + grow * 2),
                pygame.SRCALPHA
            )

            pygame.draw.rect(
                ring,
                (140, 190, 255, alpha),
                ring.get_rect(),
                border_radius=grow
            )

            self._mon_spill.append((grow, ring))

    def _monitor_ui_visible(self, now):

        if self.intro_t0 is None:
            return True

        return now - self.intro_t0 >= MON_ON_AT

    def _draw_monitor(self, now):
        """Monitor apagado -> linea de luz -> se abre -> destello."""

        if self.intro_t0 is None:
            return

        t = now - self.intro_t0

        if t >= INTRO_DURATION:
            return

        m = self.monitor_rect
        ts = t - MON_DELAY          # tiempo desde que empieza a prenderse

        line_color = (235, 245, 255)

        # Resplandor: crece hasta que prende y despues se apaga
        if ts > 0 and MON_SPILL > 0:

            on_time = MON_LINE + MON_OPEN

            if ts < on_time:
                g = ts / on_time
            else:
                g = 1 - (ts - on_time) / MON_GLOW

            g = _clamp01(g) * MON_SPILL

            for grow, ring in self._mon_spill:

                ring.set_alpha(int(255 * _clamp01(g)))

                self.screen.blit(ring, (m.x - grow, m.y - grow))

        # Base: el vidrio apagado
        self.screen.blit(self._mon_off, m.topleft)

        if ts <= 0:
            return

        # Tramo 1: linea de luz que se abre a lo ancho
        if ts < MON_LINE:

            k = _ease_out(ts / MON_LINE)

            line_w = max(4, int(m.width * k))

            glow = pygame.Surface((line_w, 13), pygame.SRCALPHA)
            glow.fill((200, 225, 255, 70))

            self.screen.blit(
                glow,
                glow.get_rect(center=(m.centerx, m.centery))
            )

            pygame.draw.rect(
                self.screen,
                line_color,
                pygame.Rect(
                    m.centerx - line_w // 2,
                    m.centery - 1,
                    line_w,
                    3
                )
            )

            return

        # Tramo 2: se abre hacia arriba y abajo mostrando el menu
        k = _ease_out((ts - MON_LINE) / MON_OPEN)

        open_h = max(3, int(m.height * k))

        band_y = (m.height - open_h) // 2
        band = pygame.Rect(0, band_y, m.width, open_h)
        dest = (m.x, m.y + band_y)

        self.screen.blit(self._mon_on, dest, area=band)

        # Brillo + parpadeo + lineas de tele, solo sobre lo ya abierto
        fade = 1 - _clamp01((ts - MON_LINE) / (MON_OPEN + MON_GLOW))

        flicker = 1.0

        if ts < MON_LINE + MON_OPEN + 0.15:
            flicker = 0.75 + 0.25 * math.sin(ts * 90)

        self._mon_white.set_alpha(int(MON_FLASH * fade * fade * flicker))
        self.screen.blit(self._mon_white, dest, area=band)

        self._mon_scan.set_alpha(int(MON_SCANLINES * fade))
        self.screen.blit(self._mon_scan, dest, area=band)

        if k < 1:

            pygame.draw.rect(
                self.screen, line_color, (m.x, m.y + band_y - 1, m.width, 3)
            )

            pygame.draw.rect(
                self.screen,
                line_color,
                (m.x, m.y + band_y + open_h - 2, m.width, 3)
            )

    def play_intro(self):
        """Dispara el efecto de prendido de pantalla."""

        self.intro_t0 = pygame.time.get_ticks() / 1000
        self.pending = None
        self.sparks = []

    def _intro_blocks_input(self):

        if self.intro_t0 is None:
            return False

        t = pygame.time.get_ticks() / 1000 - self.intro_t0

        return t < INTRO_INPUT_AT

    def _update_highlight(self, dt):

        target = float(self.get_option_rect(self.selected).y)

        if self._hl_y is None:

            self._hl_y = target

        else:

            self._hl_y += (target - self._hl_y) * (
                1 - math.exp(-HIGHLIGHT_SPEED * dt)
            )

    def _draw_intro(self, now):

        if self.intro_t0 is None:
            return

        t = now - self.intro_t0

        if t >= INTRO_DURATION:

            self.intro_t0 = None
            return

        # Despues de FULL_END solo queda el encendido del monitor
        if t >= FULL_END:
            return

        w, h = self.width, self.height

        line_color = (235, 245, 255)

        # Tramo 1: pantalla negra y una linea de luz que se abre a lo ancho
        if t < INTRO_LINE:

            k = _ease_out(t / INTRO_LINE)

            self.screen.fill((0, 0, 0))

            line_w = max(4, int(w * k))

            glow = pygame.Surface((line_w, 15), pygame.SRCALPHA)
            glow.fill((200, 225, 255, 70))

            self.screen.blit(
                glow,
                glow.get_rect(center=(w // 2, h // 2))
            )

            pygame.draw.rect(
                self.screen,
                line_color,
                pygame.Rect(
                    (w - line_w) // 2,
                    h // 2 - 1,
                    line_w,
                    3
                )
            )

            return

        # Tramo 2: la linea se abre hacia arriba y abajo mostrando el menu
        if t < INTRO_OPEN:

            k = _ease_out((t - INTRO_LINE) / (INTRO_OPEN - INTRO_LINE))

            open_h = max(3, int(h * k))

            top = (h - open_h) // 2
            bottom = top + open_h

            pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, w, top))
            pygame.draw.rect(self.screen, (0, 0, 0), (0, bottom, w, h - bottom))

            pygame.draw.rect(self.screen, line_color, (0, top - 1, w, 3))
            pygame.draw.rect(self.screen, line_color, (0, bottom - 2, w, 3))

        # Brillo que se apaga + lineas de tele que se van + parpadeo
        fade = 1 - _clamp01((t - INTRO_LINE) / (FULL_END - INTRO_LINE))

        flicker = 1.0

        if t < INTRO_OPEN + 0.2:
            flicker = 0.75 + 0.25 * math.sin(t * 90)

        self._white.set_alpha(int(INTRO_FLASH * fade * fade * flicker))
        self.screen.blit(self._white, (0, 0))

        self._scanlines.set_alpha(int(INTRO_SCANLINES * fade))
        self.screen.blit(self._scanlines, (0, 0))

    def _start_press(self, index):
        """El jugador eligio una opcion: efecto y, un instante despues,
        poll() devuelve la accion."""

        if self.pending is not None:
            return

        self.selected = index
        self.pending = self.options[index][1]
        self.press_index = index
        self.press_t0 = pygame.time.get_ticks() / 1000

        audio.play("pickup")

        rect = self.get_option_rect(index)

        for _ in range(PRESS_PARTICLES):

            angle = self.rng.uniform(0, math.tau)
            speed = self.rng.uniform(70, 240)

            self.sparks.append([
                self.rng.uniform(rect.left, rect.right),
                self.rng.uniform(rect.top + 6, rect.bottom - 6),
                math.cos(angle) * speed,
                math.sin(angle) * speed - 70,
                0.0,
                self.rng.uniform(0.3, 0.55),
                self.rng.choice((2, 3, 3, 4)),
                self.rng.choice(SPARK_COLORS),
            ])

    def _update_sparks(self, dt):

        for spark in self.sparks:

            spark[0] += spark[2] * dt
            spark[1] += spark[3] * dt
            spark[3] += 420 * dt     # gravedad
            spark[4] += dt

        self.sparks = [sp for sp in self.sparks if sp[4] < sp[5]]

    def _draw_press(self, now):

        if self.pending is None:
            return

        k = _clamp01((now - self.press_t0) / PRESS_DURATION)

        rect = self.get_option_rect(self.press_index)

        if self._hl_y is not None:
            rect.y = round(self._hl_y)

        # Destello blanco sobre la opcion
        flash_alpha = int(220 * (1 - k) ** 2)

        if flash_alpha > 0:

            flash = pygame.Surface(rect.size, pygame.SRCALPHA)

            pygame.draw.rect(
                flash,
                (255, 255, 255, flash_alpha),
                flash.get_rect(),
                border_radius=3
            )

            self.screen.blit(flash, rect.topleft)

        # Ondas que se agrandan y se desvanecen
        for delay in (0.0, 0.25):

            kk = _clamp01((k - delay) / (1 - delay))

            if kk <= 0 or kk >= 1:
                continue

            grow = int(8 + 46 * _ease_out(kk))

            ring_rect = rect.inflate(grow * 2, grow)

            ring = pygame.Surface(ring_rect.size, pygame.SRCALPHA)

            pygame.draw.rect(
                ring,
                (255, 235, 190, int(210 * (1 - kk))),
                ring.get_rect(),
                width=2,
                border_radius=8
            )

            self.screen.blit(ring, ring_rect.topleft)

        # Chispas
        for x, y, _vx, _vy, age, life, size, color in self.sparks:

            spark = pygame.Surface((size, size))
            spark.fill(color)
            spark.set_alpha(int(255 * (1 - age / life)))

            self.screen.blit(spark, (round(x), round(y)))

        # Al final la pantalla se oscurece, asi el cambio no es brusco
        if k > 0.65:

            self._fade.fill((0, 0, 0))
            self._fade.set_alpha(int(255 * (k - 0.65) / 0.35))
            self.screen.blit(self._fade, (0, 0))

    def poll(self):
        """main.py lo llama en cada cuadro. Devuelve la accion elegida
        cuando termino el efecto del clic, o None."""

        if self.pending is None:
            return None

        now = pygame.time.get_ticks() / 1000

        if now - self.press_t0 < PRESS_DURATION:
            return None

        action = self.pending

        self.pending = None
        self.sparks = []

        return action

    def _select(self, index):

        if index != self.selected:

            self.selected = index
            audio.play("click")

    def handle_event(self, event):
        """Ya no devuelve la accion: la devuelve poll() cuando termina el
        efecto. (Siempre devuelve None.)"""

        # Mientras se prende la pantalla o se esta eligiendo una opcion,
        # no se aceptan mas entradas
        if self.pending is not None or self._intro_blocks_input():
            return None

        if event.type == pygame.KEYDOWN:

            if event.key in (
                pygame.K_UP,
                pygame.K_w
            ):

                self._select((self.selected - 1) % len(self.options))

            elif event.key in (
                pygame.K_DOWN,
                pygame.K_s
            ):

                self._select((self.selected + 1) % len(self.options))

            elif event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE
            ):

                self._start_press(self.selected)

            elif event.key == pygame.K_ESCAPE:

                for i, option in enumerate(self.options):

                    if option[1] == "quit":
                        self._start_press(i)

        elif event.type == pygame.MOUSEMOTION:

            for i in range(len(self.options)):

                if self.get_option_rect(i).collidepoint(event.pos):

                    self._select(i)

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                for i in range(len(self.options)):

                    if self.get_option_rect(i).collidepoint(event.pos):

                        self._start_press(i)
                        break

        return None