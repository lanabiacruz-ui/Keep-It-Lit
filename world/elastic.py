"""Gelea elastica: se tira hacia donde mira el jugador, rebota en las
paredes y pega a los enemigos que toca."""

import pygame

SPEED = 240.0             # px del mundo por segundo
LIFE = 3.0                # se esfuma despues de estos segundos
BOUNCES = 3               # rebotes contra paredes antes de deshacerse
SIZE = 8                  # tamaño de la colision
RADIUS = 14               # alcance del golpe alrededor de la gelea
HIT_COOLDOWN = 0.35       # cada cuanto puede volver a pegar (por gelea)
ENEMY_DAMAGE = 1          # golpe a slimes y arañas
ARENA_DAMAGE = 0.25       # golpe a enemigos de las salas de combate

COLOR = (120, 240, 200)
EDGE = (40, 140, 120)
SHINE = (230, 255, 245)


class ElasticShot:

    def __init__(self, x, y, direction):

        self.pos = pygame.Vector2(x, y)

        d = pygame.Vector2(direction)

        if d.length_squared() < 0.01:
            d = pygame.Vector2(0, 1)

        self.vel = d.normalize() * SPEED
        self.bounces = BOUNCES
        self.life = LIFE
        self.hit_t = 0.0
        self.spin = 0.0
        self.done = False

    def _probe(self, x, y):

        r = pygame.Rect(0, 0, SIZE, SIZE)
        r.center = (round(x), round(y))

        return r

    def update(self, dt, collision_map):

        self.life -= dt
        self.hit_t -= dt
        self.spin = (self.spin + 540.0 * dt) % 360.0

        if self.life <= 0:
            self.done = True
            return

        for axis in ("x", "y"):

            if axis == "x":
                nx = self.pos.x + self.vel.x * dt
                ny = self.pos.y
            else:
                nx = self.pos.x
                ny = self.pos.y + self.vel.y * dt

            if collision_map.can_move(self._probe(nx, ny)):
                self.pos.update(nx, ny)
                continue

            # rebota: invierte ese eje
            if axis == "x":
                self.vel.x = -self.vel.x
            else:
                self.vel.y = -self.vel.y

            self.bounces -= 1

            if self.bounces < 0:
                self.done = True
                return

    def draw(self, screen, camera):

        r = pygame.Rect(0, 0, SIZE, SIZE)
        r.center = (round(self.pos.x), round(self.pos.y))

        dest = camera.apply(r)

        radius = max(3, int(dest.width * 0.8))
        center = dest.center

        pygame.draw.circle(screen, COLOR, center, radius)
        pygame.draw.circle(screen, EDGE, center, radius, 1)

        shine_r = max(1, radius // 3)

        pygame.draw.circle(
            screen,
            SHINE,
            (center[0] - radius // 3, center[1] - radius // 3),
            shine_r,
        )