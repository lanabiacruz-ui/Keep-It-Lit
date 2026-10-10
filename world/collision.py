import pygame


class CollisionMap:
    def __init__(self):

        
        self.world_width = 1920
        self.world_height = 1080
        self.doors = None

     

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
            pygame.Rect(865, 34, 41, 67),

            # Mesa oscura / mostrador (sala superior central)
            pygame.Rect(902, 100, 93, 40),

            # Detras del mostrador: el rojito (cabeza y cuerpo), la
            # botella y el cartel SHOP. Tapa todo el hueco entre la
            # biblioteca y el estante para que el jugador no pase al
            # otro lado de la mesa.
            pygame.Rect(906, 36, 89, 64),

            # Estante de arriba a la derecha (sala superior central)
            pygame.Rect(979, 36, 61, 26),

            # Cocina (cabaña, pared derecha)
            pygame.Rect(1022, 892, 41, 155),

            # Escritorio con computadora y silla (cabaña)
            pygame.Rect(877, 942, 69, 73),

            # Cama (cabaña, esquina inferior izquierda)
            pygame.Rect(816, 988, 61, 59),

            # ---- Sala grande derecha (la de combate) ----

            # Estructura en forma de "I": barra de arriba, barra de
            # abajo y el tallo que las une
            pygame.Rect(1384, 449, 159, 23),
            pygame.Rect(1393, 579, 152, 30),
            pygame.Rect(1446, 449, 33, 160),

            # Bloque de la izquierda
            pygame.Rect(1308, 507, 35, 45),

            # Bloque de la derecha
            pygame.Rect(1594, 501, 36, 42),

            # ---- Sala grande izquierda (la del Guardian) ----

            # Cruz de piedra del medio. La barra vertical va en tres
            # tramos porque esta un poco inclinada en el dibujo. Los
            # huecos de arriba y abajo (entre la punta y la pared) los
            # abre y cierra world/crusher.py
            pygame.Rect(374, 369, 52, 111),
            pygame.Rect(375, 480, 55, 120),
            pygame.Rect(376, 600, 58, 110),

            # Barra horizontal de la cruz
            pygame.Rect(191, 514, 383, 55),

            # Bloques sueltos
            pygame.Rect(190, 374, 70, 69),     # arriba a la izquierda
            pygame.Rect(496, 365, 36, 30),     # arriba a la derecha
            pygame.Rect(524, 430, 38, 64),     # derecha (alto)
            pygame.Rect(458, 431, 34, 38),     # centro arriba
            pygame.Rect(284, 447, 33, 34),     # chiquito izquierda
            pygame.Rect(462, 588, 30, 36),     # centro abajo
            pygame.Rect(263, 595, 82, 36),     # barra abajo izquierda
            pygame.Rect(187, 676, 94, 36),     # barra abajo del todo

            # Bloque inclinado (abajo a la derecha): como la colision
            # es de rectangulos, se arma en escalones siguiendo la
            # diagonal
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
            if self.doors is not None:

                for door in self.doors.doors:

                    if door.rect.collidepoint(x, y):
                        return False


        return True