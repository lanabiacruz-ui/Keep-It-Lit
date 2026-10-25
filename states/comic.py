import math
import random
from pathlib import Path

import pygame

from core.audio_manager import audio


PANELS = {
    "image1.png": [
        {
            "rect": (4, 3, 326, 176),
            "push": 0.05,
            "sound": "swing",
        },
        {
            "rect": (329, 3, 422, 176),
            "shake": 6.0,
            "slam": 0.10,
            "sound": "door_hit",
        },
        {
            "rect": (5, 177, 240, 323),
            "push": 0.05,
            "sound": "swing",
        },
        {
            "rect": (243, 177, 422, 323),
            "shake": 2.0,
            "push": 0.08,
            "sound": "swing",
        },
        {
            "rect": (1, 325, 427, 565),
            "shake": 16.0,
            "slam": 0.22,
            "push": 0.12,
            "flash": 0.9,
            "embers": 0.4,
            "sound": "hit_heavy",
        },
    ],
    "image2.png": [
        {
            "rect": (6, 4, 259, 214),
            "shake": 10.0,
            "slam": 0.12,
            "flash": 0.6,
            "sound": "alert",
        },
        {
            "rect": (262, 4, 422, 214),
            "push": 0.10,
            "embers": 0.5,
            "sound": "swing",
        },
        {
            "rect": (6, 216, 224, 363),
            "embers": 0.4,
            "sound": "swing",
        },
        {
            "rect": (226, 216, 422, 363),
            "push": 0.08,
            "embers": 0.4,
            "sound": "swing",
        },
        {
            "rect": (6, 365, 245, 567),
            "push": 0.08,
            "sound": "swing",
        },
        {
            "rect": (247, 365, 422, 567),
            "shake": 5.0,
            "slam": 0.16,
            "push": 0.16,
            "flash": 0.7,
            "glow": (255, 60, 35),
            "embers": 5.0,
            "sound": "fireball",
        },
    ],
}


