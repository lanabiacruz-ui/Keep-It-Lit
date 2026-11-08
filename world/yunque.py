"""Yunque: mejoras (engarces) para la antorcha.

Como funciona:
  * El yunque se compra en la tienda (Construccion), se coloca como el
    cofre, se recoge con el martillo y se abre con click derecho.
    No abre si hay enemigos cerca (se usa entre oleadas).
  * Hay 6 mejoras de 3 niveles. Se compran con monedas + monedas de gelea
    (la moneda de gelea sale de la Maquina: ver world/maquina.py).
  * Solo 3 mejoras (engarces) funcionan a la vez; se cambian gratis cada
    vez que abris el yunque.
  * Las mejoras son SOLO para la antorcha y duran la partida (se guardan en
    el save con la clave "yunque" y se pierden si se borra la partida).

Imagenes (todas opcionales, si no estan se dibujan con codigo):
  assets/maps/hud/icon_yunque.png            64x64   (item + dibujo en el mapa)
  assets/maps/ui/yunque_panel.png            cualquier tamaño (fondo del panel,
                                             se estira en 9 partes: el marco no se deforma)
  assets/maps/hud/yunque_resistencia.png     64x64   \
  assets/maps/hud/yunque_brasas.png          64x64    |
  assets/maps/hud/yunque_repelente.png       64x64    |  iconos de cada mejora
  assets/maps/hud/yunque_llama_amplia.png    64x64    |
  assets/maps/hud/yunque_llama_larga.png     64x64    |
  assets/maps/hud/yunque_manos.png           64x64   /

Imagenes del PANEL (todas opcionales; en assets/maps/ui/). Las que dicen
"9 partes" se estiran sin deformar las esquinas, asi que podes dibujarlas
de cualquier tamaño parecido al indicado:
  yunque_titulo.png            ~300x64  la palabra "Yunque" (reemplaza al texto)
  yunque_engarce.png           56x36    casillero de engarce activo (9 partes, esquina 8)
  yunque_tarjeta.png           347x130  tarjeta de cada mejora (9 partes, esquina 16)
  yunque_tarjeta_activa.png    347x130  la misma cuando esta activa
  yunque_pip.png               16x16    puntito de nivel vacio
  yunque_pip_lleno.png         16x16    puntito de nivel conseguido
  panel_btn.png                96x32    boton normal   (9 partes, esquina 8)
  panel_btn_hover.png          96x32    boton con el mouse encima
  panel_btn_off.png            96x32    boton desactivado
  panel_separador.png          ~480x6   linea de arriba del pie del panel
Los botones y el separador son compartidos con la Maquina y la Ruleta.
"""

from pathlib import Path

import pygame

from world.items import HUD_DIR

UI_DIR = HUD_DIR.parent / "ui"

TORCH = "antorcha"

ACTIVE_SLOTS = 3
MAX_LEVEL = 3

# distancia (px) a la que un enemigo vivo impide abrir el yunque
ENEMY_NEAR = 420

# ---------------------------------------------------------------------------
# Numeros de balance (todo se cambia aca)
# ---------------------------------------------------------------------------

COSTS_COINS = (60, 110, 180)
# Los costos en gelea van en MONEDAS DE GELEA (la Maquina convierte
# 2 geleas en 1 moneda de gelea).
COSTS_GELEA = (2, 3, 4)

# Resistencia cuesta distinto: 80 / 140 / 220 monedas y una moneda de gelea
# mas por nivel
RESIST_COINS = (80, 140, 220)
RESIST_GELEA = (2, 3, 5)

RESIST_PCT = (0.06, 0.12, 0.18)
EMBER_HEAL = (0.01, 0.02, 0.03)
PUSH_SPEED = (110.0, 200.0, 290.0)     # empuje extra del golpe (px/s)
WIDE_RADIUS = (270, 290, 310)          # radio de la antorcha (base 250)
LONG_BURN = (0.06, 0.12, 0.18)         # menos gasto de luz
HANDS_MAGNET = (25, 50, 75)            # px extra de imán
HANDS_CHEST = (20.0, 40.0, 60.0)       # segundos menos de espera de cofres

