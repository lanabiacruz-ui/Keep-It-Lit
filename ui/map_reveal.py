import math

import pygame

from core.audio_manager import audio


# Transicion "comic -> mapa" (sin luz: el monstruo oscuro se la llevo).
#
# El personaje despierta en la oscuridad:
#
#   0.00 - 0.45  el ultimo cuadro del comic se apaga a negro
#   0.45 - 1.40  negro total, solo latidos
#   1.40 - 3.60  los parpados se abren (un primer parpadeo corto y
#                despues del todo) y el mapa, tan oscuro como en el
#                juego, aparece desde el negro
#   1.40 - 4.00  la camara arranca cerca del personaje y se aleja lento
#   3.30 - 4.20  la interfaz (HUD / dialogo) aparece con fundido


PRE_TIME = 0.45
OPEN_START = 1.40
FADE_TIME = 2.20
ZOOM_TIME = 2.60
UI_START = 3.30
UI_TIME = 0.90
TOTAL_TIME = 4.25

ZOOM_FROM = 1.65


def _clamp(v, lo=0.0, hi=1.0):

    return max(lo, min(hi, v))


def _span(t, a, b):

    if b <= a:
        return 1.0 if t >= b else 0.0

    return _clamp((t - a) / (b - a))


def _ease_out(k, power=3.0):

    return 1.0 - (1.0 - _clamp(k)) ** power


def _ease_in(k, power=2.0):

    return _clamp(k) ** power


def _ease_in_out(k):

    k = _clamp(k)

    return k * k * (3.0 - 2.0 * k)


class MapReveal:

    def __init__(self, game, old_frame=None):

        self.game = game

        self.w, self.h = game.screen.get_size()

        self.t = 0.0

        self.old = old_frame

        if old_frame is not None:

            r, g, b = pygame.transform.average_color(old_frame)[:3]

            # si el comic ya termino en negro no hay nada que apagar
            if (r + g + b) / 3 < 8:
                self.old = None

        self.black = pygame.Surface((self.w, self.h))
        self.black.fill((0, 0, 0))

        self.canvas = pygame.Surface((self.w, self.h))

        self.full = pygame.Rect(0, 0, self.w, self.h)

        self.cues = set()

        # no se toca la luz del juego: el mapa se ve como siempre,
        # a oscuras. Solo la interfaz queda oculta al principio.
        game.cine_ui_alpha = 0.0

        self.px, self.py = self._player_point()

    @property
    def active(self):

        return self.t < TOTAL_TIME

    def _player_point(self):

        game = self.game

        zoom = game.camera.zoom

        rect = getattr(game.player, "image_rect", None)

        if rect is None:
            rect = game.player.rect

        x = rect.centerx * zoom - game.camera.x
        y = rect.centery * zoom - game.camera.y

        return (
            _clamp(x, 0, self.w),
            _clamp(y, 0, self.h)
        )

    def _cue(self, key, when, action):

        if when and key not in self.cues:

            self.cues.add(key)

            action()

    def update(self, dt):

        dt = min(dt, 0.05)

        self.t += dt

        t = self.t

        if not self.active:

            self.game.cine_ui_alpha = 1.0

            return "done"

        self._cue("hb1", t >= 0.50, lambda: audio.play("heartbeat", 0.55))
        self._cue("hb2", t >= 1.05, lambda: audio.play("heartbeat", 0.80))
        self._cue("out", t >= OPEN_START, lambda: audio.play("light_out", 0.45))
        self._cue("hb3", t >= 2.10, lambda: audio.play("heartbeat", 0.65))

        self.game.cine_ui_alpha = _ease_in_out(
            _span(t, UI_START, UI_START + UI_TIME)
        )

        return None

    def _eyelid(self):
        """0 = parpados cerrados, 1 = abiertos del todo."""

        t = self.t - OPEN_START

        if t <= 0:
            return 0.0

        # primer parpadeo: se entreabre y se cierra
        first = math.sin(_span(t, 0.0, 0.75) * math.pi) * 0.22

        # apertura final
        main = _ease_in_out(_span(t, 0.95, 2.2))

        return max(first, main)

    def _draw_world(self, surf):

        t = self.t - OPEN_START

        zoom_k = _ease_out(_span(t, 0.0, ZOOM_TIME), 2.4)

        scale = max(1.0, ZOOM_FROM ** (1 - zoom_k))

        if scale > 1.01:

            vw = self.w / scale
            vh = self.h / scale

            vx = _clamp(self.px - vw / 2, 0, self.w - vw)
            vy = _clamp(self.py - vh / 2, 0, self.h - vh)

            src = pygame.Rect(
                int(vx), int(vy), max(2, int(vw)), max(2, int(vh))
            ).clip(self.full)

            pygame.transform.scale(
                surf.subsurface(src), (self.w, self.h), self.canvas
            )

            surf.blit(self.canvas, (0, 0))

        # el mapa sale del negro
        fade = 1.0 - _ease_in_out(_span(t, 0.0, FADE_TIME))

        if fade > 0.0:

            self.black.set_alpha(int(255 * fade))

            surf.blit(self.black, (0, 0))

        # parpados
        open_amt = self._eyelid()

        lid = round(self.h / 2 * (1 - open_amt))

        if lid > 0:

            pygame.draw.rect(surf, (0, 0, 0), (0, 0, self.w, lid))
            pygame.draw.rect(surf, (0, 0, 0), (0, self.h - lid, self.w, lid))

    def draw(self, screen):

        if not self.active:
            return

        t = self.t

        if t < OPEN_START:

            screen.fill((0, 0, 0))

            if self.old is not None and t < PRE_TIME:

                screen.blit(self.old, (0, 0))

                self.black.set_alpha(
                    int(255 * _ease_in(_span(t, 0.0, PRE_TIME), 1.4))
                )

                screen.blit(self.black, (0, 0))

            return

        self._draw_world(screen)