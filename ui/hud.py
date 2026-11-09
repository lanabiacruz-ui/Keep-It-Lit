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

GEL_COIN_IMAGE = "hud_monedas_gelea.png"


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

    # Marcos de pociones: casilleros 5 y 6 (teclas 5 y 6) (a la derecha de
    # la hotbar). Solo aceptan pociones y ninguna otra cosa cae ahi.
    POTION_SLOTS = 2
    TOTAL_SLOTS = SLOTS + POTION_SLOTS
    POTION_GAP = 22
    POTION_PAD = 8          # margen del panel violeta alrededor de los marcos
    ATTACK_SCALE = 0.5      # tamano del cartel de la G (antes 0.75)

    VIDA_BBOX = (7, 7, 248, 41)
    ESCUDO_BBOX = (2, 6, 185, 34)

    COIN_TEXT_CENTER = (78, 30)

    # separacion VISIBLE entre las pastillas de monedas / menu (px)
    HUD_VISIBLE_GAP = 4

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

        self.potion_slot = self._load_scaled_or(
            "hud_pocion_slot.png", self.slot
        )
        self.potion_slot_select = self._load_scaled_or(
            "hud_pocion_slot_select.png", self.slot_select
        )

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

        self.items = [None] * self.TOTAL_SLOTS

        self.counts = [0] * self.TOTAL_SLOTS
        self.selected = None

        slot_size = self.slot.get_width()
        gap = 6                 # separacion de los marcos de pociones
        bar_gap = 0             # separacion de los slots de la hotbar
        total = self.SLOTS * slot_size + (self.SLOTS - 1) * bar_gap

        # Altura de referencia: la del panel violeta de pociones. El hotbar
        # y el cartel de la G se escalan para que su parte VISIBLE (sin los
        # margenes transparentes) mida exactamente lo mismo.
        ref_h = self.bar.get_height()

        vis_h = self.bar.get_bounding_rect(min_alpha=21).height
        bar_full_h = max(1, round(ref_h * ref_h / vis_h))

        self.bar = pygame.transform.smoothscale(
            self.bar,
            (self.SLOTS * slot_size + (self.SLOTS - 1) * gap + 12, bar_full_h)
        )

        # franja visible del hotbar (arriba/abajo) ya escalado
        bar_vis = self.bar.get_bounding_rect(min_alpha=21)

        self.bar_rect = self.bar.get_rect(
            midbottom=(w // 2, h - 12)
        )

        x0 = self.bar_rect.centerx - total // 2
        y = self.bar_rect.centery - slot_size // 2

        self.slot_pos = [
            (x0 + i * (slot_size + bar_gap), y)
            for i in range(self.SLOTS)
        ]
        
        # marcos de pociones, a la derecha de la hotbar
        px0 = self.bar_rect.right + self.POTION_GAP

        for k in range(self.POTION_SLOTS):
            self.slot_pos.append((px0 + k * (slot_size + gap), y))

        slots_right = (
            px0 + self.POTION_SLOTS * slot_size
            + (self.POTION_SLOTS - 1) * gap
        )

        # panel violeta que agrupa los dos marcos de pociones
        pad = self.POTION_PAD

        self.potion_panel_rect = pygame.Rect(
            px0 - pad,
            self.bar_rect.top + bar_vis.top,
            slots_right - px0 + pad * 2,
            ref_h
        )

        panel_img = self._load_optional("hud_pociones.png")

        self.potion_panel = (
            pygame.transform.smoothscale(
                panel_img, self.potion_panel_rect.size
            )
            if panel_img is not None else None
        )

        self.potions_right = self.potion_panel_rect.right

        self.equipped_rect = self.equipped_frame.get_rect(
            midright=(self.bar_rect.left - 12, self.bar_rect.centery)
        )

        def attack_img(name):
            img = load(name)
            vis = img.get_bounding_rect(min_alpha=21)
            k = ref_h / vis.height
            return pygame.transform.smoothscale(
                img,
                (round(img.get_width() * k), round(img.get_height() * k))
            )

        self.attack_panels = {
            "golpe": attack_img("hud_antorcha_golpe.png"),
            "fuego": attack_img("hud_antorcha_fuego.png"),
        }

        _atk = self.attack_panels["golpe"]
        _atk_vis = _atk.get_bounding_rect(min_alpha=21)

        self.attack_panel_rect = _atk.get_rect(
            topleft=(
                self.potions_right + 10,
                self.potion_panel_rect.top - _atk_vis.top
            )
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

        # los PNG tienen aire transparente a los costados: se acomodan por
        # lo que se VE (pastillas separadas HUD_VISIBLE_GAP px entre si)
        gap = self.HUD_VISIBLE_GAP

        menu_pad = self.menu_icon.get_bounding_rect().left
        coin_pad = self.coin_icon.get_bounding_rect()

        coin_right_pad = self.coin_icon.get_width() - coin_pad.right

        self.coin_rect = self.coin_icon.get_rect(
            topright=(
                self.menu_rect.left + menu_pad - gap + coin_right_pad,
                margin,
            )
        )

        # contador de monedas de gelea: la misma pastilla (110x60) con la
        # moneda de gelea, pegada a la izquierda del contador de monedas
        gcoin = self._load_optional(GEL_COIN_IMAGE)

        if gcoin is None:
            # sin imagen: la pastilla de monedas con un tinte beige
            gcoin = self.coin_icon.copy()
            gcoin.fill((235, 205, 170, 255), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            gcoin = scaled(gcoin, bar_scale)

        self.gcoin_icon = gcoin

        gcoin_pad = self.gcoin_icon.get_bounding_rect()

        self.gcoin_rect = self.gcoin_icon.get_rect(
            topright=(
                self.coin_rect.left + coin_pad.left - gap
                + (self.gcoin_icon.get_width() - gcoin_pad.right),
                margin,
            )
        )

        self.coin_font = pygame.font.Font(None, 32)

        self.gain_font = None

        self.coin_text_offset = (
            round(self.COIN_TEXT_CENTER[0] * bar_scale),
            round(self.COIN_TEXT_CENTER[1] * bar_scale)
        )

    def equip(self, name):
        self.equipped = name


    def _load_scaled_or(self, name, fallback):
        """Imagen de HUD escalada al tamano de casillero (o la de respaldo)."""

        img = self._load_optional(name)

        if img is None:
            return fallback

        return pygame.transform.smoothscale(img, fallback.get_size())

    def is_potion_slot(self, i):

        return isinstance(i, int) and self.SLOTS <= i < self.TOTAL_SLOTS

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

        for i in range(self.TOTAL_SLOTS):
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

    def draw_overlay(self, screen, item_defs, mouse_pos, holding, message,
                     message_color=None):

        if holding:

            i = self.slot_at(mouse_pos)

            item_id = self.items[i] if i is not None else None

            if item_id in item_defs:

                d = item_defs[item_id]

                potion = self.is_potion_slot(i)

                title = self.tip_title_font.render(
                    d.get("nombre", item_id), True,
                    (255, 244, 255) if potion else (40, 46, 56)
                )

                lines = [
                    self.tip_font.render(
                        t, True,
                        (240, 228, 250) if potion else (55, 62, 74)
                    )
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

                # violeta (como el marco de pociones) si el objeto esta en
                # un slot de pociones; gris en los demas
                if self.is_potion_slot(i):
                    fill, edge = (126, 93, 151), (68, 47, 84)
                else:
                    fill, edge = (150, 160, 168), (70, 78, 90)

                pygame.draw.rect(screen, fill, rect, border_radius=10)
                pygame.draw.rect(
                    screen, edge, rect, width=3, border_radius=10
                )

                y = rect.top + pad
                screen.blit(title, (rect.left + pad, y))
                y += title.get_height() + 4

                for l in lines:
                    screen.blit(l, (rect.left + pad, y))
                    y += l.get_height()

        if message:

            self._draw_message(screen, message, message_color)

    def _draw_message(self, screen, message, color=None):

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

            text = font.render(line, True, color or (255, 255, 255))
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
        attack_mode=None,
        gel_coins=0
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

        # monedas de gelea (misma pastilla, a la izquierda)
        screen.blit(self.gcoin_icon, self.gcoin_rect)

        gel_text = self.coin_font.render(
            format_coins(gel_coins),
            True,
            (255, 255, 255)
        )

        if gel_text.get_width() > max_w:

            factor = max_w / gel_text.get_width()

            gel_text = pygame.transform.smoothscale(
                gel_text,
                (
                    max_w,
                    max(1, int(gel_text.get_height() * factor))
                )
            )

        screen.blit(
            gel_text,
            gel_text.get_rect(
                center=(
                    self.gcoin_rect.left + self.coin_text_offset[0],
                    self.gcoin_rect.top + self.coin_text_offset[1]
                )
            )
        )

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

        if self.potion_panel is not None:
            screen.blit(self.potion_panel, self.potion_panel_rect)

        for i, (x, y) in enumerate(self.slot_pos):

            if self.is_potion_slot(i):
                img = (
                    self.potion_slot_select if i == self.selected
                    else self.potion_slot
                )
            else:
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