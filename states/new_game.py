import math
import random
from pathlib import Path

import pygame

from core.audio_manager import audio
from core.controls import controls, SLOT_ACTIONS
from core.achievements import achievements
from core.Save_manager import (
    save_progress, delete_save, normalize_mode, MODE_HARDCORE
)
from world.map_loader import WorldMap
from world.collision import CollisionMap
from world.camera import Camera
from world.spawn import get_spawn_point
from player.player import Player
from world.lighting import PlayerLight
from world.fx import FxManager
from world.items import (
    LightItem,
    WorldItem,
    get_gem_icon,
    get_green_gem_icon,
    load_item_defs,
    load_spawn_zones,
    make_spawn_items
)
from world.melee import Melee, TrainingDummy
from world.fireball import Fireball, FireBurst
from world.lights import LIGHTS, light_stats
from world.doors import DoorManager, Door, DOOR_LAYOUT
from world.chests import ChestManager, Chest, format_time
from world.arena import Arena, RIGHT_ARENA, LEFT_ARENA
from world.final_door import MapSwitcher, enter_map, draw_placed_gems
from world.crusher import CrusherBlocks
from world.zones import ZoneTracker, ZONES, APPROACH_ZONES
from world.slime import SlimeManager
from world.shop import (
    Shopkeeper, load_catalog, price_table, SHOP_UNLOCK_WAVES
)
from world.placeables import PlaceableManager
from world.dungeon_map import DungeonMapView
from ui.hud import Hud
from ui.effects_bar import EffectsBar
from ui.chest_minigame import ChestMinigame
from core import skins as skin_lib

from ui.shop_ui import ShopUI
from ui.tutorial import Tutorial
from ui.guide import Guide
from ui.Zone_banner import ZoneBanner
from ui.achievement_toast import AchievementToast
from ui.objectives import Objectives
from states.pause_menu import PauseMenu
from states.enemy_enciclopedia import EnemyEncyclopedia
from states.settings import Settings


MATCH_POS = (818, 1002)

MATCH_DURATION = 30.0

SHOP_RECHARGE_TIME = 4.0

SHOP_LIGHT_FADE = 24.0

TORSO_HEIGHT = 0.5

MAX_STACK = 15

MESSAGE_TIME = 2.2

NO_LIGHT_COUNTDOWN = 10.0

# version 2: se agregaron pasos de practica al principio del tutorial
# version 3: se agregaron pasos de tienda (info, recoger, inventario) y de
# construccion
OBJECTIVE_VERSION = 3

OLD_OBJECTIVE_MAP = {
    0: 0, 1: 3, 2: 5, 3: 7, 4: 8, 5: 9, 6: 10, 7: 11, 8: 12,
    9: 13, 10: 14, 11: 15, 12: 16, 13: 17, 14: 18, 15: 19, 16: 20,
}

# de la numeracion de la version 2 a la 3
V2_TO_V3 = {
    11: 12, 12: 15, 13: 16, 14: 17, 15: 18, 16: 19, 17: 20,
    18: 22, 19: 23, 20: 24,
}


def v2_to_v3(index):

    index = int(index)

    if index >= 10 ** 6:
        return index

    return V2_TO_V3.get(index, index)


FLICKER_THRESHOLD = 0.25

FIRE_DAMAGE = 2
FIRE_COST = 0.02
FIRE_COOLDOWN = 0.45
FIRE_FURY_SPEED = 2.0
FIRE_MUZZLE = 8.0

FIRE_COMBO_SIZE = 3
FIRE_HEAVY_MULT = 2
FIRE_HEAVY_COST_MULT = 2.0
FIRE_HEAVY_COOLDOWN = 0.75
FIRE_COMBO_WINDOW = 1.0

FLASH_EXPAND = 0.18
FLASH_HOLD = 1.5
FLASH_FADE = 2.5
FLASH_TOTAL = FLASH_HOLD + FLASH_FADE

DARKNESS_ALPHA = 225

DOOR_GLOW_RADIUS = 55

GANZUA_DISTANCE = 48

COIN_PICKUP_DISTANCE = 14

POLVORA_TICK = 0.5

DEBUG_COINS = 100000

COIN_VALUES = {
    "moneda": 1,
    "moneda_5": 5,
    "moneda_10": 10,
}

COIN_GAIN_TIME = 2.0
COIN_GAIN_FADE = 0.5


MAGNET_RADIUS = 130
MAGNET_SPEED_FAR = 120.0
MAGNET_SPEED_NEAR = 360.0

MAGNET_PICKUP_DISTANCE = 10

# segundos que tarda el objeto en "despertar" antes de salir volando
MAGNET_WAKE = 0.14

# largo de la estela (posiciones guardadas)
MAGNET_TRAIL = 7

MAGNET_NEEDS_ITEM = True

REPEL_RING_COLOR = (120, 235, 130)

FADE_DURATION = 2.4

INTRO_TIME = 2.2

LOST_SCREEN_TIME = 3.0

DELETE_SAVE_ON_LOSS = True

NORMAL_KEEP_COINS = True

GEMS_MARGIN = (110, 100)
OBJECTIVES_TOP = 118   # y normal del objetivo (igual a ui.objectives.TOP)

ITEM_EFFECTS = {
    "madera": {"vida": 0.20},
    "cera": {"consumo": 0.5, "duracion": 20.0},
    "aceite": {"velocidad": 1.5, "duracion": 12.0},
    "resina": {"regen": 0.9, "regen_tiempo": 8.0},
    "polvora": {"polvora_dps": 10.0, "duracion": 8.0},
    "hongo_azul": {"escudo": 0.25},
}

SLOT_KEYS = {
    pygame.K_1: 0,
    pygame.K_2: 1,
    pygame.K_3: 2,
    pygame.K_4: 3,
}



def is_skin_item(item_id):

    return item_id.startswith(skin_lib.SHOP_PREFIX)


