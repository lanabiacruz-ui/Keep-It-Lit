import math
import random
import re
from pathlib import Path

import pygame

from core.audio_manager import audio

ROOT_DIR = Path(__file__).resolve().parent.parent

UI_DIR = ROOT_DIR / "assets" / "maps" / "ui"


# Nombre del ayudante. Lo usan el tutorial y el cartelito de ayuda.
HELPER_NAME = "Cenizo"

CHARACTER_IMAGE = "botayuda.png"
FRAME_IMAGE = "texto.png"

# None = se recorta solo al borde visible de la imagen
CHARACTER_CROP = None
FRAME_CROP = None


# Marcado de los textos: lo que va entre [[ ]] se resalta como una tecla.
#   "Apretá [[E]] para agarrar"  ->  la E se dibuja como un botoncito.
TUTORIAL_PAGES = [
    "¡Hola! Soy [[Cenizo]], tu ayudante. Tu luz es tu vida: la barra naranja de abajo. Se gasta con el tiempo y, si se apaga, perdés.",
    "Moverte: [[W]] [[A]] [[S]] [[D]]. Saltar: [[ESPACIO]] (sirve para esquivar a los jefes). Atacar: [[CLICK IZQ.]] (cada golpe gasta un poquito de luz).",
    "Agarrar: acercate a algo del piso y apretá [[E]]. Soltar: [[Q]]. Soltar toda la casilla: [[SHIFT + Q]]. Soltar todo: [[CTRL + Q]] (la luz equipada se queda).",
    "Lo que tirás al piso se esfuma a los [[5 MINUTOS]]. Si lo soltás junto a una bolsa o un cofre, queda adentro para siempre.",
    "Inventario: [[1]] al [[4]] son tus casilleros, [[5]] y [[6]] las pociones y [[7]] tu luz. También sirve la [[RUEDITA]] del mouse.",
    "Usar un objeto: elegilo y apretá [[F]] o [[CLICK DER.]]. Si mantenés click izquierdo sobre un casillero, te cuento qué hace.",
    "Recuperar luz: la madera suma 25%, la resina 90% de a poco y el aceite te deja en 75% y te da velocidad. ¡Usalos ANTES de quedarte a oscuras!",
    "Monedas: se juntan solas al acercarte. Dorada = 1, azul = 5, roja = 10. Con ellas comprás cosas en la tienda: [[F]] cerca del vendedor.",
    "En la pausa ([[ESC]]) está la enciclopedia de criaturas. Tocá COBRAR en cada criatura descubierta y te llevás monedas de regalo.",
    "Salas de combate: empezá por la Zona 1 (Orkun, a la derecha). Su jefe suelta una llave dorada para la Zona 2. ¡Ojo con los mosquitos!",
    "Eso es todo. Si te perdés, abrí la pausa con [[ESC]]. ¡Que tu luz nunca se apague!",
]

# Colores de Cenizo: azul fantasma, con azul transparente
TEXT_COLOR = (20, 45, 125)
SHADOW_COLOR = (225, 236, 252)
HINT_COLOR = (45, 80, 165)

KEY_BG = (122, 168, 238)
KEY_BG_TOP = (170, 205, 250)
KEY_EDGE = (28, 58, 140)
KEY_SIDE = (58, 100, 196)
KEY_TEXT = (12, 30, 95)

NAME_BG = (110, 160, 236)
NAME_EDGE = (28, 58, 140)
NAME_TEXT = (236, 245, 255)

DOT_ON = (96, 146, 240)
DOT_ON_EDGE = (20, 48, 130)
DOT_DONE = (150, 185, 240)
DOT_NEXT = (130, 150, 200)

ARROW_COLOR = (70, 120, 225)
SPARK_COLOR = (170, 210, 255)
GLOW_COLOR = (110, 160, 255)

