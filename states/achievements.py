import pygame
from pathlib import Path

from core.achievements import achievements, ACHIEVEMENTS


GOLD = (255, 205, 90)
GOLD_LIGHT = (255, 226, 140)
NAVY = (15, 30, 70)
NAVY_ICON = (18, 36, 84)
RING_LOCKED = (120, 150, 205)
TEXT_LOCKED = (215, 228, 250)
TEXT_DESC = (205, 220, 245)
TEXT_SHADOW = (12, 26, 66)


class AchievementsMenu:

    IMG_W = 1672
    IMG_H = 941

    CLOSE_BOX = (1179, 219, 1204, 246)

    PANEL = (482, 272, 1212, 508)

    ROW_H = 56
    ROW_STEP = 59
    ROW_W = 718

    ICON_SIZE = (40, 40)

    # Contador "Logros 4/20" arriba a la izquierda, en la barra de la tablet
    HEADER_POS = (492, 221)
    HEADER_BAR_W = 170

    # Hueco libre entre las dos manos (solo con la tablet de la pausa):
    # ahi va el cuadro con el detalle completo del logro elegido.
    DETAIL_BOX = (730, 650, 1046, 800)

    # Las filas desbloqueadas se tiñen de dorado sobre el dibujo de las
    # bloqueadas (el gris de logro_fila_hecho.png se veia apagado).
    GOLD_TINT = True

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

        # convert_alpha: la tablet tiene fondo transparente, asi se ve el
        # juego detras en vez de negro
        image = pygame.image.load(background_path).convert_alpha()

        self.background = pygame.transform.smoothscale(
            image,
            (self.width, self.height)
        )

        # capa con SOLO las manos: se dibuja encima de las filas
        self.hands = None

        hands_path = ui_dir / "tablet_manos.png"

        if background_path.name.startswith("tablet") and hands_path.exists():

            hands = pygame.image.load(hands_path).convert_alpha()

            self.hands = pygame.transform.smoothscale(
                hands,
                (self.width, self.height)
            )

        self._fonts = {}
        self._text_cache = {}

        self.title_size = max(20, round(34 * self.sy))
        self.desc_size = max(16, round(24 * self.sy))
        self.desc_min = max(12, round(17 * self.sy))
        self.small_size = max(16, round(24 * self.sy))

        self.close_rect = self._box(self.CLOSE_BOX)
        self.panel = self._box(self.PANEL)

        self.rows = achievements.rows()

        self.ui_dir = ui_dir

        self.step = max(1, round(self.ROW_STEP * self.sy))
        self.row_h = max(1, round(self.ROW_H * self.sy))
        self.row_w = max(1, round(self.ROW_W * self.sx))

        # +0.25: con el redondeo del escalado 3.98 filas cuentan como 4
        self.visible_rows = max(1, int(self.panel.height / self.step + 0.25))

        # scroll: _target es a donde va, scroll_f es donde esta (suave)
        self.scroll_f = 0.0
        self._target = 0.0
        self._last_ms = None
        self._dragging = False

        self.selected = 0

        self.track = pygame.Rect(
            self.panel.right + round(6 * self.sx),
            self.panel.top,
            max(6, round(9 * self.sx)),
            self.panel.height,
        )

        row_size = (self.ROW_W, self.ROW_H)

        self.row_img = self._load_optional("logro_fila.png", row_size)

        self.row_done_img = self._load_optional(
            "logro_fila_hecho.png", row_size
        )

        if self.row_done_img is None:
            self.row_done_img = self.row_img

        self.row_hl = None

        if self.row_img is not None:

            self.row_hl = self._tint(self.row_img, (255, 255, 255), 55)

            if self.GOLD_TINT:

                gold = self.row_img.copy()

                gold.blit(self._tint(self.row_img, (255, 196, 70), 105), (0, 0))

                self.row_done_img = gold

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

    # ------------------------------------------------------------------
    # utilidades
    # ------------------------------------------------------------------

    @staticmethod
    def _tint(surface, rgb, alpha):
        """Copia de la forma de `surface` pintada de un color (con alpha)."""

        tinted = surface.copy()

        tinted.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_ADD)

        tinted.fill(
            (rgb[0], rgb[1], rgb[2], alpha),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        return tinted

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

    def _font(self, size):

        size = max(8, int(size))

        font = self._fonts.get(size)

        if font is None:
            font = pygame.font.Font(None, size)
            self._fonts[size] = font

        return font

    def _text(self, text, size, color, shadow=True):
        """Texto ya renderizado (con sombrita) y en cache."""

        key = (text, size, color, shadow)

        surf = self._text_cache.get(key)

        if surf is not None:
            return surf

        font = self._font(size)

        main = font.render(text, True, color)

        if shadow:

            back = font.render(text, True, TEXT_SHADOW)

            surf = pygame.Surface(
                (main.get_width() + 1, main.get_height() + 1),
                pygame.SRCALPHA
            )

            surf.blit(back, (1, 1))
            surf.blit(main, (0, 0))

        else:
            surf = main

        if len(self._text_cache) > 600:
            self._text_cache.clear()

        self._text_cache[key] = surf

        return surf

    def _fit_text(self, text, max_width, color):
        """Achica la letra hasta que entre; si aun asi no entra, corta con ..."""

        max_width = max(10, int(max_width))

        size = self.desc_size

        while size > self.desc_min and self._font(size).size(text)[0] > max_width:
            size -= 1

        if self._font(size).size(text)[0] > max_width:

            while len(text) > 4 and self._font(size).size(text + "...")[0] > max_width:
                text = text[:-1]

            text = text.rstrip() + "..."

        return self._text(text, size, color)

    def _wrap(self, text, size, max_width):

        font = self._font(size)

        lines = []
        current = ""

        for word in text.split():

            test = word if not current else current + " " + word

            if font.size(test)[0] <= max_width or not current:
                current = test
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    # ------------------------------------------------------------------
    # scroll y seleccion
    # ------------------------------------------------------------------

    def _max_scroll(self):

        return max(0, (len(self.rows) - self.visible_rows) * self.step)

    def _clamp(self, value):

        return max(0.0, min(float(self._max_scroll()), float(value)))

    def _scroll_rows(self, amount):
        """Mueve la vista de a filas enteras."""

        row = round(self._target / self.step) + amount

        self._target = self._clamp(row * self.step)

    def _ensure_visible(self):

        top = self.selected * self.step

        if top < self._target:
            self._target = self._clamp(top)

        elif top + self.step > self._target + self.visible_rows * self.step:
            self._target = self._clamp(
                (self.selected - self.visible_rows + 1) * self.step
            )

    def _select(self, index):

        self.selected = max(0, min(len(self.rows) - 1, index))

        self._ensure_visible()

    def _row_at(self, y):

        index = int((y - self.panel.top - 2 + self.scroll_f) // self.step)

        if 0 <= index < len(self.rows):
            return index

        return None

    def _thumb_rect(self):

        max_scroll = self._max_scroll()

        if max_scroll <= 0:
            return None

        total = self.panel.height + max_scroll

        thumb_h = max(
            round(28 * self.sy),
            round(self.track.height * self.panel.height / total)
        )

        ratio = self._clamp(self.scroll_f) / max_scroll

        return pygame.Rect(
            self.track.left,
            self.track.top + round((self.track.height - thumb_h) * ratio),
            self.track.width,
            thumb_h,
        )

    def _drag_to(self, y):

        thumb = self._thumb_rect()

        if thumb is None:
            return

        span = max(1, self.track.height - thumb.height)

        ratio = (y - self.track.top - thumb.height / 2) / span

        ratio = max(0.0, min(1.0, ratio))

        self._target = self.scroll_f = ratio * self._max_scroll()

    def _ease(self):

        now = pygame.time.get_ticks()

        dt = 0.0 if self._last_ms is None else min(
            0.05, (now - self._last_ms) / 1000
        )

        self._last_ms = now

        if self._dragging:
            return

        diff = self._target - self.scroll_f

        if abs(diff) < 0.5:
            self.scroll_f = float(self._target)
        else:
            self.scroll_f += diff * min(1.0, dt * 14.0)

    # ------------------------------------------------------------------
    # eventos
    # ------------------------------------------------------------------

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                return "back"

            if event.key in (pygame.K_UP, pygame.K_w):
                self._select(self.selected - 1)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._select(self.selected + 1)

            elif event.key == pygame.K_PAGEUP:
                self._select(self.selected - self.visible_rows)

            elif event.key == pygame.K_PAGEDOWN:
                self._select(self.selected + self.visible_rows)

            elif event.key == pygame.K_HOME:
                self._select(0)

            elif event.key == pygame.K_END:
                self._select(len(self.rows) - 1)

        elif event.type == pygame.MOUSEWHEEL:

            self._scroll_rows(-event.y)

        elif event.type == pygame.MOUSEMOTION:

            if self._dragging:

                self._drag_to(event.pos[1])

            elif self.panel.collidepoint(event.pos):

                index = self._row_at(event.pos[1])

                if index is not None:
                    self.selected = index

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:

            if self._dragging:

                self._dragging = False

                # al soltar, se acomoda en una fila entera
                self._target = self._clamp(
                    round(self.scroll_f / self.step) * self.step
                )

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.close_rect.collidepoint(event.pos):
                return "back"

            if (
                self._thumb_rect() is not None
                and self.track.inflate(round(12 * self.sx), 0).collidepoint(
                    event.pos
                )
            ):

                self._dragging = True

                self._drag_to(event.pos[1])

            elif self.panel.collidepoint(event.pos):

                index = self._row_at(event.pos[1])

                if index is not None:
                    self._select(index)

        return None

    def update(self, dt):
        pass

    # ------------------------------------------------------------------
    # dibujo
    # ------------------------------------------------------------------

    def _draw_padlock(self, center, color):

        w = max(9, round(11 * self.sx))
        h = max(7, round(8 * self.sy))

        body = pygame.Rect(0, 0, w, h)
        body.center = (center[0], center[1] + h // 3)

        arc = pygame.Rect(body.left + 2, body.top - h, max(4, w - 4), h * 2)

        pygame.draw.arc(self.screen, color, arc, 0, 3.14159, 2)

        pygame.draw.rect(self.screen, color, body, border_radius=2)

    def _draw_check(self, center, size, color, width):

        cx, cy = center

        pygame.draw.lines(
            self.screen,
            color,
            False,
            [
                (cx - size // 2, cy),
                (cx - size // 8, cy + size // 3),
                (cx + size // 2, cy - size // 3),
            ],
            width
        )

    def _draw_row(self, row, rect, selected):

        unlocked = row["unlocked"]

        row_img = self.row_done_img if unlocked else self.row_img

        if row_img is not None:

            self.screen.blit(row_img, rect.topleft)

            if selected and self.row_hl is not None:
                self.screen.blit(self.row_hl, rect.topleft)

        else:

            fill = (34, 98, 74) if unlocked else (30, 62, 118)
            border = GOLD if unlocked else RING_LOCKED

            if selected:
                fill = tuple(min(255, c + 22) for c in fill)

            pygame.draw.rect(self.screen, fill, rect, border_radius=10)
            pygame.draw.rect(
                self.screen, border, rect, width=2, border_radius=10
            )

        if selected:

            pygame.draw.rect(
                self.screen,
                GOLD_LIGHT,
                rect.inflate(-3, -3),
                width=2,
                border_radius=max(6, rect.height // 3)
            )

        # ---- icono dentro de un circulo ----
        radius = rect.height // 2 - 5

        center = (rect.left + radius + round(10 * self.sx), rect.centery)

        pygame.draw.circle(self.screen, NAVY_ICON, center, radius)

        icon = self.icons.get((row["id"], unlocked))

        if icon is not None:

            self.screen.blit(icon, icon.get_rect(center=center))

        elif unlocked:

            self._draw_check(center, radius, GOLD, max(2, radius // 5))

        else:

            self._draw_padlock(center, (150, 170, 210))

        pygame.draw.circle(
            self.screen,
            GOLD if unlocked else RING_LOCKED,
            center,
            radius,
            width=2
        )

        # ---- textos ----
        text_x = center[0] + radius + round(12 * self.sx)

        title = self._text(
            row["title"],
            self.title_size,
            (255, 255, 255) if unlocked else TEXT_LOCKED
        )

        right = rect.right - round(14 * self.sx)

        bar_w = round(150 * self.sx)

        has_bar = row["goal"] > 1 and not unlocked

        if has_bar:
            right_limit = right - bar_w - round(14 * self.sx)
        else:
            right_limit = right - round(112 * self.sx)

        desc = self._fit_text(
            row["desc"], max(40, right_limit - text_x), TEXT_DESC
        )

        self.screen.blit(title, (text_x, rect.top + round(rect.height * 0.08)))

        self.screen.blit(desc, (text_x, rect.top + round(rect.height * 0.58)))

        # ---- derecha: barra de progreso o estado ----
        if has_bar:

            bar_h = max(9, round(13 * self.sy))

            bar = pygame.Rect(0, 0, bar_w, bar_h)
            bar.midright = (right, rect.centery + round(8 * self.sy))

            pygame.draw.rect(self.screen, NAVY, bar, border_radius=bar_h // 2)

            ratio = max(0.0, min(1.0, row["progress"] / row["goal"]))

            fill_w = round(bar_w * ratio)

            if fill_w > 0:

                pygame.draw.rect(
                    self.screen,
                    GOLD,
                    (bar.left, bar.top, max(bar_h, fill_w), bar_h),
                    border_radius=bar_h // 2
                )

            pygame.draw.rect(
                self.screen,
                RING_LOCKED,
                bar,
                width=1,
                border_radius=bar_h // 2
            )

            count = self._text(
                f"{row['progress']}/{row['goal']}",
                self.small_size,
                (235, 242, 255)
            )

            self.screen.blit(
                count,
                count.get_rect(midbottom=(bar.centerx, bar.top - 1))
            )

        else:

            label = "Desbloqueado" if unlocked else "Bloqueado"
            color = GOLD if unlocked else (170, 190, 225)

            status = self._text(label, self.small_size, color)

            status_rect = status.get_rect(midright=(right, rect.centery))

            self.screen.blit(status, status_rect)

            mark = (
                status_rect.left - round(11 * self.sx),
                rect.centery
            )

            if unlocked:
                self._draw_check(
                    mark, max(8, round(11 * self.sy)), GOLD, 2
                )
            else:
                self._draw_padlock(mark, color)

    def _draw_scrollbar(self):

        thumb = self._thumb_rect()

        if thumb is None:
            return

        pygame.draw.rect(
            self.screen, NAVY, self.track, border_radius=self.track.width // 2
        )

        active = self._dragging or thumb.collidepoint(pygame.mouse.get_pos())

        pygame.draw.rect(
            self.screen,
            (150, 195, 255) if active else (110, 160, 230),
            thumb,
            border_radius=self.track.width // 2
        )

    def _draw_header(self):

        done = sum(1 for row in self.rows if row["unlocked"])
        total = max(1, len(self.rows))

        x = round(self.HEADER_POS[0] * self.sx)
        y = round(self.HEADER_POS[1] * self.sy)

        label = self._text(
            f"Logros {done}/{len(self.rows)}", self.small_size, (240, 246, 255)
        )

        self.screen.blit(label, (x, y))

        bar_h = max(6, round(8 * self.sy))

        bar = pygame.Rect(
            x,
            y + label.get_height() + 2,
            round(self.HEADER_BAR_W * self.sx),
            bar_h
        )

        pygame.draw.rect(self.screen, NAVY, bar, border_radius=bar_h // 2)

        fill_w = round(bar.width * done / total)

        if fill_w > 0:

            pygame.draw.rect(
                self.screen,
                GOLD,
                (bar.left, bar.top, max(bar_h, fill_w), bar_h),
                border_radius=bar_h // 2
            )

    def _draw_detail(self):
        """Cuadro con el logro elegido completo, en el hueco entre las manos."""

        row = self.rows[self.selected]

        unlocked = row["unlocked"]

        box = self._box(self.DETAIL_BOX)

        pad = round(10 * self.sx)

        title_size = max(18, round(30 * self.sy))
        body_size = max(14, round(22 * self.sy))

        title = self._text(
            row["title"], title_size, GOLD if unlocked else (255, 255, 255)
        )

        lines = self._wrap(row["desc"], body_size, box.width - pad * 2)[:4]

        line_h = self._font(body_size).get_linesize()

        footer_h = max(12, round(16 * self.sy))

        height = (
            pad
            + title.get_height()
            + round(4 * self.sy)
            + line_h * len(lines)
            + round(8 * self.sy)
            + footer_h
            + pad
        )

        panel = pygame.Surface((box.width, height), pygame.SRCALPHA)

        pygame.draw.rect(
            panel, (14, 28, 70, 225), panel.get_rect(), border_radius=12
        )

        pygame.draw.rect(
            panel,
            GOLD if unlocked else RING_LOCKED,
            panel.get_rect(),
            width=2,
            border_radius=12
        )

        self.screen.blit(panel, box.topleft)

        x = box.left + pad
        y = box.top + pad

        self.screen.blit(title, (x, y))

        y += title.get_height() + round(4 * self.sy)

        for line in lines:

            self.screen.blit(self._text(line, body_size, TEXT_DESC), (x, y))

            y += line_h

        y += round(8 * self.sy)

        inner_w = box.width - pad * 2

        if row["goal"] > 1 and not unlocked:

            ratio = max(0.0, min(1.0, row["progress"] / row["goal"]))

            count = self._text(
                f"{row['progress']}/{row['goal']}",
                body_size,
                (235, 242, 255)
            )

            bar = pygame.Rect(
                x, y, inner_w - count.get_width() - round(8 * self.sx), footer_h
            )

            pygame.draw.rect(self.screen, NAVY, bar, border_radius=footer_h // 2)

            fill_w = round(bar.width * ratio)

            if fill_w > 0:

                pygame.draw.rect(
                    self.screen,
                    GOLD,
                    (bar.left, bar.top, max(footer_h, fill_w), footer_h),
                    border_radius=footer_h // 2
                )

            self.screen.blit(
                count,
                count.get_rect(midright=(box.right - pad, bar.centery))
            )

        else:

            label = "Desbloqueado" if unlocked else "Bloqueado"

            status = self._text(
                label, body_size, GOLD if unlocked else (170, 190, 225)
            )

            self.screen.blit(status, (x + round(18 * self.sx), y))

            mark = (x + round(6 * self.sx), y + status.get_height() // 2)

            if unlocked:
                self._draw_check(mark, max(8, round(11 * self.sy)), GOLD, 2)
            else:
                self._draw_padlock(mark, (170, 190, 225))

    def _draw_hint(self):

        hint = self._text(
            "ESC: volver  ·  Rueda / W S: mover",
            self.small_size,
            (235, 242, 255)
        )

        rect = hint.get_rect(
            bottomright=(self.width - 18, self.height - 14)
        )

        pill = pygame.Surface(
            (rect.width + 20, rect.height + 8), pygame.SRCALPHA
        )

        pygame.draw.rect(
            pill, (10, 20, 50, 170), pill.get_rect(), border_radius=10
        )

        self.screen.blit(pill, (rect.left - 10, rect.top - 4))
        self.screen.blit(hint, rect)

    def draw(self):

        self._ease()

        self.screen.blit(self.background, (0, 0))

        previous_clip = self.screen.get_clip()

        self.screen.set_clip(self.panel)

        height = self.row_h

        for i, row in enumerate(self.rows):

            rect = pygame.Rect(
                self.panel.left + round(6 * self.sx),
                round(self.panel.top + i * self.step - self.scroll_f + 2),
                self.row_w,
                height
            )

            if rect.bottom < self.panel.top or rect.top > self.panel.bottom:
                continue

            self._draw_row(row, rect, i == self.selected)

        self.screen.set_clip(previous_clip)

        # las manos van por encima de las filas
        if self.hands is not None:
            self.screen.blit(self.hands, (0, 0))

        self._draw_scrollbar()

        self._draw_header()

        if self.hands is not None and self.rows:
            self._draw_detail()

        self._draw_hint()