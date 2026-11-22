"""Cinematica del rescate (mapa 2): cuando se va el monstruo aparece una horda
de Aurantulas que se va acercando al jugador (world/spider.py, start_horde).
Cenizo se asusta, llega el Farolero desde el cuarto de la derecha, se frena en
el punto verde y suelta una onda de luz que ilumina todo el cuarto y espanta a
todas las Aurantulas. Despues hay paz.

Textos, nombre, tiempos y coordenadas: world/map2_intro.py (secciones LA HORDA
y EL RESCATE). Imagen opcional del tipo: assets/maps/combate/salvador.png (si
no existe se usa un dibujo provisorio).

  1. wait    la horda viene saliendo de la oscuridad y acercandose
  2. cenizo  Cenizo habla (panel): "este es nuestro fin"
  3. gap     una pausa corta, las Aurantulas siguen avanzando
  4. walk    el Farolero entra caminando desde el cuarto de la derecha
  5. hold    se queda quieto en el punto verde cargando luz (suspenso)
  6. burst   la onda de luz explota: se ilumina todo el cuarto, flash y
             temblor, y las Aurantulas salen corriendo y se desvanecen
  7. talk2   habla (panel): paz. Le saca el veneno al jugador
  8. leave   la luz se apaga de a poco y el tipo se desvanece

Lo que hay que enganchar en states/new_game.py (ya esta hecho):
  - update(dt) y tick(dt) cada cuadro, after_dialog(closed) al cerrar un dialogo
  - camera_focus() para la camara
  - light_sources(zoom) y lit_rects() para la luz
  - draw(screen, camera) para dibujar al tipo
"""

import math

import pygame

from core.audio_manager import audio
from ui.boss_dialog import BossDialog, COMBAT_DIR
from ui.map2_scene import CenizoHurtDialog, CENIZO_HURT_DIALOG_HEIGHT
from ui.tutorial import DEFAULT_THEME
from world import map2_intro as cfg


RESCUER_THEME = dict(
    DEFAULT_THEME,
    name=getattr(cfg, "RESCUER_NAME", "El Farolero"),
    text=(255, 248, 224),
    shadow=(40, 28, 6),
    hint=(240, 214, 140),
    name_bg=(150, 112, 30),
    name_edge=(255, 222, 120),
    name_text=(255, 252, 232),
    dot_on=(255, 226, 130),
    dot_on_edge=(110, 78, 10),
    dot_done=(200, 164, 80),
    dot_next=(120, 100, 60),
    arrow=(255, 226, 130),
    spark=(255, 244, 190),
    glow=(255, 214, 110),
    frame_border=(255, 222, 120),
    frame_fill=(52, 38, 12),
    frame_fill_alpha=238,
)

PORTRAIT = "salvador.png"

# el cuarto que se ilumina (el contorno AZUL del dibujo)
ROOM = pygame.Rect(*cfg.RESCUE_ROOM)

STEP_RADIUS = 24        # la luz crece de a saltos (evita miles de imagenes en cache)
STEP_STRENGTH = 0.05


# ------------------------------------------------------------- imagenes

