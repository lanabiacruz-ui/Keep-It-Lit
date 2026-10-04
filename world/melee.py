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

# ---------------------------------------------------------------
# Area de ataque (la zona naranja del dibujo)
# Todo en unidades del mundo, igual que el resto de coordenadas.
# ---------------------------------------------------------------

# Donde empieza el area (el borde del cuerpo) y hasta donde llega.
# Ojo: el personaje se dibuja chico (74 px de alto en pantalla) aunque
# el mundo tenga zoom x4, asi que estos numeros son bastante menores
# que el tamano del sprite en unidades del mundo.
# 11 -> 44 px en pantalla, 26 -> 104 px (casi lo que alumbra la luz).
INNER_RADIUS = 11
OUTER_RADIUS = 26

# Que tan ancha es el area, en grados (centrada en el mouse)
ARC_DEGREES = 100

# Cuanto dura el golpe (el fosforo pasa de un borde al otro)
SWING_TIME = 0.20

# Espera despues del golpe antes de poder volver a pegar
COOLDOWN = 0.25

# Cuanto sacan los golpes
DAMAGE = 1

# Largo del fosforo dibujado, en unidades del mundo
STICK_LENGTH = 14

# Cuanto de la estela (en grados) queda atras del fosforo
TRAIL_DEGREES = 55

# Cuanto tarda en apagarse la estela cuando termina el golpe
GLOW_TIME = 0.12

# El sprite item_fosforo.png (32x32) tiene la cabeza hacia arriba a la
# derecha (-45 grados en pantalla) y el palito mide unos 23 px.
SPRITE_HEAD_ANGLE = -45
SPRITE_STICK_PX = 23

# La vela (icon_vela.png, 64x64): la llama apunta hacia arriba (-90
# grados en pantalla) y la vela entera mide unos 60 px de alto. Se
# dibuja de VELA_LENGTH unidades del mundo.
VELA_HEAD_ANGLE = -90
VELA_SPRITE_PX = 60
VELA_LENGTH = 15


def arc_points(cx, cy, radius, a0, a1, steps=14):
    """Puntos de un arco de circulo de a0 a a1 (radianes)."""

    return [
        (
            cx + math.cos(a0 + (a1 - a0) * i / steps) * radius,
            cy + math.sin(a0 + (a1 - a0) * i / steps) * radius
        )
        for i in range(steps + 1)
    ]


def sector_outline(cx, cy, r_in, r_out, a0, a1):
    """Contorno del area: arco de afuera de a0 a a1 y arco de adentro
    de vuelta (los dos bordes rectos quedan unidos solos)."""

    return (
        arc_points(cx, cy, r_out, a0, a1)
        + arc_points(cx, cy, r_in, a1, a0)
    )


def ease_out(t):
    """Arranca rapido y frena al final: un golpe con fuerza."""

    return 1 - (1 - t) ** 3


