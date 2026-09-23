import pygame

from player.movement import PlayerMovement


class Player:

    def __init__(self, x, y, width=32, height=32):

        # (x, y) es el CENTRO del jugador 
        self.rect = pygame.Rect(
            x - width // 2,
            y - height // 2,
            width,
            height
        )

        self.movement = PlayerMovement()

        self.moving = False

        # Color placeholder hasta tener el spritesheet real
        self.color = (220, 70, 70)

    def update(self, dt, collision_map):

        self.moving = self.movement.update(
            self.rect,
            collision_map,
            dt
        )

    def draw(self, screen, camera):

        screen_rect = camera.apply(self.rect)

        pygame.draw.rect(
            screen,
            self.color,
            screen_rect,
            border_radius=4
        )
