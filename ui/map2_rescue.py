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
  7. talk2   habla (panel): paz. Le saca el veneno al jugador. Cuenta que se
             queda y que le ayudo a Escupin a vender sus cosas
  8. settle  camina hasta el lugar donde se va a quedar (FAROLERO_SPOT)
  9. leave   la onda se calma y queda un resplandor fijo. El cuarto queda
             ILUMINADO PARA SIEMPRE y el tipo NO se desvanece: pasa a ser
             FaroleroNPC (mas abajo), un vendedor fijo que ademas cura

Animaciones del Farolero (FaroleroAnim, abajo): camina con los cuadros de
assets/maps/combate/farolero_caminar.png y en el punto verde hace el ritual de
farolero_ritual.png (se sienta, prende la llama y la suelta en la onda). El
cuarto toma un tono de fuego naranja (_draw_room_fire, config ROOM_FIRE_*).
Las imagenes se generan con tools/make_farolero_assets.py.

Lo que hay que enganchar en states/new_game.py (ya esta hecho):
  - update(dt) y tick(dt) cada cuadro, after_dialog(closed) al cerrar un dialogo
  - camera_focus() para la camara
  - light_sources(zoom) y lit_rects() para la luz
  - draw(screen, camera) para dibujar al tipo
  - draw_room_tint(screen, camera) despues de la oscuridad (tono naranja)
