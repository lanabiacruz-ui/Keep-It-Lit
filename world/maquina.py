"""Maquina de gelea: convierte geleas en monedas de gelea con el tiempo.

Como funciona:
  * Se compra en la tienda (Construccion), se coloca como el cofre o el
    yunque, se recoge con el martillo (solo si esta vacia) y se puede tirar
    al tacho como cualquier item.
  * Click derecho sobre ella para abrirla. Ahi pones geleas de tu hotbar;
    la maquina trabaja SOLA mientras jugas: cada GEL_PER_COIN geleas tardan
    SECONDS_PER_COIN segundos en volverse 1 moneda de gelea.
  * Las monedas listas se cobran desde el panel (boton "Cobrar"). La moneda
    de gelea es una moneda propia (game.gel_coins, se guarda en el save con
    la clave "gel_coins") y es lo que pide el yunque para las mejoras.

Imagenes (todas opcionales, si no estan se dibuja con codigo):
  assets/maps/hud/icon_maquina.png          64x64   (item + dibujo en el mapa)
  assets/maps/hud/icon_moneda_gelea.png     64x64   (la moneda de gelea)
  assets/maps/hud/hud_monedas_gelea.png     110x60  (contador del HUD)
  assets/maps/ui/maquina_panel.png          cualquier tamano (fondo del panel,
                                            se estira en 9 partes)
"""

import pygame

from world.items import HUD_DIR
from world.yunque import (
    AnvilPanel, MARGIN,
    C_PANEL, C_EDGE, C_TILE, C_LIGHT,
    count_item, take_items,
)

# ---------------------------------------------------------------------------
# Numeros de balance (todo se cambia aca)
# ---------------------------------------------------------------------------

GEL_PER_COIN = 2          # geleas que se gastan por cada moneda de gelea
SECONDS_PER_COIN = 30.0   # segundos que tarda cada moneda
MAX_GEL = 10              # geleas que caben adentro (= 5 monedas por tanda)
MAX_READY = 20            # monedas listas que puede guardar sin cobrar

GEL_ITEM = "gelea"


def fmt_time(seconds):

    seconds = max(0, int(round(seconds)))

    return f"{seconds // 60}:{seconds % 60:02d}" if seconds >= 60 else f"{seconds} s"


# ---------------------------------------------------------------------------
# Estado de una maquina (vive en el objeto colocado)
# ---------------------------------------------------------------------------

class MachineState:

    def __init__(self):

        self.gel = 0          # geleas adentro, esperando
        self.prog = 0.0       # segundos de la moneda que se esta haciendo
        self.ready = 0        # monedas de gelea listas para cobrar

    @property
    def working(self):

        return self.gel >= GEL_PER_COIN and self.ready < MAX_READY

    @property
    def empty(self):

        return self.gel <= 0 and self.ready <= 0

    def tick(self, dt):

        if self.working:

            self.prog += dt

            while (
                self.prog >= SECONDS_PER_COIN
                and self.gel >= GEL_PER_COIN
                and self.ready < MAX_READY
            ):
                self.prog -= SECONDS_PER_COIN
                self.gel -= GEL_PER_COIN
                self.ready += 1

        if self.gel < GEL_PER_COIN:
            self.prog = 0.0

    def time_left(self):
        """Segundos hasta tener todas las monedas (None si no trabaja)."""

        if not self.working:
            return None

        coins = self.gel // GEL_PER_COIN

        return (SECONDS_PER_COIN - self.prog) + (coins - 1) * SECONDS_PER_COIN

    def save(self):

        return {
            "gel": int(self.gel),
            "prog": round(float(self.prog), 2),
            "ready": int(self.ready),
        }

    def load(self, data):

        if not isinstance(data, dict):
            return

        try:
            self.gel = max(0, min(MAX_GEL, int(data.get("gel", 0))))
            self.ready = max(0, min(MAX_READY, int(data.get("ready", 0))))
            self.prog = max(
                0.0, min(SECONDS_PER_COIN, float(data.get("prog", 0.0)))
            )
        except (TypeError, ValueError):
            self.gel = self.ready = 0
            self.prog = 0.0


# ---------------------------------------------------------------------------
# Acciones (devuelven (ok, mensaje))
# ---------------------------------------------------------------------------

