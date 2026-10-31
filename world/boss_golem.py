"""Jefe de la Zona 2: Golem Colosal.

No importa nada de arena.py (para no hacer imports circulares).

Sprites propios (carpeta assets/maps/combate/), PNG con fondo transparente.
Todos son opcionales: si falta alguno se dibuja un reemplazo con codigo.

    jefe_golem.png            cuerpo, 192x192 (o jefe_golem_anim.png: tira
                              horizontal de cuadros de 192x192)
    jefe_golem_fase2.png      cuerpo con grietas verdes, 192x192
    jefe_golem_caminar.png    tira de caminata (fase 1): cuadros de 192x192,
                              se usa solo mientras persigue
    jefe_golem_fase2_caminar.png  lo mismo para la fase 2
    jefe_golem_golpe.png      cuerpo cuando recibe un golpe, 192x192
    jefe_golem_embestida.png  agachado, listo para embestir, 192x192
    jefe_golem_puno.png       brazos arriba (puno al suelo y rocas), 192x192
    jefe_golem_rayo.png       la gema cargando el rayo, 192x192
    jefe_golem_barrido.png    brazos extendidos de lado a lado, 448x448
                              (el cuerpo va en el centro, 192x192)
    jefe_golem_escudo.png     caparazon de roca, 256x256
    roca_jefe.png             roca que cae, 64x64

El tamano en el juego sale del tamano de TU imagen (zoom x4 del juego).

Patron (fase 1):  perseguir -> embestida -> rocas -> perseguir -> onda
                  -> embestida -> escudo + refuerzos
Patron (fase 2):  todo mas rapido, y suma el rayo y el barrido de brazos.

Que se esquiva con salto: las ondas y el barrido de brazos (van al ras del
piso). Las rocas, el rayo y la embestida NO se esquivan saltando.
"""

import math
import random

import pygame


BOSS_NAME = "GOLEM COLOSAL"
BOSS_TAG = "JEFE DE LA ZONA 2"
BOSS_SUB = "Salta sus ondas, esquiva las rocas y pegale cuando se aturda"
VICTORY_TITLE = "GOLEM COLOSAL DERROTADO"
VICTORY_SUB = "LA GEMA VERDE ES TUYA"
SUMMON_MESSAGE = "El golem invoca refuerzos!"
MINIONS_GONE_MESSAGE = "Los refuerzos del golem se fueron!"

BOSS_HP = 480.0

REF_ZOOM = 4

DEFAULT_BASE = 48.0

PHASE2_SPEED = 1.3

ANIM_FRAME = 0.18

WALK_FRAME = 0.12

INTRO_TIME = 1.8
PHASE_TIME = 2.4
DYING_TIME = 4.6
CRACK_EVERY = 0.75
FLASH_TIME = 0.10

CYCLE_1 = ("chase", "charge", "rocks", "chase", "slam", "charge", "shield")
CYCLE_2 = (
    "chase", "charge", "slam", "beam", "rocks", "sweep", "charge", "slam",
    "shield",
)

# --- perseguir
CHASE_SPEED = 36.0
CHASE_TIME = (3.2, 2.2)

# --- embestida
CHARGE_AIM = 1.2
CHARGE_LOCK = 0.5        # los ultimos segundos de la mira ya no sigue
CHARGE_SPEED = 330.0
CHARGE_RAMP = 0.45
CHARGE_MAX = 2.0
STUN_TIME = 2.6

# --- onda (se salta)
SLAM_WIND = 1.0
WAVE_SPEED = 190.0
WAVE_HALF = 7.0
WAVE_GAP = 1.0
SLAM_REST = 1.0
WAVE_MAX_R = 700.0

# --- rocas
ROCK_WIND = 0.8
ROCK_RADIUS = 17.0
ROCK_WARN = (1.5, 1.05)
ROCK_BATCHES = (3, 4)
ROCK_PER_BATCH = (3, 4)
ROCK_GAP = 0.85
ROCK_AFTER = 1.3
ROCK_IMPACT = 0.18
ROCK_CRATER = 0.6

# --- rayo (fase 2)
BEAM_AIM = 1.5
BEAM_LOCK = 0.6
BEAM_TIME = 0.55
BEAM_REST = 0.5
BEAM_LEN = 700.0
BEAM_HALF = 6.0

# --- barrido de brazos (fase 2, se salta)
SWEEP_WIND = 0.8
SWEEP_TIME = 2.8
SWEEP_REACH = 54.0
SWEEP_HALF = 7.0
SWEEP_RATE = 250.0
SWEEP_MOVE = 24.0
SWEEP_REST = 1.2

# --- escudo + refuerzos
SHIELD_WIND = 1.0
SHIELD_MIN = 2.2
SHIELD_MAX = 18.0

# --- danos (misma escala que el resto del juego)
BODY_DAMAGE = 0.20
CHARGE_DAMAGE = 0.35
WAVE_DAMAGE = 0.30
ROCK_DAMAGE = 0.30
BEAM_DAMAGE = 0.35
SWEEP_DAMAGE = 0.30

CONTACT_PUSH = 300.0

BAR_NAME_TOP = 104

GREEN = (70, 235, 130)
GREEN_DARK = (20, 120, 70)
STONE = (128, 134, 140)
STONE_DARK = (70, 74, 82)


def _ease(k):

    k = max(0.0, min(1.0, k))

    return k * k * (3.0 - 2.0 * k)


def _lerp(a, b, k):

    return a + (b - a) * k


def _quant(radius):

    return max(8, int(round(radius / 8.0)) * 8)


