import json
import math
from pathlib import Path

import pygame


SETTINGS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "settings.json"
)

SLOTS = 8

# Catalogo de emotes disponibles para elegir.

EMOTES = [
    {"id": "saludo",   "label": "Saludo",   "color": (120, 200, 255)},
    {"id": "risa",     "label": "Risa",     "color": (255, 214, 90)},
    {"id": "baile",    "label": "Baile",    "color": (255, 120, 180)},
    {"id": "enojo",    "label": "Enojo",    "color": (240, 90, 70)},
    {"id": "gracias",  "label": "Gracias",  "color": (130, 220, 140)},
    {"id": "triste",   "label": "Triste",   "color": (130, 150, 230)},
]

OUTER_R = 250
INNER_R = 95
GAP_DEG = 2.2

COL_DIM = (0, 0, 0, 150)
COL_SEG = (28, 26, 30, 235)
COL_SEG_HOVER = (70, 62, 52, 245)
COL_EDGE = (150, 140, 125)
COL_EDGE_HOVER = (255, 205, 120)
COL_TEXT = (235, 230, 220)
COL_MUTED = (140, 135, 128)


def _emote_by_id(emote_id):

    for emote in EMOTES:
        if emote["id"] == emote_id:
            return emote

    return None


def _segment_points(cx, cy, r_in, r_out, a0, a1, steps=14):

    points = []

    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        points.append((cx + math.cos(a) * r_out, cy + math.sin(a) * r_out))

    for i in range(steps, -1, -1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        points.append((cx + math.cos(a) * r_in, cy + math.sin(a) * r_in))

    return points


class EmoteWheel:

    def __init__(self, screen):

        self.screen = screen
        self.width, self.height = screen.get_size()
        self.cx = self.width // 2
        self.cy = self.height // 2

        self.active = False

        
        self.picking = None

        self.hover = None
        self.picker_hover = None
        self.picker_rects = []

        self.slots = [None] * SLOTS
        self._fonts = {}

        self._load()

    

    def _font(self, size):

        font = self._fonts.get(size)

        if font is None:
            font = pygame.font.Font(None, size)
            self._fonts[size] = font

        return font

    def _load(self):

        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            saved = data.get("emote_wheel")

        except (OSError, ValueError, AttributeError, UnicodeDecodeError):
            return

        if not isinstance(saved, list):
            return

        for i in range(min(SLOTS, len(saved))):

            if isinstance(saved[i], str) and _emote_by_id(saved[i]):
                self.slots[i] = saved[i]

    def _save(self):

        data = {}

        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                data = {}

        except (OSError, ValueError, UnicodeDecodeError):
            data = {}

        data["emote_wheel"] = list(self.slots)

        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        except OSError:
            pass

    # ------------------------------------------------------------ estado

    def open(self):

        self.active = True
        self.picking = None
        self.hover = None

    def close(self):

        self.active = False
        self.picking = None
        self.hover = None

    def toggle(self):

        if self.active:
            self.close()
        else:
            self.open()

    

    def _slot_at(self, pos):

        dx = pos[0] - self.cx
        dy = pos[1] - self.cy

        dist = math.hypot(dx, dy)

        if dist < INNER_R or dist > OUTER_R:
            return None

       
        angle = math.degrees(math.atan2(dy, dx)) + 90 + 180 / SLOTS

        return int((angle % 360) // (360 / SLOTS))

    def _slot_center(self, i):

        r = (INNER_R + OUTER_R) / 2

        a = math.radians(-90 + i * (360 / SLOTS))

        return (
            self.cx + math.cos(a) * r,
            self.cy + math.sin(a) * r,
        )

    def _picker_layout(self):

       
        w, h = 230, 44
        x = self.cx + OUTER_R + 30
        y = self.cy - ((len(EMOTES) + 1) * (h + 6)) // 2

        rects = []

        for i in range(len(EMOTES) + 1):
            rects.append(pygame.Rect(x, y + i * (h + 6), w, h))

        return rects

    
    def handle_event(self, event):

        """Devuelve True si el evento fue consumido por la rueda."""

        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                if self.picking is not None:
                    self.picking = None
                else:
                    self.close()

                return True

            return False

        if event.type == pygame.MOUSEMOTION:

            if self.picking is None:
                self.hover = self._slot_at(event.pos)
                self.picker_hover = None
            else:
                self.picker_hover = None

                for i, rect in enumerate(self.picker_rects):
                    if rect.collidepoint(event.pos):
                        self.picker_hover = i

            return False

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if self.picking is None:

                    slot = self._slot_at(event.pos)

                    if slot is not None:
                        self.picking = slot
                        self.picker_rects = self._picker_layout()
                        self.picker_hover = None
                    else:
                        
                        self.close()

                else:

                    chosen = None

                    for i, rect in enumerate(self.picker_rects):
                        if rect.collidepoint(event.pos):
                            chosen = i

                    if chosen is None:
                        
                        self.picking = None

                    else:

                        if chosen < len(EMOTES):
                            self.slots[self.picking] = EMOTES[chosen]["id"]
                        else:
                            self.slots[self.picking] = None

                        self._save()
                        self.picking = None

            elif event.button == 3 and self.picking is None:

                
                slot = self._slot_at(event.pos)

                if slot is not None and self.slots[slot] is not None:
                    self.slots[slot] = None
                    self._save()

            return True

        if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
            return True

        return False

    

    def _draw_icon(self, surface, emote, center, size):

        color = emote["color"]

        pygame.draw.circle(surface, color, center, size)
        pygame.draw.circle(surface, (255, 255, 255), center, size, 2)

        letter = self._font(int(size * 1.4)).render(
            emote["label"][0], True, (30, 24, 20)
        )

        surface.blit(letter, letter.get_rect(center=center))

    def draw(self, surface=None):

        if not self.active:
            return

        surface = surface or self.screen

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill(COL_DIM)
        surface.blit(dim, (0, 0))

        layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        step = 360 / SLOTS

        for i in range(SLOTS):

            a0 = -90 - step / 2 + i * step + GAP_DEG / 2
            a1 = a0 + step - GAP_DEG

            hovered = (
                i == self.hover and self.picking is None
            ) or i == self.picking

            points = _segment_points(
                self.cx, self.cy, INNER_R, OUTER_R, a0, a1
            )

            pygame.draw.polygon(
                layer,
                COL_SEG_HOVER if hovered else COL_SEG,
                points
            )

            pygame.draw.polygon(
                layer,
                COL_EDGE_HOVER if hovered else COL_EDGE,
                points,
                3 if hovered else 2
            )

        surface.blit(layer, (0, 0))

        for i in range(SLOTS):

            center = self._slot_center(i)
            center = (int(center[0]), int(center[1]))

            emote = _emote_by_id(self.slots[i])

            if emote is None:

                
                pygame.draw.line(
                    surface, COL_MUTED,
                    (center[0] - 14, center[1]), (center[0] + 14, center[1]), 3
                )
                pygame.draw.line(
                    surface, COL_MUTED,
                    (center[0], center[1] - 14), (center[0], center[1] + 14), 3
                )

            else:

                self._draw_icon(surface, emote, center, 30)

                label = self._font(24).render(emote["label"], True, COL_TEXT)
                surface.blit(
                    label,
                    label.get_rect(midtop=(center[0], center[1] + 36))
                )

        
        pygame.draw.circle(
            surface, (20, 18, 22), (self.cx, self.cy), INNER_R - 12
        )
        pygame.draw.circle(
            surface, COL_EDGE, (self.cx, self.cy), INNER_R - 12, 3
        )

        title = self._font(34).render("EMOTES", True, COL_TEXT)
        surface.blit(title, title.get_rect(center=(self.cx, self.cy - 12)))

        if self.picking is None:
            hint_text = "Click: elegir"
        else:
            hint_text = "Elegi un emote"

        hint = self._font(22).render(hint_text, True, COL_MUTED)
        surface.blit(hint, hint.get_rect(center=(self.cx, self.cy + 16)))

        if self.picking is None:
            foot = "Click derecho: vaciar   |   H / Esc: cerrar"
            foot_img = self._font(24).render(foot, True, COL_MUTED)
            surface.blit(
                foot_img,
                foot_img.get_rect(
                    midtop=(self.cx, self.cy + OUTER_R + 24)
                )
            )

        if self.picking is not None:
            self._draw_picker(surface)

    def _draw_picker(self, surface):

        if not self.picker_rects:
            self.picker_rects = self._picker_layout()

        panel = self.picker_rects[0].unionall(self.picker_rects).inflate(24, 56)

        bg = pygame.Surface(panel.size, pygame.SRCALPHA)
        bg.fill((22, 20, 24, 240))
        surface.blit(bg, panel.topleft)

        pygame.draw.rect(surface, COL_EDGE, panel, 2, border_radius=8)

        title = self._font(26).render(
            "Lugar {}".format(self.picking + 1), True, COL_TEXT
        )
        surface.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 8)))

        for i, rect in enumerate(self.picker_rects):

            hovered = i == self.picker_hover

            pygame.draw.rect(
                surface,
                COL_SEG_HOVER if hovered else (40, 37, 42),
                rect,
                border_radius=6
            )
            pygame.draw.rect(
                surface,
                COL_EDGE_HOVER if hovered else COL_EDGE,
                rect,
                2,
                border_radius=6
            )

            if i < len(EMOTES):

                emote = EMOTES[i]

                self._draw_icon(
                    surface, emote, (rect.x + 24, rect.centery), 14
                )

                text = self._font(26).render(emote["label"], True, COL_TEXT)
                surface.blit(
                    text,
                    text.get_rect(midleft=(rect.x + 50, rect.centery))
                )

                if self.slots[self.picking] == emote["id"]:
                    mark = self._font(22).render("equipado", True, COL_MUTED)
                    surface.blit(
                        mark,
                        mark.get_rect(midright=(rect.right - 10, rect.centery))
                    )

            else:

                text = self._font(26).render("Dejar vacio", True, COL_MUTED)
                surface.blit(text, text.get_rect(center=rect.center))