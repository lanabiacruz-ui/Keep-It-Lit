import pygame

from core.audio_manager import audio
from world.items import load_icon
from ui.hud import HUD_DIR


SHOW_TIME = 5.0
FADE_TIME = 0.45

TITLE_TEXT = "¡Conseguiste un objeto!"
SUBTITLE_TEXT = "Ya lo puedes comprar en la tienda"

# Colores sacados del arte del HUD (hud_hotbar.png / hud_slot.png)
PANEL_GRAY = (143, 155, 161)
PANEL_EDGE = (75, 81, 88)
PANEL_LIGHT = (176, 186, 192)

WHITE = (255, 255, 255)
INK = (40, 46, 54)          # contorno oscuro de los textos (como los numeros)
SUB_COLOR = (52, 60, 68)    # gris oscuro para el texto chico

# imagen del HUD que se usa de fondo (panel gris liso con remaches)
BG_IMAGE = "hud_hotbar.png"
SLOT_IMAGE = "hud_slot.png"

# parte VISIBLE del dibujo de la hotbar (el resto es transparente), en
# fracciones del ancho/alto de la imagen: (izq, arriba, der, abajo)
BG_VISIBLE = (22 / 560, 8 / 120, 537 / 560, 113 / 120)


class ShopUnlockToast:
    """Cartel gris (el mismo gris del HUD) que aparece arriba de la pantalla
    cuando desbloqueas un item de la tienda por llegar a cierta oleada.

    Se le pasa la lista de items recien desbloqueados con push(); si se
    desbloquean varios juntos salen en un solo cartel.
    """

    def __init__(self, size):

        self.width, self.height = size

        self.queue = []
        self.current = None
        self.started = 0

        scale = self.height / 720

        self.box_w = max(320, round(480 * scale))
        self.box_h = max(70, round(100 * scale))

        self.top_font = pygame.font.Font(None, max(18, round(26 * scale)))
        self.name_font = pygame.font.Font(None, max(22, round(36 * scale)))
        self.sub_font = pygame.font.Font(None, max(16, round(22 * scale)))

        self.outline = max(1, round(2 * scale))

        # zona visible del panel (sin los margenes transparentes)
        l, t, r, b = BG_VISIBLE

        self.vis = pygame.Rect(
            round(l * self.box_w), round(t * self.box_h),
            round((r - l) * self.box_w), round((b - t) * self.box_h)
        )

        self.slot_size = round(self.vis.height * 0.80)
        self.icon_size = round(self.slot_size * 0.78)

        self.bg = self._load_scaled(BG_IMAGE, (self.box_w, self.box_h))
        self.slot = self._load_scaled(
            SLOT_IMAGE, (self.slot_size, self.slot_size)
        )

        self._icon_cache = {}

    # ------------------------------------------------------------------

    @staticmethod
    def _load_scaled(name, size):

        try:
            img = pygame.image.load(str(HUD_DIR / name)).convert_alpha()
        except (pygame.error, FileNotFoundError):
            return None

        return pygame.transform.smoothscale(img, size)

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

        if self._fits(self.name_font, text, max_width):
            return text

        # no entra: el primero y cuantos mas
        if len(names) > 1:
            text = f"{names[0]} y {len(names) - 1} más"

        while len(text) > 4 and not self._fits(self.name_font, text, max_width):
            text = text[:-2].rstrip() + "…"

        return text

    def _fits(self, font, text, max_width):

        return font.size(text)[0] + 2 * self.outline <= max_width

    def _outlined(self, font, text, color):
        """Texto con contorno oscuro, como los numeros de la hotbar."""

        o = self.outline

        base = font.render(text, True, color)
        edge = font.render(text, True, INK)

        surf = pygame.Surface(
            (base.get_width() + 2 * o, base.get_height() + 2 * o),
            pygame.SRCALPHA
        )

        for dx in range(-o, o + 1):
            for dy in range(-o, o + 1):
                if dx or dy:
                    surf.blit(edge, (o + dx, o + dy))

        surf.blit(base, (o, o))

        return surf

    def _panel(self):
        """Fondo del cartel: el panel gris del HUD (o uno dibujado)."""

        if self.bg is not None:
            return self.bg.copy()

        box = pygame.Surface((self.box_w, self.box_h), pygame.SRCALPHA)

        pygame.draw.rect(
            box, PANEL_GRAY, self.vis, border_radius=12
        )

        pygame.draw.rect(
            box, PANEL_EDGE, self.vis, width=3, border_radius=12
        )

        return box

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

        box = self._panel()

        pad = round(self.vis.height * 0.12)

        text_left = self.vis.left + pad + 4

        # casillero del HUD con el icono del item adentro
        slot_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
        slot_rect.midleft = (self.vis.left + pad, self.vis.centery)

        if self.slot is not None:
            box.blit(self.slot, slot_rect)

        icon = self._icon(self.current[0][0])

        if icon is not None:
            box.blit(icon, icon.get_rect(center=slot_rect.center))

        text_left = slot_rect.right + pad

        text_w = self.vis.right - pad - text_left

        title = self._outlined(self.top_font, TITLE_TEXT, WHITE)

        name = self._outlined(
            self.name_font, self._label(self.current, text_w), WHITE
        )

        sub = self.sub_font.render(SUBTITLE_TEXT, True, SUB_COLOR)

        gap = 1
        total = (
            title.get_height() + gap + name.get_height()
            + gap + sub.get_height()
        )

        y = self.vis.centery - total // 2

        for surf in (title, name, sub):

            box.blit(surf, (text_left, y))

            y += surf.get_height() + gap

        box.set_alpha(round(255 * alpha))

        # un poco mas abajo que el aviso de logros para no pisarse
        screen.blit(
            box,
            box.get_rect(midtop=(self.width // 2, round(self.height * 0.13)))
        )