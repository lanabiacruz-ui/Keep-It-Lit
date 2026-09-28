import pygame
from pathlib import Path


class Loading:

    IMG_W = 1672
    IMG_H = 941

    BAR_BOX = (770, 425, 970, 437)   

    def __init__(self, screen, duration=2.0):

        self.screen = screen
        self.width, self.height = screen.get_size()

        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
            / "mapaloading.png"
        )

        self.background = pygame.image.load(image_path).convert()

        self.background = pygame.transform.scale(
            self.background,
            (self.width, self.height)
        )

        x1, y1, x2, y2 = self.BAR_BOX

        sx = self.width / self.IMG_W
        sy = self.height / self.IMG_H

        self.bar_rect = pygame.Rect(
            round(x1 * sx),
            round(y1 * sy),
            round((x2 - x1) * sx),
            round((y2 - y1) * sy)
        )

        self.duration = duration
        self.timer = 0

    def update(self, dt):

        self.timer += dt

        if self.timer >= self.duration:

            return "done"

        return None

    def draw(self):

        self.screen.blit(
            self.background,
            (0, 0)
        )

        progress = min(1, self.timer / self.duration)

        
        pygame.draw.rect(
            self.screen,
            (235, 242, 255),
            self.bar_rect,
            width=2,
            border_radius=3
        )

        
        fill_rect = self.bar_rect.inflate(-6, -6)
        fill_rect.width = int(fill_rect.width * progress)

        if fill_rect.width > 0:

            pygame.draw.rect(
                self.screen,
                (255, 255, 255),
                fill_rect,
                border_radius=2
            )
