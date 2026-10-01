import math
from pathlib import Path
 
import pygame
 
 
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
 
        self.t += dt / SWING_TIME
 
        if self.t >= 1.0:
 
            self.t = 1.0
            self.swinging = False
            self.cooldown = COOLDOWN
            self.glow = GLOW_TIME
            self.glow_angle = self.end_angle
 
    # ---------- golpes ----------
 
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
 
            pygame.draw.polygon(layer, (255, 205, 120, alpha), points)
 
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
                SPRITE_HEAD_ANGLE - math.degrees(angle)
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