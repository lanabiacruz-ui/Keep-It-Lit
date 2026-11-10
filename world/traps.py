import math
import random
from pathlib import Path

import pygame

from core.fonts import load_font
from core.accessibility import flash_level, flash_safe
from core.audio_manager import audio

BASE_DIR = Path(__file__).resolve().parent.parent
COMBAT_DIR = BASE_DIR / "assets" / "maps" / "combate"

TRAP_NAME = "Cepo Colmillo"
TRAP_COUNT = 4
TRAP_MAX = 8

TRAP_DARK = (24, 15, 15)
TRAP_MID = (96, 80, 80)
TRAP_LIGHT = (150, 130, 118)
TRAP_RED = (200, 70, 80)

HUD_GRAY = (146, 154, 163)
HUD_LINE = (76, 83, 91)
HUD_TRACK = (66, 74, 83)
HUD_FILL = (232, 146, 80)
HUD_FILL_LIGHT = (217, 179, 150)
TRAP_SIZE = (24, 16)
TRIGGER_SIZE = (14, 8)

PRESS_GAIN = 0.10
DECAY = 0.30

MIN_GAP = 70
MIN_PLAYER_DIST = 90
MIN_GATE_DIST = 80
ROOM_MARGIN = 36

HEAT_CELL = 32
HEAT_STEP = 0.15
HEAT_KEEP = 0.85
SAMPLE_TRIES = 1800
CANDIDATES = 260

ARMED = "armed"
HOLDING = "holding"
FREED = "freed"
USED = "used"

_fonts = {}


def _font(size):
    if size not in _fonts:
        _fonts[size] = load_font(size)
    return _fonts[size]


def _text(screen, text, size, color, **anchor):
    font = _font(size)
    shadow = font.render(text, True, (0, 0, 0))
    label = font.render(text, True, color)
    rect = label.get_rect(**anchor)
    screen.blit(shadow, rect.move(2, 2))
    screen.blit(label, rect)
    return rect


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    if length <= 0.0001:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length))
    return math.dist(p, (ax + dx * t, ay + dy * t))


class Trap:

    def __init__(self, center):
        self.center = center
        self.state = ARMED
        self.trigger = pygame.Rect(0, 0, *TRIGGER_SIZE)
        self.trigger.center = center
        self.body = pygame.Rect(0, 0, *TRAP_SIZE)
        self.body.center = center
        self.leave_zone = self.trigger.inflate(6, 6)
        self.phase = random.uniform(0, math.tau)


