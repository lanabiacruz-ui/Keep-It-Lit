import math
from pathlib import Path

import pygame

from world.items import load_icon, HUD_DIR
from world.lights import LIGHTS


TIENDA_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "tienda"
)

IMAGES = {
    "panel": "tienda_panel.png",
    "cart": "tienda_carrito.png",
    "card": "tienda_tarjeta.png",
    "card_hover": "tienda_tarjeta_hover.png",
    "tile": "tienda_icono_fondo.png",
    "badge": "tienda_badge.png",
    "row": "tienda_fila.png",
    "plus": "tienda_mas.png.png",
    "minus": "tienda_menos.png",
    "buy": "tienda_boton_comprar.png",
    "buy_hover": "tienda_boton_comprar_hover.png",
    "buy_off": "tienda_boton_comprar.off.png",
    "trash": "tienda_boton_tacho.png",
    "arrow": "tienda_flecha.png",
    "coins": "tienda_monedas.png",
    "close": "2026_10_04_05p_Kleki.png",
    "info": "tienda_info_panel.png",
}

OPTIONAL_IMAGES = ("info",)

INFO_PAD_X = 28
INFO_PAD_TOP = 24
INFO_HEADER_H = 44
INFO_PAD_BOTTOM = 34
INFO_FONT_SIZES = (23, 21, 19, 17, 15)

_raw_cache = {}


def _load_raw(key):

    if key not in _raw_cache:

        path = TIENDA_DIR / IMAGES[key]

        try:
            _raw_cache[key] = pygame.image.load(str(path)).convert_alpha()
        except (pygame.error, FileNotFoundError):
            if key not in OPTIONAL_IMAGES:
                print(f"[tienda] Falta la imagen {path.name}")
            _raw_cache[key] = None

    return _raw_cache[key]


C_PANEL = (24, 24, 27)
C_CARD = (30, 30, 34)
C_CARD_HOVER = (42, 42, 48)
C_BORDER = (63, 63, 70)
C_TEXT = (244, 244, 245)
C_MUTED = (161, 161, 170)
C_RED = (248, 113, 113)
C_BADGE = (251, 146, 60)

TILE_COLORS = {
    "fosforo": (66, 36, 10),
    "vela": (16, 40, 86),
    "antorcha": (86, 30, 12),
    "madera": (60, 36, 12),
    "cera": (44, 44, 48),
    "aceite": (16, 50, 18),
    "resina": (36, 30, 92),
    "polvora": (80, 20, 20),
    "ganzua": (14, 36, 80),
}

MAX_PER_ITEM = 99


