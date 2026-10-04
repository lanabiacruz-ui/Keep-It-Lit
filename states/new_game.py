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
from ui.chest_minigame import ChestMinigame
from ui.shop_ui import ShopUI


# Radio de luz, consumo y espera entre golpes de cada luz (fosforo,
# vela...): se cambian en world/lights.py

MATCH_POS = (818, 1002)

# Cuanto dura prendido el fosforo (vida), en segundos. Corto para dar
# tension, pero lo bastante largo para explorar y decidir que hacer.
MATCH_DURATION = 30.0

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

# A que distancia (unidades del mundo) del cofre sirve la ganzua.
GANZUA_DISTANCE = 48

# A que distancia se juntan solas las monedas del piso.
COIN_PICKUP_DISTANCE = 14

# Cada cuanto hace dano la luz con polvora (segundos).
POLVORA_TICK = 0.5

# F8 = trampa de prueba: suma esta cantidad de monedas.
DEBUG_COINS = 100000

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
            darkness_alpha=250
        )

        self.hud = Hud((self.width, self.height))

        self.coins = int(self.save_data.get("coins", 0))

        # ---------- Fosforo / vida ----------

        self.has_match = bool(self.save_data.get("has_match", False))

        # Vida del fosforo actual, de 0.0 a 1.0
        self.vida = 1.0

        # Escudo: por ahora solo se muestra, arranca vacio
        self.escudo = 0.0

        # Que luz esta equipada: "fosforo" o "vela" (ver world/lights.py)
        self.light_type = self.save_data.get("light", "fosforo")

        if self.light_type not in LIGHTS:
            self.light_type = "fosforo"

        # Que tan rapido se consume la luz de base (1.0 = fosforo,
        # 0.5 = vela: dura el doble). Lo fija equip_match().
        self.base_burn = 1.0

        # El golpe se crea antes porque equip_match() le avisa que luz hay
        self.melee = Melee()

        # Furia de la vela: cuenta atras hasta la proxima furia y
        # cuanto le queda a la que esta activa (ver world/lights.py)
        self.fury_timer = 0.0
        self.fury_left = 0.0

        # Luces tiradas en el piso (cada una recuerda su vida)
        self.light_drops = []

        if self.has_match:
            self.equip_match(self.light_type)
        else:
            self.light_drops.append(LightItem("fosforo", *MATCH_POS))

        # ---------- Objetos (madera, aceite, cera) ----------

        self.item_defs = load_item_defs()

        saved_inv = self.save_data.get("inventory", [])

        for i in range(self.hud.SLOTS):

            if i >= len(saved_inv):
                break

            entry = saved_inv[i]

            # Formato nuevo: [id, cantidad]. Formato viejo: solo el id.
            if isinstance(entry, (list, tuple)) and len(entry) == 2:
                item_id, count = entry[0], int(entry[1])
            else:
                item_id, count = entry, 1

            # Las luces (fosforo, vela) nunca van al inventario: si una
            # partida vieja las tenia ahi, quedan tiradas en el piso
            if item_id in LIGHTS and count > 0:

                for _ in range(count):

                    px, py = self.player.rect.center

                    self.light_drops.append(
                        LightItem(item_id, px + random.randint(-12, 12), py)
                    )

                continue

            if item_id in self.item_defs and count > 0:

                self.hud.items[i] = item_id
                self.hud.counts[i] = min(count, self._max_stack(item_id))

        self.collected = set(self.save_data.get("collected", []))

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

        # F3 = ver donde estan los objetos (para probar)
        self.debug_items = False
        self.debug_font = pygame.font.Font(None, 22)

        # Efectos temporales
        self.speed_timer = 0.0
        self.burn_factor = 1.0
        self.burn_timer = 0.0

        # Polvora: la luz hace dano mientras dura
        self.polvora_timer = 0.0
        self.polvora_dps = 0.0
        self._polvora_acc = 0.0

        # Resina: cura de a poco. regen_left = cuanta vida falta sumar
        self.regen_left = 0.0
        self.regen_rate = 0.0

        # Radio de la luz en pantalla (px), lo calcula draw()
        self._light_radius_px = self._light_radius()

        # ---------- Combate ----------
        # (self.melee ya se creo arriba, junto con la luz)
        self.melee.set_light(self.light_type)

        # Munecos de practica (F5). Mas adelante aca van los enemigos.
        self.dummies = []

        # F4 = ver el area de ataque (para probar)
        self.debug_combat = False

        # Aviso en pantalla
        self.message = ""
        self.message_timer = 0.0

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

    def equip_match(self, kind=None, life=None):
        """Equipa una luz (fosforo o vela).

        kind -> cual (None = la que ya estaba)
        life -> con cuanta vida (None = no se toca self.vida)"""

        # OJO: la vida solo cambia si se pasa `life`. Si la luz ya se
        # habia usado un poco y la soltaste, al agarrarla de nuevo tiene
        # que seguir con la vida que le quedaba, no volver a llenarse.
        if kind in LIGHTS:
            self.light_type = kind

        if life is not None:
            self.vida = max(0.0, min(1.0, float(life)))

        self.base_burn = light_stats(self.light_type)["consumo"]

        self.has_match = True
        self.hud.equip(self.light_type)
        self.player.set_torch(True, self.light_type)
        self.melee.set_light(self.light_type)
        self._reset_fury()

    def _reset_fury(self):
        """Apaga la furia y reinicia la espera para la proxima."""

        self.fury_left = 0.0
        self.fury_timer = light_stats(self.light_type).get("furia_cada", 0)
        self.melee.set_fury(1.0)

    def _update_fury(self, dt):
        """Cada `furia_cada` segundos la luz entra en furia durante
        `furia_duracion` segundos: pega `furia_velocidad` veces mas
        rapido. Solo corre con la luz prendida."""

        if not self.has_match:

            if self.fury_left > 0 or self.melee.fury:
                self._reset_fury()

            return

        stats = light_stats(self.light_type)
        every = stats.get("furia_cada", 0)
        length = stats.get("furia_duracion", 0)

        if every <= 0 or length <= 0:
            return

        if self.fury_left > 0:

            self.fury_left -= dt

            if self.fury_left <= 0:

                self.fury_left = 0.0
                self.fury_timer = every
                self.melee.set_fury(1.0)

        else:

            self.fury_timer -= dt

            if self.fury_timer <= 0:

                self.fury_left = length
                self.melee.set_fury(stats.get("furia_velocidad", 1.0))

    def _light_radius(self):
        """Radio de la luz equipada, en pixeles de pantalla."""

        return light_stats(self.light_type)["radio"]

    def _nearest_light_drop(self):
        """La luz del piso mas cercana a la que se llega (o None)."""

        near = [d for d in self.light_drops if d.is_near(self.player)]

        if not near:
            return None

        px, py = self.player.rect.center

        return min(
            near,
            key=lambda d: pygame.Vector2(d.rect.center).distance_to(
                (px, py)
            )
        )

    def _drop_match(self):

        x, y = self.player.rect.center

        # Queda en el piso con la vida que le quedaba
        self.light_drops.append(
            LightItem(self.light_type, x, y, life=self.vida)
        )

        self.has_match = False
        self.hud.equip(None)
        self.player.set_torch(False)

    def _burn_out(self):

        # Se le acabo la vida al fosforo: se consume, no queda tirado
        self.vida = 0.0
        self.base_burn = 1.0
        self.regen_left = 0.0
        self.has_match = False
        self.hud.equip(None)
        self.player.set_torch(False)
        self._reset_fury()

    # ---------- objetos ----------

    def show_message(self, text):

        self.message = text
        self.message_timer = MESSAGE_TIME

    def _nearest_item(self):

        near = [
            it for it in self.world_items
            if not it.auto and it.is_near(self.player)
        ]

        if not near:
            return None

        px, py = self.player.rect.center

        return min(
            near,
            key=lambda it: pygame.Vector2(it.rect.center).distance_to(
                (px, py)
            )
        )

    def _max_stack(self, item_id):

        return int(
            self.item_defs.get(item_id, {}).get("max_pila", MAX_STACK)
        )

    def _slot_for(self, item_id):
        """Slot donde entra 1 unidad: primero una pila que no este
        llena, despues un slot vacio. None si no hay lugar."""

        limit = self._max_stack(item_id)

        for i, stored in enumerate(self.hud.items):

            if stored == item_id and self.hud.counts[i] < limit:
                return i

        for i, stored in enumerate(self.hud.items):

            if stored is None:
                return i

        return None

    def pick_up_item(self, item):

        if item.item_id == "moneda":

            # Las monedas del cofre de la sala de combate valen mas
            self.coins += getattr(item, "value", 1)
            self.world_items.remove(item)

            return

        # Fosforo / vela: NUNCA al inventario. Se equipan directo en el
        # casillero aislado (y solo si no hay otra luz encendida).
        if item.item_id in LIGHTS:

            if self.has_match:

                self.show_message("Ya tenes una luz encendida")

                return

            self.world_items.remove(item)

            if item.spawn_id is not None:
                self.collected.add(item.spawn_id)

            self.equip_match(item.item_id, 1.0)

            name = self.item_defs.get(item.item_id, {}).get(
                "nombre", item.item_id
            )

            self.show_message(f"Equipaste {name}")

            return

        slot = self._slot_for(item.item_id)

        if slot is None:

            self.show_message("Inventario lleno")

            return

        self.hud.items[slot] = item.item_id
        self.hud.counts[slot] += 1

        self.world_items.remove(item)

        if item.spawn_id is not None:
            self.collected.add(item.spawn_id)

        name = self.item_defs[item.item_id].get("nombre", item.item_id)

        self.show_message(f"Agarraste {name}")

    def _remove_one(self, slot):

        self.hud.counts[slot] -= 1

        if self.hud.counts[slot] <= 0:

            self.hud.counts[slot] = 0
            self.hud.items[slot] = None

    def drop_item(self, slot):

        item_id = self.hud.items[slot]

        if item_id is None:
            return

        x, y = self.player.rect.center

        self.world_items.append(WorldItem(item_id, x, y))

        # Suelta de a una unidad
        self._remove_one(slot)

    def use_item(self, slot):

        item_id = self.hud.items[slot]

        if item_id is None:
            return

        data = self.item_defs.get(item_id, {})

        if data.get("requiere_fosforo") and not self.has_match:

            self.show_message("Necesitas el fosforo encendido")

            return

        effects = data.get("efectos", [])

        # No gastar madera si la llama ya esta al maximo
        if (
            any(e.get("tipo") == "vida_sumar" for e in effects)
            and not any(e.get("tipo") == "vida_fijar" for e in effects)
            and self.vida >= 1.0
        ):

            self.show_message("La llama ya esta al maximo")

            return

        # No gastar cera si ya hay una activa
        if (
            any(e.get("tipo") == "consumo_lento" for e in effects)
            and self.burn_timer > 0
        ):

            self.show_message("La cera ya esta haciendo efecto")

            return

        # No gastar polvora si ya hay una activa
        if (
            any(e.get("tipo") == "luz_dano" for e in effects)
            and self.polvora_timer > 0
        ):

            self.show_message("La polvora ya esta haciendo efecto")

            return

        # No gastar resina si la llama ya esta al maximo o ya hay una activa
        if any(e.get("tipo") == "vida_gradual" for e in effects):

            if self.vida >= 1.0:

                self.show_message("La llama ya esta al maximo")

                return

            if self.regen_left > 0:

                self.show_message("La resina ya esta haciendo efecto")

                return

        # Fosforo / vela: solo sirven si no hay ninguna luz encendida
        if (
            any(e.get("tipo") == "encender" for e in effects)
            and self.has_match
        ):

            self.show_message("Ya tenes una luz encendida")

            return

        # Ganzua: necesita un cofre listo cerca
        chest = None

        if any(e.get("tipo") == "abrir_cofre" for e in effects):

            chest = self.chests.nearest_ready(
                self.player.rect.center, GANZUA_DISTANCE
            )

            if chest is None:

                self.show_message("No hay un cofre listo cerca")

                return

        for effect in effects:

            kind = effect.get("tipo")

            if kind == "vida_sumar":

                self.vida = min(1.0, self.vida + effect["valor"])

            elif kind == "vida_fijar":

                self.vida = effect["valor"]

            elif kind == "velocidad":

                self.player.movement.speed_mult = effect["multiplicador"]
                self.speed_timer = effect["duracion"]

            elif kind == "consumo_lento":

                self.burn_factor = effect["factor"]
                self.burn_timer = effect["duracion"]

            elif kind == "luz_dano":

                self.polvora_dps = effect.get("dano_por_segundo", 1)
                self.polvora_timer = effect["duracion"]
                self._polvora_acc = 0.0

            elif kind == "vida_gradual":

                # Suma `valor` de vida repartido en `duracion` segundos
                # (sin pasar del 100%)
                self.regen_left = effect["valor"]
                self.regen_rate = effect["valor"] / effect["duracion"]

            elif kind == "abrir_cofre" and chest is not None:

                self._open_chest(chest)

            elif kind == "encender":

                self.equip_match(
                    effect.get("luz", "fosforo"),
                    effect.get("vida", 1.0)
                )

        self._remove_one(slot)

        self.show_message(f"Usaste {data.get('nombre', item_id)}")

    def _draw_debug_items(self):

        for item in self.world_items:

            center = self.camera.apply(item.rect).center

            pygame.draw.circle(
                self.screen, (255, 230, 80), center, 22, width=3
            )

            label = self.debug_font.render(
                item.item_id, True, (255, 230, 80)
            )

            self.screen.blit(
                label,
                label.get_rect(midtop=(center[0], center[1] + 26))
            )

        px, py = self.player.rect.center

        info = self.debug_font.render(
            f"F3  jugador=({px}, {py})  objetos={len(self.world_items)}",
            True,
            (255, 230, 80)
        )

        self.screen.blit(info, (12, self.height - 30))

    # ---------- combate ----------

    def _attack_pivot(self):
        """Desde donde sale el area de ataque: el torso del jugador."""

        # El sprite se dibuja a tamano real (sin zoom) apoyado en los
        # pies, asi que el torso queda unos pixeles de pantalla arriba
        # de los pies; hay que pasarlos a unidades del mundo.
        rect = self.player.image_rect

        lift = rect.height * TORSO_HEIGHT / self.camera.zoom

        return (rect.centerx, rect.bottom - lift)

    def _mouse_world(self):
        """Posicion del mouse en coordenadas del mundo."""

        mx, my = pygame.mouse.get_pos()

        return (
            (mx + self.camera.x) / self.camera.zoom,
            (my + self.camera.y) / self.camera.zoom
        )

    def combat_targets(self):
        """Todo lo que el fosforo puede golpear (cada uno con .rect y
        .take_damage(n))."""

        return (
            self.dummies
            + self.doors.doors
            + self.chests.chests
            + self.arena.targets()
        )

    def start_attack(self):

        if not self.has_match:
            return

        if not self.melee.start():
            return

        # Cada golpe gasta un poco de luz (aunque no le pegues a nada).
        # En furia no gasta. El fosforo gasta bastante mas que la vela.
        if not self.melee.fury:
            self.vida -= light_stats(self.light_type).get("golpe_costo", 0.0)

        # El personaje mira hacia donde pega
        dx = math.cos(self.melee.aim)
        dy = math.sin(self.melee.aim)

        if abs(dx) > abs(dy):
            self.player.direction = "right" if dx > 0 else "left"
        else:
            self.player.direction = "down" if dy > 0 else "up"

    def _update_combat(self, dt):

        if not self.has_match:
            self.melee.cancel()

        self._update_fury(dt)

        pivot = self._attack_pivot()

        self.melee.update(dt, pivot, self._mouse_world())

        for target in self.melee.new_hits(self.combat_targets(), pivot):

            result = target.take_damage(self.melee.damage)

            # Cada golpe a una puerta le saca vida al fosforo
            if isinstance(target, Door):
                self.vida -= result

            # Pegarle a un cofre abre el minijuego
            elif isinstance(target, Chest):
                self._on_chest_hit(target)

        self.doors.update(dt)

        for dummy in self.dummies:
            dummy.update(dt)

        self.dummies = [d for d in self.dummies if not d.dead]

    # ---------- cofres ----------

    def _on_chest_hit(self, chest):

        if chest.busy:
            return

        if chest.cooldown > 0:

            self.show_message(
                f"Cofre vacio. Volve en {format_time(chest.cooldown)}"
            )

            return

        chest.busy = True

        self.minigame_chest = chest
        self.minigame = ChestMinigame((self.width, self.height))

        # Se corta el golpe en curso
        self.melee.cancel()

    def _open_chest(self, chest):
        """El cofre suelta sus items al piso. Cada cofre se puede abrir
        10 a 15 veces (se sortea la primera vez); cuando se le acaban,
        queda en espera."""

        # Gasta una apertura. True = era la ultima y ya quedo en espera.
        exhausted = self.chests.consume_use(chest)

        drops = self.chests.spawn_drops(
            chest, self.collision_map, self.item_defs
        )

        self.world_items.extend(drops)

        # Se ve abierto un ratito (si quedo en espera, ya se ve abierto)
        chest.show_open()

        if exhausted:

            self.show_message(
                f"Cofre abierto: salieron {len(drops)} cosas. "
                "Se quedo vacio"
            )

        else:

            self.show_message(
                f"Cofre abierto: salieron {len(drops)} cosas"
            )

    def _close_minigame(self, result):

        chest = self.minigame_chest

        self.minigame = None
        self.minigame_chest = None

        if chest is None:
            return

        chest.busy = False

        if result == "win":

            self._open_chest(chest)

        elif result == "fail":

            self.show_message("El cofre se cerro. Pegale de nuevo")

    # ---------- tienda ----------

    def _open_shop(self):

        self.shop = ShopUI(
            (self.width, self.height),
            self.catalog,
            self.item_defs,
            self.coins
        )

        # Se corta el golpe en curso
        self.melee.cancel()

    def _buy(self, cart):
        """Cobra el carrito y el vendedor escupe todo lo comprado."""

        total = sum(
            self.shop_prices.get(item_id, 0) * qty
            for item_id, qty in cart.items()
        )

        if total <= 0 or total > self.coins:
            return

        self.coins -= total

        ids = []

        for item_id, qty in cart.items():

            if item_id in self.shop_prices:
                ids.extend([item_id] * qty)

        drops = self.shopkeeper.spit(ids, self.collision_map)

        self.world_items.extend(drops)

        self.shop = None

        self.show_message(f"Compraste {len(ids)} cosas")

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
            light=self.light_type,
            coins=self.coins,
            inventory=[
                [item_id, self.hud.counts[i]] if item_id else None
                for i, item_id in enumerate(self.hud.items)
            ],
            collected=sorted(self.collected),
            broken_doors=sorted(self.doors.broken_ids),
            chests=self.chests.save_data(),
            item_seed=self.item_seed,
            arena_wave=self.arena.wave
        )

    # ---------- actualizaciones extra ----------

    def _update_world_extras(self, dt):
        """Cofres, items que salen volando y monedas."""

        self.chests.update(dt)

        self.shopkeeper.update(dt)

        for item in self.world_items:
            item.update_fly(dt)

        # Las monedas se juntan solas al pasar cerca
        px, py = self.player.rect.center

        for item in list(self.world_items):

            if (
                item.auto
                and item.fly is None
                and pygame.Vector2(item.rect.center).distance_to((px, py))
                <= COIN_PICKUP_DISTANCE
            ):

                self.pick_up_item(item)

    def _update_effects(self, dt):
        """Polvora y resina. Solo corren con el fosforo prendido."""

        # Resina: sube la vida de a poco
        if self.regen_left > 0:

            add = min(self.regen_rate * dt, self.regen_left)

            self.vida = min(1.0, self.vida + add)
            self.regen_left -= add

            if self.vida >= 1.0:
                self.regen_left = 0.0

        # Polvora: la luz quema lo que alumbra
        if self.polvora_timer > 0:

            self.polvora_timer = max(0.0, self.polvora_timer - dt)
            self._polvora_acc += dt

            while self._polvora_acc >= POLVORA_TICK:

                self._polvora_acc -= POLVORA_TICK

                self._burn_with_light(self.polvora_dps * POLVORA_TICK)

    def _burn_with_light(self, amount):

        radius = self._light_radius() / self.camera.zoom

        px, py = self.player.rect.center

        for target in self.dummies + self.arena.targets():

            size = max(target.rect.width, target.rect.height) / 2

            dist = pygame.Vector2(target.rect.center).distance_to((px, py))

            if dist <= radius + size:
                target.take_damage(amount)

    # ---------- eventos ----------

    def handle_event(self, event):

        if self.state != "playing":
            return None

        # Con el minijuego abierto, solo el minijuego recibe los eventos
        if self.minigame is not None:

            if self.minigame.handle_event(event) == "cancel":
                self._close_minigame("cancel")

            return None

        # Con el menu de la sala de combate abierto, solo el menu
        if self.arena.menu_open:

            self.arena.handle_event(self, event)

            return None

        # Con la tienda abierta, solo la tienda recibe los eventos
        if self.shop is not None:

            result = self.shop.handle_event(event)

            if result == "close":
                self.shop = None

            elif isinstance(result, tuple) and result[0] == "buy":
                self._buy(result[1])

            return None

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                self.save_progress()

                return "menu"

            if event.key == pygame.K_F3:

                self.debug_items = not self.debug_items

            if event.key == pygame.K_F4:

                self.debug_combat = not self.debug_combat

            if event.key == pygame.K_F5:

                wx, wy = self._mouse_world()

                self.dummies.append(TrainingDummy(wx, wy))

            # F8 = +100000 monedas (para probar)
            if event.key == pygame.K_F8:

                self.coins += DEBUG_COINS

                self.show_message(f"+{DEBUG_COINS} monedas")

            if event.key == pygame.K_e:

                drop = self._nearest_light_drop()

                # Luz del piso: se equipa si no tenes otra encendida
                if drop is not None and not self.has_match:

                    self.light_drops.remove(drop)
                    self.equip_match(drop.kind, drop.life)

                else:

                    item = self._nearest_item()

                    if item is not None:
                        self.pick_up_item(item)

                    # Si no hay nada para agarrar, hablarle al vendedor
                    elif self.shopkeeper.can_talk(self.player):
                        self._open_shop()

                    elif drop is not None:
                        self.show_message("Ya tenes una luz encendida")

            # 1 = seleccionar la cosa iluminadora equipada
            if event.key == pygame.K_1:

                self.selected_slot = "equipped"
                self.hud.selected = None

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

                    self.drop_item(self.selected_slot)

        elif event.type == pygame.MOUSEBUTTONDOWN:

            slot = self.hud.slot_at(event.pos)

            # Click izquierdo: seleccionar el slot
            if event.button == 1 and slot is not None:

                self.selected_slot = slot
                self.hud.selected = slot

            # Click izquierdo fuera del inventario: pegar con el fosforo
            elif (
                event.button == 1
                and not self.hud.bar_rect.collidepoint(event.pos)
                and not self.hud.equipped_rect.collidepoint(event.pos)
            ):

                self.start_attack()

            # Click derecho: usar el item (el del slot bajo el mouse,
            # o si no hay, el del slot seleccionado)
            elif event.button == 3:

                if slot is None and isinstance(self.selected_slot, int):
                    slot = self.selected_slot

                if slot is not None:
                    self.use_item(slot)

        return None

    # ---------- update ----------

    def update(self, dt):

        if self.state == "playing":

            # Con la tienda abierta el tiempo se detiene (ni se gasta
            # el fosforo ni corre la cuenta regresiva)
            if self.shop is not None:

                self.shop.update(dt)

                return None

            # Con el menu de la sala de combate abierto tambien se
            # detiene el tiempo
            if self.arena.menu_open:

                self.arena.update_menu(dt)

                return None

            # Con el minijuego abierto el jugador no se mueve
            if self.minigame is None:
                self.player.update(dt, self.collision_map)

            self.camera.update(self.player, dt)

            if self.speed_timer > 0:

                self.speed_timer -= dt

                if self.speed_timer <= 0:
                    self.player.movement.speed_mult = 1.0

            if self.message_timer > 0:
                self.message_timer -= dt

            if self.minigame is None:

                self._update_combat(dt)

                self.arena.update(self, dt)

            else:

                result = self.minigame.update(dt)

                if result is not None:
                    self._close_minigame(result)

            self._update_world_extras(dt)

            if self.has_match:

                # La cera ralentiza el consumo por tiempo limitado.
                # Su tiempo solo corre mientras el fosforo esta prendido.
                if self.burn_timer > 0:

                    self.burn_timer -= dt

                    if self.burn_timer <= 0:
                        self.burn_timer = 0.0
                        self.burn_factor = 1.0

                self._update_effects(dt)

                self.vida -= (
                    dt * self.burn_factor * self.base_burn / MATCH_DURATION
                )

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

            if self.vida < FLICKER_THRESHOLD:

                self._flicker_time += 0.02

                flicker = 0.55 + 0.45 * abs(
                    math.sin(self._flicker_time * 18)
                )

                radius *= flicker

            self._light_radius_px = radius

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

        # Polvora: aro naranja en el borde de la luz
        if self.has_match and self.polvora_timer > 0:

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

            elif (
                self.shop is None
                and self.shopkeeper.can_talk(self.player)
            ):
                self.shopkeeper.draw_prompt(self.screen, self.camera)

        self.hud.draw(
            self.screen,
            vida=self.vida if self.has_match else 0.0,
            escudo=self.escudo,
            countdown=self.no_light_timer,
            coins=self.coins,
            equipped_selected=self.selected_slot == "equipped"
        )

        if self.state == "playing" and self.has_match:

            status = []

            if self.burn_timer > 0:
                status.append(
                    (f"Cera: {math.ceil(self.burn_timer)}s", (255, 225, 140))
                )

            if self.fury_left > 0:
                status.append(
                    (f"Furia: {math.ceil(self.fury_left)}s", (255, 120, 50))
                )

            if self.polvora_timer > 0:
                status.append(
                    (f"Polvora: {math.ceil(self.polvora_timer)}s", (255, 150, 70))
                )

            if self.regen_left > 0:
                secs = math.ceil(self.regen_left / self.regen_rate)
                status.append((f"Resina: {secs}s", (200, 150, 90)))

            font = self.hud.msg_font

            for i, (txt, color) in enumerate(status):

                shadow = font.render(txt, True, (0, 0, 0))
                label = font.render(txt, True, color)

                pos = label.get_rect(
                    midtop=(self.width // 2, 18 + i * 28)
                )

                self.screen.blit(shadow, pos.move(1, 1))
                self.screen.blit(label, pos)

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

        if self.arena.menu_open:
            self.arena.draw_menu(self.screen, self)

        if self.minigame is not None:

            self.minigame.draw(self.screen)

        if self.shop is not None:

            self.shop.draw(self.screen)

        if self.state in ("dying", "lost"):

            self.fade_overlay.set_alpha(int(self.fade_alpha))

            self.screen.blit(self.fade_overlay, (0, 0))

        if self.state == "lost":

            self.screen.blit(self.pantalla_perdiste, (0, 0))