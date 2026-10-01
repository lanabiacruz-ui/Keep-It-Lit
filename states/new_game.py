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
    MatchItem,
    WorldItem,
    load_item_defs,
    load_spawn_zones,
    make_spawn_items
)
from world.melee import Melee, TrainingDummy
from ui.hud import Hud


PLAYER_LIGHT_RADIUS = 100
MATCH_LIGHT_RADIUS = 60

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

        # ---------- Combate ----------
        self.melee = Melee()

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

    # ---------- objetos ----------

    def show_message(self, text):

        self.message = text
        self.message_timer = MESSAGE_TIME

    def _nearest_item(self):

        near = [
            it for it in self.world_items
            if it.is_near(self.player)
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

        return self.dummies

    def start_attack(self):

        if not self.has_match:
            return

        if not self.melee.start():
            return

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

        pivot = self._attack_pivot()

        self.melee.update(dt, pivot, self._mouse_world())

        for target in self.melee.new_hits(self.combat_targets(), pivot):
            target.take_damage(self.melee.damage)

        for dummy in self.dummies:
            dummy.update(dt)

        self.dummies = [d for d in self.dummies if not d.dead]

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
            coins=self.coins,
            inventory=[
                [item_id, self.hud.counts[i]] if item_id else None
                for i, item_id in enumerate(self.hud.items)
            ],
            collected=sorted(self.collected),
            item_seed=self.item_seed
        )

    # ---------- eventos ----------

    def handle_event(self, event):

        if self.state != "playing":
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

            if event.key == pygame.K_e:

                if (
                    self.match_item is not None
                    and self.match_item.is_near(self.player)
                ):

                    self.match_item = None
                    self.equip_match()

                else:

                    item = self._nearest_item()

                    if item is not None:
                        self.pick_up_item(item)

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

            self.player.update(dt, self.collision_map)

            self.camera.update(self.player, dt)

            if self.speed_timer > 0:

                self.speed_timer -= dt

                if self.speed_timer <= 0:
                    self.player.movement.speed_mult = 1.0

            if self.message_timer > 0:
                self.message_timer -= dt

            self._update_combat(dt)

            if self.has_match:

                # La cera ralentiza el consumo por tiempo limitado.
                # Su tiempo solo corre mientras el fosforo esta prendido.
                if self.burn_timer > 0:

                    self.burn_timer -= dt

                    if self.burn_timer <= 0:
                        self.burn_timer = 0.0
                        self.burn_factor = 1.0

                self.vida -= dt * self.burn_factor / MATCH_DURATION

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

        for item in self.world_items:
            item.draw(self.screen, self.camera)

        for dummy in self.dummies:
            dummy.draw(self.screen, self.camera)

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

        if (
            self.match_item is not None
            and self.match_item.is_near(self.player)
        ):
            self.match_item.draw_prompt(self.screen, self.camera)

        elif self.state == "playing":

            near_item = self._nearest_item()

            if near_item is not None:
                near_item.draw_prompt(self.screen, self.camera)

        self.hud.draw(
            self.screen,
            vida=self.vida if self.has_match else 0.0,
            escudo=self.escudo,
            countdown=self.no_light_timer,
            coins=self.coins,
            equipped_selected=self.selected_slot == "equipped"
        )

        if self.state == "playing" and self.has_match and self.burn_timer > 0:

            txt = f"Cera: {math.ceil(self.burn_timer)}s"

            font = self.hud.msg_font

            shadow = font.render(txt, True, (0, 0, 0))
            label = font.render(txt, True, (255, 225, 140))

            pos = label.get_rect(midtop=(self.width // 2, 18))

            self.screen.blit(shadow, pos.move(1, 1))
            self.screen.blit(label, pos)

        self.hud.draw_overlay(
            self.screen,
            self.item_defs,
            pygame.mouse.get_pos(),
            pygame.mouse.get_pressed()[0],
            self.message if self.message_timer > 0 else ""
        )

        if self.debug_items:

            self._draw_debug_items()

        if self.state in ("dying", "lost"):

            self.fade_overlay.set_alpha(int(self.fade_alpha))

            self.screen.blit(self.fade_overlay, (0, 0))

        if self.state == "lost":

            self.screen.blit(self.pantalla_perdiste, (0, 0))