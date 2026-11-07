"""Yunque: mejoras (engarces) para la antorcha.

Como funciona:
  * El yunque se compra en la tienda (Construccion), se coloca como el
    cofre, se recoge con el martillo y se abre con click derecho.
    No abre si hay enemigos cerca (se usa entre oleadas).
  * Hay 6 mejoras de 3 niveles. Se compran con monedas + gelea.
  * Solo 3 mejoras (engarces) funcionan a la vez; se cambian gratis cada
    vez que abris el yunque.
  * Las mejoras son SOLO para la antorcha y duran la partida (se guardan en
    el save con la clave "yunque" y se pierden si se borra la partida).

Imagenes (todas opcionales, si no estan se dibujan con codigo):
  assets/maps/hud/icon_yunque.png            64x64   (item + dibujo en el mapa)
  assets/maps/ui/yunque_panel.png            740x596 (fondo del panel)
  assets/maps/hud/yunque_resistencia.png     64x64   \
  assets/maps/hud/yunque_brasas.png          64x64    |
  assets/maps/hud/yunque_repelente.png       64x64    |  iconos de cada mejora
  assets/maps/hud/yunque_llama_amplia.png    64x64    |
  assets/maps/hud/yunque_llama_larga.png     64x64    |
  assets/maps/hud/yunque_manos.png           64x64   /
"""

from pathlib import Path

import pygame

from world.items import HUD_DIR

UI_DIR = HUD_DIR.parent / "ui"

BADGE_FILE = HUD_DIR.parent / "tienda" / "tienda_badge.png"

TORCH = "antorcha"

ACTIVE_SLOTS = 3
MAX_LEVEL = 3

# distancia (px) a la que un enemigo vivo impide abrir el yunque
ENEMY_NEAR = 420

# ---------------------------------------------------------------------------
# Numeros de balance (todo se cambia aca)
# ---------------------------------------------------------------------------

COSTS_COINS = (60, 110, 180)
COSTS_GELEA = (3, 5, 8)

# Resistencia cuesta distinto: 80 / 140 / 220 monedas y una gelea mas por nivel
RESIST_COINS = (80, 140, 220)
RESIST_GELEA = (4, 6, 9)

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

    if count_item(game, "gelea") < gelea:
        return False, f"Faltan geleas ({gelea} necesarias, en tu hotbar)"

    game.coins -= coins

    if getattr(game, "shop", None) is not None:
        game.shop.coins = int(game.coins)

    take_items(game, "gelea", gelea)

    state.levels[uid] = cur + 1

    # si hay lugar en los engarces, queda activa de una
    if uid not in state.active and len(state.active) < ACTIVE_SLOTS:
        state.active.append(uid)

    return True, f"{UPGRADES[uid]['name']} nivel {cur + 1}"


# ---------------------------------------------------------------------------
# Panel (colores del HUD: grises, sin acentos amarillos)
# ---------------------------------------------------------------------------

PANEL_W = 740
PANEL_H = 584

