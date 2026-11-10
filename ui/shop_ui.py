import math
from pathlib import Path

import pygame

from core.fonts import load_font
from core import skins as skin_lib
from core.controls import controls

from world.items import load_icon, HUD_DIR
from world.lights import LIGHTS

from ui.shop_plan import (
    KIND_ITEM, KIND_LIGHT, KIND_POTION,
    kind_range, light_index, plan_cap, plan_delivery,
    sanitize_draft, slot_kind, total_slots,
)


TIENDA_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "tienda"
)

IMAGES = {
    "panel": "tienda_panel.png",
    "cart": "tienda_carrito.png",
    "card": "tienda_tarjeta.png",
    "card_hover": "tienda_tarjeta_hover.png",
    "tile": "tienda_icono_fondo.png",
    "badge": "tienda_badge.png",
    "row": "tienda_fila.png",
    "plus": "tienda_mas.png.png",
    "minus": "tienda_menos.png",
    "buy": "tienda_boton_comprar.png",
    "buy_hover": "tienda_boton_comprar_hover.png",
    "buy_off": "tienda_boton_comprar.off.png",
    "trash": "tienda_boton_tacho.png",
    "arrow": "tienda_flecha.png",
    "coins": "tienda_monedas.png",
    "close": "tienda_cerrar.png",
    "info": "tienda_info_panel.png",
    # pestañas e inventario (opcionales: si falta la imagen se dibuja por codigo)
    "tab": "tienda_pestana.png",
    "tab_on": "tienda_pestana_activa.png",
    "inv_panel": "tienda_inventario.png",
    "inv_empty": "tienda_slot_vacio.png",
    # boton "x15" al lado del +  (opcional: si falta se dibuja por codigo)
    "bulk": "tienda_x15.png",
    # globito que aparece al pasar el mouse por un casillero de la hotbar
    # (opcional: si falta se dibuja por codigo)
    "tip": "tienda_tooltip.png",
}

# sprites del HUD que se reutilizan para dibujar la hotbar de la tienda
# (opcionales: si falta alguno se dibuja por codigo)
HUD_IMAGES = {
    "hud_bar": "hud_hotbar.png",
    "hud_slot": "hud_slot.png",
    "hud_slot_sel": "hud_slot_select.png",
    "hud_potion_panel": "hud_pociones.png",
    "hud_potion_slot": "hud_pocion_slot.png",
    "hud_potion_slot_sel": "hud_pocion_slot_select.png",
    "hud_light": "hud_item_equipado.png",
    "hud_light_sel": "hud_item_select.png",
}

OPTIONAL_IMAGES = (
    "info", "tab", "tab_on", "inv_panel", "inv_empty", "bulk", "tip",
    *HUD_IMAGES,
)

INFO_PAD_X = 28
INFO_PAD_TOP = 24
INFO_HEADER_H = 44
INFO_PAD_BOTTOM = 34
INFO_FONT_SIZES = (23, 21, 19, 17, 15)

_raw_cache = {}


def _load_raw(key):

    if key not in _raw_cache:

        path = (
            HUD_DIR / HUD_IMAGES[key] if key in HUD_IMAGES
            else TIENDA_DIR / IMAGES[key]
        )

        try:
            _raw_cache[key] = pygame.image.load(str(path)).convert_alpha()
        except (pygame.error, FileNotFoundError):
            if key not in OPTIONAL_IMAGES:
                print(f"[tienda] Falta la imagen {path.name}")
            _raw_cache[key] = None

    return _raw_cache[key]


C_PANEL = (24, 24, 27)
C_CARD = (30, 30, 34)
C_CARD_HOVER = (42, 42, 48)
C_BORDER = (63, 63, 70)
C_TEXT = (244, 244, 245)
C_MUTED = (161, 161, 170)
C_RED = (248, 113, 113)
C_BADGE = (251, 146, 60)

TILE_COLORS = {
    "fosforo": (66, 36, 10),
    "vela": (16, 40, 86),
    "antorcha": (86, 30, 12),
    "madera": (60, 36, 12),
    "cera": (44, 44, 48),
    "aceite": (16, 50, 18),
    "resina": (36, 30, 92),
    "polvora": (80, 20, 20),
    "ganzua": (14, 36, 80),
}

MAX_PER_ITEM = 99

# Casilleros del inventario (igual que el HUD): items, pociones y la luz
INV_SLOTS = 4
POTION_SLOTS = 2
DEFAULT_STACK = 15

# Hotbar de la pestaña Inventario
HOTBAR_H = 94
HOTBAR_SLOT = 58
HOTBAR_GAP = 4
HOTBAR_PAD = 8
HOTBAR_LIGHT = 64
HOTBAR_GROUP_GAP = 18
POP_TIME = 0.22

C_SELECT = (125, 211, 252)

# Globito de los casilleros: tamaño fijo de la imagen tienda_tooltip.png y
# margen interno donde se escribe el texto (el resto es marco)
TIP_W = 260
TIP_H = 116
TIP_PAD_X = 20
TIP_PAD_Y = 18

# Cuadro de compra de la pestaña Inventario (a la derecha de la hotbar)
INV_BOX_GAP = 12
INV_BTN_H = 34

C_SHADOW = (12, 14, 22)

# La bolsa y el candil no se guardan en un casillero: salen al piso
# y se arrastran. Las luces tienen su propio casillero extra (la mano).
NOT_IN_INVENTORY = {"bolsa", "faro"}


def is_skin(item_id):

    return item_id.startswith(skin_lib.SHOP_PREFIX)


def no_inventory(item_id):

    # las skins no son objetos: se desbloquean al comprarlas
    return item_id in NOT_IN_INVENTORY or is_skin(item_id)


def skin_of(item_id):

    return skin_lib.get(item_id[len(skin_lib.SHOP_PREFIX):])

# Cantidad que suma el boton "x15" de cada fila
BULK_AMOUNT = 15
BULK_SIZE = (32, 20)


