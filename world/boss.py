"""Jefe de la Zona 1: Piña Colosal.

Este archivo no importa nada de arena.py (para no hacer imports circulares).

Sprites propios (carpeta assets/maps/combate/), todos PNG con fondo transparente:
    jefe_pina.png               cuerpo (cuadrado). Opcional: jefe_pina_anim.png
                                (tira horizontal de cuadros cuadrados)
    jefe_pina_fase2.png         opcional, cuerpo de la fase 2 (o _fase2_anim.png)
    jefe_pina_golpe.png         opcional, cuando recibe un golpe
    jefe_pina_fragmentos.png    tira de 12 cuadros (uno por fragmento)
                                o jefe_pina_fragmento.png (uno solo para todos)

El tamaño en el juego sale del tamaño de TU imagen: se dibuja a pixeles reales
(zoom x4 del juego = REF_ZOOM). Solo se escala mientras el jefe se agranda o se
achica, que es parte de su ataque. Si falta algun archivo se dibuja un
reemplazo provisorio.

Patron (se repite en bucle):
    rodar -> agrandarse -> mantener -> achicarse -> centro -> dividirse en 12
    -> las partes rebotan por toda la sala (hay que esquivarlas, no se les
    puede pegar) -> vuelven y se juntan
    -> rodar -> agrandarse -> mantener -> achicarse -> centro
    -> invoca 5 de cada enemigo -> sigue activo mientras peleas -> cuando
    mataste a todos vuelve a empezar.

Se le puede pegar siempre que este entero. A la mitad de la vida pasa a la
Fase 2: todo va mas rapido (PHASE2_SPEED).
"""

import math
import random

import pygame


BOSS_NAME = "PIÑA COLOSAL"

# Vida total. El golpe del jugador hace 1 (fosforo/vela) o 2 (antorcha).
BOSS_HP = 360.0

# El juego dibuja con zoom x4: 1 unidad de mundo = 4 pixeles de sprite.
REF_ZOOM = 4

# Si no hay sprite propio: tamanos (en unidades de mundo) del reemplazo.
DEFAULT_BASE = 40.0
DEFAULT_FRAG = 18.0

# Cuanto se agranda (multiplo de su tamano normal) y tope respecto a la sala.
MAX_MULT = 2.4
MAX_ROOM_FRACTION = 0.8

# En fase 2 todo (movimiento, tiempos, ataques) corre a esta velocidad.
PHASE2_SPEED = 1.55

# Girar el sprite mientras rueda (como la piña normal). Ponelo en False si
# tu dibujo tiene cara y no queres que gire.
ROTATE_SPRITE = True

ANIM_FRAME = 0.14

INTRO_TIME = 1.8

ROLL_SPEED = 155.0  # Mas rapido, conservando los rebotes originales
ROLL_TIME = 5.0
GROW_TIME = 2.0
HOLD_TIME = 1.6
SHRINK_TIME = 1.5
CENTER_SPEED = 300.0
SPLIT_WIND = 1.1

FRAG_COUNT = 12
FRAG_SPEED = 175.0
FRAG_TIME = 4.5
REGROUP_START = 120.0
REGROUP_ACCEL = 200.0
REGROUP_MAX = 300.0
REGROUP_TIMEOUT = 7.0

SUMMON_WIND = 1.3
SUMMON_REST = 1.3
SUMMON_COUNT = 6
WAIT_MIN = 1.0

PHASE_TIME = 2.2
DYING_TIME = 1.8

BODY_DAMAGE = 0.20
FRAG_DAMAGE = 0.16

# Con cuanta fuerza empuja al jugador al tocarlo
CONTACT_PUSH = 300.0

BOUNCE_AIM = 0.6

CYCLE = (
    "roll", "grow", "hold", "shrink", "center", "split", "frags", "regroup",
    "roll", "grow", "hold", "shrink", "center", "summon",
)

FLASH_TIME = 0.10

BAR_NAME_TOP = 104
BAR_TOP = 128
BAR_HEIGHT = 20


def _ease(k):

    k = max(0.0, min(1.0, k))

    return k * k * (3.0 - 2.0 * k)


def _lerp(a, b, k):

    return a + (b - a) * k


def _quant(radius):

    return max(8, int(round(radius / 8.0)) * 8)


