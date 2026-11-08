"""Ruleta: apuesta monedas o monedas de gelea a rojo, negro o verde.

Imagenes (todas opcionales; en assets/maps/ui/). Si falta alguna, ese
elemento se dibuja con codigo. Las "9 partes" se estiran sin deformar las
esquinas, asi que pueden tener un tamaño parecido al indicado:
  ruleta_panel.png          640x440   fondo del panel (9 partes, esquina 60)
  ruleta_titulo.png         ~300x64   la palabra "Ruleta" (reemplaza al texto)
  ruleta_aro.png            216x216   aro FIJO de la rueda (el centro puede
                                      quedar transparente: la rueda va encima)
  ruleta_rueda.png          176x176   rueda que GIRA, con el centro incluido.
                                      Dibujala con el verde arriba y los 20
                                      casilleros asi, en sentido del reloj:
                                      V R N R N R N R N R V N R N R N R N R N
                                      (V verde, R rojo, N negro: tiene que
                                      coincidir con WHEEL de este archivo)
  ruleta_puntero.png        18x18     flechita fija de arriba (apunta abajo)
  ruleta_bola.png           16x16     la bolita
  ruleta_pestana.png        153x32    pestaña de moneda (9 partes, esquina 8)
  ruleta_pestana_sel.png    153x32    la misma cuando esta elegida
  ruleta_rojo.png           99x48     boton Rojo  (9 partes, esquina 8)
  ruleta_negro.png          99x48     boton Negro
  ruleta_verde.png          99x48     boton Verde
  ruleta_color_sel.png      99x48     marco de seleccion (fondo transparente,
                                      se dibuja ENCIMA del color elegido)
  ruleta_girar.png          314x46    boton GIRAR (9 partes, esquina 8)
  ruleta_girar_hover.png    314x46    con el mouse encima
  ruleta_girar_off.png      314x46    desactivado
  panel_btn.png             72x32     botones +10, +50, Minimo, x2, etc.
  panel_btn_hover.png       72x32     (compartidos con el Yunque y la Maquina)
  panel_btn_off.png         72x32
  panel_separador.png       ~568x6    linea de arriba del pie del panel
Los textos y numeros (apuesta, "Rojo x2", 45%) los dibuja el codigo encima.
"""

import math
import random

import pygame

from core.audio_manager import audio
from world.yunque import (
    AnvilPanel, MARGIN,
    C_PANEL, C_EDGE, C_LIGHT,
)

# 20 casilleros: 9 rojos (45%), 9 negros (45%) y 2 verdes (10%), los verdes
# enfrentados. Para cambiar las probabilidades cambia esta rueda.
WHEEL = "V" + "RNRNRNRNR" + "V" + "NRNRNRNRN"
SLOTS = len(WHEEL)
STEP = 360.0 / SLOTS

# Premio de cada color (rojo y negro x2, verde x3).
MULT = {"R": 2, "N": 2, "V": 3}
NAMES = {"R": "Rojo", "N": "Negro", "V": "Verde"}

# colores apagados, en la linea gris oscuro del resto del juego
FILL = {"R": (150, 54, 46), "N": (30, 32, 38), "V": (62, 126, 90)}

# Monedas con las que se puede apostar. "attr" es el atributo del juego
# donde esta ese saldo.
CURRENCIES = {
    "coins": {
        "attr": "coins", "icon": "moneda", "unit": "monedas",
        "min": 10, "max": 5000, "chips": (10, 50, 100, 500),
    },
    "gelea": {
        "attr": "gel_coins", "icon": "moneda_gelea",
        "unit": "monedas de gelea",
        "min": 1, "max": 100, "chips": (1, 5, 10, 25),
    },
}
CUR_ORDER = ("coins", "gelea")

GOLD = (214, 170, 72)
GOLD_DARK = (122, 84, 24)
BALL_TURNS = 5
BALL_DROP_FROM = 0.68

SPIN_TIME = 4.2
EXTRA_TURNS = 4

PANEL_W = 640
PANEL_H = 440
PANEL_FILE = "ruleta_panel.png"


