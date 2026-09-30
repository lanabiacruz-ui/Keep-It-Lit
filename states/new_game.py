import pygame

from world.map_loader import WorldMap
from world.collision import CollisionMap
from world.camera import Camera
from world.spawn import get_spawn_point
from player.player import Player
from core.Save_manager import save_progress


class NewGame:
    def __init__(
        self,
        screen,
        player_name="Jugador",
        save_path=None,
        save_data=None
    ):

        self.screen = screen
        self.player_name = player_name
        self.width, self.height = screen.get_size()

        
        self.save_path = save_path

        self.world_map = WorldMap()
        self.collision_map = CollisionMap()

        spawn_x, spawn_y = self._resolve_spawn(save_data)

        self.player = Player(spawn_x, spawn_y)

        self.camera = Camera(
            self.width,
            self.height,
            self.collision_map.world_width,
            self.collision_map.world_height,
        )

        self.camera.update(self.player)

        
        self._autosave_timer = 0
        self._autosave_interval = 20

    def _resolve_spawn(self, save_data):

        
        if save_data and "x" in save_data and "y" in save_data:

            return save_data["x"], save_data["y"]

        return get_spawn_point(
            self.collision_map,
            "cabana"
        )

    def save_progress(self):

        if self.save_path is None:
            return

        save_progress(
            self.save_path,
            player_name=self.player_name,
            x=self.player.rect.centerx,
            y=self.player.rect.centery,
        )

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                
                self.save_progress()

                return "menu"

        return None

    def update(self, dt):

        self.player.update(dt, self.collision_map)

        self.camera.update(self.player, dt)

        self._autosave_timer += dt

        if self._autosave_timer >= self._autosave_interval:

            self._autosave_timer = 0

            self.save_progress()

    def draw(self):

        self.world_map.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)