def _seg_dist(p, a, b):
    """Distancia del punto p al segmento a-b."""

    ab = b - a
    n = ab.length_squared()

    if n < 0.0001:
        return (p - a).length()

    k = max(0.0, min(1.0, (p - a).dot(ab) / n))

    return (p - (a + ab * k)).length()


# ------------------------------------------------------------------- sprites


def _placeholder_body(cracked=False):
    """Reemplazo provisorio (192x192) hasta que esten tus dibujos."""

    s = 192
    surf = pygame.Surface((s, s), pygame.SRCALPHA)

    # piernas
    pygame.draw.rect(surf, STONE_DARK, (56, 128, 34, 52), border_radius=8)
    pygame.draw.rect(surf, STONE_DARK, (102, 128, 34, 52), border_radius=8)

    # brazos
    pygame.draw.rect(surf, STONE, (14, 60, 36, 80), border_radius=12)
    pygame.draw.rect(surf, STONE, (142, 60, 36, 80), border_radius=12)
    pygame.draw.rect(surf, STONE_DARK, (10, 124, 44, 30), border_radius=10)
    pygame.draw.rect(surf, STONE_DARK, (138, 124, 44, 30), border_radius=10)

    # torso
    pygame.draw.rect(surf, STONE, (40, 50, 112, 90), border_radius=14)
    pygame.draw.rect(surf, STONE_DARK, (40, 50, 112, 90), 4, border_radius=14)

    # cabeza
    pygame.draw.rect(surf, STONE, (68, 14, 56, 44), border_radius=10)
    pygame.draw.rect(surf, STONE_DARK, (68, 14, 56, 44), 4, border_radius=10)

    eye = (255, 90, 60) if cracked else (255, 200, 80)

    pygame.draw.rect(surf, eye, (78, 30, 12, 8))
    pygame.draw.rect(surf, eye, (102, 30, 12, 8))

    # gema verde oscuro en el pecho
    pygame.draw.polygon(
        surf, GREEN_DARK, [(96, 70), (116, 92), (96, 118), (76, 92)]
    )
    pygame.draw.polygon(
        surf, GREEN, [(96, 70), (116, 92), (96, 118), (76, 92)], 3
    )
    pygame.draw.polygon(
        surf, (180, 255, 210), [(96, 78), (104, 90), (96, 98), (90, 90)]
    )

    if cracked:

        for pts in (
            [(48, 60), (62, 84), (54, 108), (70, 130)],
            [(146, 58), (132, 80), (142, 104), (126, 126)],
            [(84, 50), (92, 62), (86, 74)],
            [(22, 70), (30, 96), (24, 118)],
            [(170, 72), (162, 98), (168, 120)],
        ):
            pygame.draw.lines(surf, GREEN, False, pts, 3)

    return surf


def _placeholder_arms_up():

    surf = _placeholder_body()

    pygame.draw.rect(surf, (0, 0, 0, 0), (6, 56, 50, 110))
    pygame.draw.rect(surf, (0, 0, 0, 0), (136, 56, 50, 110))

    pygame.draw.rect(surf, STONE, (14, 6, 34, 78), border_radius=12)
    pygame.draw.rect(surf, STONE, (144, 6, 34, 78), border_radius=12)
    pygame.draw.rect(surf, STONE_DARK, (8, 0, 44, 28), border_radius=10)
    pygame.draw.rect(surf, STONE_DARK, (140, 0, 44, 28), border_radius=10)

    return surf


def _placeholder_sweep():
    """448x448: cuerpo al centro y los dos brazos hasta los bordes."""

    s = 448
    surf = pygame.Surface((s, s), pygame.SRCALPHA)

    mid = s // 2

    pygame.draw.rect(surf, STONE, (8, mid - 24, s - 16, 48), border_radius=18)
    pygame.draw.rect(
        surf, STONE_DARK, (8, mid - 24, s - 16, 48), 4, border_radius=18
    )
    pygame.draw.rect(surf, STONE_DARK, (4, mid - 34, 56, 68), border_radius=14)
    pygame.draw.rect(
        surf, STONE_DARK, (s - 60, mid - 34, 56, 68), border_radius=14
    )

    body = _placeholder_body(True)

    surf.blit(body, body.get_rect(center=(mid, mid)))

    return surf


def _placeholder_shield():

    s = 256
    surf = pygame.Surface((s, s), pygame.SRCALPHA)

    c = s // 2

    for i in range(10):

        a = math.tau * i / 10.0

        x = c + math.cos(a) * 100
        y = c + math.sin(a) * 100

        pts = []

        for j in range(5):

            b = math.tau * j / 5.0 + a

            r = random.Random(i * 7 + j).uniform(14, 26)

            pts.append((x + math.cos(b) * r, y + math.sin(b) * r))

        pygame.draw.polygon(surf, STONE, pts)
        pygame.draw.polygon(surf, STONE_DARK, pts, 3)

    pygame.draw.circle(surf, (*GREEN, 90), (c, c), 112, 3)

    return surf


def _placeholder_rock():

    s = 64
    surf = pygame.Surface((s, s), pygame.SRCALPHA)

    pts = [(10, 40), (18, 16), (40, 8), (56, 28), (48, 54), (22, 58)]

    pygame.draw.polygon(surf, STONE, pts)
    pygame.draw.polygon(surf, STONE_DARK, pts, 3)
    pygame.draw.line(surf, GREEN, (24, 22), (38, 44), 2)

    return surf


def _tint(frame):

    img = frame.copy()
    img.fill((190, 255, 205, 255), special_flags=pygame.BLEND_RGBA_MULT)

    return img


def _flash(frame):

    img = frame.copy()
    img.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

    return img


