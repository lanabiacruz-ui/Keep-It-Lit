"""Araña (enemigo del mapa 2).

- NO aparece en ninguna oleada: solo existe en el mapa 2, y SOLO en la salita
  de abajo a la izquierda (ROOM). Cuando entras a esa sala nacen SPIDER_COUNT
  arañas en ronda alrededor tuyo, ya apuntandote; desaparecen al salir del mapa.
- Se ALEJA de vos: nunca se acerca por su cuenta.
- SOLO te pegan cuando estas DENTRO de una telaraña.
- Ataque: te tira un BLOQUE DE TELARAÑA con muy buena punteria (calcula a
  donde vas a estar).
    * Si el bloque te da: queda pegado a vos (te ralentiza mucho mientras
      estes dentro).
    * TODAS las arañas que te ven dentro de una telaraña (te haya dado un
      bloque o hayas pisado una del piso) corren RAPIDO hacia vos.
    * Golpe y retirada: cada una llega, te pega rapido y se ALEJA un
      momento (para que no puedas pegarle) antes de volver a entrar. Solo
      te pegan mientras sigas dentro de la telaraña.
    * Cuando te salis de la telaraña, ven que escapaste: dejan de perseguirte,
      se vuelven a alejar y tratan de tirarte otra telaraña enseguida.
    * Si falla: el bloque cae en el piso y sigue ralentizando a quien lo
      pise. La telaraña desaparece con el tiempo (WEB_LIFE).
    * Las telarañas NUNCA se superponen: si una cae sobre otra, se desliza
      al lugar libre mas cercano hasta quedar pegada borde con borde,
      como bloques. La que te atrapo no se mueve (para no soltarte): se
      corren las demas.
- La telaraña tiene 3 imagenes distintas (assets/maps/combate/telarana_1/2/3.png);
  solo cambia el dibujo, no el comportamiento. Cada una tiene sus animaciones
  (tiras de cuadros cuadrados, ver tools/make_web_frames.py):
      telarana_<n>_vuelo.png     bloque volando (en bucle)
      telarana_<n>_aparecer.png  cae al piso / se pega al jugador
      telarana_<n>_suelo.png     quieta en el piso (en bucle)
      telarana_<n>_deshacer.png  se desarma al final de su vida
  Si falta alguna tira se usa la imagen fija telarana_<n>.png.
- Mira SIEMPRE hacia vos (8 direcciones) y camina moviendo las patas
  (hoja assets/maps/combate/arana_caminar.png: 4 cuadros x 8 direcciones,
  celdas cuadradas de 240x240 con fondo transparente; las filas van en
  sentido horario desde la derecha: der, abajo-der, abajo, abajo-izq, izq,
  arriba-izq, arriba, arriba-der). Cuando se aleja camina "de espaldas":
  mirandote pero con las patas yendo para atras.
- Otras animaciones (por transformaciones): respirar, preparar el
  lanzamiento, atacar, golpe y muerte.
- Si falta la hoja usa la imagen fija assets/maps/combate/arana.png.

AURANTULA (araña dorada, mas grande y mortal) - clase Aurantula, mas abajo:
- Nace en la sala grande del medio-izquierda del mapa 2 (AURA_TRIGGER).
- Mucha mas vida, mas grande y mas rapida.
- Tira RAFAGAS DE 4 TELARAÑAS, cada una apuntada de nuevo con anticipacion
  (puntería mucho mejor: tiro rapido, anticipa tu velocidad y no apunta a
  una pared).
- Su mordida da VENENO (game.apply_poison): drena la luz con el tiempo y SI
  mata (a diferencia del de Minecraft). Los golpes seguidos suman tiempo.
- En equipo (cantidad PAR: 2 o 4) piensan: la mitad (las mas lejanas) son
  TIRADORAS y la otra mitad (las mas cercanas) son MORDEDORAS. Si queda una
  cantidad impar, cada una hace de todo como la araña comun.
"""

import math
import random
from pathlib import Path

import pygame

from core.audio_manager import audio
from world.items import WorldItem, coin_id_for, split_coins

COMBAT_DIR = (
    Path(__file__).resolve().parent.parent / "assets" / "maps" / "combate"
)
ART_PATH = COMBAT_DIR / "arana.png"
WALK_PATH = COMBAT_DIR / "arana_caminar.png"
WALK_COLS = 4                # cuadros de la caminata
WALK_ROWS = 8                # direcciones (8, en sentido horario desde la derecha)
WEB_PATHS = [COMBAT_DIR / f"telarana_{n}.png" for n in (1, 2, 3)]

# Clave en la enciclopedia
CODEX_KEY = "arana"
DISCOVER_DISTANCE = 520

# ---- cantidad / vida / tamaño (del tamaño del jugador) ---------------------------
SPIDER_COUNT = 6

# La salita del mapa 2 donde aparecen (coordenadas del mundo = pixeles de
# assets/maps/region_01/mapa2.png: pared izquierda x~14, tabique x~308,
# techo y~1176, piso y~1370; la entrada sube por el pasillo de abajo).
ROOM = pygame.Rect(18, 1180, 285, 188)
SPAWN_AREA = ROOM.inflate(-30, -30)      # donde pueden nacer (lejos de las paredes)
TRIGGER_AREA = ROOM.inflate(-40, -40)    # al pisar esto se despiertan
HP = 12
DRAW_WIDTH = 36              # ancho dibujado de la imagen fija (158x110)
DRAW_CELL = 48               # tamaño dibujado de un cuadro de la hoja de caminata
TURN_SPEED = 720             # grados por segundo al girar para mirarte
WALK_RATE = 40.0             # velocidad / WALK_RATE = ciclos de patas por segundo
HITBOX = (22, 14)
COINS = 25

# ---- movimiento ---------------------------------------------------------------------
FLEE_SPEED = 92              # se aleja de vos
CHASE_SPEED = 170            # solo despues de atraparte: corre rapido hacia vos
SIGHT = 560                  # a esta distancia te apunta
KEEP_AWAY = 230              # si te acercas mas que esto, se aleja
SPAWN_MIN_DIST = 30          # (si no entran en ronda) al nacer: cerca, pero no encima
SPAWN_MAX_DIST = 150
SPAWN_RING = (80, 65, 95, 50, 110, 40)   # radios probados para la ronda (salita)

# ---- bloque de telaraña ----------------------------------------------------------------
FIRST_THROW = 0.55
THROW_COOLDOWN = 2.6         # (antes 1.9) cada una tira mas espaciado
THROW_GAP = 1.0              # entre telarañas de DISTINTAS arañas pasa al menos esto (no te llueven)
WIND_UP = 0.30               # tiempo de la animacion de "preparar" antes de tirar
SHOT_SPEED = 260
SHOT_RANGE = 520
SHOT_SIZE = 22
HIT_PAD = (14, 22)           # el bloque cuenta como "te dio" un poco antes

WEB_SIZE = 48                # lado del bloque de telaraña en el piso
WEB_LIFE = 9.0               # segundos hasta que se va solo
WEB_FADE = 2.0               # los ultimos segundos se va apagando
WEB_SLOW = 0.175             # multiplicador de velocidad dentro (el doble de lento que antes: 0.35)

APPEAR_TIME = 0.30           # duracion de la animacion "aparecer"
FLY_FPS = 14                 # cuadros por segundo del vuelo
SHOT_DRAW_START = 14         # tamaño (px del mundo) de la telaraña al salir: chiquita
SHOT_DRAW_END = WEB_SIZE     # ... y va creciendo hasta el tamaño que tiene en el piso
SHOT_GROW_DIST = 200         # distancia recorrida (px) para llegar al tamaño final
IDLE_FPS = 6                 # cuadros por segundo de la telaraña en el piso

