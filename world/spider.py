"""Araña (enemigo del mapa 2).

- NO aparece en ninguna oleada: solo existe en el mapa 2. Nace apenas entras
  (SPIDER_COUNT arañas cerca, ya apuntandote) y desaparece al salir.
- Se ALEJA de vos: nunca se acerca por su cuenta.
- Ataque: te tira un BLOQUE DE TELARAÑA con muy buena punteria (calcula a
  donde vas a estar).
    * Si el bloque te da: queda pegado a vos (te ralentiza mucho mientras
      estes dentro) y SOLO la araña que te atrapo va hacia vos a pegarte.
    * Si falla: el bloque cae en el piso y sigue ralentizando a quien lo
      pise. La telaraña desaparece con el tiempo (WEB_LIFE).
- La telaraña tiene 3 imagenes distintas (assets/maps/combate/telarana_1/2/3.png);
  solo cambia el dibujo, no el comportamiento. Cada una tiene sus animaciones
  (tiras de cuadros cuadrados, ver tools/make_web_frames.py):
      telarana_<n>_vuelo.png     bloque volando (en bucle)
      telarana_<n>_aparecer.png  cae al piso / se pega al jugador
      telarana_<n>_suelo.png     quieta en el piso (en bucle)
      telarana_<n>_deshacer.png  se desarma al final de su vida
  Si falta alguna tira se usa la imagen fija telarana_<n>.png.
- Mira SIEMPRE hacia vos (8 direcciones) y camina moviendo las patas
  (hoja assets/maps/combate/arana_caminar.png: 6 cuadros x 8 direcciones,
  ver tools/make_spider_frames.py). Cuando se aleja camina "de espaldas":
  mirandote pero con las patas yendo para atras.
- Otras animaciones (por transformaciones): respirar, preparar el
  lanzamiento, atacar, golpe y muerte.
- Si falta la hoja usa la imagen fija assets/maps/combate/arana.png.
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
WALK_COLS = 6                # cuadros de la caminata
WALK_ROWS = 8                # direcciones (8, en sentido horario desde la derecha)
WEB_PATHS = [COMBAT_DIR / f"telarana_{n}.png" for n in (1, 2, 3)]

# Clave en la enciclopedia
CODEX_KEY = "arana"
DISCOVER_DISTANCE = 520

# ---- cantidad / vida / tamaño (del tamaño del jugador) ---------------------------
SPIDER_COUNT = 4
HP = 12
DRAW_WIDTH = 36              # ancho dibujado de la imagen fija (158x110)
DRAW_CELL = 48               # tamaño dibujado de un cuadro de la hoja de caminata
TURN_SPEED = 720             # grados por segundo al girar para mirarte
WALK_RATE = 40.0             # velocidad / WALK_RATE = ciclos de patas por segundo
HITBOX = (22, 14)
COINS = 25

# ---- movimiento ---------------------------------------------------------------------
FLEE_SPEED = 92              # se aleja de vos
CHASE_SPEED = 80             # solo despues de atraparte
SIGHT = 560                  # a esta distancia te apunta
KEEP_AWAY = 230              # si te acercas mas que esto, se aleja
SPAWN_MIN_DIST = 170         # al nacer: cerca, pero no encima
SPAWN_MAX_DIST = 360

# ---- bloque de telaraña ----------------------------------------------------------------
FIRST_THROW = 0.55
THROW_COOLDOWN = 1.9
WIND_UP = 0.30               # tiempo de la animacion de "preparar" antes de tirar
SHOT_SPEED = 260
SHOT_RANGE = 520
SHOT_SIZE = 22
HIT_PAD = (14, 22)           # el bloque cuenta como "te dio" un poco antes

WEB_SIZE = 48                # lado del bloque de telaraña en el piso
WEB_LIFE = 9.0               # segundos hasta que se va solo
WEB_FADE = 2.0               # los ultimos segundos se va apagando
WEB_SLOW = 0.35              # multiplicador de velocidad dentro (bastante)

APPEAR_TIME = 0.30           # duracion de la animacion "aparecer"
FLY_FPS = 14                 # cuadros por segundo del vuelo
IDLE_FPS = 6                 # cuadros por segundo de la telaraña en el piso

# ---- cuerpo a cuerpo (solo despues de atraparte) -------------------------------------
HIT_DAMAGE = 0.12            # la vida del jugador va de 0 a 1
HIT_INTERVAL = 1.1
CHASE_MAX = 10.0
LOSE_DIST = 480

DEATH_TIME = 0.35


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


def _web_fallback(variant):
    """Dibujo simple por si faltan las imagenes (3 estilos distintos)."""

    s = 64
    surf = pygame.Surface((s, s), pygame.SRCALPHA)

    pygame.draw.rect(surf, (235, 238, 245, 70), surf.get_rect(),
                     border_radius=12)

    line = (245, 247, 252, 215)
    c = s // 2

    if variant == 0:

        for k in range(8):

            a = k * math.pi / 4

            pygame.draw.line(
                surf, line, (c, c),
                (c + math.cos(a) * (c - 2), c + math.sin(a) * (c - 2))
            )

    elif variant == 1:

        rng = random.Random(7)

        for _ in range(14):

            pygame.draw.line(
                surf, line,
                (rng.randint(2, s - 3), rng.randint(2, s - 3)),
                (rng.randint(2, s - 3), rng.randint(2, s - 3))
            )

    else:

        for r in (8, 16, 24, 30):
            pygame.draw.circle(surf, line, (c, c), r, 1)

    pygame.draw.rect(surf, (250, 250, 255, 230), surf.get_rect(), 2,
                     border_radius=12)

    return surf


def _load_web(variant):

    try:
        return pygame.image.load(str(WEB_PATHS[variant])).convert_alpha()
    except (pygame.error, FileNotFoundError, OSError):
        return _web_fallback(variant)


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

    def __init__(self, x, y, direction, variant):

        self.pos = pygame.Vector2(x, y)
        self.origin = pygame.Vector2(x, y)
        self.dir = pygame.Vector2(direction)
        self.travelled = 0.0
        self.variant = variant
        self.owner = None
        self.age = 0.0

        self.rect = pygame.Rect(0, 0, SHOT_SIZE, SHOT_SIZE)
        self.rect.center = (round(x), round(y))

        self.done = False


class WebPatch:
    """Bloque de telaraña en el piso: ralentiza y desaparece con el tiempo."""

    def __init__(self, x, y, variant):

        self.rect = pygame.Rect(0, 0, WEB_SIZE, WEB_SIZE)
        self.rect.center = (round(x), round(y))

        self.variant = variant
        self.age = 0.0

    @property
    def alpha(self):

        left = WEB_LIFE - self.age

        if left >= WEB_FADE:
            return 1.0

        return max(0.0, left / WEB_FADE)


class Spider:

    def __init__(self, x, y):

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
        self.hit_cool = 0.5
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

        self.hp -= amount
        self.flash = 0.12

    def start_chase(self):

        self.mode = "chase"
        self.chase_t = 0.0
        self.hit_cool = 0.5
        self.wind = 0.0

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
            game.discover_enemy(CODEX_KEY)

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

                self.cool -= dt

                if self.cool <= 0:
                    self.wind = WIND_UP

            return

        # chase: te atrapo en su telaraña, viene a pegarte
        self.chase_t += dt

        if dist > LOSE_DIST or self.chase_t > CHASE_MAX:

            self.mode = "aim"
            self.cool = 1.2

            return

        touching = self.rect.inflate(10, 10).colliderect(game.player.rect)

        if not touching and dist > 1:

            self.moving = self._move_dir(d, CHASE_SPEED, dt, cmap)

            if self.moving:
                self.walk_phase += dt * CHASE_SPEED / WALK_RATE

        self.hit_cool -= dt

        if touching and self.hit_cool <= 0:

            self.hit_cool = HIT_INTERVAL
            self.shoot_t = 0.2

            game.take_damage(HIT_DAMAGE, common=True, source=self)


class SpiderManager:

    def __init__(self):

        self.spiders = []
        self.dying = []          # [spider, tiempo] animacion de muerte
        self.shots = []
        self.webs = []

        self._active = False
        self._slow = 1.0
        self._warned = False

        self._prev_player = None
        self._player_vel = pygame.Vector2(0, 0)

        self._art = None
        self._sprites = {}
        self._web_src = {}
        self._web_cache = {}
        self._anims = {}
        self._frame_cache = {}
        self._walk = None          # [fila][columna] -> superficie (None = sin cargar)
        self._walk_tried = False

    # ---- datos para el resto del juego ------------------------------------
    def targets(self):

        return [s for s in self.spiders if not s.dead]

    def clear(self):

        self.spiders = []
        self.dying = []
        self.shots = []
        self.webs = []

        self._prev_player = None

    # ---- nacimiento (apenas entras al mapa 2) -----------------------------------
    def _spawn_all(self, game):

        cmap = game.collision_map

        px, py = game.player.rect.center

        tries = 0

        while len(self.spiders) < SPIDER_COUNT and tries < 800:

            tries += 1

            ang = random.uniform(0, math.tau)
            dist = random.uniform(SPAWN_MIN_DIST, SPAWN_MAX_DIST)

            x = px + math.cos(ang) * dist
            y = py + math.sin(ang) * dist

            spider = Spider(x, y)

            if not cmap.can_move(spider.rect):
                continue

            if any(
                math.hypot(x - s.pos.x, y - s.pos.y) < 90
                for s in self.spiders
            ):
                continue

            # que no nazcan todas pegadas: cada una tira un poco despues
            spider.cool = FIRST_THROW + len(self.spiders) * 0.45

            self.spiders.append(spider)

    def _drop(self, game, spider):

        cx, cy = spider.rect.center

        for n, value in enumerate(split_coins(COINS)):

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

        audio.play("enemy_die")

    # ---- tirar el bloque ------------------------------------------------------------
    def throw(self, spider, game):

        src = pygame.Vector2(spider.rect.center)
        target = pygame.Vector2(game.player.rect.center)

        direction = _lead_direction(
            src, target, self._player_vel, SHOT_SPEED
        )

        shot = WebShot(src.x, src.y, direction, random.randrange(3))
        shot.owner = spider

        self.shots.append(shot)

    # ---- el bloque te dio ------------------------------------------------------------
    def _hit_player(self, game, shot):

        px, py = game.player.rect.center

        self.webs.append(WebPatch(px, py, shot.variant))

        if not self._warned:

            self._warned = True

            game.show_message("¡Telaraña! Te ralentiza: sal de ella")

        # SOLO la araña que te atrapo va hacia vos
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

            if self._active or self.spiders or self.webs or self.shots:
                self.clear()

            self._active = False

            self._set_slow(game, 1.0)

            return

        player = game.player.rect

        # velocidad del jugador (para apuntarle con anticipacion)
        now = pygame.Vector2(player.center)

        if self._prev_player is not None and dt > 0:

            inst = (now - self._prev_player) / dt

            self._player_vel = self._player_vel * 0.6 + inst * 0.4

        self._prev_player = now

        if not self._active:

            self._active = True

            self._spawn_all(game)

        for spider in self.spiders:

            if spider.dead:

                if not spider.dropped:

                    spider.dropped = True

                    self._drop(game, spider)

                    self.dying.append([spider, 0.0])

                continue

            spider.update(dt, game, self)

        self.spiders = [s for s in self.spiders if not s.dead]

        for item in self.dying:
            item[1] += dt

        self.dying = [i for i in self.dying if i[1] < DEATH_TIME]

        cmap = game.collision_map

        hit_rect = player.inflate(*HIT_PAD)

        for shot in self.shots:

            step = SHOT_SPEED * dt

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
                self.webs.append(WebPatch(shot.pos.x, shot.pos.y, shot.variant))

                shot.done = True

        self.shots = [s for s in self.shots if not s.done]

        for web in self.webs:
            web.age += dt

        self.webs = [w for w in self.webs if w.age < WEB_LIFE]

        inside = any(w.rect.colliderect(player) for w in self.webs)

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

    def _walk_frames(self):
        """Hoja de caminata: [direccion][cuadro]. [] si no existe."""

        if not self._walk_tried:

            self._walk_tried = True

            try:
                sheet = pygame.image.load(str(WALK_PATH)).convert_alpha()
            except (pygame.error, FileNotFoundError, OSError):
                sheet = None

            if sheet is not None:

                cw = sheet.get_width() // WALK_COLS
                ch = sheet.get_height() // WALK_ROWS

                if cw > 0 and ch > 0:

                    self._walk = [
                        [
                            sheet.subsurface((c * cw, r * ch, cw, ch)).copy()
                            for c in range(WALK_COLS)
                        ]
                        for r in range(WALK_ROWS)
                    ]

        return self._walk or []

    def _pose(self, spider, walk_sheet=False):
        """(escala_x, escala_y, angulo, desplazamiento_y) segun la animacion."""

        t = spider.anim_t

        sx = sy = 1.0
        ang = 0.0
        dy = 0.0

        if spider.wind > 0:

            # preparar: se echa hacia atras y se agacha
            k = 1.0 - spider.wind / WIND_UP

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

        walk = self._walk_frames()

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

        size = DRAW_CELL * zoom

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

            img = pygame.transform.smoothscale(src, (max(4, side), max(4, side)))

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

        if not self._active:
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

            dest = camera.apply(shot.rect)

            fly = self._anim(shot.variant, "vuelo")

            if fly:

                idx = int(shot.age * FLY_FPS) % len(fly)

                img = self._frame_img(shot.variant, "vuelo", idx, dest.width)

            else:
                img = self._web_img(shot.variant, dest.width, 1.0)

            screen.blit(img, dest)