class ShopUI:

    PANEL_W = 900
    PANEL_H = 520
    PAD = 24

    LIST_W = 570
    COLS = 3
    CARD_W = 182
    CARD_H = 104
    GAP = 12

    ROW_H = 46
    FOOT_H = 118

    def __init__(
        self, screen_size, catalog, item_defs, coins, match_duration=30.0,
        cart=None, locks=None
    ):

        # locks: {item_id: oleada necesaria} de lo que sigue bloqueado
        self.locks = dict(locks or {})

        self.sw, self.sh = screen_size
        self.catalog = catalog
        self.defs = item_defs
        self.coins = int(coins)
        self.match_duration = float(match_duration)

        self.info_id = None

        self.prices = {
            it["id"]: it["precio"]
            for sec in catalog
            for it in sec["items"]
        }

        self.cart = {
            item_id: min(MAX_PER_ITEM, int(qty))
            for item_id, qty in (cart or {}).items()
            if item_id in self.prices and int(qty) > 0
            and item_id not in self.locks
        }

        self.message = ""
        self.message_timer = 0.0

        self.scroll = 0.0
        self.cart_scroll = 0.0

        self.title_font = pygame.font.Font(None, 46)
        self.section_font = pygame.font.Font(None, 26)
        self.name_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 23)
        self.tiny_font = pygame.font.Font(None, 21)
        self.button_font = pygame.font.Font(None, 30)
        self._font_cache = {}

        self.panel = pygame.Rect(0, 0, self.PANEL_W, self.PANEL_H)
        self.panel.center = (self.sw // 2, self.sh // 2)

        top = self.panel.y + 84

        self.list_rect = pygame.Rect(
            self.panel.x + self.PAD,
            top,
            self.LIST_W,
            self.panel.bottom - self.PAD - 24 - top
        )

        cart_x = self.list_rect.right + 24

        self.cart_rect = pygame.Rect(
            cart_x,
            top,
            self.panel.right - self.PAD - cart_x,
            self.list_rect.height
        )

        self.rows_rect = pygame.Rect(
            self.cart_rect.x + 8,
            self.cart_rect.y + 50,
            self.cart_rect.width - 16,
            self.cart_rect.height - 50 - self.FOOT_H
        )

        foot_top = self.cart_rect.bottom - self.FOOT_H

        self.total_pos_y = foot_top + 14

        self.trash_rect = pygame.Rect(0, 0, 40, 40)
        self.trash_rect.bottomright = (
            self.cart_rect.right - 16,
            self.cart_rect.bottom - 16
        )

        self.buy_rect = pygame.Rect(
            self.cart_rect.x + 16,
            self.trash_rect.y,
            self.trash_rect.x - 8 - (self.cart_rect.x + 16),
            40
        )

        self.coin_pill = pygame.Rect(
            self.panel.right - self.PAD - 112,
            self.panel.y + self.PAD,
            112,
            40
        )

        self.close_rect = pygame.Rect(
            self.coin_pill.x - 12 - 36,
            self.coin_pill.y + 2,
            36,
            36
        )

        self.arrow_center = (
            self.list_rect.centerx,
            self.list_rect.bottom - 22
        )

        self.dim = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 175))

        self._icons = {}
        self._imgs = {}

        self._layout()


    def item_name(self, item_id):

        data = self.defs.get(item_id, {})

        return data.get("nombre", item_id.capitalize())

    def info_lines(self, item_id):

        data = self.defs.get(item_id, {})

        lines = []

        if data.get("descripcion"):
            lines.append(data["descripcion"])

        stats = LIGHTS.get(item_id)

        if stats is None:
            return lines

        base = LIGHTS["fosforo"]["radio"]

        radio = f"Radio de luz: {stats['radio']}"

        if stats["radio"] != base:
            radio += f" (x{stats['radio'] / base:g} que el fósforo)"

        duracion = self.match_duration / stats["consumo"]

        lines.append("")
        lines.append(radio)
        lines.append(f"Duración: {duracion:g} segundos")

        if stats.get("dano", 1) > 1:
            lines.append(f"Fuerza: {stats['dano']:g} de daño por golpe")

        if stats.get("furia_cada", 0) > 0:
            lines.append(
                f"Furia: cada {stats['furia_cada']:g} s entra en furia "
                f"durante {stats['furia_duracion']:g} s y pega "
                f"{stats['furia_velocidad']:g} veces más rápido"
            )
        else:
            lines.append("Furia: no tiene")

        return lines

    def total(self):

        return sum(self.prices[i] * q for i, q in self.cart.items())

    def _icon(self, item_id, size):

        key = (item_id, size)

        if key not in self._icons:

            if item_id == "fosforo":

                path = HUD_DIR / "item_fosforo.png"

                icon = (
                    pygame.image.load(str(path)).convert_alpha()
                    if path.exists()
                    else load_icon(item_id)
                )

            else:

                icon = load_icon(item_id)

            if icon is not None:
                icon = pygame.transform.smoothscale(icon, (size, size))

            self._icons[key] = icon

        return self._icons[key]

    def _img(self, key, size=None, shade=0):

        cache_key = (key, size, shade)

        if cache_key not in self._imgs:

            img = _load_raw(key)

            if img is not None:

                if size is not None and img.get_size() != tuple(size):
                    img = pygame.transform.smoothscale(img, size)

                if shade > 0:

                    img = img.copy()
                    img.fill(
                        (shade, shade, shade, 0),
                        special_flags=pygame.BLEND_RGB_ADD
                    )

                elif shade < 0:

                    img = img.copy()
                    img.fill(
                        (-shade, -shade, -shade, 0),
                        special_flags=pygame.BLEND_RGB_SUB
                    )

            self._imgs[cache_key] = img

        return self._imgs[cache_key]

    def _flash(self, text):

        self.message = text
        self.message_timer = 2.0


    def _layout(self):

        self.labels = []
        self.cards = []

        y = 0

        for sec in self.catalog:

            self.labels.append((y, sec["nombre"]))

            y += 30

            for i, it in enumerate(sec["items"]):

                col = i % self.COLS
                row = i // self.COLS

                rect = pygame.Rect(
                    col * (self.CARD_W + self.GAP),
                    y + row * (self.CARD_H + self.GAP),
                    self.CARD_W,
                    self.CARD_H
                )

                self.cards.append((rect, it["id"]))

            rows = math.ceil(len(sec["items"]) / self.COLS)

            y += rows * (self.CARD_H + self.GAP) + 6

        self.content_h = y

        self.max_scroll = max(0, self.content_h - self.list_rect.height)

    def _cart_rows(self):

        rows = []

        for n, (item_id, qty) in enumerate(self.cart.items()):

            y = self.rows_rect.y + n * self.ROW_H - int(self.cart_scroll)

            row = pygame.Rect(
                self.rows_rect.x, y, self.rows_rect.width, self.ROW_H - 4
            )

            plus = pygame.Rect(row.right - 26, row.y + 12, 20, 20)
            minus = pygame.Rect(plus.x - 26, row.y + 12, 20, 20)

            rows.append((item_id, qty, row, minus, plus))

        return rows

    def _cart_max_scroll(self):

        return max(
            0, len(self.cart) * self.ROW_H - self.rows_rect.height
        )


    def add(self, item_id, amount=1):

        if item_id in self.locks:

            self._flash(
                f"Se desbloquea en la oleada {self.locks[item_id]}"
            )

            return

        current = self.cart.get(item_id, 0)

        self.cart[item_id] = min(MAX_PER_ITEM, current + amount)

    def remove(self, item_id, amount=1):

        if item_id not in self.cart:
            return

        self.cart[item_id] -= amount

        if self.cart[item_id] <= 0:
            del self.cart[item_id]

        self.cart_scroll = min(self.cart_scroll, self._cart_max_scroll())

    def clear(self):

        self.cart.clear()
        self.cart_scroll = 0.0


    def _card_at(self, pos):

        if not self.list_rect.collidepoint(pos):
            return None

        x = pos[0] - self.list_rect.x
        y = pos[1] - self.list_rect.y + int(self.scroll)

        for rect, item_id in self.cards:

            if rect.collidepoint(x, y):
                return item_id

        return None

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if self.info_id is not None:

                self.info_id = None

                return None

            if event.key in (pygame.K_ESCAPE, pygame.K_f):
                return "close"

            return None

        if event.type == pygame.MOUSEWHEEL:

            pos = pygame.mouse.get_pos()

            if self.cart_rect.collidepoint(pos):

                self.cart_scroll = max(
                    0,
                    min(
                        self._cart_max_scroll(),
                        self.cart_scroll - event.y * 40
                    )
                )

            else:

                self.scroll = max(
                    0,
                    min(self.max_scroll, self.scroll - event.y * 50)
                )

            return None

        if event.type != pygame.MOUSEBUTTONDOWN:
            return None

        if event.button not in (1, 2, 3):
            return None

        pos = event.pos

        if event.button == 2:

            card = self._card_at(pos)

            self.info_id = None if card == self.info_id else card

            return None

        if self.info_id is not None:

            self.info_id = None

            return None

        card = self._card_at(pos)

        if card is not None:

            if event.button == 1:
                self.add(card)
            else:
                self.remove(card)

            return None

        if event.button != 1:
            return None

        if self.close_rect.collidepoint(pos):
            return "close"

        if (
            self.scroll < self.max_scroll - 1
            and math.dist(pos, self.arrow_center) <= 17
        ):

            self.scroll = self.max_scroll

            return None

        if self.rows_rect.collidepoint(pos):

            for item_id, _, _, minus, plus in self._cart_rows():

                if minus.collidepoint(pos):
                    self.remove(item_id)
                    return None

                if plus.collidepoint(pos):
                    self.add(item_id)
                    return None

            return None

        if self.trash_rect.collidepoint(pos):

            self.clear()

            return None

        if self.buy_rect.collidepoint(pos):

            total = self.total()

            if total <= 0:
                return None

            if total > self.coins:

                self._flash("No te alcanzan las monedas")

                return None

            return ("buy", dict(self.cart))

        return None

    def update(self, dt):

        if self.message_timer > 0:
            self.message_timer -= dt


    def _text(self, screen, font, text, color, **anchor):

        img = font.render(text, True, color)

        screen.blit(img, img.get_rect(**anchor))

        return img

    def _font_for(self, size):

        font = self._font_cache.get(size)

        if font is None:
            font = pygame.font.Font(None, size)
            self._font_cache[size] = font

        return font

    def _fit_font(self, text, max_w, size, min_size=14):

        while size > min_size:

            font = self._font_for(size)

            if font.size(text)[0] <= max_w:
                return font

            size -= 1

        return self._font_for(min_size)

    @staticmethod
    def _wrap(font, text, max_width):

        lines = []
        line = ""

        for word in text.split():

            while font.size(word)[0] > max_width and len(word) > 1:

                n = len(word) - 1

                while n > 1 and font.size(word[:n] + "-")[0] > max_width:
                    n -= 1

                if line:
                    lines.append(line)
                    line = ""

                lines.append(word[:n] + "-")
                word = word[n:]

            test = f"{line} {word}".strip()

            if line and font.size(test)[0] > max_width:
                lines.append(line)
                line = word
            else:
                line = test

        if line:
            lines.append(line)

        return lines

    def _draw_coin_amount(
        self, screen, amount, color, midright, max_w=90
    ):

        text = self.name_font.render(str(amount), True, color)

        if text.get_width() > max_w:

            text = pygame.transform.smoothscale(
                text,
                (
                    max_w,
                    max(1, int(text.get_height() * max_w / text.get_width()))
                )
            )

        text_rect = text.get_rect(midright=midright)

        screen.blit(text, text_rect)

        coin = self._icon("moneda", 20)

        if coin is not None:

            screen.blit(
                coin,
                coin.get_rect(midright=(text_rect.left - 6, midright[1]))
            )

    def _draw_card(self, screen, rect, item_id, hover):

        card_img = self._img(
            "card_hover" if hover else "card", rect.size
        )

        if card_img is not None:

            screen.blit(card_img, rect.topleft)

        else:

            pygame.draw.rect(
                screen, C_CARD_HOVER if hover else C_CARD, rect,
                border_radius=10
            )

            pygame.draw.rect(
                screen, C_BORDER, rect, width=1, border_radius=10
            )

        tile = pygame.Rect(0, 0, 46, 46)
        tile.midtop = (rect.centerx, rect.y + 10)

        tile_img = self._img("tile", tile.size)

        if tile_img is not None:

            screen.blit(tile_img, tile.topleft)

        else:

            pygame.draw.rect(
                screen, TILE_COLORS.get(item_id, (44, 44, 50)), tile,
                border_radius=8
            )

        icon = self._icon(item_id, 34)

        if icon is not None:
            screen.blit(icon, icon.get_rect(center=tile.center))

        locked_wave = self.locks.get(item_id)

        if locked_wave is not None:

            shade = pygame.Surface(rect.size, pygame.SRCALPHA)
            shade.fill((0, 0, 0, 150))

            screen.blit(shade, rect.topleft)

        card_name = self.item_name(item_id)

        self._text(
            screen,
            self._fit_font(card_name, rect.w - 16, 28),
            card_name, C_TEXT,
            midtop=(rect.centerx, tile.bottom + 6)
        )

        self._text(
            screen, self.tiny_font,
            (
                f"Oleada {locked_wave}"
                if locked_wave is not None
                else f"{self.prices[item_id]} monedas"
            ),
            C_MUTED,
            midtop=(rect.centerx, tile.bottom + 28)
        )

        qty = self.cart.get(item_id, 0)

        if qty > 0:

            badge_img = self._img("badge")

            if badge_img is not None:

                badge = badge_img.get_rect(
                    topright=(rect.right - 6, rect.y + 6)
                )

                screen.blit(badge_img, badge.topleft)

            else:

                badge = pygame.Rect(0, 0, 26, 22)
                badge.topright = (rect.right - 6, rect.y + 6)

                pygame.draw.rect(screen, C_BADGE, badge, border_radius=11)

            self._text(
                screen, self.tiny_font, str(qty), (30, 18, 8),
                center=badge.center
            )

    def _draw_list(self, screen, mouse):

        screen.set_clip(self.list_rect)

        oy = self.list_rect.y - int(self.scroll)

        for y, name in self.labels:

            self._text(
                screen, self.section_font, name, C_MUTED,
                topleft=(self.list_rect.x + 2, oy + y + 4)
            )

        hover_id = self._card_at(mouse)

        for rect, item_id in self.cards:

            self._draw_card(
                screen,
                rect.move(self.list_rect.x, oy),
                item_id,
                item_id == hover_id
            )

        screen.set_clip(None)

        if self.scroll < self.max_scroll - 1:

            arrow_img = self._img("arrow", (34, 34))

            if arrow_img is not None:

                screen.blit(
                    arrow_img,
                    arrow_img.get_rect(center=self.arrow_center)
                )

            else:

                pygame.draw.circle(
                    screen, C_CARD_HOVER, self.arrow_center, 17
                )

                pygame.draw.circle(
                    screen, C_BORDER, self.arrow_center, 17, 1
                )

                ax, ay = self.arrow_center

                pygame.draw.lines(
                    screen, C_TEXT, False,
                    [(ax - 6, ay - 3), (ax, ay + 4), (ax + 6, ay - 3)], 2
                )

                pygame.draw.line(
                    screen, C_TEXT, (ax, ay - 6), (ax, ay + 3), 2
                )

    def _draw_cart_icon(self, screen, x, y):

        pygame.draw.lines(
            screen, C_TEXT, False,
            [(x, y + 2), (x + 4, y + 2), (x + 7, y + 13), (x + 19, y + 13),
             (x + 21, y + 5), (x + 6, y + 5)], 2
        )

        pygame.draw.circle(screen, C_TEXT, (x + 9, y + 18), 2)
        pygame.draw.circle(screen, C_TEXT, (x + 17, y + 18), 2)

    def _draw_trash_icon(self, screen, rect, color):

        cx, cy = rect.center

        pygame.draw.line(
            screen, color, (cx - 8, cy - 7), (cx + 8, cy - 7), 2
        )

        pygame.draw.line(
            screen, color, (cx - 3, cy - 10), (cx + 3, cy - 10), 2
        )

        pygame.draw.lines(
            screen, color, False,
            [(cx - 6, cy - 5), (cx - 5, cy + 9), (cx + 5, cy + 9),
             (cx + 6, cy - 5)], 2
        )

        pygame.draw.line(
            screen, color, (cx - 2, cy - 2), (cx - 2, cy + 6), 1
        )

        pygame.draw.line(
            screen, color, (cx + 2, cy - 2), (cx + 2, cy + 6), 1
        )

    def _draw_cart(self, screen, mouse):

        cart_img = self._img("cart", self.cart_rect.size)

        if cart_img is not None:

            screen.blit(cart_img, self.cart_rect.topleft)

        else:

            pygame.draw.rect(
                screen, C_CARD, self.cart_rect, border_radius=12
            )

            pygame.draw.rect(
                screen, C_BORDER, self.cart_rect, width=1, border_radius=12
            )

        self._draw_cart_icon(
            screen, self.cart_rect.x + 16, self.cart_rect.y + 14
        )

        self._text(
            screen, self.name_font, "Carrito", C_TEXT,
            midleft=(self.cart_rect.x + 46, self.cart_rect.y + 25)
        )

        if not self.cart:

            lines = self._wrap(
                self.small_font,
                "Tocá un producto para agregarlo.",
                self.rows_rect.width - 20
            )

            for n, line in enumerate(lines):

                self._text(
                    screen, self.small_font, line, C_MUTED,
                    midtop=(
                        self.rows_rect.centerx,
                        self.rows_rect.y + 24 + n * 22
                    )
                )

        else:

            screen.set_clip(self.rows_rect)

            for item_id, qty, row, minus, plus in self._cart_rows():

                row_img = self._img("row", row.size)

                if row_img is not None:
                    screen.blit(row_img, row.topleft)

                icon = self._icon(item_id, 28)

                if icon is not None:
                    screen.blit(
                        icon, icon.get_rect(midleft=(row.x + 4, row.centery))
                    )

                row_name = self.item_name(item_id)

                self._text(
                    screen,
                    self._fit_font(row_name, row.w - 96, 23),
                    row_name, C_TEXT,
                    topleft=(row.x + 40, row.y + 4)
                )

                price = self.prices[item_id]

                self._text(
                    screen, self.tiny_font,
                    f"{qty} × {price} = {qty * price}", C_MUTED,
                    topleft=(row.x + 40, row.y + 22)
                )

                for rect, symbol, key in (
                    (minus, "-", "minus"), (plus, "+", "plus")
                ):

                    hover = rect.collidepoint(mouse)

                    btn_img = self._img(
                        key, rect.size, shade=40 if hover else 0
                    )

                    if btn_img is not None:

                        screen.blit(btn_img, rect.topleft)

                        continue

                    pygame.draw.rect(
                        screen,
                        C_CARD_HOVER if hover else C_PANEL,
                        rect,
                        border_radius=5
                    )

                    pygame.draw.rect(
                        screen, C_BORDER, rect, width=1, border_radius=5
                    )

                    self._text(
                        screen, self.small_font, symbol, C_TEXT,
                        center=rect.center
                    )

            screen.set_clip(None)

        foot_top = self.cart_rect.bottom - self.FOOT_H

        pygame.draw.line(
            screen, C_BORDER,
            (self.cart_rect.x + 12, foot_top),
            (self.cart_rect.right - 12, foot_top)
        )

        total = self.total()

        self._text(
            screen, self.small_font, "Total", C_MUTED,
            midleft=(self.cart_rect.x + 16, self.total_pos_y + 10)
        )

        self._draw_coin_amount(
            screen,
            total,
            C_RED if total > self.coins else C_TEXT,
            (self.cart_rect.right - 16, self.total_pos_y + 10)
        )

        if self.message_timer > 0:

            self._text(
                screen, self.tiny_font, self.message, C_RED,
                midtop=(self.cart_rect.centerx, self.total_pos_y + 32)
            )

        enabled = total > 0

        hover = enabled and self.buy_rect.collidepoint(mouse)

        if not enabled:
            buy_key = "buy_off"
        elif hover:
            buy_key = "buy_hover"
        else:
            buy_key = "buy"

        buy_img = self._img(buy_key, self.buy_rect.size)

        if buy_img is not None:

            screen.blit(buy_img, self.buy_rect.topleft)

        else:

            pygame.draw.rect(
                screen,
                C_CARD_HOVER if hover else C_PANEL,
                self.buy_rect,
                border_radius=10
            )

            pygame.draw.rect(
                screen,
                C_TEXT if enabled else C_BORDER,
                self.buy_rect,
                width=1,
                border_radius=10
            )

        self._text(
            screen, self.button_font, "Comprar",
            C_TEXT if enabled else C_MUTED,
            center=self.buy_rect.center
        )

        hover = self.trash_rect.collidepoint(mouse)

        if not self.cart:
            shade = -70
        elif hover:
            shade = 40
        else:
            shade = 0

        trash_img = self._img("trash", self.trash_rect.size, shade=shade)

        if trash_img is not None:

            screen.blit(trash_img, self.trash_rect.topleft)

        else:

            pygame.draw.rect(
                screen,
                C_CARD_HOVER if hover else C_PANEL,
                self.trash_rect,
                border_radius=10
            )

            pygame.draw.rect(
                screen, C_BORDER, self.trash_rect, width=1, border_radius=10
            )

            self._draw_trash_icon(
                screen,
                self.trash_rect,
                C_TEXT if self.cart else C_MUTED
            )

    def _info_body(self, item_id, max_w, max_h=None):

        raws = self.info_lines(item_id)

        for size in INFO_FONT_SIZES:

            font = self._font_for(size)
            body = []

            for raw in raws:

                if raw == "":
                    body.append("")
                    continue

                body.extend(self._wrap(font, raw, max_w))

            line_h = font.get_linesize()

            if max_h is None or len(body) * line_h <= max_h:
                break

        return font, body, line_h

    def _draw_info(self, screen, item_id):

        info_img = _load_raw("info")

        if info_img is not None:

            box = info_img.get_rect(center=self.panel.center)
            box.clamp_ip(screen.get_rect())

            pad_x = INFO_PAD_X
            top = INFO_PAD_TOP

            font, body, line_h = self._info_body(
                item_id,
                box.w - pad_x * 2,
                box.h - INFO_PAD_TOP - INFO_HEADER_H - INFO_PAD_BOTTOM,
            )

            body_y = box.y + INFO_PAD_TOP + INFO_HEADER_H
            foot_y = box.bottom - 10

        else:

            pad_x = 18
            top = 18

            width = 420

            font, body, line_h = self._info_body(item_id, width - pad_x * 2)

            height = pad_x * 2 + 36 + len(body) * line_h + 22

            box = pygame.Rect(0, 0, width, height)
            box.center = self.panel.center
            box.clamp_ip(screen.get_rect())

            body_y = box.y + top + 44
            foot_y = box.bottom - 8

        shade = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 120))
        screen.blit(shade, (0, 0))

        if info_img is not None:

            screen.blit(info_img, box.topleft)

        else:

            pygame.draw.rect(screen, C_PANEL, box, border_radius=14)
            pygame.draw.rect(screen, C_BADGE, box, width=2, border_radius=14)

        icon = self._icon(item_id, 34)

        if icon is not None:
            screen.blit(icon, (box.x + pad_x, box.y + top - 2))

        name = self.item_name(item_id)
        name_w = box.w - pad_x * 2 - 44

        self._text(
            screen, self._fit_font(name, name_w, 28), name, C_TEXT,
            midleft=(box.x + pad_x + 44, box.y + top + 15)
        )

        y = body_y

        for line in body:

            if line:
                self._text(
                    screen, font, line, C_TEXT,
                    topleft=(box.x + pad_x, y)
                )

            y += line_h

        self._text(
            screen, self.tiny_font, "Click para cerrar", C_MUTED,
            midbottom=(box.centerx, foot_y)
        )

    def draw(self, screen):

        mouse = pygame.mouse.get_pos()

        screen.blit(self.dim, (0, 0))

        panel_img = self._img("panel", self.panel.size)

        if panel_img is not None:

            screen.blit(panel_img, self.panel.topleft)

        else:

            pygame.draw.rect(
                screen, C_PANEL, self.panel, border_radius=16
            )

            pygame.draw.rect(
                screen, C_BORDER, self.panel, width=1, border_radius=16
            )

        self._text(
            screen, self.title_font, "Tienda", C_TEXT,
            midleft=(self.panel.x + self.PAD, self.coin_pill.centery)
        )

        hover = self.close_rect.collidepoint(mouse)

        close_img = self._img(
            "close", self.close_rect.size, shade=40 if hover else 0
        )

        if close_img is not None:

            screen.blit(close_img, self.close_rect.topleft)

        else:

            pygame.draw.rect(
                screen,
                C_CARD_HOVER if hover else C_CARD,
                self.close_rect,
                border_radius=10
            )

            pygame.draw.rect(
                screen, C_BORDER, self.close_rect, width=1, border_radius=10
            )

            cx, cy = self.close_rect.center

            pygame.draw.line(
                screen, C_TEXT, (cx - 6, cy - 6), (cx + 6, cy + 6), 2
            )

            pygame.draw.line(
                screen, C_TEXT, (cx - 6, cy + 6), (cx + 6, cy - 6), 2
            )

        coins_img = self._img("coins", self.coin_pill.size)

        if coins_img is not None:

            screen.blit(coins_img, self.coin_pill.topleft)

        else:

            pygame.draw.rect(
                screen, C_CARD, self.coin_pill, border_radius=18
            )

            pygame.draw.rect(
                screen, C_BORDER, self.coin_pill, width=1, border_radius=18
            )

        self._draw_coin_amount(
            screen,
            self.coins,
            C_TEXT,
            (self.coin_pill.right - 14, self.coin_pill.centery),
            max_w=58
        )

        self._draw_list(screen, mouse)

        self._draw_cart(screen, mouse)

        if self.info_id is not None:
            self._draw_info(screen, self.info_id)

        help_text = (
            "Click: agregar  ·  Click derecho: quitar  ·  "
            "Click en la rueda: info  ·  Rueda: bajar  ·  E / Esc: cerrar"
        )

        self._text(
            screen,
            self._fit_font(help_text, self.panel.w - self.PAD * 2, 21),
            help_text,
            C_MUTED,
            midbottom=(self.panel.centerx, self.panel.bottom - 8)
        )