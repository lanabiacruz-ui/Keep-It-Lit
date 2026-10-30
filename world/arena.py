import math
import random
from pathlib import Path

import pygame

from core.achievements import achievements
from core.audio_manager import audio
from world.fireball import FIRE_SPEED
from world import pathing
from world.items import (
    WorldItem, coin_id_for, split_coins, get_gem_icon, get_green_gem_icon
)
from world.boss_cinematic import BossCinematic
from world.boss import (
    PinaBoss, BossArt, draw_boss_bar, SUMMON_COUNT, CONTACT_PUSH, BOSS_NAME
)
from world.melee import (
    ARC_DEGREES, COOLDOWN, INNER_RADIUS, OUTER_RADIUS, SWING_TIME,
    ease_out, sector_outline,
)


BASE_DIR = Path(__file__).resolve().parent.parent

COMBAT_DIR = BASE_DIR / "assets" / "maps" / "combate"
CHEST_DIR = BASE_DIR / "assets" / "maps" / "cofre"
HUD_DIR = BASE_DIR / "assets" / "maps" / "hud"


ROOM = pygame.Rect(1244, 388, 436, 284)

TRIGGER = pygame.Rect(1262, 400, 400, 260)

EXIT_POS = (1190, 520)

GATE = pygame.Rect(1224, 498, 14, 44)


ROOM_LEFT = pygame.Rect(148, 336, 500, 408)
TRIGGER_LEFT = pygame.Rect(166, 348, 464, 384)
EXIT_POS_LEFT = (700, 518)
GATE_LEFT = pygame.Rect(660, 495, 14, 46)


LEFT_WAVE_COMPOSITION = {
    1: (1,1,3,1,1,0,0,0),
    2: (2,1,5,1,1,0,0,0), 
    3: (3,1,7,1,1,1,0,0), 
    4: (4,1,8,1,1,1,0,0), 
    5:  (5,2,9,2,2,1,1,0),
    6:  (6,3,10,3,3,1,1,0),
    7:  (7,4,12,4,4,2,1,0),
    8:  (8,5,13,5,5,3,2,1),
    9:  (9,6,14,6,6,4,3,2),
    10: (9,6,20,6,5,3,4,3),
}
WAVE_COMPOSITION = {
    1: (1, 0, 0, 0),
    2: (4, 0, 0, 0),
    3: (5, 1, 0, 0),
    4: (5, 2, 0, 0),
    5: (4, 4, 0, 0),

    6: (4, 7, 3, 0),

    7: (10, 5, 6, 0),

    8: (10, 5, 8, 1),
    9: (4, 6, 10, 3,),
    10: (5, 6, 7, 8,),
}
# Oleadas 1-10: normales. Oleada 11: jefe (Pina Colosal). La gema la da el jefe.
LAST_WAVE = 11

PINOS_STEP = 1
TRONCOS_STEP = 1
TRONCOS_MAX = 8
ENEMIES_MAX = 32
MOSQUITOS_STEP = 1
MOSQUITOS_MAX = 20
HONGUNS_STEP = 0
HONGUNS_MAX = 8
DESTELLOS_STEP = 0
DESTELLOS_MAX = 8
GOLEMS_STEP = 0
GOLEMS_MAX = 4

MOSQUITO_TEST_WAVE = 99
MOSQUITO_TEST_COUNT = 3

DESTELLO_TEST_WAVE = 98
DESTELLO_TEST_COUNT = 3

GOLEM_TEST_WAVE = 97
GOLEM_TEST_COUNT = 2

WAVE_REWARDS = {1: 100, 2: 200, 3: 300}
REWARD_STEP = 100
NO_ESCAPE_MULT = 2

ENEMY_HP_BASE = 2
ENEMY_HP_MAX = 10
ENEMY_SPEED_BASE = 58
ENEMY_SPEED_STEP = 4
ENEMY_SPEED_MAX = 90

ENEMY_DAMAGE = 0.08
ENEMY_DAMAGE_STEP = 0.01
ENEMY_DAMAGE_MAX = 0.15

ESCAPE_REVIVE_LIFE = 0.15

ESCAPE_GRACE = 2.5


ENEMY_DRAW_SIZE = 14
ENEMY_HITBOX = (12, 10)

ENEMY_BALL_MULT = 1.8
ENEMY_ACCEL = 320.0
ENEMY_BOUNCE_AIM = 0.85
ENEMY_BOUNCE_JITTER = 6.0
ENEMY_DRAG = 1.6
ENEMY_HIT_BOUNCE = 1.2
ENEMY_TOUCH_COOLDOWN = 0.6
WALL_BOUNCE = 1.0
ENEMY_KNOCKBACK = 150.0
ENEMY_STUN_TIME = 0.25
ENEMY_FLASH_TIME = 0.12
ENEMY_SPAWN_TIME = 0.8

# Segundos que duran los enemigos que invoca el jefe antes de irse
BOSS_MINION_LIFE = 35.0
ENEMY_ANIM_FRAME = 0.15
ENEMY_SPIN_RATE = 2.0
ENEMY_HOP_DIST = 38.0
ENEMY_HOP_HEIGHT = 3.0


TRONCO_HITBOX = (14, 12)
TRONCO_DRAW_SIZE = 16
TRONCO_HP_EXTRA = 0
TRONCO_FIRST_DELAY = (2.0, 3.0)
TRONCO_WINDUP = 1.0
TRONCO_SHOOT_TIME = 0.45
TRONCO_COOLDOWN = 8.0
TRONCO_HIT_PAUSE = 1.5
TRONCO_SHOTS = 3
TRONCO_SPREAD = 24.0
TRONCO_LEAD = 0.45
TRONCO_ANIM_FRAME = 0.12

TRONCO_SPEED = 70.0
TRONCO_KEEP_DIST = 60.0
TRONCO_MAX_DIST = 120.0
TRONCO_LIGHT_MARGIN = 14.0
TRONCO_BAND = 8.0
TRONCO_FIRE_EXTRA = 10.0

SHOT_SPEED = 95.0
SHOT_HITBOX = 6
SHOT_DRAW_SIZE = 8
SHOT_BOUNCES = 2
SHOT_LIFE = 7.0
SHOT_DAMAGE_MULT = 4.5


MOSQUITO_HP = 2
MOSQUITO_HITBOX = (9, 7)
MOSQUITO_DRAW_SIZE = 13

MOSQUITO_WANDER_SPEED = 45.0
MOSQUITO_TURN_TIME = (0.8, 2.2)

MOSQUITO_ALERT_MARGIN = 90.0

MOSQUITO_ATTACK_SPEED = 280.0
MOSQUITO_ATTACK_ACCEL = 900.0
MOSQUITO_ATTACH_DIST = 10.0

MOSQUITO_ATTACH_TIME = 60.0
MOSQUITO_REST_TIME = 60.0
MOSQUITO_FLEE_TIME = 8.0
MOSQUITO_FLEE_SPEED = 85.0

MOSQUITO_REPEL_REST = 4.0
MOSQUITO_REPEL_FLEE = 0.8

MOSQUITO_DAMAGE = 0.02
MOSQUITO_DAMAGE_INTERVAL = 1.0

MOSQUITO_ANIM_FRAME = 0.10
MOSQUITO_FLASH_TIME = 0.10
MOSQUITO_SPAWN_TIME = 0.8


HONGUN_HP = 6
HONGUN_HITBOX = (10, 12)
HONGUN_DRAW_SIZE = 18

HONGUN_WANDER_SPEED = 22.0
HONGUN_CHASE_SPEED = 70.0
HONGUN_TURN_TIME = (1.0, 2.6)

HONGUN_DETECT_RADIUS = 85.0
HONGUN_LOSE_RADIUS = 140.0

HONGUN_FUSE_DIST = 34.0
HONGUN_FUSE_CANCEL_DIST = 90.0
HONGUN_FUSE_WALK_SPEED = 48.0
HONGUN_FUSE_DECAY = 0.6
HONGUN_FUSE_TIME = 1.1
HONGUN_BLAST_RADIUS = 48.0
HONGUN_DAMAGE = 0.75
HONGUN_KNOCKBACK = 340.0
HONGUN_LIGHT_MIN = 24
HONGUN_LIGHT_MAX = 80
HONGUN_BLAST_TIME = 0.65

HONGUN_ANIM_FRAME = 0.15
HONGUN_CHARGE_FRAME = 0.12


DESTELLO_HP = 3
DESTELLO_HITBOX = (10, 12)
DESTELLO_DRAW_SIZE = 17

DESTELLO_WANDER_SPEED = 20.0
DESTELLO_CHARGE_SPEED = 175.0
DESTELLO_TURN_TIME = (1.0, 2.6)

DESTELLO_LIGHT = 40
DESTELLO_LIGHT_ALERT = 64

DESTELLO_DETECT_RADIUS = 120.0
DESTELLO_LOSE_RADIUS = 220.0
DESTELLO_ALERT_TIME = 0.35
DESTELLO_EARLY_WAVES = 2
DESTELLO_ALERT_TIME_EARLY = 0.60

DESTELLO_DAMAGE = 0.15
DESTELLO_KNOCKBACK = 200.0

DESTELLO_ANIM_FRAME = 0.15
DESTELLO_RUN_FRAME = 0.06
DESTELLO_ALERT_FRAME = 0.10


GOLEM_HP = 50
GOLEM_HITBOX = (16, 18)
GOLEM_DRAW_SIZE = 28

GOLEM_WANDER_SPEED = 12.0
GOLEM_CHASE_SPEED = 30.0
GOLEM_TURN_TIME = (1.8, 4.0)

GOLEM_DETECT_RADIUS = 110.0
GOLEM_LOSE_RADIUS = 200.0
GOLEM_CHASE_FOREVER = True
GOLEM_ALERT_TIME = 0.9

GOLEM_GRAB_REACH = 3
GOLEM_GRAB_TIME = 1.8
GOLEM_SQUEEZE_AT = 0.8
GOLEM_GRAB_LIFT = 5.0
GOLEM_HOLD_DY = 2
GOLEM_HOLD_PULL = 120.0
GOLEM_KNOCKBACK = 230.0
GOLEM_POST_INVULN = 1.5
GOLEM_REST_TIME = 3.0

GOLEM_HIT_PUSH = 14.0
GOLEM_ANIM_FRAME = 0.28
GOLEM_CHASE_FRAME = 0.20
GOLEM_ALERT_FRAME = 0.12
GOLEM_FLASH_TIME = 0.10
GOLEM_SPAWN_TIME = 1.0


BANNER_TIME = 3.0
BANNER_TIME_FINAL = 5.0
COLLECT_TIMEOUT = 60.0
MAX_COIN_ITEMS = 30


_images = {}
_fonts = {}


def load_image(path, size=None):

    key = (str(path), size)

    if key in _images:
        return _images[key]

    img = None

    if Path(path).exists():

        try:

            img = pygame.image.load(str(path)).convert_alpha()

            if size is not None and img.get_size() != size:
                img = pygame.transform.smoothscale(img, size)

        except pygame.error:
            img = None

    _images[key] = img

    return img


def get_font(size):

    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)

    return _fonts[size]


def draw_text(screen, text, size, color, **anchor):

    font = get_font(size)

    shadow = font.render(text, True, (0, 0, 0))
    label = font.render(text, True, color)

    rect = label.get_rect(**anchor)

    screen.blit(shadow, rect.move(2, 2))
    screen.blit(label, rect)

    return rect


_SHADOWS = {}


def get_shadow(size, alpha=90):

    w = max(1, int(size[0]))
    h = max(1, int(size[1]))

    key = (w, h, alpha)

    surf = _SHADOWS.get(key)

    if surf is None:

        if len(_SHADOWS) > 200:
            _SHADOWS.clear()

        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.ellipse(surf, (0, 0, 0, alpha), surf.get_rect())

        _SHADOWS[key] = surf

    return surf


def quantize_radius(radius):

    return max(8, int(round(radius / 8.0)) * 8)


def wave_composition(wave, table=None):
    if table is None:
        table = WAVE_COMPOSITION
    if table is WAVE_COMPOSITION:
        if wave == MOSQUITO_TEST_WAVE:
            return 0, 0, MOSQUITO_TEST_COUNT, 0, 0, 0, 0, 0
        if wave == DESTELLO_TEST_WAVE:
            return 0, 0, 0, 0, 0, 0, DESTELLO_TEST_COUNT, 0
        if wave == GOLEM_TEST_WAVE:
            return 0, 0, 0, 0, 0, 0, 0, GOLEM_TEST_COUNT
    if wave in table:
        return tuple(table[wave]) + (0,) * (8 - len(table[wave]))
    last = max(table)
    row = tuple(table[last]) + (0,) * (8 - len(table[last]))
    pinos, troncos, mosquitos, honguns, guardians, shooters, destellos, golems = row
    extra = max(0, wave - last)
    pinos += PINOS_STEP * extra
    troncos = min(TRONCOS_MAX, troncos + TRONCOS_STEP * extra)
    mosquitos = min(MOSQUITOS_MAX, mosquitos + MOSQUITOS_STEP * extra)
    honguns = min(HONGUNS_MAX, honguns + HONGUNS_STEP * extra)
    destellos = min(DESTELLOS_MAX, destellos + DESTELLOS_STEP * extra)
    golems = min(GOLEMS_MAX, golems + GOLEMS_STEP * extra)
    total = pinos + troncos + mosquitos + honguns + destellos + golems
    if total > ENEMIES_MAX:
        mosquitos = max(0, mosquitos - (total - ENEMIES_MAX))
    return (pinos, troncos, mosquitos, honguns, guardians, shooters,
            destellos, golems)


def enemies_for_wave(wave, table=None):

    return sum(wave_composition(wave, table))


def base_reward(wave, table=None):

    if table is None:
        table = WAVE_REWARDS

    if wave in table:
        return table[wave]

    last = max(table)

    return table[last] + REWARD_STEP * (wave - last)


class MosquitoArt:

    def __init__(self):

        idle = load_strip(
            COMBAT_DIR / "mosquito_anim.png"
        )

        single = load_image(
            COMBAT_DIR / "mosquito.png"
        )

        warning = load_image(
            COMBAT_DIR / "mosquito_advertencia.png"
        )

        if idle:

            self.frames = idle

        elif single is not None:

            self.frames = [single]

        else:

            self.frames = [
                self._placeholder()
            ]

        if warning is not None:

            self.warning = warning

        else:

            self.warning = self._warning_placeholder()

        self._zoom = None
        self._scaled = None
        self._warning_scaled = None

    @staticmethod
    def _placeholder():

        surf = pygame.Surface(
            (56, 56),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            surf,
            (45, 35, 40),
            (23, 19, 14, 25)
        )

        pygame.draw.ellipse(
            surf,
            (180, 45, 55),
            (25, 31, 10, 13)
        )

        pygame.draw.ellipse(
            surf,
            (205, 220, 225, 190),
            (8, 12, 24, 12)
        )

        pygame.draw.ellipse(
            surf,
            (205, 220, 225, 190),
            (24, 10, 24, 12)
        )

        pygame.draw.circle(
            surf,
            (240, 80, 90),
            (27, 20),
            3
        )

        pygame.draw.circle(
            surf,
            (240, 80, 90),
            (33, 20),
            3
        )

        pygame.draw.line(
            surf,
            (220, 220, 220),
            (30, 42),
            (30, 50),
            2
        )

        return surf

    @staticmethod
    def _warning_placeholder():

        surf = pygame.Surface(
            (48, 48),
            pygame.SRCALPHA
        )

        pygame.draw.polygon(
            surf,
            (255, 65, 65, 240),
            [
                (24, 4),
                (44, 40),
                (4, 40)
            ]
        )

        pygame.draw.polygon(
            surf,
            (20, 20, 25, 255),
            [
                (24, 11),
                (36, 35),
                (12, 35)
            ]
        )

        pygame.draw.rect(
            surf,
            (255, 80, 80),
            (22, 16, 4, 12)
        )

        pygame.draw.circle(
            surf,
            (255, 80, 80),
            (24, 33),
            2
        )

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(
                1,
                int(MOSQUITO_DRAW_SIZE * zoom)
            )

            self._scaled = [
                pygame.transform.scale(
                    frame,
                    (px, px)
                )
                for frame in self.frames
            ]

            warning_px = max(
                16,
                int(16 * zoom)
            )

            self._warning_scaled = (
                pygame.transform.smoothscale(
                    self.warning,
                    (warning_px, warning_px)
                )
            )

            self._zoom = zoom

        return (
            self._scaled,
            self._warning_scaled
        )

