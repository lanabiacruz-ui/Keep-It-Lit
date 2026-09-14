import pygame


class Camera:
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        world_width: int,
        world_height: int,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.world_width = world_width
        self.world_height = world_height

        self.x = 0
        self.y = 0

    def update(self, player):
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