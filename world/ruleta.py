import math
import random

import pygame

from core.audio_manager import audio
from world.yunque import (
    AnvilPanel, MARGIN,
    C_PANEL, C_EDGE, C_LIGHT,
)

WHEEL = "RNRNV" * 4
SLOTS = len(WHEEL)
STEP = 360.0 / SLOTS

MULT = {"R": 2, "N": 2, "V": 3}
NAMES = {"R": "Rojo", "N": "Negro", "V": "Verde"}
FILL = {"R": (200, 54, 54), "N": (32, 34, 40), "V": (50, 160, 84)}

_SEQ = (11, 4, 15, 8, 13, 2, 9, 16, 5, 12, 1, 10, 7, 14, 3, 6)


def _numbers():

    seq = iter(_SEQ)

    return tuple(0 if c == "V" else next(seq) for c in WHEEL)


NUMBERS = _numbers()

GOLD = (214, 170, 72)
GOLD_DARK = (122, 84, 24)
BALL_TURNS = 5
BALL_DROP_FROM = 0.68

MIN_BET = 10
MAX_BET = 5000
CHIPS = (10, 50, 100, 500)
SPIN_TIME = 4.2
EXTRA_TURNS = 4

PANEL_W = 640
PANEL_H = 440
PANEL_FILE = "ruleta_panel.png"


def chance(letter):

    return WHEEL.count(letter) / SLOTS


class RouletteState:

    def __init__(self):

        self.bet = MIN_BET
        self.pick = None

        self.spinning = False
        self.finished = False

        self.t = 0.0
        self.a0 = -90.0
        self.a1 = -90.0
        self.angle = -90.0

        self.slot = 0
        self.result = None
        self.stake = 0
        self.owed = 0
        self.last_win = 0

    @property
    def busy(self):

        return self.spinning or self.finished

    def tick(self, dt):

        if not self.spinning:
            return

        self.t += dt

        k = min(1.0, self.t / SPIN_TIME)
        ease = 1.0 - (1.0 - k) ** 3

        self.angle = self.a0 + (self.a1 - self.a0) * ease

        if k >= 1.0:
            self.spinning = False
            self.finished = True

    def spin(self, game):

        if self.busy:
            return False, "La ruleta todavía está girando"

        if self.pick not in MULT:
            return False, "Elige un color"

        if self.bet < MIN_BET:
            return False, f"La apuesta mínima es {MIN_BET}"

        if int(game.coins) < self.bet:
            return False, "No tienes tantas monedas"

        game.coins -= self.bet

        self.stake = self.bet
        self.slot = random.randrange(SLOTS)
        self.result = WHEEL[self.slot]
        self.owed = (
            self.stake * MULT[self.pick] if self.result == self.pick else 0
        )

        start = self.angle % 360.0
        land = -90.0 - self.slot * STEP + random.uniform(-0.3, 0.3) * STEP
        delta = (land - start) % 360.0 + 360.0 * EXTRA_TURNS

        self.a0 = start
        self.a1 = start + delta
        self.t = 0.0
        self.spinning = True

        return True, "¡Gira la ruleta!"

    def settle(self, game):

        if not self.finished:
            return

        self.finished = False

        won = self.owed
        self.owed = 0
        self.last_win = won

        name = NAMES.get(self.result, "").lower()
        num = NUMBERS[self.slot]

        if won > 0:

            game.add_coins(won)

            if self.result == "V":
                audio.play("gem")

            game.show_message(
                f"¡Salió el {num} {name}! Ganaste {won} monedas "
                f"(apostaste {self.stake})"
            )

        else:

            audio.play("click")

            game.show_message(
                f"Salió el {num} {name}. Perdiste {self.stake} monedas"
            )

        saver = getattr(game, "save_progress", None)

        if callable(saver):
            saver()

    def save(self):

        data = {"bet": int(self.bet), "pick": self.pick}

        if self.busy:
            data.update({
                "pending": True,
                "owed": int(self.owed),
                "stake": int(self.stake),
                "slot": int(self.slot),
                "result": self.result,
            })

        return data

    def load(self, data):

        if not isinstance(data, dict):
            return

        try:
            self.bet = max(MIN_BET, min(MAX_BET, int(data.get("bet", MIN_BET))))
        except (TypeError, ValueError):
            self.bet = MIN_BET

        pick = data.get("pick")
        self.pick = pick if pick in MULT else None

        if not data.get("pending"):
            return

        try:
            self.slot = max(0, min(SLOTS - 1, int(data.get("slot", 0))))
            self.owed = max(0, int(data.get("owed", 0)))
            self.stake = max(0, int(data.get("stake", 0)))
        except (TypeError, ValueError):
            return

        result = data.get("result")
        self.result = result if result in MULT else WHEEL[self.slot]
        self.angle = -90.0 - self.slot * STEP
        self.finished = True


