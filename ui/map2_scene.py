"""Escena de entrada al mapa 2 (despues del comic final).

Coordenadas, textos y caras: world/map2_intro.py (editar SOLO ese archivo).

Este archivo tiene la logica (cambios: Cenizo mas chico y lastimado despues
del rayo, monstruo enorme con voz de miedo, musica epica en main.py):

  Map2Scene   la secuencia: Cenizo (2) -> monstruo -> Cenizo -> monstruo ->
              rayo del ojo que le pega a Cenizo -> Cenizo herido -> combate.
  EyeMonster  el monstruo del ojo en el mundo (se ve poco, el ojo brilla).
  EyeDialog   el monstruo hablando por el panel (como Cenizo y los jefes),
              con una cara distinta en cada frase.
"""

import math

import pygame

from core.audio_manager import audio
from ui.cenizo_follower import HEIGHT_FRAC
from ui.boss_dialog import BossDialog, COMBAT_DIR
from ui.eye_pupil import find_slit
from ui.tutorial import DEFAULT_THEME, Tutorial
from world import map2_intro as cfg


MONSTER_NAME = cfg.MONSTER_NAME      # se cambia en world/map2_intro.py

EYE_THEME = dict(
    DEFAULT_THEME,
    name=MONSTER_NAME,
    text=(252, 240, 176),
    shadow=(26, 20, 4),
    hint=(214, 188, 84),
    name_bg=(72, 62, 14),
    name_edge=(236, 206, 60),
    name_text=(255, 246, 196),
    dot_on=(236, 206, 60),
    dot_on_edge=(60, 48, 6),
    dot_done=(150, 126, 30),
    dot_next=(84, 78, 54),
    arrow=(236, 206, 60),
    spark=(255, 236, 124),
    glow=(220, 190, 40),
    frame_border=(236, 206, 60),
    frame_fill=(26, 24, 14),
    frame_fill_alpha=238,
)

# tiempos del rayo (segundos)
CHARGE_TIME = 1.1       # el ojo se carga (dura igual que ojo_carga.wav)
BEAM_TIME = 1.1         # el rayo sale (llega a Cenizo en RAY_TRAVEL_TIME y se queda un rato)
AFTER_TIME = 1.3        # Cenizo sale despedido y se lo ve antes de que hable

# Cenizo en el dialogo se ve del tamaño de siempre (170, como en el tutorial)
CENIZO_DIALOG_HEIGHT = 170    # alto del retrato en el dialogo
CENIZO_WORLD_SCALE = 0.70     # escala de Cenizo flotando en el mundo
CENIZO_HURT_DIALOG_HEIGHT = 200   # Cenizo lastimado: mas grande (se veia muy chico)


# ------------------------------------------------------------- imagenes

def _face_path(face):

    name = "monstruo_ojo.png" if face in (None, "base") else (
        f"monstruo_ojo_{face}.png"
    )

    return COMBAT_DIR / name


def _load_face(face):
    """Imagen de una cara, o la base si falta, o None."""

    for f in (face, "base"):

        try:
            return pygame.image.load(str(_face_path(f))).convert_alpha()
        except (pygame.error, FileNotFoundError):
            continue

    return None


def _provisional():
    """Dibujo provisorio si no hay ninguna imagen: roca con un ojo."""

    surf = pygame.Surface((200, 300), pygame.SRCALPHA)

    pygame.draw.ellipse(surf, (60, 58, 50, 200), (20, 10, 160, 280))
    pygame.draw.ellipse(surf, (210, 190, 60, 255), (50, 100, 100, 90))
    pygame.draw.ellipse(surf, (30, 26, 10, 255), (90, 106, 20, 78))

    return surf


# ------------------------------------------------------ Cenizo lastimado

class CenizoHurtDialog(Tutorial):
    """Cenizo hablando despues del rayo: dibujo herido y tembloroso
    (assets/maps/ui/botayuda_herido.png, se crea con
    tools/make_cenizo_herido.py)."""

    HURT_IMAGE = "botayuda_herido.png"

    # habla mas despacio, con pausas, como quien le duele
    TYPE_SPEED = 40.0
    PAUSE_END = 0.34
    PAUSE_COMMA = 0.14
    PAUSE_DOTS = 0.24

    def _source_character(self):

        img = Tutorial._load_cropped(self.HURT_IMAGE, None)

        if img is None:
            return super()._source_character()

        return img

    def draw(self, screen):

        if not self.active or self.phase != "show":
            return super().draw(screen)

        # tiembla mientras habla (sufriendo un poco)
        amp = 2.0 if not self._typing_done() else 0.8
        shiver = int(round(math.sin(self.age * 47.0) * amp))

        saved = self.char_rect

        self.char_rect = saved.move(shiver, 0)

        try:
            super().draw(screen)
        finally:
            self.char_rect = saved


