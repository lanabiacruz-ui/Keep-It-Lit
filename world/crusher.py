import math
import random

import pygame


CRUSH_DAMAGE = 0.35

OPEN_TIME = (3.5, 7.0)
WARN_TIME = 0.9
CLOSE_TIME = 0.22
CLOSED_TIME = (2.0, 3.5)
OPEN_ANIM_TIME = 0.9

GAPS = (
    ("top", 374, 52, 372, 330, -1),
    ("bottom", 377, 57, 708, 755, +1),
)


OPEN = "open"
WARN = "warn"
CLOSING = "closing"
CLOSED = "closed"
OPENING = "opening"


class CrusherBlock:

    def __init__(self, name, x, width, base_y, wall_y, direction,
                 first_delay):

        self.name = name
        self.x = x
        self.width = width
        self.base_y = base_y
        self.direction = direction

        self.reach = abs(wall_y - base_y)

        self.state = OPEN
        self.timer = first_delay

        self.progress = 0.0

        self.rect = pygame.Rect(x, base_y, width, 0)

        self._warn_t = 0.0


    def _refresh_rect(self):

        length = round(self.reach * self.progress)

        if self.direction < 0:

            self.rect.update(
                self.x, self.base_y - length, self.width, length
            )

        else:

            self.rect.update(
                self.x, self.base_y, self.width, length
            )

    def gap_rect(self):

        if self.direction < 0:

            return pygame.Rect(
                self.x, self.base_y - self.reach, self.width, self.reach
            )

        return pygame.Rect(
            self.x, self.base_y, self.width, self.reach
        )

    @property
    def solid(self):

        return self.progress > 0.0


    def update(self, dt):

        self.timer -= dt

        if self.state == OPEN:

            self.progress = 0.0

            if self.timer <= 0:

                self.state = WARN
                self.timer = WARN_TIME
                self._warn_t = 0.0

        elif self.state == WARN:

            self._warn_t += dt

            if self.timer <= 0:

                self.state = CLOSING
                self.timer = CLOSE_TIME

        elif self.state == CLOSING:

            self.progress = 1.0 - max(0.0, self.timer) / CLOSE_TIME

            if self.timer <= 0:

                self.progress = 1.0
                self.state = CLOSED
                self.timer = random.uniform(*CLOSED_TIME)

        elif self.state == CLOSED:

            self.progress = 1.0

            if self.timer <= 0:

                self.state = OPENING
                self.timer = OPEN_ANIM_TIME

        elif self.state == OPENING:

            self.progress = max(0.0, self.timer) / OPEN_ANIM_TIME

            if self.timer <= 0:

                self.progress = 0.0
                self.state = OPEN
                self.timer = random.uniform(*OPEN_TIME)

        self._refresh_rect()

    @property
    def crushing(self):

        return self.state in (CLOSING, CLOSED)


    def draw(self, screen, camera):

        if self.state == WARN:

            pulse = 0.5 + 0.5 * math.sin(self._warn_t * 16)

            area = camera.apply(self.gap_rect())

            if area.width > 0 and area.height > 0:

                glow = pygame.Surface(area.size, pygame.SRCALPHA)
                glow.fill((255, 60, 50, int(70 + 110 * pulse)))
                screen.blit(glow, area)

            shake = round(2 * pulse)

        else:

            shake = 0

        if not self.solid and self.state != WARN:
            return

        rect = camera.apply(self.rect)

        if self.state == WARN:

            tip = pygame.Rect(self.x, self.base_y, self.width, 6)

            if self.direction < 0:
                tip.bottom = self.base_y

            rect = camera.apply(tip)
            rect.x += shake

        if rect.width <= 0 or rect.height <= 0:
            return

        pygame.draw.rect(screen, (128, 112, 103), rect)

        step = max(6, rect.width // 4)

        for y in range(rect.top + step, rect.bottom, step):

            pygame.draw.line(
                screen, (96, 80, 69),
                (rect.left, y), (rect.right - 1, y), 1
            )

        pygame.draw.rect(
            screen, (28, 22, 20), rect, max(2, round(2 * camera.zoom))
        )


class CrusherBlocks:

    def __init__(self, collision_map):

        self.collision_map = collision_map

        self.blocks = []

        for i, (name, x, width, base_y, wall_y, direction) in enumerate(GAPS):

            block = CrusherBlock(
                name, x, width, base_y, wall_y, direction,
                first_delay=random.uniform(2.0, 4.0) + i * 1.5,
            )

            self.blocks.append(block)

            collision_map.obstacles.append(block.rect)


    @staticmethod
    def _push_out(rect, block_rect, cmap):

        left_x = block_rect.left - rect.width
        right_x = block_rect.right

        if rect.centerx < block_rect.centerx:
            order = (left_x, right_x)
        else:
            order = (right_x, left_x)

        for x in order:

            probe = rect.copy()
            probe.x = x

            if cmap.can_move(probe):

                rect.x = x

                return True

        return False

    def update(self, game, dt):

        cmap = self.collision_map

        player = game.player

        for block in self.blocks:

            block.update(dt)

            if not block.solid:
                continue

            if player.rect.colliderect(block.rect) and block.crushing:

                if player.hurt(block.rect.center):

                    game.take_damage(CRUSH_DAMAGE)

                self._push_out(player.rect, block.rect, cmap)

            for arena in game.arenas:

                for enemy in arena.enemies:

                    if enemy.rect.colliderect(block.rect):

                        if self._push_out(enemy.rect, block.rect, cmap):

                            pos = getattr(enemy, "pos", None)

                            if pos is not None:
                                pos.x = enemy.rect.centerx
                                pos.y = enemy.rect.centery

    def draw(self, screen, camera):

        for block in self.blocks:
            block.draw(screen, camera)
