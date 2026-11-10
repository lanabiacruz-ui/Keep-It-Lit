"""Dialogos de los jefes: se presentan con el mismo panel que Cenizo y Escupin.

Usa ui/tutorial.py (Tutorial): el personaje aparece a la derecha y el globo
a su lado, pero cada jefe con SUS colores, SU voz y SU forma de hablar:

  GolemDialog   Golem Colosal (zona 2). Enorme, grave, imponente: verde
                piedra y oscuridad. Cada pagina cae como un golpe de roca
                (temblor, polvo verde y un "tum" grave).
  PinaDialog    Piña Colosal (zona 1). Habla en idioma piña: no se entiende
                nada ("budi bududu badududu"), solo da risa. Voz de chillido
                de goma, rapidita y saltarina.

La primera vez que pelas contra el jefe sale la presentacion completa
(GOLEM_PAGES / PINA_PAGES). Las demas veces, una sola frase al azar
(GOLEM_TAUNTS / PINA_TAUNTS) para no hacerte repetir todo.

Para cambiar los textos: editar las listas de abajo.
Los sonidos de voz se generan con tools/make_boss_voices.py.
"""

import math
import random

import pygame

from core.audio_manager import audio
from ui.tutorial import DEFAULT_THEME, ROOT_DIR, Tutorial


COMBAT_DIR = ROOT_DIR / "assets" / "maps" / "combate"


# ----------------------------------------------------------------- textos

GOLEM_NAME = "Golem Colosal"

# Presentacion completa (la primera vez). En su sala el jugador lleva
# antorcha (no fosforo), asi que el golem habla de la antorcha.
GOLEM_PAGES = [
    "ALTO. Esta tierra es mía.",

    "Soy el GOLEM COLOSAL. Fui montaña antes de ser guardián. Los reinos se "
    "hicieron polvo... y yo sigo en pie.",

    "Cada antorcha que cruzó esa puerta terminó apagada bajo mi puño. "
    "Cada una. Sin excepción.",

    "Venciste a la piña. Qué orgullo tan pequeño. Ella era barro y semilla. "
    "Yo soy la ROCA que sostiene este mundo.",

    "Tu antorcha no es más que una chispa en mi eternidad. "
    "¡ARRODÍLLATE ANTE LA PIEDRA!",
]

# Las demas veces (una al azar)
GOLEM_TAUNTS = [
    "Volviste. La piedra no olvida.",
    "Otra antorcha que se apaga. Otra más para mi colección.",
    "Tu antorcha tiembla. Lo siento desde aquí.",
    "¿Tan pronto quieres apagarte, pequeña llama?",
    "Cada intento tuyo es otro grano de polvo bajo mi pie.",
    "Que tiemble la tierra. ¡Empecemos!",
]


PINA_NAME = "Piña Colosal"

# Idioma piña: no se entiende, es para reirse
PINA_PAGES = [
    "¡Budi bududu badududu budididdudu!",

    "¡Bududu! ¡Bidibidi budubadu... badu badu BUDIDIDU!",

    "Budididdudu bi bu bududu, ¿badu? ¡Badududu bididi!",

    "¡Bu bu bu BUDIBADUDU! ¡Bididdudu budu bududu, bidi, bidi!",

    "¡¡BADUDUDU BUDIDIDDUDU!!",
]

PINA_TAUNTS = [
    "¡Budi budu!",
    "¡Badududu bididi!",
    "¡Bududu budididdudu!",
    "¡Bidibidi badu badu!",
    "¡Budi bududu BADUDU!",
    "¡Bu bu bu bududududu!",
]


# ---------------------------------------------------------------- colores

# Golem: piedra oscura con grietas verdes
GOLEM_THEME = dict(
    DEFAULT_THEME,
    name=GOLEM_NAME,
    text=(206, 246, 222),
    shadow=(6, 22, 14),
    hint=(120, 206, 154),
    name_bg=(24, 96, 58),
    name_edge=(70, 235, 130),
    name_text=(214, 255, 228),
    dot_on=(70, 235, 130),
    dot_on_edge=(10, 60, 34),
    dot_done=(40, 130, 80),
    dot_next=(56, 84, 70),
    arrow=(70, 235, 130),
    spark=(120, 255, 175),
    glow=(40, 220, 110),
    frame_border=(70, 235, 130),
    frame_fill=(18, 28, 24),
    frame_fill_alpha=238,
)