# ------------------------------------------------------ el monstruo (mundo)

def _patch_pupil(img):
    """Borra la pupila del dibujo (la rellena con el color del iris).

    Devuelve (imagen_sin_pupila, (cx, cy, ancho, alto, color)) con la
    pupila en pixeles del dibujo original, o None si no la encuentra. La
    pupila nueva se dibuja aparte y se mueve hacia el jugador.
    """

    w, h = img.get_size()

    def get(x, y):

        if 0 <= x < w and 0 <= y < h:
            c = img.get_at((x, y))
            return (c[0], c[1], c[2], c[3])

        return (0, 0, 0, 0)

    seed = (int(cfg.EYE_FRAC[0] * w), int(cfg.EYE_FRAC[1] * h))

    found = find_slit(get, w, h, seed)

    if found is None:
        return None

    fill, bbox, color, iris = found

    out = img.copy()

    iris_c = (iris[0], iris[1], iris[2], 255)

    for x, y in fill:
        out.set_at((x, y), iris_c)

    x0, y0, x1, y1 = bbox

    slit = (
        (x0 + x1 + 1) / 2.0, (y0 + y1 + 1) / 2.0,
        x1 - x0 + 1, y1 - y0 + 1, color,
    )

    return out, slit


class EyeMonster:
    """El monstruo del ojo en el mapa 2: no pelea, pero esta VIVO.

    - Flota: sube y baja, se balancea, y las dos manos de roca se mueven
      por su cuenta (ver FLOAT_* y HAND_RECTS en world/map2_intro.py).
    - Su ojo te mira: la pupila sigue al jugador (o a Cenizo mientras
      tira el rayo). Solo en las caras de EYE_LOOK_FACES.
    - Se agita (mas rapido y tembloroso) cuando esta furioso o cargando.
    """

    def __init__(self):

        self.pos = pygame.Vector2(cfg.MONSTER_POS)
        self.height = cfg.MONSTER_HEIGHT
        self.face = "base"
        self.charge = 0.0          # 0-1: el ojo se esta cargando

        # punto del mundo que mira en vez del jugador (el rayo mira a Cenizo)
        self.look_override = None

        self.look = pygame.Vector2()          # -1..1: hacia donde mira
        self.body_off = pygame.Vector2()      # flote del cuerpo (mundo)
        self.hand_off = [pygame.Vector2(), pygame.Vector2()]

        self._t = 0.0
        self._last = None

        self._raw_imgs = {}
        self._src = {}
        self._scaled = {}
        self._pupils = {}
        self._glow = {}

    # ---- posiciones

    def eye_world(self):
        """Donde esta el ojo en el mundo AHORA (de donde sale el rayo):
        sigue al cuerpo mientras flota."""

        src = self._raw("base")
        ratio = src.get_width() / src.get_height()

        w = self.height * ratio

        fx, fy = cfg.EYE_FRAC

        return pygame.Vector2(
            self.pos.x + self.body_off.x + (fx - 0.5) * w,
            self.pos.y + self.body_off.y + (fy - 0.5) * self.height,
        )

    def hitbox(self):
        """Caja de colision del monstruo (mundo): en sus pies, quieta (no
        sigue el flote). El jugador no puede atravesarla."""

        src = self._raw("base")
        ratio = src.get_width() / src.get_height()

        w = max(4, int(self.height * ratio * cfg.MONSTER_HITBOX_W))
        h = max(4, int(cfg.MONSTER_HITBOX_H))

        feet = self.pos.y + self.height / 2

        return pygame.Rect(
            int(self.pos.x - w / 2), int(feet - h), w, h
        )

    # ---- vida: flote y mirada

    def _advance(self, look_at):
        """Calcula el flote y la mirada de este cuadro (con el reloj real:
        no hace falta llamarlo desde el update del juego)."""

        now = pygame.time.get_ticks() / 1000.0

        dt = 0.0 if self._last is None else max(0.0, min(0.1, now - self._last))

        self._last = now
        self._t = now

        h = self.height

        angry = self.face == "ira" or self.charge > 0.0

        ts = now * cfg.FLOAT_SPEED * (1.5 if angry else 1.0)

        bob = cfg.FLOAT_BOB * h
        sway = cfg.FLOAT_SWAY * h

        bx = math.sin(ts * 0.7 + 0.5) * sway + math.sin(ts * 1.9) * sway * 0.25
        by = math.sin(ts * 1.25) * bob + math.sin(ts * 2.9 + 1.3) * bob * 0.22

        # cargando el rayo tiembla
        bx += math.sin(now * 63.0) * 0.006 * h * self.charge
        by += math.sin(now * 51.0 + 1.0) * 0.004 * h * self.charge

        # se inclina un poco hacia donde mira
        bx += self.look.x * cfg.FLOAT_LEAN * h

        self.body_off = pygame.Vector2(bx, by)

        # las manos flotan por su cuenta (y siguen un poco al cuerpo)
        self.hand_off[0] = pygame.Vector2(
            math.sin(ts * 0.9 + 2.0) * 0.025 * h + bx * 0.5,
            math.sin(ts * 1.6 + 1.0) * 0.050 * h + by * 0.5,
        )
        self.hand_off[1] = pygame.Vector2(
            math.sin(ts * 1.1 + 4.0) * 0.025 * h + bx * 0.5,
            math.sin(ts * 1.45 + 3.1) * 0.055 * h + by * 0.5,
        )

        # la mirada
        target = self.look_override if self.look_override is not None else look_at

        want = pygame.Vector2()

        if target is not None:

            d = pygame.Vector2(target) - self.eye_world()
            dist = d.length()

            if dist > 1.0:
                want = d / dist * min(1.0, dist / 60.0)

        k = 1.0 - math.exp(-cfg.EYE_LOOK_SMOOTH * dt)

        self.look = self.look + (want - self.look) * k

    # ---- imagenes

    def _raw(self, face):
        """Dibujo original de una cara (o provisorio)."""

        img = self._raw_imgs.get(face)

        if img is None:

            img = _load_face(face) or _provisional()

            self._raw_imgs[face] = img

        return img

    def _prepare(self, face):
        """Piezas de una cara en tamaño original: cuerpo (sin las manos y
        sin pupila si el ojo la sigue), manos y pupila."""

        info = self._src.get(face)

        if info is not None:
            return info

        img = self._raw(face)
        w, h = img.get_size()

        slit = None

        if face in cfg.EYE_LOOK_FACES:

            try:
                res = _patch_pupil(img)
            except Exception as error:
                print(f"[map2] pupila del monstruo: {error}")
                res = None

            if res is not None:
                img, slit = res

        body = img.copy()
        hands = []

        for fx0, fy0, fx1, fy1 in cfg.HAND_RECTS:

            r = pygame.Rect(
                int(fx0 * w), int(fy0 * h),
                int((fx1 - fx0) * w), int((fy1 - fy0) * h),
            ).clip(img.get_rect())

            if r.width < 2 or r.height < 2:
                continue

            hands.append((r, img.subsurface(r).copy()))

            body.fill((0, 0, 0, 0), r)

        info = {"size": (w, h), "body": body, "hands": hands, "slit": slit}

        self._src[face] = info

        return info

    def _parts(self, face, zoom):
        """Las piezas ya escaladas al zoom actual."""

        h = max(8, int(self.height * zoom))

        key = (face, h)

        parts = self._scaled.get(key)

        if parts is not None:
            return parts

        info = self._prepare(face)

        sw, sh = info["size"]

        w = max(1, int(sw * h / sh))

        sx, sy = w / sw, h / sh

        body = pygame.transform.smoothscale(info["body"], (w, h))

        if cfg.MONSTER_ALPHA < 255:
            body.set_alpha(cfg.MONSTER_ALPHA)

        hands = []

        for r, surf in info["hands"]:

            hw = max(1, int(r.width * sx))
            hh = max(1, int(r.height * sy))

            piece = pygame.transform.smoothscale(surf, (hw, hh))

            if cfg.MONSTER_ALPHA < 255:
                piece.set_alpha(cfg.MONSTER_ALPHA)

            hands.append((int(r.x * sx), int(r.y * sy), piece))

        pupil = None

        if info["slit"] is not None:

            cx, cy, pw, ph, color = info["slit"]

            pupil = (cx * sx, cy * sy, pw * sx, ph * sy, color)

        parts = {
            "size": (w, h), "body": body, "hands": hands,
            "pupil": pupil, "eye": None,
        }

        if len(self._scaled) > 8:
            self._scaled.clear()

        self._scaled[key] = parts

        return parts

    def _eye_layer(self, parts):
        """El cuerpo recortado con un circulo suave alrededor del ojo: se
        dibuja despues de la oscuridad para que el ojo brille."""

        eye = parts["eye"]

        if eye is None:

            body = parts["body"]
            w, h = parts["size"]

            ex = int(cfg.EYE_FRAC[0] * w)
            ey = int(cfg.EYE_FRAC[1] * h)

            radius = int(0.17 * h)

            # mascara: opaca cerca del ojo y transparente hacia afuera
            mask = pygame.Surface((w, h), pygame.SRCALPHA)
            mask.fill((255, 255, 255, 0))

            for r in range(int(radius * 1.5), 0, -2):

                a = int(255 * min(1.0, (1.5 - r / radius) / 1.0))

                pygame.draw.circle(
                    mask, (255, 255, 255, max(0, a)), (ex, ey), r
                )

            eye = body.copy()
            eye.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            parts["eye"] = eye

        return eye

    def _pupil_sprite(self, w, h, color):
        """Ovalo suave de la pupila (cacheado por tamaño)."""

        w = max(2, int(w / 2.0 + 0.5) * 2)
        h = max(4, int(h / 2.0 + 0.5) * 2)

        key = (w, h, color)

        spr = self._pupils.get(key)

        if spr is None:

            big = pygame.Surface((w * 3, h * 3), pygame.SRCALPHA)

            pygame.draw.ellipse(big, (*color, 255), big.get_rect())

            spr = pygame.transform.smoothscale(big, (w, h))

            if len(self._pupils) > 60:
                self._pupils.clear()

            self._pupils[key] = spr

        return spr

    def _glow_surf(self, radius, color):

        key = (radius, color)

        glow = self._glow.get(key)

        if glow is None:

            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            for i in range(radius, 0, -3):

                a = int(120 * (1.0 - i / radius) ** 1.8)

                pygame.draw.circle(glow, (*color, a), (radius, radius), i)

            if len(self._glow) > 10:
                self._glow.clear()

            self._glow[key] = glow

        return glow

    # ---- dibujo

    def _screen_center(self, camera):

        return (
            int(self.pos.x * camera.zoom - camera.x),
            int(self.pos.y * camera.zoom - camera.y),
        )

    def _body_origin(self, parts, camera):
        """Esquina de arriba a la izquierda del cuerpo en pantalla (con el
        flote ya sumado)."""

        w, h = parts["size"]

        cx, cy = self._screen_center(camera)

        return (
            cx - w // 2 + int(self.body_off.x * camera.zoom),
            cy - h // 2 + int(self.body_off.y * camera.zoom),
        )

    def _draw_pupil(self, screen, parts, left, top):
        """La pupila nueva, mirando hacia donde esta el jugador."""

        pupil = parts["pupil"]

        if pupil is None:
            return

        w, h = parts["size"]

        cx, cy, pw, ph, color = pupil

        dx = self.look.x * cfg.EYE_LOOK_X * w
        dy = self.look.y * cfg.EYE_LOOK_Y * h

        # late despacio, se ensancha al cargar el rayo y se afina al mirar de costado
        kx = 1.0 + 0.10 * math.sin(self._t * 2.2) + 0.45 * self.charge
        ky = 1.0 - 0.12 * abs(self.look.x)

        spr = self._pupil_sprite(pw * kx, ph * ky, color)

        screen.blit(
            spr,
            spr.get_rect(center=(int(left + cx + dx), int(top + cy + dy))),
        )

    def draw(self, screen, camera, look_at=None):
        """Cuerpo del monstruo (antes de la oscuridad: se ve poco).
        look_at = punto del mundo que mira (el jugador)."""

        self._advance(look_at)

        parts = self._parts(self.face, camera.zoom)

        w, h = parts["size"]

        left, top = self._body_origin(parts, camera)

        margin = int(0.20 * h)

        area = pygame.Rect(left - margin, top - margin, w + 2 * margin, h + 2 * margin)

        if not area.colliderect(screen.get_rect()):
            return

        # las manos flotan por su cuenta (detras del cuerpo)
        cx, cy = self._screen_center(camera)

        for i, (hx, hy, piece) in enumerate(parts["hands"]):

            off = self.hand_off[i] if i < len(self.hand_off) else self.body_off

            screen.blit(
                piece,
                (
                    cx - w // 2 + hx + int(off.x * camera.zoom),
                    cy - h // 2 + hy + int(off.y * camera.zoom),
                ),
            )

        screen.blit(parts["body"], (left, top))

        self._draw_pupil(screen, parts, left, top)

    def draw_glow(self, screen, camera, look_at=None):
        """Ojo y resplandor (despues de la oscuridad: el ojo se ve)."""

        parts = self._parts(self.face, camera.zoom)

        w, h = parts["size"]

        left, top = self._body_origin(parts, camera)

        rect = pygame.Rect(left, top, w, h)

        if not rect.colliderect(screen.get_rect()):
            return

        ex = left + int(cfg.EYE_FRAC[0] * w)
        ey = top + int(cfg.EYE_FRAC[1] * h)

        angry = self.face == "ira" or self.charge > 0.0

        color = (255, 140, 60) if angry else (205, 198, 90)

        k = 1.0 + 1.6 * self.charge

        glow = self._glow_surf(max(8, int(h * 0.30 * k)), color)

        screen.blit(glow, glow.get_rect(center=(ex, ey)))

        screen.blit(self._eye_layer(parts), rect)

        self._draw_pupil(screen, parts, left, top)