UPGRADES = {
    "resistencia": {
        "name": "Resistencia",
        "desc": ("-6% daño de enemigos comunes",
                 "-12% daño de enemigos comunes",
                 "-18% daño de enemigos comunes"),
        "note": "No vale contra Hongun, Golem ni jefes",
    },
    "brasas": {
        "name": "Brasas",
        "desc": ("+1% de luz al matar comunes",
                 "+2% de luz al matar comunes",
                 "+3% de luz al matar comunes"),
        "note": "No cuentan Hongun, Golem ni jefes",
    },
    "repelente": {
        "name": "Golpe repelente",
        "desc": ("Empuja un poco al enemigo",
                 "Empuja bastante al enemigo",
                 "Empuja mucho al enemigo"),
        "note": "No cambia los golpes necesarios. Golem y jefes no se mueven",
    },
    "llama_amplia": {
        "name": "Llama amplia",
        "desc": ("Radio de luz 250 -> 270",
                 "Radio de luz 250 -> 290",
                 "Radio de luz 250 -> 310"),
        "note": "Despierta a más enemigos: ahí se equilibra",
    },
    "llama_larga": {
        "name": "Llama larga",
        "desc": ("-6% de gasto de luz",
                 "-12% de gasto de luz",
                 "-18% de gasto de luz"),
        "note": "La luz dura más",
    },
    "manos": {
        "name": "Manos ágiles",
        "desc": ("Imán +25 px, cofres -20 s",
                 "Imán +50 px, cofres -40 s",
                 "Imán +75 px, cofres -60 s"),
        "note": "Menos espera de cofres por nivel",
    },
}

ORDER = (
    "resistencia", "brasas", "repelente",
    "llama_amplia", "llama_larga", "manos",
)

ICON_FILES = {
    uid: f"yunque_{uid}.png" for uid in ORDER
}


def cost_coins(uid, level):
    """Monedas para pasar de `level` al siguiente (level = nivel actual)."""

    table = RESIST_COINS if uid == "resistencia" else COSTS_COINS

    return table[level]


def cost_gelea(uid, level):

    table = RESIST_GELEA if uid == "resistencia" else COSTS_GELEA

    return table[level]


# ---------------------------------------------------------------------------
# Estado (vive en el juego: game.anvil)
# ---------------------------------------------------------------------------

class AnvilState:

    def __init__(self, data=None):

        self.levels = {uid: 0 for uid in ORDER}
        self.active = []

        if isinstance(data, dict):

            lv = data.get("niveles", {})

            if isinstance(lv, dict):
                for uid in ORDER:
                    try:
                        self.levels[uid] = max(
                            0, min(MAX_LEVEL, int(lv.get(uid, 0)))
                        )
                    except (TypeError, ValueError):
                        pass

            act = data.get("activas", [])

            if isinstance(act, list):
                for uid in act:
                    if (
                        uid in self.levels
                        and self.levels[uid] > 0
                        and uid not in self.active
                        and len(self.active) < ACTIVE_SLOTS
                    ):
                        self.active.append(uid)

    def save(self):

        return {
            "niveles": dict(self.levels),
            "activas": list(self.active),
        }

    def level(self, uid):
        """Nivel que esta funcionando (0 si no esta en un engarce)."""

        return self.levels.get(uid, 0) if uid in self.active else 0

    def toggle(self, uid):
        """Pone o saca una mejora de los engarces. Devuelve (ok, mensaje)."""

        if self.levels.get(uid, 0) <= 0:
            return False, "Primero compra esta mejora"

        if uid in self.active:
            self.active.remove(uid)
            return True, f"{UPGRADES[uid]['name']} desactivada"

        if len(self.active) >= ACTIVE_SLOTS:
            return False, "Ya hay 3 engarces: desactiva uno primero"

        self.active.append(uid)

        return True, f"{UPGRADES[uid]['name']} activada"