CARD_W = 344
CARD_H = 130
CARD_GAP = 8

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
        top = panel.y + 134

        for i, uid in enumerate(ORDER):

            col, row = i % 2, i // 2

            card = pygame.Rect(
                panel.x + 20 + col * (CARD_W + 12),
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

    def _badge(self, width, height):
        """tienda_badge.png estirado al ancho pedido (extremos sin deformar)."""

        key = ("badge", width, height)

        if key in self._cache:
            return self._cache[key]

        if BADGE_FILE.exists():

            base = pygame.image.load(str(BADGE_FILE)).convert_alpha()
            bw, bh = base.get_size()
            cap = max(1, bw // 3)
            k = height / bh
            cap_px = max(1, int(cap * k))

            left = pygame.transform.scale(
                base.subsurface((0, 0, cap, bh)), (cap_px, height)
            )
            right = pygame.transform.scale(
                base.subsurface((bw - cap, 0, cap, bh)), (cap_px, height)
            )
            mid = pygame.transform.scale(
                base.subsurface((cap, 0, bw - 2 * cap, bh)),
                (max(1, width - 2 * cap_px), height),
            )

            img = pygame.Surface((width, height), pygame.SRCALPHA)
            img.blit(left, (0, 0))
            img.blit(mid, (cap_px, 0))
            img.blit(right, (width - cap_px, 0))

        else:

            img = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(img, C_TILE, img.get_rect(), border_radius=height // 2)
            pygame.draw.rect(
                img, C_LIGHT, img.get_rect(), 2, border_radius=height // 2
            )

        self._cache[key] = img

        return img

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

    def _button(self, screen, rect, text, enabled, mouse):

        if not enabled:
            fill, ink = C_BTN_OFF, C_BTN_OFF_TEXT
        elif rect.collidepoint(mouse):
            fill, ink = C_BTN_HOT, C_LIGHT
        else:
            fill, ink = C_BTN, C_LIGHT

        pygame.draw.rect(screen, fill, rect, border_radius=6)
        pygame.draw.rect(screen, C_EDGE, rect, 2, border_radius=6)

        t = self._font(22).render(text, True, ink)

        screen.blit(t, t.get_rect(center=rect.center))

    def draw(self, game, screen):

        panel, rows = self.layout(game)

        mouse = pygame.mouse.get_pos()

        state = game.anvil

        bg = self._image(UI_DIR / "yunque_panel.png", panel.size)

        if bg is not None:
            screen.blit(bg, panel)
        else:
            pygame.draw.rect(screen, C_PANEL, panel, border_radius=16)
            pygame.draw.rect(screen, C_EDGE, panel, 4, border_radius=16)

        title = self._font(52).render("Yunque", True, C_LIGHT)
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 14)))

        # engarces activos
        sub_text = "Engarces activos"

        if not torch_equipped(game):
            sub_text += "  ·  solo funcionan con la antorcha equipada"

        sub = self._font(23).render(sub_text, True, C_LIGHT)
        screen.blit(sub, (panel.x + 24, panel.y + 66))

        for i in range(ACTIVE_SLOTS):

            slot = pygame.Rect(panel.x + 24 + i * 64, panel.y + 92, 56, 36)

            pygame.draw.rect(screen, C_TILE, slot, border_radius=8)
            pygame.draw.rect(screen, C_LIGHT, slot, 2, border_radius=8)

            if i < len(state.active):

                icon = self._icon(state.active[i], 30)
                screen.blit(icon, icon.get_rect(center=slot.center))

        # monedas (badge de la tienda) y geleas (icono del item)
        right = panel.right - 24
        cy = panel.y + 110

        n_gel = self._font(30).render(str(count_item(game, "gelea")), True, C_LIGHT)
        screen.blit(n_gel, n_gel.get_rect(midright=(right, cy)))

        gel = self._image(HUD_DIR / "icon_gelea.png", (40, 40))

        if gel is not None:
            screen.blit(gel, gel.get_rect(midright=(n_gel.get_rect(midright=(right, cy)).left - 6, cy)))
            gel_left = n_gel.get_rect(midright=(right, cy)).left - 6 - 40
        else:
            gel_left = n_gel.get_rect(midright=(right, cy)).left

        amount = self._font(30).render(str(int(game.coins)), True, (30, 18, 8))
        bw = amount.get_width() + 34
        badge = self._badge(bw, 34)
        coin_right = gel_left - 22

        badge_rect = badge.get_rect(midright=(coin_right, cy))
        screen.blit(badge, badge_rect)
        screen.blit(amount, amount.get_rect(center=badge_rect.center))

        coin = self._image(HUD_DIR / "icon_moneda.png", (34, 34))

        if coin is not None:
            screen.blit(coin, coin.get_rect(midright=(badge_rect.left - 4, cy)))

        # tarjetas
        for uid in ORDER:

            r = rows[uid]
            card = r["card"]
            info = UPGRADES[uid]
            cur = state.levels[uid]
            on = uid in state.active

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

                cost = self._font(18).render(
                    f"{cost_coins(uid, cur)} mon + {cost_gelea(uid, cur)} gel",
                    True, C_TEXT,
                )
                screen.blit(cost, (card.x + 12, card.bottom - 31))

            if cur > 0:
                self._button(
                    screen, r["use"], "Quitar" if on else "Activar",
                    True, mouse,
                )

        hint = self._font(22).render(
            "ESC para cerrar  ·  3 mejoras activas a la vez", True, C_LIGHT
        )
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 22)))