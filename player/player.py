import pygame

from player.movement import PlayerMovement


class Player:

    def __init__(self, x, y, width=20, height=20):

       
        self.image_rect = pygame.Rect(
            x - width // 2,
            y - height // 2,
            width,
            height
        )

      
        hitbox_width = 12
        hitbox_height = 12

        self.rect = pygame.Rect(
            x - hitbox_width // 2,
            y - hitbox_height // 2,
            hitbox_width,
            hitbox_height
        )

        self.movement = PlayerMovement()

        self.moving = False

        self.color = (220, 70, 70)

    def update(self, dt, collision_map):

        self.moving = self.movement.update(
            self.rect,
            collision_map,
            dt
        )

        self.image_rect.center = self.rect.center

    def draw(self, screen, camera):

        screen_rect = camera.apply(
            self.image_rect
        )

        pygame.draw.rect(
            screen,
            self.color,
            screen_rect,
            border_radius=4
        )
