"""Sala de combate (la sala grande de la derecha).

Al entrar aparece un menu transparente: Salir / Jugar con escape /
Jugar sin escape (premio X2). Despues vienen las oleadas:

  - Con escape: si te quedas sin vida te sacan de la sala (perdes la
    oleada, nada mas). Tambien podes irte caminando.
  - Sin escape: la entrada se bloquea mientras pelean, y si te quedas
    sin vida perdes de verdad. El premio vale el doble.

Al matar al ultimo enemigo aparece un cofre que brilla y explota,
tirando las monedas del premio. Cuando las juntas vuelve el menu para
la siguiente oleada.

Imagenes (todas opcionales: si falta alguna se dibuja un reemplazo):
  assets/maps/combate/enemigo.png            56x56
  assets/maps/combate/enemigo_anim.png       224x56 (4 frames)
  assets/maps/combate/enemigo_golpe.png      56x56
  assets/maps/combate/panel_sala_combate.png 420x300
  assets/maps/combate/btn_salir.png          260x56  (+ _hover)
  assets/maps/combate/btn_jugar_escape.png   260x56  (+ _hover)
  assets/maps/combate/btn_jugar_sin_escape.png 260x56 (+ _hover)
  assets/maps/combate/hud_oleada.png         180x40
  assets/maps/combate/pantalla_oleada_completa.png 420x200
"""

import math
import random
from pathlib import Path

import pygame

from world.items import WorldItem


BASE_DIR = Path(__file__).resolve().parent.parent

COMBAT_DIR = BASE_DIR / "assets" / "maps" / "combate"
CHEST_DIR = BASE_DIR / "assets" / "maps" / "cofre"
HUD_DIR = BASE_DIR / "assets" / "maps" / "hud"


# ---------------------------------------------------------------
# Lugar (unidades del mundo)
# ---------------------------------------------------------------

# La sala grande de la derecha (igual que en world/collision.py)
ROOM = pygame.Rect(1244, 388, 436, 284)

# El menu aparece cuando el jugador pisa esta zona (un poco adentro)
TRIGGER = pygame.Rect(1262, 400, 400, 260)

# Donde te deja "Salir": en el pasillo, afuera de la sala
EXIT_POS = (1190, 520)

# Barrera que cierra la entrada en "sin escape"
GATE = pygame.Rect(1236, 500, 10, 40)


# ---------------------------------------------------------------
# Oleadas (para balancear, se cambia todo aca)
# ---------------------------------------------------------------

# Cuantos enemigos trae cada oleada. Despues de la ultima definida
# sigue subiendo de a ENEMIES_STEP hasta ENEMIES_MAX.
WAVE_ENEMIES = {1: 1, 2: 4, 3: 6}
ENEMIES_STEP = 2
ENEMIES_MAX = 16

# Monedas de premio por oleada (la 1 vale 18). Despues de la ultima
# definida sube REWARD_STEP por oleada. "Sin escape" lo multiplica.
WAVE_REWARDS = {1: 18, 2: 30, 3: 45}
REWARD_STEP = 15
NO_ESCAPE_MULT = 2

# Vida y velocidad de los enemigos segun la oleada
ENEMY_HP_BASE = 2          # vida = BASE + oleada
ENEMY_HP_MAX = 10
ENEMY_SPEED_BASE = 58      # unidades del mundo por segundo
ENEMY_SPEED_STEP = 4
ENEMY_SPEED_MAX = 90

# Cuanta vida de la llama le saca cada choque (1.0 = toda la llama)
ENEMY_DAMAGE = 0.08
ENEMY_DAMAGE_STEP = 0.01
ENEMY_DAMAGE_MAX = 0.15

# Si te quedas sin vida en "con escape", te dejan con esta llama
ESCAPE_REVIVE_LIFE = 0.15


# ---------------------------------------------------------------
# Enemigo
# ---------------------------------------------------------------

