import pygame

from states.main_menu import main_menu


# ==========================================
# INICIAR PYGAME
# ==========================================

pygame.init()


# ==========================================
# CONFIGURACION DE LA VENTANA
# ==========================================

ANCHO = 1280
ALTO = 720

screen = pygame.display.set_mode(
    (ANCHO, ALTO)
)

pygame.display.set_caption(
    "Soulmon"
)


# ==========================================
# RELOJ
# ==========================================

clock = pygame.time.Clock()


# ==========================================
# MENU
# ==========================================

menu = MainMenu(screen)


# ==========================================
# BUCLE PRINCIPAL
# ==========================================

running = True

while running:

    # ==========================
    # EVENTOS
    # ==========================

    for event in pygame.event.get():

        # Cerrar ventana
        if event.type == pygame.QUIT:

            running = False

        # Eventos del menú
        action = menu.handle_event(
            event
        )

        # ==========================
        # ACCIONES
        # ==========================

        if action == "new_game":

            print(
                "Nueva partida"
            )

        elif action == "continue":

            print(
                "Continuar partida"
            )

        elif action == "settings":

            print(
                "Configuraciones"
            )

        elif action == "achievements":

            print(
                "Logros"
            )

        elif action == "quit":

            running = False

    # ==========================
    # DIBUJAR
    # ==========================

    menu.draw()

    pygame.display.flip()

    # 60 FPS
    clock.tick(60)


# ==========================================
# CERRAR
# ==========================================

pygame.quit()