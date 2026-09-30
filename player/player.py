import pygame
from pathlib import Path

from player.movement import PlayerMovement


class Player:
    CELL_WIDTH = 176
    CELL_HEIGHT = 226

    BOTTOM_MARGIN = 6

    ROWS = ["up", "down", "left", "right"]

    def __init__(self, x, y, width=34, height=46):

        self.image_rect = pygame.Rect(
            x - width // 2,
            y - height // 2,
            width,
            height
        )

        hitbox_width = 16
        hitbox_height = 12

        self.rect = pygame.Rect(
            x - hitbox_width // 2,
            self.image_rect.bottom - hitbox_height - 3,
            hitbox_width,
            hitbox_height
        )

        self.movement = PlayerMovement()

        self.moving = False
        self.direction = "down"

        self.animation_timer = 0
        self.animation_frame = 0

        base = Path(__file__).resolve().parent.parent

        image_path = (
            base
            / "assets"
            / "maps"
            / "player"
            / "player_frames.png"
        )

        sheet = pygame.image.load(
            image_path
        ).convert_alpha()

        self.frames = self.load_frames(sheet)

    def load_frames(self, sheet):

        frames = {}

        for row, direction in enumerate(self.ROWS):

            frames[direction] = []

            for col in range(4):

                area = pygame.Rect(
                    col * self.CELL_WIDTH,
                    row * self.CELL_HEIGHT,
                    self.CELL_WIDTH,
                    self.CELL_HEIGHT
                )

                sprite = sheet.subsurface(
                    area
                ).copy()

                frames[direction].append(
                    sprite
                )

        return frames

    def update(self, dt, collision_map):

        result = self.movement.update(
            self.rect,
            collision_map,
            dt
        )

        self.moving = result[0]

        if result[1] is not None:
            self.direction = result[1]

        self.image_rect.midbottom = (
            self.rect.centerx,
            self.rect.bottom + 3
        )

        if self.moving:

            self.animation_timer += dt

            if self.animation_timer >= 0.12:

                self.animation_timer = 0

                self.animation_frame += 1

                self.animation_frame %= len(
                    self.frames[self.direction]
                )

        else:

            self.animation_frame = 0

    def draw(self, screen, camera):

        frame = self.frames[
            self.direction
        ][
            self.animation_frame
        ]

        scale = self.image_rect.height / self.CELL_HEIGHT

        sprite = pygame.transform.smoothscale(
            frame,
            (
                round(self.CELL_WIDTH * scale),
                self.image_rect.height
            )
        )

        dest = sprite.get_rect(
            midbottom=camera.apply(self.image_rect).midbottom
        )

        screen.blit(
            sprite,
            dest
        )