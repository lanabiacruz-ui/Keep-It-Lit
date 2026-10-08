import math
import random
from pathlib import Path

import pygame

from core.Save_manager import save_progress, delete_save
from world.map_loader import WorldMap
from world.collision import CollisionMap
from world.camera import Camera
from world.spawn import get_spawn_point
from player.player import Player
from world.lighting import PlayerLight
from world.items import (
    LightItem,
    WorldItem,
    get_gem_icon,
    load_item_defs,
    load_spawn_zones,
    make_spawn_items
)
from world.melee import Melee, TrainingDummy
from world.lights import LIGHTS, light_stats
from world.doors import DoorManager, Door
from world.chests import ChestManager, Chest, format_time
from world.arena import Arena
from world.shop import Shopkeeper, load_catalog, price_table
from ui.hud import Hud
from ui.effects_bar import EffectsBar
from ui.chest_minigame import ChestMinigame
from ui.shop_ui import ShopUI
from ui.tutorial import Tutorial
from states.pause_menu import PauseMenu
from states.enemy_enciclopedia import EnemyEncyclopedia
from states.settings import Settings


# Radio de luz, consumo y espera entre golpes de cada luz (fosforo,
# vela...): se cambian en world/lights.py

MATCH_POS = (818, 1002)

# Cuanto dura prendido el fosforo (vida), en segundos. Corto para dar
# tension, pero lo bastante largo para explorar y decidir que hacer.
MATCH_DURATION = 30.0

# En el cuadrado de la tienda la luz se recarga: segundos para pasar de
# 0% a 100% de vida.
SHOP_RECHARGE_TIME = 4.0

# Al entrar a la tienda la luz del jugador se va apagando de a poco
# (porque ya esta todo iluminado). Es la distancia (mundo) que tarda.
SHOP_LIGHT_FADE = 24.0

# A que altura del sprite esta el "centro" del personaje (0 = pies,
# 1 = cabeza). De ahi sale el area de ataque.
TORSO_HEIGHT = 0.5

# Maximo de unidades iguales por slot (se puede cambiar por item con
# "max_pila" en data/items.json).
MAX_STACK = 15

# Cuanto tarda en desaparecer un aviso en pantalla (segundos).
MESSAGE_TIME = 2.2

# Cuenta regresiva (en segundos) cuando no hay luz, antes de perder.
NO_LIGHT_COUNTDOWN = 10.0

# Debajo de este % de vida, la luz empieza a parpadear.
FLICKER_THRESHOLD = 0.25

# Que tan oscuro es todo lo que queda fuera de la luz (0 a 255).
# 255 = negro total, 200 = se ve algo, 0 = sin oscuridad.
DARKNESS_ALPHA = 248

# Luz de la puerta de la cabana (radio en unidades del mundo).
# Mas chico = ilumina menos. 0 = sin luz.
DOOR_GLOW_RADIUS = 55

# A que distancia (unidades del mundo) del cofre sirve la ganzua.
GANZUA_DISTANCE = 48

# A que distancia se juntan solas las monedas del piso.
COIN_PICKUP_DISTANCE = 14

# Cada cuanto hace dano la luz con polvora (segundos).
POLVORA_TICK = 0.5

# F8 = trampa de prueba: suma esta cantidad de monedas.
DEBUG_COINS = 100000

# Cuanto vale cada moneda del piso (la amarilla, la azul y la roja).
# Si el objeto trae su propio "value" (monedas del cofre de la arena),
# se usa ese.
COIN_VALUES = {
    "moneda": 1,
    "moneda_5": 5,
    "moneda_10": 10,
}

# "+N" que aparece debajo del contador de monedas: cuanto se queda
# en pantalla (segundos) despues de la ultima moneda que agarraste,
# y cuanto dura el desvanecido del final.
COIN_GAIN_TIME = 2.0
COIN_GAIN_FADE = 0.5

# ---------- Items nuevos ----------
# (la duracion de cada uno esta en data/items.json: "repelente",
# "iman" y "esfera")

# Iman: hasta donde atrae los objetos (unidades del mundo) y que tan
# rapido vuelan hacia vos (velocidad lejos -> velocidad cerca).
MAGNET_RADIUS = 130
MAGNET_SPEED_FAR = 120.0
MAGNET_SPEED_NEAR = 360.0

# Iman: a que distancia del jugador se agarra solo el objeto.
MAGNET_PICKUP_DISTANCE = 10

# Repelente: color del aro que marca el area que espanta mosquitos.
REPEL_RING_COLOR = (120, 235, 130)

# Cuanto tarda la pantalla en ponerse del todo negra al perder.
FADE_DURATION = 1.2

# Cuanto se queda la pantalla de "Perdiste" antes de volver al menu.
LOST_SCREEN_TIME = 3.0

# Al perder, borrar la partida guardada (True) o dejarla como esta (False).
# Esta en False para que no pierdas tus saves de prueba mientras probas.
DELETE_SAVE_ON_LOSS = False

# Donde se dibuja el contador de gemas (desde la esquina de arriba a la
# derecha). Si se pisa con el HUD, cambialo.
GEMS_MARGIN = (110, 100)

