import pygame



PANEL_WIDTH = 300
MARGIN = 18


TOP = 118

SLIDE_TIME = 0.45       
DONE_TIME = 0.9         

BG_COLOR = (12, 14, 18, 205)
BORDER_COLOR = (255, 170, 60)
DONE_COLOR = (96, 214, 120)
TITLE_COLOR = (255, 176, 64)
TEXT_COLOR = (245, 245, 245)


class Objectives:

    def __init__(self, screen_size, objectives):

        self.width, self.height = screen_size
        self.objectives = list(objectives)

        self.title_font = pygame.font.Font(None, 22)
        self.font = pygame.font.Font(None, 26)

       
        self.panels = [
            (
                self._build(obj["text"], done=False),
                self._build(obj["text"], done=True),
            )
            for obj in self.objectives
        ]

        self.index = 0
        self.phase = "in"
        self.phase_time = 0.0
        self.was_done = False

        self.started = False
        self.finished = not self.objectives

    @staticmethod
    def _wrap(font, text, max_width):

        lines = []
        line = ""

        for word in text.split():

            test = f"{line} {word}".strip()

            if line and font.size(test)[0] > max_width:
                lines.append(line)
                line = word
            else:
                line = test

        if line:
            lines.append(line)

        return lines

    def _build(self, text, done):

        pad = 14

        lines = self._wrap(self.font, text, PANEL_WIDTH - pad * 2)

        title_text = "¡LISTO!" if done else "OBJETIVO"
        title_color = DONE_COLOR if done else TITLE_COLOR

        title = self.title_font.render(title_text, True, title_color)

        line_h = self.font.get_linesize()

        height = pad + title.get_height() + 6 + line_h * len(lines) + pad

        surf = pygame.Surface((PANEL_WIDTH, height), pygame.SRCALPHA)

        rect = surf.get_rect()

        pygame.draw.rect(surf, BG_COLOR, rect, border_radius=10)

        pygame.draw.rect(
            surf,
            (*(DONE_COLOR if done else BORDER_COLOR), 255),
            rect,
            width=2,
            border_radius=10
        )

        surf.blit(title, (pad, pad))

        y = pad + title.get_height() + 6

        for line in lines:

            surf.blit(
                self.font.render(line, True, TEXT_COLOR),
                (pad, y)
            )

            y += line_h

        return surf

    

    def _go_next(self, game):

        self.index += 1
        self.was_done = False

        while (
            self.index < len(self.objectives)
            and self.objectives[self.index]["done"](game)
        ):
            self.index += 1

        if self.index >= len(self.objectives):
            self.finished = True
            return

        self.phase = "in"
        self.phase_time = 0.0

    def update(self, dt, game):

        if self.finished:
            return

        self.started = True
        self.phase_time += dt

        obj = self.objectives[self.index]

        if self.phase == "in":

            if self.phase_time >= SLIDE_TIME:
                self.phase = "show"
                self.phase_time = 0.0

        elif self.phase == "show":

            max_time = obj.get("max_time")

            if obj["done"](game):

                self.was_done = True
                self.phase = "done"
                self.phase_time = 0.0

            elif max_time is not None and self.phase_time >= max_time:

                self.phase = "out"
                self.phase_time = 0.0

        elif self.phase == "done":

            if self.phase_time >= DONE_TIME:
                self.phase = "out"
                self.phase_time = 0.0

        elif self.phase == "out":

            if self.phase_time >= SLIDE_TIME:
                self._go_next(game)

  
    def _offset(self):
        distance = PANEL_WIDTH + MARGIN + 12

        if self.phase == "in":

            t = min(1.0, self.phase_time / SLIDE_TIME)
            ease = 1 - (1 - t) ** 3

            return int(distance * (1 - ease))

        if self.phase == "out":

            t = min(1.0, self.phase_time / SLIDE_TIME)
            ease = t ** 3

            return int(distance * ease)

        return 0

    def draw(self, screen):

        if self.finished or not self.started:
            return

        panel = self.panels[self.index][1 if self.was_done else 0]

        rect = panel.get_rect(
            topright=(self.width - MARGIN + self._offset(), TOP)
        )

        screen.blit(panel, rect)
