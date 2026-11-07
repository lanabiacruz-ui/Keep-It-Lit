import math
import random
from pathlib import Path

import pygame

from core.audio_manager import audio
from core import story


PANELS = {
    "image1.png": [
        {
            "rect": (4, 3, 326, 176),
            "wipe": "left",
            "push": 0.05,
            "sound": "swing",
        },
        {
            "rect": (329, 3, 422, 176),
            "wipe": "cut",
            "shake": 6.0,
            "slam": 0.10,
            "sound": "door_hit",
        },
        {
            "rect": (5, 177, 240, 323),
            "wipe": "right",
            "push": 0.05,
            "sound": "swing",
        },
        {
            "rect": (243, 177, 422, 323),
            "wipe": "left",
            "shake": 2.0,
            "push": 0.08,
            "sound": "swing",
        },
        {
            "rect": (1, 325, 427, 565),
            "wipe": "iris",
            "shake": 16.0,
            "slam": 0.22,
            "push": 0.12,
            "flash": 0.9,
            "embers": 0.4,
            "beat": True,
            "sound": "hit_heavy",
        },
    ],
    "image2.png": [
        {
            "rect": (6, 4, 259, 214),
            "wipe": "cut",
            "shake": 10.0,
            "slam": 0.12,
            "flash": 0.6,
            "sound": "alert",
        },
        {
            "rect": (262, 4, 422, 214),
            "wipe": "iris",
            "push": 0.10,
            "embers": 0.5,
            "sound": "swing",
        },
        {
            "rect": (6, 216, 224, 363),
            "wipe": "down",
            "embers": 0.4,
            "sound": "swing",
        },
        {
            "rect": (226, 216, 422, 363),
            "wipe": "left",
            "push": 0.08,
            "embers": 0.4,
            "sound": "swing",
        },
        {
            "rect": (6, 365, 245, 567),
            "wipe": "up",
            "push": 0.08,
            "sound": "swing",
        },
        {
            "rect": (247, 365, 422, 567),
            "wipe": "iris",
            "shake": 5.0,
            "slam": 0.16,
            "push": 0.16,
            "flash": 0.7,
            "glow": (255, 60, 35),
            "embers": 5.0,
            "beat": True,
            "sound": "fireball",
        },
    ],
}


PAGE_OUT_TARGET = {
    0: (262, 430),
}


def _clamp(v, lo=0.0, hi=1.0):

    return max(lo, min(hi, v))


def _span(t, a, b):

    if b <= a:
        return 1.0 if t >= b else 0.0

    return _clamp((t - a) / (b - a))


def _ease_out(k):

    k = _clamp(k)

    return 1.0 - (1.0 - k) ** 3


def _ease_in(k, power=2.2):

    return _clamp(k) ** power


def _ease_in_out(k):

    k = _clamp(k)

    return k * k * (3.0 - 2.0 * k)


def _glow(size, color, power=2.0):

    surf = pygame.Surface((size, size))
    surf.fill((0, 0, 0))

    c = size // 2

    for r in range(c, 0, -1):

        k = (1 - r / c) ** power

        pygame.draw.circle(
            surf,
            (
                int(color[0] * k),
                int(color[1] * k),
                int(color[2] * k),
            ),
            (c, c),
            r
        )

    return surf


