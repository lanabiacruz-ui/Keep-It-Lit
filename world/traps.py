"""Trampas de la Zona 2 (Stonun).

Al empezar cada oleada aparecen TRAP_COUNT trampas en lugares al azar de la
sala. Si el jugador pisa una, queda quieto encima y tiene que apretar
ESPACIO muchas veces para llenar una barra. Cuando la barra se llena se
suelta y, al salirse de la trampa, esta queda usada (no vuelve a funcionar).

Se restablecen (nuevas posiciones, todas armadas) cada vez que empieza una
oleada: al pasar de oleada o al volver a entrar a la sala.
"""

import math
import random
from pathlib import Path

import pygame

from core.audio_manager import audio

BASE_DIR = Path(__file__).resolve().parent.parent
COMBAT_DIR = BASE_DIR / "assets" / "maps" / "combate"

TRAP_COUNT = 4

# tamano en el mundo (las imagenes son de 96x64 = 24x16 a zoom x4)
TRAP_SIZE = (24, 16)

# zona que hay que pisar (mas chica que la imagen para que sea justo)
TRIGGER_SIZE = (14, 8)

PRESS_GAIN = 0.10       # cuanto sube la barra por cada ESPACIO
DECAY = 0.30            # cuanto baja por segundo si no apretas

MIN_GAP = 70            # distancia minima entre trampas
MIN_PLAYER_DIST = 90    # no aparecen encima del jugador
MIN_GATE_DIST = 80      # ni pegadas a la reja
ROOM_MARGIN = 36        # alejadas de las paredes de la sala

ARMED = "armed"
HOLDING = "holding"
FREED = "freed"         # el jugador se solto pero sigue parado encima
USED = "used"

_fonts = {}


def _font(size):

    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)

    return _fonts[size]


def _text(screen, text, size, color, **anchor):

    font = _font(size)

    shadow = font.render(text, True, (0, 0, 0))
    label = font.render(text, True, color)

    rect = label.get_rect(**anchor)

    screen.blit(shadow, rect.move(2, 2))
    screen.blit(label, rect)

    return rect


class Trap:

    def __init__(self, center):

        self.center = center

        self.state = ARMED

        self.trigger = pygame.Rect(0, 0, *TRIGGER_SIZE)
        self.trigger.center = center

        self.body = pygame.Rect(0, 0, *TRAP_SIZE)
        self.body.center = center

        # zona un poco mas grande: al salir de ella queda "usada"
        self.leave_zone = self.trigger.inflate(6, 6)


