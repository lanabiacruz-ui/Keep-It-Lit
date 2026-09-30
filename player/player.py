import pygame
from pathlib import Path

from player.movement import PlayerMovement


class Player:
    CELL_WIDTH = 176
    CELL_HEIGHT = 226

    BOTTOM_MARGIN = 6

    ROWS = ["up", "down", "left", "right"]

    # Posicion (x, y, ancho, alto) de cada muñeco dentro de player.png.
    # Filas: arriba, abajo, izquierda, derecha. 4 frames por fila.
    SHEET_RECTS = [
        [(326, 37, 151, 209), (597, 36, 150, 213),
         (869, 36, 151, 214), (1141, 36, 150, 209)],
        [(323, 285, 154, 213), (597, 286, 153, 208),
         (872, 286, 152, 212), (1143, 285, 154, 210)],
        [(316, 539, 159, 209), (590, 540, 156, 208),
         (862, 539, 155, 209), (1138, 539, 155, 208)],
        [(316, 780, 158, 207), (589, 780, 161, 207),
         (868, 781, 158, 207), (1141, 782, 157, 206)],
    ]

    def __init__(self, x, y, width=34, height=46):

        self.image_rect = pygame.Rect(
            x - width // 2,
            y - height // 2,
            width,
            height
        )

        hitbox_width = 16
        hitbox_height = 12

        self.rect = pygame.Rect(
            x - hitbox_width // 2,
            self.image_rect.bottom - hitbox_height - 3,
            hitbox_width,
            hitbox_height
        )

        self.movement = PlayerMovement()

        self.moving = False
        self.direction = "down"

        self.animation_timer = 0
        self.animation_frame = 0

        base = Path(__file__).resolve().parent.parent
        player_dir = base / "assets" / "maps" / "player"

        # Si existe player_frames.png (hoja ya recortada 4x4) se usa esa.
        # Si no, se usa player.png y se recorta automaticamente.
        frames_path = player_dir / "player_frames.png"
        sheet_path = player_dir / "player.png"

        if frames_path.exists():

            sheet = pygame.image.load(
                str(frames_path)
            ).convert_alpha()

            self.frames = self.load_frames(sheet)

        else:

            sheet = pygame.image.load(
                str(sheet_path)
            ).convert()

            self.frames = self.load_frames_from_sheet(sheet)

    def load_frames(self, sheet):

        frames = {}

        for row, direction in enumerate(self.ROWS):

            frames[direction] = []

            for col in range(4):

                area = pygame.Rect(
                    col * self.CELL_WIDTH,
                    row * self.CELL_HEIGHT,
                    self.CELL_WIDTH,
                    self.CELL_HEIGHT
                )

                sprite = sheet.subsurface(
                    area
                ).copy()

                frames[direction].append(
                    sprite
                )

        return frames

    @staticmethod
    def _remove_background(crop):

        # Deja opaco solo lo oscuro (contorno) y lo azul grisaceo (cuerpo).
        # El fondo de cuadritos claros queda transparente.
        result = pygame.Surface(
            crop.get_size(),
            pygame.SRCALPHA
        )

        for px in range(crop.get_width()):

            for py in range(crop.get_height()):

                r, g, b, _ = crop.get_at((px, py))

                avg = (r + g + b) / 3

                if avg < 110 or (b - r > 12 and avg < 210):

                    result.set_at((px, py), (r, g, b, 255))

        return result

    def load_frames_from_sheet(self, sheet):

        crops = {}
        max_w = 1
        max_h = 1

        for row, direction in enumerate(self.ROWS):

            crops[direction] = []

            for rect in self.SHEET_RECTS[row]:

                crop = sheet.subsurface(
                    pygame.Rect(rect)
                ).copy()

                crop = self._remove_background(crop)

                crops[direction].append(crop)

                max_w = max(max_w, crop.get_width())
                max_h = max(max_h, crop.get_height())

        scale = min(
            (self.CELL_WIDTH - 12) / max_w,
            (self.CELL_HEIGHT - 12) / max_h
        )

        frames = {}

        for direction, images in crops.items():

            frames[direction] = []

            for crop in images:

                new_size = (
                    round(crop.get_width() * scale),
                    round(crop.get_height() * scale)
                )

                crop = pygame.transform.smoothscale(
                    crop,
                    new_size
                )

                cell = pygame.Surface(
                    (self.CELL_WIDTH, self.CELL_HEIGHT),
                    pygame.SRCALPHA
                )

                cell.blit(
                    crop,
                    (
                        (self.CELL_WIDTH - new_size[0]) // 2,
                        self.CELL_HEIGHT
                        - self.BOTTOM_MARGIN
                        - new_size[1]
                    )
                )

                frames[direction].append(cell)

        return frames

    def update(self, dt, collision_map):

        result = self.movement.update(
            self.rect,
            collision_map,
            dt
        )

        self.moving = result[0]

        if result[1] is not None:
            self.direction = result[1]

        self.image_rect.midbottom = (
            self.rect.centerx,
            self.rect.bottom + 3
        )

        if self.moving:

            self.animation_timer += dt

            if self.animation_timer >= 0.12:

                self.animation_timer = 0

                self.animation_frame += 1

                self.animation_frame %= len(
                    self.frames[self.direction]
                )

        else:

            self.animation_frame = 0

    def draw(self, screen, camera):

        frame = self.frames[
            self.direction
        ][
            self.animation_frame
        ]

        scale = self.image_rect.height / self.CELL_HEIGHT

        sprite = pygame.transform.smoothscale(
            frame,
            (
                round(self.CELL_WIDTH * scale),
                self.image_rect.height
            )
        )

        dest = sprite.get_rect(
            midbottom=camera.apply(self.image_rect).midbottom
        )

        screen.blit(
            sprite,
            dest
        )