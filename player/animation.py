import pygame


class PlayerAnimation:

    def __init__(self, sprite_path):

        self.sheet = pygame.image.load(
            sprite_path
        ).convert_alpha()

        self.frames = {
            "up": [],
            "down": [],
            "left": [],
            "right": []
        }

        self.direction = "down"
        self.current_frame = 0
        self.timer = 0
        self.animation_speed = 0.12

        self.sprite_width = 48
        self.sprite_height = 64

        self.load_sprites()

    def remove_background(self, image):

        image = image.convert_alpha()

        width, height = image.get_size()

        for x in range(width):

            for y in range(height):

                r, g, b, a = image.get_at((x, y))

                if (
                    abs(r - g) < 8
                    and abs(g - b) < 8
                    and r > 180
                ):

                    image.set_at(
                        (x, y),
                        (255, 255, 255, 0)
                    )

        return image

    def load_sprites(self):

        up = [
            pygame.Rect(330, 40, 145, 210),
            pygame.Rect(600, 40, 145, 210),
            pygame.Rect(875, 40, 145, 210),
            pygame.Rect(1150, 40, 145, 210)
        ]

        down = [
            pygame.Rect(330, 290, 145, 210),
            pygame.Rect(600, 290, 145, 210),
            pygame.Rect(875, 290, 145, 210),
            pygame.Rect(1150, 290, 145, 210)
        ]

        left = [
            pygame.Rect(330, 540, 145, 210),
            pygame.Rect(600, 540, 145, 210),
            pygame.Rect(875, 540, 145, 210),
            pygame.Rect(1150, 540, 145, 210)
        ]

        right = [
            pygame.Rect(330, 785, 145, 210),
            pygame.Rect(600, 785, 145, 210),
            pygame.Rect(875, 785, 145, 210),
            pygame.Rect(1150, 785, 145, 210)
        ]

        self.frames["up"] = self.create_frames(up)
        self.frames["down"] = self.create_frames(down)
        self.frames["left"] = self.create_frames(left)
        self.frames["right"] = self.create_frames(right)

    def create_frames(self, rectangles):

        frames = []

        for rect in rectangles:

            frame = self.sheet.subsurface(
                rect
            ).copy()

            frame = self.remove_background(frame)

            frame = pygame.transform.scale(
                frame,
                (
                    self.sprite_width,
                    self.sprite_height
                )
            )

            frames.append(frame)

        return frames

    def set_direction(self, direction):

        if direction != self.direction:

            self.direction = direction
            self.current_frame = 0
            self.timer = 0

    def update(self, moving, dt):

        if not moving:

            self.current_frame = 0
            self.timer = 0

            return

        self.timer += dt

        if self.timer >= self.animation_speed:

            self.timer = 0

            self.current_frame += 1

            if self.current_frame >= len(
                self.frames[self.direction]
            ):

                self.current_frame = 0

    def get_image(self, moving):

        return self.frames[
            self.direction
        ][self.current_frame]