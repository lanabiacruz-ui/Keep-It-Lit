"""Bloques aplastadores de la sala de la IZQUIERDA (zona 2).

La barra vertical de la cruz de piedra deja dos huecos, uno arriba y
otro abajo, entre la punta de la barra y la pared. Por esos huecos se
puede cruzar de un lado al otro de la sala.

Cada hueco tiene un bloque que a veces esta libre y a veces se mueve y
lo cierra, como una puerta automatica:

    ABIERTO  -> el hueco esta libre (tiempo al azar)
    AVISO    -> el hueco parpadea en rojo (te da tiempo de salir)
    CERRANDO -> el bloque sale de golpe hacia la pared
    CERRADO  -> el hueco queda tapado un rato
    ABRIENDO -> el bloque se retrae despacio

Si el bloque te agarra adentro del hueco te hace dano y te saca para un
costado. A los enemigos NO les hace dano (solo los saca del camino).

Las coordenadas son las del mapa (1920x1080).
"""

import math
import random

import pygame


# ---------------------------------------------------------------
# AJUSTES (tocar aca para cambiar la dificultad)
# ---------------------------------------------------------------

CRUSH_DAMAGE = 0.35        # 0.35 = 35% de la vida de la luz

OPEN_TIME = (3.5, 7.0)     # segundos libre (al azar entre los dos)
WARN_TIME = 0.9            # parpadeo rojo antes de cerrar
CLOSE_TIME = 0.22          # lo que tarda en cerrar (rapido)
CLOSED_TIME = (2.0, 3.5)   # segundos cerrado (al azar)
OPEN_ANIM_TIME = 0.9       # lo que tarda en abrir (lento)

# (nombre, x, ancho, y de la punta de la barra, y de la pared, direccion)
# La barra de la cruz esta un poco inclinada en el dibujo, por eso cada
# punta tiene su propio x/ancho.
#   arriba: la punta de la barra esta en y=372 y la pared en y=330
#   abajo:  la punta de la barra esta en y=708 y la pared en y=755
GAPS = (
    ("top", 374, 52, 372, 330, -1),
    ("bottom", 377, 57, 708, 755, +1),
)


OPEN = "open"
WARN = "warn"
CLOSING = "closing"
CLOSED = "closed"
OPENING = "opening"


