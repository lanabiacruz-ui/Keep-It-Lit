import pygame
from pathlib import Path

from core.Save_manager import (
    list_slots, delete_save, check_password, MODE_HARDCORE
)
from states.password_menu import PasswordMenu


class ContinueGame:

    IMG_W = 1672
    IMG_H = 941

    CLOSE_BOX = (1179, 219, 1204, 246)

    SLOT_IMG_W = 220
    SLOT_IMG_H = 200

    GRID_COLS = 4
    GRID_ROWS = 2
    GRID_TOP = 270
    GRID_CELL_H = 114
    GRID_GAP_X = 50
    GRID_GAP_Y = 8
    GRID_CENTER_X = 846

    SLOT_BOXES = []

    for _row in range(GRID_ROWS):
        for _col in range(GRID_COLS):
            _w = round(GRID_CELL_H * SLOT_IMG_W / SLOT_IMG_H)
            _total = GRID_COLS * _w + (GRID_COLS - 1) * GRID_GAP_X
            _x = GRID_CENTER_X - _total // 2 + _col * (_w + GRID_GAP_X)
            _y = GRID_TOP + _row * (GRID_CELL_H + GRID_GAP_Y)
            SLOT_BOXES.append((_x, _y, _x + _w, _y + GRID_CELL_H))

    MODE_LOCAL = (51, 31, 172, 48)

    NAME_LOCAL = (51, 50, 172, 73)
    DATE_LOCAL = (75, 80, 138, 96)
    PLAY_LOCAL = (48, 100, 168, 138)
    DELETE_LOCAL = (53, 140, 162, 174)

    ZOOM = 1.4

    CONFIRM_IMG_W = 420
    CONFIRM_IMG_H = 200
    CONFIRM_NO_LOCAL = (145, 111, 202, 139)
    CONFIRM_YES_LOCAL = (234, 115, 286, 142)

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()

        ui_dir = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "ui"
        )

        self.background = self._load_scaled(
            ui_dir / "mapapartidas.png",
            (self.width, self.height)
        )

        self.slot_img = pygame.image.load(
            ui_dir / "slot_partida.png"
        ).convert_alpha()

        self.slot_hover_img = pygame.image.load(
            ui_dir / "slot_partida_hover.png"
        ).convert_alpha()

        self.slot_empty_img = pygame.image.load(
            ui_dir / "slot_vacio.png"
        ).convert_alpha()

        self.confirm_img = pygame.image.load(
            ui_dir / "confirmar_eliminar.png"
        ).convert_alpha()

        self.close_rect = self._scale_box(self.CLOSE_BOX)

        self.slot_rects = [
            self._scale_box(box) for box in self.SLOT_BOXES
        ]

        self.slot_img_scaled = []
        self.slot_hover_img_scaled = []
        self.slot_empty_img_scaled = []

        for rect in self.slot_rects:

            size = (rect.width, rect.height)

            self.slot_img_scaled.append(
                pygame.transform.smoothscale(self.slot_img, size)
            )

            self.slot_hover_img_scaled.append(
                pygame.transform.smoothscale(self.slot_hover_img, size)
            )

            self.slot_empty_img_scaled.append(
                pygame.transform.smoothscale(self.slot_empty_img, size)
            )

        slot_scale = self.slot_rects[0].width / self.SLOT_IMG_W

        self.name_size = max(10, round(26 * slot_scale))
        self.date_font = pygame.font.Font(
            None, max(9, round(20 * slot_scale))
        )
        self.mode_font = pygame.font.Font(
            None, max(9, round(22 * slot_scale))
        )
        self.name_fonts = {}

        base = self.slot_rects[0]

        self.zoom_size = (
            round(base.width * self.ZOOM),
            round(base.height * self.ZOOM)
        )

        self.zoom_img = pygame.transform.smoothscale(
            self.slot_hover_img,
            self.zoom_size
        )

        self.zoom_name_size = round(self.name_size * self.ZOOM)

        self.zoom_date_font = pygame.font.Font(
            None, round(max(9, round(20 * slot_scale)) * self.ZOOM)
        )

        self.zoom_mode_font = pygame.font.Font(
            None, round(max(9, round(22 * slot_scale)) * self.ZOOM)
        )

        self.hover = None

        confirm_w = round(self.width * 0.32)
        confirm_h = round(
            confirm_w * self.CONFIRM_IMG_H / self.CONFIRM_IMG_W
        )

        self.confirm_img_scaled = pygame.transform.smoothscale(
            self.confirm_img,
            (confirm_w, confirm_h)
        )

        self.confirm_rect = self.confirm_img_scaled.get_rect(
            center=(self.width // 2, self.height // 2)
        )

        self.confirm_no_rect = self._scale_local(
            self.CONFIRM_NO_LOCAL,
            self.CONFIRM_IMG_W,
            self.CONFIRM_IMG_H,
            self.confirm_rect
        )

        self.confirm_yes_rect = self._scale_local(
            self.CONFIRM_YES_LOCAL,
            self.CONFIRM_IMG_W,
            self.CONFIRM_IMG_H,
            self.confirm_rect
        )

        self.overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )

        self.overlay.fill((0, 0, 0, 140))

        self.pending_delete = None

        self.password_menu = None
        self.pending_action = None

        self.refresh()

    def _load_scaled(self, path, size):

        image = pygame.image.load(path).convert()

        return pygame.transform.scale(image, size)

    def _scale_box(self, box):

        x1, y1, x2, y2 = box

        sx = self.width / self.IMG_W
        sy = self.height / self.IMG_H

        return pygame.Rect(
            round(x1 * sx),
            round(y1 * sy),
            round((x2 - x1) * sx),
            round((y2 - y1) * sy)
        )

    def _scale_local(self, local_box, local_w, local_h, parent_rect):

        x1, y1, x2, y2 = local_box

        sx = parent_rect.width / local_w
        sy = parent_rect.height / local_h

        return pygame.Rect(
            parent_rect.x + round(x1 * sx),
            parent_rect.y + round(y1 * sy),
            round((x2 - x1) * sx),
            round((y2 - y1) * sy)
        )

    def _button_rect(self, slot_index, local_box):

        return self._scale_local(
            local_box,
            self.SLOT_IMG_W,
            self.SLOT_IMG_H,
            self.slot_rects[slot_index]
        )

    def _zoom_rect(self, index):

        rect = pygame.Rect(0, 0, *self.zoom_size)

        rect.center = self.slot_rects[index].center

        rect.clamp_ip(pygame.Rect(0, 0, self.width, self.height))

        return rect

    def _zoom_button(self, index, local_box):

        return self._scale_local(
            local_box,
            self.SLOT_IMG_W,
            self.SLOT_IMG_H,
            self._zoom_rect(index)
        )

    def _hover_at(self, pos):

        if (
            self.hover is not None
            and not self.slots[self.hover]["empty"]
            and self._zoom_rect(self.hover).collidepoint(pos)
        ):
            return

        self.hover = None

        for i, slot in enumerate(self.slots):

            if slot["empty"]:
                continue

            if self.slot_rects[i].collidepoint(pos):

                self.hover = i

                return

    def _name_font(self, size):

        if size not in self.name_fonts:
            self.name_fonts[size] = pygame.font.Font(None, size)

        return self.name_fonts[size]

    def _fit_name(self, text, max_width, size=None):

        if size is None:
            size = self.name_size

        while size > 9:

            font = self._name_font(size)

            if font.size(text)[0] <= max_width:
                return font.render(text, True, (25, 35, 55))

            size -= 1

        font = self._name_font(9)

        while len(text) > 1 and font.size(text + "...")[0] > max_width:
            text = text[:-1]

        return font.render(text + "...", True, (25, 35, 55))

    def refresh(self):

        self.slots = list_slots()

    def _run_action(self, action, index):

        slot = self.slots[index]

        if action == "start":

            return ("start", slot["path"], slot["data"])

        self.pending_delete = index

        return None

    def _request(self, action, index):

        slot = self.slots[index]

        if not slot.get("has_password"):

            return self._run_action(action, index)

        self.password_menu = PasswordMenu(self.screen, mode="ask")
        self.pending_action = (action, index)

        return None

    def _handle_password_event(self, event):

        result = self.password_menu.handle_event(event)

        if result == "back":

            self.password_menu = None
            self.pending_action = None

            return None

        if result is None:

            return None

        action, index = self.pending_action

        slot = self.slots[index]

        if check_password(slot["data"], result[1]):

            self.password_menu.finish()

            self.password_menu = None
            self.pending_action = None

            return self._run_action(action, index)

        self.password_menu.clear()
        self.password_menu.message = "Contraseña incorrecta"

        return None

    def handle_event(self, event):

        if self.password_menu is not None:

            return self._handle_password_event(event)

        if self.pending_delete is not None:

            return self._handle_confirm_event(event)

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                return "back"

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button != 1:
                return None

            if self.close_rect.collidepoint(event.pos):

                return "back"

            self._hover_at(event.pos)

            if self.hover is not None:

                i = self.hover

                play_rect = self._zoom_button(i, self.PLAY_LOCAL)
                delete_rect = self._zoom_button(i, self.DELETE_LOCAL)

                if play_rect.collidepoint(event.pos):

                    return self._request("start", i)

                if delete_rect.collidepoint(event.pos):

                    return self._request("delete", i)

        return None

    def _handle_confirm_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                self.pending_delete = None

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button != 1:
                return None

            if self.confirm_yes_rect.collidepoint(event.pos):

                slot = self.slots[self.pending_delete]

                delete_save(slot["path"])

                self.pending_delete = None

                self.refresh()

            elif self.confirm_no_rect.collidepoint(event.pos):

                self.pending_delete = None

        return None

    def draw(self):

        if self.password_menu is not None:

            self.password_menu.draw()

            return

        self.screen.blit(self.background, (0, 0))

        mouse_pos = pygame.mouse.get_pos()

        if self.pending_delete is None:
            self._hover_at(mouse_pos)
        else:
            self.hover = None

        for i, slot in enumerate(self.slots):

            rect = self.slot_rects[i]

            if slot["empty"]:

                image = self.slot_empty_img_scaled[i]

            elif i == self.hover:

                image = self.slot_hover_img_scaled[i]

            else:

                image = self.slot_img_scaled[i]

            self.screen.blit(image, rect)

            if slot["empty"]:

                continue

            hardcore = slot.get("mode") == MODE_HARDCORE

            mode_rect = self._button_rect(i, self.MODE_LOCAL)

            mode_surface = self.mode_font.render(
                "HARDCORE" if hardcore else "NORMAL",
                True,
                (170, 25, 25) if hardcore else (25, 35, 55)
            )

            self.screen.blit(
                mode_surface,
                mode_surface.get_rect(center=mode_rect.center)
            )

            name_rect = self._button_rect(i, self.NAME_LOCAL)

            name_surface = self._fit_name(
                slot["player_name"] or "Sin nombre",
                name_rect.width
            )

            name_pos = name_surface.get_rect(center=name_rect.center)

            self.screen.blit(name_surface, name_pos)

            date_rect = self._button_rect(i, self.DATE_LOCAL)

            date_text = self._format_date(slot["last_played"])

            date_surface = self.date_font.render(
                date_text,
                True,
                (45, 55, 75)
            )

            date_pos = date_surface.get_rect(center=date_rect.center)

            self.screen.blit(date_surface, date_pos)

        if self.hover is not None:
            self._draw_zoom(self.hover)

        if self.pending_delete is not None:

            self.screen.blit(self.overlay, (0, 0))

            self.screen.blit(self.confirm_img_scaled, self.confirm_rect)

    def _draw_zoom(self, index):

        slot = self.slots[index]

        zoom = self._zoom_rect(index)

        self.screen.blit(self.zoom_img, zoom)

        hardcore = slot.get("mode") == MODE_HARDCORE

        mode_rect = self._zoom_button(index, self.MODE_LOCAL)

        mode_surface = self.zoom_mode_font.render(
            "HARDCORE" if hardcore else "NORMAL",
            True,
            (170, 25, 25) if hardcore else (25, 35, 55)
        )

        self.screen.blit(
            mode_surface,
            mode_surface.get_rect(center=mode_rect.center)
        )

        name_rect = self._zoom_button(index, self.NAME_LOCAL)

        name_surface = self._fit_name(
            slot["player_name"] or "Sin nombre",
            name_rect.width,
            self.zoom_name_size
        )

        self.screen.blit(
            name_surface,
            name_surface.get_rect(center=name_rect.center)
        )

        date_rect = self._zoom_button(index, self.DATE_LOCAL)

        date_surface = self.zoom_date_font.render(
            self._format_date(slot["last_played"]),
            True,
            (45, 55, 75)
        )

        self.screen.blit(
            date_surface,
            date_surface.get_rect(center=date_rect.center)
        )

    def _format_date(self, iso_text):

        if not iso_text:
            return ""

        try:

            date_part, time_part = iso_text.split("T")

            year, month, day = date_part.split("-")

            hour, minute = time_part.split(":")[:2]

            return f"{day}/{month}/{year} {hour}:{minute}"

        except (ValueError, IndexError):

            return iso_text