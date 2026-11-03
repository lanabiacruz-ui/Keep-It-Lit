from pathlib import Path

import pygame


class CollisionMap:

    def __init__(self):

        self.world_width = 1920
        self.world_height = 1080
        self.doors = None

        self._pt = pygame.Rect(0, 0, 1, 1)

        # Rects de cosas moviles (slimes) que el jugador no puede atravesar.
        # Los actualiza el juego en cada frame.
        self.dynamic_blockers = []

        # --------------------------------------------------
        # COLISIONES DEL MAPA 1
        # --------------------------------------------------

        self.walkable = [

            pygame.Rect(316, 44, 272, 176),

            pygame.Rect(856, 36, 184, 142),

            pygame.Rect(1248, 56, 280, 164),

            pygame.Rect(1524, 108, 180, 56),
            pygame.Rect(1644, 0, 60, 164),

            pygame.Rect(148, 336, 500, 408),

            pygame.Rect(836, 400, 216, 220),

            pygame.Rect(1244, 388, 436, 284),

            pygame.Rect(820, 900, 240, 144),

            pygame.Rect(580, 124, 324, 24),

            pygame.Rect(992, 124, 264, 24),

            pygame.Rect(932, 170, 20, 240),

            pygame.Rect(640, 504, 204, 28),

            pygame.Rect(1044, 504, 208, 32),

            pygame.Rect(932, 612, 24, 296),
        ]

        self.obstacles = [

            pygame.Rect(1465, 70, 40, 36),
            pygame.Rect(1466, 174, 40, 36),

            pygame.Rect(865, 34, 41, 67),

            pygame.Rect(902, 100, 93, 40),

            pygame.Rect(906, 36, 89, 64),

            pygame.Rect(979, 36, 61, 26),

            pygame.Rect(1022, 892, 41, 155),

            pygame.Rect(877, 942, 69, 73),

            pygame.Rect(816, 988, 61, 59),

            pygame.Rect(1384, 449, 159, 23),
            pygame.Rect(1393, 579, 152, 30),
            pygame.Rect(1446, 449, 33, 160),

            pygame.Rect(1308, 507, 35, 45),

            pygame.Rect(1594, 501, 36, 42),

            pygame.Rect(374, 369, 52, 111),
            pygame.Rect(375, 480, 55, 120),
            pygame.Rect(376, 600, 58, 110),

            pygame.Rect(191, 514, 383, 55),

            pygame.Rect(190, 374, 70, 69),
            pygame.Rect(496, 365, 36, 30),
            pygame.Rect(524, 430, 38, 64),
            pygame.Rect(458, 431, 34, 38),
            pygame.Rect(284, 447, 33, 34),
            pygame.Rect(462, 588, 30, 36),
            pygame.Rect(263, 595, 82, 36),
            pygame.Rect(187, 676, 94, 36),

            pygame.Rect(557, 597, 30, 12),
            pygame.Rect(549, 609, 56, 12),
            pygame.Rect(541, 621, 66, 12),
            pygame.Rect(533, 633, 62, 12),
            pygame.Rect(525, 645, 61, 12),
            pygame.Rect(516, 657, 61, 12),
            pygame.Rect(507, 669, 61, 12),
            pygame.Rect(501, 681, 59, 12),
            pygame.Rect(509, 693, 44, 12),
            pygame.Rect(525, 705, 21, 12),
        ]

        # --------------------------------------------------
        # COLISIONES AUTOMATICAS DEL MAPA 2
        # --------------------------------------------------

        base = Path(__file__).resolve().parent.parent

        map2_path = (
            base
            / "assets"
            / "maps"
            / "region_01"
            / "mapa2.png"
        )

        self.map2_wall_mask = None

        try:

            map2_image = pygame.image.load(
                str(map2_path)
            )

            # Las paredes del mapa son considerablemente
            # mas oscuras que el suelo.
            #
            # La mascara detecta esos pixeles oscuros para
            # impedir que el jugador atraviese las paredes.

            self.map2_wall_mask = pygame.mask.from_threshold(
                map2_image,
                (74, 74, 74),
                (14, 14, 14)
            )

        except (pygame.error, FileNotFoundError) as error:

            print(
                f"[colisiones] No se pudo cargar "
                f"la mascara de mapa2: {error}"
            )

        # --------------------------------------------------
        # MASCARA DE PISO DEL MAPA 1
        # --------------------------------------------------
        #
        # Los rects de `walkable` quedaron mas chicos que el piso
        # dibujado (paredes invisibles). Esta mascara sale de
        # tools/make_collision_mask.py y sigue el borde real de las
        # paredes. Si no existe el PNG, se usan solo los rects.

        self.map1_floor_mask = None
        self._map1_blocked_mask = None
        self._fill_masks = {}

        try:

            floor_image = pygame.image.load(
                str(
                    base
                    / "assets"
                    / "maps"
                    / "region_01"
                    / "mapa_colision.png"
                )
            )

            floor_mask = pygame.mask.from_surface(floor_image)

            blocked = floor_mask.copy()
            blocked.invert()

            self.map1_floor_mask = floor_mask
            self._map1_blocked_mask = blocked

        except (pygame.error, FileNotFoundError) as error:

            print(
                f"[colisiones] No se pudo cargar "
                f"la mascara del mapa 1: {error}"
            )

        # --------------------------------------------------
        # PUNTOS DE APARICION
        # --------------------------------------------------

        self.spawn_points = {

            "player_start": (944, 510),

            "cabana": (984, 944),

            "habitacion_central": (944, 510),

            "habitacion_superior_izquierda": (452, 132),

            "habitacion_superior_centro": (950, 160),

            "habitacion_superior_derecha": (1388, 138),

            "habitacion_izquierda": (610, 540),

            "habitacion_derecha": (1462, 530),
        }

    # ------------------------------------------------------
    # DETECTAR SI ESTAMOS EN EL MAPA 2
    # ------------------------------------------------------

    def _is_map2(self):

        return (
            self.world_height >= 1500
            and self.world_width >= 1900
        )

    def _uses_floor_mask(self):

        return (
            self.map1_floor_mask is not None
            and not self._is_map2()
            and self.map1_floor_mask.get_size()
            == (self.world_width, self.world_height)
        )

    def _filled(self, width, height):

        key = (width, height)
        mask = self._fill_masks.get(key)

        if mask is None:
            mask = pygame.mask.Mask(key, fill=True)
            self._fill_masks[key] = mask

        return mask

    # ------------------------------------------------------
    # COMPROBAR SI UN PUNTO ES TRANSITABLE
    # ------------------------------------------------------

    def point_is_walkable(self, x, y):

        if (
            x < 0
            or y < 0
            or x >= self.world_width
            or y >= self.world_height
        ):
            return False

        # En el mapa 2, los pixeles de las paredes
        # se consideran zonas no transitables.

        if self._is_map2():

            if self.map2_wall_mask is not None:

                px = int(x)
                py = int(y)

                if self.map2_wall_mask.get_at((px, py)):
                    return False

        # Comprobacion del mapa 1 y de las zonas transitables.

        pt = self._pt
        pt.topleft = (int(x), int(y))

        if self._uses_floor_mask():

            if not self.map1_floor_mask.get_at((int(x), int(y))):
                return False

        elif pt.collidelist(self.walkable) == -1:
            return False

        if pt.collidelist(self.obstacles) != -1:
            return False

        return True

    # ------------------------------------------------------
    # COMPROBAR MOVIMIENTO DEL JUGADOR
    # ------------------------------------------------------

    def hits_dynamic(self, test, current):
        """True si `test` se mete en una cosa movil (slime).

        Si el jugador ya estaba tocando esa cosa (`current`), se deja moverse
        para que pueda salir y no quede trabado.
        """

        for blocker in self.dynamic_blockers:

            if test.colliderect(blocker) and not current.colliderect(blocker):
                return True

        return False

    def can_move(self, rect):

        # En mapa 2 comprobamos toda la superficie
        # ocupada por el jugador contra las paredes.
        #
        # Esto evita atravesarlas incluso si el jugador
        # se mueve rapido o la pared es muy delgada.

        if self._is_map2():

            if self.map2_wall_mask is not None:

                player_mask = pygame.mask.Mask(
                    (rect.width, rect.height),
                    fill=True
                )

                if self.map2_wall_mask.overlap(
                    player_mask,
                    rect.topleft
                ) is not None:

                    return False

        if self._uses_floor_mask():

            if self._map1_blocked_mask.overlap(
                self._filled(rect.width, rect.height),
                rect.topleft
            ) is not None:

                return False

        door_rects = (

            [d.rect for d in self.doors.doors]

            if self.doors is not None

            else None
        )

        pt = self._pt

        left = rect.left
        right = rect.right - 1

        top = rect.top
        bottom = rect.bottom - 1

        cx = rect.centerx
        cy = rect.centery

        for x, y in (

            (left, top),
            (cx, top),
            (right, top),

            (left, cy),
            (right, cy),

            (left, bottom),
            (cx, bottom),
            (right, bottom),

        ):

            if not self.point_is_walkable(x, y):
                return False

            if door_rects:

                pt.topleft = (int(x), int(y))

                if pt.collidelist(door_rects) != -1:
                    return False

        return True