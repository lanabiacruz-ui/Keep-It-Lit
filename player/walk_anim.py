import math
import random

TAU = math.pi * 2

# --- Ritmo -----------------------------------------------------------------
# Un ciclo = 2 pasos. 0.34 s por paso coincide con STEP_INTERVAL de los sonidos.
STEP_TIME = 0.34
CYCLE_TIME = STEP_TIME * 2

# --- Intensidades (todo relativo al tamano del sprite, asi sirve con cualquier zoom)
BOB = 0.040            # rebote vertical (fraccion del alto)
STRETCH = 0.060        # estirar / aplastar
SQUEEZE = 0.035        # lo que se achica de ancho cuando se estira
SWAY_DEG = 5.5         # balanceo de lado a lado (de frente / espaldas)
LEAN_DEG = 4.0         # inclinacion hacia adelante (de perfil)
SIDE_WOBBLE_DEG = 1.8  # vaiven extra de perfil
SHIFT_X = 0.012        # el cuerpo se corre un poco hacia el pie que pisa
FOOT_LIFT = 0.055      # cuanto sube el pie que esta en el aire (fraccion del alto)
FOOT_BAND = 0.115      # franja de abajo que se considera "pies" (fraccion del alto)

BREATH_TIME = 2.7
BREATH_SQUASH = 0.020
BREATH_WIDTH = 0.010

START_RATE = 13.0      # que tan rapido arranca (mayor = mas brusco)
STOP_RATE = 9.0        # que tan rapido frena

STOP_SETTLE_TIME = 0.22


def smooth_toward(current, target, rate, dt):
    """Acerca `current` a `target` sin pasarse, independiente de los FPS."""
    k = 1.0 - math.exp(-rate * dt)
    return current + (target - current) * k


def walk_pose(phase, blend, direction, idle_t=0.0, settle=0.0, hurt=0.0, lean_in=0.0):
    """Devuelve la pose del cuerpo para este instante.

    phase   : 0..1, avanza mientras camina. En 0 y 0.5 un pie toca el piso.
    blend   : 0..1, cuanto "esta caminando" (suavizado, sube al arrancar y baja al frenar).
    direction: "up" | "down" | "left" | "right"
    idle_t  : reloj para respirar.
    settle  : 1 -> 0 despues de frenar (pequeno rebote al quedarse quieto).
    hurt    : 1 -> 0 despues de un golpe.
    lean_in : -1..1 empujon lateral (por ejemplo, del golpe).

    Devuelve un dict con:
      dy, dx    : desplazamiento (fraccion del alto del sprite)
      sx, sy    : escala
      angle     : grados, positivo = antihorario
      lift_l, lift_r : cuanto sube cada pie (fraccion del alto), solo de frente / espaldas
      contact   : 0 (en el aire) .. 1 (pisando), sirve para la sombra
    """

    s = math.sin(phase * TAU)
    h = abs(s)                      # 0 al pisar, 1 en el punto mas alto del paso
    centered = (h - 0.5) * 2.0      # -1 al pisar, +1 arriba

    walk = blend
    idle = 1.0 - blend

    breath = math.sin(idle_t * TAU / BREATH_TIME)

    dy = -h * BOB * walk
    sy = 1.0 + centered * STRETCH * walk
    sx = 1.0 - centered * SQUEEZE * walk

    # respirar (solo quieto): el pecho se infla y se achica
    sy += breath * BREATH_SQUASH * idle
    sx -= breath * BREATH_WIDTH * idle

    # al frenar: se aplasta un instante y vuelve
    if settle > 0:
        wob = math.sin((1.0 - settle) * TAU * 1.5) * settle
        sy -= wob * 0.055
        sx += wob * 0.040

    # golpe: aplastado fuerte que se recupera con rebote
    if hurt > 0:
        wob = math.cos((1.0 - hurt) * TAU * 1.25) * hurt
        sy -= wob * 0.13
        sx += wob * 0.10

    dx = 0.0
    angle = 0.0
    lift_l = 0.0
    lift_r = 0.0

    if direction in ("up", "down"):
        # balanceo de pinguino: se inclina hacia el pie que esta bajando
        angle = -s * SWAY_DEG * walk
        dx = s * SHIFT_X * walk
        lift_l = max(0.0, s) * FOOT_LIFT * walk
        lift_r = max(0.0, -s) * FOOT_LIFT * walk
    else:
        forward = 1.0 if direction == "left" else -1.0   # + = antihorario = hacia la izquierda
        angle = forward * (LEAN_DEG * walk) + s * SIDE_WOBBLE_DEG * walk
        dx = forward * -SHIFT_X * 0.3 * walk

    # respiracion: leve vaiven lateral para que no sea una estatua
    angle += math.sin(idle_t * TAU / (BREATH_TIME * 1.7)) * 0.6 * idle

    angle += lean_in * 6.0 * hurt

    return {
        "dx": dx,
        "dy": dy,
        "sx": sx,
        "sy": sy,
        "angle": angle,
        "lift_l": lift_l,
        "lift_r": lift_r,
        "contact": 1.0 - h * walk,
    }


