import pygame
from pathlib import Path


class MainMenu:

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()


        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
            / "menu.png"
        )

        self.background = pygame.image.load(image_path).convert()

        self.background = pygame.transform.scale(
            self.background,
            (self.width, self.height)
        )


        self.options = [
            ("Nueva partida", "new_game"),
            ("Continuar partida", "continue_game"),
            ("Configuraciones", "settings"),
            ("Logros", "achievements"),
            ("Salir", "quit")
        ]

        self.selected = 0

        self.menu_x = 376
        self.menu_y = 245
        self.option_height = 33

        self.font = pygame.font.Font(None,42)
        self.small_font = pygame.font.Font(None,24)


    def get_option_rect(self, index):

        y = 227.25 + index * 33

        return pygame.Rect(
            376,
            y,
            290,
            38
        )

    def draw(self):

        self.screen.blit(
            self.background,
            (0, 0)
        )

        for i in range(len(self.options)):

            self.draw_option(i)


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

    def draw_option(self, index):

        if index == self.selected:

            rect = self.get_option_rect(index)

            pygame.draw.rect(
                self.screen,
                (240, 248, 255),
                rect,
                width=2,
                border_radius=3
            )

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

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key in (
                pygame.K_UP,
                pygame.K_w
            ):

                self.selected = (
                    self.selected - 1
                ) % len(self.options)

            elif event.key in (
                pygame.K_DOWN,
                pygame.K_s
            ):

                self.selected = (
                    self.selected + 1
                ) % len(self.options)

            elif event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE
            ):

                return self.options[self.selected][1]

            elif event.key == pygame.K_ESCAPE:

                return "quit"


        elif event.type == pygame.MOUSEMOTION:

            for i in range(
                len(self.options)
            ):

                rect = self.get_option_rect(i)

                if rect.collidepoint(
                    event.pos
                ):

                    self.selected = i

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                for i, option in enumerate(
                    self.options
                ):

                    rect = self.get_option_rect(i)

                    if rect.collidepoint(event.pos):

                        self.selected = i

                        return option[1]

        return None
