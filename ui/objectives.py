"""Cartel de OBJETIVO (arriba a la derecha).

Imagenes (opcionales: si falta alguna se dibuja el rectangulo de
siempre). Las dos del MISMO tamano, PNG transparente, en assets/maps/ui/:

  objetivo.png         360x160   cartel normal (con el titulo "OBJETIVO"
                                 ya dibujado por vos)
  objetivo_hecho.png   360x160   cartel cuando se cumple (con "LISTO")

El codigo escribe SOLO el texto del objetivo, dentro de la zona de texto
(se achica solo si es largo). Zona de texto, en pixeles de la imagen:
  izquierda 26, arriba 62, derecha 26, abajo 24  (-> 308 x 74)
Dejala libre de dibujos. Si queres moverla: TEXT_MARGINS.
"""

import math
from pathlib import Path

import pygame


UI_DIR = Path(__file__).resolve().parent.parent / "assets" / "maps" / "ui"

OBJECTIVE_IMAGE = "objetivo.png"
DONE_IMAGE = "objetivo_hecho.png"

# Zona de texto dentro de la imagen: (izquierda, arriba, derecha, abajo)
TEXT_MARGINS = (26, 62, 26, 24)
IMAGE_TEXT_COLOR = (245, 245, 245)
IMAGE_TEXT_SHADOW = (0, 0, 0)
FONT_MAX = 26
FONT_MIN = 16


PANEL_WIDTH = 300
MARGIN = 18

# Minimizar: la tecla y el tamano del boton "-" y de la pestanita
MINIMIZE_KEY = pygame.K_TAB
BUTTON_SIZE = 24
PILL_SIZE = (128, 32)
MINIMIZE_TIME = 0.25     # lo que tarda en guardarse / abrirse
ALERT_TIME = 2.5         # la pestanita llama la atencion con un objetivo nuevo


TOP = 118

SLIDE_TIME = 0.45       
DONE_TIME = 0.9         

BG_COLOR = (12, 14, 18, 205)
BORDER_COLOR = (255, 170, 60)
DONE_COLOR = (96, 214, 120)
TITLE_COLOR = (255, 176, 64)
TEXT_COLOR = (245, 245, 245)


