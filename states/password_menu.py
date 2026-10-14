import pygame
from pathlib import Path

from core.Save_manager import PASSWORD_MIN, PASSWORD_MAX


UI_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "ui"
)


class PasswordMenu:
    """Pantalla para escribir una contraseña.

    mode="set"  -> al crear la partida: el jugador inventa la contraseña.
    mode="ask"  -> al jugar o borrar una partida: se la pide.

    Imagen OPCIONAL (assets/maps/ui/mapacontrasena.png, 1672x941): igual
    que mapacarga.png pero con el cartel "Contraseña:" en vez de
    "Nombre de la partida:". Si no esta, se usa mapacarga.png y el
    cartel se tapa y se escribe con codigo.

    handle_event devuelve ("password", texto), "back" o None.
    """

    IMG_W = 1672
    IMG_H = 941

    INPUT_BOX = (747, 365, 1002, 391)
    CLOSE_BOX = (1025, 299, 1042, 315)

    # Zona del cartel "Nombre de la partida:" (se tapa si no hay imagen
    # propia) y donde se escribe "Contraseña:"
    LABEL_COVER_BOX = (745, 314, 1004, 346)
    LABEL_CENTER = (875, 330)

    def __init__(self, screen, mode="set"):

        self.screen = screen
        self.mode = mode
        self.width, self.height = screen.get_size()

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        self.background = self._load_background()

        self.input_rect = self._scale_box(self.INPUT_BOX)
        self.close_rect = self._scale_box(self.CLOSE_BOX)

        self.text_max_width = self.input_rect.width - 32

        self.font = pygame.font.Font(None, 24)
        self.label_font = pygame.font.Font(None, max(18, int(30 * self.sy)))
        self.small_font = pygame.font.Font(None, 24)

        self.text = ""
        self.message = ""

        pygame.key.start_text_input()

    # ---------- carga ----------

    def _scale_box(self, box):

        x1, y1, x2, y2 = box

        return pygame.Rect(
            round(x1 * self.sx),
            round(y1 * self.sy),
            round((x2 - x1) * self.sx),
            round((y2 - y1) * self.sy),
        )

    def _load_background(self):

        own = UI_DIR / "mapacontrasena.png"

        if own.exists():

            self.has_own_image = True

            image = pygame.image.load(own).convert()

            return pygame.transform.scale(image, (self.width, self.height))

        self.has_own_image = False

        path = UI_DIR / "mapacarga.png"

        if path.exists():

            image = pygame.image.load(path).convert()

            surface = pygame.transform.scale(image, (self.width, self.height))

        else:

            surface = pygame.Surface((self.width, self.height))
            surface.fill((77, 130, 195))

        # Tapa "Nombre de la partida:" con el color del fondo de la ventana
        cover = self._scale_box(self.LABEL_COVER_BOX)

        sample = (
            min(self.width - 1, cover.left + 4),
            min(self.height - 1, cover.bottom + 2),
        )

        pygame.draw.rect(surface, surface.get_at(sample), cover)

        return surface

    # ---------- uso ----------

    def clear(self):
        """Borra lo escrito (despues de una contraseña incorrecta)."""

        self.text = ""

    def finish(self):

        pygame.key.stop_text_input()

    def handle_event(self, event):

        if event.type == pygame.TEXTINPUT:

            for char in event.text:

                if not char.isprintable() or char == " ":
                    continue

                if len(self.text) >= PASSWORD_MAX:
                    continue

                self.text += char
                self.message = ""

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_BACKSPACE:

                self.text = self.text[:-1]
                self.message = ""

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):

                if len(self.text) < PASSWORD_MIN:

                    self.message = "Escribí una contraseña"

                else:

                    return ("password", self.text)

            elif event.key == pygame.K_ESCAPE:

                self.finish()

                return "back"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.close_rect.collidepoint(event.pos):

                self.finish()

                return "back"

        return None

    # ---------- dibujo ----------

    def draw(self):

        self.screen.blit(self.background, (0, 0))

        if not self.has_own_image:

            label = self.label_font.render("Contraseña:", True, (255, 255, 255))

            self.screen.blit(
                label,
                label.get_rect(
                    center=(
                        round(self.LABEL_CENTER[0] * self.sx),
                        round(self.LABEL_CENTER[1] * self.sy),
                    )
                ),
            )

        # La contraseña se muestra con asteriscos
        shown = "*" * len(self.text)

        text_surface = self.font.render(shown, True, (255, 255, 255))

        text_rect = text_surface.get_rect(
            midleft=(self.input_rect.left + 6, self.input_rect.centery)
        )

        self.screen.blit(text_surface, text_rect)

        if (pygame.time.get_ticks() // 500) % 2 == 0:

            cursor_x = text_rect.right + 2

            pygame.draw.line(
                self.screen,
                (255, 255, 255),
                (cursor_x, self.input_rect.top + 4),
                (cursor_x, self.input_rect.bottom - 4),
                2,
            )

        hint = self.message

        if not hint and self.mode == "set":
            hint = "La vas a necesitar para jugar y borrar."

        if hint:

            color = (255, 220, 160)

            surf = self.small_font.render(hint, True, color)

            self.screen.blit(
                surf,
                surf.get_rect(
                    midtop=(
                        self.input_rect.centerx,
                        self.input_rect.bottom + 14,
                    )
                ),
            )

        controls = self.small_font.render(
            "ENTER continuar  •  ESC volver",
            True,
            (235, 242, 255),
        )

        self.screen.blit(
            controls,
            controls.get_rect(
                bottomright=(self.width - 18, self.height - 15)
            ),
        )