import heapq
import math

import pygame

CELL = 8
MAX_EXPANSIONS = 1500

PATHS_PER_FRAME = 2

KEY_CHECK_MS = 250

_SQRT2 = math.sqrt(2.0)

_cache = {"key": None, "free": {}, "checked": -10000}

_budget = {"left": PATHS_PER_FRAME}


def begin_frame():

    _budget["left"] = PATHS_PER_FRAME


def take_budget():

    if _budget["left"] <= 0:
        return False

    _budget["left"] -= 1

    return True


def _world_key(collision_map):

    doors = collision_map.doors
    n_doors = len(doors.doors) if doors is not None else 0

    obstacles = tuple(
        (r.x, r.y, r.w, r.h) for r in collision_map.obstacles
    )

    return (n_doors, hash(obstacles))


def _cell_free(cx, cy, size, room, collision_map):

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

    now = pygame.time.get_ticks()

    if now - _cache["checked"] < KEY_CHECK_MS:
        return

    _cache["checked"] = now

    key = _world_key(collision_map)

    if _cache["key"] != key:
        _cache["key"] = key
        _cache["free"] = {}


def to_cell(p):

    return (int(p[0] // CELL), int(p[1] // CELL))


def to_world(cell):

    return (cell[0] * CELL + CELL / 2.0, cell[1] * CELL + CELL / 2.0)


def nearest_free(pos, size, room, collision_map, max_radius=80):

    w, h = size

    rect = pygame.Rect(0, 0, w, h)

    step = 3

    for radius in range(0, max_radius + 1, step):

        best = None
        best_d = None

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

    _refresh_cache(collision_map)

    size = (int(size[0]), int(size[1]))

    s = to_cell(start)
    g = to_cell(goal)

    if not _cell_free(g[0], g[1], size, room, collision_map):

        g = _closest_free_cell(g, size, room, collision_map)

        if g is None:
            return None

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