# ------------------------------------------------------------------- sprites


def _placeholder_body():
    """Reemplazo provisorio (160x160) hasta que estén tus dibujos."""

    s = 160
    surf = pygame.Surface((s, s), pygame.SRCALPHA)

    pygame.draw.ellipse(surf, (230, 160, 40), (20, 36, 120, 116))
    pygame.draw.ellipse(surf, (120, 70, 20), (20, 36, 120, 116), 4)

    for i in range(-3, 4):

        pygame.draw.line(
            surf, (160, 100, 30), (80 + i * 18, 40), (80 + i * 18 + 40, 150), 2
        )
        pygame.draw.line(
            surf, (160, 100, 30), (80 + i * 18 + 40, 40), (80 + i * 18, 150), 2
        )

    for dx, h in ((-28, 30), (-12, 40), (4, 46), (20, 40), (36, 30)):

        pygame.draw.polygon(
            surf, (50, 140, 60),
            [(80 + dx - 8, 44), (80 + dx, 38 - h // 2), (80 + dx + 8, 44)]
        )

    pygame.draw.circle(surf, (30, 20, 10), (62, 88), 8)
    pygame.draw.circle(surf, (30, 20, 10), (98, 88), 8)
    pygame.draw.line(surf, (30, 20, 10), (56, 76), (72, 82), 4)
    pygame.draw.line(surf, (30, 20, 10), (104, 76), (88, 82), 4)

    return surf


def _placeholder_frag(i):

    s = 72
    surf = pygame.Surface((s, s), pygame.SRCALPHA)

    pygame.draw.circle(surf, (230, 160, 40), (s // 2, s // 2), 30)
    pygame.draw.circle(surf, (120, 70, 20), (s // 2, s // 2), 30, 3)
    pygame.draw.line(surf, (160, 100, 30), (20, 22), (52, 52), 2)
    pygame.draw.line(surf, (160, 100, 30), (52, 22), (20, 52), 2)

    return surf


def _tint(frame):

    img = frame.copy()
    img.fill((255, 175, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)

    return img


def _flash(frame):

    img = frame.copy()
    img.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

    return img


class BossArt:
    """Carga los sprites del jefe (ver docstring del archivo)."""

    def __init__(self, folder, load_image, load_strip):

        body = (
            load_strip(folder / "jefe_pina_anim.png")
            or load_strip(folder / "jefe_pina.png")
        )

        self.custom = bool(body)

        if not body:
            body = [_placeholder_body()]

        body2 = (
            load_strip(folder / "jefe_pina_fase2_anim.png")
            or load_strip(folder / "jefe_pina_fase2.png")
        )

        if not body2:
            body2 = [_tint(f) for f in body]

        hit = load_image(folder / "jefe_pina_golpe.png")

        frags = (
            load_strip(folder / "jefe_pina_fragmentos.png")
            or load_strip(folder / "jefe_pina_fragmento.png")
        )

        if not frags:
            frags = [_placeholder_frag(i) for i in range(FRAG_COUNT)]

        self.body = (body, body2)
        self.hit = (
            (hit, hit) if hit is not None
            else (_flash(body[0]), _flash(body2[0]))
        )
        self.frags = frags
        self.frags_hit = [_flash(f) for f in frags]

        self.base_size = body[0].get_width() / float(REF_ZOOM)
        self.frag_size = frags[0].get_width() / float(REF_ZOOM)


# ------------------------------------------------------------------ fragmentos


class Fragment:
    """Una de las 12 partes. No se le puede pegar: hay que esquivarla."""

    def __init__(self, index, size, pos, vel):

        self.index = index
        self.size = size

        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)

        side = max(4, int(round(size)))

        self.rect = pygame.Rect(0, 0, side, side)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.spin = random.uniform(0, 360)
        self.speed = self.vel.length()

    def sync(self):

        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def bounce_move(self, dt, room):

        self.pos += self.vel * dt

        half = self.size / 2

        if self.pos.x - half < room.left:
            self.pos.x = room.left + half
            self.vel.x = abs(self.vel.x)
        elif self.pos.x + half > room.right:
            self.pos.x = room.right - half
            self.vel.x = -abs(self.vel.x)

        if self.pos.y - half < room.top:
            self.pos.y = room.top + half
            self.vel.y = abs(self.vel.y)
        elif self.pos.y + half > room.bottom:
            self.pos.y = room.bottom - half
            self.vel.y = -abs(self.vel.y)

        self.spin = (
            self.spin + math.degrees(self.vel.x * dt / max(1.0, half))
        ) % 360.0

        self.sync()


# ------------------------------------------------------------------------ jefe


class PinaBoss:

    is_boss = True
    fixed = False
    contact_damage = False
    precise_hit = True
    attached = False
    codex_key = None
    touch_cd = 0.0
    stun = 0.0

    def __init__(self, x, y, room, art, hp=BOSS_HP):

        self.room = room
        self.art = art

        self.base = float(art.base_size)
        self.frag_size = float(art.frag_size)

        self.max_size = min(
            self.base * MAX_MULT,
            min(room.width, room.height) * MAX_ROOM_FRACTION
        )
        self.max_size = max(self.max_size, self.base)

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
        self.spin = 0.0
        self.anim_t = 0.0

        self.spawn_t = INTRO_TIME

        self.state = "intro"
        self.step = -1
        self.t = 0.0

        self.fragments = []
        self.absorbed = 0
        self.summoned = False

        # la arena lo actualiza: cuantos enemigos invocados siguen vivos
        self.minions = 0

        self.summon_request = False
        self.events = []

        self.dying = False
        self.dying_t = 0.0
        self.cleanup_done = False
        self.fx_cd = 0.0

        self.ring_t = 99.0

        self._cache = {}
        self._aura = {}
        self._shadow = {}

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

        # Solo mientras aparece o se esta muriendo. El resto del tiempo
        # recibe dano.
        return self.spawning or self.dying

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
        """A quien se le puede pegar. Los fragmentos NO se pueden golpear."""

        if self.spawning or self.dying:
            return []

        if self.state in ("frags", "regroup"):
            return []

        return [self]

    # ----------------------------------------------------------------- dano

    def contact_hit(self, body):
        """(dano, punto de origen) si algo del jefe toca el cuerpo del jugador."""

        if self.spawning or self.dying:
            return None

        if self.state in ("frags", "regroup"):

            for frag in self.fragments:

                if frag.rect.colliderect(body):
                    return FRAG_DAMAGE, frag.pos

            return None

        radius = self.size * 0.5 * 0.9

        nx = max(body.left, min(self.pos.x, body.right))
        ny = max(body.top, min(self.pos.y, body.bottom))

        if math.hypot(nx - self.pos.x, ny - self.pos.y) < radius:
            return BODY_DAMAGE, self.pos

        return None

    # ----------------------------------------------------------------- luces

    def lights(self):

        out = []

        if self.dead:
            return out

        if self.state in ("frags", "regroup"):

            for frag in self.fragments:
                out.append((frag.pos.x, frag.pos.y, 24))

            if self.state == "regroup":
                out.append(
                    (self.pos.x, self.pos.y, _quant(self.size * 0.9 + 24))
                )

            return out

        out.append((self.pos.x, self.pos.y, _quant(self.size * 0.9 + 36)))

        return out

    # ---------------------------------------------------------------- estados

    def _emit(self, name):

        self.events.append(name)

    def _go(self, step):

        self.step = step % len(CYCLE)
        self.state = CYCLE[self.step]
        self.t = 0.0

        if self.state == "split":

            self.vel.update(0, 0)
            self.shake = 0.0

        elif self.state == "summon":

            self.vel.update(0, 0)
            self.summoned = False

        elif self.state == "regroup":

            self.absorbed = 0

    def _next(self):

        self._go(self.step + 1)

    def _resume(self):
        """Despues de la fase: sigue el bucle, o espera si hay invocados."""

        if self.minions > 0:

            self.state = "wait"
            self.t = 0.0

        else:

            self._go(0)

    def _sync_rect(self):

        side = max(2, int(round(self.size)))

        self.rect.size = (side, side)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def _half(self):

        return min(
            self.size / 2, self.room.width / 2 - 1, self.room.height / 2 - 1
        )

    def _clamp(self):

        half = self._half()

        self.pos.x = max(self.room.left + half, min(self.pos.x, self.room.right - half))
        self.pos.y = max(self.room.top + half, min(self.pos.y, self.room.bottom - half))

    def update(self, dt, target):

        self.anim_t += dt

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

            k = _ease(1.0 - max(0.0, self.spawn_t) / INTRO_TIME)

            self.size = _lerp(self.base * 0.35, self.base, k)
            self.spin += 300.0 * dt
            self.shake = 0.0

            self._sync_rect()

            if self.spawn_t <= 0:

                self.ring_t = 0.0
                self._emit("roar")
                self._go(0)

            return

        if self.pending_phase and self.state != "phase":
            self._begin_phase()

        # Fase 2: todo corre mas rapido (movimiento, tiempos y ataques)
        sdt = dt * (PHASE2_SPEED if self.phase == 2 else 1.0)

        handler = getattr(self, "_s_" + self.state)
        handler(sdt, pygame.Vector2(target))

        self._sync_rect()

    # --- movimiento base

    def _roll_move(self, dt, target):

        speed = ROLL_SPEED

        cur = self.vel.length()

        if cur < 1.0:

            want = target - self.pos

            if want.length_squared() < 1.0:
                want = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            self.vel = want.normalize() * speed

        else:

            cur += (speed - cur) * min(1.0, 4.0 * dt)
            self.vel.scale_to_length(cur)

        self.pos += self.vel * dt

        half = self._half()

        hit_l = hit_r = hit_t = hit_b = False

        if self.pos.x - half < self.room.left:
            self.pos.x = self.room.left + half
            hit_l = True
        elif self.pos.x + half > self.room.right:
            self.pos.x = self.room.right - half
            hit_r = True

        if self.pos.y - half < self.room.top:
            self.pos.y = self.room.top + half
            hit_t = True
        elif self.pos.y + half > self.room.bottom:
            self.pos.y = self.room.bottom - half
            hit_b = True

        if hit_l or hit_r or hit_t or hit_b:
            self._bounce(target, hit_l, hit_r, hit_t, hit_b)

        self.spin = (
            self.spin + math.degrees(self.vel.x * dt / max(4.0, self.size / 2))
        ) % 360.0

    def _bounce(self, target, hit_l, hit_r, hit_t, hit_b):

        speed = max(1.0, self.vel.length())

        cur = self.vel / speed

        if hit_l:
            cur.x = abs(cur.x)
        if hit_r:
            cur.x = -abs(cur.x)
        if hit_t:
            cur.y = abs(cur.y)
        if hit_b:
            cur.y = -abs(cur.y)

        want = target - self.pos

        if want.length_squared() > 1.0:

            mix = cur * (1.0 - BOUNCE_AIM) + want.normalize() * BOUNCE_AIM

            if mix.length_squared() > 0.0001:

                mix = mix.normalize()

                # nunca volver contra la pared que acaba de tocar
                if hit_l:
                    mix.x = abs(mix.x) + 0.2
                if hit_r:
                    mix.x = -abs(mix.x) - 0.2
                if hit_t:
                    mix.y = abs(mix.y) + 0.2
                if hit_b:
                    mix.y = -abs(mix.y) - 0.2

                cur = mix.normalize()

        self.vel = cur * speed
        self._emit("bounce")

    # --- estados del patron

    def _s_roll(self, dt, target):

        self.t += dt
        self.shake = 0.0

        self._roll_move(dt, target)

        if self.t >= ROLL_TIME:
            self._next()

    def _s_grow(self, dt, target):

        self.t += dt

        k = _ease(self.t / GROW_TIME)

        self.size = _lerp(self.base, self.max_size, k)

        self._roll_move(dt, target)
        self._clamp()

        if self.t >= GROW_TIME:
            self._next()

    def _s_hold(self, dt, target):

        self.t += dt

        self.size = self.max_size

        self._roll_move(dt, target)
        self._clamp()

        if self.t >= HOLD_TIME:
            self._next()

    def _s_shrink(self, dt, target):

        self.t += dt

        k = _ease(self.t / SHRINK_TIME)

        self.size = _lerp(self.max_size, self.base, k)

        self._roll_move(dt, target)
        self._clamp()

        if self.t >= SHRINK_TIME:

            self.size = self.base
            self._next()

    def _s_center(self, dt, target):

        self.t += dt

        self.size = self.base
        self.shake = 0.0

        to_center = self.center - self.pos
        dist = to_center.length()

        step = CENTER_SPEED * dt

        if dist <= step or self.t > 6.0:

            self.pos = self.center.copy()
            self.vel.update(0, 0)
            self._next()

            return

        direction = to_center / dist

        self.pos += direction * step
        self.vel = direction * 40.0

        self.spin = (
            self.spin + math.degrees(direction.x * step / (self.base / 2))
        ) % 360.0

        self._clamp()

    def _s_split(self, dt, target):

        self.t += dt

        k = min(1.0, self.t / SPLIT_WIND)

        self.shake = 0.5 + 2.5 * k
        self.size = self.base * (1.0 + 0.10 * math.sin(self.t * 28.0) * k)

        self.spin = (self.spin + 400.0 * k * dt) % 360.0

        if self.t >= SPLIT_WIND:
            self._burst()

    def _burst(self):

        offset = random.uniform(0, math.tau)

        self.fragments = []

        for i in range(FRAG_COUNT):

            angle = offset + i * math.tau / FRAG_COUNT

            direction = pygame.Vector2(math.cos(angle), math.sin(angle))

            vel = direction * FRAG_SPEED * random.uniform(0.9, 1.1)

            self.fragments.append(
                Fragment(i, self.frag_size, self.pos + direction * 8, vel)
            )

        self.size = self.base
        self.shake = 0.0
        self.ring_t = 0.0

        self._emit("split")

        self._go(self.step + 1)

    def _s_frags(self, dt, target):

        self.t += dt
        self.shake = 0.0

        for frag in self.fragments:
            frag.bounce_move(dt, self.room)

        if self.t >= FRAG_TIME:

            for frag in self.fragments:
                frag.speed = REGROUP_START

            self._go(self.step + 1)

    def _s_regroup(self, dt, target):

        self.t += dt
        self.shake = 0.0

        keep = []

        for frag in self.fragments:

            to_core = self.center - frag.pos
            dist = to_core.length()

            frag.speed = min(REGROUP_MAX, frag.speed + REGROUP_ACCEL * dt)

            step = frag.speed * dt

            if dist <= max(step, 6.0) or self.t > REGROUP_TIMEOUT:

                self.absorbed += 1
                self.ring_t = min(self.ring_t, 0.45)

                continue

            direction = to_core / dist

            frag.vel = direction * frag.speed
            frag.pos += direction * step
            frag.spin = (frag.spin + 540.0 * dt) % 360.0
            frag.sync()

            keep.append(frag)

        self.fragments = keep

        k = min(1.0, self.absorbed / float(FRAG_COUNT))

        self.pos = self.center.copy()
        self.size = self.base * (0.30 + 0.70 * k)
        self.spin = (self.spin + 200.0 * dt) % 360.0

        if not self.fragments:

            self.size = self.base
            self.flash = 0.18
            self.ring_t = 0.0
            self.vel.update(0, 0)

            self._emit("merge")
            self._next()

    def _s_summon(self, dt, target):

        self.t += dt

        self.size = self.base

        if self.t < SUMMON_WIND:

            k = self.t / SUMMON_WIND

            self.shake = 0.5 + 2.0 * k
            self.spin = (self.spin + 300.0 * k * dt) % 360.0

            return

        if not self.summoned:

            self.summoned = True
            self.summon_request = True
            self.shake = 0.0
            self.ring_t = 0.0
            self.flash = 0.15

            self._emit("summon")

        if self.t >= SUMMON_WIND + SUMMON_REST:

            self.state = "wait"
            self.t = 0.0

    def _s_wait(self, dt, target):
        """Sigue activo (rueda y se le puede pegar) mientras quedan invocados.

        Cuando se mataron todos, retoma el bucle desde el principio.
        """

        self.t += dt
        self.shake = 0.0

        self.size = self.base

        self._roll_move(dt, target)

        if self.minions <= 0 and self.t >= WAIT_MIN:
            self._go(0)

    # --- cambio de fase y muerte

    def _begin_phase(self):

        # Desde aca ya es fase 2 (puede bajar de la mitad) y recibe dano.
        self.phase = 2
        self.pending_phase = False

        self.fragments = []
        self.absorbed = 0
        self.summoned = False

        self.vel.update(0, 0)

        self.state = "phase"
        self.t = 0.0
        self.ring_t = 0.0

        self._emit("phase")

    def _s_phase(self, dt, target):

        self.t += dt

        k = min(1.0, self.t / PHASE_TIME)

        self.shake = 1.0 + 3.0 * k
        self.size = _lerp(self.size, self.base * 1.15, min(1.0, 5.0 * dt))
        self.spin = (self.spin + 500.0 * k * dt) % 360.0

        self._clamp()

        if self.t >= PHASE_TIME:

            self.shake = 0.0
            self.size = self.base
            self.flash = 0.2
            self.ring_t = 0.0

            self._emit("roar")
            self._resume()

    def _begin_dying(self):

        self.dying = True
        self.dying_t = DYING_TIME

        self.fragments = []
        self.vel.update(0, 0)

        self._emit("die")

    def _update_dying(self, dt):

        self.dying_t -= dt

        self.fx_cd -= dt

        self.shake = 2.0 + 2.0 * (1.0 - max(0.0, self.dying_t) / DYING_TIME)
        self.spin = (self.spin + 500.0 * dt) % 360.0

        if int(self.anim_t * 14) % 2 == 0:
            self.flash = 0.06

        self.size = self.base * (1.0 + 0.25 * math.sin(self.anim_t * 24.0))

        self._sync_rect()

    # ----------------------------------------------------------------- dibujo

    def _sprite(self, frames, hit_img, px, key):
        """Imagen a pixeles reales; solo se escala si cambia el tamaño."""

        ck = (key, px, hit_img is not None)

        img = self._cache.get(ck)

        if img is None:

            if len(self._cache) > 120:
                self._cache.clear()

            img = hit_img if hit_img is not None else frames

            if img.get_width() != px:
                img = pygame.transform.scale(img, (px, px))

            self._cache[ck] = img

        return img

    def _world_to_screen(self, camera, x, y):

        return (
            int(x * camera.zoom - camera.x),
            int(y * camera.zoom - camera.y),
        )

    def _draw_ring(self, screen, camera, radius, color, width):

        cx, cy = self._world_to_screen(camera, self.pos.x, self.pos.y)

        pygame.draw.circle(
            screen, color, (cx, cy),
            max(1, int(radius * camera.zoom)), max(1, width)
        )

    def draw(self, screen, camera):

        if self.dead:
            return

        z = camera.zoom

        for frag in self.fragments:
            self._draw_fragment(screen, camera, frag)

        if self.state == "frags":

            self._draw_telegraph(screen, camera)

            return

        p = self.phase - 1

        frames = self.art.body[p]

        n = len(frames)

        idx = int(self.anim_t / ANIM_FRAME) % n if n > 1 else 0

        px = max(4, int(round(self.size * z)))

        if self.flash > 0:
            img = self._sprite(None, self.art.hit[p], px, ("hit", p))
        else:
            img = self._sprite(frames[idx], None, px, ("body", p, idx))

        if ROTATE_SPRITE:
            img = pygame.transform.rotate(img, self.spin)

        if self.spawning:

            img = img.copy()

            k = 1.0 - max(0.0, self.spawn_t) / INTRO_TIME

            img.set_alpha(int(60 + 195 * max(0.0, min(1.0, k))))

        cx, cy = self._world_to_screen(camera, self.pos.x, self.pos.y)

        if self.shake > 0:

            cx += int(random.uniform(-self.shake, self.shake) * z)
            cy += int(random.uniform(-self.shake, self.shake) * z)

        # sombra
        sw = int(px * 1.15)
        sh = max(2, int(px * 0.45))

        shadow = self._shadow.get((sw, sh))

        if shadow is None:

            if len(self._shadow) > 60:
                self._shadow.clear()

            shadow = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())

            self._shadow[(sw, sh)] = shadow

        screen.blit(shadow, shadow.get_rect(center=(cx, cy + int(px * 0.46))))

        # aura de fase 2
        if self.phase == 2 and not self.spawning:

            r = _quant(px * 0.62)

            aura = self._aura.get(r)

            if aura is None:

                if len(self._aura) > 40:
                    self._aura.clear()

                aura = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)

                pygame.draw.circle(aura, (255, 70, 30, 55), (r, r), r)
                pygame.draw.circle(aura, (255, 140, 40, 55), (r, r), int(r * 0.7))

                self._aura[r] = aura

            screen.blit(aura, aura.get_rect(center=(cx, cy)))

        screen.blit(img, img.get_rect(center=(cx, cy)))

        self._draw_telegraph(screen, camera)

    def _draw_fragment(self, screen, camera, frag):

        z = camera.zoom

        px = max(4, int(round(frag.size * z)))

        frames = self.art.frags

        i = frag.index % len(frames)

        img = self._sprite(frames[i], None, px, ("frag", i))

        img = pygame.transform.rotate(img, frag.spin)

        cx, cy = self._world_to_screen(camera, frag.pos.x, frag.pos.y)

        shadow = pygame.Surface(
            (int(px * 1.1), max(2, int(px * 0.4))), pygame.SRCALPHA
        )
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), shadow.get_rect())

        screen.blit(shadow, shadow.get_rect(center=(cx, cy + int(px * 0.45))))
        screen.blit(img, img.get_rect(center=(cx, cy)))

    def _draw_telegraph(self, screen, camera):

        if self.state in ("split", "summon") and not self.spawning:

            wind = SPLIT_WIND if self.state == "split" else SUMMON_WIND

            if self.t < wind:

                k = self.t / wind

                self._draw_ring(
                    screen, camera,
                    _lerp(self.base * 2.4, self.base * 0.7, k),
                    (255, 225, 90), 3
                )

        if self.ring_t < 0.6:

            k = self.ring_t / 0.6

            color = (255, 255, 255) if self.phase == 1 else (255, 170, 80)

            self._draw_ring(
                screen, camera,
                _lerp(self.base * 0.5, 120.0, 1.0 - (1.0 - k) ** 2),
                color, int(4 * (1.0 - k)) + 1
            )


# ---------------------------------------------------------------- barra de vida

_fonts = {}


def _font(size):

    f = _fonts.get(size)

    if f is None:

        f = _fonts[size] = pygame.font.Font(None, size)

    return f


def _text(screen, text, size, color, **anchor):

    font = _font(size)

    shadow = font.render(text, True, (0, 0, 0))
    label = font.render(text, True, color)

    rect = label.get_rect(**anchor)

    screen.blit(shadow, rect.move(2, 2))
    screen.blit(label, rect)

    return rect


def draw_boss_bar(screen, boss):
    """Barra arriba y centrada, debajo de la barra de efectos (no la tapa).

    Se dibuja con dos mitades: la marca del medio es el cambio de fase.
    """

    if boss.dead or boss.spawning:
        return

    w = screen.get_width()

    bw = max(120, min(460, w - 80))
    x = (w - bw) // 2
    y = BAR_TOP

    _text(
        screen, BOSS_NAME, 30, (255, 235, 190),
        midtop=(w // 2, BAR_NAME_TOP - 4)
    )

    back = pygame.Rect(x - 3, y - 3, bw + 6, BAR_HEIGHT + 6)

    pygame.draw.rect(screen, (22, 12, 12), back, border_radius=6)

    frac = max(0.0, min(1.0, boss.hp / boss.max_hp))
    shown = max(frac, min(1.0, boss.shown_hp / boss.max_hp))

    if shown > frac:

        pygame.draw.rect(
            screen, (236, 226, 200),
            pygame.Rect(x, y, int(bw * shown), BAR_HEIGHT),
            border_radius=4
        )

    if frac > 0:

        color = (40, 200, 75) if boss.phase == 1 else (20, 240, 90)

        pygame.draw.rect(
            screen, color,
            pygame.Rect(x, y, max(2, int(bw * frac)), BAR_HEIGHT),
            border_radius=4
        )

        light = (120, 255, 145) if boss.phase == 1 else (150, 255, 175)

        pygame.draw.rect(
            screen, light,
            pygame.Rect(x + 3, y + 3, max(1, int(bw * frac) - 6), 4),
            border_radius=2
        )

    mid = x + bw // 2

    pygame.draw.line(
        screen, (255, 255, 255), (mid, y - 5), (mid, y + BAR_HEIGHT + 5), 2
    )

    pygame.draw.rect(screen, (96, 62, 52), back, 2, border_radius=6)

    _text(
        screen, f"FASE {boss.phase}", 22,
        (255, 210, 160) if boss.phase == 1 else (255, 150, 90),
        midtop=(w // 2, y + BAR_HEIGHT + 6)
    )