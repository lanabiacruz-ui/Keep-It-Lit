import json
import pygame
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


def save_settings(settings):

    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)

    except OSError:
        return False

    return True


class Settings:

    IMG_W = 1672
    IMG_H = 941

    # Boton X de la ventana (mismo que en Continuar partida)
    CLOSE_BOX = (1179, 219, 1204, 246)

    # Centro vertical de cada fila (en coordenadas de la imagen 1672x941)
    ROW_Y = [335, 400, 465]

    LABEL_X = 520

    CONTROL_X = 830

    TRACK_SIZE = (280, 26)
    TOGGLE_SIZE = (80, 40)
    HANDLE_SIZE = 34

    # Margen interno del riel para que la carita no se salga
    TRACK_PAD = 14

    ROWS = [
        ("Musica", "music_volume", "slider"),
        ("Efectos", "sfx_volume", "slider"),
        ("Pantalla completa", "fullscreen", "toggle"),
    ]

    def __init__(self, screen):

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

        background = pygame.image.load(
            ui_dir / "mapaajustes.png"
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

        self.font = pygame.font.Font(
            None,
            max(20, round(38 * self.sy))
        )

        self.small_font = pygame.font.Font(
            None,
            max(16, round(24 * self.sy))
        )

        self.values = load_settings()

        self.selected = 0
        self.dragging = None

        self.close_rect = self._box(self.CLOSE_BOX)

        self.control_rects = []

        for y in self.ROW_Y:

            width, height = (
                self.TRACK_SIZE
                if self.ROWS[len(self.control_rects)][2] == "slider"
                else self.TOGGLE_SIZE
            )

            rect = pygame.Rect(0, 0, width, height)
            rect.center = (self.CONTROL_X + width // 2, y)

            self.control_rects.append(
                self._scale_rect(rect)
            )

    # ---------- utilidades ----------

    def _load(self, path, size):

        image = pygame.image.load(path).convert_alpha()

        return pygame.transform.smoothscale(
            image,
            (
                max(1, round(size[0] * self.sx)),
                max(1, round(size[1] * self.sy))
            )
        )

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

    # ---------- cambios de valor ----------

    def _apply(self, key):

        if key == "music_volume":

            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self.values[key])

        elif key == "fullscreen":

            try:
                pygame.display.toggle_fullscreen()
            except pygame.error:
                pass

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

    # ---------- eventos ----------

    def handle_event(self, event):

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

                if self.ROWS[self.selected][2] == "toggle":
                    self._toggle(self.selected)

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

                        self._toggle(i)

        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1 and self.dragging is not None:

                self.dragging = None
                save_settings(self.values)

        return None

    def update(self, dt):
        pass

    # ---------- dibujo ----------

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

            else:

                image = (
                    self.toggle_on_img
                    if self.values[key]
                    else self.toggle_off_img
                )

                self.screen.blit(image, rect)

        controls = self.small_font.render(
            "W/S mover  •  A/D ajustar  •  ENTER activar  •  ESC volver",
            True,
            (235, 242, 255)
        )

        self.screen.blit(
            controls,
            controls.get_rect(
                bottomright=(self.width - 18, self.height - 15)
            )
        )