"""Ayudas puras (sin pygame) para que el ojo del monstruo te mire.

find_slit() encuentra la pupila (la rajita oscura) en el dibujo del ojo y
devuelve los pixeles que hay que rellenar con el color del iris para
"borrarla". Despues el juego dibuja una pupila nueva que se mueve hacia el
jugador (ver EyeMonster en ui/map2_scene.py).

`get(x, y)` devuelve (r, g, b, a) y debe aceptar cualquier coordenada
(fuera del dibujo = transparente).
"""

from collections import deque


def lum(c):

    return (c[0] * 3 + c[1] * 6 + c[2]) // 10


def find_slit(
    get, w, h, seed,
    dark=70, fringe=4, limit=(0.045, 0.08, 0.105)
):
    """Busca la pupila oscura que pasa por `seed` (x, y).

    limit = (ancho a cada lado, alto hacia arriba, alto hacia abajo) como
    fraccion del dibujo: evita que se escape hacia el borde oscuro del ojo.

    Devuelve (pixeles_a_rellenar, (x0, y0, x1, y1), color_pupila,
    color_iris) o None si no la encuentra.
    """

    sx, sy = seed

    c = get(sx, sy)

    if c[3] == 0 or lum(c) > dark:

        found = None

        # el seed puede caer un poco al costado de la rajita
        for d in range(1, max(2, int(0.03 * w)) + 1):

            for dx in (-d, d):

                cc = get(sx + dx, sy)

                if cc[3] > 0 and lum(cc) <= dark:
                    found = (sx + dx, sy)
                    break

            if found:
                break

        if not found:
            return None

        sx, sy = found
        c = get(sx, sy)

    lx = int(limit[0] * w)
    lup = int(limit[1] * h)
    ldown = int(limit[2] * h)

    seen = {(sx, sy)}
    queue = deque([(sx, sy)])
    core = []

    while queue:

        x, y = queue.popleft()
        core.append((x, y))

        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):

            if (nx, ny) in seen:
                continue

            seen.add((nx, ny))

            if abs(nx - sx) > lx or ny < sy - lup or ny > sy + ldown:
                continue

            if not (0 <= nx < w and 0 <= ny < h):
                continue

            cc = get(nx, ny)

            if cc[3] > 0 and lum(cc) <= dark:
                queue.append((nx, ny))

    if len(core) < 20:
        return None

    xs = [p[0] for p in core]
    ys = [p[1] for p in core]

    bbox = (min(xs), min(ys), max(xs), max(ys))

    # color del iris: lo que hay a un costado de la rajita
    iris = None

    for dx in range(8, 44, 4):

        cc = get(bbox[0] - dx, (bbox[1] + bbox[3]) // 2)

        if cc[3] > 0 and lum(cc) > 110:
            iris = cc
            break

    if iris is None:
        return None

    # los pixeles del borde (mezcla de pupila e iris) tambien se rellenan
    fill = set(core)
    frontier = set(core)

    for _ in range(fringe):

        new = set()

        for x, y in frontier:

            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):

                if (nx, ny) in fill or ny > bbox[3]:
                    continue

                cc = get(nx, ny)

                if cc[3] == 0 or lum(cc) >= 160:
                    continue

                diff = (
                    abs(cc[0] - iris[0])
                    + abs(cc[1] - iris[1])
                    + abs(cc[2] - iris[2])
                )

                if diff > 4:
                    new.add((nx, ny))

        fill |= new
        frontier = new

    return fill, bbox, tuple(c[:3]), tuple(iris[:3])