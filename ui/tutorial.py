import math
from pathlib import Path

import pygame

ROOT_DIR = Path(__file__).resolve().parent.parent

UI_DIR = ROOT_DIR / "assets" / "maps" / "ui"


# ---------- IMAGENES DEL TUTORIAL ----------
# Nombre de cada imagen (se busca dentro de assets/maps/ui/ y, si no
# esta ahi, en cualquier otra carpeta de assets).
CHARACTER_IMAGE = "botayuda.png"   # el personaje que ayuda
FRAME_IMAGE = "texto.png"          # el cuadro donde va el texto

# Recorte de cada imagen (x, y, ancho, alto). Los valores de abajo son
# para las imagenes actuales, que tienen cosas de sobra alrededor.
# Si tu imagen nueva ya viene limpia, poné None: usa la imagen entera
# sin los bordes transparentes.
CHARACTER_CROP = pygame.Rect(490, 214, 194, 319)
FRAME_CROP = None   # texto.png nuevo (800x285): se usa entero


TUTORIAL_PAGES = [
    "Bienvenido a Keep It Lit. Tu luz es tu vida: si se apaga, perdes.",
    "Movete con W A S D o con las flechas del teclado.",
    "Click izquierdo: pegar con tu luz. Rompe puertas y abre cofres.",
    "E: agarrar objetos del piso o hablar con el vendedor.",
    "Teclas 1 a 5: elegir casillero. Click derecho: usar el objeto.",
    "Q: soltar lo que tengas elegido. ESC: guardar y volver al menu.",
]

# Letras azules (oscuras para que se lean sobre el cuadro gris)
TEXT_COLOR = (25, 60, 150)
SHADOW_COLOR = (225, 230, 240)
HINT_COLOR = (60, 95, 170)

# El interior de texto.png es semitransparente: se rellena con este
# color para que el cuadro no deje ver el mapa por detras.
FRAME_BACKING = (255, 255, 255)


