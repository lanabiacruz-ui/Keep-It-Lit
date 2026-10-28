"""Entrada y derrota "epicas" del jefe.

Es solo presentacion: barras de cine, titulo, temblores, chispas y
sonido. La arena lo arranca (start_intro / start_victory), lo actualiza
mientras esta activo y el juego deja quieto al jugador (ver
NewGame.cinematic_lock) para que no se pierda nada.

Los efectos evitan los destellos rapidos: hay como mucho UN destello
suave por momento clave y ninguna onda repetida.
"""

import math
import random

import pygame

from core.audio_manager import audio
from core.music_manager import music

# --- tiempos (segundos)

# la primera vez: el jefe sube durante este tiempo y recien ahi revienta
# el golpe. Tiene que coincidir con SLAM_T de tools/make_boss_music.py
INTRO_FIRST = 4.6
TITLE_FIRST = 3.6

# las demas veces: version corta
INTRO_SHORT = 2.0
TITLE_SHORT = 1.8

BARS_IN = 0.8
BARS_OUT = 0.7

VICTORY_TITLE = 3.4

BOSS_TAG = "JEFE DE LA ZONA 1"
BOSS_LABEL = "PIÑA COLOSAL"
BOSS_SUB = "Esquivá sus fragmentos y pegale cuando esté entera"

BAR_FRACTION = 0.115

GOLD = (255, 214, 120)
GOLD_DARK = (60, 28, 6)
WHITE_WARM = (255, 240, 214)
RED = (255, 90, 60)
GREEN_JUICE = (170, 235, 110)


def _ease_out(k):

    k = max(0.0, min(1.0, k))

    return 1.0 - (1.0 - k) ** 3


def _ease_in_out(k):

    k = max(0.0, min(1.0, k))

    return k * k * (3.0 - 2.0 * k)


