import math
import random

import pygame

_GLOW_STEPS = (3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96)

COIN_COLORS = {
    1: (255, 215, 90),
    5: (110, 190, 255),
    10: (255, 105, 90),
}


def _step(radius):
    for s in _GLOW_STEPS:
        if radius <= s:
            return s
    return _GLOW_STEPS[-1]


class FxManager:

    def __init__(self):

        self.particles = []
        self.rings = []
        self.popups = []
        self.pulses = []
        self.queue = []

        self.hitstop = 0.0
        self.hurt_t = 0.0

        self.flash_t = 0.0
        self.flash_dur = 0.0
        self.flash_color = (255, 220, 160)

        self.shake_t = 0.0
        self.shake_dur = 0.0
        self.shake_amp = 0.0

        self.title = None
        self.vignette_t = 0.0

        self._glow_cache = {}
        self._ring_cache = {}
        self._fonts = {}
        self._emit_acc = {}


    def _font(self, size):

        font = self._fonts.get(size)

        if font is None:
            font = pygame.font.Font(None, size)
            self._fonts[size] = font

        return font

    def glow_sprite(self, radius, color):

        radius = _step(max(2, int(radius)))
        key = (radius, color)

        spr = self._glow_cache.get(key)

        if spr is None:

            size = radius * 2
            spr = pygame.Surface((size, size))
            spr.fill((0, 0, 0))

            for r in range(radius, 0, -1):

                t = 1.0 - r / radius
                k = t * t

                pygame.draw.circle(
                    spr,
                    (int(color[0] * k), int(color[1] * k), int(color[2] * k)),
                    (radius, radius), r
                )

            self._glow_cache[key] = spr

        return spr

    def _ring_sprite(self, radius, color):

        radius = max(8, int(round(radius / 8)) * 8)
        key = (radius, color)

        spr = self._ring_cache.get(key)

        if spr is None:

            if len(self._ring_cache) > 40:
                self._ring_cache.clear()

            pad = 14
            size = radius * 2 + pad * 2
            c = size // 2

            spr = pygame.Surface((size, size), pygame.SRCALPHA)

            band = int(min(radius * 0.35, 46))

            for k in range(band, 0, -1):

                a = int(70 * (1 - k / band) ** 2)

                pygame.draw.circle(
                    spr, (*color, a), (c, c), radius - k + 1, 2
                )

            for k in range(1, pad):

                a = int(150 * (1 - k / pad) ** 2)

                pygame.draw.circle(
                    spr, (*color, a), (c, c), radius + k, 2
                )

            pygame.draw.circle(spr, (*color, 235), (c, c), radius, 3)

            white = tuple(min(255, v + 90) for v in color)
            pygame.draw.circle(spr, (*white, 200), (c, c), radius, 1)

            self._ring_cache[key] = spr

        return spr


    def _spark(self, x, y, angle, speed, life, color, size=2.0, drag=3.0,
               grav=0.0, delay=0.0, streak=False):

        self.particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": life, "max": life,
            "color": color, "size": size,
            "drag": drag, "grav": grav,
            "delay": delay, "streak": streak,
        })

        if len(self.particles) > 700:
            del self.particles[:100]

    def _ring(self, x, y, r0, r1, dur, color, width=3, delay=0.0):

        self.rings.append({
            "x": x, "y": y, "r0": r0, "r1": r1,
            "t": -delay, "dur": dur, "color": color, "width": width,
        })

    def hit(self, x, y, angle=None, heavy=False, color=None, fury=False):

        if color is None:
            color = (190, 110, 255) if heavy else (255, 190, 80)

        core = (255, 245, 220) if not heavy else (255, 235, 255)
        hot = (255, 120, 40) if not heavy else (140, 70, 255)

        base = angle if angle is not None else random.uniform(0, math.tau)

        n = 26 if heavy else 15

        if fury:
            n = 14
        spread = math.pi * (1.3 if heavy else 0.85)

        for _ in range(n):

            a = base + random.uniform(-spread / 2, spread / 2)
            sp = random.uniform(90, 300 if heavy else 220)

            self._spark(
                x, y, a, sp, random.uniform(0.2, 0.5),
                random.choice((color, core, hot)),
                size=random.uniform(1.5, 3.0), drag=3.2, streak=True,
            )

        for i in range(3 if fury else (7 if heavy else 4)):

            a = base + random.uniform(-0.6, 0.6)

            self._spark(
                x, y, a, random.uniform(260, 420), 0.16,
                core, size=2.4, drag=6.0, streak=True,
            )

        for _ in range(2 if fury else (8 if heavy else 4)):

            a = base + random.uniform(-1.4, 1.4)

            self._spark(
                x, y, a, random.uniform(40, 120), random.uniform(0.35, 0.7),
                hot, size=random.uniform(1.8, 3.0), drag=2.0, grav=260,
            )

        self._spark(x, y, 0, 0, 0.16, core, size=22 if heavy else 15, drag=0)
        self._spark(x, y, 0, 0, 0.30, color, size=30 if heavy else 20, drag=0)

        self._ring(x, y, 3, 30 if heavy else 20, 0.26, core, 3)

        self._ring(x, y, 2, 46 if heavy else 30, 0.38, color, 2, delay=0.04)

        if fury:
            return

        self.hitstop = max(self.hitstop, 0.085 if heavy else 0.04)

        self.shake(5.0 if heavy else 2.0, 0.2 if heavy else 0.11)

    def swing_sparks(self, x, y, angle, heavy=False, fury=False):

        if heavy:
            colors = ((200, 110, 255), (255, 235, 255))
        elif fury:
            colors = ((255, 110, 45), (255, 210, 120))
        else:
            colors = ((255, 195, 100), (255, 245, 210))

        for _ in range(1 if fury else (3 if heavy else 2)):

            a = angle - math.pi / 2 + random.uniform(-0.9, 0.9)

            self._spark(
                x, y, a, random.uniform(25, 90), random.uniform(0.18, 0.4),
                random.choice(colors), size=random.uniform(1.4, 2.6),
                drag=3.0, streak=True,
            )

    def player_hurt(self, x, y):

        self.hurt_t = 0.45
        self.shake(3.0, 0.18)

        for _ in range(10):

            self._spark(
                x, y - 4, random.uniform(0, math.tau),
                random.uniform(40, 120), random.uniform(0.25, 0.5),
                random.choice(((255, 60, 50), (255, 130, 110))),
                size=random.uniform(1.6, 2.6), drag=3.0, streak=True,
            )

        self._ring(x, y, 3, 22, 0.3, (255, 70, 60), 2)

    @staticmethod
    def item_color(item):

        value = int(getattr(item, "value", 1) or 1)

        if item.item_id in ("gema", "gema_verde"):
            return (120, 210, 255) if item.item_id == "gema" else (110, 255, 160)

        if item.item_id.startswith("moneda"):
            return COIN_COLORS.get(
                10 if value >= 10 else 5 if value >= 5 else 1
            )

        return (150, 200, 255)

    def draw_item_glow(self, screen, camera, item, t):

        f = getattr(item, "fly", None)

        if f is not None:
            return

        color = self.item_color(item)

        pulse = 0.65 + 0.35 * math.sin(t * 5 + item.rect.x * 0.37)

        radius = int((9 + 2 * pulse) * camera.zoom)

        spr = self.glow_sprite(radius, tuple(int(v * pulse) for v in color))

        sx = int(item.rect.centerx * camera.zoom - camera.x)
        sy = int(item.rect.centery * camera.zoom - camera.y)

        screen.blit(
            spr, spr.get_rect(center=(sx, sy + int(2 * camera.zoom))),
            special_flags=pygame.BLEND_RGB_ADD
        )

    def coin(self, x, y, value=1):

        value = int(value)

        color = COIN_COLORS.get(
            10 if value >= 10 else 5 if value >= 5 else 1
        )

        white = (255, 255, 235)

        for _ in range(8 + min(8, value)):

            a = -math.pi / 2 + random.uniform(-1.3, 1.3)

            self._spark(
                x, y - 2, a, random.uniform(35, 110),
                random.uniform(0.35, 0.7),
                random.choice((color, white)),
                size=random.uniform(1.5, 2.6),
                drag=2.5, grav=140,
            )

        self._spark(x, y, 0, 0, 0.18, color, size=10, drag=0)
        self._ring(x, y, 2, 16, 0.3, color, 2)

        self.popups.append({
            "x": x, "y": y - 8, "text": f"+{value}",
            "t": 0.0, "dur": 0.9, "color": color,
        })

    def wave_start(self, cx, cy, wave, room=None, enemy_positions=()):

        reach = 190

        if room is not None:
            reach = int(max(room.width, room.height) * 0.6)

        for i in range(3):
            self._ring(cx, cy, 8, reach, 0.9 + i * 0.12,
                       (255, 120, 60) if i else (255, 230, 170),
                       5 - i, delay=i * 0.12)

        for _ in range(40):

            a = random.uniform(0, math.tau)

            self._spark(
                cx, cy, a, random.uniform(80, 230),
                random.uniform(0.5, 1.0),
                random.choice(((255, 140, 60), (255, 210, 120),
                               (255, 255, 255))),
                size=random.uniform(1.8, 3.2), drag=2.2,
            )

        for k, (ex, ey) in enumerate(enemy_positions):

            d = 0.15 * k

            self._ring(ex, ey, 2, 20, 0.45, (255, 80, 60), 2, delay=d)

            for _ in range(5):
                self._spark(
                    ex, ey, random.uniform(0, math.tau),
                    random.uniform(20, 60), random.uniform(0.3, 0.6),
                    (255, 90, 70), size=2.0, drag=3.0, delay=d,
                )

        self.shake(5.0, 0.45)
        self.vignette_t = 1.4
        self.title = [0.0, f"OLEADA {wave}", (255, 225, 150)]

    def flash(self, dur, color=(255, 255, 255), strength=1.0):

        self.flash_t = dur
        self.flash_dur = dur
        self.flash_color = color
        self._flash_strength = strength

    def shake(self, amp, dur):

        if amp >= self.shake_amp * (self.shake_t / max(0.001, self.shake_dur)):
            self.shake_amp = amp
            self.shake_t = dur
            self.shake_dur = dur

    def pulse(self, name):

        self.pulses.append([0.0, name])

    def emit_aura(self, name, wx, wy, radius_world, color, dt, rate=18.0,
                  inward=False):

        acc = self._emit_acc.get(name, 0.0) + dt * rate

        while acc >= 1.0:

            acc -= 1.0

            a = random.uniform(0, math.tau)
            r = radius_world * random.uniform(0.9, 1.02)

            px = wx + math.cos(a) * r
            py = wy + math.sin(a) * r

            if inward:
                # nacen en el borde y caen hacia el centro, rapido
                vx, vy = -math.cos(a) * 95, -math.sin(a) * 95
            else:
                vx, vy = random.uniform(-8, 8), random.uniform(-45, -15)

            self.particles.append({
                "x": px, "y": py, "vx": vx, "vy": vy,
                "life": random.uniform(0.5, 1.0), "max": 1.0,
                "color": color, "size": random.uniform(1.5, 2.6),
                "drag": 1.0, "grav": 0.0, "delay": 0.0,
            })

        self._emit_acc[name] = acc


    # ---------- iman ----------

    def magnet_grab(self, x, y, color):

        # el objeto "despierta": un destello chico y chispas hacia arriba
        self._spark(x, y, 0, 0, 0.16, color, size=7, drag=0)

        for _ in range(4):

            self._spark(
                x, y, -math.pi / 2 + random.uniform(-0.9, 0.9),
                random.uniform(30, 70), random.uniform(0.2, 0.4),
                color, size=1.6, drag=3.0
            )

    def magnet_absorb(self, x, y, color):

        # al llegar al jugador: ondas y chispas que salen disparadas
        white = (235, 245, 255)

        self._spark(x, y, 0, 0, 0.2, white, size=11, drag=0)

        for i in range(9):

            a = math.tau * i / 9 + random.uniform(-0.25, 0.25)

            self._spark(
                x, y, a, random.uniform(70, 150), random.uniform(0.22, 0.4),
                random.choice((color, white, (120, 190, 255))),
                size=random.uniform(1.4, 2.4), drag=4.5, streak=True
            )

    def draw_magnet_field(self, screen, cx, cy, radius, phase, strength=1.0):

        # anillos que se achican hacia el jugador + arcos que giran:
        # se ve como un campo que succiona hacia adentro
        if radius < 12:
            return

        size = int(radius * 2 + 16)
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2

        for i in range(3):

            k = (phase * 0.9 + i / 3.0) % 1.0

            rr = int(radius * (1.0 - k * 0.92))

            if rr < 4:
                continue

            alpha = int(150 * math.sin(math.pi * k) ** 1.5 * strength)

            pygame.draw.circle(
                layer, (120, 190, 255, alpha), (c, c), rr,
                max(1, int(2 * (1.0 - k) + 1))
            )

        for i in range(4):

            a0 = phase * 2.2 + i * math.pi / 2

            rect = pygame.Rect(0, 0, radius * 2 - 6, radius * 2 - 6)
            rect.center = (c, c)

            pygame.draw.arc(
                layer, (200, 230, 255, int(170 * strength)), rect,
                a0, a0 + 0.55, 3
            )
            pygame.draw.arc(
                layer, (110, 175, 255, int(90 * strength)), rect,
                a0 - 0.35, a0, 2
            )

        screen.blit(
            layer, layer.get_rect(center=(int(cx), int(cy))),
        )

    def draw_magnet_pull(self, screen, camera, items, player_pos):

        # estela de cada objeto que esta siendo atraido
        z = camera.zoom

        for item in items:

            trail = getattr(item, "_mag_trail", None)

            if not trail or getattr(item, "_mag_t", 0) <= 0:
                continue

            color = self.item_color(item)

            n = len(trail)

            for i, (tx, ty) in enumerate(trail):

                k = (i + 1) / (n + 1)

                rad = max(3, int((3 + 6 * k) * z))

                tint = tuple(int(v * k * 0.8) for v in color)

                spr = self.glow_sprite(rad, tint)

                sx = int(tx * z - camera.x)
                sy = int(ty * z - camera.y)

                screen.blit(
                    spr, spr.get_rect(center=(sx, sy)),
                    special_flags=pygame.BLEND_RGB_ADD
                )

            # hilito de luz entre el objeto y el jugador
            ix, iy = item.rect.center
            px, py = player_pos

            d = math.hypot(px - ix, py - iy)

            if d > 14:

                a = min(1.0, getattr(item, "_mag_t", 0) / 0.25)

                sx = int(ix * z - camera.x)
                sy = int(iy * z - camera.y)

                # punta del hilo: un poco hacia el jugador
                ex = sx + int((px - ix) / d * 14 * z)
                ey = sy + int((py - iy) / d * 14 * z)

                pygame.draw.line(
                    screen, tuple(int(v * 0.55 * a) for v in color),
                    (sx, sy), (ex, ey), max(1, int(z))
                )

    def update(self, dt):

        for p in self.particles:

            if p["delay"] > 0:
                p["delay"] -= dt
                continue

            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt

            k = max(0.0, 1 - p["drag"] * dt)
            p["vx"] *= k
            p["vy"] = p["vy"] * k + p["grav"] * dt

        self.particles = [p for p in self.particles if p["life"] > 0]

        for r in self.rings:
            r["t"] += dt

        self.rings = [r for r in self.rings if r["t"] < r["dur"]]

        for p in self.popups:
            p["t"] += dt

        self.popups = [p for p in self.popups if p["t"] < p["dur"]]

        for p in self.pulses:
            p[0] += dt

        self.pulses = [p for p in self.pulses if p[0] < 0.6]

        if self.flash_t > 0:
            self.flash_t = max(0.0, self.flash_t - dt)

        if self.shake_t > 0:
            self.shake_t = max(0.0, self.shake_t - dt)

        if self.hurt_t > 0:
            self.hurt_t = max(0.0, self.hurt_t - dt)

        if self.vignette_t > 0:
            self.vignette_t = max(0.0, self.vignette_t - dt)

        if self.title is not None:

            self.title[0] += dt

            if self.title[0] > 1.8:
                self.title = None

    def shake_offset(self):

        if self.shake_t <= 0:
            return 0, 0

        k = self.shake_t / max(0.001, self.shake_dur)
        a = self.shake_amp * k

        return (
            int(random.uniform(-a, a)),
            int(random.uniform(-a, a)),
        )


    def draw(self, screen, camera):

        z = camera.zoom
        sw, sh = screen.get_size()

        for r in self.rings:

            if r["t"] < 0:
                continue

            k = r["t"] / r["dur"]
            e = 1 - (1 - k) ** 3

            radius = int((r["r0"] + (r["r1"] - r["r0"]) * e) * z)
            alpha = int(255 * (1 - k))

            if radius < 2 or alpha <= 0:
                continue

            sx = int(r["x"] * z - camera.x)
            sy = int(r["y"] * z - camera.y)

            if sx + radius < 0 or sx - radius > sw \
                    or sy + radius < 0 or sy - radius > sh:
                continue

            layer = pygame.Surface(
                (radius * 2 + 12, radius * 2 + 12), pygame.SRCALPHA
            )

            c = radius + 6

            width = max(1, int(r["width"] * (1 - k) * z * 0.5) + 1)

            pygame.draw.circle(
                layer, (*r["color"], alpha), (c, c), radius, width
            )

            screen.blit(layer, layer.get_rect(center=(sx, sy)))

        for p in self.particles:

            if p["delay"] > 0:
                continue

            a = max(0.0, p["life"] / p["max"])

            sx = int(p["x"] * z - camera.x)
            sy = int(p["y"] * z - camera.y)

            if sx < -40 or sx > sw + 40 or sy < -40 or sy > sh + 40:
                continue

            rad = max(2, int(p["size"] * z * (0.4 + 0.6 * a) * 1.6))

            spr = self.glow_sprite(rad * 2, tuple(
                int(v * (0.35 + 0.65 * a)) for v in p["color"]
            ))

            screen.blit(
                spr, spr.get_rect(center=(sx, sy)),
                special_flags=pygame.BLEND_RGB_ADD
            )

            if p.get("streak"):

                tx = sx - int(p["vx"] * 0.045 * z)
                ty = sy - int(p["vy"] * 0.045 * z)

                pygame.draw.line(
                    screen, p["color"], (sx, sy), (tx, ty),
                    max(1, int(p["size"] * a * z * 0.35))
                )

            pygame.draw.circle(
                screen, p["color"], (sx, sy), max(1, int(p["size"] * z * 0.5 * a + 1))
            )

        for p in self.popups:

            k = p["t"] / p["dur"]

            sx = int(p["x"] * z - camera.x)
            sy = int((p["y"] - 14 * k) * z - camera.y)

            font = self._font(max(18, int(7 * z)))

            txt = font.render(p["text"], True, p["color"])
            shade = font.render(p["text"], True, (20, 10, 0))

            alpha = int(255 * (1 - max(0.0, (k - 0.6) / 0.4)))

            txt.set_alpha(alpha)
            shade.set_alpha(alpha)

            screen.blit(shade, shade.get_rect(center=(sx + 2, sy + 2)))
            screen.blit(txt, txt.get_rect(center=(sx, sy)))

    def draw_aura(self, screen, name, cx, cy, radius, color, phase,
                  strength=1.0):

        if radius < 8:
            return

        pulse = 0.5 + 0.5 * math.sin(phase * 5)

        spr = self._ring_sprite(radius, color)

        spr.set_alpha(int((150 + 90 * pulse) * strength))

        screen.blit(spr, spr.get_rect(center=(int(cx), int(cy))))

        for t, n in self.pulses:

            if n != name:
                continue

            k = t / 0.6
            rr = int(radius * (0.15 + 0.85 * k))

            if rr < 3:
                continue

            layer = pygame.Surface((rr * 2 + 8, rr * 2 + 8), pygame.SRCALPHA)

            pygame.draw.circle(
                layer, (*color, int(160 * (1 - k) * strength)),
                (rr + 4, rr + 4), rr, 3
            )

            screen.blit(layer, layer.get_rect(center=(int(cx), int(cy))))

    def draw_overlay(self, screen):

        sw, sh = screen.get_size()

        if self.flash_t > 0:

            k = self.flash_t / max(0.001, self.flash_dur)

            layer = pygame.Surface((sw, sh))
            layer.fill(tuple(
                int(v * k * getattr(self, "_flash_strength", 1.0))
                for v in self.flash_color
            ))

            screen.blit(layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        if self.hurt_t > 0:

            k = min(1.0, self.hurt_t / 0.45)

            vig = pygame.Surface((sw, sh), pygame.SRCALPHA)

            for i in range(12):

                a = int(150 * k * (1 - i / 12) ** 2)

                pygame.draw.rect(
                    vig, (220, 20, 20, a),
                    pygame.Rect(i * 5, i * 5, sw - i * 10, sh - i * 10), 5
                )

            screen.blit(vig, (0, 0))

        if self.vignette_t > 0:

            k = min(1.0, self.vignette_t / 1.4)

            vig = pygame.Surface((sw, sh), pygame.SRCALPHA)

            steps = 14

            for i in range(steps):

                a = int(70 * k * (1 - i / steps) ** 2)

                pygame.draw.rect(
                    vig, (200, 20, 10, a),
                    pygame.Rect(i * 6, i * 6, sw - i * 12, sh - i * 12), 6
                )

            screen.blit(vig, (0, 0))

        if self.title is not None:

            t, text, color = self.title

            if t < 0.25:
                alpha = t / 0.25
                scale = 1.6 - 0.6 * (t / 0.25)
            elif t > 1.4:
                alpha = max(0.0, 1 - (t - 1.4) / 0.4)
                scale = 1.0
            else:
                alpha = 1.0
                scale = 1.0 + 0.03 * math.sin(t * 6)

            font = self._font(96)

            txt = font.render(text, True, color)
            shade = font.render(text, True, (30, 8, 0))

            w = max(1, int(txt.get_width() * scale))
            h = max(1, int(txt.get_height() * scale))

            txt = pygame.transform.smoothscale(txt, (w, h))
            shade = pygame.transform.smoothscale(shade, (w, h))

            txt.set_alpha(int(255 * alpha))
            shade.set_alpha(int(255 * alpha))

            pos = (sw // 2, int(sh * 0.22))

            screen.blit(shade, shade.get_rect(center=(pos[0] + 4, pos[1] + 4)))
            screen.blit(txt, txt.get_rect(center=pos))