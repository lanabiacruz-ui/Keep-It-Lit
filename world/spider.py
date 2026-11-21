"""Araña (enemigo del mapa 2).

- NO aparece en ninguna oleada: solo existe en el mapa 2. Al entrar al mapa 2
  nacen SPIDER_COUNT arañas repartidas; al salir desaparecen.
- Ataque: te tira un BLOQUE DE TELARAÑA apuntado a donde estas.
    * Si el bloque te da: queda pegado a vos (te ralentiza mucho mientras
      estes dentro) y la araña va hacia vos y te empieza a pegar.
    * Si falla: el bloque cae en el piso y sigue ralentizando a quien lo
      pise; ella vuelve a apuntar hasta darte.
- La telaraña desaparece con el tiempo (WEB_LIFE).
- Sin animacion por ahora (una sola imagen, que se espeja segun donde estes).

Imagen: assets/maps/combate/arana.png (158x110, fondo transparente).
Si falta se dibuja un reemplazo simple.
"""

import math
import random
from pathlib import Path

import pygame

from core.audio_manager import audio
from world.items import WorldItem, coin_id_for, split_coins

ART_PATH = (
    Path(__file__).resolve().parent.parent
    / "assets" / "maps" / "combate" / "arana.png"
)

# ---- cantidad / vida / tamaño --------------------------------------------
SPIDER_COUNT = 4
HP = 12
DRAW_WIDTH = 52              # ancho dibujado (la imagen es 158x110)
HITBOX = (34, 22)
COINS = 25

# ---- movimiento ------------------------------------------------------------
WALK_SPEED = 38              # acomodarse a distancia
CHASE_SPEED = 78             # cuando ya te tiene pegada la telaraña
SIGHT = 430                  # a esta distancia te empieza a apuntar
KEEP_MIN = 130               # si te acercas mas que esto, se aleja
KEEP_MAX = 250               # si estas mas lejos, se acerca
SPAWN_MIN_DIST = 260         # al nacer, lejos del jugador
SPAWN_MAX_DIST = 900

# ---- ataque a distancia (bloque de telaraña) ---------------------------------
FIRST_THROW = 1.0
THROW_COOLDOWN = 2.3
SHOT_SPEED = 200
SHOT_RANGE = 360
SHOT_SIZE = 24

WEB_SIZE = 54                # lado del bloque de telaraña en el piso
WEB_LIFE = 9.0               # segundos hasta que se va solo
WEB_FADE = 2.0               # los ultimos segundos se va apagando
WEB_SLOW = 0.35              # multiplicador de velocidad dentro (bastante)

# ---- ataque cuerpo a cuerpo (despues de atinarte) ----------------------------
HIT_DAMAGE = 0.12            # vida del jugador va de 0 a 1
HIT_INTERVAL = 1.1
CHASE_MAX = 14.0             # si no te alcanza en este tiempo, vuelve a apuntar
LOSE_DIST = 420


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


def _web_surface(size):
    """Bloque de telaraña: cuadrado blanquecino translucido con hilos."""

    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    pygame.draw.rect(
        surf, (235, 238, 245, 70), surf.get_rect(), border_radius=size // 5
    )

    c = size // 2
    line = (245, 247, 252, 210)

    for k in range(8):

        a = k * math.pi / 4

        pygame.draw.line(
            surf, line, (c, c),
            (c + math.cos(a) * c, c + math.sin(a) * c), 1
        )

    for r in (c * 0.35, c * 0.65, c * 0.95):

        pts = [
            (c + math.cos(k * math.pi / 4) * r,
             c + math.sin(k * math.pi / 4) * r)
            for k in range(8)
        ]

        pygame.draw.polygon(surf, line, pts, 1)

    pygame.draw.rect(
        surf, (250, 250, 255, 230), surf.get_rect(), 2,
        border_radius=size // 5
    )

    return surf