def put_geleas(game, state, n):
    """Pasa hasta `n` geleas de la hotbar a la maquina."""

    room = MAX_GEL - state.gel

    if room <= 0:
        return False, "La máquina está llena"

    have = count_item(game, GEL_ITEM)

    if have <= 0:
        return False, "No tienes geleas en tu hotbar"

    n = min(n, room, have)

    take_items(game, GEL_ITEM, n)

    state.gel += n

    return True, f"Pusiste {n} gelea{'s' if n != 1 else ''} en la máquina"


def take_back(game, state):
    """Devuelve a la hotbar las geleas que todavia no se usaron."""

    if state.gel <= 0:
        return False, "No hay geleas adentro"

    given = 0

    while given < state.gel:

        slot = game._free_slot_for(GEL_ITEM)

        if slot is None:
            break

        if game.hud.items[slot] is None:
            game.hud.items[slot] = GEL_ITEM
            game.hud.counts[slot] = 1
        else:
            game.hud.counts[slot] += 1

        given += 1

    if given == 0:
        return False, "Inventario lleno"

    state.gel -= given

    if state.gel < GEL_PER_COIN:
        state.prog = 0.0

    return True, f"Sacaste {given} gelea{'s' if given != 1 else ''}"


def collect(game, state):
    """Cobra las monedas de gelea listas."""

    n = state.ready

    if n <= 0:
        return False, "Todavía no hay monedas listas"

    game.gel_coins = int(getattr(game, "gel_coins", 0)) + n

    state.ready = 0

    return True, f"+{n} moneda{'s' if n != 1 else ''} de gelea"


# ---------------------------------------------------------------------------
# Panel (mismo estilo gris que el del yunque)
# ---------------------------------------------------------------------------

PANEL_W = 520
PANEL_H = 360

PANEL_FILE = "maquina_panel.png"


