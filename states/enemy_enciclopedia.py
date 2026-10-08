import json
from pathlib import Path

import pygame


DATA_PATH = (
    Path(_file_).resolve().parent.parent
    / "data"
    / "enemies.json"
)

COMBAT_DIR = (
    Path(_file_).resolve().parent.parent
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
    Enciclopedia de enemigos.

    IMPORTANTE:
    Las descripciones son SOLO DE LECTURA.
    El jugador no puede modificarlas.
    """

    ORDER = (
        "pino",
        "tronco",
        "mosquito",
        "hongun",
    )

    def _init_(self, screen):

        self.screen = screen

        self.width, self.height = screen.get_size()

        self.data = self._load_data()

        self.selected = 0

        self.images = {}

        self.title_font = pygame.font.Font(
            None,
            62
        )

        self.name_font = pygame.font.Font(
            None,
            48
        )

        self.body_font = pygame.font.Font(
            None,
            30
        )

        self.small_font = pygame.font.Font(
            None,
            24
        )

        self.resize()

        self._load_all_images()

    # ---------------------------------------------------------
    # Cargar información de los enemigos
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
    # Cargar imágenes
    # ---------------------------------------------------------

    def _load_all_images(self):

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

    # ---------------------------------------------------------
    # Tamaños de pantalla
    # ---------------------------------------------------------

    def resize(self):

        self.width, self.height = (
            self.screen.get_size()
        )

        self.background = pygame.Surface(
            (
                self.width,
                self.height
            ),
            pygame.SRCALPHA
        )

        self.background.fill(
            (8, 14, 22, 245)
        )

        margin = max(
            24,
            int(self.width * 0.04)
        )

        self.panel = pygame.Rect(
            margin,
            margin,
            self.width - margin * 2,
            self.height - margin * 2,
        )

        self.left_panel = pygame.Rect(
            self.panel.left + 24,
            self.panel.top + 95,
            max(
                230,
                int(self.panel.width * 0.30)
            ),
            self.panel.height - 175,
        )

        self.right_panel = pygame.Rect(
            self.left_panel.right + 24,
            self.left_panel.top,
            self.panel.right
            - self.left_panel.right
            - 48,
            self.left_panel.height,
        )

        self.back_rect = pygame.Rect(
            self.panel.left + 24,
            self.panel.bottom - 70,
            170,
            46,
        )

    # ---------------------------------------------------------
    # Rectángulo de cada enemigo
    # ---------------------------------------------------------

    def _enemy_rect(self, index):

        gap = 8
        row_h = 56

        return pygame.Rect(
            self.left_panel.left + 8,
            self.left_panel.top
            + 8
            + index * (row_h + gap),
            self.left_panel.width - 16,
            row_h,
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

        # ESC vuelve al menú de pausa
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

            # ENTER NO EDITA NADA.
            elif event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER
            ):

                pass

        # Mouse
        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                # Botón regresar
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

    def draw(self):

        self.screen.blit(
            self.background,
            (0, 0)
        )

        # Panel principal
        pygame.draw.rect(
            self.screen,
            (35, 70, 92),
            self.panel,
            border_radius=18,
        )

        pygame.draw.rect(
            self.screen,
            (100, 185, 220),
            self.panel,
            width=3,
            border_radius=18,
        )

        # Título
        title = self.title_font.render(
            "ENCICLOPEDIA DE ENEMIGOS",
            True,
            (240, 250, 255),
        )

        self.screen.blit(
            title,
            title.get_rect(
                midtop=(
                    self.panel.centerx,
                    self.panel.top + 20
                )
            ),
        )

        # Panel izquierdo
        pygame.draw.rect(
            self.screen,
            (20, 36, 52),
            self.left_panel,
            border_radius=12,
        )

        pygame.draw.rect(
            self.screen,
            (82, 125, 150),
            self.left_panel,
            width=2,
            border_radius=12,
        )

        # Lista de enemigos
        for index, key in enumerate(
            self.ORDER
        ):

            rect = self._enemy_rect(
                index
            )

            selected = (
                index == self.selected
            )

            fill = (
                (77, 170, 191)
                if selected
                else (49, 91, 112)
            )

            pygame.draw.rect(
                self.screen,
                fill,
                rect,
                border_radius=9,
            )

            text = self.name_font.render(
                self.data[key]["nombre"],
                True,
                (
                    (10, 22, 28)
                    if selected
                    else (235, 245, 250)
                ),
            )

            self.screen.blit(
                text,
                text.get_rect(
                    midleft=(
                        rect.left + 16,
                        rect.centery
                    )
                ),
            )

        # Enemigo seleccionado
        key = self.ORDER[
            self.selected
        ]

        enemy = self.data[key]

        # Panel derecho
        pygame.draw.rect(
            self.screen,
            (20, 36, 52),
            self.right_panel,
            border_radius=12,
        )

        pygame.draw.rect(
            self.screen,
            (82, 125, 150),
            self.right_panel,
            width=2,
            border_radius=12,
        )

        # Nombre
        name = self.name_font.render(
            enemy["nombre"],
            True,
            (240, 250, 255)
        )

        self.screen.blit(
            name,
            name.get_rect(
                centerx=self.right_panel.centerx,
                top=self.right_panel.top + 18
            )
        )

        # Imagen
        image = self.images.get(
            key
        )

        image_area = pygame.Rect(
            self.right_panel.left + 20,
            self.right_panel.top + 85,
            self.right_panel.width - 40,
            150,
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

        # Título de descripción
        desc_title = self.body_font.render(
            "Descripcion",
            True,
            (110, 220, 235),
        )

        self.screen.blit(
            desc_title,
            (
                self.right_panel.left + 24,
                self.right_panel.top + 250
            )
        )

        # Descripción SOLO LECTURA
        lines = self._wrap(
            self.body_font,
            str(
                enemy.get(
                    "descripcion",
                    ""
                )
            ),
            self.right_panel.width - 48,
        )

        y = (
            self.right_panel.top
            + 290
        )

        for line in lines:

            text = self.body_font.render(
                line,
                True,
                (235, 242, 246)
            )

            self.screen.blit(
                text,
                (
                    self.right_panel.left + 24,
                    y
                )
            )

            y += (
                text.get_height()
                + 5
            )

        # Controles
        controls = self.small_font.render(
            "Flechas / W-S: seleccionar   ESC: volver",
            True,
            (195, 215, 225),
        )

        self.screen.blit(
            controls,
            controls.get_rect(
                bottomright=(
                    self.panel.right - 24,
                    self.panel.bottom - 16
                )
            ),
        )

        # Botón regresar
        pygame.draw.rect(
            self.screen,
            (49, 91, 112),
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