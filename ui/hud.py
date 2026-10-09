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


def format_coins(amount):
    """Monedas para el cuadro del HUD, que es chico: de 10000 para arriba
    se abrevia (100000 -> '100k', 12500 -> '12.5k', 2000000 -> '2M')."""

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

    # Area util (sin transparencia) de cada marco de barra, medida
    # sobre el PNG original. El relleno comparte el mismo lienzo,
    # asi que recortarlo con este rectangulo alcanza para "vaciarlo".
    VIDA_BBOX = (7, 7, 248, 41)
    ESCUDO_BBOX = (2, 6, 185, 34)

    # Centro (x, y) del "0" dentro de hud_monedas.png (110x60 px)
    COIN_TEXT_CENTER = (78, 30)

    # Ancho maximo (px del PNG original) del numero: lo que hay a la
    # derecha de la moneda dibujada
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

        # Hotbar (inventario)
        self.bar = scaled(load("hud_hotbar.png"), scale)
        self.slot = scaled(load("hud_slot.png"), scale)
        self.slot_select = scaled(load("hud_slot_select.png"), scale)

        # Item equipado (marco vacio + icono del item)
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

        # Versiones "seleccionado" (reemplazan al contorno dibujado)
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

        # Item que tiene el jugador en la mano (None = nada)
        self.equipped = None

        # Items del inventario (por ahora vacio; el fosforo NO va aca)
        self.items = [None] * self.SLOTS

        # Cuantas unidades hay en cada slot (se apilan las iguales)
        self.counts = [0] * self.SLOTS
        self.selected = None

        slot_size = self.slot.get_width()
        gap = 6
        total = self.SLOTS * slot_size + (self.SLOTS - 1) * gap

        # El PNG de la hotbar esta dibujado para 5 slots: se ajusta
        # el ancho al de los slots que hay (mismo margen que antes).
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

        # Item equipado: a la izquierda de la hotbar
        self.equipped_rect = self.equipped_frame.get_rect(
            midright=(self.bar_rect.left - 12, self.bar_rect.centery)
        )

        # Panel "CAMBIAR GOLPE [G]" (solo con la antorcha): a la derecha
        # de la hotbar. Una imagen por modo.
        self.attack_panels = {
            "golpe": scaled(load("hud_antorcha_golpe.png"), 0.75),
            "fuego": scaled(load("hud_antorcha_fuego.png"), 0.75),
        }

        self.attack_panel_rect = self.attack_panels["golpe"].get_rect(
            bottomleft=(self.bar_rect.right + 12, self.bar_rect.bottom)
        )

        # ---------- Vida y escudo ----------

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

        # Vida y escudo: abajo, a la izquierda del item equipado
        # (fosforo). Apiladas, alineadas a la izquierda entre si y
        # centradas verticalmente con el slot del fosforo.
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

        # Textos de items (tooltip y avisos)
        self.tip_title_font = pygame.font.Font(None, 26)
        self.tip_font = pygame.font.Font(None, 22)
        self.msg_font = pygame.font.Font(None, 28)
        self.count_font = pygame.font.Font(None, 26)

        self._slot_icons = {}

        # Monedas (arriba a la derecha)
        self.coin_scale = bar_scale

        self.coin_icon = scaled(load("hud_monedas.png"), bar_scale)

        # Boton Menu: arriba a la derecha de todo, y las monedas quedan
        # a su izquierda. Al tocarlo se abre el menu de pausa.
        menu_img = load("menu.png")

        menu_size = self.coin_icon.get_height()

        self.menu_icon = pygame.transform.smoothscale(
            menu_img,
            (menu_size, menu_size)
        )

        # Version mas clara para cuando el mouse esta encima
        self.menu_icon_hover = self.menu_icon.copy()
        self.menu_icon_hover.fill(
            (45, 45, 45, 0),
            special_flags=pygame.BLEND_RGB_ADD
        )

        self.menu_rect = self.menu_icon.get_rect(
            topright=(w - margin, margin)
        )

        # new_game.py lee este nombre para detectar el click
        self.menu_button_rect = self.menu_rect

        self.coin_rect = self.coin_icon.get_rect(
            topright=(self.menu_rect.left - 6, margin)
        )

        self.coin_font = pygame.font.Font(None, 32)

        # Fuente del "+N" de debajo del contador (se crea al usarla)
        self.gain_font = None

        # Centro del numero dentro de hud_monedas.png (110x60):
        # a la derecha de la moneda dibujada.
        self.coin_text_offset = (
            round(self.COIN_TEXT_CENTER[0] * bar_scale),
            round(self.COIN_TEXT_CENTER[1] * bar_scale)
        )

    def equip(self, name):
        self.equipped = name

    # ---------- inventario ----------

    def slot_rect(self, i):

        x, y = self.slot_pos[i]

        return pygame.Rect(x, y, *self.slot.get_size())

    def slot_at(self, pos):
        """Indice del slot de inventario bajo `pos` (None si no hay)."""

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
        """Tooltip (manteniendo click sobre un slot) y aviso en pantalla."""

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

            text = self.msg_font.render(message, True, (255, 255, 255))

            shadow = self.msg_font.render(message, True, (0, 0, 0))

            pos = text.get_rect(
                midbottom=(screen.get_width() // 2, self.bar_rect.top - 14)
            )

            screen.blit(shadow, pos.move(2, 2))
            screen.blit(text, pos)

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

        # Vida y escudo, arriba a la izquierda
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

        # Boton Menu (esquina de arriba a la derecha)
        hover = self.menu_rect.collidepoint(pygame.mouse.get_pos())

        screen.blit(
            self.menu_icon_hover if hover else self.menu_icon,
            self.menu_rect
        )

        # Monedas, a la izquierda del boton Menu
        screen.blit(self.coin_icon, self.coin_rect)

        coin_text = self.coin_font.render(
            format_coins(coins),
            True,
            (255, 255, 255)
        )

        # Si aun abreviado no entra en el cuadro, se achica
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

        # "+N": las monedas que conseguiste "en el momento", justo
        # debajo del contador (se desvanece solo)
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

        # Contador de "sin luz" (10 -> 0), centrado arriba
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

        # Panel del golpe de la antorcha (G): "golpe" o "fuego"
        if attack_mode in self.attack_panels:

            screen.blit(
                self.attack_panels[attack_mode],
                self.attack_panel_rect
            )

        # Hotbar
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

            # Cantidad (solo si hay mas de una)
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

        # Item equipado (con imagen de seleccion si esta elegido)
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