class WebShot:
    """Bloque de telaraña volando hacia el jugador."""

    def __init__(self, x, y, direction):

        self.pos = pygame.Vector2(x, y)
        self.dir = pygame.Vector2(direction)
        self.travelled = 0.0

        self.rect = pygame.Rect(0, 0, SHOT_SIZE, SHOT_SIZE)
        self.rect.center = (round(x), round(y))

        self.done = False


class WebPatch:
    """Bloque de telaraña en el piso: ralentiza y desaparece con el tiempo."""

    def __init__(self, x, y):

        self.rect = pygame.Rect(0, 0, WEB_SIZE, WEB_SIZE)
        self.rect.center = (round(x), round(y))

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

        self.mode = "idle"          # idle / aim / chase
        self.cool = FIRST_THROW
        self.chase_t = 0.0
        self.hit_cool = 0.5
        self.face = 1

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

    # ---- movimiento -------------------------------------------------------
    def _move(self, delta, cmap):

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

    def update(self, dt, game, mgr):

        cmap = game.collision_map

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        # empuje al recibir un golpe
        if self.vel.length_squared() > 1.0:

            self._move(self.vel * dt, cmap)

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

        if self.mode == "idle":

            if sees and dist <= SIGHT:
                self.mode = "aim"
                self.cool = FIRST_THROW

            return

        if not sees or dist > SIGHT * 1.5:

            self.mode = "idle"

            return

        if self.mode == "aim":

            if dist > 1:

                direction = d / dist

                if dist > KEEP_MAX:
                    self._move(direction * WALK_SPEED * dt, cmap)

                elif dist < KEEP_MIN:
                    self._move(-direction * WALK_SPEED * dt, cmap)

            self.cool -= dt

            if self.cool <= 0 and dist > 1:

                self.cool = THROW_COOLDOWN

                mgr.shots.append(WebShot(me.x, me.y, d / dist))

            return

        # chase: ya te atino, viene a pegarte
        self.chase_t += dt

        if dist > LOSE_DIST or self.chase_t > CHASE_MAX:

            self.mode = "aim"
            self.cool = 1.5

            return

        touching = self.rect.inflate(10, 10).colliderect(game.player.rect)

        if not touching and dist > 1:
            self._move((d / dist) * CHASE_SPEED * dt, cmap)

        self.hit_cool -= dt

        if touching and self.hit_cool <= 0:

            self.hit_cool = HIT_INTERVAL

            game.take_damage(HIT_DAMAGE, common=True, source=self)


