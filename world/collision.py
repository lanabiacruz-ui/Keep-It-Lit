import pygame


class CollisionMap:

    def __init__(self):

      

        self.walkable = [

            pygame.Rect(
                172, 31,
                94, 59
            ),

          
            pygame.Rect(
                181, 151,
                87, 61
            ),

          
            pygame.Rect(
                42, 150,
                74, 62
            ),

          
            pygame.Rect(
                335, 150,
                80, 62
            ),

          
            pygame.Rect(
                48, 378,
                64, 49
            ),

            
            pygame.Rect(
                315, 309,
                119, 109
            ),

           
            pygame.Rect(
                184, 350,
                78, 57
            ),

          
         
            
            pygame.Rect(
                215, 88,
                20, 65
            ),

            
            pygame.Rect(
                112, 180,
                72, 17
            ),

          
            pygame.Rect(
                265, 180,
                72, 17
            ),

          
            pygame.Rect(
                70, 207,
                18, 174
            ),

           
            pygame.Rect(
                370, 207,
                19, 105
            ),

            
            pygame.Rect(
                214, 210,
                20, 143
            )
        ]

        
        self.obstacles = [

          
            pygame.Rect(
                187, 356,
                25, 20
            ),

           
            pygame.Rect(
                216, 356,
                20, 12
            ),

          
            pygame.Rect(
                235, 356,
                16, 18
            ),

          
            pygame.Rect(
                218, 389,
                20, 11
            )
        ]

   
    def point_is_walkable(self, x, y):

       
        if x < 0 or y < 0:
            return False

        point = pygame.Rect(
            int(x),
            int(y),
            1,
            1
        )

      

        inside_walkable = False

        for zone in self.walkable:

            if zone.colliderect(point):
                inside_walkable = True
                break

        if not inside_walkable:
            return False

     
        for obstacle in self.obstacles:

            if obstacle.colliderect(point):
                return False

        return True

   

    def can_move(self, rect):

        # Puntos del hitbox del jugador
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