class ShopUI:

    PANEL_W = 900
    PANEL_H = 520
    PAD = 24

    LIST_W = 570
    COLS = 3
    INV_COLS = 4
    CARD_W = 182
    CARD_H = 104
    GAP = 12

    ROW_H = 46
    FOOT_H = 118

    def __init__(
        self, screen_size, catalog, item_defs, coins, match_duration=30.0,
        cart=None, locks=None, best_wave=1,
        inventory=None, max_stack=None, inv_slots=INV_SLOTS,
        lock_zones=None, potion_slots=POTION_SLOTS,
        held=None, has_light=False
    ):

        # locks: {item_id: oleada necesaria} de lo que sigue bloqueado
        self.locks = dict(locks or {})

        # mejor oleada alcanzada en las salas de combate
        self.best_wave = int(best_wave)

        # {item_id: (nombre de zona, oleada actual en esa zona)} para los
        # objetos que piden la oleada en una zona puntual
        self.lock_zones = dict(lock_zones or {})

        self.sw, self.sh = screen_size
        self.catalog = catalog
        self.defs = item_defs
        self.coins = int(coins)
        self.match_duration = float(match_duration)

        self.info_id = None

        self.prices = {
            it["id"]: it["precio"]
            for sec in catalog
            for it in sec["items"]
        }

        self.cart = {
            item_id: min(MAX_PER_ITEM, int(qty))
            for item_id, qty in (cart or {}).items()
            if item_id in self.prices and int(qty) > 0
            and item_id not in self.locks
        }

        # inventario personalizado: un casillero por posicion,
        # cada uno None o [item_id, cantidad]
        self.inv_slots = int(inv_slots)
        self.potion_slots = int(potion_slots)

        # orden de los casilleros: items, pociones y al final la luz
        self.light_idx = light_index(self.inv_slots, self.potion_slots)
        self.total_slots = total_slots(self.inv_slots, self.potion_slots)
        self.max_stack = max_stack or (lambda item_id: DEFAULT_STACK)

        # lo que ya llevas encima: sirve para calcular que cae al piso
        hud_total = self.inv_slots + self.potion_slots
        held_items, held_counts = held if held else ([], [])

        self.held_items = (
            list(held_items) + [None] * hud_total
        )[:hud_total]
        self.held_counts = (
            list(held_counts) + [0] * hud_total
        )[:hud_total]
        self.has_light = bool(has_light)

        self.inventory = self._clean_inventory(inventory)

        # animacion de "pop" de los casilleros que cambian
        self._pop = {}

        self.tab = "shop"

        # casillero elegido en la hotbar: ahi van los productos que tocas
        # (None = automatico: el mismo item o el primer lugar libre)
        self.sel_slot = None

        self.message = ""
        self.message_timer = 0.0

        self.scroll = 0.0
        self.cart_scroll = 0.0

        self.title_font = load_font(46)
        self.section_font = load_font(26)
        self.name_font = load_font(28)
        self.small_font = load_font(23)
        self.tiny_font = load_font(21)
        self.button_font = load_font(30)
        self._font_cache = {}

        self.panel = pygame.Rect(0, 0, self.PANEL_W, self.PANEL_H)
        self.panel.center = (self.sw // 2, self.sh // 2)

        top = self.panel.y + 84

        # lista de productos: en la pestaña Inventario le cede el lugar
        # de arriba a la hotbar
        self.list_rect_shop = pygame.Rect(
            self.panel.x + self.PAD,
            top,
            self.LIST_W,
            self.panel.bottom - self.PAD - 24 - top
        )

        self.hotbar_rect = pygame.Rect(
            self.list_rect_shop.x, top, self.LIST_W, HOTBAR_H
        )

        inv_top = self.hotbar_rect.bottom + 8

        # en la pestaña Inventario la lista de productos ocupa todo el ancho
        self.list_rect_inv = pygame.Rect(
            self.list_rect_shop.x,
            inv_top,
            self.panel.w - self.PAD * 2,
            self.list_rect_shop.bottom - inv_top
        )

        self._build_hotbar()

        cart_x = self.list_rect_shop.right + 24

        self.cart_rect = pygame.Rect(
            cart_x,
            top,
            self.panel.right - self.PAD - cart_x,
            self.list_rect_shop.height
        )

        self.rows_rect = pygame.Rect(
            self.cart_rect.x + 8,
            self.cart_rect.y + 50,
            self.cart_rect.width - 16,
            self.cart_rect.height - 50 - self.FOOT_H
        )

        foot_top = self.cart_rect.bottom - self.FOOT_H

        self.total_pos_y = foot_top + 14

        self.trash_rect_shop = pygame.Rect(0, 0, 40, 40)
        self.trash_rect_shop.bottomright = (
            self.cart_rect.right - 16,
            self.cart_rect.bottom - 16
        )

        self.buy_rect_shop = pygame.Rect(
            self.cart_rect.x + 16,
            self.trash_rect_shop.y,
            self.trash_rect_shop.x - 8 - (self.cart_rect.x + 16),
            40
        )

        # cuadro de compra de la pestaña Inventario: total, comprar y tacho
        box_x = self.hotbar_rect.right + INV_BOX_GAP

        self.inv_box = pygame.Rect(
            box_x,
            self.hotbar_rect.y,
            self.panel.right - self.PAD - box_x,
            HOTBAR_H
        )

        self.inv_trash_rect = pygame.Rect(0, 0, INV_BTN_H, INV_BTN_H)
        self.inv_trash_rect.bottomright = (
            self.inv_box.right - 10,
            self.inv_box.y + 32 + INV_BTN_H
        )

        self.inv_buy_rect = pygame.Rect(
            self.inv_box.x + 10,
            self.inv_trash_rect.y,
            self.inv_trash_rect.x - 8 - (self.inv_box.x + 10),
            INV_BTN_H
        )

        self.inv_box_plate = pygame.Surface(
            self.inv_box.size, pygame.SRCALPHA
        )

        plate = self.inv_box_plate.get_rect()

        pygame.draw.rect(
            self.inv_box_plate, (16, 20, 31, 150), plate, border_radius=14
        )

        pygame.draw.rect(
            self.inv_box_plate, (10, 13, 21, 230), plate,
            width=2, border_radius=14
        )

        self.coin_pill = pygame.Rect(
            self.panel.right - self.PAD - 112,
            self.panel.y + self.PAD,
            112,
            40
        )

        self.close_rect = pygame.Rect(
            self.coin_pill.x - 12 - 36,
            self.coin_pill.y + 2,
            36,
            36
        )

        tab_w, tab_h = 120, 34
        tab_x = self.panel.x + self.PAD + 118

        self.tab_rects = {
            "shop": pygame.Rect(
                tab_x, self.coin_pill.y + 3, tab_w, tab_h
            ),
            "inv": pygame.Rect(
                tab_x + tab_w + 8, self.coin_pill.y + 3, tab_w, tab_h
            ),
        }

        self.dim = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 175))

        self._icons = {}
        self._imgs = {}

        self._layout()


    @property
    def list_rect(self):

        return (
            self.list_rect_inv if self.tab == "inv" else self.list_rect_shop
        )

    @property
    def buy_rect(self):

        return self.inv_buy_rect if self.tab == "inv" else self.buy_rect_shop

    @property
    def trash_rect(self):

        return (
            self.inv_trash_rect if self.tab == "inv"
            else self.trash_rect_shop
        )

    @property
    def cards(self):

        return self._layouts[self.tab][0]

    @property
    def labels(self):

        return self._layouts[self.tab][1]

    @property
    def content_h(self):

        return self._layouts[self.tab][2]

    @property
    def arrow_center(self):

        return (self.list_rect.centerx, self.list_rect.bottom - 22)

    @property
    def max_scroll(self):

        return max(0, self.content_h - self.list_rect.height)

    def _build_hotbar(self):

        s, gap, pad = HOTBAR_SLOT, HOTBAR_GAP, HOTBAR_PAD

        hot_w = self.inv_slots * s + (self.inv_slots - 1) * gap + pad * 2

        pot_w = (
            self.potion_slots * s + (self.potion_slots - 1) * gap + pad * 2
        )

        total_w = HOTBAR_LIGHT + HOTBAR_GROUP_GAP * 2 + hot_w + pot_w

        x = self.hotbar_rect.centerx - total_w // 2
        y = self.hotbar_rect.y + 8

        # mismo orden que el HUD del juego: luz, hotbar, pociones
        self.light_frame = pygame.Rect(
            x, y - (HOTBAR_LIGHT - s) // 2, HOTBAR_LIGHT, HOTBAR_LIGHT
        )

        x = self.light_frame.right + HOTBAR_GROUP_GAP

        self.hot_panel = pygame.Rect(x, y - 5, hot_w, s + 10)

        x = self.hot_panel.right + HOTBAR_GROUP_GAP

        self.pot_panel = pygame.Rect(x, y - 5, pot_w, s + 10)

        self.slot_rects = []

        for i in range(self.inv_slots):
            self.slot_rects.append(
                pygame.Rect(self.hot_panel.x + pad + i * (s + gap), y, s, s)
            )

        for i in range(self.potion_slots):
            self.slot_rects.append(
                pygame.Rect(self.pot_panel.x + pad + i * (s + gap), y, s, s)
            )

        self.slot_rects.append(self.light_frame.copy())

        self.hotbar_plate = pygame.Surface(
            self.hotbar_rect.size, pygame.SRCALPHA
        )

        plate = self.hotbar_plate.get_rect()

        pygame.draw.rect(
            self.hotbar_plate, (16, 20, 31, 150), plate, border_radius=14
        )

        pygame.draw.rect(
            self.hotbar_plate, (10, 13, 21, 230), plate,
            width=2, border_radius=14
        )

    def item_name(self, item_id):

        if is_skin(item_id):

            skin = skin_of(item_id)

            return skin["nombre"] if skin else item_id

        data = self.defs.get(item_id, {})

        return data.get("nombre", item_id.capitalize())

    def _lock_tile_text(self, item_id, wave):

        zone = self.lock_zones.get(item_id)

        if zone and len(zone) > 2:

            if zone[2] == "Centro":
                return "Bloqueado: Centro"

            return f"Bloqueado: oleada {wave} · {zone[2]}"

        return f"Bloqueado: oleada {wave}"

    def lock_reason(self, item_id, short=False):

        need = self.locks.get(item_id)

        if need is None:
            return ""

        zone = self.lock_zones.get(item_id)

        if zone and len(zone) > 2 and zone[2] == "Centro":

            if short:
                return "Bloqueado: llega al Centro"

            return "BLOQUEADO: se desbloquea al llegar al Centro del mapa."

        current = zone[1] if zone else self.best_wave

        missing = max(0, need + 1 - current)

        if short:
            where = f" en {zone[0]}" if zone else ""
            return (
                f"Bloqueado: termina la oleada {need}{where} "
                f"(vas por la {current})"
            )

        where = (
            f"en la {zone[0]}" if zone
            else "en cualquiera de las salas de combate"
        )

        if current == need:
            tail = f"Ya estás en la oleada {need}: termínala y es tuyo."
        else:
            tail = (
                f"Vas por la oleada {current}: te "
                f"{'falta' if missing == 1 else 'faltan'} {missing} "
                f"{'oleada' if missing == 1 else 'oleadas'} por pasar."
            )

        return (
            f"BLOQUEADO: se desbloquea al terminar la oleada {need} "
            f"{where}. {tail}"
        )

    def info_lines(self, item_id):

        if is_skin(item_id):

            owned = self._skin_owned(item_id)

            return [
                "Skin para tu personaje.",
                "",
                "Ya la tienes: equípala desde Skins en el menú principal."
                if owned
                else "Al comprarla queda desbloqueada para todas tus "
                     "partidas. Equípala desde Skins en el menú principal.",
            ]

        data = self.defs.get(item_id, {})

        lines = []

        if item_id in self.locks:
            lines.append(self.lock_reason(item_id))
            lines.append("")

        if data.get("descripcion"):
            lines.append(data["descripcion"])

        stats = LIGHTS.get(item_id)

        if stats is None:
            return lines

        base = LIGHTS["fosforo"]["radio"]

        radio = f"Radio de luz: {stats['radio']}"

        if stats["radio"] != base:
            radio += f" (x{stats['radio'] / base:g} que el fósforo)"

        duracion = self.match_duration / stats["consumo"]

        lines.append("")
        lines.append(radio)
        lines.append(f"Duración: {duracion:g} segundos")

        if stats.get("dano", 1) > 1:
            lines.append(f"Fuerza: {stats['dano']:g} de daño por golpe")

        if stats.get("furia_cada", 0) > 0:
            lines.append(
                f"Furia: cada {stats['furia_cada']:g} s entra en furia "
                f"durante {stats['furia_duracion']:g} s y pega "
                f"{stats['furia_velocidad']:g} veces más rápido"
            )
        else:
            lines.append("Furia: no tiene")

        return lines

    def total(self):

        return sum(self.prices[i] * q for i, q in self.cart.items())

    # ---------- inventario personalizado ----------

    def kind_of(self, item_id):

        if item_id in LIGHTS:
            return KIND_LIGHT

        if self.defs.get(item_id, {}).get("tipo") == "pocion":
            return KIND_POTION

        return KIND_ITEM

    def _clean_inventory(self, raw):

        return sanitize_draft(
            raw, self.inv_slots, self.potion_slots, self.kind_of,
            lambda item_id: (
                isinstance(item_id, str)
                and item_id in self.prices
                and not no_inventory(item_id)
                and item_id not in self.locks
            )
        )

    def inv_total(self):

        return sum(
            self.prices[slot[0]] * slot[1]
            for slot in self.inventory
            if slot is not None
        )

    def inv_count(self, item_id):

        return sum(
            slot[1] for slot in self.inventory
            if slot is not None and slot[0] == item_id
        )

    def delivery(self):
        """Que entra al inventario y que cae al piso con el plan actual."""

        return plan_delivery(
            self.inventory, self.held_items, self.held_counts,
            self.inv_slots, self.potion_slots,
            self.max_stack, self.kind_of
        )

    def inv_floor_total(self):

        floor = len(self.delivery()["drops"])

        # una luz comprada teniendo otra en la mano tambien sale al piso
        if self.has_light and self.inventory[self.light_idx] is not None:
            floor += 1

        return floor

    def _target_slot(self, item_id):
        """Casillero del plan donde cae item_id, o None si no hay lugar."""

        kind = self.kind_of(item_id)

        # la luz tiene un unico lugar: una nueva reemplaza a la anterior
        if kind == KIND_LIGHT:
            return self.light_idx

        # si elegiste un casillero de ese tipo, va ahi
        if (
            self.sel_slot is not None
            and slot_kind(self.sel_slot, self.inv_slots, self.potion_slots)
            == kind
        ):
            return self.sel_slot

        lo, hi = kind_range(kind, self.inv_slots, self.potion_slots)

        for n in range(lo, hi):

            slot = self.inventory[n]

            if slot is not None and slot[0] == item_id:
                return n

        for n in range(lo, hi):

            if self.inventory[n] is None:
                return n

        return None

    def _slot_full(self, n, item_id):
        """True si sumar item_id en el casillero n ya no se puede."""

        slot = self.inventory[n]

        if slot is None:
            return False

        # el casillero tiene otra cosa
        if slot[0] != item_id:
            return True

        return slot[1] >= plan_cap(self.kind_of(item_id))

    def _pop_slot(self, n):

        self._pop[n] = POP_TIME

    def inv_add(self, item_id, slot_index=None, amount=1):

        if item_id in self.locks:

            self._flash(self.lock_reason(item_id, short=True))

            return

        if no_inventory(item_id):

            self._flash("Eso no va en el inventario")

            return

        kind = self.kind_of(item_id)

        if slot_index is None:
            slot_index = self._target_slot(item_id)

        if slot_index is None:

            self._flash(
                "No quedan lugares de pociones: saca una con click derecho"
                if kind == KIND_POTION
                else "La hotbar está llena: saca algo con click derecho"
            )

            return

        if kind == KIND_LIGHT:

            current = self.inventory[self.light_idx]

            if current is not None and current[0] == item_id:
                self._flash("Ya tienes esa luz")
            else:
                self.inventory[self.light_idx] = [item_id, 1]
                self._pop_slot(self.light_idx)

            return

        cap = plan_cap(kind)

        slot = self.inventory[slot_index]

        if slot is not None and slot[0] != item_id:

            self._flash("Ese casillero ya tiene otra cosa: vacíalo primero")

            return

        current = 0 if slot is None else slot[1]

        if current >= cap:

            self._flash(
                f"Máximo {cap} "
                f"{'pociones' if kind == KIND_POTION else 'unidades'} "
                f"por compra"
            )

            return

        self.inventory[slot_index] = [
            item_id, min(cap, current + max(1, int(amount)))
        ]

        self._pop_slot(slot_index)

    def inv_remove(self, item_id=None, slot_index=None, amount=1):

        if slot_index is None:

            for n in range(len(self.inventory) - 1, -1, -1):

                slot = self.inventory[n]

                if slot is not None and slot[0] == item_id:
                    slot_index = n
                    break

        if slot_index is None:
            return

        slot = self.inventory[slot_index]

        if slot is None:
            return

        slot[1] -= max(1, int(amount))

        if slot[1] <= 0:
            self.inventory[slot_index] = None
        else:
            self._pop_slot(slot_index)

        self.cart_scroll = min(self.cart_scroll, self._cart_max_scroll())

    def inv_clear(self):

        self.inventory = [None] * self.total_slots
        self.cart_scroll = 0.0

    def inv_has_items(self):

        return any(slot is not None for slot in self.inventory)

    def active_total(self):

        return self.inv_total() if self.tab == "inv" else self.total()

    def _slot_at(self, pos):

        for n, rect in enumerate(self.slot_rects):

            if rect.collidepoint(pos):
                return n

        return None

    @staticmethod
    def _clear_rect(rect):

        return pygame.Rect(rect.right - 18, rect.y + 2, 16, 16)

    def _slot_label(self, n):

        if n == self.light_idx:
            action = "equipped"
        elif n >= self.inv_slots:
            action = f"potion{n - self.inv_slots + 1}"
        else:
            action = f"slot{n + 1}"

        try:
            return str(controls.label(action))
        except Exception:
            return ""

    def _hotbar_click(self, button, pos):

        n = self._slot_at(pos)

        if n is None:
            return

        slot = self.inventory[n]

        if button == 1:

            if slot is not None and self._clear_rect(
                self.slot_rects[n]
            ).collidepoint(pos):

                self.inventory[n] = None

                return

            # click izquierdo: elegir casillero (otra vez: volver a auto)
            self.sel_slot = None if self.sel_slot == n else n

            return

        if slot is None:
            return

        step = 5 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1

        self.inv_remove(slot_index=n, amount=step)

    def set_tab(self, tab):

        if tab in self.tab_rects and tab != self.tab:

            self.tab = tab

            self.scroll = min(self.scroll, self.max_scroll)
            self.cart_scroll = min(self.cart_scroll, self._cart_max_scroll())

    @staticmethod
    def _skin_owned(item_id):

        return skin_lib.is_unlocked(item_id[len(skin_lib.SHOP_PREFIX):])

    def _skin_icon(self, item_id, size):

        try:

            sprite = skin_lib.preview_sprite(
                item_id[len(skin_lib.SHOP_PREFIX):]
            )

        except Exception:

            return None

        k = min(size / sprite.get_width(), size / sprite.get_height())

        return pygame.transform.smoothscale(
            sprite,
            (
                max(1, round(sprite.get_width() * k)),
                max(1, round(sprite.get_height() * k)),
            )
        )

    def _icon(self, item_id, size):

        key = (item_id, size)

        if key not in self._icons and is_skin(item_id):

            self._icons[key] = self._skin_icon(item_id, size)

        if key not in self._icons:

            if item_id == "fosforo":

                path = HUD_DIR / "item_fosforo.png"

                icon = (
                    pygame.image.load(str(path)).convert_alpha()
                    if path.exists()
                    else load_icon(item_id)
                )

            else:

                icon = load_icon(item_id)

            if icon is not None:
                icon = pygame.transform.smoothscale(icon, (size, size))

            self._icons[key] = icon

        return self._icons[key]

    def _img(self, key, size=None, shade=0):

        cache_key = (key, size, shade)

        if cache_key not in self._imgs:

            img = _load_raw(key)

            if img is not None:

                if size is not None and img.get_size() != tuple(size):
                    img = pygame.transform.smoothscale(img, size)

                if shade > 0:

                    img = img.copy()
                    img.fill(
                        (shade, shade, shade, 0),
                        special_flags=pygame.BLEND_RGB_ADD
                    )

                elif shade < 0:

                    img = img.copy()
                    img.fill(
                        (-shade, -shade, -shade, 0),
                        special_flags=pygame.BLEND_RGB_SUB
                    )

            self._imgs[cache_key] = img

        return self._imgs[cache_key]

    def _fit_img(self, key, size):
        """Sprite del HUD recortado a su parte visible y escalado a size."""

        cache_key = ("fit", key, tuple(size))

        if cache_key not in self._imgs:

            img = _load_raw(key)

            if img is not None:

                box = img.get_bounding_rect(min_alpha=21)

                if box.w > 0 and box.h > 0:
                    img = img.subsurface(box)

                img = pygame.transform.smoothscale(img, tuple(size))

            self._imgs[cache_key] = img

        return self._imgs[cache_key]

    def _flash(self, text):

        self.message = text
        self.message_timer = 2.0


    def _layout(self):

        self._layouts = {
            "shop": self._build_cards(self.COLS, self.CARD_W),
            "inv": self._build_cards(
                self.INV_COLS,
                (self.list_rect_inv.w - (self.INV_COLS - 1) * self.GAP)
                // self.INV_COLS
            ),
        }

    def _build_cards(self, cols, card_w):

        labels = []
        cards = []

        y = 0

        for sec in self.catalog:

            labels.append((y, sec["nombre"]))

            y += 30

            for i, it in enumerate(sec["items"]):

                col = i % cols
                row = i // cols

                rect = pygame.Rect(
                    col * (card_w + self.GAP),
                    y + row * (self.CARD_H + self.GAP),
                    card_w,
                    self.CARD_H
                )

                cards.append((rect, it["id"]))

            rows = math.ceil(len(sec["items"]) / cols)

            y += rows * (self.CARD_H + self.GAP) + 6

        return cards, labels, y

    def _cart_rows(self):

        rows = []

        for n, (item_id, qty) in enumerate(self.cart.items()):

            y = self.rows_rect.y + n * self.ROW_H - int(self.cart_scroll)

            row = pygame.Rect(
                self.rows_rect.x, y, self.rows_rect.width, self.ROW_H - 4
            )

            bulk = pygame.Rect(
                row.right - 6 - BULK_SIZE[0], row.y + 12, *BULK_SIZE
            )
            plus = pygame.Rect(bulk.x - 24, row.y + 12, 20, 20)
            minus = pygame.Rect(plus.x - 24, row.y + 12, 20, 20)

            rows.append((item_id, qty, row, minus, plus, bulk))

        return rows

    def _cart_max_scroll(self):

        # la pestaña Inventario no tiene lista de filas
        if self.tab == "inv":
            return 0

        return max(
            0, len(self.cart) * self.ROW_H - self.rows_rect.height
        )


    def add(self, item_id, amount=1):

        if item_id in self.locks:

            self._flash(self.lock_reason(item_id, short=True))

            return

        if is_skin(item_id):

            if self._skin_owned(item_id):

                self._flash("Ya tienes esta skin")

            else:

                self.cart[item_id] = 1

            return

        current = self.cart.get(item_id, 0)

        self.cart[item_id] = min(MAX_PER_ITEM, current + amount)

    def remove(self, item_id, amount=1):

        if item_id not in self.cart:
            return

        self.cart[item_id] -= amount

        if self.cart[item_id] <= 0:
            del self.cart[item_id]

        self.cart_scroll = min(self.cart_scroll, self._cart_max_scroll())

    def clear(self):

        self.cart.clear()
        self.cart_scroll = 0.0


    def _card_at(self, pos):

        if not self.list_rect.collidepoint(pos):
            return None

        x = pos[0] - self.list_rect.x
        y = pos[1] - self.list_rect.y + int(self.scroll)

        for rect, item_id in self.cards:

            if rect.collidepoint(x, y):
                return item_id

        return None

    def _card_bulk_rect(self, card_rect):

        return pygame.Rect(
            card_rect.right - 6 - BULK_SIZE[0],
            card_rect.bottom - 6 - BULK_SIZE[1],
            *BULK_SIZE
        )

    def _card_has_bulk(self, item_id):

        if item_id in self.locks or is_skin(item_id):
            return False

        if self.tab == "inv":
            # las pociones llegan a 5 y la luz a 1: no tienen x15
            return (
                not no_inventory(item_id)
                and self.kind_of(item_id) == KIND_ITEM
            )

        return True

    def _bulk_at(self, pos):

        if not self.list_rect.collidepoint(pos):
            return None

        x = pos[0] - self.list_rect.x
        y = pos[1] - self.list_rect.y + int(self.scroll)

        for rect, item_id in self.cards:

            if (
                self._card_has_bulk(item_id)
                and self._card_bulk_rect(rect).collidepoint(x, y)
            ):
                return item_id

        return None

    def _bulk_add(self, item_id):

        if self.tab != "inv":

            self.add(item_id, BULK_AMOUNT)

            return

        self.inv_add(item_id, amount=BULK_AMOUNT)

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if self.info_id is not None:

                self.info_id = None

                return None

            if (
                event.key == pygame.K_ESCAPE
                or controls.matches("use", event.key)
            ):
                return "close"

            if event.key == pygame.K_TAB:
                self.set_tab("inv" if self.tab == "shop" else "shop")

            return None

        if event.type == pygame.MOUSEWHEEL:

            pos = pygame.mouse.get_pos()

            if self.tab == "inv" and self.hotbar_rect.collidepoint(pos):

                # rueda sobre un casillero: suma o resta de a una
                n = self._slot_at(pos)

                if n is not None and self.inventory[n] is not None:

                    if event.y > 0 and n != self.light_idx:
                        self.inv_add(self.inventory[n][0], slot_index=n)
                    elif event.y < 0:
                        self.inv_remove(slot_index=n)

                return None

            if self.tab == "shop" and self.cart_rect.collidepoint(pos):

                self.cart_scroll = max(
                    0,
                    min(
                        self._cart_max_scroll(),
                        self.cart_scroll - event.y * 40
                    )
                )

            else:

                self.scroll = max(
                    0,
                    min(self.max_scroll, self.scroll - event.y * 50)
                )

            return None

        if event.type != pygame.MOUSEBUTTONDOWN:
            return None

        if event.button not in (1, 2, 3):
            return None

        pos = event.pos

        if event.button == 2:

            card = self._card_at(pos)

            if card is None and self.tab == "inv":

                n = self._slot_at(pos)

                if n is not None and self.inventory[n] is not None:
                    card = self.inventory[n][0]

            self.info_id = None if card == self.info_id else card

            return None

        if self.info_id is not None:

            self.info_id = None

            return None

        if event.button == 1:

            bulk_card = self._bulk_at(pos)

            if bulk_card is not None:

                self._bulk_add(bulk_card)

                return None

        if self.tab == "inv" and self.hotbar_rect.collidepoint(pos):

            self._hotbar_click(event.button, pos)

            return None

        card = self._card_at(pos)

        if card is not None:

            if self.tab == "inv":

                if event.button == 1:
                    self.inv_add(card)
                else:
                    self.inv_remove(card)

            elif event.button == 1:
                self.add(card)
            else:
                self.remove(card)

            return None

        if event.button != 1:
            return None

        for tab, rect in self.tab_rects.items():

            if rect.collidepoint(pos):

                self.set_tab(tab)

                return None

        if self.close_rect.collidepoint(pos):
            return "close"

        if (
            self.scroll < self.max_scroll - 1
            and math.dist(pos, self.arrow_center) <= 17
        ):

            self.scroll = self.max_scroll

            return None

        if self.tab == "inv":

            if self.trash_rect.collidepoint(pos):

                self.inv_clear()

                return None

            if self.buy_rect.collidepoint(pos):

                total = self.inv_total()

                if total <= 0:
                    return None

                if total > self.coins:

                    self._flash("No te alcanzan las monedas")

                    return None

                return (
                    "buy_inventory",
                    [list(slot) if slot else None for slot in self.inventory]
                )

            return None

        if self.rows_rect.collidepoint(pos):

            for item_id, _, _, minus, plus, bulk in self._cart_rows():

                if bulk.collidepoint(pos) and not is_skin(item_id):
                    self.add(item_id, BULK_AMOUNT)
                    return None

                if minus.collidepoint(pos):
                    self.remove(item_id)
                    return None

                if plus.collidepoint(pos):
                    self.add(item_id)
                    return None

            return None

        if self.trash_rect.collidepoint(pos):

            self.clear()

            return None

        if self.buy_rect.collidepoint(pos):

            total = self.total()

            if total <= 0:
                return None

            if total > self.coins:

                self._flash("No te alcanzan las monedas")

                return None

            return ("buy", dict(self.cart))

        return None

    def update(self, dt):

        if self.message_timer > 0:
            self.message_timer -= dt

        for n in list(self._pop):

            self._pop[n] -= dt

            if self._pop[n] <= 0:
                del self._pop[n]


    def _text(self, screen, font, text, color, **anchor):

        img = font.render(text, True, color)

        screen.blit(img, img.get_rect(**anchor))

        return img

    def _font_for(self, size):

        font = self._font_cache.get(size)

        if font is None:
            font = load_font(size)
            self._font_cache[size] = font

        return font

    def _fit_font(self, text, max_w, size, min_size=14):

        while size > min_size:

            font = self._font_for(size)

            if font.size(text)[0] <= max_w:
                return font

            size -= 1

        return self._font_for(min_size)

    @staticmethod
    def _wrap(font, text, max_width):

        lines = []
        line = ""

        for word in text.split():

            while font.size(word)[0] > max_width and len(word) > 1:

                n = len(word) - 1

                while n > 1 and font.size(word[:n] + "-")[0] > max_width:
                    n -= 1

                if line:
                    lines.append(line)
                    line = ""

                lines.append(word[:n] + "-")
                word = word[n:]

            test = f"{line} {word}".strip()

            if line and font.size(test)[0] > max_width:
                lines.append(line)
                line = word
            else:
                line = test

        if line:
            lines.append(line)

        return lines

    def _draw_coin_amount(
        self, screen, amount, color, midright, max_w=90
    ):

        text = self.name_font.render(str(amount), True, color)

        if text.get_width() > max_w:

            text = pygame.transform.smoothscale(
                text,
                (
                    max_w,
                    max(1, int(text.get_height() * max_w / text.get_width()))
                )
            )

        text_rect = text.get_rect(midright=midright)

        screen.blit(text, text_rect)

        coin = self._icon("moneda", 20)

        if coin is not None:

            screen.blit(
                coin,
                coin.get_rect(midright=(text_rect.left - 6, midright[1]))
            )

    def _draw_card(self, screen, rect, item_id, hover):

        card_img = self._img(
            "card_hover" if hover else "card", rect.size
        )

        if card_img is not None:

            screen.blit(card_img, rect.topleft)

        else:

            pygame.draw.rect(
                screen, C_CARD_HOVER if hover else C_CARD, rect,
                border_radius=10
            )

            pygame.draw.rect(
                screen, C_BORDER, rect, width=1, border_radius=10
            )

        tile = pygame.Rect(0, 0, 46, 46)
        tile.midtop = (rect.centerx, rect.y + 10)

        tile_img = self._img("tile", tile.size)

        if tile_img is not None:

            screen.blit(tile_img, tile.topleft)

        else:

            pygame.draw.rect(
                screen, TILE_COLORS.get(item_id, (44, 44, 50)), tile,
                border_radius=8
            )

        icon = self._icon(item_id, 34)

        if icon is not None:
            screen.blit(icon, icon.get_rect(center=tile.center))

        locked_wave = self.locks.get(item_id)

        no_inv = self.tab == "inv" and no_inventory(item_id)

        if locked_wave is not None or no_inv:

            shade = pygame.Surface(rect.size, pygame.SRCALPHA)
            shade.fill((0, 0, 0, 150))

            screen.blit(shade, rect.topleft)

        card_name = self.item_name(item_id)

        self._text(
            screen,
            self._fit_font(card_name, rect.w - 16, 28),
            card_name, C_TEXT,
            midtop=(rect.centerx, tile.bottom + 6)
        )

        self._text(
            screen, self.tiny_font,
            (
                self._lock_tile_text(item_id, locked_wave)
                if locked_wave is not None
                else "No va al inventario"
                if no_inv
                else "Ya la tienes"
                if is_skin(item_id) and self._skin_owned(item_id)
                else f"{self.prices[item_id]} monedas"
            ),
            C_MUTED,
            midtop=(rect.centerx, tile.bottom + 28)
        )

        qty = (
            self.inv_count(item_id)
            if self.tab == "inv"
            else self.cart.get(item_id, 0)
        )

        if qty > 0:

            badge_img = self._img("badge")

            if badge_img is not None:

                badge = badge_img.get_rect(
                    topright=(rect.right - 6, rect.y + 6)
                )

                screen.blit(badge_img, badge.topleft)

            else:

                badge = pygame.Rect(0, 0, 26, 22)
                badge.topright = (rect.right - 6, rect.y + 6)

                pygame.draw.rect(screen, C_BADGE, badge, border_radius=11)

            self._text(
                screen, self.tiny_font, str(qty), (30, 18, 8),
                center=badge.center
            )

        if self._card_has_bulk(item_id):

            self._draw_bulk_button(
                screen, self._card_bulk_rect(rect), pygame.mouse.get_pos()
            )

    def _draw_list(self, screen, mouse):

        screen.set_clip(self.list_rect)

        oy = self.list_rect.y - int(self.scroll)

        for y, name in self.labels:

            self._text(
                screen, self.section_font, name, C_MUTED,
                topleft=(self.list_rect.x + 2, oy + y + 4)
            )

        hover_id = self._card_at(mouse)

        for rect, item_id in self.cards:

            self._draw_card(
                screen,
                rect.move(self.list_rect.x, oy),
                item_id,
                item_id == hover_id
            )

        screen.set_clip(None)

        if self.scroll < self.max_scroll - 1:

            arrow_img = self._img("arrow", (34, 34))

            if arrow_img is not None:

                screen.blit(
                    arrow_img,
                    arrow_img.get_rect(center=self.arrow_center)
                )

            else:

                pygame.draw.circle(
                    screen, C_CARD_HOVER, self.arrow_center, 17
                )

                pygame.draw.circle(
                    screen, C_BORDER, self.arrow_center, 17, 1
                )

                ax, ay = self.arrow_center

                pygame.draw.lines(
                    screen, C_TEXT, False,
                    [(ax - 6, ay - 3), (ax, ay + 4), (ax + 6, ay - 3)], 2
                )

                pygame.draw.line(
                    screen, C_TEXT, (ax, ay - 6), (ax, ay + 3), 2
                )

    def _draw_cart_icon(self, screen, x, y):

        pygame.draw.lines(
            screen, C_TEXT, False,
            [(x, y + 2), (x + 4, y + 2), (x + 7, y + 13), (x + 19, y + 13),
             (x + 21, y + 5), (x + 6, y + 5)], 2
        )

        pygame.draw.circle(screen, C_TEXT, (x + 9, y + 18), 2)
        pygame.draw.circle(screen, C_TEXT, (x + 17, y + 18), 2)

    def _draw_bulk_button(self, screen, rect, mouse):

        hover = rect.collidepoint(mouse)

        img = self._img("bulk", rect.size, shade=40 if hover else 0)

        if img is not None:

            screen.blit(img, rect.topleft)

            return

        pygame.draw.rect(
            screen,
            C_CARD_HOVER if hover else C_PANEL,
            rect,
            border_radius=5
        )

        pygame.draw.rect(
            screen, C_BADGE, rect, width=1, border_radius=5
        )

        self._text(
            screen, self.tiny_font, f"x{BULK_AMOUNT}", C_BADGE,
            center=rect.center
        )

    def _draw_trash_icon(self, screen, rect, color):

        cx, cy = rect.center

        pygame.draw.line(
            screen, color, (cx - 8, cy - 7), (cx + 8, cy - 7), 2
        )

        pygame.draw.line(
            screen, color, (cx - 3, cy - 10), (cx + 3, cy - 10), 2
        )

        pygame.draw.lines(
            screen, color, False,
            [(cx - 6, cy - 5), (cx - 5, cy + 9), (cx + 5, cy + 9),
             (cx + 6, cy - 5)], 2
        )

        pygame.draw.line(
            screen, color, (cx - 2, cy - 2), (cx - 2, cy + 6), 1
        )

        pygame.draw.line(
            screen, color, (cx + 2, cy - 2), (cx + 2, cy + 6), 1
        )

    def _draw_cart(self, screen, mouse):

        cart_img = self._img("cart", self.cart_rect.size)

        if cart_img is not None:

            screen.blit(cart_img, self.cart_rect.topleft)

        else:

            pygame.draw.rect(
                screen, C_CARD, self.cart_rect, border_radius=12
            )

            pygame.draw.rect(
                screen, C_BORDER, self.cart_rect, width=1, border_radius=12
            )

        self._draw_cart_icon(
            screen, self.cart_rect.x + 16, self.cart_rect.y + 14
        )

        self._text(
            screen, self.name_font,
            "Carrito", C_TEXT,
            midleft=(self.cart_rect.x + 46, self.cart_rect.y + 25)
        )

        if not self.cart:

            lines = self._wrap(
                self.small_font,
                "Toca un producto para agregarlo.",
                self.rows_rect.width - 20
            )

            for n, line in enumerate(lines):

                self._text(
                    screen, self.small_font, line, C_MUTED,
                    midtop=(
                        self.rows_rect.centerx,
                        self.rows_rect.y + 24 + n * 22
                    )
                )

        else:

            screen.set_clip(self.rows_rect)

            for item_id, qty, row, minus, plus, bulk in self._cart_rows():

                row_img = self._img("row", row.size)

                if row_img is not None:
                    screen.blit(row_img, row.topleft)

                icon = self._icon(item_id, 28)

                if icon is not None:
                    screen.blit(
                        icon, icon.get_rect(midleft=(row.x + 4, row.centery))
                    )

                row_name = self.item_name(item_id)

                self._text(
                    screen,
                    self._fit_font(row_name, minus.x - row.x - 44, 23),
                    row_name, C_TEXT,
                    topleft=(row.x + 40, row.y + 4)
                )

                price = self.prices[item_id]

                self._text(
                    screen, self.tiny_font,
                    f"{qty} × {price} = {qty * price}", C_MUTED,
                    topleft=(row.x + 40, row.y + 22)
                )

                if not is_skin(item_id):
                    self._draw_bulk_button(screen, bulk, mouse)

                for rect, symbol, key in (
                    (minus, "-", "minus"), (plus, "+", "plus")
                ):

                    hover = rect.collidepoint(mouse)

                    btn_img = self._img(
                        key, rect.size, shade=40 if hover else 0
                    )

                    if btn_img is not None:

                        screen.blit(btn_img, rect.topleft)

                        continue

                    pygame.draw.rect(
                        screen,
                        C_CARD_HOVER if hover else C_PANEL,
                        rect,
                        border_radius=5
                    )

                    pygame.draw.rect(
                        screen, C_BORDER, rect, width=1, border_radius=5
                    )

                    self._text(
                        screen, self.small_font, symbol, C_TEXT,
                        center=rect.center
                    )

            screen.set_clip(None)

        foot_top = self.cart_rect.bottom - self.FOOT_H

        pygame.draw.line(
            screen, C_BORDER,
            (self.cart_rect.x + 12, foot_top),
            (self.cart_rect.right - 12, foot_top)
        )

        self._draw_footer(
            screen, mouse, self.cart_rect, self.total_pos_y + 10,
            self.total_pos_y + 32
        )

    def _draw_footer(self, screen, mouse, area, total_y, note_y):
        """Total, aviso, boton de comprar y tacho (carrito e inventario)."""

        total = self.active_total()

        self._text(
            screen, self.small_font, "Total", C_MUTED,
            midleft=(area.x + 16, total_y)
        )

        self._draw_coin_amount(
            screen,
            total,
            C_RED if total > self.coins else C_TEXT,
            (area.right - 16, total_y)
        )

        if self.message_timer > 0:

            self._text(
                screen,
                self._fit_font(
                    self.message, area.w - 16, 20, min_size=12
                ),
                self.message, C_RED,
                midtop=(area.centerx, note_y)
            )

        if self.tab == "inv" and self.message_timer <= 0:

            floor = self.inv_floor_total()

            if floor > 0:

                note = f"{floor} {'cae' if floor == 1 else 'caen'} al piso"

                self._text(
                    screen,
                    self._fit_font(
                        note, area.w - 16, 22, min_size=12
                    ),
                    note, C_BADGE,
                    midtop=(area.centerx, note_y)
                )

        enabled = total > 0

        has_items = self.inv_has_items() if self.tab == "inv" else bool(
            self.cart
        )

        hover = enabled and self.buy_rect.collidepoint(mouse)

        if not enabled:
            buy_key = "buy_off"
        elif hover:
            buy_key = "buy_hover"
        else:
            buy_key = "buy"

        buy_img = self._img(buy_key, self.buy_rect.size)

        if buy_img is not None:

            screen.blit(buy_img, self.buy_rect.topleft)

        else:

            pygame.draw.rect(
                screen,
                C_CARD_HOVER if hover else C_PANEL,
                self.buy_rect,
                border_radius=10
            )

            pygame.draw.rect(
                screen,
                C_TEXT if enabled else C_BORDER,
                self.buy_rect,
                width=1,
                border_radius=10
            )

        buy_text = "Comprar inventario" if self.tab == "inv" else "Comprar"

        self._text(
            screen,
            self._fit_font(buy_text, self.buy_rect.w - 12, 30, min_size=16),
            buy_text,
            C_TEXT if enabled else C_MUTED,
            center=self.buy_rect.center
        )

        hover = self.trash_rect.collidepoint(mouse)

        if not has_items:
            shade = -70
        elif hover:
            shade = 40
        else:
            shade = 0

        trash_img = self._img("trash", self.trash_rect.size, shade=shade)

        if trash_img is not None:

            screen.blit(trash_img, self.trash_rect.topleft)

        else:

            pygame.draw.rect(
                screen,
                C_CARD_HOVER if hover else C_PANEL,
                self.trash_rect,
                border_radius=10
            )

            pygame.draw.rect(
                screen, C_BORDER, self.trash_rect, width=1, border_radius=10
            )

            self._draw_trash_icon(
                screen,
                self.trash_rect,
                C_TEXT if has_items else C_MUTED
            )

    # ---------- hotbar de la pestaña Inventario ----------

    def _outlined_text(self, screen, font, text, color, **anchor):

        base = font.render(text, True, color)
        rect = base.get_rect(**anchor)

        shadow = font.render(text, True, C_SHADOW)

        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            screen.blit(shadow, rect.move(dx, dy))

        screen.blit(base, rect)

    def _card_target(self, item_id):
        """(tipo, casillero) donde caeria el producto sobre el que estas."""

        if (
            item_id is None
            or item_id in self.locks
            or no_inventory(item_id)
        ):
            return None, None

        return self.kind_of(item_id), self._target_slot(item_id)

    def _draw_hotbar_group(self, screen, rect, key, fallback, border):

        img = self._fit_img(key, rect.size)

        if img is not None:

            screen.blit(img, rect.topleft)

            return

        pygame.draw.rect(screen, fallback, rect, border_radius=12)
        pygame.draw.rect(screen, border, rect, width=2, border_radius=12)

    def _draw_slot(self, screen, n, hover, per_slot, mouse):

        rect = self.slot_rects[n]
        slot = self.inventory[n]

        is_light = n == self.light_idx
        is_potion = self.inv_slots <= n < self.light_idx

        if is_light:
            key, fill = ("hud_light_sel" if hover else "hud_light"), (
                128, 92, 40
            )
        elif is_potion:
            key, fill = (
                "hud_potion_slot_sel" if hover else "hud_potion_slot"
            ), (112, 74, 150)
        else:
            key, fill = ("hud_slot_sel" if hover else "hud_slot"), (
                128, 138, 154
            )

        img = self._fit_img(key, rect.size)

        if img is not None:

            screen.blit(img, rect.topleft)

        else:

            pygame.draw.rect(screen, fill, rect, border_radius=10)

            pygame.draw.rect(
                screen, C_TEXT if hover else C_BORDER, rect,
                width=2, border_radius=10
            )

        label = self._slot_label(n)

        if label:
            self._outlined_text(
                screen, self._font_for(18), label, C_MUTED,
                topleft=(rect.x + 6, rect.y + 4)
            )

        if slot is None:
            return

        item_id, qty = slot

        icon = self._icon(item_id, 40 if is_light else 42)

        if icon is not None:

            t = self._pop.get(n, 0.0)

            if t > 0:

                k = 1.0 + 0.3 * (t / POP_TIME)

                icon = pygame.transform.smoothscale(
                    icon,
                    (
                        max(1, int(icon.get_width() * k)),
                        max(1, int(icon.get_height() * k))
                    )
                )

            screen.blit(icon, icon.get_rect(center=rect.center))

        if is_light:
            return

        placed, floor = per_slot.get(n, (qty, 0))

        self._outlined_text(
            screen, self.tiny_font, str(qty),
            C_BADGE if floor > 0 else C_TEXT,
            bottomright=(rect.right - 5, rect.bottom - 4)
        )

        clear = self._clear_rect(rect)

        if hover:

            over = clear.collidepoint(mouse)

            pygame.draw.circle(
                screen, (170, 56, 56) if over else (70, 34, 40),
                clear.center, 8
            )

            cx, cy = clear.center

            pygame.draw.line(
                screen, C_TEXT, (cx - 3, cy - 3), (cx + 3, cy + 3), 2
            )

            pygame.draw.line(
                screen, C_TEXT, (cx - 3, cy + 3), (cx + 3, cy - 3), 2
            )

        elif floor > 0:

            txt = self._font_for(18).render(str(floor), True, (30, 18, 8))

            pill = pygame.Rect(0, 0, txt.get_width() + 18, 16)
            pill.topright = (rect.right - 3, rect.y + 3)

            pygame.draw.rect(screen, C_BADGE, pill, border_radius=8)

            pygame.draw.polygon(
                screen, (30, 18, 8),
                [
                    (pill.x + 4, pill.y + 5),
                    (pill.x + 11, pill.y + 5),
                    (pill.x + 7, pill.y + 11),
                ]
            )

            screen.blit(txt, txt.get_rect(midright=(pill.right - 4, pill.centery)))

    def _draw_slot_tip(self, screen, n, per_slot):

        slot = self.inventory[n]

        if slot is None:
            return

        item_id, qty = slot

        lines = [(self.item_name(item_id), C_TEXT)]

        if n == self.light_idx:

            lines.append(
                ("Ya tienes luz: esta sale al piso", C_BADGE)
                if self.has_light
                else ("Se equipa en tu mano", C_MUTED)
            )

        else:

            placed, floor = per_slot.get(n, (qty, 0))

            lines.append((f"Compras {qty}", C_MUTED))

            lines.append(
                (
                    f"{placed} {'va' if placed == 1 else 'van'} "
                    f"al inventario",
                    C_MUTED
                )
            )

            if floor > 0:
                lines.append(
                    (
                        f"{floor} {'cae' if floor == 1 else 'caen'} "
                        f"al piso",
                        C_BADGE
                    )
                )

        max_w = TIP_W - TIP_PAD_X * 2

        imgs = [
            self._fit_font(text, max_w, 22, min_size=14).render(
                text, True, color
            )
            for text, color in lines
        ]

        box = pygame.Rect(0, 0, TIP_W, TIP_H)

        box.midtop = (
            self.slot_rects[n].centerx, self.slot_rects[n].bottom + 10
        )
        box.clamp_ip(self.panel)

        tip_img = self._img("tip", box.size)

        if tip_img is not None:

            screen.blit(tip_img, box.topleft)

        else:

            pygame.draw.rect(screen, C_PANEL, box, border_radius=8)
            pygame.draw.rect(screen, C_BADGE, box, width=1, border_radius=8)

        # el texto va centrado en vertical dentro del margen
        gap = 2

        text_h = sum(img.get_height() for img in imgs) + gap * (len(imgs) - 1)

        y = box.y + TIP_PAD_Y + max(0, (TIP_H - TIP_PAD_Y * 2 - text_h) // 2)

        for img in imgs:

            screen.blit(img, (box.x + TIP_PAD_X, y))

            y += img.get_height() + gap

    def _draw_hotbar(self, screen, mouse):

        screen.blit(self.hotbar_plate, self.hotbar_rect.topleft)

        self._draw_hotbar_group(
            screen, self.hot_panel, "hud_bar", (74, 84, 104), (34, 40, 56)
        )

        self._draw_hotbar_group(
            screen, self.pot_panel, "hud_potion_panel",
            (96, 62, 132), (58, 34, 82)
        )

        for rect, name in (
            (self.hot_panel, "Mochila"),
            (self.pot_panel, "Pociones"),
            (self.light_frame, "Luz"),
        ):
            self._text(
                screen, self._font_for(19), name, C_MUTED,
                midtop=(rect.centerx, self.hot_panel.bottom + 4)
            )

        per_slot = self.delivery()["per_slot"]

        hover_n = self._slot_at(mouse)

        # si estas sobre un producto, se marca donde va a caer
        hover_id = self._card_at(mouse)

        kind, target = self._card_target(hover_id)

        if kind is not None:

            if target is None:

                group = (
                    self.pot_panel if kind == KIND_POTION else self.hot_panel
                )

                pygame.draw.rect(
                    screen, C_RED, group.inflate(6, 6),
                    width=2, border_radius=14
                )

        for n in range(self.total_slots):
            self._draw_slot(screen, n, n == hover_n, per_slot, mouse)

        if self.sel_slot is not None:

            pygame.draw.rect(
                screen, C_SELECT,
                self.slot_rects[self.sel_slot].inflate(8, 8),
                width=3, border_radius=12
            )

        if kind is not None and target is not None:

            blocked = self._slot_full(target, hover_id)

            # si el destino es el casillero elegido y se puede, ya se ve
            if blocked or target != self.sel_slot:

                pygame.draw.rect(
                    screen,
                    C_RED if blocked else C_BADGE,
                    self.slot_rects[target].inflate(6, 6),
                    width=2, border_radius=12
                )

        if hover_n is not None:
            self._draw_slot_tip(screen, hover_n, per_slot)

    def _draw_inv_box(self, screen, mouse):

        screen.blit(self.inv_box_plate, self.inv_box.topleft)

        self._draw_footer(
            screen, mouse, self.inv_box, self.inv_box.y + 17,
            self.inv_box.y + 71
        )

    def _draw_tabs(self, screen, mouse):

        for tab, label in (("shop", "Productos"), ("inv", "Inventario")):

            rect = self.tab_rects[tab]

            active = tab == self.tab
            hover = rect.collidepoint(mouse)

            tab_img = self._img(
                "tab_on" if active else "tab", rect.size,
                shade=30 if (hover and not active) else 0
            )

            if tab_img is not None:

                screen.blit(tab_img, rect.topleft)

            else:

                pygame.draw.rect(
                    screen,
                    C_CARD_HOVER if (active or hover) else C_CARD,
                    rect,
                    border_radius=8
                )

                pygame.draw.rect(
                    screen,
                    C_BADGE if active else C_BORDER,
                    rect,
                    width=2 if active else 1,
                    border_radius=8
                )

            self._text(
                screen, self.section_font, label,
                C_TEXT if active else C_MUTED,
                center=rect.center
            )

    def _info_body(self, item_id, max_w, max_h=None):

        raws = self.info_lines(item_id)

        for size in INFO_FONT_SIZES:

            font = self._font_for(size)
            body = []

            for raw in raws:

                if raw == "":
                    body.append("")
                    continue

                body.extend(self._wrap(font, raw, max_w))

            line_h = font.get_linesize()

            if max_h is None or len(body) * line_h <= max_h:
                break

        return font, body, line_h

    def _draw_info(self, screen, item_id):

        info_img = _load_raw("info")

        if info_img is not None:

            box = info_img.get_rect(center=self.panel.center)
            box.clamp_ip(screen.get_rect())

            pad_x = INFO_PAD_X
            top = INFO_PAD_TOP

            font, body, line_h = self._info_body(
                item_id,
                box.w - pad_x * 2,
                box.h - INFO_PAD_TOP - INFO_HEADER_H - INFO_PAD_BOTTOM,
            )

            body_y = box.y + INFO_PAD_TOP + INFO_HEADER_H
            foot_y = box.bottom - 10

        else:

            pad_x = 18
            top = 18

            width = 420

            font, body, line_h = self._info_body(item_id, width - pad_x * 2)

            height = pad_x * 2 + 36 + len(body) * line_h + 22

            box = pygame.Rect(0, 0, width, height)
            box.center = self.panel.center
            box.clamp_ip(screen.get_rect())

            body_y = box.y + top + 44
            foot_y = box.bottom - 8

        shade = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 120))
        screen.blit(shade, (0, 0))

        if info_img is not None:

            screen.blit(info_img, box.topleft)

        else:

            pygame.draw.rect(screen, C_PANEL, box, border_radius=14)
            pygame.draw.rect(screen, C_BADGE, box, width=2, border_radius=14)

        icon = self._icon(item_id, 34)

        if icon is not None:
            screen.blit(icon, (box.x + pad_x, box.y + top - 2))

        name = self.item_name(item_id)
        name_w = box.w - pad_x * 2 - 44

        self._text(
            screen, self._fit_font(name, name_w, 28), name, C_TEXT,
            midleft=(box.x + pad_x + 44, box.y + top + 15)
        )

        y = body_y

        for line in body:

            if line:
                self._text(
                    screen, font, line, C_TEXT,
                    topleft=(box.x + pad_x, y)
                )

            y += line_h

        self._text(
            screen, self.tiny_font, "Click para cerrar", C_MUTED,
            midbottom=(box.centerx, foot_y)
        )

    def draw(self, screen):

        mouse = pygame.mouse.get_pos()

        screen.blit(self.dim, (0, 0))

        panel_img = self._img("panel", self.panel.size)

        if panel_img is not None:

            screen.blit(panel_img, self.panel.topleft)

        else:

            pygame.draw.rect(
                screen, C_PANEL, self.panel, border_radius=16
            )

            pygame.draw.rect(
                screen, C_BORDER, self.panel, width=1, border_radius=16
            )

        self._text(
            screen, self.title_font, "Tienda", C_TEXT,
            midleft=(self.panel.x + self.PAD, self.coin_pill.centery)
        )

        self._draw_tabs(screen, mouse)

        hover = self.close_rect.collidepoint(mouse)

        close_img = self._img(
            "close", self.close_rect.size, shade=40 if hover else 0
        )

        if close_img is not None:

            screen.blit(close_img, self.close_rect.topleft)

        else:

            pygame.draw.rect(
                screen,
                C_CARD_HOVER if hover else C_CARD,
                self.close_rect,
                border_radius=10
            )

            pygame.draw.rect(
                screen, C_BORDER, self.close_rect, width=1, border_radius=10
            )

            cx, cy = self.close_rect.center

            pygame.draw.line(
                screen, C_TEXT, (cx - 6, cy - 6), (cx + 6, cy + 6), 2
            )

            pygame.draw.line(
                screen, C_TEXT, (cx - 6, cy + 6), (cx + 6, cy - 6), 2
            )

        coins_img = self._img("coins", self.coin_pill.size)

        if coins_img is not None:

            screen.blit(coins_img, self.coin_pill.topleft)

        else:

            pygame.draw.rect(
                screen, C_CARD, self.coin_pill, border_radius=18
            )

            pygame.draw.rect(
                screen, C_BORDER, self.coin_pill, width=1, border_radius=18
            )

        self._draw_coin_amount(
            screen,
            self.coins,
            C_TEXT,
            (self.coin_pill.right - 14, self.coin_pill.centery),
            max_w=58
        )

        self._draw_list(screen, mouse)

        if self.tab == "inv":
            self._draw_hotbar(screen, mouse)
            self._draw_inv_box(screen, mouse)
        else:
            self._draw_cart(screen, mouse)

        if self.info_id is not None:
            self._draw_info(screen, self.info_id)

        if self.tab == "inv":

            help_text = (
                "Click en un casillero: elegirlo  ·  Click en un producto: "
                "sumar  ·  x15: sumar 15  ·  Click derecho: restar  ·  "
                "Rueda sobre un casillero: ±1  ·  Tab: cambiar  ·  "
                "E / Esc: cerrar"
            )

        else:

            help_text = (
                "Click: agregar  ·  x15: agregar 15  ·  Click derecho: quitar  ·  "
                "Click en la rueda: info  ·  Rueda: bajar  ·  "
                "Tab: cambiar  ·  E / Esc: cerrar"
            )

        self._text(
            screen,
            self._fit_font(help_text, self.panel.w - self.PAD * 2, 21),
            help_text,
            C_MUTED,
            midbottom=(self.panel.centerx, self.panel.bottom - 8)
        )