import pygame


class PlayerAnimation:

    def __init__(self, sprite_path):

        # Cargar sprites
        self.sheet = pygame.image.load(
            sprite_path
        ).convert()

        self.sheet.set_colorkey(
            self.sheet.get_at((0, 0))
        )


        self.direction = "down"

        self.current_frame = 0

        self.timer = 0

    
        self.animation_speed = 0.12


        self.sprite_width = 48
        self.sprite_height = 80
        

        self.frames = {
            "up": [],
            "down": [],
            "left": [],
            "right": []
        }

        self.idle = None

        self.load_sprites()



    def load_sprites(self):


        up = [
            pygame.Rect(225, 60, 50, 100),
            pygame.Rect(370, 60, 50, 100),
            pygame.Rect(445, 60, 50, 100),
            pygame.Rect(515, 60, 50, 100)
        ]


        left = [
            pygame.Rect(10, 220, 55, 100),
            pygame.Rect(65, 220, 55, 100),
            pygame.Rect(120, 220, 55, 100),
            pygame.Rect(175, 220, 55, 100)
        ]


        right = [
            pygame.Rect(305, 220, 55, 100),
            pygame.Rect(365, 220, 55, 100),
            pygame.Rect(425, 220, 55, 100),
            pygame.Rect(475, 220, 37, 100)
        ]


        down = [
            pygame.Rect(110, 365, 55, 110),
            pygame.Rect(185, 365, 55, 110),
            pygame.Rect(255, 365, 55, 110),
            pygame.Rect(330, 365, 55, 110)
        ]


        idle = pygame.Rect(
            235,
            220,
            55,
            100
        )

        # Crear frames
        self.frames["up"] = self.create_frames(up)
        self.frames["left"] = self.create_frames(left)
        self.frames["right"] = self.create_frames(right)
        self.frames["down"] = self.create_frames(down)

        self.idle = self.create_frame(idle)



    def create_frame(self, rect):

        frame = self.sheet.subsurface(
            rect
        ).copy()

        frame = pygame.transform.scale(
            frame,
            (
                self.sprite_width,
                self.sprite_height
            )
        )

        return frame


    def create_frames(self, rectangles):

        frames = []

        for rect in rectangles:

            frame = self.create_frame(
                rect
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


        if not moving:

            return self.idle


        return self.frames[
            self.direction
        ][self.current_frame]