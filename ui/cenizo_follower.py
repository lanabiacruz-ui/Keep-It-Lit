"""Cenizo flotando en el mundo, al lado del jugador.

Mientras dura el tutorial (los objetivos de una partida nueva) Cenizo
aparece junto al jugador y lo persigue. Cuando el tutorial termina se queda
un rato (LINGER segundos) y despues se desvanece solo.

La escena del mapa 2 (ui/map2_scene.py) tambien lo usa: lo pone al lado del
jugador, lo mantiene ahi (set_hold) y el rayo del monstruo le apunta.

Cambiar tamaño / distancia / tiempos: constantes de abajo.
"""

import math

import pygame

from ui.tutorial import CHARACTER_IMAGE, Tutorial


FOLLOW_SIDE = 62        # distancia al costado del jugador (pixeles del mundo)
FOLLOW_UP = -14         # cuanto mas arriba que el centro del jugador
SMOOTH = 3.2            # que tan rapido lo persigue (mas alto = mas pegado)
HEIGHT_FRAC = 0.55      # alto de Cenizo respecto al alto del jugador
DEFAULT_HEIGHT = 40     # alto en el mundo si no se conoce el del jugador
TELEPORT_DIST = 700     # si queda mas lejos que esto, aparece junto al jugador

IN_TIME = 0.6           # segundos en aparecer
LINGER = 12.0           # segundos que se queda despues del tutorial
FADE_TIME = 2.5         # segundos en desvanecerse

HURT_IMAGE = "botayuda_herido.png"   # Cenizo lastimado (tools/make_cenizo_herido.py)

GLOW_COLOR = (110, 160, 255)
HURT_GLOW_COLOR = (255, 120, 90)
SPRITE_ALPHA = 235


