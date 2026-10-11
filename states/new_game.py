import math
import random
from pathlib import Path

import pygame

from core.Save_manager import (
    save_progress, delete_save, normalize_mode, MODE_HARDCORE
)
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
from world.fireball import Fireball, FireBurst
from world.lights import LIGHTS, light_stats
from world.doors import DoorManager, Door
from world.chests import ChestManager, Chest, format_time
from world.arena import Arena, RIGHT_ARENA, LEFT_ARENA
from world.crusher import CrusherBlocks
from world.zones import ZoneTracker
from world.shop import Shopkeeper, load_catalog, price_table
from ui.hud import Hud
from ui.effects_bar import EffectsBar
from ui.chest_minigame import ChestMinigame
from ui.shop_ui import ShopUI
from ui.tutorial import Tutorial
from ui.zone_banner import ZoneBanner
from ui.objectives import Objectives
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

# ---------- Bola de fuego de la antorcha (tecla G) ----------
# El vuelo (velocidad, alcance, tamano) se cambia en world/fireball.py
FIRE_DAMAGE = 2          # cuanto saca cada bola (igual que el golpe de la antorcha)
FIRE_COST = 0.02         # vida de la luz que gasta cada bola (1.0 = toda)
FIRE_COOLDOWN = 0.45     # espera entre bola y bola, en segundos
FIRE_FURY_SPEED = 2.0    # en furia dispara tantas veces mas rapido (y no gasta luz)
FIRE_MUZZLE = 8.0        # a que distancia del cuerpo nace la bola (mundo)

# Combo de bolas: 2 bolas normales y la 3ra es la fuerte (x2 de dano).
FIRE_COMBO_SIZE = 3          # cada cuantas bolas sale la fuerte
FIRE_HEAVY_MULT = 2          # la fuerte saca tantas veces mas dano
FIRE_HEAVY_COST_MULT = 2.0   # y gasta tantas veces mas luz
FIRE_HEAVY_COOLDOWN = 0.75   # espera despues de la fuerte (normal: FIRE_COOLDOWN)
FIRE_COMBO_WINDOW = 1.0      # si pasa este tiempo sin tirar, el combo vuelve a 0

# ---------- Flashbang (lo provoca el enemigo Destello al explotar) ----------
# La pantalla se pone toda blanca: primero un "pum" (un circulo blanco que
# se expande desde el destello), se queda blanca y despues se va aclarando.
FLASH_EXPAND = 0.18   # duracion del "pum" (el circulo que se expande)
FLASH_HOLD = 3.0      # segundos totales con la pantalla toda blanca (incluye el pum)
FLASH_FADE = 2.0      # segundos que tarda en irse el blanco
FLASH_TOTAL = FLASH_HOLD + FLASH_FADE   # = 5 segundos tapado

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

# Iman: True = hace falta haber usado el item "Iman" (tienda) para poder
# prenderlo con la O. False = la O siempre lo prende y apaga (para probar).
MAGNET_NEEDS_ITEM = True

# Repelente: color del aro que marca el area que espanta mosquitos.
REPEL_RING_COLOR = (120, 235, 130)

# Cuanto tarda la pantalla en ponerse del todo negra al perder.
FADE_DURATION = 1.2

# Cuanto se queda la pantalla de "Perdiste" antes de volver al menu.
LOST_SCREEN_TIME = 3.0

# Al perder en modo HARDCORE, borrar la partida guardada (True) o dejarla
# como esta (False). Si queres probar sin perder tus saves, ponelo en False.
DELETE_SAVE_ON_LOSS = True

