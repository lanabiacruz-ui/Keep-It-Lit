import pygame


class CollisionMap:
    def __init__(self):

        
        self.world_width = 1920
        self.world_height = 1080

     

        self.walkable = [

            # Sala superior izquierda
            pygame.Rect(316, 44, 272, 176),

            # Sala superior central (la de la biblioteca)
            pygame.Rect(856, 36, 184, 142),

            # Sala superior derecha
            pygame.Rect(1248, 56, 280, 164),

            # Sala grande izquierda
            pygame.Rect(148, 336, 500, 408),

            # Sala central (el "hub" en el medio del mapa)
            pygame.Rect(836, 400, 216, 220),

            # Sala grande derecha
            pygame.Rect(1244, 388, 436, 284),

            # Cabaña (interior)
            pygame.Rect(820, 900, 240, 144),

           

            # Superior izquierda -> superior central
            pygame.Rect(580, 124, 324, 24),

            # Superior derecha -> superior central
            pygame.Rect(992, 124, 264, 24),

            # Superior central -> sala central (vertical)
            pygame.Rect(932, 170, 20, 240),

            # Sala grande izquierda -> sala central
            pygame.Rect(640, 504, 204, 28),

            # Sala central -> sala grande derecha
            pygame.Rect(1044, 504, 208, 32),

            # Sala central -> cabaña (vertical)
            pygame.Rect(932, 612, 24, 296),
        ]

       

        self.obstacles = [

            # Biblioteca (sala superior central)
            pygame.Rect(866, 34, 40, 66),

            # Mesa oscura (sala superior central)
            pygame.Rect(902, 100, 92, 40),

            # Cocina (cabaña, pared derecha)
            pygame.Rect(1022, 892, 41, 155),

            # Escritorio con computadora y silla (cabaña)
            pygame.Rect(877, 942, 69, 73),

            # Cama (cabaña, esquina inferior izquierda)
            pygame.Rect(816, 988, 61, 59),
        ]

    
        self.spawn_points = {

            "player_start": (944, 510),

            "cabana": (984, 944),

            "habitacion_central": (944, 510),
            "habitacion_superior_izquierda": (452, 132),
            "habitacion_superior_centro": (950, 160),
            "habitacion_superior_derecha": (1388, 138),
            "habitacion_izquierda": (398, 540),
            "habitacion_derecha": (1462, 530),
        }

   

    def point_is_walkable(self, x, y):

        # Evitar salir del mapa
        if x < 0 or y < 0:
            return False

        x = int(x)
        y = int(y)

        
        inside_walkable = False

        for zone in self.walkable:

            if zone.collidepoint(x, y):
                inside_walkable = True
                break

        if not inside_walkable:
            return False

       
        for obstacle in self.obstacles:

            if obstacle.collidepoint(x, y):
                return False

        return True

  
    def can_move(self, rect):

        
        points = [

            (rect.left, rect.top),
            (rect.centerx, rect.top),
            (rect.right - 1, rect.top),

            (rect.left, rect.centery),
            (rect.right - 1, rect.centery),

            (rect.left, rect.bottom - 1),
            (rect.centerx, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1)
        ]

        for x, y in points:

            if not self.point_is_walkable(x, y):
                return False

        return True
