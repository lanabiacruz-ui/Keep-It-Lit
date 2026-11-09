import math
import random

import pygame

from core.audio_manager import audio
from ui.tutorial import (
    CHARACTER_IMAGE,
    HELPER_NAME,
    HINT_COLOR,
    TEXT_COLOR,
    Tutorial,
    draw_marked_line,
    parse_markup,
    wrap_marked,
)


CHEERS = [
    "¡Eso es!",
    "¡Bien hecho! Tu luz brilla más.",
    "¡Lo lograste! Eres un crack.",
    "¡Pan comido para ti!",
    "¡Qué manera de prender la mecha!",
    "¡Excelente! Cenizo está orgulloso.",
    "¡Ese es mi aventurero!",
    "¡Chispa! Sigue así.",
    "¡Buuu... perdón, quise decir BRAVO!",
    "¡Hasta mi esqueleto aplaude! (No tengo esqueleto.)",
    "¡Eso me dio tanta emoción que casi me muero! Otra vez.",
]

FAREWELL = (
    "¡Terminaste el entrenamiento! Ya sabes lo básico. "
    "Yo me quedo por aquí, flotando sin hacer nada, que es mi especialidad. ¡Que tu luz nunca se apague!"
)

LOW_LIGHT = [
    "¡Ey, tu luz está bajita! Usa madera, resina o aceite con [[F]]. ¡No te sumes al club de los fantasmas todavía!",
    "¡Se está apagando! Come algo de luz antes de que sea tarde. ¡Todavía no tengo con quién jugar a las cartas!",
]

# segundos sin avanzar antes del 1er, 2do, 3er... consejo del mismo paso
HINT_DELAYS = (22.0, 40.0, 70.0, 110.0)

BUBBLE_MAX_W = 300
BUBBLE_FONT = 25

BUBBLE_BG = (255, 255, 255)
CHEER_EDGE = (255, 150, 30)
HINT_EDGE = (70, 120, 210)