class Tutorial:


    SLIDE_TIME = 0.5


    INPUT_DELAY = 0.6

    def __init__(
        self,
        screen_size,
        pages=None,
        char_height=150,
        frame_width=400,
        margin=16
    ):

        self.width, self.height = screen_size
        self.pages = list(pages or TUTORIAL_PAGES)
        self.margin = margin

        self.index = 0
        self.active = bool(self.pages)


        self.phase = "in"
        self.phase_time = 0.0
        self.age = 0.0


        char = self._load_cropped(CHARACTER_IMAGE, CHARACTER_CROP)
        frame = self._load_cropped(FRAME_IMAGE, FRAME_CROP)

        if char is None:
            char = self._fallback_character(319)

        if frame is None:
            frame = self._fallback_frame(428, 152)

        frame = self._solidify(frame, FRAME_BACKING)

        char_w = int(char.get_width() * char_height / char.get_height())

        self.character = pygame.transform.smoothscale(
            char, (char_w, char_height)
        )

        frame_height = int(
            frame.get_height() * frame_width / frame.get_width()
        )

        self.frame = pygame.transform.smoothscale(
            frame, (frame_width, frame_height)
        )


        self.char_rect = self.character.get_rect(
            bottomright=(self.width - margin, self.height - margin)
        )


        self.frame_rect = self.frame.get_rect(
            bottomright=(
                self.char_rect.left - 8,
                self.char_rect.bottom - 18
            )
        )


        self.group_rect = self.char_rect.union(self.frame_rect)


        self.font = pygame.font.Font(None, 28)
        self.hint_font = pygame.font.Font(None, 20)
        self.counter_font = pygame.font.Font(None, 20)

        self.pad_x = 20
        self.pad_y = 14

        self._lines_cache = {}
        self._text_cache = {}


    @staticmethod
    def _find_image(name):
        direct = UI_DIR / name

        if direct.exists():
            return direct

        for folder in (ROOT_DIR / "assets", ROOT_DIR):

            if folder.exists():

                for found in folder.rglob(name):
                    return found

        return None

    @staticmethod
    def _fallback_character(height):
        surf = pygame.Surface((int(height * 0.6), height), pygame.SRCALPHA)

        w = surf.get_width()

        body = pygame.Rect(0, height // 3, w * 2 // 3, height * 2 // 3)
        body.centerx = w // 2

        pygame.draw.rect(
            surf, (70, 66, 64), body, border_radius=body.width // 2
        )
        pygame.draw.circle(
            surf, (70, 66, 64), (w // 2, height // 3), w // 2 - 2
        )
        pygame.draw.circle(
            surf, (240, 232, 228), (w // 2 + 3, height // 3), w // 2 - 12
        )

        for dx in (-9, 9):
            pygame.draw.circle(
                surf, (60, 58, 58), (w // 2 + 3 + dx, height // 3 - 2), 5
            )

        return surf

    @staticmethod
    def _fallback_frame(width, height):
        surf = pygame.Surface((width, height), pygame.SRCALPHA)

        surf.fill((84, 62, 8))
        pygame.draw.rect(
            surf, (100, 78, 12), surf.get_rect().inflate(-8, -8)
        )

        return surf

    @staticmethod
    def _solidify(surf, color):
        """Pone un fondo solido detras de la silueta del cuadro, asi lo
        semitransparente del interior no deja ver lo que hay detras."""

        mask = pygame.mask.from_surface(surf, 40)

        base = mask.to_surface(
            setcolor=(color[0], color[1], color[2], 255),
            unsetcolor=(0, 0, 0, 0)
        )

        base.blit(surf, (0, 0))

        return base

    @classmethod
    def _load_cropped(cls, name, crop):
        path = cls._find_image(name)

        if path is None:
            print(f"[tutorial] No se encontro {name}: uso un dibujo simple")
            return None

        image = pygame.image.load(str(path)).convert_alpha()

        if crop is None:
            area = image.get_bounding_rect()
        else:
            area = crop.clip(image.get_rect())

        if area.width <= 0 or area.height <= 0:
            area = image.get_bounding_rect()

        if area.width <= 0 or area.height <= 0:
            return image

        return image.subsurface(area).copy()

    @staticmethod
    def _wrap(font, text, max_width):

        lines = []
        line = ""

        for word in text.split():

            test = (line + " " + word).strip()

            if line and font.size(test)[0] > max_width:

                lines.append(line)
                line = word

            else:

                line = test

        if line:
            lines.append(line)

        return lines

    def _text(self, font, text, color):
        key = (id(font), text, color)

        if key not in self._text_cache:
            self._text_cache[key] = font.render(text, True, color)

        return self._text_cache[key]

    def _lines(self, index):

        if index not in self._lines_cache:

            max_w = self.frame_rect.width - self.pad_x * 2

            self._lines_cache[index] = self._wrap(
                self.font, self.pages[index], max_w
            )

        return self._lines_cache[index]


    def handle_event(self, event):

        if not self.active or self.phase != "show":
            return False

        if event.type != pygame.KEYDOWN:
            return False

        if self.age < self.INPUT_DELAY:
            return False


        if event.key == pygame.K_ESCAPE:
            return False

        self.index += 1

        if self.index >= len(self.pages):

            self.index = len(self.pages) - 1
            self.phase = "out"
            self.phase_time = 0.0

        return True


    def update(self, dt):

        if not self.active:
            return

        self.age += dt
        self.phase_time += dt

        if self.phase == "in" and self.phase_time >= self.SLIDE_TIME:

            self.phase = "show"
            self.phase_time = 0.0

        elif self.phase == "out" and self.phase_time >= self.SLIDE_TIME:

            self.active = False


    def _offset(self):

        distance = self.width - self.group_rect.left + 10

        if self.phase == "in":

            t = min(1.0, self.phase_time / self.SLIDE_TIME)
            ease = 1 - (1 - t) ** 3

            return int(distance * (1 - ease))

        if self.phase == "out":

            t = min(1.0, self.phase_time / self.SLIDE_TIME)
            ease = t ** 3

            return int(distance * ease)

        return 0

    def draw(self, screen):

        if not self.active:
            return

        dx = self._offset()


        bob = 0

        if self.phase == "show":
            bob = int(round(math.sin(self.age * 4) * 2))

        screen.blit(
            self.character,
            self.char_rect.move(dx, bob)
        )

        frame_pos = self.frame_rect.move(dx, 0)

        screen.blit(self.frame, frame_pos)


        lines = self._lines(self.index)

        line_h = self.font.get_linesize()

        block_h = line_h * len(lines)

        top = frame_pos.top + max(
            self.pad_y,
            (frame_pos.height - block_h) // 2 - 6
        )

        for i, line in enumerate(lines):

            y = top + i * line_h

            shadow = self._text(self.font, line, SHADOW_COLOR)
            label = self._text(self.font, line, TEXT_COLOR)

            screen.blit(shadow, (frame_pos.left + self.pad_x + 1, y + 1))
            screen.blit(label, (frame_pos.left + self.pad_x, y))


        counter = self._text(
            self.counter_font,
            f"{self.index + 1}/{len(self.pages)}",
            HINT_COLOR
        )

        screen.blit(
            counter,
            counter.get_rect(
                topright=(
                    frame_pos.right - 10,
                    frame_pos.top + 8
                )
            )
        )


        if self.phase == "show" and self.age >= self.INPUT_DELAY:

            if int(self.age * 2) % 2 == 0:

                last = self.index == len(self.pages) - 1

                text = (
                    "Presiona una tecla para cerrar"
                    if last
                    else "Presiona una tecla para seguir"
                )

                hint = self._text(self.hint_font, text, HINT_COLOR)

                screen.blit(
                    hint,
                    hint.get_rect(
                        bottomright=(
                            frame_pos.right - 12,
                            frame_pos.bottom - 8
                        )
                    )
                )