class BossCinematic:

    def __init__(self):

        self.active = False
        self.mode = None

        self.t = 0.0

        self.closing = None

        self.title = None
        self.title_t = None
        self.title_len = 0.0

        self.first = False

        self._shake_cd = 0.0
        self._ember_acc = 0.0

        self._fonts = {}
        self._glow = {}

    # ------------------------------------------------------------ control

    def cancel(self):

        self.active = False
        self.mode = None
        self.closing = None
        self.title = None
        self.title_t = None

    def _begin(self, mode):

        self.active = True
        self.mode = mode
        self.t = 0.0
        self.closing = None
        self.title = None
        self.title_t = None
        self._shake_cd = 0.0
        self._ember_acc = 0.0

    def intro_time(self, first):

        return INTRO_FIRST if first else INTRO_SHORT

    def title_time(self, first):

        return TITLE_FIRST if first else TITLE_SHORT

    def hold_time(self, first):

        # lo que el jefe se queda quieto despues del golpe: el titulo y
        # las barras que se van, asi la pelea arranca con todo despejado
        return self.title_time(first) + BARS_OUT

    def start_intro(self, game, first):

        self._begin("intro")

        self.first = first

        self.title_len = self.title_time(first)

        if first:
            # la entrada completa: silencio, tension y golpe (9.8 s)
            music.stinger("boss_intro")

    def start_victory(self, game):

        self._begin("victory")

        self.first = False

    # ----------------------------------------------------------- eventos

    def on_slam(self, game, boss):
        """El jefe termina de subir: golpe, rugido y titulo."""

        fx = game.fx

        x, y = boss.pos.x, boss.pos.y

        fx.shake(13.0 if self.first else 9.0, 0.9)
        fx.hitstop = max(fx.hitstop, 0.14 if self.first else 0.08)

        # un solo destello, calido y suave
        fx.flash(0.55, (255, 190, 120), 0.26)

        # una onda grande y lenta
        fx._ring(x, y, 8, 230 if self.first else 170, 1.5, (255, 175, 80), 6)

        for _ in range(70 if self.first else 40):

            a = random.uniform(0, math.tau)

            fx._spark(
                x, y, a, random.uniform(60, 230), random.uniform(0.6, 1.3),
                random.choice(((255, 170, 70), (255, 225, 140), GREEN_JUICE)),
                size=random.uniform(1.8, 3.4), drag=1.8, streak=True,
            )

        if not self.first:
            audio.play("boss_slam")

        audio.play("boss_roar")

        self.title = ("PIÑA COLOSAL", "GUARDIANA DE LA GEMA", GOLD)
        self.title_t = 0.0

    def finale(self, game, boss):
        """El jefe termina de romperse: explosion final y titulo."""

        fx = game.fx

        x, y = boss.pos.x, boss.pos.y

        fx.shake(16.0, 1.2)
        fx.hitstop = max(fx.hitstop, 0.2)
        fx.flash(0.7, (255, 215, 150), 0.3)
        fx._ring(x, y, 10, 280, 1.9, (255, 200, 110), 7)

        for _ in range(110):

            a = random.uniform(0, math.tau)

            fx._spark(
                x, y, a, random.uniform(50, 300), random.uniform(0.7, 1.6),
                random.choice((
                    (255, 170, 70), (255, 225, 140), GREEN_JUICE,
                    (255, 255, 235),
                )),
                size=random.uniform(1.8, 3.6), drag=1.6, grav=40,
                streak=True,
            )

        audio.play("explosion")
        audio.play("boss_slam")

        music.stinger("boss_victory")

        self.title = (
            "PIÑA COLOSAL DERROTADA", "LA GEMA ES TUYA", GOLD
        )
        self.title_t = 0.0
        self.title_len = VICTORY_TITLE

    # -------------------------------------------------------- actualizar

    def update(self, dt, game, boss):

        if not self.active:
            return

        self.t += dt

        fx = game.fx

        if self.title_t is not None:

            self.title_t += dt

            if self.title_t >= self.title_len and self.closing is None:
                self.closing = 0.0

        if self.closing is not None:

            self.closing += dt

            if self.closing >= BARS_OUT:
                self.cancel()
                return

        if boss is None:
            return

        if self.mode == "intro":
            self._update_intro(dt, game, boss)

        elif self.mode == "victory":
            self._update_victory(dt, game, boss)

    def _rumble(self, dt, fx, amp):

        # temblor continuo y parejo (sin sacudidas bruscas)
        self._shake_cd -= dt

        if self._shake_cd <= 0:

            self._shake_cd = 0.12

            fx.shake(amp, 0.16)

    def _update_intro(self, dt, game, boss):

        fx = game.fx

        if not boss.spawning:
            return

        total = max(0.01, boss.intro_time)

        k = 1.0 - max(0.0, boss.spawn_t) / total

        if self.first:
            self._rumble(dt, fx, 0.8 + 4.2 * k ** 1.6)
        else:
            self._rumble(dt, fx, 0.6 + 2.2 * k)

        fx.vignette_t = max(fx.vignette_t, 0.6 + 0.8 * k)

        # brasas que suben alrededor del jefe
        self._ember_acc += dt * (8 + 40 * k ** 1.5)

        while self._ember_acc >= 1.0:

            self._ember_acc -= 1.0

            a = random.uniform(0, math.tau)
            r = boss.size * random.uniform(0.25, 0.7)

            fx._spark(
                boss.pos.x + math.cos(a) * r,
                boss.pos.y + math.sin(a) * r * 0.6,
                -math.pi / 2 + random.uniform(-0.5, 0.5),
                random.uniform(18, 55), random.uniform(0.7, 1.4),
                random.choice(((255, 150, 60), (255, 210, 110), GREEN_JUICE)),
                size=random.uniform(1.4, 2.4), drag=0.6,
            )

    def _update_victory(self, dt, game, boss):

        fx = game.fx

        if boss.dying and not boss.dead:

            k = boss.dying_k

            self._rumble(dt, fx, 1.5 + 6.0 * k ** 1.3)

            # jugo y chispas que salen cada vez mas seguido
            self._ember_acc += dt * (14 + 70 * k)

            while self._ember_acc >= 1.0:

                self._ember_acc -= 1.0

                a = random.uniform(0, math.tau)

                fx._spark(
                    boss.pos.x + random.uniform(-1, 1) * boss.size * 0.35,
                    boss.pos.y + random.uniform(-1, 1) * boss.size * 0.35,
                    a, random.uniform(40, 130), random.uniform(0.4, 0.9),
                    random.choice((
                        (255, 170, 70), GREEN_JUICE, (255, 225, 140)
                    )),
                    size=random.uniform(1.6, 2.8), drag=2.0, grav=60,
                    streak=True,
                )

    # ------------------------------------------------------------ dibujo

    def _font(self, size):

        font = self._fonts.get(size)

        if font is None:
            font = self._fonts[size] = pygame.font.Font(None, size)

        return font

    def bars_amount(self):

        if not self.active:
            return 0.0

        if self.closing is not None:
            return 1.0 - _ease_in_out(self.closing / BARS_OUT)

        return _ease_out(self.t / BARS_IN)

    def draw(self, screen):

        if not self.active:
            return

        sw, sh = screen.get_size()

        amount = self.bars_amount()

        if amount > 0.001:

            h = int(sh * BAR_FRACTION * amount)

            pygame.draw.rect(screen, (0, 0, 0), (0, 0, sw, h))
            pygame.draw.rect(screen, (0, 0, 0), (0, sh - h, sw, h))

            # filo dorado finito en el borde de las barras
            if h > 3:

                edge = (120, 84, 36)

                pygame.draw.line(screen, edge, (0, h), (sw, h), 1)
                pygame.draw.line(screen, edge, (0, sh - h - 1), (sw, sh - h - 1), 1)

        if self.mode == "intro" and self.title is None:
            self._draw_preview(screen, sw, sh)

        if self.title is not None and self.title_t is not None:
            self._draw_title(screen, sw, sh)

    def _draw_preview(self, screen, sw, sh):

        start = 0.9 if self.first else 0.5

        k = _ease_out((self.t - start) / 0.9)

        if k <= 0.01:
            return

        cy = int(sh * 0.27)

        tag = self._font(34).render(BOSS_TAG, True, (236, 224, 196))
        name = self._font(78).render(BOSS_LABEL, True, GOLD)
        sub = self._font(28).render(BOSS_SUB, True, (236, 224, 196))

        shade_tag = self._font(34).render(BOSS_TAG, True, (20, 10, 2))
        shade_name = self._font(78).render(BOSS_LABEL, True, GOLD_DARK)
        shade_sub = self._font(28).render(BOSS_SUB, True, (20, 10, 2))

        rise = int((1.0 - k) * 14)

        rows = (
            (tag, shade_tag, cy - 52),
            (name, shade_name, cy),
            (sub, shade_sub, cy + 48),
        )

        for img, shade, y in rows:

            img.set_alpha(int(255 * k))
            shade.set_alpha(int(255 * k))

            pos = (sw // 2, y + rise)

            screen.blit(shade, shade.get_rect(center=(pos[0] + 3, pos[1] + 3)))
            screen.blit(img, img.get_rect(center=pos))

    def _glow_for(self, text, size):

        key = (text, size)

        glow = self._glow.get(key)

        if glow is None:

            if len(self._glow) > 6:
                self._glow.clear()

            font = self._font(size)

            raw = font.render(text, True, (255, 170, 60))

            # sobre fondo negro: se suma a la escena sin dejar un recuadro
            base = pygame.Surface(raw.get_size())
            base.fill((0, 0, 0))
            base.blit(raw, (0, 0))

            small = pygame.transform.smoothscale(
                base, (max(2, base.get_width() // 6), max(2, base.get_height() // 6))
            )

            glow = pygame.transform.smoothscale(
                small, (base.get_width() + 60, base.get_height() + 40)
            )

            self._glow[key] = glow

        return glow

    def _draw_title(self, screen, sw, sh):

        text, sub, color = self.title

        t = self.title_t

        length = self.title_len

        fade_in = _ease_out(t / 0.5)
        fade_out = 1.0 - _ease_in_out((t - (length - 0.6)) / 0.6)

        alpha = max(0.0, min(1.0, fade_in * fade_out))

        if alpha <= 0.01:
            return

        # tamano: entra en pantalla con margen
        size = 118

        font = self._font(size)

        while font.size(text)[0] > sw * 0.86 and size > 40:

            size -= 6
            font = self._font(size)

        # las letras arrancan separadas y se juntan
        spread = (1.0 - _ease_out(t / 1.3)) * size * 0.55 + 2

        widths = [font.size(ch)[0] for ch in text]

        total = sum(widths) + spread * (len(text) - 1)

        x = sw / 2 - total / 2
        cy = int(sh * 0.27)

        glow = self._glow_for(text, size)

        # el resplandor respira lento (sin parpadeos)
        pulse = 0.78 + 0.22 * math.sin(t * 2.2)

        g = glow.copy()
        g.fill(
            (int(255 * alpha * pulse * 0.5),) * 3,
            special_flags=pygame.BLEND_RGB_MULT
        )

        # el brillo solo se ve cuando las letras ya se juntaron
        if spread < size * 0.2:
            screen.blit(
                g, g.get_rect(center=(sw // 2, cy)),
                special_flags=pygame.BLEND_RGB_ADD
            )

        for ch, w in zip(text, widths):

            if ch != " ":

                shade = font.render(ch, True, GOLD_DARK)
                body = font.render(ch, True, color)
                hi = font.render(ch, True, WHITE_WARM)

                for img in (shade, body, hi):
                    img.set_alpha(int(255 * alpha))

                px = int(x)

                screen.blit(shade, shade.get_rect(midleft=(px + 4, cy + 4)))
                screen.blit(body, body.get_rect(midleft=(px, cy)))

                # reflejo en la parte de arriba de la letra
                top = pygame.Rect(0, 0, w, body.get_height() // 2 - 6)
                hi_part = hi.subsurface(
                    top.clip(hi.get_rect())
                ) if top.w > 0 and top.h > 0 else None

                if hi_part is not None:
                    hi_part.set_alpha(int(110 * alpha))
                    screen.blit(
                        hi_part,
                        hi_part.get_rect(
                            midleft=(px, cy - body.get_height() // 4 + 3)
                        )
                    )

            x += w + spread

        # linea dorada que se abre desde el centro
        line_w = int(min(sw * 0.62, total + 60) * _ease_out((t - 0.2) / 0.9))

        if line_w > 4:

            y = cy + int(size * 0.52)

            for i in range(line_w // 2):

                k = 1.0 - i / (line_w / 2)

                col = (
                    int(255 * k * alpha), int(196 * k * alpha),
                    int(96 * k * alpha)
                )

                screen.fill(col, (sw // 2 + i, y, 1, 3))
                screen.fill(col, (sw // 2 - i - 1, y, 1, 3))

        # subtitulo
        if sub and t > 0.8:

            sub_alpha = min(1.0, (t - 0.8) / 0.6) * fade_out

            sfont = self._font(max(26, size // 3))

            label = sfont.render(sub, True, (236, 224, 196))
            shade = sfont.render(sub, True, (20, 10, 2))

            label.set_alpha(int(255 * sub_alpha))
            shade.set_alpha(int(255 * sub_alpha))

            pos = (sw // 2, cy + int(size * 0.52) + 30)

            screen.blit(shade, shade.get_rect(center=(pos[0] + 2, pos[1] + 2)))
            screen.blit(label, label.get_rect(center=pos))