# Piña: marron de piña con verde lima
PINA_THEME = dict(
    DEFAULT_THEME,
    name=PINA_NAME,
    text=(84, 42, 10),
    shadow=(255, 240, 200),
    hint=(130, 84, 28),
    name_bg=(150, 96, 40),
    name_edge=(70, 38, 10),
    name_text=(255, 248, 224),
    dot_on=(150, 220, 60),
    dot_on_edge=(70, 38, 10),
    dot_done=(214, 170, 100),
    dot_next=(180, 150, 110),
    arrow=(110, 190, 40),
    spark=(196, 244, 96),
    glow=(150, 230, 70),
    frame_border=(80, 44, 14),
    frame_fill=(246, 214, 150),
    frame_fill_alpha=218,
)


# ----------------------------------------------------------------- clases

class BossDialog(Tutorial):
    """Base: igual que Tutorial pero con la imagen y la voz de un jefe."""

    PORTRAITS = ()          # imagenes a probar, en orden (carpeta combate)
    PORTRAIT_FRAME = None   # si es una tira: (ancho, alto) del primer cuadro

    # alto del personaje en pantalla, como fraccion del alto de la pantalla
    CHAR_FRACTION = 0.40

    FRAME_WIDTH = 450

    def __init__(self, screen_size, pages=None, **kwargs):

        kwargs.setdefault(
            "char_height", int(screen_size[1] * self.CHAR_FRACTION)
        )
        kwargs.setdefault("frame_width", self.FRAME_WIDTH)

        super().__init__(
            screen_size, pages=pages or self.default_pages(), **kwargs
        )

    @classmethod
    def default_pages(cls):
        return []

    @classmethod
    def for_visit(cls, screen_size, first):
        """Presentacion completa la primera vez; despues, una sola frase."""

        raise NotImplementedError

    def _source_character(self):

        image = None

        for name in self.PORTRAITS:

            try:
                image = pygame.image.load(
                    str(COMBAT_DIR / name)
                ).convert_alpha()
                break
            except (pygame.error, FileNotFoundError):
                continue

        if image is None:
            return super()._source_character()

        if self.PORTRAIT_FRAME is not None:

            w, h = self.PORTRAIT_FRAME

            image = image.subsurface(
                pygame.Rect(0, 0, w, h).clip(image.get_rect())
            ).copy()

        area = image.get_bounding_rect()

        if area.width <= 0 or area.height <= 0:
            return image

        return image.subsurface(area).copy()

    def _scale_character(self, char, char_height):

        char_w = int(char.get_width() * char_height / char.get_height())

        # dibujo grande: se achica suavizado; pixel art: se agranda seco
        if char.get_height() > char_height:
            return pygame.transform.smoothscale(char, (char_w, char_height))

        return pygame.transform.scale(char, (char_w, char_height))


