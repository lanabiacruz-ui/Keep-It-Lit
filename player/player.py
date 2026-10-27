import pygame
from pathlib import Path

from player.movement import PlayerMovement
from player import walk_anim as wa
from core import skins as skin_lib
from core.skins import tint_frames


SHEET_CELL = (190, 214)
SHEET_COLS = 5
SHEET_ROWS = 4


def _grid_rects():
    w, h = SHEET_CELL

    return [
        [(col * w, row * h, w, h) for col in range(SHEET_COLS)]
        for row in range(SHEET_ROWS)
    ]


class Player:
    CELL_WIDTH = 176
    CELL_HEIGHT = 226

    BOTTOM_MARGIN = 6

    ROWS = ["up", "down", "left", "right"]


    # Hojas de caminata (ver tools/make_walk_frames.py): 5 columnas x 4 filas,
    # celdas de 190x214. Columnas 0..3 = pasos, columna 4 = pose quieta.
    SHEET_RECTS = _grid_rects()
    SHEET_RECTS_PHOSPHOR = _grid_rects()
    SHEET_RECTS_VELA = _grid_rects()
    SHEET_RECTS_ANTORCHA = _grid_rects()

    WALK_FRAMES = 4      # cuadros de caminata por direccion
    IDLE_FRAME = 4       # indice del cuadro de pose quieta

    JUMP_TIME = 0.36       # segundos que dura el saltito
    JUMP_HEIGHT = 9        # alto maximo (pixeles del mundo)

    HURT_TIME = 0.30
    INVULN_TIME = 0.90
    KNOCKBACK = 120.0

    def __init__(self, x, y, width=54, height=74, skin=None):

        self.image_rect = pygame.Rect(
            x - width // 2,
            y - height // 2,
            width,
            height
        )

        hitbox_width = 6
        hitbox_height = 4

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

        # --- animacion de caminata (ver player/walk_anim.py) ---
        self.walk_phase = 0.0        # 0..1, un ciclo = 2 pasos
        self.walk_blend = 0.0        # 0 quieto .. 1 caminando (suavizado)
        self.idle_t = 0.0            # reloj de la respiracion
        self.settle = 0.0            # rebote al frenar
        self.hurt_anim = 0.0         # sacudida al recibir dano
        self._hurt_dir_x = 0.0
        self._was_moving = False
        self._finishing_step = False
        self._step_pending = False   # un pie acaba de pisar (lo lee el sonido)
        self.dust = wa.DustPuffs()

        self.jump_t = 0.0            # >0 mientras esta en el aire (solo visual)

        self._sprite_cache = {}
        self._feet_cache = {}
        self._shadow_cache = {}
        self._dust_cache = {}

        self.has_torch = False
        self.torch_kind = "fosforo"

        self.hurt_timer = 0.0
        self.invuln_timer = 0.0
        self.kb_vel = pygame.Vector2()
        self._kb_rest = pygame.Vector2()

        self.grabbed = False
        self.grab_lift = 0.0

        base = Path(__file__).resolve().parent.parent
        player_dir = base / "assets" / "maps" / "player"


        skin_id = skin or skin_lib.get_skin()

        def skin_sheet(name):

            # hoja de la skin si la trae; si no, la del personaje base
            return skin_lib.sheet_path(skin_id, name) or (player_dir / name)

        frames_path = player_dir / "player_frames.png"
        sheet_path = skin_sheet("player.png")
        torch_path = skin_sheet("player_phosphor.png")
        vela_path = skin_sheet("player_vela.png")
        antorcha_path = skin_sheet("player_antorcha.png")

        if skin_lib.sheet_path(skin_id, "player.png") is not None:
            frames_path = player_dir / "__sin_frames_viejos__.png"

        self.frame_scale = None

        if frames_path.exists():

            sheet = pygame.image.load(
                str(frames_path)
            ).convert_alpha()

            self.frames = self.load_frames(sheet)

        else:

            sheet = pygame.image.load(
                str(sheet_path)
            ).convert_alpha()

            self.frames = self.load_frames_from_sheet(sheet)

        self.frames_torch = None

        if torch_path.exists():

            torch_sheet = pygame.image.load(
                str(torch_path)
            ).convert_alpha()

            self.frames_torch = self.load_frames_from_sheet(
                torch_sheet,
                self.SHEET_RECTS_PHOSPHOR
            )

        self.frames_vela = None

        if vela_path.exists():

            vela_sheet = pygame.image.load(
                str(vela_path)
            ).convert_alpha()

            self.frames_vela = self.load_frames_from_sheet(
                vela_sheet,
                self.SHEET_RECTS_VELA
            )

        self.frames_antorcha = None

        if antorcha_path.exists():

            antorcha_sheet = pygame.image.load(
                str(antorcha_path)
            ).convert_alpha()

            self.frames_antorcha = self.load_frames_from_sheet(
                antorcha_sheet,
                self.SHEET_RECTS_ANTORCHA
            )

        # skin elegida en el menu (Skins): pinta el cuerpo claro del personaje
        self.frames = tint_frames(self.frames, skin_id)
        self.frames_torch = tint_frames(self.frames_torch, skin_id)
        self.frames_vela = tint_frames(self.frames_vela, skin_id)
        self.frames_antorcha = tint_frames(self.frames_antorcha, skin_id)

    def set_torch(self, value, kind="fosforo"):

        self.torch_kind = kind

        self.has_torch = bool(value) and (
            self.frames_torch is not None
            or self.frames_vela is not None
            or self.frames_antorcha is not None
        )


    def hurt(self, from_pos=None):

        if self.invuln_timer > 0 or self.grabbed:
            return False

        self.hurt_timer = self.HURT_TIME
        self.invuln_timer = self.INVULN_TIME

        self.hurt_anim = 1.0
        self._hurt_dir_x = 0.0

        if from_pos is not None:

            away = pygame.Vector2(self.rect.center) - pygame.Vector2(from_pos)

            if away.length_squared() > 0.01:
                self.kb_vel = away.normalize() * self.KNOCKBACK
                self._hurt_dir_x = max(-1.0, min(1.0, away.normalize().x))

        return True

    def jump(self):
        """Saltito. Solo se ve (no cambia colisiones ni dano)."""

        if self.jump_t > 0 or self.grabbed:
            return False

        self.jump_t = self.JUMP_TIME

        self._emit_dust(2, 0.8)

        return True

    @property
    def jump_height(self):
        """Cuanto esta despegado del piso ahora (pixeles del mundo)."""

        if self.jump_t <= 0:
            return 0.0

        p = 1.0 - self.jump_t / self.JUMP_TIME

        return self.JUMP_HEIGHT * 4.0 * p * (1.0 - p)

    def pop_step(self):
        """True una sola vez por cada pisada (para sincronizar el sonido)."""

        pending = self._step_pending
        self._step_pending = False

        return pending

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

                # las hojas nuevas ya vienen con transparencia; solo se limpia
                # el fondo si la hoja es opaca (formato viejo)
                if crop.get_at((0, 0))[3] == 255:
                    crop = self._remove_background(crop)

                crops[direction].append(crop)

                max_w = max(max_w, crop.get_width())
                max_h = max(max_h, crop.get_height())


        if self.frame_scale is None:

            # las celdas nuevas conservan la escala de las hojas originales
            # (1 pixel de hoja = 1 pixel de celda)
            self.frame_scale = 1.0

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

        if self.grabbed:

            result = (False, None)

        else:

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

        if self.jump_t > 0:

            self.jump_t = max(0.0, self.jump_t - dt)

            if self.jump_t == 0.0:
                self._emit_dust(3, 1.0)    # aterrizaje

        self._update_walk(dt)

    # ------------------------------------------------------------------
    # Animacion de caminata
    # ------------------------------------------------------------------

    FACING_VEC = {
        "up": (0.0, -1.0),
        "down": (0.0, 1.0),
        "left": (-1.0, 0.0),
        "right": (1.0, 0.0),
    }

    def _feet_world(self):

        return (float(self.rect.centerx), float(self.rect.bottom + 3))

    def _emit_dust(self, count, strength=1.0):

        fx, fy = self._feet_world()
        vx, vy = self.FACING_VEC[self.direction]

        self.dust.emit(fx, fy, -vx, -vy, count=count, strength=strength)

    def _update_walk(self, dt):

        dt = min(dt, 0.05)

        spd = max(0.6, min(1.7, float(self.movement.speed_mult)))

        self.idle_t += dt

        target = 1.0 if self.moving else 0.0
        rate = wa.START_RATE if self.moving else wa.STOP_RATE

        self.walk_blend = wa.smooth_toward(self.walk_blend, target, rate, dt)

        if not self.moving and self.walk_blend < 0.01:
            self.walk_blend = 0.0

        prev_phase = self.walk_phase

        if self.moving:

            if not self._was_moving:

                # arranque: primer paso con un poco de polvo
                self._finishing_step = False
                self._step_pending = True
                self._emit_dust(3, 1.2)
                self.settle = 0.0

            self.walk_phase = (
                self.walk_phase + dt / wa.CYCLE_TIME * spd
            ) % 1.0

            if wa.step_crossed(prev_phase, self.walk_phase):

                self._step_pending = True

                if self.walk_blend > 0.5:
                    self._emit_dust(2)

        else:

            if self._was_moving:

                # frenada: termina el paso que venia haciendo y se aplasta un poco
                self._finishing_step = True
                self.settle = 1.0

            if self._finishing_step:

                nxt = (int(self.walk_phase * 2.0) + 1) / 2.0

                self.walk_phase += dt / wa.CYCLE_TIME * spd * 1.6

                if self.walk_phase >= nxt:
                    self.walk_phase = nxt % 1.0
                    self._finishing_step = False

                self.walk_phase %= 1.0

        self._was_moving = self.moving

        if self.settle > 0:
            self.settle = max(0.0, self.settle - dt / wa.STOP_SETTLE_TIME)

        if self.hurt_anim > 0:
            self.hurt_anim = max(0.0, self.hurt_anim - dt / 0.45)

        if (
            not self.moving
            and not self._finishing_step
            and self.walk_blend < 0.05
        ):
            # quieto del todo: pies juntos
            self.animation_frame = self.IDLE_FRAME

        else:
            self.animation_frame = wa.frame_for_phase(
                self.walk_phase,
                self.WALK_FRAMES
            )

        self.dust.update(dt)

    def _scaled_frame(self, frames, height):

        key = (id(frames), self.direction, self.animation_frame, height)

        sprite = self._sprite_cache.get(key)

        if sprite is None:

            frame = frames[self.direction][self.animation_frame]

            scale = height / self.CELL_HEIGHT

            sprite = pygame.transform.smoothscale(
                frame,
                (round(self.CELL_WIDTH * scale), height)
            )

            self._sprite_cache[key] = sprite

        return key, sprite

    def _shadow(self, width, height, alpha):

        key = (width, height, alpha)

        shadow = self._shadow_cache.get(key)

        if shadow is None:

            shadow = pygame.Surface((width, height), pygame.SRCALPHA)

            pygame.draw.ellipse(shadow, (0, 0, 0, alpha), shadow.get_rect())

            self._shadow_cache[key] = shadow

        return shadow

    def _dust_sprite(self, radius, alpha):

        key = (radius, alpha)

        spr = self._dust_cache.get(key)

        if spr is None:

            spr = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)

            pygame.draw.circle(
                spr, (196, 186, 162, alpha), (radius + 1, radius + 1), radius
            )

            self._dust_cache[key] = spr

        return spr

    def _draw_dust(self, screen, camera):

        for p in self.dust.puffs:

            t = p["t"] / p["life"]

            radius = max(1, int((p["r"] + 1.6 * t) * camera.zoom))

            alpha = int(120 * (1.0 - t) ** 1.5 // 12 * 12)

            if alpha <= 0:
                continue

            pos = camera.apply(pygame.Rect(int(p["x"]), int(p["y"]), 0, 0)).topleft

            spr = self._dust_sprite(radius, alpha)

            screen.blit(spr, spr.get_rect(center=pos))

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

        height = self.image_rect.height

        if self.animation_frame >= len(frames[self.direction]):
            self.animation_frame = 0

        key, base = self._scaled_frame(frames, height)

        pose = wa.walk_pose(
            self.walk_phase,
            self.walk_blend,
            self.direction,
            idle_t=self.idle_t,
            settle=self.settle,
            hurt=self.hurt_anim,
            lean_in=self._hurt_dir_x,
        )

        feet = None

        if self.direction in ("up", "down") and wa.FOOT_LIFT > 0:

            feet = self._feet_cache.get(key)

            if feet is None:
                feet = wa.split_feet(base, pygame)
                self._feet_cache[key] = feet

        sprite, ofs_x, ofs_y = wa.compose_pose(base, feet, pose, pygame)

        anchor = camera.apply(self.image_rect).midbottom

        # --- polvo y sombra (debajo del personaje) ---
        self._draw_dust(screen, camera)

        lift = int(
            (max(0.0, self.grab_lift) + self.jump_height) * camera.zoom
        )

        sw = base.get_width()

        k = pose["contact"]

        shadow_w = int(sw * (0.50 + 0.07 * k) * (1.0 - min(0.5, lift / 60.0)))
        shadow_h = max(3, int(shadow_w * 0.30))
        shadow_a = int((60 + 34 * k) * (1.0 - min(0.6, lift / 60.0)) // 6 * 6)

        shadow = self._shadow(max(4, shadow_w), shadow_h, shadow_a)

        screen.blit(
            shadow,
            shadow.get_rect(center=(anchor[0], anchor[1] - 4))
        )

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

        elif (
            self.invuln_timer > 0
            and not self.grabbed
            and int(self.invuln_timer * 14) % 2
        ):

            sprite.set_alpha(140)

        screen.blit(
            sprite,
            (anchor[0] + ofs_x, anchor[1] + ofs_y - lift)
        )