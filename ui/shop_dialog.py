"""Dialogo del vendedor rojo, la primera vez que le hablas.

Usa el mismo panel que Cenizo (ui/tutorial.py): el personaje aparece a la
derecha y el globo a su lado, pero todo en rojo: panel, etiqueta con el
nombre, chispas y halo. Habla en español neutro, con una voz grave y bamboleante (tonto_a/b/c,
ver tools/make_sounds.py) y un poco mas lento que el fantasma.

Para cambiarle el nombre o los textos: SHOPKEEPER_NAME y SHOPKEEPER_PAGES.
"""

import pygame

from ui.tutorial import DEFAULT_THEME, ROOT_DIR, Tutorial


SHOPKEEPER_NAME = "Escupín"

# Retrato que se ve en el dialogo. Si falta, se usa el recorte del vendedor
# animado de la tienda (world/shop.py).
PORTRAIT_IMAGE = ROOT_DIR / "assets" / "maps" / "tienda" / "escupin.png"
BODY_IMAGE = ROOT_DIR / "assets" / "maps" / "tienda" / "vendedor_cuerpo.png"

# Mostrador de adelante. Si falta, se dibuja uno simple con rectangulos.
COUNTER_IMAGE = ROOT_DIR / "assets" / "maps" / "tienda" / "mostrador.png"


# Muy poco lore: lo justo para dejar la intriga. Lo ultimo avisa que siempre
# va a estar vendiendo.
SHOPKEEPER_PAGES = [
    "¡Ehhh! ¡Un cliente! Jiji. Yo soy Escupín... creo. Sí, Escupín. "
    "Me puso así... eh... alguien. ¡Qué lindo nombre!",

    "Yo antes no era nada, ¿ves? Y un día vino el Oscuro, me sopló y... "
    "¡pum! Estaba vivo. ¡A todo el bosque también! Qué amable, ¿no?",

    "Después me olvidé qué más pasó, jeje. Me duele la cabeza si pienso. "
    "¡Así que dejémoslo ahí!",

    "Yo te vendo cosas. ¡Siempre! Ven cuando quieras con tus monedas y yo "
    "te las escupo al piso. ¡Eso sí sé hacer!",
]


# Si lo visitas con una skin roja, se sorprende (una sola vez).
SHOPKEEPER_RED_PAGES = [
    "¡¡EHHH!! ¡Espera, espera! ¡Estás rojo! ¡ROJO! ¡Como yo! Jiji... "
    "¡Nunca vi a otro rojo por acá!",

    "¿Te sopló el Oscuro a ti también? No, ¿no? Bueno, jeje. "
    "¡Igual los rojos nos entendemos!",
]


# Reacciones de una sola vez (maximo una por visita). Ver
# NewGame._shop_reaction para cuando se dispara cada una.
SHOPKEEPER_REACTIONS = {
    "elegante": [
        "¿Y ese traje? ¡Qué elegante! ¿Vas a una fiesta? Yo no fui "
        "invitado... jeje. ¡Pero me gusta!",
    ],
    "rico": [
        "¡¡¡Cuántas monedas!!! Jiji. ¿Me regalas una? No, no, es broma. "
        "¡Mejor gástalas aquí!",
    ],
    "sin_monedas": [
        "¿No traes monedas? ¿Vienes a mirar nomás? ¡Yo también miro "
        "cosas! Jeje. Mira todo lo que quieras.",
    ],
    "gemas": [
        "¡Qué brillo! ¿Eso son gemas? ¡Qué lindas! No me las des, ¿eh? "
        "Solo quería decirlo. Jiji.",
    ],
    "visitas": [
        "¿Otra vez tú? Jeje, ya te conozco. ¡Eres mi mejor cliente! "
        "Bueno... el único. ¡Pero el mejor!",
    ],
}


# colores del vendedor: marron rojizo, como su piel en el mapa
SHOPKEEPER_THEME = dict(
    DEFAULT_THEME,
    name=SHOPKEEPER_NAME,
    text=(92, 24, 30),
    shadow=(252, 228, 222),
    hint=(150, 52, 58),
    name_bg=(168, 58, 62),
    name_edge=(84, 22, 28),
    name_text=(255, 238, 232),
    dot_on=(196, 72, 72),
    dot_on_edge=(92, 24, 30),
    dot_done=(226, 150, 146),
    dot_next=(190, 130, 126),
    arrow=(190, 66, 66),
    spark=(255, 176, 150),
    glow=(220, 80, 70),
    frame_border=(96, 28, 34),
    frame_fill=(244, 196, 186),
    frame_fill_alpha=215,
)