# ---- cuerpo a cuerpo (solo despues de atraparte) -------------------------------------
HIT_DAMAGE = 0.06            # la vida del jugador va de 0 a 1 (antes 0.12)
MAX_ATTACKERS = 3            # a lo sumo estas arañas comunes te muerden a la vez (las demas esperan)
HIT_INTERVAL = 0.5           # pega rapido cuando esta cerca (y estas en la telaraña)
CHASE_FIRST_HIT = 0.2        # espera antes del primer golpe al llegar
ESCAPE_GRACE = 0.15          # tiempo fuera de la telaraña para darse cuenta de que saliste
REWEB_DELAY = (0.8, 1.5)     # al salirte: tarda esto en tirarte otra telaraña (tenes un respiro)
ALL_CHASE = True             # True: TODAS las arañas que te ven en una telaraña van a pegarte
RETREAT_TIME = (0.9, 1.4)    # despues de pegar se alejan este tiempo (segundos)
RETREAT_SPEED = 150          # velocidad con la que se alejan (de espaldas)
RETREAT_STUCK = 0.25         # si no pueden alejarse (pared) vuelven a entrar a los 0.25 s
RETURN_HIT_DELAY = 0.10      # al volver, tardan esto en pegar: el golpe sigue siendo rapido
FIRST_HIT_SPREAD = 0.25      # (0 a esto) de demora extra al azar para que no peguen todas juntas
WEB_SLIDE_SPEED = 320.0      # velocidad (px/s) con la que las telarañas se apartan entre si
CHASE_MAX = 12.0
LOSE_DIST = 480

DEATH_TIME = 0.35

# ======================================================================
# AURANTULA (araña dorada)
# ======================================================================
AURA_NAME = "Aurantula"
AURA_CODEX_KEY = "aurantula"
AURA_WALK_PATH = COMBAT_DIR / "arana_amarilla_caminar.png"   # 4 x 8, celdas de 240

AURA_COUNT = 4               # cuantas nacen (con 4 se ve el trabajo en equipo)
AURA_ROOM = pygame.Rect(100, 690, 610, 370)        # sala grande (mundo = pixeles del mapa)
AURA_SPAWN_AREA = AURA_ROOM.inflate(-30, -30)
AURA_TRIGGER = pygame.Rect(150, 730, 520, 290)     # al pisar esto se despiertan
AURA_RING = (230, 190, 270, 150, 310, 120)         # radios probados al nacer

AURA_HP = 30                 # la araña comun tiene 12
AURA_HITBOX = (36, 24)
AURA_DRAW_CELL = 80          # la comun se dibuja a 48
AURA_WALK_RATE = 60.0
AURA_COINS = 60

AURA_SIGHT = 640
AURA_FLEE_SPEED = 100
AURA_STRAFE_SPEED = 70
AURA_CHASE_SPEED = 195
AURA_KEEP_AWAY = 260         # solitaria: se aleja si te acercas mas que esto
AURA_SHOOT_MIN = 250         # tiradora: se mantiene entre estas distancias
AURA_SHOOT_MAX = 400

# rafaga de telarañas
AURA_FIRST_THROW = 0.6
AURA_THROW_COOLDOWN = 3.2
AURA_THROW_COOLDOWN_WEBBED = 4.8   # si ya estas atrapado, tira menos seguido
AURA_WIND_UP = 0.45
AURA_VOLLEY = 3              # telarañas por rafaga (antes 4)
AURA_BURST_GAP = 0.12        # entre una y otra (cada una vuelve a apuntar)
AURA_SPREAD = (0.0, -8.0, 8.0)       # grados de abanico de cada telaraña
AURA_SHOT_SPEED = 400        # (la comun: 260)
AURA_SHOT_SIZE = 30          # (la comun: 22)
AURA_SHOT_RANGE = 620

# mordida + veneno
AURA_BITE_DAMAGE = 0.04      # el golpe en si (el grueso lo hace el veneno)
AURA_HIT_INTERVAL = 0.45
AURA_POISON_TIME = 5.0       # segundos de veneno por mordida (se suman; antes 8)

_aura_uid = [0]


def _load_art():

    try:
        return pygame.image.load(str(ART_PATH)).convert_alpha()
    except (pygame.error, FileNotFoundError, OSError):
        pass

    surf = pygame.Surface((158, 110), pygame.SRCALPHA)

    pygame.draw.ellipse(surf, (50, 50, 54), pygame.Rect(30, 14, 100, 70))
    pygame.draw.ellipse(surf, (130, 40, 40), pygame.Rect(62, 52, 40, 22))

    for i in range(4):

        y = 40 + i * 14

        pygame.draw.line(surf, (30, 30, 34), (30, y), (6, y + 36), 6)
        pygame.draw.line(surf, (30, 30, 34), (130, y), (152, y + 36), 6)

    return surf


def _load_web(variant):
    """Imagen fija de la telaraña: solo se usan TUS dibujos. Si falta, None
    (no se dibuja nada: el codigo no inventa ninguna telaraña)."""

    for stem in ("telarana", "telaraña"):

        path = COMBAT_DIR / f"{stem}_{variant + 1}.png"

        try:
            return pygame.image.load(str(path)).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            continue

    return None


