import json
from pathlib import Path

import pygame

from core.audio_manager import audio
from core.controls import controls, GROUPS
from core.music_manager import music

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

    ROW_Y = (322, 376, 430)
    LABEL_X = 512
    TRACK_X = 730
    TRACK_W = 330
    VALUE_X = 1084
    TOGGLE_SIZE = (84, 42)
    CONTROLS_BTN = (186, 44)

    TOP_Y = 302
    NAV_BTN = (118, 32)
    COL_X = (508, 736, 964)
    COL_W = 216
    GROUP_Y = 334
    KEY_TOP = 346
    KEY_STEP = 24
    KEY_SIZE = (78, 22)

    TEXT = (244, 248, 255)
    TEXT_DIM = (176, 198, 232)
    ACCENT = (255, 200, 110)
    SHADOW = (14, 26, 58)

    def __init__(
        self,
        screen,
        background="mapaajustes.png",
        controls_background=None
    ):

        self.screen = screen
        self.width, self.height = screen.get_size()

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        self.view = "main"

        self.listening = None
        self.dragging = None
        self.message = ""
        self.message_timer = 0.0

        self.hover = None

        values = load_settings()

        self.music_value = values["music_volume"]
        self.sfx_value = values["sfx_volume"]
        self.fullscreen = values["fullscreen"]

        music.set_volume(self.music_value)
        audio.set_sfx_volume(self.sfx_value)

        self.font = pygame.font.Font(None, max(18, round(34 * self.sy)))
        self.small_font = pygame.font.Font(None, max(14, round(23 * self.sy)))
        self.key_font = pygame.font.Font(None, max(12, round(19 * self.sy)))
        self.title_font = pygame.font.Font(None, max(16, round(26 * self.sy)))

        self.background = self._load_background(background)

        if controls_background in (None, background):
            self.controls_background = self.background
        else:
            self.controls_background = self._load_background(
                controls_background
            )

        self.close_rect = self._box(self.CLOSE_BOX)

        self.track_w = round(self.TRACK_W * self.sx)
        self.track_h = max(8, round(self.TRACK_W * 48 / 600 * self.sy))

        self.tracks = {}

        for index, name in enumerate(("music", "sfx")):

            self.tracks[name] = pygame.Rect(
                round(self.TRACK_X * self.sx),
                round(self.ROW_Y[index] * self.sy) - self.track_h // 2,
                self.track_w,
                self.track_h
            )

        handle = max(12, round(self.TRACK_W * 64 / 600 * self.sx))

        self.handle_size = (handle, handle)

        toggle_w, toggle_h = self._size(self.TOGGLE_SIZE)

        self.toggle_rect = pygame.Rect(
            round(self.TRACK_X * self.sx),
            round(self.ROW_Y[2] * self.sy) - toggle_h // 2,
            toggle_w,
            toggle_h
        )

        btn_w, btn_h = self._size(self.CONTROLS_BTN)

        self.controls_rect = pygame.Rect(
            round((self.RIGHT - self.CONTROLS_BTN[0]) * self.sx),
            round(self.ROW_Y[2] * self.sy) - btn_h // 2,
            btn_w,
            btn_h
        )

        nav_w, nav_h = self._size(self.NAV_BTN)

        self.back_rect = pygame.Rect(
            round(self.LEFT * self.sx),
            round(self.TOP_Y * self.sy) - nav_h // 2,
            nav_w,
            nav_h
        )

        self.reset_rect = pygame.Rect(
            round((self.RIGHT - self.NAV_BTN[0]) * self.sx),
            round(self.TOP_Y * self.sy) - nav_h // 2,
            nav_w,
            nav_h
        )

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

        self.img_on = self._load("toggle_on.png", self.toggle_rect.size)
        self.img_off = self._load("toggle_off.png", self.toggle_rect.size)

        self.img_controls = self._load(
            "btn_controles.png", self.controls_rect.size
        )
        self.img_controls_hover = self._load(
            "btn_controles_hover.png", self.controls_rect.size
        )

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
            image = pygame.image.load(str(path)).convert()

        except (pygame.error, FileNotFoundError):

            surface = pygame.Surface((self.width, self.height))
            surface.fill((28, 44, 84))

            return surface

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

            if self.view == "controls":

                self.view = "main"
                return None

            return "back"

        return None

    def _on_click(self, pos):

        if self.close_rect.collidepoint(pos):

            if self.listening is not None:

                self.listening = None
                return None

            return "back"

        if self.view == "main":

            for name, track in self.tracks.items():

                if track.inflate(0, track.height).collidepoint(pos):

                    self.dragging = name

                    self._set_slider(name, self._value_from_x(track, pos[0]))

                    return None

            if self.toggle_rect.collidepoint(pos):

                self._toggle_fullscreen()
                return None

            if self.controls_rect.collidepoint(pos):

                self.view = "controls"
                self.listening = None

                return None

            return None

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


    def update(self, dt):

        if self.message_timer > 0.0:

            self.message_timer = max(0.0, self.message_timer - dt)

            if self.message_timer == 0.0:
                self.message = ""


    def draw(self):

        mouse = pygame.mouse.get_pos()

        if self.view == "main":

            self.screen.blit(self.background, (0, 0))
            self._draw_main(mouse)

        else:

            self.screen.blit(self.controls_background, (0, 0))
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

    def _draw_main(self, mouse):

        rows = (
            ("Música", "music", self.music_value),
            ("Efectos", "sfx", self.sfx_value),
        )

        for index, (label, name, value) in enumerate(rows):

            y = round(self.ROW_Y[index] * self.sy)

            self._text(
                self.font,
                label,
                self.TEXT,
                midleft=(round(self.LABEL_X * self.sx), y)
            )

            track = self.tracks[name]

            if self.img_track is not None:

                self.screen.blit(self.img_track, track)

            else:

                pygame.draw.rect(
                    self.screen, (24, 38, 78), track, border_radius=8
                )

            left, right = self._handle_x_range(track)

            hx = round(left + (right - left) * value)

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
                midleft=(round(self.VALUE_X * self.sx), y)
            )

        y = round(self.ROW_Y[2] * self.sy)

        self._text(
            self.font,
            "Pantalla completa",
            self.TEXT,
            midleft=(round(self.LABEL_X * self.sx), y)
        )

        toggle = self.img_on if self.fullscreen else self.img_off

        if toggle is not None:

            self.screen.blit(toggle, self.toggle_rect)

        else:

            pygame.draw.rect(
                self.screen,
                (90, 190, 110) if self.fullscreen else (120, 120, 130),
                self.toggle_rect,
                border_radius=self.toggle_rect.height // 2
            )

        self._draw_button(
            self.controls_rect,
            self.img_controls,
            self.img_controls_hover,
            mouse,
            "Controles"
        )

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
            title = "Apretá una tecla"
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
                (self.back_rect.right + self.reset_rect.left) // 2,
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