ENEMY_DRAW_SIZE = 14       # tamano dibujado (unidades del mundo)
ENEMY_HITBOX = (12, 10)    # lo que choca y lo que golpea el fosforo

ENEMY_ACCEL = 320.0        # cuanto empuja hacia el jugador
ENEMY_DRAG = 1.6           # frenado natural (para poder girar)
ENEMY_BOUNCE_SPEED = 170.0 # velocidad del rebote tras chocarte
ENEMY_RECOVER_TIME = 0.45  # tras chocar casi no te persigue
ENEMY_TOUCH_COOLDOWN = 0.6
WALL_BOUNCE = 0.75         # cuanta velocidad conserva al rebotar
ENEMY_KNOCKBACK = 150.0    # empujon cuando le pegas
ENEMY_STUN_TIME = 0.25
ENEMY_FLASH_TIME = 0.12
ENEMY_SPAWN_TIME = 0.8     # aparece transparente y no hace dano
ENEMY_ANIM_FRAME = 0.15

SEPARATION = 10.0          # distancia a la que se empujan entre si
SEPARATION_FORCE = 140.0

# ---------------------------------------------------------------
# Tiempos
# ---------------------------------------------------------------

BANNER_TIME = 3.0          # cuanto se ve "Oleada completada"
COLLECT_TIMEOUT = 7.0      # maximo esperando que juntes las monedas
MAX_COIN_ITEMS = 30        # monedas dibujadas (cada una vale mas)


# ---------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------

_images = {}
_fonts = {}


def load_image(path, size=None):
    """Carga un PNG (cacheado). None si no existe."""

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
    """Texto con sombra. anchor: center=, midtop=, topleft=, midleft="""

    font = get_font(size)

    shadow = font.render(text, True, (0, 0, 0))
    label = font.render(text, True, color)

    rect = label.get_rect(**anchor)

    screen.blit(shadow, rect.move(2, 2))
    screen.blit(label, rect)

    return rect


def quantize_radius(radius):
    """Radio de luz en pasos de 8 px (minimo 8): la luz se cachea por
    radio, asi no se crea una superficie nueva en cada frame."""

    return max(8, int(round(radius / 8.0)) * 8)


def enemies_for_wave(wave):

    if wave in WAVE_ENEMIES:
        return WAVE_ENEMIES[wave]

    last = max(WAVE_ENEMIES)

    return min(
        ENEMIES_MAX,
        WAVE_ENEMIES[last] + ENEMIES_STEP * (wave - last)
    )


def base_reward(wave):

    if wave in WAVE_REWARDS:
        return WAVE_REWARDS[wave]

    last = max(WAVE_REWARDS)

    return WAVE_REWARDS[last] + REWARD_STEP * (wave - last)


# ---------------------------------------------------------------
# Imagenes del enemigo (se cargan una sola vez para todos)
# ---------------------------------------------------------------

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
        """Frames y sprite de golpe ya escalados al zoom actual."""

        if self._zoom != zoom:

            px = max(1, int(ENEMY_DRAW_SIZE * zoom))

            self._scaled = [
                pygame.transform.scale(f, (px, px)) for f in self.frames
            ]

            self._scaled_hit = pygame.transform.scale(self.hit, (px, px))

            self._zoom = zoom

        return self._scaled, self._scaled_hit


