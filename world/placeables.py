"""Objetos que se colocan / mueven por el mapa: bolsa, cofre, faro y fogata.

  BOLSA   no va al inventario. Se compra en la tienda y aparece en el piso.
          Click izquierdo MANTENIDO sobre ella = la arrastras (como en
          R.E.P.O.). Click derecho sobre ella = ves lo que tiene adentro.
          4 casilleros, 15 de cada cosa por casillero.
  COFRE   item de inventario. Lo elegis en la hotbar, se ve una vista
          previa en el mapa y con click izquierdo lo pones EXACTAMENTE
          donde esta el mouse. Queda permanente. Click derecho = abrirlo.
          8 casilleros, 15 de cada cosa por casillero.
  FARO    linterna antigua. Se coloca igual que el cofre y se puede
          arrastrar (click izquierdo mantenido). Ilumina un poco y le
          devuelve vida a tu luz mientras estas cerca. Hay que alimentarla
          con CERA: con la cera elegida en la hotbar, F / click derecho
          cerca.
  FOGATA  item de inventario. Se coloca igual (permanente). Ilumina mucho,
          dura mucho y se alimenta con poquita MADERA (misma forma).

Todos los numeros para balancear estan en las constantes de abajo.
"""

import math
from pathlib import Path

import pygame

from core.audio_manager import audio
from world import items as _items
from world.items import HUD_DIR, load_icon


# ---------------------------------------------------------------
# NUMEROS PARA BALANCEAR
# ---------------------------------------------------------------

# Cuanto se puede alejar el jugador para agarrar / abrir / alimentar
REACH = 64

# Hasta donde puede llevar la bolsa / el faro respecto del jugador
DRAG_RANGE = 56

# Cuanto "tira" hacia el mouse lo que arrastras (mas = mas pegado)
DRAG_SPEED = 16.0

BAG_SLOTS = 4
CHEST_SLOTS = 8

# Cuantas unidades entran en cada casillero de la bolsa / el cofre
CONTAINER_STACK = 15

# A que distancia del jugador (en el mundo) se puede colocar un objeto
PLACE_RANGE = 72

# Combustible, en segundos de luz
FARO_MAX = 90.0            # lleno dura 90 s
FARO_START = 30.0          # recien colocado trae 30 s
FARO_PER_CERA = 25.0       # cada cera suma 25 s (3-4 ceras = lleno)
FARO_RADIUS = 140          # radio de luz (pixeles de pantalla): poquito,
                           # pero mas que el fosforo (100)
FARO_HEAL = 0.015          # vida de tu luz que recupera POR SEGUNDO si
                           # estas dentro de su luz (el fosforo gasta 0.033)

FOGATA_MAX = 900.0         # llena dura 15 minutos
FOGATA_START = 300.0       # recien colocada trae 5 minutos
FOGATA_PER_MADERA = 60.0   # cada madera suma 1 minuto (poquito)
FOGATA_RADIUS = 300        # ilumina bastante (mas que la antorcha: 250)

# Con poco combustible (fraccion del maximo) la luz parpadea y achica
LOW_FUEL = 0.15

# Item que alimenta a cada uno
FUEL_ITEM = {
    "faro": "cera",
    "fogata": "madera",
}

FUEL_PER_ITEM = {
    "faro": FARO_PER_CERA,
    "fogata": FOGATA_PER_MADERA,
}

# Items de inventario que se colocan al usarlos
PLACE_ITEMS = ("cofre", "faro", "fogata")

# Tamano en el mundo (ancho, alto) de cada objeto
WORLD_SIZE = {
    "bolsa": (16, 16),
    "cofre": (22, 18),
    "faro": (14, 16),
    "fogata": (20, 18),
}

# Tamano de los icono placeholder (inventario / tienda)
ICON_IDS = ("bolsa", "cofre", "faro", "fogata")


UI_DIR = HUD_DIR.parent / "ui"

# Imagenes del inventario de la bolsa / el cofre (carpeta assets/maps/ui)
PANEL_FILES = {
    "bolsa": "panel_bolsa.png",     # 296 x 144
    "cofre": "panel_cofre.png",     # 296 x 208
}
SLOT_FILE = "slot_contenedor.png"              # 56 x 56
SLOT_HOVER_FILE = "slot_contenedor_hover.png"  # 56 x 56

# Medidas del panel (en pixeles de pantalla)
SLOT_PX = 56
SLOT_GAP = 8
PANEL_COLS = 4
PANEL_MARGIN_X = 24       # de la izquierda del panel al primer casillero
PANEL_TOP = 56            # de arriba del panel a la primera fila
PANEL_BOTTOM = 32         # espacio de abajo (para el texto de ayuda)


