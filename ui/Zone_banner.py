import pygame



FADE_IN = 0.45      
HOLD = 1.8          
FADE_OUT = 0.9      

FONT_SIZE = 64
TEXT_COLOR = (255, 238, 196)
OUTLINE_COLOR = (0, 0, 0)
LINE_COLOR = (255, 176, 64)


CENTER_Y = 0.27


class ZoneBanner:
   
   

    def __init__(self, screen_size):

        self.width, self.height = screen_size

        self.font = pygame.font.Font(None, FONT_SIZE)

        self.age = None     
        self.image = None

    @property
    def total_time(self):
        return FADE_IN + HOLD + FADE_OUT

    def show(self, name):
       

        self.image = self._build(name)
        self.age = 0.0

    def update(self, dt):

        if self.age is None:
            return

        self.age += dt

        if self.age >= self.total_time:
            self.age = None

    def _build(self, name):
      
        text = self.font.render(name, True, TEXT_COLOR)
        outline = self.font.render(name, True, OUTLINE_COLOR)

        pad_x = 36
        pad_y = 12
        line_h = 3
        gap = 6

        w = text.get_width() + pad_x * 2
        h = text.get_height() + pad_y * 2 + gap + line_h

        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        tx = (w - text.get_width()) // 2
        ty = pad_y

        for dx, dy in (
            (-2, 0), (2, 0), (0, -2), (0, 2),
            (-2, -2), (2, 2), (-2, 2), (2, -2)
        ):
            surf.blit(outline, (tx + dx, ty + dy))

        surf.blit(text, (tx, ty))

        
        line_w = text.get_width() + pad_x
        x0 = (w - line_w) // 2
        y0 = ty + text.get_height() + gap

        for i in range(line_w):

            t = abs(i - line_w / 2) / (line_w / 2)

            alpha = int(255 * max(0.0, 1.0 - t * t))

            surf.fill(
                (*LINE_COLOR, alpha),
                pygame.Rect(x0 + i, y0, 1, line_h)
            )

        return surf

    def _progress(self):
        

        age = self.age

        if age < FADE_IN:

            t = age / FADE_IN
            t = t * t * (3 - 2 * t)

            return t, (1.0 - t) * 10

        if age < FADE_IN + HOLD:
            return 1.0, 0.0

        t = (age - FADE_IN - HOLD) / FADE_OUT
        t = min(1.0, t)
        t = t * t * (3 - 2 * t)

        return 1.0 - t, 0.0

    def draw(self, screen):

        if self.age is None or self.image is None:
            return

        opacity, drop = self._progress()

        if opacity <= 0:
            return

        self.image.set_alpha(int(255 * opacity))

        rect = self.image.get_rect(
            center=(self.width // 2, int(self.height * CENTER_Y))
        )

        screen.blit(self.image, rect.move(0, drop))
