import pygame


class PlayerAnimation:

    def __init__(self, sprite_path):

        # Cargar sprites
        self.sheet = pygame.image.load(
            sprite_path
        ).convert()

        self.sheet.set_colorkey(
            self.sheet.get_at((0, 0))
        )

        # CONFIGURACIÓN

        self.direction = "down"

        self.current_frame = 0

        self.timer = 0

        # Tiempo entre frames
        self.animation_speed = 0.12

        # Tamaño que tendrá el personaje en el juego
        self.sprite_width = 48
        self.sprite_height = 80
        
        # FRAMES

        self.frames = {
            "up": [],
            "down": [],
            "left": [],
            "right": []
        }

        # Personaje quieto del centro
        self.idle = None

        self.load_sprites()

    
    # CARGAR SPRITES
    

    def load_sprites(self):

        # --------------------------------------------------
        # ARRIBA
        # --------------------------------------------------
        #
        # Los 4 personajes de la parte superior
        #

        up = [
            pygame.Rect(225, 60, 50, 100),
            pygame.Rect(370, 60, 50, 100),
            pygame.Rect(445, 60, 50, 100),
            pygame.Rect(515, 60, 50, 100)
        ]

        # --------------------------------------------------
        # IZQUIERDA
        # --------------------------------------------------

        left = [
            pygame.Rect(10, 220, 55, 100),
            pygame.Rect(65, 220, 55, 100),
            pygame.Rect(120, 220, 55, 100),
            pygame.Rect(175, 220, 55, 100)
        ]

        # --------------------------------------------------
        # DERECHA
        # --------------------------------------------------

        right = [
            pygame.Rect(305, 220, 55, 100),
            pygame.Rect(365, 220, 55, 100),
            pygame.Rect(425, 220, 55, 100),
            pygame.Rect(475, 220, 37, 100)
        ]

        # --------------------------------------------------
        # ABAJO
        # --------------------------------------------------

        down = [
            pygame.Rect(110, 365, 55, 110),
            pygame.Rect(185, 365, 55, 110),
            pygame.Rect(255, 365, 55, 110),
            pygame.Rect(330, 365, 55, 110)
        ]

        # --------------------------------------------------
        # PERSONAJE QUIETO
        # --------------------------------------------------

        idle = pygame.Rect(
            235,
            220,
            55,
            100
        )

        # Crear frames
        self.frames["up"] = self.create_frames(up)
        self.frames["left"] = self.create_frames(left)
        self.frames["right"] = self.create_frames(right)
        self.frames["down"] = self.create_frames(down)

        self.idle = self.create_frame(idle)

    # ======================================================
    # CREAR UN FRAME
    # ======================================================

    def create_frame(self, rect):

        frame = self.sheet.subsurface(
            rect
        ).copy()

        frame = pygame.transform.scale(
            frame,
            (
                self.sprite_width,
                self.sprite_height
            )
        )

        return frame

    # ======================================================
    # CREAR VARIOS FRAMES
    # ======================================================

    def create_frames(self, rectangles):

        frames = []

        for rect in rectangles:

            frame = self.create_frame(
                rect
            )

            frames.append(frame)

        return frames

    # ======================================================
    # CAMBIAR DIRECCIÓN
    # ======================================================

    def set_direction(self, direction):

        if direction != self.direction:

            self.direction = direction

            # Empezar la animación desde el primer frame
            self.current_frame = 0

            self.timer = 0

    # ======================================================
    # ACTUALIZAR ANIMACIÓN
    # ======================================================

    def update(self, moving, dt):

        # --------------------------------------------------
        # SI ESTÁ QUIETO
        # --------------------------------------------------

        if not moving:

            self.current_frame = 0
            self.timer = 0

            return

        # --------------------------------------------------
        # SI SE ESTÁ MOVIENDO
        # --------------------------------------------------

        self.timer += dt

        if self.timer >= self.animation_speed:

            self.timer = 0

            self.current_frame += 1

            # Volver al primer frame
            if self.current_frame >= len(
                self.frames[self.direction]
            ):

                self.current_frame = 0

    # ======================================================
    # OBTENER IMAGEN ACTUAL
    # ======================================================

    def get_image(self, moving):

        # Si está quieto
        if not moving:

            return self.idle

        # Si está caminando
        return self.frames[
            self.direction
        ][self.current_frame]