class EnemyArt:

    def __init__(self):

        sheet = load_image(COMBAT_DIR / "enemigo_anim.png")
        single = load_image(COMBAT_DIR / "enemigo.png")
        hit = load_image(COMBAT_DIR / "enemigo_golpe.png")

        frames = []

        if sheet is not None and sheet.get_height() > 0:

            fw = sheet.get_height()

            for i in range(max(1, sheet.get_width() // fw)):

                frames.append(
                    sheet.subsurface((i * fw, 0, fw, fw)).copy()
                )

        elif single is not None:
            frames.append(single)

        if not frames:
            frames.append(self._placeholder())

        if hit is None:

            hit = frames[0].copy()
            hit.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.frames = frames
        self.hit = hit

        self._zoom = None
        self._scaled = None
        self._scaled_hit = None

    @staticmethod
    def _placeholder():

        surf = pygame.Surface((56, 56), pygame.SRCALPHA)

        pygame.draw.circle(surf, (120, 80, 50), (28, 30), 22)
        pygame.draw.circle(surf, (50, 30, 20), (28, 30), 22, 3)
        pygame.draw.circle(surf, (20, 10, 10), (20, 26), 4)
        pygame.draw.circle(surf, (20, 10, 10), (36, 26), 4)

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(1, int(ENEMY_DRAW_SIZE * zoom))

            self._scaled = [
                pygame.transform.scale(f, (px, px)) for f in self.frames
            ]

            self._scaled_hit = pygame.transform.scale(self.hit, (px, px))

            self._zoom = zoom

        return self._scaled, self._scaled_hit


class Enemy:

    fixed = False
    contact_damage = True

    room = ROOM

    def __init__(self, x, y, hp, max_speed, spawn_delay=0.0):

        self.rect = pygame.Rect(0, 0, *ENEMY_HITBOX)
        self.rect.center = (round(x), round(y))

        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2()

        self.hp = hp
        self.max_hp = hp
        self.max_speed = max_speed

        self.ball_speed = max_speed * ENEMY_BALL_MULT

        self.flash = 0.0
        self.stun = 0.0
        self.touch_cd = 0.0

        self.spawn_t = ENEMY_SPAWN_TIME + spawn_delay

        self.anim_t = random.uniform(0, 1)
        self.last_target = pygame.Vector2(x, y)

        self.spin = random.uniform(0, 360)
        self.hop_t = random.uniform(0, 1)

    @property
    def dead(self):

        return self.hp <= 0

    @property
    def spawning(self):

        return self.spawn_t > 0


    def take_damage(self, amount):

        if self.spawning or self.dead:
            return 0

        self.hp -= amount
        self.flash = ENEMY_FLASH_TIME
        self.stun = ENEMY_STUN_TIME

        away = self.pos - self.last_target

        if away.length_squared() > 0.01:
            self.vel = away.normalize() * ENEMY_KNOCKBACK

        return amount

    def bounce_from(self, point):

        away = self.pos - pygame.Vector2(point)

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        self.vel = away.normalize() * self.ball_speed * ENEMY_HIT_BOUNCE
        self.touch_cd = ENEMY_TOUCH_COOLDOWN


    def update(self, dt, target, collision_map, others=None):

        self.last_target = pygame.Vector2(target)
        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt

            return

        to_target = pygame.Vector2(target) - self.pos

        if self.stun > 0:

            self.stun = max(0.0, self.stun - dt)
            self.vel *= max(0.0, 1.0 - ENEMY_DRAG * dt)

        else:

            self._keep_speed(dt, to_target)

        before = self.pos.copy()

        hit_x, hit_y = self._move(dt, collision_map)

        if hit_x or hit_y:
            self.aim_after_bounce(to_target, hit_x, hit_y)

        if not self._free(self.rect, collision_map):
            self._rescue(collision_map)

        moved = self.pos.distance_to(before)
        side = 1.0 if self.vel.x >= 0 else -1.0

        self.spin = (self.spin + side * moved * ENEMY_SPIN_RATE) % 360.0
        self.hop_t = (self.hop_t + moved / ENEMY_HOP_DIST) % 1.0

    def _keep_speed(self, dt, to_target):

        speed = self.vel.length()

        if speed < 1.0:

            if to_target.length_squared() > 0.01:
                direction = to_target.normalize()
            else:
                direction = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            direction = direction.rotate(
                random.uniform(-ENEMY_BOUNCE_JITTER, ENEMY_BOUNCE_JITTER)
            )

            self.vel = direction * self.ball_speed

            return

        if speed < self.ball_speed:
            speed = min(self.ball_speed, speed + ENEMY_ACCEL * dt)
        else:
            speed = max(self.ball_speed, speed - ENEMY_ACCEL * dt)

        self.vel.scale_to_length(speed)

    def aim_after_bounce(self, to_target, hit_x, hit_y, away=None):

        speed = self.vel.length()

        if speed < 1.0 or to_target.length_squared() < 0.01:
            return

        current = self.vel / speed
        want = to_target.normalize()

        mix = current * (1.0 - ENEMY_BOUNCE_AIM) + want * ENEMY_BOUNCE_AIM

        if mix.length_squared() < 0.0001:
            return

        mix = mix.normalize().rotate(
            random.uniform(-ENEMY_BOUNCE_JITTER, ENEMY_BOUNCE_JITTER)
        )

        if hit_x and mix.x * current.x < 0:
            mix.x = current.x * 0.3

        if hit_y and mix.y * current.y < 0:
            mix.y = current.y * 0.3

        if away is not None and mix.dot(away) < 0:
            mix = mix - away * mix.dot(away) + away * 0.3

        if mix.length_squared() < 0.0001:
            return

        self.vel = mix.normalize() * speed

    def _free(self, rect, collision_map):

        return self.room.contains(rect) and collision_map.can_move(rect)

    def _move(self, dt, collision_map):

        hit_x = False
        hit_y = False

        nx = self.pos.x + self.vel.x * dt
        test = self.rect.copy()
        test.centerx = round(nx)

        if self._free(test, collision_map):

            self.pos.x = nx
            self.rect.centerx = test.centerx

        else:

            hit_x = True
            self.vel.x = -self.vel.x * WALL_BOUNCE

        ny = self.pos.y + self.vel.y * dt
        test = self.rect.copy()
        test.centery = round(ny)

        if self._free(test, collision_map):

            self.pos.y = ny
            self.rect.centery = test.centery

        else:

            hit_y = True
            self.vel.y = -self.vel.y * WALL_BOUNCE

        return hit_x, hit_y

    def push(self, offset, collision_map):

        nx = self.pos.x + offset.x
        test = self.rect.copy()
        test.centerx = round(nx)

        if self._free(test, collision_map):
            self.pos.x = nx
            self.rect.centerx = test.centerx

        ny = self.pos.y + offset.y
        test = self.rect.copy()
        test.centery = round(ny)

        if self._free(test, collision_map):
            self.pos.y = ny
            self.rect.centery = test.centery


    NAV_REPLAN = 0.35
    STUCK_CHECK = 0.25
    STUCK_MIN_MOVE = 1.2

    def _nav_init(self):

        if getattr(self, "_nav_ready", False):
            return

        self._nav_ready = True
        self._nav_path = []
        self._nav_t = random.uniform(0.0, self.NAV_REPLAN)
        self._nav_force = 0.0

        self._stk_pos = self.pos.copy()
        self._stk_clock = 0.0
        self._stk_time = 0.0
        self._stk_stage = 0

        self._esc_t = 0.0
        self._esc_dir = pygame.Vector2()

        self.last_good = self.pos.copy()

    def _body_line_free(self, a, b, collision_map):

        a = pygame.Vector2(a)
        b = pygame.Vector2(b)

        steps = max(1, int(a.distance_to(b) // 5))

        probe = self.rect.copy()

        for i in range(1, steps + 1):

            p = a.lerp(b, i / steps)

            probe.center = (round(p.x), round(p.y))

            if not self._free(probe, collision_map):
                return False

        return True

    def nav_dir(self, goal, collision_map, dt):

        self._nav_init()

        goal = pygame.Vector2(goal)

        self._nav_t -= dt
        self._nav_force = max(0.0, self._nav_force - dt)

        if self._nav_t <= 0:

            self._nav_t = self.NAV_REPLAN + random.uniform(0.0, 0.15)

            if (
                self._nav_force <= 0
                and self._body_line_free(self.pos, goal, collision_map)
            ):
                self._nav_path = []

            elif not pathing.take_budget():

                self._nav_t = 0.03

            else:

                path = pathing.find_path(
                    self.pos, goal, self.rect.size, self.room, collision_map
                )

                self._nav_path = path or []

        while self._nav_path and self.pos.distance_to(self._nav_path[0]) < 4.0:
            self._nav_path.pop(0)

        if len(self._nav_path) > 1 and self._body_line_free(
            self.pos, self._nav_path[1], collision_map
        ):
            self._nav_path.pop(0)

        aim = pygame.Vector2(self._nav_path[0]) if self._nav_path else goal

        d = aim - self.pos

        if d.length_squared() < 0.01:
            d = goal - self.pos

        if d.length_squared() < 0.01:
            return pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        return d.normalize()

    def _nudge(self, dt, direction, speed, collision_map):

        step = speed * dt

        for angle in (0, 45, -45):

            d = direction.rotate(angle)

            test = self.rect.copy()
            test.center = (
                round(self.pos.x + d.x * step),
                round(self.pos.y + d.y * step),
            )

            if self._free(test, collision_map):

                self.pos.update(
                    self.pos.x + d.x * step, self.pos.y + d.y * step
                )
                self.rect.center = test.center

                return True

        return False

    def _random_open_dir(self, collision_map):

        angles = list(range(0, 360, 45))
        random.shuffle(angles)

        for angle in angles:

            d = pygame.Vector2(1, 0).rotate(angle)

            test = self.rect.copy()
            test.center = (
                round(self.pos.x + d.x * 8),
                round(self.pos.y + d.y * 8),
            )

            if self._free(test, collision_map):
                return d

        return pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

    def _teleport(self, point):

        self.pos.update(point[0], point[1])
        self.rect.center = (round(point[0]), round(point[1]))

        self.vel = pygame.Vector2()
        self._nav_path = []
        self._nav_t = 0.0

    def _rescue(self, collision_map):

        self._nav_init()

        spot = pathing.nearest_free(
            self.last_good, self.rect.size, self.room, collision_map
        )

        if spot is None or self.pos.distance_to(spot) < 3.0:

            spot = pathing.nearest_free(
                self.pos, self.rect.size, self.room, collision_map
            )

        if spot is not None and self.pos.distance_to(spot) >= 3.0:
            self._teleport(spot)

        self._stk_time = 0.0
        self._stk_stage = 0
        self._stk_pos = self.pos.copy()

    def anti_stuck(self, dt, collision_map, goal=None, speed=40.0):

        self._nav_init()

        if not self._free(self.rect, collision_map):

            self._rescue(collision_map)

            return True

        if self._esc_t > 0:

            self._esc_t -= dt
            self._nudge(dt, self._esc_dir, speed, collision_map)

        self._stk_clock += dt

        if self._stk_clock < self.STUCK_CHECK:
            return False

        self._stk_clock = 0.0

        moved = self.pos.distance_to(self._stk_pos)
        self._stk_pos = self.pos.copy()

        if goal is not None and self.pos.distance_to(goal) < 14.0:

            self._stk_time = 0.0
            self._stk_stage = 0

            return False

        if moved >= self.STUCK_MIN_MOVE:

            self._stk_time = 0.0
            self._stk_stage = 0
            self.last_good = self.pos.copy()

            return False

        self._stk_time += self.STUCK_CHECK

        if self._stk_time >= 3.0:

            self._rescue(collision_map)

            return True

        if self._stk_time >= 1.5 and self._stk_stage < 2:

            self._stk_stage = 2
            self._esc_dir = self._random_open_dir(collision_map)
            self._esc_t = 0.8
            self._nav_force = 2.0
            self._nav_t = 0.0

            return True

        if self._stk_time >= 0.5 and self._stk_stage < 1:

            self._stk_stage = 1
            self._esc_dir = self._random_open_dir(collision_map)
            self._esc_t = 0.45
            self._nav_force = 1.5
            self._nav_t = 0.0

            return True

        return False


    def draw(self, screen, camera, art):

        frames, hit = art.get(camera.zoom)

        if self.flash > 0:

            img = hit

        else:

            img = frames[0]

            if self.hp < self.max_hp:

                shade = int(255 * (0.55 + 0.45 * self.hp / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

        if not self.spawning:
            img = pygame.transform.rotate(img, self.spin)

        if self.spawning:

            k = 1.0 - max(0.0, self.spawn_t) / ENEMY_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, k))))

        dest = camera.apply(self.rect)

        hop = 0
        if not self.spawning:
            hop = int(
                abs(math.sin(self.hop_t * math.pi))
                * ENEMY_HOP_HEIGHT * camera.zoom
            )

        shadow = get_shadow((int(dest.width * 1.3), int(dest.height * 0.6)), 90)

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            img,
            img.get_rect(
                center=(dest.centerx, dest.centery - hop)
            )
        )


def _overlap_depth(a, b):

    overlap_x = min(a.rect.right, b.rect.right) - max(a.rect.left, b.rect.left)
    overlap_y = min(a.rect.bottom, b.rect.bottom) - max(a.rect.top, b.rect.top)

    return max(1.0, min(overlap_x, overlap_y))


def bounce_enemies(enemies, collision_map, target=None):

    live = [e for e in enemies if not e.spawning and not e.dead and not getattr(e, "attached", False)]

    for i, a in enumerate(live):

        for b in live[i + 1:]:

            if not a.rect.colliderect(b.rect):
                continue

            normal = b.pos - a.pos

            if normal.length_squared() < 0.01:
                normal = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            normal = normal.normalize()

            if a.fixed and b.fixed:

                depth = _overlap_depth(a, b) / 2.0 + 1.0

                a.push(-normal * depth, collision_map)
                b.push(normal * depth, collision_map)

                continue

            if a.fixed or b.fixed:

                mobile, wall = (b, a) if a.fixed else (a, b)

                away = mobile.pos - wall.pos

                if away.length_squared() < 0.01:
                    away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

                away = away.normalize()

                closing = mobile.vel.dot(away)

                if closing < 0:

                    mobile.vel -= away * (2.0 * closing)

                    if target is not None:

                        mobile.aim_after_bounce(
                            pygame.Vector2(target) - mobile.pos,
                            False, False, away
                        )

                mobile.push(away * (_overlap_depth(a, b) + 1.0), collision_map)

                continue

            closing = (a.vel - b.vel).dot(normal)

            if closing > 0:

                a.vel -= normal * closing
                b.vel += normal * closing

                for e, sign in ((a, -1), (b, 1)):

                    if e.vel.length() < 40:
                        e.vel = normal * sign * max(40.0, e.ball_speed * 0.6)

                if target is not None:

                    a.aim_after_bounce(
                        pygame.Vector2(target) - a.pos, False, False, -normal
                    )
                    b.aim_after_bounce(
                        pygame.Vector2(target) - b.pos, False, False, normal
                    )

            depth = _overlap_depth(a, b) / 2.0 + 1.0

            a.push(-normal * depth, collision_map)
            b.push(normal * depth, collision_map)


def load_strip(path):

    sheet = load_image(path)

    if sheet is None or sheet.get_height() <= 0:
        return []

    fw = sheet.get_height()

    return [
        sheet.subsurface((i * fw, 0, fw, fw)).copy()
        for i in range(max(1, sheet.get_width() // fw))
    ]

class Mosquito(Enemy):

    fixed = False
    contact_damage = False

    def __init__(self, x, y, hp, spawn_delay=0.0):

        super().__init__(x, y, hp, MOSQUITO_ATTACK_SPEED, spawn_delay)

        self.rect = pygame.Rect(0, 0, *MOSQUITO_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = "wander"

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*MOSQUITO_TURN_TIME)

        self.attack_vel = pygame.Vector2()
        self.flash = 0.0

        self.attached = False
        self.attach_offset = pygame.Vector2()
        self.attach_t = 0.0

        self.rest_t = 0.0
        self.flee_t = 0.0

        self.returning = False

        self.alert = False

        self.damage_t = random.uniform(0, MOSQUITO_DAMAGE_INTERVAL)
        self.anim_t = random.uniform(0, 1)

    @property
    def dead(self):

        return self.hp <= 0

    @property
    def spawning(self):

        return self.spawn_t > 0

    def take_damage(self, amount):

        if self.spawning or self.dead or self.attached:
            return 0

        self.hp -= amount
        self.flash = MOSQUITO_FLASH_TIME

        if self.phase == "wander":
            self._start_attack()

        return amount

    def _repelled(self, target, light_radius, dt, collision_map):

        if self.attached:

            self._detach(target)

            self.rest_t = max(self.rest_t, MOSQUITO_REPEL_REST)

            return True

        away = self.pos - target
        dist = away.length()

        if dist > light_radius:
            return False

        if dist < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        else:
            away = away / dist

        self.alert = False
        self.returning = False
        self.phase = "leave"
        self.rest_t = max(self.rest_t, MOSQUITO_REPEL_REST)
        self.flee_t = max(self.flee_t, MOSQUITO_REPEL_FLEE)

        self.heading = away

        self._wander(dt, collision_map, MOSQUITO_FLEE_SPEED, turn=False)

        return True

    def _start_attack(self):

        self.phase = "attack"

        to_player = self.last_target - self.pos

        if to_player.length_squared() < 0.01:
            to_player = pygame.Vector2(1, 0)

        self.attack_vel = to_player.normalize() * MOSQUITO_ATTACK_SPEED

    def _detach(self, target):

        self.attached = False
        self.phase = "leave"
        self.rest_t = MOSQUITO_REST_TIME
        self.flee_t = MOSQUITO_FLEE_TIME
        self.returning = False

        away = self.pos - target

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        self.heading = away.normalize()
        self.turn_t = random.uniform(*MOSQUITO_TURN_TIME)

    def update(self, dt, target, collision_map, light_on, light_radius,
               repel=False):

        target = pygame.Vector2(target)
        self.last_target = target.copy()

        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.spawning:
            self.spawn_t -= dt
            return


        if repel and self._repelled(target, light_radius, dt, collision_map):
            return


        if self.attached:

            self.alert = False
            self.attach_t -= dt
            self.damage_t -= dt

            self.pos = target + self.attach_offset
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.attach_t <= 0:
                self._detach(target)

            return

        to_player = target - self.pos
        dist = max(0.01, to_player.length())
        toward = to_player / dist


        if self.phase == "attack":

            self.alert = self.returning

            desired = toward * MOSQUITO_ATTACK_SPEED

            self.attack_vel += (desired - self.attack_vel) * min(
                1.0,
                MOSQUITO_ATTACK_ACCEL * dt / max(1.0, MOSQUITO_ATTACK_SPEED)
            )

            self.vel = self.attack_vel.copy()
            self._move(dt, collision_map)

            if self.pos.distance_to(target) <= MOSQUITO_ATTACH_DIST:

                self.attached = True
                self.alert = False
                self.attach_t = MOSQUITO_ATTACH_TIME

                offset = self.pos - target

                if offset.length_squared() < 0.01:
                    offset = pygame.Vector2(0, -10)

                if offset.length() > 16:
                    offset.scale_to_length(16)

                self.attach_offset = offset
                self.vel = pygame.Vector2()
                self.attack_vel = pygame.Vector2()
                self.damage_t = MOSQUITO_DAMAGE_INTERVAL

            return


        if self.phase == "leave":

            self.alert = False
            self.rest_t -= dt

            if self.rest_t <= 0:

                self.returning = True
                self._start_attack()

                return

            if self.flee_t > 0:

                self.flee_t -= dt

                self.heading = -toward

                self._wander(dt, collision_map, MOSQUITO_FLEE_SPEED, turn=False)

            else:

                self._wander(dt, collision_map, MOSQUITO_WANDER_SPEED)

            return


        if light_on and dist <= light_radius:

            self.alert = False
            self._start_attack()

            return

        self.alert = light_on and dist <= light_radius + MOSQUITO_ALERT_MARGIN

        self._wander(dt, collision_map, MOSQUITO_WANDER_SPEED)

    def _wander(self, dt, collision_map, speed, turn=True):

        if turn:

            self.turn_t -= dt

            if self.turn_t <= 0:

                self.heading = self.heading.rotate(random.uniform(-70, 70))
                self.turn_t = random.uniform(*MOSQUITO_TURN_TIME)

        step = speed * dt

        for angle in (0, 40, -40, 90, -90, 140, -140, 180):

            d = self.heading.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center

                if angle:
                    self.heading = d
                    self.turn_t = random.uniform(*MOSQUITO_TURN_TIME)

                return

    def draw(self, screen, camera, art):

        frames, _ = art.get(camera.zoom)

        frame = frames[int(self.anim_t / MOSQUITO_ANIM_FRAME) % len(frames)]

        if self.attached:

            frame = pygame.transform.smoothscale(
                frame,
                (max(1, int(frame.get_width() * 0.85)),
                 max(1, int(frame.get_height() * 0.85)))
            )

            center = camera.apply(self.rect).center
            screen.blit(frame, frame.get_rect(center=center))

            return

        if self.flash > 0:
            frame = frame.copy()
            frame.fill((255, 255, 255, 90), special_flags=pygame.BLEND_RGBA_ADD)

        dest = camera.apply(self.rect)
        screen.blit(frame, frame.get_rect(center=dest.center))

class TroncoArt:

    def __init__(self):

        idle = load_strip(COMBAT_DIR / "tronco.png")
        charge = load_strip(COMBAT_DIR / "tronco_carga.png")
        shoot = load_strip(COMBAT_DIR / "tronco_disparo.png")
        hit = load_image(COMBAT_DIR / "tronco_golpe.png")
        shot = load_image(COMBAT_DIR / "bola_enemiga.png")

        self.idle = idle or [self._placeholder("idle")]
        self.charge = charge or [
            self._placeholder("charge", k) for k in (0.4, 1.0)
        ]
        self.shoot = shoot or [
            self._placeholder("shoot", k) for k in (0.0, 0.5, 1.0)
        ]

        if hit is None:

            hit = self.idle[0].copy()
            hit.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.hit = hit
        self.shot = shot if shot is not None else self._shot_placeholder()

        self._zoom = None
        self._scaled = None

    @staticmethod
    def _placeholder(mode, k=0.0):

        surf = pygame.Surface((56, 56), pygame.SRCALPHA)

        pygame.draw.rect(surf, (118, 78, 44), (12, 8, 32, 44), border_radius=6)
        pygame.draw.rect(surf, (60, 36, 18), (12, 8, 32, 44), 3, border_radius=6)
        pygame.draw.line(surf, (80, 50, 26), (20, 14), (20, 46), 2)
        pygame.draw.line(surf, (80, 50, 26), (36, 14), (36, 46), 2)

        pygame.draw.circle(surf, (20, 10, 10), (22, 20), 3)
        pygame.draw.circle(surf, (20, 10, 10), (34, 20), 3)

        mouth_h = 4 + int(10 * k) if mode != "idle" else 3
        color = (20, 10, 10) if mode == "idle" else (
            255, int(140 - 80 * k), 40
        )

        pygame.draw.ellipse(
            surf, color, (22, 30, 12, mouth_h)
        )

        return surf

    @staticmethod
    def _shot_placeholder():

        surf = pygame.Surface((24, 24), pygame.SRCALPHA)

        pygame.draw.circle(surf, (255, 90, 40, 110), (12, 12), 12)
        pygame.draw.circle(surf, (255, 150, 60), (12, 12), 8)
        pygame.draw.circle(surf, (255, 235, 170), (12, 12), 4)

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            tpx = max(1, int(TRONCO_DRAW_SIZE * zoom))
            spx = max(1, int(SHOT_DRAW_SIZE * zoom))

            def scale(frames):
                return [pygame.transform.scale(f, (tpx, tpx)) for f in frames]

            self._scaled = {
                "idle": scale(self.idle),
                "charge": scale(self.charge),
                "shoot": scale(self.shoot),
                "hit": pygame.transform.scale(self.hit, (tpx, tpx)),
                "shot": pygame.transform.scale(self.shot, (spx, spx)),
            }

            self._zoom = zoom

        return self._scaled


class Shot:

    room = ROOM

    def __init__(self, pos, angle):

        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(SHOT_SPEED, 0).rotate(angle)

        self.rect = pygame.Rect(0, 0, SHOT_HITBOX, SHOT_HITBOX)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.bounces_left = SHOT_BOUNCES
        self.life = SHOT_LIFE
        self.t = 0.0
        self.dead = False

    def _free(self, rect, collision_map):

        return self.room.contains(rect) and collision_map.can_move(rect)

    def update(self, dt, collision_map):

        self.t += dt
        self.life -= dt

        if self.life <= 0:

            self.dead = True

            return

        hit = False

        nx = self.pos.x + self.vel.x * dt
        test = self.rect.copy()
        test.centerx = round(nx)

        if self._free(test, collision_map):

            self.pos.x = nx
            self.rect.centerx = test.centerx

        else:

            hit = True
            self.vel.x = -self.vel.x

        ny = self.pos.y + self.vel.y * dt
        test = self.rect.copy()
        test.centery = round(ny)

        if self._free(test, collision_map):

            self.pos.y = ny
            self.rect.centery = test.centery

        else:

            hit = True
            self.vel.y = -self.vel.y

        if hit:

            if self.bounces_left <= 0:
                self.dead = True
            else:
                self.bounces_left -= 1

    def draw(self, screen, camera, art):

        img = art.get(camera.zoom)["shot"]

        pulse = 0.85 + 0.15 * math.sin(self.t * 14)

        size = max(1, int(img.get_width() * pulse))

        if size != img.get_width():
            img = pygame.transform.scale(img, (size, size))

        center = camera.apply(self.rect).center

        screen.blit(img, img.get_rect(center=center))


class Tronco(Enemy):

    fixed = True
    contact_damage = False

    IDLE = "idle"
    WINDUP = "windup"
    SHOOT = "shoot"

    def __init__(self, x, y, hp, spawn_delay=0.0):

        super().__init__(x, y, hp, TRONCO_SPEED, spawn_delay)

        self.rect = pygame.Rect(0, 0, *TRONCO_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.IDLE
        self.phase_t = random.uniform(*TRONCO_FIRST_DELAY)

        self.light_radius = 0.0

        self.target_vel = pygame.Vector2()
        self._prev_target = None

        self._shots = []


    def take_damage(self, amount):

        result = super().take_damage(amount)

        if result and self.phase == self.WINDUP:

            self.phase = self.IDLE
            self.phase_t = TRONCO_HIT_PAUSE

        return result


    def take_shots(self):

        shots, self._shots = self._shots, []

        return shots

    def _fire(self, target):

        aim = pygame.Vector2(target) + self.target_vel * TRONCO_LEAD

        aim.x = max(self.room.left + 4, min(self.room.right - 4, aim.x))
        aim.y = max(self.room.top + 4, min(self.room.bottom - 4, aim.y))

        direction = aim - self.pos

        if direction.length_squared() < 0.01:
            direction = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        base = pygame.Vector2(1, 0).angle_to(direction)

        for k in range(TRONCO_SHOTS):

            offset = (k - (TRONCO_SHOTS - 1) / 2.0) * TRONCO_SPREAD

            shot = Shot(self.pos, base + offset)
            shot.room = self.room
            self._shots.append(shot)


    def _ideal_distance(self):

        want = max(
            TRONCO_KEEP_DIST, self.light_radius + TRONCO_LIGHT_MARGIN
        )

        return min(TRONCO_MAX_DIST, want)

    def _walk(self, dt, direction, collision_map):

        step = TRONCO_SPEED * dt

        for angle in (0, 45, -45, 90, -90):

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center

                return True

        return False

    def update(self, dt, target, collision_map, others=None):

        target = pygame.Vector2(target)

        self.last_target = target.copy()
        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt
            self._prev_target = target

            return

        if self._prev_target is not None and dt > 0:

            raw = (target - self._prev_target) / dt

            self.target_vel += (raw - self.target_vel) * min(1.0, dt * 8.0)

        self._prev_target = target

        if self.stun > 0:

            self.stun = max(0.0, self.stun - dt)
            self.vel *= max(0.0, 1.0 - 6.0 * dt)

            hit_x, hit_y = self._move(dt, collision_map)

            if hit_x or hit_y:
                self.vel = pygame.Vector2()

            return

        self.vel = pygame.Vector2()

        if self.phase == self.WINDUP:

            self.phase_t -= dt

            if self.phase_t <= 0:

                self._fire(target)

                self.phase = self.SHOOT
                self.phase_t = TRONCO_SHOOT_TIME

            return

        if self.phase == self.SHOOT:

            self.phase_t -= dt

            if self.phase_t <= 0:

                self.phase = self.IDLE
                self.phase_t = TRONCO_COOLDOWN

            return

        self.phase_t = max(0.0, self.phase_t - dt)

        to_player = target - self.pos
        dist = to_player.length()

        if dist < 0.01:
            to_player = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            dist = 0.01

        toward = to_player / dist

        ideal = self._ideal_distance()

        if dist > ideal + TRONCO_BAND:

            self._walk(
                dt, self.nav_dir(target, collision_map, dt), collision_map
            )

            self.anti_stuck(dt, collision_map, target, TRONCO_SPEED)

        elif dist < ideal - TRONCO_BAND:

            self._walk(dt, -toward, collision_map)

        if (
            self.phase_t <= 0
            and dist <= ideal + TRONCO_BAND + TRONCO_FIRE_EXTRA
        ):

            self.phase = self.WINDUP
            self.phase_t = TRONCO_WINDUP


    def draw(self, screen, camera, art):

        sprites = art.get(camera.zoom)

        shake = 0

        if self.flash > 0:

            img = sprites["hit"]

        else:

            if self.phase == self.WINDUP:

                frames = sprites["charge"]
                index = int(self.anim_t / TRONCO_ANIM_FRAME) % len(frames)

                k = 1.0 - max(0.0, self.phase_t) / TRONCO_WINDUP
                shake = int(math.sin(self.anim_t * 55) * 1.5 * k * camera.zoom)

            elif self.phase == self.SHOOT:

                frames = sprites["shoot"]
                progress = 1.0 - max(0.0, self.phase_t) / TRONCO_SHOOT_TIME
                index = min(len(frames) - 1, int(progress * len(frames)))

            else:

                frames = sprites["idle"]
                index = int(self.anim_t / (TRONCO_ANIM_FRAME * 4)) % len(frames)

            img = frames[index]

            if self.hp < self.max_hp:

                shade = int(255 * (0.55 + 0.45 * self.hp / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

        if self.spawning:

            k = 1.0 - max(0.0, self.spawn_t) / ENEMY_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, k))))

        dest = camera.apply(self.rect)

        shadow = get_shadow((int(dest.width * 1.3), int(dest.height * 0.6)), 90)

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx + shake,
                    dest.bottom + int(2 * camera.zoom)
                )
            )
        )


