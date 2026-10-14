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

    SLOT_BOXES = [
        (470, 292, 700, 501),
        (730, 292, 960, 501),
        (990, 292, 1220, 501),
    ]

    SLOT_IMG_W = 220
    SLOT_IMG_H = 200

    # Cartelito del modo (Normal / Hardcore), arriba del nombre
    MODE_LOCAL = (51, 31, 172, 48)

    NAME_LOCAL = (51, 50, 172, 73)
    DATE_LOCAL = (75, 80, 138, 96)
    PLAY_LOCAL = (48, 100, 168, 138)
    DELETE_LOCAL = (53, 140, 162, 174)

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

        self.name_font = pygame.font.Font(None, 24)
        self.date_font = pygame.font.Font(None, 18)
        self.mode_font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 24)

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

        # Contraseña: se pide antes de jugar o borrar una partida.
        # pending_action = ("start" | "delete", numero de slot)
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

    def refresh(self):

        self.slots = list_slots()

    def _run_action(self, action, index):
        """Hace lo que se pidio (ya con la contraseña aceptada)."""

        slot = self.slots[index]

        if action == "start":

            return ("start", slot["path"], slot["data"])

        self.pending_delete = index

        return None

    def _request(self, action, index):
        """Si la partida tiene contraseña la pide; si no, sigue directo."""

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

            for i, slot in enumerate(self.slots):

                if slot["empty"]:
                    continue

                play_rect = self._button_rect(i, self.PLAY_LOCAL)
                delete_rect = self._button_rect(i, self.DELETE_LOCAL)

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

        for i, slot in enumerate(self.slots):

            rect = self.slot_rects[i]

            if slot["empty"]:

                image = self.slot_empty_img_scaled[i]

            elif rect.collidepoint(mouse_pos):

                image = self.slot_hover_img_scaled[i]

            else:

                image = self.slot_img_scaled[i]

            self.screen.blit(image, rect)

            if slot["empty"]:

                label = self.name_font.render(
                    "Vacio",
                    True,
                    (235, 242, 255)
                )

                label_rect = label.get_rect(center=rect.center)

                self.screen.blit(label, label_rect)

                continue

            # Modo de la partida
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

            name_surface = self.name_font.render(
                slot["player_name"] or "Sin nombre",
                True,
                (25, 35, 55)
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

        controls = self.small_font.render(
            "Click en Jugar para continuar  -  ESC volver",
            True,
            (235, 242, 255)
        )

        controls_rect = controls.get_rect(
            bottomright=(
                self.width - 18,
                self.height - 15
            )
        )

        self.screen.blit(controls, controls_rect)

        if self.pending_delete is not None:

            self.screen.blit(self.overlay, (0, 0))

            self.screen.blit(self.confirm_img_scaled, self.confirm_rect)

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