import pygame


class PlayerMovement:

    def __init__(self, speed=180):

        self.speed = speed

    def update(
        self,
        player_rect,
        collision_map,
        dt
    ):

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1


       

        moving = dx != 0 or dy != 0

        if not moving:
            return False

      
      

        direction = pygame.Vector2(
            dx,
            dy
        )

        direction = direction.normalize()

        dx = direction.x * self.speed * dt
        dy = direction.y * self.speed * dt

        
        

        new_rect = player_rect.copy()

        new_rect.x += round(dx)

        if collision_map.can_move(new_rect):

            player_rect.x = new_rect.x

       
       

        new_rect = player_rect.copy()

        new_rect.y += round(dy)

        if collision_map.can_move(new_rect):

            player_rect.y = new_rect.y

        return True