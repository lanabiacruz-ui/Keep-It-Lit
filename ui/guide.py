import heapq
import math

import pygame

from world.zones import ZONES


# Puntos de paso del mapa 1 (puertas y salas). La flecha guia siguiendo
# estos caminos asi no apunta a traves de las paredes.
NODES = {
    "cabin": (940, 960),
    "cabana": (941, 877),
    "hub_abajo": (943, 642),
    "central": (944, 510),
    "hub_arriba": (942, 370),
    "sup_abajo": (943, 197),
    "tienda": (944, 130),
    "izq_central": (838, 138),
    "izq_sala": (614, 137),
    "cofres": (452, 132),
    "hub_izq": (806, 518),
    "sala_izq": (682, 518),
    "comb_izq": (400, 540),
    "hub_der": (1090, 520),
    "sala_der": (1214, 519),
    "comb_der": (1460, 520),
}

EDGES = [
    ("cabin", "cabana"),
    ("cabana", "hub_abajo"),
    ("hub_abajo", "central"),
    ("central", "hub_arriba"),
    ("hub_arriba", "sup_abajo"),
    ("sup_abajo", "tienda"),
    ("tienda", "izq_central"),
    ("izq_central", "izq_sala"),
    ("izq_sala", "cofres"),
    ("central", "hub_izq"),
    ("hub_izq", "sala_izq"),
    ("sala_izq", "comb_izq"),
    ("central", "hub_der"),
    ("hub_der", "sala_der"),
    ("sala_der", "comb_der"),
]

REACH = 40          # a esta distancia de un punto de paso se pasa al siguiente
DIRECT_DIST = 90    # si el objetivo esta tan cerca, se apunta directo

ARROW_COLOR = (255, 176, 64)
ARROW_OUTLINE = (30, 18, 8)

CHECK_BG = (12, 14, 18, 215)
CHECK_BORDER = (255, 170, 60)
CHECK_DONE = (96, 214, 120)
CHECK_TEXT = (245, 245, 245)
CHECK_MUTED = (170, 170, 180)


def _dist(a, b):

    return math.hypot(a[0] - b[0], a[1] - b[1])


def _graph():

    adj = {name: [] for name in NODES}

    for a, b in EDGES:

        d = _dist(NODES[a], NODES[b])

        adj[a].append((b, d))
        adj[b].append((a, d))

    return adj


ADJ = _graph()


def _all_distances():

    result = {}

    for start in NODES:

        best = {start: 0.0}
        heap = [(0.0, start)]

        while heap:

            d, node = heapq.heappop(heap)

            if d > best.get(node, 1e18):
                continue

            for nxt, w in ADJ[node]:

                nd = d + w

                if nd < best.get(nxt, 1e18):
                    best[nxt] = nd
                    heapq.heappush(heap, (nd, nxt))

        result[start] = best

    return result


GD = _all_distances()


def _zone_of(point):

    for zone in ZONES:

        if zone.rect.collidepoint(point):
            return zone.id

    return None


def _seg_dist(p, a, b):

    ax, ay = a
    bx, by = b

    dx, dy = bx - ax, by - ay

    length2 = dx * dx + dy * dy

    if length2 == 0:
        return _dist(p, a)

    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length2))

    return _dist(p, (ax + dx * t, ay + dy * t))


def nearest_node(point):

    return min(NODES, key=lambda n: _dist(point, NODES[n]))


def next_point(player, target):
    """Punto del mundo hacia el que hay que caminar para llegar a target."""

    player = (float(player[0]), float(player[1]))
    target = (float(target[0]), float(target[1]))

    if _dist(player, target) <= DIRECT_DIST:
        return target

    zone = _zone_of(player)

    if zone is not None and zone == _zone_of(target):
        return target

    goal = nearest_node(target)

    a, b = min(
        EDGES,
        key=lambda e: _seg_dist(player, NODES[e[0]], NODES[e[1]])
    )

    cost_a = _dist(player, NODES[a]) + GD[a][goal]
    cost_b = _dist(player, NODES[b]) + GD[b][goal]

    node = a if cost_a <= cost_b else b

    if _dist(player, NODES[node]) > REACH:
        return NODES[node]

    if node == goal:
        return target

    best = min(
        ADJ[node], key=lambda nw: nw[1] + GD[nw[0]][goal]
    )

    return NODES[best[0]]