def frame_for_phase(phase, count=4):
    """Cuadro de la hoja que corresponde a esta fase (0 y 2 = pie apoyado)."""
    return int(phase * count) % count


def step_crossed(prev_phase, new_phase):
    """True si entre las dos fases un pie toco el piso (fase 0 o 0.5)."""
    a = prev_phase * 2.0
    b = new_phase * 2.0

    if new_phase < prev_phase:   # dio la vuelta
        return True

    return int(a) != int(b)


def rotation_anchor_offset(height, angle_deg):
    """Al rotar una imagen alrededor de su centro, donde queda el punto
    "abajo al medio" respecto del centro nuevo (x, y) en pixeles de pantalla."""
    a = math.radians(angle_deg)

    return (
        (height / 2.0) * math.sin(a),
        (height / 2.0) * math.cos(a),
    )


# ---------------------------------------------------------------------------
# Polvo de las pisadas (sin pygame: solo datos)
# ---------------------------------------------------------------------------

class DustPuffs:

    LIFE = 0.42
    MAX = 40

    def __init__(self):
        self.puffs = []

    def emit(self, x, y, away_x, away_y, count=3, strength=1.0):
        """x, y = pies en coordenadas del mundo. away = hacia donde sale el polvo."""

        for _ in range(count):

            spread = random.uniform(-0.6, 0.6)

            vx = away_x * random.uniform(8, 18) + spread * 10
            vy = away_y * random.uniform(8, 18) - random.uniform(4, 11)

            self.puffs.append({
                "x": x + random.uniform(-2.0, 2.0),
                "y": y + random.uniform(-1.0, 0.5),
                "vx": vx * strength,
                "vy": vy * strength,
                "t": 0.0,
                "life": self.LIFE * random.uniform(0.8, 1.2),
                "r": random.uniform(0.9, 1.5),
            })

        if len(self.puffs) > self.MAX:
            del self.puffs[: len(self.puffs) - self.MAX]

    def update(self, dt):

        for p in self.puffs:
            p["t"] += dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            k = max(0.0, 1.0 - 5.0 * dt)
            p["vx"] *= k
            p["vy"] *= k

        self.puffs = [p for p in self.puffs if p["t"] < p["life"]]


# ---------------------------------------------------------------------------
# Todo lo de abajo usa pygame
# ---------------------------------------------------------------------------