# Al perder en modo NORMAL se pierden todos los items (inventario y luces)
# y queda solo el fosforo; las oleadas, puertas y cofres siguen igual.
# Las monedas y las gemas: True = te las quedas, False = tambien se pierden.
NORMAL_KEEP_COINS = True

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
        save_data=None,
        mode=None
    ):

        self.screen = screen
        self.player_name = player_name
        self.save_path = save_path
        self.save_data = save_data or {}

        # Modo de la partida: "normal" o "hardcore". Una partida guardada
        # lo trae adentro; una vieja sin modo cuenta como normal.
        self.mode = normalize_mode(self.save_data.get("mode", mode))
        self._loss_applied = False
        self.width, self.height = screen.get_size()

        self.world_map = WorldMap()
        self.collision_map = CollisionMap()

        # Puertas: las rotas (guardadas) no vuelven a aparecer
        self.doors = DoorManager(self.save_data.get("broken_doors", []))
        self.collision_map.doors = self.doors

        # Cofres: la espera de cada uno se guarda en la partida
        self.chests = ChestManager(self.save_data.get("chests", {}))

        # Enciclopedia: enemigos que ya te encontraste en ESTA partida
        self.discovered_enemies = set(
            self.save_data.get("enemies_seen", [])
        )
        self.collision_map.obstacles.extend(self.chests.blocking_rects)

        # Salas de combate: la sala grande de la derecha (10 oleadas) y la
        # sala grande de la izquierda (2 oleadas, la 2da con el Guardian)
        self.arena = Arena((self.width, self.height), RIGHT_ARENA)
        self.arena_left = Arena((self.width, self.height), LEFT_ARENA)
        self.arenas = [self.arena, self.arena_left]

        # Bloques que abren y cierran los huecos de la cruz (sala izquierda)
        self.crushers = CrusherBlocks(self.collision_map)

        # La oleada que sigue (las que ya pasaste no se repiten)
        for arena in self.arenas:
            arena.wave = max(
                1, int(self.save_data.get(arena.cfg.save_wave, 1))
            )

        # Minijuego del cofre (None = cerrado)
        self.minigame = None
        self.minigame_chest = None

        # Tienda: el vendedor del mapa y la ventana (None = cerrada)
        self.shopkeeper = Shopkeeper()
        self.catalog = load_catalog()
        self.shop_prices = price_table(self.catalog)
        self.shop = None

        # Lo que pusiste en el carrito: se guarda al cerrar la tienda
        # sin comprar y vuelve cuando la abris de nuevo
        self.shop_cart = {}

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

        # Nombre de la sala: aparece al entrar a cada zona y se desvanece
        self.zone_tracker = ZoneTracker()
        self.zone_banner = ZoneBanner((self.width, self.height))

        # Cuantos objetos de inventario (no luces ni monedas) agarraste
        self.items_picked = 0

        # Contadores que usan los objetivos (se guardan en la partida)
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

        # Zonas a las que ya entraste (para los objetivos de explorar)
        self.zones_seen = set(self.save_data.get("zones_seen", []))

        # Objetivos (arriba a la derecha). Van de a uno y los que ya
        # estan cumplidos se saltean. Arrancan cuando termina el
        # tutorial. En partida nueva empiezan desde el primero; al
        # continuar, desde donde te quedaste (las partidas viejas, sin
        # objetivos guardados, no los tienen).
        objective_list = self._build_objectives()

        self._objective_saved = self.save_data.get("objective_index")

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

        # Golpe de la antorcha: "golpe" (normal) o "fuego" (bolas).
        # Se cambia con la tecla G o tocando el panel al lado de la hotbar.
        self.attack_mode = "golpe"
        self.fireballs = []
        self.fire_bursts = []
        self.fire_cooldown = 0.0
        self.fire_combo = 0           # bolas tiradas en el combo actual
        self.fire_combo_timer = 0.0   # cuanto queda para que se corte el combo
        self._fire_hold = False

        # Flashbang (destello): segundos que le quedan al blanco
        self.flash_t = 0.0
        self.flash_pos = (0.0, 0.0)
        self._flash_surf = None

        # Mapa completado: la sala de combate queda cerrada para siempre
        for arena in self.arenas:

            arena.completed = bool(
                self.save_data.get(arena.cfg.save_done, False)
            )

            arena.restore_completed(self)

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

        # Interruptor del iman: se prende y se apaga con la tecla O.
        # Apagado es como no tener el iman (se pueden soltar items y el
        # tiempo del item no corre).
        self.magnet_mode = False
        self._magnet_imgs = None

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

        self.attack_mode = "golpe"
        self.fire_combo = 0

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

    def count_stat(self, name, amount=1):
        """Suma a un contador de los objetivos (kills, cofres, etc.)."""

        self.stats[name] = self.stats.get(name, 0) + amount

    def _build_objectives(self):
        """Todos los objetivos del juego, en orden. Cada uno tiene el
        texto y una funcion `done(juego)`; con `max_time` el cartel se
        va solo despues de esos segundos aunque no lo cumplas."""

        def in_combat(g):

            return any(
                a.state in (a.WAVE, a.CLEAR, a.COLLECT)
                or a.wave >= 2
                or a.completed
                for a in g.arenas
            )

        return [

            # ---------- primeros pasos ----------
            {
                "text": (
                    f"Encuentra algo que ilumine o en "
                    f"{int(NO_LIGHT_COUNTDOWN)} segundos pierdes. "
                    f"¡Agárralo con E!"
                ),
                "done": lambda g: g.has_match,
            },
            {
                "text": (
                    "Encuentra objetos para mantener la luz "
                    "del fósforo prendida."
                ),
                "done": lambda g: g.items_picked > 0,
                "max_time": 30.0,
            },
            {
                "text": (
                    "Usá un objeto del inventario: elegilo con 1-4 y "
                    "apretá F o click derecho."
                ),
                "done": lambda g: g.stats["items_used"] >= 1,
                "max_time": 45.0,
            },
            {
                "text": (
                    "Salí de la cabaña: pegale a la puerta con tu luz "
                    "hasta romperla."
                ),
                "done": lambda g: "cabana" in g.doors.broken_ids,
            },

            # ---------- explorar ----------
            {
                "text": "Seguí por el camino hasta la sala central.",
                "done": lambda g: "central" in g.zones_seen,
            },
            {
                "text": (
                    "Juntá 10 monedas. Las hay tiradas por el mapa y "
                    "en los cofres."
                ),
                "done": lambda g: g.coins >= 10 or g.stats["purchases"] > 0,
            },
            {
                "text": (
                    "Andá a la tienda (arriba, al norte de la sala "
                    "central) y hablale al vendedor con F."
                ),
                "done": lambda g: "tienda" in g.zones_seen,
            },
            {
                "text": "Comprale algo al vendedor con tus monedas.",
                "done": lambda g: g.stats["purchases"] >= 1,
            },
            {
                "text": (
                    "Abrí un cofre en la sala de cofres (arriba a la "
                    "izquierda): pegale con la luz y ganá el minijuego."
                ),
                "done": lambda g: g.stats["chests_opened"] >= 1,
            },

            # ---------- mejorar la luz ----------
            {
                "text": (
                    "Conseguí una vela: se compra en la tienda o puede "
                    "salir de un cofre."
                ),
                "done": lambda g: (
                    g.has_match and g.light_type in ("vela", "antorcha")
                ),
            },
            {
                "text": (
                    "Con la vela rompé una puerta gris: las que llevan "
                    "a las salas de combate."
                ),
                "done": lambda g: (
                    "sala_izq" in g.doors.broken_ids
                    or "sala_der" in g.doors.broken_ids
                ),
            },

            # ---------- combate ----------
            {
                "text": (
                    "Entrá a una sala de combate y elegí cómo jugar: "
                    "con escape o sin escape."
                ),
                "done": in_combat,
            },
            {
                "text": (
                    "Derrotá a todos los enemigos de la oleada y "
                    "juntá las monedas del premio."
                ),
                "done": lambda g: any(
                    a.wave >= 2 or a.completed for a in g.arenas
                ),
            },
            {
                "text": (
                    "Conseguí la antorcha y lanzá una bola de fuego: "
                    "apretá G para cambiar de ataque."
                ),
                "done": lambda g: g.stats["fireballs"] >= 1,
            },
            {
                "text": (
                    "Completá la sala del Guardián (la de la "
                    "izquierda): 2 oleadas."
                ),
                "done": lambda g: g.arena_left.completed,
            },
            {
                "text": (
                    "Completá la sala de combate de la derecha: "
                    "10 oleadas. ¡Te espera una gema!"
                ),
                "done": lambda g: g.arena.completed,
            },
            {
                "text": (
                    "Completá la enciclopedia: descubrí a los "
                    f"{len(EnemyEncyclopedia.ORDER)} "
                    "enemigos (se ve desde el menú de pausa)."
                ),
                "done": lambda g: len(
                    set(g.discovered_enemies) & set(EnemyEncyclopedia.ORDER)
                ) >= len(EnemyEncyclopedia.ORDER),
            },
        ]

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

    def _nearest_pickup(self):
        """Lo que se agarra con E: ("light", luz) / ("item", objeto) /
        (None, None). Gana lo MAS CERCANO al jugador. Las luces del piso
        solo cuentan si no tenes una luz encendida (si ya tenes una no se
        pueden agarrar, asi que no tapan a los objetos de al lado)."""

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

            self.items_picked += 1

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

        # Con el iman prendido lo vuelve a agarrar enseguida
        if self._magnet_active():

            self.show_message(
                "Apagá el imán (O) para soltar items"
            )

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

        self.count_stat("items_used")

        if item_id == "iman":

            self.show_message(
                "Usaste Imán: apretá O para activarlo o desactivarlo"
            )

        else:

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

        # Las claves tienen que ser las de ui/effects_bar.py (EFFECTS):
        # aceite = velocidad, cera = consumo lento, resina = vida gradual
        if self.speed_timer > 0:
            active["aceite"] = self.speed_timer / self.speed_total

        if self.burn_timer > 0:
            active["cera"] = self.burn_timer / self.burn_total

        if self.polvora_timer > 0:
            active["polvora"] = self.polvora_timer / self.polvora_total

        if self.regen_left > 0:
            active["resina"] = min(1.0, self.regen_left / self.regen_total)

        # Furia de la vela / antorcha
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

        # Alerta "Mosquito cerca!" (la calcula la arena; no tiene tiempo,
        # parpadea mientras dure el peligro)
        if self.has_match and any(
            getattr(a, "mosquito_alert", False) for a in self.arenas
        ):
            active["mosquito"] = 1.0

        return active

    def _menu_arena(self):
        """La sala de combate que tiene el menu abierto (o None)."""

        for arena in self.arenas:

            if arena.menu_open:
                return arena

        return None

    def _polvora_hit(self, damage):
        """La polvora lastima a lo que esta dentro de la luz."""

        # El radio de la luz esta en pixeles de pantalla: se pasa a
        # unidades del mundo (como la posicion de los enemigos)
        for arena in self.arenas:

            arena.hurt_in_radius(
                self.player.rect.center,
                self._light_radius_px / max(1, self.camera.zoom),
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

        # El personaje se dibuja de rect.height px de alto en PANTALLA
        # (no en unidades del mundo, que tienen zoom): el torso esta a
        # esa altura sobre los pies, pasada a unidades del mundo.
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

    def _attack(self):

        if self.state != "playing":
            return

        if not self.has_match:
            self.show_message("Necesitas una luz")
            return

        # Modo bola de fuego (solo antorcha): no hay swing, sale una bola
        if self._fire_available() and self.attack_mode == "fuego":
            self._shoot_fireball()
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

        if not self.melee.swinging and not self.melee.final_pass:
            return

        targets = [t for a in self.arenas for t in a.targets()]
        targets += list(self.doors.doors)
        targets += list(self.chests.chests)
        targets += [d for d in self.dummies if not d.dead]

        for target in self.melee.new_hits(targets, pivot):

            # Tercer golpe (fuerte): chispazo donde pego
            if self.melee.heavy:
                self.melee.add_impact(target.rect.center)

            self._hit_target(
                target,
                self.melee.damage,
                free=self.melee.fury
            )

    def _hit_target(self, target, damage, free=False):
        """Aplica un golpe (o una bola) a lo que toco.

        free -> True si no gasta vida de la luz (furia, o la bola que
        ya cobro su costo al salir).
        """

        light = light_stats(self.light_type)

        if isinstance(target, Door):

            if not target.breakable:

                # Ninguna luz la rompe (ej: la puerta azul)
                target.resist()

                self.show_message(
                    "Esta puerta no es posible de romper"
                )

            elif target.kind not in light["rompe"]:

                target.resist()

                if target.kind == "azul":
                    self.show_message(
                        "Solo la antorcha puede romper esta puerta"
                    )
                else:
                    self.show_message(
                        "Tu luz no puede romper esta puerta"
                    )

            else:

                cost = target.take_damage(damage)

                if not free:
                    self.vida -= cost

        elif isinstance(target, Chest):

            target.take_damage(damage)

            if target.ready:

                self._open_chest(target)

            else:

                self.show_message(
                    f"Faltan {format_time(target.cooldown)}"
                )

        else:

            target.take_damage(damage)

    # ---------- flashbang (destello) ----------

    def flashbang(self, x, y):
        """Pantalla en blanco unos 5 segundos (x, y = donde exploto, en
        coordenadas del mundo). Lo llama el enemigo Destello."""

        self.flash_t = FLASH_TOTAL
        self.flash_pos = (x, y)

    def _update_flash(self, dt):

        if self.flash_t > 0:
            self.flash_t = max(0.0, self.flash_t - dt)

    def _draw_flashbang(self):
        """Blanco por encima de TODO (mundo y HUD)."""

        if self.flash_t <= 0 or self.state != "playing":
            return

        w, h = self.screen.get_size()

        elapsed = FLASH_TOTAL - self.flash_t

        # El "pum": un circulo blanco que crece desde donde exploto
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

        # Toda blanca y al final se va aclarando
        if self.flash_t > FLASH_FADE:
            alpha = 255
        else:
            alpha = int(255 * self.flash_t / FLASH_FADE)

        self._flash_surf.set_alpha(alpha)

        self.screen.blit(self._flash_surf, (0, 0))

    # ---------- bola de fuego (antorcha) ----------

    def _fire_available(self):
        """La bola de fuego solo existe con la antorcha encendida."""

        return self.has_match and self.light_type == "antorcha"

    def _hud_attack_mode(self):
        """Que muestra el panel de al lado de la hotbar (None = oculto)."""

        return self.attack_mode if self._fire_available() else None

    def _toggle_attack_mode(self):
        """G (o tocar el panel): golpe comun <-> bola de fuego."""

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
        """Tira una bola hacia el mouse. False si todavia no se puede."""

        if self.fire_cooldown > 0:
            return False

        px, py = self._attack_pivot()
        mx, my = self._mouse_world()

        angle = math.atan2(my - py, mx - px)

        x = px + math.cos(angle) * FIRE_MUZZLE
        y = py + math.sin(angle) * FIRE_MUZZLE

        # Pegado a una pared: sale desde el cuerpo
        if not self.collision_map.point_is_walkable(x, y):
            x, y = px, py

        # Combo: la ultima bola de cada serie es la fuerte (x2 de dano)
        self.fire_combo += 1

        heavy = self.fire_combo >= FIRE_COMBO_SIZE

        damage = FIRE_DAMAGE * (FIRE_HEAVY_MULT if heavy else 1)

        self.fireballs.append(
            Fireball(x, y, angle, damage, heavy=heavy)
        )

        fury = self.melee.fury

        base_cooldown = FIRE_HEAVY_COOLDOWN if heavy else FIRE_COOLDOWN

        self.fire_cooldown = base_cooldown / (
            FIRE_FURY_SPEED if fury else 1.0
        )

        # Despues de la fuerte el combo arranca de nuevo
        if heavy:

            self.fire_combo = 0
            self.fire_combo_timer = 0.0

        else:

            self.fire_combo_timer = FIRE_COMBO_WINDOW

        self.count_stat("fireballs")

        # En furia la luz no se gasta
        if not fury:

            self.vida -= FIRE_COST * (
                FIRE_HEAVY_COST_MULT if heavy else 1.0
            )

        return True

    def _update_fireballs(self, dt):

        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

        # Si dejas de tirar un rato, el combo vuelve a empezar
        if self.fire_combo > 0:

            self.fire_combo_timer -= dt

            if self.fire_combo_timer <= 0:
                self.fire_combo = 0

        # Manteniendo el click sigue tirando bolas
        if self._fire_hold:

            if not pygame.mouse.get_pressed()[0]:

                self._fire_hold = False

            elif (
                self.state == "playing"
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
        targets += list(self.chests.chests)
        targets += [d for d in self.dummies if not d.dead]

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

                self.count_stat("chests_opened")

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
            MATCH_DURATION,
            cart=self.shop_cart
        )

    def _close_shop(self):

        # Guarda el carrito para la proxima vez que se abra
        if self.shop is not None:
            self.shop_cart = dict(self.shop.cart)

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

        # El vendedor los escupe por la boca, uno atras del otro
        item_ids = []

        for item_id, qty in cart.items():
            item_ids.extend([item_id] * qty)

        for item in self.shopkeeper.spit(item_ids, self.collision_map):

            if isinstance(item, LightItem):
                self.light_drops.append(item)
            else:
                self.world_items.append(item)

        self.show_message("Compra hecha")

        self.count_stat("purchases")

        # Compraste: el carrito queda vacio y se cierra la tienda
        if self.shop is not None:
            self.shop.clear()

        self.shop_cart = {}

        self._close_shop()

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

            "mode": self.mode,

            "inventory": inventory,

            "collected": list(
                self.collected
            ),

            "item_seed": self.item_seed,

            "arena_wave": self.arena.wave,
            "arena_completed": self.arena.completed,
            "arena_left_wave": self.arena_left.wave,
            "arena_left_completed": self.arena_left.completed,

            "broken_doors": sorted(self.doors.broken_ids),

            "chests": self.chests.save_data(),

            "enemies_seen": sorted(self.discovered_enemies),

            "stats": dict(self.stats),
            "zones_seen": sorted(self.zones_seen),
        }

        # En que objetivo vas (para seguir desde ahi al continuar)
        if self.objectives is not None:
            data["objective_index"] = self.objectives.index
            data["objectives_minimized"] = self.objectives.minimized

        elif self._objective_saved is not None:
            data["objective_index"] = int(self._objective_saved)

        save_progress(
            self.save_path,
            **data
        )

    def discover_enemy(self, key):
        """Marca un enemigo como descubierto (lo llama la arena)."""

        if key in self.discovered_enemies:
            return

        # Se guarda junto con el resto de la partida (al salir, pausar
        # o terminar la oleada)
        self.discovered_enemies.add(key)

    def save_progress(self):
        """Guarda la partida (lo usa main.py al cerrar la ventana)."""

        self._save()

    def apply_loss(self):
        """Consecuencias de perder (una sola vez).

        HARDCORE: se borra toda la partida.
        NORMAL: se pierden todos los items (inventario, luces) y queda
        solo el fosforo, en la cabana. Las oleadas, las puertas rotas y
        los cofres quedan igual que antes.
        """

        if self._loss_applied or not self.save_path:
            return

        self._loss_applied = True

        if self.mode == MODE_HARDCORE:

            if DELETE_SAVE_ON_LOSS:
                delete_save(self.save_path)
            else:
                self._save()

            return

        for i in range(self.hud.SLOTS):
            self.hud.items[i] = None
            self.hud.counts[i] = 0

        self.has_match = True
        self.light_type = "fosforo"
        self.vida = 1.0
        self.escudo = 0.0

        if not NORMAL_KEEP_COINS:
            self.coins = 0
            self.gems = 0

        spawn_x, spawn_y = get_spawn_point(self.collision_map, "cabana")
        self.player.rect.center = (spawn_x, spawn_y)

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
                    self.screen,
                    self.discovered_enemies
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

        menu_arena = self._menu_arena()

        if menu_arena is not None:

            # Botones del menu (Jugar con escape / sin escape / Salir)
            # y ESC para irse. Antes se buscaba "handle_menu_event", que
            # no existe: el menu abria pero no respondia a nada.
            menu_arena.handle_event(
                self,
                event
            )

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
        # CLICK EN EL PANEL DE LA ANTORCHA: golpe comun <-> bola de fuego
        # ---------------------------------------------------------

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.state == "playing"
            and self._hud_attack_mode() is not None
            and self.hud.attack_panel_rect.collidepoint(event.pos)
        ):

            self._toggle_attack_mode()

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
        # OBJETIVOS: minimizar (TAB o el boton "-" del cartel)
        # ---------------------------------------------------------

        if (
            self.objectives is not None
            and self.state == "playing"
            and self.objectives.handle_event(event)
        ):

            return None

        # ---------------------------------------------------------
        # TECLAS DEL JUEGO
        # ---------------------------------------------------------

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_F3:

                self.debug_items = not self.debug_items

            elif event.key == pygame.K_F4:

                self.debug_combat = not self.debug_combat

            elif event.key == pygame.K_F1:

                # Ayuda: vuelve a mostrar todas las instrucciones
                if self.state == "playing":

                    self.tutorial = Tutorial(
                        (self.width, self.height)
                    )

                    return None

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

                # Agarrar lo que tengas mas cerca (luz del piso u objeto).
                # Una luz que no podes agarrar (ya tenes una encendida)
                # NO bloquea: se agarra el objeto de al lado.
                kind, thing = self._nearest_pickup()

                if kind == "light":

                    self.light_drops.remove(
                        thing
                    )

                    self.equip_match(
                        thing.kind,
                        thing.life
                    )

                    return None

                if kind == "item":

                    self.pick_up_item(
                        thing
                    )

                    return None

                # Los cofres ya NO se abren con E: solo pegandoles con
                # la luz (o usando la ganzua).

            elif event.key == pygame.K_q:

                if self.selected_slot == "equipped":

                    if self.has_match:
                        self._drop_match()

                else:

                    self.drop_item(
                        self.selected_slot
                    )

            elif event.key == pygame.K_o:

                # Iman: O lo prende y O lo apaga
                if not self._magnet_available():

                    self.show_message(
                        "No tenés el imán: usalo desde el inventario"
                    )

                else:

                    self.magnet_mode = not self.magnet_mode

                    self.show_message(
                        "Imán activado (O para desactivarlo)"
                        if self.magnet_mode
                        else "Imán desactivado (O para activarlo)"
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

            elif event.key == pygame.K_g:

                self._toggle_attack_mode()

            elif event.key == pygame.K_SPACE:

                self._attack()

        # Click izquierdo para atacar
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):

            self._fire_hold = True

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

            # Si moris con el flashbang puesto, el blanco no te sigue
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

                # Hardcore: la partida ya no existe, vuelve al menu.
                # Normal: vuelve directo a jugar (main.py recarga la
                # partida ya sin los items).
                if self.mode == MODE_HARDCORE and DELETE_SAVE_ON_LOSS:
                    return "menu"

                return "respawn"

            return None

        # ---------------------------------------------------------
        # MENSAJES
        # ---------------------------------------------------------

        if self.message_timer > 0:

            self.message_timer -= dt

            if self.message_timer <= 0:

                self.message = ""

        # ---------------------------------------------------------
        # MENU DE COMBATE: el juego queda en pausa (el personaje no se
        # mueve, nada avanza ni se gasta la luz) hasta elegir
        # ---------------------------------------------------------

        menu_arena = self._menu_arena()

        if menu_arena is not None:

            menu_arena.update_menu(
                dt
            )

            return None

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
        # GUIA: nombre de la sala y objetivos
        # ---------------------------------------------------------

        zone = self.zone_tracker.update(
            self.player.rect.center
        )

        if zone is not None:

            self.zone_banner.show(
                zone.name
            )

        if zone is not None:
            self.zones_seen.add(zone.id)

        self.zone_banner.update(
            dt
        )

        if self.objectives is not None:

            self.objectives.update(
                dt,
                self
            )

            if self.objectives.finished:

                # Se acuerda que ya los terminaste (para el guardado)
                self._objective_saved = 10 ** 6

                self.objectives = None

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

        self._update_fireballs(dt)

        self._update_flash(dt)

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

        for arena in self.arenas:

            arena.update(
                self,
                dt
            )

        # Bloques aplastadores de la sala izquierda
        self.crushers.update(self, dt)

        # Si los golpes de los enemigos te dejaron sin vida
        if self.has_match and self.vida <= 0:

            self._burn_out()

        # ---------------------------------------------------------
        # MONEDAS CERCANAS
        # ---------------------------------------------------------

        # El vendedor (boca abierta mientras escupe) y las luces que
        # salen volando de su boca
        self.shopkeeper.update(dt)

        for drop in self.light_drops:

            if getattr(drop, "fly", None) is not None:
                drop.update_fly(dt)

        px, py = self.player.rect.center

        magnet_on = self._magnet_active()

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

        # En la tienda esta todo iluminado: sin luz en la mano no corre
        # la cuenta regresiva (se reinicia al salir)
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

    # ---------- iman ----------

    def _magnet_available(self):
        """Hay iman para prender (item usado y con tiempo, o modo prueba)."""

        return self.magnet_timer > 0 or not MAGNET_NEEDS_ITEM

    def _magnet_active(self):
        """El iman esta atrayendo objetos ahora mismo."""

        return self.magnet_mode and self._magnet_available()

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

    def _load_magnet_imgs(self):
        """Carga (una vez) los iconos del iman: prendido, apagado y la
        tecla O. Si falta algun PNG se dibuja un reemplazo."""

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

            # Sin PNG: el mismo icono apagado + un tajo rojo
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
        """Icono del iman a la izquierda de las monedas (prendido o
        apagado) con la tecla O para prenderlo y apagarlo."""

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

        # Tecla O abajo a la derecha del icono: avisa como se maneja
        key = self._magnet_imgs["key"]

        self.screen.blit(
            key,
            key.get_rect(
                bottomright=(rect.right + 4, rect.bottom + 4)
            ).topleft
        )

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

        self.crushers.draw(self.screen, self.camera)

        for arena in self.arenas:
            arena.draw_world(self.screen, self.camera)

        self.player.draw(
            self.screen,
            self.camera
        )

        sources = []

        # El cofre del premio y la explosion tambien iluminan
        for arena in self.arenas:
            sources.extend(arena.light_sources())

        for drop in self.light_drops:

            # Todavia "dentro" de la boca del vendedor: no ilumina
            fly = getattr(drop, "fly", None)

            if fly is not None and fly["delay"] > 0:
                continue

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

        # Las bolas de fuego iluminan por donde pasan
        for ball in self.fireballs:
            sources.append(ball.light_source())

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
        for arena in self.arenas:
            arena.draw_fx(self.screen, self.camera)

        # El golpe va encima de la oscuridad, para que brille
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

            # El cartelito [E] sale sobre lo que se va a agarrar
            _, near_thing = self._nearest_pickup()

            if near_thing is not None:
                near_thing.draw_prompt(self.screen, self.camera)

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
            ),
            attack_mode=self._hud_attack_mode()
        )

        self._draw_gems()

        self._draw_magnet_mode()

        # Cubitos de efectos arriba al centro (se vacian hasta desaparecer)
        active = {}

        if self.state == "playing":
            active = self._active_effects()

        self.effects_bar.draw(self.screen, active)

        # Objetivos (arriba a la derecha) y nombre de la sala
        if self.state == "playing":

            if self.objectives is not None:
                self.objectives.draw(self.screen)

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

        # Flashbang del destello: blanco encima de todo
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

            self.screen.blit(self.pantalla_perdiste, (0, 0))