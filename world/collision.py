import pygame


class CollisionMap:
    def __init__(self):


        self.world_width = 1920
        self.world_height = 1080
        self.doors = None

        self._pt = pygame.Rect(0, 0, 1, 1)


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


    def point_is_walkable(self, x, y):

        if x < 0 or y < 0:
            return False

        pt = self._pt
        pt.topleft = (int(x), int(y))

        if pt.collidelist(self.walkable) == -1:
            return False

        if pt.collidelist(self.obstacles) != -1:
            return False

        return True

    def can_move(self, rect):

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
            (left, top), (cx, top), (right, top),
            (left, cy), (right, cy),
            (left, bottom), (cx, bottom), (right, bottom),
        ):

            if not self.point_is_walkable(x, y):
                return False

            if door_rects:

                pt.topleft = (int(x), int(y))

                if pt.collidelist(door_rects) != -1:
                    return False

        return True
