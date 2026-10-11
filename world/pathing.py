"""
Pathfinding simple para los enemigos (A* sobre una grilla chica).

Lo usa world/arena.py (clase Enemy) para dos cosas:
  - find_path():    camino rodeando paredes / bloques / puertas hasta el
                    jugador, en vez de ir en linea recta y quedarse pegado
  - nearest_free(): el lugar libre mas cercano (para sacar a un enemigo
                    que quedo incrustado en una pared)

Las celdas libres se guardan en un cache que se borra solo cuando cambia
el mapa (se rompe una puerta, el Crusher abre/cierra un hueco), asi que
calcular un camino es barato.
"""

import heapq
import math

import pygame

CELL = 8                # tamano de celda (unidades del mundo)
MAX_EXPANSIONS = 2500   # tope de nodos por busqueda (evita tirones)

_SQRT2 = math.sqrt(2.0)

_cache = {"key": None, "free": {}}


def _world_key(collision_map):
    """Cambia cuando cambia algo que bloquea (obstaculos o puertas)."""

    doors = collision_map.doors
    n_doors = len(doors.doors) if doors is not None else 0

    obstacles = tuple(
        (r.x, r.y, r.w, r.h) for r in collision_map.obstacles
    )

    return (n_doors, hash(obstacles))


def _cell_free(cx, cy, size, room, collision_map):
    """True si un cuerpo de `size` centrado en la celda cabe ahi."""

    key = (cx, cy, size)

    free = _cache["free"]

    if key in free:
        return free[key]

    w, h = size

    rect = pygame.Rect(0, 0, w, h)
    rect.center = (cx * CELL + CELL // 2, cy * CELL + CELL // 2)

    ok = room.contains(rect) and collision_map.can_move(rect)

    free[key] = ok

    return ok


def _refresh_cache(collision_map):

    key = _world_key(collision_map)

    if _cache["key"] != key:
        _cache["key"] = key
        _cache["free"] = {}


def to_cell(p):

    return (int(p[0] // CELL), int(p[1] // CELL))


def to_world(cell):

    return (cell[0] * CELL + CELL / 2.0, cell[1] * CELL + CELL / 2.0)


def nearest_free(pos, size, room, collision_map, max_radius=80):
    """Punto libre mas cercano a `pos` (o None si no hay en `max_radius`)."""

    w, h = size

    rect = pygame.Rect(0, 0, w, h)

    step = 3

    for radius in range(0, max_radius + 1, step):

        best = None
        best_d = None

        # anillo cuadrado de radio `radius`
        for dx in range(-radius, radius + 1, step):
            for dy in range(-radius, radius + 1, step):

                if max(abs(dx), abs(dy)) != radius:
                    continue

                rect.center = (round(pos[0] + dx), round(pos[1] + dy))

                if room.contains(rect) and collision_map.can_move(rect):

                    d = dx * dx + dy * dy

                    if best is None or d < best_d:
                        best = rect.center
                        best_d = d

        if best is not None:
            return best

    return None


def find_path(start, goal, size, room, collision_map):
    """Lista de puntos (x, y) del mundo desde `start` hasta `goal`
    rodeando lo que bloquea, o None si no hay camino.

    `size` = (ancho, alto) del cuerpo del enemigo."""

    _refresh_cache(collision_map)

    size = (int(size[0]), int(size[1]))

    s = to_cell(start)
    g = to_cell(goal)

    # El jugador puede estar pegado a una pared: se busca la celda
    # libre mas cercana al objetivo.
    if not _cell_free(g[0], g[1], size, room, collision_map):

        g = _closest_free_cell(g, size, room, collision_map)

        if g is None:
            return None

    # El enemigo mismo puede estar en una celda "no libre" por redondeo:
    # igual se arranca de ahi.
    open_heap = [(0.0, 0, s)]
    came = {s: None}
    cost = {s: 0.0}

    counter = 0
    expansions = 0

    while open_heap:

        _, _, cur = heapq.heappop(open_heap)

        if cur == g:
            break

        expansions += 1

        if expansions > MAX_EXPANSIONS:
            return None

        cx, cy = cur

        for dx, dy in (
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ):

            nxt = (cx + dx, cy + dy)

            if not _cell_free(nxt[0], nxt[1], size, room, collision_map):
                continue

            # En diagonal no se corta la esquina de una pared
            if dx != 0 and dy != 0:

                if not (
                    _cell_free(cx + dx, cy, size, room, collision_map)
                    and _cell_free(cx, cy + dy, size, room, collision_map)
                ):
                    continue

            step = _SQRT2 if (dx != 0 and dy != 0) else 1.0

            new_cost = cost[cur] + step

            if nxt not in cost or new_cost < cost[nxt]:

                cost[nxt] = new_cost
                came[nxt] = cur

                # heuristica octile
                hx = abs(nxt[0] - g[0])
                hy = abs(nxt[1] - g[1])
                h = (hx + hy) + (_SQRT2 - 2.0) * min(hx, hy)

                counter += 1

                heapq.heappush(open_heap, (new_cost + h, counter, nxt))

    if g not in came:
        return None

    cells = []
    cur = g

    while cur is not None:
        cells.append(cur)
        cur = came[cur]

    cells.reverse()

    # La primera celda es donde ya esta parado: se saltea
    points = [to_world(c) for c in cells[1:]]

    return points


def _closest_free_cell(cell, size, room, collision_map, max_ring=6):

    for ring in range(1, max_ring + 1):

        best = None
        best_d = None

        for dx in range(-ring, ring + 1):
            for dy in range(-ring, ring + 1):

                if max(abs(dx), abs(dy)) != ring:
                    continue

                c = (cell[0] + dx, cell[1] + dy)

                if _cell_free(c[0], c[1], size, room, collision_map):

                    d = dx * dx + dy * dy

                    if best is None or d < best_d:
                        best = c
                        best_d = d

        if best is not None:
            return best

    return None