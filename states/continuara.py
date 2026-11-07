import math

import pygame

from core.audio_manager import audio


def _clamp(v, lo=0.0, hi=1.0):

    return max(lo, min(hi, v))


def _ease_out(k):

    k = _clamp(k)

    return 1.0 - (1.0 - k) ** 3


class Continuara:
    """Pantalla negra con "Continuará..." que cierra el juego.

    update(dt) y handle_event(event) devuelven "done" cuando hay que
    volver al menu principal.
    """

    TEXT = "Continuará..."

    # negro total antes de que empiece a aparecer el texto
    DARK_TIME = 1.2

    # tiempo entre letra y letra
    LETTER_STEP = 0.11
    LETTER_FADE = 0.45

    # cuanto se queda el texto completo antes de irse solo
    HOLD_TIME = 3.6

    OUT_TIME = 1.4

    # desde cuando se acepta ENTER / click para salir
    INPUT_AFTER = 2.4

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()

        self.t = 0.0
        self.out_t = None
        self.cues = set()

        size = max(40, round(self.height * 0.12))

        font = pygame.font.Font(None, size)

        tracking = max(2, round(self.height * 0.006))

        self.letters = []

        x = 0

        for ch in self.TEXT:

            img = font.render(ch, True, (255, 238, 205))

            if ch == " ":
                adv = max(4, size // 3)
            else:
                adv = font.size(ch)[0]

            self.letters.append((img, x, adv))

            x += adv + tracking

        self.text_w = x - tracking
        self.text_h = font.get_height()

        hint_font = pygame.font.Font(
            None,
            max(18, round(self.height * 0.03))
        )

        self.hint = hint_font.render(
            "ENTER: volver al inicio",
            True,
            (110, 112, 125)
        )

        self.black = pygame.Surface((self.width, self.height))
        self.black.fill((0, 0, 0))

        self.glow = self._make_glow()

    def _make_glow(self):

        w = round(self.text_w * 1.5)
        h = round(self.text_h * 3.6)

        surf = pygame.Surface((w, h))
        surf.fill((0, 0, 0))

        steps = 40

        for i in range(steps, 0, -1):

            k = (1 - i / steps) ** 2.0

            rect = pygame.Rect(0, 0, w * i // steps, h * i // steps)
            rect.center = (w // 2, h // 2)

            pygame.draw.ellipse(
                surf,
                (
                    int(255 * k * 0.55),
                    int(150 * k * 0.55),
                    int(60 * k * 0.55),
                ),
                rect
            )

        return surf

    def _full_time(self):

        return (
            self.DARK_TIME
            + len(self.letters) * self.LETTER_STEP
            + self.LETTER_FADE
        )

    def _cue(self, key, when, action):

        if when and key not in self.cues:

            self.cues.add(key)

            action()

    def _leave(self):

        if self.out_t is None:
            self.out_t = 0.0

    def handle_event(self, event):

        if self.t < self.INPUT_AFTER:
            return None

        pressed = (
            event.type == pygame.KEYDOWN
            and event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_SPACE,
                pygame.K_ESCAPE,
            )
        ) or (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        )

        if pressed:
            self._leave()

        return None

    def update(self, dt):

        dt = min(dt, 0.05)

        self.t += dt

        self._cue(
            "hb1",
            self.t >= self.DARK_TIME,
            lambda: audio.play("heartbeat", 0.6)
        )

        self._cue(
            "lit",
            self.t >= self._full_time() - 0.3,
            lambda: audio.play("light_on", 0.5)
        )

        if (
            self.out_t is None
            and self.t >= self._full_time() + self.HOLD_TIME
        ):
            self._leave()

        if self.out_t is not None:

            self.out_t += dt

            if self.out_t >= self.OUT_TIME:
                return "done"

        return None

    def draw(self):

        surf = self.screen

        surf.fill((0, 0, 0))

        t = self.t - self.DARK_TIME

        if t > 0:

            cx = self.width // 2
            cy = round(self.height * 0.48)

            glow_k = _clamp(t / (len(self.letters) * self.LETTER_STEP + 1.0))

            level = int(
                140 * glow_k * (0.9 + 0.1 * math.sin(self.t * 6.0))
            )

            if level > 0:

                bloom = self.glow.copy()

                bloom.fill(
                    (level, level, level),
                    special_flags=pygame.BLEND_RGB_MULT
                )

                surf.blit(
                    bloom,
                    bloom.get_rect(center=(cx, cy)),
                    special_flags=pygame.BLEND_RGB_ADD
                )

            left = cx - self.text_w / 2

            for i, (img, x, adv) in enumerate(self.letters):

                q = _clamp((t - i * self.LETTER_STEP) / self.LETTER_FADE)

                if q <= 0:
                    continue

                e = _ease_out(q)

                scale = 1.0 + 0.5 * (1.0 - e)

                if abs(scale - 1.0) > 0.02:

                    im = pygame.transform.smoothscale(
                        img,
                        (
                            max(1, round(img.get_width() * scale)),
                            max(1, round(img.get_height() * scale))
                        )
                    )

                else:

                    im = img.copy()

                im.set_alpha(int(255 * q))

                surf.blit(
                    im,
                    im.get_rect(
                        center=(round(left + x + adv / 2), cy)
                    )
                )

            hint_k = _clamp(
                (self.t - self.INPUT_AFTER) / 1.0
            )

            if hint_k > 0 and self.out_t is None:

                self.hint.set_alpha(int(200 * hint_k))

                surf.blit(
                    self.hint,
                    self.hint.get_rect(
                        midbottom=(
                            self.width // 2,
                            self.height - round(self.height * 0.06)
                        )
                    )
                )

        if self.out_t is not None:

            fade = _clamp(self.out_t / self.OUT_TIME)

            self.black.set_alpha(int(255 * fade))

            surf.blit(self.black, (0, 0))