class MachinePanel(AnvilPanel):

    # ---- layout ----

    def layout(self, game):

        sw, sh = game.screen.get_size()

        panel = pygame.Rect(0, 0, PANEL_W, PANEL_H)
        panel.center = (sw // 2, sh // 2)
        panel.clamp_ip(game.screen.get_rect())

        inner_w = PANEL_W - 2 * MARGIN

        gap = 6
        size = min(36, (inner_w - gap * (MAX_GEL - 1)) // MAX_GEL)
        total = MAX_GEL * size + (MAX_GEL - 1) * gap
        x0 = panel.x + MARGIN + (inner_w - total) // 2

        slots = [
            pygame.Rect(x0 + i * (size + gap), panel.y + 134, size, size)
            for i in range(MAX_GEL)
        ]

        bar = pygame.Rect(panel.x + MARGIN, panel.y + 186, inner_w, 26)

        collect_btn = pygame.Rect(
            panel.right - MARGIN - 132, panel.y + 226, 132, 38
        )

        bw = 132
        bgap = (inner_w - 3 * bw) // 2
        by = panel.y + 284

        return {
            "panel": panel,
            "slots": slots,
            "bar": bar,
            "collect": collect_btn,
            "put1": pygame.Rect(panel.x + MARGIN, by, bw, 36),
            "putall": pygame.Rect(panel.x + MARGIN + bw + bgap, by, bw, 36),
            "take": pygame.Rect(panel.x + MARGIN + 2 * (bw + bgap), by, bw, 36),
        }

    # ---- eventos ----

    def click(self, game, event, obj):
        """Devuelve True si el click fue dentro del panel."""

        lay = self.layout(game)

        if not lay["panel"].collidepoint(event.pos):
            return False

        if event.button != 1:
            return True

        state = obj.m

        action = None
        sound = "pickup"

        if lay["put1"].collidepoint(event.pos):
            action = lambda: put_geleas(game, state, 1)
        elif lay["putall"].collidepoint(event.pos):
            action = lambda: put_geleas(game, state, MAX_GEL)
        elif lay["take"].collidepoint(event.pos):
            action = lambda: take_back(game, state)
        elif lay["collect"].collidepoint(event.pos):
            action = lambda: collect(game, state)
            sound = "coin"

        if action is not None:

            ok, msg = action()

            game.show_message(msg)

            if ok:
                from core.audio_manager import audio
                audio.play(sound)

        return True

    # ---- dibujo ----

    def draw(self, game, screen, obj):

        lay = self.layout(game)
        panel = lay["panel"]
        state = obj.m

        mouse = pygame.mouse.get_pos()

        bg = self._panel_bg(panel.size, PANEL_FILE)

        if bg is not None:
            screen.blit(bg, panel)
        else:
            pygame.draw.rect(screen, C_PANEL, panel, border_radius=16)
            pygame.draw.rect(screen, C_EDGE, panel, 4, border_radius=16)

        title = self._font(52).render("Máquina", True, C_LIGHT)
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 26)))

        sub = self._font(23).render(
            f"{GEL_PER_COIN} geleas = 1 moneda de gelea  ·  "
            f"{int(SECONDS_PER_COIN)} s cada una",
            True, C_LIGHT,
        )
        screen.blit(sub, sub.get_rect(midtop=(panel.centerx, panel.y + 78)))

        # geleas adentro (izquierda) y geleas en tu hotbar (derecha)
        label = self._font(24).render(
            f"Geleas adentro  {state.gel}/{MAX_GEL}", True, C_LIGHT
        )
        screen.blit(label, (panel.x + MARGIN, panel.y + 106))

        hotbar = self._font(26).render(
            str(count_item(game, GEL_ITEM)), True, C_LIGHT
        )
        hb_rect = hotbar.get_rect(
            midright=(panel.right - MARGIN, panel.y + 116)
        )
        screen.blit(hotbar, hb_rect)

        gel = self._item_icon(GEL_ITEM, 26)
        screen.blit(gel, gel.get_rect(midright=(hb_rect.left - 4, hb_rect.centery)))

        # casilleros de la cola
        icon_size = max(8, lay["slots"][0].w - 8)

        for i, slot in enumerate(lay["slots"]):

            pygame.draw.rect(screen, C_TILE, slot, border_radius=8)
            pygame.draw.rect(screen, C_LIGHT, slot, 2, border_radius=8)

            if i < state.gel:

                icon = self._item_icon(GEL_ITEM, icon_size)
                screen.blit(icon, icon.get_rect(center=slot.center))

        # barra de progreso
        bar = lay["bar"]

        pygame.draw.rect(screen, C_TILE, bar, border_radius=8)

        if state.working:
            frac = state.prog / SECONDS_PER_COIN
        else:
            frac = 0.0

        if frac > 0:

            fill = bar.copy()
            fill.w = max(10, int(bar.w * frac))

            pygame.draw.rect(screen, (176, 186, 192), fill, border_radius=8)

        pygame.draw.rect(screen, C_EDGE, bar, 2, border_radius=8)

        if state.ready >= MAX_READY:
            status = "Llena de monedas: cóbralas"
        elif state.working:
            status = (
                f"Fabricando moneda… {fmt_time(SECONDS_PER_COIN - state.prog)}"
                f"  ·  todo en {fmt_time(state.time_left())}"
            )
        elif state.gel == 1:
            status = f"Necesita {GEL_PER_COIN} geleas para fabricar"
        else:
            status = "Sin geleas"

        text = self._fit(status, 22, C_LIGHT, bar.w - 16)
        shade = self._fit(status, 22, (0, 0, 0), bar.w - 16)

        screen.blit(shade, shade.get_rect(center=(bar.centerx + 1, bar.centery + 1)))
        screen.blit(text, text.get_rect(center=bar.center))

        # monedas listas
        cy = lay["collect"].centery

        ready_label = self._font(26).render("Listas:", True, C_LIGHT)
        r1 = ready_label.get_rect(midleft=(panel.x + MARGIN, cy))
        screen.blit(ready_label, r1)

        coin = self._item_icon("moneda_gelea", 34)
        r2 = coin.get_rect(midleft=(r1.right + 10, cy))
        screen.blit(coin, r2)

        amount = self._font(38).render(f"x{state.ready}", True, C_LIGHT)
        screen.blit(amount, amount.get_rect(midleft=(r2.right + 8, cy)))

        # botones
        have = count_item(game, GEL_ITEM)
        can_put = state.gel < MAX_GEL and have > 0

        self._button(screen, lay["collect"], "Cobrar", state.ready > 0, mouse)
        self._button(screen, lay["put1"], "Poner 1", can_put, mouse)
        self._button(screen, lay["putall"], "Poner todas", can_put, mouse)
        self._button(screen, lay["take"], "Sacar", state.gel > 0, mouse)

        hint = self._font(22).render(
            "ESC para cerrar  ·  trabaja sola mientras juegas", True, C_LIGHT
        )
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 38)))