def _sprite_path(kind, suffix=""):
    return HUD_DIR / f"icon_{kind}{suffix}.png"


# ---------------------------------------------------------------
# DIBUJOS DE RESPALDO (por codigo, por si faltan los PNG)
# Si existe assets/maps/hud/icon_<id>.png se usa ese.
# ---------------------------------------------------------------

def _draw_bolsa(W, H):

    s = pygame.Surface((W, H), pygame.SRCALPHA)

    body = pygame.Rect(int(W * .12), int(H * .30), int(W * .76), int(H * .65))

    neck = [
        (W * .34, H * .34), (W * .66, H * .34),
        (W * .58, H * .10), (W * .42, H * .10),
    ]

    pygame.draw.polygon(s, (140, 95, 50), neck)
    pygame.draw.ellipse(s, (140, 95, 50), body)
    shine = body.inflate(-int(body.w * .5), -int(body.h * .55))
    shine.move_ip(-int(body.w * .08), -int(body.h * .12))

    pygame.draw.ellipse(s, (176, 126, 70), shine)
    pygame.draw.ellipse(s, (80, 50, 25), body, max(1, W // 24))
    pygame.draw.polygon(s, (80, 50, 25), neck, max(1, W // 32))
    pygame.draw.line(s, (232, 204, 120),
                     (W * .34, H * .34), (W * .66, H * .34),
                     max(2, W // 14))

    return s


def _draw_cofre(W, H):

    s = pygame.Surface((W, H), pygame.SRCALPHA)

    lw = max(1, W // 24)

    body = pygame.Rect(int(W * .05), int(H * .38), int(W * .90), int(H * .57))
    lid = pygame.Rect(int(W * .05), int(H * .10), int(W * .90), int(H * .32))

    pygame.draw.rect(s, (118, 76, 38), body, border_radius=max(2, W // 14))
    pygame.draw.rect(s, (150, 100, 52), lid, border_radius=max(3, W // 8))
    pygame.draw.rect(s, (70, 44, 22), body, lw, border_radius=max(2, W // 14))
    pygame.draw.rect(s, (70, 44, 22), lid, lw, border_radius=max(3, W // 8))

    band = max(2, W // 9)

    pygame.draw.rect(s, (205, 172, 62),
                     (W // 2 - band // 2, int(H * .10), band, int(H * .85)))

    lock = pygame.Rect(0, 0, max(3, W // 6), max(3, W // 6))
    lock.center = (W // 2, int(H * .42))

    pygame.draw.rect(s, (238, 208, 90), lock, border_radius=2)
    pygame.draw.rect(s, (90, 64, 20), lock, 1, border_radius=2)

    return s


def _draw_faro(W, H, lit=True):
    """Linterna antigua."""

    s = pygame.Surface((W, H), pygame.SRCALPHA)

    lw = max(1, W // 20)
    dark = (70, 52, 38)

    # Aro para agarrarla
    pygame.draw.ellipse(s, dark, (int(W * .36), 0, int(W * .28), int(H * .22)), lw)

    # Tapa y base
    pygame.draw.polygon(s, (120, 96, 70), [
        (W * .20, H * .30), (W * .80, H * .30), (W * .66, H * .14),
        (W * .34, H * .14),
    ])
    pygame.draw.rect(s, (120, 96, 70),
                     (int(W * .18), int(H * .86), int(W * .64), int(H * .10)))

    # Vidrio
    glass = pygame.Rect(int(W * .24), int(H * .30), int(W * .52), int(H * .56))

    pygame.draw.rect(s, (255, 226, 120) if lit else (150, 146, 140), glass)
    pygame.draw.rect(s, dark, glass, lw)

    # Llama
    if lit:
        pygame.draw.polygon(s, (255, 150, 40), [
            (W * .40, H * .80), (W * .50, H * .46), (W * .60, H * .80),
        ])

    return s


def _draw_fogata(W, H, flame=False):

    s = pygame.Surface((W, H), pygame.SRCALPHA)

    t = max(3, int(W * .11))

    # Piedras
    for i in range(6):

        a = math.pi * (0.1 + 0.8 * i / 5)
        cx = W * .5 + math.cos(a) * W * .40
        cy = H * .78 + math.sin(a) * H * .16

        r = pygame.Rect(0, 0, max(3, W // 6), max(3, W // 7))
        r.center = (int(cx), int(cy))

        pygame.draw.ellipse(s, (130, 130, 138), r)
        pygame.draw.ellipse(s, (70, 70, 78), r, 1)

    # Troncos cruzados
    pygame.draw.line(s, (112, 70, 34),
                     (W * .20, H * .90), (W * .80, H * .62), t)
    pygame.draw.line(s, (96, 58, 28),
                     (W * .20, H * .62), (W * .80, H * .90), t)

    if flame:

        pygame.draw.polygon(s, (255, 150, 40), [
            (W * .30, H * .70), (W * .50, H * .06), (W * .70, H * .70),
        ])
        pygame.draw.polygon(s, (255, 226, 110), [
            (W * .40, H * .70), (W * .50, H * .32), (W * .60, H * .70),
        ])

    return s


_DRAWERS = {
    "bolsa": _draw_bolsa,
    "cofre": _draw_cofre,
    "faro": lambda W, H: _draw_faro(W, H, lit=True),
    "fogata": lambda W, H: _draw_fogata(W, H, flame=True),
}


def install_placeholder_icons():
    """Si falta icon_<id>.png, deja un dibujo por codigo en la cache de
    iconos, asi el inventario y la tienda igual muestran algo."""

    for item_id in ICON_IDS:

        if _sprite_path(item_id).exists():
            continue

        if _items._icon_cache.get(item_id) is None:
            _items._icon_cache[item_id] = _DRAWERS[item_id](64, 64)


# ---------------------------------------------------------------
# CONTENEDOR (bolsa y cofre)
# ---------------------------------------------------------------

class Container:

    def __init__(self, slots, capacity=None):

        self.slots = [None] * slots
        self.capacity = capacity

    def total(self):

        return sum(s[1] for s in self.slots if s)

    def add(self, item_id, stack_limit):
        """Mete UNA unidad. False si no entra."""

        for s in self.slots:

            if s and s[0] == item_id and s[1] < stack_limit:

                s[1] += 1

                return True

        for i, s in enumerate(self.slots):

            if s is None:

                self.slots[i] = [item_id, 1]

                return True

        return False

    def take(self, index, amount=None):
        """Saca `amount` unidades (todas si es None). Devuelve cuantas."""

        s = self.slots[index]

        if not s:
            return 0

        n = s[1] if amount is None else min(amount, s[1])

        s[1] -= n

        if s[1] <= 0:
            self.slots[index] = None

        return n

    def save(self):

        return [list(s) if s else None for s in self.slots]

    def load(self, data):

        for i in range(len(self.slots)):

            entry = data[i] if i < len(data) else None

            if (
                isinstance(entry, (list, tuple))
                and len(entry) == 2
                and entry[1] > 0
            ):
                self.slots[i] = [str(entry[0]), int(entry[1])]


# ---------------------------------------------------------------
# OBJETOS DEL MUNDO
# ---------------------------------------------------------------

class Placeable:

    kind = "?"
    draggable = False
    container_slots = 0
    container_capacity = None
    fuel_max = 0.0
    light_radius_px = 0

    def __init__(self, x, y, fuel=None):

        w, h = WORLD_SIZE[self.kind]

        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(x), int(y))

        self.container = (
            Container(self.container_slots, self.container_capacity)
            if self.container_slots else None
        )

        self.fuel = float(fuel) if fuel is not None else 0.0

        self.near = False
        self._phase = (x * 0.37 + y * 0.11) % 6.28

        self._scaled = {}

        self._real = _sprite_path(self.kind).exists()

        self.fly = None
        self._lift = 0.0

    # ----- combustible -----

    @property
    def uses_fuel(self):
        return self.fuel_max > 0

    @property
    def lit(self):
        return self.uses_fuel and self.fuel > 0

    @property
    def fuel_fraction(self):

        if not self.uses_fuel:
            return 0.0

        return max(0.0, min(1.0, self.fuel / self.fuel_max))

    def add_fuel(self, amount):

        self.fuel = min(self.fuel_max, self.fuel + amount)

    def burn(self, dt):

        if self.lit:
            self.fuel = max(0.0, self.fuel - dt)

    # ----- luz -----

    def light_radius(self, clock):

        if not self.lit:
            return 0

        frac = self.fuel_fraction

        radius = self.light_radius_px * (0.55 + 0.45 * min(1.0, frac * 3))

        if frac < LOW_FUEL:

            radius *= 0.6 + 0.4 * abs(math.sin(clock * 14 + self._phase))

        return radius

    def heal_range(self, zoom):
        """Hasta donde (en unidades del mundo) llega su luz."""

        if not self.lit:
            return 0.0

        return (
            self.light_radius_px
            * (0.55 + 0.45 * min(1.0, self.fuel_fraction * 3))
            / max(1, zoom)
        )

    # ----- dibujo -----

    def _base_sprite(self):

        path = _sprite_path(self.kind)

        if self.uses_fuel and not self.lit:

            off = _sprite_path(self.kind, "_apagado")

            if off.exists():
                path = off

        if path.exists():
            return pygame.image.load(str(path)).convert_alpha()

        w, h = WORLD_SIZE[self.kind]

        # Se dibuja grande y se achica (queda mas suave)
        if self.kind == "fogata":
            return _draw_fogata(w * 8, h * 8, flame=False)

        return _DRAWERS[self.kind](w * 8, h * 8)

    def _sprite(self, zoom):

        key = (round(zoom, 3), self.uses_fuel and not self.lit)

        sprite = self._scaled.get(key)

        if sprite is None:

            base = self._base_sprite()

            w = max(2, int(self.rect.w * zoom))
            h = max(2, int(w * base.get_height() / base.get_width()))

            sprite = pygame.transform.smoothscale(base, (w, h))

            self._scaled[key] = sprite

        return sprite

    def hit(self, wx, wy):

        return self.rect.inflate(6, 6).collidepoint(wx, wy)

    def draw(self, screen, camera, clock):

        f = self.fly

        if f is not None and f["delay"] > 0:
            return

        sprite = self._sprite(camera.zoom)

        dest = camera.apply(self.rect)

        lift = int(self._lift * camera.zoom)

        # Apoyado en la base del rect
        r = sprite.get_rect(
            midbottom=(dest.centerx, dest.bottom - lift)
        )

        screen.blit(sprite, r)

        self.draw_extras(screen, r, clock)

        if self.near and self.uses_fuel:
            self._draw_fuel_bar(screen, r)

    def draw_extras(self, screen, r, clock):
        pass

    def _draw_fuel_bar(self, screen, r):

        w = max(16, r.w)
        bar = pygame.Rect(0, 0, w, 5)
        bar.midbottom = (r.centerx, r.top - 3)

        pygame.draw.rect(screen, (20, 20, 24), bar.inflate(2, 2))

        frac = self.fuel_fraction

        color = (255, 190, 70) if frac > LOW_FUEL else (230, 70, 50)

        fill = bar.copy()
        fill.w = int(bar.w * frac)

        pygame.draw.rect(screen, color, fill)

    # ----- guardado -----

    def save(self):

        x, y = self.rect.center

        # Si todavia vuela (recien comprada), se guarda donde va a caer
        if self.fly is not None:
            x, y = self.fly["dst"]

        data = {
            "t": self.kind,
            "x": int(x),
            "y": int(y),
        }

        if self.uses_fuel:
            data["fuel"] = round(self.fuel, 2)

        if self.container is not None:
            data["slots"] = self.container.save()

        return data


class Bag(Placeable):

    kind = "bolsa"
    draggable = True
    container_slots = BAG_SLOTS

    def start_fly(self, src, dst, delay=0.0, height=14.0, duration=0.45):

        self.fly = {
            "src": src, "dst": dst, "delay": delay,
            "t": 0.0, "dur": duration, "h": height,
        }

        self.rect.center = (round(src[0]), round(src[1]))

    update_fly = _items.WorldItem.update_fly


class Chest(Placeable):

    kind = "cofre"
    container_slots = CHEST_SLOTS


class Lighthouse(Placeable):

    kind = "faro"
    draggable = True
    fuel_max = FARO_MAX
    light_radius_px = FARO_RADIUS

    def draw_extras(self, screen, r, clock):

        if self._real or not self.lit:
            return

        # Brillito en la lampara
        pulse = 0.75 + 0.25 * math.sin(clock * 6 + self._phase)

        glow = pygame.Surface((r.w, r.w), pygame.SRCALPHA)

        pygame.draw.circle(
            glow, (255, 230, 120, int(110 * pulse)),
            (r.w // 2, r.w // 2), r.w // 2
        )

        screen.blit(
            glow,
            glow.get_rect(center=(r.centerx, r.top + int(r.h * .26)))
        )


class Campfire(Placeable):

    kind = "fogata"
    fuel_max = FOGATA_MAX
    light_radius_px = FOGATA_RADIUS

    def draw_extras(self, screen, r, clock):

        if self._real or not self.lit:
            return

        # Llama que se mueve
        s = 0.85 + 0.15 * math.sin(clock * 11 + self._phase)
        s2 = 0.85 + 0.15 * math.sin(clock * 17 + self._phase * 2)

        base_y = r.top + int(r.h * .72)
        fh = int(r.h * .85 * s)
        fw = int(r.w * .46)

        outer = [
            (r.centerx - fw // 2, base_y),
            (r.centerx + int(2 * math.sin(clock * 9)), base_y - fh),
            (r.centerx + fw // 2, base_y),
        ]

        pygame.draw.polygon(screen, (255, 150, 40), outer)

        ih = int(fh * .6 * s2)
        iw = int(fw * .5)

        pygame.draw.polygon(screen, (255, 226, 110), [
            (r.centerx - iw // 2, base_y),
            (r.centerx, base_y - ih),
            (r.centerx + iw // 2, base_y),
        ])


KINDS = {
    "bolsa": Bag,
    "cofre": Chest,
    "faro": Lighthouse,
    "fogata": Campfire,
}


# ---------------------------------------------------------------
# MANAGER
# ---------------------------------------------------------------

class PlaceableManager:

    def __init__(self, saved=None):

        install_placeholder_icons()

        self.objects = []

        self.clock = 0.0

        # Lo que se esta arrastrando
        self.dragging = None

        # Contenedor abierto (bolsa o cofre)
        self.open_obj = None

        self._fonts = {}
        self._icons = {}
        self._ui = {}
        self._ghosts = {}

        for entry in saved or []:

            cls = KINDS.get(entry.get("t")) if isinstance(entry, dict) else None

            if cls is None:
                continue

            obj = cls(entry.get("x", 0), entry.get("y", 0), entry.get("fuel"))

            if obj.container is not None:
                obj.container.load(entry.get("slots", []))

            self.objects.append(obj)

    # ---------- utilidades ----------

    def _font(self, size):

        font = self._fonts.get(size)

        if font is None:
            font = pygame.font.Font(None, size)
            self._fonts[size] = font

        return font

    def _icon(self, item_id, size):

        key = (item_id, size)

        if key not in self._icons:

            icon = load_icon(item_id)

            if icon is not None:
                icon = pygame.transform.smoothscale(icon, (size, size))

            self._icons[key] = icon

        return self._icons[key]

    @staticmethod
    def _mouse_world(game):

        mx, my = pygame.mouse.get_pos()

        return (
            (game.camera.x + mx) / game.camera.zoom,
            (game.camera.y + my) / game.camera.zoom,
        )

    @staticmethod
    def _dist(game, obj):

        return math.hypot(
            obj.rect.centerx - game.player.rect.centerx,
            obj.rect.centery - game.player.rect.centery,
        )

    def _under_mouse(self, game):
        """El objeto del mundo bajo el mouse y a tu alcance."""

        wx, wy = self._mouse_world(game)

        best = None

        for obj in self.objects:

            if obj.fly is not None:
                continue

            if obj.hit(wx, wy) and self._dist(game, obj) <= REACH:

                if best is None or obj.rect.centery > best.rect.centery:
                    best = obj

        return best

    def _nearest_feedable(self, game, item_id):
        """Faro / fogata cercano al que le sirve `item_id` (y no esta
        lleno)."""

        best = None
        best_d = None

        for obj in self.objects:

            if (
                obj.uses_fuel
                and FUEL_ITEM.get(obj.kind) == item_id
                and obj.fuel < obj.fuel_max - 0.01
            ):
                d = self._dist(game, obj)

                if d <= REACH and (best is None or d < best_d):
                    best, best_d = obj, d

        return best

    # ---------- crear ----------

    def spawn_bag(self, x, y, src=None, delay=0.0, collision_map=None):

        bag = Bag(x, y)

        if src is not None:
            bag.start_fly(src, (x, y), delay=delay)

        self.objects.append(bag)

        return bag

    def _spot_free(self, game, rect):

        pts = [
            rect.center, rect.topleft, rect.topright,
            (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1),
        ]

        for p in pts:

            if not game.collision_map.point_is_walkable(*p):
                return False

        for obj in self.objects:

            if obj.rect.colliderect(rect):
                return False

        return True

    # ---------- colocar (preciso, donde esta el mouse) ----------

    def _held(self, game):
        """(casillero, id) si tenes elegido en la hotbar un item que se
        coloca (cofre, faro, fogata). Si no, None."""

        slot = game.selected_slot

        if not isinstance(slot, int) or slot >= game.hud.SLOTS:
            return None

        item_id = game.hud.items[slot]

        if item_id in PLACE_ITEMS:
            return slot, item_id

        return None

    @staticmethod
    def _over_hud(game, pos):
        """El mouse esta sobre la hotbar, el slot de luz o el boton menu."""

        if game.hud.slot_at(pos) is not None:
            return True

        for name in ("equipped_rect", "menu_button_rect", "attack_panel_rect"):

            r = getattr(game.hud, name, None)

            if r is not None and r.collidepoint(pos):
                return True

        return False

    def _can_place(self, game, kind, wx, wy):
        """(se puede, rect) para poner `kind` con el centro en (wx, wy)."""

        w, h = WORLD_SIZE[kind]

        r = pygame.Rect(0, 0, w, h)
        r.center = (int(wx), int(wy))

        px, py = game.player.rect.center

        if math.hypot(wx - px, wy - py) > PLACE_RANGE:
            return False, r

        return self._spot_free(game, r), r

    def _place(self, game, slot, item_id, wx, wy):
        """Coloca el item en (wx, wy). True si se pudo."""

        ok, r = self._can_place(game, item_id, wx, wy)

        if not ok:

            game.show_message("No se puede poner ahí")

            return False

        obj = KINDS[item_id](r.centerx, r.centery)

        if obj.uses_fuel:
            obj.fuel = FARO_START if item_id == "faro" else FOGATA_START

        self.objects.append(obj)

        game._take_one(slot)

        audio.play("pickup")

        game.show_message(
            f"Pusiste {game._item_name(item_id)}"
            + (" (queda fijo)" if not obj.draggable else "")
        )

        return True

    # ---------- usar items del inventario ----------

    def try_use(self, game, slot):
        """Lo llama use_item. Devuelve True si se encargo el (y no hay
        que hacer el uso normal del item)."""

        item_id = game.hud.items[slot]

        if item_id is None:
            return False

        # --- colocar cofre / faro / fogata (F o click derecho) ---
        if item_id in PLACE_ITEMS:

            mouse = pygame.mouse.get_pos()

            # Si el mouse esta sobre la hotbar no hay donde ponerlo
            if self._over_hud(game, mouse):

                game.show_message(
                    "Elegilo y hacé click en el mapa donde lo querés poner"
                )

                return True

            wx, wy = self._mouse_world(game)

            self._place(game, slot, item_id, wx, wy)

            return True

        # --- alimentar faro / fogata ---
        obj = self._nearest_feedable(game, item_id)

        if obj is not None:

            obj.add_fuel(FUEL_PER_ITEM[obj.kind])

            game._take_one(slot)

            audio.play("pickup")

            game.show_message(
                f"{game._item_name(obj.kind)}: "
                f"{int(obj.fuel)} s de luz"
            )

            return True

        return False

    # ---------- eventos ----------

    def handle_event(self, game, event):
        """True si el evento se uso aca (el juego no lo procesa mas)."""

        if game.state != "playing":
            return False

        # ESC cierra el contenedor abierto (no abre la pausa)
        if (
            self.open_obj is not None
            and event.type == pygame.KEYDOWN
            and event.key == pygame.K_ESCAPE
        ):
            self.open_obj = None

            return True

        if event.type != pygame.MOUSEBUTTONDOWN:
            return False

        # ----- con el panel abierto -----
        if self.open_obj is not None:

            consumed = self._panel_click(game, event)

            if consumed:
                return True

        # ----- click izquierdo: arrastrar, o colocar lo que tenes en mano -----
        if event.button == 1:

            if self._over_hud(game, event.pos):
                return False

            obj = self._under_mouse(game)

            if obj is not None and obj.draggable:

                self.dragging = obj

                return True

            held = self._held(game)

            if held is not None and self.open_obj is None:

                wx, wy = self._mouse_world(game)

                self._place(game, held[0], held[1], wx, wy)

                return True

            return False

        # ----- click derecho: abrir / ver combustible -----
        if event.button == 3:

            obj = self._under_mouse(game)

            if obj is None:
                return False

            if obj.container is not None:

                self.open_obj = obj

                return True

            if obj.uses_fuel:

                game.show_message(
                    f"{game._item_name(obj.kind)}: "
                    f"{int(obj.fuel)} s de luz"
                )

                return True

        return False

    def draw_ghost(self, game, screen):
        """Vista previa del objeto que tenes en mano, en el mouse: verde si
        se puede poner ahi, rojo si no."""

        if game.state != "playing" or self.open_obj is not None:
            return

        if (
            getattr(game, "shop", None) is not None
            or getattr(game, "pause_view", None) is not None
            or getattr(game, "tutorial", None) is not None
        ):
            return

        held = self._held(game)

        if held is None:
            return

        mouse = pygame.mouse.get_pos()

        if self._over_hud(game, mouse):
            return

        kind = held[1]

        wx, wy = self._mouse_world(game)

        ok, r = self._can_place(game, kind, wx, wy)

        ghost = self._ghosts.get(kind)

        if ghost is None:

            ghost = KINDS[kind](0, 0)

            if ghost.uses_fuel:
                ghost.fuel = ghost.fuel_max

            self._ghosts[kind] = ghost

        ghost.rect.center = r.center

        sprite = ghost._sprite(game.camera.zoom).copy()

        sprite.set_alpha(150)

        dest = game.camera.apply(ghost.rect)

        screen.blit(sprite, sprite.get_rect(midbottom=dest.midbottom))

        color = (90, 230, 120) if ok else (240, 80, 70)

        pygame.draw.rect(screen, color, dest, 2)

    # ---------- panel de contenido ----------

    def _panel_size(self, obj):

        n = len(obj.container.slots)

        rows = math.ceil(n / PANEL_COLS)

        w = (
            PANEL_MARGIN_X * 2
            + PANEL_COLS * SLOT_PX
            + (PANEL_COLS - 1) * SLOT_GAP
        )

        h = (
            PANEL_TOP
            + rows * SLOT_PX
            + (rows - 1) * SLOT_GAP
            + PANEL_BOTTOM
        )

        return w, h

    def _panel_layout(self, game):

        obj = self.open_obj

        w, h = self._panel_size(obj)

        sw, sh = game.screen.get_size()

        panel = pygame.Rect(0, 0, w, h)
        panel.center = (sw // 2, int(sh * 0.40))

        slots = []

        for i in range(len(obj.container.slots)):

            c, r = i % PANEL_COLS, i // PANEL_COLS

            slots.append(
                pygame.Rect(
                    panel.x + PANEL_MARGIN_X + c * (SLOT_PX + SLOT_GAP),
                    panel.y + PANEL_TOP + r * (SLOT_PX + SLOT_GAP),
                    SLOT_PX, SLOT_PX
                )
            )

        return panel, slots

    def _ui_image(self, name, size=None):
        """assets/maps/ui/<name> (None si no existe), escalada a `size`."""

        key = (name, size)

        if key not in self._ui:

            path = UI_DIR / name

            img = None

            if path.exists():

                img = pygame.image.load(str(path)).convert_alpha()

                if size is not None and img.get_size() != tuple(size):
                    img = pygame.transform.smoothscale(img, size)

            self._ui[key] = img

        return self._ui[key]

    def _panel_click(self, game, event):

        panel, slots = self._panel_layout(game)

        obj = self.open_obj

        one = event.button == 3

        # Casillero del contenedor -> a tu inventario
        for i, r in enumerate(slots):

            if r.collidepoint(event.pos):

                self._to_inventory(game, obj, i, one)

                return True

        # Casillero de tu inventario -> al contenedor
        hotbar = game.hud.slot_at(event.pos)

        if hotbar is not None:

            self._to_container(game, obj, hotbar, one)

            return True

        # Click dentro del panel (aunque sea en un espacio vacio)
        if panel.collidepoint(event.pos):
            return True

        return False

    def _to_inventory(self, game, obj, index, one):

        s = obj.container.slots[index]

        if not s:
            return

        item_id = s[0]

        moved = 0

        want = 1 if one else s[1]

        for _ in range(want):

            slot = game._free_slot_for(item_id)

            if slot is None:

                game.show_message("Inventario lleno")

                break

            if game.hud.items[slot] is None:

                game.hud.items[slot] = item_id
                game.hud.counts[slot] = 1

            else:

                game.hud.counts[slot] += 1

            obj.container.take(index, 1)

            moved += 1

        if moved:
            audio.play("pickup")

    def _to_container(self, game, obj, slot, one):

        item_id = game.hud.items[slot]

        if item_id is None:
            return

        want = 1 if one else game.hud.counts[slot]

        limit = CONTAINER_STACK

        moved = 0

        for _ in range(want):

            if not obj.container.add(item_id, limit):

                game.show_message(
                    "La bolsa está llena"
                    if obj.kind == "bolsa" else "El cofre está lleno"
                )

                break

            game._take_one(slot)

            moved += 1

        if moved:
            audio.play("pickup")

    def draw_panel(self, game, screen):

        obj = self.open_obj

        if obj is None:
            return

        panel, slots = self._panel_layout(game)

        mouse = pygame.mouse.get_pos()

        # Fondo: tu imagen (panel_bolsa.png / panel_cofre.png) o, si falta,
        # uno dibujado por codigo
        bg = self._ui_image(PANEL_FILES[obj.kind], panel.size)

        if bg is not None:

            screen.blit(bg, panel)

        else:

            shade = pygame.Surface(panel.size, pygame.SRCALPHA)

            pygame.draw.rect(
                shade, (22, 24, 30, 240), shade.get_rect(), border_radius=12
            )

            screen.blit(shade, panel)

            pygame.draw.rect(
                screen, (214, 168, 84), panel, 2, border_radius=12
            )

        title = "Bolsa" if obj.kind == "bolsa" else "Cofre"

        text = self._font(30).render(title, True, (244, 236, 214))

        screen.blit(text, (panel.x + PANEL_MARGIN_X, panel.y + 16))

        slot_img = self._ui_image(SLOT_FILE, (SLOT_PX, SLOT_PX))
        slot_hover = self._ui_image(SLOT_HOVER_FILE, (SLOT_PX, SLOT_PX))

        hover_name = None

        for i, r in enumerate(slots):

            hover = r.collidepoint(mouse)

            if slot_img is not None:

                screen.blit(
                    slot_hover if (hover and slot_hover is not None)
                    else slot_img,
                    r
                )

            else:

                pygame.draw.rect(
                    screen, (62, 66, 80) if hover else (44, 47, 58), r,
                    border_radius=6
                )
                pygame.draw.rect(
                    screen, (120, 126, 146), r, 1, border_radius=6
                )

            s = obj.container.slots[i]

            if not s:
                continue

            icon = self._icon(s[0], 40)

            if icon is not None:
                screen.blit(icon, icon.get_rect(center=r.center))

            if s[1] > 1:

                n = self._font(22).render(str(s[1]), True, (255, 255, 255))

                screen.blit(
                    n, n.get_rect(bottomright=(r.right - 4, r.bottom - 2))
                )

            if hover:
                hover_name = game._item_name(s[0])

        hint = self._font(20).render(
            "Click: pasar todo  ·  Click derecho: de a 1  ·  Esc: cerrar",
            True, (170, 176, 192)
        )

        screen.blit(
            hint, hint.get_rect(midbottom=(panel.centerx, panel.bottom - 8))
        )

        if hover_name:

            tip = self._font(24).render(hover_name, True, (255, 232, 170))

            screen.blit(
                tip, tip.get_rect(midbottom=(panel.centerx, panel.y - 6))
            )

    # ---------- update ----------

    def update(self, game, dt):

        self.clock += dt

        for obj in self.objects:

            if obj.fly is not None:

                obj.update_fly(dt)

                continue

            obj.burn(dt)

            obj.near = self._dist(game, obj) <= REACH + 24

        # El faro (linterna antigua) le devuelve vida a tu luz si estas
        # dentro de su luz
        if game.has_match and game.vida < 1.0:

            for obj in self.objects:

                if (
                    obj.kind == "faro"
                    and obj.fly is None
                    and self._dist(game, obj) <= obj.heal_range(game.camera.zoom)
                ):

                    game.vida = min(1.0, game.vida + FARO_HEAL * dt)

                    break

        # Se cierra solo si te alejas del contenedor abierto
        if self.open_obj is not None:

            if (
                self.open_obj not in self.objects
                or self._dist(game, self.open_obj) > REACH + 30
            ):
                self.open_obj = None

        # Arrastre
        if self.dragging is not None:

            obj = self.dragging

            if (
                not pygame.mouse.get_pressed()[0]
                or obj not in self.objects
                or self._dist(game, obj) > DRAG_RANGE * 2
            ):

                self.dragging = None

                return

            self._drag(game, obj, dt)

    def _drag(self, game, obj, dt):

        mx, my = self._mouse_world(game)

        px, py = game.player.rect.center

        # El objetivo no se aleja mas de DRAG_RANGE del jugador
        dx, dy = mx - px, my - py

        d = math.hypot(dx, dy)

        if d > DRAG_RANGE:

            mx = px + dx / d * DRAG_RANGE
            my = py + dy / d * DRAG_RANGE

        cx, cy = obj.rect.center

        k = min(1.0, DRAG_SPEED * dt)

        nx = cx + (mx - cx) * k
        ny = cy + (my - cy) * k

        w, h = obj.rect.size

        def ok(x, y):

            r = pygame.Rect(0, 0, w, h)
            r.center = (int(x), int(y))

            for p in (
                r.center, r.topleft, r.topright,
                (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1),
            ):
                if not game.collision_map.point_is_walkable(*p):
                    return False

            for other in self.objects:

                if other is not obj and other.fly is None \
                        and other.rect.colliderect(r):
                    return False

            return True

        # Si pega contra algo, se desliza por el eje que si se puede
        if ok(nx, ny):
            obj.rect.center = (int(nx), int(ny))

        elif ok(nx, cy):
            obj.rect.center = (int(nx), cy)

        elif ok(cx, ny):
            obj.rect.center = (cx, int(ny))

    # ---------- dibujo / luz ----------

    def draw(self, screen, camera):

        for obj in sorted(self.objects, key=lambda o: o.rect.bottom):
            obj.draw(screen, camera, self.clock)

    def light_sources(self):
        """[(x, y, radio)] para PlayerLight.draw (radio en px de pantalla)."""

        out = []

        for obj in self.objects:

            if obj.fly is not None and obj.fly["delay"] > 0:
                continue

            radius = obj.light_radius(self.clock)

            if radius >= 2:

                out.append((
                    obj.rect.centerx,
                    obj.rect.centery - (3 if obj.kind == "faro" else 0),
                    radius
                ))

        return out

    # ---------- guardado ----------

    def save_data(self):

        return [obj.save() for obj in self.objects]