class SpiderManager:

    def __init__(self):

        self.spiders = []
        self.shots = []
        self.webs = []

        self._active = False
        self._slow = 1.0
        self._warned = False

        self._art = None
        self._sprites = {}
        self._web_cache = {}

    # ---- datos para el resto del juego ------------------------------------
    def targets(self):

        return [s for s in self.spiders if not s.dead]

    def clear(self):

        self.spiders = []
        self.shots = []
        self.webs = []

    # ---- nacimiento (solo al entrar al mapa 2) ----------------------------------
    def _spawn_all(self, game):

        cmap = game.collision_map

        px, py = game.player.rect.center

        tries = 0

        while len(self.spiders) < SPIDER_COUNT and tries < 600:

            tries += 1

            x = random.randint(40, cmap.world_width - 40)
            y = random.randint(40, cmap.world_height - 40)

            dist = math.hypot(x - px, y - py)

            if dist < SPAWN_MIN_DIST or dist > SPAWN_MAX_DIST:
                continue

            spider = Spider(x, y)

            if not cmap.can_move(spider.rect):
                continue

            if any(
                math.hypot(x - s.pos.x, y - s.pos.y) < 120
                for s in self.spiders
            ):
                continue

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

    # ---- el bloque te dio ------------------------------------------------------
    def _hit_player(self, game, shot_owner_pos):

        px, py = game.player.rect.center

        self.webs.append(WebPatch(px, py))

        if not self._warned:

            self._warned = True

            game.show_message("¡Telaraña! Te ralentiza: sal de ella")

        # la araña mas cercana al disparo es la que te viene a pegar
        best = None
        best_d = 1e9

        for s in self.spiders:

            if s.dead:
                continue

            dd = (s.pos - shot_owner_pos).length()

            if dd < best_d:
                best, best_d = s, dd

        if best is not None:
            best.start_chase()

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

        if not self._active:

            self._active = True

            self._spawn_all(game)

        player = game.player.rect

        for spider in self.spiders:

            if spider.dead:

                if not spider.dropped:

                    spider.dropped = True

                    self._drop(game, spider)

                continue

            spider.update(dt, game, self)

        self.spiders = [s for s in self.spiders if not s.dead]

        cmap = game.collision_map

        for shot in self.shots:

            step = SHOT_SPEED * dt

            shot.pos += shot.dir * step
            shot.travelled += step
            shot.rect.center = (round(shot.pos.x), round(shot.pos.y))

            if shot.rect.colliderect(player):

                # el origen aproximado: hacia atras por el recorrido
                origin = shot.pos - shot.dir * shot.travelled

                self._hit_player(game, origin)

                shot.done = True

            elif (
                shot.travelled >= SHOT_RANGE
                or not cmap.point_is_walkable(shot.pos.x, shot.pos.y)
            ):

                # fallo: el bloque cae en el piso y se queda un rato
                self.webs.append(WebPatch(shot.pos.x, shot.pos.y))

                shot.done = True

        self.shots = [s for s in self.shots if not s.done]

        for web in self.webs:
            web.age += dt

        self.webs = [w for w in self.webs if w.age < WEB_LIFE]

        inside = any(w.rect.colliderect(player) for w in self.webs)

        self._set_slow(game, WEB_SLOW if inside else 1.0)

    # ---- dibujo ------------------------------------------------------------------
    def _sprite(self, zoom, flip, flash):

        key = (round(zoom, 3), flip, flash)

        img = self._sprites.get(key)

        if img is None:

            if self._art is None:
                self._art = _load_art()

            w = max(2, int(DRAW_WIDTH * zoom))
            h = max(2, int(w * self._art.get_height() / self._art.get_width()))

            img = pygame.transform.smoothscale(self._art, (w, h))

            if flip:
                img = pygame.transform.flip(img, True, False)

            if flash:

                img = img.copy()
                img.fill((120, 120, 120, 0), special_flags=pygame.BLEND_RGBA_ADD)

            self._sprites[key] = img

        return img

    def _web_img(self, side, alpha):

        key = (side, int(alpha * 8))

        img = self._web_cache.get(key)

        if img is None:

            img = pygame.transform.smoothscale(
                _web_surface(64), (max(4, side), max(4, side))
            )

            img.set_alpha(int(255 * alpha))

            self._web_cache[key] = img

        return img

    def draw(self, screen, camera):

        if not self._active:
            return

        for web in self.webs:

            dest = camera.apply(web.rect)

            screen.blit(self._web_img(dest.width, web.alpha), dest)

        for spider in self.spiders:

            dest = camera.apply(spider.rect)

            shadow = pygame.Surface(
                (max(2, int(dest.width * 1.3)), max(2, int(dest.height * 0.6))),
                pygame.SRCALPHA
            )

            pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())

            screen.blit(
                shadow, shadow.get_rect(center=(dest.centerx, dest.bottom))
            )

            sprite = self._sprite(
                camera.zoom, spider.face < 0, spider.flash > 0
            )

            screen.blit(
                sprite,
                sprite.get_rect(
                    midbottom=(dest.centerx, dest.bottom + int(4 * camera.zoom))
                )
            )

        for shot in self.shots:

            dest = camera.apply(shot.rect)

            screen.blit(self._web_img(dest.width, 1.0), dest)