class HongunArt:

    def __init__(self):

        walk = load_strip(COMBAT_DIR / "hongun_anim.png")
        single = load_strip(COMBAT_DIR / "hongun.png")
        charge = load_strip(COMBAT_DIR / "hongun_carga.png")
        hit = load_image(COMBAT_DIR / "hongun_golpe.png")

        self.walk = walk or single or [self._placeholder(0), self._placeholder(1)]
        self.charge = charge or [self.walk[0], self.walk[0]]

        if hit is None:

            hit = self.walk[0].copy()
            hit.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.hit = hit

        self._zoom = None
        self._scaled = None

    @staticmethod
    def _placeholder(step=0):

        surf = pygame.Surface((56, 56), pygame.SRCALPHA)

        dark = (40, 120, 50)
        mid = (80, 175, 80)
        light = (120, 205, 110)

        pygame.draw.rect(surf, mid, (14, 6, 28, 30))
        pygame.draw.rect(surf, dark, (14, 6, 28, 30), 2)

        for x, y in ((18, 10), (32, 12), (22, 28), (34, 26)):
            pygame.draw.rect(surf, light, (x, y, 6, 6))

        off = 2 if step % 2 == 0 else -2

        pygame.draw.rect(surf, dark, (14 + off, 36, 12, 14))
        pygame.draw.rect(surf, dark, (30 - off, 36, 12, 14))

        pygame.draw.rect(surf, (15, 40, 20), (19, 14, 6, 6))
        pygame.draw.rect(surf, (15, 40, 20), (31, 14, 6, 6))
        pygame.draw.rect(surf, (15, 40, 20), (25, 20, 6, 10))
        pygame.draw.rect(surf, (15, 40, 20), (21, 24, 4, 8))
        pygame.draw.rect(surf, (15, 40, 20), (31, 24, 4, 8))

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(1, int(HONGUN_DRAW_SIZE * zoom))

            def scale(frames):
                return [pygame.transform.scale(f, (px, px)) for f in frames]

            self._scaled = {
                "walk": scale(self.walk),
                "charge": scale(self.charge),
                "hit": pygame.transform.scale(self.hit, (px, px)),
            }

            self._zoom = zoom

        return self._scaled


class Hongun(Enemy):

    fixed = False
    contact_damage = False

    WANDER = "wander"
    CHASE = "chase"
    FUSE = "fuse"

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, HONGUN_HP, HONGUN_CHASE_SPEED, spawn_delay)

        self.rect = pygame.Rect(0, 0, *HONGUN_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.WANDER

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*HONGUN_TURN_TIME)

        self.fuse_t = 0.0
        self.boom = False
        self.boomed = False


    @property
    def fuse_k(self):

        return max(0.0, min(1.0, self.fuse_t / HONGUN_FUSE_TIME))

    def light(self):

        if self.fuse_t <= 0.0 or self.spawning or self.dead:
            return None

        k = self.fuse_k

        return (
            self.pos.x, self.pos.y,
            quantize_radius(
                HONGUN_LIGHT_MIN + (HONGUN_LIGHT_MAX - HONGUN_LIGHT_MIN) * k
            )
        )


    def take_damage(self, amount):

        if self.spawning or self.dead:
            return 0

        self.hp -= amount
        self.flash = ENEMY_FLASH_TIME

        if self.phase == self.WANDER:
            self.phase = self.CHASE

        return amount


    def _walk(self, dt, direction, speed, collision_map,
              angles=(0, 45, -45, 90, -90)):

        step = speed * dt

        for angle in angles:

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center
                self.vel = d * speed

                return d

        return None

    def update(self, dt, target, collision_map, others=None):

        target = pygame.Vector2(target)

        self.last_target = target.copy()
        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt

            return

        self.vel = pygame.Vector2()

        to_player = target - self.pos
        dist = to_player.length()

        if dist < 0.01:
            to_player = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            dist = 0.01

        toward = to_player / dist

        if self.phase == self.FUSE:

            if dist > HONGUN_FUSE_CANCEL_DIST:

                self.phase = self.CHASE

            else:

                self.fuse_t += dt

                if self.fuse_t >= HONGUN_FUSE_TIME:

                    self.boom = True
                    self.hp = 0

                    return

                if dist > 14.0:

                    self._walk(
                        dt, toward, HONGUN_FUSE_WALK_SPEED, collision_map
                    )

                return

        if self.fuse_t > 0:
            self.fuse_t = max(0.0, self.fuse_t - dt * HONGUN_FUSE_DECAY)

        if self.phase == self.CHASE:

            if dist > HONGUN_LOSE_RADIUS:

                self.phase = self.WANDER
                self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            elif dist <= HONGUN_FUSE_DIST:

                self.phase = self.FUSE
                self.fuse_t = max(self.fuse_t, 0.001)

            else:

                self._walk(
                    dt,
                    self.nav_dir(target, collision_map, dt),
                    HONGUN_CHASE_SPEED,
                    collision_map,
                )

                self.anti_stuck(
                    dt, collision_map, target, HONGUN_CHASE_SPEED
                )

            return

        if dist <= HONGUN_DETECT_RADIUS:

            self.phase = self.CHASE

            return

        self.turn_t -= dt

        if self.turn_t <= 0:

            self.heading = self.heading.rotate(random.uniform(-80, 80))
            self.turn_t = random.uniform(*HONGUN_TURN_TIME)

        d = self._walk(
            dt, self.heading, HONGUN_WANDER_SPEED, collision_map,
            angles=(0, 40, -40, 90, -90, 140, -140, 180)
        )

        if d is not None:
            self.heading = d

        if self.anti_stuck(dt, collision_map, None, HONGUN_WANDER_SPEED):
            self.heading = self._random_open_dir(collision_map)


    def draw(self, screen, camera, art):

        sprites = art.get(camera.zoom)

        shake = 0
        k = self.fuse_k
        fusing = self.phase == self.FUSE and self.fuse_t > 0

        if self.flash > 0:

            img = sprites["hit"]

        else:

            if fusing:

                frames = sprites["charge"]
                index = int(self.anim_t / HONGUN_CHARGE_FRAME) % len(frames)

            else:

                frames = sprites["walk"]
                moving = self.vel.length_squared() > 1.0

                index = (
                    int(self.anim_t / HONGUN_ANIM_FRAME) % len(frames)
                    if moving else 0
                )

            img = frames[index]

            if self.hp < self.max_hp and not fusing:

                shade = int(255 * (0.55 + 0.45 * self.hp / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

            if fusing:

                blink_on = math.sin(self.anim_t * (14 + 36 * k)) > 0

                white = 255 if blink_on else int(70 * k)

                img = img.copy()
                img.fill((white, white, white, 0), special_flags=pygame.BLEND_RGB_ADD)

                grow = 1.0 + 0.30 * k

                size = (
                    max(1, int(img.get_width() * grow)),
                    max(1, int(img.get_height() * grow))
                )

                img = pygame.transform.scale(img, size)

                shake = int(math.sin(self.anim_t * 60) * 1.5 * k * camera.zoom)

        if self.spawning:

            t = 1.0 - max(0.0, self.spawn_t) / ENEMY_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, t))))

        dest = camera.apply(self.rect)

        shadow = get_shadow((int(dest.width * 1.4), int(dest.height * 0.6)), 90)

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx + shake,
                    dest.bottom + int(2 * camera.zoom)
                )
            )
        )


class DestelloArt:

    def __init__(self):

        walk = load_strip(COMBAT_DIR / "destello_anim.png")
        single = load_strip(COMBAT_DIR / "destello.png")
        run = load_strip(COMBAT_DIR / "destello_correr.png")
        alert = load_strip(COMBAT_DIR / "destello_alerta.png")
        hit = load_image(COMBAT_DIR / "destello_golpe.png")

        self.walk = walk or single or [self._placeholder(0), self._placeholder(1)]
        self.run = run or self.walk
        self.alert = alert or [self.walk[0]]

        if hit is None:

            hit = self.walk[0].copy()
            hit.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.hit = hit

        self._zoom = None
        self._scaled = None

    @staticmethod
    def _placeholder(step=0):

        surf = pygame.Surface((56, 56), pygame.SRCALPHA)

        dark = (150, 120, 40)
        mid = (240, 220, 110)
        light = (255, 250, 200)

        pygame.draw.rect(surf, mid, (14, 6, 28, 30))
        pygame.draw.rect(surf, dark, (14, 6, 28, 30), 2)

        for x, y in ((18, 10), (32, 12), (22, 28), (34, 26)):
            pygame.draw.rect(surf, light, (x, y, 6, 6))

        off = 2 if step % 2 == 0 else -2

        pygame.draw.rect(surf, dark, (14 + off, 36, 12, 14))
        pygame.draw.rect(surf, dark, (30 - off, 36, 12, 14))

        pygame.draw.rect(surf, (40, 30, 10), (19, 14, 6, 8))
        pygame.draw.rect(surf, (40, 30, 10), (31, 14, 6, 8))
        pygame.draw.rect(surf, (40, 30, 10), (24, 26, 8, 3))

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(1, int(DESTELLO_DRAW_SIZE * zoom))

            def scale(frames):
                return [pygame.transform.scale(f, (px, px)) for f in frames]

            self._scaled = {
                "walk": scale(self.walk),
                "run": scale(self.run),
                "alert": scale(self.alert),
                "hit": pygame.transform.scale(self.hit, (px, px)),
            }

            self._zoom = zoom

        return self._scaled