def draw_rescuer(height):
    """Dibujo provisorio: encapuchado con un farol encendido."""

    h = max(40, int(height))
    w = int(h * 0.62)

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    cx = w // 2

    robe = (226, 212, 168)
    shade = (158, 138, 84)
    dark = (44, 34, 20)
    trim = (255, 238, 170)

    # capa
    body = [
        (cx - w * 0.15, h * 0.30), (cx + w * 0.15, h * 0.30),
        (cx + w * 0.40, h * 0.98), (cx - w * 0.40, h * 0.98),
    ]

    pygame.draw.polygon(surf, robe, body)

    pygame.draw.polygon(surf, shade, [
        (cx + w * 0.02, h * 0.30), (cx + w * 0.15, h * 0.30),
        (cx + w * 0.40, h * 0.98), (cx + w * 0.10, h * 0.98),
    ])

    # ribete de abajo
    pygame.draw.line(
        surf, trim, (cx - w * 0.40, h * 0.965), (cx + w * 0.40, h * 0.965),
        max(2, h // 70)
    )

    # capucha y cara en sombra
    head = (cx, int(h * 0.22))
    r = int(w * 0.20)

    pygame.draw.circle(surf, robe, head, r)
    pygame.draw.circle(surf, shade, (head[0] + r // 3, head[1] + r // 4), r // 2)
    pygame.draw.ellipse(
        surf, dark,
        pygame.Rect(0, 0, int(r * 1.2), int(r * 1.3)).move(
            head[0] - int(r * 0.6), head[1] - int(r * 0.55)
        )
    )

    for dx in (-0.2, 0.2):

        pygame.draw.circle(
            surf, (255, 244, 190),
            (head[0] + int(r * dx), head[1] - int(r * 0.05)), max(2, r // 7)
        )

    # brazo estirado con el farol
    hand = (int(cx + w * 0.38), int(h * 0.56))

    pygame.draw.line(
        surf, shade, (cx + w * 0.10, h * 0.36), hand, max(4, h // 26)
    )

    # farol: caja, luz y gancho
    lw = max(8, int(w * 0.17))
    lh = max(10, int(h * 0.11))

    lamp = pygame.Rect(0, 0, lw, lh)
    lamp.midtop = (hand[0], hand[1] + 2)

    pygame.draw.line(
        surf, dark, (hand[0], hand[1] - 2), (hand[0], lamp.top), 2
    )
    pygame.draw.rect(surf, (255, 226, 120), lamp, border_radius=3)
    pygame.draw.rect(surf, dark, lamp, 2, border_radius=3)

    return surf


_glow_cache = {}


def _glow(radius, color=(255, 214, 120)):
    """Circulo de luz suave (se suma sobre la escena)."""

    radius = max(4, int(radius))

    key = (radius, color)

    img = _glow_cache.get(key)

    if img is None:

        if len(_glow_cache) > 60:
            _glow_cache.clear()

        img = pygame.Surface((radius * 2, radius * 2))

        for j in range(radius, 0, -3):

            k = (1.0 - j / radius) ** 1.8

            pygame.draw.circle(
                img,
                (int(color[0] * k), int(color[1] * k), int(color[2] * k)),
                (radius, radius), j,
            )

        _glow_cache[key] = img

    return img


# ------------------------------------------------------------- dialogo

class RescuerDialog(BossDialog):
    """El tipo hablando por el panel."""

    THEME = RESCUER_THEME

    PORTRAITS = (PORTRAIT,)

    CHAR_FRACTION = 0.58
    FRAME_WIDTH = 450

    TYPE_SPEED = 38.0
    PAUSE_END = 0.40
    PAUSE_COMMA = 0.16
    PAUSE_DOTS = 0.30

    def _source_character(self):

        if (COMBAT_DIR / PORTRAIT).exists():
            return super()._source_character()

        return draw_rescuer(420)


# ------------------------------------------------------------- la escena

class Map2Rescue:

    def __init__(self, game):

        self.game = game

        self.stage = "idle"
        self.done = False

        self.t = 0.0
        self.pos = pygame.Vector2(cfg.RESCUER_ENTRY)

        self.walked = 0.0            # cuanto camino desde que entro (px del mundo)
        self.fade = 0.0              # 0 invisible -> 1 se ve entero
        self.aura = 0.0              # radio (mundo) de la luz que sale de el
        self.room = 0.0              # 0-1: cuanta luz hay en el cuarto
        self.wave = 0.0              # 0-1: avance de la onda de luz (anillo)

        self._current = None
        self._old_smooth = None
        self._sprites = {}

    # ---- datos

    def _size(self):
        return (self.game.width, self.game.height)

    @property
    def active(self):
        return self.stage not in ("idle", "end")

    # ---- camara

    def camera_focus(self):
        """Mientras llega, carga y suelta la luz, la camara se desplaza hacia
        el (a medias entre el jugador y el Farolero)."""

        if self.stage not in ("walk", "hold", "talk1", "burst", "talk2"):
            return None

        p = pygame.Vector2(self.game.player.image_rect.center)

        f = p.lerp(self.pos, 0.55)

        return (f.x, f.y, 1.0, 0.5)

    def tick(self, dt):
        """Mueve la camara de a poco mientras el dialogo esta abierto."""

        if self.stage not in ("talk1", "talk2"):
            return

        g = self.game

        g.camera.update(g.player, dt=dt, focus=self.camera_focus())

    # ---- secuencia

    def start(self):
        """La horda ya esta saliendo: se espera un poco y habla Cenizo."""

        self.stage = "wait"
        self.t = 0.0

    def _open(self, pages, stage, dialog=None, **kw):

        self.stage = stage

        cls = dialog or RescuerDialog

        self._current = cls(self._size(), pages=pages, **kw)

        self.game.tutorial = self._current

    def _cenizo(self):
        """Cenizo ve la horda y se asusta."""

        self._open(
            cfg.CENIZO_FIN, "cenizo", dialog=CenizoHurtDialog,
            char_height=CENIZO_HURT_DIALOG_HEIGHT,
        )

    def _begin_walk(self):
        """El Farolero viene caminando desde el cuarto de la derecha."""

        g = self.game

        self._old_smooth = g.camera.smoothing
        g.camera.smoothing = cfg.CAMERA_SMOOTH

        self.pos = pygame.Vector2(cfg.RESCUER_ENTRY)
        self.walked = 0.0
        self.fade = 0.0

        self.stage = "walk"
        self.t = 0.0

        audio.play("light_on")

    def after_dialog(self, closed):
        """new_game la llama cuando se cierra cualquier dialogo."""

        if closed is not self._current:
            return

        self._current = None

        if self.stage == "cenizo":

            self.stage = "gap"
            self.t = 0.0

        elif self.stage == "talk1":
            self._burst()

        elif self.stage == "talk2":
            self._leave()

    def _before_burst(self):
        """Ya esta en el punto verde y las Aurantulas casi atacan."""

        if cfg.RESCUER_1:

            # (opcional) dice algo antes de tirar la luz
            self._open(cfg.RESCUER_1, "talk1")

            return

        self._burst()

    def _burst(self):
        """Onda de luz: se ilumina el cuarto y las Aurantulas huyen."""

        g = self.game

        self.stage = "burst"
        self.t = 0.0
        self.wave = 0.0

        fx = getattr(g, "fx", None)

        if fx is not None:

            try:
                fx.flash(0.9, (255, 238, 180), 0.9)
                fx.shake(7.0, 1.2)
            except Exception as error:
                print(f"[rescate] efecto: {error}")

        audio.play("flashbang")
        audio.play("light_on")

        g.spiders.scare_all(g, self.pos)

    def _leave(self):

        g = self.game

        self.stage = "leave"
        self.t = 0.0

        old = self._old_smooth

        if old is not None:
            g.camera.smoothing = old

        if getattr(cfg, "RESCUE_CURE_POISON", False):

            cure = getattr(g, "cure_poison", None)

            if cure is not None:
                cure()

        audio.play("heal")

    def update(self, dt):
        """Lo llama new_game en cada cuadro (el juego corriendo)."""

        g = self.game

        if self.stage == "wait":

            self.t += dt

            # Cenizo habla cuando ya se ven varias (no antes)
            if (
                self.t >= cfg.HORDE_CENIZO_DELAY
                and g.spiders.horde_spawned() >= 3
            ) or self.t >= cfg.HORDE_CENIZO_DELAY + 6.0:
                self._cenizo()

        elif self.stage == "gap":

            self.t += dt

            if self.t >= cfg.RESCUE_GAP:
                self._begin_walk()

        elif self.stage == "walk":

            self.t += dt

            target = pygame.Vector2(cfg.RESCUER_STOP)

            to = target - self.pos

            step = cfg.RESCUER_WALK_SPEED * dt

            if to.length() <= step:

                self.pos = target

                self.stage = "hold"
                self.t = 0.0

            else:

                self.pos += to.normalize() * step
                self.walked += step

            # sale de la oscuridad de a poco y trae su luz
            self.fade = min(1.0, self.walked / 120.0)
            self.aura = 110.0 * self.fade

        elif self.stage == "hold":

            self.t += dt

            # carga luz alrededor de el (el circulo amarillo del dibujo)
            k = min(1.0, self.t / cfg.RESCUE_HOLD_MIN)

            self.fade = 1.0
            self.aura = 110.0 + (cfg.RESCUE_CHARGE_RADIUS * 1.6 - 110.0) * k

            near = g.spiders.horde_nearest(g)

            if self.t >= cfg.RESCUE_HOLD_MIN and (
                (near is not None and near <= cfg.RESCUE_TRIGGER_DIST)
                or self.t >= cfg.RESCUE_HOLD_MAX
            ):
                self._before_burst()

        elif self.stage == "burst":

            self.t += dt

            k = min(1.0, self.t / cfg.RESCUE_BURST_TIME)
            e = 1.0 - (1.0 - k) ** 3

            start = cfg.RESCUE_CHARGE_RADIUS * 1.6

            self.wave = e
            self.aura = start + (cfg.RESCUE_AURA_RADIUS - start) * e
            self.room = min(1.0, e * 1.15)

            if self.t >= cfg.RESCUE_BURST_TIME:
                self._open(cfg.RESCUER_2, "talk2")

        elif self.stage == "leave":

            self.t += dt

            k = min(1.0, self.t / cfg.RESCUE_LEAVE_TIME)

            self.fade = 1.0 - k
            self.aura = cfg.RESCUE_AURA_RADIUS * (1.0 - k)
            self.room = 1.0 - k

            if k >= 1.0:

                self.stage = "end"
                self.done = True

                self.game.spiders.peace = True

    # ---- luz (new_game la suma a la oscuridad)

    def light_sources(self, zoom):
        """[(x, y, radio_en_pantalla)] para world/lighting.py."""

        if not self.active or self.aura < 8:
            return []

        radius = int(round(self.aura / STEP_RADIUS)) * STEP_RADIUS

        if radius < STEP_RADIUS:
            return []

        return [(self.pos.x, self.pos.y, int(radius * zoom))]

    def lit_rects(self):
        """[(rect_mundo, fuerza, borde)]: el cuarto entero iluminado."""

        if not self.active or self.room < 0.03:
            return []

        strength = round(self.room / STEP_STRENGTH) * STEP_STRENGTH

        if strength <= 0:
            return []

        return [(ROOM, min(1.0, strength), 60)]

    # ---- dibujo

    def _sprite(self, side_h):

        img = self._sprites.get(side_h)

        if img is None:

            path = COMBAT_DIR / PORTRAIT

            src = None

            try:
                src = pygame.image.load(str(path)).convert_alpha()
            except (pygame.error, FileNotFoundError, OSError):
                pass

            if src is None:
                src = draw_rescuer(256)
            else:

                area = src.get_bounding_rect()

                if area.width > 0 and area.height > 0:
                    src = src.subsurface(area).copy()

            w = max(2, int(src.get_width() * side_h / src.get_height()))

            img = pygame.transform.smoothscale(src, (w, side_h))

            if len(self._sprites) > 12:
                self._sprites.clear()

            self._sprites[side_h] = img

        return img

    def _draw_wave(self, screen, camera, sx, sy):
        """El anillo de la onda de luz que sale de el (se suma a la escena)."""

        if self.stage != "burst" or not (0.0 < self.wave < 1.0):
            return

        zoom = camera.zoom

        radius = int(cfg.RESCUE_AURA_RADIUS * 1.1 * self.wave * zoom)

        if radius < 6:
            return

        width = max(3, int(radius * 0.10))

        k = (1.0 - self.wave) ** 1.2

        col = (int(255 * k), int(236 * k), int(170 * k))

        # solo la parte del anillo que cae en pantalla
        view = screen.get_rect()
        box = pygame.Rect(0, 0, radius * 2 + 4, radius * 2 + 4)
        box.center = (sx, sy)
        box = box.clip(view)

        if box.width < 2 or box.height < 2:
            return

        ring = pygame.Surface(box.size)

        pygame.draw.circle(
            ring, col, (sx - box.x, sy - box.y), radius, width
        )

        screen.blit(ring, box.topleft, special_flags=pygame.BLEND_RGB_ADD)

    def draw(self, screen, camera):
        """El tipo (y su resplandor) en el mundo."""

        if not self.active or self.fade <= 0.01:
            return

        g = self.game

        zoom = camera.zoom

        base_h = getattr(getattr(g.player, "image_rect", None), "height", 40)

        side_h = int(base_h * cfg.RESCUE_HEIGHT * zoom / 4) * 4

        side_h = max(16, side_h)

        img = self._sprite(side_h)

        t = pygame.time.get_ticks() / 1000.0

        bob = math.sin(t * 2.2) * 2.5 * zoom

        # caminando: sube y baja con cada paso
        if self.stage == "walk":

            phase = (self.t / max(0.05, cfg.RESCUER_WALK_STEP)) * math.pi

            bob = -abs(math.sin(phase)) * cfg.RESCUER_WALK_HOP * img.get_height()

        sx = int(self.pos.x * zoom - camera.x)
        sy = int(self.pos.y * zoom - camera.y + bob)

        # resplandor detras (luz sumada)
        gr = int(img.get_height() * (0.95 + 0.08 * math.sin(t * 5.0)))

        if self.stage == "hold":
            gr = int(gr * (1.0 + 0.5 * min(1.0, self.t / cfg.RESCUE_HOLD_MIN)))

        halo = _glow(gr // STEP_RADIUS * STEP_RADIUS or STEP_RADIUS)

        k = self.fade * 0.85

        if k < 0.999:

            halo = halo.copy()
            halo.fill(
                (int(255 * k), int(255 * k), int(255 * k)),
                special_flags=pygame.BLEND_RGB_MULT
            )

        screen.blit(
            halo,
            halo.get_rect(center=(sx, sy - img.get_height() // 2)),
            special_flags=pygame.BLEND_RGB_ADD,
        )

        # sombra en el piso
        shadow = pygame.Surface(
            (max(4, int(img.get_width() * 0.9)), max(2, int(img.get_width() * 0.28))),
            pygame.SRCALPHA,
        )

        pygame.draw.ellipse(
            shadow, (0, 0, 0, int(90 * self.fade)), shadow.get_rect()
        )

        screen.blit(shadow, shadow.get_rect(center=(sx, sy)))

        body = img

        if self.fade < 0.999:

            body = img.copy()
            body.set_alpha(int(255 * self.fade))

        screen.blit(body, body.get_rect(midbottom=(sx, sy)))

        self._draw_wave(screen, camera, sx, sy - img.get_height() // 2)