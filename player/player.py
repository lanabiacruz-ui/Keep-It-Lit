import pygame
from pathlib import Path

from player.movement import PlayerMovement


class Player:
    CELL_WIDTH = 176
    CELL_HEIGHT = 226

    BOTTOM_MARGIN = 6

    ROWS = ["up", "down", "left", "right"]


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


    SHEET_RECTS_PHOSPHOR = [
        [(341, 48, 150, 206), (594, 46, 151, 209),
         (847, 47, 149, 208), (1099, 47, 150, 208)],
        [(325, 295, 168, 209), (581, 294, 166, 210),
         (834, 294, 168, 211), (1087, 294, 169, 211)],
        [(328, 541, 159, 208), (585, 541, 157, 208),
         (840, 541, 159, 208), (1092, 541, 160, 208)],
        [(333, 783, 158, 205), (588, 783, 155, 204),
         (847, 783, 157, 205), (1099, 783, 157, 206)],
    ]

    # Hoja del personaje con la vela (assets/maps/player/player_vela.png)
    SHEET_RECTS_VELA = [
        [(343, 50, 161, 203), (596, 49, 162, 204),
         (848, 49, 164, 204), (1101, 49, 163, 204)],
        [(318, 297, 173, 205), (573, 297, 171, 205),
         (829, 297, 170, 206), (1082, 297, 173, 206)],
        [(315, 544, 170, 202), (572, 545, 168, 202),
         (827, 545, 170, 203), (1084, 545, 167, 202)],
        [(337, 785, 165, 202), (591, 785, 166, 201),
         (850, 785, 163, 202), (1102, 785, 168, 202)],
    ]

    # Hoja del personaje con la antorcha (assets/maps/player/player_antorcha.png)
    SHEET_RECTS_ANTORCHA = [
        [(343, 49, 166, 204), (596, 49, 167, 204),
         (848, 49, 168, 204), (1101, 49, 168, 204)],
        [(313, 297, 178, 205), (568, 297, 176, 205),
         (824, 297, 175, 206), (1076, 297, 179, 206)],
        [(310, 544, 175, 202), (568, 545, 172, 202),
         (825, 545, 172, 203), (1079, 545, 172, 202)],
        [(335, 785, 172, 202), (589, 785, 173, 201),
         (845, 785, 172, 202), (1102, 785, 172, 202)],
    ]

    # Golpe recibido: se pone rojo un ratito y queda invulnerable
    HURT_TIME = 0.30
    INVULN_TIME = 0.90
    KNOCKBACK = 120.0

    def __init__(self, x, y, width=54, height=74):

        self.image_rect = pygame.Rect(
            x - width // 2,
            y - height // 2,
            width,
            height
        )

        hitbox_width = 6
        hitbox_height = 4

        # Los pies quedan donde estaban con el tamano anterior (46 px),
        # asi el personaje no aparece corrido al hacerlo mas grande.
        feet_y = y + 46 // 2

        self.rect = pygame.Rect(
            x - hitbox_width // 2,
            feet_y - hitbox_height - 3,
            hitbox_width,
            hitbox_height
        )

        self.movement = PlayerMovement()

        self.moving = False
        self.direction = "down"

        self.animation_timer = 0
        self.animation_frame = 0

        self.has_torch = False
        self.torch_kind = "fosforo"

        # Golpes recibidos (enemigos)
        self.hurt_timer = 0.0
        self.invuln_timer = 0.0
        self.kb_vel = pygame.Vector2()
        self._kb_rest = pygame.Vector2()

        base = Path(__file__).resolve().parent.parent
        player_dir = base / "assets" / "maps" / "player"


        frames_path = player_dir / "player_frames.png"
        sheet_path = player_dir / "player.png"
        torch_path = player_dir / "player_phosphor.png"
        vela_path = player_dir / "player_vela.png"
        antorcha_path = player_dir / "player_antorcha.png"

        self.frame_scale = None

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

        self.frames_torch = None

        if torch_path.exists():

            torch_sheet = pygame.image.load(
                str(torch_path)
            ).convert()

            self.frames_torch = self.load_frames_from_sheet(
                torch_sheet,
                self.SHEET_RECTS_PHOSPHOR
            )

        self.frames_vela = None

        if vela_path.exists():

            vela_sheet = pygame.image.load(
                str(vela_path)
            ).convert()

            self.frames_vela = self.load_frames_from_sheet(
                vela_sheet,
                self.SHEET_RECTS_VELA
            )

        self.frames_antorcha = None

        if antorcha_path.exists():

            antorcha_sheet = pygame.image.load(
                str(antorcha_path)
            ).convert()

            self.frames_antorcha = self.load_frames_from_sheet(
                antorcha_sheet,
                self.SHEET_RECTS_ANTORCHA
            )

    def set_torch(self, value, kind="fosforo"):
        """Con luz en la mano el personaje cambia de dibujo: el del
        fosforo, el de la vela o el de la antorcha."""

        self.torch_kind = kind

        self.has_torch = bool(value) and (
            self.frames_torch is not None
            or self.frames_vela is not None
            or self.frames_antorcha is not None
        )

    # ---------- golpes recibidos ----------

    def hurt(self, from_pos=None):
        """Recibe un golpe: se pone rojo, empujon y un rato sin poder
        recibir otro. Devuelve False si todavia era invulnerable."""

        if self.invuln_timer > 0:
            return False

        self.hurt_timer = self.HURT_TIME
        self.invuln_timer = self.INVULN_TIME

        if from_pos is not None:

            away = pygame.Vector2(self.rect.center) - pygame.Vector2(from_pos)

            if away.length_squared() > 0.01:
                self.kb_vel = away.normalize() * self.KNOCKBACK

        return True

    def _apply_knockback(self, dt, collision_map):

        if self.kb_vel.length_squared() < 4:

            self.kb_vel = pygame.Vector2()
            self._kb_rest = pygame.Vector2()

            return

        self._kb_rest += self.kb_vel * dt

        step_x = int(self._kb_rest.x)
        step_y = int(self._kb_rest.y)

        self._kb_rest.x -= step_x
        self._kb_rest.y -= step_y

        self.movement._move(self.rect, collision_map, step_x, 0)
        self.movement._move(self.rect, collision_map, 0, step_y)

        self.kb_vel *= max(0.0, 1.0 - 9.0 * dt)

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

        
        result = pygame.Surface(
            crop.get_size(),
            pygame.SRCALPHA
        )

        for px in range(crop.get_width()):

            for py in range(crop.get_height()):

                r, g, b, _ = crop.get_at((px, py))

                avg = (r + g + b) / 3

                if (
                    avg < 110
                    or (b - r > 12 and avg < 210)
                    or (r - b > 40 and avg < 250)
                ):

                    result.set_at((px, py), (r, g, b, 255))

        return result

    def load_frames_from_sheet(self, sheet, rects=None):

        if rects is None:
            rects = self.SHEET_RECTS

        crops = {}
        max_w = 1
        max_h = 1

        for row, direction in enumerate(self.ROWS):

            crops[direction] = []

            for rect in rects[row]:

                crop = sheet.subsurface(
                    pygame.Rect(rect)
                ).copy()

                crop = self._remove_background(crop)

                crops[direction].append(crop)

                max_w = max(max_w, crop.get_width())
                max_h = max(max_h, crop.get_height())

  
        if self.frame_scale is None:

            self.frame_scale = min(
                (self.CELL_WIDTH - 12) / max_w,
                (self.CELL_HEIGHT - 12) / max_h
            )

        scale = self.frame_scale

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

        if self.hurt_timer > 0:
            self.hurt_timer = max(0.0, self.hurt_timer - dt)

        if self.invuln_timer > 0:
            self.invuln_timer = max(0.0, self.invuln_timer - dt)

        self._apply_knockback(dt, collision_map)

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

        if (
            self.has_torch
            and self.torch_kind == "antorcha"
            and self.frames_antorcha is not None
        ):
            frames = self.frames_antorcha
        elif (
            self.has_torch
            and self.torch_kind == "vela"
            and self.frames_vela is not None
        ):
            frames = self.frames_vela
        elif self.has_torch and self.frames_torch is not None:
            frames = self.frames_torch
        else:
            frames = self.frames

        frame = frames[
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

        # Golpe recibido: rojo (como en Minecraft) que se va apagando
        if self.hurt_timer > 0:

            k = self.hurt_timer / self.HURT_TIME

            sprite.fill(
                (255, int(255 - 190 * k), int(255 - 190 * k), 255),
                special_flags=pygame.BLEND_RGBA_MULT
            )

            sprite.fill(
                (int(120 * k), 0, 0, 0),
                special_flags=pygame.BLEND_RGB_ADD
            )

        # Despues del rojo, parpadea un poco mientras es invulnerable
        elif self.invuln_timer > 0 and int(self.invuln_timer * 14) % 2:

            sprite.set_alpha(140)

        dest = sprite.get_rect(
            midbottom=camera.apply(self.image_rect).midbottom
        )

        screen.blit(
            sprite,
            dest
        )