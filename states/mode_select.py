import pygame
from pathlib import Path

from core.Save_manager import MODE_NORMAL, MODE_HARDCORE


UI_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "ui"
)


class ModeSelect:
    """Pantalla para elegir el modo al crear una partida.

    Todas las imagenes son OPCIONALES (si falta alguna se dibuja con
    codigo), en assets/maps/ui:

      mapamodo.png            1672x941  fondo (la compu con el titulo)
                                        Si no esta, se usa mapaajustes.png
      btn_normal.png          320x80    boton "Normal"
      btn_normal_hover.png    320x80    el mismo, resaltado
      btn_hardcore.png        320x80    boton "Hardcore"
      btn_hardcore_hover.png  320x80    el mismo, resaltado

    Las medidas de las cajas estan en pixeles de la imagen de fondo
    (1672x941) y se escalan solas a la ventana.
    """

    IMG_W = 1672
    IMG_H = 941

    # (x1, y1, x2, y2) en pixeles de la imagen de fondo
    BTN_NORMAL_BOX = (505, 318, 825, 398)
    BTN_HARDCORE_BOX = (857, 318, 1177, 398)

    # Donde va el texto de abajo de cada boton
    DESC_NORMAL_BOX = (505, 408, 825, 500)
    DESC_HARDCORE_BOX = (857, 408, 1177, 500)

    # Donde va el "Elegi el modo" (centro del texto)
    TITLE_POS = (845, 292)

    CLOSE_BOX = (1179, 219, 1204, 246)

    DESC_NORMAL = (
        "Si perdés, te queda solo el fósforo y perdés todos los items. "
        "Las oleadas siguen igual."
    )
    DESC_HARDCORE = (
        "Si perdés, perdés todo: se borra la partida."
    )

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        self.background = self._load_background()

        self.normal_rect = self._scale_box(self.BTN_NORMAL_BOX)
        self.hardcore_rect = self._scale_box(self.BTN_HARDCORE_BOX)
        self.close_rect = self._scale_box(self.CLOSE_BOX)

        self.desc_normal_rect = self._scale_box(self.DESC_NORMAL_BOX)
        self.desc_hardcore_rect = self._scale_box(self.DESC_HARDCORE_BOX)

        size = self.normal_rect.size

        self.img_normal = self._load_button("btn_normal.png", size)
        self.img_normal_hover = self._load_button(
            "btn_normal_hover.png", size
        )
        self.img_hardcore = self._load_button("btn_hardcore.png", size)
        self.img_hardcore_hover = self._load_button(
            "btn_hardcore_hover.png", size
        )

        self.title_font = pygame.font.Font(None, max(18, int(34 * self.sy)))
        self.button_font = pygame.font.Font(None, max(18, int(44 * self.sy)))
        self.desc_font = pygame.font.Font(None, max(14, int(28 * self.sy)))
        self.small_font = pygame.font.Font(None, 24)

        # 0 = normal, 1 = hardcore
        self.selected = 0

    # ---------- carga ----------

    def _load_background(self):

        for name in ("mapamodo.png", "mapaajustes.png", "mapacarga.png"):

            path = UI_DIR / name

            if path.exists():

                image = pygame.image.load(path).convert()

                return pygame.transform.scale(
                    image, (self.width, self.height)
                )

        surface = pygame.Surface((self.width, self.height))
        surface.fill((77, 130, 195))

        return surface

    def _load_button(self, name, size):

        path = UI_DIR / name

        if not path.exists():
            return None

        image = pygame.image.load(path).convert_alpha()

        return pygame.transform.smoothscale(image, size)

    def _scale_box(self, box):

        x1, y1, x2, y2 = box

        return pygame.Rect(
            round(x1 * self.sx),
            round(y1 * self.sy),
            round((x2 - x1) * self.sx),
            round((y2 - y1) * self.sy),
        )

    # ---------- eventos ----------

    def _mode_of(self, index):

        return MODE_NORMAL if index == 0 else MODE_HARDCORE

    def handle_event(self, event):
        """Devuelve ("mode", "normal"/"hardcore"), "back" o None."""

        if event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = 0

            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = 1

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return ("mode", self._mode_of(self.selected))

            elif event.key == pygame.K_ESCAPE:
                return "back"

        elif event.type == pygame.MOUSEMOTION:

            if self.normal_rect.collidepoint(event.pos):
                self.selected = 0

            elif self.hardcore_rect.collidepoint(event.pos):
                self.selected = 1

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.close_rect.collidepoint(event.pos):
                return "back"

            if self.normal_rect.collidepoint(event.pos):
                return ("mode", MODE_NORMAL)

            if self.hardcore_rect.collidepoint(event.pos):
                return ("mode", MODE_HARDCORE)

        return None

    # ---------- dibujo ----------

    def _draw_button(self, rect, label, image, image_hover, hovered, accent):

        img = image_hover if hovered and image_hover else image

        if img is not None:

            self.screen.blit(img, rect)

            if hovered and image_hover is None:
                pygame.draw.rect(
                    self.screen, (255, 255, 255), rect, 3, border_radius=8
                )

            return

        # Sin imagen: se dibuja con codigo
        fill = (55, 80, 135) if hovered else (30, 45, 85)

        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(
            self.screen,
            (255, 255, 255) if hovered else accent,
            rect,
            3,
            border_radius=8,
        )

        text = self.button_font.render(label, True, (255, 255, 255))

        self.screen.blit(text, text.get_rect(center=rect.center))

    def _draw_wrapped(self, text, rect, color):

        words = text.split(" ")
        lines = []
        line = ""

        for word in words:

            test = word if not line else line + " " + word

            if self.desc_font.size(test)[0] <= rect.width:
                line = test
            else:
                lines.append(line)
                line = word

        if line:
            lines.append(line)

        y = rect.top

        for line in lines:

            surf = self.desc_font.render(line, True, color)

            self.screen.blit(surf, surf.get_rect(midtop=(rect.centerx, y)))

            y += surf.get_height() + 2

    def draw(self):

        self.screen.blit(self.background, (0, 0))

        title = self.title_font.render(
            "Elegí el modo de juego", True, (255, 255, 255)
        )

        self.screen.blit(
            title,
            title.get_rect(
                center=(
                    round(self.TITLE_POS[0] * self.sx),
                    round(self.TITLE_POS[1] * self.sy),
                )
            ),
        )

        self._draw_button(
            self.normal_rect,
            "NORMAL",
            self.img_normal,
            self.img_normal_hover,
            self.selected == 0,
            (140, 210, 150),
        )

        self._draw_button(
            self.hardcore_rect,
            "HARDCORE",
            self.img_hardcore,
            self.img_hardcore_hover,
            self.selected == 1,
            (235, 90, 80),
        )

        self._draw_wrapped(
            self.DESC_NORMAL, self.desc_normal_rect, (235, 242, 255)
        )

        self._draw_wrapped(
            self.DESC_HARDCORE, self.desc_hardcore_rect, (255, 200, 190)
        )

        controls = self.small_font.render(
            "Izq/Der elegir  •  ENTER confirmar  •  ESC volver",
            True,
            (235, 242, 255),
        )

        self.screen.blit(
            controls,
            controls.get_rect(
                bottomright=(self.width - 18, self.height - 15)
            ),
        )