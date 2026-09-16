import pygame


class CollisionMap:

    def __init__(self):

        # Tamaño del mapa
        self.world_width = 1312
        self.world_height = 1199

        
        # HABITACIONES

        # Habitación superior
        self.habitacion_superior = pygame.Rect(
            420, 65,
            675, 240
        )

        # Habitación central / inicio
        self.habitacion_central = pygame.Rect(
            435, 365,
            680, 550
        )

        # Habitación izquierda
        self.habitacion_izquierda = pygame.Rect(
            90, 350,
            220, 195
        )

        # Habitación derecha
        self.habitacion_derecha = pygame.Rect(
            815, 350,
            250, 195
        )

        # Habitación inferior izquierda
        self.habitacion_inferior = pygame.Rect(
            115, 925,
            285, 155
        )

        # Habitación del jefe
        self.habitacion_jefe = pygame.Rect(
            765, 750,
            345, 310
        )

        # Interior de la cabaña
        self.cabana = pygame.Rect(
            465, 850,
            185, 170
        )

        
        # CAMINOS / CONEXIONES
        

        # Central → habitación superior
        self.camino_superior = pygame.Rect(
            525, 225,
            575, 140
        )

        # Central → izquierda
        self.camino_izquierda = pygame.Rect(
            300, 430,
            145, 45
        )

        # Central → derecha
        self.camino_derecha = pygame.Rect(
            665, 430,
            150, 45
        )

        # Izquierda → inferior
        self.camino_inferior = pygame.Rect(
            170, 535,
            50, 390
        )

        # Central → jefe
        self.camino_jefe = pygame.Rect(
            905, 535,
            50, 215
        )

        # Central → cabaña
        self.camino_cabana = pygame.Rect(
            525, 545,
            50, 305
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

        # Revisa las  esquinas del jugador
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