class Guide:

    def __init__(self):

        self.t = 0.0

        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 20)

        self._arrow_cache = {}

    def update(self, dt):

        self.t += dt

    def _arrow_surface(self, angle_deg):

        key = int(round(angle_deg / 5.0)) * 5

        if key not in self._arrow_cache:

            size = 44

            base = pygame.Surface((size, size), pygame.SRCALPHA)

            pts = [(size - 4, size // 2), (8, 6), (16, size // 2), (8, size - 6)]

            pygame.draw.polygon(base, ARROW_OUTLINE, pts)

            inner = [
                (size - 10, size // 2), (13, 12), (19, size // 2), (13, size - 12)
            ]

            pygame.draw.polygon(base, ARROW_COLOR, inner)

            self._arrow_cache[key] = pygame.transform.rotate(base, -key)

        return self._arrow_cache[key]

    def draw_arrow(self, screen, camera, player_rect, target):

        player = player_rect.center

        wp = next_point(player, target)

        dx = wp[0] - player[0]
        dy = wp[1] - player[1]

        if abs(dx) < 1 and abs(dy) < 1:
            return

        angle = math.degrees(math.atan2(dy, dx))

        pulse = 0.5 + 0.5 * math.sin(self.t * 6)

        origin = camera.apply(
            pygame.Rect(player[0], player[1], 1, 1)
        ).topleft

        radius = 78 + 8 * pulse

        pos = (
            origin[0] + math.cos(math.radians(angle)) * radius,
            origin[1] + math.sin(math.radians(angle)) * radius,
        )

        arrow = self._arrow_surface(angle)

        screen.blit(arrow, arrow.get_rect(center=(int(pos[0]), int(pos[1]))))

        self._draw_marker(screen, camera, target)

    def _draw_marker(self, screen, camera, target):

        spot = camera.apply(
            pygame.Rect(int(target[0]), int(target[1]), 1, 1)
        ).topleft

        if not screen.get_rect().inflate(-40, -40).collidepoint(spot):
            return

        bob = int(math.sin(self.t * 5) * 6)

        x, y = spot[0], spot[1] - 46 + bob

        tip = [(x, y + 18), (x - 14, y), (x + 14, y)]

        pygame.draw.polygon(screen, ARROW_OUTLINE, [
            (x, y + 22), (x - 18, y - 3), (x + 18, y - 3)
        ])
        pygame.draw.polygon(screen, ARROW_COLOR, tip)

    def draw_checklist(self, screen, entries):
        """entries: lista de (texto, hecho)."""

        if not entries:
            return

        pad = 10
        row_h = 26

        title = self.title_font.render("PROBÁ TODO", True, CHECK_BORDER)

        labels = [
            self.font.render(text, True, CHECK_TEXT if not done else CHECK_DONE)
            for text, done in entries
        ]

        width = max(
            [title.get_width()] + [l.get_width() + 30 for l in labels]
        ) + pad * 2

        height = pad + title.get_height() + 4 + row_h * len(entries) + pad - 4

        panel = pygame.Surface((width, height), pygame.SRCALPHA)

        pygame.draw.rect(panel, CHECK_BG, panel.get_rect(), border_radius=10)
        pygame.draw.rect(
            panel, CHECK_BORDER, panel.get_rect(), width=2, border_radius=10
        )

        panel.blit(title, (pad, pad))

        y = pad + title.get_height() + 4

        for (text, done), label in zip(entries, labels):

            box = pygame.Rect(pad, y + 3, 16, 16)

            pygame.draw.rect(
                panel, CHECK_DONE if done else CHECK_MUTED, box,
                width=0 if done else 2, border_radius=3
            )

            if done:
                pygame.draw.lines(
                    panel, (20, 40, 24), False,
                    [(box.x + 3, box.y + 8), (box.x + 7, box.y + 12),
                     (box.x + 13, box.y + 4)], 3
                )

            panel.blit(label, (pad + 24, y + 1))

            y += row_h

        screen.blit(panel, panel.get_rect(midtop=(screen.get_width() // 2, 14)))