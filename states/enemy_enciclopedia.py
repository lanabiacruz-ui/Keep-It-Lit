import json
from pathlib import Path

import pygame


DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "enemies.json"
)

UI_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "ui"
)

COMBAT_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "combate"
)


DEFAULT_DATA = {
    "pino": {
        "nombre": "Piña",
        "imagen": "enemigo.png",
        "descripcion": (
            "Enemigo de contacto que se mueve por la sala y rebota "
            "contra los obstaculos. Hace daño cuando choca con el jugador."
        ),
    },

    "tronco": {
        "nombre": "Tronco",
        "imagen": "tronco.png",
        "descripcion": (
            "Mantiene distancia del jugador y dispara tres proyectiles "
            "que rebotan por la sala."
        ),
    },

    "mosquito": {
        "nombre": "Mosquito",
        "imagen": "mosquito.png",
        "descripcion": (
            "Persigue al jugador y puede acercarse para atacar. "
            "Su aviso indica cuando esta por realizar una accion peligrosa."
        ),
    },

    "hongun": {
        "nombre": "Hongun",
        "imagen": "hongun.png",
        "descripcion": (
            "Camina por la sala y persigue al jugador cuando lo detecta. "
            "Puede cargar y liberar una explosion."
        ),
    },
}


class EnemyEncyclopedia:
    """
    Enciclopedia de enemigos (se ve en la tablet).

    IMPORTANTE:
    Las descripciones son SOLO DE LECTURA.
    El jugador no puede modificarlas.

    Imagenes (en assets/maps/ui/). Si alguna falta, se dibuja con
    colores como antes:
        tablet_enemigos.png      1672x941  fondo completo
        fila_enemigo.png         520x112   fila de la lista
        fila_enemigo_sel.png     520x112   fila seleccionada
        btn_regresar.png         340x92    boton REGRESAR
        btn_regresar_hover.png   340x92    boton REGRESAR resaltado
    """

    ORDER = (
        "pino",
        "tronco",
        "mosquito",
        "hongun",
    )

    # ---------- distribucion (en coordenadas de la imagen 1672x941) ----

    IMG_W = 1672
    IMG_H = 941

    # Pantalla de la tablet
    SCREEN_BOX = (436, 170, 800, 500)

    # Lista de enemigos (izquierda)
    ROW_X = 456
    ROW_Y = 260
    ROW_W = 260
    ROW_H = 56
    ROW_GAP = 8

    # Ficha del enemigo (derecha)
    CARD_BOX = (736, 260, 480, 390)

    # Boton REGRESAR (abajo a la izquierda)
    BACK_BOX = (456, 590, 170, 46)

    TEXT_COLOR = (235, 245, 250)
    TEXT_DARK = (10, 22, 28)
    TITLE_COLOR = (110, 220, 235)

    def __init__(self, screen):

        self.screen = screen

        self.data = self._load_data()

        self.selected = 0

        self.images = {}

        self.resize()

        self._load_all_images()

    # ---------------------------------------------------------
    # Cargar informacion de los enemigos
    # ---------------------------------------------------------

    def _load_data(self):

        data = None

        try:

            with open(
                DATA_PATH,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except (
            OSError,
            json.JSONDecodeError,
            UnicodeDecodeError
        ):

            data = None

        if not isinstance(data, dict):

            data = DEFAULT_DATA

        merged = {}

        for key in self.ORDER:

            base = dict(
                DEFAULT_DATA[key]
            )

            if isinstance(
                data.get(key),
                dict
            ):

                base.update(
                    data[key]
                )

            merged[key] = base

        return merged

    # ---------------------------------------------------------
    # Cargar imagenes
    # ---------------------------------------------------------

    def _load_all_images(self):

        # Dibujos de los enemigos
        for key in self.ORDER:

            filename = self.data[key].get(
                "imagen",
                ""
            )

            path = COMBAT_DIR / filename

            try:

                image = pygame.image.load(
                    path
                ).convert_alpha()

            except (
                OSError,
                pygame.error
            ):

                image = None

            self.images[key] = image

    @staticmethod
    def _load_ui(name, size=None, alpha=True):
        """Carga una imagen de assets/maps/ui. None si no existe."""

        path = UI_DIR / name

        try:

            image = pygame.image.load(path)

            image = (
                image.convert_alpha()
                if alpha
                else image.convert()
            )

        except (OSError, pygame.error):

            return None

        if size is not None and image.get_size() != size:

            image = pygame.transform.smoothscale(
                image,
                size
            )

        return image

    # ---------------------------------------------------------
    # Tamanos de pantalla
    # ---------------------------------------------------------

    def _box(self, box):
        """(x, y, ancho, alto) de la imagen 1672x941 -> Rect en pantalla."""

        x, y, w, h = box

        return pygame.Rect(
            round(x * self.sx),
            round(y * self.sy),
            max(1, round(w * self.sx)),
            max(1, round(h * self.sy)),
        )

    def resize(self):

        self.width, self.height = (
            self.screen.get_size()
        )

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        self.title_font = pygame.font.Font(
            None,
            max(30, round(62 * self.sy))
        )

        self.name_font = pygame.font.Font(
            None,
            max(24, round(48 * self.sy))
        )

        self.body_font = pygame.font.Font(
            None,
            max(18, round(32 * self.sy))
        )

        self.small_font = pygame.font.Font(
            None,
            max(14, round(24 * self.sy))
        )

        self.screen_rect = self._box(self.SCREEN_BOX)
        self.card_rect = self._box(self.CARD_BOX)
        self.back_rect = self._box(self.BACK_BOX)

        # Lista (todo el recuadro, por si se dibuja con colores)
        rows_h = (
            len(self.ORDER) * (self.ROW_H + self.ROW_GAP)
            + self.ROW_GAP
        )

        self.list_rect = self._box(
            (
                self.ROW_X - self.ROW_GAP,
                self.ROW_Y - self.ROW_GAP,
                self.ROW_W + self.ROW_GAP * 2,
                rows_h,
            )
        )

        back_size = self.back_rect.size

        # Imagenes (escaladas al tamano de la pantalla actual)
        self.bg_img = self._load_ui(
            "tablet_enemigos.png",
            (self.width, self.height),
            alpha=False
        )

        self.row_img = self._load_ui(
            "fila_enemigo.png",
            self._enemy_rect(0).size
        )

        self.row_sel_img = self._load_ui(
            "fila_enemigo_sel.png",
            self._enemy_rect(0).size
        )

        self.back_img = self._load_ui(
            "btn_regresar.png",
            back_size
        )

        self.back_hover_img = self._load_ui(
            "btn_regresar_hover.png",
            back_size
        )

        # Fondo oscuro para cuando no hay imagen de la tablet
        self.dim = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )

        self.dim.fill((8, 14, 22, 245))

    # ---------------------------------------------------------
    # Rectangulo de cada enemigo
    # ---------------------------------------------------------

    def _enemy_rect(self, index):

        return self._box(
            (
                self.ROW_X,
                self.ROW_Y + index * (self.ROW_H + self.ROW_GAP),
                self.ROW_W,
                self.ROW_H,
            )
        )

    # ---------------------------------------------------------
    # Dividir texto
    # ---------------------------------------------------------

    @staticmethod
    def _wrap(font, text, max_width):

        lines = []

        current = ""

        for word in text.split():

            test = (
                f"{current} {word}"
            ).strip()

            if (
                current
                and font.size(test)[0]
                > max_width
            ):

                lines.append(
                    current
                )

                current = word

            else:

                current = test

        if current:

            lines.append(
                current
            )

        return lines

    # ---------------------------------------------------------
    # Eventos
    # ---------------------------------------------------------

    def handle_event(self, event):

        # ESC vuelve al menu de pausa
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                return "back"

            # Subir
            if event.key in (
                pygame.K_UP,
                pygame.K_w
            ):

                self.selected = (
                    self.selected - 1
                ) % len(self.ORDER)

            # Bajar
            elif event.key in (
                pygame.K_DOWN,
                pygame.K_s
            ):

                self.selected = (
                    self.selected + 1
                ) % len(self.ORDER)

        # Mouse
        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                # Boton regresar
                if self.back_rect.collidepoint(
                    event.pos
                ):
                    return "back"

                # Seleccionar enemigo
                for index in range(
                    len(self.ORDER)
                ):

                    if self._enemy_rect(
                        index
                    ).collidepoint(
                        event.pos
                    ):

                        self.selected = index
                        break

        return None

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update(self, dt):

        return None

    # ---------------------------------------------------------
    # Dibujar
    # ---------------------------------------------------------

    def _draw_fallback_frames(self):
        """Sin la imagen de la tablet: paneles de colores."""

        self.screen.blit(
            self.dim,
            (0, 0)
        )

        pygame.draw.rect(
            self.screen,
            (35, 70, 92),
            self.screen_rect,
            border_radius=18,
        )

        pygame.draw.rect(
            self.screen,
            (100, 185, 220),
            self.screen_rect,
            width=3,
            border_radius=18,
        )

        title = self.title_font.render(
            "ENEMIGOS",
            True,
            (240, 250, 255),
        )

        self.screen.blit(
            title,
            title.get_rect(
                midtop=(
                    self.screen_rect.centerx,
                    self.screen_rect.top + round(12 * self.sy)
                )
            ),
        )

        for rect in (self.list_rect, self.card_rect):

            pygame.draw.rect(
                self.screen,
                (20, 36, 52),
                rect,
                border_radius=12,
            )

            pygame.draw.rect(
                self.screen,
                (82, 125, 150),
                rect,
                width=2,
                border_radius=12,
            )

    def draw(self):

        # ---------- fondo ----------

        if self.bg_img is not None:

            self.screen.blit(
                self.bg_img,
                (0, 0)
            )

        else:

            self._draw_fallback_frames()

        # ---------- lista ----------

        for index, key in enumerate(
            self.ORDER
        ):

            rect = self._enemy_rect(
                index
            )

            selected = (
                index == self.selected
            )

            row = (
                self.row_sel_img
                if selected
                else self.row_img
            )

            if row is not None:

                self.screen.blit(
                    row,
                    rect
                )

            else:

                pygame.draw.rect(
                    self.screen,
                    (77, 170, 191)
                    if selected
                    else (49, 91, 112),
                    rect,
                    border_radius=9,
                )

            # Sin imagen de fila, el seleccionado es claro: texto oscuro
            dark = selected and self.row_sel_img is None

            text = self.name_font.render(
                self.data[key]["nombre"],
                True,
                self.TEXT_DARK if dark else self.TEXT_COLOR,
            )

            self.screen.blit(
                text,
                text.get_rect(
                    midleft=(
                        rect.left + round(16 * self.sx),
                        rect.centery
                    )
                ),
            )

        # ---------- ficha del enemigo ----------

        key = self.ORDER[
            self.selected
        ]

        enemy = self.data[key]

        card = self.card_rect

        pad = round(20 * self.sx)

        # Nombre
        name = self.name_font.render(
            enemy["nombre"],
            True,
            self.TEXT_COLOR
        )

        self.screen.blit(
            name,
            name.get_rect(
                centerx=card.centerx,
                top=card.top + round(10 * self.sy)
            )
        )

        # Dibujo del enemigo
        image = self.images.get(
            key
        )

        image_area = pygame.Rect(
            card.left + pad,
            card.top + round(58 * self.sy),
            card.width - pad * 2,
            round(150 * self.sy),
        )

        if image is not None:

            scale = min(
                image_area.width
                / image.get_width(),
                image_area.height
                / image.get_height(),
                2.8,
            )

            size = (
                max(
                    1,
                    round(
                        image.get_width()
                        * scale
                    )
                ),
                max(
                    1,
                    round(
                        image.get_height()
                        * scale
                    )
                ),
            )

            sprite = pygame.transform.scale(
                image,
                size
            )

            self.screen.blit(
                sprite,
                sprite.get_rect(
                    center=image_area.center
                )
            )

        # Titulo de descripcion
        desc_title = self.body_font.render(
            "Descripcion",
            True,
            self.TITLE_COLOR,
        )

        self.screen.blit(
            desc_title,
            (
                card.left + pad,
                card.top + round(222 * self.sy)
            )
        )

        # Descripcion SOLO LECTURA
        lines = self._wrap(
            self.body_font,
            str(
                enemy.get(
                    "descripcion",
                    ""
                )
            ),
            card.width - pad * 2,
        )

        y = card.top + round(256 * self.sy)

        for line in lines:

            if y > card.bottom - round(20 * self.sy):
                break

            text = self.body_font.render(
                line,
                True,
                self.TEXT_COLOR
            )

            self.screen.blit(
                text,
                (
                    card.left + pad,
                    y
                )
            )

            y += (
                text.get_height()
                + 4
            )

        # ---------- controles ----------

        hint_x = self._enemy_rect(0).left

        hint_y = (
            self._enemy_rect(len(self.ORDER) - 1).bottom
            + round(14 * self.sy)
        )

        for line in self._wrap(
            self.small_font,
            "Flechas / W-S: elegir   ESC: volver",
            self._enemy_rect(0).width,
        ):

            hint = self.small_font.render(
                line,
                True,
                (195, 215, 225),
            )

            self.screen.blit(
                hint,
                (hint_x, hint_y)
            )

            hint_y += hint.get_height() + 2

        # ---------- boton regresar ----------

        hover = self.back_rect.collidepoint(
            pygame.mouse.get_pos()
        )

        button = (
            self.back_hover_img
            if hover and self.back_hover_img is not None
            else self.back_img
        )

        if button is not None:

            self.screen.blit(
                button,
                self.back_rect
            )

        else:

            pygame.draw.rect(
                self.screen,
                (77, 170, 191) if hover else (49, 91, 112),
                self.back_rect,
                border_radius=9,
            )

            back_text = self.body_font.render(
                "REGRESAR",
                True,
                (240, 250, 255)
            )

            self.screen.blit(
                back_text,
                back_text.get_rect(
                    center=self.back_rect.center
                )
            )