# ---------------------------------------------------------------------------
# Ayudas para el juego
# ---------------------------------------------------------------------------

def torch_equipped(game):

    return bool(getattr(game, "has_match", False)) and (
        getattr(game, "light_type", None) == TORCH
    )


def lvl(game, uid):
    """Nivel de una mejora SOLO si la antorcha esta equipada."""

    state = getattr(game, "anvil", None)

    if state is None or not torch_equipped(game):
        return 0

    return state.level(uid)


def damage_mult(game):

    n = lvl(game, "resistencia")

    return 1.0 - RESIST_PCT[n - 1] if n else 1.0


def ember_heal(game):

    n = lvl(game, "brasas")

    return EMBER_HEAL[n - 1] if n else 0.0


def push_speed(game):

    n = lvl(game, "repelente")

    return PUSH_SPEED[n - 1] if n else 0.0


def light_radius(game, base):

    n = lvl(game, "llama_amplia")

    return WIDE_RADIUS[n - 1] if n else base


def burn_mult(game):

    n = lvl(game, "llama_larga")

    return 1.0 - LONG_BURN[n - 1] if n else 1.0


def magnet_bonus(game):

    n = lvl(game, "manos")

    return HANDS_MAGNET[n - 1] if n else 0


def chest_reduction(game):

    n = lvl(game, "manos")

    return HANDS_CHEST[n - 1] if n else 0.0


def enemies_near(game, pos, radius=ENEMY_NEAR):
    """True si hay un enemigo vivo (ya aparecido) cerca de `pos`."""

    px, py = pos

    for name in ("arena", "arena_left"):

        arena = getattr(game, name, None)

        for e in getattr(arena, "enemies", []) or []:

            if getattr(e, "dead", False) or getattr(e, "spawning", False):
                continue

            if getattr(e, "attached", False):
                continue

            ex, ey = e.pos

            if (ex - px) ** 2 + (ey - py) ** 2 <= radius * radius:
                return True

    return False


def count_item(game, item_id):

    return sum(
        int(game.hud.counts[i])
        for i in range(game.hud.SLOTS)
        if game.hud.items[i] == item_id
    )


def take_items(game, item_id, n):

    for i in range(game.hud.SLOTS):

        while n > 0 and game.hud.items[i] == item_id:
            game._take_one(i)
            n -= 1


def buy_next(game, uid):
    """Compra el siguiente nivel. Devuelve (ok, mensaje)."""

    state = game.anvil
    cur = state.levels[uid]

    if cur >= MAX_LEVEL:
        return False, "Ya está al máximo"

    coins = cost_coins(uid, cur)
    gelea = cost_gelea(uid, cur)

    if game.coins < coins:
        return False, f"Faltan monedas ({coins} necesarias)"

    if int(getattr(game, "gel_coins", 0)) < gelea:
        return False, f"Faltan monedas de gelea ({gelea} necesarias)"

    game.coins -= coins

    if getattr(game, "shop", None) is not None:
        game.shop.coins = int(game.coins)

    game.gel_coins = int(game.gel_coins) - gelea

    state.levels[uid] = cur + 1

    # si hay lugar en los engarces, queda activa de una
    if uid not in state.active and len(state.active) < ACTIVE_SLOTS:
        state.active.append(uid)

    # la compra gasta monedas y monedas de gelea: se guarda en el momento
    saver = getattr(game, "save_progress", None)

    if callable(saver):
        saver()

    return True, f"{UPGRADES[uid]['name']} nivel {cur + 1}"


# ---------------------------------------------------------------------------
# Panel (colores del HUD: grises, sin acentos amarillos)
# ---------------------------------------------------------------------------

