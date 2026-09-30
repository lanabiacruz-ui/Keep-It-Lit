import pygame
from pathlib import Path


class Startup:

    def __init__(self, screen, duration=1.2):

        self.screen = screen
        self.width, self.height = screen.get_size()

        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
            / "title.png"
        )

        self.title = pygame.image.load(
            image_path
        ).convert_alpha()

        
        max_width = 700
        max_height = 300

        scale = min(
            max_width / self.title.get_width(),
            max_height / self.title.get_height(),
            1
        )

        if scale != 1:

            self.title = pygame.transform.smoothscale(
                self.title,
                (
                    round(self.title.get_width() * scale),
                    round(self.title.get_height() * scale)
                )
            )

        self.duration = duration
        self.timer = 0

        self.font = pygame.font.Font(
            None,
            28
        )

    def update(self, dt):

        self.timer += dt

        if self.timer >= self.duration:

            return "done"

        return None

    def draw(self):

        self.screen.fill(
            (0, 0, 0)
        )

        
        title_rect = self.title.get_rect(
            center=(
                self.width // 2,
                self.height // 2 - 80
            )
        )

        self.screen.blit(
            self.title,
            title_rect
        )

        
        loading_text = self.font.render(
            "Loading...",
            True,
            (255, 255, 255)
        )

        loading_rect = loading_text.get_rect(
            center=(
                self.width // 2,
                self.height // 2 + 80
            )
        )

        self.screen.blit(
            loading_text,
            loading_rect
        )

       
        bar_width = 350
        bar_height = 12

        bar_rect = pygame.Rect(
            self.width // 2 - bar_width // 2,
            self.height // 2 + 120,
            bar_width,
            bar_height
        )

        pygame.draw.rect(
            self.screen,
            (235, 242, 255),
            bar_rect,
            width=2,
            border_radius=4
        )

        progress = min(
            1,
            self.timer / self.duration
        )

        fill_rect = bar_rect.inflate(
            -4,
            -4
        )

        fill_rect.width = int(
            fill_rect.width * progress
        )

        if fill_rect.width > 0:

            pygame.draw.rect(
                self.screen,
                (255, 255, 255),
                fill_rect,
                border_radius=3
            )