# RECONSTRUIDO: que hace cada objeto al usarlo (tecla F). Si un objeto
# en data/items.json tiene un campo "efecto", se usa ese en vez de esto.
# Claves posibles:
#   vida          -> suma vida de golpe (0.0 a 1.0)
#   regen         -> suma vida de a poco; "regen_tiempo" = segundos
#   velocidad     -> multiplica la velocidad; "duracion" = segundos
#   consumo       -> multiplica lo rapido que se gasta la luz; "duracion"
#   polvora_dps   -> dano por segundo de la luz; "duracion"
#   escudo        -> suma escudo (0.0 a 1.0)
ITEM_EFFECTS = {
    "madera": {"vida": 0.20},
    "cera": {"consumo": 0.5, "duracion": 20.0},
    "aceite": {"velocidad": 1.5, "duracion": 12.0},
    "resina": {"regen": 0.5, "regen_tiempo": 10.0},
    "polvora": {"polvora_dps": 10.0, "duracion": 8.0},
    "hongo_azul": {"escudo": 0.25},
}

SLOT_KEYS = {
    pygame.K_1: 0,
    pygame.K_2: 1,
    pygame.K_3: 2,
    pygame.K_4: 3,
}


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

        # Puertas: las rotas (guardadas) no vuelven a aparecer
        self.doors = DoorManager(self.save_data.get("broken_doors", []))
        self.collision_map.doors = self.doors

        # Cofres: la espera de cada uno se guarda en la partida
        self.chests = ChestManager(self.save_data.get("chests", {}))
        self.collision_map.obstacles.extend(self.chests.blocking_rects)

        # Sala de combate (la sala grande de la derecha)
        self.arena = Arena((self.width, self.height))

        # La oleada que sigue (las que ya pasaste no se repiten)
        self.arena.wave = max(1, int(self.save_data.get("arena_wave", 1)))

        # Minijuego del cofre (None = cerrado)
        self.minigame = None
        self.minigame_chest = None

        # Tienda: el vendedor del mapa y la ventana (None = cerrada)
        self.shopkeeper = Shopkeeper()
        self.catalog = load_catalog()
        self.shop_prices = price_table(self.catalog)
        self.shop = None

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
            darkness_alpha=DARKNESS_ALPHA
        )

        self.hud = Hud((self.width, self.height))

        # Menu de pausa y pantallas accesibles desde el menu de pausa.
        self.pause_menu = PauseMenu(self.screen)
        self.pause_settings = None
        self.enemy_encyclopedia = None
        self.pause_view = None

        # Efectos activos (y la alerta del mosquito) como cubitos arriba
        self.effects_bar = EffectsBar((self.width, self.height))
        self.effects_bar.set_alert_image(self.arena.mosquito_art.warning)

        # Tutorial: solo en partida nueva (al continuar no aparece).
        # Mientras esta abierto el juego queda en pausa.
        self.tutorial = (
            None if self.save_data else Tutorial((self.width, self.height))
        )

        self.coins = int(self.save_data.get("coins", 0))

        # Gemas (las tira el cofre al completar el mapa)
        self.gems = int(self.save_data.get("gems", 0))

        # ---------- Fosforo / vida ----------

        self.has_match = bool(self.save_data.get("has_match", False))

        # Vida del fosforo actual, de 0.0 a 1.0
        self.vida = max(
            0.0,
            min(1.0, float(self.save_data.get("vida", 1.0)))
        )

        # Escudo: por ahora solo se muestra, arranca vacio
        self.escudo = max(
            0.0,
            min(1.0, float(self.save_data.get("escudo", 0.0)))
        )

        # Que luz esta equipada: "fosforo" o "vela"
        self.light_type = self.save_data.get("light", "fosforo")

        if self.light_type not in LIGHTS:
            self.light_type = "fosforo"

        # Que tan rapido se consume la luz de base
        self.base_burn = 1.0

        # El golpe se crea antes porque equip_match() le avisa que luz hay
        self.melee = Melee()

        # Mapa completado: la sala de combate queda cerrada para siempre
        self.arena.completed = bool(
            self.save_data.get("arena_completed", False)
        )

        self.arena.restore_completed(self)

        # Furia de la vela
        self.fury_timer = 0.0
        self.fury_left = 0.0

        # Luces tiradas en el piso
        self.light_drops = []

        if self.has_match:
            self.equip_match(self.light_type)
        else:
            self.light_drops.append(
                LightItem("fosforo", *MATCH_POS)
            )

        # ---------- Objetos (madera, aceite, cera) ----------

        self.item_defs = load_item_defs()

        saved_inv = self.save_data.get("inventory", [])

        for i in range(self.hud.SLOTS):

            if i >= len(saved_inv):
                break

            entry = saved_inv[i]

            if entry is None:
                continue

            # Formato nuevo: [id, cantidad].
            # Formato viejo: solo el id.
            if isinstance(entry, (list, tuple)) and len(entry) == 2:
                item_id, count = entry[0], int(entry[1])
            else:
                item_id, count = entry, 1

            # Las monedas nunca van al inventario: si una partida vieja
            # las guardo ahi (bug anterior), se pasan al contador.
            if item_id in COIN_VALUES and count > 0:

                self.coins += COIN_VALUES[item_id] * count
                continue

            # Las luces nunca van al inventario
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

        print(
            f"[items] {len(self.item_defs)} tipos de item, "
            f"{len(self.world_items)} objetos en el mapa"
        )

        # F3 = ver donde estan los objetos
        self.debug_items = False
        self._font_cache = {}

        # Efectos temporales
        self.speed_timer = 0.0
        self.burn_factor = 1.0
        self.burn_timer = 0.0

        # Duracion total de cada efecto
        self.speed_total = 1.0
        self.burn_total = 1.0
        self.polvora_total = 1.0
        self.regen_total = 1.0

        # Polvora: la luz hace dano mientras dura
        self.polvora_timer = 0.0
        self.polvora_dps = 0.0
        self._polvora_acc = 0.0

        # Resina: cura de a poco
        self.regen_left = 0.0
        self.regen_rate = 0.0

        # Repelente de mosquitos: tu luz los espanta mientras dura
        self.repel_timer = 0.0
        self.repel_total = 1.0

        # Iman: atrae los objetos del piso mientras dura
        self.magnet_timer = 0.0
        self.magnet_total = 1.0

        # Esfera de vidrio: mas radio de luz mientras dura
        self.sphere_timer = 0.0
        self.sphere_total = 1.0
        self.sphere_mult = 1.0

        # "+N" debajo del contador de monedas (lo conseguido "en el
        # momento": se suma mientras sigas agarrando y se desvanece)
        self.coin_gain = 0
        self.coin_gain_timer = 0.0

        # Radio de la luz en pantalla
        self._light_radius_px = self._light_radius()

        # ---------- Combate ----------

        self.melee.set_light(self.light_type)

        # Munecos de practica
        self.dummies = []

        # F4 = ver el area de ataque
        self.debug_combat = False

        # Aviso en pantalla
        self.message = ""
        self.message_timer = 0.0

        # Cuenta regresiva cuando no hay luz
        self.no_light_timer = None

        # Casillero seleccionado
        self.selected_slot = "equipped"

        # Estados:
        # "playing" -> "dying" -> "lost"
        self.state = "playing"

        self.fade_alpha = 0
        self.lost_timer = 0

        self._flicker_time = 0.0

        self._gem_icon = None

        pantalla_perdiste_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
            / "pantalla_perdiste.png"
        )

        self.pantalla_perdiste = pygame.transform.smoothscale(
            pygame.image.load(
                str(pantalla_perdiste_path)
            ).convert(),
            (self.width, self.height)
        )

        self.fade_overlay = pygame.Surface(
            (self.width, self.height)
        )

        self.fade_overlay.fill((0, 0, 0))

    # ---------- utilidades ----------

    def _font(self, size):

        font = self._font_cache.get(size)

        if font is None:
            font = pygame.font.Font(None, size)
            self._font_cache[size] = font

        return font

    # ---------- dano ----------

    def take_damage(self, amount):
        """El jugador recibe dano.

        El escudo es la primera vida y se gasta primero.
        Cuando se acaba, lo que sobra del golpe le pega
        a la vida de la luz.
        """

        if amount <= 0:
            return

        absorbed = min(self.escudo, amount)

        self.escudo -= absorbed
        self.vida -= amount - absorbed

        if self.escudo < 1e-6:
            self.escudo = 0.0

    # ---------- fosforo ----------

    def equip_match(self, kind=None, life=None):
        """Equipa una luz (fosforo o vela).

        kind -> cual
        life -> con cuanta vida
        """

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

        self._reset_fury()

    def _reset_fury(self):
        """Apaga la furia y reinicia la espera."""

        self.fury_left = 0.0

        self.fury_timer = light_stats(
            self.light_type
        ).get(
            "furia_cada",
            0
        )

        self.melee.set_fury(1.0)

    def _update_fury(self, dt):
        """Actualiza la furia de la luz."""

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
        """Radio de la luz equipada."""

        radius = light_stats(
            self.light_type
        )["radio"]

        # Esfera de vidrio: mas radio mientras dura
        if self.sphere_timer > 0:
            radius *= self.sphere_mult

        return radius

    def _nearest_light_drop(self):
        """La luz del piso mas cercana."""

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

        # Queda en el piso con la vida que le quedaba
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

        # Se le acabo la vida al fosforo
        self.vida = 0.0

        self.base_burn = 1.0

        self.regen_left = 0.0

        self.has_match = False

        self.hud.equip(None)

        self.player.set_torch(False)

        self._reset_fury()

    # ---------- objetos ----------
    # RECONSTRUIDO: estos metodos no estaban en el archivo que pegaste.

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
        """El objeto del piso mas cercano que se puede agarrar."""

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

    def pick_up_item(self, item):
        """Agarra un objeto del piso (moneda o item de inventario)."""

        item_id = item.item_id

        if item_id in COIN_VALUES:

            # Amarilla = 1, azul = 5, roja = 10 (o el "value" propio)
            value = getattr(item, "value", None)

            if value is None:
                value = COIN_VALUES[item_id]

            self.add_coins(int(value))

        elif item_id == "gema":

            # Las gemas no van al inventario. Las del cofre de la arena
            # ya se contaron al explotar (value = 0).
            self.gems += int(getattr(item, "value", 1))

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

            self.show_message(
                f"Agarraste {self._item_name(item_id)}"
            )

        # Que no vuelva a aparecer cuando se carga la partida
        for attr in ("key", "uid", "spawn_id", "id"):

            value = getattr(item, attr, None)

            if value is not None:

                self.collected.add(value)
                break

        if item in self.world_items:
            self.world_items.remove(item)

    def add_coins(self, amount):
        """Suma monedas al contador y al "+N" de debajo del HUD."""

        amount = int(amount)

        if amount <= 0:
            return

        self.coins += amount

        # Si todavia se ve el "+N" anterior, se acumula
        if self.coin_gain_timer <= 0:
            self.coin_gain = 0

        self.coin_gain += amount
        self.coin_gain_timer = COIN_GAIN_TIME

    def _free_slot_for(self, item_id):
        """Casillero donde entra el objeto (None si no hay lugar)."""

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
        """Tira una unidad del casillero al piso."""

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

    def _take_one(self, slot):

        self.hud.counts[slot] -= 1

        if self.hud.counts[slot] <= 0:

            self.hud.items[slot] = None
            self.hud.counts[slot] = 0

    def use_item(self, slot):
        """Usa una unidad del casillero (efectos de data/items.json)."""

        item_id = self.hud.items[slot]

        if item_id is None:
            return

        item = self.item_defs.get(item_id, {})

        # Las luces (fosforo, vela) se equipan solas al agarrarlas
        if item.get("tipo") == "luz":

            self.show_message(
                "Las luces se equipan solas al agarrarlas"
            )
            return

        efectos = item.get("efectos")

        if efectos:

            if item.get("requiere_fosforo") and not self.has_match:

                self.show_message(
                    "Necesitas una luz encendida"
                )
                return

            used = False

            for efecto in efectos:

                if self._apply_item_effect(efecto):
                    used = True

            # Si no se pudo usar (ej: ganzua sin cofre) no se gasta
            if not used:
                return

        else:

            # Compatibilidad: formato viejo con un solo "efecto"
            legacy = (
                item.get("efecto")
                or ITEM_EFFECTS.get(item_id)
            )

            if not legacy:

                self.show_message("Eso no se puede usar")
                return

            self._apply_effect(legacy)

        self._take_one(slot)

        self.show_message(
            f"Usaste {self._item_name(item_id)}"
        )

    def _apply_item_effect(self, e):
        """
        Aplica UN efecto de la lista "efectos" de items.json.
        Devuelve True si se aplico (False = no se gasta el objeto).
        """

        tipo = e.get("tipo")

        if tipo == "vida_sumar":

            self.vida = min(
                1.0,
                self.vida + float(e.get("valor", 0.0))
            )

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

            # Abre sin minijuego: gasta una apertura y suelta los
            # objetos (no se saltea la espera entre aperturas)
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
        """Efectos activos para la barra de arriba (fraccion 0 a 1)."""

        active = {}

        if self.speed_timer > 0:
            active["speed"] = self.speed_timer / self.speed_total

        if self.burn_timer > 0:
            active["burn"] = self.burn_timer / self.burn_total

        if self.polvora_timer > 0:
            active["polvora"] = self.polvora_timer / self.polvora_total

        if self.regen_left > 0:
            active["regen"] = min(1.0, self.regen_left / self.regen_total)

        if self.repel_timer > 0:
            active["repelente"] = self.repel_timer / self.repel_total

        if self.magnet_timer > 0:
            active["iman"] = self.magnet_timer / self.magnet_total

        if self.sphere_timer > 0:
            active["esfera"] = self.sphere_timer / self.sphere_total

        return active

    def _polvora_hit(self, damage):
        """La polvora lastima a lo que esta dentro de la luz."""

        hurt = getattr(self.arena, "hurt_in_radius", None)

        if hurt is None:
            return

        hurt(
            self.player.rect.center,
            self._light_radius_px,
            damage
        )

    # ---------- combate ----------

    def _mouse_world(self):

        mx, my = pygame.mouse.get_pos()

        # Misma cuenta que usa el dibujo (ver el aro de polvora)
        return (
            (self.camera.x + mx) / self.camera.zoom,
            (self.camera.y + my) / self.camera.zoom
        )

    def _attack_pivot(self):
        """Centro del cuerpo del jugador (de ahi sale el golpe)."""

        rect = self.player.image_rect

        return (
            rect.centerx,
            rect.bottom - rect.height * TORSO_HEIGHT
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

    def _attack(self):

        if self.state != "playing":
            return

        if not self.has_match:
            self.show_message("Necesitas una luz")
            return

        if not self.melee.can_attack():
            return

        if not self.melee.start():
            return

        # Cada golpe gasta un poco de la vida de la luz (en furia no)
        if not self.melee.fury:

            self.vida -= light_stats(
                self.light_type
            )["golpe_costo"]

    def _melee_hits(self, pivot):
        """Reparte lo que toco el golpe: enemigos, puertas, cofres y
        munecos."""

        if not self.melee.swinging:
            return

        targets = list(self.arena.targets())
        targets += list(self.doors.doors)
        targets += list(self.chests.chests)
        targets += [d for d in self.dummies if not d.dead]

        light = light_stats(self.light_type)

        for target in self.melee.new_hits(targets, pivot):

            if isinstance(target, Door):

                if target.kind not in light["rompe"]:

                    target.resist()

                    self.show_message(
                        "Tu luz no puede romper esta puerta"
                    )

                else:

                    cost = target.take_damage(self.melee.damage)

                    if not self.melee.fury:
                        self.vida -= cost

            elif isinstance(target, Chest):

                target.take_damage(self.melee.damage)

                if target.ready:

                    self._open_chest(target)

                else:

                    self.show_message(
                        f"Faltan {format_time(target.cooldown)}"
                    )

            else:

                target.take_damage(self.melee.damage)

    # ---------- cofres ----------

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

                # Gasta una apertura (al agotarse queda en espera) y
                # sueltan los objetos del cofre
                self.chests.consume_use(chest)

                self.world_items.extend(
                    self.chests.spawn_drops(
                        chest,
                        self.collision_map,
                        self.item_defs
                    )
                )

                chest.show_open()

        self.minigame = None
        self.minigame_chest = None

    # ---------- tienda ----------

    def _open_shop(self):

        if self.shop is not None:
            return

        self.shop = ShopUI(
            self.screen.get_size(),
            self.catalog,
            self.item_defs,
            self.coins,
            MATCH_DURATION
        )

    def _close_shop(self):

        self.shop = None

    def _buy(self, cart):
        """RECONSTRUIDO: compra lo que hay en el carrito.

        cart = {id_del_item: cantidad}
        """

        total = sum(
            self.shop_prices.get(item_id, 0) * qty
            for item_id, qty in cart.items()
        )

        if total <= 0:
            return

        if total > self.coins:
            self.show_message("No te alcanzan las monedas")
            return

        self.coins -= total

        # La tienda muestra las monedas que le pasaron al abrirse
        if self.shop is not None:
            self.shop.coins = int(self.coins)

        # El vendedor escupe todo lo comprado
        rect = getattr(self.shopkeeper, "rect", None)

        if rect is not None:
            x, y = rect.center
        else:
            x, y = self.player.rect.center

        for item_id, qty in cart.items():

            for _ in range(qty):

                px = x + random.randint(-24, 24)
                py = y + random.randint(10, 40)

                if item_id in LIGHTS:
                    self.light_drops.append(LightItem(item_id, px, py))
                else:
                    self.world_items.append(WorldItem(item_id, px, py))

        self.show_message("Compra hecha")

    # ---------- guardado ----------

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
            "gems": self.gems,

            "has_match": self.has_match,
            "light": self.light_type,
            "vida": self.vida,

            "escudo": self.escudo,

            "inventory": inventory,

            "collected": list(
                self.collected
            ),

            "item_seed": self.item_seed,

            "arena_wave": self.arena.wave,
            "arena_completed": self.arena.completed,

            "broken_doors": sorted(self.doors.broken_ids),

            "chests": self.chests.save_data(),
        }

        save_progress(
            self.save_path,
            **data
        )

    def save_progress(self):
        """Guarda la partida (lo usa main.py al cerrar la ventana)."""

        self._save()

    # ---------- eventos ----------

    def handle_event(self, event):

        # ---------------------------------------------------------
        # TUTORIAL
        # ---------------------------------------------------------

        if self.tutorial is not None:

            result = self.tutorial.handle_event(
                event
            )

            if result == "close" or not self.tutorial.active:

                self.tutorial = None

            return None

        # ---------------------------------------------------------
        # MINIJUEGO DEL COFRE
        # ---------------------------------------------------------

        if self.minigame is not None:

            result = self.minigame.handle_event(
                event
            )

            # Esc = salir del minijuego
            if result == "cancel":

                self._finish_chest(
                    False
                )

            return None

        # ---------------------------------------------------------
        # MENU DE PAUSA
        # ---------------------------------------------------------

        if self.pause_view == "pause":

            result = self.pause_menu.handle_event(
                event
            )

            if result == "resume":

                self.pause_view = None

            elif result == "settings":

                self.pause_settings = Settings(
                    self.screen,
                    background="tablet_ajustes.png"
                )

                self.pause_view = "settings"

            elif result == "enemies":

                self.enemy_encyclopedia = EnemyEncyclopedia(
                    self.screen
                )

                self.pause_view = "enemies"

            elif result == "back":

                self._save()

                return "menu"

            return None

        # ---------------------------------------------------------
        # AJUSTES DESDE PAUSA
        # ---------------------------------------------------------

        if self.pause_view == "settings":

            result = self.pause_settings.handle_event(
                event
            )

            if result == "back":

                self.pause_view = "pause"
                self.pause_settings = None

            return None

        # ---------------------------------------------------------
        # ENCICLOPEDIA DE ENEMIGOS
        # ---------------------------------------------------------

        if self.pause_view == "enemies":

            result = self.enemy_encyclopedia.handle_event(
                event
            )

            if result == "back":

                self.pause_view = "pause"
                self.enemy_encyclopedia = None

            return None

        # ---------------------------------------------------------
        # TIENDA
        # ---------------------------------------------------------

        if self.shop is not None:

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

            return None

        # ---------------------------------------------------------
        # MENU DE LA ARENA (oleadas)
        # ---------------------------------------------------------

        if self.arena.menu_open:

            handler = getattr(
                self.arena,
                "handle_menu_event",
                None
            )

            if handler is not None:

                handler(
                    event,
                    self
                )

            elif (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):

                self.arena.menu_open = False

            return None

        # ---------------------------------------------------------
        # ESC DURANTE EL JUEGO
        # ---------------------------------------------------------

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                self.pause_view = "pause"

                return None

        # ---------------------------------------------------------
        # CLICK EN EL BOTON MENU DEL HUD
        # ---------------------------------------------------------

        menu_button = getattr(
            self.hud,
            "menu_button_rect",
            None
        )

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and menu_button is not None
            and menu_button.collidepoint(event.pos)
        ):

            self.pause_view = "pause"

            return None

        # ---------------------------------------------------------
        # CLICK DERECHO: CONSUMIR EL OBJETO SELECCIONADO
        # (si el mouse esta sobre un slot, usa ese)
        # ---------------------------------------------------------

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 3
            and self.state == "playing"
        ):

            slot = self.hud.slot_at(event.pos)

            if slot is not None:
                self.selected_slot = slot

            if self.selected_slot != "equipped":

                self.use_item(
                    self.selected_slot
                )

            return None

        # ---------------------------------------------------------
        # CLICK EN LA HOTBAR: SELECCIONAR SLOT
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # TECLAS DEL JUEGO
        # ---------------------------------------------------------

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_F3:

                self.debug_items = not self.debug_items

            elif event.key == pygame.K_F4:

                self.debug_combat = not self.debug_combat

            elif event.key == pygame.K_F5:

                self._spawn_dummy()

            elif event.key == pygame.K_F8:

                self.coins += DEBUG_COINS

            elif event.key in SLOT_KEYS:

                slot = SLOT_KEYS[event.key]

                if slot < self.hud.SLOTS:
                    self.selected_slot = slot

            elif event.key == pygame.K_5:

                self.selected_slot = "equipped"

            elif event.key == pygame.K_e:

                # Agarrar luz
                light = self._nearest_light_drop()

                if light is not None:

                    if not self.has_match:

                        self.light_drops.remove(
                            light
                        )

                        self.equip_match(
                            light.kind,
                            light.life
                        )

                    else:

                        self.show_message(
                            "Ya tenes una luz encendida"
                        )

                    return None

                # Agarrar objeto
                item = self._nearest_item()

                if item is not None:

                    self.pick_up_item(
                        item
                    )

                    return None

                # Abrir cofre
                chest = self.chests.nearest_ready(
                    self.player.rect.center,
                    GANZUA_DISTANCE
                )

                if chest is not None:

                    self._open_chest(
                        chest
                    )

                    return None

            elif event.key == pygame.K_q:

                if self.selected_slot == "equipped":

                    if self.has_match:
                        self._drop_match()

                else:

                    self.drop_item(
                        self.selected_slot
                    )

            elif event.key == pygame.K_f:

                # Hablar con el vendedor (abre la tienda)
                if self.shopkeeper.can_talk(
                    self.player
                ):

                    self._open_shop()

                    return None

                if self.selected_slot != "equipped":

                    self.use_item(
                        self.selected_slot
                    )

            elif event.key == pygame.K_SPACE:

                self._attack()

        # Click izquierdo para atacar
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):

            self._attack()

        return None

    # ---------- update ----------

    def update(self, dt):

        # ---------------------------------------------------------
        # TUTORIAL
        # ---------------------------------------------------------

        if self.tutorial is not None:

            self.tutorial.update(
                dt
            )

            # Cuando el tutorial termina (se desliza afuera) se libera
            # el juego; antes quedaba congelado para siempre.
            if not self.tutorial.active:

                self.tutorial = None

            return None

        # ---------------------------------------------------------
        # PAUSA / AJUSTES / ENCICLOPEDIA
        # ---------------------------------------------------------

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

            # MUY IMPORTANTE:
            # no se actualiza el jugador,
            # enemigos, luz, cofres, etc.
            return None

        # ---------------------------------------------------------
        # PANTALLA DE DERROTA
        # ---------------------------------------------------------

        if self.state == "dying":

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

                if DELETE_SAVE_ON_LOSS and self.save_path:
                    delete_save(self.save_path)
                else:
                    self._save()

                return "menu"

            return None

        # ---------------------------------------------------------
        # MENSAJES
        # ---------------------------------------------------------

        if self.message_timer > 0:

            self.message_timer -= dt

            if self.message_timer <= 0:

                self.message = ""

        # ---------------------------------------------------------
        # MINIJUEGO DEL COFRE (el mundo queda congelado)
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # TIEMPO DE LUZ
        # ---------------------------------------------------------

        in_shop = self.shopkeeper.zone_inset(
            self.player
        ) > 0

        if self.has_match:

            if in_shop:

                # En la tienda la luz se recarga
                self.vida = min(
                    1.0,
                    self.vida + dt / SHOP_RECHARGE_TIME
                )

            else:

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

        # ---------------------------------------------------------
        # FURIA
        # ---------------------------------------------------------

        self._update_fury(
            dt
        )

        # ---------------------------------------------------------
        # EFECTOS
        # ---------------------------------------------------------

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

            if self.polvora_timer <= 0:

                self.polvora_timer = 0
                self.polvora_dps = 0.0
                self._polvora_acc = 0.0

        if self.repel_timer > 0:

            self.repel_timer = max(0.0, self.repel_timer - dt)

        if self.magnet_timer > 0:

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

        # ---------------------------------------------------------
        # JUGADOR
        # ---------------------------------------------------------

        self.player.update(
            dt,
            self.collision_map
        )

        # ---------------------------------------------------------
        # CAMARA
        # ---------------------------------------------------------

        self.camera.update(
            self.player
        )

        # ---------------------------------------------------------
        # ATAQUE
        # ---------------------------------------------------------

        pivot = self._attack_pivot()

        self.melee.update(
            dt,
            pivot,
            self._mouse_world()
        )

        self._melee_hits(pivot)

        # ---------------------------------------------------------
        # MUNECOS
        # ---------------------------------------------------------

        self._update_dummies(
            dt
        )

        # ---------------------------------------------------------
        # COFRES
        # ---------------------------------------------------------

        self.chests.update(
            dt
        )

        # ---------------------------------------------------------
        # PUERTAS
        # ---------------------------------------------------------

        self.doors.update(
            dt
        )

        # ---------------------------------------------------------
        # ARENA / ENEMIGOS
        # ---------------------------------------------------------

        self.arena.update(
            self,
            dt
        )

        # Si los golpes de los enemigos te dejaron sin vida
        if self.has_match and self.vida <= 0:

            self._burn_out()

        # ---------------------------------------------------------
        # MONEDAS CERCANAS
        # ---------------------------------------------------------

        px, py = self.player.rect.center

        magnet_on = self.magnet_timer > 0

        for item in list(
            self.world_items
        ):

            # Los que salen disparados de un cofre vuelan un ratito
            if getattr(item, "fly", None) is not None:
                item.update_fly(dt)
                continue

            ix, iy = item.rect.center

            dist = math.hypot(
                ix - px,
                iy - py
            )

            # IMAN: todos los objetos cercanos vuelan hacia vos y se
            # agarran solos (si el inventario esta lleno, los items
            # se quedan donde estan).
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

            # Las monedas (amarilla, azul y roja) se juntan solas al
            # pasar cerca, sin apretar E
            if item.item_id not in COIN_VALUES:
                continue

            if dist <= COIN_PICKUP_DISTANCE:

                self.pick_up_item(
                    item
                )

        # ---------------------------------------------------------
        # TIENDA
        # ---------------------------------------------------------

        if self.shop is not None:

            self.shop.update(
                dt
            )

        # ---------------------------------------------------------
        # SI SE QUEDA SIN LUZ
        # ---------------------------------------------------------

        if not self.has_match:

            if self.no_light_timer is None:

                self.no_light_timer = NO_LIGHT_COUNTDOWN

            else:

                self.no_light_timer -= dt

                if self.no_light_timer <= 0:

                    self.no_light_timer = 0.0
                    self.state = "dying"
                    self.fade_alpha = 0

        else:

            self.no_light_timer = None

        return None

    # ---------- iman ----------

    def _magnet_can_take(self, item):
        """El iman solo atrae lo que se puede agarrar de verdad."""

        item_id = item.item_id

        if item_id in COIN_VALUES or item_id == "gema":
            return True

        # Items de inventario: solo si hay lugar
        return self._free_slot_for(item_id) is not None

    def _magnet_pull(self, item, px, py, dist, dt):
        """Mueve el objeto hacia el jugador (sin atravesar paredes)."""

        k = 1.0 - min(1.0, dist / MAGNET_RADIUS)

        speed = (
            MAGNET_SPEED_FAR
            + (MAGNET_SPEED_NEAR - MAGNET_SPEED_FAR) * k
        )

        step = min(speed * dt, dist)

        # Posicion con decimales (el rect solo guarda enteros y a
        # poca velocidad no se movia nada)
        fx = getattr(item, "_mag_x", None)
        fy = getattr(item, "_mag_y", None)

        if fx is None or (
            abs(fx - item.rect.centerx) > 1.5
            or abs(fy - item.rect.centery) > 1.5
        ):

            fx, fy = item.rect.center

        dx = (px - fx) / max(0.01, dist)
        dy = (py - fy) / max(0.01, dist)

        nx = fx + dx * step
        ny = fy + dy * step

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

    # ---------- luz ----------

    def _lit_rects(self):
        """Zonas que siempre estan iluminadas: (rect, fuerza, borde)."""

        rects = []

        # La zona de la tienda siempre esta iluminada (el vendedor la
        # define como ZONE; el borde se difumina con ZONE_FEATHER)
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

    # ---------- dibujo ----------

    def _draw_gems(self):
        """RECONSTRUIDO: contador de gemas arriba a la derecha."""

        if self.gems <= 0:
            return

        if self._gem_icon is None:

            try:
                self._gem_icon = get_gem_icon(24)
            except TypeError:
                self._gem_icon = get_gem_icon()

        x = self.width - GEMS_MARGIN[0]
        y = GEMS_MARGIN[1]

        if self._gem_icon is not None:

            self.screen.blit(
                self._gem_icon,
                (x, y)
            )

            x += self._gem_icon.get_width() + 6

        text = self._font(28).render(
            str(self.gems),
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            text,
            (x, y)
        )

    def _draw_debug_items(self):
        """F3: marca donde estan los objetos y las luces."""

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

        self.world_map.draw(
            self.screen,
            self.camera
        )

        for drop in self.light_drops:
            drop.draw(self.screen, self.camera)

        for item in self.world_items:
            item.draw(self.screen, self.camera)

        self.doors.draw(self.screen, self.camera)

        self.chests.draw(self.screen, self.camera)

        self.shopkeeper.draw(self.screen, self.camera)

        for dummy in self.dummies:
            dummy.draw(self.screen, self.camera)

        self.arena.draw_world(self.screen, self.camera)

        self.player.draw(
            self.screen,
            self.camera
        )

        sources = []

        # El cofre del premio y la explosion tambien iluminan
        sources.extend(self.arena.light_sources())

        for drop in self.light_drops:

            sources.append((
                drop.rect.centerx,
                drop.rect.centery,
                drop.light_radius
            ))

        if self.has_match:

            radius = self._light_radius()

            # Adentro de la tienda ya esta todo iluminado: la luz del
            # jugador se apaga de a poco al entrar (y vuelve al salir)
            inset = self.shopkeeper.zone_inset(self.player)

            if inset > 0:
                radius *= max(0.0, 1.0 - inset / SHOP_LIGHT_FADE)

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

        # La puerta de la cabana queda iluminada despues del tutorial
        # (luz redonda y suave). Si ya se rompio, deja de iluminar.
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

        # Polvora: aro naranja en el borde de la luz
        if (
            self.has_match
            and self.polvora_timer > 0
            and self._light_radius_px >= 2
        ):

            cx = int(self.player.rect.centerx * self.camera.zoom - self.camera.x)
            cy = int(self.player.rect.centery * self.camera.zoom - self.camera.y)

            pulse = 2 + int(abs(math.sin(self._flicker_time * 6 + self.polvora_timer * 5)) * 3)

            pygame.draw.circle(
                self.screen,
                (255, 140, 40),
                (cx, cy),
                int(self._light_radius_px),
                pulse
            )

        # Repelente: aro verde en el borde de la luz (area que espanta
        # a los mosquitos)
        if (
            self.has_match
            and self.repel_timer > 0
            and self._light_radius_px >= 2
        ):

            cx = int(self.player.rect.centerx * self.camera.zoom - self.camera.x)
            cy = int(self.player.rect.centery * self.camera.zoom - self.camera.y)

            pulse = 0.5 + 0.5 * math.sin(self._flicker_time * 5 + self.repel_timer * 3)

            ring = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA
            )

            pygame.draw.circle(
                ring,
                (*REPEL_RING_COLOR, int(70 + 70 * pulse)),
                (cx, cy),
                int(self._light_radius_px),
                3
            )

            self.screen.blit(ring, (0, 0))

        # Brillo del cofre, explosion y chispas (encima de la oscuridad)
        self.arena.draw_fx(self.screen, self.camera)

        # El golpe va encima de la oscuridad, para que brille
        self.melee.draw(
            self.screen,
            self.camera,
            self._attack_pivot()
        )

        if self.debug_combat:

            self.melee.draw_debug(
                self.screen,
                self.camera,
                self._attack_pivot()
            )

        near_drop = (
            None if self.has_match else self._nearest_light_drop()
        )

        if near_drop is not None:
            near_drop.draw_prompt(self.screen, self.camera)

        elif self.state == "playing":

            near_item = self._nearest_item()

            if near_item is not None:
                near_item.draw_prompt(self.screen, self.camera)

        # Cartelito [F] del vendedor
        if (
            self.state == "playing"
            and self.shop is None
            and self.shopkeeper.can_talk(self.player)
        ):
            self.shopkeeper.draw_prompt(self.screen, self.camera)

        # El HUD dibuja el marco de seleccion con hud.selected
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
            )
        )

        self._draw_gems()

        # Cubitos de efectos arriba al centro (se vacian hasta desaparecer)
        active = {}

        if self.state == "playing" and self.has_match:
            active = self._active_effects()

        self.effects_bar.draw(self.screen, active)

        self.hud.draw_overlay(
            self.screen,
            self.item_defs,
            pygame.mouse.get_pos(),
            pygame.mouse.get_pressed()[0],
            self.message if self.message_timer > 0 else ""
        )

        self.arena.draw_hud(self.screen)

        if self.debug_items:

            self._draw_debug_items()

        if self.pause_view == "pause":
            self.pause_menu.draw()

        elif self.pause_view == "settings":
            self.pause_settings.draw()

        elif self.pause_view == "enemies":
            self.enemy_encyclopedia.draw()

        if self.arena.menu_open and self.pause_view is None:
            self.arena.draw_menu(self.screen, self)

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

            self.screen.blit(self.pantalla_perdiste, (0, 0))