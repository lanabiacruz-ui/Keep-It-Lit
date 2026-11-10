import json
from pathlib import Path

import pygame

from core.fonts import load_font
from core import accessibility
from core.audio_manager import audio
from core.controls import controls, GROUPS
from core.music_manager import music
from ui import room_light

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "assets" / "maps" / "ui"
SETTINGS_PATH = ROOT / "data" / "settings.json"

DEFAULT_SETTINGS = {
    "music_volume": 0.7,
    "sfx_volume": 0.7,
    "fullscreen": False,
}


def _clamp01(value, default):

    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _read_file():

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except (OSError, ValueError, UnicodeDecodeError):
        pass

    return {}


def load_settings():
    data = _read_file()
    
    settings = dict(data)

    settings["music_volume"] = _clamp01(
        data.get("music_volume"), DEFAULT_SETTINGS["music_volume"]
    )

    settings["sfx_volume"] = _clamp01(
        data.get("sfx_volume"), DEFAULT_SETTINGS["sfx_volume"]
    )

    settings["fullscreen"] = bool(
        data.get("fullscreen", DEFAULT_SETTINGS["fullscreen"])
    )

    return settings


def save_settings(**changes):
    data = _read_file()

    data.update(changes)

    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    except OSError:
        return False

    return True


class Settings:

    IMG_W = 1672
    IMG_H = 941

    CLOSE_BOX = (1179, 219, 1204, 246)

    LEFT = 508
    RIGHT = 1188

    ROW_Y = (302, 342, 382, 422, 462, 502)
    LABEL_X = 512
    TRACK_X = 730
    TRACK_W = 330
    VALUE_X = 1084
    TOGGLE_SIZE = (68, 34)
    CONTROLS_BTN = (160, 34)

    # Fila -> (x del texto, x del control, y centro, x del valor en %)
    ROWS = {
        "music": (512, 730, 302, 1084),
        "sfx": (512, 730, 342, 1084),
        "fullscreen": (512, 730, 382, None),
        "flash": (512, 730, 422, None),
        "hints": (512, 730, 462, None),
        "fps": (512, 730, 502, None),
    }
    CONTROLS_POS = (1028, 382)      # esquina izquierda x, centro y
    GUIDE_POS = (1028, 422)
    GUIDE_X1 = 508
    GUIDE_X2 = 1188
    GUIDE_TAB_Y = 300
    GUIDE_TAB_H = 24
    GUIDE_TOP = 324
    GUIDE_ROW_H = 70
    GUIDE_KEY_W = 124
    GUIDE_CHIP_H = 19
    GUIDE_GAP = 12
    GUIDE_TAB_NAMES = (
        "Movimiento",
        "Acciones",
        "Inventario",
        "Combos",
        "Mouse",
        "Menús",
    )
    GOLD = (255, 226, 150)
    FONT_SIZE = 34
    SMALL_FONT_SIZE = 23
    NAV_CX = None                   # None = centro de LEFT..RIGHT

    # La tablet de la pausa es mas baja que la compu y las manos tapan el
    # borde de abajo: el area libre es x 490-1200, y 290-455 (y el hueco
    # entre las manos). Por eso va en DOS columnas y el boton "Controles"
    # queda en el hueco de las manos.
    TABLET_LAYOUT = {
        "ROWS": {
            "music": (500, 606, 312, 806),
            "sfx": (500, 606, 356, 806),
            "flash": (500, 606, 400, None),
            "fullscreen": (888, 1110, 312, None),
            "hints": (888, 1110, 356, None),
            "fps": (888, 1110, 400, None),
        },
        "TRACK_W": 190,
        "TOGGLE_SIZE": (72, 36),
        "CONTROLS_BTN": (170, 38),
        "CONTROLS_POS": (660, 446),
        "GUIDE_POS": (846, 446),
        "GUIDE_X1": 496,
        "GUIDE_X2": 1196,
        "GUIDE_TAB_Y": 297,
        "GUIDE_TAB_H": 24,
        "GUIDE_TOP": 316,
        "GUIDE_ROW_H": 66,
        "FONT_SIZE": 30,
        "SMALL_FONT_SIZE": 21,
        # vista de teclas
        "TOP_Y": 292,
        "GROUP_Y": 318,
        "KEY_TOP": 332,
        "KEY_STEP": 21,
        "KEY_SIZE": (78, 18),
        "NAV_Y": 486,
        "NAV_CX": 872,
    }

    TOP_Y = 302
    NAV_BTN = (118, 32)
    NAV_Y = 487
    NAV_GAP = 24
    COL_X = (508, 736, 964)
    COL_W = 216
    # 6 filas por columna (Inventario tiene 6): el paso y el alto de las
    # teclas son chicos para que la ultima fila termine antes de los botones
    # Regresar / Restablecer (NAV_Y).
    GROUP_Y = 332
    KEY_TOP = 344
    KEY_STEP = 20
    KEY_SIZE = (78, 19)

    TEXT = (244, 248, 255)
    TEXT_DIM = (176, 198, 232)
    ACCENT = (140, 200, 255)
    FILL = (30, 84, 196)
    SHADOW = (14, 26, 58)

    def __init__(
        self,
        screen,
        background="mapaajustes.png",
        controls_background=None
    ):

        self.screen = screen
        self.width, self.height = screen.get_size()

        self.tablet = str(background).startswith("tablet")

        if self.tablet:
            for key, value in self.TABLET_LAYOUT.items():
                setattr(self, key, value)

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        self.view = "main"
        self.guide_page = 0
        self.font_cache = {}

        self.listening = None
        self.dragging = None
        self.message = ""
        self.message_timer = 0.0

        self.hover = None

        values = load_settings()

        self.music_value = values["music_volume"]
        self.sfx_value = values["sfx_volume"]
        self.fullscreen = values["fullscreen"]
        # Interruptor: encendido = destellos normales (blancos);
        # apagado = destellos grises que tapan la pantalla igual.
        self.flash_on = (
            accessibility.flash_level() >= accessibility.SAFE_BELOW
        )
        self.hints_on = accessibility.tutorial_hints()
        self.fps_on = accessibility.show_fps()

        music.set_volume(self.music_value)
        audio.set_sfx_volume(self.sfx_value)

        self.font = pygame.font.Font(
            None, max(18, round(self.FONT_SIZE * self.sy))
        )
        self.small_font = pygame.font.Font(
            None, max(14, round(self.SMALL_FONT_SIZE * self.sy))
        )
        self.key_font = load_font(max(12, round(19 * self.sy)))
        self.chip_font = load_font(max(11, round(18 * self.sy)))
        self.guide_tab_font = pygame.font.Font(
            None, max(14, round(20 * self.sy))
        )
        self.title_font = load_font(max(16, round(26 * self.sy)))

        self.background = self._load_background(background)

        # solo la cabaña se oscurece (la tablet del juego no)
        self.cabin = room_light.is_cabin(background)

        if controls_background in (None, background):
            self.controls_background = self.background
            self.controls_cabin = self.cabin
        else:
            self.controls_background = self._load_background(
                controls_background
            )
            self.controls_cabin = room_light.is_cabin(controls_background)

        self.close_rect = self._box(self.CLOSE_BOX)

        self.track_w = round(self.TRACK_W * self.sx)
        self.track_h = max(8, round(self.TRACK_W * 48 / 600 * self.sy))

        self.tracks = {}

        for name in ("music", "sfx"):

            _, ctrl_x, row_y, _ = self.ROWS[name]

            self.tracks[name] = pygame.Rect(
                round(ctrl_x * self.sx),
                round(row_y * self.sy) - self.track_h // 2,
                self.track_w,
                self.track_h
            )

        handle = max(12, round(self.TRACK_W * 64 / 600 * self.sx))

        self.handle_size = (handle, handle)

        toggle_w, toggle_h = self._size(self.TOGGLE_SIZE)

        def toggle_at(name):

            _, ctrl_x, row_y, _ = self.ROWS[name]

            return pygame.Rect(
                round(ctrl_x * self.sx),
                round(row_y * self.sy) - toggle_h // 2,
                toggle_w,
                toggle_h
            )

        self.toggle_rect = toggle_at("fullscreen")
        self.flash_rect = toggle_at("flash")
        self.hints_rect = toggle_at("hints")
        self.fps_rect = toggle_at("fps")

        btn_w, btn_h = self._size(self.CONTROLS_BTN)

        self.controls_rect = pygame.Rect(
            round(self.CONTROLS_POS[0] * self.sx),
            round(self.CONTROLS_POS[1] * self.sy) - btn_h // 2,
            btn_w,
            btn_h
        )

        self.guide_rect = pygame.Rect(
            round(self.GUIDE_POS[0] * self.sx),
            round(self.GUIDE_POS[1] * self.sy) - btn_h // 2,
            btn_w,
            btn_h
        )

        nav_w, nav_h = self._size(self.NAV_BTN)

        center_x = (
            self.NAV_CX if self.NAV_CX is not None
            else (self.LEFT + self.RIGHT) / 2
        )

        nav_y = round(self.NAV_Y * self.sy) - nav_h // 2

        self.back_rect = pygame.Rect(
            round((center_x - self.NAV_GAP / 2 - self.NAV_BTN[0]) * self.sx),
            nav_y,
            nav_w,
            nav_h
        )

        self.reset_rect = pygame.Rect(
            round((center_x + self.NAV_GAP / 2) * self.sx),
            nav_y,
            nav_w,
            nav_h
        )

        pager_w = round(self.reset_rect.width * 0.28)

        self.prev_rect = pygame.Rect(
            self.reset_rect.left,
            self.reset_rect.top,
            pager_w,
            self.reset_rect.height
        )

        self.next_rect = pygame.Rect(
            self.reset_rect.right - pager_w,
            self.reset_rect.top,
            pager_w,
            self.reset_rect.height
        )

        tab_count = len(self.GUIDE_TAB_NAMES)
        tab_gap = round(5 * self.sx)
        tab_area = round((self.GUIDE_X2 - self.GUIDE_X1) * self.sx)
        tab_w = (tab_area - tab_gap * (tab_count - 1)) // tab_count
        tab_h = max(14, round(self.GUIDE_TAB_H * self.sy))

        self.guide_tabs = [
            pygame.Rect(
                round(self.GUIDE_X1 * self.sx) + i * (tab_w + tab_gap),
                round(self.GUIDE_TAB_Y * self.sy) - tab_h // 2,
                tab_w,
                tab_h
            )
            for i in range(tab_count)
        ]

        self.key_rects = {}
        self.label_pos = {}
        self.group_pos = []

        key_w, key_h = self._size(self.KEY_SIZE)

        for col, (title, actions) in enumerate(GROUPS):

            col_x = self.COL_X[col % len(self.COL_X)]

            self.group_pos.append((
                title,
                round((col_x + self.COL_W / 2) * self.sx),
                round(self.GROUP_Y * self.sy)
            ))

            for row, (action, label) in enumerate(actions):

                top = round((self.KEY_TOP + row * self.KEY_STEP) * self.sy)

                self.label_pos[action] = (
                    label,
                    round(col_x * self.sx),
                    top + key_h // 2
                )

                self.key_rects[action] = pygame.Rect(
                    round((col_x + self.COL_W) * self.sx) - key_w,
                    top,
                    key_w,
                    key_h
                )

        self.img_track = self._load("slider_track.png", self.tracks["music"].size)

        self.img_handle = self._load("slider_handle.png", self.handle_size)

        self.img_fill = self._load("slider_relleno.png", self.tracks["music"].size)

        self.img_on = self._load("toggle_on.png", self.toggle_rect.size)
        self.img_off = self._load("toggle_off.png", self.toggle_rect.size)

        self.img_controls = self._load(
            "btn_controles.png", self.controls_rect.size
        )
        self.img_controls_hover = self._load(
            "btn_controles_hover.png", self.controls_rect.size
        )

        self.img_guide = self._load("btn_guia.png", self.guide_rect.size)
        self.img_guide_hover = self._load(
            "btn_guia_hover.png", self.guide_rect.size
        )

        tab_size = self.guide_tabs[0].size

        self.img_tab = self._load("guia_tab.png", tab_size)
        self.img_tab_hover = self._load("guia_tab_hover.png", tab_size)
        self.img_tab_active = self._load("guia_tab_activa.png", tab_size)

        arrow_size = self.prev_rect.size

        self.img_arrow = {
            -1: self._load("guia_flecha_izq.png", arrow_size),
            1: self._load("guia_flecha_der.png", arrow_size),
        }

        self.img_arrow_hover = {
            -1: self._load("guia_flecha_izq_hover.png", arrow_size),
            1: self._load("guia_flecha_der_hover.png", arrow_size),
        }

        self.img_chip_raw = self._load_raw("guia_tecla.png")
        self.chip_cache = {}

        self.img_back = self._load("btn_volver_ajustes.png", self.back_rect.size)
        self.img_back_hover = self._load(
            "btn_volver_ajustes_hover.png", self.back_rect.size
        )

        self.img_reset = self._load("btn_restablecer.png", self.reset_rect.size)
        self.img_reset_hover = self._load(
            "btn_restablecer_hover.png", self.reset_rect.size
        )

        key_size = (key_w, key_h)

        self.img_key = self._load("tecla.png", key_size)
        self.img_key_hover = self._load("tecla_hover.png", key_size)
        self.img_key_listen = self._load("tecla_escuchando.png", key_size)


    def _size(self, size):

        return (
            max(1, round(size[0] * self.sx)),
            max(1, round(size[1] * self.sy))
        )

    def _box(self, box):

        x1, y1, x2, y2 = box

        return pygame.Rect(
            round(x1 * self.sx),
            round(y1 * self.sy),
            round((x2 - x1) * self.sx),
            round((y2 - y1) * self.sy)
        )

    def _load_background(self, name):

        path = UI_DIR / name

        if not path.exists():
            path = UI_DIR / "mapaajustes.png"

        try:
            image = pygame.image.load(str(path)).convert_alpha()

        except (pygame.error, FileNotFoundError):

            surface = pygame.Surface((self.width, self.height))
            surface.fill((28, 44, 84))

            return surface

        # Se mantiene el alfa: las partes transparentes del PNG dejan
        # ver lo que hay detras (el juego en pausa). Las imagenes opacas
        # (mapaajustes.png, etc.) se ven igual que antes.
        return pygame.transform.smoothscale(
            image, (self.width, self.height)
        )

    @staticmethod
    def _load_raw(name):

        path = UI_DIR / name

        if not path.exists():
            return None

        try:
            return pygame.image.load(str(path)).convert_alpha()

        except pygame.error:
            return None

    def _load(self, name, size):

        image = self._load_raw(name)

        if image is None:
            return None

        return pygame.transform.smoothscale(
            image, (max(1, size[0]), max(1, size[1]))
        )

    def _text(self, font, text, color, center=None, midleft=None):

        shadow = font.render(text, True, self.SHADOW)
        image = font.render(text, True, color)

        rect = image.get_rect()

        if center is not None:
            rect.center = center
        elif midleft is not None:
            rect.midleft = midleft

        self.screen.blit(shadow, rect.move(1, 1))
        self.screen.blit(image, rect)

        return rect

    def _flash(self, text, seconds=2.2):

        self.message = text
        self.message_timer = seconds


    def _handle_x_range(self, track):

        half = self.handle_size[0] // 2

        return track.left + half, track.right - half

    def _value_from_x(self, track, x):

        left, right = self._handle_x_range(track)

        if right <= left:
            return 0.0

        return max(0.0, min(1.0, (x - left) / (right - left)))

    def _set_slider(self, name, value):

        value = max(0.0, min(1.0, value))

        if name == "music":

            self.music_value = value
            music.set_volume(value)

        else:

            self.sfx_value = value
            audio.set_sfx_volume(value)

    def _toggle_fullscreen(self):

        self.fullscreen = not self.fullscreen

        try:
            pygame.display.toggle_fullscreen()

        except pygame.error:
            pass

        save_settings(fullscreen=self.fullscreen)

    def _save_volumes(self):

        save_settings(
            music_volume=round(self.music_value, 3),
            sfx_volume=round(self.sfx_value, 3)
        )


    def handle_event(self, event):

        if event.type == pygame.MOUSEMOTION:

            self.hover = None

            if self.dragging is not None:

                track = self.tracks[self.dragging]

                self._set_slider(
                    self.dragging,
                    self._value_from_x(track, event.pos[0])
                )

            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:

            if self.dragging is not None:

                name = self.dragging
                self.dragging = None

                self._save_volumes()

                if name == "sfx":
                    audio.play("coin")

            return None

        if (
            event.type == pygame.MOUSEWHEEL
            and self.view == "guide"
            and event.y != 0
        ):

            self._guide_move(-1 if event.y > 0 else 1)

            return None

        if event.type == pygame.KEYDOWN:
            return self._on_key(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._on_click(event.pos)

        return None

    def _on_key(self, event):

        if self.listening is not None:

            action = self.listening

            if event.key == pygame.K_ESCAPE:

                self.listening = None
                return None

            ok, swapped = controls.rebind(action, event.key)

            self.listening = None

            if not ok:

                self._flash("Esa tecla esta reservada")
                audio.play("alert")

            elif swapped is not None:

                self._flash(
                    "Intercambiada con "
                    f"{self.label_pos[swapped][0]}"
                )

            return None

        if event.key == pygame.K_ESCAPE:

            if self.view in ("controls", "guide"):

                self.view = "main"
                return None

            return "back"

        if self.view == "guide":

            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._guide_move(-1)

            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._guide_move(1)

        return None

    def _on_click(self, pos):

        if self.close_rect.collidepoint(pos):

            if self.listening is not None:

                self.listening = None
                return None

            return "back"

        if self.view == "main":

            for name, track in self.tracks.items():

                if track.inflate(0, 8).collidepoint(pos):

                    self.dragging = name

                    self._set_slider(name, self._value_from_x(track, pos[0]))

                    return None

            if self.toggle_rect.collidepoint(pos):

                self._toggle_fullscreen()
                return None

            if self.flash_rect.collidepoint(pos):

                self.flash_on = not self.flash_on
                accessibility.set_flash_level(1.0 if self.flash_on else 0.0)

                return None

            if self.hints_rect.collidepoint(pos):

                self.hints_on = not self.hints_on
                accessibility.set_tutorial_hints(self.hints_on)

                return None

            if self.fps_rect.collidepoint(pos):

                self.fps_on = not self.fps_on
                accessibility.set_show_fps(self.fps_on)

                return None

            if self.controls_rect.collidepoint(pos):

                self.view = "controls"
                self.listening = None

                return None

            if self.guide_rect.collidepoint(pos):

                self.view = "guide"
                self.guide_page = 0
                self.listening = None

                return None

            return None

        if self.view == "guide":
            return self._on_guide_click(pos)

        if self.back_rect.collidepoint(pos):

            self.view = "main"
            self.listening = None

            return None

        if self.reset_rect.collidepoint(pos):

            controls.reset()
            self.listening = None
            self._flash("Teclas restablecidas")

            return None

        for action, rect in self.key_rects.items():

            if rect.collidepoint(pos):

                self.listening = action
                return None

        self.listening = None

        return None


    def _guide_flat(self):

        flat = []

        for cat, entries in enumerate(self._guide_pages()):

            for start in range(0, len(entries), 4):
                flat.append((cat, entries[start:start + 4]))

        return flat

    def _guide_move(self, step):

        count = len(self._guide_flat())

        self.guide_page = (self.guide_page + step) % count

    def _on_guide_click(self, pos):

        if self.back_rect.collidepoint(pos):

            self.view = "main"

            return None

        if self.prev_rect.collidepoint(pos):

            self._guide_move(-1)

            return None

        if self.next_rect.collidepoint(pos):

            self._guide_move(1)

            return None

        for index, rect in enumerate(self.guide_tabs):

            if rect.collidepoint(pos):

                for number, (cat, _) in enumerate(self._guide_flat()):

                    if cat == index:

                        self.guide_page = number
                        break

                return None

        return None

    def update(self, dt):

        if self.message_timer > 0.0:

            self.message_timer = max(0.0, self.message_timer - dt)

            if self.message_timer == 0.0:
                self.message = ""


    def draw(self):

        mouse = pygame.mouse.get_pos()

        if self.view == "main":

            room_light.blit_background(
                self.screen, self.background, self.cabin
            )
            self._draw_main(mouse)

        elif self.view == "guide":

            room_light.blit_background(
                self.screen, self.controls_background, self.controls_cabin
            )
            self._draw_guide(mouse)

        else:

            room_light.blit_background(
                self.screen, self.controls_background, self.controls_cabin
            )
            self._draw_controls(mouse)

    def _draw_button(self, rect, image, image_hover, mouse, fallback_text):

        hovered = rect.collidepoint(mouse)

        picture = image_hover if (hovered and image_hover) else image

        if picture is not None:

            self.screen.blit(picture, rect)
            return

        pygame.draw.rect(
            self.screen,
            (236, 226, 190) if hovered else (206, 196, 160),
            rect,
            border_radius=6
        )

        pygame.draw.rect(
            self.screen, (60, 46, 30), rect, 2, border_radius=6
        )

        self._text(
            self.small_font, fallback_text, (40, 30, 20), center=rect.center
        )

    def _draw_fill(self, track, handle_x):

        width = min(track.width, handle_x - track.left)

        if width <= 0:
            return

        if self.img_fill is not None:

            crop = self.img_fill.subsurface(
                pygame.Rect(0, 0, width, self.img_fill.get_height())
            )

            self.screen.blit(crop, track.topleft)

            return

        inner = pygame.Rect(
            track.left + round(track.width * 0.055),
            track.top + round(track.height * 0.34),
            round(track.width * 0.89),
            max(2, round(track.height * 0.34))
        )

        pygame.draw.rect(
            self.screen,
            self.FILL,
            pygame.Rect(
                inner.left, inner.top,
                max(1, min(inner.width, handle_x - inner.left)),
                inner.height
            ),
            border_radius=inner.height // 2
        )

    def _draw_toggle(self, rect, flag):

        toggle = self.img_on if flag else self.img_off

        if toggle is not None:

            self.screen.blit(toggle, rect)

            return

        pygame.draw.rect(
            self.screen,
            (90, 190, 110) if flag else (120, 120, 130),
            rect,
            border_radius=rect.height // 2
        )

    def _draw_main(self, mouse):

        for label, name, value in (
            ("Música", "music", self.music_value),
            ("Sonido", "sfx", self.sfx_value),
        ):

            label_x, _, row_y, value_x = self.ROWS[name]

            y = round(row_y * self.sy)

            self._text(
                self.font,
                label,
                self.TEXT,
                midleft=(round(label_x * self.sx), y)
            )

            track = self.tracks[name]

            left, right = self._handle_x_range(track)

            hx = round(left + (right - left) * value)

            self._draw_fill(track, hx)

            if self.img_track is not None:

                self.screen.blit(self.img_track, track)

            else:

                pygame.draw.rect(
                    self.screen, (24, 38, 78), track, border_radius=8
                )

            if self.img_handle is not None:

                self.screen.blit(
                    self.img_handle,
                    self.img_handle.get_rect(center=(hx, track.centery))
                )

            else:

                pygame.draw.circle(
                    self.screen,
                    self.ACCENT,
                    (hx, track.centery),
                    self.handle_size[0] // 2
                )

            self._text(
                self.font,
                f"{round(value * 100)}%",
                self.TEXT_DIM,
                midleft=(round(value_x * self.sx), y)
            )

        for label, name, flag, rect in (
            ("Pantalla completa", "fullscreen", self.fullscreen,
             self.toggle_rect),
            ("Flashes", "flash", self.flash_on, self.flash_rect),
            ("Avisos tutorial", "hints", self.hints_on, self.hints_rect),
            ("Mostrar FPS", "fps", self.fps_on, self.fps_rect),
        ):

            label_x, _, row_y, _ = self.ROWS[name]

            self._text(
                self.font,
                label,
                self.TEXT,
                midleft=(round(label_x * self.sx), round(row_y * self.sy))
            )

            self._draw_toggle(rect, flag)

        self._draw_button(
            self.controls_rect,
            self.img_controls,
            self.img_controls_hover,
            mouse,
            "Controles"
        )

        self._draw_button(
            self.guide_rect,
            self.img_guide,
            self.img_guide_hover,
            mouse,
            "Guía de teclas"
        )

    def _font(self, size):

        size = max(10, int(size))

        font = self.font_cache.get(size)

        if font is None:

            font = load_font(size)
            self.font_cache[size] = font

        return font

    def _wrap(self, font, text, width):

        lines = []
        line = ""

        for word in text.split(" "):

            test = word if not line else line + " " + word

            if not line or font.size(test)[0] <= width:
                line = test

            else:

                lines.append(line)
                line = word

        if line:
            lines.append(line)

        return lines

    def _fit_lines(self, text, width, base_size, max_lines):

        size = max(10, int(base_size))

        while True:

            font = self._font(size)
            lines = self._wrap(font, text, width)

            if len(lines) <= max_lines:
                return font, lines

            if size <= 11:
                break

            size -= 1

        lines = lines[:max_lines]

        while lines[-1] and font.size(lines[-1] + "...")[0] > width:
            lines[-1] = lines[-1][:-1]

        lines[-1] = lines[-1].rstrip() + "..."

        return font, lines

    def _guide_pages(self):

        key = controls.label
        plus = ("sep", "+")
        also = ("sep", "/")

        return [
            [
                (
                    [
                        key("up"), key("left"), key("down"), key("right"),
                        also, "FLECHAS"
                    ],
                    "Moverte",
                    "Camina por el mapa en las cuatro direcciones."
                ),
                (
                    ["ESPACIO"],
                    "Saltar",
                    "Esquiva las ondas y los barridos del jefe de la "
                    "zona 2."
                ),
                (
                    ["ESPACIO"],
                    "Soltarte de una trampa",
                    "Si una trampa te atrapa, púlsalo rápido para "
                    "liberarte."
                ),
                (
                    [key("emotes")],
                    "Baile",
                    "Abre la rueda de bailes para elegir uno."
                ),
            ],
            [
                (
                    [key("pickup")],
                    "Recoger",
                    "Toma objetos y luces. Para tomar otra luz, suelta "
                    "antes la tuya."
                ),
                (
                    [key("drop")],
                    "Soltar",
                    "Suelta el objeto elegido. Con la luz elegida, "
                    "suelta la luz."
                ),
                (
                    [key("use")],
                    "Usar / Tienda",
                    "Abre la tienda, usa cofres y la puerta final, o "
                    "el objeto elegido."
                ),
                (
                    [key("magnet")],
                    "Imán",
                    "Activa o desactiva el modo imán (necesitas tener "
                    "el imán)."
                ),
                (
                    [key("attack_mode")],
                    "Cambiar golpe",
                    "Alterna entre golpe común y bola de fuego (solo "
                    "con la antorcha)."
                ),
                (
                    [key("equipped")],
                    "Luz equipada",
                    "Elige la luz del casillero aparte, la que te "
                    "ilumina."
                ),
            ],
            [
                (
                    [
                        key("slot1"), key("slot2"),
                        key("slot3"), key("slot4")
                    ],
                    "Casilleros",
                    "Eligen un casillero del inventario."
                ),
                (
                    [key("potion1"), key("potion2")],
                    "Pociones",
                    "Eligen las pociones de los marcos violeta."
                ),
                (
                    [key("equipped")],
                    "Luz equipada",
                    "Elige el casillero aparte donde va tu luz."
                ),
                (
                    ["RUEDA"],
                    "Cambiar casillero",
                    "Recorre los casilleros y la luz equipada."
                ),
                (
                    ["CLIC IZQ"],
                    "Mover objetos",
                    "Arrastra un objeto a otro casillero para cambiarlo "
                    "de lugar."
                ),
                (
                    ["CLIC DER"],
                    "Mapa",
                    "Con el Mapa elegido, mantén el clic derecho para "
                    "verlo."
                ),
            ],
            [
                (
                    ["CTRL", plus, key("drop")],
                    "Soltar todo",
                    "Suelta todo el inventario. La luz equipada no se "
                    "suelta."
                ),
                (
                    ["SHIFT", plus, key("drop")],
                    "Soltar un montón",
                    "Suelta todo el montón del casillero elegido."
                ),
                (
                    ["CTRL", plus, "CLIC IZQ"],
                    "Tirar al basurero",
                    "Sobre un basurero, tira todo el montón elegido en vez "
                    "de uno solo."
                ),
                (
                    ["SHIFT", plus, "CLIC DER"],
                    "Quitar 5 en la tienda",
                    "En la tienda, quita 5 unidades de un casillero en "
                    "vez de 1."
                ),
            ],
            [
                (
                    ["CLIC IZQ"],
                    "Atacar",
                    "Golpea con la luz equipada. Mantenlo para seguir "
                    "atacando."
                ),
                (
                    ["CLIC DER"],
                    "Usar objeto",
                    "Usa el objeto del casillero elegido, igual que "
                    f"{key('use')}."
                ),
                (
                    ["CLIC IZQ"],
                    "Colocar",
                    "Pon la construcción que llevas (cofre, fogata...) "
                    "donde apuntes."
                ),
                (
                    ["CLIC DER"],
                    "Abrir construcciones",
                    "Sobre un cofre, bolsa, yunque o ruleta abre su "
                    "panel."
                ),
                (
                    ["CLIC IZQ", also, "DER"],
                    "Cofre o bolsa",
                    "En su panel: izquierdo pasa el montón completo; "
                    "derecho, solo uno."
                ),
                (
                    ["CLIC CENTRAL"],
                    "Info en la tienda",
                    "En la tienda, muestra qué hace cada objeto."
                ),
            ],
            [
                (
                    ["ESC"],
                    "Pausa y volver",
                    "Abre la pausa en partida y retrocede en cualquier "
                    "pantalla."
                ),
                (
                    ["TAB"],
                    "Objetivos y tienda",
                    "Minimiza el cuadro de objetivos. En la tienda "
                    "cambia de pestaña."
                ),
                (
                    ["ESC", also, key("use")],
                    "Cerrar tienda",
                    "Con la tienda abierta, cierra la pantalla."
                ),
                (
                    ["K"],
                    "Saltar tutorial",
                    "Quita el tutorial cuando el juego permite "
                    "saltarlo."
                ),
                (
                    ["ENTER", also, "ESPACIO"],
                    "Avanzar",
                    "Pasa el cómic y el tutorial, y confirma en los "
                    "menús."
                ),
                (
                    ["F3", also, "F4"],
                    "Ayudas visuales",
                    "F3 muestra las cajas de objetos; F4, la zona de "
                    "tus golpes."
                ),
            ],
        ]

    def _draw_chips(self, keys, x, y, max_w):

        chip_h = max(14, round(self.GUIDE_CHIP_H * self.sy))
        step = chip_h + max(2, round(2 * self.sy))
        pad = round(6 * self.sx)
        gap = max(2, round(3 * self.sx))

        def chip_image(label):

            image = self.chip_font.render(label, True, (36, 30, 26))

            width = max(chip_h, image.get_width() + 2 * pad)

            if width > max_w:

                scale = (max_w - 2 * pad) / max(1, image.get_width())

                image = pygame.transform.smoothscale(
                    image,
                    (
                        max(1, round(image.get_width() * scale)),
                        max(1, round(image.get_height() * scale))
                    )
                )

                width = max_w

            return image, width

        cx = x
        cy = y

        index = 0

        while index < len(keys):

            token = keys[index]

            if isinstance(token, tuple):

                sep_w = self.chip_font.size(token[1])[0]

                need = sep_w + gap

                if index + 1 < len(keys) and not isinstance(
                    keys[index + 1], tuple
                ):
                    need += chip_image(str(keys[index + 1]))[1]

                if cx > x and cx + need > x + max_w:

                    cx = x
                    cy += step

                self._text(
                    self.chip_font,
                    token[1],
                    self.TEXT,
                    midleft=(cx, cy + chip_h // 2)
                )

                cx += sep_w + gap
                index += 1

                continue

            image, width = chip_image(str(token))

            if cx > x and cx + width > x + max_w:

                cx = x
                cy += step

            rect = pygame.Rect(cx, cy, width, chip_h)

            plate = self._chip_surface(width, chip_h)

            if plate is not None:

                self.screen.blit(plate, rect)

            else:

                pygame.draw.rect(
                    self.screen,
                    (20, 48, 110),
                    rect.move(0, 2),
                    border_radius=4
                )

                pygame.draw.rect(
                    self.screen, (232, 236, 246), rect, border_radius=4
                )

                pygame.draw.rect(
                    self.screen, (70, 84, 122), rect, 1, border_radius=4
                )

            self.screen.blit(image, image.get_rect(center=rect.center))

            cx += width + gap
            index += 1

    def _chip_surface(self, width, height):

        raw = self.img_chip_raw

        if raw is None:
            return None

        key = (width, height)

        cached = self.chip_cache.get(key)

        if cached is not None:
            return cached

        cap = max(2, min(width // 2, round(height * 0.38)))

        src_cap = max(1, round(raw.get_width() * 0.2))

        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        left = raw.subsurface(
            pygame.Rect(0, 0, src_cap, raw.get_height())
        )
        right = raw.subsurface(
            pygame.Rect(
                raw.get_width() - src_cap, 0, src_cap, raw.get_height()
            )
        )
        middle = raw.subsurface(
            pygame.Rect(
                src_cap, 0,
                raw.get_width() - 2 * src_cap, raw.get_height()
            )
        )

        surface.blit(
            pygame.transform.smoothscale(left, (cap, height)), (0, 0)
        )

        surface.blit(
            pygame.transform.smoothscale(
                middle, (max(1, width - 2 * cap), height)
            ),
            (cap, 0)
        )

        surface.blit(
            pygame.transform.smoothscale(right, (cap, height)),
            (width - cap, 0)
        )

        self.chip_cache[key] = surface

        return surface

    def _chips_total(self, keys):

        chip_h = max(14, round(self.GUIDE_CHIP_H * self.sy))
        pad = round(6 * self.sx)
        gap = max(2, round(3 * self.sx))

        total = 0

        for token in keys:

            if isinstance(token, tuple):
                total += self.chip_font.size(token[1])[0] + gap

            else:

                total += max(
                    chip_h,
                    self.chip_font.size(str(token))[0] + 2 * pad
                ) + gap

        return total - gap

    def _draw_entry(self, rect, entry, key_w):

        keys, title, desc = entry

        gap = round(8 * self.sx)

        self._draw_chips(keys, rect.left, rect.top, key_w)

        text_x = rect.left + key_w + gap
        text_w = rect.width - key_w - gap

        title_font, title_lines = self._fit_lines(
            title, text_w, 25 * self.sy, 1
        )

        title_h = title_font.get_height()

        self._text(
            title_font,
            title_lines[0],
            self.GOLD,
            midleft=(text_x, rect.top + title_h // 2)
        )

        desc_font, desc_lines = self._fit_lines(
            desc, text_w, 20 * self.sy, 2
        )

        line_h = desc_font.get_height()

        y = rect.top + title_h + max(1, round(2 * self.sy))

        for line in desc_lines:

            self._text(
                desc_font,
                line,
                self.TEXT,
                midleft=(text_x, y + line_h // 2)
            )

            y += line_h

    def _draw_pager(self, mouse):

        for rect, direction in ((self.prev_rect, -1), (self.next_rect, 1)):

            hovered = rect.collidepoint(mouse)

            picture = (
                self.img_arrow_hover[direction] if hovered
                else self.img_arrow[direction]
            ) or self.img_arrow[direction]

            if picture is not None:

                self.screen.blit(picture, rect)

                continue

            pygame.draw.rect(
                self.screen,
                (70, 132, 206) if hovered else (50, 104, 178),
                rect,
                border_radius=6
            )

            pygame.draw.rect(
                self.screen, (26, 64, 132), rect, 2, border_radius=6
            )

            cx, cy = rect.center
            half = max(4, rect.height // 5)

            if direction < 0:

                points = [
                    (cx + half // 2, cy - half),
                    (cx + half // 2, cy + half),
                    (cx - half // 2, cy)
                ]

            else:

                points = [
                    (cx - half // 2, cy - half),
                    (cx - half // 2, cy + half),
                    (cx + half // 2, cy)
                ]

            pygame.draw.polygon(self.screen, self.TEXT, points)

        self._text(
            self.guide_tab_font,
            f"{self.guide_page + 1}/{len(self._guide_flat())}",
            self.TEXT,
            center=(
                (self.prev_rect.right + self.next_rect.left) // 2,
                self.prev_rect.centery
            )
        )

    def _draw_guide(self, mouse):

        self._draw_button(
            self.back_rect,
            self.img_back,
            self.img_back_hover,
            mouse,
            "Volver"
        )

        self._draw_pager(mouse)

        flat = self._guide_flat()
        current, entries = flat[min(self.guide_page, len(flat) - 1)]

        for index, rect in enumerate(self.guide_tabs):

            active = index == current
            hovered = rect.collidepoint(mouse)

            if active:
                picture = self.img_tab_active
            elif hovered:
                picture = self.img_tab_hover
            else:
                picture = self.img_tab

            if picture is not None:

                self.screen.blit(picture, rect)

            else:

                if active:
                    fill = (16, 40, 98)
                elif hovered:
                    fill = (74, 136, 210)
                else:
                    fill = (50, 104, 178)

                pygame.draw.rect(self.screen, fill, rect, border_radius=6)

                pygame.draw.rect(
                    self.screen,
                    self.ACCENT if active else (26, 64, 132),
                    rect,
                    2,
                    border_radius=6
                )

            tab_font, tab_lines = self._fit_lines(
                self.GUIDE_TAB_NAMES[index],
                rect.width - round(10 * self.sx),
                20 * self.sy,
                1
            )

            self._text(
                tab_font,
                tab_lines[0],
                self.GOLD if active else self.TEXT,
                center=rect.center
            )

        area_x = round(self.GUIDE_X1 * self.sx)
        area_w = round((self.GUIDE_X2 - self.GUIDE_X1) * self.sx)
        gap = round(self.GUIDE_GAP * self.sx)
        col_w = (area_w - gap) // 2
        row_h = round(self.GUIDE_ROW_H * self.sy)
        top = round(self.GUIDE_TOP * self.sy)

        per_col = 2

        key_cap = round(self.GUIDE_KEY_W * self.sx)

        key_widths = [
            min(
                key_cap,
                max(
                    [
                        self._chips_total(entry[0])
                        for entry in entries[start:start + per_col]
                    ] or [0]
                ) + round(2 * self.sx)
            )
            for start in (0, per_col)
        ]

        for index, entry in enumerate(entries):

            col = index // per_col
            row = index % per_col

            rect = pygame.Rect(
                area_x + col * (col_w + gap),
                top + row * row_h,
                col_w,
                row_h
            )

            self._draw_entry(rect, entry, key_widths[col])

    def _draw_controls(self, mouse):

        self._draw_button(
            self.back_rect,
            self.img_back,
            self.img_back_hover,
            mouse,
            "Volver"
        )

        self._draw_button(
            self.reset_rect,
            self.img_reset,
            self.img_reset_hover,
            mouse,
            "Restablecer"
        )

        if self.listening is not None:
            title = "Presiona una tecla"
            color = self.ACCENT

        elif self.message:
            title = self.message
            color = self.ACCENT

        else:
            title = "Controles"
            color = self.TEXT

        self._text(
            self.title_font,
            title,
            color,
            center=(
                round((self.LEFT + self.RIGHT) / 2 * self.sx),
                round(self.TOP_Y * self.sy)
            )
        )

        for title, cx, cy in self.group_pos:

            self._text(
                self.small_font, title, self.ACCENT, center=(cx, cy)
            )

        for action, rect in self.key_rects.items():

            label, lx, ly = self.label_pos[action]

            self._text(
                self.key_font, label, self.TEXT, midleft=(lx, ly)
            )

            listening = self.listening == action
            hovered = rect.collidepoint(mouse)

            if listening:
                picture = self.img_key_listen or self.img_key

            elif hovered:
                picture = self.img_key_hover or self.img_key

            else:
                picture = self.img_key

            if picture is not None:

                self.screen.blit(picture, rect)

            else:

                pygame.draw.rect(
                    self.screen,
                    (255, 230, 150) if listening else (214, 218, 232),
                    rect,
                    border_radius=4
                )

            text = "..." if listening else controls.label(action)

            image = self.key_font.render(text, True, (36, 30, 26))

            if image.get_width() > rect.width - 8:

                scale = (rect.width - 8) / image.get_width()

                image = pygame.transform.smoothscale(
                    image,
                    (
                        max(1, round(image.get_width() * scale)),
                        max(1, round(image.get_height() * scale))
                    )
                )

            self.screen.blit(image, image.get_rect(center=rect.center))