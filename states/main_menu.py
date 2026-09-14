import pygame
from pathlib import Path


class MainMenu:

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()


        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "ui"
            / "menu.png"
        )

        self.background = pygame.image.load(image_path).convert()

        self.background = pygame.transform.scale(
            self.background,
            (self.width, self.height)
        )

        # ==========================
        # OPCIONES
        # ==========================

        self.options = [
            ("Nueva partida", "new_game"),
            ("Continuar partida", "continue"),
            ("Configuraciones", "settings"),
            ("Logros", "achievements"),
            ("Salir", "quit")
        ]

        self.selected = 0

        # ==========================
        # POSICION DEL MENU
        # ==========================

        self.menu_x = int(self.width * 0.315)
        self.menu_y = int(self.height * 0.405)

        self.option_height = int(self.height * 0.067)

        # ==========================
        # FUENTES
        # ==========================

        self.font = pygame.font.Font(
            None,
            42
        )

        self.small_font = pygame.font.Font(
            None,
            24
        )

    # ==================================================
    # RECTANGULO DE CADA OPCION
    # ==================================================

    def get_option_rect(self, index):

        y = (
            self.menu_y
            + index * self.option_height
        )

        return pygame.Rect(
            self.menu_x - 18,
            y - 5,
            int(self.width * 0.285),
            self.option_height - 4
        )

    # ==================================================
    # DIBUJAR MENU
    # ==================================================

    def draw(self):

        # Dibujar imagen de fondo
        self.screen.blit(
            self.background,
            (0, 0)
        )

        # ==================================================
        # TAPAR EL MENU QUE YA ESTA DIBUJADO EN LA IMAGEN
        # ==================================================

        cover = pygame.Rect(
            int(self.width * 0.275),
            int(self.height * 0.365),
            int(self.width * 0.30),
            int(self.height * 0.30)
        )

        surface = pygame.Surface(
            cover.size,
            pygame.SRCALPHA
        )

        surface.fill(
            (0, 45, 120, 190)
        )

        self.screen.blit(
            surface,
            cover.topleft
        )

        # ==================================================
        # DIBUJAR OPCIONES
        # ==================================================

        for i in range(len(self.options)):

            self.draw_option(i)

        # ==================================================
        # CONTROLES
        # ==================================================

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

    # ==================================================
    # DIBUJAR UNA OPCION
    # ==================================================

    def draw_option(self, index):

        text, action = self.options[index]

        rect = self.get_option_rect(index)

        # ¿Está seleccionada?
        selected = (
            index == self.selected
        )

        # ==================================================
        # OPCION SELECCIONADA
        # ==================================================

        if selected:

            pygame.draw.rect(
                self.screen,
                (24, 125, 205),
                rect,
                border_radius=3
            )

            pygame.draw.rect(
                self.screen,
                (240, 248, 255),
                rect,
                width=2,
                border_radius=3
            )

            # Flecha
            arrow = self.font.render(
                "▶",
                True,
                (255, 255, 255)
            )

            arrow_rect = arrow.get_rect(
                midleft=(
                    rect.left + 10,
                    rect.centery
                )
            )

            self.screen.blit(
                arrow,
                arrow_rect
            )

        # ==================================================
        # TEXTO
        # ==================================================

        label = self.font.render(
            text,
            True,
            (255, 255, 255)
        )

        label_rect = label.get_rect(
            midleft=(
                rect.left + 40,
                rect.centery
            )
        )

        self.screen.blit(
            label,
            label_rect
        )

    # ==================================================
    # EVENTOS
    # ==================================================

    def handle_event(self, event):

        # ==========================
        # TECLADO
        # ==========================

        if event.type == pygame.KEYDOWN:

            # Arriba
            if event.key in (
                pygame.K_UP,
                pygame.K_w
            ):

                self.selected = (
                    self.selected - 1
                ) % len(self.options)

            # Abajo
            elif event.key in (
                pygame.K_DOWN,
                pygame.K_s
            ):

                self.selected = (
                    self.selected + 1
                ) % len(self.options)

            # Seleccionar
            elif event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE
            ):

                return self.options[
                    self.selected
                ][1]

            # Salir
            elif event.key == pygame.K_ESCAPE:

                return "quit"

        # ==========================
        # MOUSE
        # ==========================

        elif event.type == pygame.MOUSEMOTION:

            for i in range(
                len(self.options)
            ):

                rect = self.get_option_rect(i)

                if rect.collidepoint(
                    event.pos
                ):

                    self.selected = i

        # ==========================
        # CLICK
        # ==========================

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                for i, option in enumerate(
                    self.options
                ):

                    rect = self.get_option_rect(i)

                    if rect.collidepoint(
                        event.pos
                    ):

                        self.selected = i

                        return option[1]

        return Noneimport pygame
