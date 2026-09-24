import pygame


class CollisionMap:

    def __init__(self):

        # =========================================================
        # ZONAS CAMINABLES
        # =========================================================

        self.walkable = [

            # -------------------------------------------------
            # HABITACIÓN SUPERIOR
            # -------------------------------------------------
            pygame.Rect(
                172, 31,
                94, 59
            ),

            # -------------------------------------------------
            # HABITACIÓN CENTRAL
            # -------------------------------------------------
            pygame.Rect(
                181, 151,
                87, 61
            ),

            # -------------------------------------------------
            # HABITACIÓN IZQUIERDA
            # -------------------------------------------------
            pygame.Rect(
                42, 150,
                74, 62
            ),

            # -------------------------------------------------
            # HABITACIÓN DERECHA
            # -------------------------------------------------
            pygame.Rect(
                335, 150,
                80, 62
            ),

            # -------------------------------------------------
            # HABITACIÓN INFERIOR IZQUIERDA
            # -------------------------------------------------
            pygame.Rect(
                48, 378,
                64, 49
            ),

            # -------------------------------------------------
            # HABITACIÓN GRANDE INFERIOR DERECHA
            # -------------------------------------------------
            pygame.Rect(
                315, 309,
                119, 109
            ),

            # -------------------------------------------------
            # CABAÑA
            # -------------------------------------------------
            pygame.Rect(
                184, 350,
                78, 57
            ),

            # =================================================
            # CAMINOS
            # =================================================

            # Central -> superior
            pygame.Rect(
                215, 88,
                20, 65
            ),

            # Central -> izquierda
            pygame.Rect(
                112, 180,
                72, 17
            ),

            # Central -> derecha
            pygame.Rect(
                265, 180,
                72, 17
            ),

            # Izquierda -> inferior
            pygame.Rect(
                70, 207,
                18, 174
            ),

            # Derecha -> habitación grande
            pygame.Rect(
                370, 207,
                19, 105
            ),

            # Central -> cabaña
            pygame.Rect(
                214, 210,
                20, 143
            )
        ]

        # =========================================================
        # OBSTÁCULOS
        # =========================================================

        self.obstacles = [

            # -----------------------------
            # CAMA
            # -----------------------------
            pygame.Rect(
                187, 356,
                25, 20
            ),

            # -----------------------------
            # MUEBLE
            # -----------------------------
            pygame.Rect(
                216, 356,
                20, 12
            ),

            # -----------------------------
            # COMPUTADORA
            # -----------------------------
            pygame.Rect(
                235, 356,
                16, 18
            ),

            # -----------------------------
            # MUEBLE INFERIOR
            # -----------------------------
            pygame.Rect(
                218, 389,
                20, 11
            )
        ]

    # =========================================================
    # COMPROBAR SI UN PUNTO SE PUEDE PISAR
    # =========================================================

    def point_is_walkable(self, x, y):

        # Evitar salir del mapa
        if x < 0 or y < 0:
            return False

        point = pygame.Rect(
            int(x),
            int(y),
            1,
            1
        )

        # -------------------------------------------------
        # Primero: tiene que estar dentro de una zona
        # caminable
        # -------------------------------------------------

        inside_walkable = False

        for zone in self.walkable:

            if zone.colliderect(point):
                inside_walkable = True
                break

        if not inside_walkable:
            return False

        # -------------------------------------------------
        # Segundo: comprobar obstáculos
        # -------------------------------------------------

        for obstacle in self.obstacles:

            if obstacle.colliderect(point):
                return False

        return True

    # =========================================================
    # COMPROBAR SI EL JUGADOR ENTERO SE PUEDE MOVER
    # =========================================================

    def can_move(self, rect):

        # Puntos del hitbox del jugador
        points = [

            # -----------------------------
            # ARRIBA
            # -----------------------------
            (rect.left, rect.top),
            (rect.centerx, rect.top),
            (rect.right - 1, rect.top),

            # -----------------------------
            # MEDIO
            # -----------------------------
            (rect.left, rect.centery),
            (rect.right - 1, rect.centery),

            # -----------------------------
            # ABAJO
            # -----------------------------
            (rect.left, rect.bottom - 1),
            (rect.centerx, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1)
        ]

        # Comprobar todos los puntos
        for x, y in points:

            if not self.point_is_walkable(x, y):
                return False

        return True