# --------------------------------------------------- el monstruo (panel)

class EyeDialog(BossDialog):
    """El monstruo hablando por el panel, con una cara por pagina.

    Da miedo: es enorme (casi toda la pantalla de alto), su voz es un
    gruñido grave propio (ojo_a/b/c, se hacen con tools/make_eye_sounds.py),
    cada frase arranca con un rugido y un temblor de pantalla, el borde de
    la pantalla se tiñe de rojo oscuro y el ojo late mientras habla.
    """

    THEME = EYE_THEME

    PORTRAITS = ("monstruo_ojo.png",)

    CHAR_FRACTION = 0.84          # era 0.50: ahora ocupa casi toda la pantalla
    FRAME_WIDTH = 450

    # voz grave y lenta: cada letra es un gruñido
    TYPE_SPEED = 24.0
    BLIP_EVERY = 2
    PAUSE_END = 0.70
    PAUSE_COMMA = 0.30
    PAUSE_DOTS = 0.45
    BLIPS = ("ojo_a", "ojo_b", "ojo_c")

    HOP_TIME = 0.5

    def __init__(self, screen_size, pages, faces=(), fx=None):

        self.faces = list(faces)
        self.fx = fx
        self._face_cache = {}
        self._crop = None
        self._vignette = None
        self._vignette_size = None

        super().__init__(screen_size, pages=pages)

    def _face_for(self, index):

        if 0 <= index < len(self.faces):
            return self.faces[index]

        return "base"

    def _face_surface(self, face):
        """La cara recortada igual que la base y del mismo tamaño que el
        personaje del panel (asi no cambia de tamaño entre frases)."""

        surf = self._face_cache.get(face)

        if surf is not None:
            return surf

        img = _load_face(face)

        if img is None:
            return None

        if self._crop is None:

            base = _load_face("base") or img

            self._crop = base.get_bounding_rect()

        crop = self._crop.clip(img.get_rect())

        if crop.width > 0 and crop.height > 0:
            img = img.subsurface(crop).copy()

        surf = pygame.transform.smoothscale(
            img, self.character.get_size()
        )

        self._face_cache[face] = surf

        return surf

    def _pop(self):

        super()._pop()

        # cambia la cara cada vez que cambia la pagina
        if not hasattr(self, "_face_cache"):
            return

        surf = self._face_surface(self._face_for(self.index))

        if surf is not None:
            self.character = surf

        # rugido + temblor de pantalla cada vez que habla
        audio.play("ojo_rugido")

        fx = getattr(self, "fx", None)

        if fx is not None:

            try:
                fx.shake(5.0, 0.9)
                fx.flash(0.30, (120, 0, 0), 0.35)
            except Exception as error:
                print(f"[map2] efecto de la voz: {error}")

    # ---- el miedo se dibuja aca

    def _make_vignette(self, size):
        """Borde de pantalla rojo oscuro (centro transparente)."""

        steps = 40

        # se pinta de afuera hacia adentro y el alfa va bajando: el borde
        # queda oscuro y el centro limpio
        vignette = pygame.Surface((160, 90), pygame.SRCALPHA)

        for i in range(steps, 0, -1):

            k = i / steps                     # 1 = borde, ~0 = centro

            alpha = int(205 * k ** 2.4)

            rect = pygame.Rect(0, 0, int(160 * k * 1.45), int(90 * k * 1.45))
            rect.center = (80, 45)

            pygame.draw.ellipse(vignette, (46, 0, 0, alpha), rect)

        return pygame.transform.smoothscale(vignette, size)

    def draw(self, screen):

        if not self.active:
            return

        size = screen.get_size()

        if self._vignette is None or self._vignette_size != size:

            self._vignette = self._make_vignette(size)
            self._vignette_size = size

        # entra y sale con el panel: el rojo no queda colgado en pantalla
        if self.phase == "in":
            k = min(1.0, self.phase_time / max(0.01, self.SLIDE_TIME))
        elif self.phase == "out":
            k = 1.0 - min(1.0, self.phase_time / max(0.01, self.SLIDE_TIME))
        else:
            k = 1.0

        # el rojo late como un corazon y parpadea de vez en cuando
        beat = 0.55 + 0.45 * math.sin(self.age * 5.2) ** 2
        flicker = 0.85 if math.sin(self.age * 23.0) > 0.93 else 1.0

        self._vignette.set_alpha(int(255 * k * beat * flicker))

        screen.blit(self._vignette, (0, 0))

        # el monstruo tiembla de furia mientras habla (como un gruñido)
        talking = self.phase == "show" and not self._typing_done()

        if talking:

            shake_x = int(round(math.sin(self.age * 61.0) * 3.0))
            shake_y = int(round(math.sin(self.age * 53.0 + 1.0) * 2.0))

            saved = self.char_rect

            self.char_rect = saved.move(shake_x, shake_y)

            try:
                super().draw(screen)
            finally:
                self.char_rect = saved

        else:
            super().draw(screen)

        if self.phase != "show":
            return

        # el ojo late rojo-naranja (luz aditiva, sin alpha)
        pulse = 0.5 + 0.5 * math.sin(self.age * (9.0 if talking else 3.0))

        r = int(self.char_rect.width * (0.20 + 0.04 * pulse))

        eye = pygame.Surface((r * 2, r * 2))

        for j in range(r, 0, -3):

            glow = (1.0 - j / r) ** 1.6 * (0.30 + 0.35 * pulse)

            pygame.draw.circle(
                eye,
                (int(255 * glow), int(90 * glow), int(20 * glow)),
                (r, r), j,
            )

        fx_, fy_ = cfg.EYE_FRAC

        screen.blit(
            eye,
            eye.get_rect(
                center=(
                    self.char_rect.left + int(fx_ * self.char_rect.width),
                    self.char_rect.top + int(fy_ * self.char_rect.height),
                )
            ),
            special_flags=pygame.BLEND_RGB_ADD,
        )


