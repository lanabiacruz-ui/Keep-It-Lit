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

    # ---------- LO BASICO ----------
    "¡Bienvenido a Keep It Lit! Tu luz es tu vida: la barra naranja de abajo. Se gasta con el tiempo y, si se apaga, perdés.",
    "MOVERTE: usá W A S D. Buscá en esta cabaña objetos para alimentar tu llama antes de que se apague.",
    "ATACAR: click izquierdo (o ESPACIO) para pegar con tu luz. Mantené el click para seguir pegando. Cada golpe le baja vida a tu luz.",
    "AGARRAR: acercate a un objeto o a una luz del piso y apretá E. Con Q soltás lo que tengas seleccionado.",
    "INVENTARIO: tenés 4 casilleros (teclas 1 al 4). La tecla 5 elige el casillero de tu luz equipada, que está aparte.",
    "USAR OBJETOS: elegí el casillero y apretá F o click derecho. Mantené click izquierdo sobre un casillero para ver qué hace el objeto.",
    "MENÚ: ESC o el botón de menú abren la pausa: ajustes, enciclopedia de enemigos y volver al menú. Al volver al menú se guarda tu partida.",

    "OBJETIVOS: arriba a la derecha ves tu objetivo actual. Apretá TAB o el botón con el signo menos para minimizarlo, y TAB o la pestañita para abrirlo.",

    # ---------- LUCES ----------
    "LUCES: el fósforo dura 30 segundos, la vela 60 y la antorcha 120. Al agarrar una se equipa sola en el casillero de la luz. Solo podés llevar una.",
    "VELA Y ANTORCHA: alumbran más y cada tanto entran en FURIA: pegan rapidísimo. Son las únicas que rompen las puertas grises.",
    "ANTORCHA: apretá G para cambiar entre golpe común y bola de fuego, que sale disparada hacia el mouse. Solo la antorcha lanza fuego.",

    # ---------- OBJETOS ----------
    "RECUPERAR LUZ: la madera suma 25% a tu luz, la resina la recupera de a poco y el aceite la deja en 75% y te da velocidad un rato.",
    "ESCUDO: el hongo azul te da 25% de escudo. El escudo se gasta antes que tu vida y no se consume con el tiempo.",
    "MÁS OBJETOS: la cera hace que tu luz dure casi 3 veces más, la pólvora hace que tu luz queme a los enemigos y la esfera de vidrio amplía tu luz.",
    "REPELENTE: durante casi 2 minutos tu luz espanta a los mosquitos y los que tenés pegados se sueltan.",
    "IMÁN: una vez usado, atrae solo las monedas, gemas e items cercanos durante 7 minutos. Apretá O para prenderlo o apagarlo (apagado no gasta tiempo).",

    # ---------- MAPA ----------
    "PUERTAS: pegales con la luz para romperlas (cada golpe gasta un poco de luz). Las marrones aguantan 2 golpes y las verdes 6. Una puerta rota no vuelve.",
    "PUERTAS GRISES: solo las rompen la vela y la antorcha. Las azules tienen candado: todavía no se pueden abrir.",
    "COFRES: pegale a un cofre con la luz para abrirlo. Sale un minijuego: frená el marcador dentro de la zona con click, ESPACIO o E. Hay que acertar 3 veces.",
    "COFRES: si fallás, el minijuego termina; ESC lo cancela. Después tardan 3 minutos en recargarse. La ganzúa abre un cofre cercano sin minijuego.",
    "MONEDAS Y GEMAS: las monedas amarillas valen 1, las azules 5 y las rojas 10, y se juntan solas al acercarte. Las gemas son el premio por completar una sala.",
    "TIENDA: el vendedor está en la sala de arriba, en el centro. Acercate y apretá F para comprar luces y objetos con tus monedas.",

    # ---------- COMBATE ----------
    "SALAS DE COMBATE: las dos salas grandes (izquierda y derecha) tienen oleadas de enemigos. Al entrar aparece un menú: Salir, Jugar con escape o Jugar sin escape.",
    "CON ESCAPE podés irte caminando de la sala (cancela la oleada). SIN ESCAPE la entrada se bloquea mientras peleás, pero el premio vale el doble.",
    "OLEADAS: al derrotar al último enemigo aparece un cofre que explota y tira monedas. Juntalas y vuelve el menú para la siguiente oleada.",
    "ATENCIÓN: si tu luz se apaga peleando en una sala de combate, perdés de verdad, aunque hayas elegido jugar con escape.",
    "SALAS COMPLETAS: la sala de la derecha tiene 10 oleadas y la de la izquierda 2, con el Guardián al final. Al completarla se cierra para siempre.",
    "ENEMIGOS: las piñas chocan y rebotan, los troncos disparan proyectiles, los mosquitos se pegan, los hongun explotan y los guardianes pelean con armas.",
    "DESTELLOS: pasean dando un poco de luz. Si te ven, parpadean en blanco y salen corriendo: al chocarte explotan y te dejan la pantalla en blanco unos 5 segundos. Matalos a golpes antes de que te alcancen y no explotan.",
    "MOSQUITOS: si tu luz los toca van directo hacia vos y se pegan un minuto chupándote vida. Después se sueltan y vuelven a intentarlo.",
    "ENCICLOPEDIA: en el menú de pausa. Cada enemigo se descubre cuando te lo encontrás en una oleada, y se empieza de cero en cada partida.",
    "SALA IZQUIERDA: los bloques de la cruz de piedra abren y cierran los pasos solos. Si el hueco parpadea en rojo, salí rápido: te aplastan y te sacan mucha luz.",

    # ---------- PERDER / AYUDA ----------
    "PERDER: en modo Normal perdés todos tus objetos y te quedás con un fósforo en la cabaña. En modo Hardcore se borra toda la partida.",
    "AYUDA: podés volver a ver estas instrucciones cuando quieras apretando F1. ¡Mucha suerte y que tu luz nunca se apague!",
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

    # Letra mas chica a la que se llega para que el texto entre
    MIN_FONT = 17

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
        self._fonts = {}


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

    def _font_size(self, size):

        font = self._fonts.get(size)

        if font is None:

            font = pygame.font.Font(None, size)

            self._fonts[size] = font

        return font

    def _lines(self, index):
        """Devuelve (fuente, lineas) de la pagina. Si el texto no entra
        en el cuadro, se achica la letra hasta que entre."""

        if index not in self._lines_cache:

            max_w = self.frame_rect.width - self.pad_x * 2

            # Alto libre: sin el contador (arriba) ni el aviso (abajo)
            max_h = self.frame_rect.height - 52

            size = 28

            while True:

                font = self._font_size(size)

                lines = self._wrap(font, self.pages[index], max_w)

                if (
                    len(lines) * font.get_linesize() <= max_h
                    or size <= self.MIN_FONT
                ):
                    break

                size -= 1

            self._lines_cache[index] = (font, lines)

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

        # ENTER: saltar todas las instrucciones
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):

            self.phase = "out"
            self.phase_time = 0.0

            return True

        # Solo la barra espaciadora avanza el tutorial
        if event.key != pygame.K_SPACE:
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


        font, lines = self._lines(self.index)

        line_h = font.get_linesize()

        block_h = line_h * len(lines)

        top = frame_pos.top + max(
            self.pad_y,
            (frame_pos.height - block_h) // 2 - 6
        )

        for i, line in enumerate(lines):

            y = top + i * line_h

            shadow = self._text(font, line, SHADOW_COLOR)
            label = self._text(font, line, TEXT_COLOR)

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
                    "Espacio: cerrar"
                    if last
                    else "Espacio: seguir   Enter: saltar"
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