class GolemDialog(BossDialog):
    """El Golem Colosal: enorme, lento y grave."""

    THEME = GOLEM_THEME

    PORTRAITS = ("jefe_golem.png",)

    # ocupa casi media pantalla de alto: se tiene que sentir GIGANTE
    CHAR_FRACTION = 0.58
    FRAME_WIDTH = 470

    # habla despacio, con peso; pausas largas entre frase y frase
    TYPE_SPEED = 24.0
    BLIP_EVERY = 2
    PAUSE_END = 0.62
    PAUSE_COMMA = 0.30
    PAUSE_DOTS = 0.34
    BLIPS = ("golem_a", "golem_b", "golem_c")

    HOP_TIME = 0.55

    @classmethod
    def default_pages(cls):
        return GOLEM_PAGES

    @classmethod
    def for_visit(cls, screen_size, first):

        pages = GOLEM_PAGES if first else [random.choice(GOLEM_TAUNTS)]

        return cls(screen_size, pages=pages)

    def _pop(self):
        """Cada pagina cae como un golpe de roca: tum + polvo verde."""

        super()._pop()

        audio.play("golem_thud")

        cx = self.char_rect.centerx
        base = self.char_rect.bottom - 6

        # polvo de piedra que sale a los costados, a ras del piso
        for _ in range(12):

            side = random.choice((-1, 1))

            self.sparks.append({
                "x": cx + side * random.uniform(30, self.char_rect.width * 0.42),
                "y": base - random.uniform(0, 14),
                "vx": side * random.uniform(30, 120),
                "vy": random.uniform(-70, -20),
                "life": random.uniform(0.5, 1.0),
                "age": 0.0,
                "size": random.randint(3, 6),
            })

    def draw(self, screen):

        super().draw(screen)

        if (
            not self.active
            or self.phase != "show"
            or self._typing_done()
        ):
            return

        # el ojo verde late mientras habla (luz aditiva, sin alpha)
        pulse = 0.5 + 0.5 * math.sin(self.age * 7.0)

        r = int(self.char_rect.width * (0.07 + 0.015 * pulse))

        eye = pygame.Surface((r * 2, r * 2))

        for k in range(r, 0, -2):

            glow = (1.0 - k / r) ** 1.5 * (0.35 + 0.35 * pulse)

            pygame.draw.circle(
                eye,
                (int(70 * glow), int(255 * glow), int(140 * glow)),
                (r, r), k,
            )

        screen.blit(
            eye,
            eye.get_rect(
                center=(
                    self.char_rect.centerx + int(self.char_rect.width * 0.11),
                    self.char_rect.top + int(self.char_rect.height * 0.30),
                )
            ),
            special_flags=pygame.BLEND_RGB_ADD,
        )


class PinaDialog(BossDialog):
    """La Piña Colosal: habla idioma piña. Nadie entiende nada."""

    THEME = PINA_THEME

    PORTRAITS = ("jefe_pina.png",)

    CHAR_FRACTION = 0.42

    # rapidita y con un chillido por casi cada letra
    TYPE_SPEED = 42.0
    BLIP_EVERY = 2
    PAUSE_END = 0.28
    PAUSE_COMMA = 0.10
    PAUSE_DOTS = 0.10
    BLIPS = ("pina_a", "pina_b", "pina_c")

    HOP_TIME = 0.32

    @classmethod
    def default_pages(cls):
        return PINA_PAGES

    @classmethod
    def for_visit(cls, screen_size, first):

        pages = PINA_PAGES if first else [random.choice(PINA_TAUNTS)]

        return cls(screen_size, pages=pages)

    def _pop(self):
        """Saltito de goma: la piña rebota y larga confeti verde lima."""

        super()._pop()

        audio.play("pina_boing")

        cx = self.char_rect.centerx
        top = self.char_rect.top + 30

        for _ in range(10):

            self.sparks.append({
                "x": cx + random.uniform(-40, 40),
                "y": top + random.uniform(-10, 30),
                "vx": random.uniform(-110, 110),
                "vy": random.uniform(-150, -60),
                "life": random.uniform(0.5, 1.0),
                "age": 0.0,
                "size": random.randint(3, 5),
            })

    def draw(self, screen):

        # la piña se achata y se estira mientras habla (como goma)
        if self.active and self.phase == "show" and not self._typing_done():

            squash = math.sin(self.age * 18.0) * 0.045

            base = self.character

            w = int(base.get_width() * (1.0 + squash))
            h = int(base.get_height() * (1.0 - squash))

            stretched = pygame.transform.scale(base, (w, h))

            rect = stretched.get_rect(
                midbottom=(self.char_rect.centerx, self.char_rect.bottom)
            )

            saved, saved_rect = self.character, self.char_rect

            self.character = stretched
            self.char_rect = rect

            try:
                super().draw(screen)
            finally:
                self.character = saved
                self.char_rect = saved_rect

            return

        super().draw(screen)