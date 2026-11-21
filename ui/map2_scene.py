"""Escena de entrada al mapa 2 (despues del comic final).

Coordenadas, textos y caras: world/map2_intro.py (editar SOLO ese archivo).

Este archivo tiene la logica:

  Map2Scene   la secuencia: Cenizo (2) -> monstruo -> Cenizo -> monstruo ->
              rayo del ojo que le pega a Cenizo -> Cenizo herido -> combate.
  EyeMonster  el monstruo del ojo en el mundo (se ve poco, el ojo brilla).
  EyeDialog   el monstruo hablando por el panel (como Cenizo y los jefes),
              con una cara distinta en cada frase.
"""

import math

import pygame

from core.audio_manager import audio
from ui.boss_dialog import BossDialog, COMBAT_DIR
from ui.tutorial import DEFAULT_THEME, Tutorial
from world import map2_intro as cfg


MONSTER_NAME = "Monstruo del ojo"

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
CHARGE_TIME = 1.1       # el ojo se carga
BEAM_TIME = 0.5         # el rayo sale
AFTER_TIME = 0.6        # silencio antes de que Cenizo hable


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


# ------------------------------------------------------ el monstruo (mundo)

class EyeMonster:
    """El monstruo del ojo en el mapa 2: solo se ve (no pelea)."""

    def __init__(self):

        self.pos = pygame.Vector2(cfg.MONSTER_POS)
        self.height = cfg.MONSTER_HEIGHT
        self.face = "base"
        self.charge = 0.0          # 0-1: el ojo se esta cargando

        self._src = {}
        self._scaled = {}
        self._masked = {}
        self._glow = {}

    # ---- posiciones

    def eye_world(self):
        """Donde esta el ojo en el mundo (de donde sale el rayo)."""

        src = self._source("base")
        ratio = src.get_width() / src.get_height()

        w = self.height * ratio

        fx, fy = cfg.EYE_FRAC

        return pygame.Vector2(
            self.pos.x + (fx - 0.5) * w,
            self.pos.y + (fy - 0.5) * self.height,
        )

    # ---- imagenes

    def _source(self, face):

        img = self._src.get(face)

        if img is None:

            img = _load_face(face) or _provisional()

            self._src[face] = img

        return img

    def _scaled_face(self, face, zoom):

        h = max(8, int(self.height * zoom))

        key = (face, h)

        img = self._scaled.get(key)

        if img is None:

            src = self._source(face)

            w = max(1, int(src.get_width() * h / src.get_height()))

            img = pygame.transform.smoothscale(src, (w, h))

            if cfg.MONSTER_ALPHA < 255:
                img.set_alpha(cfg.MONSTER_ALPHA)

            if len(self._scaled) > 8:
                self._scaled.clear()
                self._masked.clear()

            self._scaled[key] = img

        return img

    def _eye_only(self, face, zoom):
        """La imagen recortada con un circulo suave alrededor del ojo: se
        dibuja despues de la oscuridad para que el ojo brille."""

        img = self._scaled_face(face, zoom)

        key = (face, img.get_height())

        out = self._masked.get(key)

        if out is None:

            w, h = img.get_size()

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

            out = img.copy()
            out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            self._masked[key] = out

        return out

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

    def draw(self, screen, camera):
        """Cuerpo del monstruo (antes de la oscuridad: se ve poco)."""

        img = self._scaled_face(self.face, camera.zoom)

        rect = img.get_rect(center=self._screen_center(camera))

        if rect.colliderect(screen.get_rect()):
            screen.blit(img, rect)

    def draw_glow(self, screen, camera):
        """Ojo y resplandor (despues de la oscuridad: el ojo se ve)."""

        img = self._scaled_face(self.face, camera.zoom)

        rect = img.get_rect(center=self._screen_center(camera))

        if not rect.colliderect(screen.get_rect()):
            return

        h = img.get_height()

        ex = rect.left + int(cfg.EYE_FRAC[0] * img.get_width())
        ey = rect.top + int(cfg.EYE_FRAC[1] * h)

        angry = self.face == "ira" or self.charge > 0.0

        color = (255, 140, 60) if angry else (205, 198, 90)

        k = 1.0 + 1.6 * self.charge

        glow = self._glow_surf(max(8, int(h * 0.30 * k)), color)

        screen.blit(glow, glow.get_rect(center=(ex, ey)))

        eye = self._eye_only(self.face, camera.zoom)

        screen.blit(eye, rect)


# --------------------------------------------------- el monstruo (panel)