class CenizoFollower:

    def __init__(self):

        self.pos = pygame.Vector2()
        self.alpha = 0.0
        self.visible = False

        self.hold = False          # True: no se va (tutorial / escena)
        self.linger_t = None
        self.fading = False

        self.t = 0.0
        self.facing = 1
        self.height_world = DEFAULT_HEIGHT

        self.hurt_t = 0.0
        self.kick = pygame.Vector2()

        # size_mul: escala extra (la escena del mapa 2 lo achica)
        # injured: queda lastimado (dibujo herido) hasta el proximo appear()
        self.size_mul = 1.0
        self.injured = False

        self._sources = {}
        self._cache = {}
        self._glow = {}

    # ----------------------------------------------------------- estado

    @property
    def center(self):
        """Centro de Cenizo en el mundo (a donde apunta el rayo)."""

        return pygame.Vector2(self.pos) + self.kick

    def appear(self, pos, instant=False):

        self.pos = pygame.Vector2(pos)
        self.visible = True
        self.fading = False
        self.linger_t = None
        self.kick = pygame.Vector2()

        self.size_mul = 1.0
        self.injured = False

        self.alpha = 1.0 if instant else 0.0

    def set_hold(self, flag):
        """True: se queda siguiendote. Al pasar a False empieza la cuenta
        para desvanecerse (LINGER segundos)."""

        flag = bool(flag)

        if flag == self.hold:
            return

        self.hold = flag

        if flag:
            self.fading = False
            self.linger_t = None
        elif self.visible and not self.fading:
            self.linger_t = LINGER

    def hurt(self, away_from=None):
        """Golpe del rayo: parpadea en rojo, sale empujado y se queda
        lastimado (con su dibujo herido)."""

        self.hurt_t = 1.0
        self.injured = True

        if away_from is not None:

            d = self.pos - pygame.Vector2(away_from)

            if d.length() > 0.01:
                self.kick = d.normalize() * 9.0

    # ----------------------------------------------------------- update

    def update(self, dt, player):

        if not self.visible:
            return

        self.t += dt

        h = getattr(getattr(player, "image_rect", None), "height", None)

        if h:
            self.height_world = h * HEIGHT_FRAC * self.size_mul

        if self.fading:

            self.alpha -= dt / FADE_TIME

            if self.alpha <= 0.0:
                self.alpha = 0.0
                self.visible = False
                self.fading = False

            return

        self.alpha = min(1.0, self.alpha + dt / IN_TIME)

        if not self.hold and self.linger_t is not None:

            self.linger_t -= dt

            if self.linger_t <= 0.0:
                self.fading = True

        base = pygame.Vector2(player.image_rect.center)
        target = base + (FOLLOW_SIDE, FOLLOW_UP)

        if (target - self.pos).length() > TELEPORT_DIST:
            self.pos = pygame.Vector2(target)

        k = 1.0 - math.exp(-SMOOTH * dt)

        dx = target.x - self.pos.x

        self.pos += (target - self.pos) * k

        if abs(dx) > 6.0:
            self.facing = 1 if dx > 0 else -1

        if self.hurt_t > 0.0:
            self.hurt_t = max(0.0, self.hurt_t - dt)

        self.kick *= math.exp(-4.0 * dt)

    # ------------------------------------------------------------ dibujo

    def _src(self):

        name = HURT_IMAGE if self.injured else CHARACTER_IMAGE

        img = self._sources.get(name)

        if img is None:

            img = Tutorial._load_cropped(name, None)

            # sin el dibujo herido se usa el normal
            if img is None and name != CHARACTER_IMAGE:
                img = Tutorial._load_cropped(CHARACTER_IMAGE, None)

            if img is None:
                img = Tutorial._fallback_character(300)

            self._sources[name] = img

        return img

    def _sprite(self, height, flip):

        key = (height, flip, self.injured)

        spr = self._cache.get(key)

        if spr is None:

            src = self._src()

            w = max(1, int(src.get_width() * height / src.get_height()))

            spr = pygame.transform.smoothscale(src, (w, height))

            if flip:
                spr = pygame.transform.flip(spr, True, False)

            if len(self._cache) > 12:
                self._cache.clear()

            self._cache[key] = spr

        return spr

    def _glow_surf(self, radius):

        key = (radius, self.injured)

        glow = self._glow.get(key)

        if glow is None:

            color = HURT_GLOW_COLOR if self.injured else GLOW_COLOR

            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            for i in range(radius, 0, -3):

                a = int(70 * (1.0 - i / radius) ** 1.6)

                pygame.draw.circle(glow, (*color, a), (radius, radius), i)

            if len(self._glow) > 6:
                self._glow.clear()

            self._glow[key] = glow

        return glow

    def draw(self, screen, camera):
        """Se dibuja DESPUES de la oscuridad: es un fantasma que brilla."""

        if not self.visible or self.alpha <= 0.0:
            return

        zoom = camera.zoom

        height = max(8, int(self.height_world * zoom))

        spr = self._sprite(height, self.facing < 0)

        bob = math.sin(self.t * 2.2) * 3.0

        if self.injured:
            # lastimado: flota mas bajo y tiembla
            bob = bob * 0.5 + 3.0 + math.sin(self.t * 31.0) * 0.8

        c = self.center

        sx = c.x * zoom - camera.x
        sy = (c.y + bob) * zoom - camera.y

        rect = spr.get_rect(center=(int(sx), int(sy)))

        if not rect.inflate(height, height).colliderect(screen.get_rect()):
            return

        a = self.alpha

        glow = self._glow_surf(max(8, int(height * 0.85)))
        glow.set_alpha(int(255 * a))
        screen.blit(glow, glow.get_rect(center=rect.center))

        out = spr

        if self.hurt_t > 0.0 and int(self.t * 18) % 2 == 0:

            out = spr.copy()
            out.fill((190, 0, 0, 0), special_flags=pygame.BLEND_RGB_ADD)

        out.set_alpha(int(SPRITE_ALPHA * a))
        screen.blit(out, rect)