class Comic:

    IMAGES = ["image1.png", "image2.png"]

    FADE_TIME = 0.6

    INPUT_DELAY = 0.3

    STEP_DELAY = 0.35

    INTRO_TIME = 1.6

    BLUR = 24

    DARKEN = 150

    SHADOW = 18

    HIDDEN_VEIL = 238

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

        self.bar_height = round(self.height * self.BAR_RATIO)

        self.particles = []
        self.spawn_acc = 0.0

        self.total_time = 0.0

        self.page = 0

        self._start_page(0)

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

            veil = pygame.Surface(rect.size)
            veil.fill((0, 0, 0))

            panels.append(
                {
                    "rect": rect,
                    "veil": veil,
                    "shake": item.get("shake", 0.0),
                    "slam": item.get("slam", 0.0),
                    "push": item.get("push", 0.04),
                    "flash": item.get("flash", 0.45),
                    "glow": item.get("glow"),
                    "embers": item.get("embers", 1.0),
                    "sound": item.get("sound"),
                }
            )

        if not panels:

            panels.append(
                {
                    "rect": bounds.copy(),
                    "veil": pygame.Surface(bounds.size),
                    "shake": 0.0,
                    "slam": 0.0,
                    "push": 0.04,
                    "flash": 0.45,
                    "glow": None,
                    "embers": 1.0,
                    "sound": None,
                }
            )

        return panels

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

        self.phase = "intro"
        self.focus = -1
        self.max_focus = -1

        self.page_time = 0.0
        self.step_time = 0.0
        self.panel_time = 0.0
        self.out_time = 0.0

        self.shake = 0.0

        available = self.height - self.bar_height * 2

        self.k0 = min(
            self.width * 0.92 / self.pw,
            available * 0.98 / self.ph
        )

        self.cam_x = self.pw / 2
        self.cam_y = self.ph / 2
        self.cam_k = self.k0 * 0.86

        page_size = pygame.Rect(
            0,
            0,
            round(self.pw * self.k0),
            round(self.ph * self.k0)
        )

        self.shadow = self._make_shadow(page_size)

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

        if not first:
            return

        self.max_focus = index

        panel = self.panels[index]

        self.flash[index] = panel["flash"]

        self.shake = max(self.shake, panel["shake"])

        if panel["slam"] > 0:
            self.cam_k *= 1 + panel["slam"]

        if panel["sound"]:

            volume = 0.5 if panel["sound"] == "swing" else 0.9

            audio.play(panel["sound"], volume)

    def _advance(self):

        if self.phase == "intro":

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
                return "done"

            self.phase = "out"
            self.out_time = 0.0

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

        if self.page_time < self.INPUT_DELAY:
            return None

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
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

        return self.pw / 2, self.ph / 2, self.k0

    def _approach(self, current, target, rate, dt):

        return current + (target - current) * (1 - math.exp(-dt * rate))

    def update(self, dt):

        dt = min(dt, 0.05)

        self.total_time += dt
        self.page_time += dt
        self.step_time += dt
        self.panel_time += dt

        if self.phase == "intro" and self.page_time >= self.INTRO_TIME:
            self._focus(0)

        if self.phase == "out":

            self.out_time += dt

            if self.out_time >= self.FADE_TIME:
                self._start_page(self.page + 1)

                return None

        overview = self.phase == "overview"

        for i in range(len(self.panels)):

            show = 1.0 if (i <= self.max_focus or overview) else 0.0

            lit = 1.0 if (i == self.focus or overview) else 0.0

            if self.phase == "out":
                show = 1.0
                lit = 1.0

            self.reveal[i] = self._approach(
                self.reveal[i],
                show,
                7.0,
                dt
            )

            self.focus_amt[i] = self._approach(
                self.focus_amt[i],
                lit,
                5.0,
                dt
            )

            self.flash[i] = max(0.0, self.flash[i] - dt * 1.8)

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

        self.shake *= math.exp(-dt * 3.5)

        if self.shake < 0.05:
            self.shake = 0.0

        self._update_particles(dt)

        return None

    def _ember_rate(self):

        if self.phase == "panel":
            return 9.0 * self.panels[self.focus]["embers"]

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

        alive = []

        for p in self.particles:

            p[4] -= dt

            if p[4] <= 0:
                continue

            p[0] += (p[2] + math.sin(p[4] * 2.5 + p[7]) * 14) * dt
            p[1] += p[3] * dt

            if p[1] < -10:
                continue

            alive.append(p)

        self.particles = alive

    def _compose_page(self):

        self.work.blit(self.source, (0, 0))

        for i, panel in enumerate(self.panels):

            rect = panel["rect"]

            r = self.reveal[i]
            f = self.focus_amt[i]

            alpha = self.HIDDEN_VEIL * (1 - r) + self.DIM_VEIL * r * (1 - f)

            if alpha > 1:

                panel["veil"].set_alpha(int(alpha))

                self.work.blit(panel["veil"], rect)

            if self.flash[i] > 0.01:

                v = int(255 * min(1.0, self.flash[i]) * 0.6)

                self.work.fill(
                    (v, v, v),
                    rect,
                    special_flags=pygame.BLEND_RGB_ADD
                )

            glow = panel["glow"]

            if glow and r > 0.5 and f > 0.05:

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

    def _draw_page(self):

        self._compose_page()

        k = self.cam_k

        ox = oy = 0.0

        if self.shake > 0:

            ox = random.uniform(-1, 1) * self.shake
            oy = random.uniform(-1, 1) * self.shake

        left = self.cam_x - (self.width / 2 + ox) / k
        top = self.cam_y - (self.height / 2 + oy) / k

        right = left + self.width / k
        bottom = top + self.height / k

        page_rect = pygame.Rect(
            round(-left * k),
            round(-top * k),
            round(self.pw * k),
            round(self.ph * k)
        )

        if page_rect.width < self.width or page_rect.height < self.height:

            self.screen.blit(
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

        self.screen.blit(
            scaled,
            (
                round((sl - left) * k),
                round((st - top) * k)
            )
        )

    def _draw_particles(self):

        for x, y, _, _, life, max_life, size, _ in self.particles:

            level = int(5 * (life / max_life))

            level = max(0, min(5, level))

            sprite = self.sprites[size][level]

            self.screen.blit(
                sprite,
                (round(x) - sprite.get_width() // 2, round(y) - sprite.get_height() // 2),
                special_flags=pygame.BLEND_RGB_ADD
            )

    def _draw_bars(self):

        t = min(1.0, self.total_time / 1.0)

        eased = 1 - (1 - t) ** 3

        height = round(self.bar_height * eased)

        if height <= 0:
            return None

        pygame.draw.rect(
            self.screen,
            (0, 0, 0),
            (0, 0, self.width, height)
        )

        pygame.draw.rect(
            self.screen,
            (0, 0, 0),
            (0, self.height - height, self.width, height)
        )

        if eased < 1.0:
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
                    self.screen,
                    (255, 190, 90),
                    pos,
                    max(4, gap // 3)
                )

            elif lit:

                pygame.draw.circle(
                    self.screen,
                    (200, 130, 60),
                    pos,
                    max(3, gap // 4)
                )

            else:

                pygame.draw.circle(
                    self.screen,
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

        self.screen.blit(
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

        self.screen.blit(
            hint,
            hint.get_rect(
                midright=(self.width - 18, center_y)
            )
        )

        return None

    def draw(self):

        self.screen.fill((12, 12, 16))

        self.screen.blit(self.background, (0, 0))

        self._draw_page()

        self._draw_particles()

        self.screen.blit(self.vignette, (0, 0))

        self._draw_bars()

        if self.phase == "out":

            fade = min(1.0, self.out_time / self.FADE_TIME)

        else:

            fade = max(0.0, 1.0 - self.page_time / self.FADE_TIME)

        if fade > 0.0:

            self.black.set_alpha(int(255 * fade))

            self.screen.blit(self.black, (0, 0))