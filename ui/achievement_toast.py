from pathlib import Path

import pygame

from core.achievements import achievements


SHOW_TIME = 3.5
FADE_TIME = 0.4


class AchievementToast:

    def __init__(self, size):

        self.width, self.height = size

        self.queue = []
        self.current = None
        self.started = 0

        scale = self.height / 720

        self.box_w = max(260, round(380 * scale))
        self.box_h = max(54, round(66 * scale))

        self.top_font = pygame.font.Font(None, max(16, round(22 * scale)))
        self.title_font = pygame.font.Font(None, max(20, round(32 * scale)))

        self.bg = None

        bg_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
            / "logro_aviso.png"
        )

        if bg_path.exists():

            try:

                self.bg = pygame.transform.smoothscale(
                    pygame.image.load(bg_path).convert_alpha(),
                    (self.box_w, self.box_h)
                )

            except pygame.error:
                self.bg = None

    def _next(self):

        if not self.queue:
            self.current = None
            return

        self.current = self.queue.pop(0)
        self.started = pygame.time.get_ticks()

    def draw(self, screen):

        for achievement_id in achievements.take_pending():
            self.queue.append(achievement_id)

        if self.current is None:
            self._next()

        if self.current is None:
            return

        elapsed = (pygame.time.get_ticks() - self.started) / 1000

        if elapsed >= SHOW_TIME:

            self._next()

            if self.current is None:
                return

            elapsed = 0.0

        if elapsed < FADE_TIME:
            alpha = elapsed / FADE_TIME
        elif elapsed > SHOW_TIME - FADE_TIME:
            alpha = (SHOW_TIME - elapsed) / FADE_TIME
        else:
            alpha = 1.0

        alpha = max(0.0, min(1.0, alpha))

        box = pygame.Surface((self.box_w, self.box_h), pygame.SRCALPHA)

        if self.bg is not None:

            box.blit(self.bg, (0, 0))

        else:

            pygame.draw.rect(
                box, (20, 24, 40, 235), box.get_rect(), border_radius=12
            )

            pygame.draw.rect(
                box, (255, 205, 90, 255), box.get_rect(), width=3,
                border_radius=12
            )

        top = self.top_font.render(
            "¡Logro desbloqueado!", True, (255, 205, 90)
        )

        title = self.title_font.render(
            achievements.title_of(self.current), True, (255, 255, 255)
        )

        box.blit(
            top,
            top.get_rect(midtop=(self.box_w // 2, round(self.box_h * 0.12)))
        )

        box.blit(
            title,
            title.get_rect(midbottom=(self.box_w // 2, round(self.box_h * 0.9)))
        )

        box.set_alpha(round(255 * alpha))

        screen.blit(
            box,
            box.get_rect(midtop=(self.width // 2, round(self.height * 0.03)))
        )