class Companion:
    """Cenizo: el ayudante que aparece con un cartelito para festejar los
    objetivos cumplidos, dar una mano si te trabás y avisar si tu luz está
    por apagarse. No frena el juego."""

    IN_TIME = 0.45
    OUT_TIME = 0.4

    def __init__(self, screen_size, char_height=104, margin=16):

        self.width, self.height = screen_size
        self.margin = margin

        char = Tutorial._load_cropped(CHARACTER_IMAGE, None)

        if char is None:
            char = Tutorial._fallback_character(300)

        w = int(char.get_width() * char_height / char.get_height())

        self.character = pygame.transform.smoothscale(char, (w, char_height))

        self.font = pygame.font.Font(None, BUBBLE_FONT)
        self.name_font = pygame.font.Font(None, 20)

        self.rest_rect = self.character.get_rect(
            bottomright=(self.width - margin, self.height - margin)
        )

        self.t = 0.0

        self.text = None
        self.kind = "cheer"
        self.priority = 0
        self.lines = []

        self.phase = None          # None, "in", "show", "out"
        self.phase_time = 0.0
        self.duration = 4.0
        self.hops = 0

        self.bubble = None

        self._last_cheer = None

        # seguimiento de "me trabe"
        self._step_index = None
        self._stuck = 0.0
        self._hints_given = 0
        self._light_cooldown = 0.0

    @property
    def busy(self):

        return self.phase is not None

    # ------------------------------------------------------------ hablar

    def say(self, text, seconds=None, kind="cheer", priority=0):

        if self.busy and priority < self.priority:
            return False

        self.text = text
        self.kind = kind
        self.priority = priority

        if seconds is None:
            seconds = 3.2 if kind == "cheer" else 5.5

        self.duration = seconds

        self.bubble = self._build_bubble(text, kind)

        if self.phase in (None, "out"):
            self.phase = "in"
            self.phase_time = 0.0
        elif self.phase == "show":
            # ya estaba en pantalla: solo cambia el texto y salta de nuevo
            self.phase_time = 0.0

        self.hops = 2 if kind == "cheer" else 1

        audio.play("talk_a")

        return True

    def cheer(self, text=None):

        if text is None:

            options = [c for c in CHEERS if c != self._last_cheer]

            text = random.choice(options)

            self._last_cheer = text

        self.say(text, kind="cheer", priority=1)

    def farewell(self):

        self.say(FAREWELL, seconds=7.0, kind="cheer", priority=3)

    def _build_bubble(self, text, kind):

        plain, flags = parse_markup(text)

        pad = 14

        lines = wrap_marked(self.font, plain, flags, BUBBLE_MAX_W - pad * 2)

        line_h = self.font.get_linesize()

        width = max(self.font.size(t)[0] for t, _ in lines) + pad * 2 + 8

        width = max(width, 120)

        name_h = 18

        height = pad + name_h + line_h * len(lines) + pad - 2

        surf = pygame.Surface((width, height + 10), pygame.SRCALPHA)

        body = pygame.Rect(0, 0, width, height)

        edge = CHEER_EDGE if kind == "cheer" else HINT_EDGE

        pygame.draw.rect(surf, BUBBLE_BG, body, border_radius=14)
        pygame.draw.rect(surf, edge, body, width=3, border_radius=14)

        # colita hacia el ayudante (a la derecha)
        tail = [
            (width - 3, height - 34),
            (width + 11, height - 24),
            (width - 3, height - 14),
        ]

        pygame.draw.polygon(surf, BUBBLE_BG, tail)
        pygame.draw.lines(surf, edge, False, tail, 3)
        pygame.draw.line(
            surf, BUBBLE_BG,
            (width - 3, height - 33), (width - 3, height - 15), 4
        )

        name = self.name_font.render(
            HELPER_NAME.upper() if kind == "cheer" else HELPER_NAME.upper() + " TE AYUDA",
            True,
            (150, 70, 0) if kind == "cheer" else HINT_COLOR
        )

        surf.blit(name, (pad, pad - 4))

        y = pad - 4 + name_h

        for line, line_flags in lines:

            draw_marked_line(
                surf, self.font, line, line_flags, pad, y, TEXT_COLOR
            )

            y += line_h

        return surf

    # --------------------------------------------------- mirar la partida

    def observe(self, dt, game, step_index, step):
        """Llamar una vez por frame mientras se juega normal. Da consejos si
        el jugador se traba en un paso y avisa si la luz esta baja."""

        if self._light_cooldown > 0:
            self._light_cooldown = max(0.0, self._light_cooldown - dt)

        if step_index != self._step_index:

            self._step_index = step_index
            self._stuck = 0.0
            self._hints_given = 0

        else:

            self._stuck += dt

        vida = getattr(game, "vida", 1.0)

        if (
            0.0 < vida < 0.22
            and getattr(game, "has_match", False)
            and self._light_cooldown <= 0
            and not self.busy
        ):

            self._light_cooldown = 75.0

            self.say(random.choice(LOW_LIGHT), kind="hint", priority=2)

            return

        if self.busy or step is None:
            return

        hint = step.get("hint")

        if not hint or self._hints_given >= len(HINT_DELAYS):
            return

        if self._stuck >= HINT_DELAYS[self._hints_given]:

            self._hints_given += 1
            self._stuck = 0.0

            self.say(hint, kind="hint", priority=1)

    def reset_stuck(self):

        self._stuck = 0.0

    # ---------------------------------------------------------- update

    def update(self, dt):

        self.t += dt

        if self.phase is None:
            return

        self.phase_time += dt

        if self.phase == "in" and self.phase_time >= self.IN_TIME:

            self.phase = "show"
            self.phase_time = 0.0

        elif self.phase == "show" and self.phase_time >= self.duration:

            self.phase = "out"
            self.phase_time = 0.0

        elif self.phase == "out" and self.phase_time >= self.OUT_TIME:

            self.phase = None
            self.priority = 0

    def _slide(self):
        """0 = en su lugar, 1 = fuera de la pantalla."""

        if self.phase == "in":

            t = min(1.0, self.phase_time / self.IN_TIME)

            # llega pasadito y rebota un poco
            ease = 1 - (1 - t) ** 3

            return (1 - ease) - math.sin(t * math.pi) * 0.05

        if self.phase == "out":

            t = min(1.0, self.phase_time / self.OUT_TIME)

            return t ** 2

        return 0.0

    def draw(self, screen):

        if self.phase is None or self.bubble is None:
            return

        slide = self._slide()

        dx = int((self.character.get_width() + self.margin + 20) * slide)

        bob = int(math.sin(self.t * 3.2) * 3)

        if self.phase == "show" and self.hops > 0:

            # saltitos de festejo al empezar a hablar
            period = 0.28

            n = self.phase_time / period

            if n < self.hops:
                bob -= int(abs(math.sin(n * math.pi)) * 16)

        char_pos = self.rest_rect.move(dx, bob)

        screen.blit(self.character, char_pos)

        bubble_rect = self.bubble.get_rect(
            bottomright=(char_pos.left - 2, self.rest_rect.bottom - 16)
        )

        # el globito aparece creciendo un poquito
        if self.phase == "in":

            t = min(1.0, self.phase_time / self.IN_TIME)

            alpha = int(255 * t)

            img = self.bubble.copy()
            img.set_alpha(alpha)

            screen.blit(img, bubble_rect)

        elif self.phase == "out":

            t = min(1.0, self.phase_time / self.OUT_TIME)

            img = self.bubble.copy()
            img.set_alpha(int(255 * (1 - t)))

            screen.blit(img, bubble_rect)

        else:

            screen.blit(self.bubble, bubble_rect)