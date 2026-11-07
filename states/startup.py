import math
import random
from pathlib import Path

import pygame


# Duracion "de diseno" de la secuencia, en segundos. Coincide con el largo
# del sonido de inicio (intro.ogg ~5.5 s). Si la Startup recibe otra
# duracion, toda la secuencia se estira o se achica en proporcion.
DESIGN_TIME = 5.4


def _clamp(v, lo=0.0, hi=1.0):

    return max(lo, min(hi, v))


def _span(t, a, b):

    """0 antes de a, 1 despues de b, y progresa lineal entre medio."""

    if b <= a:
        return 1.0 if t >= b else 0.0

    return _clamp((t - a) / (b - a))


def _smooth(k):

    k = _clamp(k)

    return k * k * (3.0 - 2.0 * k)


def _ease_out(k):

    k = _clamp(k)

    return 1.0 - (1.0 - k) ** 3


def _radial_alpha(size, color, power=2.0, max_alpha=255):

    """Bola de luz suave (centro opaco, borde transparente)."""

    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    c = (size - 1) / 2.0

    steps = int(c)

    for r in range(steps, 0, -1):

        k = r / float(steps)

        a = int(max_alpha * (1.0 - k) ** power)

        pygame.draw.circle(
            surf, (color[0], color[1], color[2], a), (round(c), round(c)), r
        )

    return surf