def chance(letter):

    return WHEEL.count(letter) / SLOTS


def pct(letter):

    return int(round(chance(letter) * 100))


class RouletteState:

    def __init__(self):

        self.cur = "coins"
        self.bets = {k: CURRENCIES[k]["min"] for k in CUR_ORDER}
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
    def bet(self):

        return self.bets[self.cur]

    @bet.setter
    def bet(self, value):

        self.bets[self.cur] = int(value)

    @property
    def cfg(self):

        return CURRENCIES[self.cur]

    def have(self, game):

        return int(getattr(game, self.cfg["attr"], 0))

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

        if self.bet < self.cfg["min"]:
            return False, f"La apuesta mínima es {self.cfg['min']}"

        if self.have(game) < self.bet:
            return False, f"No tienes tantas {self.cfg['unit']}"

        setattr(game, self.cfg["attr"], self.have(game) - self.bet)

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
        unit = self.cfg["unit"]

        if won > 0:

            if self.cur == "coins":
                game.add_coins(won)
            else:
                game.gel_coins = int(getattr(game, "gel_coins", 0)) + won
                audio.play("coin_big")

            if self.result == "V":
                audio.play("gem")

            game.show_message(
                f"¡Salió el {name}! Ganaste {won} {unit} "
                f"(apostaste {self.stake})"
            )

        else:

            audio.play("click")

            game.show_message(
                f"Salió el {name}. Perdiste {self.stake} {unit}"
            )

        saver = getattr(game, "save_progress", None)

        if callable(saver):
            saver()

    def save(self):

        data = {
            "bet": int(self.bets["coins"]),
            "bet_gelea": int(self.bets["gelea"]),
            "cur": self.cur,
            "pick": self.pick,
        }

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

        cur = data.get("cur")
        self.cur = cur if cur in CURRENCIES else "coins"

        for key, field in (("coins", "bet"), ("gelea", "bet_gelea")):

            cfg = CURRENCIES[key]

            try:
                value = int(data.get(field, cfg["min"]))
            except (TypeError, ValueError):
                value = cfg["min"]

            self.bets[key] = max(cfg["min"], min(cfg["max"], value))

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

    def layout(self, game, st=None):

        sw, sh = game.screen.get_size()

        panel = pygame.Rect(0, 0, PANEL_W, PANEL_H)
        panel.center = (sw // 2, sh // 2)
        panel.clamp_ip(game.screen.get_rect())

        wheel_c = (panel.x + MARGIN + 112, panel.y + 226)

        rx = panel.x + 290
        rw = panel.right - MARGIN - rx

        tw = (rw - 8) // 2
        tabs = {
            key: pygame.Rect(rx + i * (tw + 8), panel.y + 106, tw, 32)
            for i, key in enumerate(CUR_ORDER)
        }

        bw = (rw - 16) // 3
        colors = {
            letter: pygame.Rect(rx + i * (bw + 8), panel.y + 146, bw, 48)
            for i, letter in enumerate("RNV")
        }

        cw = (rw - 3 * 8) // 4
        chips = [
            (chip, pygame.Rect(rx + i * (cw + 8), panel.y + 244, cw, 32))
            for i, chip in enumerate(
                (st.cfg if st is not None else CURRENCIES["coins"])["chips"]
            )
        ]

        sw3 = (rw - 16) // 3
        quick = {
            key: pygame.Rect(rx + i * (sw3 + 8), panel.y + 282, sw3, 32)
            for i, key in enumerate(("min", "double", "max"))
        }

        return {
            "panel": panel,
            "wheel": wheel_c,
            "radius": 88,
            "right": pygame.Rect(rx, panel.y + 112, rw, 0),
            "tabs": tabs,
            "colors": colors,
            "chips": chips,
            "quick": quick,
            "spin": pygame.Rect(rx, panel.y + 324, rw, 46),
            "footer": panel.bottom - 30,
        }

    _chips = CURRENCIES["coins"]["chips"]

    def _limit(self, game, st):

        cfg = st.cfg

        return max(cfg["min"], min(cfg["max"], st.have(game)))

    def click(self, game, event, obj):

        st = obj.r

        lay = self.layout(game, st)

        if not lay["panel"].collidepoint(event.pos):
            return False

        if event.button != 1:
            return True

        if st.busy:
            return True

        for key, rect in lay["tabs"].items():

            if rect.collidepoint(event.pos):
                if st.cur != key:
                    st.cur = key
                    audio.play("click")
                return True

        for letter, rect in lay["colors"].items():

            if rect.collidepoint(event.pos):
                st.pick = letter
                audio.play("click")
                return True

        for chip, rect in lay["chips"]:

            if rect.collidepoint(event.pos):
                st.bet = min(self._limit(game, st), st.bet + chip)
                audio.play("click")
                return True

        for key, rect in lay["quick"].items():

            if rect.collidepoint(event.pos):

                if key == "min":
                    st.bet = st.cfg["min"]
                elif key == "double":
                    st.bet = min(self._limit(game, st), st.bet * 2)
                else:
                    st.bet = self._limit(game, st)

                audio.play("click")
                return True

        if lay["spin"].collidepoint(event.pos):

            ok, msg = st.spin(game)

            if not ok:
                game.show_message(msg)
            else:
                audio.play("pickup")

        return True

    def _draw_wheel(self, screen, cx, cy, radius, angle):

        track = radius + 15
        outer = track + 5

        # ---- aro fijo (tu imagen o dibujo) ----
        ring = self._skin("ruleta_aro.png", (outer * 2, outer * 2))

        if ring is not None:

            screen.blit(ring, ring.get_rect(center=(cx, cy)))

        else:

            pygame.draw.circle(screen, (22, 24, 28), (cx, cy), track + 5)
            pygame.draw.circle(screen, (78, 84, 94), (cx, cy), track)
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

        # ---- rueda que gira (tu imagen o dibujo) ----
        disc = self._skin("ruleta_rueda.png", (radius * 2, radius * 2))

        if disc is not None:

            # la imagen se dibuja con el casillero 0 (verde) arriba
            spun = pygame.transform.rotozoom(disc, -(angle + 90.0), 1.0)
            screen.blit(spun, spun.get_rect(center=(cx, cy)))

        else:

            self._draw_disc_code(screen, cx, cy, radius, angle)

        # ---- puntero ----
        tip_img = self._raw("ruleta_puntero.png")

        if tip_img is not None:

            screen.blit(
                tip_img, tip_img.get_rect(midbottom=(cx, cy - track - 2))
            )

        else:

            tip = [
                (cx - 9, cy - track - 20),
                (cx + 9, cy - track - 20),
                (cx, cy - track - 3),
            ]

            pygame.draw.polygon(screen, GOLD, tip)
            pygame.draw.polygon(screen, GOLD_DARK, tip, 2)

    def _draw_disc_code(self, screen, cx, cy, radius, angle):

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

            if letter == "V":

                # el verde lleva un rombo dorado para reconocerlo rapido
                m = math.radians(mid)
                gx = cx + math.cos(m) * radius * 0.80
                gy = cy + math.sin(m) * radius * 0.80

                gem = [
                    (gx, gy - 5), (gx + 4, gy), (gx, gy + 5), (gx - 4, gy)
                ]

                pygame.draw.polygon(screen, GOLD, gem)
                pygame.draw.polygon(screen, GOLD_DARK, gem, 1)

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

        ball = self._skin("ruleta_bola.png", (16, 16))

        if ball is not None:

            screen.blit(ball, ball.get_rect(center=(bx, by)))
            return

        pygame.draw.circle(screen, (16, 16, 18), (bx + 2, by + 3), 7)
        pygame.draw.circle(screen, (232, 188, 62), (bx, by), 7)
        pygame.draw.circle(screen, GOLD_DARK, (bx, by), 7, 1)
        pygame.draw.circle(screen, (255, 244, 180), (bx - 2, by - 2), 2)

    def draw(self, game, screen, obj):

        st = obj.r
        lay = self.layout(game, st)
        panel = lay["panel"]
        cfg = st.cfg
        have = st.have(game)

        mouse = pygame.mouse.get_pos()

        bg = self._panel_bg(panel.size, PANEL_FILE)

        if bg is not None:
            screen.blit(bg, panel)
        else:
            pygame.draw.rect(screen, C_PANEL, panel, border_radius=16)
            pygame.draw.rect(screen, C_EDGE, panel, 4, border_radius=16)

        if not self._title(screen, panel, "ruleta_titulo.png"):

            title = self._font(54).render("Ruleta", True, C_LIGHT)
            shade = self._font(54).render("Ruleta", True, C_EDGE)

            t_rect = title.get_rect(midtop=(panel.centerx, panel.y + 22))
            screen.blit(shade, t_rect.move(0, 3))
            screen.blit(title, t_rect)

        cx, cy = lay["wheel"]
        radius = lay["radius"]

        self._draw_wheel(screen, cx, cy, radius, st.angle)
        self._draw_ball(screen, cx, cy, radius, st)

        idx = int(math.floor((-90.0 - st.angle) / STEP + 0.5)) % SLOTS

        if st.spinning and idx != self._last_idx:
            audio.play("click")

        self._last_idx = idx

        status = None

        if st.spinning:
            status = "Girando…"
        elif st.result in FILL:
            status = f"Salió el {NAMES[st.result].lower()}"

        if status is not None:

            label = self._font(28).render(status, True, C_LIGHT)
            l_rect = label.get_rect(center=(cx + 10, cy + radius + 34))

            if st.result in FILL and not st.spinning:
                dot = pygame.Rect(0, 0, 18, 18)
                dot.midright = (l_rect.left - 8, l_rect.centery)
                pygame.draw.rect(screen, FILL[st.result], dot, border_radius=4)
                pygame.draw.rect(screen, C_LIGHT, dot, 2, border_radius=4)

            screen.blit(label, l_rect)

        rx = lay["right"].x
        rw = lay["right"].w

        disabled = st.busy

        # pestañas de moneda: icono + cuanto tienes de cada una
        for key, rect in lay["tabs"].items():

            on = st.cur == key
            hot = rect.collidepoint(mouse) and not disabled

            if on:
                fill = (150, 108, 36)
            elif hot:
                fill = (84, 91, 100)
            else:
                fill = (60, 66, 74)

            if disabled and not on:
                fill = (96, 104, 112)

            tab_img = self._nine(
                rect.size,
                "ruleta_pestana_sel.png" if on else "ruleta_pestana.png", 8,
            )

            if tab_img is not None:

                if disabled and not on:
                    tab_img = tab_img.copy()
                    tab_img.set_alpha(150)

                screen.blit(tab_img, rect)

            else:

                pygame.draw.rect(screen, fill, rect, border_radius=6)
                pygame.draw.rect(
                    screen, GOLD if on else C_EDGE, rect, 3 if on else 2,
                    border_radius=6,
                )

            icon = self._item_icon(CURRENCIES[key]["icon"], 24)
            amount = int(getattr(game, CURRENCIES[key]["attr"], 0))
            txt = self._fit(f"{amount}", 26, C_LIGHT, rect.w - 24 - 20)

            gap = 6
            total = icon.get_width() + gap + txt.get_width()
            x0 = rect.centerx - total // 2

            screen.blit(icon, icon.get_rect(midleft=(x0, rect.centery)))
            screen.blit(
                txt,
                txt.get_rect(
                    midleft=(x0 + icon.get_width() + gap, rect.centery)
                ),
            )

        for letter, rect in lay["colors"].items():

            selected = st.pick == letter

            fill = FILL[letter]

            if disabled and not selected:
                fill = tuple(int(c * 0.55 + 60 * 0.45) for c in fill)

            color_img = self._nine(
                rect.size, f"ruleta_{NAMES[letter].lower()}.png", 8
            )

            if color_img is not None:

                if disabled and not selected:
                    color_img = color_img.copy()
                    color_img.set_alpha(150)

                screen.blit(color_img, rect)

                sel_img = self._nine(rect.size, "ruleta_color_sel.png", 8)

                if selected:
                    if sel_img is not None:
                        screen.blit(sel_img, rect)
                    else:
                        pygame.draw.rect(screen, GOLD, rect, 4, border_radius=8)
                elif (
                    rect.collidepoint(mouse) and not disabled
                    and sel_img is not None
                ):
                    hover = sel_img.copy()
                    hover.set_alpha(110)
                    screen.blit(hover, rect)

            else:

                pygame.draw.rect(screen, fill, rect, border_radius=8)

                if selected:
                    pygame.draw.rect(screen, GOLD, rect, 4, border_radius=8)
                elif rect.collidepoint(mouse) and not disabled:
                    pygame.draw.rect(
                        screen, (214, 218, 222), rect, 2, border_radius=8
                    )
                else:
                    pygame.draw.rect(screen, C_EDGE, rect, 2, border_radius=8)

            name = self._font(26).render(
                f"{NAMES[letter]} x{MULT[letter]}", True, (255, 255, 255)
            )
            pc = self._font(20).render(
                f"{pct(letter)}%", True, (235, 238, 240)
            )

            screen.blit(name, name.get_rect(center=(rect.centerx, rect.y + 17)))
            screen.blit(pc, pc.get_rect(center=(rect.centerx, rect.y + 36)))

        bet_label = self._font(26).render("Apuesta", True, C_LIGHT)
        screen.blit(bet_label, bet_label.get_rect(midleft=(rx, panel.y + 218)))

        bet_coin = self._item_icon(cfg["icon"], 30)
        bet_txt = self._font(44).render(f"{st.bet}", True, C_LIGHT)

        b_rect = bet_txt.get_rect(midright=(rx + rw, panel.y + 218))
        screen.blit(bet_txt, b_rect)
        screen.blit(
            bet_coin, bet_coin.get_rect(midright=(b_rect.left - 8, b_rect.centery))
        )

        lack = have < st.bet

        for chip, rect in lay["chips"]:
            self._button(screen, rect, f"+{chip}", not disabled, mouse)

        quick_text = {"min": "Mínimo", "double": "x2", "max": "Máximo"}

        for key, rect in lay["quick"].items():
            self._button(screen, rect, quick_text[key], not disabled, mouse)

        can_spin = not disabled and st.pick in MULT and not lack

        spin_rect = lay["spin"]

        spin_hot = can_spin and spin_rect.collidepoint(mouse)
        spin_img = self._btn_img(spin_rect, can_spin, spin_hot, "ruleta_girar")

        if spin_img is not None:

            screen.blit(spin_img, spin_rect)

        else:

            if spin_hot:
                fill = (176, 130, 46)
            elif can_spin:
                fill = (150, 108, 36)
            else:
                fill = (128, 138, 146)

            pygame.draw.rect(screen, fill, spin_rect, border_radius=8)
            pygame.draw.rect(screen, C_EDGE, spin_rect, 3, border_radius=8)

        if st.busy:
            spin_text = "Girando…"
        elif st.pick not in MULT:
            spin_text = "Elige un color"
        elif lack:
            spin_text = (
                "Te faltan monedas" if st.cur == "coins"
                else "Te faltan geleas"
            )
        else:
            gain = st.bet * MULT[st.pick]
            spin_text = f"GIRAR  (ganas {gain})"

        ink = (255, 255, 255) if can_spin else (176, 184, 190)
        txt = self._fit(spin_text, 32, ink, spin_rect.w - 16)
        screen.blit(txt, txt.get_rect(center=spin_rect.center))

        fy = lay["footer"]

        self._separator(
            screen, panel.x + MARGIN, panel.right - MARGIN, fy - 16
        )

        hint_color = (255, 150, 140) if lack and not st.busy else (214, 218, 222)

        if lack and not st.busy:
            hint = f"Necesitas {st.bet - have} {cfg['unit']} más para esta apuesta"
        else:
            hint = (
                f"ESC para cerrar  ·  apuesta de {cfg['min']} a {cfg['max']} "
                f"{cfg['unit']}"
            )

        hint_surf = self._fit(hint, 22, hint_color, panel.w - 2 * MARGIN)
        screen.blit(hint_surf, hint_surf.get_rect(center=(panel.centerx, fy)))