class Enemy:
    """Persigue al jugador, le pega al chocarlo y rebota por toda la
    sala (paredes y obstaculos). Es un objetivo mas de los golpes del
    fosforo (tiene .rect y .take_damage)."""

    def __init__(self, x, y, hp, max_speed, spawn_delay=0.0):

        self.rect = pygame.Rect(0, 0, *ENEMY_HITBOX)
        self.rect.center = (round(x), round(y))

        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2()

        self.hp = hp
        self.max_hp = hp
        self.max_speed = max_speed

        self.flash = 0.0
        self.stun = 0.0
        self.recover = 0.0
        self.touch_cd = 0.0

        # Mientras es > 0 el enemigo esta apareciendo: no se mueve,
        # no hace dano y tampoco se lo puede golpear
        self.spawn_t = ENEMY_SPAWN_TIME + spawn_delay

        self.anim_t = random.uniform(0, 1)
        self.last_target = pygame.Vector2(x, y)

    @property
    def dead(self):

        return self.hp <= 0

    @property
    def spawning(self):

        return self.spawn_t > 0

    # ---------- golpes ----------

    def take_damage(self, amount):

        if self.spawning or self.dead:
            return 0

        self.hp -= amount
        self.flash = ENEMY_FLASH_TIME
        self.stun = ENEMY_STUN_TIME

        # Empujon hacia atras, lejos del jugador
        away = self.pos - self.last_target

        if away.length_squared() > 0.01:
            self.vel = away.normalize() * ENEMY_KNOCKBACK

        return amount

    def bounce_from(self, point):
        """Rebota despues de chocar al jugador."""

        away = self.pos - pygame.Vector2(point)

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        self.vel = away.normalize() * ENEMY_BOUNCE_SPEED
        self.recover = ENEMY_RECOVER_TIME
        self.touch_cd = ENEMY_TOUCH_COOLDOWN

    # ---------- movimiento ----------

    def update(self, dt, target, collision_map, others):

        self.last_target = pygame.Vector2(target)
        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt

            return

        if self.stun > 0:
            self.stun = max(0.0, self.stun - dt)

        if self.recover > 0:
            self.recover = max(0.0, self.recover - dt)

        # Ir directo hacia el jugador (acelerando, asi puede girar)
        to_target = pygame.Vector2(target) - self.pos
        dist = to_target.length()

        if dist > 0.01 and self.stun <= 0:

            push = ENEMY_ACCEL * (0.25 if self.recover > 0 else 1.0)

            self.vel += to_target / dist * push * dt

        # Separarse de los otros enemigos
        for other in others:

            if other is self or other.spawning:
                continue

            away = self.pos - other.pos
            length = away.length()

            if 0 < length < SEPARATION:
                self.vel += away / length * SEPARATION_FORCE * dt

        self.vel *= max(0.0, 1.0 - ENEMY_DRAG * dt)

        # Velocidad maxima (el rebote y el golpe pueden pasarla un rato)
        if self.stun > 0 or self.recover > 0:
            limit = ENEMY_BOUNCE_SPEED * 1.2
        else:
            limit = self.max_speed

        speed = self.vel.length()

        if speed > limit:
            self.vel *= limit / speed

        self._move(dt, collision_map)

    def _free(self, rect, collision_map):
        """True si el enemigo puede estar en `rect`: dentro de la sala
        (no se escapa por el pasillo) y sin tocar paredes ni bloques."""

        return ROOM.contains(rect) and collision_map.can_move(rect)

    def _move(self, dt, collision_map):

        # Eje X
        nx = self.pos.x + self.vel.x * dt
        test = self.rect.copy()
        test.centerx = round(nx)

        if self._free(test, collision_map):

            self.pos.x = nx
            self.rect.centerx = test.centerx

        else:
            self.vel.x = (
                -self.vel.x * WALL_BOUNCE if abs(self.vel.x) > 25 else 0.0
            )

        # Eje Y
        ny = self.pos.y + self.vel.y * dt
        test = self.rect.copy()
        test.centery = round(ny)

        if self._free(test, collision_map):

            self.pos.y = ny
            self.rect.centery = test.centery

        else:
            self.vel.y = (
                -self.vel.y * WALL_BOUNCE if abs(self.vel.y) > 25 else 0.0
            )

    # ---------- dibujo ----------

    def draw(self, screen, camera, art):

        frames, hit = art.get(camera.zoom)

        if self.flash > 0:

            img = hit

        else:

            index = int(self.anim_t / ENEMY_ANIM_FRAME) % len(frames)
            img = frames[index]

            # Herido = mas oscuro (asi se nota sin barras de vida)
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

        # Sombra
        shadow = pygame.Surface(
            (int(dest.width * 1.3), int(dest.height * 0.6)),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx,
                    dest.bottom + int(2 * camera.zoom)
                )
            )
        )