# panel: borde azul oscuro y relleno azul transparente
FRAME_BORDER = (36, 72, 158)
FRAME_FILL = (168, 200, 246)
FRAME_FILL_ALPHA = 205

FRAME_BACKING = (255, 255, 255)

# Colores de Cenizo en un solo lugar. Otros personajes (ver
# ui/shop_dialog.py) heredan de Tutorial y cambian THEME.
DEFAULT_THEME = {
    "name": HELPER_NAME,
    "text": TEXT_COLOR,
    "shadow": SHADOW_COLOR,
    "hint": HINT_COLOR,
    "name_bg": NAME_BG,
    "name_edge": NAME_EDGE,
    "name_text": NAME_TEXT,
    "dot_on": DOT_ON,
    "dot_on_edge": DOT_ON_EDGE,
    "dot_done": DOT_DONE,
    "dot_next": DOT_NEXT,
    "arrow": ARROW_COLOR,
    "spark": SPARK_COLOR,
    "glow": GLOW_COLOR,
    "frame_border": FRAME_BORDER,
    "frame_fill": FRAME_FILL,
    "frame_fill_alpha": FRAME_FILL_ALPHA,
}

_MARK = re.compile(r"(\[\[|\]\])")


_GHOST_FRAMES = {}


def ghost_frame(surf, border=None, fill=None, fill_alpha=None):
    """Pinta el panel con los colores de Cenizo (azul y azul transparente).
    Con border / fill / fill_alpha se pinta con otros colores."""

    border = border or FRAME_BORDER
    fill = fill or FRAME_FILL
    fill_alpha = FRAME_FILL_ALPHA if fill_alpha is None else fill_alpha

    key = (surf.get_size(), border, fill, fill_alpha)

    if key in _GHOST_FRAMES:
        return _GHOST_FRAMES[key].copy()

    w, h = surf.get_size()

    out = pygame.Surface((w, h), pygame.SRCALPHA)

    for y in range(h):
        for x in range(w):

            r, g, b, a = surf.get_at((x, y))

            if a == 0:
                continue

            t = max(0.0, min(1.0, ((r + g + b) / 3 - 95) / 70))

            color = tuple(
                int(border[i] + (fill[i] - border[i]) * t)
                for i in range(3)
            )

            alpha = (255 + (fill_alpha - 255) * t) * a / 255

            out.set_at((x, y), (*color, int(alpha)))

    _GHOST_FRAMES[key] = out

    return out.copy()


def parse_markup(text):
    """Devuelve (texto_plano, flags) donde flags[i] es 0 si el caracter i
    es texto normal, o el numero de grupo ([[ ]]) al que pertenece. Asi
    "[[W]] [[A]]" son dos botones y "[[CTRL + Q]]" es uno solo."""

    plain = []
    flags = []

    group = 0
    on = 0

    for part in _MARK.split(text):

        if part == "[[":
            group += 1
            on = group
        elif part == "]]":
            on = 0
        else:
            plain.append(part)
            flags.extend([on] * len(part))

    return "".join(plain), flags


def wrap_marked(font, plain, flags, max_width):
    """Parte el texto en lineas por palabras. Devuelve una lista de
    (linea, flags_de_la_linea)."""

    words = []

    start = None

    for i, ch in enumerate(plain + " "):

        if ch.isspace():

            if start is not None:
                words.append((start, i))
                start = None

        elif start is None:

            start = i

    lines = []

    cur_text = ""
    cur_flags = []

    for a, b in words:

        word = plain[a:b]
        word_flags = flags[a:b]

        test = (cur_text + " " + word) if cur_text else word

        if cur_text and font.size(test)[0] > max_width:

            lines.append((cur_text, cur_flags))

            cur_text = word
            cur_flags = list(word_flags)

        else:

            if cur_text:
                # el espacio se resalta solo si une dos palabras del mismo grupo
                joined = (
                    cur_flags[-1] if cur_flags[-1] == word_flags[0] else 0
                )
                cur_flags = cur_flags + [joined] + list(word_flags)
            else:
                cur_flags = list(word_flags)

            cur_text = test

    if cur_text:
        lines.append((cur_text, cur_flags))

    return lines