from pathlib import Path


class MainMenu:

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()

        # ==========================
        # IMAGEN DEL MENU
        # ==========================

        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "ui"
            / "menu.png"
        )

        self.background = pygame.image.load(image_path).convert()

        self.background = pygame.transform.scale(
            self.background,
            (self.width, self.height)
        )

        # ==========================
        # OPCIONES
        # ==========================

        self.options = [
            ("Nueva partida", "new_game"),
            ("Continuar partida", "continue"),
            ("Configuraciones", "settings"),
            ("Logros", "achievements"),
            ("Salir", "quit")
        ]

        self.selected = 0

        # ==========================
        # POSICION DEL MENU
        # ==========================

        self.menu_x = int(self.width * 0.315)
        self.menu_y = int(self.height * 0.405)

        self.option_height = int(self.height * 0.067)

        # ==========================
        # FUENTES
        # ==========================

        self.font = pygame.font.Font(
            None,
            42
        )

        self.small_font = pygame.font.Font(
            None,
            24
        )

    # ==================================================
    # RECTANGULO DE CADA OPCION
    # ==================================================

    def get_option_rect(self, index):

        y = (
            self.menu_y
            + index * self.option_height
        )

        return pygame.Rect(
            self.menu_x - 18,
            y - 5,
            int(self.width * 0.285),
            self.option_height - 4
        )

    # ==================================================
    # DIBUJAR MENU
    # ==================================================

    def draw(self):

        # Dibujar imagen de fondo
        self.screen.blit(
            self.background,
            (0, 0)
        )

        # ==================================================
        # TAPAR EL MENU QUE YA ESTA DIBUJADO EN LA IMAGEN
        # ==================================================

        cover = pygame.Rect(
            int(self.width * 0.275),
            int(self.height * 0.365),
            int(self.width * 0.30),
            int(self.height * 0.30)
        )

        surface = pygame.Surface(
            cover.size,
            pygame.SRCALPHA
        )

        surface.fill(
            (0, 45, 120, 190)
        )

        self.screen.blit(
            surface,
            cover.topleft
        )

        # ==================================================
        # DIBUJAR OPCIONES
        # ==================================================

        for i in range(len(self.options)):

            self.draw_option(i)

        # ==================================================
        # CONTROLES
        # ==================================================

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

    # ==================================================
    # DIBUJAR UNA OPCION
    # ==================================================

    def draw_option(self, index):

        text, action = self.options[index]

        rect = self.get_option_rect(index)

        # ¿Está seleccionada?
        selected = (
            index == self.selected
        )

        # ==================================================
        # OPCION SELECCIONADA
        # ==================================================

        if selected:

            pygame.draw.rect(
                self.screen,
                (24, 125, 205),
                rect,
                border_radius=3
            )

            pygame.draw.rect(
                self.screen,
                (240, 248, 255),
                rect,
                width=2,
                border_radius=3
            )

            # Flecha
            arrow = self.font.render(
                "▶",
                True,
                (255, 255, 255)
            )

            arrow_rect = arrow.get_rect(
                midleft=(
                    rect.left + 10,
                    rect.centery
                )
            )

            self.screen.blit(
                arrow,
                arrow_rect
            )

        # ==================================================
        # TEXTO
        # ==================================================

        label = self.font.render(
            text,
            True,
            (255, 255, 255)
        )

        label_rect = label.get_rect(
            midleft=(
                rect.left + 40,
                rect.centery
            )
        )

        self.screen.blit(
            label,
            label_rect
        )

    # ==================================================
    # EVENTOS
    # ==================================================

    def handle_event(self, event):

        # ==========================
        # TECLADO
        # ==========================

        if event.type == pygame.KEYDOWN:

            # Arriba
            if event.key in (
                pygame.K_UP,
                pygame.K_w
            ):

                self.selected = (
                    self.selected - 1
                ) % len(self.options)

            # Abajo
            elif event.key in (
                pygame.K_DOWN,
                pygame.K_s
            ):

                self.selected = (
                    self.selected + 1
                ) % len(self.options)

            # Seleccionar
            elif event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE
            ):

                return self.options[
                    self.selected
                ][1]

            # Salir
            elif event.key == pygame.K_ESCAPE:

                return "quit"

        # ==========================
        # MOUSE
        # ==========================

        elif event.type == pygame.MOUSEMOTION:

            for i in range(
                len(self.options)
            ):

                rect = self.get_option_rect(i)

                if rect.collidepoint(
                    event.pos
                ):

                    self.selected = i

        # ==========================
        # CLICK
        # ==========================

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                for i, option in enumerate(
                    self.options
                ):

                    rect = self.get_option_rect(i)

                    if rect.collidepoint(
                        event.pos
                    ):

                        self.selected = i

                        return option[1]

        return None