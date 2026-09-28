import pygame
from pathlib import Path


class Comic:

    IMAGES = ["image1.png", "image2.png"]

  
    FADE_TIME = 0.5


    INPUT_DELAY = 0.25

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()

        folder = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
        )

        self.pages = []

        for name in self.IMAGES:

            image = pygame.image.load(
                folder / name
            ).convert()

            
            scale = min(
                self.width / image.get_width(),
                self.height / image.get_height()
            )

            size = (
                round(image.get_width() * scale),
                round(image.get_height() * scale)
            )

            self.pages.append(
                pygame.transform.smoothscale(image, size)
            )

        self.font = pygame.font.Font(None, 24)

        self.index = 0
        self.timer = 0

    def _next(self):

        self.index += 1
        self.timer = 0

        if self.index >= len(self.pages):

            return "done"

        return None

    def handle_event(self, event):
      

        if self.timer < self.INPUT_DELAY:

            return None

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                return "done"

            if event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_SPACE,
                pygame.K_RIGHT
            ):

                return self._next()

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                return self._next()

        return None

    def update(self, dt):

        self.timer += dt

    def draw(self):

        self.screen.fill((12, 12, 16))

        page = self.pages[
            min(self.index, len(self.pages) - 1)
        ]

        page.set_alpha(
            int(255 * min(1, self.timer / self.FADE_TIME))
        )

        self.screen.blit(
            page,
            page.get_rect(
                center=(
                    self.width // 2,
                    self.height // 2
                )
            )
        )

        hint = self.font.render(
            "ENTER: continuar  •  ESC: saltar",
            True,
            (150, 155, 170)
        )

        self.screen.blit(
            hint,
            hint.get_rect(
                bottomright=(
                    self.width - 18,
                    self.height - 15
                )
            )
        )