"""

import json
import math
import random

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

# el cuarto que se ilumina: BANDAS que siguen el interior de la sala (asi la
# luz no se escapa afuera de las paredes)
ROOM_BANDS = [pygame.Rect(*b) for b in cfg.RESCUE_ROOM_BANDS]
ROOM_FEATHER = int(getattr(cfg, "RESCUE_ROOM_FEATHER", 3))

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


# ------------------------------------------------------------- animaciones

# cuanta luz tiene la llama en cada cuadro de la hoja del ritual (0 a 15):
# parado, se sienta (0-4), prende (5-7), pico del estallido (8), se apaga (9-12)
# y vuelve a pararse (13-15)
RITUAL_GLOW = [
    0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.5, 0.75,
    1.0, 0.8, 0.5, 0.3, 0.15, 0.0, 0.0, 0.0,
]


def _ritual_glow(frame):

    frame = max(0.0, min(len(RITUAL_GLOW) - 1.0, float(frame)))

    a = int(frame)
    b = min(len(RITUAL_GLOW) - 1, a + 1)

    return RITUAL_GLOW[a] + (RITUAL_GLOW[b] - RITUAL_GLOW[a]) * (frame - a)


DEFAULT_ANIM_META = {
    "stand": {"file": "salvador.png", "size": [130, 234]},
    "walk": {
        "file": "farolero_caminar.png", "frames": 4, "cell": [160, 245],
        "stand_h": 237, "dirs": {"down": 0, "left": 1, "up": 2},
        "faces": "left",
    },
    "ritual": {
        "file": "farolero_ritual.png", "cols": 4, "rows": 4,
        "cell": [384, 256], "stand_h": 234, "foot": [202, 241],
    },
    "sit": {
        "file": "farolero_sentarse.png", "cols": 4, "rows": 4,
        "cell": [384, 256], "stand_h": 249, "foot": [192, 253],
        "down": [0, 15], "idle": [12, 15],
    },
}


class FaroleroAnim:
    """Cuadros animados del Farolero (los genera tools/make_farolero_assets.py).

    Si faltan los archivos todo sigue andando con el dibujo quieto."""

    def __init__(self):

        self.meta = None
        self._sheets = {}
        self._cache = {}

        try:

            with open(
                COMBAT_DIR / getattr(cfg, "FAROLERO_ANIM_JSON", "farolero_anim.json"),
                encoding="utf-8",
            ) as f:
                self.meta = json.load(f)

        except (OSError, ValueError):
            self.meta = None

        if self.meta is None:
            # sin json: medidas de las hojas que vienen en assets/maps/combate
            self.meta = json.loads(json.dumps(DEFAULT_ANIM_META))

    def _sheet(self, key, alpha):

        if key not in self._sheets:

            img = None
            info = (self.meta or {}).get(key)

            if info:

                try:

                    img = pygame.image.load(str(COMBAT_DIR / info["file"]))
                    img = img.convert_alpha() if alpha else img.convert()

                except (pygame.error, FileNotFoundError, OSError, KeyError):
                    img = None

            self._sheets[key] = img

        return self._sheets[key]

    @property
    def has_walk(self):
        return self._sheet("walk", True) is not None

    @property
    def has_ritual(self):
        return self._sheet("ritual", True) is not None

    @property
    def has_sit(self):
        return self._sheet("sit", True) is not None

    def _remember(self, key, img):

        if len(self._cache) > 120:
            self._cache.clear()

        self._cache[key] = img

    def walk(self, n, side_h, direction="left"):
        """Cuadro `n` de la caminata, con el alto del dibujo = side_h.

        `direction`: "down" (de frente), "up" (de espaldas), "left" o "right".
        La hoja tiene una fila por direccion (json "dirs"); "right" es "left"
        espejado. Con un json viejo (una sola tira) se usa esa tira."""

        sheet = self._sheet("walk", True)

        if sheet is None:
            return None

        info = self.meta["walk"]
        cw, ch = info["cell"]

        n %= max(1, int(info["frames"]))

        dirs = info.get("dirs")

        flip = False
        row = 0

        if dirs:

            if direction == "right" and "right" not in dirs:
                direction, flip = "left", True

            row = int(dirs.get(direction, dirs.get("down", 0)))

        else:

            faces_right = info.get("faces", "right") == "right"
            flip = (direction == "right") != faces_right

        key = ("walk", n, side_h, row, flip)

        img = self._cache.get(key)

        if img is None:

            scale = side_h / float(info["stand_h"])

            cell = sheet.subsurface(pygame.Rect(n * cw, row * ch, cw, ch))

            img = pygame.transform.smoothscale(
                cell, (max(2, int(cw * scale)), max(2, int(ch * scale)))
            )

            if flip:
                img = pygame.transform.flip(img, True, False)

            self._remember(key, img)

        return img

    def _grid(self, key, n, side_h):
        """(imagen, (ancla_x, ancla_y)) del cuadro `n` de una hoja en grilla
        (ritual o sentarse). Tiene transparencia; el ancla son los pies."""

        sheet = self._sheet(key, True)

        if sheet is None:
            return None

        info = self.meta[key]
        cw, ch = info["cell"]
        cols = int(info["cols"])

        n = max(0, min(cols * int(info["rows"]) - 1, int(n)))

        ck = (key, n, side_h)

        got = self._cache.get(ck)

        if got is None:

            scale = side_h / float(info["stand_h"])

            r, c = divmod(n, cols)

            cell = sheet.subsurface(pygame.Rect(c * cw, r * ch, cw, ch))

            img = pygame.transform.smoothscale(
                cell, (max(2, int(cw * scale)), max(2, int(ch * scale)))
            )

            anchor = (
                int(info["foot"][0] * scale), int(info["foot"][1] * scale)
            )

            got = (img, anchor)

            self._remember(ck, got)

        return got

    def ritual(self, n, side_h):
        """Cuadro `n` del ritual (parado -> sentado -> llama -> parado)."""

        return self._grid("ritual", n, side_h)

    def sit(self, n, side_h):
        """Cuadro `n` (0 a 15) de sentarse detras de la mesita. Los ultimos
        quedan sentado y se repiten (ver sit_idle_frame)."""

        return self._grid("sit", n, side_h)


def _dir_name(vec, last="down"):
    """Direccion de la caminata segun el vector de movimiento (ejes de pantalla:
    y positivo = hacia abajo). Si casi no se mueve se queda con la anterior."""

    if abs(vec.x) < 0.5 and abs(vec.y) < 0.5:
        return last

    if abs(vec.x) >= abs(vec.y):
        return "right" if vec.x > 0 else "left"

    return "down" if vec.y > 0 else "up"


_anim_cache = []


def anim():
    """El FaroleroAnim compartido (se carga una sola vez)."""

    if not _anim_cache:
        _anim_cache.append(FaroleroAnim())

    return _anim_cache[0]


def sit_idle_frame(t):
    """Cuadro de la animacion de quedarse sentado (va y vuelve, para siempre)."""

    info = (anim().meta or {}).get("sit") or {}

    first, last = info.get("idle", [12, 15])

    seq = list(range(first, last + 1)) + list(range(last - 1, first, -1))

    return seq[int(t * getattr(cfg, "FAROLERO_SIT_IDLE_FPS", 2.5)) % len(seq)]


def _draw_room_fire(screen, camera, strength, center, boost=1.0):
    """Tono de fuego del cuarto: tiñe de naranja lo que esta iluminado (se
    multiplica), suma un brillo naranja que titila y un resplandor fuerte
    alrededor del Farolero. Se dibuja despues de la oscuridad."""

    if not getattr(cfg, "FAROLERO_WARM_TINT", False):
        return

    s = max(0.0, min(1.0, strength))

    if s <= 0.02:
        return

    zoom = camera.zoom
    view = screen.get_rect()

    boxes = []

    for band in ROOM_BANDS:

        dest = camera.apply(band).clip(view)

        if dest.width > 0 and dest.height > 0:
            boxes.append(dest)

    if not boxes:
        return

    t = pygame.time.get_ticks() / 1000.0

    flick = (
        1.0 + 0.10 * math.sin(t * 7.3) + 0.06 * math.sin(t * 12.9 + 1.7)
        + 0.04 * math.sin(t * 3.1)
    )

    mult = tuple(
        int(255 - (255 - c) * s) for c in getattr(cfg, "ROOM_FIRE_MULT", (255, 176, 112))
    )

    add = tuple(
        max(0, min(255, int(c * s * flick * boost)))
        for c in getattr(cfg, "ROOM_FIRE_ADD", (34, 12, 0))
    )

    # resplandor alrededor del fuego (a la altura del pecho)
    radius = float(getattr(cfg, "ROOM_FIRE_RADIUS", 150)) * zoom * (0.5 + 0.5 * min(1.0, s))
    radius = int(round(radius * flick / 32.0)) * 32

    glow = None

    if radius >= 32:

        gc = getattr(cfg, "ROOM_FIRE_GLOW", (150, 62, 12))

        # la intensidad va de a saltos (cada variante se guarda en cache)
        level = max(1, int(round(min(1.0, s * boost) * 4)))

        glow = _glow(radius, tuple(int(c * level / 4.0) for c in gc))

    cx = int(center[0] * zoom - camera.x)
    cy = int((center[1] - 18) * zoom - camera.y)

    old_clip = screen.get_clip()

    for dest in boxes:

        screen.fill(mult, dest, special_flags=pygame.BLEND_RGB_MULT)
        screen.fill(add, dest, special_flags=pygame.BLEND_RGB_ADD)

        if glow is not None:

            screen.set_clip(dest)

            screen.blit(
                glow, glow.get_rect(center=(cx, cy)),
                special_flags=pygame.BLEND_RGB_ADD,
            )

    screen.set_clip(old_clip)


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
        self.ritual = None           # cuadro (0-15) de la hoja del ritual; None = no se ve
        self.seat = None             # cuadro (0-15) de la hoja de sentarse; None = no se ve
        self.walk_dir = "left"       # hacia donde camina: down / up / left / right

        self._current = None
        self._old_smooth = None
        self._sprites = {}
        self._path = []

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

        if self.stage not in ("walk", "hold", "talk1", "burst", "talk2", "settle"):
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

        # primero camina hasta el lugar donde se va a quedar (detras de la
        # mesita), por los puntos de FAROLERO_PATH
        self.stage = "settle"
        self.t = 0.0

        self._path = [pygame.Vector2(p) for p in cfg.FAROLERO_PATH]
        self._path.append(pygame.Vector2(cfg.FAROLERO_SPOT))

        # la tiendita (mesita, alfombra, estante...) aparece
        decor = getattr(g, "shop_decor", None)

        if decor is not None:
            decor.reveal()

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

            self.walk_dir = _dir_name(to, self.walk_dir)

            if to.length() <= step:

                self.pos = target

                self.stage = "hold"
                self.t = 0.0

            else:

                self.pos += to.normalize() * step
                self.walked += step

            # se lo ve tal cual desde que sale (no es una luz) y NO ilumina:
            # la luz aparece recien cuando abre la cabeza (el ritual)
            self.fade = 1.0
            self.aura = 0.0

            door = getattr(g, "map2_door", None)

            if (
                door is not None and not door.broken
                and self.pos.x <= door.rect.right + cfg.DOOR_BREAK_DIST
            ):
                door.smash(g)

        elif self.stage == "hold":

            self.t += dt

            # carga luz alrededor de el (el circulo amarillo del dibujo)
            k = min(1.0, self.t / cfg.RESCUE_HOLD_MIN)

            self.fade = 1.0

            if anim().has_ritual:

                # ritual: se sienta (cuadros 0-4) y prende la llama (5-7);
                # despues titila hasta que explota
                f = min(7.0, self.t * cfg.RITUAL_BUILD_FPS)

                if f >= 7.0:
                    f = 7.0 if math.sin(self.t * 9.0) > 0 else 6.0

                self.ritual = f

                # sentado no ilumina; la luz crece con la llama de la cabeza
                self.aura = cfg.RESCUE_CHARGE_RADIUS * 1.6 * _ritual_glow(f)

            else:
                self.aura = cfg.RESCUE_CHARGE_RADIUS * 1.6 * k

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

            # su luz propia se apaga con la llama; el cuarto queda iluminado
            if k > 0.7:
                self.aura *= max(0.0, 1.0 - (k - 0.7) / 0.3)
            self.room = min(1.0, e * 1.15)

            if anim().has_ritual:

                # pico de la llama (cuadro 8) y se apaga hasta pararse (15)
                self.ritual = 8.0 + 7.0 * k

            if self.t >= cfg.RESCUE_BURST_TIME:

                self.ritual = None

                self._open(cfg.RESCUER_2, "talk2")

        elif self.stage == "settle":

            self.t += dt

            target = self._path[0]

            to = target - self.pos

            step = cfg.RESCUER_WALK_SPEED * dt

            self.walk_dir = _dir_name(to, self.walk_dir)

            if to.length() <= step:

                self.pos = pygame.Vector2(target)

                self._path.pop(0)

                if not self._path:

                    # llega a la mesita: se sienta (y queda sentado para siempre)
                    self.stage = "sit" if anim().has_sit else "leave"
                    self.t = 0.0
                    self.seat = 0.0 if anim().has_sit else None
                    self.aura = 0.0

            else:

                self.pos += to.normalize() * step

        elif self.stage == "sit":

            self.t += dt

            last = float((anim().meta["sit"].get("down") or [0, 15])[1])

            self.fade = 1.0
            self.room = 1.0
            self.aura = 0.0
            self.seat = min(last, self.t * cfg.FAROLERO_SIT_FPS)

            if self.seat >= last:

                self.stage = "leave"
                self.t = 0.0

        elif self.stage == "leave":

            self.t += dt

            k = min(1.0, self.t / cfg.RESCUE_LEAVE_TIME)

            # la onda se calma hasta un resplandor fijo; el cuarto sigue
            # iluminado y el tipo se queda
            glow = cfg.FAROLERO_GLOW_RADIUS

            self.fade = 1.0
            self.aura = float(glow) * k
            self.room = 1.0

            if self.seat is not None:
                self.seat = sit_idle_frame(self.t)

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

        return [(b, min(1.0, strength), ROOM_FEATHER) for b in ROOM_BANDS]

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

        bob = 0.0     # sin flotar

        # ritual de luz: cuadro de la hoja (con transparencia)
        ritual = None
        glow_k = 0.0

        if self.ritual is not None and self.stage in ("hold", "talk1", "burst"):

            ritual = anim().ritual(int(self.ritual), side_h)

            if ritual is not None:

                glow_k = _ritual_glow(self.ritual)
                bob = 0.0

        # caminando: cuadros de la caminata + un saltito en cada paso
        walk_img = None

        if self.stage in ("walk", "settle"):

            phase = (self.t / max(0.05, cfg.RESCUER_WALK_STEP)) * math.pi

            walk_img = anim().walk(
                int(self.t * getattr(cfg, "FAROLERO_WALK_FPS", 6.0)), side_h,
                self.walk_dir,
            )

            hop = 0.0 if walk_img is not None else 1.0

            bob = -abs(math.sin(phase)) * cfg.RESCUER_WALK_HOP * img.get_height() * hop

        # sentado detras de la mesita (despues de llegar)
        seat = None

        if self.seat is not None and self.stage in ("sit", "leave"):
            seat = anim().sit(int(self.seat), side_h)

        sx = int(self.pos.x * zoom - camera.x)
        sy = int(self.pos.y * zoom - camera.y + bob)

        # resplandor detras (luz sumada)
        gr = int(img.get_height() * (0.95 + 0.08 * math.sin(t * 5.0)))

        if self.stage == "hold":
            gr = int(gr * (1.0 + 0.5 * min(1.0, self.t / cfg.RESCUE_HOLD_MIN)))

        if getattr(cfg, "FAROLERO_WARM_TINT", False):

            halo = _glow(gr // STEP_RADIUS * STEP_RADIUS or STEP_RADIUS)

            k = self.fade * 0.85

            if ritual is not None:
                k *= 0.2 + 0.5 * glow_k

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

        if seat is not None:

            simg, (ax, ay) = seat

            screen.blit(simg, (sx - ax, sy - ay))

        elif ritual is not None:

            rimg, (ax, ay) = ritual

            screen.blit(rimg, (sx - ax, sy - ay))

        else:

            body = walk_img if walk_img is not None else img

            if self.fade < 0.999:

                body = body.copy()
                body.set_alpha(int(255 * self.fade))

            screen.blit(body, body.get_rect(midbottom=(sx, sy)))

        self._draw_wave(screen, camera, sx, sy - img.get_height() // 2)

    def draw_room_tint(self, screen, camera):
        """Tono de fuego del cuarto mientras se ilumina (despues de la
        oscuridad). Al terminar sigue FaroleroNPC.draw_room_tint."""

        if not self.active or self.room < 0.03:
            return

        boost = 1.0

        if self.stage == "burst":

            flash = float(getattr(cfg, "ROOM_FIRE_FLASH", 0.0))

            boost += flash * max(0.0, 1.0 - self.t / 1.2)

        _draw_room_fire(screen, camera, self.room, self.pos, boost)


# ------------------------------------------------------------- imagenes opcionales

_img_cache = {}


def _combat_image(name):
    """assets/maps/combate/<name> o None si falta."""

    if not name:
        return None

    if name not in _img_cache:

        try:
            _img_cache[name] = pygame.image.load(
                str(COMBAT_DIR / name)
            ).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            _img_cache[name] = None

    return _img_cache[name]


_deco_cache = {}


def _scaled_art(key, size, zoom, builder):
    """Dibujo provisorio (hecho a pixel real del mundo) agrandado `zoom` veces
    sin suavizar; se guarda para no rehacerlo cada cuadro."""

    ck = (key, size, zoom)

    img = _deco_cache.get(ck)

    if img is None:

        if len(_deco_cache) > 60:
            _deco_cache.clear()

        base = builder(*size)

        w = max(1, int(round(size[0] * zoom)))
        h = max(1, int(round(size[1] * zoom)))

        img = pygame.transform.scale(base, (w, h))

        _deco_cache[ck] = img

    return img


def _fit_image(img, size, zoom):
    """Imagen del usuario ajustada al rectangulo (conserva la proporcion)."""

    ck = (id(img), size, zoom)

    out = _deco_cache.get(ck)

    if out is None:

        if len(_deco_cache) > 60:
            _deco_cache.clear()

        tw = max(1, int(size[0] * zoom))
        th = max(1, int(size[1] * zoom))

        k = min(tw / img.get_width(), th / img.get_height())

        out = pygame.transform.smoothscale(
            img,
            (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k)))
        )

        _deco_cache[ck] = out

    return out


# ---- dibujos provisorios (pixel art chiquito)

WOOD = (122, 84, 48)
WOOD_LIGHT = (160, 114, 66)
WOOD_DARK = (74, 48, 26)
IRON = (62, 62, 70)


def _build_door(w, h):

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    surf.fill(WOOD)

    # tablas verticales
    for x in range(2, w - 1, 3):
        pygame.draw.line(surf, WOOD_DARK, (x, 0), (x, h - 1))

    pygame.draw.line(surf, WOOD_LIGHT, (1, 0), (1, h - 1))

    # herrajes
    for y in (int(h * 0.18), int(h * 0.80)):
        pygame.draw.rect(surf, IRON, (0, y, w, 3))
        pygame.draw.rect(surf, (110, 110, 120), (0, y, w, 1))

    # manija
    pygame.draw.rect(surf, (214, 178, 80), (w - 4, h // 2 - 1, 2, 3))

    pygame.draw.rect(surf, WOOD_DARK, surf.get_rect(), 1)

    return surf


def _build_table(w, h):

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    top_h = max(6, int(h * 0.55))

    # patas
    for x in (3, w - 6):
        pygame.draw.rect(surf, WOOD_DARK, (x, top_h, 3, h - top_h))

    # tapa
    pygame.draw.rect(surf, WOOD_LIGHT, (0, 0, w, top_h))
    pygame.draw.rect(surf, WOOD, (0, top_h - 3, w, 3))
    pygame.draw.rect(surf, WOOD_DARK, (0, 0, w, top_h), 1)

    # mantel (franja)
    pygame.draw.rect(surf, (150, 52, 52), (6, 1, w - 12, top_h - 2))
    pygame.draw.rect(surf, (214, 168, 80), (6, 1, w - 12, 1))

    # lo que vende: botellas, hongos, un candil
    for i, col in enumerate(((120, 70, 190), (200, 140, 60), (90, 150, 220))):
        bx = 11 + i * 6
        pygame.draw.rect(surf, col, (bx, 2, 3, 5))
        pygame.draw.rect(surf, (230, 230, 240), (bx + 1, 1, 1, 1))

    for hx in (31, 37):
        pygame.draw.rect(surf, (40, 90, 190), (hx, 3, 5, 3))
        pygame.draw.rect(surf, (230, 230, 240), (hx + 1, 6, 3, 1))

    lx = w - 15
    pygame.draw.rect(surf, (255, 226, 120), (lx, 1, 4, 5))
    pygame.draw.rect(surf, IRON, (lx, 1, 4, 5), 1)

    return surf


def _build_rug(w, h):

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    pygame.draw.rect(surf, (96, 38, 40), surf.get_rect(), border_radius=3)
    pygame.draw.rect(surf, (186, 140, 70), surf.get_rect(), 1, border_radius=3)
    pygame.draw.rect(surf, (140, 62, 56), surf.get_rect().inflate(-8, -8), 1)

    for x in range(8, w - 6, 8):
        pygame.draw.rect(surf, (186, 140, 70), (x, h // 2 - 1, 3, 3))

    return surf


def _build_shelf(w, h):

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    pygame.draw.rect(surf, WOOD_DARK, (0, h - 4, w, 4))
    pygame.draw.rect(surf, WOOD, (0, h - 4, w, 2))

    cols = ((120, 70, 190), (214, 168, 80), (90, 150, 220), (150, 52, 52),
            (60, 150, 90), (200, 140, 60))

    x = 3

    for i in range(6):

        if x > w - 7:
            break

        bh = 5 + (i % 3) * 2

        pygame.draw.rect(surf, cols[i % len(cols)], (x, h - 4 - bh, 5, bh))
        pygame.draw.rect(surf, (235, 235, 245), (x + 1, h - 4 - bh - 1, 3, 1))

        x += 8

    return surf


def _build_crate(w, h):

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    surf.fill(WOOD)

    pygame.draw.rect(surf, WOOD_DARK, surf.get_rect(), 1)
    pygame.draw.line(surf, WOOD_DARK, (1, 1), (w - 2, h - 2))
    pygame.draw.line(surf, WOOD_DARK, (w - 2, 1), (1, h - 2))
    pygame.draw.rect(surf, WOOD_LIGHT, (1, 1, w - 2, 1))

    return surf


# ------------------------------------------------------------- la puerta

class RescueDoor:
    """Tapa el hueco de la pared derecha. Cerrada y SOLIDA hasta que el
    Farolero entra y la rompe con efecto (astillas, polvo, flash, temblor).
    Imagen: assets/maps/combate/<DOOR_IMAGE> (o un dibujo provisorio)."""

    COLORS = (WOOD, WOOD_LIGHT, WOOD_DARK, IRON)

    def __init__(self, broken=False):

        self.rect = pygame.Rect(*cfg.DOOR_RECT)

        self.broken = bool(broken)

        self.debris = []
        self.dust = []

        rng = random.Random(7)

        self.rubble = []

        for _ in range(int(getattr(cfg, "DOOR_RUBBLE", 9))):

            self.rubble.append((
                rng.uniform(self.rect.left - 9, self.rect.right + 3),
                rng.uniform(self.rect.top + 1, self.rect.bottom - 3),
                rng.choice((2, 2, 3, 4)),
                rng.choice((1, 2, 2, 3)),
                rng.choice(self.COLORS),
            ))

    def solid_rect(self):
        """Caja que bloquea al jugador (None si ya se rompio)."""

        return None if self.broken else self.rect

    def smash(self, game):
        """Se rompe de golpe."""

        if self.broken:
            return

        self.broken = True

        cx, cy = self.rect.center

        for _ in range(int(getattr(cfg, "DOOR_DEBRIS", 34))):

            # salen sobre todo hacia adentro de la sala (izquierda)
            ang = math.radians(random.uniform(125, 235))
            speed = random.uniform(70, 230)

            self.debris.append({
                "x": cx + random.uniform(-2, 2),
                "y": cy + random.uniform(-self.rect.height * 0.45, self.rect.height * 0.45),
                "vx": math.cos(ang) * speed,
                "vy": math.sin(ang) * speed * 0.8,
                "size": random.choice((2, 2, 3, 3, 4)),
                "col": random.choice(self.COLORS),
                "age": 0.0,
                "life": cfg.DOOR_DEBRIS_LIFE * random.uniform(0.7, 1.1),
            })

        for _ in range(10):

            self.dust.append({
                "x": cx + random.uniform(-6, 4),
                "y": cy + random.uniform(-self.rect.height * 0.4, self.rect.height * 0.4),
                "vx": random.uniform(-40, -6),
                "vy": random.uniform(-10, 10),
                "r": random.uniform(4, 7),
                "age": 0.0,
                "life": random.uniform(0.7, 1.2),
            })

        fx = getattr(game, "fx", None)

        if fx is not None:

            try:
                fx.flash(0.55, (255, 232, 170), 0.5)
                fx.shake(6.0, 0.7)
            except Exception as error:
                print(f"[puerta] efecto: {error}")

        audio.play("door_break")
        audio.play("explosion", 0.6)

    def update(self, dt):

        if not self.broken:
            return

        for d in self.debris:

            d["age"] += dt

            k = math.exp(-3.2 * dt)

            d["vx"] *= k
            d["vy"] *= k

            d["x"] += d["vx"] * dt
            d["y"] += d["vy"] * dt

        self.debris = [d for d in self.debris if d["age"] < d["life"]]

        for p in self.dust:

            p["age"] += dt

            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= math.exp(-2.0 * dt)

            p["r"] += 9.0 * dt

        self.dust = [p for p in self.dust if p["age"] < p["life"]]

    def draw(self, screen, camera):

        zoom = camera.zoom

        r = self.rect

        if not self.broken:

            dest = camera.apply(r)

            if not dest.colliderect(screen.get_rect()):
                return

            img = _combat_image(getattr(cfg, "DOOR_IMAGE", None))

            if img is not None:
                art = _fit_image(img, (r.width, r.height), zoom)
            else:
                art = _scaled_art("door", (r.width, r.height), zoom, _build_door)

            screen.blit(art, art.get_rect(center=dest.center))

            return

        # astillas que quedan en el piso para siempre
        for x, y, w, h, col in self.rubble:

            pygame.draw.rect(screen, col, (
                int(x * zoom - camera.x), int(y * zoom - camera.y),
                int(w * zoom), int(h * zoom),
            ))

        for d in self.debris:

            left = d["life"] - d["age"]

            size = d["size"] * min(1.0, left / 0.35) * zoom

            if size < 1:
                continue

            pygame.draw.rect(screen, d["col"], (
                int(d["x"] * zoom - camera.x - size / 2),
                int(d["y"] * zoom - camera.y - size / 2),
                int(size), int(size),
            ))

        for p in self.dust:

            k = 1.0 - p["age"] / p["life"]

            rad = max(2, int(p["r"] * zoom))

            puff = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)

            pygame.draw.circle(puff, (190, 184, 170, int(110 * k)), (rad, rad), rad)

            screen.blit(puff, (
                int(p["x"] * zoom - camera.x - rad),
                int(p["y"] * zoom - camera.y - rad),
            ))


# ------------------------------------------------------------- la tiendita

class ShopDecor:
    """Lo que hace que el cuarto del Farolero se sienta una tienda: alfombra,
    estante en la pared, mesita con mercaderia, cajas y lamparas. Aparece
    (con un fundido) cuando el Farolero va a su lugar. Los dibujos provisorios
    se pueden reemplazar con assets/maps/combate/<TABLE_IMAGE>."""

    FADE_TIME = 1.2

    def __init__(self, shown=False):

        self.shown = bool(shown)
        self.appear = 1.0 if shown else 0.0

        self.table = pygame.Rect(*cfg.TABLE_RECT)
        self.rug = pygame.Rect(*cfg.SHOP_RUG)
        self.shelf = pygame.Rect(*cfg.SHOP_SHELF)
        self.crates = [pygame.Rect(*c) for c in cfg.SHOP_CRATES]

    def reveal(self):

        self.shown = True

    def update(self, dt):

        if self.shown and self.appear < 1.0:
            self.appear = min(1.0, self.appear + dt / self.FADE_TIME)

    def visible(self, game):

        return self.shown and getattr(game, "current_map", "mapa1") == "mapa2"

    def solids(self):
        """Cajas que bloquean al jugador (la mesita y las cajas)."""

        if not self.shown:
            return []

        return [self.table] + list(self.crates)

    def light_sources(self, zoom):
        """Las lamparas de la mesa (luz fija)."""

        if self.appear < 0.99:
            return []

        return [
            (x, y, int(r * zoom)) for x, y, r in cfg.SHOP_LAMPS
        ]

    def _blit(self, screen, camera, rect, key, builder, img=None):

        dest = camera.apply(rect)

        if not dest.colliderect(screen.get_rect()):
            return

        zoom = camera.zoom

        if img is not None:
            art = _fit_image(img, (rect.width, rect.height), zoom)
        else:
            art = _scaled_art(key, (rect.width, rect.height), zoom, builder)

        alpha = int(255 * self.appear)

        if alpha < 255:
            art.set_alpha(alpha)

        screen.blit(art, art.get_rect(midbottom=dest.midbottom))

        if alpha < 255:
            art.set_alpha(255)

    def draw(self, screen, camera):
        """Se dibuja en el mundo (antes de la luz, asi lo alumbra el cuarto)."""

        if self.appear <= 0.01:
            return

        self._blit(
            screen, camera, self.rug, "rug", _build_rug,
            img=_combat_image(getattr(cfg, "RUG_IMAGE", None)),
        )
        self._blit(
            screen, camera, self.shelf, "shelf", _build_shelf,
            img=_combat_image(getattr(cfg, "SHELF_IMAGE", None)),
        )

        crate_img = _combat_image(getattr(cfg, "CRATE_IMAGE", None))

        for crate in self.crates:
            self._blit(
                screen, camera, crate, "crate", _build_crate, img=crate_img
            )

        self._blit(
            screen, camera, self.table, "table", _build_table,
            img=_combat_image(getattr(cfg, "TABLE_IMAGE", None)),
        )


# ------------------------------------------------------------- el Farolero fijo

_f_icon = [None]


def _prompt_icon():

    if _f_icon[0] is None:

        from world.shop import Shopkeeper

        _f_icon[0] = Shopkeeper._load_f_icon()

    return _f_icon[0]


class FaroleroNPC:
    """El Farolero DESPUES del rescate: se queda en su lugar (FAROLERO_SPOT).

    - El cuarto (RESCUE_ROOM) queda iluminado para siempre y CURA al jugador
      mientras este adentro, igual que la sala de la tienda.
    - Es solido (no se lo puede atravesar) y se le habla con la tecla de uso.
    - Es un segundo vendedor: abre la tienda con todo desbloqueado (ver
      FAROLERO_SHOP_UNLOCKED) y lo que compras cae al piso cerca de el.
    Solo existe en el mapa 2 (new_game lo crea cuando el rescate termina o
    cuando se carga una partida que ya lo paso).
    """

    ZONE_FEATHER = ROOM_FEATHER

    def __init__(self, game):

        self.game = game

        self.pos = pygame.Vector2(cfg.FAROLERO_SPOT)

        self.zone = ROOM_BANDS

        dx, dy, w, h = cfg.FAROLERO_TALK_RECT

        self._talk = pygame.Rect(dx, dy, w, h)

        hw, hh = cfg.FAROLERO_HITBOX

        self._hit = pygame.Rect(0, 0, hw, hh)

        self._sprites = {}

        # sale de donde termino el rescate: la luz no pega un salto
        self.spit_time = 0.0

    # ---- datos

    @property
    def visible(self):

        return getattr(self.game, "current_map", "mapa1") == "mapa2"

    @property
    def talk_rect(self):

        r = self._talk.copy()
        r.move_ip(int(self.pos.x), int(self.pos.y))

        return r

    def hitbox(self):

        r = self._hit.copy()
        r.midbottom = (int(self.pos.x), int(self.pos.y))

        return r

    def can_talk(self, player):

        return self.visible and player.rect.colliderect(self.talk_rect)

    def in_room(self, player):
        """El jugador esta en el cuarto que ilumina y cura."""

        c = player.rect.center

        return self.visible and any(b.collidepoint(c) for b in self.zone)

    # ---- luz

    def light_sources(self, zoom):

        if not self.visible:
            return []

        radius = int(round(cfg.FAROLERO_GLOW_RADIUS / STEP_RADIUS)) * STEP_RADIUS

        if radius < STEP_RADIUS:
            return []

        return [(self.pos.x, self.pos.y, int(radius * zoom))]

    def lit_rects(self):
        """El cuarto entero, iluminado siempre."""

        if not self.visible:
            return []

        return [(b, 1.0, self.ZONE_FEATHER) for b in self.zone]

    # ---- lo que compras

    def hand(self):
        """De donde sale lo que vende."""

        return (self.pos.x + 8, self.pos.y - 26)

    def _landing_point(self, collision_map):

        dx, dy, w, h = cfg.FAROLERO_LAND_RECT

        area = pygame.Rect(
            int(self.pos.x + dx), int(self.pos.y + dy), w, h
        )

        for _ in range(30):

            x = random.randint(area.left, area.right)
            y = random.randint(area.top, area.bottom)

            if collision_map.point_is_walkable(x, y):
                return (x, y)

        return area.center

    def deliver(self, item_ids, collision_map):
        """Saca las cosas compradas y las tira al piso cerca de el (el
        equivalente de Shopkeeper.spit). Devuelve los objetos creados."""

        from world.items import WorldItem, LightItem, set_expiry
        from world.lights import LIGHTS

        count = len(item_ids)

        if count == 0:
            return []

        gap = min(0.14, 4.0 / count)

        hx, hy = self.hand()

        items = []

        for n, item_id in enumerate(item_ids):

            if item_id in LIGHTS:
                item = LightItem(item_id, hx, hy)
            else:
                item = WorldItem(item_id, hx, hy)

            set_expiry(item)

            item.start_fly(
                (hx, hy),
                self._landing_point(collision_map),
                delay=0.25 + n * gap,
                height=22,
                duration=0.55,
                fancy=True,
            )

            items.append(item)

        return items

    # ---- dibujo

    def _sprite(self, side_h):

        img = self._sprites.get(side_h)

        if img is None:

            src = None

            try:
                src = pygame.image.load(str(COMBAT_DIR / PORTRAIT)).convert_alpha()
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

        if not self.visible:
            return

        zoom = camera.zoom

        base_h = getattr(getattr(self.game.player, "image_rect", None), "height", 40)

        side_h = max(16, int(base_h * cfg.RESCUE_HEIGHT * zoom / 4) * 4)

        img = self._sprite(side_h)

        t = pygame.time.get_ticks() / 1000.0

        bob = 0.0     # sin flotar

        # sentado detras de la mesita, con su animacion (para siempre)
        seat = None

        if anim().has_sit:
            seat = anim().sit(sit_idle_frame(t), side_h)

        # sin hoja de sentarse: cuadro parado de la hoja del ritual, respirando
        idle = anim().ritual(0, side_h) if anim().has_ritual else None

        if idle is not None:
            bob = 0.0

        sx = int(self.pos.x * zoom - camera.x)
        sy = int(self.pos.y * zoom - camera.y + bob)

        # fuera de pantalla: no se dibuja
        if not screen.get_rect().inflate(img.get_width() * 2, img.get_height() * 2).collidepoint(sx, sy):
            return

        # resplandor de su farol (luz sumada)
        gr = int(img.get_height() * (0.95 + 0.08 * math.sin(t * 5.0)))

        if getattr(cfg, "FAROLERO_WARM_TINT", False):

            halo = _glow(gr // STEP_RADIUS * STEP_RADIUS or STEP_RADIUS, (255, 168, 80))

            halo = halo.copy()
            halo.fill((217, 217, 217), special_flags=pygame.BLEND_RGB_MULT)

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

        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())

        screen.blit(shadow, shadow.get_rect(center=(sx, sy)))

        if seat is not None:

            simg, (ax, ay) = seat

            screen.blit(simg, (sx - ax, sy - ay))

        elif idle is not None:

            rimg, (ax, ay) = idle

            # respira: se estira y se achica de a poco (cada nivel se guarda)
            level = int(round(math.sin(t * 2.0) * 3))
            sway = int(round(math.sin(t * 1.1) * 2))

            key = ("idle", side_h, level)

            body = self._sprites.get(key)

            if body is None:

                k = 1.0 + 0.012 * level

                body = pygame.transform.smoothscale(
                    rimg,
                    (
                        max(2, int(rimg.get_width() * (2.0 - k))),
                        max(2, int(rimg.get_height() * k)),
                    ),
                )

                self._sprites[key] = body

            fx = ax * body.get_width() / float(rimg.get_width())
            fy = ay * body.get_height() / float(rimg.get_height())

            screen.blit(body, (int(sx - fx + sway * 0.5), int(sy - fy)))

        else:

            screen.blit(img, img.get_rect(midbottom=(sx, sy)))

    def draw_room_tint(self, screen, camera):
        """Tono de fuego del cuarto (queda para siempre)."""

        if not self.visible:
            return

        _draw_room_fire(screen, camera, 1.0, self.pos)

    def draw_prompt(self, screen, camera):
        """El icono de la tecla de uso arriba de su cabeza."""

        dest = camera.apply(pygame.Rect(int(self.pos.x) - 1, int(self.pos.y) - 40, 2, 2))

        icon = _prompt_icon()

        screen.blit(icon, icon.get_rect(midbottom=(dest.centerx, dest.top - 6)))