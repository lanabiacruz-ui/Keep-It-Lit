"""Sala de combate (la sala grande de la derecha).

Al entrar aparece un menu transparente: Salir / Jugar con escape /
Jugar sin escape (premio X2). Despues vienen las oleadas:

  - Con escape: podes irte caminando de la sala (cancela la oleada).
  - Sin escape: la entrada se bloquea mientras pelean. El premio vale
    el doble.
  - En los dos modos, si te quedas sin vida perdes la partida de verdad.

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

# Que trae cada oleada: (pinos, troncos). Los pinos rebotan y te
# pegan al chocarte; los troncos te siguen de lejos y disparan 3 bolas que rebotan.
# Despues de la ultima definida sube PINOS_STEP pinos y TRONCOS_STEP
# troncos por oleada, sin pasar de ENEMIES_MAX en total.
WAVE_COMPOSITION = {
    1: (1, 0, 0),
    2: (4, 0, 0),
    3: (5, 1, 0),
    4: (5, 2, 0),
    5: (4, 4, 0),

    # Oleada 6
    6: (4, 7, 3),

    # Oleada 7
    7: (10, 7, 6),
}
PINOS_STEP = 1
TRONCOS_STEP = 1
TRONCOS_MAX = 8
ENEMIES_MAX = 32
MOSQUITOS_STEP = 1   # mosquitos que se suman por oleada despues de la ultima definida
MOSQUITOS_MAX = 20

# Oleada de PRUEBA (solo mosquitos). La usa la partida "Prueba mosquitos".
# Para cambiar cuantos salen, cambia el 3. Se puede borrar cuando termines.
MOSQUITO_TEST_WAVE = 99
MOSQUITO_TEST_COUNT = 3

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
# Piña
# ---------------------------------------------------------------

ENEMY_DRAW_SIZE = 14       # tamano dibujado (unidades del mundo)
ENEMY_HITBOX = (12, 10)    # lo que choca y lo que golpea el fosforo

ENEMY_BALL_MULT = 1.8      # velocidad de la bola = velocidad de la oleada x esto
ENEMY_ACCEL = 320.0        # que tan rapido vuelve a su velocidad tras un empujon
ENEMY_BOUNCE_AIM = 0.85    # 0 = rebota normal, 1 = sale derecho hacia el jugador
ENEMY_BOUNCE_JITTER = 6.0  # grados al azar en cada rebote (para que no sea predecible)
ENEMY_DRAG = 1.6           # frenado del empujon cuando le pegas
ENEMY_HIT_BOUNCE = 1.2     # velocidad con la que sale rebotado tras chocarte (x bola)
ENEMY_TOUCH_COOLDOWN = 0.6
WALL_BOUNCE = 1.0          # cuanta velocidad conserva al rebotar (1 = toda)
ENEMY_KNOCKBACK = 150.0    # empujon cuando le pegas
ENEMY_STUN_TIME = 0.25
ENEMY_FLASH_TIME = 0.12
ENEMY_SPAWN_TIME = 0.8     # aparece transparente y no hace daño
ENEMY_ANIM_FRAME = 0.15
ENEMY_SPIN_RATE = 2.0      # cuanto gira mientras rueda (grados por unidad recorrida)
ENEMY_HOP_DIST = 38.0      # cada cuantas unidades recorridas da un saltito
ENEMY_HOP_HEIGHT = 3.0     # altura del saltito (unidades del mundo)

# ---------------------------------------------------------------
# Tronco (dispara 3 bolas que rebotan)
# ---------------------------------------------------------------

TRONCO_HITBOX = (14, 12)
TRONCO_DRAW_SIZE = 16      # tamano dibujado (unidades del mundo)
TRONCO_HP_EXTRA = 0        # vida = la del pino + esto
TRONCO_FIRST_DELAY = (2.0, 3.0)  # primera espera (al azar, para que no disparen todos juntos)
TRONCO_WINDUP = 1.0        # cuanto tarda quieto apuntandote antes de soltar las bolas
TRONCO_SHOOT_TIME = 0.45   # duracion de la animacion de disparo
TRONCO_COOLDOWN = 8.0      # segundos entre un disparo y el siguiente
TRONCO_HIT_PAUSE = 1.5     # si le pegas mientras carga, se le corta y espera esto
TRONCO_SHOTS = 3           # bolas por disparo
TRONCO_SPREAD = 24.0       # grados entre una bola y la siguiente
TRONCO_LEAD = 0.45         # cuanto adelanta la punteria hacia donde te estas moviendo (seg)
TRONCO_ANIM_FRAME = 0.12

# Movimiento del tronco: te sigue pero manteniendo distancia y sin
# meterse en tu luz (asi no lo ves ni lo alcanzas a pegar).
TRONCO_SPEED = 70.0        # unidades del mundo por segundo (el jugador va a 95)
TRONCO_KEEP_DIST = 60.0    # distancia minima que intenta mantener
TRONCO_MAX_DIST = 120.0    # distancia maxima a la que se queda (si tu luz es enorme)
TRONCO_LIGHT_MARGIN = 14.0 # cuanto afuera del borde de tu luz se queda
TRONCO_BAND = 8.0          # tolerancia: dentro de esta franja no se mueve
TRONCO_FIRE_EXTRA = 10.0   # puede empezar a cargar si esta a ideal + BAND + esto

SHOT_SPEED = 95.0          # unidades del mundo por segundo
SHOT_HITBOX = 6
SHOT_DRAW_SIZE = 8
SHOT_BOUNCES = 2           # cuantas veces rebota (al tercer choque desaparece)
SHOT_LIFE = 7.0            # maximo de segundos en el aire
SHOT_DAMAGE_MULT = 4.5     # x el dano de un choque de pino

# ---------------------------------------------------------------
# Mosquito
# ---------------------------------------------------------------

MOSQUITO_HP = 2   # golpes que aguanta (el fosforo y la vela pegan 1 por golpe)
MOSQUITO_HITBOX = (9, 7)
MOSQUITO_DRAW_SIZE = 13

# Vuelo libre por la sala
MOSQUITO_WANDER_SPEED = 45.0     # velocidad volando libre
MOSQUITO_TURN_TIME = (0.8, 2.2)  # cada cuanto cambia un poco de rumbo

# Alerta en el HUD: aparece cuando esta a esta distancia EXTRA del borde
# de tu luz (o sea, antes de que lo toque tu luz)
MOSQUITO_ALERT_MARGIN = 90.0

# Ataque: cuando tu luz lo toca va directo hacia vos y se pega
MOSQUITO_ATTACK_SPEED = 280.0
MOSQUITO_ATTACK_ACCEL = 900.0
MOSQUITO_ATTACH_DIST = 10.0

# Ciclo (segundos)
MOSQUITO_ATTACH_TIME = 60.0      # pegado: te chupa 1 minuto y se suelta
MOSQUITO_REST_TIME = 60.0        # despues de soltarte, a este tiempo vuelve a atacar
MOSQUITO_FLEE_TIME = 8.0         # apenas te suelta, intenta irse (se aleja rapido)
MOSQUITO_FLEE_SPEED = 85.0

# Daño
# 0.02 = 2% de la vida de la luz
MOSQUITO_DAMAGE = 0.02
MOSQUITO_DAMAGE_INTERVAL = 1.0

# Animación
MOSQUITO_ANIM_FRAME = 0.10
MOSQUITO_FLASH_TIME = 0.10
MOSQUITO_SPAWN_TIME = 0.8
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


def wave_composition(wave):
    """(pinos, troncos, mosquitos) de una oleada."""
    if wave == MOSQUITO_TEST_WAVE:
        return 0, 0, MOSQUITO_TEST_COUNT
    if wave in WAVE_COMPOSITION:
        return WAVE_COMPOSITION[wave]
    last = max(WAVE_COMPOSITION)
    pinos, troncos, mosquitos = WAVE_COMPOSITION[last]
    extra = max(0, wave - last)
    pinos += PINOS_STEP * extra
    troncos = min(TRONCOS_MAX, troncos + TRONCOS_STEP * extra)
    mosquitos = min(MOSQUITOS_MAX, mosquitos + MOSQUITOS_STEP * extra)
    total = pinos + troncos + mosquitos
    if total > ENEMIES_MAX:
        mosquitos = max(0, mosquitos - (total - ENEMIES_MAX))
    return pinos, troncos, mosquitos


def enemies_for_wave(wave):
    """Cuantos enemigos trae la oleada en total."""

    return sum(wave_composition(wave))


def base_reward(wave):

    if wave in WAVE_REWARDS:
        return WAVE_REWARDS[wave]

    last = max(WAVE_REWARDS)

    return WAVE_REWARDS[last] + REWARD_STEP * (wave - last)

# ---------------------------------------------------------------
# Mosquito - sprites
# ---------------------------------------------------------------

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

        # cuerpo
        pygame.draw.ellipse(
            surf,
            (45, 35, 40),
            (23, 19, 14, 25)
        )

        # abdomen
        pygame.draw.ellipse(
            surf,
            (180, 45, 55),
            (25, 31, 10, 13)
        )

        # alas
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

        # ojos
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

        # aguijón
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

    # fixed: no se mueve solo (los otros rebotan contra el)
    # contact_damage: te saca vida al tocarte
    fixed = False
    contact_damage = True

    def __init__(self, x, y, hp, max_speed, spawn_delay=0.0):

        self.rect = pygame.Rect(0, 0, *ENEMY_HITBOX)
        self.rect.center = (round(x), round(y))

        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2()

        self.hp = hp
        self.max_hp = hp
        self.max_speed = max_speed

        # Velocidad de "bola": rebota siempre a este ritmo
        self.ball_speed = max_speed * ENEMY_BALL_MULT

        self.flash = 0.0
        self.stun = 0.0
        self.touch_cd = 0.0

        # Mientras es > 0 el enemigo esta apareciendo: no se mueve,
        # no hace dano y tampoco se lo puede golpear
        self.spawn_t = ENEMY_SPAWN_TIME + spawn_delay

        self.anim_t = random.uniform(0, 1)
        self.last_target = pygame.Vector2(x, y)

        # Para dibujarlo rodando y saltando como una pelota
        self.spin = random.uniform(0, 360)
        self.hop_t = random.uniform(0, 1)

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
        """Sale rebotado despues de chocar al jugador."""

        away = self.pos - pygame.Vector2(point)

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        self.vel = away.normalize() * self.ball_speed * ENEMY_HIT_BOUNCE
        self.touch_cd = ENEMY_TOUCH_COOLDOWN

    # ---------- movimiento ----------

    def update(self, dt, target, collision_map, others=None):
        """Es una pelota: NO camina ni gira hacia el jugador. Va en
        linea recta y solo cambia de direccion al rebotar (contra las
        paredes, los bloques del mapa o otro enemigo). En cada rebote
        sale apuntando hacia donde esta el jugador, asi siempre rebota
        cerca suyo para pegarle."""

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

            # Empujon del golpe: se frena solo, sin controlarse
            self.stun = max(0.0, self.stun - dt)
            self.vel *= max(0.0, 1.0 - ENEMY_DRAG * dt)

        else:

            self._keep_speed(dt, to_target)

        before = self.pos.copy()

        hit_x, hit_y = self._move(dt, collision_map)

        if hit_x or hit_y:
            self.aim_after_bounce(to_target, hit_x, hit_y)

        # Rueda y salta segun lo que recorrio (no camina)
        moved = self.pos.distance_to(before)
        side = 1.0 if self.vel.x >= 0 else -1.0

        self.spin = (self.spin + side * moved * ENEMY_SPIN_RATE) % 360.0
        self.hop_t = (self.hop_t + moved / ENEMY_HOP_DIST) % 1.0

    def _keep_speed(self, dt, to_target):
        """Mantiene la velocidad de bola SIN cambiar la direccion."""

        speed = self.vel.length()

        # Recien aparecido (o frenado del todo): sale disparado hacia
        # el jugador, y de ahi en adelante solo rebota
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
        """Despues de rebotar, la direccion del rebote se acerca a la
        direccion hacia el jugador (sin volver a meterse en la pared
        que acaba de tocar)."""

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

        # Nunca apuntar de nuevo contra la pared que acaba de tocar
        if hit_x and mix.x * current.x < 0:
            mix.x = current.x * 0.3

        if hit_y and mix.y * current.y < 0:
            mix.y = current.y * 0.3

        # Ni contra el enemigo con el que acaba de chocar
        if away is not None and mix.dot(away) < 0:
            mix = mix - away * mix.dot(away) + away * 0.3

        if mix.length_squared() < 0.0001:
            return

        self.vel = mix.normalize() * speed

    def _free(self, rect, collision_map):
        """True si el enemigo puede estar en `rect`: dentro de la sala
        (no se escapa por el pasillo) y sin tocar paredes ni bloques."""

        return ROOM.contains(rect) and collision_map.can_move(rect)

    def _move(self, dt, collision_map):
        """Mueve al enemigo y rebota contra paredes y bloques del mapa.
        Devuelve (choco_en_x, choco_en_y)."""

        hit_x = False
        hit_y = False

        # Eje X
        nx = self.pos.x + self.vel.x * dt
        test = self.rect.copy()
        test.centerx = round(nx)

        if self._free(test, collision_map):

            self.pos.x = nx
            self.rect.centerx = test.centerx

        else:

            hit_x = True
            self.vel.x = -self.vel.x * WALL_BOUNCE

        # Eje Y
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
        """Mueve al enemigo `offset` (para separarlo de otro), solo si
        hay lugar. Prueba cada eje por separado."""

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


    # ---------- dibujo ----------

    def draw(self, screen, camera, art):

        frames, hit = art.get(camera.zoom)

        if self.flash > 0:

            img = hit

        else:

            # Sin animacion de caminar: es una pelota, usa un solo
            # cuadro y se lo hace rodar
            img = frames[0]

            # Herido = mas oscuro (asi se nota sin barras de vida)
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

        # Saltito (la sombra se queda en el piso)
        hop = 0
        if not self.spawning:
            hop = int(
                abs(math.sin(self.hop_t * math.pi))
                * ENEMY_HOP_HEIGHT * camera.zoom
            )

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
                center=(dest.centerx, dest.centery - hop)
            )
        )


def _overlap_depth(a, b):
    """Cuanto se pisan dos rects (para separarlos)."""

    overlap_x = min(a.rect.right, b.rect.right) - max(a.rect.left, b.rect.left)
    overlap_y = min(a.rect.bottom, b.rect.bottom) - max(a.rect.top, b.rect.top)

    return max(1.0, min(overlap_x, overlap_y))


def bounce_enemies(enemies, collision_map, target=None):
    """Choque entre enemigos: si se tocan, rebotan hacia otro lado y
    se separan para no quedar pegados. Los troncos no se mueven: el
    pino rebota contra ellos como contra una pared. Si se pasa `target`
    (posicion del jugador) cada uno se reorienta hacia el despues del
    choque."""

    live = [e for e in enemies if not e.spawning and not e.dead and not getattr(e, "attached", False)]

    for i, a in enumerate(live):

        for b in live[i + 1:]:

            if not a.rect.colliderect(b.rect):
                continue

            normal = b.pos - a.pos

            if normal.length_squared() < 0.01:
                normal = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            normal = normal.normalize()

            # Dos troncos: solo se separan
            if a.fixed and b.fixed:

                depth = _overlap_depth(a, b) / 2.0 + 1.0

                a.push(-normal * depth, collision_map)
                b.push(normal * depth, collision_map)

                continue

            # Un tronco y un pino: el pino rebota contra el tronco
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

            # Dos pinos: choque elastico entre iguales (intercambian la
            # velocidad que llevaban uno contra el otro)
            closing = (a.vel - b.vel).dot(normal)

            if closing > 0:

                a.vel -= normal * closing
                b.vel += normal * closing

                # Si quedaron casi quietos, se empujan igual
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

            # Separarlos para que no queden uno dentro del otro
            depth = _overlap_depth(a, b) / 2.0 + 1.0

            a.push(-normal * depth, collision_map)
            b.push(normal * depth, collision_map)


# ---------------------------------------------------------------
# Imagenes del tronco y de la bola (opcionales: si falta alguna se
# dibuja un reemplazo)
# ---------------------------------------------------------------

def load_strip(path):
    """Tira horizontal de cuadros cuadrados (ancho de cuadro = alto).
    Devuelve la lista de cuadros, o [] si no existe el archivo."""

    sheet = load_image(path)

    if sheet is None or sheet.get_height() <= 0:
        return []

    fw = sheet.get_height()

    return [
        sheet.subsurface((i * fw, 0, fw, fw)).copy()
        for i in range(max(1, sheet.get_width() // fw))
    ]

class Mosquito(Enemy):
    """Ciclo: vuela tranquilo -> la luz lo toca y va directo al jugador ->
    se pega 1 minuto -> se suelta e intenta irse -> a los 60 s vuelve a
    chuparte (sin necesitar la luz) -> y asi."""

    fixed = False
    contact_damage = False

    def __init__(self, x, y, hp, spawn_delay=0.0):

        super().__init__(x, y, hp, MOSQUITO_ATTACK_SPEED, spawn_delay)

        self.rect = pygame.Rect(0, 0, *MOSQUITO_HITBOX)
        self.rect.center = (round(x), round(y))

        # "wander" = vuela tranquilo esperando que lo toque la luz
        # "attack" = va directo al jugador
        # "leave"  = ya te solto: se va y descansa hasta volver
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

        # True si vuelve solo (no lo toco la luz)
        self.returning = False

        # True mientras esta cerca del jugador y viene a chuparlo pero
        # todavia no se pego (el HUD muestra la advertencia)
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

        # Un mosquito pegado NO puede recibir ataques
        if self.spawning or self.dead or self.attached:
            return 0

        self.hp -= amount
        self.flash = MOSQUITO_FLASH_TIME

        # Si todavia no te chupo y lo golpean, ataca. Si ya se estaba
        # yendo, sigue yendose.
        if self.phase == "wander":
            self._start_attack()

        return amount

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

    def update(self, dt, target, collision_map, light_on, light_radius):

        target = pygame.Vector2(target)
        self.last_target = target.copy()

        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.spawning:
            self.spawn_t -= dt
            return

        # -------------------------------------------------------
        # PEGADO: te chupa 1 minuto y despues se suelta
        # -------------------------------------------------------

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

        # -------------------------------------------------------
        # ATAQUE: va directo al jugador y se pega
        # -------------------------------------------------------

        if self.phase == "attack":

            # Si vuelve solo, avisa en el HUD hasta que se pega
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

        # -------------------------------------------------------
        # SE FUE: se aleja y despues vuela tranquilo hasta que
        # pasa el minuto y vuelve a chuparte
        # -------------------------------------------------------

        if self.phase == "leave":

            self.alert = False
            self.rest_t -= dt

            if self.rest_t <= 0:

                self.returning = True
                self._start_attack()

                return

            if self.flee_t > 0:

                self.flee_t -= dt

                # Se aleja del jugador
                self.heading = -toward

                self._wander(dt, collision_map, MOSQUITO_FLEE_SPEED, turn=False)

            else:

                self._wander(dt, collision_map, MOSQUITO_WANDER_SPEED)

            return

        # -------------------------------------------------------
        # VUELO LIBRE: tranquilo por el mapa (no huye de la luz)
        # -------------------------------------------------------

        # Lo toca tu luz -> va directo hacia vos
        if light_on and dist <= light_radius:

            self.alert = False
            self._start_attack()

            return

        # Advertencia en el HUD: esta cerca pero todavia no lo toca la luz
        self.alert = light_on and dist <= light_radius + MOSQUITO_ALERT_MARGIN

        self._wander(dt, collision_map, MOSQUITO_WANDER_SPEED)

    def _wander(self, dt, collision_map, speed, turn=True):

        if turn:

            self.turn_t -= dt

            if self.turn_t <= 0:

                self.heading = self.heading.rotate(random.uniform(-70, 70))
                self.turn_t = random.uniform(*MOSQUITO_TURN_TIME)

        step = speed * dt

        # Si choca con algo, prueba otros rumbos hasta encontrar uno libre
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
    """Imagenes del tronco y de sus bolas (se cargan una sola vez).

      assets/maps/combate/tronco.png          56x56   (reposo)
      assets/maps/combate/tronco_carga.png    56x56 o tira de cuadros 56x56
      assets/maps/combate/tronco_disparo.png  tira de cuadros 56x56 (4)
      assets/maps/combate/tronco_golpe.png    56x56   (cuando le pegas)
      assets/maps/combate/bola_enemiga.png    24x24   (la bola)
    """

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

        # cuerpo del tronco
        pygame.draw.rect(surf, (118, 78, 44), (12, 8, 32, 44), border_radius=6)
        pygame.draw.rect(surf, (60, 36, 18), (12, 8, 32, 44), 3, border_radius=6)
        pygame.draw.line(surf, (80, 50, 26), (20, 14), (20, 46), 2)
        pygame.draw.line(surf, (80, 50, 26), (36, 14), (36, 46), 2)

        # ojos
        pygame.draw.circle(surf, (20, 10, 10), (22, 20), 3)
        pygame.draw.circle(surf, (20, 10, 10), (34, 20), 3)

        # boca: se abre y se pone naranja cuando carga o dispara
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
        """Todo ya escalado al zoom actual."""

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


# ---------------------------------------------------------------
# Bola que dispara el tronco
# ---------------------------------------------------------------

class Shot:
    """Bola que rebota SHOT_BOUNCES veces contra las paredes y los
    bloques del mapa; al siguiente choque desaparece. Si te toca, te
    saca vida y desaparece."""

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

        return ROOM.contains(rect) and collision_map.can_move(rect)

    def update(self, dt, collision_map):

        self.t += dt
        self.life -= dt

        if self.life <= 0:

            self.dead = True

            return

        hit = False

        # Eje X
        nx = self.pos.x + self.vel.x * dt
        test = self.rect.copy()
        test.centerx = round(nx)

        if self._free(test, collision_map):

            self.pos.x = nx
            self.rect.centerx = test.centerx

        else:

            hit = True
            self.vel.x = -self.vel.x

        # Eje Y
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

            # Los dos primeros choques rebotan, el tercero la rompe
            if self.bounces_left <= 0:
                self.dead = True
            else:
                self.bounces_left -= 1

    def draw(self, screen, camera, art):

        img = art.get(camera.zoom)["shot"]

        # Late un poco para que se note en la oscuridad
        pulse = 0.85 + 0.15 * math.sin(self.t * 14)

        size = max(1, int(img.get_width() * pulse))

        if size != img.get_width():
            img = pygame.transform.scale(img, (size, size))

        center = camera.apply(self.rect).center

        screen.blit(img, img.get_rect(center=center))


# ---------------------------------------------------------------
# Tronco
# ---------------------------------------------------------------

class Tronco(Enemy):
    """Te sigue por la sala pero manteniendo distancia: si te acercas
    retrocede, y se queda siempre afuera del borde de tu luz para que
    no lo veas. Cuando le toca disparar (cada TRONCO_COOLDOWN segundos)
    se queda quieto apuntandote y suelta 3 bolas abiertas en abanico
    hacia donde te podrias mover. Despues hace la animacion de disparo
    y vuelve a seguirte.
    Si le pegas mientras carga se le corta el disparo.
    No te hace dano al tocarlo."""

    # fixed: es el tipo que dispara (los pinos rebotan contra el)
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

        # Radio de la luz del jugador en unidades del mundo (lo setea
        # la arena en cada frame)
        self.light_radius = 0.0

        # Velocidad del jugador (para adelantar la punteria)
        self.target_vel = pygame.Vector2()
        self._prev_target = None

        self._shots = []

    # ---------- golpes ----------

    def take_damage(self, amount):

        result = super().take_damage(amount)

        # Le pegaste mientras cargaba: se le corta el disparo
        if result and self.phase == self.WINDUP:

            self.phase = self.IDLE
            self.phase_t = TRONCO_HIT_PAUSE

        return result

    # ---------- disparo ----------

    def take_shots(self):
        """Las bolas que acaba de soltar (y se vacia la lista)."""

        shots, self._shots = self._shots, []

        return shots

    def _fire(self, target):

        # Hacia donde vas a estar: la posicion de ahora mas lo que te
        # moves en TRONCO_LEAD segundos (sin salirse de la sala)
        aim = pygame.Vector2(target) + self.target_vel * TRONCO_LEAD

        aim.x = max(ROOM.left + 4, min(ROOM.right - 4, aim.x))
        aim.y = max(ROOM.top + 4, min(ROOM.bottom - 4, aim.y))

        direction = aim - self.pos

        if direction.length_squared() < 0.01:
            direction = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        base = pygame.Vector2(1, 0).angle_to(direction)

        for k in range(TRONCO_SHOTS):

            offset = (k - (TRONCO_SHOTS - 1) / 2.0) * TRONCO_SPREAD

            self._shots.append(Shot(self.pos, base + offset))

    # ---------- movimiento / estado ----------

    def _ideal_distance(self):
        """A que distancia del jugador quiere estar: afuera de su luz
        (para que no lo vea) y nunca mas cerca que TRONCO_KEEP_DIST."""

        want = max(
            TRONCO_KEEP_DIST, self.light_radius + TRONCO_LIGHT_MARGIN
        )

        return min(TRONCO_MAX_DIST, want)

    def _walk(self, dt, direction, collision_map):
        """Camina hacia `direction`. Si hay una pared o un bloque
        adelante, prueba rodearlo en diagonal o de costado."""

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

        # Velocidad del jugador, suavizada
        if self._prev_target is not None and dt > 0:

            raw = (target - self._prev_target) / dt

            self.target_vel += (raw - self.target_vel) * min(1.0, dt * 8.0)

        self._prev_target = target

        # Empujon del golpe: se desliza un poco y se frena
        if self.stun > 0:

            self.stun = max(0.0, self.stun - dt)
            self.vel *= max(0.0, 1.0 - 6.0 * dt)

            hit_x, hit_y = self._move(dt, collision_map)

            if hit_x or hit_y:
                self.vel = pygame.Vector2()

            return

        self.vel = pygame.Vector2()

        # ---- apuntando: quieto, mirandote hasta soltar las bolas ----
        if self.phase == self.WINDUP:

            self.phase_t -= dt

            if self.phase_t <= 0:

                self._fire(target)

                self.phase = self.SHOOT
                self.phase_t = TRONCO_SHOOT_TIME

            return

        # ---- animacion de disparo: tambien quieto ----
        if self.phase == self.SHOOT:

            self.phase_t -= dt

            if self.phase_t <= 0:

                self.phase = self.IDLE
                self.phase_t = TRONCO_COOLDOWN

            return

        # ---- siguiendote (esperando el proximo disparo) ----
        self.phase_t = max(0.0, self.phase_t - dt)

        to_player = target - self.pos
        dist = to_player.length()

        if dist < 0.01:
            to_player = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            dist = 0.01

        toward = to_player / dist

        ideal = self._ideal_distance()

        if dist > ideal + TRONCO_BAND:

            self._walk(dt, toward, collision_map)

        elif dist < ideal - TRONCO_BAND:

            # Muy cerca o adentro de la luz: se aleja
            self._walk(dt, -toward, collision_map)

        # Le toca disparar: cuando ya esta a buena distancia, frena
        # y empieza a apuntar
        if (
            self.phase_t <= 0
            and dist <= ideal + TRONCO_BAND + TRONCO_FIRE_EXTRA
        ):

            self.phase = self.WINDUP
            self.phase_t = TRONCO_WINDUP

    # ---------- dibujo ----------

    def draw(self, screen, camera, art):

        sprites = art.get(camera.zoom)

        shake = 0

        if self.flash > 0:

            img = sprites["hit"]

        else:

            if self.phase == self.WINDUP:

                frames = sprites["charge"]
                index = int(self.anim_t / TRONCO_ANIM_FRAME) % len(frames)

                # Tiembla cada vez mas fuerte hasta soltar las bolas
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

            # Herido = mas oscuro
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
                    dest.centerx + shake,
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
        self.shots = []
        self.art = EnemyArt()
        self.tronco_art = TroncoArt()
        self.mosquito_art = MosquitoArt()
        self.mosquito_alert = False
        self._alert_t = 0.0

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

        return [e for e in self.enemies if not e.spawning and not e.dead and not getattr(e, "attached", False)]

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

        pinos, troncos, mosquitos = wave_composition(self.wave)

        kinds = (["pino"] * pinos + ["tronco"] * troncos + ["mosquito"] * mosquitos)
        random.shuffle(kinds)

        hp = min(ENEMY_HP_MAX, ENEMY_HP_BASE + self.wave)
        tronco_hp = min(ENEMY_HP_MAX, hp + TRONCO_HP_EXTRA)
        speed = min(ENEMY_SPEED_MAX, ENEMY_SPEED_BASE + ENEMY_SPEED_STEP * self.wave)

        cmap = game.collision_map
        player_pos = pygame.Vector2(game.player.rect.center)
        corners = [
            (ROOM.left + 40, ROOM.top + 30),
            (ROOM.right - 40, ROOM.top + 30),
            (ROOM.left + 40, ROOM.bottom - 30),
            (ROOM.right - 40, ROOM.bottom - 30),
        ]

        self.enemies = []
        self.shots = []

        for i, kind in enumerate(kinds):
            pos = None
            min_dist = 135 if kind == "mosquito" else 110
            hitbox = MOSQUITO_HITBOX if kind == "mosquito" else ENEMY_HITBOX

            for _ in range(120):
                x = random.randint(ROOM.left + 16, ROOM.right - 16)
                y = random.randint(ROOM.top + 16, ROOM.bottom - 16)
                probe = pygame.Rect(0, 0, *hitbox)
                probe.center = (x, y)
                if pygame.Vector2(x, y).distance_to(player_pos) < min_dist:
                    continue
                if not (ROOM.contains(probe) and cmap.can_move(probe)):
                    continue
                if any(pygame.Vector2(x, y).distance_to(e.pos) < 18 for e in self.enemies):
                    continue
                pos = (x, y)
                break

            if pos is None:
                pos = corners[i % len(corners)]

            delay = i * 0.15
            if kind == "tronco":
                self.enemies.append(Tronco(pos[0], pos[1], tronco_hp, spawn_delay=delay))
            elif kind == "mosquito":
                self.enemies.append(Mosquito(pos[0], pos[1], MOSQUITO_HP, spawn_delay=delay))
            else:
                self.enemies.append(Enemy(pos[0], pos[1], hp, speed, spawn_delay=delay))

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
        self.shots = []
        self.chest = None
        self.reward = 0
        self.mode = None
        self.banner_t = 0.0
        self.state = self.IDLE

    def _leave(self, game):
        """Boton Salir (o ESC en el menu)."""

        self._end_run(game)
        self._teleport_out(game)

    def _player_died(self, game):
        """Morir en la sala (con o sin escape) es perder de verdad:
        termina la partida."""

        self._end_run(game)

        game.state = "dying"
        game.fade_alpha = 0

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
        light_on = bool(game.has_match)
        light_world = game._light_radius() / game.camera.zoom if light_on else 0.0

        for enemy in self.enemies:
            if isinstance(enemy, Mosquito):
                enemy.update(dt, target, game.collision_map, light_on, light_world)
                if enemy.attached and enemy.damage_t <= 0.0:
                    game.take_damage(MOSQUITO_DAMAGE)
                    enemy.damage_t = MOSQUITO_DAMAGE_INTERVAL
            else:
                if enemy.fixed:
                    enemy.light_radius = light_world
                enemy.update(dt, target, game.collision_map, self.enemies)
                if enemy.fixed:
                    self.shots.extend(enemy.take_shots())

        self.mosquito_alert = any(
            isinstance(e, Mosquito) and e.alert and not e.dead
            for e in self.enemies
        )

        bounce_enemies(self.enemies, game.collision_map, target)

        for shot in self.shots:
            shot.update(dt, game.collision_map)

        body = pygame.Rect(0, 0, 10, 16)
        body.midbottom = (p.rect.centerx, p.rect.bottom)
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
                    game.take_damage(damage * SHOT_DAMAGE_MULT)
                shot.dead = True

        self.shots = [s for s in self.shots if not s.dead]

        for enemy in self.enemies:
            if enemy.dead:
                self.last_death = (enemy.pos.x, enemy.pos.y)
                self._death_puff(enemy.pos)

        self.enemies = [e for e in self.enemies if not e.dead]

        if game.vida <= 0:
            self._player_died(game)
            return

        # La oleada termina solo cuando no queda NINGUN enemigo (los
        # mosquitos pegados tambien cuentan: aunque te chupen todos, la
        # partida sigue)
        if not self.enemies:
            self.shots = []
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
            if isinstance(enemy, Mosquito):
                enemy.draw(screen, camera, self.mosquito_art)
            else:
                enemy.draw(
                    screen, camera,
                    self.tronco_art if enemy.fixed else self.art
                )

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

        # Las bolas se ven siempre, aunque no las alumbres
        for shot in self.shots:
            shot.draw(screen, camera, self.tronco_art)

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

        # ---------- alerta de mosquito ----------

        if self.state == self.WAVE and self.mosquito_alert:
            self._draw_mosquito_alert(screen)

        # ---------- oleada completada ----------

        if self.banner_t > 0:
            self._draw_banner(screen)

    def _draw_mosquito_alert(self, screen):
        """Imagen de advertencia en pantalla (HUD, arriba al centro),
        parpadeando, para avisar que hay un mosquito cerca."""

        self._alert_t += 1 / 60

        pulse = 0.5 + 0.5 * math.sin(self._alert_t * 8)

        w, h = self.size

        icon = self.mosquito_art.warning.copy()
        icon.set_alpha(int(150 + 105 * pulse))

        rect = icon.get_rect(midtop=(w // 2, 14))
        screen.blit(icon, rect)

        draw_text(
            screen, "Mosquito cerca!", 24, (255, 120, 110),
            center=(rect.centerx, rect.bottom + 12)
        )

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