class CrusherBlock:
    """Un bloque que cierra y abre uno de los huecos."""

    def __init__(self, name, x, width, base_y, wall_y, direction,
                 first_delay):

        self.name = name
        self.x = x
        self.width = width
        self.base_y = base_y
        self.direction = direction

        # Cuanto avanza el bloque desde la punta de la barra hasta la pared
        self.reach = abs(wall_y - base_y)

        self.state = OPEN
        self.timer = first_delay

        # 0.0 = retraido (hueco libre)   1.0 = cerrado del todo
        self.progress = 0.0

        # Rect de colision. Es SIEMPRE el mismo objeto (se modifica en
        # el lugar), asi puede quedar adentro de la lista de obstaculos.
        self.rect = pygame.Rect(x, base_y, width, 0)

        self._warn_t = 0.0

    # ---------- geometria ----------

    def _refresh_rect(self):

        length = round(self.reach * self.progress)

        if self.direction < 0:

            # Sale hacia arriba: la base queda abajo
            self.rect.update(
                self.x, self.base_y - length, self.width, length
            )

        else:

            # Sale hacia abajo: la base queda arriba
            self.rect.update(
                self.x, self.base_y, self.width, length
            )

    def gap_rect(self):
        """Todo el hueco (para el parpadeo rojo del aviso)."""

        if self.direction < 0:

            return pygame.Rect(
                self.x, self.base_y - self.reach, self.width, self.reach
            )

        return pygame.Rect(
            self.x, self.base_y, self.width, self.reach
        )

    @property
    def solid(self):

        return self.progress > 0.0

    # ---------- logica ----------

    def update(self, dt):

        self.timer -= dt

        if self.state == OPEN:

            self.progress = 0.0

            if self.timer <= 0:

                self.state = WARN
                self.timer = WARN_TIME
                self._warn_t = 0.0

        elif self.state == WARN:

            self._warn_t += dt

            if self.timer <= 0:

                self.state = CLOSING
                self.timer = CLOSE_TIME

        elif self.state == CLOSING:

            self.progress = 1.0 - max(0.0, self.timer) / CLOSE_TIME

            if self.timer <= 0:

                self.progress = 1.0
                self.state = CLOSED
                self.timer = random.uniform(*CLOSED_TIME)

        elif self.state == CLOSED:

            self.progress = 1.0

            if self.timer <= 0:

                self.state = OPENING
                self.timer = OPEN_ANIM_TIME

        elif self.state == OPENING:

            self.progress = max(0.0, self.timer) / OPEN_ANIM_TIME

            if self.timer <= 0:

                self.progress = 0.0
                self.state = OPEN
                self.timer = random.uniform(*OPEN_TIME)

        self._refresh_rect()

    @property
    def crushing(self):
        """True mientras el bloque puede aplastar (se esta cerrando o
        ya esta cerrado)."""

        return self.state in (CLOSING, CLOSED)

    # ---------- dibujo ----------

    def draw(self, screen, camera):

        # Aviso: el hueco parpadea en rojo
        if self.state == WARN:

            pulse = 0.5 + 0.5 * math.sin(self._warn_t * 16)

            area = camera.apply(self.gap_rect())

            if area.width > 0 and area.height > 0:

                glow = pygame.Surface(area.size, pygame.SRCALPHA)
                glow.fill((255, 60, 50, int(70 + 110 * pulse)))
                screen.blit(glow, area)

            # El bloque tiembla un poco antes de salir
            shake = round(2 * pulse)

        else:

            shake = 0

        if not self.solid and self.state != WARN:
            return

        rect = camera.apply(self.rect)

        if self.state == WARN:

            # Todavia retraido: se ve solo la puntita temblando
            tip = pygame.Rect(self.x, self.base_y, self.width, 6)

            if self.direction < 0:
                tip.bottom = self.base_y

            rect = camera.apply(tip)
            rect.x += shake

        if rect.width <= 0 or rect.height <= 0:
            return

        # Piedra con borde oscuro (parecido a la barra de la cruz)
        pygame.draw.rect(screen, (128, 112, 103), rect)

        # Juntas de las piedras
        step = max(6, rect.width // 4)

        for y in range(rect.top + step, rect.bottom, step):

            pygame.draw.line(
                screen, (96, 80, 69),
                (rect.left, y), (rect.right - 1, y), 1
            )

        pygame.draw.rect(
            screen, (28, 22, 20), rect, max(2, round(2 * camera.zoom))
        )


class CrusherBlocks:
    """Los dos bloques de la sala de la izquierda."""

    def __init__(self, collision_map):

        self.collision_map = collision_map

        self.blocks = []

        for i, (name, x, width, base_y, wall_y, direction) in enumerate(GAPS):

            # Cada uno arranca en un momento distinto
            block = CrusherBlock(
                name, x, width, base_y, wall_y, direction,
                first_delay=random.uniform(2.0, 4.0) + i * 1.5,
            )

            self.blocks.append(block)

            # Su rect es el obstaculo: se agranda/achica solo
            collision_map.obstacles.append(block.rect)

    # ---------- aplastar / sacar del camino ----------

    @staticmethod
    def _push_out(rect, block_rect, cmap):
        """Saca `rect` de adentro del bloque, para el costado mas
        cercano (el hueco es angosto: no hay otra salida)."""

        left_x = block_rect.left - rect.width
        right_x = block_rect.right

        if rect.centerx < block_rect.centerx:
            order = (left_x, right_x)
        else:
            order = (right_x, left_x)

        for x in order:

            probe = rect.copy()
            probe.x = x

            if cmap.can_move(probe):

                rect.x = x

                return True

        return False

    def update(self, game, dt):

        cmap = self.collision_map

        player = game.player

        for block in self.blocks:

            block.update(dt)

            if not block.solid:
                continue

            # ---- jugador: dano + lo saca para el costado ----
            if player.rect.colliderect(block.rect) and block.crushing:

                if player.hurt(block.rect.center):

                    game.take_damage(CRUSH_DAMAGE)

                self._push_out(player.rect, block.rect, cmap)

            # ---- enemigos: solo los saca del camino (sin dano) ----
            for arena in game.arenas:

                for enemy in arena.enemies:

                    if enemy.rect.colliderect(block.rect):

                        if self._push_out(enemy.rect, block.rect, cmap):

                            pos = getattr(enemy, "pos", None)

                            if pos is not None:
                                pos.x = enemy.rect.centerx
                                pos.y = enemy.rect.centery

    def draw(self, screen, camera):

        for block in self.blocks:
            block.draw(screen, camera)