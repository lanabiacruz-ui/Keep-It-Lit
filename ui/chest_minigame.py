import random
from pathlib import Path

import pygame


MG_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "minijuego"
)

# ---------------------------------------------------------------
# Dificultad
# ---------------------------------------------------------------

# Aciertos para abrir el cofre
HITS_NEEDED = 3

# Ancho de la zona (en px) segun cuantos aciertos llevas.
# La primera es el ancho real del PNG (140).
ZONE_WIDTHS = [140, 98, 62]

# Velocidad del marcador (px por segundo) segun cuantos aciertos llevas
SPEEDS = [300, 460, 680]

# Despues de abrirse, se ignoran los golpes un ratito para que el
# mismo click que le pego al cofre no cuente como acierto
INPUT_GRACE = 0.4

# Cuanto se queda la pestana al ganar / perder antes de cerrarse
END_DELAY = 0.55

# ---------------------------------------------------------------
# Posiciones dentro del panel (640x200)
# ---------------------------------------------------------------
BARRA_POS = (40, 40)       # barra de 560x44
BARRA_W = 560
BARRA_H = 44
BARRA_MARGIN = 16          # lo que sobra a los costados de la barra

PROGRESO_POS = (120, 122)  # barra de progreso de 400x32

HINT_Y = 172


def _load(name):

    return pygame.image.load(str(MG_DIR / name)).convert_alpha()


