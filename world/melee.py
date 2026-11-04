import math
from pathlib import Path

import pygame

from world.lights import light_stats


HUD_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "hud"
)


INNER_RADIUS = 11
OUTER_RADIUS = 26

ARC_DEGREES = 100

SWING_TIME = 0.20

COOLDOWN = 0.25

DAMAGE = 1

STICK_LENGTH = 14

TRAIL_DEGREES = 55

GLOW_TIME = 0.12

COMBO_KINDS = ("vela", "antorcha")
COMBO_HITS = 3
COMBO_WINDOW = 0.9
HEAVY_DAMAGE_MULT = 2

HEAVY_COLOR = (90, 170, 255)
HEAVY_CORE = (225, 245, 255)
HEAVY_RADIUS_MULT = 1.35
GLOW_TIME_HEAVY = 0.30
IMPACT_TIME = 0.35

# Calidad de la estela: se dibuja al doble de resolucion y se reduce con
# suavizado (sin bordes dentados), mas un resplandor difuso por detras.
TRAIL_SS = 2
TRAIL_SEGMENTS = 36

SPRITE_HEAD_ANGLE = -45
SPRITE_STICK_PX = 23

VELA_HEAD_ANGLE = -90
VELA_SPRITE_PX = 60
VELA_LENGTH = 15

ANTORCHA_HEAD_ANGLE = -50
ANTORCHA_SPRITE_PX = 74
ANTORCHA_LENGTH = 21


def arc_points(cx, cy, radius, a0, a1, steps=14):

    return [
        (
            cx + math.cos(a0 + (a1 - a0) * i / steps) * radius,
            cy + math.sin(a0 + (a1 - a0) * i / steps) * radius
        )
        for i in range(steps + 1)
    ]


def sector_outline(cx, cy, r_in, r_out, a0, a1):

    return (
        arc_points(cx, cy, r_out, a0, a1)
        + arc_points(cx, cy, r_in, a1, a0)
    )


def ease_out(t):

    return 1 - (1 - t) ** 3