class GolemBossArt:
    """Carga los sprites del jefe (ver docstring del archivo)."""

    def __init__(self, folder, load_image, load_strip):

        body = (
            load_strip(folder / "jefe_golem_anim.png")
            or load_strip(folder / "jefe_golem.png")
        )

        self.custom = bool(body)

        if not body:
            body = [_placeholder_body()]

        body2 = (
            load_strip(folder / "jefe_golem_fase2_anim.png")
            or load_strip(folder / "jefe_golem_fase2.png")
        )

        if not body2:

            body2 = (
                [_tint(f) for f in body] if self.custom
                else [_placeholder_body(True)]
            )

        walk = load_strip(folder / "jefe_golem_caminar.png")

        walk2 = load_strip(folder / "jefe_golem_fase2_caminar.png")

        if walk and not walk2:
            walk2 = [_tint(f) for f in walk]

        # sin tira de caminata: sigue usando la animacion normal
        self.walk = (walk or None, walk2 or None)

        hit = load_image(folder / "jefe_golem_golpe.png")

        self.body = (body, body2)

        self.hit = (
            (hit, hit) if hit is not None
            else (_flash(body[0]), _flash(body2[0]))
        )

        self.poses = {}

        for pose, name, fallback in (
            ("charge", "jefe_golem_embestida.png", None),
            ("slam", "jefe_golem_puno.png", _placeholder_arms_up),
            ("beam", "jefe_golem_rayo.png", None),
        ):

            img = load_image(folder / name)

            if img is None:

                if fallback is not None and not self.custom:
                    img = fallback()
                else:
                    img = None

            if img is None:
                self.poses[pose] = None
            else:
                self.poses[pose] = (img, _tint(img))

        sweep = load_image(folder / "jefe_golem_barrido.png")

        if sweep is None:
            sweep = _placeholder_sweep()

        self.sweep = (sweep, _tint(sweep))

        shield = load_image(folder / "jefe_golem_escudo.png")

        self.shield = shield if shield is not None else _placeholder_shield()

        rock = load_image(folder / "roca_jefe.png")

        self.rock = rock if rock is not None else _placeholder_rock()

        self.base_size = body[0].get_width() / float(REF_ZOOM)
        self.sweep_size = self.sweep[0].get_width() / float(REF_ZOOM)


# ------------------------------------------------------------------------ jefe