# ---------------------------------------------------------------
# Cofre del premio
# ---------------------------------------------------------------

class RewardChest:
    """Aparece al ganar la oleada, brilla cada vez mas y explota."""

    APPEAR_TIME = 0.6
    GLOW_TIME = 2.4
    OPEN_TIME = 0.5
    SIZE = 20                 # unidades del mundo (igual que los cofres)

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.t = 0.0
        self.phase = "appear"      # appear -> glow -> open
        self.done = False

        self._glow_cache = {}

    # ---------- logica ----------

    def update(self, dt):
        """Devuelve True justo el frame en que explota."""

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
        """0 a 1: cuanto falta para que explote."""

        if self.phase == "appear":
            return 0.0

        if self.phase == "open":
            return 1.0

        return min(1.0, (self.t - self.APPEAR_TIME) / self.GLOW_TIME)

    def light(self):
        """(x, y, radio en pixeles de pantalla) para iluminar."""

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

    # ---------- dibujo ----------

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
        """El cofre en si (va debajo de la oscuridad)."""

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

            # Cae desde arriba con rebotito
            k = min(1.0, self.t / self.APPEAR_TIME)
            fall = (1 - k) ** 2

            dy = -int(fall * 26 * camera.zoom)

        elif self.phase == "glow":

            # Tiembla cada vez mas fuerte antes de explotar
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
        """El brillo (va encima de la oscuridad)."""

        if self.phase == "appear":
            return

        k = self.glow_k

        radius = (20 + 30 * k + 4 * math.sin(self.t * 10)) * camera.zoom

        # Por pasos de 16 px, asi se reutilizan las superficies
        radius = max(16, int(round(radius / 16.0)) * 16)

        glow = self._glow_surface(radius)

        cx, cy = self._center_px(camera)

        screen.blit(glow, glow.get_rect(center=(cx, cy)))


