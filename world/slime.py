import math
import random
from pathlib import Path

import pygame

from core.achievements import achievements
from core.audio_manager import audio
from world.items import WorldItem, coin_id_for, split_coins
from world.zones import ZONES

COMBAT_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "combate"
)

DRAW_SIZE = 18
HITBOX = (14, 14)
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

CHECK_INTERVAL = 8.0
FIRST_CHECK = (3.0, 6.0)
MIN_SPAWN_DIST = 90
SPAWN_TRIES = 40

ZONE_CHANCE = {
    "central": 0.55,
    "cofres": 0.75,
}

MAX_PER_ZONE = 3

HUD_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
)

# Variantes. "art" = prefijo de los strips opcionales en assets/maps/combate
# (<art>_idle.png, <art>_anim.png, <art>_correr.png, <art>_golpe.png).
# Si no existen, se usa la imagen "sprite" de assets/maps/hud animada
# con squash/stretch a partir de las animaciones del slime base.
# flee_mult: multiplicador de velocidad al correr; chops/coins: drops.
VARIANTS = {
    "normal": dict(
        art=None, sprite=None, weight=55,
        hp=4, flee_mult=1.35, walk_mult=1.15, flee_time=4.0,
        chops=2, coins=10,
    ),
    "dorado": dict(
        art="slime2", sprite="slime2.png", weight=30,
        hp=4, flee_mult=1.7, walk_mult=1.3, flee_time=4.5,
        chops=3, coins=18,
    ),
    "brillante": dict(
        art="slime3", sprite="slime3.png", weight=15,
        hp=5, flee_mult=2.1, walk_mult=1.5, flee_time=5.0,
        chops=5, coins=30,
    ),
}

# Clave de cada variante en la enciclopedia.
CODEX_KEYS = {
    "normal": "slime",
    "dorado": "slime2",
    "brillante": "slime3",
}

# Distancia (en pixeles del mundo) a la que el jugador "ve" al slime.
DISCOVER_DISTANCE = 120

COIN_DROPS = 10
COIN_DELAY = 0.025
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


def _restyle(frames, base_ref, sprite):
    """Anima `sprite` (una sola imagen) copiando el squash/stretch de los
    frames del slime base. Cada frame se alinea por la base del cuerpo."""

    ref = base_ref.get_bounding_rect()
    crop_rect = sprite.get_bounding_rect()

    if ref.width <= 0 or ref.height <= 0 or crop_rect.width <= 0:
        return [sprite.copy() for _ in frames]

    crop = sprite.subsurface(crop_rect).copy()

    out = []

    for f in frames:

        box = f.get_bounding_rect()

        w = max(1, round(crop_rect.width * box.width / ref.width))
        h = max(1, round(crop_rect.height * box.height / ref.height))

        surf = pygame.Surface(f.get_size(), pygame.SRCALPHA)

        scaled = pygame.transform.scale(crop, (w, h))

        surf.blit(scaled, scaled.get_rect(midbottom=box.midbottom))

        out.append(surf)

    return out


class SlimeArt:

    def __init__(self, variant=None):

        cfg = VARIANTS.get(variant or "normal", VARIANTS["normal"])

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

        if cfg["art"]:
            self._apply_variant(cfg)

        self._zoom = None
        self._scaled = None

    def _apply_variant(self, cfg):

        name = cfg["art"]

        own_idle = _load_strip(COMBAT_DIR / f"{name}_idle.png")
        own_walk = _load_strip(COMBAT_DIR / f"{name}_anim.png")
        own_run = _load_strip(COMBAT_DIR / f"{name}_correr.png")
        own_hit = _load_image(COMBAT_DIR / f"{name}_golpe.png")

        sprite = _load_image(HUD_DIR / cfg["sprite"]) if cfg["sprite"] else None

        if sprite is not None:

            ref = self.idle[0]

            self.idle = own_idle or _restyle(self.idle, ref, sprite)
            self.walk = own_walk or _restyle(self.walk, ref, sprite)
            self.run = own_run or _restyle(self.run, ref, sprite)

        else:

            self.idle = own_idle or self.idle
            self.walk = own_walk or self.walk
            self.run = own_run or self.run

        if own_hit is not None:
            self.hit = own_hit

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

    def __init__(self, x, y, zone_id=None, variant="normal"):

        cfg = VARIANTS.get(variant, VARIANTS["normal"])

        self.variant = variant if variant in VARIANTS else "normal"
        self.cfg = cfg

        self.walk_speed = WALK_SPEED * cfg["walk_mult"]
        self.flee_speed = FLEE_SPEED * cfg["flee_mult"]
        self.flee_time = cfg["flee_time"]

        self.rect = pygame.Rect(0, 0, *HITBOX)
        self.rect.center = (round(x), round(y))

        self.pos = pygame.Vector2(x, y)

        self.zone = zone_id

        self.hp = cfg["hp"]
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
    def _flee_cycle(self):

        return FLEE_CYCLE / (1.0 + (self.cfg["flee_mult"] - 1.0) * 0.5)

    @property
    def fleeing(self):

        return self.mode == "flee"

    def take_damage(self, amount):

        self.hp -= amount
        self.flash = 0.15
        self.flee_t = self.flee_time

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

            speed = self.walk_speed / (WALK_AIR[1] - WALK_AIR[0])

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

        cycle = self._flee_cycle

        phase = self.anim_t / cycle

        if FLEE_AIR[0] <= phase < FLEE_AIR[1]:

            speed = self.flee_speed / (FLEE_AIR[1] - FLEE_AIR[0])

            step = self.flee_dir * speed * dt

            if not self._try_move(step.x, step.y, collision_map):

                self.side = -self.side
                self.hop_new = True

        if self.anim_t >= cycle:

            self.anim_t -= cycle

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
            sprite = _frame(frames["run"], self.anim_t, self._flee_cycle)

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

        self.arts = {name: SlimeArt(name) for name in VARIANTS}

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

    def _pick_variant(self):

        names = list(VARIANTS)
        weights = [VARIANTS[n]["weight"] for n in names]

        return random.choices(names, weights=weights, k=1)[0]

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
                self.slimes.append(
                    Slime(pos[0], pos[1], zone.id, self._pick_variant())
                )

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

        drops = []

        for n in range(slime.cfg["chops"]):

            chop = WorldItem("gelea", cx, cy)

            chop.start_fly(
                (cx, cy),
                self._scatter_target(game, cx, cy),
                delay=n * 0.05,
                height=20
            )

            drops.append(chop)

        # pocas monedas grandes (azules/rojas) en vez de muchas doradas
        for n, value in enumerate(split_coins(slime.cfg["coins"])):

            coin = WorldItem(coin_id_for(value), cx, cy)

            coin.value = value
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

                    achievements.add_counter("slimes")

                    if slime.variant == "brillante":
                        achievements.unlock("slime_brillante")

                    game.discover_enemy(
                        CODEX_KEYS.get(slime.variant, "slime")
                    )

                    self._drop(game, slime)

                continue

            slime.update(dt, center, game.collision_map)

            if (
                pygame.Vector2(center).distance_to(slime.pos)
                <= DISCOVER_DISTANCE
            ):
                game.discover_enemy(
                    CODEX_KEYS.get(slime.variant, "slime")
                )

        self.slimes = [
            s for s in self.slimes
            if not s.dead and not s.gone
        ]

    def draw(self, screen, camera):

        for slime in self.slimes:
            slime.draw(screen, camera, self.arts[slime.variant])