import pygame


class CollisionMap:

    def __init__(self):

        # Tamaño del mapa (coincide con assets/maps/region_01/mapabeta.png)
        self.world_width = 512
        self.world_height = 468

        
        # HABITACIONES

        # Habitación superior
        self.habitacion_superior = pygame.Rect(
            164, 25,
            263, 94
        )

        # Habitación central / inicio
        self.habitacion_central = pygame.Rect(
            170, 142,
            265, 215
        )

        # Habitación izquierda
        self.habitacion_izquierda = pygame.Rect(
            35, 137,
            86, 76
        )

        # Habitación derecha
        self.habitacion_derecha = pygame.Rect(
            318, 137,
            98, 76
        )

        # Habitación inferior izquierda
        self.habitacion_inferior = pygame.Rect(
            45, 361,
            111, 61
        )

        # Habitación del jefe
        self.habitacion_jefe = pygame.Rect(
            299, 293,
            135, 121
        )

        # Interior de la cabaña
        self.cabana = pygame.Rect(
            181, 332,
            72, 66
        )

        
        # CAMINOS / CONEXIONES
        

        # Central → habitación superior
        self.camino_superior = pygame.Rect(
            205, 88,
            224, 55
        )

        # Central → izquierda
        self.camino_izquierda = pygame.Rect(
            117, 168,
            57, 18
        )

        # Central → derecha
        self.camino_derecha = pygame.Rect(
            260, 168,
            59, 18
        )

        # Izquierda → inferior
        self.camino_inferior = pygame.Rect(
            66, 209,
            20, 152
        )

        # Central → jefe
        self.camino_jefe = pygame.Rect(
            353, 209,
            20, 84
        )

        # Central → cabaña
        self.camino_cabana = pygame.Rect(
            205, 213,
            20, 119
        )

        
        # ZONAS POR LAS QUE SE PUEDE CAMINAR
        

        self.zonas_caminables = [

            # Habitaciones
            self.habitacion_superior,
            self.habitacion_central,
            self.habitacion_izquierda,
            self.habitacion_derecha,
            self.habitacion_inferior,
            self.habitacion_jefe,
            self.cabana,

            # Conexiones
            self.camino_superior,
            self.camino_izquierda,
            self.camino_derecha,
            self.camino_inferior,
            self.camino_jefe,
            self.camino_cabana
        ]

    
    # ¿SE PUEDE CAMINAR EN ESTA POSICIÓN?

    def is_walkable(self, x, y):

        # Fuera del mapa
        if x < 0 or y < 0:
            return False

        if x >= self.world_width or y >= self.world_height:
            return False

        point = pygame.Rect(
            int(x),
            int(y),
            1,
            1
        )

        
        # caminable
        for zona in self.zonas_caminables:

            if zona.colliderect(point):
                return True

        return False

    
    # ¿PUEDE EL JUGADOR MOVERSE?
    

    def can_move(self, rect):

        # Revisa las esquinas del jugador
        puntos = [

            (rect.left, rect.top),

            (rect.right - 1, rect.top),

            (rect.left, rect.bottom - 1),

            (rect.right - 1, rect.bottom - 1)
        ]

        for x, y in puntos:

            if not self.is_walkable(x, y):
                return False

        return True
        