# ---------------------------------------------------------------
# La sala
# ---------------------------------------------------------------

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

    def __init__(self, screen_size):

        self.size = screen_size

        self.state = self.IDLE

        # True = puede abrir el menu al pisar la sala. Se desarma al
        # abrirlo y se arma de nuevo cuando el jugador sale.
        self.armed = True

        self.wave = 1
        self.mode = None            # "escape" / "noescape"

        self.enemies = []
        self.art = EnemyArt()

        self.chest = None
        self.reward = 0
        self.reward_coins = []

        self.banner_t = 0.0
        self.collect_t = 0.0
        self.last_death = None
        self.gate_on = False

        self.particles = []
        self.ring_t = None
        self.ring_pos = (0, 0)
        self.boom_light_t = None

        self._gate_time = 0.0

        # ---------- imagenes ----------

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

        self.coin_icon = load_image(HUD_DIR / "icon_moneda.png", (22, 22))

        self.btn_imgs = {}

        for key, name in self.BUTTON_FILES.items():

            self.btn_imgs[key] = (
                load_image(COMBAT_DIR / f"{name}.png", self.BUTTON_SIZE),
                load_image(COMBAT_DIR / f"{name}_hover.png", self.BUTTON_SIZE),
            )

        # ---------- posiciones del menu ----------

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

    # ---------- estado ----------

    @property
    def menu_open(self):

        return self.state == self.MENU

    @property
    def active(self):

        return self.state in (self.WAVE, self.CLEAR, self.COLLECT)

    @property
    def current_reward(self):
        """Premio de la oleada actual (con el X2 si es sin escape)."""

        mult = NO_ESCAPE_MULT if self.mode == "noescape" else 1

        return base_reward(self.wave) * mult

    def targets(self):
        """Lo que el fosforo puede golpear."""

        return [e for e in self.enemies if not e.spawning and not e.dead]

    def light_sources(self):
        """Luces extra (el cofre ilumina y la explosion tambien)."""

        sources = []

        if self.chest is not None and not self.chest.done:
            sources.append(self.chest.light())

        if self.boom_light_t is not None:

            k = self.boom_light_t / 0.7

            sources.append((
                self.ring_pos[0], self.ring_pos[1],
                quantize_radius(120 + 200 * (1 - k))
            ))

        return sources

    # ---------- menu ----------

    def _open_menu(self, game):

        self.state = self.MENU
        self.armed = False
        self.banner_t = 0.0

        game.melee.cancel()

    def update_menu(self, dt):
        """El juego esta en pausa mientras el menu esta abierto."""

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

        game.show_message(f"Oleada {self.wave}")

    # ---------- barrera ----------

    def _close_gate(self, game):

        if not self.gate_on:

            game.collision_map.obstacles.append(GATE.copy())
            self.gate_on = True

    def _open_gate(self, game):

        if self.gate_on:

            obstacles = game.collision_map.obstacles

            if GATE in obstacles:
                obstacles.remove(GATE)

            self.gate_on = False

    # ---------- oleadas ----------

    def _spawn_wave(self, game):

        count = enemies_for_wave(self.wave)

        hp = min(ENEMY_HP_MAX, ENEMY_HP_BASE + self.wave)

        speed = min(
            ENEMY_SPEED_MAX,
            ENEMY_SPEED_BASE + ENEMY_SPEED_STEP * self.wave
        )

        cmap = game.collision_map
        player_pos = pygame.Vector2(game.player.rect.center)

        corners = [
            (ROOM.left + 40, ROOM.top + 30),
            (ROOM.right - 40, ROOM.top + 30),
            (ROOM.left + 40, ROOM.bottom - 30),
            (ROOM.right - 40, ROOM.bottom - 30),
        ]

        self.enemies = []

        for i in range(count):

            pos = None

            for _ in range(80):

                x = random.randint(ROOM.left + 16, ROOM.right - 16)
                y = random.randint(ROOM.top + 16, ROOM.bottom - 16)

                probe = pygame.Rect(0, 0, *ENEMY_HITBOX)
                probe.center = (x, y)

                if pygame.Vector2(x, y).distance_to(player_pos) < 110:
                    continue

                if not (ROOM.contains(probe) and cmap.can_move(probe)):
                    continue

                if any(
                    pygame.Vector2(x, y).distance_to(e.pos) < 18
                    for e in self.enemies
                ):
                    continue

                pos = (x, y)

                break

            if pos is None:
                pos = corners[i % len(corners)]

            self.enemies.append(
                Enemy(pos[0], pos[1], hp, speed, spawn_delay=i * 0.15)
            )

    def _wave_cleared(self, game):

        pos = self.last_death or ROOM.center

        self.reward = self.current_reward
        self.chest = RewardChest(pos[0], pos[1])
        self.state = self.CLEAR

        # Ya no quedan enemigos: se puede salir
        self._open_gate(game)

    def _explode(self, game):
        """El cofre explota y tira las monedas del premio."""

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

        # Monedas: como mucho MAX_COIN_ITEMS dibujadas, cada una con
        # su parte del premio (la suma da exacto el premio)
        items = max(1, min(self.reward, MAX_COIN_ITEMS))

        base, extra = divmod(self.reward, items)

        self.reward_coins = []

        for n in range(items):

            coin = WorldItem("moneda", cx, cy)

            coin.value = base + (1 if n < extra else 0)

            target = self._coin_target(game, cx, cy)

            coin.start_fly((cx, cy), target, delay=n * 0.025, height=18)

            self.reward_coins.append(coin)

        game.world_items.extend(self.reward_coins)

        self.state = self.COLLECT
        self.collect_t = 0.0
        self.banner_t = BANNER_TIME

        # La siguiente oleada ya queda lista
        self.wave += 1

    @staticmethod
    def _coin_target(game, cx, cy):

        for _ in range(30):

            angle = random.uniform(0, math.tau)
            dist = random.uniform(14, 46)

            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist

            if ROOM.collidepoint(x, y) and game.collision_map.point_is_walkable(x, y):
                return (x, y)

        return (cx, cy + 14)

    def _coins_left(self, game):

        return [c for c in self.reward_coins if c in game.world_items]

    def _credit_leftover(self, game):
        """Las monedas que quedaron en el piso se suman solas."""

        for coin in self._coins_left(game):

            game.world_items.remove(coin)
            game.coins += getattr(coin, "value", 1)

        self.reward_coins = []

    # ---------- salir / terminar ----------

    def _teleport_out(self, game):

        p = game.player

        p.rect.center = EXIT_POS
        p.image_rect.midbottom = (p.rect.centerx, p.rect.bottom + 3)

        p.kb_vel = pygame.Vector2()

        game.camera.update(p)
        game.melee.cancel()

    def _end_run(self, game):

        self._credit_leftover(game)
        self._open_gate(game)

        self.enemies = []
        self.chest = None
        self.reward = 0
        self.wave = 1
        self.mode = None
        self.banner_t = 0.0
        self.state = self.IDLE

    def _leave(self, game):
        """Boton Salir (o ESC en el menu)."""

        self._end_run(game)
        self._teleport_out(game)

    def _player_died(self, game):

        if self.mode == "noescape":

            # Sin escape: perdes de verdad
            self._end_run(game)

            game.state = "dying"
            game.fade_alpha = 0

            return

        # Con escape: te sacan de la sala
        self._end_run(game)
        self._teleport_out(game)

        if game.has_match:
            game.vida = max(game.vida, ESCAPE_REVIVE_LIFE)

        game.show_message("Te sacaron de la sala. Perdiste la oleada")

    # ---------- update ----------

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

        self._gate_time += dt

    def update(self, game, dt):
        """Se llama una vez por frame con el juego en marcha."""

        self._update_fx(dt)

        p = game.player

        if self.state == self.IDLE:

            center = p.rect.center

            if self.armed and TRIGGER.collidepoint(center):
                self._open_menu(game)

            elif not self.armed and not ROOM.collidepoint(center):
                self.armed = True

            return

        if self.state == self.MENU:
            return

        if self.banner_t > 0:
            self.banner_t = max(0.0, self.banner_t - dt)

        # Con escape podes irte caminando
        if not ROOM.collidepoint(p.rect.center):

            if self.state == self.WAVE:

                game.show_message("Saliste de la sala. Oleada cancelada")

            elif self.state == self.CLEAR:

                # Se va antes de la explosion: el premio se cobra igual
                game.coins += self.reward

                game.show_message(f"+{self.reward} monedas")

            self._end_run(game)

            return

        if self.state == self.WAVE:
            self._update_wave(game, dt)

        elif self.state == self.CLEAR:

            if self.chest.update(dt):
                self._explode(game)

        elif self.state == self.COLLECT:
            self._update_collect(game, dt)

    def _update_wave(self, game, dt):

        p = game.player
        target = p.rect.center

        for enemy in self.enemies:
            enemy.update(dt, target, game.collision_map, self.enemies)

        # Choque con el jugador
        body = pygame.Rect(0, 0, 10, 16)
        body.midbottom = (p.rect.centerx, p.rect.bottom)

        damage = min(
            ENEMY_DAMAGE_MAX,
            ENEMY_DAMAGE + ENEMY_DAMAGE_STEP * (self.wave - 1)
        )

        for enemy in self.enemies:

            if enemy.spawning or enemy.touch_cd > 0 or enemy.dead:
                continue

            if enemy.rect.colliderect(body):

                if p.hurt(enemy.pos):
                    game.vida -= damage

                enemy.bounce_from(body.center)

        # Los que murieron (los golpes ya se aplicaron antes)
        for enemy in self.enemies:

            if enemy.dead:

                self.last_death = (enemy.pos.x, enemy.pos.y)

                self._death_puff(enemy.pos)

        self.enemies = [e for e in self.enemies if not e.dead]

        if game.vida <= 0 or not game.has_match:

            self._player_died(game)

            return

        if not self.enemies:
            self._wave_cleared(game)

    def _death_puff(self, pos):

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

        if (not left and self.collect_t > 1.0) or (
            self.collect_t > COLLECT_TIMEOUT
        ):

            self.chest = None
            self._open_menu(game)

    # ---------- dibujo ----------

    def draw_world(self, screen, camera):
        """Enemigos, cofre y barrera (debajo de la oscuridad)."""

        for enemy in self.enemies:
            enemy.draw(screen, camera, self.art)

        if self.chest is not None and not self.chest.done:
            self.chest.draw(screen, camera)

        if self.gate_on:

            rect = camera.apply(GATE)

            pulse = 0.5 + 0.5 * math.sin(self._gate_time * 6)

            bar = pygame.Surface(rect.size, pygame.SRCALPHA)
            bar.fill((255, 60, 50, int(90 + 90 * pulse)))

            screen.blit(bar, rect)

    def draw_fx(self, screen, camera):
        """Brillo, explosion y chispas (encima de la oscuridad)."""

        if self.chest is not None and not self.chest.done:
            self.chest.draw_glow(screen, camera)

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

    def draw_hud(self, screen):
        """Cartel de oleada arriba a la izquierda + aviso de victoria."""

        if not self.active:
            return

        # ---------- cartel de oleada ----------

        rect = pygame.Rect(18, 18, 180, 40)

        if self.hud_img is not None:

            screen.blit(self.hud_img, rect)

        else:

            pygame.draw.rect(screen, (138, 146, 158), rect, border_radius=8)
            pygame.draw.rect(screen, (84, 92, 104), rect, 3, border_radius=8)

        # En CLEAR todavia no se sumo la oleada; en COLLECT ya si
        number = self.wave - 1 if self.state == self.COLLECT else self.wave

        draw_text(
            screen, f"Oleada {number}", 28, (255, 255, 255),
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

        # ---------- oleada completada ----------

        if self.banner_t > 0:
            self._draw_banner(screen)

    def _draw_banner(self, screen):

        w, h = self.size

        alpha = int(255 * min(1.0, self.banner_t / 0.5))

        rect = pygame.Rect(0, 0, 420, 200)
        rect.center = (w // 2, int(h * 0.30))

        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        local = layer.get_rect()

        if self.banner_img is not None:

            layer.blit(self.banner_img, (0, 0))

        else:

            pygame.draw.rect(layer, (30, 30, 38, 225), local, border_radius=14)
            pygame.draw.rect(layer, (200, 200, 210), local, 3, border_radius=14)

            draw_text(
                layer, "Oleada completada!", 40, (255, 240, 170),
                center=(local.centerx, 56)
            )

        draw_text(
            layer, f"+{self.reward}", 64, (255, 225, 120),
            center=(local.centerx + 14, local.centery + 28)
        )

        if self.coin_icon is not None:

            coin = pygame.transform.smoothscale(self.coin_icon, (40, 40))

            layer.blit(coin, coin.get_rect(center=(local.centerx - 62, local.centery + 28)))

        layer.set_alpha(alpha)

        screen.blit(layer, rect)

    def draw_menu(self, screen, game):
        """Pantalla transparente con Salir / Jugar con escape / Jugar
        sin escape."""

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
            screen, "Sala de combate", 36, (255, 240, 200),
            center=(self.panel_rect.centerx, self.panel_rect.top + 26)
        )

        reward = base_reward(self.wave)

        draw_text(
            screen,
            f"Oleada {self.wave}   Premio: {reward}   "
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

            # Sin luz no se puede pelear
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