# ------------------------------------------------------------- la escena

class Map2Scene:
    """Secuencia de la entrada al mapa 2 (ver world/map2_intro.py)."""

    def __init__(self, game, mark_keys):

        self.game = game
        self.mark_keys = mark_keys

        self.stage = "idle"
        self.done = False
        self.ray_active = False

        self._current = None

        self.t = 0.0
        self._started = False
        self._fired = False
        self._ended = False

    # ---- ayudas

    @property
    def eye(self):
        return self.game.eye_monster()

    def _size(self):
        return (self.game.width, self.game.height)

    def camera_focus(self):
        """Hacia donde mira la camara en cada momento (lo usa
        new_game._cinematic_focus). Devuelve (x, y, k, ancla) o None:

            Cenizo habla      -> el jugador y Cenizo juntos, arriba del
                                 cuadro de dialogo (se ven los dos)
            el monstruo habla -> la camara se desplaza hacia el monstruo
            el rayo           -> sigue al rayo del ojo hasta Cenizo
            Cenizo herido     -> igual que cuando habla
        """

        if self.stage in ("idle", "end"):
            return None

        if self.stage in ("m1", "m2"):

            p = pygame.Vector2(self.game.player.image_rect.center)
            m = pygame.Vector2(self.eye.pos)

            f = p.lerp(m, cfg.CAMERA_MIX_MONSTER)

            return (f.x, f.y, 1.0, 0.5)

        if self.stage == "ray":
            return self._ray_focus()

        return self._talk_focus()

    def talk_point(self):
        """Punto medio entre el jugador y Cenizo (mundo)."""

        p = pygame.Vector2(self.game.player.image_rect.center)

        return p.lerp(pygame.Vector2(self.game.cenizo.pos), 0.5)

    def _talk_focus(self):
        """El jugador y Cenizo juntos, por encima del cuadro de dialogo."""

        f = self.talk_point()

        return (f.x, f.y, 1.0, cfg.CAMERA_ANCHOR_TALK)

    def _ray_focus(self):
        """La camara acompaña al rayo: se queda en el ojo mientras se
        carga y despues viaja con el rayo hasta Cenizo, donde termina
        encuadrando a Cenizo y al jugador (y se asoma el monstruo)."""

        eye = self.eye.eye_world()

        if self.t < CHARGE_TIME:
            return (eye.x, eye.y, 1.0, 0.5)

        u = min(1.0, (self.t - CHARGE_TIME) / max(0.05, cfg.RAY_TRAVEL_TIME))
        u = u * u * (3.0 - 2.0 * u)

        f = eye.lerp(self.talk_point(), u)

        anchor = 0.5 + (cfg.CAMERA_ANCHOR_TALK - 0.5) * u

        return (f.x, f.y, 1.0, anchor)

    def tick(self, dt):
        """Mueve la camara de a poco (los dialogos frenan el juego, por eso
        se llama desde new_game tambien mientras hay un dialogo abierto)."""

        if self.stage in ("idle", "end"):
            return

        g = self.game

        g.camera.update(g.player, dt=dt, focus=self.camera_focus())

    def _snap_camera(self):
        """Los dialogos frenan el juego: hay que acomodar la camara a mano."""

        g = self.game

        g.camera.update(g.player, focus=self.camera_focus())

    def _open_cenizo(self, pages, stage, hurt=False):

        self.stage = stage

        # al empezar la camara se acomoda de golpe; despues se desplaza sola
        if stage == "c1":
            self._snap_camera()

        # Cenizo con el tamaño de siempre; despues del rayo, lastimado
        # (y ahi se lo ve un poco mas grande)
        cls = CenizoHurtDialog if hurt else Tutorial

        self._current = cls(
            self._size(),
            pages=self.mark_keys(pages),
            char_height=(
                CENIZO_HURT_DIALOG_HEIGHT if hurt else CENIZO_DIALOG_HEIGHT
            ),
        )

        self.game.tutorial = self._current

    def _open_monster(self, pages, faces, stage):

        self.stage = stage

        self.eye.face = faces[0] if faces else "base"

        # la camara se desplaza hacia el monstruo (ver tick)

        self._current = EyeDialog(
            self._size(), pages=pages, faces=faces,
            fx=getattr(self.game, "fx", None),
        )

        self.game.tutorial = self._current

    # ---- secuencia

    def start(self):
        """Despues de la transicion: Cenizo ya esta al lado y habla."""

        g = self.game

        spot = pygame.Vector2(g.player.image_rect.center) + (
            62, -14
        )

        # la camara se mueve mas lento durante la escena (se restaura al final)
        self._old_smooth = g.camera.smoothing
        g.camera.smoothing = cfg.CAMERA_SMOOTH

        g.cenizo.appear(spot, instant=True)
        g.cenizo.size_mul = CENIZO_WORLD_SCALE
        g.cenizo.set_hold(True)

        # la transicion de entrada no corre el update: Cenizo ya tiene que
        # tener su tamaño final (si no, aparece grande y se achica de golpe)
        h = getattr(getattr(g.player, "image_rect", None), "height", None)

        if h:
            g.cenizo.height_world = h * HEIGHT_FRAC * CENIZO_WORLD_SCALE

        self.eye.face = "base"
        self.eye.charge = 0.0

        self._open_cenizo(cfg.CENIZO_1, "c1")

    def after_dialog(self, closed):
        """new_game la llama cuando se cierra cualquier dialogo."""

        if closed is not self._current:
            return

        self._current = None

        if self.stage == "c1":

            self._open_monster(
                cfg.MONSTER_1, cfg.MONSTER_1_FACES, "m1"
            )

        elif self.stage == "m1":

            self.eye.face = "base"
            self._open_cenizo(cfg.CENIZO_2, "c2")

        elif self.stage == "c2":

            self._open_monster(
                cfg.MONSTER_2, cfg.MONSTER_2_FACES, "m2"
            )

        elif self.stage == "m2":

            self.stage = "ray"
            self.ray_active = True
            self.t = 0.0
            self._started = False
            self._fired = False
            self._ended = False
            self.eye.face = "ira"

            # la camara acompaña al rayo mas rapido que en los dialogos
            self.game.camera.smoothing = cfg.CAMERA_SMOOTH_RAY

            # el ojo se clava en Cenizo mientras se carga
            self.eye.look_override = self._target()

            audio.play("ojo_carga")

        elif self.stage == "hurt":

            self._finish()

    def _finish(self):
        """Empieza el combate: las arañas despiertan solas (el juego ya no
        esta frenado). Cenizo se queda un rato y se desvanece."""

        self.stage = "end"
        self.eye.charge = 0.0
        self.eye.look_override = None
        self.eye.face = "base"

        self.game.cenizo.set_hold(False)

        old = getattr(self, "_old_smooth", None)

        if old is not None:
            self.game.camera.smoothing = old

        self.done = True

    # ---- el rayo

    def _target(self):
        return self.game.cenizo.center

    def update(self, dt):
        """Solo durante el rayo (new_game la llama mientras ray_active)."""

        if not self.ray_active:
            return

        g = self.game

        self.t += dt

        self.tick(dt)

        self.eye.look_override = self._target()

        g.cenizo.update(dt, g.player)

        # el ojo se carga
        if self.t < CHARGE_TIME:

            self.eye.charge = self.t / CHARGE_TIME

            g.fx.shake(1.5 + 4.5 * self.eye.charge, 0.1)

        # sale el rayo: viaja del ojo a Cenizo (la camara lo acompaña)
        else:

            self.eye.charge = 1.0

            if not self._started:

                self._started = True

                try:
                    audio.play("ojo_rayo")
                except Exception:
                    pass

            # el rayo llega: golpe, temblor y Cenizo sale despedido
            if not self._fired and (
                self.t >= CHARGE_TIME + cfg.RAY_TRAVEL_TIME
            ):

                self._fired = True

                target = self._target()

                try:
                    g.fx.shake(11.0, 1.1)
                    g.fx.flash(0.55, (255, 170, 90), 0.9)
                    g.fx.hit(
                        target.x, target.y, heavy=True, color=(255, 150, 70)
                    )
                    g.fx.hit(
                        target.x, target.y, heavy=True, color=(255, 230, 160)
                    )
                except Exception as error:
                    print(f"[map2] efecto del rayo: {error}")

                try:
                    audio.play("hit_heavy")
                except Exception:
                    pass

                g.cenizo.hurt(away_from=self.eye.eye_world())

        # termina: Cenizo habla herido
        if self.t >= CHARGE_TIME + BEAM_TIME + AFTER_TIME and not self._ended:

            self._ended = True
            self.ray_active = False
            self.eye.charge = 0.0

            self.game.camera.smoothing = cfg.CAMERA_SMOOTH

            # despues del golpe el ojo vuelve a mirar al jugador
            self.eye.look_override = None

            self._open_cenizo(cfg.CENIZO_HURT, "hurt", hurt=True)

    def draw_overlay(self, screen):
        """Carga del ojo y rayo (despues de todo lo demas)."""

        if not self.ray_active:
            return

        cam = self.game.camera

        eye = self.eye.eye_world()
        a = pygame.Vector2(
            eye.x * cam.zoom - cam.x, eye.y * cam.zoom - cam.y
        )

        if self.t < CHARGE_TIME:
            return

        beam_t = self.t - CHARGE_TIME

        if beam_t > BEAM_TIME:
            return

        tgt = self._target()
        b = pygame.Vector2(
            tgt.x * cam.zoom - cam.x, tgt.y * cam.zoom - cam.y
        )

        # la punta del rayo viaja del ojo hasta Cenizo
        u = min(1.0, beam_t / max(0.05, cfg.RAY_TRAVEL_TIME))
        u = 1.0 - (1.0 - u) ** 2

        b = a.lerp(b, u)

        fade = 1.0 - max(0.0, (beam_t - BEAM_TIME * 0.6) / (BEAM_TIME * 0.4))

        jitter = 0.85 + 0.15 * math.sin(self.t * 70.0)

        self._draw_beam(screen, a, b, fade * jitter)

    @staticmethod
    def _draw_beam(screen, a, b, k):

        pad = 120

        left = int(min(a.x, b.x)) - pad
        top = int(min(a.y, b.y)) - pad
        w = int(abs(a.x - b.x)) + pad * 2
        h = int(abs(a.y - b.y)) + pad * 2

        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        pa = (a.x - left, a.y - top)
        pb = (b.x - left, b.y - top)

        layers = (
            (84, (255, 70, 20, 60)),
            (56, (255, 100, 30, 100)),
            (34, (255, 150, 60, 150)),
            (18, (255, 214, 130, 215)),
            (8, (255, 255, 238, 255)),
        )

        for width, color in layers:

            wd = max(1, int(width * k))

            col = (*color[:3], int(color[3] * min(1.0, k + 0.2)))

            pygame.draw.line(surf, col, pa, pb, wd)

            pygame.draw.circle(surf, col, (int(pb[0]), int(pb[1])), wd // 2)
            pygame.draw.circle(surf, col, (int(pa[0]), int(pa[1])), wd // 2)

        screen.blit(surf, (left, top))