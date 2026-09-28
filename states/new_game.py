import pygame

from world.map_loader import WorldMap
from world.collision import CollisionMap
from world.camera import Camera
from world.spawn import get_spawn_point
from player.player import Player


class NewGame:
    def __init__(self, screen, player_name="Jugador"):

        self.screen = screen
        self.player_name = player_name
        self.width, self.height = screen.get_size()

        self.world_map = WorldMap()
        self.collision_map = CollisionMap()

        # El jugador aparece en la cabaña de madera
        spawn_x, spawn_y = get_spawn_point(
            self.collision_map,
            "cabana"
        )

        self.player = Player(spawn_x, spawn_y)

        self.camera = Camera(
            self.width,
            self.height,
            self.collision_map.world_width,
            self.collision_map.world_height,
        )

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                # Volver al menú principal
                return "menu"

        return None

    def update(self, dt):

        self.player.update(dt, self.collision_map)
        self.camera.update(self.player)

    def draw(self):

        self.world_map.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