class NewGame:
    def __init__(
        self,
        screen,
        player_name="Jugador",
        save_path=None,
        save_data=None,
        mode=None
    ):

        self.screen = screen
        self.player_name = player_name
        self.save_path = save_path
        self.save_data = save_data or {}

        self.mode = normalize_mode(self.save_data.get("mode", mode))
        self._loss_applied = False
        self._defeat_counted = False
        self.width, self.height = screen.get_size()
        self.achievement_toast = AchievementToast((self.width, self.height))

        self.world_map = WorldMap()
        self.collision_map = CollisionMap()

        self.doors = DoorManager(
            self.save_data.get("broken_doors", []),
            self.save_data.get("final_door_slots"),
        )

        if self.doors.final_door is not None:
            self.doors.final_door.game = self
        self.collision_map.doors = self.doors

        self.chests = ChestManager(self.save_data.get("chests", {}))

        self.discovered_enemies = set(
            self.save_data.get("enemies_seen", [])
        )
        self.collision_map.obstacles.extend(self.chests.blocking_rects)

        self.arena = Arena((self.width, self.height), RIGHT_ARENA)
        self.arena_left = Arena((self.width, self.height), LEFT_ARENA)
        self.arenas = [self.arena, self.arena_left]

        self.crushers = CrusherBlocks(self.collision_map)

        for arena in self.arenas:
            arena.wave = max(
                1, int(self.save_data.get(arena.cfg.save_wave, 1))
            )

        self.minigame = None
        self.minigame_chest = None

        self.shopkeeper = Shopkeeper()
        self.catalog = load_catalog()
        self.shop_prices = price_table(self.catalog)
        self.shop = None

        self.shop_cart = {}

        # inventario personalizado de la tienda (se guarda en la partida)
        self.shop_inventory = [
            entry if isinstance(entry, (list, tuple)) else None
            for entry in self.save_data.get("shop_inventory", [])
        ]

        spawn_x, spawn_y = get_spawn_point(
            self.collision_map,
            "cabana"
        )

        self.player = Player(spawn_x, spawn_y)

        spawn_center = self.player.rect.center

        saved_pos = None

        if "x" in self.save_data and "y" in self.save_data:

            try:
                saved_pos = (
                    int(self.save_data["x"]),
                    int(self.save_data["y"]),
                )
            except (TypeError, ValueError):
                saved_pos = None

            if saved_pos is not None:

                self.player.rect.center = saved_pos

                self.player.image_rect.midbottom = (
                    self.player.rect.centerx,
                    self.player.rect.bottom + 3,
                )

        if self.save_data.get("current_map") != "mapa2":
            self._unstick_player(spawn_center)

        self.camera = Camera(
            self.width,
            self.height,
            self.collision_map.world_width,
            self.collision_map.world_height,
        )

        self.current_map = "mapa1"
        self.map_switch = MapSwitcher()

        self.camera.update(self.player)

        self.light = PlayerLight(
            (self.width, self.height),
            darkness_alpha=DARKNESS_ALPHA
        )

        self.fx = FxManager()
        self._intro_pending = False
        self.intro_t = None

        self.hud = Hud((self.width, self.height))

        self.pause_menu = PauseMenu(self.screen)
        self.pause_settings = None
        self.enemy_encyclopedia = None
        self.pause_view = None

        self.effects_bar = EffectsBar((self.width, self.height))
        self.effects_bar.set_alert_image(self.arena.mosquito_art.warning)

        self.tutorial = None

        self.zone_tracker = ZoneTracker()
        self._approach_current = None
        self.zone_banner = ZoneBanner((self.width, self.height))

        self.items_picked = 0

        # golpes que recibio el jugador (para el logro "Intocable")
        self.hits_taken = 0

        saved_stats = self.save_data.get("stats", {})

        self.stats = {
            "items_used": 0,
            "chests_opened": 0,
            "purchases": 0,
            "fireballs": 0,
            "kills": 0,
        }

        if isinstance(saved_stats, dict):

            for key in self.stats:
                self.stats[key] = int(saved_stats.get(key, 0))

        self.zones_seen = set(self.save_data.get("zones_seen", []))

        objective_list = self._build_objectives()

        self._objective_saved = self.save_data.get("objective_index")

        # Las partidas viejas contaban los objetivos sin los pasos nuevos
        # del tutorial: se pasa el numero viejo al que le corresponde ahora.
        saved_version = self.save_data.get("objective_version", 1)

        if (
            self._objective_saved is not None
            and saved_version < 2
            and "tuto_seen" not in self.save_data
        ):

            old = int(self._objective_saved)

            self._objective_saved = (
                OLD_OBJECTIVE_MAP.get(old, 10 ** 6)
                if old <= max(OLD_OBJECTIVE_MAP)
                else 10 ** 6
            )

        # version 2 -> 3: se corren los numeros por los pasos nuevos
        if saved_version < 3:

            if self._objective_saved is not None:
                self._objective_saved = v2_to_v3(self._objective_saved)

        if not self.save_data:
            start = 0
        elif self._objective_saved is not None:
            start = int(self._objective_saved)
        else:
            start = None

        if start is not None and start < len(objective_list):

            self.objectives = Objectives(
                (self.width, self.height),
                objective_list,
                start,
                minimized=bool(
                    self.save_data.get("objectives_minimized", False)
                ),
            )

        else:

            self.objectives = None

        # guia: flechas, lista de botones a probar y explicaciones
        # que frenan el juego al empezar cada paso
        self.guide = Guide()
        self.tuto_flags = set()
        self._tuto_last = None

        saved_seen = self.save_data.get("tuto_seen")

        if saved_seen is not None:
            self.tuto_seen = {int(i) for i in saved_seen}

            if saved_version < 3:
                self.tuto_seen = {v2_to_v3(i) for i in self.tuto_seen}
        elif self.save_data:
            self.tuto_seen = set(range(min(start or 0, 200) + 1))
        else:
            self.tuto_seen = set()

        if not self.save_data and objective_list:

            self.tuto_seen.add(0)

            self.tutorial = Tutorial(
                (self.width, self.height),
                pages=objective_list[0]["tuto"],
                can_skip=True
            )

        self.coins = int(self.save_data.get("coins", 0))

        self.gems = int(self.save_data.get("gems", 0))

        # la entrada epica del jefe se muestra completa solo la primera vez
        self.boss_intro_seen = bool(
            self.save_data.get("boss_intro_seen", False)
        )

        self.gems_green = int(self.save_data.get("gems_green", 0))

        # usos ya gastados de la ganzua que se esta usando (dura varios usos)
        self.ganzua_uses = int(self.save_data.get("ganzua_uses", 0))


        self.has_match = bool(self.save_data.get("has_match", False))

        self.vida = max(
            0.0,
            min(1.0, float(self.save_data.get("vida", 1.0)))
        )

        self.escudo = max(
            0.0,
            min(1.0, float(self.save_data.get("escudo", 0.0)))
        )

        self.light_type = self.save_data.get("light", "fosforo")

        if self.light_type not in LIGHTS:
            self.light_type = "fosforo"

        self.base_burn = 1.0

        self.melee = Melee()

        self.attack_mode = "golpe"
        self.fireballs = []
        self.fire_bursts = []
        self.fire_cooldown = 0.0
        self.fire_combo = 0
        self.fire_combo_timer = 0.0
        self._fire_hold = False

        self.flash_t = 0.0
        self.flash_pos = (0.0, 0.0)
        self._flash_surf = None

        for arena in self.arenas:

            arena.completed = bool(
                self.save_data.get(arena.cfg.save_done, False)
            )

            arena.restore_completed(self)

        self.fury_timer = 0.0
        self.fury_left = 0.0

        self.light_drops = []

        if self.has_match:
            self.equip_match(self.light_type)
        else:
            start_match = LightItem("fosforo", *MATCH_POS)
            start_match.initial = True
            self.light_drops.append(start_match)


        self.item_defs = load_item_defs()

        saved_inv = self.save_data.get("inventory", [])

        for i in range(self.hud.SLOTS):

            if i >= len(saved_inv):
                break

            entry = saved_inv[i]

            if entry is None:
                continue

            if isinstance(entry, (list, tuple)) and len(entry) == 2:
                item_id, count = entry[0], int(entry[1])
            else:
                item_id, count = entry, 1

            if item_id in COIN_VALUES and count > 0:

                self.coins += COIN_VALUES[item_id] * count
                continue

            if item_id in LIGHTS and count > 0:

                for _ in range(count):

                    px, py = self.player.rect.center

                    self.light_drops.append(
                        LightItem(
                            item_id,
                            px + random.randint(-12, 12),
                            py
                        )
                    )

                continue

            if item_id in self.item_defs and count > 0:

                self.hud.items[i] = item_id
                self.hud.counts[i] = min(
                    count,
                    self._max_stack(item_id)
                )

        self.collected = set(
            self.save_data.get("collected", [])
        )

        self.item_seed = self.save_data.get(
            "item_seed",
            random.randint(0, 10 ** 9)
        )

        self.world_items = make_spawn_items(
            load_spawn_zones(),
            self.item_defs,
            self.collision_map,
            self.item_seed,
            self.collected
        )

        # items que se soltaron al morir: quedan guardados en el mapa
        self._death_dropped = False
        self._force_home = False
        self.pending_drops = {}

        for entry in self.save_data.get("death_drops", []):

            if isinstance(entry, dict):
                self.pending_drops.setdefault(
                    entry.get("map", "mapa1"), []
                ).append(entry)

        drop_items, drop_lights = self.materialize_drops("mapa1")

        self.world_items.extend(drop_items)
        self.light_drops.extend(drop_lights)

        if self.save_data.get("current_map") == "mapa2":

            enter_map(self, "mapa2", saved_pos)

        print(
            f"[items] {len(self.item_defs)} tipos de item, "
            f"{len(self.world_items)} objetos en el mapa"
        )

        self.placeables = PlaceableManager(
            self.save_data.get("placeables", [])
        )

        self.debug_items = False
        self._font_cache = {}

        self.speed_timer = 0.0
        self.burn_factor = 1.0
        self.burn_timer = 0.0

        self.speed_total = 1.0
        self.burn_total = 1.0
        self.polvora_total = 1.0
        self.regen_total = 1.0

        self.polvora_timer = 0.0
        self.polvora_dps = 0.0
        self._polvora_acc = 0.0

        self.regen_left = 0.0
        self.regen_rate = 0.0

        self.repel_timer = 0.0
        self.repel_total = 1.0

        self.magnet_timer = 0.0
        self.magnet_total = 1.0

        self.magnet_mode = False
        self._magnet_imgs = None

        self.dungeon_map = DungeonMapView()
        self._map_hold = False

        self.sphere_timer = 0.0
        self.sphere_total = 1.0
        self.sphere_mult = 1.0

        self.coin_gain = 0
        self.coin_gain_timer = 0.0

        self._light_radius_px = self._light_radius()


        self.melee.set_light(self.light_type)

        self.dummies = []

        self.slimes = SlimeManager()

        self.last_heal = 0.0

        self.debug_combat = False

        self.message = ""
        self.message_timer = 0.0

        self.no_light_timer = None

        self.selected_slot = "equipped"

        self.state = "playing"

        self.fade_alpha = 0
        self.lost_timer = 0

        self._flicker_time = 0.0

        self._gem_icon = None
        self._gem_green_icon = None

        ui_dir = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
        )

        def _lost_img(name):
            return pygame.transform.smoothscale(
                pygame.image.load(str(ui_dir / name)).convert(),
                (self.width, self.height)
            )

        self.pantalla_perdiste = _lost_img("pantalla_perdiste.png")
        self.pantalla_perdiste_normal = _lost_img("pantalla_perdiste2.png")

        self.fade_overlay = pygame.Surface(
            (self.width, self.height)
        )

        self.fade_overlay.fill((0, 0, 0))


    def _unstick_player(self, fallback_center, max_radius=120):

        rect = self.player.rect

        if self.collision_map.can_move(rect):
            return

        origin = rect.center

        for radius in range(1, max_radius + 1):

            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):

                    if max(abs(dx), abs(dy)) != radius:
                        continue

                    test = rect.copy()
                    test.center = (origin[0] + dx, origin[1] + dy)

                    if self.collision_map.can_move(test):

                        rect.center = test.center

                        self.player.image_rect.midbottom = (
                            rect.centerx,
                            rect.bottom + 3,
                        )

                        return

        self.player.rect.center = fallback_center

        self.player.image_rect.midbottom = (
            self.player.rect.centerx,
            self.player.rect.bottom + 3,
        )

    def _font(self, size):

        font = self._font_cache.get(size)

        if font is None:
            font = pygame.font.Font(None, size)
            self._font_cache[size] = font

        return font


    def take_damage(self, amount):

        if amount <= 0:
            return

        audio.play("hurt")

        self.hits_taken += 1

        self.fx.player_hurt(*self.player.rect.center)

        absorbed = min(self.escudo, amount)

        self.escudo -= absorbed
        self.vida -= amount - absorbed

        if self.escudo < 1e-6:
            self.escudo = 0.0


    def equip_match(self, kind=None, life=None):

        left = getattr(self, "no_light_timer", None)

        if left is not None and 0 < left < 2.0:
            achievements.unlock("ultimo_segundo")

        if kind in LIGHTS:
            self.light_type = kind

        if life is not None:
            self.vida = max(
                0.0,
                min(1.0, float(life))
            )

        self.base_burn = light_stats(
            self.light_type
        )["consumo"]

        self.has_match = True

        self.hud.equip(
            self.light_type
        )

        self.player.set_torch(
            True,
            self.light_type
        )

        self.melee.set_light(
            self.light_type
        )

        self.attack_mode = "golpe"
        self.fire_combo = 0

        self._reset_fury()

    def _reset_fury(self):

        self.fury_left = 0.0

        self.fury_timer = light_stats(
            self.light_type
        ).get(
            "furia_cada",
            0
        )

        self.melee.set_fury(1.0)

    def _update_fury(self, dt):

        if not self.has_match:

            if self.fury_left > 0 or self.melee.fury:
                self._reset_fury()

            return

        stats = light_stats(
            self.light_type
        )

        every = stats.get(
            "furia_cada",
            0
        )

        length = stats.get(
            "furia_duracion",
            0
        )

        if every <= 0 or length <= 0:
            return

        if self.fury_left > 0:

            self.fury_left -= dt

            if self.fury_left <= 0:

                self.fury_left = 0.0
                self.fury_timer = every

                self.melee.set_fury(
                    1.0
                )

        else:

            self.fury_timer -= dt

            if self.fury_timer <= 0:

                self.fury_left = length

                self.melee.set_fury(
                    stats.get(
                        "furia_velocidad",
                        1.0
                    )
                )

    def _light_radius(self):

        radius = light_stats(
            self.light_type
        )["radio"]

        if self.sphere_timer > 0:
            radius *= self.sphere_mult

        return radius

    def _nearest_light_drop(self):

        near = [
            d
            for d in self.light_drops
            if d.is_near(self.player)
        ]

        if not near:
            return None

        px, py = self.player.rect.center

        return min(
            near,
            key=lambda d:
                pygame.Vector2(
                    d.rect.center
                ).distance_to(
                    (px, py)
                )
        )

    def _drop_match(self):

        x, y = self.player.rect.center

        self.light_drops.append(
            LightItem(
                self.light_type,
                x,
                y,
                life=self.vida
            )
        )

        self.has_match = False

        self.hud.equip(None)

        self.player.set_torch(False)

    def _burn_out(self):

        audio.play("light_out")

        self.vida = 0.0

        self.base_burn = 1.0

        self.regen_left = 0.0

        self.has_match = False

        self.hud.equip(None)

        self.player.set_torch(False)

        self._reset_fury()


    TUTO_KEYS = {
        pygame.K_w: "w",
        pygame.K_a: "a",
        pygame.K_s: "s",
        pygame.K_d: "d",
        pygame.K_1: "slotkey",
        pygame.K_2: "slotkey",
        pygame.K_3: "slotkey",
        pygame.K_4: "slotkey",
        pygame.K_5: "k5",
        pygame.K_ESCAPE: "esc",
        pygame.K_TAB: "tab",
        pygame.K_F1: "f1",
    }

    def _record_tuto_input(self, event):

        if self.state != "playing" or self.objectives is None:
            return

        if event.type == pygame.KEYDOWN:

            action = controls.action_for(event.key)

            if action in ("up", "down", "left", "right"):
                name = {
                    "up": "w",
                    "down": "s",
                    "left": "a",
                    "right": "d",
                }[action]

            elif action in SLOT_ACTIONS:
                name = "slotkey"

            elif action == "equipped":
                name = "k5"

            elif event.key in (
                pygame.K_ESCAPE,
                pygame.K_TAB,
                pygame.K_F1
            ):
                name = self.TUTO_KEYS.get(event.key)

            else:
                name = None

            if name:
                self.tuto_flags.add(name)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            self.tuto_flags.add("click_l")

        elif event.type == pygame.MOUSEWHEEL and event.y != 0:

            self.tuto_flags.add("wheel")

    def _skip_tutorial(self):

        self.tutorial = None
        self.objectives = None
        self._objective_saved = 10 ** 6
        self.tuto_flags = set()

        self.tuto_seen = set(range(200))

        self.show_message("Tutorial sacado. Con F1 volvés a ver la ayuda")

        self._save()

    def _tuto_step_check(self):

        obj = self.objectives

        if obj is None or not obj.started:
            return

        idx = obj.index

        if idx == self._tuto_last:
            return

        self._tuto_last = idx
        self.tuto_flags = set()

        if idx >= len(obj.objectives) or idx in self.tuto_seen:
            return

        self.tuto_seen.add(idx)

        pages = obj.objectives[idx].get("tuto")

        if pages and self.tutorial is None:

            self.tutorial = Tutorial(
                (self.width, self.height), pages=pages, can_skip=True
            )

    def _draw_guidance(self):

        obj = self.objectives

        if (
            obj is None or obj.finished or not obj.started
            or obj.index >= len(obj.objectives)
            or self.tutorial is not None
            or self.shop is not None
            or self.minigame is not None
            or self.pause_view is not None
        ):
            return

        step = obj.objectives[obj.index]

        if obj.phase == "done":
            return

        checks = step.get("checks")

        if checks is not None:
            self.guide.draw_checklist(self.screen, checks(self))

        target_fn = step.get("target")

        if (
            target_fn is None
            or getattr(self, "current_map", "mapa1") != "mapa1"
        ):
            return

        target = target_fn(self)

        if target is not None:

            self.guide.draw_arrow(
                self.screen, self.camera, self.player.rect, target
            )

    def count_stat(self, name, amount=1):

        self.stats[name] = self.stats.get(name, 0) + amount

    def _build_objectives(self):

        def in_combat(g):

            return any(
                a.state in (a.WAVE, a.CLEAR, a.COLLECT)
                or a.wave >= 2
                or a.completed
                for a in g.arenas
            )

        def flag(name):

            return lambda g: name in g.tuto_flags

        def checks_done(checks):

            return lambda g: all(ok for _, ok in checks(g))

        def zone_center(zone_id):

            for zone in ZONES:
                if zone.id == zone_id:
                    return zone.rect.center

            return None

        def door_point(door_id):

            for entry in DOOR_LAYOUT:
                if entry[0] == door_id:
                    return (entry[3], entry[4])

            return None

        def nearest(g, points):

            points = [p for p in points if p is not None]

            if not points:
                return None

            px, py = g.player.rect.center

            return min(
                points,
                key=lambda p: (p[0] - px) ** 2 + (p[1] - py) ** 2
            )

        def item_points(g, coins):

            return [
                it.rect.center
                for it in g.world_items
                if str(getattr(it, "item_id", "")).startswith("moneda")
                == coins
                and getattr(it, "fly", None) is None
            ]

        def light_point(g):

            return nearest(
                g, [d.rect.center for d in g.light_drops]
            ) or MATCH_POS

        def hotbar_empty(g):

            return all(i is None for i in g.hud.items)

        def move_checks(g):

            return [
                ("W  (arriba)", "w" in g.tuto_flags),
                ("A  (izquierda)", "a" in g.tuto_flags),
                ("S  (abajo)", "s" in g.tuto_flags),
                ("D  (derecha)", "d" in g.tuto_flags),
            ]

        def attack_checks(g):

            return [
                ("Click izquierdo", "click_l" in g.tuto_flags),
            ]

        def slot_checks(g):

            return [
                ("Teclas 1 a 4 (casilleros)", "slotkey" in g.tuto_flags),
                ("Tecla 5 (tu luz)", "k5" in g.tuto_flags),
                ("Ruedita del mouse", "wheel" in g.tuto_flags),
            ]

        def use_checks(g):

            return [
                ("Usar un objeto (F o click derecho)",
                 "used" in g.tuto_flags),
                ("Soltar un objeto (Q)", "dropped" in g.tuto_flags),
            ]

        def help_checks(g):

            return [
                ("ESC: pausa (volvé con ESC)", "esc" in g.tuto_flags),
                ("TAB: ocultar el objetivo", "tab" in g.tuto_flags),
                ("F1: ver la ayuda", "f1" in g.tuto_flags),
            ]

        return [

            {
                "text": (
                    "Está oscuro: buscá el fósforo del piso (te lo marca "
                    "la flecha) y agarralo con E. Si en "
                    f"{int(NO_LIGHT_COUNTDOWN)} segundos no tenés luz, perdés."
                ),
                "tuto": [
                    "¡Bienvenido a Keep It Lit! Tu luz es tu vida: la barra naranja de abajo. Se gasta con el tiempo y, si se apaga, perdés.",
                    "Está oscuro. Una flecha naranja te va a guiar. Movete con W A S D hasta el fósforo del piso y agarralo con E. Tenés 10 segundos sin luz antes de perder.",
                ],
                "target": light_point,
                "done": lambda g: g.has_match,
            },
            {
                "text": "Probá moverte con las cuatro teclas: W, A, S y D.",
                "tuto": [
                    "¡Ya tenés luz! Ahora vamos a practicar. MOVERTE: probá las cuatro teclas W A S D, una por una. La lista de arriba se tilda sola.",
                ],
                "checks": move_checks,
                "done": checks_done(move_checks),
            },
            {
                "text": (
                    "Probá atacar con click izquierdo. "
                    "Cada golpe gasta un poco de luz."
                ),
                "tuto": [
                    "ATACAR: click izquierdo. Cada golpe gasta un poco de luz, así que no pegues de más. Probalo.",
                ],
                "checks": attack_checks,
                "done": checks_done(attack_checks),
            },
            {
                "text": (
                    "Agarrá un objeto del piso con E (madera, resina, "
                    "aceite): sirven para que tu luz no se apague."
                ),
                "tuto": [
                    "AGARRAR: acercate a un objeto del piso (madera, resina, aceite) y apretá E. Sirven para recuperar luz. Seguí la flecha.",
                ],
                "target": lambda g: nearest(g, item_points(g, False)),
                "done": lambda g: g.items_picked > 0,
            },
            {
                "text": (
                    "Probá elegir casilleros: teclas 1 a 4, la tecla 5 "
                    "(tu luz) y la ruedita del mouse."
                ),
                "tuto": [
                    "INVENTARIO: tenés 4 casilleros (teclas 1 al 4) y la tecla 5 elige tu luz equipada. También podés recorrerlos con la RUEDITA. Probá las tres cosas.",
                ],
                "checks": slot_checks,
                "done": checks_done(slot_checks),
            },
            {
                "text": (
                    "Usá un objeto (F o click derecho) y soltá otro con Q. "
                    "Si te quedás sin objetos, agarrá más del piso."
                ),
                "tuto": [
                    "USAR: elegí un casillero con un objeto y apretá F o click derecho. SOLTAR: con Q tirás el objeto elegido. Probá las dos. Podés volver a agarrar con E.",
                    "OBJETOS: la madera suma 25% de luz, la resina recupera 90% de a poco y el aceite la deja en 75% y te da velocidad. La GELEA (la sueltan los slimes) cura al azar. Usalos ANTES de quedarte sin luz.",
                ],
                "target": lambda g: (
                    nearest(g, item_points(g, False))
                    if hotbar_empty(g) else None
                ),
                "checks": use_checks,
                "done": checks_done(use_checks),
            },
            {
                "text": (
                    "Probá los botones de ayuda: ESC (pausa), TAB "
                    "(ocultar el objetivo) y F1 (ayuda)."
                ),
                "tuto": [
                    "AYUDA: ESC abre la pausa (ahí está la enciclopedia de criaturas), TAB esconde o muestra el objetivo y F1 vuelve a mostrar la ayuda completa. Probá las tres.",
                ],
                "checks": help_checks,
                "done": checks_done(help_checks),
            },
            {
                "text": (
                    "Salí de la cabaña: pegale a la puerta con click "
                    "izquierdo hasta romperla. Cada golpe "
                    "gasta luz."
                ),
                "tuto": [
                    "PUERTAS: pegale a la puerta con tu luz (click izquierdo) hasta romperla. Cada golpe gasta luz, y cada tipo de puerta pide una luz distinta. Seguí la flecha.",
                ],
                "target": lambda g: door_point("cabana"),
                "done": lambda g: "cabana" in g.doors.broken_ids,
            },
            {
                "text": "Seguí el camino al norte hasta la sala central.",
                "tuto": [
                    "Seguí el camino hacia el norte. La flecha te lleva hasta la sala central, que conecta todo el mapa.",
                ],
                "target": lambda g: zone_center("central"),
                "done": lambda g: "central" in g.zones_seen,
            },
            {
                "text": (
                    "Juntá 10 monedas: hay tiradas por el mapa, en los "
                    "cofres y las sueltan los slimes (matalos a golpes)."
                ),
                "tuto": [
                    "MONEDAS: sirven para comprar luces y objetos en la tienda. Se juntan solas al acercarte. Hay tiradas por el mapa y en los cofres. Juntá 10 siguiendo la flecha.",
                    "SLIMES: son criaturas tranquilas que andan por la sala central y la de cofres. No te atacan: pegales con tu luz hasta matarlos. Sueltan 10 monedas y una gelea que te cura al comerla.",
                ],
                "target": lambda g: nearest(g, item_points(g, True)),
                "done": lambda g: g.coins >= 10 or g.stats["purchases"] > 0,
            },
            {
                "text": (
                    "Andá a la tienda (al norte de la sala central) y "
                    "apretá F cerca del vendedor para hablarle."
                ),
                "tuto": [
                    "TIENDA: está al norte de la sala central. Acercate al vendedor hasta que aparezca la tecla F y apretala para abrir la tienda. Se cierra con E o ESC.",
                    "Ahí gastás las monedas en luces, objetos y construcciones. Cada producto muestra su precio. Algunos están bloqueados hasta llegar a cierta oleada en las salas de combate.",
                ],
                "target": lambda g: g.shopkeeper.TALK_RECT.center,
                "done": flag("shop_opened"),
            },
            {
                "text": (
                    "Con la tienda abierta, hacé click con la RUEDITA del "
                    "mouse sobre un producto para ver qué hace."
                ),
                "tuto": [
                    "INFO: apuntá a un producto y hacé click con la ruedita del mouse (el botón del medio). Te explica qué hace y, en las luces, cuánto duran y cuánto pegan. Otro click la cierra.",
                ],
                "target": lambda g: (
                    g.shopkeeper.TALK_RECT.center
                    if g.shop is None else None
                ),
                "done": flag("shop_info"),
            },
            {
                "text": (
                    "Comprale algo al vendedor: elegí un objeto, la "
                    "cantidad y apretá Comprar."
                ),
                "tuto": [
                    "COMPRAR: click en un producto lo suma al carrito, click derecho saca uno y el botón x15 suma 15 de golpe. Abajo ves el total y el tachito vacía el carrito.",
                    "Cuando estés listo, apretá Comprar. Si no te alcanzan las monedas no cobra nada: sacá algo del carrito o juntá más. Conviene comprar un objeto (madera, cera...).",
                ],
                "done": lambda g: g.stats["purchases"] >= 1,
            },
            {
                "text": (
                    "El vendedor escupe lo que comprás: agarralo del piso "
                    "con E."
                ),
                "tuto": [
                    "LO COMPRADO: el vendedor lo escupe al piso, cerca de él. Acercate y apretá E para agarrarlo. Con el imán (tecla O) los objetos sueltos se juntan solos.",
                ],
                "target": lambda g: (
                    nearest(
                        g,
                        item_points(g, False)
                        + [d.rect.center for d in g.light_drops]
                    )
                ),
                "done": flag("picked"),
            },
            {
                "text": (
                    "Volvé a abrir la tienda (F) y apretá TAB para ir a la "
                    "pestaña Inventario."
                ),
                "tuto": [
                    "INVENTARIO DE LA TIENDA: con TAB cambiás entre Tienda e Inventario. En Inventario armás tus casilleros y tu luz como quieras y comprás todo junto con 'Comprar inventario'. Probalo con TAB.",
                ],
                "target": lambda g: (
                    g.shopkeeper.TALK_RECT.center
                    if g.shop is None else None
                ),
                "done": flag("shop_inv"),
            },
            {
                "text": (
                    "Andá a la sala de cofres (arriba a la izquierda). "
                    "Acercate a un cofre y apretá F, después ESPACIO en la "
                    "zona marcada para abrirlo."
                ),
                "tuto": [
                    "COFRES: están en la sala de arriba a la izquierda. Acercate y apretá F (cuenta como un golpe) y después ESPACIO cuando el marcador esté en la zona marcada.",
                    "Cada cofre se abre de 10 a 15 veces seguidas y después descansa 3 minutos. Dan monedas, madera, cera, aceite... y con suerte una GANZÚA, que abre un cofre sin minijuego y dura 3 usos.",
                ],
                "target": lambda g: zone_center("cofres"),
                "done": lambda g: g.stats["chests_opened"] >= 1,
            },
            {
                "text": (
                    "Conseguí una vela, una luz mejor que el fósforo: "
                    "solo se consigue en la tienda y cuesta 55 monedas. "
                    "Soltá el fósforo antes (casillero de luz y Q)."
                ),
                "tuto": [
                    "LUCES: la vela ilumina más y dura más que el fósforo. Solo se consigue en la tienda (los cofres no la dan) y cuesta 55 monedas.",
                    "CAMBIAR DE LUZ: solo podés tener una luz equipada. Si agarrás otra con el fósforo en la mano, no se cambia: tenés que soltar el fósforo primero. Elegí el casillero de la luz (el aislado) y apretá Q. Después agarrá la vela con E y se equipa sola.",
                ],
                "target": lambda g: (
                    nearest(g, [d.rect.center for d in g.light_drops])
                    or g.shopkeeper.TALK_RECT.center
                ),
                "done": lambda g: (
                    g.has_match and g.light_type in ("vela", "antorcha")
                ),
            },
            {
                "text": (
                    "Pegale con tu vela a una puerta gris de la sala "
                    "central para romperla."
                ),
                "tuto": [
                    "PUERTAS: las puertas grises de la sala central llevan a las zonas de combate. Se rompen solo con vela o antorcha. Seguí la flecha.",
                ],
                "target": lambda g: door_point("sala_der"),
                "done": lambda g: "sala_der" in g.doors.broken_ids,
            },
            {
                "text": (
                    "Entrá a una zona de combate y elegí cómo "
                    "jugar: con escape o sin escape (premio doble)."
                ),
                "tuto": [
                    "ZONAS DE COMBATE: tienen oleadas de enemigos. Antes de entrar te avisa el nombre de la zona y al entrar elegís cómo jugar.",
                    "JUGAR CON ESCAPE: la salida queda abierta, así que si te complicás podés irte caminando y volver después. El premio es el normal. Ideal para aprender.",
                    "JUGAR SIN ESCAPE (X2 PREMIO): la salida se cierra hasta que termines la oleada. No podés huir, pero ganás el doble de monedas. Si tu luz se apaga, perdés.",
                ],
                "target": lambda g: zone_center("combate"),
                "done": lambda g: (
                    g.arena.state in (
                        g.arena.WAVE, g.arena.CLEAR, g.arena.COLLECT
                    )
                    or g.arena.wave >= 2
                    or g.arena.completed
                ),
            },
            {
                "text": (
                    "Derrotá a todos los enemigos de la oleada pegándoles "
                    "con tu luz y juntá las monedas del premio."
                ),
                "tuto": [
                    "COMBATE: pegales a los enemigos con tu luz hasta eliminarlos a todos. Cuando termine la oleada aparece el premio: juntá las monedas. Cada golpe gasta un poco de luz, así que no pegues al aire.",
                    "CUIDADO: los mosquitos se te pegan y chupan tu luz; matalos rápido. Usá tus objetos (madera, cera, aceite) a tiempo para que tu luz dure más. Entre oleadas podés irte o seguir.",
                    "PREMIOS: al terminar cada oleada ganás monedas. Al completar todas las oleadas de una zona ganás una gema, que sirve para abrir la puerta final del mapa.",
                ],
                "done": lambda g: any(
                    a.wave >= 2 or a.completed for a in g.arenas
                ),
            },
            {
                "text": (
                    "Conseguí la antorcha: con G cambiás de golpe y "
                    "lanzás una bola de fuego. ¡Probala!"
                ),
                "tuto": [
                    "ANTORCHA: se desbloquea en la tienda al llegar a la oleada 6. Con G cambiás de golpe y lanzás una bola de fuego. ¡Probala!",
                ],
                "target": lambda g: (
                    None
                    if g.has_match and g.light_type == "antorcha"
                    else g.shopkeeper.TALK_RECT.center
                ),
                "done": lambda g: g.stats["fireballs"] >= 1,
            },
            {
                "text": (
                    "Armá una base: comprá una fogata en la tienda, "
                    "elegila en tu casillero y hacé click en el mapa para "
                    "ponerla."
                ),
                "tuto": [
                    "CONSTRUIR: la sección Construcción de la tienda vende bolsa, cofre, fogata y candil. La bolsa y el candil salen al piso y los movés con click izquierdo mantenido. El cofre y la fogata los elegís en tu casillero y hacés click en el mapa: quedan fijos para siempre.",
                    "La FOGATA ilumina mucho y te devuelve luz mientras estés cerca: dale madera con F o click derecho. El CANDIL es más chico y come cera. Ideales como base de descanso entre oleadas.",
                ],
                "target": lambda g: (
                    None
                    if any(
                        o.kind in ("fogata", "faro")
                        for o in g.placeables.objects
                    )
                    else g.shopkeeper.TALK_RECT.center
                ),
                "done": lambda g: any(
                    o.kind in ("fogata", "faro")
                    for o in g.placeables.objects
                ),
            },
            {
                "text": (
                    "Completá Orkun (zona 1, derecha): 10 oleadas, un "
                    "jefe y una gema verde clara te esperan."
                ),
                "target": lambda g: zone_center("combate"),
                "done": lambda g: g.arena.completed,
            },
            {
                "text": (
                    "Ahora sí, Stonun (zona 2, izquierda, la del "
                    "Guardián): 10 oleadas y una gema verde oscuro."
                ),
                "target": lambda g: zone_center("combate_izq"),
                "done": lambda g: g.arena_left.completed,
            },
            {
                "text": (
                    "Completá la enciclopedia: descubrí los "
                    f"{len(EnemyEncyclopedia.ORDER)} criaturas del juego "
                    "(la abrís desde la pausa con ESC)."
                ),
                "done": lambda g: len(
                    set(g.discovered_enemies) & set(EnemyEncyclopedia.ORDER)
                ) >= len(EnemyEncyclopedia.ORDER),
            },
        ]

    def _check_achievements(self):

        if self.arena.completed:
            achievements.unlock("zona_1")

        if self.arena_left.completed:
            achievements.unlock("zona_2")

        if getattr(self, "current_map", "mapa1") == "mapa2":
            achievements.unlock("region_1")

        if self.mode == MODE_HARDCORE and (
            self.arena.completed or self.arena_left.completed
        ):
            achievements.unlock("sin_red")

        if not achievements.is_unlocked("coctel"):

            effects = set(self._active_effects()) - {"mosquito", "furia"}

            if len(effects) >= 3:
                achievements.unlock("coctel")

    def show_message(self, text):

        self.message = text
        self.message_timer = MESSAGE_TIME

    def _max_stack(self, item_id):

        return int(
            self.item_defs.get(item_id, {}).get(
                "max_pila",
                MAX_STACK
            )
        )

    def _item_name(self, item_id):

        return self.item_defs.get(item_id, {}).get(
            "nombre",
            str(item_id).replace("_", " ")
        )

    def _nearest_item(self):

        near = [
            it
            for it in self.world_items
            if it.is_near(self.player)
        ]

        if not near:
            return None

        px, py = self.player.rect.center

        return min(
            near,
            key=lambda it:
                pygame.Vector2(
                    it.rect.center
                ).distance_to(
                    (px, py)
                )
        )

    def _nearest_pickup(self):

        px, py = self.player.rect.center
        me = pygame.Vector2(px, py)

        best = (None, None)
        best_dist = None

        if not self.has_match:

            light = self._nearest_light_drop()

            if light is not None:

                best = ("light", light)
                best_dist = pygame.Vector2(light.rect.center).distance_to(me)

        item = self._nearest_item()

        if item is not None:

            d = pygame.Vector2(item.rect.center).distance_to(me)

            if best_dist is None or d < best_dist:
                best = ("item", item)

        return best

    def pick_up_item(self, item):

        item_id = item.item_id

        if getattr(item, "_mag_t", 0) > 0:

            # llego por el iman: absorbe con destello y onda
            self.fx.magnet_absorb(
                item.rect.centerx, item.rect.centery,
                self.fx.item_color(item)
            )

        if item_id in COIN_VALUES:

            value = getattr(item, "value", None)

            if value is None:
                value = COIN_VALUES[item_id]

            self.add_coins(int(value))

            self.fx.coin(item.rect.centerx, item.rect.centery, int(value))

        elif item_id == "gema":

            self.gems += int(getattr(item, "value", 1))

            audio.play("gem")

        elif item_id == "gema_verde":

            self.gems_green += int(getattr(item, "value", 1))

            audio.play("gem")

        else:

            slot = self._free_slot_for(item_id)

            if slot is None:
                self.show_message("Inventario lleno")
                return

            if self.hud.items[slot] is None:

                self.hud.items[slot] = item_id
                self.hud.counts[slot] = 1

            else:

                self.hud.counts[slot] += 1

            self.items_picked += 1

            self.tuto_flags.add("picked")

            audio.play("pickup")

            self.show_message(
                f"Agarraste {self._item_name(item_id)}"
            )

        for attr in ("key", "uid", "spawn_id", "id"):

            value = getattr(item, attr, None)

            if value is not None:

                self.collected.add(value)
                break

        if item in self.world_items:
            self.world_items.remove(item)

    def add_coins(self, amount):

        amount = int(amount)

        if amount <= 0:
            return

        self.coins += amount

        if self.coins >= 500:
            achievements.unlock("dragon_monedas")

        audio.play("coin_big" if amount >= 5 else "coin")

        if self.coin_gain_timer <= 0:
            self.coin_gain = 0

        self.coin_gain += amount
        self.coin_gain_timer = COIN_GAIN_TIME

    def _free_slot_for(self, item_id):

        limit = self._max_stack(item_id)

        for i in range(self.hud.SLOTS):

            if (
                self.hud.items[i] == item_id
                and self.hud.counts[i] < limit
            ):
                return i

        for i in range(self.hud.SLOTS):

            if self.hud.items[i] is None:
                return i

        return None

    def drop_item(self, slot):

        item_id = self.hud.items[slot]

        if item_id is None:
            return

        x, y = self.player.rect.center

        self.world_items.append(
            WorldItem(
                item_id,
                x + random.randint(-12, 12),
                y + random.randint(-12, 12)
            )
        )

        self._take_one(slot)

        self.tuto_flags.add("dropped")

        if self._magnet_active():

            self.show_message(
                "Apagá el imán (O) para soltar items"
            )

    def drop_all_items(self):
        """Suelta TODO el inventario (los 4 casilleros, con todas sus unidades).

        La luz equipada se queda con vos.
        """

        x, y = self.player.rect.center

        dropped = 0

        for slot in range(self.hud.SLOTS):

            item_id = self.hud.items[slot]

            if item_id is None:
                continue

            for _ in range(max(1, int(self.hud.counts[slot]))):

                self.world_items.append(
                    WorldItem(
                        item_id,
                        x + random.randint(-18, 18),
                        y + random.randint(-18, 18)
                    )
                )

                dropped += 1

            self.hud.items[slot] = None
            self.hud.counts[slot] = 0

        if dropped:

            self.tuto_flags.add("dropped")

            if self._magnet_active():

                self.show_message(
                    "Apagá el imán (O) para soltar items"
                )

        else:

            self.show_message("No tenés nada para soltar")

    def _take_one(self, slot):

        self.hud.counts[slot] -= 1

        if self.hud.counts[slot] <= 0:

            self.hud.items[slot] = None
            self.hud.counts[slot] = 0

    def use_item(self, slot):

        item_id = self.hud.items[slot]

        if item_id is None:
            return

        if item_id == "mapa":

            self.show_message(
                "Mantené click derecho para ver el mapa"
            )
            return

        if self.placeables.try_use(self, slot):
            return

        item = self.item_defs.get(item_id, {})

        if item.get("tipo") == "luz":

            self.show_message(
                "Las luces se equipan solas al agarrarlas (soltá antes la que tenés)"
            )
            return

        fed_obj = self.placeables.feed_target(self, item_id)

        vida_antes = self.vida

        efectos = item.get("efectos")

        if efectos:

            can_effect = not (
                item.get("requiere_fosforo") and not self.has_match
            )

            if not can_effect and fed_obj is None:

                self.show_message(
                    "Necesitas una luz encendida"
                )
                return

            used = False

            if can_effect:

                for efecto in efectos:

                    if self._apply_item_effect(efecto):
                        used = True

            if not used and fed_obj is None:
                return

        else:

            legacy = (
                item.get("efecto")
                or ITEM_EFFECTS.get(item_id)
            )

            if not legacy and fed_obj is None:

                self.show_message("Eso no se puede usar")
                return

            if legacy:
                self._apply_effect(legacy)

        if item_id == "ganzua":

            # la ganzua no se gasta de una: dura varios usos
            usos = max(1, int(item.get("usos", 3)))

            self.ganzua_uses += 1

            if self.ganzua_uses < usos:

                self.count_stat("items_used")

                self.tuto_flags.add("used")

                self.show_message(
                    f"Ganzúa: te quedan {usos - self.ganzua_uses} usos"
                )

                return

            self.ganzua_uses = 0

        self._take_one(slot)

        self.count_stat("items_used")

        self.tuto_flags.add("used")

        if fed_obj is not None:

            self.placeables.feed(self, fed_obj, item_id)

            curado = round((self.vida - vida_antes) * 100)

            texto = (
                f"{self._item_name(fed_obj.kind)}: "
                f"{int(fed_obj.fuel)} s de luz"
            )

            if curado > 0:
                texto += f"  (+{curado}% de luz)"

            self.show_message(texto)

        elif item_id == "iman":

            self.show_message(
                f"Usaste Imán: apretá {controls.label('magnet')} para activarlo o desactivarlo"
            )

        elif item_id == "gelea":

            self.show_message(
                f"Comiste una gelea: curaste {round(self.last_heal * 100)}%"
            )

        else:

            self.show_message(
                f"Usaste {self._item_name(item_id)}"
            )

    def _apply_item_effect(self, e):

        tipo = e.get("tipo")

        if tipo == "vida_sumar":

            self.vida = min(
                1.0,
                self.vida + float(e.get("valor", 0.0))
            )

        elif tipo == "vida_azar":

            opciones = e.get("opciones") or [0.15, 0.45, 0.88]
            pesos = e.get("pesos") or [1] * len(opciones)

            valor = float(
                random.choices(opciones, weights=pesos, k=1)[0]
            )

            self.vida = min(1.0, self.vida + valor)
            self.last_heal = valor

        elif tipo == "vida_fijar":

            self.vida = max(
                0.0,
                min(1.0, float(e.get("valor", self.vida)))
            )

        elif tipo == "vida_gradual":

            seconds = max(0.1, float(e.get("duracion", 10.0)))

            self.regen_left += float(e.get("valor", 0.0))
            self.regen_total = max(self.regen_left, 0.001)
            self.regen_rate = self.regen_left / seconds

        elif tipo == "velocidad":

            self.player.movement.speed_mult = float(
                e.get("multiplicador", 1.0)
            )
            self.speed_total = float(e.get("duracion", 10.0))
            self.speed_timer = self.speed_total

        elif tipo == "consumo_lento":

            self.burn_factor = float(e.get("factor", 1.0))
            self.burn_total = float(e.get("duracion", 10.0))
            self.burn_timer = self.burn_total

        elif tipo == "luz_dano":

            self.polvora_dps = float(e.get("dano_por_segundo", 1.0))
            self.polvora_total = float(e.get("duracion", 8.0))
            self.polvora_timer = self.polvora_total
            self._polvora_acc = 0.0

        elif tipo == "repelente":

            self.repel_total = float(e.get("duracion", 105.0))
            self.repel_timer = self.repel_total

        elif tipo == "iman":

            self.magnet_total = float(e.get("duracion", 420.0))
            self.magnet_timer = self.magnet_total
            self.magnet_mode = True

        elif tipo == "luz_radio":

            self.sphere_mult = float(e.get("multiplicador", 1.25))
            self.sphere_total = float(e.get("duracion", 120.0))
            self.sphere_timer = self.sphere_total

        elif tipo == "escudo_sumar":

            self.escudo = min(
                1.0,
                self.escudo + float(e.get("valor", 0.0))
            )

        elif tipo == "abrir_cofre":

            chest = self.chests.nearest_ready(
                self.player.rect.center,
                GANZUA_DISTANCE
            )

            if chest is None:

                self.show_message(
                    "No hay un cofre listo cerca"
                )
                return False

            self.minigame_chest = chest

            self._finish_chest(True)

        else:

            return False

        return True

    def _apply_effect(self, e):

        if "vida" in e:

            self.vida = min(1.0, self.vida + e["vida"])

        if "regen" in e:

            seconds = max(0.1, e.get("regen_tiempo", 10.0))

            self.regen_left += e["regen"]
            self.regen_total = max(self.regen_left, 0.001)
            self.regen_rate = self.regen_left / seconds

        if "velocidad" in e:

            self.player.movement.speed_mult = e["velocidad"]
            self.speed_total = e.get("duracion", 10.0)
            self.speed_timer = self.speed_total

        if "consumo" in e:

            self.burn_factor = e["consumo"]
            self.burn_total = e.get("duracion", 10.0)
            self.burn_timer = self.burn_total

        if "polvora_dps" in e:

            self.polvora_dps = e["polvora_dps"]
            self.polvora_total = e.get("duracion", 8.0)
            self.polvora_timer = self.polvora_total
            self._polvora_acc = 0.0

        if "escudo" in e:

            self.escudo = min(1.0, self.escudo + e["escudo"])

    def _active_effects(self):

        active = {}

        if self.speed_timer > 0:
            active["aceite"] = self.speed_timer / self.speed_total

        if self.burn_timer > 0:
            active["cera"] = self.burn_timer / self.burn_total

        if self.polvora_timer > 0:
            active["polvora"] = self.polvora_timer / self.polvora_total

        if self.regen_left > 0:
            active["resina"] = min(1.0, self.regen_left / self.regen_total)

        if self.fury_left > 0:

            fury_len = light_stats(
                self.light_type
            ).get("furia_duracion", 0)

            if fury_len > 0:
                active["furia"] = min(1.0, self.fury_left / fury_len)

        if self.repel_timer > 0:
            active["repelente"] = self.repel_timer / self.repel_total

        if self.magnet_timer > 0:
            active["iman"] = self.magnet_timer / self.magnet_total

        if self.sphere_timer > 0:
            active["esfera"] = self.sphere_timer / self.sphere_total

        if self.has_match and any(
            getattr(a, "mosquito_alert", False) for a in self.arenas
        ):
            active["mosquito"] = 1.0

        return active

    def _menu_arena(self):

        for arena in self.arenas:

            if arena.menu_open:
                return arena

        return None

    def _polvora_hit(self, damage):

        for arena in self.arenas:

            arena.hurt_in_radius(
                self.player.rect.center,
                self._light_radius_px / max(1, self.camera.zoom),
                damage
            )


    def _mouse_world(self):

        mx, my = pygame.mouse.get_pos()

        return (
            (self.camera.x + mx) / self.camera.zoom,
            (self.camera.y + my) / self.camera.zoom
        )

    def _attack_pivot(self):

        rect = self.player.image_rect

        zoom = max(1, self.camera.zoom)

        return (
            rect.centerx,
            rect.bottom - rect.height * TORSO_HEIGHT / zoom
        )

    def _spawn_dummy(self):

        px, py = self.player.rect.center

        for _ in range(20):

            angle = random.random() * math.tau
            distance = random.randint(100, 180)

            x = px + math.cos(angle) * distance
            y = py + math.sin(angle) * distance

            rect = pygame.Rect(
                0,
                0,
                40,
                40
            )

            rect.center = (
                int(x),
                int(y)
            )

            if self.collision_map.can_move(rect):
                self.dummies.append(
                    TrainingDummy(
                        int(x),
                        int(y)
                    )
                )
                return

    def _update_dummies(self, dt):

        for dummy in self.dummies:

            dummy.update(
                dt
            )

    def cinematic_lock(self):

        # mientras entra o cae el jefe, el jugador mira (no se mueve ni pega)
        return any(
            getattr(a, "cinematic", None) is not None and a.cinematic.active
            for a in self.arenas
        )

    def _attack(self):

        if self.state != "playing":
            return

        if self.cinematic_lock():
            return

        if not self.has_match:
            self.show_message("Necesitas una luz")
            return

        if self.player.grabbed:
            return

        if self._fire_available() and self.attack_mode == "fuego":
            self._shoot_fireball()
            return

        if not self.melee.can_attack():
            return

        if not self.melee.start():
            return

        audio.play("swing")

        if not self.melee.fury:

            self.vida -= light_stats(
                self.light_type
            )["golpe_costo"]

    CHEST_REACH = 14    # px alrededor del cofre en los que F funciona

    def _chest_in_reach(self):

        # los cofres ya no se abren a golpes: se abren con F estando cerca
        # (asi se puede pelear con slimes al lado de un cofre sin abrirlo)
        best = None
        best_dist = None

        for chest in self.chests.chests:

            if chest.busy:
                continue

            zone = chest.block.inflate(
                self.CHEST_REACH * 2, self.CHEST_REACH * 2
            )

            if not zone.colliderect(self.player.rect):
                continue

            dist = pygame.Vector2(chest.rect.center).distance_to(
                self.player.rect.center
            )

            if best is None or dist < best_dist:
                best, best_dist = chest, dist

        return best

    def _use_chest(self, chest):

        # F cuenta como un golpe al cofre: destello + sacudida + sonido
        audio.play("door_hit")

        chest.take_damage(1)

        if chest.ready:
            self._open_chest(chest)
        else:
            self.show_message(f"Faltan {format_time(chest.cooldown)}")

    def _melee_hits(self, pivot):

        if not self.melee.swinging and not self.melee.final_pass:
            return

        targets = [t for a in self.arenas for t in a.targets()]
        targets += list(self.doors.doors)

        targets += [d for d in self.dummies if not d.dead]
        targets += self.slimes.targets()

        for target in self.melee.new_hits(targets, pivot):

            if self.melee.heavy and not self.melee.fury:
                self.melee.add_impact(target.rect.center)

            self._hit_target(
                target,
                self.melee.damage,
                free=self.melee.fury
            )

    def _update_fx(self, dt):

        self.fx.update(dt)

        if self.intro_t is not None:

            self.intro_t += dt

            if self.intro_t >= INTRO_TIME:
                self.intro_t = None

        if self.melee.swinging:

            ang = self.melee.current_angle
            pvx, pvy = self._attack_pivot()
            reach = 24 * (1.35 if self.melee.heavy else 1.0)

            self.fx.swing_sparks(
                pvx + math.cos(ang) * reach,
                pvy + math.sin(ang) * reach,
                ang, self.melee.heavy, self.melee.fury
            )

        if not self.has_match or self._light_radius_px < 8:
            return

        z = max(1, self.camera.zoom)
        px, py = self.player.rect.center
        r = self._light_radius_px / z

        if self.polvora_timer > 0:
            self.fx.emit_aura(
                "polvora", px, py, r, (255, 150, 50), dt, rate=26
            )

        if self.repel_timer > 0:
            self.fx.emit_aura(
                "repel", px, py, r, REPEL_RING_COLOR, dt, rate=14
            )

        if self._magnet_active():
            self.fx.emit_aura(
                "iman", px, py, MAGNET_RADIUS, (120, 190, 255), dt,
                rate=10, inward=True
            )

        if self.fury_active_fx():
            self.fx.emit_aura(
                "furia", px, py, 6, (255, 70, 50), dt, rate=30
            )

    def fury_active_fx(self):

        return bool(getattr(self.melee, "fury", 0) and self.melee.fury)

    GLOW_COLORS = {
        "fosforo": (255, 175, 80),
        "vela": (255, 190, 95),
        "antorcha": (255, 120, 45),
    }

    def _draw_warm_glows(self, sources):

        t = pygame.time.get_ticks() / 1000.0

        for i, (wx, wy, radius) in enumerate(sources):

            if radius < 12:
                continue

            is_player = (
                self.has_match
                and int(wx) == int(self.player.rect.centerx)
                and int(wy) == int(self.player.rect.centery)
            )

            if is_player:

                color = self.GLOW_COLORS.get(self.light_type, (255, 180, 85))

                k = 0.5 + 0.08 * math.sin(t * 40 + 1.3) \
                    + 0.06 * math.sin(t * 23)

                self.light.add_glow(
                    self.screen, self.camera, wx, wy,
                    radius * 1.05, color, k
                )

            else:

                self.light.add_glow(
                    self.screen, self.camera, wx, wy,
                    radius, (255, 170, 90),
                    0.28 + 0.05 * math.sin(t * 31 + i)
                )

    def _hit_target(self, target, damage, free=False):

        light = light_stats(self.light_type)

        tx, ty = target.rect.center
        px, py = self.player.rect.center

        self.fx.hit(
            tx, ty,
            angle=math.atan2(ty - py, tx - px),
            heavy=bool((self.melee.heavy or damage >= 2) and not self.melee.fury),
            fury=bool(self.melee.fury),
        )

        if isinstance(target, Door):

            if not target.breakable:

                target.resist()
                audio.play("door_resist")

                if getattr(target, "is_final", False):
                    self.show_message(
                        "Esta puerta se abre poniendo las 2 gemas en los altares (F)"
                    )
                else:
                    self.show_message(
                        "Esta puerta no es posible de romper"
                    )

            elif target.kind not in light["rompe"]:

                target.resist()
                audio.play("door_resist")

                if target.kind == "azul":
                    self.show_message(
                        "Solo la antorcha puede romper esta puerta"
                    )
                else:
                    self.show_message(
                        "Tu luz no puede romper esta puerta"
                    )

            else:

                was_broken = target.broken

                cost = target.take_damage(damage)

                if target.broken and not was_broken:
                    achievements.add_counter("doors")

                audio.play(
                    "door_break" if target.broken else "door_hit"
                )

                if not free:
                    self.vida -= cost

        elif isinstance(target, Chest):

            audio.play("door_hit")

            target.take_damage(damage)

            if target.ready:

                self._open_chest(target)

            else:

                self.show_message(
                    f"Faltan {format_time(target.cooldown)}"
                )

        else:

            audio.play(
                "hit_heavy" if self.melee.heavy or damage >= 2 else "hit"
            )

            target.take_damage(damage)


    def flashbang(self, x, y):

        self.flash_t = FLASH_TOTAL
        self.flash_pos = (x, y)

        audio.play("flashbang")

    def _update_flash(self, dt):

        if self.flash_t > 0:
            self.flash_t = max(0.0, self.flash_t - dt)

    def _draw_flashbang(self):

        if self.flash_t <= 0 or self.state != "playing":
            return

        w, h = self.screen.get_size()

        elapsed = FLASH_TOTAL - self.flash_t

        if elapsed < FLASH_EXPAND:

            k = elapsed / FLASH_EXPAND
            k = 1.0 - (1.0 - k) ** 3

            cx = int(self.flash_pos[0] * self.camera.zoom - self.camera.x)
            cy = int(self.flash_pos[1] * self.camera.zoom - self.camera.y)

            radius = int((0.05 + 0.95 * k) * math.hypot(w, h))

            pygame.draw.circle(
                self.screen, (255, 255, 255), (cx, cy), max(1, radius)
            )

            return

        if self._flash_surf is None or self._flash_surf.get_size() != (w, h):

            self._flash_surf = pygame.Surface((w, h))
            self._flash_surf.fill((255, 255, 255))

        if self.flash_t > FLASH_FADE:
            alpha = 255
        else:
            alpha = int(255 * self.flash_t / FLASH_FADE)

        self._flash_surf.set_alpha(alpha)

        self.screen.blit(self._flash_surf, (0, 0))


    def _fire_available(self):

        return self.has_match and self.light_type == "antorcha"

    def _hud_attack_mode(self):

        return self.attack_mode if self._fire_available() else None

    def _toggle_attack_mode(self):

        if self.state != "playing":
            return

        if not self._fire_available():

            self.show_message(
                "Solo la antorcha lanza bolas de fuego"
            )

            return

        if self.attack_mode == "golpe":

            self.attack_mode = "fuego"
            self.fire_combo = 0

            self.show_message("Bola de fuego")

        else:

            self.attack_mode = "golpe"
            self.fire_combo = 0

            self.show_message("Golpe comun")

    def _shoot_fireball(self):

        if self.fire_cooldown > 0:
            return False

        px, py = self._attack_pivot()
        mx, my = self._mouse_world()

        angle = math.atan2(my - py, mx - px)

        x = px + math.cos(angle) * FIRE_MUZZLE
        y = py + math.sin(angle) * FIRE_MUZZLE

        if not self.collision_map.point_is_walkable(x, y):
            x, y = px, py

        self.fire_combo += 1

        heavy = self.fire_combo >= FIRE_COMBO_SIZE

        damage = FIRE_DAMAGE * (FIRE_HEAVY_MULT if heavy else 1)

        self.fireballs.append(
            Fireball(x, y, angle, damage, heavy=heavy)
        )

        audio.play("fireball")

        fury = self.melee.fury

        base_cooldown = FIRE_HEAVY_COOLDOWN if heavy else FIRE_COOLDOWN

        self.fire_cooldown = base_cooldown / (
            FIRE_FURY_SPEED if fury else 1.0
        )

        if heavy:

            self.fire_combo = 0
            self.fire_combo_timer = 0.0

        else:

            self.fire_combo_timer = FIRE_COMBO_WINDOW

        self.count_stat("fireballs")
        achievements.add_counter("fireballs")

        if not fury:

            self.vida -= FIRE_COST * (
                FIRE_HEAVY_COST_MULT if heavy else 1.0
            )

        return True

    def _update_fireballs(self, dt):

        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

        if self.fire_combo > 0:

            self.fire_combo_timer -= dt

            if self.fire_combo_timer <= 0:
                self.fire_combo = 0

        if self._fire_hold:

            if not pygame.mouse.get_pressed()[0]:

                self._fire_hold = False

            elif (
                self.state == "playing"
                and not self.player.grabbed
                and self._fire_available()
                and self.attack_mode == "fuego"
            ):

                self._shoot_fireball()

        for burst in self.fire_bursts:
            burst.update(dt)

        self.fire_bursts = [
            b for b in self.fire_bursts if not b.done
        ]

        if not self.fireballs:
            return

        targets = [t for a in self.arenas for t in a.targets()]
        targets += list(self.doors.doors)
        targets += [d for d in self.dummies if not d.dead]
        targets += self.slimes.targets()

        walkable = self.collision_map.point_is_walkable

        for ball in self.fireballs:

            hit = ball.update(dt, targets, walkable)

            if hit is not None:

                self._hit_target(hit, ball.damage, free=True)

            if ball.dead:

                self.fire_bursts.append(
                    FireBurst(ball.x, ball.y, ball.heavy)
                )

        self.fireballs = [
            b for b in self.fireballs if not b.dead
        ]


    def _open_chest(self, chest):

        if not chest.ready:

            self.show_message(
                f"Faltan {format_time(chest.cooldown)}"
            )
            return

        chest.busy = True

        self.minigame_chest = chest

        self.minigame = ChestMinigame(
            self.screen.get_size()
        )

    def _finish_chest(self, success):

        chest = self.minigame_chest

        if chest is not None:

            chest.busy = False

            if success:

                self.chests.consume_use(chest)

                self.count_stat("chests_opened")
                achievements.add_counter("chests")

                self.world_items.extend(
                    self.chests.spawn_drops(
                        chest,
                        self.collision_map,
                        self.item_defs
                    )
                )

                chest.show_open()

                audio.play("chest_open")

        self.minigame = None
        self.minigame_chest = None


    def best_wave(self):

        return max(a.wave for a in self.arenas)

    def shop_locks(self):

        wave = self.best_wave()

        return {
            item_id: need
            for item_id, need in SHOP_UNLOCK_WAVES.items()
            if wave < need
        }

    def _open_shop(self):

        if self.shop is not None:
            return

        self.tuto_flags.add("shop_opened")

        self.shop = ShopUI(
            self.screen.get_size(),
            self.catalog,
            self.item_defs,
            self.coins,
            MATCH_DURATION,
            cart=self.shop_cart,
            locks=self.shop_locks(),
            best_wave=self.best_wave(),
            inventory=self.shop_inventory,
            max_stack=self._max_stack,
            inv_slots=self.hud.SLOTS
        )

    def _close_shop(self):

        if self.shop is not None:
            self.shop_cart = dict(self.shop.cart)
            self.shop_inventory = [
                list(slot) if slot else None
                for slot in self.shop.inventory
            ]

        self.shop = None

    def _shop_notice(self, text):

        if self.shop is not None:
            self.shop._flash(text)
        else:
            self.show_message(text)

    def _buy(self, cart):

        locks = self.shop_locks()

        cart = {i: q for i, q in cart.items() if i not in locks}

        # skins: se desbloquean (una sola vez), no son objetos del juego
        skin_ids = []

        for item_id in [i for i in cart if is_skin_item(i)]:

            skin_id = item_id[len(skin_lib.SHOP_PREFIX):]

            if skin_lib.is_unlocked(skin_id):
                del cart[item_id]
            else:
                cart[item_id] = 1
                skin_ids.append(skin_id)

        if not cart:

            self._shop_notice("Ya tenés esa skin")

            return

        total = sum(
            self.shop_prices.get(item_id, 0) * qty
            for item_id, qty in cart.items()
        )

        if total <= 0:
            return

        if total > self.coins:
            self._shop_notice("No te alcanzan las monedas")
            return

        self.coins -= total

        if self.shop is not None:
            self.shop.coins = int(self.coins)

        rect = getattr(self.shopkeeper, "rect", None)

        if rect is not None:
            x, y = rect.center
        else:
            x, y = self.player.rect.center

        for skin_id in skin_ids:
            skin_lib.buy(skin_id)

        item_ids = []

        for item_id, qty in cart.items():

            if is_skin_item(item_id):
                continue

            if item_id in ("bolsa", "faro"):

                for _ in range(qty):

                    try:
                        landing = self.shopkeeper._landing_point(
                            self.collision_map
                        )
                        mouth = self.shopkeeper.MOUTH
                    except Exception:
                        landing = self.player.rect.center
                        mouth = None

                    self.placeables.spawn(
                        item_id, landing[0], landing[1],
                        src=mouth, delay=0.3
                    )

                    self.shopkeeper.add_shot(landing, 0.3)

                continue

            item_ids.extend([item_id] * qty)

        for item in (
            self.shopkeeper.spit(item_ids, self.collision_map)
            if item_ids else []
        ):

            if isinstance(item, LightItem):
                self.light_drops.append(item)
            else:
                self.world_items.append(item)

        audio.play("buy")

        self.show_message("Compra hecha")

        self.count_stat("purchases")

        if self.shop is not None:
            self.shop.clear()

        self.shop_cart = {}

        self._close_shop()


    def _buy_inventory(self, slots):

        locks = self.shop_locks()

        def valid(slot):
            return bool(
                slot and slot[0] not in locks
                and slot[0] in self.shop_prices
            )

        # los primeros casilleros son los del HUD, el ultimo es la luz
        wanted = [
            (slot[0], int(slot[1]))
            for slot in slots[:self.hud.SLOTS]
            if valid(slot)
        ]

        light = None

        if len(slots) > self.hud.SLOTS and valid(slots[self.hud.SLOTS]):
            light = slots[self.hud.SLOTS][0]

        if light not in LIGHTS:
            light = None

        total = sum(
            self.shop_prices[item_id] * qty for item_id, qty in wanted
        )

        if light is not None:
            total += self.shop_prices[light]

        if total <= 0:
            return

        if total > self.coins:
            self._shop_notice("No te alcanzan las monedas")
            return

        # Primero se prueba si entra todo en los casilleros reales,
        # asi no se cobra una compra que no se puede entregar.
        items = list(self.hud.items)
        counts = list(self.hud.counts)

        for item_id, qty in wanted:

            limit = self._max_stack(item_id)

            for _ in range(qty):

                spot = None

                for i in range(self.hud.SLOTS):
                    if items[i] == item_id and counts[i] < limit:
                        spot = i
                        break

                if spot is None:
                    for i in range(self.hud.SLOTS):
                        if items[i] is None:
                            spot = i
                            break

                if spot is None:
                    self._shop_notice(
                        "Tu inventario está lleno: soltá o usá items antes de comprar"
                    )
                    return

                items[spot] = item_id
                counts[spot] += 1

        self.coins -= total

        for i in range(self.hud.SLOTS):
            self.hud.items[i] = items[i]
            self.hud.counts[i] = counts[i]

        if light is not None:

            if self.has_match:

                # ya tenes una luz en la mano: la nueva sale por la boca
                for item in self.shopkeeper.spit(
                    [light], self.collision_map
                ):
                    self.light_drops.append(item)

            else:

                self.equip_match(light, 1.0)

        if self.shop is not None:
            self.shop.coins = int(self.coins)

        audio.play("buy")

        self.show_message("Inventario comprado")

        self.count_stat("purchases")

        self._close_shop()

        self._save()

    def _save(self):

        if not self.save_path:
            return

        inventory = []

        for i in range(
            self.hud.SLOTS
        ):

            item_id = self.hud.items[i]
            count = self.hud.counts[i]

            if item_id is None or count <= 0:

                inventory.append(None)

            else:

                inventory.append(
                    [
                        item_id,
                        count
                    ]
                )

        data = {
            "x": self.player.rect.centerx,
            "y": self.player.rect.centery,

            "coins": self.coins,
            "ganzua_uses": self.ganzua_uses,
            "boss_intro_seen": self.boss_intro_seen,
            "gems": self.gems,
            "gems_green": self.gems_green,

            "has_match": self.has_match,
            "light": self.light_type,
            "vida": self.vida,

            "escudo": self.escudo,

            "mode": self.mode,

            "inventory": inventory,

            "shop_inventory": [
                list(slot) if slot else None
                for slot in self.shop_inventory
            ],

            "collected": list(
                self.collected
            ),

            "item_seed": self.item_seed,

            "arena_wave": self.arena.wave,
            "arena_completed": self.arena.completed,
            "arena_left_wave": self.arena_left.wave,
            "arena_left_completed": self.arena_left.completed,

            "broken_doors": sorted(self.doors.broken_ids),
            "final_door_slots": (
                self.doors.final_door.slots_for_save()
                if self.doors.final_door is not None else {}
            ),
            "current_map": (
                "mapa1" if self._force_home
                else getattr(self, "current_map", "mapa1")
            ),

            "chests": self.chests.save_data(),

            "placeables": self.placeables.save_data(),

            "enemies_seen": sorted(self.discovered_enemies),

            "stats": dict(self.stats),
            "zones_seen": sorted(self.zones_seen),
            "tuto_seen": sorted(self.tuto_seen),
            "death_drops": self._collect_drops_for_save(),
        }

        if self.objectives is not None:
            data["objective_index"] = self.objectives.index
            data["objective_version"] = OBJECTIVE_VERSION
            data["objectives_minimized"] = self.objectives.minimized

        elif self._objective_saved is not None:
            data["objective_index"] = int(self._objective_saved)
            data["objective_version"] = OBJECTIVE_VERSION

        save_progress(
            self.save_path,
            **data
        )

    def discover_enemy(self, key):

        if key in self.discovered_enemies:
            return

        self.discovered_enemies.add(key)

        if set(EnemyEncyclopedia.ORDER) <= self.discovered_enemies:
            achievements.unlock("entomologo")

    def save_progress(self):

        self._save()

    def materialize_drops(self, map_name):

        items = []
        lights = []

        for e in self.pending_drops.pop(map_name, []):

            try:

                if e.get("k") == "light":

                    it = LightItem(
                        e["id"], e["x"], e["y"], e.get("life", 0.5)
                    )
                    lights.append(it)

                else:

                    it = WorldItem(e["id"], e["x"], e["y"])
                    items.append(it)

                it.death_drop = True

            except Exception as error:

                print(f"[drops] No se pudo cargar un item: {error}")

        return items, lights

    @staticmethod
    def _drop_entries(map_name, items, lights):

        out = []

        for it in list(items) + list(lights):

            if getattr(it, "initial", False):
                continue

            if (
                not getattr(it, "death_drop", False)
                and getattr(it, "spawn_id", None) is not None
            ):
                continue

            fly = getattr(it, "fly", None)

            x, y = fly["dst"] if fly is not None else it.rect.center

            if isinstance(it, LightItem):

                out.append({
                    "k": "light", "id": it.kind, "life": float(it.life),
                    "x": int(x), "y": int(y), "map": map_name,
                })

            else:

                out.append({
                    "k": "item", "id": it.item_id,
                    "x": int(x), "y": int(y), "map": map_name,
                })

        return out

    def _collect_drops_for_save(self):

        cur = getattr(self, "current_map", "mapa1")

        out = self._drop_entries(cur, self.world_items, self.light_drops)

        for name, st in getattr(self, "_map_states", {}).items():

            if name != cur:
                out.extend(
                    self._drop_entries(
                        name, st.get("items", []), st.get("drops", [])
                    )
                )

        for entries in self.pending_drops.values():
            out.extend(entries)

        return out

    def _death_landing(self, cx, cy):

        for _ in range(25):

            angle = random.uniform(0, math.tau)
            dist = random.uniform(18, 72)

            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist

            if self.collision_map.point_is_walkable(int(x), int(y)):
                return (x, y)

        return (cx, cy)

    def _drop_death_items(self):

        if self._death_dropped or self.mode == MODE_HARDCORE:
            return

        self._death_dropped = True

        cx, cy = self.player.rect.center

        def launch(it, lst):

            it.death_drop = True

            it.start_fly(
                (cx, cy),
                self._death_landing(cx, cy),
                delay=random.uniform(0.0, 0.35),
                height=random.uniform(24, 44),
                duration=random.uniform(0.5, 0.8),
            )

            lst.append(it)

        for i in range(self.hud.SLOTS):

            item_id = self.hud.items[i]
            count = self.hud.counts[i]

            if item_id is None or count <= 0:
                continue

            for _ in range(count):
                launch(WorldItem(item_id, cx, cy), self.world_items)

        if self.has_match and self.light_type != "fosforo":

            launch(
                LightItem(self.light_type, cx, cy, 0.5),
                self.light_drops
            )

    def apply_loss(self):

        if self._loss_applied or not self.save_path:
            return

        self._loss_applied = True

        if self.mode == MODE_HARDCORE:

            if DELETE_SAVE_ON_LOSS:
                delete_save(self.save_path)
            else:
                self._save()

            return

        self._drop_death_items()

        self._force_home = True

        for i in range(self.hud.SLOTS):
            self.hud.items[i] = None
            self.hud.counts[i] = 0

        # los objetos del mapa vuelven a aparecer
        self.collected = set()

        self.has_match = True
        self.light_type = "fosforo"
        self.vida = 1.0
        self.escudo = 0.0

        if not NORMAL_KEEP_COINS:
            self.coins = 0
            self.gems = 0
            self.gems_green = 0

        spawn_x, spawn_y = get_spawn_point(self.collision_map, "cabana")
        self.player.rect.center = (spawn_x, spawn_y)

        self._save()


    def handle_event(self, event):


        if self.tutorial is not None:

            result = self.tutorial.handle_event(
                event
            )

            if getattr(self.tutorial, "skip_all", False):

                self._skip_tutorial()

                return None

            if result == "close" or not self.tutorial.active:

                self.tutorial = None

            return None


        if self.minigame is not None:

            result = self.minigame.handle_event(
                event
            )

            if result == "cancel":

                self._finish_chest(
                    False
                )

            return None


        if self.pause_view == "pause":

            result = self.pause_menu.handle_event(
                event
            )

            if result == "resume":

                self.pause_view = None

            elif result == "settings":

                self.pause_settings = Settings(
                    self.screen,
                    background="tablet_ajustes.png",
                    controls_background="tablet_ajustes.png"
                )

                self.pause_view = "settings"

            elif result == "enemies":

                self.enemy_encyclopedia = EnemyEncyclopedia(
                    self.screen,
                    self.discovered_enemies
                )

                self.pause_view = "enemies"

            elif result == "back":

                self._save()

                return "menu"

            return None


        if self.pause_view == "settings":

            result = self.pause_settings.handle_event(
                event
            )

            if result == "back":

                self.pause_view = "pause"
                self.pause_settings = None

            return None


        if self.pause_view == "enemies":

            result = self.enemy_encyclopedia.handle_event(
                event
            )

            if result == "back":

                self.pause_view = "pause"
                self.enemy_encyclopedia = None

            return None


        if self.shop is not None:

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 2
            ):
                self.tuto_flags.add("shop_info")

            result = self.shop.handle_event(
                event
            )

            if (
                result == "close"
                or (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                )
            ):

                self._close_shop()

            elif isinstance(result, dict):

                self._buy(result)

            elif (
                isinstance(result, tuple)
                and len(result) == 2
                and result[0] == "buy"
            ):

                self._buy(result[1])

            elif (
                isinstance(result, tuple)
                and len(result) == 2
                and result[0] == "buy_inventory"
            ):

                self._buy_inventory(result[1])

            return None


        self._record_tuto_input(event)

        menu_arena = self._menu_arena()

        if menu_arena is not None:

            menu_arena.handle_event(
                self,
                event
            )

            return None


        if self.placeables.handle_event(self, event):

            return None


        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                self.pause_view = "pause"

                return None


        menu_button = getattr(
            self.hud,
            "menu_button_rect",
            None
        )

        giveup_button = getattr(self.hud, "giveup_rect", None)

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.state == "playing"
            and self.no_light_timer is not None
            and giveup_button is not None
            and giveup_button.collidepoint(event.pos)
        ):

            self.no_light_timer = 0.0
            self.state = "dying"
            self.fade_alpha = 255
            self.flash_t = 0.0

            return None

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and menu_button is not None
            and menu_button.collidepoint(event.pos)
        ):

            self.pause_view = "pause"

            return None


        if (
            event.type == pygame.MOUSEWHEEL
            and self.state == "playing"
            and event.y != 0
        ):

            order = list(range(self.hud.SLOTS)) + ["equipped"]

            try:
                i = order.index(self.selected_slot)
            except ValueError:
                i = 0

            step = -1 if event.y > 0 else 1

            self.selected_slot = order[(i + step) % len(order)]

            return None


        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 3
            and self.state == "playing"
        ):

            slot = self.hud.slot_at(event.pos)

            if slot is not None:
                self.selected_slot = slot

            if self._selected_item() == "mapa":

                self._map_hold = True

                return None

            if self.selected_slot != "equipped":

                self.use_item(
                    self.selected_slot
                )

            return None


        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.state == "playing"
            and self._hud_attack_mode() is not None
            and self.hud.attack_panel_rect.collidepoint(event.pos)
        ):

            self._toggle_attack_mode()

            return None


        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):

            slot = self.hud.slot_at(event.pos)

            if slot is not None:

                self.selected_slot = slot

                return None

            equipped_rect = getattr(
                self.hud,
                "equipped_rect",
                None
            )

            if (
                equipped_rect is not None
                and equipped_rect.collidepoint(event.pos)
            ):

                self.selected_slot = "equipped"

                return None


        if (
            self.objectives is not None
            and self.state == "playing"
            and self.objectives.handle_event(event)
        ):

            return None


        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_F3:

                self.debug_items = not self.debug_items

            elif event.key == pygame.K_F4:

                self.debug_combat = not self.debug_combat

            elif event.key == pygame.K_F1:

                if self.state == "playing":

                    self.tutorial = Tutorial(
                        (self.width, self.height),
                        can_skip=self.objectives is not None
                    )

                    return None

            elif event.key == pygame.K_F5:

                self._spawn_dummy()

            elif event.key == pygame.K_F8:

                self.coins += DEBUG_COINS

            elif event.key == pygame.K_F9:

                # al reves de F8 (debug): resta monedas, sin bajar de 0
                self.coins = max(0, self.coins - DEBUG_COINS)

            elif event.key == pygame.K_SPACE and self.state == "playing":

                # saltito (solo visual, no sirve para nada todavia)
                self.player.jump()

            elif controls.slot_for(event.key) is not None:

                slot = controls.slot_for(event.key)

                if slot < self.hud.SLOTS:
                    self.selected_slot = slot

            elif controls.matches("equipped", event.key):

                self.selected_slot = "equipped"

            elif controls.matches("pickup", event.key):

                kind, thing = self._nearest_pickup()

                if kind == "light":

                    self.tuto_flags.add("picked")

                    self.light_drops.remove(
                        thing
                    )

                    self.equip_match(
                        thing.kind,
                        thing.life
                    )

                    return None

                if (
                    kind is None
                    and self.has_match
                    and self._nearest_light_drop() is not None
                ):

                    self.show_message(
                        "Ya tenés una luz: soltala primero "
                        f"({controls.label('equipped')} y después "
                        f"{controls.label('drop')}) para agarrar esta"
                    )

                    return None

                if kind == "item":

                    self.pick_up_item(
                        thing
                    )

                    return None


            elif controls.matches("drop", event.key):

                if pygame.key.get_mods() & pygame.KMOD_CTRL:

                    # CTRL + Q: suelta todo el inventario (la luz equipada no)
                    self.drop_all_items()

                elif self.selected_slot == "equipped":

                    if self.has_match:
                        self._drop_match()

                else:

                    self.drop_item(
                        self.selected_slot
                    )

            elif controls.matches("magnet", event.key):

                if not self._magnet_available():

                    self.show_message(
                        "No tenés el imán: usalo desde el inventario"
                    )

                else:

                    self.magnet_mode = not self.magnet_mode

                    self.show_message(
                        f"Imán activado ({controls.label('magnet')} para desactivarlo)"
                        if self.magnet_mode
                        else f"Imán desactivado ({controls.label('magnet')} para activarlo)"
                    )

            elif controls.matches("use", event.key):

                fd = self.doors.final_door

                if fd is not None and fd.try_interact(self):
                    return None

                if self.shopkeeper.can_talk(
                    self.player
                ):

                    self._open_shop()

                    return None

                chest = self._chest_in_reach()

                if chest is not None:

                    self._use_chest(chest)

                    return None

                if self.selected_slot != "equipped":

                    self.use_item(
                        self.selected_slot
                    )

            elif controls.matches("attack_mode", event.key):

                self._toggle_attack_mode()

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):

            self._fire_hold = True

            self._attack()

        return None


    def update(self, dt):

        if (
            self.fx.hitstop > 0
            and self.state == "playing"
            and self.pause_view is None
            and self.tutorial is None
        ):

            self.fx.hitstop = max(0.0, self.fx.hitstop - dt)
            self.fx.update(dt * 0.25)

            return None

        fd = self.doors.final_door

        if self.state == "playing" and self.map_switch.active:

            self.map_switch.update(dt, self)
            self._update_fx(dt)

            return None

        if (
            fd is not None
            and fd.sequence_active
            and self.state == "playing"
        ):

            self._update_fx(dt)
            self.doors.update(dt)

            return None


        if self.tutorial is not None:

            self.tutorial.update(
                dt
            )

            if not self.tutorial.active:

                self.tutorial = None

                if getattr(self, "_intro_pending", False):
                    self._intro_pending = False
                    self.intro_t = 0.0
                    self.fx._ring(
                        *self.player.rect.center, 4, 70, 1.1,
                        (255, 215, 140), 3
                    )

            return None


        if self.pause_view is not None:

            if self.pause_view == "pause":

                self.pause_menu.update(
                    dt
                )

            elif self.pause_view == "settings":

                self.pause_settings.update(
                    dt
                )

            elif self.pause_view == "enemies":

                self.enemy_encyclopedia.update(
                    dt
                )

            return None


        if self.state == "dying":

            if not self._defeat_counted:

                self._defeat_counted = True

                achievements.add_defeat()

            self._drop_death_items()

            for it in self.world_items + self.light_drops:

                if getattr(it, "fly", None) is not None:
                    it.update_fly(dt)

            self.flash_t = 0.0

            self.fade_alpha += (
                255 / FADE_DURATION
            ) * dt

            if self.fade_alpha >= 255:

                self.fade_alpha = 255
                self.state = "lost"
                self.lost_timer = LOST_SCREEN_TIME

            return None

        if self.state == "lost":

            self.lost_timer -= dt

            if self.lost_timer <= 0:

                self.apply_loss()

                if self.mode == MODE_HARDCORE and DELETE_SAVE_ON_LOSS:
                    return "menu"

                return "respawn"

            return None


        if self.message_timer > 0:

            self.message_timer -= dt

            if self.message_timer <= 0:

                self.message = ""


        menu_arena = self._menu_arena()

        if menu_arena is not None:

            menu_arena.update_menu(
                dt
            )

            return None


        if self.minigame is not None:

            update = getattr(
                self.minigame,
                "update",
                None
            )

            result = update(dt) if update is not None else None

            if result == "win":

                self._finish_chest(
                    True
                )

            elif result == "fail":

                self._finish_chest(
                    False
                )

            return None


        zone = self.zone_tracker.update(
            self.player.rect.center
        )

        if zone is not None:

            self.zone_banner.show(
                zone.name
            )

        approach = None

        for az in APPROACH_ZONES:

            if az.rect.collidepoint(self.player.rect.center):
                approach = az
                break

        if approach is not None and approach is not self._approach_current:

            self.zone_banner.show(approach.name)

        self._approach_current = approach

        if zone is not None:
            self.zones_seen.add(zone.id)

            if (
                zone.id == "cofres"
                and self.stats.get("chests_opened", 0) < 1
            ):
                self.show_message(
                    "Acercate a un cofre y apretá F para abrirlo"
                )

        self.zone_banner.update(
            dt
        )

        if self.objectives is not None:

            self.objectives.update(
                dt,
                self
            )

            if self.objectives.skip_requested:

                self._skip_tutorial()

            else:

                self._tuto_step_check()

                self.guide.update(dt)

            if self.objectives is not None and self.objectives.finished:

                self._objective_saved = 10 ** 6

                self.objectives = None


        in_shop = self.shopkeeper.zone_inset(
            self.player
        ) > 0

        lock = self.cinematic_lock()

        if self.has_match:

            if in_shop:

                self.vida = min(
                    1.0,
                    self.vida + dt / SHOP_RECHARGE_TIME
                )

            elif not lock:

                burn = (
                    self.base_burn
                    * self.burn_factor
                )

                self.vida -= (
                    burn
                    * dt
                    / MATCH_DURATION
                )

                if self.vida <= 0:

                    self._burn_out()


        self._update_fury(
            dt
        )


        if self.speed_timer > 0:

            self.speed_timer -= dt

            if self.speed_timer <= 0:

                self.speed_timer = 0
                self.player.movement.speed_mult = 1.0

        if self.burn_timer > 0:

            self.burn_timer -= dt

            if self.burn_timer <= 0:

                self.burn_timer = 0
                self.burn_factor = 1.0

        if self.polvora_timer > 0:

            self.polvora_timer -= dt
            self._polvora_acc += dt

            while self._polvora_acc >= POLVORA_TICK:

                self._polvora_acc -= POLVORA_TICK

                if self.has_match:

                    self._polvora_hit(
                        self.polvora_dps * POLVORA_TICK
                    )

                    self.fx.pulse("polvora")

            if self.polvora_timer <= 0:

                self.polvora_timer = 0
                self.polvora_dps = 0.0
                self._polvora_acc = 0.0

        if self.repel_timer > 0:

            self.repel_timer = max(0.0, self.repel_timer - dt)

        if self.magnet_timer > 0 and self.magnet_mode:

            self.magnet_timer = max(0.0, self.magnet_timer - dt)

        if self.sphere_timer > 0:

            self.sphere_timer = max(0.0, self.sphere_timer - dt)

            if self.sphere_timer <= 0:
                self.sphere_mult = 1.0

        if self.coin_gain_timer > 0:

            self.coin_gain_timer = max(0.0, self.coin_gain_timer - dt)

            if self.coin_gain_timer <= 0:
                self.coin_gain = 0

        if self.regen_left > 0:

            amount = min(
                self.regen_left,
                self.regen_rate * dt
            )

            self.vida = min(
                1.0,
                self.vida + amount
            )

            self.regen_left -= amount

            if self.regen_left <= 0:

                self.regen_left = 0.0
                self.regen_rate = 0.0


        if not lock:

            self.player.update(
                dt,
                self.collision_map
            )


        self.camera.update(
            self.player
        )


        pivot = self._attack_pivot()

        self.melee.update(
            dt,
            pivot,
            self._mouse_world()
        )

        self._melee_hits(pivot)

        self._update_fx(dt)

        self._update_fireballs(dt)

        self._update_flash(dt)


        self._update_dummies(
            dt
        )

        self.slimes.update(dt, self)


        self.chests.update(
            dt
        )


        self.doors.update(
            dt
        )

        if (
            self.doors.final_door is not None
            and self.current_map == "mapa1"
        ):
            self.doors.final_door.set_player_near(
                self.doors.final_door.player_near(self.player.rect)
            )

        if self.state == "playing":
            self.map_switch.check(self)


        for arena in self.arenas:

            arena.update(
                self,
                dt
            )

        self._check_achievements()

        self.crushers.update(self, dt)

        if self.has_match and self.vida <= 0:

            self._burn_out()


        self.shopkeeper.update(dt, self.player)

        self.placeables.update(self, dt)

        for drop in self.light_drops:

            if getattr(drop, "fly", None) is not None:
                drop.update_fly(dt)

        px, py = self.player.rect.center

        magnet_on = self._magnet_active()

        for item in list(
            self.world_items
        ):

            if getattr(item, "fly", None) is not None:
                item.update_fly(dt)
                continue

            ix, iy = item.rect.center

            dist = math.hypot(
                ix - px,
                iy - py
            )

            if magnet_on and self._magnet_can_take(item):

                if dist <= MAGNET_PICKUP_DISTANCE:

                    self.pick_up_item(
                        item
                    )

                    continue

                if dist <= MAGNET_RADIUS:

                    self._magnet_pull(
                        item,
                        px,
                        py,
                        dist,
                        dt
                    )

                    continue

            self._magnet_release(item)

            if item.item_id not in COIN_VALUES:
                continue

            if dist <= COIN_PICKUP_DISTANCE:

                self.pick_up_item(
                    item
                )


        if self.shop is not None:

            if self.shop.tab == "inv":
                self.tuto_flags.add("shop_inv")

            self.shop.update(
                dt
            )


        in_shop_now = self.shopkeeper.zone_inset(
            self.player
        ) > 0

        if not self.has_match and in_shop_now:

            self.no_light_timer = None

        elif not self.has_match:

            if self.no_light_timer is None:

                self.no_light_timer = NO_LIGHT_COUNTDOWN

            else:

                self.no_light_timer -= dt

                if self.no_light_timer <= 0:

                    self.no_light_timer = 0.0
                    self.state = "dying"
                    self.fade_alpha = 0
                    self.flash_t = 0.0

        else:

            self.no_light_timer = None

        return None


    def _selected_item(self):

        if not isinstance(self.selected_slot, int):
            return None

        if not 0 <= self.selected_slot < self.hud.SLOTS:
            return None

        return self.hud.items[self.selected_slot]

    def _map_held(self):

        if not self._map_hold:
            return False

        if not pygame.mouse.get_pressed()[2]:

            self._map_hold = False

            return False

        if (
            self.state != "playing"
            or self.pause_view is not None
            or self.shop is not None
            or self.minigame is not None
            or self.tutorial is not None
            or self._selected_item() != "mapa"
        ):

            self._map_hold = False

            return False

        return True

    def _magnet_available(self):

        return self.magnet_timer > 0 or not MAGNET_NEEDS_ITEM

    def _magnet_active(self):

        return self.magnet_mode and self._magnet_available()

    def _magnet_can_take(self, item):

        item_id = item.item_id

        if item_id in COIN_VALUES or item_id in ("gema", "gema_verde"):
            return True

        return self._free_slot_for(item_id) is not None

    def _magnet_release(self, item):

        # el objeto ya no esta siendo atraido: vuelve a su estado normal
        if getattr(item, "_mag_t", 0) > 0:

            item._mag_t = 0.0
            item._mag_trail = []
            item._lift = 0.0

    def _magnet_pull(self, item, px, py, dist, dt):

        t = getattr(item, "_mag_t", 0.0)

        if t <= 0:

            # recien lo agarra el iman: destello + semilla del giro
            item._mag_trail = []
            item._mag_spin = random.choice((-1.0, 1.0))

            self.fx.magnet_grab(
                item.rect.centerx, item.rect.centery,
                self.fx.item_color(item)
            )

        t += dt
        item._mag_t = t

        k = 1.0 - min(1.0, dist / MAGNET_RADIUS)

        # primero "despierta" (se levanta y retrocede un poquito) y
        # despues acelera cada vez mas fuerte hacia el jugador
        ramp = min(1.0, t / MAGNET_WAKE)

        speed = (
            MAGNET_SPEED_FAR
            + (MAGNET_SPEED_NEAR - MAGNET_SPEED_FAR) * (k ** 1.4)
        ) * (0.25 + 0.75 * ramp) * (1.0 + min(1.0, t) * 0.6)

        if t < MAGNET_WAKE:
            speed = -26.0 * (1.0 - t / MAGNET_WAKE)

        step = min(abs(speed) * dt, dist) * (1 if speed >= 0 else -1)

        fx = getattr(item, "_mag_x", None)
        fy = getattr(item, "_mag_y", None)

        if fx is None or (
            abs(fx - item.rect.centerx) > 1.5
            or abs(fy - item.rect.centery) > 1.5
        ):

            fx, fy = item.rect.center

        dx = (px - fx) / max(0.01, dist)
        dy = (py - fy) / max(0.01, dist)

        # curva: un empuje de costado que se apaga al acercarse, asi
        # los objetos entran en espiral en vez de ir en linea recta
        swirl = item._mag_spin * (1.0 - k) * 0.55 * min(1.0, t / 0.4)

        mx = dx - dy * swirl
        my = dy + dx * swirl

        norm = max(0.01, math.hypot(mx, my))

        nx = fx + mx / norm * step
        ny = fy + my / norm * step

        walk = self.collision_map.point_is_walkable

        if walk(nx, ny):

            fx, fy = nx, ny

        elif walk(nx, fy):

            fx = nx

        elif walk(fx, ny):

            fy = ny

        item._mag_x = fx
        item._mag_y = fy

        item.rect.center = (round(fx), round(fy))

        # flota mientras viaja y baja al llegar
        item._lift = 6.0 * min(1.0, t / 0.2) * (1.0 - 0.7 * k)

        trail = item._mag_trail

        trail.append((fx, fy - item._lift))

        if len(trail) > MAGNET_TRAIL:
            del trail[0]


    def _lit_rects(self):

        rects = []

        zone = getattr(
            self.shopkeeper,
            "ZONE",
            None
        )

        if isinstance(zone, pygame.Rect):

            rects.append(
                (
                    zone,
                    1.0,
                    getattr(
                        self.shopkeeper,
                        "ZONE_FEATHER",
                        22
                    )
                )
            )

        return rects


    def _load_magnet_imgs(self):

        hud_dir = (
            Path(__file__).resolve().parent.parent
            / "assets" / "maps" / "hud"
        )

        def load(name):

            try:
                return pygame.image.load(
                    str(hud_dir / name)
                ).convert_alpha()
            except (pygame.error, FileNotFoundError):
                return None

        on = load("modo_iman.png")

        if on is None:

            on = pygame.Surface((64, 64), pygame.SRCALPHA)

            pygame.draw.rect(
                on, (86, 92, 104), (2, 2, 60, 60), border_radius=12
            )
            pygame.draw.arc(
                on, (214, 52, 60), (16, 12, 32, 32), 3.14, 6.28, 8
            )
            pygame.draw.rect(on, (214, 52, 60), (16, 28, 8, 16))
            pygame.draw.rect(on, (214, 52, 60), (40, 28, 8, 16))

        off = load("modo_iman_off.png")

        if off is None:

            off = on.copy()
            shade = pygame.Surface(off.get_size(), pygame.SRCALPHA)
            shade.fill((40, 40, 40, 150))
            off.blit(shade, (0, 0))
            w, h = off.get_size()
            pygame.draw.line(
                off, (204, 66, 70), (w // 5, h // 5),
                (w * 4 // 5, h * 4 // 5), max(2, w // 12)
            )

        key = load("O.png")

        if key is None:

            key = pygame.Surface((32, 32), pygame.SRCALPHA)

            pygame.draw.rect(
                key, (111, 121, 130), (2, 2, 28, 28), border_radius=7
            )
            pygame.draw.rect(
                key, (70, 82, 92), (2, 2, 28, 28), 2, border_radius=7
            )
            font = pygame.font.Font(None, 26)
            txt = font.render("O", True, (40, 48, 56))
            key.blit(txt, txt.get_rect(center=(16, 16)))

        size = max(1, self.hud.coin_icon.get_height())
        key_size = max(8, int(size * 0.5))

        self._magnet_imgs = {
            "on": pygame.transform.smoothscale(on, (size, size)),
            "off": pygame.transform.smoothscale(off, (size, size)),
            "key": pygame.transform.smoothscale(
                key, (key_size, key_size)
            ),
        }

    def _draw_magnet_mode(self):

        if self.state != "playing" or not self._magnet_available():
            return

        if self._magnet_imgs is None:
            self._load_magnet_imgs()

        img = self._magnet_imgs[
            "on" if self.magnet_mode else "off"
        ]

        rect = img.get_rect(
            topright=(
                self.hud.coin_rect.left - 8,
                self.hud.coin_rect.top
            )
        )

        self.screen.blit(img, rect.topleft)

        key = self._magnet_imgs["key"]

        self.screen.blit(
            key,
            key.get_rect(
                bottomright=(rect.right + 4, rect.bottom + 4)
            ).topleft
        )

    def _draw_gems(self):

        self._gems_bottom = 0

        if self.gems <= 0 and self.gems_green <= 0:
            return

        if self._gem_icon is None:

            try:
                self._gem_icon = get_gem_icon(24)
            except TypeError:
                self._gem_icon = get_gem_icon()

        if self._gem_green_icon is None:
            self._gem_green_icon = get_green_gem_icon()

        rows = []

        if self.gems > 0:
            rows.append((self._gem_icon, self.gems))

        if self.gems_green > 0:
            rows.append((self._gem_green_icon, self.gems_green))

        y = GEMS_MARGIN[1]

        for icon, amount in rows:

            x = self.width - GEMS_MARGIN[0]

            if icon is not None:

                self.screen.blit(icon, (x, y))

                x += icon.get_width() + 6

            text = self._font(28).render(
                str(amount),
                True,
                (255, 255, 255)
            )

            self.screen.blit(text, (x, y))

            row_h = icon.get_height() if icon is not None else 28

            y += row_h + 4

        # hasta donde llegan las gemas (el objetivo se dibuja debajo)
        self._gems_bottom = y

    def _draw_debug_items(self):

        for item in self.world_items:

            pygame.draw.rect(
                self.screen,
                (0, 255, 0),
                self.camera.apply(item.rect),
                1
            )

        for drop in self.light_drops:

            pygame.draw.rect(
                self.screen,
                (255, 200, 0),
                self.camera.apply(drop.rect),
                1
            )

        text = self._font(22).render(
            f"objetos: {len(self.world_items)}  "
            f"luces: {len(self.light_drops)}",
            True,
            (0, 255, 0)
        )

        self.screen.blit(
            text,
            (10, self.height - 30)
        )

    def draw(self):

        shake_x, shake_y = self.fx.shake_offset()

        self.camera.x += shake_x
        self.camera.y += shake_y

        self._draw_scene()

        self.camera.x -= shake_x
        self.camera.y -= shake_y

        self.achievement_toast.draw(self.screen)

    def _draw_scene(self):

        self.world_map.draw(
            self.screen,
            self.camera
        )

        self.shopkeeper.draw_body(self.screen, self.camera)

        for drop in self.light_drops:
            drop.draw(self.screen, self.camera)

        for item in self.world_items:
            item.draw(self.screen, self.camera)

        self.doors.draw(self.screen, self.camera)

        self.chests.draw(self.screen, self.camera)

        self.placeables.draw(self.screen, self.camera)

        self.shopkeeper.draw(self.screen, self.camera)

        for dummy in self.dummies:
            dummy.draw(self.screen, self.camera)

        self.slimes.draw(self.screen, self.camera)

        self.crushers.draw(self.screen, self.camera)

        for arena in self.arenas:
            arena.draw_world(self.screen, self.camera)

        self.player.draw(
            self.screen,
            self.camera
        )

        sources = []

        for arena in self.arenas:
            sources.extend(arena.light_sources())

        for drop in self.light_drops:

            fly = getattr(drop, "fly", None)

            if fly is not None and fly["delay"] > 0:
                continue

            sources.append((
                drop.rect.centerx,
                drop.rect.centery,
                drop.light_radius
            ))

        sources.extend(self.placeables.light_sources())

        if self.has_match:

            radius = self._light_radius()

            inset = self.shopkeeper.zone_inset(self.player)

            if inset > 0:
                radius *= max(0.0, 1.0 - inset / SHOP_LIGHT_FADE)

            if self.intro_t is not None:

                k = min(1.0, self.intro_t / INTRO_TIME)

                radius *= 0.3 + 0.7 * (1 - (1 - k) ** 3)

            if self.state in ("dying", "lost"):
                radius *= max(0.0, 1.0 - 1.5 * self.fade_alpha / 255)

            if self.vida < FLICKER_THRESHOLD:

                self._flicker_time += 0.02

                flicker = 0.55 + 0.45 * abs(
                    math.sin(self._flicker_time * 18)
                )

                radius *= flicker

            self._light_radius_px = radius

            if radius >= 2:

                sources.append((
                    self.player.rect.centerx,
                    self.player.rect.centery,
                    radius
                ))

        for ball in self.fireballs:
            sources.append(ball.light_source())

        if self.tutorial is None and DOOR_GLOW_RADIUS > 0:

            for door in self.doors.doors:

                if door.id != "cabana":
                    continue

                sources.append((
                    door.rect.centerx,
                    door.rect.centery,
                    int(DOOR_GLOW_RADIUS * self.camera.zoom)
                ))

                break

        self.light.draw(
            self.screen,
            self.camera,
            sources,
            self._lit_rects()
        )

        self._draw_warm_glows(sources)

        if self.has_match and self._light_radius_px >= 8:

            cx = self.player.rect.centerx * self.camera.zoom - self.camera.x
            cy = self.player.rect.centery * self.camera.zoom - self.camera.y

            if self.polvora_timer > 0:
                self.fx.draw_aura(
                    self.screen, "polvora", cx, cy,
                    self._light_radius_px, (255, 140, 40),
                    pygame.time.get_ticks() / 1000.0 + self.polvora_timer
                )

            if self.repel_timer > 0:
                self.fx.draw_aura(
                    self.screen, "repel", cx, cy,
                    self._light_radius_px, REPEL_RING_COLOR,
                    pygame.time.get_ticks() / 1000.0 * 0.8 + self.repel_timer, 0.8
                )

            if self._magnet_active():
                self.fx.draw_aura(
                    self.screen, "iman", cx, cy,
                    MAGNET_RADIUS * self.camera.zoom, (110, 180, 255),
                    pygame.time.get_ticks() / 1000.0 * 0.6, 0.55
                )

        self.placeables.draw_ghost(self, self.screen)

        for arena in self.arenas:
            arena.draw_fx(self.screen, self.camera)

        now = pygame.time.get_ticks() / 1000.0

        for item in self.world_items:

            if getattr(item, "sparkle", False):
                self.fx.draw_item_glow(self.screen, self.camera, item, now)

        if self._magnet_active():
            self.fx.draw_magnet_pull(
                self.screen, self.camera, self.world_items,
                self.player.rect.center
            )

        self.fx.draw(self.screen, self.camera)

        if (
            self.doors.final_door is not None
            and self.current_map == "mapa1"
        ):
            self.doors.final_door.draw_fx(self.screen, self.camera)

        elif (
            self.doors.final_door is None
            and self.current_map == "mapa1"
            and "puerta_final" in self.doors.broken_ids
        ):
            draw_placed_gems(
                self.screen, self.camera,
                pygame.time.get_ticks() / 1000.0
            )

        self.melee.draw(
            self.screen,
            self.camera,
            self._attack_pivot()
        )

        for ball in self.fireballs:
            ball.draw(self.screen, self.camera)

        for burst in self.fire_bursts:
            burst.draw(self.screen, self.camera)

        if self.debug_combat:

            self.melee.draw_debug(
                self.screen,
                self.camera,
                self._attack_pivot()
            )

        if self.state == "playing":

            _, near_thing = self._nearest_pickup()

            if near_thing is not None:
                near_thing.draw_prompt(self.screen, self.camera)

        if (
            self.state == "playing"
            and self.shop is None
            and self.shopkeeper.can_talk(self.player)
        ):
            self.shopkeeper.draw_prompt(self.screen, self.camera)

        if self.state == "playing" and self.minigame is None:

            near_chest = self._chest_in_reach()

            if near_chest is not None and near_chest.ready:

                dest = self.camera.apply(near_chest.rect)

                icon = self.shopkeeper.f_icon

                self.screen.blit(
                    icon,
                    icon.get_rect(
                        midbottom=(dest.centerx, dest.top - 6)
                    )
                )

        self.dungeon_map.draw(
            self.screen,
            self.collision_map.walkable,
            self._map_held(),
            self._font(28),
            map_name=getattr(self, "current_map", "mapa1"),
        )

        self.hud.selected = (
            self.selected_slot
            if isinstance(self.selected_slot, int)
            else None
        )

        self.hud.draw(
            self.screen,
            vida=self.vida if self.has_match else 0.0,
            escudo=self.escudo,
            countdown=self.no_light_timer,
            coins=self.coins,
            equipped_selected=self.selected_slot == "equipped",
            coin_gain=self.coin_gain if self.coin_gain_timer > 0 else 0,
            coin_gain_alpha=min(
                1.0,
                self.coin_gain_timer / COIN_GAIN_FADE
            ),
            attack_mode=self._hud_attack_mode()
        )

        self._draw_gems()

        self._draw_magnet_mode()

        active = {}

        if self.state == "playing":
            active = self._active_effects()

        self.effects_bar.draw(self.screen, active)

        if self.state == "playing":

            if self.objectives is not None:

                # que el objetivo no tape las gemas
                gems_bottom = getattr(self, "_gems_bottom", 0)

                self.objectives.top = max(
                    OBJECTIVES_TOP,
                    gems_bottom + 8 if gems_bottom else 0
                )

                self.objectives.draw(self.screen)

            self._draw_guidance()

            self.zone_banner.draw(self.screen)

        self.hud.draw_overlay(
            self.screen,
            self.item_defs,
            pygame.mouse.get_pos(),
            pygame.mouse.get_pressed()[0],
            self.message if self.message_timer > 0 else ""
        )

        for arena in self.arenas:
            arena.draw_hud(self.screen)

        self.placeables.draw_panel(self, self.screen)

        self.fx.draw_overlay(self.screen)

        if (
            self.doors.final_door is not None
            and self.current_map == "mapa1"
        ):
            self.doors.final_door.draw_overlay(self.screen)

        self.map_switch.draw(self.screen)

        if self.intro_t is not None:

            k = min(1.0, self.intro_t / INTRO_TIME)

            fade = pygame.Surface((self.width, self.height))
            fade.fill((0, 0, 0))
            fade.set_alpha(int(200 * (1 - k) ** 2))

            self.screen.blit(fade, (0, 0))

        self._draw_flashbang()

        if self.debug_items:

            self._draw_debug_items()

        if self.pause_view == "pause":
            self.pause_menu.draw()

        elif self.pause_view == "settings":
            self.pause_settings.draw()

        elif self.pause_view == "enemies":
            self.enemy_encyclopedia.draw()

        menu_arena = self._menu_arena()

        if menu_arena is not None and self.pause_view is None:
            menu_arena.draw_menu(self.screen, self)

        if self.pause_view is None:

            if self.minigame is not None:
                self.minigame.draw(self.screen)

            if self.shop is not None:
                self.shop.draw(self.screen)

            if self.tutorial is not None:
                self.tutorial.draw(self.screen)

        if self.state in ("dying", "lost"):

            self.fade_overlay.set_alpha(int(self.fade_alpha))

            self.screen.blit(self.fade_overlay, (0, 0))

        if self.state == "lost":

            if self.mode == MODE_HARDCORE and DELETE_SAVE_ON_LOSS:
                lost_img = self.pantalla_perdiste
            else:
                lost_img = self.pantalla_perdiste_normal

            lost_img.set_alpha(
                int(255 * min(1.0, (LOST_SCREEN_TIME - self.lost_timer) / 0.6))
            )

            self.screen.blit(lost_img, (0, 0))