class Melee:

    def __init__(self):

        self.aim = 0.0            # angulo hacia el mouse (radianes)
        self.swinging = False
        self.t = 0.0              # progreso del golpe, 0 a 1
        self.cooldown = 0.0
        self.glow = 0.0
        self.glow_angle = 0.0

        # Que luz se esta usando para pegar y cuanto espera entre golpes
        self.kind = "fosforo"
        self.cooldown_time = COOLDOWN

        # Furia (vela): cuantas veces mas rapido pega. 1.0 = normal
        self.fury_speed = 1.0

        self._hit_ids = set()

        self._sprite_zoom = None
        self._sprite = None

    # ---------- estado ----------

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
        """Donde esta el fosforo ahora mismo."""

        return self.start_angle + (
            self.end_angle - self.start_angle
        ) * ease_out(self.t)

    @property
    def damage(self):

        return DAMAGE

    def set_light(self, kind):
        """Cambia la luz con la que se pega (fosforo, vela...): cambia
        el sprite del golpe y la espera entre golpes."""

        self.kind = kind
        self.cooldown_time = light_stats(kind)["cooldown"]
        self.fury_speed = 1.0

        # Obliga a rearmar el sprite en el proximo dibujo
        self._sprite_zoom = None

    def set_fury(self, speed):
        """Pega `speed` veces mas rapido (1.0 = velocidad normal)."""

        self.fury_speed = max(1.0, float(speed))

    @property
    def fury(self):

        return self.fury_speed > 1.0

    def _head_angle(self):
        """Hacia donde mira la punta (la llama) en el PNG."""

        return VELA_HEAD_ANGLE if self.kind == "vela" else SPRITE_HEAD_ANGLE

    def can_attack(self):

        return not self.swinging and self.cooldown <= 0

    def start(self):
        """Empieza un golpe. El area queda fija hacia donde apuntabas."""

        if not self.can_attack():
            return False

        self.swinging = True
        self.t = 0.0
        self.glow = 0.0
        self._hit_ids = set()

        return True

    def cancel(self):
        """Corta el golpe (por ejemplo si se apaga el fosforo)."""

        self.swinging = False
        self.glow = 0.0

    def update(self, dt, pivot, mouse_world):
        """pivot y mouse_world en coordenadas del mundo."""

        if self.cooldown > 0:
            self.cooldown = max(0.0, self.cooldown - dt)

        if self.glow > 0:
            self.glow = max(0.0, self.glow - dt)

        if not self.swinging:

            # El area sigue al mouse mientras no estas pegando
            self.aim = math.atan2(
                mouse_world[1] - pivot[1],
                mouse_world[0] - pivot[0]
            )

            return

        self.t += dt * self.fury_speed / SWING_TIME

        if self.t >= 1.0:

            self.t = 1.0
            self.swinging = False
            self.cooldown = self.cooldown_time / self.fury_speed
            self.glow = GLOW_TIME
            self.glow_angle = self.end_angle

    # ---------- golpes ----------

    def _rect_touched(self, rect, pivot, swept, arc):
        """True si algun punto del rect cae dentro de la parte del
        area que el fosforo ya barrio."""

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
        """Objetivos (con .rect en coordenadas del mundo) que el
        fosforo acaba de tocar. Cada uno se golpea una sola vez por
        golpe: cuenta lo que ya barrio el fosforo, no todo el area."""

        if not self.swinging:
            return []

        swept = self.current_angle - self.start_angle
        arc = self.end_angle - self.start_angle

        hits = []

        for target in targets:

            if id(target) in self._hit_ids:
                continue

            # Objetos grandes y alargados (puertas): se prueba el
            # borde real y no solo el centro.
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

            # Angulo medido desde el borde donde empezo el golpe
            rel = (
                math.atan2(dy, dx) - self.start_angle + math.pi
            ) % math.tau - math.pi

            margin = size / max(dist, 1.0)

            if -margin <= rel <= min(swept, arc) + margin:

                self._hit_ids.add(id(target))
                hits.append(target)

        return hits

    # ---------- dibujo ----------

    def _get_sprite(self, zoom):

        if self._sprite_zoom != zoom:

            if self.kind == "vela":

                original = pygame.image.load(
                    str(HUD_DIR / "icon_vela.png")
                ).convert_alpha()

                scale = VELA_LENGTH / VELA_SPRITE_PX

            else:

                original = pygame.image.load(
                    str(HUD_DIR / "item_fosforo.png")
                ).convert_alpha()

                scale = STICK_LENGTH / SPRITE_STICK_PX

            size = max(
                1,
                round(original.get_width() * scale * zoom)
            )

            self._sprite = pygame.transform.scale(original, (size, size))
            self._sprite_zoom = zoom

        return self._sprite

    @staticmethod
    def _to_screen(camera, x, y):

        return (
            x * camera.zoom - camera.x,
            y * camera.zoom - camera.y
        )

    def _draw_trail(self, screen, camera, pivot, angle, strength):
        """Estela: franja que se va apagando detras del fosforo."""

        zoom = camera.zoom

        size = int(OUTER_RADIUS * 2 * zoom) + 4
        center = size / 2

        layer = pygame.Surface((size, size), pygame.SRCALPHA)

        trail = math.radians(TRAIL_DEGREES)

        back = max(self.start_angle, angle - trail)

        segments = 10

        r_in = (INNER_RADIUS + 2) * zoom
        r_out = OUTER_RADIUS * zoom

        for i in range(segments):

            a0 = back + (angle - back) * i / segments
            a1 = back + (angle - back) * (i + 1) / segments

            alpha = int(170 * strength * ((i + 1) / segments) ** 2)

            if alpha <= 0:
                continue

            points = (
                arc_points(center, center, r_out, a0, a1, 2)
                + arc_points(center, center, r_in, a1, a0, 2)
            )

            color = (255, 120, 50) if self.fury else (255, 205, 120)

            pygame.draw.polygon(layer, (*color, alpha), points)

        px, py = self._to_screen(camera, pivot[0], pivot[1])

        screen.blit(layer, layer.get_rect(center=(round(px), round(py))))

    def draw(self, screen, camera, pivot):
        """Estela y fosforo girando. Se dibuja encima de la oscuridad
        para que brille."""

        if self.swinging:

            angle = self.current_angle

            self._draw_trail(screen, camera, pivot, angle, 1.0)

            sprite = pygame.transform.rotate(
                self._get_sprite(camera.zoom),
                self._head_angle() - math.degrees(angle)
            )

            # El palito queda un poco corrido del centro del sprite
            distance = INNER_RADIUS + STICK_LENGTH / 2 + 2

            px, py = self._to_screen(
                camera,
                pivot[0] + math.cos(angle) * distance,
                pivot[1] + math.sin(angle) * distance
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
                self.glow / GLOW_TIME
            )

    def draw_debug(self, screen, camera, pivot):
        """Como tu dibujo: el area en naranja y el recorrido en rojo."""

        zoom = camera.zoom

        px, py = self._to_screen(camera, pivot[0], pivot[1])

        outline = sector_outline(
            px, py,
            INNER_RADIUS * zoom, OUTER_RADIUS * zoom,
            self.start_angle, self.end_angle
        )

        pygame.draw.polygon(screen, (255, 130, 30), outline, 3)

        # Linea hacia donde apunta el mouse
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
    """Muneco para probar los golpes (F5 lo crea donde esta el mouse)."""

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

        # Barrita de vida
        bar = pygame.Rect(0, 0, dest.width, 6)
        bar.midbottom = (dest.centerx, dest.top - 6)

        pygame.draw.rect(screen, (40, 20, 20), bar)

        fill = bar.copy()
        fill.width = max(0, round(bar.width * self.hp / self.max_hp))

        pygame.draw.rect(screen, (220, 70, 60), fill)