def _load_strip(path):
    """Tira horizontal de cuadros cuadrados -> lista de superficies."""

    try:
        sheet = pygame.image.load(str(path)).convert_alpha()
    except (pygame.error, FileNotFoundError, OSError):
        return []

    h = sheet.get_height()

    if h <= 0:
        return []

    return [
        sheet.subsurface((i * h, 0, h, h)).copy()
        for i in range(max(1, sheet.get_width() // h))
    ]


def _lead_direction(src, target, vel, speed):
    """Direccion para que un disparo de velocidad `speed` desde `src` le de a
    `target` que se mueve con velocidad `vel` (puntería con anticipacion)."""

    rel = target - src

    a = vel.x * vel.x + vel.y * vel.y - speed * speed
    b = 2.0 * (rel.x * vel.x + rel.y * vel.y)
    c = rel.x * rel.x + rel.y * rel.y

    t = None

    if abs(a) < 1e-6:

        if abs(b) > 1e-6:
            t = -c / b

    else:

        disc = b * b - 4.0 * a * c

        if disc >= 0:

            r = math.sqrt(disc)

            roots = [(-b - r) / (2 * a), (-b + r) / (2 * a)]
            roots = [x for x in roots if x > 0]

            if roots:
                t = min(roots)

    if t is None or t <= 0:
        t = 0.0

    aim = rel + vel * t

    if aim.length_squared() < 1e-6:
        aim = rel

    if aim.length_squared() < 1e-6:
        return pygame.Vector2(1, 0)

    return aim.normalize()


class WebShot:
    """Bloque de telaraña volando hacia el jugador."""

    def __init__(self, x, y, direction, variant,
                 speed=SHOT_SPEED, size=SHOT_SIZE):

        self.speed = speed
        self.pos = pygame.Vector2(x, y)
        self.origin = pygame.Vector2(x, y)
        self.dir = pygame.Vector2(direction)
        self.travelled = 0.0
        self.variant = variant
        self.owner = None
        self.age = 0.0

        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (round(x), round(y))

        self.done = False


class WebPatch:
    """Bloque de telaraña en el piso: ralentiza y desaparece con el tiempo."""

    def __init__(self, x, y, variant):

        self.rect = pygame.Rect(0, 0, WEB_SIZE, WEB_SIZE)
        self.rect.center = (round(x), round(y))

        # lugar al que va (enteros: asi quedan pegadas justo borde con borde)
        self.tx = self.rect.centerx
        self.ty = self.rect.centery

        # posicion real mientras se desliza hacia (tx, ty)
        self.pos = pygame.Vector2(self.tx, self.ty)

        self.variant = variant
        self.age = 0.0

    def target_rect(self):

        r = pygame.Rect(0, 0, WEB_SIZE, WEB_SIZE)
        r.center = (self.tx, self.ty)

        return r

    def slide(self, dt):
        """Se desliza hacia el lugar que le toca (sin saltos)."""

        goal = pygame.Vector2(self.tx, self.ty)
        d = goal - self.pos
        dist = d.length()

        if dist <= 0.01:
            return

        step = WEB_SLIDE_SPEED * dt

        if dist <= step:
            self.pos.update(goal)
        else:
            self.pos += d * (step / dist)

        self.rect.center = (round(self.pos.x), round(self.pos.y))

    @property
    def alpha(self):

        left = WEB_LIFE - self.age

        if left >= WEB_FADE:
            return 1.0

        return max(0.0, left / WEB_FADE)


class Spider:

    # lo que cambia en las subclases (ver Aurantula)
    CODEX_KEY = CODEX_KEY
    WALK_PATH = WALK_PATH
    DRAW_CELL = DRAW_CELL
    WIND_UP = WIND_UP
    COINS = COINS

    # sonidos (ver tools/make_sounds_spider.py)
    SND_SKITTER = "spider_skitter"
    SND_THROW = "spider_web_throw"
    SND_BITE = "spider_bite"
    SND_HURT = "spider_hurt"
    SND_DIE = "spider_die"
    STEP_GAP = 0.20              # segundos entre un "tic tic tic" de patas y otro

    def __init__(self, x, y):

        self.step_t = random.uniform(0.0, self.STEP_GAP)

        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)

        self.rect = pygame.Rect(0, 0, *HITBOX)
        self.rect.center = (round(x), round(y))

        self.hp = HP
        self.flash = 0.0

        self.mode = "aim"            # idle / aim / chase
        self.cool = FIRST_THROW
        self.wind = 0.0              # >0: preparando el lanzamiento
        self.shoot_t = 0.0           # animacion despues de tirar
        self.chase_t = 0.0
        self.out_t = 0.0             # tiempo que lleva el jugador fuera de la telaraña
        self.hit_cool = 0.5
        self.phase = "approach"      # approach (va a pegar) / retreat (se aleja)
        self.retreat_t = 0.0
        self.stuck_t = 0.0
        self.face = 1

        self.moving = False
        self.back = False            # camina "de espaldas" (mirando al jugador)
        self.heading = random.uniform(0.0, 360.0)   # a donde mira (grados)
        self.walk_phase = random.uniform(0.0, 1.0)
        self.anim_t = random.uniform(0.0, 6.0)

        self.death_t = 0.0
        self.dropped = False

    @property
    def dead(self):

        return self.hp <= 0

    def take_damage(self, amount):

        # solo suena en el primer golpe de una racha (la luz pega seguido)
        if self.flash <= 0.0 and self.hp > 0:
            audio.play(self.SND_HURT, jitter=0.12)

        self.hp -= amount
        self.flash = 0.12

    def footsteps(self, dt, game):
        """Patitas: un tic-tic-tic mientras camina (suena segun la distancia)."""

        if not self.moving:

            self.step_t = self.STEP_GAP * 0.5

            return

        self.step_t += dt

        if self.step_t >= self.STEP_GAP:

            self.step_t = 0.0

            audio.play_at(
                self.SND_SKITTER, self.rect.center,
                game.player.rect.center, radius=420.0
            )

    def start_chase(self):

        self.mode = "chase"
        self.phase = "approach"
        self.retreat_t = 0.0
        self.stuck_t = 0.0
        self.chase_t = 0.0
        self.out_t = 0.0
        self.hit_cool = CHASE_FIRST_HIT + random.uniform(0.0, FIRST_HIT_SPREAD)
        self.wind = 0.0

    def stop_chase(self):
        """Ve que te saliste de la telaraña: vuelve a alejarse y a tirar otra."""

        self.mode = "aim"
        self.phase = "approach"
        self.wind = 0.0
        self.out_t = 0.0
        self.cool = random.uniform(*REWEB_DELAY)

    def _start_retreat(self):
        """Despues de pegar: se aleja un momento para que no le pegues."""

        self.phase = "retreat"
        self.retreat_t = random.uniform(*RETREAT_TIME)
        self.stuck_t = 0.0

    # ---- movimiento -------------------------------------------------------
    def _step(self, delta, cmap):

        moved = False

        for axis in (0, 1):

            step = delta[axis]

            if abs(step) < 1e-6:
                continue

            new = self.rect.copy()

            if axis == 0:
                new.centerx = round(self.pos.x + step)
            else:
                new.centery = round(self.pos.y + step)

            if cmap.can_move(new):

                if axis == 0:
                    self.pos.x += step
                else:
                    self.pos.y += step

                self.rect.center = (round(self.pos.x), round(self.pos.y))

                moved = True

        return moved

    def _move_dir(self, direction, speed, dt, cmap):
        """Se mueve hacia `direction`; si choca con algo prueba de costado."""

        if direction.length_squared() < 1e-6:
            return False

        base = direction.normalize()

        for ang in (0, 50, -50, 100, -100):

            d = base.rotate(ang)

            if self._step(d * speed * dt, cmap):
                return True

        return False

    def update(self, dt, game, mgr):

        cmap = game.collision_map

        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.shoot_t > 0:
            self.shoot_t = max(0.0, self.shoot_t - dt)

        # empuje al recibir un golpe
        if self.vel.length_squared() > 1.0:

            self._step(self.vel * dt, cmap)

            self.vel *= max(0.0, 1.0 - 9.0 * dt)

        else:
            self.vel.update(0, 0)

        me = pygame.Vector2(self.rect.center)
        target = pygame.Vector2(game.player.rect.center)

        d = target - me
        dist = d.length()

        if abs(d.x) > 2:
            self.face = 1 if d.x > 0 else -1

        sees = not getattr(game, "invisible", False)

        self.moving = False
        self.back = False

        # gira (de a poco) para mirar al jugador
        if dist > 0.5:

            want = math.degrees(math.atan2(d.y, d.x))

            diff = (want - self.heading + 180.0) % 360.0 - 180.0

            turn = TURN_SPEED * dt

            self.heading = (
                self.heading + max(-turn, min(turn, diff))
            ) % 360.0

        if dist <= DISCOVER_DISTANCE:
            game.discover_enemy(self.CODEX_KEY)

        if not sees or dist > SIGHT * 1.5:

            self.mode = "idle" if self.mode != "chase" else "idle"
            self.wind = 0.0

            return

        if self.mode == "idle":

            self.mode = "aim"
            self.cool = FIRST_THROW

        if self.mode == "aim":

            # nunca se acerca: solo se aleja
            if dist < KEEP_AWAY and dist > 0.5:

                self.moving = self._move_dir(-d, FLEE_SPEED, dt, cmap)
                self.back = True

                if self.moving:
                    self.walk_phase -= dt * FLEE_SPEED / WALK_RATE

            if self.wind > 0:

                self.wind -= dt

                if self.wind <= 0:

                    self.wind = 0.0
                    self.shoot_t = 0.25
                    self.cool = THROW_COOLDOWN

                    mgr.throw(self, game)

            else:

                # si ya estas atrapado no gasta telarañas: espera a que salgas
                if not mgr.player_in_web:
                    self.cool -= dt

                if (
                    self.cool <= 0
                    and not mgr.player_in_web
                    and mgr.throw_lock <= 0
                ):
                    self.wind = WIND_UP

                    mgr.throw_lock = THROW_GAP

            return

        # chase: te atrapo en su telaraña, viene a pegarte
        self.chase_t += dt

        if mgr.player_in_web:
            self.out_t = 0.0
        else:
            self.out_t += dt

        if (
            self.out_t > ESCAPE_GRACE
            or dist > LOSE_DIST
            or self.chase_t > CHASE_MAX
        ):

            self.stop_chase()

            return

        # golpe y retirada: se aleja mirandote (camina de espaldas)
        if self.phase == "retreat":

            self.retreat_t -= dt

            self.moving = self._move_dir(-d, RETREAT_SPEED, dt, cmap)
            self.back = True

            if self.moving:
                self.walk_phase -= dt * RETREAT_SPEED / WALK_RATE
                self.stuck_t = 0.0
            else:
                self.stuck_t += dt

            if self.retreat_t <= 0 or self.stuck_t >= RETREAT_STUCK:

                self.phase = "approach"
                self.hit_cool = RETURN_HIT_DELAY

            return

        touching = self.rect.inflate(10, 10).colliderect(game.player.rect)

        if not touching and dist > 1:

            self.moving = self._move_dir(d, CHASE_SPEED, dt, cmap)

            if self.moving:
                self.walk_phase += dt * CHASE_SPEED / WALK_RATE

        self.hit_cool -= dt

        if touching and self.hit_cool <= 0 and mgr.player_in_web:

            self.shoot_t = 0.2

            game.take_damage(HIT_DAMAGE, common=True, source=self)

            audio.play(self.SND_BITE, jitter=0.08)

            self._start_retreat()


class Aurantula(Spider):
    """Araña dorada: grande, aguanta mucho, tira rafagas de 4 telarañas con
    muy buena punteria y su mordida envenena (el veneno SI mata).

    Roles (los reparte SpiderManager._assign_roles):
        solo      cantidad impar: hace de todo, como la araña comun.
        shooter   en equipo par: se queda lejos tirando telarañas.
        biter     en equipo par: va directo a morderte (no espera la telaraña).
    """

    CODEX_KEY = AURA_CODEX_KEY
    WALK_PATH = AURA_WALK_PATH
    DRAW_CELL = AURA_DRAW_CELL
    WIND_UP = AURA_WIND_UP
    COINS = AURA_COINS

    SND_SKITTER = "aura_skitter"
    SND_THROW = "aura_web_throw"
    SND_BITE = "aura_bite"
    SND_HURT = "aura_hurt"
    SND_DIE = "aura_die"
    STEP_GAP = 0.28

    def __init__(self, x, y):

        super().__init__(x, y)

        _aura_uid[0] += 1
        self.uid = _aura_uid[0]

        self.rect = pygame.Rect(0, 0, *AURA_HITBOX)
        self.rect.center = (round(x), round(y))

        self.hp = AURA_HP
        self.cool = AURA_FIRST_THROW

        self.role = "solo"

        self.burst_left = 0
        self.burst_idx = 0
        self.burst_t = 0.0

        self.strafe = random.choice((-1, 1))
        self.strafe_t = random.uniform(1.0, 2.2)

    # ---- roles ------------------------------------------------------------
    def set_role(self, role):

        if role == self.role:
            return

        self.role = role

        self.wind = 0.0
        self.burst_left = 0
        self.phase = "approach"
        self.retreat_t = 0.0
        self.stuck_t = 0.0

        if role == "biter":

            self.mode = "chase"
            self.chase_t = 0.0
            self.out_t = 0.0
            self.hit_cool = 0.3 + random.uniform(0.0, FIRST_HIT_SPREAD)

        else:

            self.mode = "aim"
            self.cool = random.uniform(*REWEB_DELAY)

    def start_chase(self):
        """Las tiradoras nunca van a morder (aunque la telaraña las avise)."""

        if self.role == "shooter":
            return

        super().start_chase()

    # ---- movimiento ---------------------------------------------------------
    def _keep_distance(self, d, dist, dt, cmap, lo, hi=None, strafe=False):
        """Se aleja si estas muy cerca; si tiene `hi`, se acerca si estas muy
        lejos; y si `strafe`, camina de costado para ser dificil de pegar."""

        self.strafe_t -= dt

        if self.strafe_t <= 0:

            self.strafe = -self.strafe
            self.strafe_t = random.uniform(1.2, 2.4)

        # preparando la rafaga: quieta, apuntando
        if self.wind > 0 or dist < 0.5:
            return

        if dist < lo:

            move, speed, back = -d, AURA_FLEE_SPEED, True

        elif hi is not None and dist > hi:

            move, speed, back = d, AURA_FLEE_SPEED * 0.9, False

        elif strafe:

            move = pygame.Vector2(-d.y, d.x) * self.strafe
            speed, back = AURA_STRAFE_SPEED, False

        else:

            return

        self.moving = self._move_dir(move, speed, dt, cmap)
        self.back = back

        if self.moving:
            self.walk_phase += (
                dt * speed / AURA_WALK_RATE * (-1.0 if back else 1.0)
            )

    # ---- rafaga de telarañas --------------------------------------------------
    def _try_throw(self, dt, game, mgr, dist, cmap, me, target):

        if self.wind > 0:

            self.wind -= dt

            if self.wind <= 0:

                self.wind = 0.0
                self.burst_left = AURA_VOLLEY
                self.burst_idx = 0
                self.burst_t = 0.0

                self.cool = (
                    AURA_THROW_COOLDOWN_WEBBED if mgr.player_in_web
                    else AURA_THROW_COOLDOWN
                )

            return

        self.cool -= dt

        if (
            self.cool <= 0
            and dist <= AURA_SHOT_RANGE - 60
            and mgr._clear_line(cmap, me, target)
        ):
            self.wind = AURA_WIND_UP

            audio.play_at(
                "aura_hiss", self.rect.center, game.player.rect.center,
                radius=700.0
            )

    # ---- cuerpo a cuerpo --------------------------------------------------------
    def _melee(self, dt, game, mgr, d, dist, cmap, needs_web):

        # golpe y retirada
        if self.phase == "retreat":

            self.retreat_t -= dt

            self.moving = self._move_dir(-d, RETREAT_SPEED, dt, cmap)
            self.back = True

            if self.moving:
                self.walk_phase -= dt * RETREAT_SPEED / AURA_WALK_RATE
                self.stuck_t = 0.0
            else:
                self.stuck_t += dt

            if self.retreat_t <= 0 or self.stuck_t >= RETREAT_STUCK:

                self.phase = "approach"
                self.hit_cool = RETURN_HIT_DELAY

            return

        touching = self.rect.inflate(14, 14).colliderect(game.player.rect)

        if not touching and dist > 1:

            speed = AURA_CHASE_SPEED * (1.15 if mgr.player_in_web else 1.0)

            self.moving = self._move_dir(d, speed, dt, cmap)

            if self.moving:
                self.walk_phase += dt * speed / AURA_WALK_RATE

        self.hit_cool -= dt

        if touching and self.hit_cool <= 0 and (
            mgr.player_in_web or not needs_web
        ):

            self.shoot_t = 0.22

            self._bite(game)

            self._start_retreat()

            self.hit_cool = AURA_HIT_INTERVAL

    def _bite(self, game):
        """Mordida: un golpe chico + veneno."""

        game.take_damage(AURA_BITE_DAMAGE, common=True, source=self)

        audio.play(self.SND_BITE, jitter=0.08)

        poison = getattr(game, "apply_poison", None)

        if poison is not None:
            poison(AURA_POISON_TIME, source=self)

    # ---- cerebro ----------------------------------------------------------------
    def update(self, dt, game, mgr):

        cmap = game.collision_map

        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.shoot_t > 0:
            self.shoot_t = max(0.0, self.shoot_t - dt)

        # empuje al recibir un golpe
        if self.vel.length_squared() > 1.0:

            self._step(self.vel * dt, cmap)

            self.vel *= max(0.0, 1.0 - 9.0 * dt)

        else:
            self.vel.update(0, 0)

        me = pygame.Vector2(self.rect.center)
        target = pygame.Vector2(game.player.rect.center)

        d = target - me
        dist = d.length()

        if abs(d.x) > 2:
            self.face = 1 if d.x > 0 else -1

        sees = not getattr(game, "invisible", False)

        self.moving = False
        self.back = False

        # gira (de a poco) para mirar al jugador
        if dist > 0.5:

            want = math.degrees(math.atan2(d.y, d.x))

            diff = (want - self.heading + 180.0) % 360.0 - 180.0

            turn = TURN_SPEED * dt

            self.heading = (
                self.heading + max(-turn, min(turn, diff))
            ) % 360.0

        if dist <= DISCOVER_DISTANCE:
            game.discover_enemy(self.CODEX_KEY)

        if not sees or dist > AURA_SIGHT * 1.5:

            self.mode = "idle" if self.role != "biter" else "chase"
            self.wind = 0.0
            self.burst_left = 0

            return

        # una rafaga en curso: cada telaraña vuelve a apuntar
        if self.burst_left > 0:

            self.burst_t -= dt

            if self.burst_t <= 0:

                mgr.throw(self, game, self.burst_idx)

                self.burst_idx += 1
                self.burst_left -= 1
                self.burst_t = AURA_BURST_GAP
                self.shoot_t = 0.2

            return

        # ---- tiradora: lejos, de costado, tirando rafagas ----
        if self.role == "shooter":

            self._keep_distance(
                d, dist, dt, cmap, AURA_SHOOT_MIN, AURA_SHOOT_MAX, strafe=True
            )

            self._try_throw(dt, game, mgr, dist, cmap, me, target)

            return

        # ---- mordedora: va directo, no espera la telaraña ----
        if self.role == "biter":

            self.mode = "chase"

            self._melee(dt, game, mgr, d, dist, cmap, needs_web=False)

            return

        # ---- solitaria: como la araña comun, pero con rafagas ----
        if self.mode == "idle":

            self.mode = "aim"
            self.cool = AURA_FIRST_THROW

        if self.mode == "aim":

            self._keep_distance(d, dist, dt, cmap, AURA_KEEP_AWAY)

            if not mgr.player_in_web:
                self._try_throw(dt, game, mgr, dist, cmap, me, target)

            return

        self.chase_t += dt

        if mgr.player_in_web:
            self.out_t = 0.0
        else:
            self.out_t += dt

        if (
            self.out_t > ESCAPE_GRACE
            or dist > LOSE_DIST
            or self.chase_t > CHASE_MAX
        ):

            self.stop_chase()

            return

        self._melee(dt, game, mgr, d, dist, cmap, needs_web=True)


class SpiderManager:

    def __init__(self):

        self.spiders = []
        self.dying = []          # [spider, tiempo] animacion de muerte
        self.shots = []
        self.webs = []

        self._active = False
        self._slow = 1.0
        self._warned = False
        self.player_in_web = False     # el jugador esta dentro de una telaraña
        self.throw_lock = 0.0          # >0: ninguna araña comun empieza otro lanzamiento

        self._prev_player = None
        self._player_vel = pygame.Vector2(0, 0)

        self._art = None
        self._sprites = {}
        self._web_src = {}
        self._web_cache = {}
        self._anims = {}
        self._frame_cache = {}
        self._walks = {}           # ruta de la hoja -> [fila][columna] -> superficie

        self._big_active = False   # ya desperto la sala de las Aurantulas
        self._role_sig = None      # (para repartir los roles solo cuando cambia el grupo)
        self._player_vel_fast = pygame.Vector2(0, 0)

    # ---- datos para el resto del juego ------------------------------------
    def targets(self):

        return [s for s in self.spiders if not s.dead]

    def clear(self):

        self.spiders = []
        self.dying = []
        self.shots = []
        self.webs = []

        self.player_in_web = False

        self._big_active = False
        self._role_sig = None

        self._prev_player = None

    # ---- escena de entrada al mapa 2 (ver world/map2_intro.py) -------------------
    def spawn_intro(self, game, spider_pos, aura_pos):
        """Pone las arañas y las aurantulas YA en su lugar, quietas (modo
        idle). Mientras el dialogo esta abierto el juego no se actualiza,
        asi que no se mueven; al cerrarlo despiertan solas."""

        self.clear()

        px, py = game.player.rect.center

        for cls, spots in ((Spider, spider_pos), (Aurantula, aura_pos)):

            for i, (x, y) in enumerate(spots):

                spider = cls(x, y)

                spider.mode = "idle"
                spider.heading = (
                    math.degrees(math.atan2(py - y, px - x)) % 360.0
                )
                spider.cool = (
                    (AURA_FIRST_THROW if cls is Aurantula else FIRST_THROW)
                    + i * 0.4
                )

                self.spiders.append(spider)

        # ya estan en juego (se dibujan y se actualizan). La sala grande de
        # las Aurantulas sigue igual: nacen mas cuando la pises.
        self._active = True
        self._role_sig = None

    # ---- nacimiento (apenas entras al mapa 2) -----------------------------------
    @staticmethod
    def _clear_line(cmap, a, b, step=10.0):
        """True si entre a y b no hay paredes (que nazcan en la misma sala)."""

        d = pygame.Vector2(b) - pygame.Vector2(a)
        n = max(1, int(d.length() / step))

        for i in range(1, n + 1):

            p = pygame.Vector2(a) + d * (i / n)

            if not cmap.point_is_walkable(p.x, p.y):
                return False

        return True

    def _place(self, game, x, y, min_gap):
        """Crea una araña en (x, y) si el lugar sirve; devuelve True si la puso."""

        cmap = game.collision_map

        px, py = game.player.rect.center

        if not SPAWN_AREA.collidepoint(x, y):
            return False

        spider = Spider(x, y)

        if not cmap.can_move(spider.rect):
            return False

        if not self._clear_line(cmap, (px, py), (x, y)):
            return False

        if any(
            math.hypot(x - s.pos.x, y - s.pos.y) < min_gap
            for s in self.spiders
        ):
            return False

        # ya nacen mirandote
        spider.heading = math.degrees(math.atan2(py - y, px - x)) % 360.0

        # que no tiren todas a la vez: cada una un poco despues
        spider.cool = FIRST_THROW + len(self.spiders) * 0.35

        self.spiders.append(spider)

        return True

    def _spawn_all(self, game):
        """Nacen en ronda alrededor tuyo, en la salita de entrada."""

        px, py = game.player.rect.center

        base = random.uniform(0, math.tau)

        for i in range(SPIDER_COUNT):

            target = base + math.tau * i / SPIDER_COUNT

            placed = False

            for jitter in (0.0, 0.25, -0.25, 0.5, -0.5):

                ang = target + jitter

                for radius in SPAWN_RING:

                    if self._place(
                        game,
                        px + math.cos(ang) * radius,
                        py + math.sin(ang) * radius,
                        min_gap=34,
                    ):
                        placed = True
                        break

                if placed:
                    break

        # si la sala es muy chica y faltan: las que falten, en cualquier lugar libre
        tries = 0

        while len(self.spiders) < SPIDER_COUNT and tries < 800:

            tries += 1

            ang = random.uniform(0, math.tau)
            dist = random.uniform(SPAWN_MIN_DIST, SPAWN_MAX_DIST)

            self._place(
                game, px + math.cos(ang) * dist, py + math.sin(ang) * dist,
                min_gap=28,
            )

        # ultimo recurso: cualquier lugar libre de la sala
        tries = 0

        while len(self.spiders) < SPIDER_COUNT and tries < 800:

            tries += 1

            self._place(
                game,
                random.uniform(SPAWN_AREA.left, SPAWN_AREA.right),
                random.uniform(SPAWN_AREA.top, SPAWN_AREA.bottom),
                min_gap=22,
            )

    def _drop(self, game, spider):

        cx, cy = spider.rect.center

        for n, value in enumerate(split_coins(spider.COINS)):

            coin = WorldItem(coin_id_for(value), cx, cy)

            coin.value = value
            coin.sparkle = True

            coin.start_fly(
                (cx, cy),
                (cx + random.randint(-34, 34), cy + random.randint(-34, 34)),
                delay=0.1 + n * 0.03,
                height=18
            )

            game.world_items.append(coin)

        audio.play(spider.SND_DIE, jitter=0.08)

    # ---- Aurantulas: nacimiento y trabajo en equipo ----------------------------
    def _place_aura(self, game, x, y, min_gap, idx):

        if not AURA_SPAWN_AREA.collidepoint(x, y):
            return False

        spider = Aurantula(x, y)

        if not game.collision_map.can_move(spider.rect):
            return False

        if any(
            math.hypot(x - s.pos.x, y - s.pos.y) < min_gap
            for s in self.spiders
        ):
            return False

        px, py = game.player.rect.center

        spider.heading = math.degrees(math.atan2(py - y, px - x)) % 360.0
        spider.cool = AURA_FIRST_THROW + idx * 0.4

        self.spiders.append(spider)

        return True

    def _spawn_aurantulas(self, game):
        """Nacen en ronda alrededor tuyo, ya apuntandote."""

        px, py = game.player.rect.center

        base = random.uniform(0, math.tau)

        made = 0

        for i in range(AURA_COUNT):

            target = base + math.tau * i / AURA_COUNT

            placed = False

            for jitter in (0.0, 0.3, -0.3, 0.6, -0.6):

                for radius in AURA_RING:

                    ang = target + jitter

                    if self._place_aura(
                        game,
                        px + math.cos(ang) * radius,
                        py + math.sin(ang) * radius,
                        min_gap=70, idx=made
                    ):
                        placed = True
                        break

                if placed:
                    break

            if placed:
                made += 1

        # las que falten: en cualquier lugar libre de la sala
        tries = 0

        while made < AURA_COUNT and tries < 800:

            tries += 1

            if self._place_aura(
                game,
                random.uniform(AURA_SPAWN_AREA.left, AURA_SPAWN_AREA.right),
                random.uniform(AURA_SPAWN_AREA.top, AURA_SPAWN_AREA.bottom),
                min_gap=50, idx=made
            ):
                made += 1

        self._role_sig = None

        if made:
            audio.play("aura_screech")

    def _assign_roles(self, game):
        """Si hay una cantidad PAR (2, 4...) piensan en equipo: las mas
        cercanas a vos muerden y las mas lejanas tiran telarañas. Si es
        impar, cada una hace de todo. Se reparte solo cuando cambia el grupo
        (al morir una) para que no cambien de rol a cada rato."""

        auras = [
            s for s in self.spiders
            if isinstance(s, Aurantula) and not s.dead
        ]

        sig = tuple(sorted(s.uid for s in auras))

        if sig == self._role_sig:
            return

        self._role_sig = sig

        n = len(auras)

        if n < 2 or n % 2 == 1:

            for s in auras:
                s.set_role("solo")

            return

        px, py = game.player.rect.center

        auras.sort(key=lambda s: math.hypot(s.pos.x - px, s.pos.y - py))

        half = n // 2

        for i, s in enumerate(auras):
            s.set_role("biter" if i < half else "shooter")

    # ---- tirar el bloque ------------------------------------------------------------
    def throw(self, spider, game, k=0):

        src = pygame.Vector2(spider.rect.center)
        target = pygame.Vector2(game.player.rect.center)

        if isinstance(spider, Aurantula):

            speed = AURA_SHOT_SPEED
            size = AURA_SHOT_SIZE

            direction = self._aura_aim(game, src, target, speed)

            # abanico: las telarañas del medio cubren si cambias de rumbo
            direction = direction.rotate(AURA_SPREAD[k % len(AURA_SPREAD)])

        else:

            speed = SHOT_SPEED
            size = SHOT_SIZE

            direction = _lead_direction(
                src, target, self._player_vel, SHOT_SPEED
            )

        audio.play_at(
            spider.SND_THROW, src, target, radius=700.0
        )

        shot = WebShot(
            src.x, src.y, direction, random.randrange(3),
            speed=speed, size=size
        )
        shot.owner = spider

        self.shots.append(shot)

    def _aura_aim(self, game, src, target, speed):
        """Puntería de la Aurantula: anticipa tu velocidad (medida rapido) y,
        si el punto donde ibas a estar es una pared, tira a donde estas."""

        vel = self._player_vel_fast

        direction = _lead_direction(src, target, vel, speed)

        rel = (target - src).length()
        t = min(1.2, rel / max(1.0, speed))

        predicted = target + vel * t

        if not game.collision_map.point_is_walkable(predicted.x, predicted.y):

            direction = target - src

            if direction.length_squared() < 1e-6:
                return pygame.Vector2(1, 0)

            return direction.normalize()

        return direction

    # ---- telarañas como bloques (nunca se superponen) --------------------------------
    @staticmethod
    def _spot_rect(cx, cy):

        r = pygame.Rect(0, 0, WEB_SIZE, WEB_SIZE)
        r.center = (cx, cy)

        return r

    def _free_spot(self, cmap, cx, cy, rects):
        """Lugar libre mas cercano a (cx, cy) para una telaraña: el mismo punto
        si esta libre o, si no, pegada borde con borde a otra (como bloques).
        None si no hay lugar."""

        half = WEB_SIZE // 2

        cands = [(round(cx), round(cy))]

        for e in rects:

            for y in (round(cy), e.centery):
                cands.append((e.right + half, y))
                cands.append((e.left - half, y))

            for x in (round(cx), e.centerx):
                cands.append((x, e.bottom + half))
                cands.append((x, e.top - half))

        best = None
        best_d = None

        for x, y in cands:

            if not cmap.point_is_walkable(x, y):
                continue

            r = self._spot_rect(x, y)

            if any(r.colliderect(e) for e in rects):
                continue

            d = (x - cx) ** 2 + (y - cy) ** 2

            if best_d is None or d < best_d:
                best, best_d = (x, y), d

        return best

    def _add_web(self, game, x, y, variant, pinned=False):
        """Pone una telaraña sin que se superponga con otra.

        - Normal (bloque que fallo): si cae sobre otra, se aparta hasta el
          lugar libre mas cercano, pegada borde con borde.
        - pinned (la que te atrapo): se queda justo donde estas, para no
          soltarte; las que la pisan son las que se apartan.
        """

        cmap = game.collision_map

        web = WebPatch(x, y, variant)

        if not pinned:

            spot = self._free_spot(
                cmap, web.tx, web.ty,
                [w.target_rect() for w in self.webs],
            )

            if spot is None:
                return None

            web.tx, web.ty = spot

            self.webs.append(web)

            return web

        mine = web.target_rect()

        hit = [w for w in self.webs if w.target_rect().colliderect(mine)]

        # las que mas la pisan se acomodan primero
        hit.sort(key=lambda w: -(
            w.target_rect().clip(mine).width * w.target_rect().clip(mine).height
        ))

        self.webs = [w for w in self.webs if w not in hit]

        keep = [w.target_rect() for w in self.webs] + [mine]

        for old in hit:

            spot = self._free_spot(cmap, old.tx, old.ty, keep)

            if spot is None:
                continue                    # sin lugar: se deshace

            old.tx, old.ty = spot

            keep.append(old.target_rect())

            self.webs.append(old)

        self.webs.append(web)

        return web

    # ---- el bloque te dio ------------------------------------------------------------
    def _hit_player(self, game, shot):

        px, py = game.player.rect.center

        audio.play("web_stick", jitter=0.1)

        if self.player_in_web:

            # ya estabas atrapado (rafaga): la telaraña de abajo se renueva
            for w in self.webs:

                if w.rect.colliderect(game.player.rect):
                    w.age = min(w.age, 1.0)

        else:

            self._add_web(game, px, py, shot.variant, pinned=True)

        if not self._warned:

            self._warned = True

            game.show_message("¡Telaraña! Te ralentiza: sal de ella")

        # la que te atrapo corre hacia vos; las demas, apenas ven que estas
        # dentro de la telaraña (ver update)
        if shot.owner is not None and not shot.owner.dead:
            shot.owner.start_chase()

    def _set_slow(self, game, value):

        if abs(value - self._slow) < 1e-6:
            return

        self._slow = value

        game.web_slow = value

        game._refresh_speed()

    # ---- update ------------------------------------------------------------------
    def update(self, dt, game):

        in_map2 = getattr(game, "current_map", "mapa1") == "mapa2"

        if not in_map2:

            if (
                self._active or self._big_active
                or self.spiders or self.webs or self.shots
            ):
                self.clear()

            self._active = False
            self._big_active = False

            self._set_slow(game, 1.0)

            return

        player = game.player.rect

        # velocidad del jugador (para apuntarle con anticipacion)
        now = pygame.Vector2(player.center)

        if self._prev_player is not None and dt > 0:

            inst = (now - self._prev_player) / dt

            self._player_vel = self._player_vel * 0.6 + inst * 0.4
            self._player_vel_fast = self._player_vel_fast * 0.25 + inst * 0.75

        self._prev_player = now

        if not self._big_active and AURA_TRIGGER.collidepoint(player.center):

            self._big_active = True

            self._spawn_aurantulas(game)

        if not self._active:

            if TRIGGER_AREA.collidepoint(player.center):

                self._active = True

                self._spawn_all(game)

            elif not self._big_active:

                # todavia no entraste a ninguna sala: no hay arañas ni telarañas
                self._set_slow(game, 1.0)

                return

        self._assign_roles(game)

        for spider in self.spiders:

            if spider.dead:

                if not spider.dropped:

                    spider.dropped = True

                    self._drop(game, spider)

                    self.dying.append([spider, 0.0])

                continue

            spider.update(dt, game, self)

            spider.footsteps(dt, game)

        self.spiders = [s for s in self.spiders if not s.dead]

        for item in self.dying:
            item[1] += dt

        self.dying = [i for i in self.dying if i[1] < DEATH_TIME]

        cmap = game.collision_map

        hit_rect = player.inflate(*HIT_PAD)

        for shot in self.shots:

            step = shot.speed * dt

            shot.age += dt
            shot.pos += shot.dir * step
            shot.travelled += step
            shot.rect.center = (round(shot.pos.x), round(shot.pos.y))

            if shot.rect.colliderect(hit_rect):

                self._hit_player(game, shot)

                shot.done = True

            elif (
                shot.travelled >= SHOT_RANGE
                or not cmap.point_is_walkable(shot.pos.x, shot.pos.y)
            ):

                # fallo: el bloque cae en el piso y se queda un rato
                land = shot.pos

                if not cmap.point_is_walkable(land.x, land.y):
                    # se choco con una pared: cae un paso antes (en el piso)
                    land = shot.pos - shot.dir * step

                self._add_web(game, land.x, land.y, shot.variant)

                shot.done = True

        self.shots = [s for s in self.shots if not s.done]

        for web in self.webs:

            web.age += dt
            web.slide(dt)

        self.webs = [w for w in self.webs if w.age < WEB_LIFE]

        inside = any(w.rect.colliderect(player) for w in self.webs)

        # saliste de la telaraña: todas intentan tirarte otra enseguida
        if self.player_in_web and not inside:

            for spider in self.spiders:

                if spider.mode == "aim" and spider.wind <= 0:
                    spider.cool = min(spider.cool, random.uniform(*REWEB_DELAY))

        self.throw_lock = max(0.0, self.throw_lock - dt)

        # las que ven que estas dentro de una telaraña vienen a pegarte: las
        # mas cercanas primero y, de las comunes, a lo sumo MAX_ATTACKERS
        if inside and ALL_CHASE:

            def _dist(s):
                return math.hypot(
                    s.rect.centerx - player.centerx,
                    s.rect.centery - player.centery,
                )

            chasing = sum(
                1 for s in self.spiders
                if not s.dead and s.mode == "chase"
                and not isinstance(s, Aurantula)
            )

            for spider in sorted(self.spiders, key=_dist):

                if spider.dead or spider.mode != "aim":
                    continue

                if _dist(spider) > LOSE_DIST:
                    continue

                if not isinstance(spider, Aurantula):

                    if chasing >= MAX_ATTACKERS:
                        continue

                    chasing += 1

                spider.start_chase()

        self.player_in_web = inside

        self._set_slow(game, WEB_SLOW if inside else 1.0)

    # ---- dibujo ------------------------------------------------------------------
    def _base(self, zoom):

        key = round(zoom, 3)

        img = self._sprites.get(key)

        if img is None:

            if self._art is None:
                self._art = _load_art()

            w = max(2, int(DRAW_WIDTH * zoom))
            h = max(2, int(w * self._art.get_height() / self._art.get_width()))

            img = pygame.transform.smoothscale(self._art, (w, h))

            self._sprites[key] = img

        return img

    def _walk_frames(self, path=None):
        """Hoja de caminata: [direccion][cuadro]. [] si no existe."""

        path = path or WALK_PATH

        frames = self._walks.get(path)

        if frames is not None:
            return frames

        frames = []

        try:
            sheet = pygame.image.load(str(path)).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            sheet = None

        if sheet is not None:

            cw = sheet.get_width() // WALK_COLS
            ch = sheet.get_height() // WALK_ROWS

            if cw > 0 and ch > 0:

                frames = [
                    [
                        sheet.subsurface((c * cw, r * ch, cw, ch)).copy()
                        for c in range(WALK_COLS)
                    ]
                    for r in range(WALK_ROWS)
                ]

        self._walks[path] = frames

        return frames

    def _pose(self, spider, walk_sheet=False):
        """(escala_x, escala_y, angulo, desplazamiento_y) segun la animacion."""

        t = spider.anim_t

        sx = sy = 1.0
        ang = 0.0
        dy = 0.0

        if spider.wind > 0:

            # preparar: se echa hacia atras y se agacha
            k = 1.0 - spider.wind / spider.WIND_UP

            sx = 1.0 + 0.10 * k
            sy = 1.0 - 0.18 * k
            ang = -8.0 * k * spider.face

        elif spider.shoot_t > 0:

            # soltar: se estira de golpe
            k = spider.shoot_t / 0.25

            sx = 1.0 - 0.10 * k
            sy = 1.0 + 0.16 * k
            ang = 6.0 * k * spider.face

        elif spider.moving and walk_sheet:

            # las patas ya se mueven en la hoja: no hace falta rebotar
            pass

        elif spider.moving:

            fast = 1.5 if spider.mode == "chase" else 1.0

            ph = math.sin(t * 16.0 * fast)

            dy = -abs(ph) * 1.6
            ang = ph * 5.0
            sx = 1.0 + 0.04 * ph
            sy = 1.0 - 0.04 * ph

        else:

            b = math.sin(t * 2.6)

            sy = 1.0 + 0.035 * b
            sx = 1.0 - 0.02 * b

        if spider.flash > 0:

            dy += math.sin(t * 90.0) * 1.2

        return sx, sy, ang, dy

    def _draw_spider(self, screen, camera, spider, scale=1.0, alpha=255):

        zoom = camera.zoom

        walk = self._walk_frames(spider.WALK_PATH)

        if walk:
            return self._draw_walker(
                screen, camera, spider, walk, scale, alpha
            )

        base = self._base(zoom)

        sx, sy, ang, dy = self._pose(spider)

        w = max(2, int(base.get_width() * sx * scale))
        h = max(2, int(base.get_height() * sy * scale))

        img = pygame.transform.scale(base, (w, h))

        if spider.face < 0:
            img = pygame.transform.flip(img, True, False)

        if abs(ang) > 0.5:
            img = pygame.transform.rotate(img, ang)

        if spider.flash > 0:

            img = img.copy()
            img.fill((120, 120, 120, 0), special_flags=pygame.BLEND_RGBA_ADD)

        if alpha < 255:

            img = img.copy()
            img.set_alpha(alpha)

        dest = camera.apply(spider.rect)

        shadow = pygame.Surface(
            (max(2, int(dest.width * 1.4 * scale)),
             max(2, int(dest.height * 0.7 * scale))),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            shadow, (0, 0, 0, int(90 * alpha / 255)), shadow.get_rect()
        )

        screen.blit(shadow, shadow.get_rect(center=(dest.centerx, dest.bottom)))

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx,
                    dest.bottom + int((3 + dy) * zoom)
                )
            )
        )

    def _draw_walker(self, screen, camera, spider, walk, scale, alpha):
        """Dibuja la araña con la hoja de caminata, mirando hacia donde mira."""

        zoom = camera.zoom

        sx, sy, ang, dy = self._pose(spider, walk_sheet=True)

        row = int(round(spider.heading / 45.0)) % WALK_ROWS

        col = (
            int(spider.walk_phase * WALK_COLS) % WALK_COLS
            if spider.moving else 0
        )

        cell = walk[row][col]

        size = spider.DRAW_CELL * zoom

        w = max(2, int(size * sx * scale))
        h = max(2, int(size * sy * scale))

        img = pygame.transform.scale(cell, (w, h))

        if spider.flash > 0:

            img = img.copy()
            img.fill((120, 120, 120, 0), special_flags=pygame.BLEND_RGBA_ADD)

        if alpha < 255:

            img = img.copy()
            img.set_alpha(alpha)

        dest = camera.apply(spider.rect)

        center = (dest.centerx, dest.centery + int(dy * zoom))

        shadow = pygame.Surface(
            (max(2, int(size * 0.55 * scale)),
             max(2, int(size * 0.28 * scale))),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            shadow, (0, 0, 0, int(80 * alpha / 255)), shadow.get_rect()
        )

        screen.blit(
            shadow,
            shadow.get_rect(center=(center[0], center[1] + int(size * 0.10)))
        )

        screen.blit(img, img.get_rect(center=center))

    def _web_img(self, variant, side, alpha):

        key = (variant, side, int(alpha * 8))

        img = self._web_cache.get(key)

        if img is None:

            src = self._web_src.get(variant)

            if src is None:

                src = _load_web(variant)

                self._web_src[variant] = src

            if src is None:

                img = pygame.Surface((4, 4), pygame.SRCALPHA)

            else:

                img = pygame.transform.smoothscale(
                    src, (max(4, side), max(4, side))
                )

                img.set_alpha(int(255 * alpha))

            self._web_cache[key] = img

        return img

    def _anim(self, variant, kind):
        """Cuadros de una animacion de telaraña ([] si no existe la tira)."""

        key = (variant, kind)

        frames = self._anims.get(key)

        if frames is None:

            frames = _load_strip(
                COMBAT_DIR / f"telarana_{variant + 1}_{kind}.png"
            )

            self._anims[key] = frames

        return frames

    def _frame_img(self, variant, kind, idx, side):

        key = (variant, kind, idx, side)

        img = self._frame_cache.get(key)

        if img is None:

            frames = self._anim(variant, kind)

            img = pygame.transform.smoothscale(
                frames[idx], (max(4, side), max(4, side))
            )

            self._frame_cache[key] = img

        return img

    def _patch_img(self, web, side):
        """Imagen de un bloque en el piso segun su edad: aparecer -> suelo ->
        deshacer. Sin tiras usa la imagen fija con fundido."""

        appear = self._anim(web.variant, "aparecer")
        idle = self._anim(web.variant, "suelo")
        undo = self._anim(web.variant, "deshacer")

        left = WEB_LIFE - web.age

        if appear and web.age < APPEAR_TIME:

            idx = min(len(appear) - 1, int(web.age / APPEAR_TIME * len(appear)))

            return self._frame_img(web.variant, "aparecer", idx, side)

        if undo and left <= WEB_FADE:

            k = 1.0 - max(0.0, left) / WEB_FADE

            idx = min(len(undo) - 1, int(k * len(undo)))

            return self._frame_img(web.variant, "deshacer", idx, side)

        if idle:

            idx = int(web.age * IDLE_FPS) % len(idle)

            return self._frame_img(web.variant, "suelo", idx, side)

        return self._web_img(web.variant, side, web.alpha)

    def draw(self, screen, camera):

        if not (self._active or self._big_active):
            return

        for web in self.webs:

            dest = camera.apply(web.rect)

            screen.blit(self._patch_img(web, dest.width), dest)

        for spider, t in self.dying:

            k = min(1.0, t / DEATH_TIME)

            self._draw_spider(
                screen, camera, spider, scale=1.0 - 0.5 * k,
                alpha=int(255 * (1.0 - k))
            )

        for spider in self.spiders:
            self._draw_spider(screen, camera, spider)

        for shot in self.shots:

            center = camera.apply(shot.rect).center

            # sale chiquita y va creciendo mientras vuela (arranca rapido y
            # se va frenando hasta llegar al tamaño final)
            k = min(1.0, shot.travelled / SHOT_GROW_DIST)
            k = 1.0 - (1.0 - k) * (1.0 - k)

            world_side = SHOT_DRAW_START + (SHOT_DRAW_END - SHOT_DRAW_START) * k

            # tamaños pares para no llenar la memoria de imagenes casi iguales
            side = max(4, int(round(world_side * camera.zoom / 2.0)) * 2)

            fly = self._anim(shot.variant, "vuelo")

            if fly:

                idx = int(shot.age * FLY_FPS) % len(fly)

                img = self._frame_img(shot.variant, "vuelo", idx, side)

            else:
                img = self._web_img(shot.variant, side, 1.0)

            screen.blit(img, img.get_rect(center=center))