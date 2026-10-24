import math
import random
from pathlib import Path

import pygame

from core.audio_manager import audio
from world.items import WorldItem
from world.zones import ZONES

COMBAT_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "combate"
)

DRAW_SIZE = 15
HITBOX = (12, 12)
HP = 4

WALK_SPEED = 24
FLEE_SPEED = 86
FLEE_TIME = 3.0
FLEE_PROBE = 12
FLEE_OFFSETS = (0, 40, 80, 120, 160)

WALK_CYCLE = 0.75
FLEE_CYCLE = 0.45
IDLE_CYCLE = 1.8

WALK_AIR = (0.37, 0.75)
FLEE_AIR = (0.33, 0.83)

HOPS = (1, 3)
HOP_TURN = 70
REST_TIME = (0.9, 2.4)

LIFE_TIME = (120.0, 200.0)
KEEP_DISTANCE = 160

CHECK_INTERVAL = 18.0
FIRST_CHECK = (8.0, 14.0)
MIN_SPAWN_DIST = 90
SPAWN_TRIES = 40

ZONE_CHANCE = {
    "central": 0.18,
    "cofres": 0.34,
}

MAX_PER_ZONE = 1

COIN_DROPS = 10
COIN_DELAY = 0.04
SCATTER_MIN = 12
SCATTER_MAX = 44


def _load_image(path):

    try:
        return pygame.image.load(str(path)).convert_alpha()
    except (pygame.error, FileNotFoundError, OSError):
        return None


