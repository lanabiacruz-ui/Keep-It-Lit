import pygame


class PlayerMovement:

    def __init__(self, speed=140):

        self.speed = speed

        self._rest_x = 0.0
        self._rest_y = 0.0

    def update(
        self,
        player_rect,
        collision_map,
        dt
    ):

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        moving = dx != 0 or dy != 0

        if not moving:

            self._rest_x = 0.0
            self._rest_y = 0.0

            return False, None

        direction = pygame.Vector2(
            dx,
            dy
        ).normalize()

        self._rest_x += direction.x * self.speed * dt
        self._rest_y += direction.y * self.speed * dt

        step_x = int(self._rest_x)
        step_y = int(self._rest_y)

        self._rest_x -= step_x
        self._rest_y -= step_y

        self._move(player_rect, collision_map, step_x, 0)
        self._move(player_rect, collision_map, 0, step_y)

        # Direccion para la animacion (en diagonal gana izquierda/derecha)
        if dx < 0:
            facing = "left"
        elif dx > 0:
            facing = "right"
        elif dy < 0:
            facing = "up"
        else:
            facing = "down"

        return True, facing

    def _move(
        self,
        rect,
        collision_map,
        step_x,
        step_y
    ):

        sign_x = (step_x > 0) - (step_x < 0)
        sign_y = (step_y > 0) - (step_y < 0)

        for _ in range(abs(step_x) + abs(step_y)):

            test = rect.move(sign_x, sign_y)

            if not collision_map.can_move(test):
                break

            rect.x = test.x
            rect.y = test.y