class Destello(Enemy):

    fixed = False
    contact_damage = False

    WANDER = "wander"
    ALERT = "alert"
    CHARGE = "charge"

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, DESTELLO_HP, DESTELLO_CHARGE_SPEED, spawn_delay)

        self.rect = pygame.Rect(0, 0, *DESTELLO_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.WANDER

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*DESTELLO_TURN_TIME)

        self.alert_t = 0.0
        self.alert_time = DESTELLO_ALERT_TIME
        self.boom = False
        self.boomed = False


    @property
    def can_explode(self):

        return (
            self.phase == self.CHARGE
            and not self.spawning
            and not self.dead
            and not self.boomed
        )

    def light(self):

        if self.spawning or self.dead:
            return None

        radius = (
            DESTELLO_LIGHT if self.phase == self.WANDER
            else DESTELLO_LIGHT_ALERT
        )

        return (self.pos.x, self.pos.y, quantize_radius(radius))


    def take_damage(self, amount):

        if self.spawning or self.dead:
            return 0

        self.hp -= amount
        self.flash = ENEMY_FLASH_TIME

        if self.phase == self.WANDER and not self.dead:

            self.phase = self.ALERT
            self.alert_t = self.alert_time

        return amount


    def _line_clear(self, a, b, collision_map):

        a = pygame.Vector2(a)
        b = pygame.Vector2(b)

        steps = max(1, int(a.distance_to(b) // 4))

        probe = pygame.Rect(0, 0, 4, 4)

        for i in range(1, steps + 1):

            p = a.lerp(b, i / steps)

            probe.center = (round(p.x), round(p.y))

            if not (self.room.contains(probe) and collision_map.can_move(probe)):
                return False

        return True

    def _walk(self, dt, direction, speed, collision_map,
              angles=(0, 45, -45, 90, -90)):

        step = speed * dt

        for angle in angles:

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center
                self.vel = d * speed

                return d

        return None

    def _run(self, dt, direction, collision_map):

        pieces = max(1, math.ceil(DESTELLO_CHARGE_SPEED * dt / 3.0))

        last = None

        for _ in range(pieces):

            d = self._walk(
                dt / pieces, direction, DESTELLO_CHARGE_SPEED, collision_map
            )

            if d is None:
                break

            last = d

        return last

    def update(self, dt, target, collision_map, others=None):

        target = pygame.Vector2(target)

        self.last_target = target.copy()
        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt

            return

        self.vel = pygame.Vector2()

        to_player = target - self.pos
        dist = to_player.length()

        if dist < 0.01:
            to_player = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            dist = 0.01

        toward = to_player / dist

        if self.phase == self.ALERT:

            self.alert_t -= dt

            if self.alert_t <= 0:
                self.phase = self.CHARGE

            return

        if self.phase == self.CHARGE:

            if dist > DESTELLO_LOSE_RADIUS:

                self.phase = self.WANDER
                self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            else:

                self._run(
                    dt, self.nav_dir(target, collision_map, dt), collision_map
                )

                self.anti_stuck(
                    dt, collision_map, target, DESTELLO_CHARGE_SPEED
                )

            return

        if (
            dist <= DESTELLO_DETECT_RADIUS
            and self._line_clear(self.pos, target, collision_map)
        ):

            self.phase = self.ALERT
            self.alert_t = self.alert_time

            return

        self.turn_t -= dt

        if self.turn_t <= 0:

            self.heading = self.heading.rotate(random.uniform(-80, 80))
            self.turn_t = random.uniform(*DESTELLO_TURN_TIME)

        d = self._walk(
            dt, self.heading, DESTELLO_WANDER_SPEED, collision_map,
            angles=(0, 40, -40, 90, -90, 140, -140, 180)
        )

        if d is not None:
            self.heading = d

        if self.anti_stuck(dt, collision_map, None, DESTELLO_WANDER_SPEED):
            self.heading = self._random_open_dir(collision_map)


    def draw(self, screen, camera, art):

        sprites = art.get(camera.zoom)

        shake = 0
        alerting = self.phase == self.ALERT
        charging = self.phase == self.CHARGE

        if self.flash > 0:

            img = sprites["hit"]

        else:

            if alerting:

                frames = sprites["alert"]
                index = int(self.anim_t / DESTELLO_ALERT_FRAME) % len(frames)

            elif charging:

                frames = sprites["run"]
                index = int(self.anim_t / DESTELLO_RUN_FRAME) % len(frames)

            else:

                frames = sprites["walk"]
                moving = self.vel.length_squared() > 1.0

                index = (
                    int(self.anim_t / DESTELLO_ANIM_FRAME) % len(frames)
                    if moving else 0
                )

            img = frames[index]

            if self.hp < self.max_hp and not alerting:

                shade = int(255 * (0.55 + 0.45 * max(0, self.hp) / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

            if alerting:

                blink_on = math.sin(self.anim_t * 40) > 0

                white = 255 if blink_on else 60

                img = img.copy()
                img.fill((white, white, white, 0), special_flags=pygame.BLEND_RGB_ADD)

                shake = int(math.sin(self.anim_t * 70) * 1.5 * camera.zoom)

        if self.spawning:

            t = 1.0 - max(0.0, self.spawn_t) / ENEMY_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, t))))

        dest = camera.apply(self.rect)

        shadow = get_shadow((int(dest.width * 1.4), int(dest.height * 0.6)), 90)

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        if charging and self.vel.length_squared() > 1.0 and not self.spawning:

            back = -self.vel.normalize()

            for i, alpha in ((2, 50), (1, 100)):

                ghost = img.copy()
                ghost.set_alpha(alpha)

                screen.blit(
                    ghost,
                    ghost.get_rect(
                        midbottom=(
                            dest.centerx + int(back.x * 3 * i * camera.zoom),
                            dest.bottom + int(2 * camera.zoom)
                            + int(back.y * 3 * i * camera.zoom)
                        )
                    )
                )

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx + shake,
                    dest.bottom + int(2 * camera.zoom)
                )
            )
        )


class GolemArt:

    FRAME = 112

    def __init__(self):

        walk = load_strip(COMBAT_DIR / "golem_anim.png")
        single = load_strip(COMBAT_DIR / "golem.png")
        chase = load_strip(COMBAT_DIR / "golem_perseguir.png")
        alert = load_strip(COMBAT_DIR / "golem_alerta.png")
        grab = load_strip(COMBAT_DIR / "golem_agarre.png")
        hit = load_image(COMBAT_DIR / "golem_golpe.png")

        self.walk = walk or single or [self._placeholder("walk", 0),
                                       self._placeholder("walk", 1)]
        self.chase = chase or self.walk
        self.alert = alert or (
            [self._placeholder("alert", 0), self._placeholder("alert", 1)]
            if not (walk or single) else [self.walk[0]]
        )
        self.grab = grab or [
            self._placeholder("grab", i) for i in range(6)
        ]

        if hit is None:

            hit = self.walk[0].copy()
            hit.fill((150, 150, 150, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.hit = hit

        self._zoom = None
        self._scaled = None

    @classmethod
    def _placeholder(cls, mode="walk", step=0):

        s = cls.FRAME
        surf = pygame.Surface((s, s), pygame.SRCALPHA)

        stone = (116, 116, 128)
        dark = (66, 66, 78)
        light = (158, 158, 170)
        eye = (255, 170, 50) if mode != "alert" else (255, 60, 40)

        bob = 2 if (step % 2 == 1 and mode == "walk") else 0

        off = 4 if step % 2 == 0 else -4

        if mode == "walk":
            pygame.draw.rect(surf, dark, (32 + off, 82, 20, 28))
            pygame.draw.rect(surf, dark, (60 - off, 82, 20, 28))
        else:
            pygame.draw.rect(surf, dark, (32, 82, 20, 28))
            pygame.draw.rect(surf, dark, (60, 82, 20, 28))

        pygame.draw.rect(surf, stone, (24, 32 - bob, 64, 54))
        pygame.draw.rect(surf, dark, (24, 32 - bob, 64, 54), 3)

        pygame.draw.line(surf, dark, (40, 44 - bob), (52, 62 - bob), 2)
        pygame.draw.line(surf, dark, (52, 62 - bob), (46, 76 - bob), 2)
        pygame.draw.rect(surf, (80, 120, 74), (66, 38 - bob, 14, 8))

        pygame.draw.rect(surf, stone, (38, 8 - bob, 36, 28))
        pygame.draw.rect(surf, dark, (38, 8 - bob, 36, 28), 3)
        pygame.draw.rect(surf, eye, (45, 18 - bob, 8, 7))
        pygame.draw.rect(surf, eye, (59, 18 - bob, 8, 7))

        if mode == "walk":

            sw = 5 if step % 2 == 0 else -5

            pygame.draw.rect(surf, stone, (6, 38 + sw, 20, 46))
            pygame.draw.rect(surf, dark, (6, 38 + sw, 20, 46), 3)
            pygame.draw.rect(surf, stone, (86, 38 - sw, 20, 46))
            pygame.draw.rect(surf, dark, (86, 38 - sw, 20, 46), 3)

        elif mode == "alert":

            up = 0 if step % 2 == 0 else 6

            pygame.draw.rect(surf, stone, (4, 6 + up, 20, 44))
            pygame.draw.rect(surf, dark, (4, 6 + up, 20, 44), 3)
            pygame.draw.rect(surf, stone, (88, 6 + up, 20, 44))
            pygame.draw.rect(surf, dark, (88, 6 + up, 20, 44), 3)

        else:

            hands = [
                (14, 70), (26, 84), (38, 90),
                (44, 86), (40, 86),
                (6, 54),
            ][min(step, 5)]

            hx, hy = hands

            for side in (-1, 1):

                shoulder = (56 + side * 34, 48)
                hand = (56 + side * (56 - hx), hy)

                pygame.draw.line(surf, dark, shoulder, hand, 18)
                pygame.draw.line(surf, stone, shoulder, hand, 12)
                pygame.draw.rect(
                    surf, light, (hand[0] - 9, hand[1] - 9, 18, 18)
                )
                pygame.draw.rect(
                    surf, dark, (hand[0] - 9, hand[1] - 9, 18, 18), 3
                )

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(1, int(GOLEM_DRAW_SIZE * zoom))

            def scale(frames):
                return [pygame.transform.scale(f, (px, px)) for f in frames]

            self._scaled = {
                "walk": scale(self.walk),
                "chase": scale(self.chase),
                "alert": scale(self.alert),
                "grab": scale(self.grab),
                "hit": pygame.transform.scale(self.hit, (px, px)),
            }

            self._zoom = zoom

        return self._scaled


class Golem(Enemy):

    fixed = False
    contact_damage = False

    WANDER = "wander"
    ALERT = "alert"
    CHASE = "chase"
    GRAB = "grab"
    REST = "rest"

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, GOLEM_HP, GOLEM_CHASE_SPEED, spawn_delay)

        self.spawn_t = GOLEM_SPAWN_TIME + spawn_delay

        self.rect = pygame.Rect(0, 0, *GOLEM_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.WANDER

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*GOLEM_TURN_TIME)

        self.phase_t = 0.0
        self.moving = False

        self.grab_dir = pygame.Vector2(0, 1)
        self._squeeze_pending = False
        self._release_pending = False
        self._squeezed = False


    @property
    def holding(self):

        return self.phase == self.GRAB

    @property
    def lift(self):

        if self.phase != self.GRAB:
            return 0.0

        up = min(1.0, self.phase_t / 0.35)
        down = min(1.0, max(0.0, (GOLEM_GRAB_TIME - self.phase_t) / 0.25))

        return GOLEM_GRAB_LIFT * ease_out(min(up, down))

    def can_grab(self, body):

        if self.phase != self.CHASE or self.spawning or self.dead:
            return False

        reach = self.rect.inflate(GOLEM_GRAB_REACH * 2, GOLEM_GRAB_REACH * 2)

        return reach.colliderect(body)

    def start_grab(self, direction=None):

        if direction is not None and pygame.Vector2(direction).length_squared() > 0.01:
            self.grab_dir = pygame.Vector2(direction).normalize()
        else:
            self.grab_dir = pygame.Vector2(0, 1)

        self.phase = self.GRAB
        self.phase_t = 0.0
        self.vel = pygame.Vector2()
        self._squeeze_pending = False
        self._release_pending = False
        self._squeezed = False

    def take_squeeze(self):

        if self._squeeze_pending:

            self._squeeze_pending = False

            return True

        return False

    def take_release(self):

        if self._release_pending:

            self._release_pending = False

            return True

        return False


    def take_damage(self, amount):

        if self.spawning or self.dead or self.phase == self.GRAB:
            return 0

        self.hp -= amount
        self.flash = GOLEM_FLASH_TIME

        away = self.pos - self.last_target

        if away.length_squared() > 0.01 and self.phase != self.ALERT:
            self.pos += away.normalize() * GOLEM_HIT_PUSH * 0.05
            self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.phase == self.WANDER:

            self.phase = self.ALERT
            self.phase_t = 0.0

        return amount


    def _line_clear(self, a, b, collision_map):

        a = pygame.Vector2(a)
        b = pygame.Vector2(b)

        steps = max(1, int(a.distance_to(b) // 4))

        probe = pygame.Rect(0, 0, 4, 4)

        for i in range(1, steps + 1):

            p = a.lerp(b, i / steps)

            probe.center = (round(p.x), round(p.y))

            if not (self.room.contains(probe) and collision_map.can_move(probe)):
                return False

        return True

    def _walk(self, dt, direction, speed, collision_map,
              angles=(0, 45, -45, 90, -90)):

        step = speed * dt

        for angle in angles:

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center
                self.vel = d * speed

                return d

        return None

    def update(self, dt, target, collision_map, others=None):

        target = pygame.Vector2(target)

        self.last_target = target.copy()
        self.anim_t += dt
        self.moving = False

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt

            return

        self.vel = pygame.Vector2()

        to_player = target - self.pos
        dist = to_player.length()

        if self.phase == self.GRAB:

            self.phase_t += dt

            if not self._squeezed and self.phase_t >= GOLEM_SQUEEZE_AT:

                self._squeezed = True
                self._squeeze_pending = True

            if self.phase_t >= GOLEM_GRAB_TIME:

                self.phase = self.REST
                self.phase_t = 0.0
                self._release_pending = True

            return

        if self.phase == self.REST:

            self.phase_t += dt

            if self.phase_t >= GOLEM_REST_TIME:

                self.phase = (
                    self.CHASE
                    if GOLEM_CHASE_FOREVER or dist <= GOLEM_LOSE_RADIUS
                    else self.WANDER
                )
                self.phase_t = 0.0

            return

        if self.phase == self.ALERT:

            self.phase_t += dt

            if self.phase_t >= GOLEM_ALERT_TIME:

                self.phase = self.CHASE
                self.phase_t = 0.0

            return

        if self.phase == self.CHASE:

            if not GOLEM_CHASE_FOREVER and dist > GOLEM_LOSE_RADIUS:

                self.phase = self.WANDER
                self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

                return

            d = self._walk(
                dt,
                self.nav_dir(target, collision_map, dt),
                GOLEM_CHASE_SPEED,
                collision_map,
            )

            self.anti_stuck(dt, collision_map, target, GOLEM_CHASE_SPEED)

            if d is not None:
                self.moving = True

            return

        if (
            dist <= GOLEM_DETECT_RADIUS
            and self._line_clear(self.pos, target, collision_map)
        ):

            self.phase = self.ALERT
            self.phase_t = 0.0

            return

        self.turn_t -= dt

        if self.turn_t <= 0:

            self.heading = self.heading.rotate(random.uniform(-80, 80))
            self.turn_t = random.uniform(*GOLEM_TURN_TIME)

        d = self._walk(
            dt, self.heading, GOLEM_WANDER_SPEED, collision_map,
            angles=(0, 40, -40, 90, -90, 140, -140, 180)
        )

        if d is not None:
            self.heading = d
            self.moving = True

        if self.anti_stuck(dt, collision_map, None, GOLEM_WANDER_SPEED):
            self.heading = self._random_open_dir(collision_map)


    def draw(self, screen, camera, art):

        sprites = art.get(camera.zoom)

        shake = 0
        alerting = self.phase == self.ALERT

        if self.flash > 0:

            img = sprites["hit"]

        else:

            if self.phase == self.GRAB:

                frames = sprites["grab"]
                index = min(
                    len(frames) - 1,
                    int(self.phase_t / GOLEM_GRAB_TIME * len(frames))
                )

            elif alerting:

                frames = sprites["alert"]
                index = int(self.anim_t / GOLEM_ALERT_FRAME) % len(frames)

            elif self.phase == self.CHASE:

                frames = sprites["chase"]
                index = (
                    int(self.anim_t / GOLEM_CHASE_FRAME) % len(frames)
                    if self.moving else 0
                )

            else:

                frames = sprites["walk"]
                index = (
                    int(self.anim_t / GOLEM_ANIM_FRAME) % len(frames)
                    if self.moving else 0
                )

            img = frames[index]

            if self.hp < self.max_hp:

                shade = int(255 * (0.55 + 0.45 * max(0, self.hp) / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

            if alerting:

                blink_on = math.sin(self.anim_t * 30) > 0

                img = img.copy()
                img.fill(
                    (90 if blink_on else 30, 0, 0, 0),
                    special_flags=pygame.BLEND_RGB_ADD
                )

                shake = int(math.sin(self.anim_t * 60) * 1.5 * camera.zoom)

            elif self.phase == self.GRAB:

                if abs(self.phase_t - GOLEM_SQUEEZE_AT) < 0.3:
                    shake = int(math.sin(self.anim_t * 80) * 1.2 * camera.zoom)

            elif self.phase == self.REST:

                img = img.copy()
                img.fill(
                    (200, 200, 215, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

        if self.spawning:

            t = 1.0 - max(0.0, self.spawn_t) / GOLEM_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, t))))

        dest = camera.apply(self.rect)

        shadow = get_shadow((int(img.get_width() * 0.7), int(img.get_height() * 0.22)), 100)

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx + shake,
                    dest.bottom + int(2 * camera.zoom)
                )
            )
        )


GUARDIAN_HP = 30
GUARDIAN_HITBOX = (10, 16)
GUARDIAN_DRAW_SIZE = (14.5, 18.5)

GUARDIAN_WANDER_SPEED = 35.0
GUARDIAN_CHASE_SPEED = 70.0
GUARDIAN_TURN_TIME = (1.2, 3.0)

GUARDIAN_INNER = INNER_RADIUS
GUARDIAN_OUTER = OUTER_RADIUS
GUARDIAN_ARC = ARC_DEGREES
GUARDIAN_SWING_TIME = SWING_TIME

GUARDIAN_ATTACK_DIST = 22.0
GUARDIAN_WINDUP = 0.15
GUARDIAN_COOLDOWN = COOLDOWN
GUARDIAN_DAMAGE = 0.45
GUARDIAN_KNOCKBACK = 150.0
GUARDIAN_HIT_PUSH = 28.0
GUARDIAN_WEAPON_LENGTH = 21.0

GUARDIAN_ANIM_FRAME = 0.14
GUARDIAN_FLASH_TIME = 0.10
GUARDIAN_SPAWN_TIME = 1.0


