import pygame

from core.Save_manager import save_progress
from world.map_loader import WorldMap
from world.collision import CollisionMap
from world.camera import Camera
from world.spawn import get_spawn_point
from player.player import Player
from world.lighting import PlayerLight
from world.items import MatchItem
from ui.hud import Hud


PLAYER_LIGHT_RADIUS = 100
MATCH_LIGHT_RADIUS = 60  


MATCH_POS = (818, 1002)


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
        self.save_path = save_path
        self.save_data = save_data or {}
        self.width, self.height = screen.get_size()

        self.world_map = WorldMap()
        self.collision_map = CollisionMap()

        spawn_x, spawn_y = get_spawn_point(
            self.collision_map,
            "cabana"
        )

        spawn_x = self.save_data.get("x", spawn_x)
        spawn_y = self.save_data.get("y", spawn_y)

        self.player = Player(spawn_x, spawn_y)

        self.camera = Camera(
            self.width,
            self.height,
            self.collision_map.world_width,
            self.collision_map.world_height,
        )

        self.camera.update(self.player)

        self.light = PlayerLight(
            (self.width, self.height),
            darkness_alpha=245
        )

        self.hud = Hud((self.width, self.height))


        self.has_match = bool(self.save_data.get("has_match", False))

        if self.has_match:
            self.match_item = None
            self.equip_match()
        else:
            self.match_item = MatchItem(*MATCH_POS)

    def equip_match(self):
       
        self.has_match = True
        self.hud.equip("fosforo")
        self.player.set_torch(True)

    def save_progress(self):

        if self.save_path is None:
            return False

        x, y = self.player.image_rect.center

        return save_progress(
            self.save_path,
            player_name=self.player_name,
            x=x,
            y=y,
            has_match=self.has_match
        )

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.save_progress()
                return "menu"

            if event.key == pygame.K_e:

                if (
                    self.match_item is not None
                    and self.match_item.is_near(self.player)
                ):
                    self.match_item = None
                    self.equip_match()

        return None

    def update(self, dt):

        self.player.update(dt, self.collision_map)

        self.camera.update(self.player, dt)

    def draw(self):

        self.world_map.draw(
            self.screen,
            self.camera
        )

        if self.match_item is not None:
            self.match_item.draw(self.screen, self.camera)

        self.player.draw(
            self.screen,
            self.camera
        )


        sources = []

        if self.match_item is not None:
            sources.append((
                self.match_item.rect.centerx,
                self.match_item.rect.centery,
                MATCH_LIGHT_RADIUS
            ))

        if self.has_match:
            sources.append((
                self.player.rect.centerx,
                self.player.rect.centery,
                PLAYER_LIGHT_RADIUS
            ))

        self.light.draw(
            self.screen,
            self.camera,
            sources
        )

  
        if (
            self.match_item is not None
            and self.match_item.is_near(self.player)
        ):
            self.match_item.draw_prompt(self.screen, self.camera)

        self.hud.draw(self.screen)