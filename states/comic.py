import pygame
from pathlib import Path


class Comic:

    IMAGES = ["image1.png", "image2.png"]


    FADE_TIME = 0.5


    INPUT_DELAY = 0.25

    BLUR = 24

    DARKEN = 150

    SHADOW = 18

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
        self.backgrounds = []

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

            self.backgrounds.append(
                self._make_background(image)
            )

        self.font = pygame.font.Font(None, 24)

        self.index = 0
        self.timer = 0

    def _make_background(self, image):

        cover = max(
            self.width / image.get_width(),
            self.height / image.get_height()
        )

        big = pygame.transform.smoothscale(
            image,
            (
                round(image.get_width() * cover),
                round(image.get_height() * cover)
            )
        )

        bg = pygame.Surface((self.width, self.height))

        bg.blit(
            big,
            big.get_rect(center=(self.width // 2, self.height // 2))
        )

        tiny = pygame.transform.smoothscale(
            bg,
            (max(1, self.width // self.BLUR), max(1, self.height // self.BLUR))
        )

        bg = pygame.transform.smoothscale(
            tiny,
            (self.width, self.height)
        )

        shade = pygame.Surface((self.width, self.height))
        shade.fill((8, 8, 14))
        shade.set_alpha(self.DARKEN)

        bg.blit(shade, (0, 0))

        return bg

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

        i = min(self.index, len(self.pages) - 1)

        page = self.pages[i]

        fade = int(255 * min(1, self.timer / self.FADE_TIME))

        background = self.backgrounds[i]
        background.set_alpha(fade)

        self.screen.blit(background, (0, 0))

        rect = page.get_rect(
            center=(
                self.width // 2,
                self.height // 2
            )
        )

        shadow = pygame.Surface(
            (
                rect.width + self.SHADOW * 2,
                rect.height + self.SHADOW * 2
            ),
            pygame.SRCALPHA
        )

        for step in range(self.SHADOW):

            pygame.draw.rect(
                shadow,
                (0, 0, 0, 12),
                shadow.get_rect().inflate(-step * 2, -step * 2),
                border_radius=10
            )

        self.screen.blit(
            shadow,
            shadow.get_rect(center=rect.center).move(0, 4)
        )

        page.set_alpha(fade)

        self.screen.blit(page, rect)

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