import math

import pygame
from pathlib import Path

from world.items import load_icon

HUD_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
)


GIVEUP_IMAGE = "btn_rendirse.png"
GIVEUP_IMAGE_HOVER = "btn_rendirse_hover.png"
GIVEUP_GAP = 50


def format_coins(amount):

    amount = int(amount)

    if amount < 10000:
        return str(amount)

    if amount < 999950:
        value, suffix = amount / 1000, "k"
    else:
        value, suffix = amount / 1000000, "M"

    text = f"{value:.1f}".rstrip("0").rstrip(".")

    return text + suffix


class Hud:

    SLOTS = 4

    VIDA_BBOX = (7, 7, 248, 41)
    ESCUDO_BBOX = (2, 6, 185, 34)

    COIN_TEXT_CENTER = (78, 30)

    COIN_TEXT_MAX_W = 44

    def __init__(
        self,
        screen_size,
        scale=0.6,
        equipped_scale=0.75,
        bar_scale=1.0,
        bars_scale=0.7
    ):

        w, h = screen_size

        def load(name):
            return pygame.image.load(
                str(HUD_DIR / name)
            ).convert_alpha()

        def scaled(img, factor):
            return pygame.transform.smoothscale(
                img,
                (
                    int(img.get_width() * factor),
                    int(img.get_height() * factor)
                )
            )

        self.bar = scaled(load("hud_hotbar.png"), scale)
        self.slot = scaled(load("hud_slot.png"), scale)
        self.slot_select = scaled(load("hud_slot_select.png"), scale)

        self.equipped_frame = scaled(
            load("hud_item_equipado.png"),
            equipped_scale
        )

        self.equipped_icons = {
            "fosforo": scaled(load("icon_fosforo.png"), equipped_scale),
            "vela": scaled(load("icon_vela_equipado.png"), equipped_scale),
            "antorcha": scaled(
                load("icon_antorcha_equipado.png"),
                equipped_scale
            )
        }

        self.equipped_frame_select = scaled(
            load("hud_item_select.png"),
            equipped_scale
        )

        self.equipped_icons_select = {
            "fosforo": scaled(
                load("icon_fosforo_select.png"),
                equipped_scale
            ),
            "vela": scaled(
                load("icon_vela_equipado_select.png"),
                equipped_scale
            ),
            "antorcha": scaled(
                load("icon_antorcha_equipado_select.png"),
                equipped_scale
            )
        }

        self.equipped = None

        self.items = [None] * self.SLOTS

        self.counts = [0] * self.SLOTS
        self.selected = None

        slot_size = self.slot.get_width()
        gap = 6
        total = self.SLOTS * slot_size + (self.SLOTS - 1) * gap

        self.bar = pygame.transform.smoothscale(
            self.bar,
            (total + 12, self.bar.get_height())
        )

        self.bar_rect = self.bar.get_rect(
            midbottom=(w // 2, h - 12)
        )

        x0 = self.bar_rect.centerx - total // 2
        y = self.bar_rect.centery - slot_size // 2

        self.slot_pos = [
            (x0 + i * (slot_size + gap), y)
            for i in range(self.SLOTS)
        ]

        self.equipped_rect = self.equipped_frame.get_rect(
            midright=(self.bar_rect.left - 12, self.bar_rect.centery)
        )

        self.attack_panels = {
            "golpe": scaled(load("hud_antorcha_golpe.png"), 0.75),
            "fuego": scaled(load("hud_antorcha_fuego.png"), 0.75),
        }

        self.attack_panel_rect = self.attack_panels["golpe"].get_rect(
            bottomleft=(self.bar_rect.right + 12, self.bar_rect.bottom)
        )


        self.vida_frame = scaled(load("hud_barra2.png"), bars_scale)
        self.vida_fill = scaled(load("hud_vida_relleno.png"), bars_scale)

        self.escudo_frame = scaled(load("hud_barra1.png"), bars_scale)
        self.escudo_fill = scaled(load("hud_escudo_relleno.png"), bars_scale)

        self.vida_bbox = tuple(
            round(v * bars_scale) for v in self.VIDA_BBOX
        )

        self.escudo_bbox = tuple(
            round(v * bars_scale) for v in self.ESCUDO_BBOX
        )

        margin = 18

        gap_bars = 6
        bars_h = (
            self.vida_frame.get_height()
            + gap_bars
            + self.escudo_frame.get_height()
        )

        bars_left = (
            self.equipped_rect.left
            - 14
            - max(
                self.vida_frame.get_width(),
                self.escudo_frame.get_width()
            )
        )

        bars_top = self.equipped_rect.centery - bars_h // 2

        self.vida_pos = (bars_left, bars_top)

        self.escudo_pos = (
            bars_left,
            bars_top + self.vida_frame.get_height() + gap_bars
        )

        self.countdown_font = pygame.font.Font(None, 90)

        giveup = self._load_optional(GIVEUP_IMAGE)
        giveup_hover = self._load_optional(GIVEUP_IMAGE_HOVER)

        if giveup is None:
            giveup = self._fallback_giveup(False)
            giveup_hover = self._fallback_giveup(True)

        elif giveup_hover is None:
            giveup_hover = giveup.copy()
            giveup_hover.fill(
                (45, 45, 45, 0),
                special_flags=pygame.BLEND_RGB_ADD
            )

        self.giveup_img = giveup
        self.giveup_img_hover = giveup_hover

        self.giveup_rect = None

        self.tip_title_font = pygame.font.Font(None, 26)
        self.tip_font = pygame.font.Font(None, 22)
        self.msg_font = pygame.font.Font(None, 28)
        self.count_font = pygame.font.Font(None, 26)

        self._slot_icons = {}

        self.coin_scale = bar_scale

        self.coin_icon = scaled(load("hud_monedas.png"), bar_scale)

        menu_img = load("menu.png")

        menu_size = self.coin_icon.get_height()

        self.menu_icon = pygame.transform.smoothscale(
            menu_img,
            (menu_size, menu_size)
        )

        self.menu_icon_hover = self.menu_icon.copy()
        self.menu_icon_hover.fill(
            (45, 45, 45, 0),
            special_flags=pygame.BLEND_RGB_ADD
        )

        self.menu_rect = self.menu_icon.get_rect(
            topright=(w - margin, margin)
        )

        self.menu_button_rect = self.menu_rect

        self.coin_rect = self.coin_icon.get_rect(
            topright=(self.menu_rect.left - 6, margin)
        )

        self.coin_font = pygame.font.Font(None, 32)

        self.gain_font = None

        self.coin_text_offset = (
            round(self.COIN_TEXT_CENTER[0] * bar_scale),
            round(self.COIN_TEXT_CENTER[1] * bar_scale)
        )

    def equip(self, name):
        self.equipped = name


    @staticmethod
    def _load_optional(name):

        path = HUD_DIR / name

        if not path.exists():
            return None

        return pygame.image.load(str(path)).convert_alpha()

    @staticmethod
    def _fallback_giveup(hover):

        surf = pygame.Surface((180, 64), pygame.SRCALPHA)

        color = (150, 60, 50) if hover else (110, 40, 36)

        pygame.draw.rect(surf, color, surf.get_rect(), border_radius=14)
        pygame.draw.rect(
            surf, (235, 225, 215), surf.get_rect(), 3, border_radius=14
        )

        font = pygame.font.Font(None, 34)
        label = font.render("Terminar", True, (255, 255, 255))

        surf.blit(label, label.get_rect(center=surf.get_rect().center))

        return surf

    def slot_rect(self, i):

        x, y = self.slot_pos[i]

        return pygame.Rect(x, y, *self.slot.get_size())

    def slot_at(self, pos):

        for i in range(self.SLOTS):
            if self.slot_rect(i).collidepoint(pos):
                return i

        return None

    def _slot_icon(self, item_id):

        if item_id not in self._slot_icons:

            icon = load_icon(item_id)

            if icon is not None:

                size = int(self.slot.get_width() * 0.78)

                icon = pygame.transform.smoothscale(icon, (size, size))

            self._slot_icons[item_id] = icon

        return self._slot_icons[item_id]

    @staticmethod
    def _wrap(font, text, max_width):

        lines = []
        line = ""

        for word in text.split():

            test = f"{line} {word}".strip()

            if line and font.size(test)[0] > max_width:
                lines.append(line)
                line = word
            else:
                line = test

        if line:
            lines.append(line)

        return lines

    def draw_overlay(self, screen, item_defs, mouse_pos, holding, message):

        if holding:

            i = self.slot_at(mouse_pos)

            item_id = self.items[i] if i is not None else None

            if item_id in item_defs:

                d = item_defs[item_id]

                title = self.tip_title_font.render(
                    d.get("nombre", item_id), True, (40, 46, 56)
                )

                lines = [
                    self.tip_font.render(t, True, (55, 62, 74))
                    for t in self._wrap(
                        self.tip_font, d.get("descripcion", ""), 230
                    )
                ]

                pad = 10
                width = max(
                    [title.get_width()] + [l.get_width() for l in lines]
                ) + pad * 2
                height = (
                    title.get_height() + 4
                    + sum(l.get_height() for l in lines)
                    + pad * 2
                )

                rect = pygame.Rect(0, 0, width, height)
                rect.midbottom = (
                    self.slot_rect(i).centerx,
                    self.bar_rect.top - 8
                )
                rect.clamp_ip(screen.get_rect())

                pygame.draw.rect(
                    screen, (150, 160, 168), rect, border_radius=10
                )
                pygame.draw.rect(
                    screen, (70, 78, 90), rect, width=3, border_radius=10
                )

                y = rect.top + pad
                screen.blit(title, (rect.left + pad, y))
                y += title.get_height() + 4

                for l in lines:
                    screen.blit(l, (rect.left + pad, y))
                    y += l.get_height()

        if message:

            self._draw_message(screen, message)

    def _draw_message(self, screen, message):

        max_w = screen.get_width() - 40

        lines = [message]
        font = self.msg_font

        cache = self.__dict__.setdefault("_msg_fonts", {})

        for size in (28, 26, 24, 22):

            font = cache.get(size)

            if font is None:
                font = cache[size] = pygame.font.Font(None, size)

            if font.size(message)[0] <= max_w:
                lines = [message]
                break

        else:

            lines = []
            cur = ""

            for word in message.split():

                test = f"{cur} {word}".strip()

                if cur and font.size(test)[0] > max_w:
                    lines.append(cur)
                    cur = word
                else:
                    cur = test

            if cur:
                lines.append(cur)

        y = self.bar_rect.top - 14

        for line in reversed(lines):

            text = font.render(line, True, (255, 255, 255))
            shadow = font.render(line, True, (0, 0, 0))

            pos = text.get_rect(midbottom=(screen.get_width() // 2, y))

            screen.blit(shadow, pos.move(2, 2))
            screen.blit(text, pos)

            y -= font.get_linesize()

    def _draw_bar(self, screen, frame, fill, pos, pct, bbox):

        screen.blit(frame, pos)

        pct = max(0.0, min(1.0, pct))

        if pct <= 0:
            return

        x1, y1, x2, y2 = bbox

        width = x2 if pct >= 1 else round(
            x1 + (x2 - x1) * pct
        )

        width = max(1, min(width, fill.get_width()))

        crop = fill.subsurface(
            pygame.Rect(0, 0, width, fill.get_height())
        )

        screen.blit(crop, pos)

    def draw(
        self,
        screen,
        vida=1.0,
        escudo=0.0,
        countdown=None,
        coins=0,
        equipped_selected=False,
        coin_gain=0,
        coin_gain_alpha=1.0,
        attack_mode=None
    ):

        self._draw_bar(
            screen,
            self.vida_frame,
            self.vida_fill,
            self.vida_pos,
            vida,
            self.vida_bbox
        )

        self._draw_bar(
            screen,
            self.escudo_frame,
            self.escudo_fill,
            self.escudo_pos,
            escudo,
            self.escudo_bbox
        )

        hover = self.menu_rect.collidepoint(pygame.mouse.get_pos())

        screen.blit(
            self.menu_icon_hover if hover else self.menu_icon,
            self.menu_rect
        )

        screen.blit(self.coin_icon, self.coin_rect)

        coin_text = self.coin_font.render(
            format_coins(coins),
            True,
            (255, 255, 255)
        )

        max_w = round(self.COIN_TEXT_MAX_W * self.coin_scale)

        if coin_text.get_width() > max_w:

            factor = max_w / coin_text.get_width()

            coin_text = pygame.transform.smoothscale(
                coin_text,
                (
                    max_w,
                    max(1, int(coin_text.get_height() * factor))
                )
            )

        coin_text_rect = coin_text.get_rect(
            center=(
                self.coin_rect.left + self.coin_text_offset[0],
                self.coin_rect.top + self.coin_text_offset[1]
            )
        )

        screen.blit(coin_text, coin_text_rect)

        if coin_gain > 0 and coin_gain_alpha > 0:

            gain_text = f"+{format_coins(coin_gain)}"

            if self.gain_font is None:
                self.gain_font = pygame.font.Font(None, 30)

            alpha = int(255 * max(0.0, min(1.0, coin_gain_alpha)))

            shadow = self.gain_font.render(gain_text, True, (0, 0, 0))
            label = self.gain_font.render(gain_text, True, (255, 226, 92))

            shadow.set_alpha(alpha)
            label.set_alpha(alpha)

            pos = label.get_rect(
                midtop=(
                    self.coin_rect.left + self.coin_text_offset[0],
                    self.coin_rect.bottom + 2
                )
            )

            screen.blit(shadow, pos.move(2, 2))
            screen.blit(label, pos)

        if countdown is not None:

            seconds_left = max(0, math.ceil(countdown))

            color = (255, 90, 70) if seconds_left <= 3 else (255, 255, 255)

            number = self.countdown_font.render(
                str(seconds_left),
                True,
                color
            )

            number_rect = number.get_rect(
                midtop=(screen.get_width() // 2, 18)
            )

            screen.blit(number, number_rect)

            self.giveup_rect = self.giveup_img.get_rect(
                midleft=(
                    screen.get_width() // 2 + GIVEUP_GAP,
                    number_rect.centery
                )
            )

            hovered = self.giveup_rect.collidepoint(pygame.mouse.get_pos())

            screen.blit(
                self.giveup_img_hover if hovered else self.giveup_img,
                self.giveup_rect
            )

        else:

            self.giveup_rect = None

        if attack_mode in self.attack_panels:

            screen.blit(
                self.attack_panels[attack_mode],
                self.attack_panel_rect
            )

        screen.blit(self.bar, self.bar_rect)

        for i, (x, y) in enumerate(self.slot_pos):

            img = self.slot_select if i == self.selected else self.slot
            screen.blit(img, (x, y))

            icon = (
                self._slot_icon(self.items[i])
                if self.items[i] is not None
                else None
            )

            if icon is not None:
                screen.blit(
                    icon,
                    icon.get_rect(
                        center=self.slot_rect(i).center
                    )
                )

            if self.items[i] is not None and self.counts[i] > 1:

                txt = str(self.counts[i])

                shadow = self.count_font.render(txt, True, (30, 34, 40))
                text = self.count_font.render(txt, True, (255, 255, 255))

                pos = text.get_rect(
                    bottomright=self.slot_rect(i).bottomright
                )

                pos.move_ip(-5, -4)

                screen.blit(shadow, pos.move(1, 1))
                screen.blit(text, pos)

        if equipped_selected:
            screen.blit(self.equipped_frame_select, self.equipped_rect)
        else:
            screen.blit(self.equipped_frame, self.equipped_rect)

        if self.equipped in self.equipped_icons:

            if equipped_selected:
                icon = self.equipped_icons_select[self.equipped]
                screen.blit(icon, self.equipped_rect)
            else:
                icon = self.equipped_icons[self.equipped]
                screen.blit(
                    icon,
                    icon.get_rect(center=self.equipped_rect.center)
                )