import pygame
from pathlib import Path


class MenuCarga:

    
    IMG_W = 1672
    IMG_H = 941

    INPUT_BOX = (747, 365, 1002, 391)   
    CLOSE_BOX = (1025, 299, 1042, 315)  

    MAX_CHARS = 16

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()

        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
            / "mapacarga.png"
        )

        self.background = pygame.image.load(image_path).convert()

        self.background = pygame.transform.scale(
            self.background,
            (self.width, self.height)
        )

        self.input_rect = self._scale_box(self.INPUT_BOX)
        self.close_rect = self._scale_box(self.CLOSE_BOX)

        # Espacio libre dentro de la caja (dejamos lugar a la lupa)
        self.text_max_width = self.input_rect.width - 32

        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 24)

        self.name = ""
        self.message = ""

        
        pygame.key.start_text_input()

    def _scale_box(self, box):

        x1, y1, x2, y2 = box

        sx = self.width / self.IMG_W
        sy = self.height / self.IMG_H

        return pygame.Rect(
            round(x1 * sx),
            round(y1 * sy),
            round((x2 - x1) * sx),
            round((y2 - y1) * sy)
        )

    def _finish(self, action):

        pygame.key.stop_text_input()

        return action

    def handle_event(self, event):

        if event.type == pygame.TEXTINPUT:

            for char in event.text:

                if not (char.isalnum() or char in " -_"):
                    continue

                # No arrancar con espacios
                if char == " " and not self.name:
                    continue

                if len(self.name) >= self.MAX_CHARS:
                    continue

                if self.font.size(self.name + char)[0] > self.text_max_width:
                    continue

                self.name += char
                self.message = ""

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_BACKSPACE:

                self.name = self.name[:-1]

            elif event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER
            ):

                final_name = self.name.strip()

                if not final_name:

                    self.message = "Escribí un nombre para continuar"

                else:

                    return self._finish(("start", final_name))

            elif event.key == pygame.K_ESCAPE:

                return self._finish("back")

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if self.close_rect.collidepoint(event.pos):

                    return self._finish("back")

        return None

    def draw(self):

        self.screen.blit(
            self.background,
            (0, 0)
        )

        # Texto escrito
        text_surface = self.font.render(
            self.name,
            True,
            (255, 255, 255)
        )

        text_rect = text_surface.get_rect(
            midleft=(
                self.input_rect.left + 6,
                self.input_rect.centery
            )
        )

        self.screen.blit(
            text_surface,
            text_rect
        )

        # Cursor parpadeante
        if (pygame.time.get_ticks() // 500) % 2 == 0:

            cursor_x = text_rect.right + 2

            pygame.draw.line(
                self.screen,
                (255, 255, 255),
                (cursor_x, self.input_rect.top + 4),
                (cursor_x, self.input_rect.bottom - 4),
                2
            )

        if self.message:

            message_surface = self.small_font.render(
                self.message,
                True,
                (255, 220, 160)
            )

            message_rect = message_surface.get_rect(
                midtop=(
                    self.input_rect.centerx,
                    self.input_rect.bottom + 14
                )
            )

            self.screen.blit(
                message_surface,
                message_rect
            )

        controls = self.small_font.render(
            "ENTER continuar  •  ESC volver",
            True,
            (235, 242, 255)
        )

        controls_rect = controls.get_rect(
            bottomright=(
                self.width - 18,
                self.height - 15
            )
        )

        self.screen.blit(
            controls,
            controls_rect
        )