class Objectives:

    def __init__(self, screen_size, objectives, start=0, minimized=False):

        self.width, self.height = screen_size
        self.objectives = list(objectives)

        self.title_font = pygame.font.Font(None, 22)
        self.font = pygame.font.Font(None, 26)

        # Carteles dibujados por vos (None = se dibuja el rectangulo)
        self.frame_normal = self._load_frame(OBJECTIVE_IMAGE)
        self.frame_done = self._load_frame(DONE_IMAGE)

        self.use_images = (
            self.frame_normal is not None and self.frame_done is not None
        )

        # Ancho del cartel (para que se deslice bien)
        self.slide_w = (
            self.frame_normal.get_width() if self.use_images else PANEL_WIDTH
        )

       
        self.panels = [
            (
                self._build(obj["text"], done=False),
                self._build(obj["text"], done=True),
            )
            for obj in self.objectives
        ]

        # start: en que objetivo arranca (al continuar una partida)
        self.index = max(0, int(start))
        self.phase = "in"
        self.phase_time = 0.0
        self.was_done = False

        self.started = False
        self.finished = (
            not self.objectives or self.index >= len(self.objectives)
        )

        # Minimizar: el cartel se guarda y queda una pestanita chica.
        # min_t: 0.0 = cartel abierto ... 1.0 = solo la pestanita
        self.minimized = bool(minimized)
        self.min_t = 1.0 if self.minimized else 0.0
        self.alert_t = 0.0

        self._button_rect = None    # boton "-" del cartel (None = oculto)
        self._pill_rect = None      # la pestanita (None = oculta)

    @staticmethod
    def _load_frame(name):

        try:

            return pygame.image.load(str(UI_DIR / name)).convert_alpha()

        except (pygame.error, FileNotFoundError):

            return None

    def _build_framed(self, text, done):
        """Tu cartel + el texto del objetivo escrito en la zona de texto."""

        surf = (self.frame_done if done else self.frame_normal).copy()

        left, top, right, bottom = TEXT_MARGINS

        area = pygame.Rect(
            left, top,
            max(1, surf.get_width() - left - right),
            max(1, surf.get_height() - top - bottom),
        )

        # El texto largo se achica hasta que entre
        for size in range(FONT_MAX, FONT_MIN - 1, -1):

            font = pygame.font.Font(None, size)
            lines = self._wrap(font, text, area.width)

            if font.get_linesize() * len(lines) <= area.height:
                break

        line_h = font.get_linesize()

        # Centrado vertical dentro de la zona
        y = area.top + (area.height - line_h * len(lines)) // 2

        for line in lines:

            surf.blit(
                font.render(line, True, IMAGE_TEXT_SHADOW), (area.left + 1, y + 1)
            )
            surf.blit(
                font.render(line, True, IMAGE_TEXT_COLOR), (area.left, y)
            )

            y += line_h

        return surf

    @staticmethod
    def _wrap(font, text, max_width):

        lines = []
        line = ""

        for word in text.split():

            test = f"{line} {word}".strip()

            if line and font.size(test)[0] > max_width:
                lines.append(line)
                line = word
            else:
                line = test

        if line:
            lines.append(line)

        return lines

    def _build(self, text, done):

        if self.use_images:
            return self._build_framed(text, done)

        pad = 14

        lines = self._wrap(self.font, text, PANEL_WIDTH - pad * 2)

        title_text = "¡LISTO!" if done else "OBJETIVO"
        title_color = DONE_COLOR if done else TITLE_COLOR

        title = self.title_font.render(title_text, True, title_color)

        line_h = self.font.get_linesize()

        height = pad + title.get_height() + 6 + line_h * len(lines) + pad

        surf = pygame.Surface((PANEL_WIDTH, height), pygame.SRCALPHA)

        rect = surf.get_rect()

        pygame.draw.rect(surf, BG_COLOR, rect, border_radius=10)

        pygame.draw.rect(
            surf,
            (*(DONE_COLOR if done else BORDER_COLOR), 255),
            rect,
            width=2,
            border_radius=10
        )

        surf.blit(title, (pad, pad))

        y = pad + title.get_height() + 6

        for line in lines:

            surf.blit(
                self.font.render(line, True, TEXT_COLOR),
                (pad, y)
            )

            y += line_h

        return surf

    

    def _go_next(self, game):

        self.index += 1
        self.was_done = False

        while (
            self.index < len(self.objectives)
            and self.objectives[self.index]["done"](game)
        ):
            self.index += 1

        if self.index >= len(self.objectives):
            self.finished = True
            return

        self.phase = "in"
        self.phase_time = 0.0

        # Minimizado: la pestanita avisa que hay un objetivo nuevo
        if self.minimized:
            self.alert_t = ALERT_TIME

    def update(self, dt, game):

        if self.finished:
            return

        # Al continuar una partida: los objetivos que ya cumpliste
        # no se vuelven a mostrar
        if not self.started:

            while (
                self.index < len(self.objectives)
                and self.objectives[self.index]["done"](game)
            ):
                self.index += 1

            if self.index >= len(self.objectives):

                self.finished = True

                return

        self.started = True
        self.phase_time += dt

        # Animacion de minimizar / abrir
        target = 1.0 if self.minimized else 0.0

        step = dt / MINIMIZE_TIME

        if self.min_t < target:
            self.min_t = min(target, self.min_t + step)
        elif self.min_t > target:
            self.min_t = max(target, self.min_t - step)

        if self.alert_t > 0:
            self.alert_t = max(0.0, self.alert_t - dt)

        obj = self.objectives[self.index]

        if self.phase == "in":

            if self.phase_time >= SLIDE_TIME:
                self.phase = "show"
                self.phase_time = 0.0

        elif self.phase == "show":

            max_time = obj.get("max_time")

            if obj["done"](game):

                self.was_done = True
                self.phase = "done"
                self.phase_time = 0.0

            elif max_time is not None and self.phase_time >= max_time:

                self.phase = "out"
                self.phase_time = 0.0

        elif self.phase == "done":

            if self.phase_time >= DONE_TIME:
                self.phase = "out"
                self.phase_time = 0.0

        elif self.phase == "out":

            if self.phase_time >= SLIDE_TIME:
                self._go_next(game)

  
    def _offset(self):
        distance = self.slide_w + MARGIN + 12

        if self.phase == "in":

            t = min(1.0, self.phase_time / SLIDE_TIME)
            ease = 1 - (1 - t) ** 3

            return int(distance * (1 - ease))

        if self.phase == "out":

            t = min(1.0, self.phase_time / SLIDE_TIME)
            ease = t ** 3

            return int(distance * ease)

        return 0

    # ---------- minimizar ----------

    def toggle(self):
        """Minimiza o abre el cartel."""

        self.minimized = not self.minimized
        self.alert_t = 0.0

    def handle_event(self, event):
        """Devuelve True si el evento era para el cartel (asi el click
        no cuenta como un golpe)."""

        if self.finished or not self.started:
            return False

        if event.type == pygame.KEYDOWN and event.key == MINIMIZE_KEY:

            self.toggle()

            return True

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):

            if (
                self._pill_rect is not None
                and self.minimized
                and self._pill_rect.collidepoint(event.pos)
            ):

                self.toggle()

                return True

            if (
                self._button_rect is not None
                and not self.minimized
                and self._button_rect.collidepoint(event.pos)
            ):

                self.toggle()

                return True

        return False

    def _draw_button(self, screen, panel_rect):
        """Boton "-" en la esquina de arriba a la derecha del cartel."""

        rect = pygame.Rect(0, 0, BUTTON_SIZE, BUTTON_SIZE)
        rect.topright = (panel_rect.right - 8, panel_rect.top + 8)

        hover = rect.collidepoint(pygame.mouse.get_pos())

        pygame.draw.rect(
            screen,
            (255, 200, 110) if hover else (30, 32, 40),
            rect,
            border_radius=6,
        )
        pygame.draw.rect(
            screen, BORDER_COLOR, rect, width=2, border_radius=6
        )

        pygame.draw.line(
            screen,
            (20, 20, 24) if hover else (255, 255, 255),
            (rect.left + 6, rect.centery),
            (rect.right - 7, rect.centery),
            3,
        )

        self._button_rect = rect

    def _draw_pill(self, screen, offset):
        """La pestanita que queda cuando minimizas el cartel."""

        w, h = PILL_SIZE

        rect = pygame.Rect(0, 0, w, h)
        rect.topright = (self.width - MARGIN + offset, TOP)

        done = self.was_done and self.phase in ("done", "out")

        color = DONE_COLOR if done else BORDER_COLOR

        # Con un objetivo nuevo late un ratito para que lo notes
        pulse = 0.0

        if self.alert_t > 0:
            pulse = 0.5 + 0.5 * math.sin(self.alert_t * 10)

        hover = rect.collidepoint(pygame.mouse.get_pos())

        pill = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.rect(
            pill,
            (40, 42, 52, 235) if hover else BG_COLOR,
            pill.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            pill,
            (*color, int(150 + 105 * pulse) if self.alert_t > 0 else 255),
            pill.get_rect(),
            width=2 + (1 if self.alert_t > 0 else 0),
            border_radius=10,
        )

        if done:
            label = "¡LISTO!"
        elif self.alert_t > 0:
            label = "¡NUEVO!"
        else:
            label = "OBJETIVO"

        text = self.title_font.render(label, True, color)

        pill.blit(text, (12, (h - text.get_height()) // 2))

        # "+" para abrirlo
        cx = w - 16
        cy = h // 2

        pygame.draw.line(pill, (255, 255, 255), (cx - 5, cy), (cx + 5, cy), 2)
        pygame.draw.line(pill, (255, 255, 255), (cx, cy - 5), (cx, cy + 5), 2)

        screen.blit(pill, rect)

        self._pill_rect = rect

    def draw(self, screen):

        self._button_rect = None
        self._pill_rect = None

        if self.finished or not self.started:
            return

        # Easing de minimizar (0 = abierto, 1 = guardado)
        t = self.min_t
        ease = 1 - (1 - t) ** 3

        panel = self.panels[self.index][1 if self.was_done else 0]

        # El cartel se desliza hacia afuera al minimizar
        panel_extra = int((self.slide_w + MARGIN + 12) * ease)

        if ease < 1.0:

            rect = panel.get_rect(
                topright=(
                    self.width - MARGIN + self._offset() + panel_extra,
                    TOP
                )
            )

            screen.blit(panel, rect)

            if ease == 0.0 and self.phase in ("show", "done"):
                self._draw_button(screen, rect)

        # La pestanita entra desde afuera mientras el cartel sale
        if ease > 0.0:

            pill_extra = int((PILL_SIZE[0] + MARGIN + 12) * (1.0 - ease))

            self._draw_pill(screen, pill_extra)