class ShopkeeperDialog(Tutorial):
    """Igual que Tutorial, pero con el vendedor en vez de Cenizo."""

    THEME = SHOPKEEPER_THEME

    # un poco mas lento y con una voz cada 3 letras
    TYPE_SPEED = 32.0
    BLIP_EVERY = 3
    PAUSE_END = 0.16
    PAUSE_COMMA = 0.07
    PAUSE_DOTS = 0.16
    BLIPS = ("tonto_a", "tonto_b", "tonto_c")

    def __init__(self, screen_size, pages=None, **kwargs):

        kwargs.setdefault("char_height", 190)

        super().__init__(
            screen_size,
            pages=pages or SHOPKEEPER_PAGES,
            **kwargs
        )

        self._place_behind_counter()

    COUNTER_H = 30

    COUNTER_EDGE = (44, 24, 14)
    COUNTER_WOOD = (120, 76, 44)
    COUNTER_TOP = (174, 116, 68)
    COUNTER_DARK = (86, 52, 30)

    def _place_behind_counter(self):
        """Escupin atiende detras de un mostrador pegado al borde de abajo
        de la pantalla: el corte de la imagen queda tapado y no flota."""

        dy = (self.height + 6) - self.char_rect.bottom

        self.char_rect.move_ip(0, dy)
        self.frame_rect.move_ip(0, dy)

        self.group_rect = self.char_rect.union(self.frame_rect)

        w = self.char_rect.width + 80

        self.counter_img = self._load_counter(w)

        if self.counter_img is not None:

            self.counter_rect = self.counter_img.get_rect()

            self.counter_rect.top = self.height - self.COUNTER_H

        else:

            self.counter_rect = pygame.Rect(
                0, self.height - self.COUNTER_H, w, self.COUNTER_H + 12
            )

        self.counter_rect.centerx = self.char_rect.centerx

        # las chispas de la primera pagina nacieron en la posicion vieja
        self.sparks.clear()
        self._pop()

    @staticmethod
    def _load_counter(width):
        """Carga mostrador.png y lo ajusta al ancho pedido (None si falta)."""

        try:
            image = pygame.image.load(str(COUNTER_IMAGE)).convert_alpha()
        except (pygame.error, FileNotFoundError):
            return None

        height = max(1, int(image.get_height() * width / image.get_width()))

        # imagen grande: se achica suavizada; pixel art: se agranda seca
        if image.get_width() > width:
            return pygame.transform.smoothscale(image, (width, height))

        return pygame.transform.scale(image, (width, height))

    def _draw_front(self, screen, dx):

        r = self.counter_rect.move(dx, 0)

        if self.counter_img is not None:

            screen.blit(self.counter_img, r)

            return

        pygame.draw.rect(screen, self.COUNTER_EDGE, r, border_radius=5)

        body = r.inflate(-6, -6)
        body.top = r.top + 3

        pygame.draw.rect(screen, self.COUNTER_WOOD, body, border_radius=4)

        # tapa clara arriba y tablones verticales
        top = pygame.Rect(body.left, body.top, body.width, 9)

        pygame.draw.rect(screen, self.COUNTER_TOP, top, border_radius=4)
        pygame.draw.line(
            screen, self.COUNTER_DARK,
            (body.left, top.bottom), (body.right - 1, top.bottom), 2
        )

        x = body.left + 44

        while x < body.right - 8:

            pygame.draw.line(
                screen, self.COUNTER_DARK,
                (x, top.bottom + 3), (x, body.bottom - 2), 2
            )

            x += 44

    def _source_character(self):

        image = None

        for path in (PORTRAIT_IMAGE, BODY_IMAGE):

            try:
                image = pygame.image.load(str(path)).convert_alpha()
                break
            except (pygame.error, FileNotFoundError):
                continue

        if image is None:
            return super()._source_character()

        area = image.get_bounding_rect()

        if area.width <= 0 or area.height <= 0:
            return image

        return image.subsurface(area).copy()

    def _scale_character(self, char, char_height):

        char_w = int(char.get_width() * char_height / char.get_height())

        # una imagen grande (dibujo en alta calidad) se achica suavizado;
        # una chiquita (pixel art) se agranda sin suavizar para no borronear
        if char.get_height() > char_height:
            return pygame.transform.smoothscale(char, (char_w, char_height))

        return pygame.transform.scale(char, (char_w, char_height))