class ArenaTraps:

    def __init__(self, count=TRAP_COUNT):

        self.count = count
        self.traps = []

        self.holding = None
        self.progress = 0.0
        self.flash = 0.0
        self.time = 0.0

        self._images = None
        self._scaled = {}

    # ------------------------------------------------------
    # IMAGENES
    # ------------------------------------------------------

    def _load(self):

        if self._images is not None:
            return

        self._images = {}

        files = {
            ARMED: "trampa.png",
            HOLDING: "trampa_activa.png",
            USED: "trampa_usada.png",
        }

        for state, name in files.items():

            path = COMBAT_DIR / name

            try:
                self._images[state] = pygame.image.load(
                    str(path)
                ).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self._images[state] = self._placeholder(state)

    @staticmethod
    def _placeholder(state):

        surf = pygame.Surface((96, 64), pygame.SRCALPHA)

        color = {
            ARMED: (200, 70, 40),
            HOLDING: (230, 40, 40),
            USED: (90, 80, 76),
        }[state]

        pygame.draw.ellipse(surf, color, surf.get_rect().inflate(-8, -8))
        pygame.draw.ellipse(surf, (20, 17, 15), surf.get_rect().inflate(-8, -8), 4)

        return surf

    def _image(self, state, zoom):

        if state == FREED:
            state = HOLDING

        key = (state, zoom)

        img = self._scaled.get(key)

        if img is None:

            size = (int(TRAP_SIZE[0] * zoom), int(TRAP_SIZE[1] * zoom))

            img = pygame.transform.smoothscale(self._images[state], size)

            self._scaled[key] = img

        return img

    # ------------------------------------------------------
    # ESTADO
    # ------------------------------------------------------

    def reset(self, game, room, gate=None):
        """Nuevas trampas, todas armadas, en lugares al azar de la sala."""

        self.clear(game)

        cmap = game.collision_map
        player = game.player

        area = room.inflate(-ROOM_MARGIN * 2, -ROOM_MARGIN * 2)

        if area.width <= 0 or area.height <= 0:
            return

        probe = pygame.Rect(0, 0, TRAP_SIZE[0] + 10, TRAP_SIZE[1] + 10)

        placed = []

        for _ in range(900):

            if len(placed) >= self.count:
                break

            x = random.randint(area.left, area.right)
            y = random.randint(area.top, area.bottom)

            probe.center = (x, y)

            if not cmap.can_move(probe):
                continue

            if math.dist((x, y), player.rect.center) < MIN_PLAYER_DIST:
                continue

            if gate is not None and math.dist((x, y), gate.center) < MIN_GATE_DIST:
                continue

            if any(math.dist((x, y), c) < MIN_GAP for c in placed):
                continue

            placed.append((x, y))

        self.traps = [Trap(c) for c in placed]

    def clear(self, game=None):
        """Saca todas las trampas y suelta al jugador si estaba atrapado."""

        was_holding = self.holding is not None

        self.traps = []
        self.holding = None
        self.progress = 0.0
        self.flash = 0.0

        # solo soltamos al jugador si lo tenia esta misma sala
        if game is not None and was_holding:
            game.player.trapped = False

    # ------------------------------------------------------
    # ACTUALIZAR
    # ------------------------------------------------------

    def update(self, game, dt, can_trigger=True):

        if not self.traps:
            return

        self.time += dt

        player = game.player

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt * 6.0)

        if self.holding is not None:

            trap = self.holding

            # sigue clavado en la trampa aunque lo empujen
            player.rect.center = trap.center
            player.image_rect.midbottom = (
                player.rect.centerx,
                player.rect.bottom + 3,
            )
            player.kb_vel = pygame.Vector2()
            player.trapped = True

            self.progress = max(0.0, self.progress - DECAY * dt)

            return

        for trap in self.traps:

            if trap.state == FREED:

                if not player.rect.colliderect(trap.leave_zone):
                    trap.state = USED

            elif (
                trap.state == ARMED
                and can_trigger
                and not player.grabbed
                and player.rect.colliderect(trap.trigger)
            ):
                self._snap(game, trap)

                return

    def _snap(self, game, trap):

        trap.state = HOLDING

        self.holding = trap
        self.progress = 0.0
        self.flash = 1.0

        player = game.player

        player.trapped = True
        player.rect.center = trap.center
        player.image_rect.midbottom = (
            player.rect.centerx,
            player.rect.bottom + 3,
        )
        player.kb_vel = pygame.Vector2()

        audio.play("hit_heavy", 0.7)

        game.show_message("¡Una trampa! Apretá ESPACIO para soltarte")

    def press_space(self, game):
        """Devuelve True si el ESPACIO se uso para zafarse (no salta)."""

        if self.holding is None:
            return False

        self.progress = min(1.0, self.progress + PRESS_GAIN)
        self.flash = 1.0

        if self.progress >= 1.0:

            trap = self.holding

            trap.state = FREED

            self.holding = None
            self.progress = 0.0

            game.player.trapped = False

            audio.play("pickup", 0.6)

        return True

    # ------------------------------------------------------
    # DIBUJAR
    # ------------------------------------------------------

    def draw_world(self, screen, camera):

        if not self.traps:
            return

        self._load()

        view = screen.get_rect().inflate(200, 200)

        for trap in self.traps:

            dest = camera.apply(trap.body)

            if not view.colliderect(dest):
                continue

            state = trap.state

            img = self._image(
                USED if state == USED else state,
                camera.zoom,
            )

            if state == ARMED:

                # la placa roja late despacio para que se vea
                k = 0.5 + 0.5 * math.sin(self.time * 3.0 + trap.center[0])

                glow = pygame.Surface(img.get_size(), pygame.SRCALPHA)

                pygame.draw.ellipse(
                    glow,
                    (255, 90, 40, int(18 + 34 * k)),
                    glow.get_rect().inflate(-4, -4),
                )

                screen.blit(glow, dest.topleft)

            screen.blit(img, dest.topleft)

    def draw_hud(self, screen):

        if self.holding is None:
            return

        sw, sh = screen.get_size()

        width = min(460, int(sw * 0.5))
        height = 30

        bar = pygame.Rect(0, 0, width, height)
        bar.midbottom = (sw // 2, sh - 46)

        _text(
            screen,
            "¡ATRAPADO!  Apretá ESPACIO muchas veces",
            32,
            (255, 214, 120),
            midbottom=(bar.centerx, bar.top - 8),
        )

        shake = int(3 * self.flash)

        shown = bar.move(
            random.randint(-shake, shake) if shake else 0,
            0,
        )

        pygame.draw.rect(screen, (24, 20, 18), shown.inflate(10, 10), border_radius=10)
        pygame.draw.rect(screen, (70, 62, 58), shown, border_radius=8)

        fill = shown.copy()
        fill.width = max(0, int((shown.width - 6) * self.progress))
        fill.height = shown.height - 6
        fill.topleft = (shown.left + 3, shown.top + 3)

        if fill.width > 0:

            r = int(220 + 35 * self.flash)
            g = int(110 + 80 * self.progress)

            pygame.draw.rect(
                screen, (min(255, r), min(255, g), 50), fill, border_radius=6
            )

            shine = fill.copy()
            shine.height = max(2, fill.height // 3)

            pygame.draw.rect(
                screen, (255, 235, 170), shine, border_radius=6
            )

        pygame.draw.rect(screen, (20, 17, 15), shown, 3, border_radius=8)