import pygame


class Camera:

    def __init__(
        self,
        screen_width,
        screen_height,
        world_width,
        world_height,
        zoom=2.5
    ):

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.world_width = world_width
        self.world_height = world_height

        self.zoom = zoom


        self.scaled_width = int(
            world_width * zoom
        )

        self.scaled_height = int(
            world_height * zoom
        )

        self.x = 0
        self.y = 0

    def update(self, player):



        # Limitar cam

        player_x = player.rect.centerx * self.zoom
        player_y = player.rect.centery * self.zoom


        self.x = (
            player_x
            - self.screen_width // 2
        )

        self.y = (
            player_y
            - self.screen_height // 2
        )

 
        max_x = max(
            0,
            self.scaled_width
            - self.screen_width
        )


        self.x = max(
            0,
            min(self.x, max_x)
        )

        max_y = max(
            0,
            self.scaled_height
            - self.screen_height
        )

        self.y = max(
            0,
            min(self.y, max_y)
        )


    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        

    def apply(self, rect):


        return pygame.Rect(
            int(rect.x * self.zoom - self.x),
            int(rect.y * self.zoom - self.y),
            int(rect.width * self.zoom),
            int(rect.height * self.zoom)
        )