class GolemBoss:

    is_boss = True
    always_draw = True
    uses_jump = True
    fixed = False
    contact_damage = False
    precise_hit = True
    attached = False
    codex_key = None
    touch_cd = 0.0
    stun = 0.0

    boss_name = BOSS_NAME
    title = (BOSS_NAME, "GUARDIAN DE LA GEMA VERDE")
    tag = BOSS_TAG
    sub = BOSS_SUB
    victory_title = (VICTORY_TITLE, VICTORY_SUB)
    summon_message = SUMMON_MESSAGE
    minions_gone_message = MINIONS_GONE_MESSAGE
    contact_push = CONTACT_PUSH

    def __init__(self, x, y, room, art, hp=BOSS_HP, intro_time=INTRO_TIME,
                 hold_time=0.0):

        self.room = room
        self.art = art

        self.base = float(art.base_size) if art.base_size > 4 else DEFAULT_BASE

        self.pos = pygame.Vector2(x, y)
        self.center = pygame.Vector2(room.center)
        self.vel = pygame.Vector2()

        self.size = self.base * 0.35

        self.rect = pygame.Rect(0, 0, 8, 8)

        self.max_hp = float(hp)
        self._hp = float(hp)
        self.shown_hp = float(hp)

        self.phase = 1
        self.pending_phase = False

        self.flash = 0.0
        self.shake = 0.0
        self.anim_t = 0.0

        self.intro_time = float(intro_time)
        self.spawn_t = self.intro_time

        self.hold_after = float(hold_time)
        self.hold_t = 0.0

        self._crack_t = 0.0

        self.state = "intro"
        self.step = -1
        self.t = 0.0

        self.minions = 0
        self.summon_request = False
        self.events = []
        self.event_pos = pygame.Vector2(self.pos)

        self.dying = False
        self.dying_t = 0.0
        self.cleanup_done = False
        self.fx_cd = 0.0

        self.ring_t = 99.0

        # ataques
        self.dir = pygame.Vector2(1, 0)
        self.charge_speed = 0.0
        self.stun_len = STUN_TIME
        self.sweep_angle = 0.0
        self.waves_left = 0
        self.wave_cd = 0.0
        self.rest_t = 0.0
        self.batches_left = 0
        self.batch_cd = 0.0
        self.beam_on = False
        self.beam_t = 0.0
        self.beam_hit = False
        self.shielded = False
        self.summoned = False

        self.waves = []
        self.rocks = []

        self.last_target = pygame.Vector2(self.pos)

        self._cache = {}
        self._shadow = {}
        self._glow = {}

        self._sync_rect()

    # ------------------------------------------------------------------ vida

    @property
    def hp(self):

        return self._hp

    @hp.setter
    def hp(self, value):

        if value < self._hp:

            if self.invulnerable:
                return

            half = self.max_hp * 0.5

            # no se puede saltear la fase 2 de un solo golpe
            if self.phase == 1 and value <= half:
                value = half
                self.pending_phase = True

        self._hp = min(value, self.max_hp)

    @property
    def spawning(self):

        return self.spawn_t > 0

    @property
    def invulnerable(self):

        return (
            self.spawning or self.dying or self.hold_t > 0
            or self.shielded or self.state == "phase"
        )

    @property
    def dying_k(self):

        return 1.0 - max(0.0, self.dying_t) / DYING_TIME

    @property
    def dead(self):

        return self.dying and self.dying_t <= 0

    def take_damage(self, amount):

        if self.invulnerable or self.dead:
            return 0

        self.hp -= amount
        self.flash = FLASH_TIME

        return amount

    def hit_targets(self):

        if self.spawning or self.dying or self.hold_t > 0:
            return []

        return [self]

    # ----------------------------------------------------------------- dano

    def _arm_segments(self):

        out = []

        a = math.radians(self.sweep_angle)

        d = pygame.Vector2(math.cos(a), math.sin(a))

        out.append((self.pos, self.pos + d * SWEEP_REACH))
        out.append((self.pos, self.pos - d * SWEEP_REACH))

        return out

    def contact_hit(self, body, airborne=False):
        """(dano, punto de origen) si algo del jefe toca al jugador.

        airborne: el jugador esta en el aire (esquiva ondas y barrido).
        """

        if self.spawning or self.dying or self.hold_t > 0:
            return None

        feet = pygame.Vector2(body.midbottom)
        center = pygame.Vector2(body.center)

        # rocas (no se esquivan saltando)
        for rock in self.rocks:

            if rock["state"] != "impact" or rock["hit"]:
                continue

            if center.distance_to(rock["pos"]) < ROCK_RADIUS + 5:

                rock["hit"] = True

                return ROCK_DAMAGE, rock["pos"]

        # rayo (no se esquiva saltando)
        if self.beam_on and not self.beam_hit:

            end = self.pos + self.dir * BEAM_LEN

            if _seg_dist(center, self.pos, end) < BEAM_HALF + 5:

                self.beam_hit = True

                return BEAM_DAMAGE, self.pos

        if not airborne:

            # barrido de brazos (al ras del piso)
            if self.state == "sweep" and self.t >= SWEEP_WIND:

                for a, b in self._arm_segments():

                    if _seg_dist(feet, a, b) < SWEEP_HALF + 5:
                        return SWEEP_DAMAGE, self.pos

            # ondas (al ras del piso)
            for wave in self.waves:

                if wave["hit"]:
                    continue

                d = feet.distance_to(wave["origin"])

                if abs(d - wave["r"]) < WAVE_HALF + 5:

                    wave["hit"] = True

                    return WAVE_DAMAGE, wave["origin"]

        # cuerpo
        if self.state in ("stun", "phase"):
            return None

        radius = self.size * 0.5 * 0.85

        nx = max(body.left, min(self.pos.x, body.right))
        ny = max(body.top, min(self.pos.y, body.bottom))

        if math.hypot(nx - self.pos.x, ny - self.pos.y) < radius:

            if self.state == "charge_run":
                return CHARGE_DAMAGE, self.pos

            return BODY_DAMAGE, self.pos

        return None

    # ----------------------------------------------------------------- luces

    def lights(self):

        out = []

        if self.dead:
            return out

        out.append((self.pos.x, self.pos.y, _quant(self.size * 0.9 + 32)))

        # lo que avisa tiene que verse aunque la sala este a oscuras
        for rock in self.rocks:

            if rock["state"] != "done":
                out.append((rock["pos"].x, rock["pos"].y, 32))

        for wave in self.waves:

            r = wave["r"]

            n = max(8, min(16, int(r / 14)))

            for i in range(n):

                a = math.tau * i / n

                out.append((
                    wave["origin"].x + math.cos(a) * r,
                    wave["origin"].y + math.sin(a) * r,
                    24
                ))

        if self.state == "charge_aim" or (
            self.beam_on or self.state == "beam"
        ):

            length = (
                BEAM_LEN if self.state == "beam" else self._ray_length()
            )

            for i in range(1, 13):

                p = self.pos + self.dir * (length * i / 12.0)

                out.append((p.x, p.y, 24))

        if self.state == "sweep" and self.t >= SWEEP_WIND:

            for a, b in self._arm_segments():

                for i in range(1, 4):

                    p = a + (b - a) * (i / 3.0)

                    out.append((p.x, p.y, 24))

        return out

    # ---------------------------------------------------------------- estados

    def _emit(self, name, pos=None):

        self.events.append(name)

        if pos is not None:
            self.event_pos = pygame.Vector2(pos)

    def _cycle(self):

        return CYCLE_1 if self.phase == 1 else CYCLE_2

    def _next(self):

        self._go(self.step + 1)

    def _go(self, step):

        cycle = self._cycle()

        self.step = step % len(cycle)

        self._enter(cycle[self.step])

    def _enter(self, name):

        self.t = 0.0
        self.vel.update(0, 0)
        self.shake = 0.0
        self.sweep_angle = 0.0

        if name == "charge":

            self.state = "charge_aim"

        elif name == "slam":

            self.state = "slam"
            self.waves_left = (
                random.choice((1, 2)) if self.phase == 1
                else random.choice((2, 3))
            )
            self.wave_cd = 0.0
            self.rest_t = 0.0

        elif name == "rocks":

            self.state = "rocks"
            self.batches_left = ROCK_BATCHES[self.phase - 1]
            self.batch_cd = 0.0
            self.rest_t = 0.0

        elif name == "beam":

            self.state = "beam"
            self.beam_on = False
            self.beam_hit = False
            self.beam_t = 0.0

        elif name == "sweep":

            self.state = "sweep"

        elif name == "shield":

            self.state = "shield"
            self.summoned = False

        else:

            self.state = name

    def _sync_rect(self):

        side = max(2, int(round(self.size)))

        self.rect.size = (side, side)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def _half(self):

        return min(
            self.size / 2, self.room.width / 2 - 1, self.room.height / 2 - 1
        )

    def _clamp(self):
        """Lo deja dentro de la sala. True si toco alguna pared."""

        half = self._half()

        touched = False

        if self.pos.x < self.room.left + half:
            self.pos.x = self.room.left + half
            touched = True
        elif self.pos.x > self.room.right - half:
            self.pos.x = self.room.right - half
            touched = True

        if self.pos.y < self.room.top + half:
            self.pos.y = self.room.top + half
            touched = True
        elif self.pos.y > self.room.bottom - half:
            self.pos.y = self.room.bottom - half
            touched = True

        return touched

    def _ray_length(self):
        """Hasta donde llega una linea recta desde el jefe (pared de la sala)."""

        half = self._half()

        best = 9999.0

        d = self.dir

        if d.x > 0.001:
            best = min(best, (self.room.right - half - self.pos.x) / d.x)
        elif d.x < -0.001:
            best = min(best, (self.room.left + half - self.pos.x) / d.x)

        if d.y > 0.001:
            best = min(best, (self.room.bottom - half - self.pos.y) / d.y)
        elif d.y < -0.001:
            best = min(best, (self.room.top + half - self.pos.y) / d.y)

        return max(20.0, best)

    def _aim_at(self, target):

        want = pygame.Vector2(target) - self.pos

        if want.length_squared() > 1.0:
            self.dir = want.normalize()

    def update(self, dt, target):

        self.anim_t += dt

        target = pygame.Vector2(target)

        self.last_target = target

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.ring_t < 5.0:
            self.ring_t += dt

        if self.shown_hp > self._hp:
            self.shown_hp = max(
                self._hp, self.shown_hp - self.max_hp * 0.35 * dt
            )
        else:
            self.shown_hp = self._hp

        if self.dying:
            self._update_dying(dt)
            return

        if self._hp <= 0:
            self._begin_dying()
            return

        if self.spawning:

            self.spawn_t -= dt

            raw = 1.0 - max(0.0, self.spawn_t) / self.intro_time

            self.size = _lerp(self.base * 0.35, self.base, _ease(raw))

            self.shake = 0.4 + 2.2 * raw ** 1.5

            self._sync_rect()

            if self.spawn_t <= 0:

                self.ring_t = 0.0
                self.shake = 0.0
                self.flash = 0.12

                self._emit("slam", self.pos)

                if self.hold_after > 0:

                    self.state = "idle"
                    self.hold_t = self.hold_after

                else:
                    self._go(0)

            return

        if self.hold_t > 0:

            self.hold_t -= dt

            self.size = self.base * (1.0 + 0.02 * math.sin(self.anim_t * 2.2))
            self.shake = 0.0

            self._sync_rect()

            if self.hold_t <= 0:

                self.hold_t = 0.0
                self.size = self.base
                self._go(0)

            return

        if self.pending_phase and self.state != "phase":
            self._begin_phase()

        sdt = dt * (PHASE2_SPEED if self.phase == 2 else 1.0)

        self._update_hazards(sdt)

        handler = getattr(self, "_s_" + self.state)
        handler(sdt, target)

        self._sync_rect()

    # --- peligros que siguen vivos aunque el jefe cambie de ataque

    def _update_hazards(self, dt):

        keep = []

        for wave in self.waves:

            wave["r"] += WAVE_SPEED * dt

            if wave["r"] < WAVE_MAX_R:
                keep.append(wave)

        self.waves = keep

        for rock in self.rocks:

            rock["t"] += dt

            if rock["state"] == "warn" and rock["t"] >= rock["warn"]:

                rock["state"] = "impact"
                rock["t"] = 0.0

                self._emit("rock", rock["pos"])

            elif rock["state"] == "impact" and rock["t"] >= ROCK_IMPACT:

                rock["state"] = "crater"
                rock["t"] = 0.0

            elif rock["state"] == "crater" and rock["t"] >= ROCK_CRATER:

                rock["state"] = "done"

        self.rocks = [r for r in self.rocks if r["state"] != "done"]

        if self.beam_on:

            self.beam_t += dt

            if self.beam_t >= BEAM_TIME:
                self.beam_on = False

    def _clear_hazards(self):

        self.waves = []
        self.rocks = []
        self.beam_on = False

    # --- estados del patron

    def _s_chase(self, dt, target):

        self.t += dt

        want = target - self.pos

        if want.length_squared() > 4.0:

            self.dir = want.normalize()
            self.pos += self.dir * CHASE_SPEED * dt

        self._clamp()

        # pasos pesados: tiembla un poquito al pisar
        self.shake = 0.35 if math.sin(self.anim_t * 7.0) > 0.92 else 0.0

        if self.t >= CHASE_TIME[self.phase - 1]:
            self._next()

    def _s_charge_aim(self, dt, target):

        self.t += dt

        if self.t < CHARGE_AIM - CHARGE_LOCK:
            self._aim_at(target)

        k = self.t / CHARGE_AIM

        self.shake = 0.3 + 1.7 * k

        if self.t >= CHARGE_AIM:

            self.state = "charge_run"
            self.t = 0.0
            self.charge_speed = 120.0
            self.shake = 0.0

            self._emit("roar", self.pos)

    def _s_charge_run(self, dt, target):

        self.t += dt

        self.charge_speed = min(
            CHARGE_SPEED,
            self.charge_speed + (CHARGE_SPEED - 120.0) * dt / CHARGE_RAMP
        )

        self.pos += self.dir * self.charge_speed * dt

        if self._clamp():

            self.stun_len = STUN_TIME
            self.state = "stun"
            self.t = 0.0
            self.shake = 3.0
            self.flash = 0.1

            self._emit("wallhit", self.pos)

            return

        if self.t >= CHARGE_MAX:

            self.stun_len = 1.2
            self.state = "stun"
            self.t = 0.0

    def _s_stun(self, dt, target):

        self.t += dt

        self.shake = max(0.0, 2.5 * (1.0 - self.t / 0.5))

        if self.t >= self.stun_len:
            self._next()

    def _s_slam(self, dt, target):

        self.t += dt

        if self.t < SLAM_WIND:

            k = self.t / SLAM_WIND

            self.shake = 0.4 + 1.8 * k

            return

        self.shake = 0.0

        if self.waves_left > 0:

            self.wave_cd -= dt

            if self.wave_cd <= 0:

                self.waves.append({
                    "r": 10.0, "hit": False,
                    "origin": pygame.Vector2(self.pos),
                })

                self.waves_left -= 1
                self.wave_cd = WAVE_GAP
                self.ring_t = 0.0

                self._emit("wave", self.pos)

            return

        self.rest_t += dt

        if self.rest_t >= SLAM_REST:
            self._next()

    def _spawn_rock(self, x, y):

        self.rocks.append({
            "pos": pygame.Vector2(x, y),
            "t": 0.0,
            "warn": ROCK_WARN[self.phase - 1],
            "state": "warn",
            "hit": False,
        })

    def _spawn_batch(self, target):

        count = random.randint(*ROCK_PER_BATCH)

        margin = ROCK_RADIUS + 4

        placed = []

        for i in range(count):

            for _ in range(30):

                if i == 0:
                    p = pygame.Vector2(target)
                else:

                    ang = random.uniform(0, math.tau)
                    dist = random.uniform(30, 140)

                    p = pygame.Vector2(target) + pygame.Vector2(
                        math.cos(ang), math.sin(ang)
                    ) * dist

                p.x = max(self.room.left + margin,
                          min(p.x, self.room.right - margin))
                p.y = max(self.room.top + margin,
                          min(p.y, self.room.bottom - margin))

                if all(p.distance_to(q) > ROCK_RADIUS * 1.6 for q in placed):
                    break

            placed.append(p)

            self._spawn_rock(p.x, p.y)

    def _s_rocks(self, dt, target):

        self.t += dt

        if self.t < ROCK_WIND:

            self.shake = 0.4 + 1.2 * (self.t / ROCK_WIND)

            return

        self.shake = 0.0

        if self.batches_left > 0:

            self.batch_cd -= dt

            if self.batch_cd <= 0:

                self._spawn_batch(target)

                self.batches_left -= 1
                self.batch_cd = ROCK_GAP

            return

        self.rest_t += dt

        if self.rest_t >= ROCK_AFTER:
            self._next()

    def _s_beam(self, dt, target):

        self.t += dt

        if self.t < BEAM_AIM:

            if self.t < BEAM_AIM - BEAM_LOCK:
                self._aim_at(target)

            self.shake = 0.3 + 1.2 * (self.t / BEAM_AIM)

            return

        if not self.beam_on and self.beam_t <= 0.0 and not self.beam_hit:

            self.beam_on = True
            self.beam_hit = False
            self.beam_t = 0.0
            self.shake = 2.0

            self._emit("beam", self.pos)

        if not self.beam_on and self.t >= BEAM_AIM + BEAM_TIME + BEAM_REST:

            self.beam_t = 0.0
            self.beam_hit = False
            self._next()

    def _s_sweep(self, dt, target):

        self.t += dt

        if self.t < SWEEP_WIND:

            k = self.t / SWEEP_WIND

            self.sweep_angle = (
                self.sweep_angle + SWEEP_RATE * 0.4 * k * dt
            ) % 360.0

            self.shake = 0.4 + 1.2 * k

            return

        if self.t < SWEEP_WIND + SWEEP_TIME:

            self.sweep_angle = (self.sweep_angle + SWEEP_RATE * dt) % 360.0

            want = target - self.pos

            if want.length_squared() > 4.0:
                self.pos += want.normalize() * SWEEP_MOVE * dt

            self._clamp()

            self.shake = 0.5

            return

        self.shake = 0.0

        self.stun_len = SWEEP_REST
        self.state = "stun"
        self.t = 0.0

    def _s_shield(self, dt, target):

        self.t += dt

        if self.t < SHIELD_WIND:

            self.shake = 0.5 + 1.8 * (self.t / SHIELD_WIND)

            return

        if not self.summoned:

            self.summoned = True
            self.summon_request = True
            self.shielded = True
            self.shake = 0.0
            self.ring_t = 0.0
            self.flash = 0.15

            self._emit("summon", self.pos)

            return

        waited = self.t - SHIELD_WIND

        if (
            (self.minions <= 0 and waited >= SHIELD_MIN)
            or waited >= SHIELD_MAX
        ):

            self.shielded = False
            self.flash = 0.2
            self.ring_t = 0.0

            self._emit("shatter", self.pos)

            self._next()

    # --- cambio de fase y muerte

    def _begin_phase(self):

        self.phase = 2
        self.pending_phase = False
        self.shielded = False

        self._clear_hazards()

        self.vel.update(0, 0)

        self.state = "phase"
        self.t = 0.0
        self.ring_t = 0.0

        self.step = -1

        self._emit("phase", self.pos)

    def _s_phase(self, dt, target):

        self.t += dt

        k = min(1.0, self.t / PHASE_TIME)

        self.shake = 1.0 + 3.0 * k
        self.size = _lerp(self.size, self.base * 1.08, min(1.0, 5.0 * dt))

        self._clamp()

        if self.t >= PHASE_TIME:

            self.shake = 0.0
            self.size = self.base
            self.flash = 0.2
            self.ring_t = 0.0

            self._emit("roar", self.pos)

            self._go(0)

    def _begin_dying(self):

        self.dying = True
        self.dying_t = DYING_TIME

        self.shielded = False

        self._clear_hazards()

        self.vel.update(0, 0)

        self._emit("die", self.pos)

    def _update_dying(self, dt):

        self.dying_t -= dt

        self.fx_cd -= dt

        k = self.dying_k

        self.shake = 1.2 + 3.8 * k ** 1.3

        self.size = self.base * (1.0 + 0.04 * math.sin(self.anim_t * 9.0))

        self._crack_t += dt

        if self._crack_t >= CRACK_EVERY * (1.0 - 0.45 * k):

            self._crack_t = 0.0
            self.flash = 0.09

            self._emit("crack", self.pos)

        self._sync_rect()

    # ----------------------------------------------------------------- dibujo

    def _sprite(self, img, px, key, alpha=None):
        """Imagen a pixeles reales; solo se escala si cambia el tamano."""

        ck = (key, px)

        out = self._cache.get(ck)

        if out is None:

            if len(self._cache) > 160:
                self._cache.clear()

            out = img

            if img.get_width() != px or img.get_height() != px:
                out = pygame.transform.scale(img, (px, px))

            self._cache[ck] = out

        return out

    def _to_screen(self, camera, x, y):

        return (
            int(x * camera.zoom - camera.x),
            int(y * camera.zoom - camera.y),
        )

    def _body_frame(self):

        p = self.phase - 1

        frames = self.art.body[p]

        n = len(frames)

        idx = int(self.anim_t / ANIM_FRAME) % n if n > 1 else 0

        pose = None

        if self.state in ("charge_aim", "charge_run"):
            pose = self.art.poses.get("charge")
        elif self.state in ("slam", "rocks"):
            pose = self.art.poses.get("slam")
        elif self.state == "beam":
            pose = self.art.poses.get("beam")

        if pose is not None:
            return pose[p], ("pose", self.state, p)

        walk = self.art.walk[p]

        if walk and self.state == "chase":

            step = WALK_FRAME / (PHASE2_SPEED if p == 1 else 1.0)
            widx = int(self.anim_t / step) % len(walk)

            return walk[widx], ("walk", p, widx)

        return frames[idx], ("body", p, idx)

    def draw(self, screen, camera):

        if self.dead:
            return

        self._draw_ground(screen, camera)
        self._draw_body(screen, camera)
        self._draw_air(screen, camera)

    def _draw_body(self, screen, camera):

        z = camera.zoom

        p = self.phase - 1

        px = max(4, int(round(self.size * z)))

        cx, cy = self._to_screen(camera, self.pos.x, self.pos.y)

        if self.shake > 0:

            cx += int(random.uniform(-self.shake, self.shake) * z)
            cy += int(random.uniform(-self.shake, self.shake) * z)

        # sombra
        sw = int(px * 1.1)
        sh = max(2, int(px * 0.38))

        shadow = self._shadow.get((sw, sh))

        if shadow is None:

            if len(self._shadow) > 60:
                self._shadow.clear()

            shadow = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 100), shadow.get_rect())

            self._shadow[(sw, sh)] = shadow

        screen.blit(shadow, shadow.get_rect(center=(cx, cy + int(px * 0.46))))

        if self.state == "sweep":

            big = int(round(self.art.sweep_size * (self.size / self.base) * z))

            img = self._sprite(
                self.art.sweep[p], max(8, big), ("sweep", p)
            )

            img = pygame.transform.rotate(img, -self.sweep_angle)

            screen.blit(img, img.get_rect(center=(cx, cy)))

            return

        frame, key = self._body_frame()

        if self.flash > 0:

            img = self._sprite(self.art.hit[p], px, ("hit", p))

            # las poses sin dibujo propio de golpe usan el cuerpo
        else:

            img = self._sprite(frame, px, key)

        if self.dying:

            k = self.dying_k

            if k > 0.8:

                img = img.copy()
                img.set_alpha(int(255 * (1.0 - (k - 0.8) / 0.2)))

        elif self.spawning:

            img = img.copy()

            k = 1.0 - max(0.0, self.spawn_t) / self.intro_time

            img.set_alpha(int(60 + 195 * max(0.0, min(1.0, k))))

        # brillo verde de la fase 2 (la sala es oscura: es lo que mas se ve)
        if self.phase == 2 and not self.spawning:

            r = _quant(px * 0.60)

            glow = self._glow.get(r)

            if glow is None:

                if len(self._glow) > 40:
                    self._glow.clear()

                glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)

                pygame.draw.circle(glow, (40, 230, 120, 45), (r, r), r)
                pygame.draw.circle(
                    glow, (90, 255, 160, 45), (r, r), int(r * 0.65)
                )

                self._glow[r] = glow

            screen.blit(glow, glow.get_rect(center=(cx, cy)))

        screen.blit(img, img.get_rect(center=(cx, cy)))

        if self.shielded or self.state == "shield" and self.t >= SHIELD_WIND:

            sp = int(px * 1.3)

            sh_img = self._sprite(self.art.shield, sp, ("shield",))

            sh_img = pygame.transform.rotate(sh_img, self.anim_t * 25.0)

            screen.blit(sh_img, sh_img.get_rect(center=(cx, cy)))

    def _draw_ground(self, screen, camera):
        """Avisos y ataques que van pegados al piso (debajo del jefe)."""

        z = camera.zoom

        # rocas: circulo de aviso, y la roca baja justo antes de caer
        for rock in self.rocks:

            sx, sy = self._to_screen(camera, rock["pos"].x, rock["pos"].y)

            r = int(ROCK_RADIUS * z)

            if rock["state"] == "warn":

                k = rock["t"] / rock["warn"]

                pulse = 0.5 + 0.5 * math.sin(rock["t"] * (8.0 + 12.0 * k))

                col = (
                    int(_lerp(60, 120, pulse)),
                    int(_lerp(200, 255, pulse)),
                    int(_lerp(110, 170, pulse)),
                )

                pygame.draw.circle(screen, col, (sx, sy), r, max(2, int(z)))

                inner = max(2, int(r * k))

                pygame.draw.circle(screen, GREEN, (sx, sy), inner, 1)

                fall = max(0.0, (k - 0.7) / 0.3)

                if fall > 0:

                    rp = max(8, int(ROCK_RADIUS * 1.5 * z))

                    img = self._sprite(self.art.rock, rp, ("rock",))

                    off = int((1.0 - fall) ** 2 * 260)

                    screen.blit(
                        img, img.get_rect(center=(sx, sy - off))
                    )

            elif rock["state"] == "impact":

                pygame.draw.circle(screen, (235, 255, 240), (sx, sy), r)
                pygame.draw.circle(screen, GREEN, (sx, sy), r, max(2, int(z)))

            elif rock["state"] == "crater":

                k = rock["t"] / ROCK_CRATER

                col = (
                    int(_lerp(90, 30, k)),
                    int(_lerp(96, 36, k)),
                    int(_lerp(100, 40, k)),
                )

                pygame.draw.circle(screen, col, (sx, sy), int(r * 0.8))

        # linea de la embestida
        if self.state == "charge_aim":

            length = self._ray_length()

            a = self._to_screen(camera, self.pos.x, self.pos.y)
            b = self._to_screen(
                camera,
                self.pos.x + self.dir.x * length,
                self.pos.y + self.dir.y * length
            )

            locked = self.t >= CHARGE_AIM - CHARGE_LOCK

            col = (255, 90, 60) if locked else (255, 200, 90)

            if not locked or int(self.t * 14) % 2 == 0:
                pygame.draw.line(screen, col, a, b, max(3, int(2.5 * z)))

        # linea fina del rayo mientras apunta
        if self.state == "beam" and self.t < BEAM_AIM and not self.beam_on:

            a = self._to_screen(camera, self.pos.x, self.pos.y)
            b = self._to_screen(
                camera,
                self.pos.x + self.dir.x * BEAM_LEN,
                self.pos.y + self.dir.y * BEAM_LEN
            )

            locked = self.t >= BEAM_AIM - BEAM_LOCK

            col = (255, 255, 255) if locked else GREEN

            if not locked or int(self.t * 16) % 2 == 0:
                pygame.draw.line(screen, col, a, b, max(1, int(z * 0.5)))

        # aviso de la onda: anillo que se cierra sobre el jefe
        if self.state == "slam" and self.t < SLAM_WIND:

            k = self.t / SLAM_WIND

            cx, cy = self._to_screen(camera, self.pos.x, self.pos.y)

            pygame.draw.circle(
                screen, (255, 225, 90), (cx, cy),
                int(_lerp(self.base * 2.6, self.base * 0.7, k) * z), 3
            )

        # ondas de piedra
        for wave in self.waves:

            ox, oy = self._to_screen(
                camera, wave["origin"].x, wave["origin"].y
            )

            r = int(wave["r"] * z)

            if r < 4 or r > 4200:
                continue

            w = max(4, int(WAVE_HALF * 2 * z))

            pygame.draw.circle(screen, STONE_DARK, (ox, oy), r + 2, w + 4)
            pygame.draw.circle(screen, (170, 178, 184), (ox, oy), r, w)
            pygame.draw.circle(screen, GREEN, (ox, oy), r, max(2, w // 4))

        # anillo cuando se arma o se rompe algo
        if self.ring_t < 0.6:

            k = self.ring_t / 0.6

            cx, cy = self._to_screen(camera, self.pos.x, self.pos.y)

            col = (255, 255, 255) if self.phase == 1 else (150, 255, 190)

            pygame.draw.circle(
                screen, col, (cx, cy),
                int(_lerp(self.base * 0.5, 120.0, 1.0 - (1.0 - k) ** 2) * z),
                int(4 * (1.0 - k)) + 1
            )

    def _draw_air(self, screen, camera):
        """Lo que va por encima del jefe: rayo y estrellitas del aturdido."""

        z = camera.zoom

        if self.beam_on:

            a = self._to_screen(camera, self.pos.x, self.pos.y)
            b = self._to_screen(
                camera,
                self.pos.x + self.dir.x * BEAM_LEN,
                self.pos.y + self.dir.y * BEAM_LEN
            )

            k = self.beam_t / BEAM_TIME

            w = max(4, int(BEAM_HALF * 2 * z * (1.0 - 0.4 * k)))

            pygame.draw.line(screen, GREEN_DARK, a, b, w + 8)
            pygame.draw.line(screen, GREEN, a, b, w)
            pygame.draw.line(screen, (235, 255, 240), a, b, max(2, w // 3))

        if self.state == "stun" and not self.dying:

            cx, cy = self._to_screen(
                camera, self.pos.x, self.pos.y - self.size * 0.55
            )

            for i in range(3):

                a = self.anim_t * 4.0 + i * math.tau / 3.0

                sx = cx + int(math.cos(a) * self.size * 0.35 * z)
                sy = cy + int(math.sin(a) * self.size * 0.10 * z)

                pygame.draw.circle(
                    screen, (255, 235, 120), (sx, sy), max(3, int(1.6 * z))
                )
                pygame.draw.circle(
                    screen, (255, 255, 255), (sx, sy), max(1, int(0.7 * z))
                )