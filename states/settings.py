import json
import pygame

from core.audio_manager import audio
from core.controls import controls, GROUPS, key_label
from pathlib import Path


SETTINGS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "settings.json"
)

DEFAULTS = {
    "music_volume": 0.7,
    "sfx_volume": 0.7,
    "fullscreen": False,
}

ACTION_LABELS = {
    action: label
    for _, actions in GROUPS
    for action, label in actions
}


def load_settings():

    settings = dict(DEFAULTS)

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            settings.update(
                {k: data[k] for k in DEFAULTS if k in data}
            )

    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        pass

    return settings


def window_is_fullscreen():

    try:
        return bool(pygame.display.is_fullscreen())
    except AttributeError:
        surface = pygame.display.get_surface()

        return bool(surface and surface.get_flags() & pygame.FULLSCREEN)


def save_settings(settings):

    data = {}

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            data = {}

    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        data = {}

    data.update(settings)

    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    except OSError:
        return False

    return True


class ControlsScreen:

    IMG_W = 1672
    IMG_H = 941

    CLOSE_BOX = (1179, 219, 1204, 246)

    COL_X = (494, 735, 976)
    COL_W = 223

    HEADER_Y = 280
    HEADER_H = 26

    ROW_Y = 310
    ROW_H = 30

    CHIP_SIZE = (84, 26)

    BTN_Y = 462
    BTN_SIZE = (126, 34)
    BTN_GAP = 20
    CENTER_X = 846

    SHORT = {
        "use": "Usar/Tienda",
        "attack_mode": "Modo ataque",
    }

    INFO = [
        "Click izq: atacar",
        "Ruedita: cambia casillero",
    ]

    TEXT = (228, 238, 255)
    HEADER = (255, 205, 120)
    MUTED = (190, 210, 245)

    def __init__(self, screen, background="mapacontroles.png"):

        self.screen = screen
        self.width, self.height = screen.get_size()

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        self.ui_dir = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
        )

        path = self.ui_dir / background

        if not path.exists():
            path = self.ui_dir / "mapaajustes.png"

        image = pygame.image.load(path).convert()

        self.background = pygame.transform.smoothscale(
            image,
            (self.width, self.height)
        )

        self.font = pygame.font.Font(
            None,
            max(16, round(30 * self.sy))
        )

        self.header_font = pygame.font.Font(
            None,
            max(18, round(34 * self.sy))
        )

        self.small_font = pygame.font.Font(
            None,
            max(13, round(21 * self.sy))
        )

        self.close_rect = self._r(
            (
                self.CLOSE_BOX[0],
                self.CLOSE_BOX[1],
                self.CLOSE_BOX[2] - self.CLOSE_BOX[0],
                self.CLOSE_BOX[3] - self.CLOSE_BOX[1],
            )
        )

        self.selected = 0
        self.listening = None

        self.message = ""
        self.message_time = 0.0

        self.headers = []
        self.items = []

        self._layout()

        self.chip_img = self._optional(
            "tecla.png",
            self.items[0]["chip"].size
        )

        self.chip_hover_img = self._optional(
            "tecla_hover.png",
            self.items[0]["chip"].size
        )

        self.chip_listen_img = self._optional(
            "tecla_escuchando.png",
            self.items[0]["chip"].size
        )

        button_size = self.items[-1]["chip"].size

        self.reset_img = self._optional("btn_restablecer.png", button_size)

        self.reset_hover_img = self._optional(
            "btn_restablecer_hover.png",
            button_size
        )

        self.back_img = self._optional("btn_regresar.png", button_size)

        self.back_hover_img = self._optional(
            "btn_regresar_hover.png",
            button_size
        )

    def _r(self, box):

        x, y, w, h = box

        return pygame.Rect(
            round(x * self.sx),
            round(y * self.sy),
            max(1, round(w * self.sx)),
            max(1, round(h * self.sy))
        )

    def _optional(self, name, size):

        path = self.ui_dir / name

        if not path.exists():
            return None

        try:
            image = pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None

        return pygame.transform.smoothscale(image, size)

    def _layout(self):

        cw, ch = self.CHIP_SIZE

        for col, (title, actions) in enumerate(GROUPS):

            x = self.COL_X[col]

            self.headers.append(
                (
                    title,
                    self._r((x, self.HEADER_Y, self.COL_W, self.HEADER_H))
                )
            )

            for n, (action, label) in enumerate(actions):

                y = self.ROW_Y + n * self.ROW_H

                self.items.append(
                    {
                        "kind": "action",
                        "action": action,
                        "label": self.SHORT.get(action, label),
                        "hit": self._r((x, y, self.COL_W, self.ROW_H)),
                        "chip": self._r(
                            (
                                x + self.COL_W - cw,
                                y + (self.ROW_H - ch) // 2,
                                cw,
                                ch
                            )
                        ),
                    }
                )

        bw, bh = self.BTN_SIZE

        reset_rect = self._r(
            (
                self.CENTER_X - self.BTN_GAP // 2 - bw,
                self.BTN_Y,
                bw,
                bh
            )
        )

        back_rect = self._r(
            (
                self.CENTER_X + self.BTN_GAP // 2,
                self.BTN_Y,
                bw,
                bh
            )
        )

        self.items.append(
            {
                "kind": "reset",
                "label": "Restablecer",
                "hit": reset_rect,
                "chip": reset_rect,
            }
        )

        self.items.append(
            {
                "kind": "back",
                "label": "Volver",
                "hit": back_rect,
                "chip": back_rect,
            }
        )

        self.info_pos = self._r(
            (
                self.COL_X[0],
                self.ROW_Y + 4 * self.ROW_H + 2,
                self.COL_W,
                self.ROW_H
            )
        ).topleft

    def _say(self, text):

        self.message = text
        self.message_time = 3.0

    def _activate(self, index):

        item = self.items[index]

        if item["kind"] == "action":

            self.listening = item["action"]

            self._say("Presioná la nueva tecla (ESC cancela)")

            return None

        if item["kind"] == "reset":

            controls.reset()

            self._say("Controles restablecidos")

            return None

        return "back"

    def _listen(self, key):

        if key == pygame.K_ESCAPE:

            self.listening = None

            self._say("Cancelado")

            return None

        if controls.is_reserved(key):

            self._say("Esa tecla está reservada, probá con otra")

            return None

        action = self.listening

        ok, swapped = controls.rebind(action, key)

        self.listening = None

        if not ok:

            self._say("No se pudo asignar esa tecla")

            return None

        if swapped is not None:

            self._say(
                f"{ACTION_LABELS[action]} y {ACTION_LABELS[swapped]} intercambiadas"
            )

        else:

            self._say(
                f"{ACTION_LABELS[action]} = {key_label(key)}"
            )

        return None

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if self.listening is not None:
                return self._listen(event.key)

            if event.key == pygame.K_ESCAPE:
                return "back"

            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.items)

            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.items)

            elif event.key == pygame.K_LEFT:
                self.selected = max(0, self.selected - 5)

            elif event.key == pygame.K_RIGHT:
                self.selected = min(len(self.items) - 1, self.selected + 5)

            elif event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_SPACE
            ):
                return self._activate(self.selected)

        elif event.type == pygame.MOUSEMOTION:

            if self.listening is None:

                for i, item in enumerate(self.items):

                    if item["hit"].collidepoint(event.pos):
                        self.selected = i

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if self.listening is not None:

                    self.listening = None

                    return None

                if self.close_rect.collidepoint(event.pos):
                    return "back"

                for i, item in enumerate(self.items):

                    if item["hit"].collidepoint(event.pos):

                        self.selected = i

                        return self._activate(i)

        return None

    def update(self, dt):

        if self.message_time > 0:
            self.message_time = max(0.0, self.message_time - dt)

    def _fit(self, text, font, color, max_width):

        surface = font.render(text, True, color)

        if surface.get_width() <= max_width:
            return surface

        height = max(1, round(surface.get_height() * max_width / surface.get_width()))

        return pygame.transform.smoothscale(surface, (max_width, height))

    def _chip(self, item, selected, listening):

        rect = item["chip"]

        if listening:
            image = self.chip_listen_img
            fill = (214, 126, 40)
        elif selected:
            image = self.chip_hover_img or self.chip_img
            fill = (74, 134, 214)
        else:
            image = self.chip_img
            fill = (24, 46, 102)

        if image is not None:

            self.screen.blit(image, rect)

        else:

            pygame.draw.rect(self.screen, fill, rect, border_radius=6)

            pygame.draw.rect(
                self.screen,
                (255, 255, 255) if (selected or listening) else (190, 210, 245),
                rect,
                2,
                border_radius=6
            )

        text = "Presioná..." if listening else controls.label(item["action"])

        surface = self._fit(
            text,
            self.small_font,
            (255, 255, 255),
            round(rect.width * 0.86)
        )

        self.screen.blit(surface, surface.get_rect(center=rect.center))

    def _button(self, item, selected):

        rect = item["chip"]

        if item["kind"] == "reset":
            image = (self.reset_hover_img or self.reset_img) if selected else self.reset_img
        else:
            image = (self.back_hover_img or self.back_img) if selected else self.back_img

        if image is not None:

            self.screen.blit(image, rect)

            return None

        pygame.draw.rect(
            self.screen,
            (74, 134, 214) if selected else (24, 46, 102),
            rect,
            border_radius=8
        )

        pygame.draw.rect(
            self.screen,
            (255, 255, 255) if selected else (190, 210, 245),
            rect,
            2,
            border_radius=8
        )

        surface = self._fit(
            item["label"],
            self.small_font,
            (255, 255, 255),
            round(rect.width * 0.86)
        )

        self.screen.blit(surface, surface.get_rect(center=rect.center))

        return None

    def draw(self):

        self.screen.blit(self.background, (0, 0))

        for title, rect in self.headers:

            header = self.header_font.render(title, True, self.HEADER)

            self.screen.blit(header, header.get_rect(midleft=(rect.left + 4, rect.centery)))

            pygame.draw.line(
                self.screen,
                (130, 170, 230),
                (rect.left, rect.bottom),
                (rect.right, rect.bottom),
                1
            )

        for i, item in enumerate(self.items):

            selected = i == self.selected

            if item["kind"] != "action":

                self._button(item, selected)

                continue

            row = item["hit"]

            if selected:

                pygame.draw.rect(
                    self.screen,
                    (74, 134, 214),
                    row.inflate(-4, -2),
                    border_radius=5
                )

            label = self._fit(
                item["label"],
                self.font,
                (255, 255, 255) if selected else self.TEXT,
                row.width - item["chip"].width - 14
            )

            self.screen.blit(
                label,
                label.get_rect(midleft=(row.left + 8, row.centery))
            )

            self._chip(item, selected, self.listening == item["action"])

        x, y = self.info_pos

        for line in self.INFO:

            text = self._fit(line, self.small_font, self.MUTED, round(self.COL_W * self.sx))

            self.screen.blit(text, (x + 4, y))

            y += text.get_height() + 1

        if self.message_time > 0:

            shadow = self.font.render(self.message, True, (20, 12, 8))
            text = self.font.render(self.message, True, (255, 224, 160))

            pos = (18, self.height - 15)

            self.screen.blit(shadow, shadow.get_rect(bottomleft=(pos[0] + 1, pos[1] + 1)))
            self.screen.blit(text, text.get_rect(bottomleft=pos))

        hint = self.small_font.render(
            "Click en una tecla para cambiarla  •  ESC volver",
            True,
            (235, 242, 255)
        )

        self.screen.blit(
            hint,
            hint.get_rect(
                bottomright=(self.width - 18, self.height - 15)
            )
        )


