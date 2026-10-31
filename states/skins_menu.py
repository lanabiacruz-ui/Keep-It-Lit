import re
import pygame
from pathlib import Path

from core import skins as skin_lib
from core.audio_manager import audio


class SkinsMenu:

    IMG_W = 1672
    IMG_H = 941

    CLOSE_BOX = (1179, 219, 1204, 246)

    # Rectangulo real que dibuja la tablet (la linea oscura del fondo).
    # Las tarjetas van ADENTRO de este rectangulo, con margen.
    PANEL = (480, 270, 1238, 510)

    PAD = 10          # margen entre la linea de la tablet y las tarjetas
    BAR_W = 8         # ancho de la barra de scroll

    COLS = 6
    ROWS = 2          # filas visibles a la vez (siempre completas)
    GAP_X = 8
    GAP_Y = 8

    FILL = (31, 70, 134)
    FILL_SEL = (46, 104, 178)
    FILL_LOCKED = (24, 46, 92)
    FILL_LOCKED_SEL = (36, 64, 120)

    GOLD = (255, 205, 90)

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

        self.name_size = max(14, round(21 * self.sy))
        self.name_min = max(11, round(16 * self.sy))
        self.small_font = pygame.font.Font(None, max(13, round(18 * self.sy)))
        self.tag_font = pygame.font.Font(None, max(12, round(17 * self.sy)))
        self.controls_font = pygame.font.Font(
            None, max(14, round(20 * self.sy))
        )

        self.close_rect = self._box(self.CLOSE_BOX)
        self.panel = self._box(self.PANEL)

        self.skins = list(skin_lib.SKINS)

        self.equipped = skin_lib.get_skin()

        self.selected = 0

        for i, skin in enumerate(self.skins):

            if skin["id"] == self.equipped:
                self.selected = i

        padx = round(self.PAD * self.sx)
        pady = round(self.PAD * self.sy)
        bar_w = max(5, round(self.BAR_W * self.sx))

        self.gx = round(self.GAP_X * self.sx)
        self.gy = round(self.GAP_Y * self.sy)

        grid_w = self.panel.width - padx * 3 - bar_w
        grid_h = self.panel.height - pady * 2

        self.cw = (grid_w - (self.COLS - 1) * self.gx) // self.COLS
        self.ch = (grid_h - (self.ROWS - 1) * self.gy) // self.ROWS

        used_w = self.COLS * self.cw + (self.COLS - 1) * self.gx
        used_h = self.ROWS * self.ch + (self.ROWS - 1) * self.gy

        self.grid = pygame.Rect(
            self.panel.left + padx + (grid_w - used_w) // 2,
            self.panel.top + pady + (grid_h - used_h) // 2,
            used_w,
            used_h,
        )

        self.track = pygame.Rect(
            self.panel.right - padx - bar_w,
            self.grid.top,
            bar_w,
            self.grid.height,
        )

        self.row_target = 0
        self.scroll_f = 0.0
        self._last_ms = None
        self._dragging = False

        self._scroll_to_selected(instant=True)

        self._scaled = {}
        self._names = {}
        self._lines = {}

        self.coin = self._load_coin()

    def _box(self, box):

        x1, y1, x2, y2 = box

        return pygame.Rect(
            round(x1 * self.sx),
            round(y1 * self.sy),
            round((x2 - x1) * self.sx),
            round((y2 - y1) * self.sy),
        )

    def _load_coin(self):

        path = (
            Path(__file__).resolve().parent.parent
            / "assets" / "maps" / "hud" / "icon_moneda.png"
        )

        try:
            img = pygame.image.load(path).convert_alpha()
        except (OSError, pygame.error):
            return None

        h = max(8, round(15 * self.sy))

        return pygame.transform.smoothscale(
            img, (max(1, round(img.get_width() * h / img.get_height())), h)
        )

    # ---------- layout ----------

    def _rows(self):

        return (len(self.skins) + self.COLS - 1) // self.COLS

    def _max_row(self):

        return max(0, self._rows() - self.ROWS)

    def _row_px(self):

        return self.ch + self.gy

    def _card_rect(self, index):

        row, col = divmod(index, self.COLS)

        return pygame.Rect(
            self.grid.left + col * (self.cw + self.gx),
            self.grid.top + row * self._row_px() - round(self.scroll_f),
            self.cw,
            self.ch,
        )

    def _scroll_to_selected(self, instant=False):

        row = self.selected // self.COLS

        if row < self.row_target:
            self.row_target = row

        elif row > self.row_target + self.ROWS - 1:
            self.row_target = row - self.ROWS + 1

        self.row_target = max(0, min(self._max_row(), self.row_target))

        if instant:
            self.scroll_f = float(self.row_target * self._row_px())

    def _thumb_rect(self):

        rows = self._rows()

        if rows <= self.ROWS:
            return None

        h = max(
            round(24 * self.sy),
            round(self.track.height * self.ROWS / rows),
        )

        travel = self.track.height - h

        pos = self.scroll_f / max(1, self._max_row() * self._row_px())

        pos = max(0.0, min(1.0, pos))

        return pygame.Rect(
            self.track.left, self.track.top + round(travel * pos),
            self.track.width, h
        )

    def _drag_to(self, y):

        thumb = self._thumb_rect()

        if thumb is None:
            return

        travel = max(1, self.track.height - thumb.height)

        frac = (y - self.track.top - thumb.height / 2) / travel

        frac = max(0.0, min(1.0, frac))

        self.row_target = round(frac * self._max_row())

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

    def _card_at(self, pos):

        if not self.grid.collidepoint(pos):
            return None

        for i in range(len(self.skins)):

            if self._card_rect(i).collidepoint(pos):
                return i

        return None

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

            self.row_target = max(
                0, min(self._max_row(), self.row_target - event.y)
            )

        elif event.type == pygame.MOUSEMOTION:

            if self._dragging:

                self._drag_to(event.pos[1])

            else:

                i = self._card_at(event.pos)

                if i is not None:

                    if i != self.selected:
                        audio.play("click")

                    self.selected = i

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:

            self._dragging = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.close_rect.collidepoint(event.pos):
                return "back"

            if self._thumb_rect() is not None and self.track.inflate(
                round(10 * self.sx), 0
            ).collidepoint(event.pos):

                self._dragging = True

                self._drag_to(event.pos[1])

                return None

            i = self._card_at(event.pos)

            if i is not None:
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

        max_h = round(self.ch * 0.52)
        max_w = self.cw - round(20 * self.sx)

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

    @staticmethod
    def _short_name(name):

        # "Skin Saqueador" -> "Saqueador" (la palabra "Skin" sobra en la tarjeta)
        if name.lower().startswith("skin "):
            return name[5:]

        return name

    def _name_lines(self, text, color, width):

        """Nombre en 1 linea; si no entra, en 2 lineas antes que achicarlo."""

        key = (text, color, width)

        if key in self._names:
            return self._names[key]

        lines = None

        for size in range(self.name_size, self.name_min - 1, -1):

            font = pygame.font.Font(None, size)

            if font.size(text)[0] <= width:

                lines = [font.render(text, True, color)]

                break

        if lines is None:

            words = text.split()

            best = None

            for size in range(self.name_size - 2, self.name_min - 3, -1):

                font = pygame.font.Font(None, size)

                for cut in range(1, len(words)):

                    a = " ".join(words[:cut])
                    b = " ".join(words[cut:])

                    w = max(font.size(a)[0], font.size(b)[0])

                    if w <= width and (best is None or w < best[0]):
                        best = (w, font, a, b)

                if best is not None:
                    break

            if best is not None:

                _, font, a, b = best

                lines = [
                    font.render(a, True, color),
                    font.render(b, True, color),
                ]

            else:

                font = pygame.font.Font(None, self.name_min)

                surf = font.render(text, True, color)

                k = width / surf.get_width()

                lines = [pygame.transform.smoothscale(
                    surf, (width, max(1, round(surf.get_height() * k)))
                )]

        self._names[key] = lines

        return lines

    def _draw_card(self, index, rect):

        skin = self.skins[index]

        unlocked = skin_lib.is_unlocked(skin["id"])
        equipped = skin["id"] == self.equipped
        selected = index == self.selected

        if unlocked:
            fill = self.FILL_SEL if selected else self.FILL
        else:
            fill = self.FILL_LOCKED_SEL if selected else self.FILL_LOCKED

        radius = max(8, round(11 * self.sy))

        pygame.draw.rect(self.screen, fill, rect, border_radius=radius)

        # brillo suave arriba para que no se vea plano
        sheen = pygame.Rect(
            rect.x + 3, rect.y + 3, rect.width - 6, rect.height // 3
        )

        light = tuple(min(255, c + 14) for c in fill)

        pygame.draw.rect(
            self.screen, light, sheen,
            border_top_left_radius=radius - 2,
            border_top_right_radius=radius - 2,
        )

        # sprite
        sprite_zone = pygame.Rect(
            rect.x, rect.y + round(6 * self.sy),
            rect.width, round(self.ch * 0.52),
        )

        sprite = self._sprite(skin["id"], not unlocked)

        if sprite is not None:

            self.screen.blit(sprite, sprite.get_rect(center=sprite_zone.center))

        if not unlocked:

            self._draw_lock(
                (rect.right - round(14 * self.sx), rect.top + round(14 * self.sy))
            )

        # nombre (en el centro, debajo del sprite)
        name_zone = pygame.Rect(
            rect.x + 4, sprite_zone.bottom,
            rect.width - 8, round(self.ch * 0.26),
        )

        color = (255, 255, 255) if unlocked else (176, 190, 220)

        lines = self._name_lines(
            self._short_name(skin["nombre"]), color, name_zone.width
        )

        total_h = sum(l.get_height() for l in lines)

        y = name_zone.centery - total_h // 2

        for line in lines:

            self.screen.blit(
                line, line.get_rect(midtop=(rect.centerx, y))
            )

            y += line.get_height()

        # estado abajo
        status_zone = pygame.Rect(
            rect.x + round(10 * self.sx),
            name_zone.bottom,
            rect.width - round(20 * self.sx),
            rect.bottom - name_zone.bottom - round(5 * self.sy),
        )

        self._draw_status(skin, status_zone, unlocked, equipped)

        # borde (adentro del rect, nunca se sale)
        if equipped:
            border, width = self.GOLD, 3
        elif selected:
            border, width = (240, 247, 255), 2
        else:
            border, width = (96, 132, 200), 2

        pygame.draw.rect(
            self.screen, border, rect, width=width, border_radius=radius
        )

    def _draw_status(self, skin, zone, unlocked, equipped):

        if equipped:

            pill = pygame.Rect(0, 0, zone.width, max(10, zone.height))

            pill.center = zone.center

            pygame.draw.rect(
                self.screen, self.GOLD, pill, border_radius=pill.height // 2
            )

            tag = self.tag_font.render("EQUIPADA", True, (84, 50, 6))

            self.screen.blit(tag, tag.get_rect(center=pill.center))

            return

        if unlocked:
            return

        progress = skin_lib.progress_text(skin["id"])

        match = re.match(r"\s*(\d+)\s*/\s*(\d+)", progress or "")

        if match:

            have, goal = int(match.group(1)), max(1, int(match.group(2)))

            bar = pygame.Rect(0, 0, zone.width, max(10, zone.height))

            bar.center = zone.center

            pygame.draw.rect(
                self.screen, (12, 26, 58), bar, border_radius=bar.height // 2
            )

            if have > 0:

                fill = bar.copy()

                fill.width = max(
                    bar.height, round(bar.width * min(1.0, have / goal))
                )

                pygame.draw.rect(
                    self.screen, (86, 168, 255), fill,
                    border_radius=bar.height // 2,
                )

            pygame.draw.rect(
                self.screen, (96, 132, 200), bar, width=1,
                border_radius=bar.height // 2,
            )

            label = self.tag_font.render(f"{have}/{goal}", True, (255, 255, 255))

            self.screen.blit(label, label.get_rect(center=bar.center))

            return

        price = skin.get("precio")

        if price is not None and not skin.get("logro"):

            text = self.small_font.render(f"{price}", True, self.GOLD)

            gap = round(4 * self.sx)

            coin_w = self.coin.get_width() + gap if self.coin else 0

            x = zone.centerx - (coin_w + text.get_width()) // 2

            if self.coin:

                self.screen.blit(
                    self.coin, self.coin.get_rect(midleft=(x, zone.centery))
                )

            self.screen.blit(
                text,
                text.get_rect(midleft=(x + coin_w, zone.centery)),
            )

            return

        label = self.small_font.render("Bloqueada", True, (150, 170, 205))

        self.screen.blit(label, label.get_rect(center=zone.center))

    def _draw_lock(self, center):

        w = max(10, round(15 * self.sx))
        h = max(8, round(11 * self.sy))

        body = pygame.Rect(0, 0, w, h)
        body.center = (center[0], center[1] + h // 3)

        pygame.draw.arc(
            self.screen, (225, 234, 252),
            pygame.Rect(body.x + w // 5, body.y - h + 2, w * 3 // 5, h * 2 - 2),
            0, 3.14159, max(2, w // 7)
        )

        pygame.draw.rect(
            self.screen, (225, 234, 252), body, border_radius=3
        )

        pygame.draw.circle(
            self.screen, (60, 80, 120), body.center, max(1, w // 8)
        )

    def _draw_scrollbar(self):

        thumb = self._thumb_rect()

        if thumb is None:
            return

        pygame.draw.rect(
            self.screen, (18, 40, 84), self.track,
            border_radius=self.track.width // 2
        )

        hover = self._dragging or thumb.collidepoint(pygame.mouse.get_pos())

        pygame.draw.rect(
            self.screen,
            (170, 205, 255) if hover else (118, 164, 228),
            thumb,
            border_radius=self.track.width // 2,
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

    def _ease(self):

        now = pygame.time.get_ticks()

        dt = 0.0 if self._last_ms is None else min(0.05, (now - self._last_ms) / 1000)

        self._last_ms = now

        target = self.row_target * self._row_px()

        diff = target - self.scroll_f

        if abs(diff) < 0.5:
            self.scroll_f = float(target)
        else:
            self.scroll_f += diff * min(1.0, dt * 14.0)

    def draw(self):

        self._ease()

        self.screen.blit(self.background, (0, 0))

        previous_clip = self.screen.get_clip()

        self.screen.set_clip(
            self.grid.inflate(round(6 * self.sx), round(6 * self.sy))
        )

        for i in range(len(self.skins)):

            rect = self._card_rect(i)

            if rect.bottom < self.grid.top or rect.top > self.grid.bottom:
                continue

            self._draw_card(i, rect)

        self.screen.set_clip(previous_clip)

        self._draw_scrollbar()

        skin = self.skins[self.selected]

        if skin_lib.is_unlocked(skin["id"]):

            hint = skin["nombre"]

            if skin["id"] == self.equipped:
                hint += "  ·  Equipada"
            else:
                hint += "  ·  ENTER para equipar"

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

        controls = self.controls_font.render(
            f"Skins {done}/{len(self.skins)}  •  flechas elegir  •  "
            "ENTER equipar  •  rueda para ver más  •  ESC volver",
            True,
            (235, 242, 255)
        )

        self.screen.blit(
            controls,
            controls.get_rect(
                bottomright=(self.width - 18, self.height - 15)
            )
        )