class Melee:

    def __init__(self):

        self.aim = 0.0
        self.swinging = False
        self.t = 0.0
        self.cooldown = 0.0
        self.glow = 0.0
        self.glow_angle = 0.0
        self.glow_total = GLOW_TIME
        self.glow_heavy = False

        self.combo = 0
        self.combo_t = 0.0
        self.heavy = False

        self.impacts = []

        self.kind = "fosforo"
        self.cooldown_time = COOLDOWN

        self.fury_speed = 1.0

        self._hit_ids = set()

        self.final_pass = False

        self._sprite_zoom = None
        self._sprite = None


    @property
    def half_arc(self):

        return math.radians(ARC_DEGREES) / 2

    @property
    def start_angle(self):

        return self.aim - self.half_arc

    @property
    def end_angle(self):

        return self.aim + self.half_arc

    @property
    def current_angle(self):

        return self.start_angle + (
            self.end_angle - self.start_angle
        ) * ease_out(self.t)

    @property
    def damage(self):

        base = light_stats(self.kind).get("dano", DAMAGE)

        return base * HEAVY_DAMAGE_MULT if self.heavy else base

    def add_impact(self, pos):

        self.impacts.append([pos[0], pos[1], IMPACT_TIME])

    def set_light(self, kind):

        self.kind = kind
        self.cooldown_time = light_stats(kind)["cooldown"]
        self.fury_speed = 1.0
        self.combo = 0
        self.combo_t = 0.0
        self.heavy = False

        self._sprite_zoom = None

    def set_fury(self, speed):

        self.fury_speed = max(1.0, float(speed))

    @property
    def fury(self):

        return self.fury_speed > 1.0

    def _head_angle(self):

        if self.kind == "vela":
            return VELA_HEAD_ANGLE

        if self.kind == "antorcha":
            return ANTORCHA_HEAD_ANGLE

        return SPRITE_HEAD_ANGLE

    def can_attack(self):

        return not self.swinging and self.cooldown <= 0

    def start(self):

        if not self.can_attack():
            return False

        if self.kind in COMBO_KINDS:

            self.combo = self.combo + 1 if self.combo_t > 0 else 1
            self.heavy = self.combo >= COMBO_HITS

        else:

            self.combo = 0
            self.heavy = False

        self.swinging = True
        self.final_pass = False
        self.t = 0.0
        self.glow = 0.0
        self._hit_ids = set()

        return True

    def cancel(self):

        self.swinging = False
        self.final_pass = False
        self.glow = 0.0
        self.heavy = False
        self.combo = 0
        self.combo_t = 0.0

    def update(self, dt, pivot, mouse_world):

        self.final_pass = False

        if self.cooldown > 0:
            self.cooldown = max(0.0, self.cooldown - dt)

        if self.glow > 0:
            self.glow = max(0.0, self.glow - dt)

        if self.impacts:
            for imp in self.impacts:
                imp[2] -= dt
            self.impacts = [i for i in self.impacts if i[2] > 0]

        if not self.swinging and self.combo_t > 0:

            self.combo_t = max(0.0, self.combo_t - dt)

            if self.combo_t <= 0:
                self.combo = 0

        if not self.swinging:

            self.aim = math.atan2(
                mouse_world[1] - pivot[1],
                mouse_world[0] - pivot[0]
            )

            return

        self.t += dt * self.fury_speed / SWING_TIME

        if self.t >= 1.0:

            self.t = 1.0
            self.swinging = False

            self.final_pass = True

            self.cooldown = self.cooldown_time / self.fury_speed

            self.glow_heavy = self.heavy
            self.glow_total = GLOW_TIME_HEAVY if self.heavy else GLOW_TIME
            self.glow = self.glow_total
            self.glow_angle = self.end_angle

            if self.heavy:
                self.combo = 0
                self.combo_t = 0.0
            else:
                self.combo_t = COMBO_WINDOW


    def _rect_touched(self, rect, pivot, swept, arc):

        step = 3

        xs = list(range(rect.left, rect.right, step)) + [rect.right - 1]
        ys = list(range(rect.top, rect.bottom, step)) + [rect.bottom - 1]

        for x in xs:
            for y in ys:

                dx = x - pivot[0]
                dy = y - pivot[1]

                dist = math.hypot(dx, dy)

                if dist < INNER_RADIUS or dist > OUTER_RADIUS:
                    continue

                rel = (
                    math.atan2(dy, dx) - self.start_angle + math.pi
                ) % math.tau - math.pi

                if 0 <= rel <= min(swept, arc):
                    return True

        return False

    def new_hits(self, targets, pivot):

        if not self.swinging and not self.final_pass:
            return []

        swept = self.current_angle - self.start_angle
        arc = self.end_angle - self.start_angle

        hits = []

        for target in targets:

            if id(target) in self._hit_ids:
                continue

            if getattr(target, "precise_hit", False):

                if self._rect_touched(target.rect, pivot, swept, arc):

                    self._hit_ids.add(id(target))
                    hits.append(target)

                continue

            tx, ty = target.rect.center

            dx = tx - pivot[0]
            dy = ty - pivot[1]

            dist = math.hypot(dx, dy)

            size = max(target.rect.width, target.rect.height) / 2

            if dist < INNER_RADIUS - size or dist > OUTER_RADIUS + size:
                continue

            rel = (
                math.atan2(dy, dx) - self.start_angle + math.pi
            ) % math.tau - math.pi

            margin = size / max(dist, 1.0)

            if -margin <= rel <= min(swept, arc) + margin:

                self._hit_ids.add(id(target))
                hits.append(target)

        return hits


    def _get_sprite(self, zoom):

        if self._sprite_zoom != zoom:

            if self.kind == "vela":

                original = pygame.image.load(
                    str(HUD_DIR / "icon_vela.png")
                ).convert_alpha()

                scale = VELA_LENGTH / VELA_SPRITE_PX

            elif self.kind == "antorcha":

                original = pygame.image.load(
                    str(HUD_DIR / "icon_antorcha.png")
                ).convert_alpha()

                scale = ANTORCHA_LENGTH / ANTORCHA_SPRITE_PX

            else:

                original = pygame.image.load(
                    str(HUD_DIR / "item_fosforo.png")
                ).convert_alpha()

                scale = STICK_LENGTH / SPRITE_STICK_PX

            size = max(
                1,
                round(original.get_width() * scale * zoom)
            )

            self._sprite = pygame.transform.smoothscale(original, (size, size))
            self._sprite_zoom = zoom

        return self._sprite

    @staticmethod
    def _to_screen(camera, x, y):

        return (
            x * camera.zoom - camera.x,
            y * camera.zoom - camera.y
        )

    @staticmethod
    def _mix(c1, c2, k):

        return (
            int(c1[0] + (c2[0] - c1[0]) * k),
            int(c1[1] + (c2[1] - c1[1]) * k),
            int(c1[2] + (c2[2] - c1[2]) * k),
        )

    def _trail_palette(self, heavy):

        # El golpe fuerte (el 3ro del combo) es AZUL tambien en furia.
        if heavy:
            return HEAVY_COLOR, HEAVY_CORE, (35, 95, 235)

        if self.fury:
            return (255, 105, 40), (255, 235, 175), (205, 40, 25)

        if self.kind == "antorcha":
            return (255, 150, 45), (255, 240, 180), (220, 80, 20)

        return (255, 195, 100), (255, 250, 220), (240, 140, 50)

    def _draw_trail(self, screen, camera, pivot, angle, strength,
                    heavy=False):

        zoom = camera.zoom
        ss = TRAIL_SS

        outer = OUTER_RADIUS * (HEAVY_RADIUS_MULT if heavy else 1.0)

        pad = int(8 * zoom)

        size = int(outer * 2 * zoom) + 4 + pad * 2
        big = size * ss
        center = big / 2

        trail = math.radians(TRAIL_DEGREES * (1.2 if heavy else 1.0))

        back = max(self.start_angle, angle - trail)

        segments = TRAIL_SEGMENTS

        color, core, deep = self._trail_palette(heavy)
        mid = self._mix(color, core, 0.55)

        r_in = (INNER_RADIUS + 2) * zoom * ss
        r_out = outer * zoom * ss

        # ---- resplandor difuso (baja resolucion + agrandado = blur) ----
        glow_size = max(8, size // 2)
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        g_center = glow_size / 2
        g_scale = glow_size / big

        halo_out = r_out + 7 * zoom * ss
        halo_in = r_in - 2 * zoom * ss

        for i in range(segments):

            a0 = back + (angle - back) * i / segments
            a1 = back + (angle - back) * (i + 1) / segments + 0.02

            t = (i + 1) / segments

            alpha = int((120 if heavy else 95) * strength * t ** 1.7)

            if alpha <= 0:
                continue

            pts = (
                arc_points(g_center, g_center, halo_out * g_scale, a0, a1, 2)
                + arc_points(g_center, g_center, halo_in * g_scale, a1, a0, 2)
            )

            pygame.draw.polygon(glow, (*color, alpha), pts)

        tiny = pygame.transform.smoothscale(
            glow, (max(2, glow_size // 3), max(2, glow_size // 3))
        )
        glow = pygame.transform.smoothscale(tiny, (size, size))

        # ---- cuerpo de la estela (alta resolucion) ----
        layer = pygame.Surface((big, big), pygame.SRCALPHA)

        for i in range(segments):

            a0 = back + (angle - back) * i / segments
            a1 = back + (angle - back) * (i + 1) / segments + 0.02

            t = (i + 1) / segments

            alpha = int((245 if heavy else 205) * strength * t ** 1.4)

            if alpha <= 0:
                continue

            thick = 0.26 + 0.74 * t ** 0.8
            seg_in = r_out - (r_out - r_in) * thick
            width = r_out - seg_in

            bands = (
                (0.00, deep, 0.55),
                (0.22, color, 1.00),
                (0.55, mid, 1.00),
                (0.80, core, 0.95),
            )

            for start, band_color, mult in bands:

                inner = seg_in + width * start

                pts = (
                    arc_points(center, center, r_out, a0, a1, 3)
                    + arc_points(center, center, inner, a1, a0, 3)
                )

                pygame.draw.polygon(
                    layer, (*band_color, int(alpha * mult)), pts
                )

        # borde delantero brillante
        edge = [
            (center + math.cos(back + (angle - back) * k / 28) * r_out,
             center + math.sin(back + (angle - back) * k / 28) * r_out)
            for k in range(29)
        ]

        pygame.draw.lines(
            layer, (*core, int(215 * strength)), False, edge,
            max(1, round(zoom * 0.6 * ss))
        )

        # punta: destello con degradado
        tip_x = center + math.cos(angle) * r_out * 0.94
        tip_y = center + math.sin(angle) * r_out * 0.94

        for rad, a in ((11, 40), (8, 85), (5, 150), (2.6, 245)):

            pygame.draw.circle(
                layer, (*core, int(a * strength)),
                (round(tip_x), round(tip_y)),
                max(2, round(rad * zoom * 0.5 * ss))
            )

        if heavy:

            tip_a = int(255 * strength)

            pygame.draw.line(
                layer,
                (*HEAVY_CORE, tip_a),
                (center + math.cos(angle) * r_in,
                 center + math.sin(angle) * r_in),
                (center + math.cos(angle) * r_out,
                 center + math.sin(angle) * r_out),
                max(2, round(2 * zoom * ss)),
            )

            # destello en cruz en la punta
            flare = 9 * zoom * ss

            for da in (0.0, math.pi / 2):

                pygame.draw.line(
                    layer,
                    (*HEAVY_CORE, int(200 * strength)),
                    (tip_x - math.cos(angle + da) * flare,
                     tip_y - math.sin(angle + da) * flare),
                    (tip_x + math.cos(angle + da) * flare,
                     tip_y + math.sin(angle + da) * flare),
                    max(1, round(zoom * ss * 0.8)),
                )

        body = pygame.transform.smoothscale(layer, (size, size))

        glow.blit(body, (0, 0))

        px, py = self._to_screen(camera, pivot[0], pivot[1])

        screen.blit(glow, glow.get_rect(center=(round(px), round(py))))

    def draw(self, screen, camera, pivot):

        self._draw_impacts(screen, camera)

        if self.swinging:

            angle = self.current_angle

            self._draw_trail(
                screen, camera, pivot, angle, 1.0, self.heavy
            )

            sprite = pygame.transform.rotozoom(
                self._get_sprite(camera.zoom),
                self._head_angle() - math.degrees(angle),
                1.0
            )

            distance = INNER_RADIUS + STICK_LENGTH / 2 + 2

            px, py = self._to_screen(
                camera,
                pivot[0] + math.cos(angle) * distance,
                pivot[1] + math.sin(angle) * distance
            )

            if self.heavy or self.fury:

                if self.heavy:
                    outer_c, inner_c = HEAVY_COLOR, HEAVY_CORE
                else:
                    outer_c, inner_c = (255, 120, 40), (255, 225, 160)

                radius = round(12 * camera.zoom)

                halo = pygame.Surface(
                    (radius * 2, radius * 2), pygame.SRCALPHA
                )

                for k in range(5, 0, -1):

                    pygame.draw.circle(
                        halo, (*outer_c, 22 + 14 * (5 - k)),
                        (radius, radius), max(2, radius * k // 5)
                    )

                pygame.draw.circle(
                    halo, (*inner_c, 130), (radius, radius),
                    max(2, radius // 3)
                )

                screen.blit(
                    halo,
                    halo.get_rect(center=(round(px), round(py)))
                )

            screen.blit(
                sprite,
                sprite.get_rect(center=(round(px), round(py)))
            )

        elif self.glow > 0:

            self._draw_trail(
                screen,
                camera,
                pivot,
                self.glow_angle,
                self.glow / self.glow_total,
                self.glow_heavy,
            )

    def _draw_impacts(self, screen, camera):

        for x, y, t in self.impacts:

            k = 1.0 - t / IMPACT_TIME

            radius = max(2, round((5 + 16 * k) * camera.zoom))

            alpha = int(230 * (1.0 - k))

            layer = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)

            c = radius + 4

            pygame.draw.circle(
                layer, (*HEAVY_COLOR, alpha), (c, c), radius,
                max(2, round(1.5 * camera.zoom))
            )

            pygame.draw.circle(
                layer, (*HEAVY_CORE, int(alpha * 0.6)), (c, c),
                max(1, int(radius * 0.6)),
                max(1, round(camera.zoom * 0.8))
            )

            for i in range(8):

                a = math.tau * i / 8 + k

                pygame.draw.line(
                    layer,
                    (*HEAVY_CORE, alpha),
                    (c + math.cos(a) * radius * 0.5,
                     c + math.sin(a) * radius * 0.5),
                    (c + math.cos(a) * radius,
                     c + math.sin(a) * radius),
                    max(1, round(camera.zoom * 0.7)),
                )

            sx, sy = self._to_screen(camera, x, y)

            screen.blit(layer, layer.get_rect(center=(round(sx), round(sy))))

    def draw_debug(self, screen, camera, pivot):

        zoom = camera.zoom

        px, py = self._to_screen(camera, pivot[0], pivot[1])

        outline = sector_outline(
            px, py,
            INNER_RADIUS * zoom, OUTER_RADIUS * zoom,
            self.start_angle, self.end_angle
        )

        pygame.draw.polygon(screen, (255, 130, 30), outline, 3)

        pygame.draw.line(
            screen,
            (235, 30, 40),
            (px + math.cos(self.aim) * INNER_RADIUS * zoom,
             py + math.sin(self.aim) * INNER_RADIUS * zoom),
            (px + math.cos(self.aim) * OUTER_RADIUS * zoom,
             py + math.sin(self.aim) * OUTER_RADIUS * zoom),
            2
        )

        if self.swinging:

            a = self.current_angle

            pygame.draw.line(
                screen,
                (235, 30, 40),
                (px + math.cos(a) * INNER_RADIUS * zoom,
                 py + math.sin(a) * INNER_RADIUS * zoom),
                (px + math.cos(a) * OUTER_RADIUS * zoom,
                 py + math.sin(a) * OUTER_RADIUS * zoom),
                5
            )


class TrainingDummy:

    def __init__(self, x, y, hp=5):

        self.rect = pygame.Rect(0, 0, 10, 10)
        self.rect.center = (x, y)

        self.hp = hp
        self.max_hp = hp
        self.flash = 0.0

    @property
    def dead(self):

        return self.hp <= 0

    def take_damage(self, amount):

        self.hp -= amount
        self.flash = 0.15

    def update(self, dt):

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

    def draw(self, screen, camera):

        dest = camera.apply(self.rect)

        color = (255, 255, 255) if self.flash > 0 else (150, 105, 70)

        pygame.draw.ellipse(screen, color, dest)
        pygame.draw.ellipse(screen, (50, 35, 25), dest, 3)

        bar = pygame.Rect(0, 0, dest.width, 6)
        bar.midbottom = (dest.centerx, dest.top - 6)

        pygame.draw.rect(screen, (40, 20, 20), bar)

        fill = bar.copy()
        fill.width = max(0, round(bar.width * self.hp / self.max_hp))

        pygame.draw.rect(screen, (220, 70, 60), fill)