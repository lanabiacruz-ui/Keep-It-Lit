import math

import pygame
from pathlib import Path

HUD_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
)


class Hud:

    SLOTS = 5

    # Area util (sin transparencia) de cada marco de barra, medida
    # sobre el PNG original. El relleno comparte el mismo lienzo,
    # asi que recortarlo con este rectangulo alcanza para "vaciarlo".
    VIDA_BBOX = (7, 7, 248, 41)
    ESCUDO_BBOX = (2, 6, 185, 34)

    def __init__(
        self,
        screen_size,
        scale=0.6,
        equipped_scale=0.75,
        bar_scale=1.0
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
            "fosforo": scaled(load("icon_fosforo.png"), equipped_scale)
        }

        # Item que tiene el jugador en la mano (None = nada)
        self.equipped = None

        # Items del inventario (por ahora vacio; el fosforo NO va aca)
        self.items = [None] * self.SLOTS
        self.selected = None

        self.bar_rect = self.bar.get_rect(
            midbottom=(w // 2, h - 12)
        )

        slot_size = self.slot.get_width()
        gap = 6
        total = self.SLOTS * slot_size + (self.SLOTS - 1) * gap

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

        # ---------- Vida y escudo ----------

        self.vida_frame = scaled(load("hud_barra2.png"), bar_scale)
        self.vida_fill = scaled(load("hud_vida_relleno.png"), bar_scale)

        self.escudo_frame = scaled(load("hud_barra1.png"), bar_scale)
        self.escudo_fill = scaled(load("hud_escudo_relleno.png"), bar_scale)

        self.vida_bbox = tuple(
            round(v * bar_scale) for v in self.VIDA_BBOX
        )

        self.escudo_bbox = tuple(
            round(v * bar_scale) for v in self.ESCUDO_BBOX
        )

        margin = 18

        self.vida_pos = (margin, margin)

        self.escudo_pos = (
            margin,
            margin + self.vida_frame.get_height() + 8
        )

        self.countdown_font = pygame.font.Font(None, 90)

        # Monedas (arriba a la derecha)
        self.coin_icon = scaled(load("hud_monedas.png"), bar_scale)

        self.coin_rect = self.coin_icon.get_rect(
            topright=(w - margin, margin)
        )

        self.coin_font = pygame.font.Font(None, 32)

    def equip(self, name):
        self.equipped = name

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
        coins=0
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

        # Monedas, arriba a la derecha
        screen.blit(self.coin_icon, self.coin_rect)

        coin_text = self.coin_font.render(
            str(coins),
            True,
            (255, 255, 255)
        )

        coin_text_rect = coin_text.get_rect(
            center=(
                self.coin_rect.centerx,
                self.coin_rect.centery
            )
        )

        screen.blit(coin_text, coin_text_rect)

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

        # Hotbar
        screen.blit(self.bar, self.bar_rect)

        for i, (x, y) in enumerate(self.slot_pos):

            img = self.slot_select if i == self.selected else self.slot
            screen.blit(img, (x, y))

        # Item equipado
        screen.blit(self.equipped_frame, self.equipped_rect)

        if self.equipped in self.equipped_icons:

            icon = self.equipped_icons[self.equipped]

            screen.blit(
                icon,
                icon.get_rect(center=self.equipped_rect.center)
            )