from pathlib import Path

import pygame


# Menu de emotes: una imagen (assets/maps/hud/emotes_panel.png) con 3
# tarjetas. Al pasar el mouse se pega encima la tarjeta resaltada y con un
# click se hace el emote. Las imagenes las genera tools/make_emote_wheel.py.

EMOTES = [
    {"id": "six_seven", "label": "Six Seven"},
    {"id": "dab",       "label": "Dab"},
    {"id": "saludo",    "label": "Saludo"},
]

SLOTS = len(EMOTES)

HUD_DIR = Path(__file__).resolve().parent.parent / "assets" / "maps" / "hud"

# tienen que coincidir con tools/make_emote_wheel.py (pixeles de la imagen)
CARDS = [(84, 138, 252, 330), (374, 138, 252, 330), (664, 138, 252, 330)]
HOVER_PAD = 24

COL_DIM = (0, 0, 0, 150)


class EmoteWheel:

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()

        self.active = False
        self.hover = None

        self.selected = None

        self._panel_src = pygame.image.load(
            str(HUD_DIR / "emotes_panel.png")
        ).convert_alpha()

        self._hover_src = [
            pygame.image.load(
                str(HUD_DIR / f"emotes_card_hover_{i}.png")
            ).convert_alpha()
            for i in range(SLOTS)
        ]

        self._build()

    def _build(self):
        """Escala la imagen al tamaño de la pantalla y calcula las zonas."""

        pw, ph = self._panel_src.get_size()

        self.scale = min(
            self.width * 0.5 / pw,
            self.height * 0.55 / ph,
            1.0,
        )

        size = (int(pw * self.scale), int(ph * self.scale))

        self.panel = pygame.transform.smoothscale(self._panel_src, size)

        self.panel_pos = (
            (self.width - size[0]) // 2,
            (self.height - size[1]) // 2,
        )

        self.hovers = []
        self.rects = []

        for i, (x, y, w, h) in enumerate(CARDS):

            s = self.scale

            self.rects.append(pygame.Rect(
                self.panel_pos[0] + int(x * s),
                self.panel_pos[1] + int(y * s),
                int(w * s),
                int(h * s),
            ))

            src = self._hover_src[i]

            self.hovers.append(pygame.transform.smoothscale(
                src,
                (int(src.get_width() * s), int(src.get_height() * s)),
            ))

        self._dim = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        self._dim.fill(COL_DIM)

    # ------------------------------------------------------------ estado

    def open(self):

        self.active = True
        self.hover = None
        self.selected = None

        self.hover = self._slot_at(pygame.mouse.get_pos())

    def close(self):

        self.active = False
        self.hover = None

    def toggle(self):

        if self.active:
            self.close()
        else:
            self.open()

    def pop_selected(self):
        """Devuelve el id del emote elegido (una sola vez) o None."""

        chosen = self.selected
        self.selected = None

        return chosen

    # ---------------------------------------------------------- geometria

    def _slot_at(self, pos):

        for i, rect in enumerate(self.rects):

            if rect.collidepoint(pos):
                return i

        return None

    # ------------------------------------------------------------ eventos

    def handle_event(self, event):

        """Devuelve True si el evento fue consumido por el menu."""

        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.close()
                return True

            return False

        if event.type == pygame.MOUSEMOTION:

            self.hover = self._slot_at(event.pos)

            return False

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                slot = self._slot_at(event.pos)

                if slot is not None:
                    self.selected = EMOTES[slot]["id"]
                    self.close()

                elif not pygame.Rect(
                    self.panel_pos, self.panel.get_size()
                ).collidepoint(event.pos):
                    # click afuera del panel: cerrar
                    self.close()

            return True

        if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
            return True

        return False

    # ------------------------------------------------------------- dibujo

    def draw(self, surface=None):

        if not self.active:
            return

        surface = surface or self.screen

        surface.blit(self._dim, (0, 0))
        surface.blit(self.panel, self.panel_pos)

        if self.hover is not None:

            rect = self.rects[self.hover]
            pad = int(HOVER_PAD * self.scale)

            surface.blit(
                self.hovers[self.hover],
                (rect.x - pad, rect.y - pad),
            )