class RoulettePanel(AnvilPanel):

    def __init__(self):

        super().__init__()

        self._last_idx = None
        self._nums = {}

    def layout(self, game):

        sw, sh = game.screen.get_size()

        panel = pygame.Rect(0, 0, PANEL_W, PANEL_H)
        panel.center = (sw // 2, sh // 2)
        panel.clamp_ip(game.screen.get_rect())

        wheel_c = (panel.x + MARGIN + 112, panel.y + 226)

        rx = panel.x + 290
        rw = panel.right - MARGIN - rx

        bw = (rw - 16) // 3
        colors = {
            letter: pygame.Rect(rx + i * (bw + 8), panel.y + 150, bw, 50)
            for i, letter in enumerate("RNV")
        }

        cw = (rw - 3 * 8) // 4
        chips = [
            (chip, pygame.Rect(rx + i * (cw + 8), panel.y + 262, cw, 34))
            for i, chip in enumerate(CHIPS)
        ]

        sw3 = (rw - 16) // 3
        quick = {
            key: pygame.Rect(rx + i * (sw3 + 8), panel.y + 304, sw3, 34)
            for i, key in enumerate(("min", "double", "max"))
        }

        return {
            "panel": panel,
            "wheel": wheel_c,
            "radius": 88,
            "right": pygame.Rect(rx, panel.y + 112, rw, 0),
            "colors": colors,
            "chips": chips,
            "quick": quick,
            "spin": pygame.Rect(rx, panel.y + 350, rw, 46),
            "footer": panel.bottom - 30,
        }

    def _limit(self, game):

        return max(MIN_BET, min(MAX_BET, int(game.coins)))

    def click(self, game, event, obj):

        lay = self.layout(game)

        if not lay["panel"].collidepoint(event.pos):
            return False

        if event.button != 1:
            return True

        st = obj.r

        if st.busy:
            return True

        for letter, rect in lay["colors"].items():

            if rect.collidepoint(event.pos):
                st.pick = letter
                audio.play("click")
                return True

        for chip, rect in lay["chips"]:

            if rect.collidepoint(event.pos):
                st.bet = min(self._limit(game), st.bet + chip)
                audio.play("click")
                return True

        for key, rect in lay["quick"].items():

            if rect.collidepoint(event.pos):

                if key == "min":
                    st.bet = MIN_BET
                elif key == "double":
                    st.bet = min(self._limit(game), st.bet * 2)
                else:
                    st.bet = self._limit(game)

                audio.play("click")
                return True

        if lay["spin"].collidepoint(event.pos):

            ok, msg = st.spin(game)

            if not ok:
                game.show_message(msg)
            else:
                audio.play("pickup")

        return True

    def _num_surface(self, number):

        img = self._nums.get(number)

        if img is None:
            img = self._font(21).render(str(number), True, (246, 246, 246))
            self._nums[number] = img

        return img

    def _draw_wheel(self, screen, cx, cy, radius, angle):

        track = radius + 15

        pygame.draw.circle(screen, (22, 24, 28), (cx, cy), track + 5)
        pygame.draw.circle(screen, (46, 49, 56), (cx, cy), track)
        pygame.draw.circle(screen, GOLD, (cx, cy), track + 5, 3)

        for deg in (45, 135, 225, 315):

            a = math.radians(deg)
            dx = cx + math.cos(a) * (radius + 9)
            dy = cy + math.sin(a) * (radius + 9)

            diamond = [
                (dx, dy - 5), (dx + 4, dy), (dx, dy + 5), (dx - 4, dy)
            ]

            pygame.draw.polygon(screen, GOLD, diamond)
            pygame.draw.polygon(screen, GOLD_DARK, diamond, 1)

        inner = radius * 0.60

        for i, letter in enumerate(WHEEL):

            mid = angle + i * STEP
            a0 = math.radians(mid - STEP / 2)
            a1 = math.radians(mid + STEP / 2)

            pts = []

            for j in range(5):
                a = a0 + (a1 - a0) * j / 4
                pts.append(
                    (cx + math.cos(a) * radius, cy + math.sin(a) * radius)
                )

            for j in range(4, -1, -1):
                a = a0 + (a1 - a0) * j / 4
                pts.append(
                    (cx + math.cos(a) * inner, cy + math.sin(a) * inner)
                )

            pygame.draw.polygon(screen, FILL[letter], pts)
            pygame.draw.polygon(screen, GOLD, pts, 1)

            m = math.radians(mid)
            num = pygame.transform.rotate(
                self._num_surface(NUMBERS[i]), -(mid + 90.0)
            )

            screen.blit(
                num,
                num.get_rect(center=(
                    cx + math.cos(m) * radius * 0.80,
                    cy + math.sin(m) * radius * 0.80,
                ))
            )

        pygame.draw.circle(screen, (38, 40, 46), (cx, cy), int(inner))
        pygame.draw.circle(screen, GOLD, (cx, cy), int(inner), 2)

        core = int(inner * 0.55)

        pygame.draw.circle(screen, (60, 64, 72), (cx, cy), core)
        pygame.draw.circle(screen, GOLD_DARK, (cx, cy), core, 2)

        for k in range(4):

            a = math.radians(angle + k * 90.0)

            pygame.draw.line(
                screen, GOLD,
                (cx + math.cos(a) * 6, cy + math.sin(a) * 6),
                (cx + math.cos(a) * core, cy + math.sin(a) * core), 3,
            )

        pygame.draw.circle(screen, GOLD, (cx, cy), max(5, int(radius * 0.11)))
        pygame.draw.circle(
            screen, GOLD_DARK, (cx, cy), max(5, int(radius * 0.11)), 2
        )

        tip = [
            (cx - 9, cy - track - 20),
            (cx + 9, cy - track - 20),
            (cx, cy - track - 3),
        ]

        pygame.draw.polygon(screen, GOLD, tip)
        pygame.draw.polygon(screen, GOLD_DARK, tip, 2)

    def _ball_state(self, radius, st):

        if st.spinning:

            k = min(1.0, st.t / SPIN_TIME)

            free = -90.0 + 360.0 * BALL_TURNS * (1.0 - k) ** 2

            attached = st.angle + st.slot * STEP

            x = max(0.0, min(1.0, (k - BALL_DROP_FROM) / (1.0 - BALL_DROP_FROM)))
            w = x * x * (3.0 - 2.0 * x)

            diff = ((attached - free + 180.0) % 360.0) - 180.0

            angle = free + diff * w
            dist = (radius + 8) * (1.0 - w) + radius * 0.80 * w

            if 0.0 < w < 1.0:
                dist += abs(math.sin(w * math.pi * 3.5)) * (1.0 - w) * 8.0

            return angle, dist

        if st.result in FILL:
            return st.angle + st.slot * STEP, radius * 0.80

        return None

    def _draw_ball(self, screen, cx, cy, radius, st):

        state = self._ball_state(radius, st)

        if state is None:
            return

        angle, dist = state

        a = math.radians(angle)

        bx = int(cx + math.cos(a) * dist)
        by = int(cy + math.sin(a) * dist)

        pygame.draw.circle(screen, (16, 16, 18), (bx + 2, by + 3), 7)
        pygame.draw.circle(screen, (232, 188, 62), (bx, by), 7)
        pygame.draw.circle(screen, GOLD_DARK, (bx, by), 7, 1)
        pygame.draw.circle(screen, (255, 244, 180), (bx - 2, by - 2), 2)

    def draw(self, game, screen, obj):

        lay = self.layout(game)
        panel = lay["panel"]
        st = obj.r
        coins = int(game.coins)

        mouse = pygame.mouse.get_pos()

        bg = self._panel_bg(panel.size, PANEL_FILE)

        if bg is not None:
            screen.blit(bg, panel)
        else:
            pygame.draw.rect(screen, C_PANEL, panel, border_radius=16)
            pygame.draw.rect(screen, C_EDGE, panel, 4, border_radius=16)

        title = self._font(54).render("Ruleta", True, C_LIGHT)
        shade = self._font(54).render("Ruleta", True, C_EDGE)

        t_rect = title.get_rect(midtop=(panel.centerx, panel.y + 22))
        screen.blit(shade, t_rect.move(0, 3))
        screen.blit(title, t_rect)

        sub = self._font(23).render(
            f"Rojo y Negro x2 ({int(chance('R') * 100)}%)  ·  "
            f"Verde x3 ({int(chance('V') * 100)}%)",
            True, C_LIGHT,
        )
        screen.blit(sub, sub.get_rect(midtop=(panel.centerx, panel.y + 80)))

        cx, cy = lay["wheel"]
        radius = lay["radius"]

        self._draw_wheel(screen, cx, cy, radius, st.angle)
        self._draw_ball(screen, cx, cy, radius, st)

        idx = int(math.floor((-90.0 - st.angle) / STEP + 0.5)) % SLOTS

        if st.spinning and idx != self._last_idx:
            audio.play("click")

        self._last_idx = idx

        if st.spinning:
            status, ink = "Girando…", C_LIGHT
        elif st.result in FILL:
            status = f"Salió el {NUMBERS[st.slot]} {NAMES[st.result].lower()}"
            ink = C_LIGHT
        else:
            status, ink = "Haz tu apuesta", C_LIGHT

        label = self._font(28).render(status, True, ink)
        l_rect = label.get_rect(center=(cx + 10, cy + radius + 34))

        if st.result in FILL and not st.spinning:
            dot = pygame.Rect(0, 0, 18, 18)
            dot.midright = (l_rect.left - 8, l_rect.centery)
            pygame.draw.rect(screen, FILL[st.result], dot, border_radius=4)
            pygame.draw.rect(screen, C_LIGHT, dot, 2, border_radius=4)

        screen.blit(label, l_rect)

        rx = lay["right"].x
        rw = lay["right"].w

        coin = self._item_icon("moneda", 28)
        have = self._font(30).render(f"{coins}", True, C_LIGHT)

        coin_rect = coin.get_rect(midleft=(rx, panel.y + 124))
        screen.blit(coin, coin_rect)
        screen.blit(have, have.get_rect(midleft=(coin_rect.right + 8, coin_rect.centery)))

        small = self._font(22).render("tus monedas", True, (214, 218, 222))
        screen.blit(small, small.get_rect(midright=(rx + rw, coin_rect.centery)))

        disabled = st.busy

        for letter, rect in lay["colors"].items():

            selected = st.pick == letter

            fill = FILL[letter]

            if disabled and not selected:
                fill = tuple(int(c * 0.55 + 60 * 0.45) for c in fill)

            pygame.draw.rect(screen, fill, rect, border_radius=8)

            if selected:
                pygame.draw.rect(screen, C_LIGHT, rect, 4, border_radius=8)
            elif rect.collidepoint(mouse) and not disabled:
                pygame.draw.rect(screen, (214, 218, 222), rect, 2, border_radius=8)
            else:
                pygame.draw.rect(screen, C_EDGE, rect, 2, border_radius=8)

            name = self._font(26).render(
                f"{NAMES[letter]} x{MULT[letter]}", True, (255, 255, 255)
            )
            pct = self._font(20).render(
                f"{int(chance(letter) * 100)}%", True, (235, 238, 240)
            )

            screen.blit(name, name.get_rect(center=(rect.centerx, rect.y + 18)))
            screen.blit(pct, pct.get_rect(center=(rect.centerx, rect.y + 37)))

        bet_label = self._font(26).render("Apuesta", True, C_LIGHT)
        screen.blit(bet_label, bet_label.get_rect(midleft=(rx, panel.y + 226)))

        bet_coin = self._item_icon("moneda", 30)
        bet_txt = self._font(44).render(f"{st.bet}", True, C_LIGHT)

        b_rect = bet_txt.get_rect(midright=(rx + rw, panel.y + 226))
        screen.blit(bet_txt, b_rect)
        screen.blit(
            bet_coin, bet_coin.get_rect(midright=(b_rect.left - 8, b_rect.centery))
        )

        lack = coins < st.bet

        for chip, rect in lay["chips"]:
            self._button(screen, rect, f"+{chip}", not disabled, mouse)

        quick_text = {"min": "Mínimo", "double": "x2", "max": "Máximo"}

        for key, rect in lay["quick"].items():
            self._button(screen, rect, quick_text[key], not disabled, mouse)

        can_spin = not disabled and st.pick in MULT and not lack

        spin_rect = lay["spin"]

        if can_spin and spin_rect.collidepoint(mouse):
            fill = (74, 150, 92)
        elif can_spin:
            fill = (52, 120, 70)
        else:
            fill = (128, 138, 146)

        pygame.draw.rect(screen, fill, spin_rect, border_radius=8)
        pygame.draw.rect(screen, C_EDGE, spin_rect, 3, border_radius=8)

        if st.busy:
            spin_text = "Girando…"
        elif st.pick not in MULT:
            spin_text = "Elige un color"
        elif lack:
            spin_text = "Te faltan monedas"
        else:
            gain = st.bet * MULT[st.pick]
            spin_text = f"GIRAR  (ganas {gain})"

        ink = (255, 255, 255) if can_spin else (176, 184, 190)
        txt = self._fit(spin_text, 32, ink, spin_rect.w - 16)
        screen.blit(txt, txt.get_rect(center=spin_rect.center))

        fy = lay["footer"]

        pygame.draw.line(
            screen, C_EDGE,
            (panel.x + MARGIN, fy - 16), (panel.right - MARGIN, fy - 16), 2,
        )

        hint_color = (255, 150, 140) if lack and not st.busy else (214, 218, 222)

        if lack and not st.busy:
            hint = f"Necesitas {st.bet - coins} monedas más para esta apuesta"
        else:
            hint = (
                f"ESC para cerrar  ·  apuesta de {MIN_BET} a {MAX_BET} "
                "monedas"
            )

        hint_surf = self._font(22).render(hint, True, hint_color)
        screen.blit(hint_surf, hint_surf.get_rect(center=(panel.centerx, fy)))