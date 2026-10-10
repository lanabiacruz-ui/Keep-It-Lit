"""Cartel con el nombre de la zona (aparece al entrar a una sala).

Imagen (opcional: si falta se dibuja el texto con la linea naranja de
siempre):

  assets/maps/hud/cartel_zona.png   560x140  PNG transparente

    Es el cartel VACIO (sin texto): el codigo escribe el nombre de la
    zona encima, centrado ("Tienda", "Sala de combate", ...). La linea
    naranja de abajo ya no se dibuja: si la queres, dibujala en la
    imagen. Si el nombre es muy largo el texto se achica solo para que
    entre. Para subir/bajar el texto: TEXT_OFFSET_Y.
"""

from pathlib import Path

import pygame


BANNER_IMAGE = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
    / "cartel_zona.png"
)

# Con imagen: margen a cada lado donde NO se escribe, y ajuste vertical
# del texto (positivo = mas abajo).
TEXT_MARGIN_X = 70
TEXT_OFFSET_Y = 0


FADE_IN = 0.45      
HOLD = 1.8          
FADE_OUT = 0.9      

FONT_SIZE = 64
TEXT_COLOR = (255, 238, 196)
OUTLINE_COLOR = (0, 0, 0)
LINE_COLOR = (255, 176, 64)


CENTER_Y = 0.27


class ZoneBanner:
   
   

    def __init__(self, screen_size):

        self.width, self.height = screen_size

        self.font = pygame.font.Font(None, FONT_SIZE)

        self.age = None     
        self.image = None

        # Cartel dibujado por vos (None = se usa el texto con la linea)
        self.frame = self._load_frame()

    @staticmethod
    def _load_frame():

        try:

            return pygame.image.load(str(BANNER_IMAGE)).convert_alpha()

        except (pygame.error, FileNotFoundError):

            return None

    @property
    def total_time(self):
        return FADE_IN + HOLD + FADE_OUT

    def show(self, name):
       

        self.image = self._build(name)
        self.age = 0.0

    def update(self, dt):

        if self.age is None:
            return

        self.age += dt

        if self.age >= self.total_time:
            self.age = None

    def _build_framed(self, name):
        """El cartel dibujado + el nombre escrito encima, centrado."""

        surf = self.frame.copy()
        w, h = surf.get_size()

        text = self.font.render(name, True, TEXT_COLOR)
        outline = self.font.render(name, True, OUTLINE_COLOR)

        # Si el nombre no entra, se achica
        max_w = max(1, w - TEXT_MARGIN_X * 2)

        if text.get_width() > max_w:

            k = max_w / text.get_width()
            size = (max_w, max(1, int(text.get_height() * k)))

            text = pygame.transform.smoothscale(text, size)
            outline = pygame.transform.smoothscale(outline, size)

        tx = (w - text.get_width()) // 2
        ty = (h - text.get_height()) // 2 + TEXT_OFFSET_Y

        for dx, dy in (
            (-2, 0), (2, 0), (0, -2), (0, 2),
            (-2, -2), (2, 2), (-2, 2), (2, -2)
        ):
            surf.blit(outline, (tx + dx, ty + dy))

        surf.blit(text, (tx, ty))

        return surf

    def _build(self, name):

        if self.frame is not None:
            return self._build_framed(name)

        text = self.font.render(name, True, TEXT_COLOR)
        outline = self.font.render(name, True, OUTLINE_COLOR)

        pad_x = 36
        pad_y = 12
        line_h = 3
        gap = 6

        w = text.get_width() + pad_x * 2
        h = text.get_height() + pad_y * 2 + gap + line_h

        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        tx = (w - text.get_width()) // 2
        ty = pad_y

        for dx, dy in (
            (-2, 0), (2, 0), (0, -2), (0, 2),
            (-2, -2), (2, 2), (-2, 2), (2, -2)
        ):
            surf.blit(outline, (tx + dx, ty + dy))

        surf.blit(text, (tx, ty))

        
        line_w = text.get_width() + pad_x
        x0 = (w - line_w) // 2
        y0 = ty + text.get_height() + gap

        for i in range(line_w):

            t = abs(i - line_w / 2) / (line_w / 2)

            alpha = int(255 * max(0.0, 1.0 - t * t))

            surf.fill(
                (*LINE_COLOR, alpha),
                pygame.Rect(x0 + i, y0, 1, line_h)
            )

        return surf

    def _progress(self):
        

        age = self.age

        if age < FADE_IN:

            t = age / FADE_IN
            t = t * t * (3 - 2 * t)

            return t, (1.0 - t) * 10

        if age < FADE_IN + HOLD:
            return 1.0, 0.0

        t = (age - FADE_IN - HOLD) / FADE_OUT
        t = min(1.0, t)
        t = t * t * (3 - 2 * t)

        return 1.0 - t, 0.0

    def draw(self, screen):

        if self.age is None or self.image is None:
            return

        opacity, drop = self._progress()

        if opacity <= 0:
            return

        self.image.set_alpha(int(255 * opacity))

        rect = self.image.get_rect(
            center=(self.width // 2, int(self.height * CENTER_Y))
        )

        screen.blit(self.image, rect.move(0, drop))