def split_feet(sprite, pygame, band=FOOT_BAND):
    """Parte un sprite en (cuerpo, pie_izq, pie_der, y_corte, x_corte).

    Los pies son la franja de abajo. Se corta al medio para que cada pie
    se pueda mover solo. Cada pieza es del tamano completo del sprite
    (con transparencia) asi se vuelven a pegar en la misma posicion.
    """

    w, h = sprite.get_size()
    cut_y = h - max(3, int(round(h * band)))
    cut_x = w // 2

    # el punto de corte se ajusta a la fila mas angosta del sprite cerca del corte,
    # que es donde el cuerpo termina y empiezan los pies
    best_y = cut_y
    best_w = None

    for y in range(max(0, cut_y - 4), min(h, cut_y + 5)):
        run = 0
        for x in range(w):
            if sprite.get_at((x, y))[3] > 40:
                run += 1
        if best_w is None or run < best_w:
            best_w = run
            best_y = y

    cut_y = best_y

    body = pygame.Surface((w, h), pygame.SRCALPHA)
    body.blit(sprite, (0, 0), pygame.Rect(0, 0, w, cut_y))

    left = pygame.Surface((w, h), pygame.SRCALPHA)
    left.blit(sprite, (0, cut_y), pygame.Rect(0, cut_y, cut_x, h - cut_y))

    right = pygame.Surface((w, h), pygame.SRCALPHA)
    right.blit(sprite, (cut_x, cut_y), pygame.Rect(cut_x, cut_y, w - cut_x, h - cut_y))

    return body, left, right, cut_y, cut_x


def compose_pose(base, feet, pose, pygame, anchor_pad=10):
    """Arma el sprite final aplicando la pose.

    base : sprite ya escalado al tamano en pantalla.
    feet : resultado de split_feet(base) o None (de perfil no se separan los pies).
    Devuelve (superficie, ofs_x, ofs_y): donde pegarla respecto de "abajo al medio" del sprite.
    """

    w, h = base.get_size()

    # 1) pies sueltos + cuerpo, en un lienzo con margen
    if feet is not None and (pose["lift_l"] > 0.0005 or pose["lift_r"] > 0.0005):

        body, left, right, cut_y, cut_x = feet

        canvas = pygame.Surface((w, h + anchor_pad), pygame.SRCALPHA)

        ly = int(round(pose["lift_l"] * h))
        ry = int(round(pose["lift_r"] * h))

        # los pies que suben quedan detras del cuerpo, asi no se ve el corte
        canvas.blit(left, (0, anchor_pad - ly))
        canvas.blit(right, (0, anchor_pad - ry))
        canvas.blit(body, (0, anchor_pad))

    else:

        canvas = pygame.Surface((w, h + anchor_pad), pygame.SRCALPHA)
        canvas.blit(base, (0, anchor_pad))

    cw, ch = canvas.get_size()

    # 2) escala (abajo-al-medio queda fijo, asi no "flota")
    sx = max(0.5, pose["sx"])
    sy = max(0.5, pose["sy"])

    new_w = max(1, int(round(cw * sx)))
    new_h = max(1, int(round(ch * sy)))

    if (new_w, new_h) != (cw, ch):
        canvas = pygame.transform.smoothscale(canvas, (new_w, new_h))

    # 3) rotacion alrededor de "abajo al medio" de la imagen
    angle = pose["angle"]
    cw2, ch2 = canvas.get_size()

    if abs(angle) > 0.15:

        canvas = pygame.transform.rotozoom(canvas, angle, 1.0)

        px, py = rotation_anchor_offset(ch2, angle)

        rw, rh = canvas.get_size()

        # centro de la imagen rotada = (rw/2, rh/2); el ancla (abajo al medio) queda en
        # centro + (px, py)
        ofs_x = -(rw / 2.0 + px)
        ofs_y = -(rh / 2.0 + py)

    else:

        rw, rh = canvas.get_size()

        ofs_x = -rw / 2.0
        ofs_y = -rh

    # 4) desplazamientos de la pose
    ofs_x += pose["dx"] * h
    ofs_y += pose["dy"] * h

    return canvas, int(round(ofs_x)), int(round(ofs_y))