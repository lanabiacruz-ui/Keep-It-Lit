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

    def __init__(self, screen_size, scale=0.6, equipped_scale=0.75):

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
        self.selected = 0

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
        # (cambia esta posicion si lo queres en otro lado)
        self.equipped_rect = self.equipped_frame.get_rect(
            midright=(self.bar_rect.left - 12, self.bar_rect.centery)
        )

    def equip(self, name):
        self.equipped = name

    def draw(self, screen):

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