class ArenaTraps:

    def __init__(self, count=TRAP_COUNT):
        self.count = count
        self.traps = []
        self.holding = None
        self.progress = 0.0
        self.flash = 0.0
        self.recoil = 0.0
        self.time = 0.0
        self.heat = {}
        self.particles = []
        self._rec = 0.0
        self._hold_screen = None
        self._vig = None
        self._vig_size = None
        self._images = None
        self._scaled = {}

    def _load(self):
        if self._images is not None:
            return
        self._images = {}
        files = {
            ARMED: "trampa.png",
            HOLDING: "trampa_activa.png",
            USED: "trampa_usada.png",
        }
        for state, name in files.items():
            path = COMBAT_DIR / name
            try:
                self._images[state] = pygame.image.load(
                    str(path)
                ).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self._images[state] = self._placeholder(state)

    @staticmethod
    def _placeholder(state):
        surf = pygame.Surface((96, 64), pygame.SRCALPHA)
        color = {
            ARMED: (200, 70, 40),
            HOLDING: (230, 40, 40),
            USED: (90, 80, 76),
        }[state]
        pygame.draw.ellipse(surf, color, surf.get_rect().inflate(-8, -8))
        pygame.draw.ellipse(surf, (20, 17, 15), surf.get_rect().inflate(-8, -8), 4)
        return surf

    def _image(self, state, zoom):
        if state == FREED:
            state = HOLDING
        key = (state, zoom)
        img = self._scaled.get(key)
        if img is None:
            size = (int(TRAP_SIZE[0] * zoom), int(TRAP_SIZE[1] * zoom))
            img = pygame.transform.smoothscale(self._images[state], size)
            self._scaled[key] = img
        return img

    def _heat_at(self, x, y):
        cx, cy = int(x // HEAT_CELL), int(y // HEAT_CELL)
        total = 0.0
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                total += self.heat.get((cx + ox, cy + oy), 0.0)
        return total

    def _record(self, player, dt):
        self._rec += dt
        if self._rec < HEAT_STEP:
            return
        self._rec = 0.0
        cell = (
            int(player.rect.centerx // HEAT_CELL),
            int(player.rect.centery // HEAT_CELL),
        )
        self.heat[cell] = self.heat.get(cell, 0.0) + 1.0

    def _decay_heat(self):
        for key in list(self.heat):
            self.heat[key] *= HEAT_KEEP
            if self.heat[key] < 0.3:
                del self.heat[key]

    def reset(self, game, room, gate=None, count=None):
        self.clear(game)

        count = self.count if count is None else count
        self._decay_heat()

        cmap = game.collision_map
        player = game.player

        area = room.inflate(-ROOM_MARGIN * 2, -ROOM_MARGIN * 2)

        if area.width <= 0 or area.height <= 0:
            return

        probe = pygame.Rect(0, 0, TRAP_SIZE[0] + 10, TRAP_SIZE[1] + 10)

        start = player.rect.center
        room_c = room.center
        gate_c = gate.center if gate is not None else start
        ring_r = min(room.width, room.height) * 0.28
        heat_peak = max(self.heat.values()) if self.heat else 0.0

        gap = MIN_GAP if count <= 5 else MIN_GAP - 14

        candidates = []

        for _ in range(SAMPLE_TRIES):

            if len(candidates) >= CANDIDATES:
                break

            x = random.randint(area.left, area.right)
            y = random.randint(area.top, area.bottom)

            probe.center = (x, y)

            if not cmap.can_move(probe):
                continue

            if math.dist((x, y), start) < MIN_PLAYER_DIST:
                continue

            if gate is not None and math.dist((x, y), gate.center) < MIN_GATE_DIST:
                continue

            p = (x, y)

            path = max(
                math.exp(-_seg_dist(p, start, room_c) / 45.0),
                math.exp(-_seg_dist(p, gate_c, room_c) / 45.0) * 0.8,
            )

            ring = math.exp(-abs(math.dist(p, room_c) - ring_r) / 50.0)

            heat = 0.0
            if heat_peak > 0:
                heat = min(1.0, self._heat_at(x, y) / (heat_peak * 3.0))

            score = path + 0.7 * ring + 1.6 * heat + random.uniform(0, 0.35)

            candidates.append((score, p))

        candidates.sort(key=lambda item: item[0], reverse=True)

        placed = []

        for _, p in candidates:

            if len(placed) >= count:
                break

            if any(math.dist(p, c) < gap for c in placed):
                continue

            placed.append(p)

        self.traps = [Trap(c) for c in placed]

    def clear(self, game=None):
        was_holding = self.holding is not None

        self.traps = []
        self.holding = None
        self.progress = 0.0
        self.flash = 0.0
        self.recoil = 0.0
        self.particles = []

        if game is not None and was_holding:
            game.player.trapped = False

    def _burst(self, pos, count, colors, speed, life, up=0.0, size=(1.5, 3.2)):
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(speed * 0.4, speed)
            life_t = random.uniform(life * 0.6, life)
            self.particles.append([
                pos[0] + random.uniform(-5, 5),
                pos[1] + random.uniform(-3, 3),
                math.cos(ang) * spd,
                math.sin(ang) * spd * 0.6 - up,
                life_t,
                life_t,
                random.choice(colors),
                random.uniform(*size),
            ])

    def _update_particles(self, dt):
        alive = []
        for p in self.particles:
            p[4] -= dt
            if p[4] <= 0:
                continue
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= max(0.0, 1.0 - 2.2 * dt)
            p[3] *= max(0.0, 1.0 - 2.2 * dt)
            alive.append(p)
        self.particles = alive

    def update(self, game, dt, can_trigger=True):
        self._update_particles(dt)

        if not self.traps:
            return

        self.time += dt

        player = game.player

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt * 6.0)

        if self.recoil > 0:
            self.recoil = max(0.0, self.recoil - dt * 4.0)

        if self.holding is not None:

            trap = self.holding

            player.rect.center = trap.center
            player.image_rect.midbottom = (
                player.rect.centerx,
                player.rect.bottom + 3,
            )
            player.kb_vel = pygame.Vector2()
            player.trapped = True

            self.progress = max(0.0, self.progress - DECAY * dt)

            if random.random() < dt * 9.0:
                self._burst(
                    trap.center, 1, (TRAP_DARK, TRAP_MID),
                    22, 0.7, up=26, size=(1.2, 2.4),
                )

            return

        if can_trigger and not player.grabbed:
            self._record(player, dt)

        for trap in self.traps:

            if trap.state == FREED:

                if not player.rect.colliderect(trap.leave_zone):
                    trap.state = USED

            elif (
                trap.state == ARMED
                and can_trigger
                and not player.grabbed
                and player.rect.colliderect(trap.trigger)
            ):
                self._snap(game, trap)

                return

    def _snap(self, game, trap):
        trap.state = HOLDING

        self.holding = trap
        self.progress = 0.0
        self.flash = 1.0
        self.recoil = 0.0

        player = game.player

        player.trapped = True
        player.rect.center = trap.center
        player.image_rect.midbottom = (
            player.rect.centerx,
            player.rect.bottom + 3,
        )
        player.kb_vel = pygame.Vector2()

        self._burst(
            trap.center, 22,
            (TRAP_DARK, TRAP_MID, TRAP_LIGHT, TRAP_MID, TRAP_RED),
            70, 0.9, up=30,
        )

        fx = getattr(game, "fx", None)
        if fx is not None:
            fx.shake(2.5 if flash_safe() else 3.5, 0.28)

        audio.play("hit_heavy", 0.7)

        discover = getattr(game, "discover_enemy", None)

        if discover is not None:
            discover("trampa")

        game.show_message(
            f"¡Te atrapó un {TRAP_NAME}! Aprieta ESPACIO para soltarte"
        )

    def press_space(self, game):
        if self.holding is None:
            return False

        self.progress = min(1.0, self.progress + PRESS_GAIN)
        self.flash = flash_level()
        self.recoil = 1.0

        self._burst(
            self.holding.center, 3, ((255, 210, 110), (255, 160, 60)),
            55, 0.45, up=18, size=(1.2, 2.6),
        )

        if self.progress >= 1.0:

            trap = self.holding

            trap.state = FREED

            self._burst(
                trap.center, 34,
                ((255, 235, 170), (255, 200, 90), (255, 140, 50)),
                120, 0.9, up=10, size=(1.5, 3.6),
            )

            self.holding = None
            self.progress = 0.0

            game.player.trapped = False

            fx = getattr(game, "fx", None)
            if fx is not None:
                fx.shake(1.8, 0.18)

            audio.play("pickup", 0.6)

            game.show_message(f"¡Te soltaste del {TRAP_NAME}!")

        return True

    def _draw_tendrils(self, screen, camera, trap):
        zoom = camera.zoom
        cx, cy = trap.center

        pull = 1.0 - 0.75 * self.progress - 0.25 * self.recoil
        pull = max(0.15, pull)

        count = 8

        for i in range(count):

            ang = trap.phase + i * math.tau / count
            bx = cx + math.cos(ang) * 11
            by = cy + math.sin(ang) * 6 + 2

            height = (13 + 6 * math.sin(i * 1.7 + trap.phase)) * pull

            points = []

            for step in range(9):

                t = step / 8.0

                wob = math.sin(self.time * 3.2 + i * 1.3 + t * 4.5) * 2.6 * t

                x = bx + (cx - bx) * 0.45 * t + wob
                y = by - height * t

                points.append(camera.apply(pygame.Rect(int(x), int(y), 1, 1)).center)

            width = max(2, int(3 * zoom))

            pygame.draw.lines(screen, TRAP_LIGHT, False, points, width + 2)
            pygame.draw.lines(screen, TRAP_DARK, False, points, width)

    def draw_world(self, screen, camera):
        if not self.traps and not self.particles:
            return

        self._load()

        view = screen.get_rect().inflate(200, 200)

        for trap in self.traps:

            dest = camera.apply(trap.body)

            if not view.colliderect(dest):
                continue

            state = trap.state

            img = self._image(state, camera.zoom)

            if state == ARMED:

                k = 0.5 + 0.5 * math.sin(self.time * 3.0 + trap.center[0])

                glow = pygame.Surface(img.get_size(), pygame.SRCALPHA)

                pygame.draw.ellipse(
                    glow,
                    (255, 90, 40, int(18 + 34 * k)),
                    glow.get_rect().inflate(-4, -4),
                )

                screen.blit(glow, dest.topleft)

            if state == HOLDING and trap is self.holding:

                pool = pygame.Surface(
                    (int(dest.width * 1.7), int(dest.height * 1.9)),
                    pygame.SRCALPHA,
                )

                k = 0.5 + 0.5 * math.sin(self.time * 2.4)

                pygame.draw.ellipse(
                    pool, (20, 10, 10, int(150 + 50 * k)), pool.get_rect()
                )

                screen.blit(pool, pool.get_rect(center=dest.center))

                self._hold_screen = dest.center

            screen.blit(img, dest.topleft)

            if state == HOLDING and trap is self.holding:
                self._draw_tendrils(screen, camera, trap)

        for p in self.particles:

            rect = camera.apply(pygame.Rect(int(p[0]), int(p[1]), 1, 1))

            if not view.collidepoint(rect.center):
                continue

            k = p[4] / p[5]

            radius = max(1, int(p[7] * camera.zoom * (0.4 + 0.6 * k)))

            pygame.draw.circle(screen, p[6], rect.center, radius)

    def _vignette(self, size):
        if self._vig is not None and self._vig_size == size:
            return self._vig

        sw, sh = size

        small = pygame.Surface((160, 90), pygame.SRCALPHA)

        cx, cy = 80, 45
        maxd = math.hypot(80, 45)

        for y in range(90):
            for x in range(160):

                d = math.hypot(x - cx, y - cy) / maxd

                t = max(0.0, min(1.0, (d - 0.12) / 0.55))
                t = t * t * (3 - 2 * t)

                small.set_at((x, y), (14, 6, 6, int(235 * t)))

        self._vig = pygame.transform.smoothscale(small, (sw * 2, sh * 2))
        self._vig_size = size

        return self._vig

    def _draw_flame(self, screen, center, scale):
        pts = ((0, -12), (7, -2), (5, 8), (0, 12), (-5, 8), (-7, -2))

        outer = [(center[0] + x * scale, center[1] + y * scale) for x, y in pts]
        inner = [
            (center[0] + x * scale * 0.5, center[1] + y * scale * 0.55 + 2)
            for x, y in pts
        ]

        pygame.draw.polygon(screen, (230, 90, 30), outer)
        pygame.draw.polygon(screen, (255, 220, 110), inner)

    def draw_hud(self, screen):
        if self.holding is None:
            return

        sw, sh = screen.get_size()

        vig = self._vignette((sw, sh))

        strength = 0.35 + 0.65 * (1.0 - self.progress)

        strength *= 1.0 - 0.08 * flash_level() * (
            0.5 - 0.5 * math.sin(self.time * 2.2)
        )

        if flash_safe():
            strength = min(strength, 0.7)

        vig.set_alpha(int(255 * max(0.0, min(1.0, strength))))

        cx, cy = self._hold_screen or (sw // 2, sh // 2)

        screen.blit(vig, (cx - sw, cy - sh))

        width = min(460, int(sw * 0.5))
        height = 30

        bar = pygame.Rect(0, 0, width, height)
        bar.midbottom = (sw // 2, sh - 46)

        if self.progress < 0.3:
            sub = "¡Tu luz se está apagando! Aprieta ESPACIO"
        elif self.progress > 0.7:
            sub = "¡Casi te sueltas! Sigue apretando ESPACIO"
        else:
            sub = "Aprieta ESPACIO muchas veces para avivar tu luz"

        _text(
            screen,
            f"¡{TRAP_NAME.upper()}!",
            40,
            (232, 160, 140),
            midbottom=(bar.centerx, bar.top - 36),
        )

        _text(
            screen,
            sub,
            28,
            (255, 214, 120),
            midbottom=(bar.centerx, bar.top - 10),
        )

        shake = int(3 * self.flash)

        shown = bar.move(
            random.randint(-shake, shake) if shake else 0,
            0,
        )

        pygame.draw.rect(screen, HUD_LINE, shown.inflate(12, 12), border_radius=11)
        pygame.draw.rect(screen, HUD_GRAY, shown.inflate(8, 8), border_radius=10)
        pygame.draw.rect(screen, HUD_TRACK, shown, border_radius=8)

        fill = shown.copy()
        fill.width = max(0, int((shown.width - 6) * self.progress))
        fill.height = shown.height - 6
        fill.topleft = (shown.left + 3, shown.top + 3)

        if fill.width > 0:

            pygame.draw.rect(screen, HUD_FILL, fill, border_radius=6)

            shine = fill.copy()
            shine.height = max(2, fill.height // 3)

            pygame.draw.rect(screen, HUD_FILL_LIGHT, shine, border_radius=6)

        pygame.draw.rect(screen, HUD_LINE, shown, 2, border_radius=8)

        scale = 0.8 + 0.7 * self.progress

        scale *= 1.0 - 0.06 * flash_level() * (
            0.5 - 0.5 * math.sin(self.time * 11.0)
        )

        self._draw_flame(screen, (shown.left - 24, shown.centery), scale)