def runs(text, flags):
    """Agrupa caracteres consecutivos con la misma marca."""

    out = []

    for ch, flag in zip(text, flags):

        if out and out[-1][1] == flag:
            out[-1][0] += ch
        else:
            out.append([ch, flag])

    return out


def draw_marked_line(
    screen, font, text, flags, x, y, text_color=None, shadow_color=None
):
    """Dibuja una linea; lo marcado con [[ ]] sale como boton de tecla."""

    color = text_color or TEXT_COLOR
    shadow = shadow_color or SHADOW_COLOR

    for chunk, flag in runs(text, flags):

        w = font.size(chunk)[0]

        if flag:

            # tecla amarilla con relieve: base oscura abajo y cara clara
            chip = pygame.Rect(x - 4, y - 2, w + 8, font.get_linesize() - 3)

            base = chip.copy()
            base.height += 3

            pygame.draw.rect(screen, KEY_SIDE, base, border_radius=6)
            pygame.draw.rect(screen, KEY_EDGE, base, width=1, border_radius=6)

            face = chip.inflate(-2, -2)
            face.height -= 1

            pygame.draw.rect(screen, KEY_BG, face, border_radius=5)
            pygame.draw.line(
                screen, KEY_BG_TOP,
                (face.left + 4, face.top + 1), (face.right - 5, face.top + 1)
            )

            screen.blit(font.render(chunk, True, KEY_TEXT), (x, y))

        else:

            screen.blit(font.render(chunk, True, shadow), (x + 1, y + 1))
            screen.blit(font.render(chunk, True, color), (x, y))

        x += w