class Settings:

    IMG_W = 1672
    IMG_H = 941

    CLOSE_BOX = (1179, 219, 1204, 246)

    ROW_Y = [305, 360, 415, 470]

    LABEL_X = 520

    CONTROL_X = 830

    TRACK_SIZE = (280, 26)
    TOGGLE_SIZE = (80, 40)
    BUTTON_SIZE = (170, 40)
    HANDLE_SIZE = 34

    TRACK_PAD = 14

    ROWS = [
        ("Musica", "music_volume", "slider"),
        ("Efectos", "sfx_volume", "slider"),
        ("Pantalla completa", "fullscreen", "toggle"),
        ("Controles", "controls", "button"),
    ]

    def __init__(self, screen, background="mapaajustes.png"):

        self.screen = screen
        self.width, self.height = screen.get_size()

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        ui_dir = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
        )

        background_path = ui_dir / background

        if not background_path.exists():
            background_path = ui_dir / "mapaajustes.png"

        background = pygame.image.load(
            background_path
        ).convert()

        self.background = pygame.transform.smoothscale(
            background,
            (self.width, self.height)
        )

        self.track_img = self._load(
            ui_dir / "slider_track.png",
            self.TRACK_SIZE
        )

        self.handle_img = self._load(
            ui_dir / "slider_handle.png",
            (self.HANDLE_SIZE, self.HANDLE_SIZE)
        )

        self.toggle_on_img = self._load(
            ui_dir / "toggle_on.png",
            self.TOGGLE_SIZE
        )

        self.toggle_off_img = self._load(
            ui_dir / "toggle_off.png",
            self.TOGGLE_SIZE
        )

        self.button_img = self._load_optional(
            ui_dir / "btn_controles.png",
            self.BUTTON_SIZE
        )

        self.button_hover_img = self._load_optional(
            ui_dir / "btn_controles_hover.png",
            self.BUTTON_SIZE
        )

        self.font = pygame.font.Font(
            None,
            max(20, round(38 * self.sy))
        )

        self.small_font = pygame.font.Font(
            None,
            max(16, round(24 * self.sy))
        )

        self.values = load_settings()

        self.values["fullscreen"] = window_is_fullscreen()

        self.selected = 0
        self.dragging = None

        self.panel = None

        self.close_rect = self._box(self.CLOSE_BOX)

        self.control_rects = []

        for y in self.ROW_Y:

            kind = self.ROWS[len(self.control_rects)][2]

            if kind == "slider":
                width, height = self.TRACK_SIZE
            elif kind == "toggle":
                width, height = self.TOGGLE_SIZE
            else:
                width, height = self.BUTTON_SIZE

            rect = pygame.Rect(0, 0, width, height)
            rect.center = (self.CONTROL_X + width // 2, y)

            self.control_rects.append(
                self._scale_rect(rect)
            )


    def _load(self, path, size):

        image = pygame.image.load(path).convert_alpha()

        return pygame.transform.smoothscale(
            image,
            (
                max(1, round(size[0] * self.sx)),
                max(1, round(size[1] * self.sy))
            )
        )

    def _load_optional(self, path, size):

        if not path.exists():
            return None

        try:
            return self._load(path, size)
        except pygame.error:
            return None

    def _box(self, box):

        x1, y1, x2, y2 = box

        return pygame.Rect(
            round(x1 * self.sx),
            round(y1 * self.sy),
            round((x2 - x1) * self.sx),
            round((y2 - y1) * self.sy)
        )

    def _scale_rect(self, rect):

        return pygame.Rect(
            round(rect.x * self.sx),
            round(rect.y * self.sy),
            round(rect.width * self.sx),
            round(rect.height * self.sy)
        )

    def _slider_bounds(self, rect):

        pad = round(self.TRACK_PAD * self.sx)

        return rect.left + pad, rect.right - pad


    def _apply(self, key):

        if key == "music_volume":

            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self.values[key])

        elif key == "sfx_volume":

            audio.set_sfx_volume(self.values[key])

        elif key == "fullscreen":

            before = window_is_fullscreen()

            if before != bool(self.values[key]):

                try:
                    pygame.display.toggle_fullscreen()
                except pygame.error:
                    self.values[key] = before

    def _set_slider_from_mouse(self, index, mouse_x):

        key = self.ROWS[index][1]

        left, right = self._slider_bounds(
            self.control_rects[index]
        )

        value = (mouse_x - left) / max(1, right - left)

        self.values[key] = round(max(0.0, min(1.0, value)), 2)

        self._apply(key)

    def _change_slider(self, index, delta):

        key = self.ROWS[index][1]

        value = self.values[key] + delta

        self.values[key] = round(max(0.0, min(1.0, value)), 2)

        self._apply(key)

        save_settings(self.values)

    def _toggle(self, index):

        key = self.ROWS[index][1]

        self.values[key] = not self.values[key]

        self._apply(key)

        save_settings(self.values)

    def _open_controls(self):

        self.dragging = None

        self.panel = ControlsScreen(self.screen)

    def _activate(self, index):

        kind = self.ROWS[index][2]

        if kind == "toggle":
            self._toggle(index)

        elif kind == "button":
            self._open_controls()


    def handle_event(self, event):

        if self.panel is not None:

            if self.panel.handle_event(event) == "back":
                self.panel = None

            return None

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                save_settings(self.values)
                return "back"

            if event.key in (pygame.K_UP, pygame.K_w):

                self.selected = (self.selected - 1) % len(self.ROWS)

            elif event.key in (pygame.K_DOWN, pygame.K_s):

                self.selected = (self.selected + 1) % len(self.ROWS)

            elif event.key in (pygame.K_LEFT, pygame.K_a):

                if self.ROWS[self.selected][2] == "slider":
                    self._change_slider(self.selected, -0.05)

            elif event.key in (pygame.K_RIGHT, pygame.K_d):

                if self.ROWS[self.selected][2] == "slider":
                    self._change_slider(self.selected, 0.05)

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):

                self._activate(self.selected)

        elif event.type == pygame.MOUSEMOTION:

            if self.dragging is not None:

                self._set_slider_from_mouse(
                    self.dragging,
                    event.pos[0]
                )

            else:

                for i, rect in enumerate(self.control_rects):

                    if rect.inflate(20, 20).collidepoint(event.pos):
                        self.selected = i

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if self.close_rect.collidepoint(event.pos):

                    save_settings(self.values)
                    return "back"

                for i, rect in enumerate(self.control_rects):

                    if not rect.inflate(20, 20).collidepoint(event.pos):
                        continue

                    self.selected = i

                    if self.ROWS[i][2] == "slider":

                        self.dragging = i

                        self._set_slider_from_mouse(
                            i,
                            event.pos[0]
                        )

                    else:

                        self._activate(i)

        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1 and self.dragging is not None:

                self.dragging = None
                save_settings(self.values)

        return None

    def update(self, dt):

        if self.panel is not None:
            self.panel.update(dt)


    def draw(self):

        self.screen.blit(self.background, (0, 0))

        for i, (label, key, kind) in enumerate(self.ROWS):

            rect = self.control_rects[i]
            selected = i == self.selected

            color = (255, 255, 255) if selected else (215, 228, 250)

            text = self.font.render(label, True, color)

            text_rect = text.get_rect(
                midleft=(
                    round(self.LABEL_X * self.sx),
                    rect.centery
                )
            )

            self.screen.blit(text, text_rect)

            if selected:

                marker = self.font.render(">", True, (255, 255, 255))

                self.screen.blit(
                    marker,
                    marker.get_rect(
                        midright=(text_rect.left - 8, rect.centery)
                    )
                )

            if kind == "slider":

                self.screen.blit(self.track_img, rect)

                left, right = self._slider_bounds(rect)

                x = left + self.values[key] * (right - left)
                fill_left = rect.left + round(27 * rect.width / 600)
                fill_top = rect.top + round(19 * rect.height / 48)
                fill_height = max(1, round(14 * rect.height / 48))
                fill_width = round(x) - fill_left

                if fill_width > 0:

                    pygame.draw.rect(
                        self.screen,
                        (36, 78, 150),
                        (fill_left, fill_top, fill_width, fill_height),
                        border_radius=fill_height // 2
                    )
                handle_rect = self.handle_img.get_rect(
                    center=(round(x), rect.centery)
                )

                self.screen.blit(self.handle_img, handle_rect)

                percent = self.small_font.render(
                    f"{round(self.values[key] * 100)}%",
                    True,
                    color
                )

                self.screen.blit(
                    percent,
                    percent.get_rect(
                        midleft=(rect.right + 14, rect.centery)
                    )
                )

            elif kind == "toggle":

                image = (
                    self.toggle_on_img
                    if self.values[key]
                    else self.toggle_off_img
                )

                self.screen.blit(image, rect)

            elif self.button_img is not None:

                image = (
                    self.button_hover_img or self.button_img
                    if selected
                    else self.button_img
                )

                self.screen.blit(image, rect)

            else:

                pygame.draw.rect(
                    self.screen,
                    (74, 134, 214) if selected else (24, 46, 102),
                    rect,
                    border_radius=8
                )

                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255) if selected else (190, 210, 245),
                    rect,
                    2,
                    border_radius=8
                )

                button_text = self.small_font.render(
                    "Cambiar teclas",
                    True,
                    (255, 255, 255)
                )

                self.screen.blit(
                    button_text,
                    button_text.get_rect(center=rect.center)
                )

        controls_hint = self.small_font.render(
            "W/S mover  •  A/D ajustar  •  ENTER activar  •  ESC volver",
            True,
            (235, 242, 255)
        )

        self.screen.blit(
            controls_hint,
            controls_hint.get_rect(
                bottomright=(self.width - 18, self.height - 15)
            )
        )

        if self.panel is not None:
            self.panel.draw()