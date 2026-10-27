import pygame
from pathlib import Path

from core import skins as skin_lib
from core.audio_manager import audio


class SkinsMenu:

    IMG_W = 1672
    IMG_H = 941

    CLOSE_BOX = (1179, 219, 1204, 246)

    PANEL = (482, 272, 1212, 508)

    COLS = 6
    CARD_W = 110
    CARD_H = 108
    GAP_X = 14
    GAP_Y = 12

    def __init__(self, screen, background="mapaajustes.png"):

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

        image = pygame.image.load(ui_dir / background).convert()

        self.background = pygame.transform.smoothscale(
            image, (self.width, self.height)
        )

        self.font = pygame.font.Font(None, max(16, round(26 * self.sy)))
        self.small_font = pygame.font.Font(None, max(14, round(20 * self.sy)))
        self.info_font = pygame.font.Font(None, max(18, round(28 * self.sy)))

        self.close_rect = self._box(self.CLOSE_BOX)
        self.panel = self._box(self.PANEL)

        self.skins = list(skin_lib.SKINS)

        self.equipped = skin_lib.get_skin()

        self.selected = 0

        for i, skin in enumerate(self.skins):

            if skin["id"] == self.equipped:
                self.selected = i

        self.cw = round(self.CARD_W * self.sx)
        self.ch = round(self.CARD_H * self.sy)
        self.gx = round(self.GAP_X * self.sx)
        self.gy = round(self.GAP_Y * self.sy)

        self.left = (
            self.panel.centerx
            - (self.COLS * self.cw + (self.COLS - 1) * self.gx) // 2
        )

        self.scroll = 0

        self._scroll_to_selected(instant=True)

        self._scaled = {}
        self._lines = {}

    def _box(self, box):

        x1, y1, x2, y2 = box

        return pygame.Rect(
            round(x1 * self.sx),
            round(y1 * self.sy),
            round((x2 - x1) * self.sx),
            round((y2 - y1) * self.sy),
        )

    # ---------- layout ----------

    def _rows(self):

        return (len(self.skins) + self.COLS - 1) // self.COLS

    def _max_scroll(self):

        total = self._rows() * (self.ch + self.gy) - self.gy

        return max(0, total - self.panel.height + 8)

    def _card_rect(self, index):

        row, col = divmod(index, self.COLS)

        return pygame.Rect(
            self.left + col * (self.cw + self.gx),
            self.panel.top + 4 + row * (self.ch + self.gy) - self.scroll,
            self.cw,
            self.ch,
        )

    def _scroll_to_selected(self, instant=False):

        row = self.selected // self.COLS

        top = row * (self.ch + self.gy)
        bottom = top + self.ch

        if top < self.scroll:
            self.scroll = top

        elif bottom > self.scroll + self.panel.height - 8:
            self.scroll = bottom - self.panel.height + 8

        self.scroll = max(0, min(self._max_scroll(), self.scroll))

    # ---------- acciones ----------

    def _choose(self, index):

        skin = self.skins[index]

        if not skin_lib.is_unlocked(skin["id"]):

            audio.play("door_resist")

            return

        self.selected = index

        if skin["id"] != self.equipped and skin_lib.set_skin(skin["id"]):

            self.equipped = skin["id"]

            audio.play("pickup")

    def _select(self, index):

        index = max(0, min(len(self.skins) - 1, index))

        if index != self.selected:

            self.selected = index

            self._scroll_to_selected()

            audio.play("click")

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                return "back"

            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._select(self.selected - 1)

            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._select(self.selected + 1)

            elif event.key in (pygame.K_UP, pygame.K_w):
                self._select(self.selected - self.COLS)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._select(self.selected + self.COLS)

            elif event.key in (
                pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE
            ):
                self._choose(self.selected)

        elif event.type == pygame.MOUSEWHEEL:

            step = self.ch + self.gy

            self.scroll = max(
                0, min(self._max_scroll(), self.scroll - event.y * step)
            )

        elif event.type == pygame.MOUSEMOTION:

            if self.panel.collidepoint(event.pos):

                for i in range(len(self.skins)):

                    if self._card_rect(i).collidepoint(event.pos):

                        if i != self.selected:
                            audio.play("click")

                        self.selected = i

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.close_rect.collidepoint(event.pos):
                return "back"

            if self.panel.collidepoint(event.pos):

                for i in range(len(self.skins)):

                    if self._card_rect(i).collidepoint(event.pos):
                        self._choose(i)

        return None

    def update(self, dt):
        pass

    # ---------- dibujo ----------

    def _sprite(self, skin_id, locked):

        key = (skin_id, locked)

        if key in self._scaled:
            return self._scaled[key]

        try:
            base = skin_lib.preview_sprite(skin_id)
        except Exception:
            base = None

        if base is None:

            self._scaled[key] = None

            return None

        max_h = self.ch - round(46 * self.sy)
        max_w = self.cw - round(16 * self.sx)

        k = min(max_w / base.get_width(), max_h / base.get_height())

        size = (
            max(1, round(base.get_width() * k)),
            max(1, round(base.get_height() * k)),
        )

        sprite = pygame.transform.smoothscale(base, size)

        if locked:

            sprite.fill(
                (40, 40, 55, 255), special_flags=pygame.BLEND_RGBA_MULT
            )

        self._scaled[key] = sprite

        return sprite

    def _draw_card(self, index, rect):

        skin = self.skins[index]

        unlocked = skin_lib.is_unlocked(skin["id"])
        equipped = skin["id"] == self.equipped
        hovered = index == self.selected

        fill = (30, 82, 150) if hovered else (30, 66, 126)

        if not unlocked:
            fill = (26, 46, 88)

        pygame.draw.rect(self.screen, fill, rect, border_radius=10)

        if equipped:
            border, width = (255, 205, 90), 3
        elif hovered:
            border, width = (235, 245, 255), 2
        else:
            border, width = (110, 145, 205), 2

        pygame.draw.rect(
            self.screen, border, rect, width=width, border_radius=10
        )

        sprite = self._sprite(skin["id"], not unlocked)

        if sprite is not None:

            self.screen.blit(
                sprite,
                sprite.get_rect(
                    midtop=(rect.centerx, rect.top + round(8 * self.sy))
                )
            )

        if not unlocked:
            self._draw_lock(rect)

        name = self.font.render(
            skin["nombre"], True,
            (255, 255, 255) if unlocked else (170, 185, 215)
        )

        if name.get_width() > rect.width - 8:

            name = pygame.transform.smoothscale(
                name,
                (
                    rect.width - 8,
                    max(1, round(
                        name.get_height()
                        * (rect.width - 8) / name.get_width()
                    ))
                )
            )

        self.screen.blit(
            name,
            name.get_rect(
                midbottom=(rect.centerx, rect.bottom - round(18 * self.sy))
            )
        )

        if equipped:
            status, color = "Equipada", (255, 205, 90)
        elif not unlocked:
            status, color = skin_lib.status_text(skin["id"]), (150, 170, 205)
        else:
            status, color = "", (255, 255, 255)

        if status:

            label = self.small_font.render(status, True, color)

            self.screen.blit(
                label,
                label.get_rect(
                    midbottom=(rect.centerx, rect.bottom - round(3 * self.sy))
                )
            )

    def _draw_lock(self, rect):

        w = max(10, round(18 * self.sx))
        h = max(8, round(14 * self.sy))

        body = pygame.Rect(0, 0, w, h)
        body.center = (rect.centerx, rect.top + round(40 * self.sy))

        pygame.draw.arc(
            self.screen, (220, 230, 250),
            pygame.Rect(body.x + w // 5, body.y - h, w * 3 // 5, h * 2),
            0, 3.14159, max(2, w // 7)
        )

        pygame.draw.rect(
            self.screen, (220, 230, 250), body, border_radius=3
        )

    def _fit_line(self, text, max_width):

        key = (text, max_width)

        if key in self._lines:
            return self._lines[key]

        size = max(18, round(28 * self.sy))

        while True:

            font = pygame.font.Font(None, size)

            line = font.render(text, True, (235, 242, 255))

            if line.get_width() <= max_width or size <= 14:
                self._lines[key] = line
                return line

            size -= 1

    def draw(self):

        self.screen.blit(self.background, (0, 0))

        previous_clip = self.screen.get_clip()

        self.screen.set_clip(self.panel)

        for i in range(len(self.skins)):

            rect = self._card_rect(i)

            if rect.bottom < self.panel.top or rect.top > self.panel.bottom:
                continue

            self._draw_card(i, rect)

        self.screen.set_clip(previous_clip)

        skin = self.skins[self.selected]

        if skin_lib.is_unlocked(skin["id"]):
            hint = skin["nombre"]
        else:
            hint = f"{skin['nombre']}: {skin_lib.requirement_text(skin['id'])}"

        info = self._fit_line(hint, self.panel.width - 12)

        self.screen.blit(
            info,
            info.get_rect(
                midtop=(self.panel.centerx, self.panel.bottom + round(10 * self.sy))
            )
        )

        done = sum(1 for s in self.skins if skin_lib.is_unlocked(s["id"]))

        controls = self.small_font.render(
            f"Skins {done}/{len(self.skins)}  •  flechas elegir  •  "
            "ENTER equipar  •  ESC volver",
            True,
            (235, 242, 255)
        )

        self.screen.blit(
            controls,
            controls.get_rect(
                bottomright=(self.width - 18, self.height - 15)
            )
        )