class EyeDialog(BossDialog):
    """El monstruo hablando por el panel, con una cara por pagina."""

    THEME = EYE_THEME

    PORTRAITS = ("monstruo_ojo.png",)

    CHAR_FRACTION = 0.50
    FRAME_WIDTH = 450

    # voz grave y lenta, mas amenazante que graciosa
    TYPE_SPEED = 30.0
    BLIP_EVERY = 2
    PAUSE_END = 0.5
    PAUSE_COMMA = 0.2
    PAUSE_DOTS = 0.3
    BLIPS = ("golem_a", "golem_b", "golem_c")

    HOP_TIME = 0.5

    def __init__(self, screen_size, pages, faces=()):

        self.faces = list(faces)
        self._face_cache = {}
        self._crop = None

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
        self._fired = False
        self._ended = False

    # ---- ayudas

    @property
    def eye(self):
        return self.game.eye_monster()

    def _size(self):
        return (self.game.width, self.game.height)

    def camera_focus(self):
        """La camara mira entre el jugador y el ojo para que se vean los
        dos (lo usa new_game._cinematic_focus)."""

        if self.stage in ("idle", "end"):
            return None

        p = pygame.Vector2(self.game.player.image_rect.center)
        e = self.eye.eye_world()

        f = p.lerp(e, 0.55)

        return (f.x, f.y, 1.0, 0.5)

    def _snap_camera(self):
        """Los dialogos frenan el juego: hay que acomodar la camara a mano."""

        g = self.game

        g.camera.update(g.player, focus=self.camera_focus())

    def _open_cenizo(self, pages, stage):

        self.stage = stage

        self._snap_camera()

        self._current = Tutorial(
            self._size(), pages=self.mark_keys(pages)
        )

        self.game.tutorial = self._current

    def _open_monster(self, pages, faces, stage):

        self.stage = stage

        self.eye.face = faces[0] if faces else "base"

        self._snap_camera()

        self._current = EyeDialog(self._size(), pages=pages, faces=faces)

        self.game.tutorial = self._current

    # ---- secuencia

    def start(self):
        """Despues de la transicion: Cenizo ya esta al lado y habla."""

        g = self.game

        spot = pygame.Vector2(g.player.image_rect.center) + (
            62, -14
        )

        g.cenizo.appear(spot, instant=True)
        g.cenizo.set_hold(True)

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
            self._fired = False
            self._ended = False
            self.eye.face = "ira"
            self._snap_camera()

        elif self.stage == "hurt":

            self._finish()

    def _finish(self):
        """Empieza el combate: las arañas despiertan solas (el juego ya no
        esta frenado). Cenizo se queda un rato y se desvanece."""

        self.stage = "end"
        self.eye.charge = 0.0
        self.eye.face = "base"

        self.game.cenizo.set_hold(False)

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

        g.cenizo.update(dt, g.player)

        # el ojo se carga
        if self.t < CHARGE_TIME:

            self.eye.charge = self.t / CHARGE_TIME

            g.fx.shake(1.0 + 2.0 * self.eye.charge, 0.1)

        # sale el rayo
        elif not self._fired:

            self._fired = True

            self.eye.charge = 1.0

            target = self._target()

            try:
                g.fx.shake(6.0, 0.5)
                g.fx.flash(0.22, (255, 150, 70), 0.6)
                g.fx.hit(
                    target.x, target.y, heavy=True, color=(255, 150, 70)
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

            self._open_cenizo(cfg.CENIZO_HURT, "hurt")

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

        fade = 1.0 - max(0.0, (beam_t - BEAM_TIME * 0.6) / (BEAM_TIME * 0.4))

        jitter = 0.85 + 0.15 * math.sin(self.t * 70.0)

        self._draw_beam(screen, a, b, fade * jitter)

    @staticmethod
    def _draw_beam(screen, a, b, k):

        pad = 90

        left = int(min(a.x, b.x)) - pad
        top = int(min(a.y, b.y)) - pad
        w = int(abs(a.x - b.x)) + pad * 2
        h = int(abs(a.y - b.y)) + pad * 2

        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        pa = (a.x - left, a.y - top)
        pb = (b.x - left, b.y - top)

        layers = (
            (48, (255, 90, 30, 70)),
            (30, (255, 140, 50, 125)),
            (16, (255, 214, 130, 205)),
            (7, (255, 255, 238, 255)),
        )

        for width, color in layers:

            wd = max(1, int(width * k))

            col = (*color[:3], int(color[3] * min(1.0, k + 0.2)))

            pygame.draw.line(surf, col, pa, pb, wd)

            pygame.draw.circle(surf, col, (int(pb[0]), int(pb[1])), wd // 2)
            pygame.draw.circle(surf, col, (int(pa[0]), int(pa[1])), wd // 2)

        screen.blit(surf, (left, top))