class GuardianArt:

    DIRS = ("up", "down", "left", "right")
    CELL = (64, 80)

    WALK_FILE = "guardian.png"
    ATTACK_FILE = "guardian_ataque.png"
    WEAPON_FILE = "guardian_arma.png"
    CLOTH = (88, 58, 120)
    DARK = (46, 30, 68)

    def __init__(self):

        walk = load_image(COMBAT_DIR / self.WALK_FILE)
        attack = load_image(COMBAT_DIR / self.ATTACK_FILE)

        self.walk = self._cut(walk, 4) or self._placeholder_walk()
        self.attack = self._cut(attack, 2) or self._placeholder_attack()
        self.weapon = (
            load_image(COMBAT_DIR / self.WEAPON_FILE)
            if self.WEAPON_FILE else None
        )

        self._zoom = None
        self._scaled = None
        self._weapon_zoom = None
        self._weapon_scaled = None


    @classmethod
    def _cut(cls, sheet, cols):

        if sheet is None:
            return None

        cw = sheet.get_width() // cols
        ch = sheet.get_height() // 4

        if cw <= 0 or ch <= 0:
            return None

        return {
            d: [
                sheet.subsurface((c * cw, r * ch, cw, ch)).copy()
                for c in range(cols)
            ]
            for r, d in enumerate(cls.DIRS)
        }


    @classmethod
    def _body(cls, direction, step, raised):

        w, h = cls.CELL
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        cloth = cls.CLOTH
        dark = cls.DARK
        skin = (200, 175, 150)
        eye = (255, 215, 90)

        off = (0, 3, 0, -3)[step % 4]

        pygame.draw.rect(surf, dark, (w // 2 - 12, 52 + off, 10, 22))
        pygame.draw.rect(surf, dark, (w // 2 + 2, 52 - off, 10, 22))

        pygame.draw.rect(surf, cloth, (w // 2 - 15, 24, 30, 32), border_radius=4)
        pygame.draw.rect(surf, dark, (w // 2 - 15, 24, 30, 32), 2, border_radius=4)

        arm_y = 14 if raised else 28
        if direction in ("down", "up"):
            pygame.draw.rect(surf, cloth, (w // 2 - 22, arm_y, 8, 22))
            pygame.draw.rect(surf, cloth, (w // 2 + 14, arm_y, 8, 22))
        elif direction == "left":
            pygame.draw.rect(surf, cloth, (w // 2 - 20, arm_y, 8, 22))
        else:
            pygame.draw.rect(surf, cloth, (w // 2 + 12, arm_y, 8, 22))

        pygame.draw.circle(surf, skin, (w // 2, 14), 12)
        pygame.draw.circle(surf, dark, (w // 2, 14), 12, 2)

        if direction == "down":
            pygame.draw.rect(surf, eye, (w // 2 - 7, 11, 4, 4))
            pygame.draw.rect(surf, eye, (w // 2 + 3, 11, 4, 4))
        elif direction == "left":
            pygame.draw.rect(surf, eye, (w // 2 - 9, 11, 4, 4))
        elif direction == "right":
            pygame.draw.rect(surf, eye, (w // 2 + 5, 11, 4, 4))
        else:
            pygame.draw.rect(surf, dark, (w // 2 - 8, 4, 16, 6))

        return surf

    @classmethod
    def _placeholder_walk(cls):

        return {
            d: [cls._body(d, i, False) for i in range(4)]
            for d in cls.DIRS
        }

    @classmethod
    def _placeholder_attack(cls):

        return {
            d: [cls._body(d, 0, True), cls._body(d, 2, False)]
            for d in cls.DIRS
        }


    def get(self, zoom):

        if self._zoom != zoom:

            size = (
                max(1, int(GUARDIAN_DRAW_SIZE[0] * zoom)),
                max(1, int(GUARDIAN_DRAW_SIZE[1] * zoom)),
            )

            def scale(table):
                return {
                    d: [pygame.transform.smoothscale(f, size) for f in frames]
                    for d, frames in table.items()
                }

            self._scaled = (scale(self.walk), scale(self.attack))
            self._zoom = zoom

        return self._scaled

    def get_weapon(self, zoom):

        if self.weapon is None:
            return None

        if self._weapon_zoom != zoom:

            h = max(1, int(GUARDIAN_WEAPON_LENGTH * zoom))
            w = max(1, int(self.weapon.get_width() * h / self.weapon.get_height()))

            self._weapon_scaled = pygame.transform.smoothscale(self.weapon, (w, h))
            self._weapon_zoom = zoom

        return self._weapon_scaled


class Guardian(Enemy):

    fixed = False
    contact_damage = False

    WANDER = "wander"
    CHASE = "chase"
    WINDUP = "windup"
    SWING = "swing"

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, GUARDIAN_HP, GUARDIAN_CHASE_SPEED, spawn_delay)

        self.spawn_t = GUARDIAN_SPAWN_TIME + spawn_delay

        self.rect = pygame.Rect(0, 0, *GUARDIAN_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.WANDER

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*GUARDIAN_TURN_TIME)

        self.facing = "down"
        self.moving = False

        self.phase_t = 0.0
        self.cooldown = 0.0
        self.aim = 0.0
        self.hit_done = False


    @property
    def awake(self):

        return self.phase != self.WANDER

    @property
    def attacking(self):

        return self.phase in (self.WINDUP, self.SWING)

    @property
    def swing_k(self):

        return max(0.0, min(1.0, self.phase_t / GUARDIAN_SWING_TIME))

    def weapon_angle(self):

        half = math.radians(GUARDIAN_ARC) / 2

        if self.phase == self.WINDUP:
            return self.aim - half

        if self.phase == self.SWING:
            return self.aim - half + 2 * half * ease_out(self.swing_k)

        return self.aim


    def take_damage(self, amount):

        if self.spawning or self.dead:
            return 0

        self.hp -= amount
        self.flash = GUARDIAN_FLASH_TIME

        away = self.pos - self.last_target

        if away.length_squared() > 0.01 and not self.attacking:
            self.pos += away.normalize() * GUARDIAN_HIT_PUSH * 0.05
            self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.phase == self.WANDER:
            self.phase = self.CHASE

        return amount


    def _walk(self, dt, direction, speed, collision_map,
              angles=(0, 45, -45, 90, -90)):

        step = speed * dt

        for angle in angles:

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center
                self.vel = d * speed

                return d

        return None

    def _face(self, direction):

        if abs(direction.x) > abs(direction.y):
            self.facing = "right" if direction.x > 0 else "left"
        elif abs(direction.y) > 0.001:
            self.facing = "down" if direction.y > 0 else "up"

    def swing_hits(self, point):

        if self.phase != self.SWING or self.hit_done:
            return False

        offset = pygame.Vector2(point) - self.pos
        dist = offset.length()

        if dist < GUARDIAN_INNER - 8 or dist > GUARDIAN_OUTER + 5:
            return False

        half = math.radians(GUARDIAN_ARC) / 2
        angle = math.atan2(offset.y, offset.x)

        start = self.aim - half
        now = self.weapon_angle()

        delta = (angle - start + math.pi) % math.tau - math.pi
        reach = now - start

        if -0.15 <= delta <= reach + 0.15:

            self.hit_done = True

            return True

        return False

    def update(self, dt, target, collision_map, light_on, light_radius):

        target = pygame.Vector2(target)
        self.last_target = target.copy()

        self.anim_t += dt
        self.moving = False

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.spawning:
            self.spawn_t -= dt
            return

        if self.cooldown > 0:
            self.cooldown = max(0.0, self.cooldown - dt)

        to_player = target - self.pos
        dist = to_player.length()
        toward = to_player / dist if dist > 0.01 else pygame.Vector2(1, 0)

        if self.phase == self.WANDER:

            if light_on and dist <= light_radius:

                self.phase = self.CHASE

            else:

                self.turn_t -= dt

                if self.turn_t <= 0:

                    self.heading = self.heading.rotate(random.uniform(-80, 80))
                    self.turn_t = random.uniform(*GUARDIAN_TURN_TIME)

                d = self._walk(
                    dt, self.heading, GUARDIAN_WANDER_SPEED, collision_map,
                    angles=(0, 40, -40, 90, -90, 140, -140, 180)
                )

                if d is not None:
                    self.heading = d
                    self.moving = True
                    self._face(d)

                return

        if self.phase == self.WINDUP:

            self.phase_t += dt

            want = math.atan2(toward.y, toward.x)
            diff = (want - self.aim + math.pi) % math.tau - math.pi
            self.aim += diff * min(1.0, 6.0 * dt)

            self._face(pygame.Vector2(math.cos(self.aim), math.sin(self.aim)))

            if self.phase_t >= GUARDIAN_WINDUP:

                self.phase = self.SWING
                self.phase_t = 0.0
                self.hit_done = False

            return

        if self.phase == self.SWING:

            self.phase_t += dt

            if self.phase_t >= GUARDIAN_SWING_TIME:

                self.phase = self.CHASE
                self.cooldown = GUARDIAN_COOLDOWN

            return

        if dist <= GUARDIAN_ATTACK_DIST and self.cooldown <= 0:

            self.phase = self.WINDUP
            self.phase_t = 0.0
            self.aim = math.atan2(toward.y, toward.x)

            return

        if dist > GUARDIAN_ATTACK_DIST * 0.7:

            d = self._walk(
                dt,
                self.nav_dir(target, collision_map, dt),
                GUARDIAN_CHASE_SPEED,
                collision_map,
            )

            self.anti_stuck(dt, collision_map, target, GUARDIAN_CHASE_SPEED)

            if d is not None:
                self.moving = True
                self._face(d)

        else:

            self._face(toward)


    def draw(self, screen, camera, art):

        walk, attack = art.get(camera.zoom)

        if self.attacking:

            frames = attack[self.facing]
            img = frames[0] if self.phase == self.WINDUP else frames[min(1, len(frames) - 1)]

        else:

            frames = walk[self.facing]

            index = (
                int(self.anim_t / GUARDIAN_ANIM_FRAME) % len(frames)
                if self.moving else 0
            )

            img = frames[index]

        if self.flash > 0:

            img = img.copy()
            img.fill((200, 200, 200, 0), special_flags=pygame.BLEND_RGB_ADD)

        if self.spawning:

            k = 1.0 - max(0.0, self.spawn_t) / GUARDIAN_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(40 + 160 * max(0.0, min(1.0, k))))

        dest = camera.apply(self.rect)

        shadow = get_shadow((int(dest.width * 1.5), int(dest.height * 0.35)), 90)

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        sprite_rect = img.get_rect(
            midbottom=(dest.centerx, dest.bottom + int(2 * camera.zoom))
        )

        screen.blit(img, sprite_rect)

        if self.spawning or self.dead:
            return

        if self.attacking:
            self._draw_attack(screen, camera, dest, art)

    def _draw_attack(self, screen, camera, dest, art):

        zoom = camera.zoom
        cx, cy = dest.center

        r_in = GUARDIAN_INNER * zoom

        angle = self.weapon_angle()
        direction = pygame.Vector2(math.cos(angle), math.sin(angle))
        length = GUARDIAN_WEAPON_LENGTH * zoom

        weapon = art.get_weapon(zoom)

        start = pygame.Vector2(cx, cy) + direction * r_in * 0.6

        if weapon is not None:

            img = pygame.transform.rotate(weapon, -(math.degrees(angle) + 90))
            center = start + direction * (weapon.get_height() / 2)

            screen.blit(img, img.get_rect(center=(round(center.x), round(center.y))))

            return

        end = start + direction * length

        pygame.draw.line(screen, (60, 40, 25), start, end, max(3, int(zoom * 1.1)))
        pygame.draw.line(screen, (150, 105, 60), start, end, max(2, int(zoom * 0.6)))
        pygame.draw.circle(screen, (255, 160, 60), (int(end.x), int(end.y)), max(2, int(zoom * 0.9)))


GSHOOT_HP = 28

GSHOOT_WANDER_SPEED = GUARDIAN_WANDER_SPEED
GSHOOT_MOVE_SPEED = 70.0
GSHOOT_RETREAT_SPEED = 80.0
GSHOOT_STRAFE_TIME = (1.0, 2.2)

GSHOOT_MIN_DIST = 70.0
GSHOOT_MAX_DIST = 120.0

GSHOOT_BOLT_SPEED = FIRE_SPEED
GSHOOT_BOLT_RANGE = 190.0
GSHOOT_BOLT_HITBOX = 5
GSHOOT_BOLT_DRAW_SIZE = 7.0
GSHOOT_MUZZLE = 8.0

GSHOOT_AIM_TIME = 0.35
GSHOOT_RECOVER = 0.18
GSHOOT_COOLDOWN = 1.2
GSHOOT_AIM_TURN = 14.0
GSHOOT_LEAD_MAX = 0.8
GSHOOT_DAMAGE = 0.15
GSHOOT_KNOCKBACK = 90.0


_gshoot_bolt_cache = {}


def _gshoot_bolt_base():

    img = load_image(COMBAT_DIR / "bola_guardian.png")

    if img is None:

        img = pygame.Surface((32, 32), pygame.SRCALPHA)

        pygame.draw.circle(img, (120, 50, 200), (22, 16), 9)
        pygame.draw.circle(img, (190, 130, 255), (22, 16), 6)
        pygame.draw.circle(img, (245, 230, 255), (22, 16), 3)

    return img


def _gshoot_bolt_sprite(zoom, angle_deg):

    deg = round(-angle_deg / 10) * 10

    key = (zoom, deg)

    if key not in _gshoot_bolt_cache:

        size = max(4, int(GSHOOT_BOLT_DRAW_SIZE * zoom))

        sprite = pygame.transform.smoothscale(_gshoot_bolt_base(), (size, size))

        _gshoot_bolt_cache[key] = pygame.transform.rotate(sprite, deg)

    return _gshoot_bolt_cache[key]


class GuardianShooterArt(GuardianArt):

    WALK_FILE = "guardian_tirador.png"
    ATTACK_FILE = "guardian_tirador_disparo.png"
    WEAPON_FILE = None

    CLOTH = (40, 96, 112)
    DARK = (20, 52, 66)


class GuardianBolt(Shot):

    damage = GSHOOT_DAMAGE
    knockback = GSHOOT_KNOCKBACK

    def __init__(self, pos, angle_deg):

        super().__init__(pos, angle_deg)

        self.angle = angle_deg
        self.vel = pygame.Vector2(GSHOOT_BOLT_SPEED, 0).rotate(angle_deg)

        self.rect = pygame.Rect(0, 0, GSHOOT_BOLT_HITBOX, GSHOOT_BOLT_HITBOX)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.range_left = GSHOOT_BOLT_RANGE

    def update(self, dt, collision_map):

        self.t += dt

        if self.dead:
            return

        dist = self.vel.length() * dt

        steps = max(1, math.ceil(dist / 3.0))
        step = dist / steps

        move = self.vel.normalize() * step if self.vel.length_squared() > 0 else None

        if move is None:
            self.dead = True
            return

        for _ in range(steps):

            self.pos += move
            self.range_left -= step

            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.range_left <= 0 or not self._free(self.rect, collision_map):

                self.dead = True

                return

    def draw(self, screen, camera, art=None):

        img = _gshoot_bolt_sprite(camera.zoom, self.angle)

        center = camera.apply(self.rect).center

        screen.blit(img, img.get_rect(center=center))


class GuardianShooter(Guardian):

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, spawn_delay)

        self.hp = GSHOOT_HP
        self.max_hp = GSHOOT_HP
        self.max_speed = GSHOOT_MOVE_SPEED

        self.target_vel = pygame.Vector2()
        self._prev_target = None

        self.strafe_dir = random.choice((-1, 1))
        self.strafe_t = random.uniform(*GSHOOT_STRAFE_TIME)

        self.cooldown = random.uniform(0.3, 0.9)

        self._shots = []


    def take_shots(self):

        shots, self._shots = self._shots, []

        return shots

    def _line_clear(self, a, b, collision_map):

        a = pygame.Vector2(a)
        b = pygame.Vector2(b)

        steps = max(1, int(a.distance_to(b) // 4))

        probe = pygame.Rect(0, 0, 4, 4)

        for i in range(1, steps + 1):

            p = a.lerp(b, i / steps)

            probe.center = (round(p.x), round(p.y))

            if not (self.room.contains(probe) and collision_map.can_move(probe)):
                return False

        return True

    def _lead_point(self, target):

        origin = self.pos
        d = target - origin
        v = self.target_vel
        speed = GSHOOT_BOLT_SPEED

        a = v.dot(v) - speed * speed
        b = 2.0 * d.dot(v)
        c = d.dot(d)

        t = None

        if abs(a) < 1e-6:

            if abs(b) > 1e-6:
                t = -c / b

        else:

            disc = b * b - 4.0 * a * c

            if disc >= 0:

                root = math.sqrt(disc)

                times = [
                    x for x in ((-b - root) / (2.0 * a), (-b + root) / (2.0 * a))
                    if x > 0
                ]

                if times:
                    t = min(times)

        if t is None or t <= 0:
            t = d.length() / speed

        t = min(t, GSHOOT_LEAD_MAX)

        point = pygame.Vector2(target) + v * t

        point.x = max(self.room.left + 4, min(self.room.right - 4, point.x))
        point.y = max(self.room.top + 4, min(self.room.bottom - 4, point.y))

        return point

    def _aim_angle(self, target):

        point = self._lead_point(target)

        direction = point - self.pos

        if direction.length_squared() < 0.01:
            direction = pygame.Vector2(target) - self.pos

        if direction.length_squared() < 0.01:
            return self.aim

        return math.atan2(direction.y, direction.x)

    def _fire(self):

        direction = pygame.Vector2(math.cos(self.aim), math.sin(self.aim))

        start = self.pos + direction * GSHOOT_MUZZLE

        shot = GuardianBolt(start, math.degrees(self.aim))
        shot.room = self.room

        self._shots.append(shot)


    def _keep_distance(self, dt, toward, dist, can_see, collision_map):

        side = self.strafe_dir

        self.strafe_t -= dt

        if self.strafe_t <= 0:

            self.strafe_dir = side = -side
            self.strafe_t = random.uniform(*GSHOOT_STRAFE_TIME)

        perp = pygame.Vector2(-toward.y, toward.x) * side

        if dist < GSHOOT_MIN_DIST:

            d = self._walk(
                dt, -toward, GSHOOT_RETREAT_SPEED, collision_map,
                angles=(0, 40 * side, -40 * side, 80 * side, -80 * side)
            )

            if d is None:
                d = self._walk(
                    dt, perp, GSHOOT_MOVE_SPEED, collision_map,
                    angles=(0, 30, -30)
                )

        elif dist > GSHOOT_MAX_DIST:

            d = self._walk(
                dt,
                self.nav_dir(self.last_target, collision_map, dt),
                GSHOOT_MOVE_SPEED,
                collision_map,
            )

            self.anti_stuck(
                dt, collision_map, self.last_target, GSHOOT_MOVE_SPEED
            )

        else:

            d = self._walk(
                dt, perp, GSHOOT_MOVE_SPEED, collision_map,
                angles=(0, 25, -25)
            )

            if d is None:
                self.strafe_dir = -side

        if d is not None:
            self.moving = True

        self._face(toward)


    def update(self, dt, target, collision_map, light_on, light_radius):

        target = pygame.Vector2(target)
        self.last_target = target.copy()

        self.anim_t += dt
        self.moving = False

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.spawning:

            self.spawn_t -= dt
            self._prev_target = target.copy()

            return

        if self._prev_target is not None and dt > 0:

            raw = (target - self._prev_target) / dt

            if raw.length() > 140.0:
                raw.scale_to_length(140.0)

            self.target_vel += (raw - self.target_vel) * min(1.0, dt * 10.0)

        self._prev_target = target.copy()

        if self.cooldown > 0:
            self.cooldown = max(0.0, self.cooldown - dt)

        to_player = target - self.pos
        dist = to_player.length()
        toward = to_player / dist if dist > 0.01 else pygame.Vector2(1, 0)

        if self.phase == self.WANDER:

            if light_on and dist <= light_radius:

                self.phase = self.CHASE

            else:

                self.turn_t -= dt

                if self.turn_t <= 0:

                    self.heading = self.heading.rotate(random.uniform(-80, 80))
                    self.turn_t = random.uniform(*GUARDIAN_TURN_TIME)

                d = self._walk(
                    dt, self.heading, GSHOOT_WANDER_SPEED, collision_map,
                    angles=(0, 40, -40, 90, -90, 140, -140, 180)
                )

                if d is not None:
                    self.heading = d
                    self.moving = True
                    self._face(d)

                return

        if self.phase == self.WINDUP:

            self.phase_t += dt

            want = self._aim_angle(target)
            diff = (want - self.aim + math.pi) % math.tau - math.pi
            self.aim += diff * min(1.0, GSHOOT_AIM_TURN * dt)

            self._face(pygame.Vector2(math.cos(self.aim), math.sin(self.aim)))

            if self.phase_t >= GSHOOT_AIM_TIME:

                if not self._line_clear(self.pos, target, collision_map):

                    self.phase = self.CHASE
                    self.cooldown = 0.3

                    return

                self.aim = self._aim_angle(target)

                self._fire()

                self.phase = self.SWING
                self.phase_t = 0.0
                self.cooldown = GSHOOT_COOLDOWN

            return

        if self.phase == self.SWING:

            self.phase_t += dt

            if self.phase_t >= GSHOOT_RECOVER:
                self.phase = self.CHASE

            return

        can_see = False

        if self.cooldown <= 0 or dist <= GSHOOT_MAX_DIST:

            can_see = self._line_clear(self.pos, target, collision_map)

        if (
            can_see
            and self.cooldown <= 0
            and dist <= GSHOOT_MAX_DIST + 25.0
        ):

            self.phase = self.WINDUP
            self.phase_t = 0.0
            self.aim = self._aim_angle(target)

            return

        self._keep_distance(dt, toward, dist, can_see, collision_map)


    def _draw_attack(self, screen, camera, dest, art):

        if self.phase != self.WINDUP:
            return

        zoom = camera.zoom

        direction = pygame.Vector2(math.cos(self.aim), math.sin(self.aim))

        pos = pygame.Vector2(dest.center) + direction * GSHOOT_MUZZLE * zoom

        k = min(1.0, self.phase_t / GSHOOT_AIM_TIME)

        radius = max(2, int((1.0 + 2.5 * k) * zoom))

        center = (round(pos.x), round(pos.y))

        pygame.draw.circle(screen, (120, 50, 200), center, radius)
        pygame.draw.circle(screen, (190, 130, 255), center, max(1, int(radius * 0.65)))
        pygame.draw.circle(screen, (245, 230, 255), center, max(1, int(radius * 0.3)))


class RewardChest:

    APPEAR_TIME = 0.6
    GLOW_TIME = 2.4
    OPEN_TIME = 0.5
    SIZE = 20

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.t = 0.0
        self.phase = "appear"
        self.done = False

        self._glow_cache = {}


    def update(self, dt):

        self.t += dt

        if self.phase == "appear" and self.t >= self.APPEAR_TIME:
            self.phase = "glow"

        if self.phase == "glow" and self.t >= (
            self.APPEAR_TIME + self.GLOW_TIME
        ):

            self.phase = "open"
            self.t = 0.0

            return True

        if self.phase == "open" and self.t >= self.OPEN_TIME:
            self.done = True

        return False

    @property
    def glow_k(self):

        if self.phase == "appear":
            return 0.0

        if self.phase == "open":
            return 1.0

        return min(1.0, (self.t - self.APPEAR_TIME) / self.GLOW_TIME)

    def light(self):

        if self.phase == "appear":

            return (
                self.x, self.y,
                quantize_radius(60 * (self.t / self.APPEAR_TIME))
            )

        k = self.glow_k

        pulse = math.sin(self.t * (6 + 14 * k))

        return (
            self.x, self.y, quantize_radius(95 + 55 * k + 18 * pulse)
        )


    def _sprite(self, name, zoom):

        px = int(self.SIZE * zoom)

        return load_image(CHEST_DIR / name, (px, px))

    def _glow_surface(self, radius):

        radius = max(4, int(radius))

        if radius not in self._glow_cache:

            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            for r in range(radius, 0, -3):

                a = int(150 * (1 - r / radius) ** 1.6)

                pygame.draw.circle(
                    surf, (255, 210, 90, a), (radius, radius), r
                )

            self._glow_cache[radius] = surf

        return self._glow_cache[radius]

    def _center_px(self, camera):

        return (
            int(self.x * camera.zoom - camera.x),
            int(self.y * camera.zoom - camera.y)
        )

    def draw(self, screen, camera):

        if self.phase == "open" and self.t > 0.15:
            sprite = self._sprite("cofre_abierto.png", camera.zoom)
        else:
            sprite = self._sprite("cofre_cerrado.png", camera.zoom)

        if sprite is None:
            return

        cx, cy = self._center_px(camera)

        dx = 0
        dy = 0

        if self.phase == "appear":

            k = min(1.0, self.t / self.APPEAR_TIME)
            fall = (1 - k) ** 2

            dy = -int(fall * 26 * camera.zoom)

        elif self.phase == "glow":

            k = self.glow_k

            dx = int(math.sin(self.t * 70) * (1 + 4 * k))

        if self.phase == "glow" and self.glow_k > 0.5:

            sprite = sprite.copy()

            add = int(140 * (self.glow_k - 0.5) * 2)

            sprite.fill(
                (add, add, add // 2, 0),
                special_flags=pygame.BLEND_RGB_ADD
            )

        screen.blit(sprite, sprite.get_rect(center=(cx + dx, cy + dy)))

    def draw_glow(self, screen, camera):

        if self.phase == "appear":
            return

        k = self.glow_k

        radius = (20 + 30 * k + 4 * math.sin(self.t * 10)) * camera.zoom

        radius = max(16, int(round(radius / 16.0)) * 16)

        glow = self._glow_surface(radius)

        cx, cy = self._center_px(camera)

        screen.blit(glow, glow.get_rect(center=(cx, cy)))


class ArenaConfig:

    def __init__(self, key, title, room, trigger, exit_pos, gate,
                 table, rewards, last_wave, save_wave, save_done,
                 show_total=False,
                 sealed_text="Mapa completado: la sala esta cerrada",
                 done_text="Mapa completado! La sala se cerro para siempre",
                 gem_id="gema", gem_name="gema",
                 zone_name="", zone_tag="", hard=False, boss=False):

        self.key = key
        self.zone_name = zone_name
        self.zone_tag = zone_tag
        self.hard = hard
        self.boss = boss
        self.title = title
        self.room = room
        self.trigger = trigger
        self.exit_pos = exit_pos
        self.gate = gate
        self.table = table
        self.rewards = rewards
        self.last_wave = last_wave
        self.save_wave = save_wave
        self.save_done = save_done
        self.show_total = show_total
        self.sealed_text = sealed_text
        self.done_text = done_text
        self.gem_id = gem_id
        self.gem_name = gem_name


RIGHT_ARENA = ArenaConfig(
    "right", "Orkun - Zona 1",
    ROOM, TRIGGER, EXIT_POS, GATE,
    WAVE_COMPOSITION, WAVE_REWARDS, LAST_WAVE,
    "arena_wave", "arena_completed",
    zone_name="ORKUN", zone_tag="ZONA 1", boss=True,
)


LEFT_WAVE_REWARDS = {
    1: 1500, 2: 1700, 3: 1900, 4: 2100, 5: 2300,
    6: 2500, 7: 2700, 8: 2900, 9: 3100, 10: 3300,
}

LEFT_LAST_WAVE = 10

LEFT_ARENA = ArenaConfig(
    "left", "Stonun - Zona 2",
    ROOM_LEFT, TRIGGER_LEFT, EXIT_POS_LEFT, GATE_LEFT,
    LEFT_WAVE_COMPOSITION, LEFT_WAVE_REWARDS, LEFT_LAST_WAVE,
    "arena_left_wave", "arena_left_completed",
    show_total=True,
    sealed_text="Sala completada: esta cerrada",
    done_text="Sala completada! Se cerro para siempre",
    gem_id="gema_verde",
    gem_name="gema verde oscuro",
    zone_name="STONUN", zone_tag="ZONA 2", hard=True,
)


class Arena:

    IDLE = "idle"
    MENU = "menu"
    WAVE = "wave"
    CLEAR = "clear"
    COLLECT = "collect"

    PANEL_SIZE = (420, 300)
    BUTTON_SIZE = (260, 56)

    BUTTONS = ["exit", "escape", "noescape"]

    BUTTON_FILES = {
        "exit": "btn_salir",
        "escape": "btn_jugar_escape",
        "noescape": "btn_jugar_sin_escape",
    }

    BUTTON_LABELS = {
        "exit": "Salir",
        "escape": "Jugar con escape",
        "noescape": "Jugar sin escape  X2 premio",
    }

    def __init__(self, screen_size, cfg=None):

        self.cfg = cfg or RIGHT_ARENA

        self.size = screen_size

        self.state = self.IDLE

        self.armed = True

        self.wave = 1
        self.mode = None

        self.enemies = []
        self.shots = []
        self.art = EnemyArt()
        self.tronco_art = TroncoArt()
        self.mosquito_art = MosquitoArt()
        self.hongun_art = HongunArt()
        self.destello_art = DestelloArt()
        self.golem_art = GolemArt()
        self.guardian_art = GuardianArt()
        self.shooter_art = GuardianShooterArt()
        self.boss_art = (
            BossArt(COMBAT_DIR, load_image, load_strip)
            if self.cfg.boss else None
        )

        # entrada y derrota "epicas" del jefe (barras, titulo, musica)
        self.cinematic = BossCinematic()

        self.blasts = []
        self.mosquito_alert = False

        self.chest = None
        self.reward = 0
        self.reward_coins = []

        self.banner_t = 0.0
        self.collect_t = 0.0
        self.last_death = None
        self.gate_on = False

        self.completed = False
        self.final_clear = False
        self._sealed_msg_t = -10.0

        self.particles = []
        self.ring_t = None
        self.ring_pos = (0, 0)
        self.boom_light_t = None

        self._gate_time = 0.0

        self._out_t = 0.0


        w, h = screen_size

        self.dim = pygame.Surface((w, h), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 150))

        self.panel_img = load_image(
            COMBAT_DIR / "panel_sala_combate.png", self.PANEL_SIZE
        )

        self.hud_img = load_image(
            COMBAT_DIR / "hud_oleada.png", (180, 40)
        )

        self.banner_img = load_image(
            COMBAT_DIR / "pantalla_oleada_completa.png", (420, 200)
        )

        self.map_banner_img = load_image(
            COMBAT_DIR / "pantalla_mapa_completado.png", (420, 200)
        )

        self.sealed_img = load_image(
            COMBAT_DIR / "sala_sellada.png", (40, 160)
        )

        self.coin_icon = load_image(HUD_DIR / "icon_moneda.png", (22, 22))
        self.gem_icon = (
            get_green_gem_icon() if self.cfg.gem_id == "gema_verde"
            else get_gem_icon()
        )

        self.btn_imgs = {}

        for key, name in self.BUTTON_FILES.items():

            self.btn_imgs[key] = (
                load_image(COMBAT_DIR / f"{name}.png", self.BUTTON_SIZE),
                load_image(COMBAT_DIR / f"{name}_hover.png", self.BUTTON_SIZE),
            )


        self.panel_rect = pygame.Rect(0, 0, *self.PANEL_SIZE)
        self.panel_rect.center = (w // 2, h // 2)

        self.button_rects = {}

        for i, key in enumerate(self.BUTTONS):

            rect = pygame.Rect(0, 0, *self.BUTTON_SIZE)

            rect.midtop = (
                self.panel_rect.centerx,
                self.panel_rect.top + 78 + i * 70
            )

            self.button_rects[key] = rect


    @property
    def menu_open(self):

        return self.state == self.MENU

    @property
    def active(self):

        return self.state in (self.WAVE, self.CLEAR, self.COLLECT)

    @property
    def current_reward(self):

        mult = NO_ESCAPE_MULT if self.mode == "noescape" else 1

        return base_reward(self.wave, self.cfg.rewards) * mult

    def targets(self):

        out = []

        for e in self.enemies:

            if getattr(e, "is_boss", False):
                out.extend(e.hit_targets())
            elif not e.spawning and not e.dead and not getattr(e, "attached", False):
                out.append(e)

        return out

    def hurt_in_radius(self, center, radius, damage):

        cx, cy = center

        for enemy in self.targets():

            size = max(enemy.rect.width, enemy.rect.height) / 2

            dist = math.hypot(
                enemy.rect.centerx - cx,
                enemy.rect.centery - cy
            )

            if dist <= radius + size:

                enemy.hp -= damage
                enemy.flash = max(enemy.flash, ENEMY_FLASH_TIME)

    def light_sources(self):

        sources = []

        if self.chest is not None and not self.chest.done:
            sources.append(self.chest.light())

        for enemy in self.enemies:

            if isinstance(enemy, (Hongun, Destello)):

                light = enemy.light()

                if light is not None:
                    sources.append(light)

            elif isinstance(enemy, PinaBoss):

                sources.extend(enemy.lights())

        for blast in self.blasts:

            k = blast["t"] / HONGUN_BLAST_TIME

            sources.append((
                blast["x"], blast["y"],
                quantize_radius(80 + 190 * (1 - k) ** 1.5)
            ))

        if self.boom_light_t is not None:

            k = self.boom_light_t / 0.7

            sources.append((
                self.ring_pos[0], self.ring_pos[1],
                quantize_radius(120 + 200 * (1 - k))
            ))

        return sources


    def _open_menu(self, game):

        self.state = self.MENU
        self.armed = False
        self.banner_t = 0.0

        game.melee.cancel()

    def update_menu(self, dt):

        self._gate_time += dt

    def handle_event(self, game, event):

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:

            self._leave(game)

            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            for key, rect in self.button_rects.items():

                if rect.collidepoint(event.pos):

                    if key == "exit":
                        self._leave(game)
                    else:
                        self._begin(game, key)

                    return

    def _begin(self, game, mode):

        if not game.has_match:

            game.show_message("Necesitas una luz encendida para pelear")

            return

        self.mode = mode
        self.state = self.WAVE
        self.banner_t = 0.0
        self.last_death = None

        if mode == "noescape":
            self._close_gate(game)

        self._spawn_wave(game)

        if not self._is_boss_wave():
            game.show_message(f"Oleada {self.wave}")


    def _close_gate(self, game):

        if not self.gate_on:

            game.collision_map.obstacles.append(self.cfg.gate.copy())
            self.gate_on = True

    def _open_gate(self, game):

        if self.completed:
            return

        if self.gate_on:

            obstacles = game.collision_map.obstacles

            if self.cfg.gate in obstacles:
                obstacles.remove(self.cfg.gate)

            self.gate_on = False

    def restore_completed(self, game):

        if not self.completed:
            return

        self._seal(game)

    def _seal(self, game):

        p = game.player

        if self.cfg.room.collidepoint(p.rect.center) or p.rect.colliderect(
            self.cfg.gate.inflate(24, 24)
        ):
            self._teleport_out(game)

        self._close_gate(game)


    def _is_boss_wave(self):

        return bool(self.cfg.boss and self.wave == self.cfg.last_wave)

    def _spawn_boss(self, game):

        room = self.cfg.room

        if self.boss_art is None:
            self.boss_art = BossArt(COMBAT_DIR, load_image, load_strip)

        # la primera vez se ve la entrada completa; despues, una version corta
        first = not getattr(game, "boss_intro_seen", False)

        game.boss_intro_seen = True

        cin = self.cinematic

        boss = PinaBoss(
            room.centerx, room.centery, room, self.boss_art,
            intro_time=cin.intro_time(first),
            hold_time=cin.hold_time(first),
        )

        self.enemies = [boss]
        self.shots = []
        self.blasts = []

        cin.start_intro(game, first)

    def _boss_sound(self, event):

        if event in ("roar", "summon"):
            audio.play("alert")
        elif event in ("split", "phase", "die"):
            audio.play("explosion")
        elif event == "merge":
            audio.play("hit_heavy")

    def _boss_event(self, game, boss, event):

        fx = game.fx

        if event == "slam":

            self.cinematic.on_slam(game, boss)

        elif event == "die":

            # el golpe final: todo se congela un instante y arranca la caida
            self.cinematic.start_victory(game)

            fx.hitstop = max(fx.hitstop, 0.3)
            fx.shake(9.0, 0.7)

            audio.play("boss_slam")
            audio.play("boss_roar")

        elif event == "crack":

            audio.play("explosion")

            fx.shake(7.0, 0.45)

            for _ in range(14):

                a = random.uniform(0, math.tau)

                fx._spark(
                    boss.pos.x, boss.pos.y, a, random.uniform(50, 160),
                    random.uniform(0.4, 0.9),
                    random.choice(((255, 170, 70), (170, 235, 110))),
                    size=random.uniform(1.6, 2.8), drag=2.2, streak=True,
                )

        else:

            self._boss_sound(event)

    def _boss_summon(self, game, boss):

        wave = self.cfg.last_wave - 1

        hp = min(ENEMY_HP_MAX, ENEMY_HP_BASE + wave)
        tronco_hp = min(ENEMY_HP_MAX, hp + TRONCO_HP_EXTRA)
        speed = min(ENEMY_SPEED_MAX, ENEMY_SPEED_BASE + ENEMY_SPEED_STEP * wave)

        room = self.cfg.room
        cmap = game.collision_map
        player_pos = pygame.Vector2(game.player.rect.center)
        center = pygame.Vector2(room.center)

        kinds = ["pino", "tronco", "mosquito", "hongun"] * SUMMON_COUNT
        random.shuffle(kinds)

        hitboxes = {
            "mosquito": MOSQUITO_HITBOX,
            "hongun": HONGUN_HITBOX,
        }

        for i, kind in enumerate(kinds):

            hitbox = hitboxes.get(kind, ENEMY_HITBOX)

            pos = None

            for _ in range(80):

                angle = random.uniform(0, math.tau)
                dist = random.uniform(40, 135)

                x = center.x + math.cos(angle) * dist
                y = center.y + math.sin(angle) * dist * 0.8

                probe = pygame.Rect(0, 0, *hitbox)
                probe.center = (round(x), round(y))

                if not (room.contains(probe) and cmap.can_move(probe)):
                    continue
                if player_pos.distance_to((x, y)) < 70:
                    continue
                if any(
                    pygame.Vector2(x, y).distance_to(e.pos) < 14
                    for e in self.enemies if e is not boss
                ):
                    continue

                pos = (x, y)
                break

            if pos is None:
                pos = (center.x + random.uniform(-30, 30),
                       center.y + random.uniform(-30, 30))

            delay = i * 0.06

            if kind == "tronco":
                enemy = Tronco(pos[0], pos[1], tronco_hp, spawn_delay=delay)
            elif kind == "mosquito":
                enemy = Mosquito(pos[0], pos[1], MOSQUITO_HP, spawn_delay=delay)
            elif kind == "hongun":
                enemy = Hongun(pos[0], pos[1], spawn_delay=delay)
            else:
                enemy = Enemy(pos[0], pos[1], hp, speed, spawn_delay=delay)

            enemy.codex_key = kind
            enemy.room = room

            # se van solos a los BOSS_MINION_LIFE segundos
            enemy.boss_life = BOSS_MINION_LIFE

            self.enemies.append(enemy)

        game.show_message("La piña invoca refuerzos!")

    def _expire_minions(self, game, boss, dt):
        """Los enemigos invocados por el jefe desaparecen despues de 35 s.

        Se van sin soltar nada (no cuentan como muertos del jugador).
        """

        gone = []

        for e in self.enemies:

            life = getattr(e, "boss_life", None)

            if life is None or e is boss:
                continue

            e.boss_life = life - dt

            if e.boss_life <= 0:
                gone.append(e)

        if not gone:
            return

        for e in gone:
            self._death_puff(pygame.Vector2(e.pos))

        self.enemies = [e for e in self.enemies if e not in gone]

        game.show_message("Los refuerzos de la piña se fueron!")

    def _update_boss(self, game, boss, dt, target, body):

        boss.minions = sum(
            1 for e in self.enemies if e is not boss and not e.dead
        )

        boss.update(dt, target)

        if not boss.dying:
            self._expire_minions(game, boss, dt)

        for event in boss.events:
            self._boss_event(game, boss, event)

        boss.events = []

        self.cinematic.update(dt, game, boss)

        if boss.summon_request:

            boss.summon_request = False
            self._boss_summon(game, boss)

        if boss.dying:

            if not boss.cleanup_done:

                boss.cleanup_done = True

                for e in self.enemies:
                    if e is not boss:
                        self._death_puff(e.pos)

                self.enemies = [boss]
                self.shots = []

            if boss.fx_cd <= 0:

                boss.fx_cd = 0.32 - 0.22 * boss.dying_k

                self._death_puff(pygame.Vector2(
                    boss.pos.x + random.uniform(-boss.size / 2, boss.size / 2),
                    boss.pos.y + random.uniform(-boss.size / 2, boss.size / 2),
                ))

            return

        hit = boss.contact_hit(body)

        if hit is not None:

            damage, origin = hit
            p = game.player

            if p.hurt(origin):

                game.take_damage(damage)

                away = pygame.Vector2(body.center) - pygame.Vector2(origin)

                if away.length_squared() > 0.01:
                    p.kb_vel = away.normalize() * CONTACT_PUSH

    def _spawn_wave(self, game):

        self._hits_at_wave_start = getattr(game, "hits_taken", 0)

        if self._is_boss_wave():

            self._spawn_boss(game)

            return

        (pinos, troncos, mosquitos, honguns, guardians,
         shooters, destellos, golems) = wave_composition(
            self.wave, self.cfg.table
        )

        kinds = (
            ["pino"] * pinos + ["tronco"] * troncos
            + ["mosquito"] * mosquitos + ["hongun"] * honguns
            + ["guardian"] * guardians + ["tirador"] * shooters
            + ["destello"] * destellos + ["golem"] * golems
        )
        random.shuffle(kinds)

        hp = min(ENEMY_HP_MAX, ENEMY_HP_BASE + self.wave)
        tronco_hp = min(ENEMY_HP_MAX, hp + TRONCO_HP_EXTRA)
        speed = min(ENEMY_SPEED_MAX, ENEMY_SPEED_BASE + ENEMY_SPEED_STEP * self.wave)

        cmap = game.collision_map
        player_pos = pygame.Vector2(game.player.rect.center)
        corners = [
            (self.cfg.room.left + 40, self.cfg.room.top + 30),
            (self.cfg.room.right - 40, self.cfg.room.top + 30),
            (self.cfg.room.left + 40, self.cfg.room.bottom - 30),
            (self.cfg.room.right - 40, self.cfg.room.bottom - 30),
        ]

        self.enemies = []
        self.shots = []
        self.blasts = []

        for i, kind in enumerate(kinds):
            pos = None
            min_dist = 135 if kind in ("mosquito", "hongun", "guardian", "tirador", "destello", "golem") else 110

            if kind == "mosquito":
                hitbox = MOSQUITO_HITBOX
            elif kind == "hongun":
                hitbox = HONGUN_HITBOX
            elif kind == "destello":
                hitbox = DESTELLO_HITBOX
            elif kind == "golem":
                hitbox = GOLEM_HITBOX
            elif kind in ("guardian", "tirador"):
                hitbox = GUARDIAN_HITBOX
            else:
                hitbox = ENEMY_HITBOX

            for _ in range(120):
                x = random.randint(self.cfg.room.left + 16, self.cfg.room.right - 16)
                y = random.randint(self.cfg.room.top + 16, self.cfg.room.bottom - 16)
                probe = pygame.Rect(0, 0, *hitbox)
                probe.center = (x, y)
                if pygame.Vector2(x, y).distance_to(player_pos) < min_dist:
                    continue
                if not (self.cfg.room.contains(probe) and cmap.can_move(probe)):
                    continue
                if any(pygame.Vector2(x, y).distance_to(e.pos) < 18 for e in self.enemies):
                    continue
                pos = (x, y)
                break

            if pos is None:
                pos = corners[i % len(corners)]

            delay = i * 0.15
            if kind == "tronco":
                enemy = Tronco(pos[0], pos[1], tronco_hp, spawn_delay=delay)
            elif kind == "mosquito":
                enemy = Mosquito(pos[0], pos[1], MOSQUITO_HP, spawn_delay=delay)
            elif kind == "hongun":
                enemy = Hongun(pos[0], pos[1], spawn_delay=delay)
            elif kind == "destello":
                enemy = Destello(pos[0], pos[1], spawn_delay=delay)
                if self.wave <= DESTELLO_EARLY_WAVES:
                    enemy.alert_time = DESTELLO_ALERT_TIME_EARLY
            elif kind == "golem":
                enemy = Golem(pos[0], pos[1], spawn_delay=delay)
            elif kind == "guardian":
                enemy = Guardian(pos[0], pos[1], spawn_delay=delay)
            elif kind == "tirador":
                enemy = GuardianShooter(pos[0], pos[1], spawn_delay=delay)
            else:
                enemy = Enemy(pos[0], pos[1], hp, speed, spawn_delay=delay)

            enemy.codex_key = (
                "guardian_tirador" if kind == "tirador" else kind
            )

            enemy.room = self.cfg.room

            self.enemies.append(enemy)

        fx = getattr(game, "fx", None)

        if fx is not None:
            fx.wave_start(
                self.cfg.room.centerx, self.cfg.room.centery, self.wave,
                self.cfg.room,
                [e.pos for e in self.enemies]
            )

    def _wave_cleared(self, game):

        if (
            self.wave >= 5
            and getattr(game, "hits_taken", 0)
            == getattr(self, "_hits_at_wave_start", -1)
        ):
            achievements.unlock("intocable")

        pos = self.last_death or self.cfg.room.center

        self.reward = self.current_reward
        self.chest = RewardChest(pos[0], pos[1])
        self.state = self.CLEAR

        if not self._is_boss_wave():
            audio.play("wave_clear")

        self._open_gate(game)

    def _explode(self, game):

        cx, cy = self.chest.x, self.chest.y

        self.ring_t = 0.0
        self.ring_pos = (cx, cy)
        self.boom_light_t = 0.0

        for _ in range(45):

            angle = random.uniform(0, math.tau)
            speed = random.uniform(30, 120)
            life = random.uniform(0.4, 0.9)

            self.particles.append({
                "x": cx,
                "y": cy - 4,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 30,
                "life": life,
                "max": life,
                "color": random.choice([
                    (255, 235, 140), (255, 200, 70),
                    (255, 255, 255), (255, 160, 50)
                ]),
            })

        # pocas monedas grandes (azules/rojas) en vez de muchas doradas
        values = split_coins(self.reward, MAX_COIN_ITEMS) or [self.reward]

        self.reward_coins = []

        for n, value in enumerate(values):

            coin = WorldItem(coin_id_for(value), cx, cy)

            coin.value = value
            coin.sparkle = True

            target = self._coin_target(game, cx, cy)

            coin.start_fly((cx, cy), target, delay=n * 0.025, height=18)

            self.reward_coins.append(coin)

        game.world_items.extend(self.reward_coins)

        self.state = self.COLLECT
        self.collect_t = 0.0
        self.banner_t = BANNER_TIME

        if self.wave == self.cfg.last_wave:

            # la gema se cuenta recien cuando la agarras
            gem = WorldItem(self.cfg.gem_id, cx, cy)
            gem.value = 1
            gem.sparkle = True

            gem.start_fly(
                (cx, cy), self._coin_target(game, cx, cy),
                delay=0.25, height=26, duration=0.6
            )

            self.reward_coins.append(gem)
            game.world_items.append(gem)

            self.final_clear = True
            self.completed = True
            self.banner_t = BANNER_TIME_FINAL

        self.wave += 1

    def _coin_target(self, game, cx, cy):

        for _ in range(30):

            angle = random.uniform(0, math.tau)
            dist = random.uniform(14, 46)

            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist

            if self.cfg.room.collidepoint(x, y) and game.collision_map.point_is_walkable(x, y):
                return (x, y)

        return (cx, cy + 14)

    def _coins_left(self, game):

        return [c for c in self.reward_coins if c in game.world_items]

    def _credit_leftover(self, game):

        for coin in self._coins_left(game):

            game.world_items.remove(coin)

            if coin.item_id in ("gema", "gema_verde"):
                self._add_gem(
                    game, getattr(coin, "value", 1), coin.item_id
                )
            else:
                game.add_coins(getattr(coin, "value", 1))

        self.reward_coins = []


    def _add_gem(self, game, amount=1, item_id=None):

        if (item_id or self.cfg.gem_id) == "gema_verde":
            game.gems_green += amount
        else:
            game.gems += amount


    def _teleport_out(self, game):

        p = game.player

        p.rect.center = self.cfg.exit_pos
        p.image_rect.midbottom = (p.rect.centerx, p.rect.bottom + 3)

        p.kb_vel = pygame.Vector2()

        game.camera.update(p)
        game.melee.cancel()

    def _release_player(self, game):

        p = game.player

        p.grabbed = False
        p.grab_lift = 0.0

    def _end_run(self, game):

        self._release_player(game)
        self._credit_leftover(game)
        self._open_gate(game)

        self.cinematic.cancel()

        self.enemies = []
        self.shots = []
        self.chest = None
        self.reward = 0
        self.mode = None
        self.banner_t = 0.0
        self.final_clear = False
        self._out_t = 0.0
        self.state = self.IDLE

        if self.completed:
            self._seal(game)

    def _finish_map(self, game):

        self._end_run(game)
        self._teleport_out(game)

        game.show_message(self.cfg.done_text)
        game.save_progress()

    def _leave(self, game):

        self._end_run(game)
        self._teleport_out(game)

    def _player_died(self, game):

        self._end_run(game)

        game.state = "dying"
        game.fade_alpha = 0


    def _update_fx(self, dt):

        for p in self.particles:

            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= max(0.0, 1 - 2.0 * dt)
            p["vy"] *= max(0.0, 1 - 2.0 * dt)

        self.particles = [p for p in self.particles if p["life"] > 0]

        if self.ring_t is not None:

            self.ring_t += dt

            if self.ring_t > 0.5:
                self.ring_t = None

        if self.boom_light_t is not None:

            self.boom_light_t += dt

            if self.boom_light_t > 0.7:
                self.boom_light_t = None

        for blast in self.blasts:
            blast["t"] += dt

        self.blasts = [b for b in self.blasts if b["t"] < HONGUN_BLAST_TIME]

        self._gate_time += dt

    def update(self, game, dt):

        self._update_fx(dt)

        if self.state != self.WAVE:
            self.mosquito_alert = False

            if self.cinematic.active:
                self.cinematic.update(dt, game, None)

        p = game.player

        if self.state == self.IDLE:

            if self.completed:

                if (
                    p.rect.colliderect(self.cfg.gate.inflate(40, 30))
                    and self._gate_time - self._sealed_msg_t > 2.5
                ):
                    self._sealed_msg_t = self._gate_time
                    game.show_message(
                        self.cfg.sealed_text
                    )

                return

            center = p.rect.center

            if self.armed and self.cfg.trigger.collidepoint(center):
                self._open_menu(game)

            elif not self.armed and not self.cfg.room.collidepoint(center):
                self.armed = True

            return

        if self.state == self.MENU:
            return

        if self.banner_t > 0:
            self.banner_t = max(0.0, self.banner_t - dt)

        outside = not self.cfg.room.collidepoint(p.rect.center)

        if outside:
            self._out_t += dt
        else:
            self._out_t = 0.0

        if outside and self._out_t < ESCAPE_GRACE:

            if self._out_t - dt <= 0.0 and self.state == self.WAVE:
                game.show_message("Volve a la sala o se cancela la oleada")

            outside = False

        if outside:

            if self.state == self.WAVE:

                game.show_message("Saliste de la sala. Oleada cancelada")

            elif self.state == self.CLEAR:

                game.add_coins(self.reward)

                game.show_message(f"+{self.reward} monedas")

                if self.wave == self.cfg.last_wave:

                    self._add_gem(game)

                    self.wave += 1
                    self.completed = True

                    game.show_message(
                        f"+{self.reward} monedas y 1 {self.cfg.gem_name}. "
                        "Mapa completado!"
                    )

                    game.save_progress()

            self._end_run(game)

            if self.completed:
                game.save_progress()

            return

        if self.state == self.WAVE:
            self._update_wave(game, dt)

        elif self.state == self.CLEAR:

            if self.chest.update(dt):
                self._explode(game)

        elif self.state == self.COLLECT:
            self._update_collect(game, dt)

    def _update_wave(self, game, dt):

        pathing.begin_frame()

        for e in self.enemies:

            key = getattr(e, "codex_key", None)

            if key and not e.spawning:
                game.discover_enemy(key)

        p = game.player
        target = p.rect.center
        body = pygame.Rect(0, 0, 10, 16)
        body.midbottom = (p.rect.centerx, p.rect.bottom)
        light_on = bool(game.has_match)
        light_world = game._light_radius() / game.camera.zoom if light_on else 0.0
        repel = light_on and game.repel_timer > 0

        for enemy in list(self.enemies):
            if isinstance(enemy, PinaBoss):
                self._update_boss(game, enemy, dt, target, body)
            elif isinstance(enemy, Mosquito):
                enemy.update(dt, target, game.collision_map, light_on, light_world, repel)
                if enemy.attached and enemy.damage_t <= 0.0:
                    game.take_damage(MOSQUITO_DAMAGE)
                    enemy.damage_t = MOSQUITO_DAMAGE_INTERVAL
            elif isinstance(enemy, GuardianShooter):
                enemy.update(dt, target, game.collision_map, light_on, light_world)
                new_shots = enemy.take_shots()
                if new_shots:
                    audio.play("shot")
                self.shots.extend(new_shots)
            elif isinstance(enemy, Golem):
                enemy.update(dt, target, game.collision_map, others=self.enemies)
                self._golem_step(game, enemy, body, dt)
            elif isinstance(enemy, Guardian):
                enemy.update(dt, target, game.collision_map, light_on, light_world)
                if enemy.swing_hits(body.center):
                    if p.hurt(enemy.pos):
                        game.take_damage(GUARDIAN_DAMAGE)
                        away = pygame.Vector2(body.center) - enemy.pos
                        if away.length_squared() > 0.01:
                            p.kb_vel = away.normalize() * GUARDIAN_KNOCKBACK
            else:
                if enemy.fixed:
                    enemy.light_radius = light_world
                enemy.update(dt, target, game.collision_map, self.enemies)
                if enemy.fixed:
                    new_shots = enemy.take_shots()
                    if new_shots:
                        audio.play("shot")
                    self.shots.extend(new_shots)

        if p.grabbed and not any(
            isinstance(e, Golem) and e.holding and not e.dead
            for e in self.enemies
        ):
            self._release_player(game)

        was_alert = self.mosquito_alert

        self.mosquito_alert = any(
            isinstance(e, Mosquito) and e.alert and not e.dead
            for e in self.enemies
        )

        if self.mosquito_alert and not was_alert:
            audio.play("alert")

        bounce_enemies(
            [e for e in self.enemies if not isinstance(e, PinaBoss)],
            game.collision_map, target
        )

        for shot in self.shots:
            shot.update(dt, game.collision_map)

        damage = min(ENEMY_DAMAGE_MAX, ENEMY_DAMAGE + ENEMY_DAMAGE_STEP * (self.wave - 1))

        for enemy in self.enemies:
            if (enemy.spawning or enemy.touch_cd > 0 or enemy.dead
                    or not enemy.contact_damage or getattr(enemy, "attached", False)):
                continue
            if enemy.rect.colliderect(body):
                if p.hurt(enemy.pos):
                    game.take_damage(damage)
                enemy.bounce_from(body.center)

        for shot in self.shots:
            if shot.dead:
                continue
            if shot.rect.colliderect(body):
                if p.hurt(shot.pos):
                    amount = getattr(shot, "damage", None)
                    game.take_damage(
                        amount if amount is not None
                        else damage * SHOT_DAMAGE_MULT
                    )
                    push = getattr(shot, "knockback", 0.0)
                    away = pygame.Vector2(body.center) - shot.pos
                    if push and away.length_squared() > 0.01:
                        p.kb_vel = away.normalize() * push
                shot.dead = True

        self.shots = [s for s in self.shots if not s.dead]

        for enemy in self.enemies:
            if isinstance(enemy, Hongun) and enemy.boom and not enemy.boomed:
                enemy.boomed = True
                self._hongun_explode(game, enemy)

        for enemy in self.enemies:
            if (
                isinstance(enemy, Destello)
                and enemy.can_explode
                and enemy.rect.colliderect(body)
            ):
                enemy.boom = True
                enemy.boomed = True
                enemy.hp = 0
                self._destello_explode(game, enemy)

        for enemy in self.enemies:
            if enemy.dead:
                self.last_death = (enemy.pos.x, enemy.pos.y)

                if isinstance(enemy, PinaBoss):
                    self.cinematic.finale(game, enemy)

                game.count_stat("kills")
                achievements.add_counter("kills")

                if (
                    isinstance(enemy, Destello)
                    and not getattr(enemy, "boom", False)
                ):
                    achievements.unlock("desactivado")

                if not getattr(enemy, "boom", False):
                    self._death_puff(enemy.pos)

        self.enemies = [e for e in self.enemies if not e.dead]

        if game.vida <= 0:
            self._player_died(game)
            return

        if not self.enemies:
            self.shots = []
            self._wave_cleared(game)


    def _golem_step(self, game, enemy, body, dt):

        p = game.player

        if (
            enemy.can_grab(body)
            and not p.grabbed
            and p.invuln_timer <= 0
        ):
            enemy.start_grab(pygame.Vector2(p.rect.center) - enemy.pos)

            achievements.unlock("abrazo_golem")

            p.grabbed = True
            p.kb_vel = pygame.Vector2()
            game.melee.cancel()

        if enemy.holding:

            self._golem_hold(game, enemy, dt)

            if enemy.take_squeeze():
                self._golem_squeeze(game, enemy)

        if enemy.take_release():

            p.grabbed = False
            p.grab_lift = 0.0

            p.kb_vel = enemy.grab_dir * GOLEM_KNOCKBACK
            p.invuln_timer = max(p.invuln_timer, GOLEM_POST_INVULN)

    def _golem_hold(self, game, enemy, dt):

        p = game.player

        hold = pygame.Vector2(
            enemy.rect.centerx, enemy.rect.bottom + GOLEM_HOLD_DY
        )
        cur = pygame.Vector2(p.rect.center)
        gap = hold - cur
        dist = gap.length()

        if dist > 0.5:

            nxt = cur + gap / dist * min(dist, GOLEM_HOLD_PULL * dt)

            test = p.rect.copy()
            test.center = (round(nxt.x), round(nxt.y))

            if game.collision_map.can_move(test):
                p.rect.center = test.center

        p.image_rect.midbottom = (p.rect.centerx, p.rect.bottom + 3)

        p.kb_vel = pygame.Vector2()
        p.grabbed = True
        p.grab_lift = enemy.lift

        game.melee.cancel()

    def _golem_squeeze(self, game, enemy):

        p = game.player

        game.hits_taken = getattr(game, "hits_taken", 0) + 1
        pos = pygame.Vector2(p.rect.center)

        p.hurt_timer = p.HURT_TIME

        if game.escudo > 0:

            game.escudo = 0.0

            game.show_message("El Golem te saco todo el escudo!")

        else:

            game.vida = 0.0

            game.show_message("El Golem te aplasto: se apago tu luz!")

        for _ in range(34):

            angle = random.uniform(0, math.tau)
            speed = random.uniform(25, 110)
            life = random.uniform(0.3, 0.8)

            self.particles.append({
                "x": pos.x,
                "y": pos.y - 6,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": life,
                "max": life,
                "color": random.choice([
                    (150, 150, 160), (110, 110, 122),
                    (190, 190, 198), (90, 80, 70)
                ]),
            })

    def _hongun_fx(self, game, pos, player_dist):

        fx = game.fx

        x, y = pos.x, pos.y
        R = HONGUN_BLAST_RADIUS

        fx._spark(x, y, 0, 0, 0.12, (255, 255, 255), size=44, drag=0)
        fx._spark(x, y, 0, 0, 0.22, (255, 250, 200), size=34, drag=0)
        fx._spark(x, y, 0, 0, 0.45, (130, 235, 120), size=R * 0.75, drag=0)

        fx._ring(x, y, 4, R, 0.32, (255, 255, 255), 6)
        fx._ring(x, y, 2, R * 1.2, 0.5, (150, 255, 140), 4, delay=0.05)
        fx._ring(x, y, 2, R * 0.65, 0.28, (255, 236, 150), 3, delay=0.09)

        for _ in range(38):

            fx._spark(
                x, y, random.uniform(0, math.tau),
                random.uniform(150, 430), random.uniform(0.25, 0.6),
                random.choice((
                    (255, 255, 255), (235, 255, 215),
                    (150, 240, 130), (255, 235, 140)
                )),
                size=random.uniform(1.6, 3.2), drag=3.2, streak=True
            )

        for _ in range(28):

            fx._spark(
                x + random.uniform(-4, 4), y + random.uniform(-4, 4),
                random.uniform(0, math.tau),
                random.uniform(20, 95), random.uniform(0.8, 1.6),
                random.choice((
                    (90, 190, 85), (120, 215, 110), (170, 240, 150)
                )),
                size=random.uniform(2.5, 5.0), drag=1.7, grav=-22
            )

        for _ in range(14):

            fx._spark(
                x, y - 3, random.uniform(math.pi * 1.05, math.pi * 1.95),
                random.uniform(70, 190), random.uniform(0.5, 0.95),
                random.choice((
                    (205, 70, 60), (240, 215, 175), (170, 50, 50)
                )),
                size=random.uniform(2.0, 3.6), drag=1.6, grav=340
            )

        for _ in range(10):

            fx._spark(
                x + random.uniform(-5, 5), y + random.uniform(-3, 3),
                random.uniform(0, math.tau),
                random.uniform(8, 40), random.uniform(1.0, 1.7),
                (95, 100, 98),
                size=random.uniform(4.0, 6.5), drag=1.4, grav=-12,
                delay=0.08
            )

        near = max(0.0, min(1.0, 1.0 - player_dist / (R * 2.4)))

        fx.shake(2.5 + 8.0 * near, 0.3 + 0.3 * near)

        if player_dist <= R:

            fx.hitstop = max(fx.hitstop, 0.06)

            fx.flash(0.2, (225, 255, 215), 0.45)

    def _hongun_explode(self, game, enemy):

        p = game.player
        pos = pygame.Vector2(enemy.pos)

        audio.play("explosion")

        self.blasts.append({"x": pos.x, "y": pos.y, "t": 0.0})

        body = pygame.Vector2(p.rect.center)

        self._hongun_fx(game, pos, body.distance_to(pos))

        body = pygame.Vector2(p.rect.center)

        if body.distance_to(pos) > HONGUN_BLAST_RADIUS:
            return

        p.invuln_timer = 0.0
        p.hurt(pos)

        game.take_damage(HONGUN_DAMAGE)

        away = body - pos

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        p.kb_vel = away.normalize() * HONGUN_KNOCKBACK

    def _destello_explode(self, game, enemy):

        achievements.unlock("ojos_ciegos")

        p = game.player
        pos = pygame.Vector2(enemy.pos)
        body = pygame.Vector2(p.rect.center)

        p.invuln_timer = 0.0
        p.hurt(pos)

        game.take_damage(DESTELLO_DAMAGE)

        away = body - pos

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        p.kb_vel = away.normalize() * DESTELLO_KNOCKBACK

        game.flashbang(pos.x, pos.y)

    def _death_puff(self, pos):

        audio.play("enemy_die")

        for _ in range(10):

            angle = random.uniform(0, math.tau)
            speed = random.uniform(15, 50)

            self.particles.append({
                "x": pos.x,
                "y": pos.y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 0.4,
                "max": 0.4,
                "color": (150, 105, 70),
            })

    def _update_collect(self, game, dt):

        self.collect_t += dt

        self.chest.update(dt)

        left = self._coins_left(game)

        done = not left and self.collect_t > 1.0

        if self.final_clear:
            done = done and self.banner_t <= 0

        if done or self.collect_t > COLLECT_TIMEOUT:

            self.chest = None

            if self.final_clear:
                self._finish_map(game)
            else:
                self._open_menu(game)


    def draw_world(self, screen, camera):

        view = screen.get_rect().inflate(320, 320)

        for enemy in self.enemies:
            if not view.colliderect(camera.apply(enemy.rect)):
                continue
            if isinstance(enemy, PinaBoss):
                enemy.draw(screen, camera)
            elif isinstance(enemy, Mosquito):
                enemy.draw(screen, camera, self.mosquito_art)
            elif isinstance(enemy, Hongun):
                enemy.draw(screen, camera, self.hongun_art)
            elif isinstance(enemy, Destello):
                enemy.draw(screen, camera, self.destello_art)
            elif isinstance(enemy, Golem):
                enemy.draw(screen, camera, self.golem_art)
            elif isinstance(enemy, GuardianShooter):
                enemy.draw(screen, camera, self.shooter_art)
            elif isinstance(enemy, Guardian):
                enemy.draw(screen, camera, self.guardian_art)
            else:
                enemy.draw(
                    screen, camera,
                    self.tronco_art if enemy.fixed else self.art
                )

        if self.chest is not None and not self.chest.done:
            self.chest.draw(screen, camera)

        if self.gate_on and self.completed:

            rect = camera.apply(self.cfg.gate)

            if self.sealed_img is not None:

                img = self.sealed_img

                if img.get_size() != rect.size:
                    img = pygame.transform.smoothscale(img, rect.size)

                screen.blit(img, rect)

            else:

                pygame.draw.rect(screen, (46, 46, 54), rect)
                pygame.draw.rect(screen, (120, 120, 134), rect, 2)

        elif self.gate_on:

            rect = camera.apply(self.cfg.gate)

            pulse = 0.5 + 0.5 * math.sin(self._gate_time * 6)

            bar = pygame.Surface(rect.size, pygame.SRCALPHA)
            bar.fill((255, 60, 50, int(90 + 90 * pulse)))

            screen.blit(bar, rect)

    def draw_fx(self, screen, camera):

        if self.chest is not None and not self.chest.done:
            self.chest.draw_glow(screen, camera)

        for shot in self.shots:
            shot.draw(screen, camera, self.tronco_art)

        for enemy in self.enemies:

            if isinstance(enemy, Hongun) and enemy.fuse_t > 0 and not enemy.dead:
                self._draw_hongun_glow(screen, camera, enemy)

        for blast in self.blasts:

            k = blast["t"] / HONGUN_BLAST_TIME

            radius = int((4 + HONGUN_BLAST_RADIUS * k) * camera.zoom)

            cx = int(blast["x"] * camera.zoom - camera.x)
            cy = int(blast["y"] * camera.zoom - camera.y)

            ring = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)

            pygame.draw.circle(
                ring, (255, 255, 255, int(70 * (1 - k))),
                (radius + 4, radius + 4), radius
            )

            pygame.draw.circle(
                ring, (255, 255, 235, int(230 * (1 - k))),
                (radius + 4, radius + 4), radius,
                max(2, int(7 * (1 - k)))
            )

            screen.blit(ring, ring.get_rect(center=(cx, cy)))

        if self.ring_t is not None:

            k = self.ring_t / 0.5

            radius = int((6 + 46 * k) * camera.zoom)

            cx = int(self.ring_pos[0] * camera.zoom - camera.x)
            cy = int(self.ring_pos[1] * camera.zoom - camera.y)

            ring = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)

            pygame.draw.circle(
                ring,
                (255, 240, 170, int(220 * (1 - k))),
                (radius + 4, radius + 4),
                radius,
                max(2, int(8 * (1 - k)))
            )

            screen.blit(ring, ring.get_rect(center=(cx, cy)))

        for part in self.particles:

            alpha = max(0.0, part["life"] / part["max"])

            sx = int(part["x"] * camera.zoom - camera.x)
            sy = int(part["y"] * camera.zoom - camera.y)

            size = max(2, int(3 * camera.zoom * alpha))

            pygame.draw.circle(screen, part["color"], (sx, sy), size)

    def _draw_hongun_glow(self, screen, camera, enemy):

        k = enemy.fuse_k

        blink = 0.5 + 0.5 * math.sin(enemy.anim_t * (14 + 36 * k))

        radius = max(4, int((10 + 16 * k) * camera.zoom))

        cx = int(enemy.pos.x * camera.zoom - camera.x)
        cy = int(enemy.pos.y * camera.zoom - camera.y)

        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

        for i in range(4, 0, -1):

            alpha = int((25 + 55 * k) * (0.5 + 0.5 * blink) * (5 - i) / 4)

            pygame.draw.circle(
                glow, (255, 255, 255, alpha),
                (radius, radius), int(radius * i / 4)
            )

        screen.blit(glow, glow.get_rect(center=(cx, cy)))

    def draw_hud(self, screen):

        if not self.active:
            return


        rect = pygame.Rect(18, 18, 180, 40)

        if self.hud_img is not None:

            screen.blit(self.hud_img, rect)

        else:

            pygame.draw.rect(screen, (138, 146, 158), rect, border_radius=8)
            pygame.draw.rect(screen, (84, 92, 104), rect, 3, border_radius=8)

        number = self.wave - 1 if self.state == self.COLLECT else self.wave

        if self.cfg.boss and number == self.cfg.last_wave:
            label = "JEFE"
        else:
            label = f"Oleada {number}"

        if self.cfg.show_total:
            label += f"/{self.cfg.last_wave}"

        draw_text(
            screen, label, 28, (255, 255, 255),
            center=rect.center
        )

        if self.state == self.WAVE:

            draw_text(
                screen, f"Enemigos: {len(self.enemies)}", 24,
                (235, 235, 235), topleft=(rect.left + 4, rect.bottom + 8)
            )

            premio_y = rect.bottom + 34

        else:

            premio_y = rect.bottom + 8

        premio = self.current_reward if self.state == self.WAVE else self.reward

        x = rect.left + 4

        if self.coin_icon is not None:

            screen.blit(self.coin_icon, (x, premio_y - 2))
            x += 28

        text_rect = draw_text(
            screen, f"{premio}", 26, (255, 225, 120),
            topleft=(x, premio_y)
        )

        if self.mode == "noescape":

            draw_text(
                screen, "X2", 26, (255, 150, 60),
                topleft=(text_rect.right + 8, premio_y)
            )


        if self.state == self.WAVE and not self.cinematic.active:

            for enemy in self.enemies:
                if getattr(enemy, "is_boss", False):
                    draw_boss_bar(screen, enemy)

        if self.banner_t > 0 and not self.cinematic.active:
            self._draw_banner(screen)

        self.cinematic.draw(screen)

    def _draw_banner(self, screen):

        w, h = self.size

        alpha = int(255 * min(1.0, self.banner_t / 0.5))

        rect = pygame.Rect(0, 0, 420, 200)
        rect.center = (w // 2, int(h * 0.30))

        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        local = layer.get_rect()

        final = self.final_clear

        img = self.map_banner_img if final else self.banner_img

        if img is not None:

            layer.blit(img, (0, 0))

        else:

            pygame.draw.rect(layer, (30, 30, 38, 225), local, border_radius=14)
            pygame.draw.rect(layer, (200, 200, 210), local, 3, border_radius=14)

            draw_text(
                layer,
                "Mapa completado!" if final else "Oleada completada!",
                40, (255, 240, 170),
                center=(local.centerx, 56)
            )

        # el premio va abajo, para no tapar el texto de felicitaciones del cartel
        y = local.h - 44

        if final:

            if self.coin_icon is not None:

                coin = pygame.transform.smoothscale(self.coin_icon, (32, 32))
                layer.blit(coin, coin.get_rect(center=(local.centerx - 120, y)))

            draw_text(
                layer, f"+{self.reward}", 44, (255, 225, 120),
                midleft=(local.centerx - 98, y)
            )

            gem = pygame.transform.smoothscale(self.gem_icon, (32, 32))

            layer.blit(gem, gem.get_rect(center=(local.centerx + 50, y)))

            draw_text(
                layer, "+1", 44, (190, 235, 255),
                midleft=(local.centerx + 74, y)
            )

        else:

            draw_text(
                layer, f"+{self.reward}", 48, (255, 225, 120),
                center=(local.centerx + 14, y)
            )

            if self.coin_icon is not None:

                coin = pygame.transform.smoothscale(self.coin_icon, (32, 32))
                layer.blit(coin, coin.get_rect(center=(local.centerx - 52, y)))

        layer.set_alpha(alpha)

        screen.blit(layer, rect)

    def _draw_zone_warning(self, screen, game):

        cfg = self.cfg

        if not cfg.zone_name:
            return

        cx = self.panel_rect.centerx
        top = self.panel_rect.top

        lines = [
            (f"Estás en la zona {cfg.zone_name} ({cfg.zone_tag})", 34,
             (255, 240, 200)),
        ]

        right = getattr(game, "arena", None)
        right_done = bool(right is not None and right.completed)

        if self._is_boss_wave():
            lines.append((
                f"¡JEFE! Te enfrentás a la {BOSS_NAME}", 30, (255, 214, 120)
            ))
            lines.append((
                "Guardiana de la gema: se parte en pedazos y invoca ayudantes.",
                24, (255, 170, 120)
            ))

        lines.append((
            "Al empezar la oleada se oscurece: fijate bien dónde estás.",
            22, (220, 220, 235)
        ))

        gap = 8
        heights = [get_font(size).get_height() for _, size, _ in lines]
        total = sum(heights) + gap * (len(lines) - 1) + 24
        width = 640

        box = pygame.Rect(0, 0, width, total)
        box.midbottom = (cx, top - 10)

        back = pygame.Surface(box.size, pygame.SRCALPHA)

        border = (255, 110, 90, 230) if (
            cfg.hard and not right_done
        ) else (226, 201, 150, 200)

        pygame.draw.rect(
            back, (0, 0, 0, 170), back.get_rect(), border_radius=12
        )
        pygame.draw.rect(
            back, border, back.get_rect(), 2, border_radius=12
        )

        screen.blit(back, box)

        y = box.top + 12

        for (text, size, color), h in zip(lines, heights):

            draw_text(screen, text, size, color, midtop=(cx, y))

            y += h + gap

    def draw_menu(self, screen, game):

        screen.blit(self.dim, (0, 0))

        if self.panel_img is not None:

            screen.blit(self.panel_img, self.panel_rect)

        else:

            pygame.draw.rect(
                screen, (24, 24, 32), self.panel_rect, border_radius=16
            )
            pygame.draw.rect(
                screen, (180, 180, 192), self.panel_rect, 3, border_radius=16
            )

        draw_text(
            screen, self.cfg.title, 36, (255, 240, 200),
            center=(self.panel_rect.centerx, self.panel_rect.top + 26)
        )

        reward = base_reward(self.wave, self.cfg.rewards)

        draw_text(
            screen,
            f"{'JEFE' if self._is_boss_wave() else 'Oleada ' + str(self.wave)}   Premio: {reward}   "
            f"(sin escape: {reward * NO_ESCAPE_MULT})",
            22, (255, 225, 120),
            center=(self.panel_rect.centerx, self.panel_rect.top + 54)
        )

        mouse = pygame.mouse.get_pos()

        for key in self.BUTTONS:

            rect = self.button_rects[key]

            hover = rect.collidepoint(mouse)

            normal, over = self.btn_imgs[key]

            img = over if (hover and over is not None) else normal

            if img is not None:

                screen.blit(img, rect)

            else:

                color = (92, 92, 116) if hover else (60, 60, 76)

                pygame.draw.rect(screen, color, rect, border_radius=10)
                pygame.draw.rect(
                    screen, (200, 200, 212), rect, 2, border_radius=10
                )

                draw_text(
                    screen, self.BUTTON_LABELS[key], 26, (255, 255, 255),
                    center=rect.center
                )

            if key != "exit" and not game.has_match:

                veil = pygame.Surface(rect.size, pygame.SRCALPHA)
                veil.fill((0, 0, 0, 140))

                screen.blit(veil, rect)

        if not game.has_match:

            draw_text(
                screen, "Necesitas una luz encendida para pelear", 22,
                (255, 150, 130),
                center=(self.panel_rect.centerx, self.panel_rect.bottom - 14)
            )