class Tutorial:

    SLIDE_TIME = 0.5

    INPUT_DELAY = 0.45

    START_FONT = 30
    MIN_FONT = 18

    TYPE_SPEED = 46.0
    BLIP_EVERY = 2
    PAUSE_END = 0.16
    PAUSE_COMMA = 0.07
    BLIPS = ("talk_a", "talk_b", "talk_c", "talk_d")

    HOP_TIME = 0.4

    THEME = DEFAULT_THEME

    def __init__(
        self,
        screen_size,
        pages=None,
        char_height=170,
        frame_width=450,
        margin=16,
        can_skip=False
    ):

        self.can_skip = can_skip
        self.skip_all = False

        self.width, self.height = screen_size
        self.pages = list(pages or TUTORIAL_PAGES)
        self.margin = margin

        self.parsed = [parse_markup(p) for p in self.pages]

        self.index = 0
        self.active = bool(self.pages)

        self.phase = "in"
        self.phase_time = 0.0
        self.age = 0.0

        # salto del ayudante cuando cambia la pagina
        self.hop = 0.0

        self.sparks = []

        char = self._source_character()
        frame = self._load_cropped(FRAME_IMAGE, FRAME_CROP)

        if frame is None:
            frame = self._fallback_frame(428, 152)

        frame = self._solidify(frame, FRAME_BACKING)

        self.character = self._scale_character(char, char_height)

        frame_height = int(
            frame.get_height() * frame_width / frame.get_width()
        )

        self.frame = pygame.transform.smoothscale(
            frame, (frame_width, frame_height)
        )

        t = self.THEME

        self.frame = ghost_frame(
            self.frame,
            t["frame_border"], t["frame_fill"], t["frame_fill_alpha"]
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

        self.hint_font = pygame.font.Font(None, 21)
        self.counter_font = pygame.font.Font(None, 20)
        self.name_font = pygame.font.Font(None, 22)

        self.pad_x = 22
        self.pad_y = 14

        self._lines_cache = {}
        self._text_cache = {}
        self._fonts = {}

        self.glow = self._make_glow(char_height, t["glow"])

        self._reset_typing()
        self._pop()

    # ---------------------------------------------------------- imagenes

    def _source_character(self):
        """Imagen original del personaje (sin escalar)."""

        char = self._load_cropped(CHARACTER_IMAGE, CHARACTER_CROP)

        if char is None:
            char = self._fallback_character(319)

        return char

    def _scale_character(self, char, char_height):

        char_w = int(char.get_width() * char_height / char.get_height())

        return pygame.transform.smoothscale(char, (char_w, char_height))

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
    def _make_glow(char_height, color=GLOW_COLOR):
        """Halo azul detras del ayudante: es un fantasma que cuida tu luz."""

        size = int(char_height * 1.5)

        glow = pygame.Surface((size, size), pygame.SRCALPHA)

        center = size // 2

        for r in range(center, 0, -3):

            alpha = int(46 * (1 - r / center) ** 2)

            pygame.draw.circle(glow, (*color, alpha), (center, center), r)

        return glow

    # ------------------------------------------------------------ texto

    def _text(self, font, text, color):
        key = (id(font), text, color)

        if key not in self._text_cache:
            self._text_cache[key] = font.render(text, True, color)

        return self._text_cache[key]

    def _font_size(self, size):

        font = self._fonts.get(size)

        if font is None:

            font = pygame.font.Font(None, size)

            self._fonts[size] = font

        return font

    def _lines(self, index):

        if index not in self._lines_cache:

            plain, flags = self.parsed[index]

            max_w = self.frame_rect.width - self.pad_x * 2

            max_h = self.frame_rect.height - 56

            size = self.START_FONT

            while True:

                font = self._font_size(size)

                lines = wrap_marked(font, plain, flags, max_w)

                if (
                    len(lines) * font.get_linesize() <= max_h
                    or size <= self.MIN_FONT
                ):
                    break

                size -= 1

            self._lines_cache[index] = (font, lines)

        return self._lines_cache[index]

    # ----------------------------------------------------------- tipeo

    def _reset_typing(self):

        self.shown = 0
        self.reveal = 0.0
        self.pause = 0.0
        self._blip_count = 0
        self._last_blip = None

    def _flat(self):

        _, lines = self._lines(self.index)

        return "".join(text for text, _ in lines)

    def _typing_done(self):

        return self.shown >= len(self._flat())

    def _blip(self):

        names = [n for n in self.BLIPS if n != self._last_blip]

        self._last_blip = random.choice(names)

        audio.play(self._last_blip)

    def _update_typing(self, dt):

        if self.phase != "show" or self._typing_done():
            return

        if self.pause > 0.0:

            self.pause -= dt

            return

        flat = self._flat()

        self.reveal += dt * self.TYPE_SPEED

        while self.shown < min(int(self.reveal), len(flat)):

            ch = flat[self.shown]

            self.shown += 1

            if ch.isalnum():

                self._blip_count += 1

                if self._blip_count % self.BLIP_EVERY == 0:
                    self._blip()

            if ch in ".!?:":

                self.pause = self.PAUSE_END
                self.reveal = float(self.shown)

                break

            if ch in ",;":

                self.pause = self.PAUSE_COMMA
                self.reveal = float(self.shown)

                break

    # --------------------------------------------------------- efectos

    def _pop(self):
        """Saltito del ayudante y chispitas al cambiar de pagina."""

        self.hop = self.HOP_TIME

        cx = self.char_rect.centerx
        top = self.char_rect.top + 20

        for _ in range(7):

            self.sparks.append({
                "x": cx + random.uniform(-26, 26),
                "y": top + random.uniform(-6, 24),
                "vx": random.uniform(-40, 40),
                "vy": random.uniform(-90, -40),
                "life": random.uniform(0.5, 0.9),
                "age": 0.0,
                "size": random.randint(3, 5),
            })

    def _update_fx(self, dt):

        if self.hop > 0:
            self.hop = max(0.0, self.hop - dt)

        for s in self.sparks:

            s["age"] += dt
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt

        self.sparks = [s for s in self.sparks if s["age"] < s["life"]]

    # --------------------------------------------------------- entrada

    def _close(self):

        self.phase = "out"
        self.phase_time = 0.0

    def _advance(self):

        if not self._typing_done():

            self.shown = len(self._flat())

            return True

        if self.index >= len(self.pages) - 1:

            self._close()

            return True

        self.index += 1

        self._reset_typing()
        self._pop()

        return True

    def _back(self):

        if self.index <= 0:
            return True

        self.index -= 1

        self._reset_typing()

        # al volver atras el texto aparece completo, sin esperar
        self.shown = len(self._flat())

        self._pop()

        return True

    def handle_event(self, event):

        if not self.active or self.phase != "show":
            return False

        if self.age < self.INPUT_DELAY:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:
                return self._advance()

            if event.button == 3:
                return self._back()

            return False

        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_ESCAPE:
            return False

        if self.can_skip and event.key == pygame.K_k:

            self.skip_all = True
            self._close()

            return True

        if event.key in (
            pygame.K_SPACE,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_RIGHT,
        ):
            return self._advance()

        if event.key in (pygame.K_LEFT, pygame.K_BACKSPACE):
            return self._back()

        return False

    def update(self, dt):

        if not self.active:
            return

        self.age += dt
        self.phase_time += dt

        self._update_typing(dt)
        self._update_fx(dt)

        if self.phase == "in" and self.phase_time >= self.SLIDE_TIME:

            self.phase = "show"
            self.phase_time = 0.0

        elif self.phase == "out" and self.phase_time >= self.SLIDE_TIME:

            self.active = False

    # ---------------------------------------------------------- dibujo

    def _draw_front(self, screen, dx):
        """Lo que se dibuja delante del personaje (por defecto nada)."""

    def _offset(self):

        distance = self.width - self.group_rect.left + 10

        if self.phase == "in":

            t = min(1.0, self.phase_time / self.SLIDE_TIME)

            # entra con un pequeño rebote
            ease = 1 - (1 - t) ** 3

            overshoot = math.sin(t * math.pi) * 0.06

            return int(distance * (1 - ease - overshoot))

        if self.phase == "out":

            t = min(1.0, self.phase_time / self.SLIDE_TIME)
            ease = t ** 3

            return int(distance * ease)

        return 0

    def _draw_line(self, screen, font, text, flags, x, y, count):
        """Una linea con las teclas resaltadas. count = cuantos caracteres
        mostrar (efecto maquina de escribir)."""

        draw_marked_line(
            screen, font, text[:count], flags[:count], x, y,
            self.THEME["text"], self.THEME["shadow"]
        )

    def _draw_dots(self, screen, frame_pos):

        total = len(self.pages)

        if total <= 1:
            return

        t = self.THEME

        gap = 12

        x = frame_pos.right - 46 - gap * (total - 1)
        y = frame_pos.top + 26

        for i in range(total):

            if i == self.index:
                pygame.draw.circle(screen, t["dot_on"], (x, y), 5)
                pygame.draw.circle(screen, t["dot_on_edge"], (x, y), 5, 1)
            else:
                color = t["dot_done"] if i < self.index else t["dot_next"]
                pygame.draw.circle(screen, color, (x, y), 3)

            x += gap

    def _draw_name_tag(self, screen, frame_pos):

        t = self.THEME

        label = self._text(self.name_font, t["name"].upper(), t["name_text"])

        tag = label.get_rect()
        tag.inflate_ip(18, 6)
        tag.bottomleft = (frame_pos.left + 16, frame_pos.top + 6)

        pygame.draw.rect(screen, t["name_bg"], tag, border_radius=8)
        pygame.draw.rect(
            screen, t["name_edge"], tag, width=2, border_radius=8
        )

        screen.blit(label, label.get_rect(center=tag.center))

    def _draw_sparks(self, screen, dx):

        for s in self.sparks:

            t = s["age"] / s["life"]

            alpha = int(255 * (1 - t))

            size = s["size"]

            star = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)

            c = size * 2

            pts = [
                (c, c - size * 2), (c + 1, c - 1), (c + size * 2, c),
                (c + 1, c + 1), (c, c + size * 2), (c - 1, c + 1),
                (c - size * 2, c), (c - 1, c - 1),
            ]

            pygame.draw.polygon(star, (*self.THEME["spark"], alpha), pts)

            screen.blit(
                star, (int(s["x"]) + dx - c, int(s["y"]) - c)
            )

    def draw(self, screen):

        if not self.active:
            return

        dx = self._offset()

        # halo detras del ayudante
        pulse = 0.8 + 0.2 * math.sin(self.age * 2.2)

        glow = self.glow

        if pulse < 0.999:
            glow = pygame.transform.smoothscale(
                self.glow,
                (int(self.glow.get_width() * pulse),
                 int(self.glow.get_height() * pulse))
            )

        screen.blit(
            glow,
            glow.get_rect(center=self.char_rect.center).move(dx, 0)
        )

        bob = 0

        if self.phase == "show":

            if self._typing_done():
                bob = int(round(math.sin(self.age * 3) * 3))
            else:
                bob = int(round(math.sin(self.age * 22) * 2.5))

        if self.hop > 0:

            t = 1 - self.hop / self.HOP_TIME

            bob -= int(math.sin(t * math.pi) * 14)

        screen.blit(
            self.character,
            self.char_rect.move(dx, bob)
        )

        self._draw_front(screen, dx)

        self._draw_sparks(screen, dx)

        frame_pos = self.frame_rect.move(dx, 0)

        screen.blit(self.frame, frame_pos)

        self._draw_name_tag(screen, frame_pos)

        font, lines = self._lines(self.index)

        line_h = font.get_linesize()

        block_h = line_h * len(lines)

        top = frame_pos.top + max(
            self.pad_y + 4,
            (frame_pos.height - block_h) // 2 - 4
        )

        remaining = (
            sum(len(text) for text, _ in lines)
            if self.phase == "out" else self.shown
        )

        for i, (text, flags) in enumerate(lines):

            if remaining <= 0:
                break

            self._draw_line(
                screen, font, text, flags,
                frame_pos.left + self.pad_x,
                top + i * line_h,
                remaining
            )

            remaining -= len(text)

        self._draw_dots(screen, frame_pos)

        if self.phase != "show" or self.age < self.INPUT_DELAY:
            return

        # ayuda de teclas, abajo del globo
        done = self._typing_done()

        last = self.index == len(self.pages) - 1

        parts = []

        if self.index > 0:
            parts.append("← volver")

        parts.append("cerrar" if last and done else "seguir")

        text = "   ".join(parts)

        hint = self._text(self.hint_font, text, self.THEME["hint"])

        hint_pos = hint.get_rect(
            bottomright=(frame_pos.right - 30, frame_pos.bottom - 9)
        )

        screen.blit(hint, hint_pos)

        # triangulito que parpadea cuando se puede seguir
        if done:

            tx = frame_pos.right - 18
            ty = frame_pos.bottom - 17 + int(math.sin(self.age * 6) * 2)

            pygame.draw.polygon(
                screen, self.THEME["arrow"],
                [(tx - 5, ty - 5), (tx + 5, ty - 5), (tx, ty + 3)]
            )

        if self.can_skip:

            skip = self._text(
                self.hint_font, "K: sacar tutorial", self.THEME["hint"]
            )

            screen.blit(
                skip,
                skip.get_rect(
                    bottomleft=(
                        frame_pos.left + self.pad_x,
                        frame_pos.bottom - 9
                    )
                )
            )