class Comic:

    IMAGES = ["image1.png", "image2.png"]

    TITLE = "LA NOCHE EN QUE TODO SE APAGÓ"
    FINALE = "LA BÚSQUEDA COMIENZA"

    FINALE_TARGET = (336, 458)

    DONE_EVENT = pygame.USEREVENT + 37

    FADE_TIME = 0.9

    INPUT_DELAY = 0.3

    STEP_DELAY = 0.35

    TITLE_TIME = 3.4

    TITLE_DISSOLVE = 0.75

    INTRO_TIME = 1.7

    IRIS_TIME = 1.0

    PAGE_INTRO_TIME = 1.2

    OUT_TIME = 1.0

    FIN_FLASH_AT = 1.2

    FIN_FADE_AT = 3.4

    FIN_TIME = 3.95

    BLUR = 24

    DARKEN = 150

    SHADOW = 18

    HIDDEN_VEIL = 236

    DIM_VEIL = 120

    CAM_SPEED = 3.4

    BAR_RATIO = 0.06

    EMBER_COLOR = (255, 150, 60)

    MAX_PARTICLES = 110

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()

        folder = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
        )

        self.sources = []
        self.backgrounds = []
        self.shadows = []
        self.page_panels = []

        for name in self.IMAGES:

            image = pygame.image.load(
                folder / name
            ).convert()

            self.sources.append(image)

            self.backgrounds.append(
                self._make_background(image)
            )

            self.page_panels.append(
                self._build_panels(name, image.get_size())
            )

        self.font = pygame.font.Font(
            None,
            max(18, round(self.height * 0.03))
        )

        self.vignette = self._make_vignette()
        self.sprites = self._make_sprites()

        self.black = pygame.Surface(
            (self.width, self.height)
        )
        self.black.fill((0, 0, 0))

        self.white = pygame.Surface(
            (self.width, self.height)
        )
        self.white.fill((255, 255, 255))

        self.scene = pygame.Surface(
            (self.width, self.height)
        )

        self.glow_src = _glow(128, (255, 150, 60))

        self.bar_height = round(self.height * self.BAR_RATIO)

        self.particles = []
        self.spawn_acc = 0.0

        self.total_time = 0.0

        self.screen_flash = 0.0
        self.shake = 0.0
        self.beat = 0.0
        self.beat_timer = 0.0

        self._view = (0.0, 0.0, 1.0)

        self._build_text()

        self.page = 0

        self._start_page(0)

    def _layout(self, text, size, color, tracking, max_w):

        while True:

            font = pygame.font.Font(None, size)

            items = []

            x = 0

            for ch in text:

                img = font.render(ch, True, color)

                if ch == " ":
                    adv = max(4, size // 3)
                else:
                    adv = font.size(ch)[0]

                items.append((img, x, adv))

                x += adv + tracking

            total = x - tracking

            if total <= max_w or size <= 14:
                break

            size = int(size * 0.92)

        return {
            "items": items,
            "w": total,
            "h": font.get_height(),
        }

    def _build_text(self):

        w, h = self.width, self.height

        self.title_layout = self._layout(
            self.TITLE,
            round(h * 0.098),
            (255, 238, 205),
            round(h * 0.006),
            w * 0.86
        )

        self.finale_layout = self._layout(
            self.FINALE,
            round(h * 0.1),
            (255, 238, 205),
            round(h * 0.008),
            w * 0.82
        )

        self.title_bloom = pygame.transform.smoothscale(
            self.glow_src,
            (
                round(self.title_layout["w"] * 1.5),
                round(self.title_layout["h"] * 4.2)
            )
        )

        self.finale_bloom = pygame.transform.smoothscale(
            self.glow_src,
            (
                round(self.finale_layout["w"] * 1.5),
                round(self.finale_layout["h"] * 4.2)
            )
        )

    def _build_panels(self, name, size):

        bounds = pygame.Rect(0, 0, size[0], size[1])

        raw = PANELS.get(name)

        if not raw:
            raw = [{"rect": (0, 0, size[0], size[1])}]

        panels = []

        for item in raw:

            x0, y0, x1, y1 = item["rect"]

            rect = pygame.Rect(
                x0,
                y0,
                x1 - x0,
                y1 - y0
            ).clip(bounds)

            if rect.width < 4 or rect.height < 4:
                continue

            panels.append(self._panel_data(rect, item))

        if not panels:

            panels.append(
                self._panel_data(bounds.copy(), {})
            )

        return panels

    def _panel_data(self, rect, item):

        veil = pygame.Surface(rect.size)
        veil.fill((0, 0, 0))

        wipe = item.get("wipe", "left")

        if wipe == "cut":
            reveal_time = 0.001
        elif wipe == "iris":
            reveal_time = 0.65
        else:
            reveal_time = 0.45

        return {
            "rect": rect,
            "veil": veil,
            "wipe": wipe,
            "reveal_time": reveal_time,
            "beat": item.get("beat", False),
            "shake": item.get("shake", 0.0),
            "slam": item.get("slam", 0.0),
            "push": item.get("push", 0.04),
            "flash": item.get("flash", 0.45),
            "glow": item.get("glow"),
            "embers": item.get("embers", 1.0),
            "sound": item.get("sound"),
        }

    def _make_background(self, image):

        cover = max(
            self.width / image.get_width(),
            self.height / image.get_height()
        )

        big = pygame.transform.smoothscale(
            image,
            (
                round(image.get_width() * cover),
                round(image.get_height() * cover)
            )
        )

        bg = pygame.Surface((self.width, self.height))

        bg.blit(
            big,
            big.get_rect(center=(self.width // 2, self.height // 2))
        )

        tiny = pygame.transform.smoothscale(
            bg,
            (
                max(1, self.width // self.BLUR),
                max(1, self.height // self.BLUR)
            )
        )

        bg = pygame.transform.smoothscale(
            tiny,
            (self.width, self.height)
        )

        shade = pygame.Surface((self.width, self.height))
        shade.fill((8, 8, 14))
        shade.set_alpha(self.DARKEN)

        bg.blit(shade, (0, 0))

        return bg

    def _make_vignette(self):

        w, h = 96, 54

        small = pygame.Surface((w, h), pygame.SRCALPHA)

        for y in range(h):

            for x in range(w):

                dx = (x + 0.5) / w * 2 - 1
                dy = (y + 0.5) / h * 2 - 1

                d = min(1.0, math.sqrt(dx * dx + dy * dy) / 1.35)

                a = int(200 * max(0.0, (d - 0.42) / 0.58) ** 1.6)

                small.set_at((x, y), (0, 0, 0, min(255, a)))

        return pygame.transform.smoothscale(
            small,
            (self.width, self.height)
        )

    def _make_sprites(self):

        sprites = []

        for radius in (2, 3, 5):

            levels = []

            for level in range(1, 7):

                size = radius * 4

                surf = pygame.Surface((size, size))
                surf.fill((0, 0, 0))

                for r in range(radius * 2, 0, -1):

                    t = (1 - r / (radius * 2)) ** 1.5

                    k = t * level / 6

                    color = (
                        int(self.EMBER_COLOR[0] * k),
                        int(self.EMBER_COLOR[1] * k),
                        int(self.EMBER_COLOR[2] * k),
                    )

                    pygame.draw.circle(
                        surf,
                        color,
                        (size // 2, size // 2),
                        r
                    )

                levels.append(surf)

            sprites.append(levels)

        return sprites

    def _make_shadow(self, rect):

        shadow = pygame.Surface(
            (
                rect.width + self.SHADOW * 2,
                rect.height + self.SHADOW * 2
            ),
            pygame.SRCALPHA
        )

        for step in range(self.SHADOW):

            pygame.draw.rect(
                shadow,
                (0, 0, 0, 12),
                shadow.get_rect().inflate(-step * 2, -step * 2),
                border_radius=10
            )

        return shadow

    def _start_page(self, index):

        self.page = index

        self.source = self.sources[index]
        self.background = self.backgrounds[index]
        self.panels = self.page_panels[index]

        self.pw, self.ph = self.source.get_size()

        self.work = self.source.copy()

        count = len(self.panels)

        self.reveal = [0.0] * count
        self.focus_amt = [0.0] * count
        self.flash = [0.0] * count
        self.pop = [0.0] * count

        self.focus = -1
        self.max_focus = -1

        self.page_time = 0.0
        self.step_time = 0.0
        self.panel_time = 0.0
        self.out_time = 0.0

        self.title_t = 0.0
        self.title_fade_t = 99.0
        self.intro_time = 0.0
        self.intro_len = self.INTRO_TIME
        self.iris_on = False
        self.iris_origin = (self.width // 2, self.height // 2)

        self.fin_t = 0.0
        self.done_sent = False

        self.beat = 0.0
        self.beat_timer = 0.0

        self.cues = set()

        self.shake = 0.0
        self.screen_flash = 0.0

        available = self.height - self.bar_height * 2

        self.k0 = min(
            self.width * 0.92 / self.pw,
            available * 0.98 / self.ph
        )

        self.cam_x = self.pw / 2
        self.cam_y = self.ph / 2

        page_size = pygame.Rect(
            0,
            0,
            round(self.pw * self.k0),
            round(self.ph * self.k0)
        )

        self.shadow = self._make_shadow(page_size)

        if index == 0:

            self.phase = "title"

            self.cam_k = self.k0 * 0.9

        else:

            self.phase = "intro"

            self.intro_len = self.PAGE_INTRO_TIME

            self.cam_k = self.k0 * 1.3

            audio.play("light_out", 0.8)

    def _cue(self, key, when, action):

        if when and key not in self.cues:

            self.cues.add(key)

            action()

    def _jitter(self):

        if self.shake <= 0:
            return 0, 0

        return (
            round(random.uniform(-1, 1) * self.shake),
            round(random.uniform(-1, 1) * self.shake)
        )

    def _burst(self, x, y, count, speed=220.0):

        for _ in range(count):

            if len(self.particles) >= self.MAX_PARTICLES + 90:
                break

            angle = random.uniform(0, math.tau)

            sp = random.uniform(0.25, 1.0) * speed

            life = random.uniform(1.4, 3.2)

            self.particles.append(
                [
                    x,
                    y,
                    math.cos(angle) * sp,
                    math.sin(angle) * sp - 40,
                    life,
                    life,
                    random.choice((0, 1, 2, 2)),
                    random.uniform(0, 6.28),
                ]
            )

    def _ignite(self):

        self.phase = "intro"

        self.intro_time = 0.0
        self.intro_len = self.INTRO_TIME

        self.iris_on = True
        self.iris_origin = (
            self.width // 2,
            round(self.height * 0.70)
        )

        self.title_fade_t = 0.0

        self.screen_flash = 1.0
        self.shake = 20.0

        self.step_time = 0.0

        self.cam_x = self.pw / 2
        self.cam_y = self.ph / 2
        self.cam_k = self.k0 * 1.55

        self._burst(
            self.iris_origin[0],
            self.iris_origin[1],
            60,
            420.0
        )

        audio.play("hit_heavy", 1.0)
        audio.play("explosion", 0.5)

    def _begin_out(self):

        self.phase = "out"
        self.out_time = 0.0

        self.pop = [0.0] * len(self.panels)
        self.beat = 0.0

        self.out_x0 = self.cam_x
        self.out_y0 = self.cam_y
        self.out_k0 = self.cam_k

        target = PAGE_OUT_TARGET.get(self.page)

        if target is None:
            target = self.panels[-1]["rect"].center

        self.out_tx, self.out_ty = target

        audio.play("boss_roar", 0.55)
        audio.play("swing", 0.6)

    def _begin_finale(self):

        self.phase = "finale"

        self.pop = [0.0] * len(self.panels)
        self.flash = [0.0] * len(self.panels)
        self.beat = 0.0

        self.fin_t = 0.0
        self.done_sent = False

        self.fin_x0 = self.cam_x
        self.fin_y0 = self.cam_y
        self.fin_k0 = self.cam_k

        audio.play("swing", 0.5)

    def _fit(self, rect):

        return min(
            self.width * 0.80 / rect.width,
            self.height * 0.74 / rect.height
        )

    def _focus(self, index):

        first = index > self.max_focus

        self.phase = "panel"
        self.focus = index
        self.step_time = 0.0
        self.panel_time = 0.0

        panel = self.panels[index]

        if panel["beat"]:
            self.beat_timer = 0.5

        if not first:
            return

        self.max_focus = index

        if self.page == 1 and index >= 2:
            story.set_cat_gone()

        self.flash[index] = panel["flash"]
        self.pop[index] = 1.0

        self.shake = max(self.shake, panel["shake"])

        if panel["flash"] >= 0.7:
            self.screen_flash = max(self.screen_flash, 0.3)

        if panel["shake"] >= 10 or panel["slam"] >= 0.2:

            self._burst(
                self.width * 0.5,
                self.height * 0.55,
                26,
                260.0
            )

        if panel["slam"] > 0:
            self.cam_k *= 1 + panel["slam"]

        if panel["sound"]:

            volume = 0.5 if panel["sound"] == "swing" else 0.9

            audio.play(panel["sound"], volume)

    def _advance(self):

        if self.phase == "title":

            if self.title_t >= 0.5:
                self._ignite()

            return None

        if self.phase == "finale":

            if self.fin_t >= 0.8:
                return "done"

            return None

        if self.phase == "intro":

            self.iris_on = False

            self._focus(0)

            return None

        if self.phase == "panel":

            if self.focus + 1 < len(self.panels):

                self._focus(self.focus + 1)

            else:

                self.phase = "overview"
                self.step_time = 0.0

                audio.play("swing", 0.4)

            return None

        if self.phase == "overview":

            if self.page + 1 >= len(self.sources):

                story.set_cat_gone()

                self._begin_finale()

                return None

            self._begin_out()

        return None

    def _back(self):

        if self.phase == "overview":

            self.phase = "panel"
            self.focus = len(self.panels) - 1
            self.step_time = 0.0
            self.panel_time = 0.0

        elif self.phase == "panel" and self.focus > 0:

            self.focus -= 1
            self.step_time = 0.0
            self.panel_time = 0.0

    def handle_event(self, event):

        if event.type == self.DONE_EVENT:

            story.set_cat_gone()

            return "done"

        if self.page_time < self.INPUT_DELAY:
            return None

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                story.set_cat_gone()
                return "done"

            if event.key in (
                pygame.K_LEFT,
                pygame.K_BACKSPACE
            ):

                if self.step_time >= self.STEP_DELAY:
                    self._back()

                return None

            if event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_SPACE,
                pygame.K_RIGHT
            ):

                if self.step_time < self.STEP_DELAY:
                    return None

                return self._advance()

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if self.step_time < self.STEP_DELAY:
                    return None

                return self._advance()

        return None

    def _camera_target(self):

        if self.phase == "panel":

            panel = self.panels[self.focus]
            rect = panel["rect"]

            k = self._fit(rect) * (
                1 + panel["push"] * min(1.0, self.panel_time / 7.0)
            )

            angle = (self.page * 7 + self.focus) * 2.399

            drift = min(self.panel_time, 10.0) * 0.5

            return (
                rect.centerx + math.cos(angle) * drift,
                rect.centery + math.sin(angle) * drift * 0.6,
                k
            )

        if self.phase == "intro":
            return self.pw / 2, self.ph / 2, self.k0 * 0.9

        return self.pw / 2, self.ph / 2, self.k0

    def _approach(self, current, target, rate, dt):

        return current + (target - current) * (1 - math.exp(-dt * rate))

    def _tick_title(self):

        t = self.title_t

        self._cue(
            "hb1",
            t >= 0.35,
            lambda: audio.play("heartbeat", 0.45)
        )

        self._cue(
            "spark",
            t >= 0.8,
            lambda: audio.play("crackle", 0.9)
        )

        self._cue(
            "lit",
            t >= 1.15,
            lambda: audio.play("light_on", 0.6)
        )

        self._cue(
            "hb2",
            t >= 2.45,
            lambda: audio.play("heartbeat", 0.75)
        )

        if t >= self.TITLE_TIME:
            self._ignite()

    def _tick_finale(self):

        t = self.fin_t

        self._cue(
            "f_hb1",
            t >= 0.05,
            lambda: audio.play("heartbeat", 0.7)
        )

        self._cue(
            "f_hb2",
            t >= 0.65,
            lambda: audio.play("heartbeat", 0.9)
        )

        if t < self.FIN_FLASH_AT:

            span = _span(t, 0.0, self.FIN_FLASH_AT)

            move = _ease_in_out(span)

            zoom = _ease_in(span, 2.0)

            tx, ty = self.FINALE_TARGET

            self.cam_x = self.fin_x0 + (tx - self.fin_x0) * move
            self.cam_y = self.fin_y0 + (ty - self.fin_y0) * move

            self.cam_k = self.fin_k0 * (
                (self.k0 * 11.0) / self.fin_k0
            ) ** zoom

            self.shake = max(self.shake, 3.0 * zoom)

        def boom():

            self.screen_flash = 1.0
            self.shake = 16.0

            self._burst(
                self.width * 0.5,
                self.height * 0.55,
                70,
                380.0
            )

            audio.play("fireball", 0.9)
            audio.play("light_on", 0.9)

        self._cue("f_boom", t >= self.FIN_FLASH_AT, boom)

        if t >= self.FIN_TIME and not self.done_sent:

            self.done_sent = True

            pygame.event.post(
                pygame.event.Event(self.DONE_EVENT)
            )

    def update(self, dt):

        dt = min(dt, 0.05)

        self.total_time += dt
        self.page_time += dt
        self.step_time += dt
        self.panel_time += dt
        self.title_fade_t += dt

        self.screen_flash = max(0.0, self.screen_flash - dt * 2.2)

        self.shake *= math.exp(-dt * 3.5)

        if self.shake < 0.05:
            self.shake = 0.0

        if self.phase == "title":

            self.title_t += dt

            self._tick_title()

            self._update_particles(dt)

            return None

        if self.phase == "finale":

            self.fin_t += dt

            self._tick_finale()

            self._update_particles(dt)

            return None

        if self.phase == "intro":

            self.intro_time += dt

            if self.intro_time >= self.intro_len:

                self.iris_on = False

                self._focus(0)

        if self.phase == "out":

            self.out_time += dt

            if self.out_time >= self.OUT_TIME:
                self._start_page(self.page + 1)

                return None

        overview = self.phase == "overview"

        for i, panel in enumerate(self.panels):

            show = (
                i <= self.max_focus
                or overview
                or self.phase == "out"
            )

            lit = 1.0 if (i == self.focus or overview) else 0.0

            if self.phase == "out":
                lit = 1.0

            if show:

                self.reveal[i] = min(
                    1.0,
                    self.reveal[i] + dt / panel["reveal_time"]
                )

            self.focus_amt[i] = self._approach(
                self.focus_amt[i],
                lit,
                5.0,
                dt
            )

            self.flash[i] = max(0.0, self.flash[i] - dt * 1.8)

            self.pop[i] = max(0.0, self.pop[i] - dt * 2.2)

        if self.phase == "out":

            e = _span(self.out_time, 0.0, self.OUT_TIME)

            move = _ease_in_out(e)

            self.cam_x = self.out_x0 + (self.out_tx - self.out_x0) * move
            self.cam_y = self.out_y0 + (self.out_ty - self.out_y0) * move

            self.cam_k = self.out_k0 * (1 + 1.9 * e ** 2.2)

            self.shake = max(self.shake, 6.0 * e)

        else:

            tx, ty, tk = self._camera_target()

            self.cam_x = self._approach(self.cam_x, tx, self.CAM_SPEED, dt)
            self.cam_y = self._approach(self.cam_y, ty, self.CAM_SPEED, dt)

            self.cam_k = math.exp(
                self._approach(
                    math.log(self.cam_k),
                    math.log(tk),
                    self.CAM_SPEED,
                    dt
                )
            )

        if self.phase == "panel" and self.panels[self.focus]["beat"]:

            self.beat_timer += dt

            if self.beat_timer >= 1.15:

                self.beat_timer = 0.0
                self.beat = 1.0

                audio.play("heartbeat", 0.65)

        self.beat *= math.exp(-dt * 6.0)

        if self.beat < 0.01:
            self.beat = 0.0

        self._update_particles(dt)

        return None

    def _ember_rate(self):

        if self.phase == "panel":
            return 9.0 * self.panels[self.focus]["embers"]

        if self.phase == "title":
            return 7.0

        if self.phase == "finale":
            return 14.0

        return 8.0

    def _update_particles(self, dt):

        self.spawn_acc += self._ember_rate() * dt

        while (
            self.spawn_acc >= 1.0
            and len(self.particles) < self.MAX_PARTICLES
        ):

            self.spawn_acc -= 1.0

            life = random.uniform(4.0, 8.0)

            self.particles.append(
                [
                    random.uniform(0, self.width),
                    random.uniform(self.height * 0.5, self.height + 10),
                    random.uniform(-10, 10),
                    -random.uniform(25, 80),
                    life,
                    life,
                    random.choice((0, 0, 1, 2)),
                    random.uniform(0, 6.28),
                ]
            )

        self.spawn_acc = min(self.spawn_acc, 2.0)

        drag = math.exp(-dt * 1.6)

        alive = []

        for p in self.particles:

            p[4] -= dt

            if p[4] <= 0:
                continue

            if abs(p[2]) > 26:
                p[2] *= drag

            if abs(p[3]) > 95:
                p[3] *= drag

            p[0] += (p[2] + math.sin(p[4] * 2.5 + p[7]) * 14) * dt
            p[1] += p[3] * dt

            if p[1] < -10 or p[1] > self.height + 40:
                continue

            alive.append(p)

        self.particles = alive

    def _blit_veil(self, panel, alpha):

        panel["veil"].set_alpha(int(alpha))

        self.work.blit(panel["veil"], panel["rect"])

    def _blit_wipe(self, panel, progress, dim):

        rect = panel["rect"]
        kind = panel["wipe"]

        e = _ease_out(progress)

        w, h = rect.size

        veil = pygame.Surface((w, h), pygame.SRCALPHA)
        veil.fill((0, 0, 0, self.HIDDEN_VEIL))

        clear = (0, 0, 0, int(dim))

        edge = None

        if kind == "iris":

            radius = round(e * math.hypot(w / 2, h / 2)) + 1

            pygame.draw.circle(
                veil,
                clear,
                (w // 2, h // 2),
                radius
            )

        else:

            if kind == "right":

                size = round(w * e)

                area = pygame.Rect(w - size, 0, size, h)
                edge = pygame.Rect(w - size - 2, 0, 3, h)

            elif kind == "down":

                size = round(h * e)

                area = pygame.Rect(0, 0, w, size)
                edge = pygame.Rect(0, size - 1, w, 3)

            elif kind == "up":

                size = round(h * e)

                area = pygame.Rect(0, h - size, w, size)
                edge = pygame.Rect(0, h - size - 2, w, 3)

            else:

                size = round(w * e)

                area = pygame.Rect(0, 0, size, h)
                edge = pygame.Rect(size - 1, 0, 3, h)

            veil.fill(clear, area)

        self.work.blit(veil, rect)

        if edge is not None:

            level = 1.0 - progress

            color = (
                int(255 * level),
                int(200 * level),
                int(115 * level)
            )

            spot = edge.move(rect.topleft).clip(rect)

            if spot.width > 0 and spot.height > 0:

                self.work.fill(
                    color,
                    spot,
                    special_flags=pygame.BLEND_RGB_ADD
                )

    def _compose_page(self):

        self.work.blit(self.source, (0, 0))

        for i, panel in enumerate(self.panels):

            rect = panel["rect"]

            p = self.reveal[i]
            f = self.focus_amt[i]

            dim = self.DIM_VEIL * (1 - f)

            if p <= 0:

                self._blit_veil(panel, self.HIDDEN_VEIL)

            elif p < 1.0:

                self._blit_wipe(panel, p, dim)

            elif dim > 1:

                self._blit_veil(panel, dim)

            if self.flash[i] > 0.01:

                v = int(255 * min(1.0, self.flash[i]) * 0.6)

                self.work.fill(
                    (v, v, v),
                    rect,
                    special_flags=pygame.BLEND_RGB_ADD
                )

            glow = panel["glow"]

            if glow and p > 0.5 and f > 0.05:

                pulse = (0.55 + 0.45 * math.sin(self.total_time * 3.2)) * f

                self.work.fill(
                    (
                        int(glow[0] * 0.20 * pulse),
                        int(glow[1] * 0.20 * pulse),
                        int(glow[2] * 0.20 * pulse),
                    ),
                    rect,
                    special_flags=pygame.BLEND_RGB_ADD
                )

            if f > 0.05 and p >= 1.0 and self.phase == "panel":

                pulse = 0.65 + 0.35 * math.sin(self.total_time * 2.6)

                a = 0.5 * f * pulse

                color = (
                    int(255 * a),
                    int(160 * a),
                    int(60 * a)
                )

                t = 2

                for edge in (
                    pygame.Rect(rect.x, rect.y, rect.w, t),
                    pygame.Rect(rect.x, rect.bottom - t, rect.w, t),
                    pygame.Rect(rect.x, rect.y, t, rect.h),
                    pygame.Rect(rect.right - t, rect.y, t, rect.h),
                ):

                    self.work.fill(
                        color,
                        edge,
                        special_flags=pygame.BLEND_RGB_ADD
                    )

    def _draw_page(self, surf):

        self._compose_page()

        k = self.cam_k * (1 + 0.02 * self.beat)

        ox = oy = 0.0

        if self.shake > 0:

            ox = random.uniform(-1, 1) * self.shake
            oy = random.uniform(-1, 1) * self.shake

        left = self.cam_x - (self.width / 2 + ox) / k
        top = self.cam_y - (self.height / 2 + oy) / k

        self._view = (left, top, k)

        right = left + self.width / k
        bottom = top + self.height / k

        page_rect = pygame.Rect(
            round(-left * k),
            round(-top * k),
            round(self.pw * k),
            round(self.ph * k)
        )

        if page_rect.width < self.width or page_rect.height < self.height:

            surf.blit(
                self.shadow,
                self.shadow.get_rect(center=page_rect.center).move(0, 4)
            )

        sl = max(0, math.floor(left))
        st = max(0, math.floor(top))
        sr = min(self.pw, math.ceil(right))
        sb = min(self.ph, math.ceil(bottom))

        if sr <= sl or sb <= st:
            return

        src = pygame.Rect(sl, st, sr - sl, sb - st)

        size = (
            max(1, round(src.width * k)),
            max(1, round(src.height * k))
        )

        scaled = pygame.transform.smoothscale(
            self.work.subsurface(src),
            size
        )

        surf.blit(
            scaled,
            (
                round((sl - left) * k),
                round((st - top) * k)
            )
        )

    def _draw_pops(self, surf):

        left, top, k = self._view

        for i, panel in enumerate(self.panels):

            v = self.pop[i]

            if v <= 0.02:
                continue

            rect = panel["rect"]

            grow = round(((1 - v) ** 0.7) * 70)

            area = pygame.Rect(
                round((rect.x - left) * k),
                round((rect.y - top) * k),
                round(rect.w * k),
                round(rect.h * k)
            ).inflate(grow * 2, grow * 2)

            if area.width < 6 or area.height < 6:
                continue

            ring = pygame.Surface(area.size, pygame.SRCALPHA)

            pygame.draw.rect(
                ring,
                (255, 226, 160, int(230 * v ** 1.3)),
                ring.get_rect(),
                width=max(2, round(4 * v)),
                border_radius=4
            )

            surf.blit(ring, area.topleft)

    def _draw_particles(self, surf):

        for x, y, _, _, life, max_life, size, _ in self.particles:

            level = int(5 * (life / max_life))

            level = max(0, min(5, level))

            sprite = self.sprites[size][level]

            surf.blit(
                sprite,
                (round(x) - sprite.get_width() // 2, round(y) - sprite.get_height() // 2),
                special_flags=pygame.BLEND_RGB_ADD
            )

    def _draw_scene(self, surf):

        surf.fill((12, 12, 16))

        surf.blit(self.background, (0, 0))

        self._draw_page(surf)

        self._draw_particles(surf)

        surf.blit(self.vignette, (0, 0))

        if self.beat > 0.03:

            self.vignette.set_alpha(int(150 * self.beat))

            surf.blit(self.vignette, (0, 0))

            self.vignette.set_alpha(255)

        self._draw_pops(surf)

    def _draw_letters(
        self,
        surf,
        layout,
        cx,
        cy,
        t,
        t0,
        step,
        dur,
        pop=1.9,
        spread=1.0,
        alpha=1.0
    ):

        left = -layout["w"] / 2

        for i, (img, x, adv) in enumerate(layout["items"]):

            q = _clamp((t - t0 - i * step) / dur)

            if q <= 0:
                continue

            a = int(255 * q * alpha)

            if a <= 0:
                continue

            e = _ease_out(q)

            scale = (1 + (pop - 1) * (1 - e)) * spread

            px = cx + (left + x + adv / 2) * spread

            if abs(scale - 1) > 0.02:

                im = pygame.transform.smoothscale(
                    img,
                    (
                        max(1, round(img.get_width() * scale)),
                        max(1, round(img.get_height() * scale))
                    )
                )

            else:

                im = img

            im.set_alpha(a)

            surf.blit(im, im.get_rect(center=(round(px), round(cy))))

    def _draw_title(self, surf):

        w, h = self.width, self.height

        t = self.title_t

        jx, jy = self._jitter()

        surf.fill((0, 0, 0))

        cx = w // 2 + jx

        bloom_k = _span(t, 1.3, 2.4)

        if bloom_k > 0:

            bloom = self.title_bloom.copy()

            level = int(
                150 * bloom_k * (0.88 + 0.12 * math.sin(t * 17.0))
            )

            bloom.fill(
                (level, level, level),
                special_flags=pygame.BLEND_RGB_MULT
            )

            surf.blit(
                bloom,
                bloom.get_rect(center=(cx, round(h * 0.46 + jy))),
                special_flags=pygame.BLEND_RGB_ADD
            )

        self._draw_letters(
            surf,
            self.title_layout,
            cx,
            h * 0.46 + jy,
            t,
            1.4,
            0.04,
            0.35,
            pop=1.9
        )

        self._draw_particles(surf)

        surf.blit(self.vignette, (0, 0))

    def _draw_title_dissolve(self, surf):

        e = _ease_out(self.title_fade_t / self.TITLE_DISSOLVE)

        spread = 1 + 0.35 * e

        alpha = 1 - e

        w, h = self.width, self.height

        self._draw_letters(
            surf,
            self.title_layout,
            w // 2,
            h * 0.46,
            99.0,
            0.0,
            0.0,
            1.0,
            pop=1.0,
            spread=spread,
            alpha=alpha
        )

    def _draw_iris(self, surf):

        w, h = self.width, self.height

        p = _span(self.intro_time, 0.0, self.IRIS_TIME)

        e = _ease_out(p)

        cx, cy = self.iris_origin

        diag = math.hypot(max(cx, w - cx), max(cy, h - cy)) + 30

        r = diag * e

        self._draw_scene(self.scene)

        d = 6

        sw, sh = max(1, w // d), max(1, h // d)

        center = (round(cx / d), round(cy / d))

        mask = pygame.Surface((sw, sh), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 255))

        pygame.draw.circle(
            mask,
            (0, 0, 0, 0),
            center,
            max(1, round(r / d))
        )

        mask = pygame.transform.smoothscale(mask, (w, h))

        self.scene.blit(mask, (0, 0))

        surf.blit(self.scene, (0, 0))

        ring = pygame.Surface((sw, sh))
        ring.fill((0, 0, 0))

        ring_w = max(2, round(r / d * 0.14))

        pygame.draw.circle(
            ring,
            (255, 170, 80),
            center,
            max(ring_w + 1, round(r / d)),
            ring_w
        )

        ring = pygame.transform.smoothscale(ring, (w, h))

        level = int(255 * (1 - p) ** 0.8)

        ring.fill(
            (level, level, level),
            special_flags=pygame.BLEND_RGB_MULT
        )

        surf.blit(ring, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        tint = 1 - p

        surf.fill(
            (int(60 * tint), int(30 * tint), int(8 * tint)),
            special_flags=pygame.BLEND_RGB_ADD
        )

    def _draw_finale(self, surf):

        w, h = self.width, self.height

        t = self.fin_t

        if t < self.FIN_FLASH_AT:

            self._draw_scene(surf)

            g = _ease_in(_span(t, 0.2, self.FIN_FLASH_AT), 1.6)

            surf.fill(
                (
                    int(255 * g * 0.9),
                    int(120 * g * 0.9),
                    int(40 * g * 0.9)
                ),
                special_flags=pygame.BLEND_RGB_ADD
            )

            return

        jx, jy = self._jitter()

        surf.fill((0, 0, 0))

        cx = w // 2 + jx

        k = _span(t, 1.3, 2.3)

        if k > 0:

            bloom = self.finale_bloom.copy()

            level = int(170 * k * (0.9 + 0.1 * math.sin(t * 15.0)))

            bloom.fill(
                (level, level, level),
                special_flags=pygame.BLEND_RGB_MULT
            )

            surf.blit(
                bloom,
                bloom.get_rect(center=(cx, round(h * 0.46 + jy))),
                special_flags=pygame.BLEND_RGB_ADD
            )

        self._draw_letters(
            surf,
            self.finale_layout,
            cx,
            h * 0.46 + jy,
            t,
            1.45,
            0.045,
            0.35,
            pop=2.0
        )

        line_k = _ease_out(_span(t, 2.0, 2.7))

        line_w = round(self.finale_layout["w"] * 0.7 * line_k)

        if line_w > 2:

            pygame.draw.rect(
                surf,
                (255, 176, 64),
                (
                    cx - line_w // 2,
                    round(h * 0.55 + jy),
                    line_w,
                    3
                )
            )

        self._draw_particles(surf)

        surf.blit(self.vignette, (0, 0))

    def _draw_bars(self, surf):

        t = min(1.0, self.total_time / 1.0)

        eased = 1 - (1 - t) ** 3

        height = round(self.bar_height * eased)

        if height <= 0:
            return None

        pygame.draw.rect(
            surf,
            (0, 0, 0),
            (0, 0, self.width, height)
        )

        pygame.draw.rect(
            surf,
            (0, 0, 0),
            (0, self.height - height, self.width, height)
        )

        if eased < 1.0 or self.phase in ("title", "finale"):
            return None

        center_y = self.height - height // 2

        count = len(self.panels)

        gap = max(14, round(self.height * 0.026))

        start_x = self.width // 2 - (count - 1) * gap // 2

        for i in range(count):

            lit = i <= self.max_focus or self.phase == "overview"

            pos = (start_x + i * gap, center_y)

            if i == self.focus and self.phase == "panel":

                pygame.draw.circle(
                    surf,
                    (255, 190, 90),
                    pos,
                    max(4, gap // 3)
                )

            elif lit:

                pygame.draw.circle(
                    surf,
                    (200, 130, 60),
                    pos,
                    max(3, gap // 4)
                )

            else:

                pygame.draw.circle(
                    surf,
                    (90, 92, 105),
                    pos,
                    max(3, gap // 4),
                    1
                )

        page_text = self.font.render(
            f"{self.page + 1}/{len(self.sources)}",
            True,
            (150, 155, 170)
        )

        surf.blit(
            page_text,
            page_text.get_rect(
                midleft=(18, center_y)
            )
        )

        hint = self.font.render(
            "ENTER: seguir  •  RETROCESO: volver  •  ESC: saltar",
            True,
            (150, 155, 170)
        )

        surf.blit(
            hint,
            hint.get_rect(
                midright=(self.width - 18, center_y)
            )
        )

        return None

    def draw(self):

        surf = self.screen

        if self.phase == "title":

            self._draw_title(surf)

        elif self.phase == "finale":

            self._draw_finale(surf)

        elif (
            self.phase == "intro"
            and self.iris_on
            and self.intro_time < self.IRIS_TIME + 0.05
        ):

            self._draw_iris(surf)

        else:

            self._draw_scene(surf)

        if (
            self.phase not in ("title", "finale")
            and self.title_fade_t < self.TITLE_DISSOLVE
        ):
            self._draw_title_dissolve(surf)

        self._draw_bars(surf)

        if self.screen_flash > 0.01:

            self.white.set_alpha(
                int(255 * min(1.0, self.screen_flash) ** 1.4 * 0.9)
            )

            surf.blit(self.white, (0, 0))

        if self.phase == "out":

            fade = _ease_in(
                _span(self.out_time, 0.35, self.OUT_TIME),
                1.4
            )

        elif self.phase == "finale":

            fade = _span(self.fin_t, self.FIN_FADE_AT, self.FIN_TIME)

        elif self.page > 0:

            fade = max(0.0, 1.0 - self.page_time / self.FADE_TIME)

        else:

            fade = 0.0

        if fade > 0.0:

            self.black.set_alpha(int(255 * fade))

            surf.blit(self.black, (0, 0))