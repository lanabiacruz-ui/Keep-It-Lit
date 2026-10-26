import pygame
from pathlib import Path

from core.achievements import achievements, ACHIEVEMENTS


class AchievementsMenu:

    IMG_W = 1672
    IMG_H = 941

    CLOSE_BOX = (1179, 219, 1204, 246)

    PANEL = (482, 272, 1212, 508)

    ROW_H = 56
    ROW_STEP = 59
    ROW_W = 718

    ICON_SIZE = (40, 40)

    def __init__(self, screen, background="mapalogros.png"):

        self.screen = screen
        self.width, self.height = screen.get_size()

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        ui_dir = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
        )

        background_path = ui_dir / background

        if not background_path.exists():
            background_path = ui_dir / "mapaajustes.png"

        image = pygame.image.load(background_path).convert()

        self.background = pygame.transform.smoothscale(
            image,
            (self.width, self.height)
        )

        self.font = pygame.font.Font(None, max(20, round(34 * self.sy)))
        self.desc_font = pygame.font.Font(None, max(16, round(24 * self.sy)))
        self.small_font = pygame.font.Font(None, max(16, round(24 * self.sy)))

        self.close_rect = self._box(self.CLOSE_BOX)
        self.panel = self._box(self.PANEL)

        self.scroll = 0

        self.rows = achievements.rows()

        self.ui_dir = ui_dir

        row_size = (self.ROW_W, self.ROW_H)

        self.row_img = self._load_optional("logro_fila.png", row_size)

        self.row_done_img = self._load_optional(
            "logro_fila_hecho.png", row_size
        )

        if self.row_done_img is None:
            self.row_done_img = self.row_img

        self.icons = {}

        for ach in ACHIEVEMENTS:

            color = self._load_optional(
                f"logro_{ach['id']}.png", self.ICON_SIZE
            )

            locked = self._load_optional(
                f"logro_{ach['id']}_bloqueado.png", self.ICON_SIZE
            )

            if color is not None and locked is None:

                locked = color.copy()

                locked.fill(
                    (90, 90, 90, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

            self.icons[(ach["id"], True)] = color
            self.icons[(ach["id"], False)] = locked

    def _load_optional(self, name, size):

        path = self.ui_dir / name

        if not path.exists():
            return None

        try:
            image = pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None

        return pygame.transform.smoothscale(
            image,
            (
                max(1, round(size[0] * self.sx)),
                max(1, round(size[1] * self.sy))
            )
        )

    def _box(self, box):

        x1, y1, x2, y2 = box

        return pygame.Rect(
            round(x1 * self.sx),
            round(y1 * self.sy),
            round((x2 - x1) * self.sx),
            round((y2 - y1) * self.sy)
        )

    def _max_scroll(self):

        step = round(self.ROW_STEP * self.sy)

        total = len(self.rows) * step

        return max(0, total - self.panel.height)

    def _move_scroll(self, amount):

        self.scroll = max(0, min(self._max_scroll(), self.scroll + amount))

    def handle_event(self, event):

        step = round(self.ROW_STEP * self.sy)

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                return "back"

            if event.key in (pygame.K_UP, pygame.K_w):
                self._move_scroll(-step)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_scroll(step)

            elif event.key == pygame.K_PAGEUP:
                self._move_scroll(-step * 3)

            elif event.key == pygame.K_PAGEDOWN:
                self._move_scroll(step * 3)

            elif event.key == pygame.K_HOME:
                self.scroll = 0

            elif event.key == pygame.K_END:
                self.scroll = self._max_scroll()

        elif event.type == pygame.MOUSEWHEEL:

            self._move_scroll(-event.y * step)

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1 and self.close_rect.collidepoint(event.pos):
                return "back"

        return None

    def update(self, dt):
        pass

    def _fit_text(self, text, max_width, color):

        font = self.desc_font

        size = font.get_height()

        while font.size(text)[0] > max_width and size > 12:

            size -= 1

            font = pygame.font.Font(None, size)

        return font.render(text, True, color)

    def _draw_row(self, row, rect):

        unlocked = row["unlocked"]

        row_img = self.row_done_img if unlocked else self.row_img

        if row_img is not None:

            self.screen.blit(row_img, rect.topleft)

        else:

            fill = (34, 98, 74) if unlocked else (30, 62, 118)
            border = (255, 205, 90) if unlocked else (120, 150, 205)

            pygame.draw.rect(self.screen, fill, rect, border_radius=10)
            pygame.draw.rect(
                self.screen, border, rect, width=2, border_radius=10
            )

        radius = rect.height // 2 - 8

        center = (rect.left + radius + 12, rect.centery)

        icon = self.icons.get((row["id"], unlocked))

        if icon is not None:

            self.screen.blit(icon, icon.get_rect(center=center))

        elif unlocked:

            pygame.draw.circle(self.screen, (255, 205, 90), center, radius)

            pygame.draw.lines(
                self.screen,
                (60, 40, 10),
                False,
                [
                    (center[0] - radius // 2, center[1]),
                    (center[0] - radius // 8, center[1] + radius // 3),
                    (center[0] + radius // 2, center[1] - radius // 3),
                ],
                max(2, radius // 5)
            )

        else:

            pygame.draw.circle(self.screen, (70, 90, 130), center, radius)
            pygame.draw.circle(
                self.screen, (150, 170, 210), center, radius, width=2
            )

        text_x = center[0] + radius + 14

        title = self.font.render(
            row["title"], True,
            (255, 255, 255) if unlocked else (215, 228, 250)
        )

        right_limit = rect.right - 14

        if row["goal"] > 1 and not unlocked:
            right_limit -= round(150 * self.sx) + 14
        else:
            right_limit -= round(120 * self.sx)

        desc = self._fit_text(
            row["desc"], max(40, right_limit - text_x), (205, 220, 245)
        )

        self.screen.blit(title, (text_x, rect.top + round(rect.height * 0.10)))

        self.screen.blit(desc, (text_x, rect.top + round(rect.height * 0.58)))

        right = rect.right - 14

        if row["goal"] > 1 and not unlocked:

            bar_w = round(150 * self.sx)
            bar_h = max(8, round(14 * self.sy))

            bar = pygame.Rect(0, 0, bar_w, bar_h)
            bar.midright = (right, rect.centery + round(8 * self.sy))

            pygame.draw.rect(self.screen, (15, 30, 70), bar, border_radius=bar_h // 2)

            ratio = row["progress"] / row["goal"]

            fill_w = round(bar_w * ratio)

            if fill_w > 0:

                pygame.draw.rect(
                    self.screen,
                    (255, 205, 90),
                    (bar.left, bar.top, fill_w, bar_h),
                    border_radius=bar_h // 2
                )

            count = self.small_font.render(
                f"{row['progress']}/{row['goal']}", True, (235, 242, 255)
            )

            self.screen.blit(
                count,
                count.get_rect(midbottom=(bar.centerx, bar.top - 2))
            )

        else:

            status = self.small_font.render(
                "Desbloqueado" if unlocked else "Bloqueado",
                True,
                (255, 205, 90) if unlocked else (170, 190, 225)
            )

            self.screen.blit(
                status,
                status.get_rect(midright=(right, rect.centery))
            )

    def _draw_scrollbar(self):

        max_scroll = self._max_scroll()

        if max_scroll <= 0:
            return

        track = pygame.Rect(
            self.panel.right + round(6 * self.sx),
            self.panel.top,
            max(4, round(7 * self.sx)),
            self.panel.height,
        )

        pygame.draw.rect(
            self.screen, (15, 30, 70), track, border_radius=track.width // 2
        )

        total = self.panel.height + max_scroll

        thumb_h = max(round(24 * self.sy), round(track.height * self.panel.height / total))

        thumb = pygame.Rect(
            track.left,
            track.top + round((track.height - thumb_h) * self.scroll / max_scroll),
            track.width,
            thumb_h,
        )

        pygame.draw.rect(
            self.screen, (110, 160, 230), thumb, border_radius=track.width // 2
        )

    def draw(self):

        self.screen.blit(self.background, (0, 0))

        previous_clip = self.screen.get_clip()

        self.screen.set_clip(self.panel)

        step = round(self.ROW_STEP * self.sy)
        height = round(self.ROW_H * self.sy)

        for i, row in enumerate(self.rows):

            rect = pygame.Rect(
                self.panel.left + round(6 * self.sx),
                self.panel.top + i * step - self.scroll + 2,
                round(self.ROW_W * self.sx),
                height
            )

            if rect.bottom < self.panel.top or rect.top > self.panel.bottom:
                continue

            self._draw_row(row, rect)

        self.screen.set_clip(previous_clip)

        self._draw_scrollbar()

        done = sum(1 for row in self.rows if row["unlocked"])

        info = self.small_font.render(
            f"Logros {done}/{len(self.rows)}  •  ESC volver",
            True,
            (235, 242, 255)
        )

        self.screen.blit(
            info,
            info.get_rect(bottomright=(self.width - 18, self.height - 15))
        )