PANEL_W = 780
PANEL_H = 612

# el marco dibujado del fondo ocupa ~19 px por lado: todo lo que va adentro
# (slots, tarjetas, textos) respeta este margen para no pisarlo
MARGIN = 36
CORNER = 60            # esquina (px del png) que no se estira

CARD_H = 130
CARD_GAP = 8           # separacion vertical entre tarjetas
CARD_COL_GAP = 14      # separacion horizontal
CARD_W = (PANEL_W - 2 * MARGIN - CARD_COL_GAP) // 2
CARDS_TOP = 148        # desde el borde de arriba del panel

# paleta tomada de hud_hotbar / hud_slot
C_PANEL = (113, 121, 130)
C_EDGE = (44, 49, 56)
C_CARD = (143, 155, 161)
C_CARD_ON = (176, 186, 192)
C_TILE = (60, 66, 74)
C_TEXT = (30, 34, 40)
C_TEXT_SOFT = (58, 64, 72)
C_LIGHT = (240, 242, 244)
C_BTN = (60, 66, 74)
C_BTN_HOT = (84, 91, 100)
C_BTN_OFF = (128, 138, 146)
C_BTN_OFF_TEXT = (176, 184, 190)
C_LACK = (140, 36, 36)      # costo que no te alcanza


class AnvilPanel:

    def __init__(self):

        self._cache = {}
        self._fonts = {}

    # ---- recursos ----

    def _font(self, size):

        f = self._fonts.get(size)

        if f is None:
            f = pygame.font.Font(None, size)
            self._fonts[size] = f

        return f

    def _image(self, path, size):

        key = (str(path), size)

        if key not in self._cache:

            img = None

            if Path(path).exists():
                img = pygame.image.load(str(path)).convert_alpha()

                if img.get_size() != tuple(size):
                    img = pygame.transform.smoothscale(img, size)

            self._cache[key] = img

        return self._cache[key]

    # ---- layout ----

    def layout(self, game):

        sw, sh = game.screen.get_size()

        panel = pygame.Rect(0, 0, PANEL_W, PANEL_H)
        panel.center = (sw // 2, sh // 2)
        panel.clamp_ip(game.screen.get_rect())

        rows = {}
        top = panel.y + CARDS_TOP

        for i, uid in enumerate(ORDER):

            col, row = i % 2, i // 2

            card = pygame.Rect(
                panel.x + MARGIN + col * (CARD_W + CARD_COL_GAP),
                top + row * (CARD_H + CARD_GAP),
                CARD_W, CARD_H,
            )

            rows[uid] = {
                "card": card,
                "buy": pygame.Rect(card.right - 104, card.bottom - 36, 96, 28),
                "use": pygame.Rect(card.right - 208, card.bottom - 36, 96, 28),
            }

        return panel, rows

    # ---- eventos ----

    def click(self, game, event):
        """Devuelve True si el click fue dentro del panel."""

        panel, rows = self.layout(game)

        if not panel.collidepoint(event.pos):
            return False

        if event.button != 1:
            return True

        for uid in ORDER:

            r = rows[uid]

            if r["buy"].collidepoint(event.pos):

                ok, msg = buy_next(game, uid)

                game.show_message(msg)

                if ok:
                    from core.audio_manager import audio
                    audio.play("buy")

                return True

            if r["use"].collidepoint(event.pos):

                ok, msg = game.anvil.toggle(uid)

                game.show_message(msg)

                return True

        return True

    # ---- dibujo ----

    def _icon(self, uid, size):
        """Icono de la mejora: tu imagen si existe, si no uno gris del HUD."""

        img = self._image(HUD_DIR / ICON_FILES[uid], (size, size))

        if img is not None:
            return img

        s = pygame.Surface((size, size), pygame.SRCALPHA)

        pygame.draw.rect(s, C_TILE, s.get_rect(), border_radius=size // 6)
        pygame.draw.rect(
            s, C_EDGE, s.get_rect(), max(1, size // 20),
            border_radius=size // 6,
        )

        letter = self._font(int(size * 0.8)).render(
            UPGRADES[uid]["name"][0], True, C_LIGHT
        )

        s.blit(letter, letter.get_rect(center=(size // 2, size // 2 + 1)))

        return s

    def _skin(self, name, size):
        """Tu imagen de assets/maps/ui/<name> escalada a `size`, o None."""

        return self._image(UI_DIR / name, tuple(size))

    def _raw(self, name):
        """Tu imagen de assets/maps/ui/<name> sin escalar, o None."""

        key = ("raw", name)

        if key not in self._cache:

            path = UI_DIR / name
            img = None

            if path.exists():
                img = pygame.image.load(str(path)).convert_alpha()

            self._cache[key] = img

        return self._cache[key]

    def _nine(self, size, name, corner):
        """Imagen en 9 partes (esquinas fijas) o None si no existe."""

        return self._panel_bg(size, name, corner)

    def _title(self, screen, panel, name):
        """Titulo hecho por vos. Devuelve False si no esta la imagen."""

        img = self._raw(name)

        if img is None:
            return False

        screen.blit(img, img.get_rect(midtop=(panel.centerx, panel.y + 14)))

        return True

    def _separator(self, screen, x1, x2, y):
        """Linea de separacion: panel_separador.png o una linea simple."""

        img = self._raw("panel_separador.png")

        if img is not None:

            w = x2 - x1

            if img.get_width() != w:
                img = pygame.transform.smoothscale(img, (w, img.get_height()))

            screen.blit(img, (x1, y - img.get_height() // 2))

        else:

            pygame.draw.line(screen, C_EDGE, (x1, y), (x2, y), 2)

    def _btn_img(self, rect, enabled, hot, prefix="panel_btn"):
        """Imagen del boton segun su estado, o None si no hay ninguna."""

        state = "_off" if not enabled else ("_hover" if hot else "")

        for pre in dict.fromkeys((prefix, "panel_btn")):

            img = self._nine(rect.size, f"{pre}{state}.png", 8)

            if img is not None:
                return img

            if state:

                base = self._nine(rect.size, f"{pre}.png", 8)

                if base is not None:

                    if not enabled:
                        base = base.copy()
                        base.set_alpha(120)

                    return base

        return None

    def _panel_bg(self, size, name="yunque_panel.png", corner=None):
        """yunque_panel.png en 9 partes: las esquinas y el borde no se
        deforman al agrandar el panel, solo se estira el centro."""

        corner = CORNER if corner is None else corner

        key = ("bg9", name, size, corner)

        if key in self._cache:
            return self._cache[key]

        path = UI_DIR / name

        if not path.exists():
            self._cache[key] = None
            return None

        src = pygame.image.load(str(path)).convert_alpha()
        sw, sh = src.get_size()
        w, h = size
        c = min(corner, sw // 2 - 1, sh // 2 - 1)

        out = pygame.Surface(size, pygame.SRCALPHA)

        xs = ((0, c, 0), (c, sw - 2 * c, c), (sw - c, c, w - c))
        ys = ((0, c, 0), (c, sh - 2 * c, c), (sh - c, c, h - c))

        for sx, swid, dx in xs:

            dw = c if swid == c else w - 2 * c

            for sy, shei, dy in ys:

                dh = c if shei == c else h - 2 * c

                part = src.subsurface((sx, sy, swid, shei))

                if (swid, shei) != (dw, dh):
                    part = pygame.transform.smoothscale(part, (dw, dh))

                out.blit(part, (dx, dy))

        self._cache[key] = out

        return out

    def _item_icon(self, item_id, size):
        """Icono de moneda/item; si falta el png dibuja una moneda simple."""

        img = self._image(HUD_DIR / f"icon_{item_id}.png", (size, size))

        if img is not None:
            return img

        key = ("coin_fallback", item_id, size)

        if key not in self._cache:

            fill = (196, 160, 118) if item_id == "moneda_gelea" else (230, 190, 70)

            s = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(s, fill, (size // 2, size // 2), size // 2 - 1)
            pygame.draw.circle(
                s, C_EDGE, (size // 2, size // 2), size // 2 - 1,
                max(1, size // 12),
            )

            self._cache[key] = s

        return self._cache[key]

    def _fit(self, text, size, color, max_w):
        """Texto que se achica solo si no entra en `max_w`."""

        while size > 13:

            surf = self._font(size).render(text, True, color)

            if surf.get_width() <= max_w:
                return surf

            size -= 1

        return self._font(13).render(text, True, color)

    def _wrap(self, text, size, color, max_w, max_lines=2):
        """Parte el texto en renglones que entran en `max_w`."""

        font = self._font(size)
        lines, cur = [], ""

        for word in text.split():

            test = (cur + " " + word).strip()

            if font.size(test)[0] <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word

        if cur:
            lines.append(cur)

        return [font.render(t, True, color) for t in lines[:max_lines]]

    def _button(self, screen, rect, text, enabled, mouse, prefix="panel_btn"):

        hot = enabled and rect.collidepoint(mouse)

        if not enabled:
            fill, ink = C_BTN_OFF, C_BTN_OFF_TEXT
        elif hot:
            fill, ink = C_BTN_HOT, C_LIGHT
        else:
            fill, ink = C_BTN, C_LIGHT

        img = self._btn_img(rect, enabled, hot, prefix)

        if img is not None:

            screen.blit(img, rect)

        else:

            pygame.draw.rect(screen, fill, rect, border_radius=6)
            pygame.draw.rect(screen, C_EDGE, rect, 2, border_radius=6)

        t = self._font(22).render(text, True, ink)

        screen.blit(t, t.get_rect(center=rect.center))

    def _cost(self, screen, game, x, cy, coins, gelea):
        """Precio como en la tienda: icono del item + cantidad."""

        have_coins = game.coins >= coins
        have_gelea = int(getattr(game, "gel_coins", 0)) >= gelea

        for item_id, amount, ok in (
            ("moneda", coins, have_coins),
            ("moneda_gelea", gelea, have_gelea),
        ):

            icon = self._item_icon(item_id, 24)

            screen.blit(icon, icon.get_rect(midleft=(x, cy)))
            x += 24 + 3

            num = self._font(24).render(
                str(amount), True, C_TEXT if ok else C_LACK
            )
            screen.blit(num, num.get_rect(midleft=(x, cy)))

            x += num.get_width() + 10

    def draw(self, game, screen):

        panel, rows = self.layout(game)

        mouse = pygame.mouse.get_pos()

        state = game.anvil

        bg = self._panel_bg(panel.size)

        if bg is not None:
            screen.blit(bg, panel)
        else:
            pygame.draw.rect(screen, C_PANEL, panel, border_radius=16)
            pygame.draw.rect(screen, C_EDGE, panel, 4, border_radius=16)

        if not self._title(screen, panel, "yunque_titulo.png"):

            title = self._font(52).render("Yunque", True, C_LIGHT)
            screen.blit(
                title, title.get_rect(midtop=(panel.centerx, panel.y + 26))
            )

        # engarces activos
        sub_text = "Engarces activos"

        if not torch_equipped(game):
            sub_text += "  ·  solo funcionan con la antorcha equipada"

        sub = self._font(23).render(sub_text, True, C_LIGHT)
        screen.blit(sub, (panel.x + MARGIN, panel.y + 80))

        for i in range(ACTIVE_SLOTS):

            slot = pygame.Rect(panel.x + MARGIN + i * 64, panel.y + 104, 56, 36)

            slot_img = self._nine(slot.size, "yunque_engarce.png", 8)

            if slot_img is not None:

                screen.blit(slot_img, slot)

            else:

                pygame.draw.rect(screen, C_TILE, slot, border_radius=8)
                pygame.draw.rect(screen, C_LIGHT, slot, 2, border_radius=8)

            if i < len(state.active):

                icon = self._icon(state.active[i], 30)
                screen.blit(icon, icon.get_rect(center=slot.center))

        # monedas y geleas: icono del item + numero, sin badge
        right = panel.right - MARGIN
        cy = panel.y + 122

        for item_id, value in (
            ("moneda_gelea", int(getattr(game, "gel_coins", 0))),
            ("moneda", int(game.coins)),
        ):

            num = self._font(30).render(str(value), True, C_LIGHT)
            num_rect = num.get_rect(midright=(right, cy))
            screen.blit(num, num_rect)

            left = num_rect.left

            icon = self._item_icon(item_id, 38)

            icon_rect = icon.get_rect(midright=(num_rect.left - 6, cy))
            screen.blit(icon, icon_rect)
            left = icon_rect.left

            right = left - 22

        # tarjetas
        for uid in ORDER:

            r = rows[uid]
            card = r["card"]
            info = UPGRADES[uid]
            cur = state.levels[uid]
            on = uid in state.active

            card_img = self._nine(
                card.size,
                "yunque_tarjeta_activa.png" if on else "yunque_tarjeta.png",
                16,
            )

            if card_img is None and on:
                card_img = self._nine(card.size, "yunque_tarjeta.png", 16)

            if card_img is not None:

                screen.blit(card_img, card)

            else:

                pygame.draw.rect(
                    screen, C_CARD_ON if on else C_CARD, card, border_radius=10
                )
                pygame.draw.rect(
                    screen, C_LIGHT if on else C_EDGE, card,
                    3 if on else 2, border_radius=10,
                )

            icon = self._icon(uid, 56)
            screen.blit(icon, (card.x + 10, card.y + 10))

            name = self._font(30).render(info["name"], True, C_TEXT)
            screen.blit(name, (card.x + 76, card.y + 10))

            # puntitos de nivel
            for n in range(MAX_LEVEL):

                pip = pygame.Rect(card.right - 74 + n * 22, card.y + 14, 16, 16)

                pip_img = self._skin(
                    "yunque_pip_lleno.png" if n < cur else "yunque_pip.png",
                    pip.size,
                )

                if pip_img is not None:

                    screen.blit(pip_img, pip)

                else:

                    pygame.draw.rect(
                        screen, C_TILE if n < cur else C_CARD_ON,
                        pip, border_radius=4,
                    )
                    pygame.draw.rect(screen, C_EDGE, pip, 2, border_radius=4)

            text_w = card.w - 88

            line = self._fit(
                info["desc"][max(cur, 1) - 1], 21,
                C_TEXT if cur > 0 else C_TEXT_SOFT, text_w,
            )
            screen.blit(line, (card.x + 76, card.y + 44))

            y = card.y + 64

            for surf in self._wrap(info["note"], 17, C_TEXT_SOFT, text_w, 2):
                screen.blit(surf, (card.x + 76, y))
                y += 15

            # botones
            if cur >= MAX_LEVEL:
                self._button(screen, r["buy"], "Máximo", False, mouse)
            else:
                self._button(screen, r["buy"], "Mejorar", True, mouse)

                self._cost(
                    screen, game, card.x + 12, card.bottom - 22,
                    cost_coins(uid, cur), cost_gelea(uid, cur),
                )

            if cur > 0:
                self._button(
                    screen, r["use"], "Quitar" if on else "Activar",
                    True, mouse,
                )

        hint = self._font(22).render(
            "ESC para cerrar  ·  3 mejoras activas a la vez", True, C_LIGHT
        )
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 38)))