class ChestMinigame:
    """Frena el marcador dentro de la zona. 3 aciertos = cofre abierto.
    Si fallas una vez, se cierra.

    Controles: Espacio, E o click izquierdo = golpear. Esc = salir."""

    def __init__(self, screen_size):

        self.screen_w, self.screen_h = screen_size

        self.panel = _load("minijuego_panel.png")
        self.barra = _load("minijuego_barra.png")
        self.zona = _load("minijuego_zona.png")
        self.marcador = _load("minijuego_marcador.png")
        self.progreso = _load("minijuego_progreso.png")
        self.relleno = _load("minijuego_progreso_relleno.png")

        # Marcador en rojo para cuando fallas
        self.marcador_fallo = self.marcador.copy()
        self.marcador_fallo.fill(
            (150, 0, 0, 0), special_flags=pygame.BLEND_RGB_ADD
        )

        # Zona con brillo verde para cuando aciertas
        self.zona_ok = self.zona.copy()
        self.zona_ok.fill(
            (0, 90, 0, 0), special_flags=pygame.BLEND_RGB_ADD
        )

        # Parte del PNG de relleno que tiene dibujo (para cortarlo bien)
        self.relleno_bbox = self.relleno.get_bounding_rect()

        self._zone_cache = {}

        self.panel_rect = self.panel.get_rect(
            center=(self.screen_w // 2, self.screen_h // 2 - 40)
        )

        self.dim = pygame.Surface(
            (self.screen_w, self.screen_h), pygame.SRCALPHA
        )
        self.dim.fill((0, 0, 0, 150))

        self.font = pygame.font.Font(None, 26)

        # Zona donde se mueve el marcador (px dentro de la barra)
        self.length = BARRA_W - BARRA_MARGIN * 2

        self.pos = 0.0
        self.direction = 1
        self.hits = 0

        self.zone_x = 0.0
        self.zone_w = ZONE_WIDTHS[0]

        self.state = "play"       # "play" -> "win" / "fail"
        self.end_timer = 0.0
        self.grace = INPUT_GRACE
        self.flash = 0.0

        self._new_zone()

    # ---------- logica ----------

    def _new_zone(self):

        self.zone_w = ZONE_WIDTHS[min(self.hits, len(ZONE_WIDTHS) - 1)]

        room = self.length - self.zone_w

        # Que no aparezca justo debajo del marcador
        for _ in range(12):

            x = random.uniform(0, room)

            center = x + self.zone_w / 2

            if abs(center - self.pos) > 150:
                break

        self.zone_x = x

    @property
    def speed(self):

        return SPEEDS[min(self.hits, len(SPEEDS) - 1)]

    def hit(self):

        if self.state != "play" or self.grace > 0:
            return

        if self.zone_x <= self.pos <= self.zone_x + self.zone_w:

            self.hits += 1
            self.flash = 0.18

            if self.hits >= HITS_NEEDED:

                self.state = "win"
                self.end_timer = END_DELAY

            else:

                self._new_zone()

        else:

            self.state = "fail"
            self.end_timer = END_DELAY

    def handle_event(self, event):
        """Devuelve 'cancel' si el jugador sale con Esc."""

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                return "cancel"

            if event.key in (pygame.K_SPACE, pygame.K_e):
                self.hit()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            self.hit()

        return None

    def update(self, dt):
        """Devuelve 'win' o 'fail' cuando termina, si no None."""

        if self.grace > 0:
            self.grace = max(0.0, self.grace - dt)

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.state == "play":

            self.pos += self.direction * self.speed * dt

            if self.pos >= self.length:
                self.pos = self.length
                self.direction = -1

            elif self.pos <= 0:
                self.pos = 0
                self.direction = 1

            return None

        self.end_timer -= dt

        if self.end_timer <= 0:
            return self.state

        return None

    # ---------- dibujo ----------

    def _zone_image(self, width):

        if width not in self._zone_cache:

            self._zone_cache[width] = (
                pygame.transform.smoothscale(
                    self.zona, (width, self.zona.get_height())
                ),
                pygame.transform.smoothscale(
                    self.zona_ok, (width, self.zona_ok.get_height())
                ),
            )

        return self._zone_cache[width]

    def _text(self, screen, text, center, color=(235, 228, 205)):

        shadow = self.font.render(text, True, (0, 0, 0))
        label = self.font.render(text, True, color)

        rect = label.get_rect(center=center)

        screen.blit(shadow, rect.move(2, 2))
        screen.blit(label, rect)

    def draw(self, screen):

        screen.blit(self.dim, (0, 0))

        ox, oy = self.panel_rect.topleft

        screen.blit(self.panel, self.panel_rect)

        # Barra
        barra_x = ox + BARRA_POS[0]
        barra_y = oy + BARRA_POS[1]

        screen.blit(self.barra, (barra_x, barra_y))

        play_left = barra_x + BARRA_MARGIN

        # Zona
        zone_img, zone_ok_img = self._zone_image(self.zone_w)

        screen.blit(
            zone_ok_img if self.flash > 0 else zone_img,
            (play_left + round(self.zone_x), barra_y)
        )

        # Marcador (sobresale de la barra, centrado)
        marker = (
            self.marcador_fallo if self.state == "fail" else self.marcador
        )

        marker_rect = marker.get_rect(
            center=(
                play_left + round(self.pos),
                barra_y + BARRA_H // 2
            )
        )

        screen.blit(marker, marker_rect)

        # Progreso: el relleno se corta segun los aciertos
        prog_x = ox + PROGRESO_POS[0]
        prog_y = oy + PROGRESO_POS[1]

        screen.blit(self.progreso, (prog_x, prog_y))

        if self.hits > 0:

            bb = self.relleno_bbox

            width = bb.x + round(bb.width * self.hits / HITS_NEEDED)
            width = max(1, min(width, self.relleno.get_width()))

            crop = self.relleno.subsurface(
                pygame.Rect(0, 0, width, self.relleno.get_height())
            )

            screen.blit(crop, (prog_x, prog_y))

        # Texto de ayuda
        if self.state == "fail":
            hint = "Fallaste: el cofre se cerro"
        elif self.state == "win":
            hint = "Cofre abierto"
        else:
            hint = "Espacio, E o click para golpear   -   Esc para salir"

        self._text(
            screen,
            hint,
            (self.panel_rect.centerx, oy + HINT_Y)
        )