class Startup:

    """Intro cinematica: una chispa se enciende, se abre en un barrido de
    luz que revela el titulo, destello con temblor, brasas flotando, brillo
    que recorre las letras y la frase final, con barras de cine."""

    BAR_RATIO = 0.085
    EMBER_MAX = 80
    TAGLINE = "MANTENÉ LA LUZ ENCENDIDA"

    FADE_OUT = 0.55     # (en segundos de diseno)
    FLASH_AT = 1.45

    def __init__(self, screen, duration=DESIGN_TIME):

        self.screen = screen
        self.width, self.height = screen.get_size()

        self.duration = max(0.5, float(duration))
        self.timer = 0.0

        self.rng = random.Random()

        self.embers = []
        self._ember_acc = 0.0

        self.canvas = pygame.Surface((self.width, self.height))

        self._load_title()
        self._build_fx()

    # ------------------------------------------------------------------
    # armado de recursos
    # ------------------------------------------------------------------

    def _load_title(self):

        path = (
            Path(__file__).resolve().parent.parent
            / "assets" / "maps" / "ui" / "title.png"
        )

        raw = pygame.image.load(str(path)).convert()

        rw, rh = raw.get_size()

        # la imagen es 1920x1080 con el texto en el medio: se recorta
        crop = pygame.Rect(
            int(rw * 0.21), int(rh * 0.28), int(rw * 0.56), int(rh * 0.40)
        )

        title = raw.subsurface(crop).copy()

        self.tw = round(self.width * 0.58)
        self.th = round(crop.height * self.tw / crop.width)

        title = pygame.transform.smoothscale(title, (self.tw, self.th))

        # blanco calido (parece luz de fuego)
        title.fill((255, 238, 205), special_flags=pygame.BLEND_RGB_MULT)

        self.title = title

        self.layer = pygame.Surface((self.tw, self.th))

    def _build_fx(self):

        w, h = self.width, self.height

        # resplandor naranja detras del titulo
        self.bloom = pygame.transform.smoothscale(
            _radial_alpha(96, (255, 140, 50), 2.0, 210),
            (round(self.tw * 1.45), round(self.th * 2.4)),
        )

        # chispa inicial
        self.spark = _radial_alpha(64, (255, 225, 170), 1.4, 255)

        # puntas luminosas del borde de la revelacion
        self.edge = pygame.transform.smoothscale(
            _radial_alpha(64, (255, 235, 190), 1.2, 255),
            (max(4, round(h * 0.05)), round(self.th * 1.25)),
        )

        # barrido de luz horizontal (anamorfico)
        self.streak = self._make_streak(round(w * 1.25), 28)

        # banda de brillo que recorre las letras
        band_w = max(8, round(self.th * 0.55))

        band = pygame.Surface((band_w, round(self.th * 2.0)))

        for x in range(band_w):

            k = abs(x - (band_w - 1) / 2.0) / ((band_w - 1) / 2.0)

            v = int(255 * (1.0 - k) ** 2)

            pygame.draw.line(
                band, (v, v, round(v * 0.9)), (x, 0), (x, band.get_height())
            )

        self.band = pygame.transform.rotate(band, 16)

        # vineta (oscurece los bordes)
        vw, vh = 64, 36

        vig = pygame.Surface((vw, vh), pygame.SRCALPHA)

        for y in range(vh):
            for x in range(vw):

                dx = (x - (vw - 1) / 2.0) / (vw / 2.0)
                dy = (y - (vh - 1) / 2.0) / (vh / 2.0)

                d = math.hypot(dx, dy)

                a = int(235 * _clamp((d - 0.55) / 0.85))

                vig.set_at((x, y), (0, 0, 0, a))

        self.vignette = pygame.transform.smoothscale(vig, (w, h))

        # pantallas de color para destello y fundido
        self.flash_surf = pygame.Surface((w, h))
        self.flash_surf.fill((255, 235, 200))

        self.fade_surf = pygame.Surface((w, h))
        self.fade_surf.fill((0, 0, 0))

        # frase final con las letras separadas
        font = pygame.font.Font(None, max(18, round(h * 0.036)))

        self.tagline = self._spaced_text(
            font, self.TAGLINE, (205, 188, 160), round(h * 0.012)
        )

    def _make_streak(self, length, thickness):

        strip = pygame.Surface((length, 1))

        for x in range(length):

            k = abs(x - (length - 1) / 2.0) / ((length - 1) / 2.0)

            v = int(255 * (1.0 - k) ** 1.4)

            strip.set_at((x, 0), (v, round(v * 0.84), round(v * 0.62)))

        streak = pygame.transform.smoothscale(strip, (length, thickness))

        # perfil vertical: fino y brillante en el centro
        profile = pygame.Surface((1, thickness))

        c = (thickness - 1) / 2.0

        for y in range(thickness):

            k = abs(y - c) / max(1.0, c)

            v = int(255 * (1.0 - k) ** 2)

            profile.set_at((0, y), (v, v, v))

        profile = pygame.transform.scale(profile, (length, thickness))

        streak.blit(profile, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        return streak

    def _spaced_text(self, font, text, color, spacing):

        glyphs = [font.render(ch, True, color) for ch in text]

        width = sum(g.get_width() for g in glyphs) + spacing * (len(glyphs) - 1)

        height = max(g.get_height() for g in glyphs)

        surf = pygame.Surface((max(1, width), height), pygame.SRCALPHA)

        x = 0

        for g in glyphs:

            surf.blit(g, (x, 0))

            x += g.get_width() + spacing

        return surf

    # ------------------------------------------------------------------
    # logica
    # ------------------------------------------------------------------

    @property
    def _t(self):

        """Tiempo en segundos de diseno (la secuencia se adapta a duration)."""

        return self.timer * (DESIGN_TIME / self.duration)

    def skip(self):

        """Salta al final: queda el titulo completo y se funde a negro."""

        target = (DESIGN_TIME - self.FADE_OUT * 0.6) * (
            self.duration / DESIGN_TIME
        )

        self.timer = max(self.timer, target)

    def update(self, dt):

        self.timer += dt

        self._update_embers(dt)

        if self.timer >= self.duration:

            return "done"

        return None

    def _update_embers(self, dt):

        t = self._t

        # empiezan despues de la chispa y van en aumento
        rate = 0.0

        if t > 0.9:
            rate = 10.0 + 14.0 * _smooth((t - 0.9) / 2.0)

        self._ember_acc += rate * dt

        while self._ember_acc >= 1.0 and len(self.embers) < self.EMBER_MAX:

            self._ember_acc -= 1.0

            life = self.rng.uniform(2.4, 4.4)

            self.embers.append({
                "x": self.rng.uniform(self.width * 0.12, self.width * 0.88),
                "y": self.rng.uniform(self.height * 0.78, self.height * 0.95),
                "vx": self.rng.uniform(-10, 10),
                "vy": -self.rng.uniform(26, 78),
                "life": life,
                "max": life,
                "size": self.rng.choice((1, 1, 2, 2, 3)),
                "phase": self.rng.uniform(0, math.tau),
                "color": self.rng.choice(
                    ((255, 175, 75), (255, 125, 45), (255, 225, 150))
                ),
            })

        self._ember_acc = min(self._ember_acc, 3.0)

        for e in self.embers:

            e["life"] -= dt
            e["phase"] += dt * 4.0

            e["x"] += (e["vx"] + math.sin(e["phase"]) * 14.0) * dt
            e["y"] += e["vy"] * dt

        self.embers = [e for e in self.embers if e["life"] > 0]

    # ------------------------------------------------------------------
    # dibujo
    # ------------------------------------------------------------------

    def _flicker(self, t):

        """Parpadeo de llama (0..1), suave y irregular."""

        return _clamp(
            0.5
            + 0.25 * math.sin(t * 9.1)
            + 0.15 * math.sin(t * 17.3 + 1.7)
            + 0.10 * math.sin(t * 31.0 + 0.4)
        )

    def _draw_title(self, c, t, cx, cy):

        layer = self.layer

        layer.fill((0, 0, 0))

        # la revelacion avanza desde el centro hacia los costados
        reveal = _ease_out(_span(t, 1.0, 2.35))

        rw = round(self.tw * reveal)

        if rw > 0:

            rx = (self.tw - rw) // 2

            layer.blit(
                self.title, (rx, 0), area=pygame.Rect(rx, 0, rw, self.th)
            )

        # brillo que recorre las letras una vez
        sweep = _span(t, 3.0, 4.0)

        if 0.0 < sweep < 1.0 and rw >= self.tw:

            tmp = pygame.Surface((self.tw, self.th))

            tmp.fill((0, 0, 0))

            bx = round(
                -self.band.get_width()
                + (self.tw + self.band.get_width() * 2) * _smooth(sweep)
            )

            tmp.blit(
                self.band,
                (bx, (self.th - self.band.get_height()) // 2),
                special_flags=pygame.BLEND_ADD,
            )

            tmp.blit(
                self.title, (0, 0), special_flags=pygame.BLEND_RGB_MULT
            )

            layer.blit(tmp, (0, 0), special_flags=pygame.BLEND_ADD)

        # titilar de llama
        flick = 0.90 + 0.10 * self._flicker(t)

        v = int(255 * flick)

        layer.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)

        # empuje lento hacia la camara
        zoom = 1.0 + 0.07 * _smooth(_span(t, 1.6, DESIGN_TIME))

        size = (round(self.tw * zoom), round(self.th * zoom))

        scaled = pygame.transform.scale(layer, size)

        # halo: la misma imagen un poco mas grande y tenue
        if reveal > 0.2:

            halo = pygame.transform.scale(
                layer, (round(size[0] * 1.045), round(size[1] * 1.08))
            )

            halo.fill((95, 62, 34), special_flags=pygame.BLEND_RGB_MULT)

            c.blit(
                halo, halo.get_rect(center=(cx, cy)),
                special_flags=pygame.BLEND_ADD,
            )

        c.blit(
            scaled, scaled.get_rect(center=(cx, cy)),
            special_flags=pygame.BLEND_ADD,
        )

        return reveal, zoom

    def draw(self):

        t = self._t

        w, h = self.width, self.height

        c = self.canvas

        c.fill((0, 0, 0))

        cx = w // 2
        cy = round(h * 0.46)

        flick = self._flicker(t)

        # --- resplandor detras del titulo ---------------------------------
        bloom_k = _smooth(_span(t, 1.2, 2.9)) * (0.78 + 0.22 * flick)

        if bloom_k > 0.01:

            self.bloom.set_alpha(int(255 * bloom_k))

            c.blit(self.bloom, self.bloom.get_rect(center=(cx, cy)))

        # --- chispa inicial ------------------------------------------------
        spark_k = _span(t, 0.25, 0.9)

        if 0.0 < spark_k and t < 1.7:

            fade = 1.0 - _span(t, 1.2, 1.7)

            s = round(h * (0.02 + 0.10 * _smooth(spark_k)))

            s = max(2, s)

            spark = pygame.transform.scale(self.spark, (s, s))

            spark.set_alpha(int(255 * fade * (0.7 + 0.3 * flick)))

            c.blit(spark, spark.get_rect(center=(cx, cy)))

        # --- barrido de luz horizontal -------------------------------------
        grow = _ease_out(_span(t, 0.8, 1.5))

        thin = 1.0 - _smooth(_span(t, 1.7, 2.9))

        if grow > 0.0 and thin > 0.0:

            length = max(2, round(self.streak.get_width() * grow))

            thick = max(2, round(self.streak.get_height() * (0.35 + 0.65 * thin)))

            streak = pygame.transform.scale(self.streak, (length, thick))

            tone = int(255 * thin)

            streak.fill(
                (tone, tone, tone), special_flags=pygame.BLEND_RGB_MULT
            )

            c.blit(
                streak, streak.get_rect(center=(cx, cy)),
                special_flags=pygame.BLEND_ADD,
            )

        # --- titulo --------------------------------------------------------
        reveal, zoom = self._draw_title(c, t, cx, cy)

        # puntas luminosas en los bordes mientras se abre (y un poco despues)
        tip = 1.0 - _smooth(_span(t, 2.2, 2.8))

        if reveal > 0.0 and tip > 0.0:

            half = round(self.tw * zoom * reveal / 2.0)

            self.edge.set_alpha(int(255 * tip))

            for sign in (-1, 1):

                c.blit(
                    self.edge,
                    self.edge.get_rect(center=(cx + sign * half, cy)),
                )

        # --- brasas --------------------------------------------------------
        for e in self.embers:

            life_k = e["life"] / e["max"]

            a = min(1.0, life_k * 2.2) * (
                0.55 + 0.45 * math.sin(e["phase"] * 2.0) ** 2
            )

            col = (
                int(e["color"][0] * a),
                int(e["color"][1] * a),
                int(e["color"][2] * a),
            )

            pygame.draw.circle(
                c, col, (round(e["x"]), round(e["y"])), e["size"]
            )

        # --- vineta --------------------------------------------------------
        c.blit(self.vignette, (0, 0))

        # --- frase final ---------------------------------------------------
        tag_k = _smooth(_span(t, 3.3, 4.2))

        if tag_k > 0.0:

            ty = cy + round(self.th * zoom / 2.0) + round(h * 0.075)

            line_w = round(self.tagline.get_width() * (0.35 + 0.65 * tag_k))

            line_col = (
                int(150 * tag_k), int(122 * tag_k), int(88 * tag_k)
            )

            line_y = ty - round(h * 0.022)

            pygame.draw.line(
                c, line_col,
                (cx - line_w // 2, line_y),
                (cx + line_w // 2, line_y),
                max(1, round(h / 540)),
            )

            self.tagline.set_alpha(int(255 * tag_k))

            c.blit(self.tagline, self.tagline.get_rect(midtop=(cx, ty)))

        # --- destello + temblor del golpe de luz ---------------------------
        flash = 1.0 - _span(t, self.FLASH_AT, self.FLASH_AT + 0.4)

        ox = oy = 0

        if t >= self.FLASH_AT and flash > 0.0:

            self.flash_surf.set_alpha(int(120 * flash ** 2))

            c.blit(self.flash_surf, (0, 0))

            amp = 6.0 * flash

            ox = round(self.rng.uniform(-amp, amp))
            oy = round(self.rng.uniform(-amp, amp))

        # --- barras de cine ------------------------------------------------
        bar = round(h * self.BAR_RATIO * _ease_out(_span(t, 0.0, 1.0)))

        if bar > 0:

            pygame.draw.rect(c, (0, 0, 0), (0, 0, w, bar))
            pygame.draw.rect(c, (0, 0, 0), (0, h - bar, w, bar))

        # --- barra de carga fina -------------------------------------------
        prog = _clamp(self.timer / self.duration)

        bar_w = round(w * 0.26)
        bar_x = cx - bar_w // 2
        bar_y = h - max(6, round(h * 0.042))

        load_k = _smooth(_span(t, 0.6, 1.4))

        if load_k > 0.0:

            line_w = max(1, round(h / 360))

            pygame.draw.line(
                c,
                (int(58 * load_k), int(46 * load_k), int(34 * load_k)),
                (bar_x, bar_y), (bar_x + bar_w, bar_y), line_w,
            )

            head = bar_x + round(bar_w * prog)

            pygame.draw.line(
                c,
                (int(255 * load_k), int(185 * load_k), int(95 * load_k)),
                (bar_x, bar_y), (head, bar_y), line_w,
            )

            pygame.draw.circle(
                c,
                (int(255 * load_k), int(225 * load_k), int(160 * load_k)),
                (head, bar_y), max(2, round(h / 270)),
            )

        # --- fundido final -------------------------------------------------
        out = _span(t, DESIGN_TIME - self.FADE_OUT, DESIGN_TIME)

        if out > 0.0:

            self.fade_surf.set_alpha(int(255 * out))

            c.blit(self.fade_surf, (0, 0))

        # --- a pantalla ----------------------------------------------------
        if ox or oy:
            self.screen.fill((0, 0, 0))

        self.screen.blit(c, (ox, oy))