import pygame

from player.movement import PlayerMovement
from player.animation import PlayerAnimation


class Player:

    def __init__(self, x, y, width=48, height=64):

        self.animation = PlayerAnimation(
            "assets/maps/player/player.png"
        )

        hitbox_width = 20
        hitbox_height = 14

        self.rect = pygame.Rect(
            x - hitbox_width // 2,
            y - hitbox_height // 2,
            hitbox_width,
            hitbox_height
        )

        self.image_rect = pygame.Rect(
            0,
            0,
            width,
            height
        )

        self.image_rect.center = self.rect.center

        self.movement = PlayerMovement()

        self.moving = False

    def update(self, dt, collision_map):

        self.moving = self.movement.update(
            self.rect,
            collision_map,
            dt
        )

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w] or keys[pygame.K_UP]:

            self.animation.set_direction("up")

        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:

            self.animation.set_direction("down")

        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:

            self.animation.set_direction("left")

        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:

            self.animation.set_direction("right")

        self.animation.update(
            self.moving,
            dt
        )

        self.image_rect.center = self.rect.center

    def draw(self, screen, camera):

        screen_rect = camera.apply(
            self.image_rect
        )

        image = self.animation.get_image(
            self.moving
        )

        screen.blit(
            image,
            screen_rect
        )