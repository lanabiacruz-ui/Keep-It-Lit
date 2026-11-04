import pygame

from core.audio_manager import audio
from world.items import load_icon


SHOW_TIME = 5.0
FADE_TIME = 0.45

TITLE_TEXT = "¡Nuevo item en la tienda!"
SUBTITLE_TEXT = "Ya lo podés comprar"

GOLD = (255, 205, 90)
WHITE = (255, 255, 255)
SOFT = (200, 210, 235)

BG_COLOR = (20, 24, 40, 235)


class ShopUnlockToast:
    """Cartel arriba de la pantalla: "desbloqueaste un item en la tienda".

    Se le pasa la lista de items recien desbloqueados con push(); si se
    desbloquean varios juntos salen en un solo cartel.
    """

    def __init__(self, size):

        self.width, self.height = size

        self.queue = []
        self.current = None
        self.started = 0

        scale = self.height / 720

        self.box_w = max(300, round(430 * scale))
        self.box_h = max(64, round(84 * scale))

        self.top_font = pygame.font.Font(None, max(18, round(26 * scale)))
        self.name_font = pygame.font.Font(None, max(22, round(34 * scale)))
        self.sub_font = pygame.font.Font(None, max(16, round(22 * scale)))

        self.icon_size = self.box_h - 2 * round(self.box_h * 0.14)

        self._icon_cache = {}

    # ------------------------------------------------------------------

    def push(self, entries):
        """entries: lista de (item_id, nombre) recien desbloqueados."""

        entries = [e for e in entries if e]

        if not entries:
            return

        self.queue.append(list(entries))

    def _next(self):

        if not self.queue:
            self.current = None
            return

        self.current = self.queue.pop(0)
        self.started = pygame.time.get_ticks()

        audio.play("objective_new")

    def _icon(self, item_id):

        if item_id not in self._icon_cache:

            icon = load_icon(item_id)

            if icon is not None:
                icon = pygame.transform.smoothscale(
                    icon, (self.icon_size, self.icon_size)
                )

            self._icon_cache[item_id] = icon

        return self._icon_cache[item_id]

    def _label(self, entries, max_width):

        names = [name for _, name in entries]

        text = names[0] if len(names) == 1 else ", ".join(names)

        if self.name_font.size(text)[0] <= max_width:
            return text

        # no entra: el primero y cuantos mas
        if len(names) > 1:
            text = f"{names[0]} y {len(names) - 1} más"

        while (
            len(text) > 4
            and self.name_font.size(text)[0] > max_width
        ):
            text = text[:-2].rstrip() + "…"

        return text

    # ------------------------------------------------------------------

    def draw(self, screen):

        if self.current is None:
            self._next()

        if self.current is None:
            return

        elapsed = (pygame.time.get_ticks() - self.started) / 1000

        if elapsed >= SHOW_TIME:

            self._next()

            if self.current is None:
                return

            elapsed = 0.0

        if elapsed < FADE_TIME:
            alpha = elapsed / FADE_TIME
        elif elapsed > SHOW_TIME - FADE_TIME:
            alpha = (SHOW_TIME - elapsed) / FADE_TIME
        else:
            alpha = 1.0

        alpha = max(0.0, min(1.0, alpha))

        box = pygame.Surface((self.box_w, self.box_h), pygame.SRCALPHA)

        pygame.draw.rect(
            box, BG_COLOR, box.get_rect(), border_radius=12
        )

        pygame.draw.rect(
            box, GOLD, box.get_rect(), width=3, border_radius=12
        )

        pad = round(self.box_h * 0.14)

        text_left = pad + 4

        icon = self._icon(self.current[0][0])

        if icon is not None:

            icon_rect = icon.get_rect(midleft=(pad + 2, self.box_h // 2))

            box.blit(icon, icon_rect)

            text_left = icon_rect.right + pad

        text_w = self.box_w - text_left - pad

        title = self.top_font.render(TITLE_TEXT, True, GOLD)

        name = self.name_font.render(
            self._label(self.current, text_w), True, WHITE
        )

        sub = self.sub_font.render(SUBTITLE_TEXT, True, SOFT)

        gap = 2
        total = (
            title.get_height() + gap + name.get_height()
            + gap + sub.get_height()
        )

        y = (self.box_h - total) // 2

        for surf in (title, name, sub):

            box.blit(surf, (text_left, y))

            y += surf.get_height() + gap

        box.set_alpha(round(255 * alpha))

        # un poco mas abajo que el aviso de logros para no pisarse
        screen.blit(
            box,
            box.get_rect(midtop=(self.width // 2, round(self.height * 0.14)))
        )