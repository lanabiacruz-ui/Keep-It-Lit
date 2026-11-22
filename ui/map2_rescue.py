"""Cinematica del rescate (mapa 2): cuando vienen muchas Aurantulas aparece
un tipo, llena de luz toda la sala y las espanta a todas. Despues hay paz.

Textos, nombre y tiempos: world/map2_intro.py (seccion EL RESCATE).
Imagen opcional del tipo: assets/maps/combate/salvador.png (si no existe se
usa un dibujo provisorio).

  1. arrive   aparece una lucecita flotando y el tipo se hace visible; las
              Aurantulas se quedan quietas, asustadas
  2. talk1    habla (panel)
  3. burst    la luz explota: se ilumina toda la sala, flash y temblor, y las
              Aurantulas salen corriendo y se desvanecen
  4. talk2    habla (panel): paz. Le saca el veneno al jugador
  5. leave    la luz se apaga de a poco y el tipo se desvanece

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
from ui.tutorial import DEFAULT_THEME
from world import map2_intro as cfg
from world import spider as spider_mod


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

# la sala que se ilumina (la sala grande de las Aurantulas)
ROOM = spider_mod.AURA_ROOM

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
        self.pos = pygame.Vector2()

        self.fade = 0.0              # 0 invisible -> 1 se ve entero
        self.aura = 0.0              # radio (mundo) de la luz que sale de el
        self.room = 0.0              # 0-1: cuanta luz hay en la sala

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
        """Mientras aparece y habla, la camara se desplaza hacia el."""

        if self.stage not in ("arrive", "talk1", "burst", "talk2"):
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

    def _find_spot(self):
        """Donde aparece: cerca del jugador, en el piso y con camino libre."""

        g = self.game

        cmap = g.collision_map

        px, py = g.player.rect.center

        me = pygame.Vector2(px, py)

        best = None

        for dist in (150, 120, 190, 90):

            for ang in (-90, -45, -135, 0, 180, 45, 135, 90):

                p = me + pygame.Vector2(dist, 0).rotate(ang)

                if not cmap.point_is_walkable(p.x, p.y):
                    continue

                if not g.spiders._clear_line(cmap, (px, py), (p.x, p.y)):
                    continue

                best = p

                break

            if best is not None:
                break

        return best if best is not None else me + (0, -110)

    def start(self):

        g = self.game

        self._old_smooth = g.camera.smoothing
        g.camera.smoothing = cfg.CAMERA_SMOOTH

        self.pos = self._find_spot()

        self.stage = "arrive"
        self.t = 0.0

        # las Aurantulas se quedan quietas, como si sintieran algo
        g.spiders.pause()

        audio.play("light_on")

    def _open(self, pages, stage):

        self.stage = stage

        self._current = RescuerDialog(self._size(), pages=pages)

        self.game.tutorial = self._current

    def after_dialog(self, closed):
        """new_game la llama cuando se cierra cualquier dialogo."""

        if closed is not self._current:
            return

        self._current = None

        if self.stage == "talk1":
            self._burst()

        elif self.stage == "talk2":
            self._leave()

    def _burst(self):
        """La luz explota: se ilumina la sala y las Aurantulas huyen."""

        g = self.game

        self.stage = "burst"
        self.t = 0.0

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

        if cfg.RESCUE_CURE_POISON:

            cure = getattr(g, "cure_poison", None)

            if cure is not None:
                cure()

        audio.play("heal")

    def update(self, dt):
        """Lo llama new_game en cada cuadro (el juego corriendo)."""

        if self.stage == "arrive":

            self.t += dt

            k = min(1.0, self.t / cfg.RESCUE_ARRIVE_TIME)

            self.fade = min(1.0, k * 1.6)
            self.aura = 150.0 * k

            if self.t >= cfg.RESCUE_ARRIVE_TIME:
                self._open(cfg.RESCUER_1, "talk1")

        elif self.stage == "burst":

            self.t += dt

            k = min(1.0, self.t / cfg.RESCUE_BURST_TIME)
            e = 1.0 - (1.0 - k) ** 3

            self.aura = 150.0 + (cfg.RESCUE_AURA_RADIUS - 150.0) * e
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
        """[(rect_mundo, fuerza, borde)]: la sala entera iluminada."""

        if not self.active or self.room < 0.03:
            return []

        strength = round(self.room / STEP_STRENGTH) * STEP_STRENGTH

        if strength <= 0:
            return []

        return [(
            ROOM.inflate(cfg.RESCUE_ROOM_PAD, cfg.RESCUE_ROOM_PAD),
            min(1.0, strength), 90,
        )]

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

        sx = int(self.pos.x * zoom - camera.x)
        sy = int(self.pos.y * zoom - camera.y + bob)

        # resplandor detras (luz sumada)
        gr = int(img.get_height() * (0.95 + 0.08 * math.sin(t * 5.0)))

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