def _load_strip(path):

    sheet = _load_image(path)

    if sheet is None or sheet.get_height() <= 0:
        return []

    fw = sheet.get_height()

    return [
        sheet.subsurface((i * fw, 0, fw, fw)).copy()
        for i in range(max(1, sheet.get_width() // fw))
    ]


def _placeholder(step=0, scared=False):

    surf = pygame.Surface((64, 64), pygame.SRCALPHA)

    squash = (0, 5, 0, -5)[step % 4]

    width = 44 + squash
    height = 34 - squash

    body = pygame.Rect(0, 0, width, height)
    body.midbottom = (32, 56)

    dark = (40, 120, 60)
    mid = (90, 205, 110)
    light = (170, 240, 175)

    pygame.draw.ellipse(surf, mid, body)
    pygame.draw.ellipse(surf, dark, body, 3)

    shine = pygame.Rect(0, 0, 10, 6)
    shine.topleft = (body.x + 9, body.y + 6)

    pygame.draw.ellipse(surf, light, shine)

    eye = 5 if scared else 4

    for ex in (body.centerx - 8, body.centerx + 8):
        pygame.draw.circle(surf, (255, 255, 255), (ex, body.centery - 2), eye + 2)
        pygame.draw.circle(surf, (20, 40, 25), (ex, body.centery - 2), eye)

    if scared:
        pygame.draw.ellipse(
            surf,
            (20, 40, 25),
            (body.centerx - 4, body.centery + 7, 8, 7)
        )
    else:
        pygame.draw.arc(
            surf,
            (20, 40, 25),
            (body.centerx - 6, body.centery + 2, 12, 8),
            math.pi,
            math.tau,
            2
        )

    return surf


_shadow_cache = {}


def _shadow(size):

    if size not in _shadow_cache:

        surf = pygame.Surface(size, pygame.SRCALPHA)

        pygame.draw.ellipse(surf, (0, 0, 0, 90), surf.get_rect())

        _shadow_cache[size] = surf

    return _shadow_cache[size]


class SlimeArt:

    def __init__(self):

        single = (
            _load_strip(COMBAT_DIR / "slime_idle.png")
            or _load_strip(COMBAT_DIR / "slime.png")
        )
        walk = _load_strip(COMBAT_DIR / "slime_anim.png")
        run = _load_strip(COMBAT_DIR / "slime_correr.png")
        hit = _load_image(COMBAT_DIR / "slime_golpe.png")

        self.idle = single or [_placeholder(0)]

        self.walk = walk or [_placeholder(n) for n in range(4)]

        self.run = run or [_placeholder(n, True) for n in range(4)]

        if hit is None:

            hit = self.idle[0].copy()
            hit.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.hit = hit

        self._zoom = None
        self._scaled = None

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(1, int(DRAW_SIZE * zoom))

            def scale(frames):
                return [pygame.transform.scale(f, (px, px)) for f in frames]

            self._scaled = {
                "idle": scale(self.idle),
                "walk": scale(self.walk),
                "run": scale(self.run),
                "hit": scale([self.hit])[0],
            }

            self._zoom = zoom

        return self._scaled


def _frame(frames, t, cycle):

    n = len(frames)

    index = int((t % cycle) / cycle * n)

    return frames[min(index, n - 1)]


class Slime:

    def __init__(self, x, y, zone_id=None):

        self.rect = pygame.Rect(0, 0, *HITBOX)
        self.rect.center = (round(x), round(y))

        self.pos = pygame.Vector2(x, y)

        self.zone = zone_id

        self.hp = HP
        self.flash = 0.0

        self.mode = "rest"
        self.anim_t = random.uniform(0.0, IDLE_CYCLE)
        self.phase_t = random.uniform(*REST_TIME)

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.hops_left = 0
        self.hop_new = False

        self.flee_t = 0.0
        self.flee_dir = pygame.Vector2(1, 0)
        self.side = random.choice((1, -1))

        self.age = 0.0
        self.life = random.uniform(*LIFE_TIME)

        self.gone = False
        self.dropped = False

    @property
    def dead(self):

        return self.hp <= 0

    @property
    def fleeing(self):

        return self.mode == "flee"

    def take_damage(self, amount):

        self.hp -= amount
        self.flash = 0.15
        self.flee_t = FLEE_TIME

    def _try_move(self, dx, dy, collision_map):

        moved = False

        if dx:

            probe = self.rect.copy()
            probe.centerx = round(self.pos.x + dx)

            if collision_map.can_move(probe):
                self.pos.x += dx
                self.rect = probe
                moved = True

        if dy:

            probe = self.rect.copy()
            probe.centery = round(self.pos.y + dy)

            if collision_map.can_move(probe):
                self.pos.y += dy
                self.rect = probe
                moved = True

        return moved

    def _pick_flee(self, away, collision_map):

        for offset in FLEE_OFFSETS:

            for sign in (self.side, -self.side):

                direction = away.rotate(offset * sign)

                probe = self.rect.copy()
                probe.center = (
                    round(self.pos.x + direction.x * FLEE_PROBE),
                    round(self.pos.y + direction.y * FLEE_PROBE),
                )

                if collision_map.can_move(probe):
                    return direction

                if offset == 0:
                    break

        return away

    def _to_rest(self):

        self.mode = "rest"
        self.anim_t = 0.0
        self.phase_t = random.uniform(*REST_TIME)

    def _to_walk(self):

        self.mode = "walk"
        self.anim_t = 0.0
        self.hops_left = random.randint(*HOPS)
        self.hop_new = True
        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

    def _to_flee(self):

        self.mode = "flee"
        self.anim_t = 0.0
        self.hop_new = True

    def _update_rest(self, dt):

        self.anim_t += dt
        self.phase_t -= dt

        if self.phase_t <= 0:
            self._to_walk()

    def _update_walk(self, dt, collision_map):

        self.anim_t += dt

        if self.hop_new:

            self.hop_new = False

            self.heading = self.heading.rotate(
                random.uniform(-HOP_TURN, HOP_TURN)
            )

        phase = self.anim_t / WALK_CYCLE

        if WALK_AIR[0] <= phase < WALK_AIR[1]:

            speed = WALK_SPEED / (WALK_AIR[1] - WALK_AIR[0])

            step = self.heading * speed * dt

            if not self._try_move(step.x, step.y, collision_map):

                self.heading = self.heading.rotate(
                    random.uniform(120, 240)
                )

        if self.anim_t >= WALK_CYCLE:

            self.anim_t -= WALK_CYCLE
            self.hops_left -= 1

            if self.hops_left <= 0:
                self._to_rest()
            else:
                self.hop_new = True

    def _update_flee(self, dt, player_center, collision_map):

        self.anim_t += dt

        if self.hop_new:

            self.hop_new = False

            away = self.pos - pygame.Vector2(player_center)

            if away.length_squared() < 0.01:
                away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            else:
                away = away.normalize()

            self.flee_dir = self._pick_flee(away, collision_map)

        phase = self.anim_t / FLEE_CYCLE

        if FLEE_AIR[0] <= phase < FLEE_AIR[1]:

            speed = FLEE_SPEED / (FLEE_AIR[1] - FLEE_AIR[0])

            step = self.flee_dir * speed * dt

            if not self._try_move(step.x, step.y, collision_map):

                self.side = -self.side
                self.hop_new = True

        if self.anim_t >= FLEE_CYCLE:

            self.anim_t -= FLEE_CYCLE

            if self.flee_t <= 0:
                self._to_rest()
            else:
                self.hop_new = True

    def update(self, dt, player_center, collision_map):

        self.age += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.age >= self.life and self.mode == "rest":

            far = (
                pygame.Vector2(player_center).distance_to(self.pos)
                > KEEP_DISTANCE
            )

            if far:
                self.gone = True
                return

        if self.flee_t > 0:

            self.flee_t = max(0.0, self.flee_t - dt)

            if self.mode != "flee":
                self._to_flee()

        if self.mode == "flee":
            self._update_flee(dt, player_center, collision_map)

        elif self.mode == "walk":
            self._update_walk(dt, collision_map)

        else:
            self._update_rest(dt)

    def draw(self, screen, camera, art):

        frames = art.get(camera.zoom)

        if self.flash > 0:
            sprite = frames["hit"]

        elif self.mode == "flee":
            sprite = _frame(frames["run"], self.anim_t, FLEE_CYCLE)

        elif self.mode == "walk":
            sprite = _frame(frames["walk"], self.anim_t, WALK_CYCLE)

        else:
            sprite = _frame(frames["idle"], self.anim_t, IDLE_CYCLE)

        dest = camera.apply(self.rect)

        shadow = _shadow(
            (max(2, int(dest.width * 1.3)), max(2, int(dest.height * 0.5)))
        )

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            sprite,
            sprite.get_rect(
                midbottom=(
                    dest.centerx,
                    dest.bottom + int(3 * camera.zoom)
                )
            )
        )


class SlimeManager:

    def __init__(self):

        self.slimes = []

        self.art = SlimeArt()

        self.zones = [z for z in ZONES if z.id in ZONE_CHANCE]

        self.check_t = random.uniform(*FIRST_CHECK)

    def targets(self):

        return [s for s in self.slimes if not s.dead]

    def clear(self):

        self.slimes = []

    def _spawn_point(self, game, zone_rect, px, py):

        area = zone_rect.inflate(-24, -24)

        if area.width <= 0 or area.height <= 0:
            return None

        for _ in range(SPAWN_TRIES):

            x = random.randint(area.left, area.right)
            y = random.randint(area.top, area.bottom)

            if math.hypot(x - px, y - py) < MIN_SPAWN_DIST:
                continue

            probe = pygame.Rect(0, 0, *HITBOX)
            probe.center = (x, y)

            if game.collision_map.can_move(probe):
                return (x, y)

        return None

    def _try_spawn(self, game):

        px, py = game.player.rect.center

        for zone in self.zones:

            alive = sum(1 for s in self.slimes if s.zone == zone.id)

            if alive >= MAX_PER_ZONE:
                continue

            if random.random() > ZONE_CHANCE[zone.id]:
                continue

            pos = self._spawn_point(game, zone.rect, px, py)

            if pos is not None:
                self.slimes.append(Slime(pos[0], pos[1], zone.id))

    def _scatter_target(self, game, cx, cy):

        for _ in range(30):

            angle = random.uniform(0, math.tau)
            dist = random.uniform(SCATTER_MIN, SCATTER_MAX)

            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist

            if game.collision_map.point_is_walkable(x, y):
                return (x, y)

        return (cx, cy + SCATTER_MIN)

    def _drop(self, game, slime):

        cx, cy = slime.rect.center

        chop = WorldItem("chuleta", cx, cy)

        chop.start_fly(
            (cx, cy),
            self._scatter_target(game, cx, cy),
            height=20
        )

        drops = [chop]

        for n in range(COIN_DROPS):

            coin = WorldItem("moneda", cx, cy)

            coin.value = 1
            coin.sparkle = True

            coin.start_fly(
                (cx, cy),
                self._scatter_target(game, cx, cy),
                delay=0.12 + n * COIN_DELAY,
                height=18
            )

            drops.append(coin)

        game.world_items.extend(drops)

        audio.play("enemy_die")

    def update(self, dt, game):

        if getattr(game, "current_map", "mapa1") != "mapa1":

            self.slimes = []

            return

        center = game.player.rect.center

        self.check_t -= dt

        if self.check_t <= 0:

            self.check_t = CHECK_INTERVAL

            self._try_spawn(game)

        for slime in self.slimes:

            if slime.dead:

                if not slime.dropped:

                    slime.dropped = True

                    self._drop(game, slime)

                continue

            slime.update(dt, center, game.collision_map)

        self.slimes = [
            s for s in self.slimes
            if not s.dead and not s.gone
        ]

    def draw(self, screen, camera):

        for slime in self.slimes:
            slime.draw(screen, camera, self.art)