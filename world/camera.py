import pygame


class Camera:
<<<<<<< HEAD
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        world_width: int,
        world_height: int,
=======

    def __init__(
        self,
        screen_width,
        screen_height,
        world_width,
        world_height,
        zoom=2.5
>>>>>>> ae8f728aa85800bea3daf94ebc74ac8829cd825b
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.world_width = world_width
        self.world_height = world_height

<<<<<<< HEAD
=======
        self.zoom = zoom

        self.scaled_width = int(world_width * zoom)
        self.scaled_height = int(world_height * zoom)

>>>>>>> ae8f728aa85800bea3daf94ebc74ac8829cd825b
        self.x = 0
        self.y = 0

    def update(self, player):
<<<<<<< HEAD
        """
        Sigue al jugador utilizando sus coordenadas
        dentro del mundo.
        """

        self.x = player.rect.centerx - self.screen_width // 2
        self.y = player.rect.centery - self.screen_height // 2

        # Limitar cámara al tamaño del mundo
        self.x = max(
            0,
            min(self.x, self.world_width - self.screen_width)
        )

        self.y = max(
            0,
            min(self.y, self.world_height - self.screen_height)
        )

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """
        Convierte coordenadas del mundo
        a coordenadas de pantalla.
        """

        return pygame.Rect(
            rect.x - self.x,
            rect.y - self.y,
            rect.width,
            rect.height,
        )
=======
        
        player_x = player.rect.centerx * self.zoom
        player_y = player.rect.centery * self.zoom

        self.x = player_x - self.screen_width // 2
        self.y = player_y - self.screen_height // 2

      
        max_x = max(0, self.scaled_width - self.screen_width)
        max_y = max(0, self.scaled_height - self.screen_height)

        self.x = max(0, min(self.x, max_x))
        self.y = max(0, min(self.y, max_y))

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(
            int(rect.x * self.zoom - self.x),
            int(rect.y * self.zoom - self.y),
            int(rect.width * self.zoom),
            int(rect.height * self.zoom)
        )
>>>>>>> ae8f728aa85800bea3daf94ebc74ac8829cd825b
