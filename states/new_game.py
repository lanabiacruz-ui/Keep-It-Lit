import math
from pathlib import Path

import pygame

from core.Save_manager import save_progress, delete_save
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

# Cuanto dura prendido el fosforo (vida), en segundos. Baja rapido.
MATCH_DURATION = 12.0

# Cuenta regresiva (en segundos) cuando no hay luz, antes de perder.
NO_LIGHT_COUNTDOWN = 10.0

# Debajo de este % de vida, la luz empieza a parpadear.
FLICKER_THRESHOLD = 0.25

# Cuanto tarda la pantalla en ponerse del todo negra al perder.
FADE_DURATION = 1.2

# Cuanto se queda la pantalla de "Perdiste" antes de volver al menu.
LOST_SCREEN_TIME = 3.0


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

        self.coins = int(self.save_data.get("coins", 0))

        # ---------- Fosforo / vida ----------

        self.has_match = bool(self.save_data.get("has_match", False))

        # Vida del fosforo actual, de 0.0 a 1.0
        self.vida = 1.0

        # Escudo: por ahora solo se muestra, arranca vacio
        self.escudo = 0.0

        if self.has_match:
            self.match_item = None
            self.equip_match()
        else:
            self.match_item = MatchItem(*MATCH_POS)

        # Cuenta regresiva cuando no hay luz. None = no esta corriendo.
        self.no_light_timer = None

        # Que casillero esta seleccionado: "equipped" (el fosforo
        # equipado) o un numero 0-3 (un slot del inventario).
        self.selected_slot = "equipped"

        # Estados: "playing" -> "dying" (se pone todo negro) -> "lost"
        self.state = "playing"
        self.fade_alpha = 0
        self.lost_timer = 0

        self._flicker_time = 0.0

        pantalla_perdiste_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
            / "pantalla_perdiste.png"
        )

        self.pantalla_perdiste = pygame.transform.smoothscale(
            pygame.image.load(str(pantalla_perdiste_path)).convert(),
            (self.width, self.height)
        )

        self.fade_overlay = pygame.Surface(
            (self.width, self.height)
        )

        self.fade_overlay.fill((0, 0, 0))

    # ---------- fosforo ----------

    def equip_match(self):

        # OJO: no se reinicia self.vida aca. Si el fosforo ya se habia
        # usado un poco y lo soltaste, al agarrarlo de nuevo tiene que
        # seguir con la vida que le quedaba, no volver a llenarse.
        self.has_match = True
        self.hud.equip("fosforo")
        self.player.set_torch(True)

    def _drop_match(self):

        x, y = self.player.rect.center

        self.match_item = MatchItem(x, y)

        self.has_match = False
        self.hud.equip(None)
        self.player.set_torch(False)

    def _burn_out(self):

        # Se le acabo la vida al fosforo: se consume, no queda tirado
        self.vida = 0.0
        self.has_match = False
        self.match_item = None
        self.hud.equip(None)
        self.player.set_torch(False)

    # ---------- guardado ----------

    def save_progress(self):

        if self.save_path is None:
            return False

        x, y = self.player.image_rect.center

        return save_progress(
            self.save_path,
            player_name=self.player_name,
            x=x,
            y=y,
            has_match=self.has_match,
            coins=self.coins
        )

    # ---------- eventos ----------

    def handle_event(self, event):

        if self.state != "playing":
            return None

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

            # 1 = seleccionar la cosa iluminadora equipada
            if event.key == pygame.K_1:

                self.selected_slot = "equipped"

            # 2, 3, 4, 5 = seleccionar cada slot del inventario (0 a 3)
            elif event.key in (
                pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5
            ):

                index = event.key - pygame.K_2

                self.selected_slot = index
                self.hud.selected = index

            # Q = soltar lo que este seleccionado en este momento
            elif event.key == pygame.K_q:

                if self.selected_slot == "equipped":

                    if self.has_match:
                        self._drop_match()

                else:

                    # Los slots de inventario todavia no tienen items
                    # reales, asi que por ahora no hay nada que soltar.
                    pass

        return None

    # ---------- update ----------

    def update(self, dt):

        if self.state == "playing":

            self.player.update(dt, self.collision_map)

            self.camera.update(self.player, dt)

            if self.has_match:

                self.vida -= dt / MATCH_DURATION

                if self.vida <= 0:

                    self._burn_out()

            if not self.has_match:

                if self.no_light_timer is None:

                    self.no_light_timer = NO_LIGHT_COUNTDOWN

                else:

                    self.no_light_timer -= dt

                    if self.no_light_timer <= 0:

                        self.no_light_timer = 0

                        self.state = "dying"
                        self.fade_alpha = 0

            else:

                self.no_light_timer = None

            return None

        elif self.state == "dying":

            self.fade_alpha += dt * (255 / FADE_DURATION)

            if self.fade_alpha >= 255:

                self.fade_alpha = 255
                self.state = "lost"
                self.lost_timer = 0

                if self.save_path:
                    delete_save(self.save_path)

            return None

        elif self.state == "lost":

            self.lost_timer += dt

            if self.lost_timer >= LOST_SCREEN_TIME:

                return "menu"

            return None

        return None

    # ---------- dibujo ----------

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

            radius = PLAYER_LIGHT_RADIUS

            if self.vida < FLICKER_THRESHOLD:

                self._flicker_time += 0.02

                flicker = 0.55 + 0.45 * abs(
                    math.sin(self._flicker_time * 18)
                )

                radius *= flicker

            sources.append((
                self.player.rect.centerx,
                self.player.rect.centery,
                radius
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

        self.hud.draw(
            self.screen,
            vida=self.vida if self.has_match else 0.0,
            escudo=self.escudo,
            countdown=self.no_light_timer,
            coins=self.coins
        )

        if self.selected_slot == "equipped":

            pygame.draw.rect(
                self.screen,
                (255, 225, 120),
                self.hud.equipped_rect.inflate(8, 8),
                width=3,
                border_radius=10
            )

        if self.state in ("dying", "lost"):

            self.fade_overlay.set_alpha(int(self.fade_alpha))

            self.screen.blit(self.fade_overlay, (0, 0))

        if self.state == "lost":

            self.screen.blit(self.pantalla_perdiste, (0, 0))